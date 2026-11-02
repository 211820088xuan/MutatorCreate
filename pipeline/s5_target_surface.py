#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""s5_target_surface.py —— 阶段5.1：抽取 fuzz target 的输入攻击面（**确定性，0 LLM**）

职责边界
  只描述「输入从 harness 怎么进来、能到哪些函数、哪些函数在解析输入、哪里有内存操作」。
  **不判断漏洞**，也不声称「某个字段一定控制某条分支」——那属于 candidate/feature/plan 层。

产出
  v2/target_surface.json（schema: stage5.target_surface.v1）

`field_mapping_complete` 的判据（4 条全部满足才算 complete）
  ① 输入格式已知（line_record / binary_record / raw_bytes）
  ② 至少有一个 field 带 locator（record_sequence + anchor 即可，不要求字节偏移）
  ③ 从 harness 到故障函数存在一条**每跳都有源码证据**的路径
  ④ 该路径上没有 unknown 跳

  这四条都可以由程序判定，不靠人工拍板。

用法
  python3 s5_target_surface.py --osv ARVO-42494732
  python3 s5_target_surface.py --osv ARVO-42494732 --selftest   # 只跑证据链自检
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys

import cfg_lib

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
TOP = os.path.dirname(ROOT)
OUT = os.path.join(ROOT, "projects")

ENTRY = "LLVMFuzzerTestOneInput"

# 解析类函数的命名线索（只用于"候选"，不是结论）
PARSER_RX = re.compile(r"(read|parse|decode|load|scan|unpack|deserial|ingest)", re.I)
# 内存操作 / sink 线索
SINK_RX = re.compile(r"\b(free|destroy|release|malloc|calloc|realloc|memcpy|memmove|memset"
                     r"|strcpy|strcat|strlen|sprintf)\s*\(", re.I)

# 记录的格式线索：形如 "  0\r\nSECTION\r\n"
DXF_RECORD_RX = re.compile(rb"^\s*(\d{1,3})\r?\n", re.M)


# ────────────────────────── 读取输入 ──────────────────────────

def load_json(p):
    return json.load(open(p, encoding="utf-8"))


def read_lines(p):
    return open(p, encoding="utf-8", errors="replace").read().split("\n")


def read_cpg_dump(p):
    methods, edges = [], []
    for ln in open(p, encoding="utf-8"):
        t = ln.rstrip("\n").split("\t")
        if t[0] == "@@M" and len(t) >= 6:
            methods.append({"file": t[1], "name": t[2], "start": int(t[3] or 0),
                            "end": int(t[4] or 0), "external": t[5] == "1"})
        elif t[0] == "@@C" and len(t) >= 4:
            edges.append((t[1], t[2], t[3]))
    return methods, edges


# ────────────────────────── 抽取 ──────────────────────────

def extract_entry(harness_src: str) -> dict:
    """从 harness 源码里取入口函数名、参数名、直接调用。"""
    m = re.search(rf"\b{ENTRY}\s*\(([^)]*)\)", harness_src)
    params = []
    if m:
        parts = [p.strip() for p in m.group(1).split(",") if p.strip()]
        for p in parts:
            ids = re.findall(r"[A-Za-z_]\w*", p)
            params.append(ids[-1] if ids else p)
    body = harness_src[m.start():] if m else ""
    calls = sorted({c for c in re.findall(r"\b([A-Za-z_]\w*)\s*\(", body)
                    if c not in {"if", "for", "while", "switch", "return", "sizeof",
                                 "else", "do", "case", "break", "continue", ENTRY}})
    return {"entry_symbol": ENTRY,
            "parameters": params,
            "input_parameter": params[0] if params else None,
            "input_length_parameter": params[1] if len(params) > 1 else None,
            "direct_calls": calls}


def direct_callees(edges, entry_name: str) -> set[str]:
    out = set()
    for cf, cn, cs in edges:
        if cn == entry_name:
            out |= {c for c in cs.split("|")
                    if re.match(r"^[A-Za-z_]", c) and not c.startswith("<operator>")}
    return out


def detect_format(seed: bytes) -> dict:
    """按字节特征粗判输入格式。只判大类，不解析字段。"""
    if not seed:
        return {"format": "raw_bytes", "evidence": "no seed"}
    if DXF_RECORD_RX.search(seed[:4096]):
        codes = [int(x) for x in DXF_RECORD_RX.findall(seed[:20000])]
        return {"format": "line_record",
                "evidence": f"前 4KB 内出现 {len(DXF_RECORD_RX.findall(seed[:4096]))} 次 '^<数字>\\n' 记录头",
                "record_header_rx": r"^\s*(\d{1,3})\r?\n",
                "group_codes_seen": sorted(set(codes))[:40],
                "group_code_count": len(set(codes))}
    printable = sum(1 for b in seed[:2048] if 32 <= b < 127 or b in (9, 10, 13))
    if printable / max(1, min(len(seed), 2048)) > 0.9:
        return {"format": "line_record", "evidence": "前 2KB >90% 可打印字符", "group_codes_seen": []}
    return {"format": "binary_record", "evidence": "非文本特征", "group_codes_seen": []}


def find_parser_candidates(reachable: list[dict], src_cache: dict, input_names: list[str]) -> list[dict]:
    """在可达函数里找"可能在解析输入"的函数：命名线索 + 源码里引用了输入缓冲。"""
    out = []
    for f in reachable:
        lines = src_cache.get(f["file"])
        if not lines:
            continue
        lo, hi = f["lines"][0] - 1, min(f["lines"][1], len(lines))
        body = "\n".join(lines[lo:hi])
        hits = []
        for pat in (r"->chain\b", r"->byte\b", r"->size\b", r"->opts\b"):
            for i in range(lo, hi):
                if re.search(pat, lines[i]):
                    hits.append([i + 1, lines[i].strip()[:160]])
                    break
        name_hit = bool(PARSER_RX.search(f["name"]))
        if not (name_hit or hits):
            continue
        out.append({
            "function": f["name"], "file": f["file"], "lines": f["lines"],
            "depth": f["depth"],
            "role": ("entry_api" if f["depth"] == 1 else "record_parser" if name_hit else "helper"),
            "input_expressions": sorted({h[1].split("->")[1].split()[0] for h in hits
                                         if "->" in h[1]})[:6],
            "evidence_lines": hits[:3],
            "confidence": "medium" if (name_hit and hits) else "low",
        })
    return out


def find_sinks(reachable: list[dict], src_cache: dict) -> list[dict]:
    out = []
    for f in reachable:
        lines = src_cache.get(f["file"])
        if not lines:
            continue
        lo, hi = f["lines"][0] - 1, min(f["lines"][1], len(lines))
        hits = []
        for i in range(lo, hi):
            m = SINK_RX.search(lines[i])
            if m:
                hits.append({"line": i + 1, "call": m.group(1).lower(),
                             "code": lines[i].strip()[:160]})
            if len(hits) >= 6:
                break
        if hits:
            out.append({"function": f["name"], "file": f["file"], "lines": f["lines"],
                        "kinds": sorted({h["call"] for h in hits}),
                        "evidence_lines": hits[:4]})
    return out



def fault_flow_evidence(src_cache, fault, fault_range=None):
    """在**故障函数自己的行范围**内找两类证据：字段写入局部变量、分支判据。

    ⚠ 必须限定在函数范围内。libredwg 里 `dxf_entities_read`(12205-12240) 和
    `dxf_objects_read`(12261-12293) 几乎是同一段代码的复制，用 ±80 行窗口会跨到
    前一个函数，取到错误证据。
    """
    rel = None
    for f, lines in src_cache.items():
        if lines and fault.get("file") and f.endswith(fault["file"]):
            rel = f
            break
    if not rel or not fault.get("line"):
        return [], []
    lines = src_cache[rel]
    if fault_range:
        lo, hi = max(0, fault_range[0] - 1), min(len(lines), fault_range[1])
    else:
        lo = max(0, fault["line"] - 80)
        hi = min(len(lines), fault["line"] + 40)
    field_ev, branch_ev = [], []
    for i in range(lo, hi):
        t = lines[i].strip()
        if re.search(r"\b(strncpy|memcpy|strdup)\s*\(", t) or re.search(r"=\s*\w+->(value|chain|string|name)\b", t):
            field_ev.append([i + 1, t[:160]])
        if re.match(r"^(if|while|for)\s*\(", t):
            branch_ev.append([i + 1, t[:160]])
        if len(field_ev) >= 4 and len(branch_ev) >= 6:
            break
    return field_ev, branch_ev


FREE_CALL_RX = re.compile(r"\b([A-Za-z_]\w*)\s*\(\s*&?\s*([A-Za-z_]\w*)\s*\)\s*;")


def step6_flow_evidence(src_cache, fault, fault_range):
    """用 flow 证明「释放后控制流能回到解引用同一变量的行」。

    这是 §8.1 第 6 步。做法：
      · 在故障函数里找"释放类调用 W(v)"
      · 从该行开始走控制流
      · 若轨迹里出现回边⟲，且回边之后的某行仍解引用 v（v-> / v. / v[）
        → 说明下一轮迭代会读到已释放内存 → complete
    """
    rel = next((f for f, ls in src_cache.items()
                if ls and fault.get("file") and f.endswith(fault["file"])), None)
    if not rel or not fault_range:
        return None
    lines = src_cache[rel]
    lo, hi = max(0, fault_range[0] - 1), min(len(lines), fault_range[1] - 1)
    for i in range(lo, hi + 1):
        m = FREE_CALL_RX.search(cfg_lib.strip_code(lines[i]))
        if not m:
            continue
        callee, var = m.group(1), m.group(2)
        if not re.search(r"(free|destroy|release)", callee, re.I):
            continue
        trace = cfg_lib.flow(lines, lo, hi, i, 20)
        bi = next((k for k, t in enumerate(trace) if t["back_edge"]), None)
        if bi is None:
            continue
        deref = re.compile(rf"\b{re.escape(var)}\b\s*(->|\.|\[)")
        for t in trace[bi:]:
            if deref.search(cfg_lib.strip_code(lines[t["line"]])):
                return {"free_line": i + 1, "free_code": lines[i].strip()[:160],
                        "back_edge_to": trace[bi]["next"] + 1 if trace[bi]["next"] is not None else None,
                        "deref_line": t["line"] + 1,
                        "deref_code": lines[t["line"]].strip()[:160],
                        "variable": var, "callee": callee}
    return None


def step5_predicate_evidence(src_cache, fault, fault_range, free_line):
    """证明「释放发生在哪个 else 分支、由哪个 if 条件决定」。

    做法：用块结构找到 free_line 所在的 else 块，再找紧挨它前面的 if 块，
    取出 if 的条件原文。
    """
    rel = next((f for f, ls in src_cache.items()
                if ls and fault.get("file") and f.endswith(fault["file"])), None)
    if not rel or not fault_range:
        return None
    lines = src_cache[rel]
    lo, hi = max(0, fault_range[0] - 1), min(len(lines), fault_range[1] - 1)
    fl = free_line - 1
    blks = cfg_lib.blocks(lines, lo, hi)
    encl = [b for b in blks if b["open"] <= fl <= b["close"]]
    else_blk = next((b for b in encl if b["kind"] == "else"), None)
    if not else_blk:
        return None
    if_blk = next((b for b in blks if b["kind"] == "if"
                   and b["close"] + 1 == else_blk["header"]), None)
    if not if_blk:
        return None
    return {"if_line": if_blk["header"] + 1,
            "if_code": lines[if_blk["header"]].strip()[:160],
            "else_line": else_blk["header"] + 1,
            "else_code": lines[else_blk["header"]].strip()[:160],
            "free_line": free_line}

def evidence_chain(harness: dict, reachable: list[dict], parsers: list[dict],
                   sinks: list[dict], fault: dict, src_cache: dict) -> list[dict]:
    """§8.1 的六步证据链，每步给出 status（complete / partial / unknown）与证据。"""
    steps = []
    steps_meta = {}

    def add(step, question, status, evidence, note=""):
        steps.append({"step": step, "question": question, "status": status,
                      "evidence": evidence, "note": note})

    add(1, "LLVMFuzzerTestOneInput(data,size) 如何构造解析上下文",
        "complete" if harness.get("parameters") else "unknown",
        [f"entry={harness['entry_symbol']} params={harness['parameters']}"])

    add(2, "输入缓冲区如何绑定到解析器读取的结构",
        "complete" if any(p["input_expressions"] for p in parsers) else "unknown",
        [list(e) if isinstance(e, (list, tuple)) else [e.get("line"), e.get("code")]
         for p in parsers[:1] for e in (p.get("evidence_lines") or [])])

    feat = [p for p in parsers if p["function"] == fault.get("function")]
    rp = [p for p in parsers if p.get("role") == "record_parser"]
    add(3, "解析器把输入记录转成内部结构",
        "complete" if rp else "unknown",
        [[p["function"], p["file"], p["lines"][0]] for p in rp[:4]])

    fr = next((f["lines"] for f in reachable if f["name"] == fault.get("function")), None)
    if fr:
        steps_meta["fault_function_range"] = fr
    f6 = step6_flow_evidence(src_cache, fault, fr)
    field_ev, branch_ev = fault_flow_evidence(src_cache, fault, fr)
    add(4, "输入的哪个字段进入目标变量",
        "complete" if field_ev else "partial", field_ev,
        "找到『字段写入局部变量』的语句即算闭合" if field_ev else "故障函数里没有字段写入语句")

    f5 = step5_predicate_evidence(src_cache, fault, fr, f6["free_line"]) if f6 else None
    if f5:
        add(5, "目标函数的判据如何决定分支", "complete",
            [[f5["if_line"], f5["if_code"]], [f5["else_line"], f5["else_code"]]],
            f"L{f5['free_line']} 的释放位于 L{f5['else_line']} 的 else 分支，"
            f"该分支由 L{f5['if_line']} 的 `{f5['if_code']}` 决定")
        steps_meta["step5_predicate"] = f5
    else:
        add(5, "目标函数的判据如何决定分支",
            "partial" if branch_ev else "unknown", branch_ev,
            "只列出了分支条件，未能把释放点绑定到具体的 if/else" if branch_ev else "")

    if f6:
        add(6, "后续记录如何让控制流再次读到目标变量", "complete",
            [[f6["free_line"], f6["free_code"]], [f6["deref_line"], f6["deref_code"]]],
            f"flow 证明：L{f6['free_line']} 释放 `{f6['variable']}` 后经回边⟲回到 "
            f"L{f6['back_edge_to']}，再在 L{f6['deref_line']} 解引用它")
        steps_meta["step6_flow"] = f6
    else:
        add(6, "后续记录如何让控制流再次读到目标变量", "unknown", [],
            'flow 未发现「释放类调用 → 回边 → 解引用同一变量」的路径')

    return steps


# ────────────────────────── 主流程 ──────────────────────────

def main():
    ap = argparse.ArgumentParser(description="阶段5.1：抽取 target surface（0 LLM）")
    ap.add_argument("--osv", required=True)
    ap.add_argument("--seed", default=None, help="用于格式判定的种子（默认取 seeds/ 第一个）")
    ap.add_argument("--selftest", action="store_true", help="只打印证据链自检")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    S5 = os.path.join(OUT, args.osv)
    for need in ("source_context.json", "audit_worklist.json", "cpg_dump.tsv"):
        if not os.path.exists(os.path.join(S5, need)):
            raise SystemExit(f"缺少 {S5}/{need}")

    ctx = load_json(os.path.join(S5, "source_context.json"))
    wl = load_json(os.path.join(S5, "audit_worklist.json"))
    root = ctx["repo_local"]
    methods, edges = read_cpg_dump(os.path.join(S5, "cpg_dump.tsv"))

    hdir = os.path.join(S5, "harness")
    hsrc = {}
    if os.path.isdir(hdir):
        for fn in sorted(os.listdir(hdir)):
            if fn.endswith((".c", ".cc", ".cpp")):
                hsrc[fn] = open(os.path.join(hdir, fn), encoding="utf-8", errors="replace").read()
    # 挑真正定义入口的 harness（可能是 dwgfuzz.c 或 llvmfuzz.c）
    harness, harness_file = {"entry_symbol": ENTRY, "parameters": [],
                             "input_parameter": None, "input_length_parameter": None,
                             "direct_calls": []}, None
    for fn, txt in hsrc.items():
        h = extract_entry(txt)
        if h["parameters"] and len(h["parameters"]) >= len(harness["parameters"]):
            harness, harness_file = h, fn

    reachable = wl["functions"]
    src_cache = {}
    for f in reachable:
        if f["file"] not in src_cache:
            p = os.path.join(root, f["file"])
            src_cache[f["file"]] = read_lines(p) if os.path.isfile(p) else None

    parsers = find_parser_candidates(reachable, src_cache, harness["parameters"])
    sinks = find_sinks(reachable, src_cache)

    # 输入格式：从种子判定
    seeddir = os.path.join(S5, "seeds")
    seedp = args.seed
    if not seedp and os.path.isdir(seeddir):
        cands = [f for f in sorted(os.listdir(seeddir)) if not f.startswith(".")]
        seedp = os.path.join(seeddir, cands[0]) if cands else None
    fmt = detect_format(open(seedp, "rb").read() if seedp and os.path.isfile(seedp) else b"")

    # field：line_record 下把"出现过的组码"当成候选字段（locator 是记录序列，不是字节偏移）
    fields = []
    for code in fmt.get("group_codes_seen", [])[:20]:
        fields.append({
            "field_id": f"record.group_code.{code}",
            "format": fmt["format"],
            "anchor": f"记录头组码 {code}",
            "value_kind": "the next line after this code",
            "locator": {"kind": "record_sequence", "anchor": str(code),
                        "regex": fmt.get("record_header_rx")},
            "source_path": [],
            "controls": [],
            "confidence": "unknown",
        })

    fault = {"file": (ctx.get("fault_file") or "").split("/")[-1],
             "line": ctx.get("fault_line"), "function": ctx.get("fault_fn")}
    chain = evidence_chain(harness, reachable, parsers, sinks, fault, src_cache)

    # 四条判据
    c1 = fmt["format"] in ("line_record", "binary_record", "raw_bytes")
    c2 = bool(fields) and all(f.get("locator") for f in fields)
    c3 = all(s["status"] in ("complete",) for s in chain[:5])
    c4 = not any(s["status"] == "unknown" for s in chain[:5])
    complete = bool(c1 and c2 and c3 and c4)

    unknowns = []
    for s in chain:
        if s["status"] != "complete":
            unknowns.append({"area": f"evidence_chain.step{s['step']}",
                             "question": s["question"], "status": s["status"],
                             "note": s.get("note") or ""})
    if not parsers:
        unknowns.append({"area": "parsers", "question": "未识别到解析输入的函数", "status": "unknown"})

    surface = {
        "schema_version": "stage5.target_surface.v1",
        "target": {"osv_id": args.osv, "project": ctx.get("project"),
                   "commit": ctx.get("commit_used") or ctx.get("pin_commit"),
                   "harness": ctx.get("fuzz_target"),
                   "crash_type": ctx.get("crash_type"),
                   "fault_function": ctx.get("fault_fn"),
                   "fault_file": (ctx.get("fault_file") or "").split("/")[-1],
                   "fault_line": ctx.get("fault_line"),
                   "entry_symbol": harness["entry_symbol"],
                   "input_parameter": harness["input_parameter"],
                   "input_length_parameter": harness["input_length_parameter"]},
        "call_surface": {
            "direct_calls": sorted(direct_callees(edges, ENTRY)),
            "reachable_functions": [f["name"] for f in reachable],
            "reachable_files": sorted({f["file"] for f in reachable}),
            "depth": wl["_meta"]["depth"],
            "source": "joern_cpg",
        },
        "input_format": fmt,
        "parsers": parsers,
        "fields": fields,
        "conditions": [],
        "sinks": sinks,
        "evidence_chain": chain,
        "unknowns": unknowns,
        "validation": {
            "fixed_commit": bool(surface_commit_ok(ctx)),
            "source_files_present": all(os.path.isfile(os.path.join(root, f)) for f in
                                        {x["file"] for x in reachable}),
            "harness_present": bool(hsrc),
            "cpg_present": True,
            "criteria": {"format_known": c1, "locator_present": c2,
                         "chain_all_complete": c3, "no_unknown_hop": c4},
            "field_mapping_complete": complete,
        },
    }

    if args.selftest or args.dry_run:
        print(f"=== {args.osv} target surface 自检 ===")
        for s in chain:
            print(f"  step{s['step']} [{s['status']:<8}] {s['question']}")
            for e in s["evidence"][:2]:
                print(f"           {e}")
        print(f"\n  判据: {surface['validation']['criteria']}")
        print(f"  field_mapping_complete = {complete}")
        if args.selftest:
            return

    p = os.path.join(S5, "v2", "target_surface.json")
    os.makedirs(os.path.dirname(p), exist_ok=True)
    json.dump(surface, open(p, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(f"\n  写出 {p}")
    print(f"  格式={fmt['format']}  解析器候选={len(parsers)}  sink 函数={len(sinks)}")
    print(f"  字段候选={len(fields)}（组码 {len(fmt.get('group_codes_seen', []))} 个）")
    print(f"  field_mapping_complete = {complete}  （判据 {surface['validation']['criteria']}）")
    print(f"  unknowns = {len(unknowns)} 条")


def surface_commit_ok(ctx):
    c = ctx.get("commit_used") or ctx.get("pin_commit")
    return bool(c) and len(str(c)) >= 7


if __name__ == "__main__":
    main()

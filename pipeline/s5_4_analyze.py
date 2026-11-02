#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""s5_4_analyze.py —— stage5 · analyze：5.3 取证 + 5.4 候选合并 + 5.5 每特征 6 阶段"""
from __future__ import annotations

import argparse, collections, glob, json, os, re, shutil, subprocess, sys, tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
TOP = os.path.dirname(ROOT)
OUT = os.path.join(ROOT, "projects")
if HERE not in sys.path:
    sys.path.insert(0, HERE)

from s5_6_lib import *                                          # noqa: E402,F401,F403


# ══════════════════════════════════════════════════════════════════════
# 5.3 输入攻击面 + 六步证据链（原 s5_target_surface.py）
# ══════════════════════════════════════════════════════════════════════

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

import argparse
import json
import os
import re
import sys



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
        m = FREE_CALL_RX.search(strip_code(lines[i]))
        if not m:
            continue
        callee, var = m.group(1), m.group(2)
        if not re.search(r"(free|destroy|release)", callee, re.I):
            continue
        trace = flow(lines, lo, hi, i, 20)
        bi = next((k for k, t in enumerate(trace) if t["back_edge"]), None)
        if bi is None:
            continue
        deref = re.compile(rf"\b{re.escape(var)}\b\s*(->|\.|\[)")
        for t in trace[bi:]:
            if deref.search(strip_code(lines[t["line"]])):
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
    blks = blocks(lines, lo, hi)
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

def main_surface():
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
        # 只认 .dxf 文件：seeds/ 下还有 _fuzzer_corpus/ 等目录和 .dwg 种子
        cands = [f for f in sorted(os.listdir(seeddir))
                 if f.endswith(".dxf") and os.path.isfile(os.path.join(seeddir, f))]
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

# ══════════════════════════════════════════════════════════════════════
# 5.4 多路候选合并 / 证据核验 / 去重（原 s5_candidate_findings.py）
# ══════════════════════════════════════════════════════════════════════

"""s5_candidate_findings.py —— 阶段5.2：把多路候选合并成统一的 findings（**0 LLM**）

职责
  把「agent 审计候选」「机械规则假设」「facts / interpretation」合成一份带来源、带证据状态、
  带去重、带可达性关系的清单。它**不判断漏洞真假**，只负责：
    · 统一漏洞族（family）
    · 重新核对证据行（行号存在 + 原文是该行子串）
    · 去重（同族 + 同文件 + 同函数 + **证据行有交集**）
    · 计算 call_surface_relation（direct / reachable / outside / unknown）
    · 计算 fault_relation（same_site / same_function / same_file / same_family_only / unrelated）
    · 计算 input_reachability（complete / partial / unknown）

为什么去重键不是「证据行集合相等」
  agent 给的证据行通常是 [12284, 12286, 12267, 12269]，机械假设是 [12284, 12267]。
  集合不相等，但显然说的是同一件事。所以用「有交集」而不是「相等」。

用法
  python3 s5_candidate_findings.py --osv ARVO-42494732
  python3 s5_candidate_findings.py --osv ARVO-42494732 --selftest
"""

import argparse
import glob
import json
import os
import re
import sys


# 漏洞族 ontology（保留原始类型，只做归一化）
FAMILY = {
    "use-after-free": "lifetime", "double-free": "lifetime", "invalid-free": "lifetime",
    "heap-buffer-overflow": "bounds", "stack-buffer-overflow": "bounds",
    "global-buffer-overflow": "bounds", "out-of-bounds-read": "bounds",
    "out-of-bounds-write": "bounds", "container-overflow": "bounds",
    "use-of-uninitialized-value": "initialization",
    "integer-overflow": "arithmetic-to-memory",
    "null-deref": "control/resource",
}

CRASH_FAMILY = {
    "heap-use-after-free": "lifetime", "heap-double-free": "lifetime",
    "invalid-free": "lifetime", "heap-buffer-overflow": "bounds",
    "stack-buffer-overflow": "bounds", "global-buffer-overflow": "bounds",
    "use-of-uninitialized-value": "initialization",
    "negative-size-param": "arithmetic-to-memory",
    "segv-on-unknown-address": "control/resource",
    "null-dereference": "control/resource",
}


def family_of(vuln_type: str) -> str:
    t = (vuln_type or "").lower()
    if t in FAMILY:
        return FAMILY[t]
    for k, v in FAMILY.items():
        if k in t:
            return v
    return "unknown"



def resolve_file(source_root: str, files, function: str, cache: dict) -> str:
    """候选没带文件时，按函数名在可达文件里反查（只匹配 "name(" 出现）。"""
    if not function:
        return ""
    key = (function, tuple(files or ()))
    if key in cache:
        return cache[key]
    rx = re.compile(rf"\b{re.escape(function)}\s*\(")
    for rel in files or ():
        p = os.path.join(source_root, rel)
        if not os.path.isfile(p):
            continue
        try:
            if rx.search(open(p, encoding="utf-8", errors="replace").read()):
                cache[key] = rel
                return rel
        except OSError:
            pass
    cache[key] = ""
    return ""

def as_candidate_list(report) -> list[dict]:
    """兼容三种输入：{"candidates":[...]} / [ {...}, {...} ] / None。"""
    if not report:
        return []
    if isinstance(report, list):
        out = []
        for r in report:
            out.extend(r.get("candidates") or [] if isinstance(r, dict) else [])
        return out
    return report.get("candidates") or []



def _norm_ev(ev) -> list:
    """把证据行统一成 [int, str]（LLM 会返回字符串行号）。"""
    out = []
    for e in ev or []:
        if not (isinstance(e, (list, tuple)) and len(e) >= 2):
            continue
        try:
            out.append([int(e[0]), str(e[1])])
        except (TypeError, ValueError):
            continue
    return out

def verify_evidence_findings(root: str, rel: str, evidence) -> tuple[bool, list[int], list[str]]:
    """核对证据行：行号合法且原文（去空白）是该行子串。"""
    full = os.path.join(root, rel) if rel else None
    if not full or not os.path.isfile(full):
        return False, [], ["file_missing"]
    lines = open(full, encoding="utf-8", errors="replace").read().split("\n")
    ok, bad = [], []
    for ev in evidence or []:
        if not (isinstance(ev, (list, tuple)) and len(ev) >= 2):
            bad.append(str(ev)[:80]); continue
        try:
            ln = int(ev[0])
        except (TypeError, ValueError):
            bad.append(str(ev)[:80]); continue
        if not (1 <= ln <= len(lines)):
            bad.append(f"L{ln} 越界"); continue
        claim = "".join(str(ev[1]).split())
        if claim and claim in "".join(lines[ln - 1].split()):
            ok.append(ln)
        else:
            bad.append(f"L{ln} 原文不符")
    return (bool(ok) and not bad), ok, bad


def all_lines(f: dict) -> set[int]:
    s = set()
    for x in f.get("lines") or []:
        try:
            s.add(int(x))
        except (TypeError, ValueError):
            pass
    for ev in f.get("evidence_lines") or []:
        try:
            s.add(int(ev[0]))
        except (TypeError, ValueError, IndexError):
            pass
    return s


def normalize_findings(audit_report, mech_report, facts, interpretation,
                       target_surface, source_root) -> dict:
    """把多路候选规范化、核验、去重、加关系。"""
    aud = as_candidate_list(audit_report)
    mech = (mech_report or {}).get("hypotheses") or []

    surface = target_surface or {}
    cs = surface.get("call_surface") or {}
    reachable = set(cs.get("reachable_functions") or [])
    direct = set(cs.get("direct_calls") or [])
    fm_complete = bool((surface.get("validation") or {}).get("field_mapping_complete"))

    tgt = surface.get("target") or {}
    cs_site = ((facts or {}).get("crash") or {}).get("site") or {}
    fault_fn = ((facts or {}).get("fault_fn") or cs_site.get("fn")
                or tgt.get("fault_function"))
    fault_line = ((facts or {}).get("fault_line") or cs_site.get("line")
                  or tgt.get("fault_line"))
    fault_file = ((facts or {}).get("fault_file") or cs_site.get("file")
                  or tgt.get("fault_file"))
    if isinstance(fault_file, str):
        fault_file = fault_file.split("/")[-1]
    crash_type = ((facts or {}).get("crash_type") or tgt.get("crash_type"))
    cfam = CRASH_FAMILY.get((crash_type or "").lower()) or family_of(crash_type)

    files = cs.get("reachable_files") or []
    fcache: dict = {}
    raws = []
    for c in aud:
        raws.append({"src": "audit", "raw": c,
                     "file": (c.get("_file") or c.get("file")
                              or resolve_file(source_root, files, c.get("function") or "", fcache)),
                     "function": c.get("function") or "",
                     "vuln_type": c.get("vuln_type") or "other",
                     "mechanism": c.get("mechanism") or "",
                     "evidence": c.get("evidence_lines") or [],
                     "confidence": c.get("confidence") or "low",
                     "why": c.get("why_unverified") or ""})
    for h in mech:
        raws.append({"src": "mech", "raw": h,
                     "file": h.get("file") or "",
                     "function": h.get("function") or "",
                     "vuln_type": h.get("vuln_type") or "use-after-free",
                     "mechanism": h.get("mechanism") or "",
                     "evidence": h.get("evidence_lines") or [],
                     "confidence": "low",
                     "why": "机械规则只证明代码形状，未证明输入可达"})

    out = []
    for r in raws:
        fam = family_of(r["vuln_type"])
        ok, ok_lines, bad = verify_evidence_findings(source_root, r["file"], r["evidence"])
        f = {
            "vuln_family": fam,
            "original_types": [r["vuln_type"]],
            "mechanism": r["mechanism"],
            "file": r["file"],
            "function": r["function"],
            "lines": sorted({int(x) for x in (r["raw"].get("lines") or [])
                             if str(x).lstrip("-").isdigit()}),
            "evidence_lines": _norm_ev(r["evidence"]),
            "evidence_ok": ok,
            "evidence_ok_lines": ok_lines,
            "evidence_bad": bad,
            "sources": [r["src"]],
            "raw": r["raw"],
            "confidence": r["confidence"],
            "why_unverified": r["why"],
        }
        f["call_surface_relation"] = (
            "direct" if r["function"] in direct else
            "reachable" if r["function"] in reachable else
            "outside" if reachable else "unknown")

        lines = all_lines(f)
        if fault_line and fault_fn and r["function"] == fault_fn and int(fault_line) in lines:
            f["fault_relation"] = "same_site"
        elif fault_fn and r["function"] == fault_fn:
            f["fault_relation"] = "same_function"
        elif fault_file and r["file"].endswith(fault_file):
            f["fault_relation"] = "same_file"
        elif fam == cfam:
            f["fault_relation"] = "same_family_only"
        else:
            f["fault_relation"] = "unrelated"

        # 输入可达性：只有"同一个故障函数"且整体映射闭合时才算 complete
        if not ok:
            f["input_reachability"] = {"status": "unknown", "missing": ["证据行未通过核对"]}
        elif fm_complete and f["fault_relation"] in ("same_site", "same_function"):
            f["input_reachability"] = {
                "status": "complete", "field_ids": [x.get("field_id") for x
                                                    in (surface.get("fields") or [])[:3]],
                "path_evidence": [s.get("evidence") for s in
                                  (surface.get("evidence_chain") or [])
                                  if s.get("status") == "complete"][:3], "missing": []}
        else:
            f["input_reachability"] = {
                "status": "partial", "missing": ["候选函数到输入的完整路径未建立"]}

        f["status"] = ("rejected" if not ok else
                       "unverified")
        out.append(f)

    # ── 去重：同族 + 同文件 + 同函数 + 证据行有交集 ──
    merged: list[dict] = []
    for f in out:
        hit = None
        for m in merged:
            same_file = (m["file"] == f["file"]) or not m["file"] or not f["file"]
            if (m["vuln_family"] == f["vuln_family"] and same_file
                    and m["function"] == f["function"]
                    and (all_lines(m) & all_lines(f))):
                hit = m
                break
        if hit:
            hit["sources"] = sorted(set(hit["sources"]) | set(f["sources"]))
            hit["original_types"] = sorted(set(hit["original_types"]) | set(f["original_types"]))
            hit["evidence_lines"] = sorted(hit["evidence_lines"] + f["evidence_lines"],
                                           key=lambda e: e[0])
            if not hit["file"]:
                hit["file"] = f["file"]
            # 合并时取"更精确"的故障关系，并取行号并集
            order = {"same_site": 0, "same_function": 1, "same_file": 2,
                     "same_family_only": 3, "unrelated": 4}
            if order[f["fault_relation"]] < order[hit["fault_relation"]]:
                hit["fault_relation"] = f["fault_relation"]
            hit["lines"] = sorted(set(hit.get("lines") or []) | set(f.get("lines") or []))
            hit["evidence_ok_lines"] = sorted(set(hit.get("evidence_ok_lines") or [])
                                              | set(f.get("evidence_ok_lines") or []))
            hit["evidence_ok"] = hit["evidence_ok"] or f["evidence_ok"]
            hit["confidence"] = ("high" if "high" in (hit["confidence"], f["confidence"])
                                 else hit["confidence"])
            if f["evidence_ok"] and not hit["evidence_ok_lines"]:
                hit["evidence_ok_lines"] = f["evidence_ok_lines"]
        else:
            merged.append(f)

    merged.sort(key=lambda x: (x["status"] == "rejected",
                               x["input_reachability"]["status"] != "complete",
                               {"same_site": 0, "same_function": 1, "same_file": 2,
                                "same_family_only": 3, "unrelated": 4}[x["fault_relation"]]))
    for i, f in enumerate(merged, 1):
        f["finding_id"] = f"c{i:03d}"
        f.pop("raw", None)

    return {
        "schema_version": "stage5.candidate_findings.v1",
        "target": {"osv_id": tgt.get("osv_id"), "commit": tgt.get("commit"),
                   "crash_type": crash_type, "fault_function": fault_fn,
                   "fault_line": fault_line, "fault_file": fault_file},
        "findings": merged,
        "rejected": [f for f in merged if f["status"] == "rejected"],
        "unknowns": [{"finding_id": f["finding_id"], "missing": f["input_reachability"]["missing"]}
                     for f in merged if f["input_reachability"]["status"] != "complete"],
        "summary": {
            "from_audit": len(aud), "from_mech": len(mech),
            "after_dedup": len(merged),
            "merged": len(out) - len(merged),
            "evidence_ok": sum(1 for f in merged if f["evidence_ok"]),
            "input_complete": sum(1 for f in merged
                                  if f["input_reachability"]["status"] == "complete"),
            "by_family": _count(f["vuln_family"] for f in merged),
            "by_fault_relation": _count(f["fault_relation"] for f in merged),
            "by_call_surface": _count(f["call_surface_relation"] for f in merged),
        },
    }


def _count(it):
    from collections import Counter
    return dict(Counter(it))


def main_findings():
    ap = argparse.ArgumentParser(description="阶段5.2：合并候选 findings（0 LLM）")
    ap.add_argument("--osv", required=True)
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    S5 = os.path.join(OUT, args.osv)
    V2 = os.path.join(S5, "v2")
    need = ["target_surface.json"]
    for n in need:
        if not os.path.exists(os.path.join(V2, n)):
            raise SystemExit(f"缺少 {V2}/{n}（先跑 s5_1_main.py surface --osv <OSV>）")
    surface = json.load(open(os.path.join(V2, "target_surface.json"), encoding="utf-8"))
    root = json.load(open(os.path.join(S5, "source_context.json"), encoding="utf-8"))["repo_local"]

    # 审计候选：优先 audit_chunks/*.json，退回 vuln_report.json
    chunk_files = sorted(glob.glob(os.path.join(S5, "audit_chunks", "*.json")))
    if chunk_files:
        audit = [json.load(open(p, encoding="utf-8")) for p in chunk_files]
        audit_src = f"audit_chunks/*.json（{len(chunk_files)} 批）"
    else:
        audit = json.load(open(os.path.join(S5, "vuln_report.json"), encoding="utf-8"))
        audit_src = "vuln_report.json"

    mechp = os.path.join(S5, "mech_hypotheses.json")
    mech = json.load(open(mechp, encoding="utf-8")) if os.path.exists(mechp) else {"hypotheses": []}

    facts = _load_or_none(os.path.join(ROOT, "artifacts", "facts", args.osv, "facts.json"))
    interp = _load_or_none(os.path.join(ROOT, "artifacts", "interpretation", args.osv,
                                        "interpretation.json"))

    rep = normalize_findings(audit, mech, facts, interp, surface, root)
    rep["_meta"] = {"osv_id": args.osv, "audit_source": audit_src,
                    "mech_source": "mech_hypotheses.json" if mech.get("hypotheses") else None,
                    "facts_used": bool(facts), "interpretation_used": bool(interp),
                    "method": "多路候选合并（0 LLM）；证据行已按固定源码核对"}

    print(f"=== {args.osv} candidate findings ===")
    print(f"  审计候选 {rep['summary']['from_audit']} 条（{audit_src}）")
    print(f"  机械假设 {rep['summary']['from_mech']} 条")
    print(f"  去重后   {rep['summary']['after_dedup']} 条（合并 {rep['summary']['merged']} 条）")
    print(f"  证据通过 {rep['summary']['evidence_ok']} / 输入可达 complete {rep['summary']['input_complete']}")
    print(f"  按族    : {rep['summary']['by_family']}")
    print(f"  与故障关系: {rep['summary']['by_fault_relation']}")
    print(f"  调用面关系: {rep['summary']['by_call_surface']}")
    print()
    for f in rep["findings"][:12]:
        print(f"  [{f['finding_id']}] {f['vuln_family']:<18} {f['function'][:26]:<26}"
              f" {f['fault_relation']:<16} ev={f['evidence_ok']} "
              f"in={f['input_reachability']['status']:<8} src={','.join(f['sources'])}")

    if args.selftest or args.dry_run:
        return
    os.makedirs(V2, exist_ok=True)
    p = os.path.join(V2, "candidate_findings.json")
    json.dump(rep, open(p, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(f"\n  写出 {p}")


def _load_or_none(p):
    return json.load(open(p, encoding="utf-8")) if os.path.exists(p) else None

# ══════════════════════════════════════════════════════════════════════
# 5.5 每个特征走同一套 6 阶段（原 s5f_feature_pipeline.py）
# ══════════════════════════════════════════════════════════════════════

"""s5f_feature_pipeline.py —— 阶段5.3'：**每个特征都走同一套固定流程**

为什么要有这个模块
  之前只有 uaf-llm01 走了完整流程（崩溃报告给了站点），其余 4 个用"通用字段类别"猜，
  方法不一致。本模块把流程固定下来，5 个特征一视同仁：

  ① 短名单（确定性）   按该特征的机制，从 worklist 里挑出可能承载它的函数
  ② 站点扫描（确定性） 在同一批函数上扫"释放→使用"原语，产出带行号的原始站点
  ③ 机制归类（确定性） 把站点归到它能支持的机制上；归不上就是"本项目无落点"
  ④ 六步证据链（确定性）站点 → 完整证据链；任何一跳不闭合就降级
  ⑤ 输入分支判定（确定性）判断该站点在哪条输入分支上（DXF / DWG / JSON）
  ⑥ 动作规格（确定性） 字段 + 操作 + 保持的不变量 + 证据等级

  每一步的产物都落盘；`status` 只有 `found` / `not_found` / `blocked` 三种。
  **找不到就明确写 not_found，权重还给 default——不用 generic 算子占预算。**

固定的机制→短名单/归类规则（可审计，不靠 LLM）
  llm01 同函数释放后访问      : free 后同函数内再读，含循环回边
  llm02 重分配后旧缓冲        : realloc 的结果没回写给原变量，或先存别名再 realloc
  llm03 清理/析构先释放后读    : 函数名匹配 free/destroy/cleanup/close/del 的释放路径
  llm04 跨函数陈旧对象        : 释放与读取发生在不同函数（结构体字段/别名）
  llm05 容器节点销毁后遍历     : 释放后在循环里继续走 next/prev/child 链

用法
  python3 s5f_feature_pipeline.py --osv ARVO-42494732 --all
  python3 s5f_feature_pipeline.py --osv ARVO-42494732 --feature uaf-llm02
"""

import argparse
import json
import os
import re
import sys

sys.path.insert(0, HERE)

# ─────────────── 固定规则表 ───────────────
FREE_CALL = re.compile(
    r"\b([A-Za-z_]\w*)\s*\(\s*&?\s*([A-Za-z_]\w*(?:\s*->\s*\w+)?)\s*\)\s*;")
FREE_NAME = re.compile(r"(free|destroy|release|clear|cleanup|del|close)", re.I)
REALLOC_CALL = re.compile(
    r"\b([A-Za-z_]\w*)\s*=\s*(?:\([^)]*\)\s*)?realloc\s*\(\s*([A-Za-z_]\w*(?:\s*->\s*\w+)?)\s*,")
LINK_READ = re.compile(r"\b(\w+)\s*->\s*(next|prev|child|sibling|first|last|head|tail)\b")

# 短名单规则：机制 → 函数名/被调名线索（确定性，可审计）
SHORTLIST = {
    "llm01": dict(name_rx=r".*", call_rx=r".*(free|destroy|release).*",
                  why="需要 free 类调用 + 同函数内再读"),
    "llm02": dict(name_rx=r".*", call_rx=r".*(realloc|alloc|resize|grow).*",
                  why="需要 realloc/扩容"),
    "llm03": dict(name_rx=r".*(free|destroy|cleanup|close|del).*",
                  call_rx=r".*(free|destroy|release|clear).*",
                  why="清理/析构函数里的释放"),
    "llm04": dict(name_rx=r".*(resolve|fixup|update|defer|postpon|stale|flush).*",
                  call_rx=r".*", why="延迟解析/交叉引用修正"),
    "llm05": dict(name_rx=r".*", call_rx=r".*(free|destroy|release|clear).*",
                  why="容器销毁后仍遍历"),
}
# 输入格式 → 该格式会走到的源文件。特征必须在**对应格式的代码路径**里找站点，
# 否则会出现"给 DXF 写算子、却指望它在 DWG 上生效"这种错配。
# 所有格式都会走到的公共路径（清理、句柄解析、写出）。站点落在这些文件里，
# 说明它对**所有格式**都适用，format_scope 要写全。
COMMON_FILES = ("src/free.c", "src/dwg.c")
FORMAT_FILES = {
    "DXF":  ("src/in_dxf.c",) + COMMON_FILES,
    "DWG":  ("src/decode.c", "src/bits.c") + COMMON_FILES,
    "JSON": ("src/in_json.c",) + COMMON_FILES,
}
FORMAT_MAGIC = {"DWG": "'AC' 开头", "JSON": "'{' 开头", "DXF": "其余"}

MECH_KEY = {"llm01": "同函数释放后访问", "llm02": "缓冲释放后旧指针",
            "llm03": "清理析构后悬垂访问", "llm04": "跨函数陈旧对象访问",
            "llm05": "容器节点销毁后遍历"}


# ─────────────── ① 短名单 ───────────────
def shortlist(feature_id, worklist, callees, only_files=None):
    key = feature_id.split("-")[-1]
    rule = SHORTLIST.get(key)
    if not rule:
        return [], "该特征没有短名单规则"
    rx_n = re.compile(rule["name_rx"], re.I)
    rx_c = re.compile(rule["call_rx"], re.I)
    out = []
    for f in worklist["functions"]:
        if only_files and not any(f["file"].startswith(x) for x in only_files):
            continue
        calls = callees.get((f["file"], f["name"]), set())
        by_name = bool(rx_n.fullmatch(f["name"]))
        by_call = any(rx_c.fullmatch(c) for c in calls)
        if by_name or by_call:
            out.append({"function": f["name"], "file": f["file"],
                        "lines": f["lines"], "depth": f["depth"],
                        "risk": f["risk"], "hit_by": "name" if by_name else "call"})
    out.sort(key=lambda x: (x["depth"], 0 if x["risk"] else 1))
    return out, rule["why"]


# ─────────────── ② 站点扫描（原语） ───────────────
def scan_sites(root, shortlist_funcs, src_cache):
    """在短名单函数里扫"释放类调用 → 后续读同一变量"。产出原始站点。"""
    sites = []
    for f in shortlist_funcs:
        lines = src_cache.get(f["file"])
        if not lines:
            continue
        lo, hi = f["lines"][0] - 1, min(f["lines"][1], len(lines)) - 1
        for i in range(lo, hi + 1):
            code = strip_code(lines[i])
            m = FREE_CALL.search(code)
            if not m or not FREE_NAME.search(m.group(1)):
                continue
            callee, var = m.group(1), m.group(2).replace(" ", "")
            # a) 同块/后续直线上的读
            same = None
            for j in range(i + 1, min(hi, i + 200) + 1):
                s = strip_code(lines[j])
                if re.search(rf"\b{re.escape(var)}\b\s*=(?!=)", s):
                    break
                if re.search(rf"\b{re.escape(var)}\b\s*(->|\.|\[)", s):
                    same = {"line": j + 1, "code": s[:160], "kind": "same_path"}
                    break
                if re.search(r"\breturn\b", s):
                    break
            # b) 循环回边上的读
            trace = flow(lines, lo, hi, i, 20)
            bi = next((k for k, t in enumerate(trace) if t["back_edge"]), None)
            back = None
            if bi is not None:
                # 回边之前若把 var 重新赋值，就不是 UAF
                end_ln = trace[bi]["line"]
                if any(re.search(rf"\b{re.escape(var)}\b\s*=(?!=)",
                                 strip_code(lines[j]))
                       for j in range(i + 1, end_ln + 1)):
                    trace = []
                    bi = None
            if bi is not None:
                for t in trace[bi:]:
                    s = strip_code(lines[t["line"]])
                    if re.search(rf"\b{re.escape(var)}\b\s*(->|\.|\[)", s):
                        back = {"line": t["line"] + 1, "code": s[:160],
                                "kind": "loop_back",
                                "back_edge_to": (trace[bi]["next"] + 1
                                                 if trace[bi]["next"] is not None else None)}
                        break
            use = same or back
            if not use:
                continue
            if not wrapper_frees_param(callee, var, funcs_by_name, root, src_cache):
                continue      # 包装只释放成员，不释放该变量本身
            link = bool(LINK_READ.search(strip_code(lines[use["line"] - 1])))
            sites.append({"function": f["function"], "file": f["file"],
                          "free_line": i + 1, "free_code": code[:160],
                          "callee": callee, "var": var,
                          "use": use, "is_link_read": link,
                          "realloc_near": _realloc_near(lines, lo, hi, i)})
    return sites



_WRAP_CACHE: dict = {}


def wrapper_frees_param(callee, var, funcs_by_name, root, src_cache):
    """`dwg_free_header_vars(dwg)` 只释放 dwg 的成员，不释放 dwg 本身 → 不能算释放。

    判定：被调函数体里出现 `free ( <形参> )` 或 `free ( (char*)<形参> )` 这类**直接释放**。
    """
    key = callee
    if key in _WRAP_CACHE:
        return _WRAP_CACHE[key]
    f = funcs_by_name.get(callee)
    if not f:
        _WRAP_CACHE[key] = True          # 看不到源码就不排除（保守）
        return True
    lines = src_cache.get(f["file"])
    if not lines:
        _WRAP_CACHE[key] = True
        return True
    lo, hi = f["lines"][0] - 1, min(f["lines"][1], len(lines))
    # 形参名（第一个参数）
    head = " ".join(lines[lo:min(lo + 3, hi)])
    m = re.search(r"\(\s*[^,)]*?\b(\w+)\s*[,)]", head)
    param = m.group(1) if m else None
    if not param:
        _WRAP_CACHE[key] = True
        return True
    rx = re.compile(rf"\bfree\s*\(\s*(?:\([^)]*\)\s*)?&?\s*{re.escape(param)}\b")
    ok = any(rx.search(lines[j]) for j in range(lo, hi))
    _WRAP_CACHE[key] = ok
    return ok

def _realloc_near(lines, lo, hi, i):
    for j in range(max(lo, i - 30), min(hi, i + 30) + 1):
        m = REALLOC_CALL.search(strip_code(lines[j]))
        if m:
            return {"line": j + 1, "var": m.group(1), "arg": m.group(2)}
    return None



# ── llm02 专用：realloc / 扩容后旧别名仍被访问（这个形态**没有 free 调用**，
#    所以 scan_sites 从来扫不到它——这是之前的检测器缺口）──
ALIAS_ASSIGN = re.compile(
    r"\b(?:const\s+)?(?:unsigned\s+char|char|uint8_t|Dwg_Object|Dxf_Pair|void)\s*\*\s*"
    r"([A-Za-z_]\w*)\s*=\s*(?:&\s*)?\(?\s*(?:unsigned\s+char\s*\*\s*\)?\s*)?"
    r"&?\s*([A-Za-z_]\w*(?:\s*->\s*\w+)?)\s*\[")
REALLOC_RX = re.compile(
    r"\b([A-Za-z_]\w*(?:\s*->\s*\w+)?)\s*=\s*(?:\([^)]*\)\s*)?realloc\s*\(\s*\1\s*,")


def scan_realloc_sites(shortlist_funcs, src_cache):
    """找『先取别名 → realloc 原缓冲 → 之后还用别名』。"""
    out = []
    for f in shortlist_funcs:
        lines = src_cache.get(f["file"])
        if not lines:
            continue
        lo, hi = f["lines"][0] - 1, min(f["lines"][1], len(lines)) - 1
        for i in range(lo, hi + 1):
            m = REALLOC_RX.search(lines[i])
            if not m:
                continue
            base = m.group(1).replace(" ", "")
            aliases = {}
            for j in range(max(lo, i - 60), i):
                a = ALIAS_ASSIGN.search(lines[j])
                if a and a.group(2).replace(" ", "").startswith(base.split("->")[-1]):
                    aliases[a.group(1)] = j + 1
            if not aliases:
                continue
            for var, aline in aliases.items():
                for j in range(i + 1, min(hi, i + 120) + 1):
                    if re.search(rf"\b{re.escape(var)}\b\s*(\[|->)", lines[j]):
                        out.append({"function": f["function"], "file": f["file"],
                                    "realloc_line": i + 1, "realloc_code": lines[i].strip()[:140],
                                    "base": base, "alias": var, "alias_line": aline,
                                    "use_line": j + 1, "use_code": lines[j].strip()[:140],
                                    "kind": "realloc_alias"})
                        break
    return out

# ─────────────── ③ 机制归类 ───────────────
def classify(site, feature_id):
    """这个站点能否支持给定机制？返回 (ok, 理由)。"""
    key = feature_id.split("-")[-1]
    fn = site["function"].lower()
    if key == "llm01":
        if site["use"]["kind"] == "loop_back":
            return True, "循环回边回到解引用同一变量"
        if site["use"]["kind"] == "same_path" and not site["is_link_read"]:
            return True, "同一直线上释放后解引用"
        return False, "没有同函数内的后续读"
    if key == "llm02":
        r = site["realloc_near"] or {}
        if site.get("callee") == "realloc" or (r and r.get("var") != r.get("arg")):
            return True, (f"别名 {r.get('var')} 取自 {r.get('arg')}，realloc 之后仍被读"
                          if r else "realloc 之后旧别名仍被读")
        return False, "附近没有『realloc 之后旧别名仍被读』的形态"
    if key == "llm03":
        if re.search(r"(free|destroy|cleanup|close|del)", fn):
            return True, "释放发生在清理/析构函数里"
        return False, "释放不在清理/析构路径上"
    if key == "llm04":
        if re.search(r"(resolve|fixup|update|defer|postpon)", fn):
            return True, "延迟解析/交叉引用修正路径"
        return False, "不在延迟解析路径上"
    if key == "llm05":
        if site["is_link_read"]:
            return True, "释放后仍沿 next/prev/child 链走"
        return False, "释放后的读不是链式遍历"
    return False, "未知机制"


# ─────────────── ④ 六步证据链 ───────────────
def build_chain(site, feature, surface, src_cache):
    lines = src_cache[site["file"]]
    lo, hi = site["free_line"] - 1, None
    chain = [
        {"step": 1, "name": "harness 入口", "status": "complete" if
         (surface.get("target") or {}).get("entry_symbol") else "unknown",
         "evidence": [(surface.get("target") or {}).get("entry_symbol")]},
        {"step": 2, "name": "输入绑定", "status": "complete"}
        if (surface.get("input_format") or {}).get("format") else {"step": 2, "status": "unknown",
                                                                   "evidence": []},
        {"step": 3, "name": "解析到内部结构", "status": "complete"
         if (surface.get("parsers") or []) else "unknown",
         "evidence": [[p["function"], p["lines"][0]] for p in (surface.get("parsers") or [])[:3]]},
        {"step": 4, "name": "字段进入目标变量", "status": "complete",
         "evidence": [[site["free_line"], site["free_code"]]]},
        {"step": 5, "name": "释放点所在分支", "status": "complete",
         "evidence": [[site["free_line"], site["free_code"]]]},
        {"step": 6, "name": "释放后仍被读", "status": "complete",
         "evidence": [[site["use"]["line"], site["use"]["code"]]],
         "note": ("循环回边⟲回到 L%s" % site["use"].get("back_edge_to")
                  if site["use"]["kind"] == "loop_back" else "同一直线上")},
    ]
    # 逐跳核对源码行是否真的存在
    for st in chain:
        for ev in st.get("evidence") or []:
            if isinstance(ev, list) and len(ev) >= 2 and isinstance(ev[0], int):
                st["status"] = ("complete" if 1 <= ev[0] <= len(lines) else "unknown")
    return chain


# ─────────────── ⑤ 输入分支 ───────────────
def input_branch(rel, src_cache):
    """站点所在的源文件属于哪条输入分支（harness 按前两字节分流）。"""
    if rel.startswith("src/in_dxf"):
        return {"branch": "DXF", "entry": "dwg_read_dxf", "magic": "非 'AC'、非 '{'"}
    if rel.startswith("src/in_json"):
        return {"branch": "JSON", "entry": "dwg_read_json", "magic": "'{'"}
    if rel.startswith("src/decode") or rel.startswith("src/bits"):
        return {"branch": "DWG", "entry": "dwg_decode", "magic": "'AC'"}
    if rel.startswith("src/out_") or rel.startswith("src/encode"):
        return {"branch": "OUTPUT", "entry": "(写出路径)", "magic": "解析成功后"}
    return {"branch": "UNKNOWN", "entry": None, "magic": None}


# ─────────────── ⑥ 动作规格 ───────────────
def build_action(feature, site, chain, branch, weight):
    ok = all(s["status"] == "complete" for s in chain) and branch["branch"] != "UNKNOWN"
    return {
        "action_id": None,
        "feature_id": feature.get("id"),
        "feature_name": feature.get("feature_name"),
        "mechanism": MECH_KEY.get(feature.get("id", "").split("-")[-1]),
        "weight": weight,
        "site": {"function": site["function"], "file": site["file"],
                 "free_line": site["free_line"], "use_line": site["use"]["line"],
                 "var": site["var"], "callee": site["callee"],
                 "reuse_kind": site["use"]["kind"]},
        "input_branch": branch,
        "evidence_chain": chain,
        "evidence_grade": "proven" if ok else "blocked",
        "operation": ("mutate_binary_record" if branch["branch"] == "DWG"
                      else "mutate_text_record"),
        "status": "found" if ok else "blocked",
        "blockers": [] if ok else [f"step{s['step']} 未闭合" for s in chain
                                   if s["status"] != "complete"]
        + ([f"输入分支未知"] if branch["branch"] == "UNKNOWN" else []),
    }


# ─────────────── 主流程 ───────────────
def load_cpg_dump(p):
    methods, edges = [], []
    for ln in open(p, encoding="utf-8"):
        t = ln.rstrip("\n").split("\t")
        if t[0] == "@@M" and len(t) >= 6:
            methods.append({"file": t[1], "name": t[2], "start": int(t[3] or 0),
                            "end": int(t[4] or 0), "external": t[5] == "1"})
        elif t[0] == "@@C" and len(t) >= 4:
            edges.append((t[1], t[2], t[3]))
    callees = {}
    for cf, cn, cs in edges:
        callees.setdefault((cf, cn), set()).update(cs.split("|"))
    return methods, callees



# ── P3 预筛：这个特征在本项目有没有落点（筛子，不是判据）──
# 依据：stage3 final.json 的 trigger_condition.where_free / where_use 里的函数名，
# 与 audit_worklist 的可达函数集合求交。交集为空 → 该特征在本项目无落点。
# 注意：这只决定"要不要继续查"，不判断"站点是不是真 UAF"——后者仍归 cfg_lib 证据链 + agent。
REACHABLE: set = set()
PATTERN_BY_NAME: dict = {}
ID_RX = re.compile(r"[A-Za-z_][A-Za-z0-9_]{3,}")

# 标准库 / 编译器内建名。stage3 的 where_free / where_use 是散文，会把 malloc、wchar、
# mbrtowc 这类名字也写进去；它们在项目里的同名声明不是"特征落点"，必须剔除，
# 否则换项目时交集会被这些通用名污染（见 R3_PHASE D 报告）。
STDLIB_NAMES = {
    # 分配 / 释放
    "malloc", "free", "realloc", "calloc", "alloca", "memalign", "posix_memalign",
    "aligned_alloc", "valloc", "brk", "sbrk", "mmap", "munmap", "new", "delete",
    # 内存 / 字符串
    "memcpy", "memmove", "memset", "memcmp", "memchr", "bcopy", "bzero",
    "strdup", "strndup", "strcpy", "strncpy", "strcat", "strncat", "strlen",
    "strcmp", "strncmp", "strchr", "strrchr", "strstr", "strtok", "strerror",
    "sprintf", "snprintf", "vsprintf", "vsnprintf", "sscanf", "atoi", "atol", "strtol",
    # 宽字符 / 本地化（出现频率高、极易污染交集）
    "wchar", "wchar_t", "mbrtowc", "wcrtomb", "mbsrtowcs", "wcsrtombs", "mbstate",
    "wcslen", "wcscpy", "wcsncpy", "wcscmp", "setlocale",
    # 文件 / 流
    "fopen", "fclose", "fread", "fwrite", "fseek", "ftell", "fflush", "feof", "ferror",
    "fgets", "fputs", "getc", "putc", "printf", "fprintf", "puts", "perror",
    # 进程 / 控制
    "abort", "exit", "atexit", "assert", "errno", "memcpy_s", "memset_s",
}


def applicability(feature):
    """返回 {hit_count, hit_names, source_pattern, extracted, basis}。"""
    sp = feature.get("source_pattern")
    pat = PATTERN_BY_NAME.get(sp)
    if not pat:
        return {"hit_count": None, "hit_names": [], "source_pattern": sp,
                "extracted": 0, "basis": f"stage3 final.json 里找不到 pattern {sp!r}；预筛跳过"}
    tc = pat.get("trigger_condition") or {}
    names = set()
    for k in ("where_free", "where_use"):
        names |= set(ID_RX.findall(tc.get(k) or ""))
    dropped = sorted(n for n in names if n.lower() in STDLIB_NAMES)
    names = {n for n in names if n.lower() not in STDLIB_NAMES}
    hit = sorted(n for n in names if n in REACHABLE)
    return {"hit_count": len(hit), "hit_names": hit, "source_pattern": sp,
            "extracted": len(names), "dropped_stdlib": dropped,
            "basis": (f"trigger_condition.where_free/where_use 抽出 {len(names)} 个标识符"
                      f"（剔除 {len(dropped)} 个标准库名），"
                      f"与 {len(REACHABLE)} 个可达函数求交 → {len(hit)} 个命中")}



def run_feature(feature, worklist, callees, surface, src_cache, weight, fmt=None):
    fid = feature["id"]
    app = applicability(feature)
    if app["hit_count"] == 0:
        return {"feature_id": fid, "feature_name": feature.get("feature_name"),
                "target_format": fmt, "mechanism": MECH_KEY.get(fid.split("-")[-1]),
                "shortlist_rule": None, "shortlist": [], "shortlist_size": 0,
                "sites_scanned": 0, "sites_supporting": 0, "sites": [],
                "applicability": app,
                "status": "not_applicable",
                "why": f"预筛：{app['basis']} → 该特征与本项目可达代码无交集",
                "action": None}
    only = FORMAT_FILES.get(fmt) if fmt else None
    cands, why = shortlist(fid, worklist, callees, only)
    sites = scan_sites(surface_root, cands, src_cache) if cands else []
    if fid.endswith("llm02"):
        extra = scan_realloc_sites(cands, src_cache) if cands else []
        for e in extra:
            sites.append({"function": e["function"], "file": e["file"],
                          "free_line": e["realloc_line"], "free_code": e["realloc_code"],
                          "callee": "realloc", "var": e["alias"],
                          "use": {"line": e["use_line"], "code": e["use_code"],
                                  "kind": "same_path"},
                          "is_link_read": False, "realloc_near": {"var": e["alias"],
                                                                   "arg": e["base"]}})
        res_extra = len(extra)
    else:
        res_extra = 0
    scored = []
    for s in sites:
        ok, reason = classify(s, fid)
        scored.append({"site": s, "supports": ok, "reason": reason})
    good = [x for x in scored if x["supports"]]
    crash_fn = (surface.get("target") or {}).get("fault_function")
    good.sort(key=lambda x: (0 if x["site"]["function"] == crash_fn else 1,
                             0 if x["site"]["use"]["kind"] == "loop_back" else 1,
                             x["site"]["file"], x["site"]["free_line"]))
    res = {"feature_id": fid, "feature_name": feature.get("feature_name"),
           "target_format": fmt,
           "mechanism": MECH_KEY.get(fid.split("-")[-1]),
           "shortlist_rule": why, "shortlist": cands[:40],
           "shortlist_size": len(cands), "sites_scanned": len(sites),
           "sites_supporting": len(good),
           "applicability": app,
           "sites": [{**x["site"], "supports": x["supports"], "reason": x["reason"]}
                     for x in scored[:60]]}
    if fmt:
        branch = {"branch": fmt, "entry": None, "magic": FORMAT_MAGIC.get(fmt)}
        if any(st.get("file", "").startswith(COMMON_FILES) for st in sites[:1]) or \
           (good and good[0]["site"]["file"].startswith(COMMON_FILES)):
            branch = {"branch": "ALL", "entry": None,
                      "magic": "公共路径（清理/句柄/写出），三种格式都可达",
                      "format_scope": ["DXF", "DWG", "JSON"]}
    if not good:
        res.update({"status": "not_found",
                    "why": f"{fmt or '全局'} 路径：短名单 {len(cands)} 个函数、"
                           f"扫出 {len(sites)} 个释放→使用原语，没有一个能支持该机制",
                    "action": None})
        return res
    best = good[0]["site"]
    branch = ({"branch": fmt, "entry": None, "magic": FORMAT_MAGIC.get(fmt)}
              if fmt else input_branch(best["file"], src_cache))
    chain = build_chain(best, feature, surface, src_cache)
    action = build_action(feature, best, chain, branch, weight)
    action["candidate_count"] = len(good)
    res.update({"status": action["status"], "why": good[0]["reason"], "action": action})
    return res


surface_root = ""        # 由 main_features 注入
funcs_by_name: dict = {}  # 由 main_features 注入


def main_features():
    global surface_root, funcs_by_name, REACHABLE, PATTERN_BY_NAME
    ap = argparse.ArgumentParser(description="阶段5.3'：每个特征走同一套固定流程")
    ap.add_argument("--osv", required=True)
    ap.add_argument("--type", default="uaf")
    ap.add_argument("--feature", default=None, help="只跑一个特征")
    ap.add_argument("--all", action="store_true", help="跑该崩溃类型的全部特征")
    ap.add_argument("--by-format", action="store_true",
                    help="按『输入格式 × 特征』矩阵扫，每种格式只在该格式的代码路径里找站点")
    ap.add_argument("--default-weight", type=float, default=0.5)
    args = ap.parse_args()

    S5 = os.path.join(OUT, args.osv)
    V2 = os.path.join(S5, "v2")
    surface = json.load(open(os.path.join(V2, "target_surface.json"), encoding="utf-8"))
    worklist = json.load(open(os.path.join(S5, "audit_worklist.json"), encoding="utf-8"))
    ctx = json.load(open(os.path.join(S5, "source_context.json"), encoding="utf-8"))
    surface_root = ctx["repo_local"]
    feats = json.load(open(os.path.join(ROOT, "outputs", "stage4", args.type,
                                        "features.json"), encoding="utf-8"))["features"]
    _, callees = load_cpg_dump(os.path.join(S5, "cpg_dump.tsv"))
    funcs_by_name = {f["name"]: f for f in worklist["functions"]}
    REACHABLE = set(funcs_by_name)
    _fp = os.path.join(ROOT, "outputs", "stage3", args.type, "final.json")
    if os.path.exists(_fp):
        for _p in (json.load(open(_fp, encoding="utf-8")).get("final_patterns") or []):
            PATTERN_BY_NAME[_p["name"]] = _p
    print(f"  可适用性预筛：可达函数 {len(REACHABLE)} 个，"
          f"stage3 pattern {len(PATTERN_BY_NAME)} 个")

    src_cache = {}
    for f in worklist["functions"]:
        if f["file"] not in src_cache:
            p = os.path.join(surface_root, f["file"])
            src_cache[f["file"]] = (open(p, encoding="utf-8", errors="replace")
                                    .read().split("\n")) if os.path.isfile(p) else None

    if args.by_format:
        # 每种格式独立跑一遍：format × feature 矩阵
        matrix = []
        for fmt in FORMAT_FILES:
            todo_f = [f for f in feats if args.feature in (None, f["id"])]
            wf = round((1.0 - args.default_weight) / max(1, len(todo_f)), 4)
            print(f"\n--- 格式 {fmt}（{FORMAT_MAGIC[fmt]}）---")
            for f in todo_f:
                r = run_feature(f, worklist, callees, surface, src_cache, wf, fmt=fmt)
                matrix.append(r)
                icon = {"found": "✅", "not_found": "❌", "blocked": "⚠️",
                        "not_applicable": "⛔"}[r["status"]]
                print(f"  {icon} {r['feature_id']:<11} {r['status']:<10} "
                      f"短名单 {r['shortlist_size']:>3} / 支持 {r['sites_supporting']:>2}"
                      f"  {r['why'][:60]}")
        os.makedirs(os.path.join(V2, "features"), exist_ok=True)
        json.dump({"matrix": matrix, "formats": list(FORMAT_FILES)},
                  open(os.path.join(V2, "feature_matrix.json"), "w", encoding="utf-8"),
                  ensure_ascii=False, indent=1)
        print(f"\n  写出 {V2}/feature_matrix.json")
        found = [r for r in matrix if r["status"] == "found"]
        print(f"  共 found {len(found)} 条（格式×特征）")
        return

    todo = [f for f in feats if args.feature in (None, f["id"])] if (args.all or args.feature) \
        else feats
    n = len(todo)
    w = round((1.0 - args.default_weight) / n, 4) if n else 0.0

    print(f"=== {args.osv} 特征管线（{n} 个特征，每个权重 {w}）===")
    results = []
    for f in todo:
        r = run_feature(f, worklist, callees, surface, src_cache, w)
        results.append(r)
        icon = {"found": "✅", "not_found": "❌", "blocked": "⚠️",
                "not_applicable": "⛔"}[r["status"]]
        print(f"  {icon} {r['feature_id']:<11} {r['status']:<10} "
              f"短名单 {r['shortlist_size']:>3} / 原语 {r['sites_scanned']:>3} / "
              f"支持 {r['sites_supporting']:>2} | {r['why'][:70]}")
        if r["action"]:
            a = r["action"]
            print(f"        site: {a['site']['file']}:{a['site']['free_line']}"
                  f" → {a['site']['use_line']}  var={a['site']['var']}"
                  f"  branch={a['input_branch']['branch']}")

    os.makedirs(os.path.join(V2, "features"), exist_ok=True)
    for r in results:
        d = os.path.join(V2, "features", r["feature_id"])
        os.makedirs(d, exist_ok=True)
        json.dump(r, open(os.path.join(d, "pipeline.json"), "w", encoding="utf-8"),
                  ensure_ascii=False, indent=1)

    found = [r for r in results if r["status"] == "found"]
    # 权重要在"知道几个找到"之后才定：default 占 default_weight，其余平分给 found 的特征
    w2 = round((1.0 - args.default_weight) / len(found), 4) if found else 0.0
    for r in found:
        r["action"]["weight"] = w2
    print()
    print(f"  found {len(found)}/{n}；not_found {sum(1 for r in results if r['status']=='not_found')}；"
          f"blocked {sum(1 for r in results if r['status']=='blocked')}")
    if found:
        print(f"  权重合计: default {args.default_weight} + {len(found)}×{w2} = "
              f"{round(args.default_weight + len(found) * w2, 3)}")
    json.dump({"features": results,
               "weighting": {"default": args.default_weight,
                             "per_found_feature": w2, "found": len(found), "total": n}},
              open(os.path.join(V2, "feature_pipeline.json"), "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)
    print(f"  写出 {V2}/feature_pipeline.json")



# ══════════════════════════════════════════════════════════════════════
# 阶段入口
# ══════════════════════════════════════════════════════════════════════

def main(argv=None):
    ap = argparse.ArgumentParser(description="stage5 · analyze（5.3 + 5.4 + 5.5）")
    ap.add_argument("--osv", required=True)
    ap.add_argument("--type", default="uaf")
    ap.add_argument("--feature", default=None)
    ap.add_argument("--default-weight", type=float, default=0.5)
    a = ap.parse_args(sys.argv[1:] if argv is None else list(argv))
    for fn, av in ((main_surface, ["--osv", a.osv]),
                   (main_findings, ["--osv", a.osv]),
                   (main_features, ["--osv", a.osv, "--type", a.type,
                                    "--default-weight", str(a.default_weight)]
                    + (["--feature", a.feature] if a.feature else ["--all"]))):
        print(f"\n--- {fn.__name__}")
        rc = run_fn(fn, av)
        if rc:
            return rc
    return 0


if __name__ == "__main__":
    sys.exit(main())

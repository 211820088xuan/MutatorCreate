#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""s5b_audit_agent.py —— 阶段5②：对 fuzz target 覆盖的源码做「静态漏洞发现」

三种运行方式
  批次模式（配合 s5a_scan_target.py 的 worklist）
    python3 s5b_audit_agent.py --osv ARVO-42494732 --chunk 26
    python3 s5b_audit_agent.py --osv ARVO-42494732 --all-chunks --workers 3
    python3 s5b_audit_agent.py --osv ARVO-42494732 --merge
  文件模式（调试）
    python3 s5b_audit_agent.py --osv ARVO-42494732 --files src/free.c

为什么要有批次
  `src/in_dxf.c` 492 KB，一次 agent 调用装不下（实测盲测只读 18.8% 就收工）。
  s5a 把文件按函数边界切成 ≤3 万字符的批次，每批一个 agent，
  并且**要求对批内每个函数给出裁决**，这样覆盖率可测。

产物
  <OSV>/audit_chunks/chunk_026.json   每批结果（含 verdicts + 覆盖率）
  <OSV>/vuln_report.json              --merge 后的合并报告
  <OSV>/audit_logs/*.jsonl            每轮工具调用日志
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
TOP = os.path.dirname(ROOT)
sys.path.insert(0, HERE)

from agent_runtime import (Agent, Tool, grep_tool, list_dir_tool,  # noqa: E402
                           read_file_tool)
import cfg_lib  # noqa: E402

OUT = os.path.join(ROOT, "projects")
FALLBACK_FILES = ["src/in_dxf.c", "src/decode.c", "src/bits.c", "src/free.c",
                  "src/out_dxf.c", "src/in_json.c", "src/classes.c"]

SYSTEM = """你是一名 C/C++ 内存安全审计员，正在为一个**已确认存在漏洞**的开源库做静态审计。

# 任务
在**指定的函数清单**里，找出「一个外部输入（fuzz target 的输入）可能触发的内存安全缺陷」。

# 硬性规则
1. **只读**：只能调用 read_file / grep / list_dir。
2. **必须逐个函数裁决**：清单里每个函数都要在 `verdicts` 里给
   `candidate`（有嫌疑）/ `clean`（看过没问题）/ `skipped`（没看，说明原因）。
   给 candidate/clean 前**必须真的 read_file 读过它的函数体**。
3. **不许猜行号**：候选必须给 `evidence_lines` = `[行号, 该行代码原文]`，
   原文必须是文件里逐字存在的子串（校验器会比对）。
4. **只报内存安全类**：use-after-free / double-free / invalid-free /
   heap·stack·global-buffer-overflow / out-of-bounds read·write /
   use-of-uninitialized-value / null-deref / 整数溢出导致越界。
   不报风格问题、资源泄漏、性能问题。
5. **必须能连到输入**：说明输入的哪个部分影响它。连不到的写 `not_input_reachable`。
6. 你不跑程序，每条候选都是**未验证**假设，`why_unverified` 写清缺什么证据。
7. 宁少不滥：0~5 条高质量候选好过 20 条噪声；没有候选是合法结论。
8. **效率**：先按清单顺序读完每个函数体再判断；跨文件查找最多 3 次；不要重复同一 grep。
10. **对每一处"调用释放类函数"必须走一遍三问**（答案写进 `candidates` 或 `verdicts[].reason`）：
    ① 释放的是不是**调用方变量经形参传入**？若是，调用方那个变量仍然悬垂
       （被调用函数里的 `p = NULL` 只影响形参）。
    ② 这之后，**调用方那个变量**有没有被重新赋值？没有 == 悬垂。
    ③ 之后（**包括循环回到开头重新判断条件**）有没有**解引用**它（`v->` / `v.` / `v[`）？
       **只判空（`if (v)` / `if (!v)`）不算解引用。**
    三问都成立 ⇒ 必须报 `candidate`，不许判 clean。
9. **必查的 C 陷阱（最容易漏的一类）**：
   形如 `void f(T *p) { ... free(p); p = NULL; }` 的释放包装函数，`p = NULL` 只置空**形参**，
   **调用方的变量仍然指向已释放内存**。所以判断"释放后有没有置空"时，必须检查
   **调用方那个变量**在释放之后、下一次解引用之前有没有被重新赋值——只看被调用函数里
   有没有 `p = NULL` 会漏判。
   同理：如果释放包装函数的参数是结构体成员（`dxf_free_pair (pair->x)`），
   要检查成员有没有被置空。

11. **每个"释放类调用"都必须先调 `flow` 再判断**。
    调 `flow(function, line)` 看这一行执行完之后控制流去哪。
    如果轨迹里出现 ⟲ 回边，并且回到了一个**会解引用同一变量**的行
    （`v->` / `v.` / `v[`），而中间**没有**对该变量赋值
    → 这是释放后使用，必须报 `candidate`。
    **禁止在没调过 flow 的情况下对"释放后是否安全"下结论。**
    在 `verdicts[].reason` 里写明你对哪几行调过 flow。

# 输出
调用 `finish` 提交 JSON，不要解释文字。
`mechanism` / `precondition` / `notes` / `why_unverified` / `verdicts[].reason` **一律用中文**。"""

VERDICT_SCHEMA = {
    "type": "array",
    "items": {"type": "object",
              "properties": {"function": {"type": "string"},
                             "verdict": {"type": "string",
                                         "enum": ["candidate", "clean", "skipped"]},
                             "reason": {"type": "string"}},
              "required": ["function", "verdict", "reason"]},
}

CAND_SCHEMA = {
    "type": "array",
    "items": {"type": "object",
              "properties": {
                  "vuln_type": {"type": "string", "enum": [
                      "use-after-free", "double-free", "invalid-free",
                      "heap-buffer-overflow", "stack-buffer-overflow",
                      "global-buffer-overflow", "out-of-bounds-read",
                      "out-of-bounds-write", "use-of-uninitialized-value",
                      "null-deref", "integer-overflow", "other"]},
                  "function": {"type": "string"},
                  "lines": {"type": "array", "items": {"type": "integer"}},
                  "mechanism": {"type": "string"},
                  "input_field": {"type": "string"},
                  "precondition": {"type": "array", "items": {"type": "string"}},
                  "evidence_lines": {"type": "array",
                                     "items": {"type": "array", "items": {"type": "string"}}},
                  "confidence": {"type": "string", "enum": ["high", "medium", "low"]},
                  "why_unverified": {"type": "string"}},
              "required": ["vuln_type", "function", "lines", "mechanism",
                           "evidence_lines", "confidence", "why_unverified"]},
}

FINISH_SCHEMA = {
    "type": "object",
    "properties": {
        "file": {"type": "string"},
        "verdicts": VERDICT_SCHEMA,
        "candidates": CAND_SCHEMA,
        "not_input_reachable": {"type": "array", "items": {"type": "object", "properties": {
            "function": {"type": "string"}, "why": {"type": "string"}}}},
        "notes": {"type": "array", "items": {"type": "string"}},
    },
    "required": ["file", "verdicts", "candidates"],
}

HEAD = """# 审计目标

- 项目：`{project}`
- 仓库（漏洞版 commit `{commit}`）：`{root}`
- fuzz target 入口：`{harness}`
- harness 直接调用的库函数：{apis}

# 参考：该库已知的崩溃类型分布（只用于排优先级，不要照抄结论）

{crash_hint}
"""

CHUNK_TASK = HEAD + """
# 本批次：chunk #{cid} —— 文件 `{file}`，行 {lo}-{hi}

**必须审计下面这 {n} 个函数**（都在 `{file}` 里）：

{fn_list}

# 开始
1. 按清单顺序，每个函数先 `read_file` 读完整函数体（别分段碎读）；
2. 判断有没有「释放后继续用 / 长度算错导致越界 / 下标未校验 / 未初始化」等；
3. 需要确认调用者或宏定义时最多跨文件查 3 次；
4. 对**每个函数**给出 verdict，有嫌疑的写进 `candidates`（带 `evidence_lines`），调用 `finish`。

你只有 {turns} 轮。10 轮内开始写结论，不要追调用链追到底。"""

FILE_TASK = HEAD + """
# 本次你负责的文件

`{file}`（共 {nlines} 行）

# 开始
1. `grep` 出 free / destroy / release / memcpy / malloc / calloc / realloc 的行；
2. 读这些行前后 30~60 行判断；
3. 跨文件查找最多 3 次；
4. 对看过的每个函数给出 verdict，填好 `evidence_lines`，调用 `finish`。

你只有 {turns} 轮。"""


def load_ctx(osv: str) -> dict:
    p = os.path.join(OUT, osv, "source_context.json")
    if not os.path.exists(p):
        raise SystemExit(f"缺少 {p}（先跑 s5_fetch_source.py {osv}）")
    return json.load(open(p, encoding="utf-8"))


def load_worklist(osv: str) -> dict:
    p = os.path.join(OUT, osv, "audit_worklist.json")
    if not os.path.exists(p):
        raise SystemExit(f"缺少 {p}（先跑 s5a_scan_target.py --osv {osv}）")
    return json.load(open(p, encoding="utf-8"))


def harness_apis(osv: str) -> list[str]:
    d = os.path.join(OUT, osv, "harness")
    names: set[str] = set()
    if os.path.isdir(d):
        for fn in os.listdir(d):
            if fn.endswith((".c", ".cc", ".cpp")):
                txt = open(os.path.join(d, fn), encoding="utf-8", errors="replace").read()
                names |= set(re.findall(r"\b((?:dwg|bit_chain|dxf)_[a-z0-9_]+)\s*\(", txt))
    return sorted(names)


def verify_evidence(root: str, cand: dict, rel: str) -> dict:
    """核对 evidence_lines：行号存在 + 代码原文是该行的子串（去空白）。"""
    full = os.path.join(root, rel)
    if not os.path.isfile(full):
        return {"evidence_ok": False, "evidence_ok_lines": [], "evidence_bad": ["file_missing"]}
    lines = open(full, encoding="utf-8", errors="replace").read().split("\n")
    ok, bad = [], []
    for ev in cand.get("evidence_lines") or []:
        if not (isinstance(ev, (list, tuple)) and len(ev) >= 2):
            bad.append(str(ev)[:80]); continue
        try:
            ln = int(ev[0])
        except (TypeError, ValueError):
            bad.append(str(ev)[:80]); continue
        if not (1 <= ln <= len(lines)):
            bad.append(f"L{ln} 越界"); continue
        if "".join(str(ev[1]).split()) and "".join(str(ev[1]).split()) in "".join(lines[ln - 1].split()):
            ok.append(ln)
        else:
            bad.append(f"L{ln} 原文不符")
    return {"evidence_ok": bool(ok) and not bad, "evidence_ok_lines": ok, "evidence_bad": bad}



def make_flow_tool(fn_ranges: dict[str, tuple[str, int, int]]) -> Tool:
    """`flow` 工具：从某一行按真实控制流单步走，回边会被标出来。

    fn_ranges: 函数名 -> (文件, 起始行, 结束行)，1-based
    """
    def run(a: dict, ag) -> str:
        fn = a.get("function")
        line = int(a["line"])
        steps = min(int(a.get("steps") or 8), 20)
        rel = start = end = None
        if fn and fn in fn_ranges:
            rel, start, end = fn_ranges[fn]
        else:
            rel = a.get("file"); start = a.get("start_line"); end = a.get("end_line")
        if not (rel and start and end):
            return ("[错误] 需要 function（本批次清单里的函数名），"
                    "或同时给 file + start_line + end_line")
        full = os.path.join(ag.root, rel)
        if not os.path.isfile(full):
            return f"[错误] 文件不存在: {rel}"
        lines = open(full, encoding="utf-8", errors="replace").read().split("\n")
        lo, hi = int(start) - 1, min(int(end) - 1, len(lines) - 1)
        if not (lo <= line - 1 <= hi):
            return f"[错误] L{line} 不在 {fn or rel} 的 [{lo+1}, {hi+1}] 内"
        tr = cfg_lib.flow(lines, lo, hi, line - 1, steps)
        ag.spent_chars += sum(len(t["code"]) for t in tr)
        return (f"从 L{line} 开始的执行轨迹（{fn or rel}）：\n" + cfg_lib.render(tr)
                + "\n（⟲ 标出的是回边：执行会跳回到前面某一行）")

    return Tool(
        name="flow",
        description=("单步控制流：从 function 的第 line 行开始，按真实控制流走 steps 步，"
                     "返回每一行的下一站；循环回边（⟲）会被显式标出。"
                     "**每个释放类调用都必须用它走一遍。**"),
        schema={"type": "object", "properties": {
            "function": {"type": "string", "description": "本批次清单里的函数名"},
            "line": {"type": "integer", "description": "起始行（1-based）"},
            "steps": {"type": "integer", "description": "走几步（默认 8，上限 20）"},
            "file": {"type": "string"}, "start_line": {"type": "integer"},
            "end_line": {"type": "integer"}},
            "required": ["line"]},
        fn=run,
    )


def run_agent(osv: str, root: str, tag: str, task: str, args,
              extra_tools: list | None = None) -> tuple[dict, int]:
    logdir = os.path.join(OUT, osv, "audit_logs")
    os.makedirs(logdir, exist_ok=True)
    ag = Agent(name=f"audit::{tag}", root=root, system=SYSTEM,
               tools=[read_file_tool(), grep_tool(), list_dir_tool()] + (extra_tools or []),
               finish_schema=FINISH_SCHEMA, model=args.model,
               max_turns=args.max_turns, max_chars=args.max_chars,
               log_path=os.path.join(logdir, tag + ".jsonl"))
    return ag.run(task), ag.spent_chars


def audit_chunk(osv: str, ctx: dict, wl: dict, chunk: dict, apis: list[str], args) -> dict:
    root, rel = ctx["repo_local"], chunk["file"]
    lo, hi = chunk["lines"]
    byname = {f["name"]: f for f in wl["functions"]
              if f["file"] == rel and f["name"] in set(chunk["functions"])}
    fn_list = "\n".join(
        f"- `{n}`（L{byname[n]['lines'][0]}-{byname[n]['lines'][1]}）"
        f"  风险: {','.join(byname[n]['risk']) or '—'}"
        for n in chunk["functions"] if n in byname)
    task = CHUNK_TASK.format(
        project=ctx.get("project"), commit=ctx.get("commit_used"), root=root,
        harness=ctx.get("fuzz_target"), apis=", ".join(apis) or "(未提取到)",
        crash_hint=args.crash_hint or "(无)",
        cid=chunk["id"], file=rel, lo=lo, hi=hi,
        n=len(chunk["functions"]), fn_list=fn_list, turns=args.max_turns)
    fn_ranges = {n: (rel, byname[n]["lines"][0], byname[n]["lines"][1])
                 for n in chunk["functions"] if n in byname}
    try:
        r, spent = run_agent(osv, root, f"chunk_{chunk['id']:03d}", task, args,
                             extra_tools=[make_flow_tool(fn_ranges)])
    except Exception as e:                        # noqa: BLE001
        return {"chunk": chunk["id"], "file": rel, "lines": [lo, hi],
                "functions": chunk["functions"], "verdicts": [], "candidates": [],
                "coverage": {"required": len(chunk["functions"]), "adjudicated": 0,
                             "missing": chunk["functions"]},
                "error": f"{type(e).__name__}: {e}"[:300], "chars_read": 0}
    got = {v.get("function") for v in (r.get("verdicts") or [])}
    for c in r.get("candidates") or []:
        c["_file"] = rel
        c.update(verify_evidence(root, c, rel))
    return {"chunk": chunk["id"], "file": rel, "lines": [lo, hi],
            "functions": chunk["functions"],
            "verdicts": r.get("verdicts") or [],
            "candidates": r.get("candidates") or [],
            "not_input_reachable": r.get("not_input_reachable") or [],
            "notes": r.get("notes") or [],
            "coverage": {"required": len(chunk["functions"]),
                         "adjudicated": len(got),
                         "missing": [n for n in chunk["functions"] if n not in got]},
            "chars_read": spent}


def audit_file(osv: str, ctx: dict, rel: str, apis: list[str], args) -> dict:
    root = ctx["repo_local"]
    nlines = sum(1 for _ in open(os.path.join(root, rel), encoding="utf-8", errors="replace"))
    task = FILE_TASK.format(project=ctx.get("project"), commit=ctx.get("commit_used"),
                            root=root, harness=ctx.get("fuzz_target"),
                            apis=", ".join(apis) or "(未提取到)", crash_hint=args.crash_hint or "(无)",
                            file=rel, nlines=nlines, turns=args.max_turns)
    try:
        r, spent = run_agent(osv, root, rel.replace("/", "__"), task, args)
    except Exception as e:                        # noqa: BLE001
        return {"file": rel, "verdicts": [], "candidates": [],
                "error": f"{type(e).__name__}: {e}"[:300], "chars_read": 0}
    for c in r.get("candidates") or []:
        c["_file"] = rel
        c.update(verify_evidence(root, c, rel))
    r["file"] = rel; r["chars_read"] = spent
    return r


def merge(osv: str, ctx: dict, parts: list[dict]) -> dict:
    cands = [c for p in parts for c in (p.get("candidates") or [])]
    cands.sort(key=lambda c: (not c.get("evidence_ok"), c.get("confidence") != "high"))
    for i, c in enumerate(cands, 1):
        c["id"] = f"c{i:03d}"
    req = sum((p.get("coverage") or {}).get("required", 0) for p in parts)
    adj = sum((p.get("coverage") or {}).get("adjudicated", 0) for p in parts)
    return {
        "_meta": {"osv_id": osv, "project": ctx.get("project"),
                  "commit": ctx.get("commit_used"),
                  "method": "LLM agent 静态审计（**未经 fuzz 实测**）",
                  "parts": len(parts),
                  "coverage": {"required": req, "adjudicated": adj,
                               "ratio": round(adj / req, 4) if req else None,
                               "missing": [n for p in parts
                                           for n in (p.get("coverage") or {}).get("missing", [])]},
                  "prompt_system": SYSTEM},
        "candidates": cands,
        "by_part": [{"chunk": p.get("chunk"), "file": p.get("file"), "lines": p.get("lines"),
                     "n_candidates": len(p.get("candidates") or []),
                     "coverage": p.get("coverage"), "error": p.get("error"),
                     "chars_read": p.get("chars_read")} for p in parts],
        "verdicts": [dict(v, file=p.get("file"), chunk=p.get("chunk"))
                     for p in parts for v in (p.get("verdicts") or [])],
        "not_input_reachable": [dict(x, file=p.get("file"))
                                for p in parts for x in (p.get("not_input_reachable") or [])],
        "notes": [x for p in parts for x in (p.get("notes") or [])],
    }


def main():
    ap = argparse.ArgumentParser(description="阶段5②：静态漏洞发现 agent")
    ap.add_argument("--osv", required=True)
    ap.add_argument("--chunk", type=int, nargs="*", help="只跑这些批次号")
    ap.add_argument("--all-chunks", action="store_true")
    ap.add_argument("--only-function", help="只审计这一个函数（实验用，单独成一档）")
    ap.add_argument("--files", nargs="*", help="文件模式（调试用）")
    ap.add_argument("--merge", action="store_true", help="合并已完成批次 → vuln_report.json")
    ap.add_argument("--model", default=os.environ.get("AUDIT_MODEL", "deepseek-chat"))
    ap.add_argument("--workers", type=int, default=int(os.environ.get("AUDIT_WORKERS", "3")))
    ap.add_argument("--max-turns", type=int, default=40)
    ap.add_argument("--max-chars", type=int, default=400_000)
    ap.add_argument("--crash-hint", default="")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--force", action="store_true")
    args = ap.parse_args()

    ctx = load_ctx(args.osv)
    root = ctx.get("repo_local")
    if not root or not os.path.isdir(root):
        raise SystemExit(f"仓库不存在: {root}")
    apis = harness_apis(args.osv)
    hdir = os.path.join(OUT, args.osv, "harness")
    harness = ", ".join(sorted(os.listdir(hdir))) if os.path.isdir(hdir) else "(无)"
    chunkdir = os.path.join(OUT, args.osv, "audit_chunks")

    if args.merge:
        if not os.path.isdir(chunkdir):
            raise SystemExit(f"没有批次结果目录 {chunkdir}")
        parts = [json.load(open(os.path.join(chunkdir, f), encoding="utf-8"))
                 for f in sorted(os.listdir(chunkdir)) if f.endswith(".json")]
        rep = merge(args.osv, ctx, parts)
        p = os.path.join(OUT, args.osv, "vuln_report.json")
        json.dump(rep, open(p, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
        cov = rep["_meta"]["coverage"]
        print(f"  合并 {len(parts)} 批 → {p}")
        print(f"  候选 {len(rep['candidates'])} 条（证据通过 "
              f"{sum(1 for c in rep['candidates'] if c.get('evidence_ok'))} 条）")
        print(f"  覆盖率 {cov['adjudicated']}/{cov['required']} = "
              f"{(cov['ratio'] or 0)*100:.1f}%   未裁决 {len(cov['missing'])}")
        return

    if args.files:
        print(f"=== {args.osv} 文件模式 ===\n  文件: {args.files}")
        if args.dry_run:
            return
        res = []
        with ThreadPoolExecutor(max_workers=args.workers) as ex:
            futs = {ex.submit(audit_file, args.osv, ctx, f, apis, args): f for f in args.files}
            for i, fu in enumerate(as_completed(futs), 1):
                r = fu.result(); res.append(r)
                print(f"  [{i}/{len(args.files)}] {futs[fu]:<28} 候选 "
                      f"{len(r.get('candidates') or [])}"
                      f"{'  ⚠ ' + r['error'] if r.get('error') else ''}", flush=True)
        rep = merge(args.osv, ctx, res)
        p = os.path.join(OUT, args.osv, "vuln_report.json")
        json.dump(rep, open(p, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
        print(f"\n  写出 {p}（候选 {len(rep['candidates'])} 条）")
        return

    wl = load_worklist(args.osv)
    if args.only_function:
        f = next((x for x in wl["functions"] if x["name"] == args.only_function), None)
        if not f:
            raise SystemExit(f"worklist 里没有函数 {args.only_function}")
        want = [{"id": 9000, "file": f["file"], "lines": f["lines"],
                 "functions": [f["name"]], "chars": f["chars"]}]
        print(f"  [单函数模式] {f['name']} @ {f['file']} L{f['lines'][0]}-{f['lines'][1]}")
    else:
        want = [c for c in wl["chunks"]
                if args.all_chunks or (args.chunk and c["id"] in args.chunk)]
    if not want:
        raise SystemExit("没指定批次：--chunk N / --all-chunks / --files")
    os.makedirs(chunkdir, exist_ok=True)

    print(f"=== {args.osv} 批次模式 ===")
    print(f"  仓库 : {root} @ {ctx.get('commit_used')}")
    print(f"  批次 : {len(want)} / worklist 共 {len(wl['chunks'])}")
    for c in want:
        print(f"      chunk #{c['id']:<3} {c['file']:<22} L{c['lines'][0]}-{c['lines'][1]}"
              f"  {c['chars']:>6} 字符  {len(c['functions'])} 函数")
    if args.dry_run:
        print("\n  [dry-run] 不调用模型")
        return

    todo = []
    for c in want:
        p = os.path.join(chunkdir, f"chunk_{c['id']:03d}.json")
        if os.path.exists(p) and not args.force:
            print(f"  chunk #{c['id']} 已有结果，跳过（--force 重跑）")
        else:
            todo.append(c)

    with ThreadPoolExecutor(max_workers=args.workers) as ex:
        futs = {ex.submit(audit_chunk, args.osv, ctx, wl, c, apis, args): c for c in todo}
        for i, fu in enumerate(as_completed(futs), 1):
            c = futs[fu]; r = fu.result()
            json.dump(r, open(os.path.join(chunkdir, f"chunk_{c['id']:03d}.json"), "w",
                              encoding="utf-8"), ensure_ascii=False, indent=1)
            cov = r.get("coverage") or {}
            print(f"  [{i}/{len(todo)}] chunk #{c['id']:<3} {c['file']:<20}"
                  f"候选 {len(r.get('candidates') or []):<3}"
                  f"裁决 {cov.get('adjudicated', 0)}/{cov.get('required', 0)}"
                  f"{'  ⚠ ' + r['error'] if r.get('error') else ''}", flush=True)

    print(f"\n  批次结果在 {chunkdir}/，用 --merge 合并")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""s5_3_audit.py —— stage5 · audit：5.2 agent 审计 + 5.2b 机械规则 + 5.2c 跨函数 + 5.2d 特征审计"""
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
# 5.2 agent 静态审计（每批一个 agent）（原 s5b_audit_agent.py）
# ══════════════════════════════════════════════════════════════════════

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

import argparse
import json
import os
import re
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed

sys.path.insert(0, HERE)


FALLBACK_FILES = ["src/in_dxf.c", "src/decode.c", "src/bits.c", "src/free.c",
                  "src/out_dxf.c", "src/in_json.c", "src/classes.c"]

SYSTEM_AUDIT = """你是一名 C/C++ 内存安全审计员，正在为一个**已确认存在漏洞**的开源库做静态审计。

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

FINISH_SCHEMA_AUDIT = {
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
        raise SystemExit(f"缺少 {p}（先跑 s5_1_main.py fetch --osv {osv}）")
    return json.load(open(p, encoding="utf-8"))


def load_worklist(osv: str) -> dict:
    p = os.path.join(OUT, osv, "audit_worklist.json")
    if not os.path.exists(p):
        raise SystemExit(f"缺少 {p}（先跑 s5_1_main.py worklist --osv {osv}）")
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


def verify_evidence_audit(root: str, cand: dict, rel: str) -> dict:
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
        tr = flow(lines, lo, hi, line - 1, steps)
        ag.spent_chars += sum(len(t["code"]) for t in tr)
        return (f"从 L{line} 开始的执行轨迹（{fn or rel}）：\n" + render(tr)
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
    ag = Agent(name=f"audit::{tag}", root=root, system=SYSTEM_AUDIT,
               tools=[read_file_tool(), grep_tool(), list_dir_tool()] + (extra_tools or []),
               finish_schema=FINISH_SCHEMA_AUDIT, model=args.model,
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
        c.update(verify_evidence_audit(root, c, rel))
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
        c.update(verify_evidence_audit(root, c, rel))
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
                  "prompt_system": SYSTEM_AUDIT},
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


def main_audit():
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

# ══════════════════════════════════════════════════════════════════════
# 5.2b 机械规则找「释放→使用」形态（离线自检）（原 s5c_mech_hypotheses.py）
# ══════════════════════════════════════════════════════════════════════

"""s5c_mech_hypotheses.py —— 阶段5③：用机械规则提出「可能崩溃点」的假设

为什么要有这一步
  agent 能读懂代码，但**判断不可靠**：实测两次把真实的 UAF 判成 clean，
  第二次还编了错误理由（"释放后立即重新赋值"）。所以不能让 agent 当判定器。
  这一步用**确定性规则**提出假设，agent 只负责补上下文（输入怎么控制、有没有守卫）。

规则（针对"释放后继续使用"这一类，数据流可判）
  R1 循环内释放后未重新赋值
       在循环体 L = [loop_start, loop_end] 内有一次调用释放包装函数 W(v)
       · 在 (call_line, loop_end] 内**没有**对 v 的赋值
       · 在 [loop_start, call_line) 内**读**过 v（`v->` / `v.` / `v[` / `v ==` / `v !=` …）
       → 下一轮迭代读到已释放的 v ⇒ 候选 UAF
       （这正是 in_dxf.c:12284 → 12267 的形态：释放后回到 while 条件读 pair->code）
  R2 同一基本块内释放后继续用
       在 (call_line, block_end] 内没有赋值 v，但读到了 v
       → 候选 UAF

  "释放包装函数" = 名字匹配 free/destroy/release/clear/cleanup 的**仓库内**函数。
  之所以要看包装函数：`dxf_free_pair (pair)` 里的 `pair = NULL` 只置空形参，
  调用方的 `pair` 仍然悬垂 —— 这是最容易漏的一类。

它产出什么
  <OSV>/mech_hypotheses.json：每条假设带 规则名 / 变量 / 释放行 / 使用行 / 证据原文。
  **这是"假设"，不是结论**：后续用 fuzz 或人工验证。

用法
  python3 s5c_mech_hypotheses.py --osv ARVO-42494732
  python3 s5c_mech_hypotheses.py --osv ARVO-42494732 --rules R1
"""

import argparse
import json
import os
import re
import sys


FREE_WRAPPER = re.compile(r"\b\w*(free|destroy|release|cleanup|clear)\w*\s*$", re.I)
CALL_RX = re.compile(r"\b([A-Za-z_]\w*)\s*\(\s*&?\s*([A-Za-z_]\w*)\s*\)\s*;")
LOOP_RX = re.compile(r"\b(while|for)\s*\(")


# ────────────────────────── 基础工具 ──────────────────────────

def strip_code(line: str) -> str:
    """去掉行内字符串与注释（粗略，够用）。"""
    line = re.sub(r'"(?:\\.|[^"\\])*"', '""', line)
    line = re.sub(r"'(?:\\.|[^'\\])*'", "''", line)
    return line.split("//")[0]


def match_brace(lines: list[str], start: int) -> int:
    """从 start 行开始找第一个 '{'，返回配对的 '}' 所在行（0-based，闭区间）。越界返回 -1。"""
    depth, i, seen = 0, start, False
    while i < len(lines):
        for ch in strip_code(lines[i]):
            if ch == "{":
                depth += 1; seen = True
            elif ch == "}":
                depth -= 1
                if seen and depth == 0:
                    return i
        i += 1
        if i - start > 4000:
            break
    return -1


def find_loops(lines: list[str], lo: int, hi: int) -> list[tuple[int, int]]:
    """在 [lo, hi] 行内找 while/for 块，返回 (起始行, 结束行)（0-based）。"""
    out = []
    for i in range(lo, hi + 1):
        if LOOP_RX.search(strip_code(lines[i])):
            j = i
            while j <= hi and "{" not in strip_code(lines[j]) and j < i + 3:
                j += 1
            end = match_brace(lines, j)
            if end > 0 and end <= hi:
                out.append((i, end))
    return out


def reads_of(lines: list[str], lo: int, hi: int, var: str) -> int | None:
    """在 [lo, hi] 行内找第一次"读" var 的行；赋值不算读。"""
    # 只认"解引用"：v-> / v. / v[] ；`if (v)` / `if (!v)` 只是判空，不算 UAF
    pat_read = re.compile(rf"\b{re.escape(var)}\b\s*(->|\.|\[)")
    pat_assign = re.compile(rf"^\s*\b{re.escape(var)}\b\s*=[^=]")
    for i in range(lo, hi + 1):
        s = strip_code(lines[i])
        if pat_assign.search(s):
            continue
        if pat_read.search(s):
            return i
    return None


def assigned_in(lines: list[str], lo: int, hi: int, var: str) -> bool:
    pat = re.compile(rf"\b{re.escape(var)}\b\s*=(?!=)|\b{re.escape(var)}\b\s*=(?!=)\s*[^=]")
    for i in range(lo, hi + 1):
        s = strip_code(lines[i])
        if re.search(rf"(^|[;{{(])\s*&?\s*\b{re.escape(var)}\b\s*=(?!=)", s):
            return True
        if re.search(rf"\b{re.escape(var)}\b\s*=(?!=)", s) and not re.search(
                rf"{re.escape(var)}\s*(==|!=|>=|<=)", s):
            if pat.search(s):
                return True
    return False



def param_name(lines: list[str], lo: int, hi: int, fname: str) -> str | None:
    """从函数源码里取第一个形参的名字。"""
    sig = " ".join(strip_code(x) for x in lines[lo:min(hi, lo + 3) + 1])
    m = re.search(rf"\b{re.escape(fname)}\s*\(([^)]*)\)", sig)
    if not m:
        return None
    first = m.group(1).split(",")[0].strip()
    if not first or first == "void":
        return None
    ids = re.findall(r"[A-Za-z_]\w*", first)
    return ids[-1] if ids else None


def frees_param_itself(lines: list[str], lo: int, hi: int, fname: str) -> bool:
    """W(v) 到底是不是释放 v 本身？（而不是释放 v->member）

    判据：函数体里出现 `free (<param>)` / `free(<param>)`，而不是 `free(<param>->x)`。
    这条过滤很关键：`dwg_free_appinfo (dwg)` 释放的是 dwg->appinfo，
    dwg 本身仍然有效，不该被当成悬垂。
    """
    p = param_name(lines, lo, hi, fname)
    if not p:
        return False
    body = "\n".join(strip_code(x) for x in lines[lo:hi + 1])
    if re.search(rf"\bfree\s*\(\s*{re.escape(p)}\s*\)", body):
        return True
    if re.search(rf"\b(kfree|g_free|sdsfree)\s*\(\s*{re.escape(p)}\s*\)", body):
        return True
    return False


# ────────────────────────── 规则 ──────────────────────────

def candidate_from(lines: list[str], rel: str, fn: str, var: str, call_i: int,
                   use_i: int, loop: tuple[int, int] | None, rule: str) -> dict:
    return {
        "rule": rule,
        "vuln_type": "use-after-free",
        "file": rel,
        "function": fn,
        "variable": var,
        "free_line": call_i + 1,
        "use_line": use_i + 1,
        "loop": [loop[0] + 1, loop[1] + 1] if loop else None,
        "evidence_lines": [[call_i + 1, lines[call_i].strip()],
                           [use_i + 1, lines[use_i].strip()]],
        "mechanism": (
            f"`{var}` 在第 {call_i+1} 行被释放包装函数释放后，"
            + (f"循环 [L{loop[0]+1}-L{loop[1]+1}] 内没有重新赋值，"
               if loop else "同一块内没有重新赋值，")
            + f"而第 {use_i+1} 行仍会读它"
            + ("（下一轮迭代回到循环开头时读到已释放内存）" if loop else "")
        ),
        "status": "hypothesis_unverified",
    }


def scan_function(lines: list[str], rel: str, fn: str, lo: int, hi: int,
                  wrappers: set[str], rules: set[str]) -> list[dict]:
    out = []
    loops = find_loops(lines, lo, hi) if "R1" in rules else []

    for i in range(lo, hi + 1):
        m = CALL_RX.search(strip_code(lines[i]))
        if not m:
            continue
        callee, var = m.group(1), m.group(2)
        if callee not in wrappers or callee == var:
            continue

        # R1：所在的循环（取最内层包含该行的）
        encl = [L for L in loops if L[0] <= i <= L[1]]
        if encl and "R1" in rules:
            loop = max(encl, key=lambda L: L[0])       # 最内层
            if not assigned_in(lines, i + 1, loop[1], var):
                u = reads_of(lines, loop[0], i - 1, var)
                if u is not None:
                    out.append(candidate_from(lines, rel, fn, var, i, u, loop, "R1"))
                    continue

        # R2：同一块内（用函数体 [i+1, hi] 作粗略基本块）
        if "R2" in rules:
            if not assigned_in(lines, i + 1, hi, var):
                u = reads_of(lines, i + 1, min(hi, i + 120), var)
                if u is not None:
                    out.append(candidate_from(lines, rel, fn, var, i, u, None, "R2"))
    return out


# ────────────────────────── 主流程 ──────────────────────────

def main_mech():
    ap = argparse.ArgumentParser(description="阶段5③：机械规则提假设")
    ap.add_argument("--osv", required=True)
    ap.add_argument("--rules", nargs="*", default=["R1", "R2"])
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--merge", action="store_true")
    args = ap.parse_args()
    rules = set(args.rules)

    ctxp = os.path.join(OUT, args.osv, "source_context.json")
    wlp = os.path.join(OUT, args.osv, "audit_worklist.json")
    for p in (ctxp, wlp):
        if not os.path.exists(p):
            raise SystemExit(f"缺少 {p}")
    ctx = json.load(open(ctxp, encoding="utf-8"))
    wl = json.load(open(wlp, encoding="utf-8"))
    root = ctx["repo_local"]

    # 释放包装函数候选：名字匹配 free/destroy/release/clear/cleanup
    cand_wrappers = {f["name"] for f in wl["functions"] if FREE_WRAPPER.search(f["name"])}

    # 预读源码（后面既要用它过滤包装函数，也要扫描）
    src_cache: dict[str, list[str]] = {}
    for f in wl["functions"]:
        rel = f["file"]
        if rel not in src_cache:
            p = os.path.join(root, rel)
            src_cache[rel] = (open(p, encoding="utf-8", errors="replace").read().split("\n")
                              if os.path.isfile(p) else [])

    # 只保留"直接释放第一个形参本身"的包装函数（排除 dwg_free_appinfo(dwg) 这类
    # 只释放成员的）；这能大幅降低假阳性
    wrappers, rejected = set(), []
    for f in wl["functions"]:
        if f["name"] not in cand_wrappers:
            continue
        lines = src_cache[f["file"]]
        lo, hi = f["lines"][0] - 1, f["lines"][1] - 1
        if lines and 0 <= lo <= hi < len(lines) and frees_param_itself(lines, lo, hi, f["name"]):
            wrappers.add(f["name"])
        else:
            rejected.append(f["name"])

    print(f"=== {args.osv} 机械规则提假设 ===")
    print(f"  规则        : {sorted(rules)}")
    print(f"  包装函数候选 : {len(cand_wrappers)} 个 → 直接释放形参的 {len(wrappers)} 个"
          f"（排除 {len(rejected)} 个只释放成员的）")
    print(f"  保留         : {sorted(wrappers)[:6]}{'…' if len(wrappers) > 6 else ''}")

    funcs = wl["functions"]
    hyps = []
    skipped = 0
    for f in funcs:
        rel = f["file"]
        lines = src_cache.get(rel, [])
        lo, hi = f["lines"][0] - 1, f["lines"][1] - 1
        if not lines or hi >= len(lines) or lo < 0:
            skipped += 1
            continue
        for h in scan_function(lines, rel, f["name"], lo, hi, wrappers, rules):
            h["chars"] = f["chars"]
            hyps.append(h)

    hyps.sort(key=lambda h: (h["rule"], h["file"], h["free_line"]))
    for i, h in enumerate(hyps, 1):
        h["id"] = f"h{i:03d}"

    # 自检：已知崩溃行是否被某条假设的 use_line 覆盖
    fl, ff = ctx.get("fault_line"), (ctx.get("fault_file") or "").split("/")[-1]
    cov = [h for h in hyps if ff and h["file"].endswith(ff) and
           min(h["free_line"], h["use_line"]) <= (fl or -1) <= max(h["free_line"], h["use_line"])]

    print(f"  扫描函数    : {len(funcs)} 个（跳过 {skipped}）")
    print(f"  假设        : {len(hyps)} 条")
    from collections import Counter
    print(f"  按规则      : {dict(Counter(h['rule'] for h in hyps))}")
    print(f"  按文件      : {dict(Counter(h['file'] for h in hyps).most_common(8))}")
    if fl is not None:
        print(f"  自检：已知崩溃行 {ff}:{fl} "
              f"{'✅ 被假设覆盖' if cov else '❌ 未被覆盖'}")
        for h in cov[:3]:
            print(f"      {h['id']} {h['rule']} {h['function']} "
                  f"释放L{h['free_line']} → 使用L{h['use_line']}")

    out = {"_meta": {"osv_id": args.osv, "project": ctx.get("project"),
                     "commit": ctx.get("commit_used"), "rules": sorted(rules),
                     "free_wrappers": sorted(wrappers),
                     "method": "确定性源码规则（0 LLM），产出的是**未验证假设**",
                     "fault_file": ctx.get("fault_file"), "fault_line": fl,
                     "covers_fault_line": bool(cov)},
           "hypotheses": hyps}
    if args.dry_run:
        print("\n  [dry-run] 不写出")
        return
    p = os.path.join(OUT, args.osv, "mech_hypotheses.json")
    json.dump(out, open(p, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(f"\n  写出 {p}")

# ══════════════════════════════════════════════════════════════════════
# 5.2c 跨函数证据（补 llm04/llm05 缺的那一环）（原 s5g_interproc.py）
# ══════════════════════════════════════════════════════════════════════

"""s5g_interproc.py —— 跨函数证据工具（补上 llm04/llm05 缺的那一环）

问题
  `s5f_feature_pipeline.py` 是**行级**扫描器。它能判定"同函数释放后使用"（llm01/llm03），
  但建立不了"函数 A 释放、函数 B 读取"的关系——所以 llm04（跨函数陈旧对象）和
  llm05（容器销毁后遍历）只能报 `not_found`，而那是**方法局限，不是项目里没有**。

本模块提供的三个原语
  · `callers(fn)`  谁调用了它
  · `callees(fn)`  它调用了谁
  · `field_uses(field)`  结构体字段 `->field` 在**所有可达函数**里的写点 / 释放点 / 读点

  有了 field_uses，就能拼出 llm04 的形状：
      写点(存指针) ——释放点——> 读点，且释放与读不在同一函数
  以及 llm05 的形状：
      容器销毁点 ——> 遍历点，遍历点读的是 next/prev/child 链

用法
  python3 s5g_interproc.py --osv ARVO-42494732 --field obj_hdls
  python3 s5g_interproc.py --osv ARVO-42494732 --callers resolve_postponed_object_refs
  python3 s5g_interproc.py --osv ARVO-42494732 --callees resolve_postponed_object_refs
"""

import argparse
import json
import os
import re
import sys



def load_dump(p):
    methods, edges = [], {}
    for ln in open(p, encoding="utf-8"):
        t = ln.rstrip("\n").split("\t")
        if t[0] == "@@M" and len(t) >= 6:
            methods.append({"file": t[1], "name": t[2], "start": int(t[3] or 0),
                            "end": int(t[4] or 0), "external": t[5] == "1"})
        elif t[0] == "@@C" and len(t) >= 4:
            edges.setdefault((t[1], t[2]), set()).update(t[3].split("|"))
    return methods, edges


class Interproc:
    def __init__(self, root, methods, edges, worklist):
        self.root = root
        self.methods = methods
        self.edges = edges
        self.by_name = {}
        for m in methods:
            if not m["external"] and m["name"] != "<global>":
                self.by_name.setdefault(m["name"], m)
        self.reachable = {f["name"] for f in worklist["functions"]}
        self._src = {}

    # ── 调用关系 ──
    def callers(self, fn):
        out = []
        for (cf, cn), cs in self.edges.items():
            if fn in cs and cn in self.by_name:
                out.append({"function": cn, "file": cf,
                            "reachable": cn in self.reachable})
        return sorted(out, key=lambda x: (not x["reachable"], x["file"]))

    def callees(self, fn):
        m = self.by_name.get(fn)
        if not m:
            return []
        return sorted(c for c in self.edges.get((m["file"], fn), set())
                      if re.match(r"^[A-Za-z_]", c) and not c.startswith("<operator>"))

    # ── 字段级 def-use ──
    def lines(self, rel):
        if rel not in self._src:
            p = os.path.join(self.root, rel)
            self._src[rel] = (open(p, encoding="utf-8", errors="replace").read().split("\n")
                              if os.path.isfile(p) else None)
        return self._src[rel]

    def field_uses(self, field, only_reachable=True):
        """在所有可达函数里找 `->field` 的写 / 释放 / 读。"""
        rx = re.compile(rf"->\s*{re.escape(field)}\b")
        free_rx = re.compile(r"\b\w*(free|destroy|release|clear)\w*\s*\(")
        write_rx = re.compile(rf"->\s*{re.escape(field)}\s*=(?!=)")
        out = {"writes": [], "frees": [], "reads": []}
        for name, m in self.by_name.items():
            if only_reachable and name not in self.reachable:
                continue
            lines = self.lines(m["file"])
            if not lines:
                continue
            lo, hi = m["start"] - 1, min(m["end"], len(lines))
            for i in range(lo, hi):
                # 同时处理 `free(x->f)` 和 `FREE_IF(x->f)` 两种形态
                if not rx.search(lines[i]):
                    continue
                rec = {"function": name, "file": m["file"], "line": i + 1,
                       "code": lines[i].strip()[:140]}
                if free_rx.search(lines[i]):
                    out["frees"].append(rec)
                elif write_rx.search(lines[i]):
                    out["writes"].append(rec)
                else:
                    out["reads"].append(rec)
        return out


def cross_function_shape(ip, field, min_gap=1):
    """llm04/llm05 的判定形状：同名字段上存在 写点/释放点/读点，且释放与读**不同函数**。"""
    u = ip.field_uses(field)
    fns_free = {r["function"] for r in u["frees"]}
    fns_read = {r["function"] for r in u["reads"]}
    fns_write = {r["function"] for r in u["writes"]}
    pairs = []
    for f in u["frees"]:
        for r in u["reads"]:
            if f["function"] != r["function"]:
                pairs.append({"free": f, "use": r,
                              "gap_functions": [f["function"], r["function"]]})
    return {
        "field": field,
        "counts": {k: len(v) for k, v in u.items()},
        "free_functions": sorted(fns_free),
        "read_functions": sorted(fns_read),
        "write_functions": sorted(fns_write),
        "cross_function_pairs": pairs[:12],
        "verdict": ("cross_function_free_then_use_candidate" if pairs
                    else "no_cross_function_shape"),
    }


def main_interproc():
    ap = argparse.ArgumentParser(description="跨函数证据工具")
    ap.add_argument("--osv", required=True)
    ap.add_argument("--field", help="结构体字段名（不带 ->）")
    ap.add_argument("--callers")
    ap.add_argument("--callees")
    ap.add_argument("--json-out", default=None)
    args = ap.parse_args()

    S5 = os.path.join(OUT, args.osv)
    root = json.load(open(os.path.join(S5, "source_context.json"),
                         encoding="utf-8"))["repo_local"]
    worklist = json.load(open(os.path.join(S5, "audit_worklist.json"), encoding="utf-8"))
    methods, edges = load_dump(os.path.join(S5, "cpg_dump.tsv"))
    ip = Interproc(root, methods, edges, worklist)

    res = {}
    if args.callers:
        res["callers"] = ip.callers(args.callers)
        print(f"=== callers({args.callers}) ===")
        for c in res["callers"]:
            print(f"  {'●' if c['reachable'] else '·'} {c['function']:<34} {c['file']}")
    if args.callees:
        res["callees"] = ip.callees(args.callees)
        print(f"=== callees({args.callees}) ===")
        for c in res["callees"]:
            m = ip.by_name.get(c)
            print(f"  {c:<34} " + (f"{m['file']}:{m['start']}" if m else "(外部)"))
    if args.field:
        res["field"] = cross_function_shape(ip, args.field)
        f = res["field"]
        print(f"=== field_uses(->{args.field}) ===")
        print(f"  写点 {f['counts']['writes']}  释放点 {f['counts']['frees']}  "
              f"读点 {f['counts']['reads']}")
        print(f"  释放所在函数: {f['free_functions'][:5]}")
        print(f"  读取所在函数: {f['read_functions'][:5]}")
        print(f"  判定: {f['verdict']}")
        for p in f["cross_function_pairs"][:4]:
            print(f"    释放 {p['free']['function']}:{p['free']['line']} "
                  f"→ 读取 {p['use']['function']}:{p['use']['line']}")

    if args.json_out:
        json.dump(res, open(args.json_out, "w", encoding="utf-8"),
                  ensure_ascii=False, indent=1)
        print(f"\n写出 {args.json_out}")

# ══════════════════════════════════════════════════════════════════════
# 5.2d 带跨函数视野的特征站点审计（原 s5h_feature_audit.py）
# ══════════════════════════════════════════════════════════════════════

"""s5h_feature_audit.py —— 带**跨函数视野**的特征站点审计（agent 判定）

为什么需要它
  `s5f_feature_pipeline.py` 是行级扫描器，能判"同函数释放后使用"，但建立不了
  "函数 A 释放、函数 B 读取"的关系。所以 llm04（跨函数陈旧对象）只能报 not_found，
  而那是**方法局限**。本脚本把三个跨函数原语交给 agent，让它逐个候选判定：

      real            有真实的 free-then-use 路径（给证据行）
      false_positive  看着像，但生命周期不同 / 顺序不对 / 有置空或提前返回
      unclear         证据不足

给 agent 的工具
  callers(fn) / callees(fn)        调用关系
  field_uses(field)                某字段的 写点 / 释放点 / 读点（跨所有可达函数）
  read_file / grep / flow          源码与单步控制流

用法
  python3 s5h_feature_audit.py --osv ARVO-42494732 --feature uaf-llm04
  python3 s5h_feature_audit.py --osv ARVO-42494732 --feature uaf-llm05 --max-candidates 6
"""

import argparse
import json
import os
import re
import sys

sys.path.insert(0, HERE)


SYSTEM_FEAT = """你是 C 代码的内存安全审计员。你的任务：判定在**给定机制**下，
项目中是否存在一条真实的"释放后仍使用"路径。

关键：你要判的是**控制流事实**，不是代码长得像。

判定规则
1. `free(x->f)` 之后 `x->f->...` 是嫌疑；但如果两次访问属于**不同生命周期**
   （例如分别在两次独立调用里、中间结构体被重新初始化/重新分配），**不是** UAF。
2. 释放之后如果对同一指针做了**置空**或**重新赋值**，不是 UAF。
3. 释放之后控流直接 `return` / `goto` 到函数外，且之后没有再用，不是 UAF。
4. 同一字段在不同函数里被释放和读取，**必须**能说明存在一条真实调用路径让
   释放先发生、读取后发生。说不出来就判 false_positive 或 unclear。
5. 只相信你在源码里看到的行。**不要**用"通常""可能"来补证据。

判不了就写 unclear，并说明缺什么信息——这比编一个结论有价值。
"""

FINISH_SCHEMA_FEAT = {
    "type": "object",
    "properties": {
        "verdicts": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "candidate": {"type": "string"},
                    "verdict": {"type": "string",
                                "enum": ["real", "false_positive", "unclear"]},
                    "evidence_lines": {
                        "type": "array",
                        "items": {"type": "array", "items": {"type": "string"}}},
                    "reason": {"type": "string"},
                },
                "required": ["candidate", "verdict", "reason"],
            },
        },
        "sites": {
            "type": "array",
            "description": "判为 real 的站点（结构化，便于后续归并）",
            "items": {
                "type": "object",
                "properties": {
                    "file": {"type": "string"},
                    "function": {"type": "string"},
                    "free_line": {"type": "integer"},
                    "use_line": {"type": "integer"},
                    "var": {"type": "string"},
                    "format": {"type": "string"}},
                "required": ["file", "function", "free_line", "use_line"],
            },
        },
        "summary": {"type": "string"},
    },
    "required": ["verdicts", "summary"],
}


def collect_candidates(ip: Interproc, max_n=10):
    """一次遍历，按字段聚合 写点/释放点/读点；留下有跨函数释放-读取的字段。"""
    agg = {}
    free_rx = re.compile(r"\b\w*(free|destroy|release|clear)\w*\s*\(")
    write_rx = re.compile(r"->\s*(\w+)\s*=(?!=)")
    deref_rx = re.compile(r"->\s*(\w+)\b")
    for name in ip.reachable:
        m = ip.by_name.get(name)
        if not m:
            continue
        lines = ip.lines(m["file"])
        if not lines:
            continue
        lo, hi = m["start"] - 1, min(m["end"], len(lines))
        for i in range(lo, hi):
            t = lines[i]
            if "->" not in t:
                continue
            is_free = bool(free_rx.search(t))
            for fld in set(deref_rx.findall(t)):
                d = agg.setdefault(fld, {"writes": [], "frees": [], "reads": []})
                rec = {"function": name, "file": m["file"], "line": i + 1,
                       "code": t.strip()[:140]}
                if is_free:
                    d["frees"].append(rec)
                elif write_rx.search(t) and write_rx.search(t).group(1) == fld:
                    d["writes"].append(rec)
                else:
                    d["reads"].append(rec)
    cands = []
    for fld, d in agg.items():
        fns_f = {r["function"] for r in d["frees"]}
        fns_r = {r["function"] for r in d["reads"]}
        cross = [(r["function"], u["function"]) for r in d["frees"] for u in d["reads"]
                 if r["function"] != u["function"]]
        if not cross:
            continue
        cands.append({"field": fld,
                      "counts": {k: len(v) for k, v in d.items()},
                      "free_functions": sorted(fns_f), "read_functions": sorted(fns_r),
                      "cross_pairs": len(cross),
                      "sample": {"free": d["frees"][0], "read": d["reads"][0]}})
    cands.sort(key=lambda c: (-c["cross_pairs"], -c["counts"]["frees"]))
    return cands[:max_n]


def make_tools(ip: Interproc):
    def t_callers(a, ag):
        fn = a["function"]
        rows = ip.callers(fn)
        ag.spent_chars += 200
        return "\n".join(f"{'●' if r['reachable'] else '·'} {r['function']}  {r['file']}"
                         for r in rows) or "（没有调用者）"

    def t_callees(a, ag):
        fn = a["function"]
        rows = ip.callees(fn)
        ag.spent_chars += 200
        return "\n".join(f"{c}  " + (f"{ip.by_name[c]['file']}:{ip.by_name[c]['start']}"
                                     if c in ip.by_name else "(外部)") for c in rows) or "（没有）"

    def t_field(a, ag):
        fld = a["field"].lstrip("-").lstrip(">")
        u = ip.field_uses(fld, only_reachable=True)
        ag.spent_chars += 800
        out = [f"->{fld}: 写 {len(u['writes'])}  释放 {len(u['frees'])}  读 {len(u['reads'])}"]
        for k in ("frees", "writes", "reads"):
            for r in u[k][:8]:
                out.append(f"  [{k[:4]}] {r['function']}:{r['line']}  {r['code']}")
        return "\n".join(out)

    def t_flow(a, ag):
        fn, line = a.get("function"), int(a["line"])
        m = ip.by_name.get(fn)
        if not m:
            return f"[错误] 未知函数 {fn}"
        lines = ip.lines(m["file"])
        lo, hi = m["start"] - 1, min(m["end"], len(lines)) - 1
        tr = flow(lines, lo, hi, line - 1, min(int(a.get("steps") or 8), 20))
        ag.spent_chars += sum(len(x["code"]) for x in tr)
        return render(tr) + "\n（⟲ 是回边）"

    return [
        Tool("callers", "谁调用了这个函数", {"type": "object",
             "properties": {"function": {"type": "string"}}, "required": ["function"]}, t_callers),
        Tool("callees", "这个函数调用了谁", {"type": "object",
             "properties": {"function": {"type": "string"}}, "required": ["function"]}, t_callees),
        Tool("field_uses", "某结构体字段在所有可达函数里的 写/释放/读 点",
             {"type": "object", "properties": {"field": {"type": "string"}},
              "required": ["field"]}, t_field),
        Tool("flow", "从某函数的某一行按控制流单步走，回边会标 ⟲",
             {"type": "object", "properties": {"function": {"type": "string"},
                                               "line": {"type": "integer"},
                                               "steps": {"type": "integer"}},
              "required": ["function", "line"]}, t_flow),
        read_file_tool(), grep_tool(),
    ]


def main_feat_audit():
    ap = argparse.ArgumentParser(description="带跨函数视野的特征站点审计")
    ap.add_argument("--osv", required=True)
    ap.add_argument("--feature", required=True)
    ap.add_argument("--type", default="uaf")
    ap.add_argument("--max-candidates", type=int, default=8)
    ap.add_argument("--max-turns", type=int, default=30)
    ap.add_argument("--model", default=os.environ.get("AUDIT_MODEL", "deepseek-chat"))
    args = ap.parse_args()

    S5 = os.path.join(OUT, args.osv)
    root = json.load(open(os.path.join(S5, "source_context.json"),
                          encoding="utf-8"))["repo_local"]
    worklist = json.load(open(os.path.join(S5, "audit_worklist.json"), encoding="utf-8"))
    methods, edges = load_dump(os.path.join(S5, "cpg_dump.tsv"))
    ip = Interproc(root, methods, edges, worklist)

    feats = json.load(open(os.path.join(ROOT, "outputs", "stage4", args.type,
                                       "features.json"), encoding="utf-8"))["features"]
    feat = next((f for f in feats if f["id"] == args.feature), None)
    if not feat:
        raise SystemExit(f"没有特征 {args.feature}")

    cands = collect_candidates(ip, args.max_candidates)
    print(f"=== {args.feature} 跨函数审计 ===")
    print(f"  候选字段 {len(cands)} 个（有跨函数 释放→读取 的）")
    for c in cands:
        print(f"    ->{c['field']:<16} 写 {c['counts']['writes']:>2} 释放 "
              f"{c['counts']['frees']:>2} 读 {c['counts']['reads']:>3}  跨函数对 {c['cross_pairs']}")

    task = (f"# 机制\n"
            f"特征 {feat['id']}「{feat.get('feature_name')}」\n\n"
            f"## 前置条件\n" +
            "\n".join(f"- {p}" for p in feat.get("precondition") or []) +
            f"\n\n## 变异目标\n" +
            "\n".join(f"- {m}" for m in feat.get("mutation_target") or []) +
            f"\n\n## 候选（按字段聚合，已确认存在跨函数的 释放→读取）\n" +
            "\n".join(
                f"### 候选 {i+1}: ->{c['field']}\n"
                f"- 计数: 写 {c['counts']['writes']} 释放 {c['counts']['frees']} 读 {c['counts']['reads']}\n"
                f"- 释放所在函数: {c['free_functions'][:6]}\n"
                f"- 读取所在函数: {c['read_functions'][:6]}\n"
                f"- 样例释放: {c['sample']['free']['function']}:{c['sample']['free']['line']}  "
                f"`{c['sample']['free']['code']}`\n"
                f"- 样例读取: {c['sample']['read']['function']}:{c['sample']['read']['line']}  "
                f"`{c['sample']['read']['code']}`\n"
                for i, c in enumerate(cands)) +
            "\n# 你的任务\n"
            "对**每个候选**判定 real / false_positive / unclear，并给证据行。\n"
            "工具：`field_uses(field)` 看全部点，`callers/callees` 看调用路径，"
            "`flow(function,line)` 看控制流，`read_file/grep` 看源码。\n"
            "**必须**说明是什么调用路径让释放先发生、读取后发生；说不出来就 false_positive 或 unclear。\n"
            "**判为 real 的候选，必须在 `sites` 里给出结构化站点**："
            "`{file, function, free_line, use_line, var, format}`。\n"
            "最后调用 finish 提交 JSON。")

    ag = Agent(name=f"feataudit::{args.feature}", root=root, system=SYSTEM_FEAT,
               tools=make_tools(ip), finish_schema=FINISH_SCHEMA_FEAT, model=args.model,
               max_turns=args.max_turns,
               log_path=os.path.join(S5, "audit_logs", f"feat_{args.feature}.jsonl"))
    res = ag.run(task)

    d = os.path.join(S5, "v2", "features", args.feature)
    os.makedirs(d, exist_ok=True)
    json.dump({"feature_id": args.feature, "candidates": cands,
               "agent_verdicts": res, "spent_chars": ag.spent_chars},
              open(os.path.join(d, "cross_function_audit.json"), "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)

    with open(os.path.join(d, "history.jsonl"), "a", encoding="utf-8") as fh:
        vs = (res.get("verdicts") or [])
        fh.write(json.dumps({
            "ts": __import__("datetime").datetime.now().astimezone().isoformat(timespec="seconds"),
            "model": ag.model, "max_turns": args.max_turns,
            "counts": {"real": sum(1 for v in vs if v["verdict"] == "real"),
                       "false_positive": sum(1 for v in vs if v["verdict"] == "false_positive"),
                       "unclear": sum(1 for v in vs if v["verdict"] == "unclear")},
            "sites": res.get("sites"), "summary": res.get("summary")},
            ensure_ascii=False) + "\n")

    print("\n  判定：")
    for v in (res.get("verdicts") or []):
        icon = {"real": "✅", "false_positive": "❌", "unclear": "⚠️"}.get(v["verdict"], "?")
        print(f"    {icon} {v.get('candidate'):<18} {v.get('verdict'):<15} {v.get('reason','')[:80]}")
    print(f"\n  summary: {res.get('summary','')[:300]}")
    print(f"  写出 {d}/cross_function_audit.json")



# ══════════════════════════════════════════════════════════════════════
# 阶段入口
# ══════════════════════════════════════════════════════════════════════

def main(argv=None, what="audit", **kw):
    """默认跑 audit + mech；what 可取 audit/mech/interproc/feat-audit。"""
    ap = argparse.ArgumentParser(description="stage5 · audit")
    ap.add_argument("--osv", required=True)
    ap.add_argument("--all-chunks", action="store_true")
    ap.add_argument("--chunk", action="append", type=int)
    ap.add_argument("--merge", action="store_true")
    ap.add_argument("--model", default=None)
    ap.add_argument("--max-turns", type=int, default=None)
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args(sys.argv[1:] if argv is None else list(argv))

    if not (a.all_chunks or a.chunk or a.merge) and what == "audit":
        print("\n[stage5] audit 需要显式给出范围：\n"
              "  --all-chunks        跑全部批次（LLM，很贵）\n"
              "  --chunk N --chunk M 只跑指定批次\n"
              "  --merge             只把已有 audit_chunks/ 合并成 vuln_report.json（不调 LLM）",
              file=sys.stderr)
        return 2

    av = ["--osv", a.osv]
    if a.all_chunks: av += ["--all-chunks"]
    av += sum((["--chunk", str(c)] for c in a.chunk or []), [])
    if a.merge:     av += ["--merge"]
    if a.model:     av += ["--model", a.model]
    if a.max_turns: av += ["--max-turns", str(a.max_turns)]
    if a.dry_run:   av += ["--dry-run"]

    if what != "audit":
        fn = {"mech": main_mech, "interproc": main_interproc,
              "feat-audit": main_feat_audit}[what]
        return run_fn(fn, av)

    for fn, arg in ((main_audit, av), (main_mech, ["--osv", a.osv])):
        if a.merge and fn is main_mech:
            break
        print(f"\n--- {fn.__name__}")
        rc = run_fn(fn, arg)
        if rc:
            return rc
    return 0


if __name__ == "__main__":
    sys.exit(main())

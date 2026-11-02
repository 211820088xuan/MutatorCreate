#!/usr/bin/env python3
# -*- coding: utf-8 -*-
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
from __future__ import annotations

import argparse
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
TOP = os.path.dirname(ROOT)
OUT = os.path.join(ROOT, "projects")
sys.path.insert(0, HERE)

from agent_runtime import Agent, Tool, grep_tool, read_file_tool  # noqa: E402
import cfg_lib  # noqa: E402
from s5g_interproc import Interproc, load_dump  # noqa: E402

SYSTEM = """你是 C 代码的内存安全审计员。你的任务：判定在**给定机制**下，
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

FINISH_SCHEMA = {
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
        tr = cfg_lib.flow(lines, lo, hi, line - 1, min(int(a.get("steps") or 8), 20))
        ag.spent_chars += sum(len(x["code"]) for x in tr)
        return cfg_lib.render(tr) + "\n（⟲ 是回边）"

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


def main():
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

    ag = Agent(name=f"feataudit::{args.feature}", root=root, system=SYSTEM,
               tools=make_tools(ip), finish_schema=FINISH_SCHEMA, model=args.model,
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


if __name__ == "__main__":
    main()

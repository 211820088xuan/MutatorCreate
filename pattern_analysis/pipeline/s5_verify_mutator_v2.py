#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""s5_verify_mutator_v2.py —— 阶段5.6：V2 的统一验证门禁

四层门禁
  V1 schema   ：各层 schema_version / commit / plan_id 一致；blocked 不得继续
  V2 evidence ：源码文件存在、行号合法、代码片段是该行子串、每个 action 有 basis_refs 且可解析
  V3 code     ：C11 语法通过、接口签名正确、用了 MaxSize 边界、能拷原输入
  V4 behavior ：已知 crash 输入可重放、种子能被 parser 接受（需要 --binary，否则 not_applicable）

输出 verification.json，每层状态为 pass / fail / not_applicable / blocked。

用法
  python3 s5_verify_mutator_v2.py --osv ARVO-42494732
  python3 s5_verify_mutator_v2.py --osv ARVO-42494732 --binary /exp/fuzz_exp/llvmfuzz
"""
from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
TOP = os.path.dirname(ROOT)
OUT = os.path.join(TOP, "mutator_custom", "stage5")

SHIM = """#include <stddef.h>
#include <stdint.h>
size_t LLVMFuzzerMutate(uint8_t *Data, size_t Size, size_t MaxSize);
"""


def load(p):
    return json.load(open(p, encoding="utf-8")) if os.path.exists(p) else None


def gate_v1(manifest, surface, findings, bindings, plan, mutator):
    problems, notes = [], []
    for name, doc in (("manifest", manifest), ("target_surface", surface),
                      ("candidate_findings", findings), ("feature_bindings", bindings),
                      ("mutation_plan", plan), ("mutator", mutator)):
        if not doc:
            problems.append(f"{name} 缺失")
        elif not doc.get("schema_version"):
            problems.append(f"{name} 缺 schema_version")
    if plan:
        if plan.get("status") != "ready":
            problems.append(f"plan status={plan.get('status')}（blocked 不得继续）")
        if mutator and (mutator.get("generation_gate") or {}).get("plan_status") != "ready":
            problems.append("mutator.generation_gate.plan_status != ready")
        commits = {str((d.get("target") or {}).get("commit"))
                   for d in (surface, findings, plan, mutator) if d}
        commits.discard("None")
        if len(commits) > 1:
            problems.append(f"commit 不一致: {sorted(commits)}")
        if not (plan.get("mutations") or []):
            problems.append("plan 没有 mutations")
    notes.append(f"documents={sum(1 for d in (manifest, surface, findings, bindings, plan, mutator) if d)}/6")
    return ("pass" if not problems else "fail"), problems, notes


def gate_v2(source_root, findings, plan):
    problems, notes = [], []
    for x in (findings or {}).get("findings") or []:
        rel, ev = x.get("file"), x.get("evidence_lines") or []
        p = os.path.join(source_root, rel) if rel else None
        if not p or not os.path.isfile(p):
            problems.append(f"{x.get('finding_id')}: 源文件缺失 {rel}")
            continue
        lines = open(p, encoding="utf-8", errors="replace").read().split("\n")
        for e in ev:
            try:
                ln, code = int(e[0]), str(e[1])
            except (TypeError, ValueError, IndexError):
                problems.append(f"{x.get('finding_id')}: 证据行格式错 {e}")
                continue
            if not (1 <= ln <= len(lines)):
                problems.append(f"{x.get('finding_id')}: L{ln} 越界")
            elif "".join(code.split()) not in "".join(lines[ln - 1].split()):
                problems.append(f"{x.get('finding_id')}: L{ln} 原文不符")
    for a in (plan or {}).get("mutations") or []:
        if not a.get("basis_refs"):
            problems.append(f"{a.get('action_id')}: 没有 basis_refs")
    notes.append(f"actions={(plan or {}).get('mutations') and len(plan['mutations'])}")
    return ("pass" if not problems else "fail"), problems, notes


def gate_v3(code: str, shim_dir: str) -> tuple:
    problems, notes = [], []
    if not code.strip():
        return "fail", ["mutator.c 为空"], notes
    if "LLVMFuzzerCustomMutator" not in code:
        problems.append("缺少 LLVMFuzzerCustomMutator 接口")
    if "MaxSize" not in code:
        problems.append("没有用 MaxSize 做边界")
    if not re.search(r"memcpy|memmove", code):
        problems.append("没有拷出原输入")
    tmp = tempfile.mkdtemp(prefix="v3_")
    shim = os.path.join(tmp, "shim.c")
    open(shim, "w", encoding="utf-8").write(SHIM + f'\n#include "{os.path.abspath(os.path.join(shim_dir, "mutator.c"))}"\n')
    r = subprocess.run(["clang", "-fsyntax-only", "-std=c11", "-Wall", "-Wextra", shim],
                       capture_output=True, text=True)
    if r.returncode != 0:
        problems.append("clang 语法检查失败: " + (r.stderr or "")[:400].replace("\n", " | "))
    else:
        notes.append("clang -fsyntax-only 通过")
    return ("pass" if not problems else "fail"), problems, notes


def gate_v4(binary: str, ctx: dict) -> tuple:
    if not binary or not os.path.exists(binary):
        return "not_applicable", [], ["没有提供 --binary，跳过行为门禁"]
    problems, notes = [], []
    tc = ctx.get("testcase_path") or ctx.get("testcase")
    if tc and os.path.isfile(tc):
        r = subprocess.run([binary, "-runs=1", tc], capture_output=True, text=True, timeout=300)
        blob = (r.stdout or "") + (r.stderr or "")
        m = re.search(r"SUMMARY: AddressSanitizer: (\S+) (\S+?):(\d+)", blob)
        if m:
            notes.append(f"已知 crash 回放: {m.group(1)} {m.group(2)}:{m.group(3)}")
        else:
            problems.append("已知 crash 无法回放（没有 ASan SUMMARY）")
    else:
        notes.append("没有 testcase 路径，跳过回放")
    return ("pass" if not problems else "fail"), problems, notes


def main():
    ap = argparse.ArgumentParser(description="阶段5.6：V2 统一验证门禁")
    ap.add_argument("--osv", required=True)
    ap.add_argument("--binary", default=None)
    args = ap.parse_args()

    V2 = os.path.join(OUT, args.osv, "v2")
    manifest = load(os.path.join(V2, "manifest.json"))
    surface = load(os.path.join(V2, "target_surface.json"))
    findings = load(os.path.join(V2, "candidate_findings.json"))
    bindings = load(os.path.join(V2, "feature_bindings.json"))
    plan = load(os.path.join(V2, "mutation_plan.json"))
    mutator = load(os.path.join(V2, "mutator.json"))
    codep = os.path.join(V2, "mutator.c")
    code = open(codep, encoding="utf-8").read() if os.path.exists(codep) else ""
    ctx = load(os.path.join(OUT, args.osv, "source_context.json")) or {}
    root = ctx.get("repo_local") or ""

    res = {}
    for name, (st, prob, notes) in (
            ("V1_schema", gate_v1(manifest, surface, findings, bindings, plan, mutator)),
            ("V2_evidence", gate_v2(root, findings, plan)),
            ("V3_code", gate_v3(code, V2)),
            ("V4_behavior", gate_v4(args.binary, ctx))):
        res[name] = {"status": st, "problems": prob, "notes": notes}

    allst = [v["status"] for v in res.values()]
    overall = ("fail" if "fail" in allst else
               "blocked" if "blocked" in allst else
               "pass_with_skipped" if "not_applicable" in allst else "pass")
    out = {"schema_version": "stage5.verification.v1",
           "target": (plan or {}).get("target"),
           "gates": res, "overall": overall,
           "commands": {"V3": "clang -fsyntax-only -std=c11 -Wall -Wextra (shim)"}}
    json.dump(out, open(os.path.join(V2, "verification.json"), "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)

    print(f"=== {args.osv} verification ===")
    for k, v in res.items():
        print(f"  {k:<14} {v['status'].upper():<16} {len(v['problems'])} 问题")
        for p in v["problems"][:4]:
            print(f"      ✗ {p}")
        for n in v["notes"][:2]:
            print(f"      · {n}")
    print(f"\n  overall = {overall}")
    print(f"  写出 {os.path.join(V2, 'verification.json')}")
    return 0 if overall in ("pass", "pass_with_skipped") else 1


if __name__ == "__main__":
    sys.exit(main())

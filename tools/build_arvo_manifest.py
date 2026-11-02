#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""build_arvo_manifest.py —— 生成 ARVO 复现状态清单

输入
  /root/gyx/arvo/data/arvo.db                                   ARVO 数据集（6,138 行 / 311 项目）
  artifacts/reproduced_crashes.jsonl           已复现台账（1,154 条）
  reproduce_crash/artifacts/logs/reproduce/*.log                复现尝试日志（1,174 次）
  artifacts/facts|interpretation/<OSV>/        下游产物
  cpg_files/<project>_<commit>.cpg                              CPG 图

输出（默认写到 manifests/）
  arvo_manifest.jsonl        每行一个 ARVO 崩溃，含复现状态与证据
  arvo_manifest.csv          同上，表格版
  outside_manifest.jsonl     ARVO 之外（OSS-Fuzz）的复现/失败记录
  arvo_summary.json          按项目/类型/语言/状态聚合

状态定义
  reproduced       我们本地复现成功（有日志 + 台账行）
  not_reproduced   未复现。reason 目前只可能是 not_attempted（没有尝试日志）；
                   注意 ARVO 库里的 reproduced / verified / patch_located 是**常量列**，
                   没有区分度，不能用来解释原因。

用法
  python3 tools/build_arvo_manifest.py
  python3 tools/build_arvo_manifest.py --out manifests
"""
from __future__ import annotations

import argparse
import collections
import csv
import glob
import json
import os
import re
import sqlite3
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB = os.path.join(os.path.dirname(ROOT), "arvo", "data", "arvo.db")

CRASH_FAMILY = [
    ("heap-use-after-free", "use-after-free"),
    ("use-after-free", "use-after-free"),
    ("double-free", "double-free"),
    ("invalid-free", "invalid-free"),
    ("heap-buffer-overflow", "heap-buffer-overflow"),
    ("stack-buffer-overflow", "stack-buffer-overflow"),
    ("global-buffer-overflow", "global-buffer-overflow"),
    ("dynamic-stack-buffer-overflow", "stack-buffer-overflow"),
    ("container-overflow", "container-overflow"),
    ("use-of-uninitialized-value", "uninitialized-value"),
    ("integer-overflow", "integer-overflow"),
    ("negative-size-param", "negative-size-param"),
    ("null-dereference", "null-dereference"),
    ("segv", "segv"),
    ("timeout", "timeout"),
    ("oom", "out-of-memory"),
    ("stack-use-after-return", "stack-use-after-return"),
    ("stack-use-after-scope", "stack-use-after-scope"),
    ("use-after-poison", "use-after-poison"),
    ("bad-free", "bad-free"),
    ("memcpy-param-overlap", "memcpy-param-overlap"),
    ("stack-buffer-underflow", "stack-buffer-underflow"),
    ("unknown read", "unknown-read"),
    ("unknown write", "unknown-write"),
    ("unknown signal", "unknown-signal"),
]


def family(crash_type: str) -> str:
    t = (crash_type or "").lower().replace("_", "-")
    for pat, fam in CRASH_FAMILY:
        if pat in t:
            return fam
    head = re.split(r"[\s:]+", t)[0] if t else "unknown"
    return head or "unknown"


def load_ledger():
    p = os.path.join(ROOT, "artifacts", "reproduced_crashes.jsonl")
    out = {}
    for line in open(p, encoding="utf-8"):
        line = line.strip()
        if not line:
            continue
        d = json.loads(line)
        out[d["osv_id"]] = d
    return out


def attempt_logs():
    d = os.path.join(ROOT, "reproduce_crash", "artifacts", "logs", "reproduce")
    return {os.path.basename(p)[:-4]
            for p in glob.glob(os.path.join(d, "*.log"))}


def have_dirs(kind):
    d = os.path.join(ROOT, "artifacts", kind)
    return {os.path.basename(p) for p in glob.glob(os.path.join(d, "*"))
            if os.path.isdir(p)}


def cpg_by_project():
    """cpg_files/<project>_<commit12>.cpg → {project: [文件名]}"""
    out = collections.defaultdict(list)
    for p in glob.glob(os.path.join(ROOT, "cpg_files", "*.cpg")):
        base = os.path.basename(p)[:-4]
        proj, _, commit = base.rpartition("_")
        out[proj].append(base)
    return out


def main():
    ap = argparse.ArgumentParser(description="生成 ARVO 复现状态清单")
    ap.add_argument("--out", default=os.path.join(ROOT, "manifests"))
    ap.add_argument("--db", default=DB)
    args = ap.parse_args()

    if not os.path.exists(args.db):
        raise SystemExit(f"找不到 ARVO 库: {args.db}")

    ledger = load_ledger()
    logs = attempt_logs()
    facts = have_dirs("facts")
    interp = have_dirs("interpretation")
    cpgs = cpg_by_project()

    con = sqlite3.connect(args.db)
    con.row_factory = sqlite3.Row
    rows = con.execute("select * from arvo").fetchall()

    out_rows = []
    for r in rows:
        lid = str(r["localId"])
        osv = f"ARVO-{lid}"
        hit = ledger.get(osv)
        attempted = osv in logs
        row = {
            "osv_id": osv,
            "local_id": lid,
            "project": r["project"],
            "repo_addr": r["repo_addr"],
            "fix_commit": r["fix_commit"],
            "fix_commit_short": (r["fix_commit"] or "")[:12],
            "fuzz_target": r["fuzz_target"],
            "fuzz_engine": r["fuzz_engine"],
            "sanitizer": r["sanitizer"],
            "language": r["language"],
            "crash_type": r["crash_type"],
            "crash_family": family(r["crash_type"]),
            "severity": r["severity"],
            "submodule_bug": r["submodule_bug"],
            "report_url": r["report"],
            "status": "reproduced" if hit else "not_reproduced",
            "reason": None if hit else ("not_attempted" if not attempted else "attempt_failed"),
            "attempted": attempted,
            "has_fault_location": False,
            "fault_file": None, "fault_fn": None, "fault_line": None,
            "pin_commit": None, "testcase_size": None,
            "crash_type_norm": None, "has_facts": False,
            "has_interpretation": False, "has_deep": False, "cpg_count": 0,
        }
        if hit:
            row.update({
                "fault_file": hit.get("fault_file"),
                "fault_fn": hit.get("fault_fn"),
                "fault_line": hit.get("fault_line"),
                "pin_commit": hit.get("pin_commit"),
                "testcase_size": hit.get("testcase_size"),
                "crash_type_norm": hit.get("crash_type_norm"),
                "has_facts": bool(hit.get("has_facts")) or osv in facts,
                "has_interpretation": bool(hit.get("has_interpretation")) or osv in interp,
                "has_deep": bool(hit.get("has_deep")),
                "has_fault_location": bool(hit.get("fault_fn") and hit.get("fault_line")),
            })
        row["cpg_count"] = len(cpgs.get(r["project"], []))
        out_rows.append(row)

    # ARVO 之外：OSS-Fuzz 的复现/失败记录
    outside = []
    for osv, d in ledger.items():
        if d.get("source") == "ARVO":
            continue
        outside.append({
            "osv_id": osv, "project": d.get("project"),
            "repo_url": d.get("repo_url"), "fix_commit": d.get("fix_commit"),
            "fuzz_target": d.get("fuzz_target"), "sanitizer": d.get("sanitizer"),
            "crash_type": d.get("crash_type"),
            "crash_family": family(d.get("crash_type")),
            "status": "reproduced", "reason": None,
            "fault_file": d.get("fault_file"), "fault_fn": d.get("fault_fn"),
            "fault_line": d.get("fault_line"), "pin_commit": d.get("pin_commit"),
            "testcase_size": d.get("testcase_size"),
            "has_facts": osv in facts, "has_interpretation": osv in interp,
        })
    for osv in sorted(logs - set(ledger)):
        outside.append({
            "osv_id": osv, "project": None, "repo_url": None, "fix_commit": None,
            "fuzz_target": None, "sanitizer": None, "crash_type": None,
            "crash_family": None, "status": "not_reproduced",
            "reason": "attempt_failed",
            "fault_file": None, "fault_fn": None, "fault_line": None,
            "pin_commit": None, "testcase_size": None,
            "has_facts": osv in facts, "has_interpretation": osv in interp,
        })

    os.makedirs(args.out, exist_ok=True)
    jl = os.path.join(args.out, "arvo_manifest.jsonl")
    with open(jl, "w", encoding="utf-8") as f:
        for r in out_rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")

    cs = os.path.join(args.out, "arvo_manifest.csv")
    with open(cs, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(out_rows[0].keys()))
        w.writeheader()
        w.writerows(out_rows)

    jl2 = os.path.join(args.out, "outside_manifest.jsonl")
    with open(jl2, "w", encoding="utf-8") as f:
        for r in outside:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")

    def agg(key):
        return dict(collections.Counter(r[key] for r in out_rows).most_common())

    by_proj = collections.Counter(r["project"] for r in out_rows)
    rep_proj = collections.Counter(r["project"] for r in out_rows if r["status"] == "reproduced")
    summary = {
        "arvo_total": len(out_rows),
        "arvo_projects": len(by_proj),
        "reproduced": sum(1 for r in out_rows if r["status"] == "reproduced"),
        "not_reproduced": sum(1 for r in out_rows if r["status"] != "reproduced"),
        "reproduced_projects": len(rep_proj),
        "by_status": agg("status"),
        "by_reason": agg("reason"),
        "by_crash_family": agg("crash_family"),
        "by_language": agg("language"),
        "by_sanitizer": agg("sanitizer"),
        "by_fuzz_engine": agg("fuzz_engine"),
        "reproduced_by_crash_family": dict(collections.Counter(
            r["crash_family"] for r in out_rows if r["status"] == "reproduced")),
        "reproduced_with_fault_location": sum(
            1 for r in out_rows
            if r["status"] == "reproduced" and r["has_fault_location"]),
        "reproduced_without_fault_location": sum(
            1 for r in out_rows
            if r["status"] == "reproduced" and not r["has_fault_location"]),
        "reproduced_by_project": dict(rep_proj.most_common()),
        "projects_total": dict(by_proj.most_common()),
        "outside": {
            "total": len(outside),
            "reproduced": sum(1 for r in outside if r["status"] == "reproduced"),
            "attempt_failed": sum(1 for r in outside if r["reason"] == "attempt_failed"),
        },
        "notes": [
            "arvo.reproduced / verified / patch_located 是常量列（全 1 / 全 0 / 全 1），无区分度",
            "ARVO 里没有『尝试过但失败』的记录：31 次失败尝试全部是 OSS-Fuzz（OSV-*）",
            "not_reproduced 的 5,223 条均为 not_attempted（没有复现日志）",
            "cpG_count 是该项目的 CPG 图数量（与具体崩溃无关，只看项目维度）",
        ],
    }
    sp = os.path.join(args.out, "arvo_summary.json")
    json.dump(summary, open(sp, "w", encoding="utf-8"), ensure_ascii=False, indent=1)

    print(f"=== ARVO 复现清单 ===")
    print(f"  ARVO 总数      : {summary['arvo_total']}（{summary['arvo_projects']} 个项目）")
    print(f"  已复现         : {summary['reproduced']}（{summary['reproduced_projects']} 个项目）")
    print(f"  未复现         : {summary['not_reproduced']}")
    print(f"    └ 未尝试     : {summary['by_reason'].get('not_attempted', 0)}")
    print(f"    └ 尝试失败   : {summary['by_reason'].get('attempt_failed', 0)}")
    print(f"  ARVO 之外      : {summary['outside']['total']}"
          f"（复现 {summary['outside']['reproduced']} / 失败 {summary['outside']['attempt_failed']}）")
    print(f"  已复现且有故障位置: {summary['reproduced_with_fault_location']}"
          f" / 无位置: {summary['reproduced_without_fault_location']}")
    print(f"  已复现的 crash family: {summary['reproduced_by_crash_family']}")
    print()
    for p in (jl, cs, jl2, sp):
        print(f"  写出 {p}  ({os.path.getsize(p)/1024:.0f} KB)")


if __name__ == "__main__":
    main()

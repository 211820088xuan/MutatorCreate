#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""summarize.py —— V2 单特征对照实验汇总

指标（都按文档 §6 Task 7 的口径）
  execs / exec/s、cov、ft
  崩溃文件数（**不等于**漏洞数）、去重后的唯一崩溃点
  目标崩溃（in_dxf.c:12267）的出现情况
  每 100k exec 的目标崩溃触发密度

用法
  python3 summarize.py <experiment_dir> [--binary <bin>]
"""
from __future__ import annotations

import argparse
import collections
import json
import os
import re
import subprocess
import sys

TARGET = "in_dxf.c:12267"
SUMMARY_RX = re.compile(r"SUMMARY: AddressSanitizer: (\S+) (\S+?):(\d+)")


def parse_log(p: str) -> dict:
    if not os.path.exists(p):
        return {}
    txt = open(p, encoding="utf-8", errors="replace").read()
    last = None
    for m in re.finditer(r"^#(\d+):.*?cov: (\d+).*?ft: (\d+).*?exec/s:?\s*(\d+).*?"
                         r"oom/timeout/crash: (\d+)/(\d+)/(\d+)", txt, re.M):
        last = {"execs": int(m.group(1)), "cov": int(m.group(2)), "ft": int(m.group(3)),
                "exec_s": int(m.group(4)),
                "oom": int(m.group(5)), "timeout": int(m.group(6)),
                "crash": int(m.group(7))}
    if "stat::number_of_executed_units" in txt:
        m = re.search(r"stat::number_of_executed_units:\s*(\d+)", txt)
        if m and last:
            last["execs_total"] = int(m.group(1))
    return last or {}


def classify(binary: str, path: str) -> str:
    try:
        r = subprocess.run([binary, "-runs=1", path], capture_output=True,
                           text=True, timeout=180,
                           env={**os.environ, "ASAN_OPTIONS": "detect_leaks=0",
                                "LSAN_OPTIONS": "detect_leaks=0"})
    except subprocess.TimeoutExpired:
        return "TIMEOUT:?"
    m = SUMMARY_RX.search((r.stdout or "") + (r.stderr or ""))
    if not m:
        return "NO_CRASH"
    return f"{m.group(1)} @ {os.path.basename(m.group(2))}:{m.group(3)}"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("root")
    ap.add_argument("--binary", default=None)
    ap.add_argument("--no-dedup", action="store_true")
    args = ap.parse_args()

    rows = {}
    for arm in ("default", "custom"):
        d = os.path.join(args.root, arm)
        log = parse_log(os.path.join(d, "run.log"))
        cr = os.path.join(d, "crash")
        files = sorted(f for f in os.listdir(cr) if f.startswith(("crash-", "oom-", "timeout-"))) \
            if os.path.isdir(cr) else []
        kinds = collections.Counter()
        if args.binary and not args.no_dedup:
            for f in files:
                kinds[classify(args.binary, os.path.join(cr, f))] += 1
        rows[arm] = {"log": log, "crash_files": len(files),
                     "kinds": dict(kinds), "unique": len(kinds)}

    print(f"# V2 单特征对照汇总  root={args.root}\n")
    print("| 口径 | default | custom |")
    print("|---|---|---|")
    for k, label in (("execs", "execs"), ("cov", "cov"), ("ft", "ft"),
                     ("exec_s", "exec/s"), ("crash", "log 里的 crash 计数")):
        a, b = rows["default"]["log"].get(k), rows["custom"]["log"].get(k)
        print(f"| {label} | {a} | {b} |")
    print(f"| 崩溃文件数 | {rows['default']['crash_files']} | {rows['custom']['crash_files']} |")
    if not args.no_dedup:
        print(f"| **唯一崩溃点** | **{rows['default']['unique']}** | **{rows['custom']['unique']}** |")

    print()
    for arm in ("default", "custom"):
        ks = rows[arm]["kinds"]
        if not ks:
            continue
        tgt = sum(v for k, v in ks.items() if TARGET in k)
        ex = rows[arm]["log"].get("execs") or 0
        print(f"## {arm}")
        for k, v in sorted(ks.items(), key=lambda kv: -kv[1]):
            mark = "  ← 目标" if TARGET in k else ""
            print(f"  - {k} × {v}{mark}")
        if ex:
            print(f"  目标触发密度: {tgt}/{ex} = **{tgt / ex * 1e5:.2f} / 100k exec**")
        print()

    out = os.path.join(args.root, "summary.json")
    json.dump(rows, open(out, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(f"写出 {out}")


if __name__ == "__main__":
    main()

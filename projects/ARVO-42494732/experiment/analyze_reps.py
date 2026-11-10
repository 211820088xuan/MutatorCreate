#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""analyze_reps.py —— 重复对照实验的配对分析

读 reps/repNN/{default,custom}/run.log + crash/，给出：
  · 每次 rep 的 execs / cov / ft / 崩溃文件 / 唯一崩溃点
  · 目标崩溃的**合并率比**与 95% CI（Poisson）
  · 每次 rep 的配对率比 + 符号检验（几个 rep 里 custom 更好）
  · 目标崩溃点的去重明细

用法（在容器内）：
  python3 analyze_reps.py /exp/v2/experiment/reps --binary /exp/v2/experiment/llvmfuzz
"""
from __future__ import annotations

import argparse
import collections
import glob
import json
import math
import os
import re
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor

TARGET = "in_dxf.c:12267"
SUMMARY_RX = re.compile(r"SUMMARY: AddressSanitizer: (\S+) (\S+?):(\d+)")
PROG_RX = re.compile(r"^#(\d+):.*?cov: (\d+).*?ft: (\d+).*?exec/s:?\s*(\d+)", re.M)


def parse_log(p: str) -> dict:
    if not os.path.exists(p):
        return {}
    last = {}
    for m in PROG_RX.finditer(open(p, encoding="utf-8", errors="replace").read()):
        last = {"execs": int(m.group(1)), "cov": int(m.group(2)),
                "ft": int(m.group(3)), "exec_s": int(m.group(4))}
    return last


def classify(binary: str, path: str) -> str:
    env = {**os.environ, "ASAN_OPTIONS": "detect_leaks=0", "LSAN_OPTIONS": "detect_leaks=0"}
    try:
        r = subprocess.run([binary, "-runs=1", path], capture_output=True,
                           text=True, timeout=20, env=env)
    except subprocess.TimeoutExpired:
        return "TIMEOUT:?"
    m = SUMMARY_RX.search((r.stdout or "") + (r.stderr or ""))
    return f"{m.group(1)} @ {os.path.basename(m.group(2))}:{m.group(3)}" if m else "NO_CRASH"


def analyze_arm(d: str, binary: str | None) -> dict:
    log = parse_log(os.path.join(d, "run.log"))
    cr = os.path.join(d, "crash")
    files = sorted(f for f in os.listdir(cr)
                   if f.startswith(("crash-", "oom-", "timeout-"))) if os.path.isdir(cr) else []
    kinds = collections.Counter()
    if binary:
        with ThreadPoolExecutor(max_workers=8) as ex:
            for res in ex.map(lambda f: classify(binary, os.path.join(cr, f)), files):
                kinds[res] += 1
    tgt = sum(v for k, v in kinds.items() if TARGET in k) if binary else None
    return {"log": log, "crash_files": len(files), "kinds": dict(kinds),
            "unique": len(kinds), "target": tgt,
            "execs": log.get("execs", 0), "cov": log.get("cov", 0),
            "ft": log.get("ft", 0)}


def poisson_rr_ci(a: int, na: int, b: int, nb: int) -> tuple[float, float, float]:
    """custom(b/nb) vs default(a/na) 的率比与 95% CI。"""
    if a == 0 or b == 0 or na == 0 or nb == 0:
        return float("nan"), float("nan"), float("nan")
    rr = (b / nb) / (a / na)
    se = math.sqrt(1 / a + 1 / b)
    return rr, math.exp(math.log(rr) - 1.96 * se), math.exp(math.log(rr) + 1.96 * se)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("root")
    ap.add_argument("--binary", default=None)
    ap.add_argument("--json-out", default=None)
    args = ap.parse_args()

    reps = sorted(d for d in glob.glob(os.path.join(args.root, "rep*")) if os.path.isdir(d))
    rows = []
    for r in reps:
        dflt = analyze_arm(os.path.join(r, "default"), args.binary)
        cust = analyze_arm(os.path.join(r, "custom"), args.binary)
        rows.append({"rep": os.path.basename(r), "default": dflt, "custom": cust})

    if not rows:
        sys.exit(f"没有找到 {args.root}/rep*")

    print(f"# 重复对照分析  n={len(rows)}  (目标崩溃点: {TARGET})\n")
    print("| rep | 臂 | execs | cov | ft | 崩溃文件 | 唯一点 | 目标命中 | 目标/100k |")
    print("|---|---|---|---|---|---|---|---|---|")
    for x in rows:
        for arm in ("default", "custom"):
            a = x[arm]
            dens = (a["target"] / a["execs"] * 1e5) if (a["target"] is not None and a["execs"]) else None
            print(f"| {x['rep']} | {arm} | {a['execs']} | {a['cov']} | {a['ft']} | "
                  f"{a['crash_files']} | {a['unique']} | {a['target']} | "
                  f"{dens:.2f} |" if dens is not None else
                  f"| {x['rep']} | {arm} | {a['execs']} | {a['cov']} | {a['ft']} | "
                  f"{a['crash_files']} | {a['unique']} | - | - |")

    # 配对率比
    print("\n## 每次 rep 的配对率比（custom / default）\n")
    print("| rep | default 率/100k | custom 率/100k | 比值 |")
    print("|---|---|---|---|")
    ratios = []
    for x in rows:
        d, c = x["default"], x["custom"]
        if d["target"] is None or c["target"] is None or not d["execs"] or not c["execs"]:
            print(f"| {x['rep']} | - | - | - |")
            continue
        rd = d["target"] / d["execs"] * 1e5
        rc = c["target"] / c["execs"] * 1e5
        rr = rc / rd if rd else float("nan")
        ratios.append(rr)
        print(f"| {x['rep']} | {rd:.2f} | {rc:.2f} | **{rr:.2f}×** |")

    # 合并
    ta = sum((x["default"]["target"] or 0) for x in rows)
    na = sum(x["default"]["execs"] for x in rows)
    tb = sum((x["custom"]["target"] or 0) for x in rows)
    nb = sum(x["custom"]["execs"] for x in rows)
    rr, lo, hi = poisson_rr_ci(ta, na, tb, nb)
    print("\n## 合并（Poisson 率比）\n")
    print(f"- default: {ta} 次目标崩溃 / {na:,} execs = "
          f"{ta / na * 1e5:.2f} / 100k")
    print(f"- custom : {tb} 次目标崩溃 / {nb:,} execs = "
          f"{tb / nb * 1e5:.2f} / 100k")
    print(f"- **RR = {rr:.3f}，95% CI = [{lo:.2f}, {hi:.2f}]**  "
          f"→ {'CI 含 1，不显著' if lo < 1 < hi else 'CI 不含 1'}")
    if ratios:
        wins = sum(1 for r in ratios if r > 1)
        print(f"- 配对胜出: {wins}/{len(ratios)} 个 rep 里 custom 更高；"
              f"中位比值 {sorted(ratios)[len(ratios) // 2]:.2f}×")

    # 覆盖率
    cv = [(x["custom"]["cov"] / x["default"]["cov"]) for x in rows if x["default"]["cov"]]
    if cv:
        print(f"- 覆盖率比 custom/default: 中位 {sorted(cv)[len(cv) // 2]:.3f}，"
              f"范围 [{min(cv):.3f}, {max(cv):.3f}]")

    # 唯一崩溃点汇总
    allk = collections.Counter()
    for x in rows:
        for arm in ("default", "custom"):
            allk.update(x[arm]["kinds"])
    if allk:
        print("\n## 所有 rep 里出现过的唯一崩溃点\n")
        for k, v in sorted(allk.items(), key=lambda kv: -kv[1]):
            print(f"- {k} × {v}" + ("  ← 目标" if TARGET in k else ""))

    if args.json_out:
        json.dump({"reps": rows,
                   "pooled": {"default": {"target": ta, "execs": na},
                              "custom": {"target": tb, "execs": nb},
                              "rr": rr, "ci": [lo, hi]}},
                  open(args.json_out, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
        print(f"\n写出 {args.json_out}")


if __name__ == "__main__":
    main()

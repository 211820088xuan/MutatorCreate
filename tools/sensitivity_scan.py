#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""字节敏感性扫描：定位「改动哪个输入字节会改变崩溃行为」。

背景（查漏补缺第 2 项 · 便宜补缺口 B · 已修正）
----------------------------------------------
ddmin（分块删除）对**压缩/序列化格式**的输入无效——实测 c-blosc2 两条崩溃
无论删前半还是后半都不再崩（结构是紧耦合的，删任意一段都破坏格式）。
正确做法不是"删除"，而是"**改写单个字节看崩溃是否变化**"：
  * 改某字节 → 崩溃消失 = 该字节是触发必要条件（如魔数、类型标志）；
  * 改某字节 → 崩溃仍在但**越界宽度变化** = 该字节是**长度/计数参数**（正是缺口 B 要的）。

输出：每个字节位置对若干 sentinel 值的响应（still_crash / no_crash / width_changed），
汇总出「敏感字节位置」与「疑似长度字段位置」。

用法：
    python3 tools/sensitivity_scan.py --bin <fuzzer> --input <testcase> \
        --docker --range 0:64 --sentinel 0,255,127,128 --out <json>
"""
from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time

CRASH_PATTERNS = (
    "ERROR: AddressSanitizer",
    "ERROR: MemorySanitizer",
    "WARNING: MemorySanitizer",
    "ERROR: ThreadSanitizer",
)
# 抓 "WRITE of size N" / "READ of size N"
SZ_RE = re.compile(r"(WRITE|READ) of size (\d+)")


def run_once(binpath, data, tmpdir, docker):
    p = os.path.join(tmpdir, "in.bin")
    with open(p, "wb") as f:
        f.write(data)
    try:
        if docker:
            bname = os.path.basename(binpath)
            r = subprocess.run(
                ["docker", "run", "--rm", "-v", f"{tmpdir}:/out", "-v", f"{p}:/testcase",
                 "gcr.io/oss-fuzz-base/base-runner:ubuntu-24-04",
                 "bash", "-c",
                 f"cd /out; ./{bname} -rss_limit_mb=2560 -timeout=25 /testcase < /dev/null"],
                stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL,
                stderr=subprocess.PIPE, timeout=25,
            )
        else:
            r = subprocess.run([binpath, "-rss_limit_mb=2560", "-timeout=25", p],
                               stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL,
                               stderr=subprocess.PIPE, timeout=25)
        err = r.stderr.decode("utf-8", "replace")
        crashed = any(pat in err for pat in CRASH_PATTERNS)
        m = SZ_RE.search(err)
        width = int(m.group(2)) if m else None
        return crashed, width
    except subprocess.TimeoutExpired:
        return False, None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--bin", required=True)
    ap.add_argument("--input", required=True)
    ap.add_argument("--docker", action="store_true")
    ap.add_argument("--range", default="0:64", help="字节区间 [lo:hi)，默认头 64 字节")
    ap.add_argument("--sentinel", default="0,255,127,128")
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    lo, hi = (int(x) for x in args.range.split(":"))
    sentinels = [int(x) for x in args.sentinel.split(",")]
    orig = bytearray(open(args.input, "rb").read())
    hi = min(hi, len(orig))

    tmpdir = tempfile.mkdtemp(prefix="sens_")
    binpath = args.bin
    if args.docker:
        shutil.copy(args.bin, os.path.join(tmpdir, os.path.basename(args.bin)))
        binpath = os.path.join(tmpdir, os.path.basename(args.bin))

    base_crash, base_width = run_once(binpath, bytes(orig), tmpdir, args.docker)
    if not base_crash:
        print(f"❌ 原始输入未复现崩溃，中止", file=sys.stderr)
        sys.exit(2)
    print(f"✅ 基线崩溃：dir={'WRITE/READ'} width={base_width}")

    rows = []
    for i in range(lo, hi):
        orig_b = orig[i]
        for v in sentinels:
            if v == orig_b:
                continue
            data = bytearray(orig)
            data[i] = v
            crash, w = run_once(binpath, bytes(data), tmpdir, args.docker)
            if not crash:
                eff = "no_crash"
            elif base_width and w and w != base_width:
                eff = f"width_changed:{w}"
            else:
                eff = "same"
            rows.append({"pos": i, "orig": orig_b, "sentinel": v, "effect": eff})

    # 汇总：每个字节位置是否敏感
    sens = {}
    for r in rows:
        pos = r["pos"]
        key = "SENSITIVE" if r["effect"] in ("no_crash",) or r["effect"].startswith("width_changed") else "inert"
        s = sens.setdefault(pos, {"no_crash": False, "width_changed": [], "n_tested": 0})
        s["n_tested"] += 1
        if r["effect"] == "no_crash":
            s["no_crash"] = True
        elif r["effect"].startswith("width_changed"):
            s["width_changed"].append(r["effect"].split(":", 1)[1])

    out = {
        "input": args.input, "range": [lo, hi], "sentinels": sentinels,
        "base_width": base_width, "rows": rows,
        "sensitive_positions": {k: v for k, v in sorted(sens.items()) if v["no_crash"] or v["width_changed"]},
    }
    json.dump(out, open(args.out, "w"), ensure_ascii=False, indent=2)

    print(f"\n=== 敏感字节（改动后崩溃消失或宽度变化）===")
    for pos, v in sorted(out["sensitive_positions"].items()):
        print(f"  pos {pos}: no_crash={v['no_crash']} width_changed={v['width_changed']}")
    print(f"\n结果写入 {args.out}")


if __name__ == "__main__":
    main()

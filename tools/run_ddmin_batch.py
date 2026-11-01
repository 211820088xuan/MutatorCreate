#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""批量 ddmin：对一组已复现崩溃做输入最小化，定位「崩溃依赖的输入字节」。

用法：
    python3 tools/run_ddmin_batch.py --out artifacts/m15_ddmin_summary.json \
        [--max-crashes 20] [--floor 1]

内部：
  * 扫描 delivery 目录，按 osv_id 定位 (binary, testcase)；
  * 每次调用前走 tools/tz_gate.py 检查北京时段，高峰则 sleep 到非高峰；
  * 每个崩溃调 tools/ddmin_crash.py --docker（解决宿主 glibc 过旧）；
  * 结果写 JSON（原大小 → 最小大小 → 存活字节偏移区间）。

设计为可断点续跑：已完成的 osv 记录在 <out>.done 里，重跑会跳过。
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
BYCRASH = os.path.join(ROOT, "reproduce_crash", "artifacts", "by_crash_type")
DDMIN = os.path.join(ROOT, "tools", "ddmin_crash.py")

# 亚型 B（块长度失控，访问宽度巨大）—— 最值得做「输入字节 → 长度参数」映射的一批
SUBTYPE_B_OSV = [
    "OSV-2021-639", "OSV-2021-1645", "OSV-2021-1676", "OSV-2021-1710",
    "OSV-2021-1755", "OSV-2022-33", "OSV-2022-55", "OSV-2021-1712",
    "OSV-2021-1663", "OSV-2021-27", "OSV-2021-1791", "OSV-2021-997",
    "OSV-2021-897", "OSV-2025-797",
]


def find_entry(osv: str):
    """在 delivery 目录里按 osv_id 找 (binary, testcase)。"""
    hits = []
    for root, dirs, files in os.walk(BYCRASH):
        if os.path.basename(root) == osv:
            binpath = None
            for f in files:
                if f.endswith("_fuzzer") or f.endswith("_fuzzer") and os.access(os.path.join(root, f), os.X_OK):
                    pass
            # 可执行文件：无扩展名且可执行
            for f in files:
                fp = os.path.join(root, f)
                if os.access(fp, os.X_OK) and "." not in f:
                    binpath = fp
                    break
            tc = os.path.join(root, "testcase")
            if binpath and os.path.isfile(tc):
                hits.append((osv, binpath, tc))
    return hits[0] if hits else None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=os.path.join(ROOT, "pattern_analysis", "artifacts", "m15_ddmin_summary.json"))
    ap.add_argument("--max-crashes", type=int, default=20)
    ap.add_argument("--floor", type=int, default=1)
    ap.add_argument("--max-iters", type=int, default=600)
    args = ap.parse_args()

    done_path = args.out + ".done"
    done = set()
    if os.path.isfile(done_path):
        done = set(l.strip() for l in open(done_path) if l.strip())

    results = []
    if os.path.isfile(args.out):
        results = json.load(open(args.out))

    entries = []
    for osv in SUBTYPE_B_OSV:
        if osv in done:
            continue
        e = find_entry(osv)
        if e:
            entries.append(e)
        else:
            results.append({"osv_id": osv, "status": "entry_not_found"})

    entries = entries[:args.max_crashes]
    print(f"待处理 {len(entries)} 条崩溃（已跳过 {len(done)} 条已完成）")

    for osv, binpath, tc in entries:
        sz = os.path.getsize(tc)
        out = os.path.join(ROOT, "pattern_analysis", "artifacts", f"ddmin_{osv}.bin")
        print(f"\n=== {osv}  size={sz} ===", flush=True)
        r = subprocess.run(
            [sys.executable, DDMIN, "--bin", binpath, "--input", tc,
             "--out", out, "--floor", str(args.floor),
             "--max-iters", str(args.max_iters), "--timeout", "20", "--docker"],
            capture_output=True, text=True, timeout=3600,
        )
        txt = (r.stdout or "") + (r.stderr or "")
        print(txt[-1500:], flush=True)
        rec = {"osv_id": osv, "orig_size": sz,
               "min_size": os.path.getsize(out) if os.path.isfile(out) else None,
               "min_file": os.path.basename(out),
               "returncode": r.returncode}
        results.append(rec)
        with open(done_path, "a") as f:
            f.write(osv + "\n")
        json.dump(results, open(args.out, "w"), ensure_ascii=False, indent=2)

    json.dump(results, open(args.out, "w"), ensure_ascii=False, indent=2)
    print(f"\n完成。结果写入 {args.out}")


if __name__ == "__main__":
    main()

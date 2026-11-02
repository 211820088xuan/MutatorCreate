#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""批量字节敏感性扫描：对亚型 B（块长度失控）崩溃定位「长度/计数参数所在字节」。

与 ddmin 的区别：ddmin（删块）对压缩格式无效；敏感性扫描（改单字节看崩溃是否
变化/宽度是否变化）才能定位长度字段。

用法：
    python3 tools/run_sensitivity_batch.py --out artifacts/m15_sensitivity_summary.json
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
SCAN = os.path.join(ROOT, "tools", "sensitivity_scan.py")

SUBTYPE_B_OSV = [
    "OSV-2021-639", "OSV-2021-1645", "OSV-2021-1676", "OSV-2021-1710",
    "OSV-2021-1755", "OSV-2022-33", "OSV-2022-55", "OSV-2021-1712",
    "OSV-2021-1663", "OSV-2021-27", "OSV-2021-1791", "OSV-2021-997",
    "OSV-2021-897", "OSV-2025-797",
]


def find_entry(osv: str):
    for root, dirs, files in os.walk(BYCRASH):
        if os.path.basename(root) == osv:
            binpath = None
            for f in files:
                fp = os.path.join(root, f)
                if os.access(fp, os.X_OK) and "." not in f:
                    binpath = fp
                    break
            tc = os.path.join(root, "testcase")
            if binpath and os.path.isfile(tc):
                return binpath, tc
    return None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=os.path.join(ROOT, "artifacts",
                                                  "m15_sensitivity_summary.json"))
    ap.add_argument("--max-crashes", type=int, default=20)
    ap.add_argument("--sentinel", default="0,255,127,128")
    args = ap.parse_args()

    done_path = args.out + ".done"
    done = set(l.strip() for l in open(done_path)) if os.path.isfile(done_path) else set()
    results = json.load(open(args.out)) if os.path.isfile(args.out) else []

    for osv in SUBTYPE_B_OSV:
        if osv in done:
            continue
        e = find_entry(osv)
        if not e:
            results.append({"osv_id": osv, "status": "entry_not_found"})
            with open(done_path, "a") as f:
                f.write(osv + "\n")
            continue
        binpath, tc = e
        sz = os.path.getsize(tc)
        scan_hi = min(sz, 256)      # 先扫头 256 字节（长度字段多在头部/早期 payload）
        out = os.path.join(ROOT, "artifacts", f"sens_{osv}.json")
        print(f"\n=== {osv}  size={sz} scan_range=0:{scan_hi} ===", flush=True)
        r = subprocess.run(
            [sys.executable, SCAN, "--bin", binpath, "--input", tc,
             "--docker", "--range", f"0:{scan_hi}", "--sentinel", args.sentinel,
             "--out", out],
            capture_output=True, text=True, timeout=4 * 3600,
        )
        print((r.stdout or "")[-1200:], flush=True)
        rec = {"osv_id": osv, "orig_size": sz, "result_file": os.path.basename(out),
               "returncode": r.returncode}
        if os.path.isfile(out):
            try:
                d = json.load(open(out))
                rec["base_width"] = d.get("base_width")
                rec["n_sensitive"] = len(d.get("sensitive_positions", {}))
                rec["sensitive_positions"] = list(d.get("sensitive_positions", {}).keys())
            except Exception:
                pass
        results.append(rec)
        with open(done_path, "a") as f:
            f.write(osv + "\n")
        json.dump(results, open(args.out, "w"), ensure_ascii=False, indent=2)

    json.dump(results, open(args.out, "w"), ensure_ascii=False, indent=2)
    print(f"\n完成。结果写入 {args.out}")


if __name__ == "__main__":
    main()

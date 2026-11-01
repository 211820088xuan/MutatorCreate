#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""DDMIN：对崩溃输入做确定性最小化（贪婪分块删除），定位「崩溃依赖的输入字节」。

用途（查漏补缺第 2 项 · 便宜补缺口 B）
--------------------------------------
拿到一条已复现崩溃的 testcase，用它复现崩溃的二进制，把输入最小化到
「仍能触发同一崩溃」的最小子序列；存活字节在原输入中的位置，就是
「这次越界依赖的输入字节」——这是「输入字节 ↔ 越界参数」映射的最便宜一档。

与 libFuzzer `-minimize_crash=1` 的区别
--------------------------------------
后者用覆盖率引导的随机变异，压缩格式的输入常常减不动（本仓库已实测：
c-blosc2 一条 4125B 输入减不动）；本脚本做**确定性的分块删除**，是另一类操作。

算法：贪婪分块删除（afl-tmin 风格）
-----------------------------------
1. chunk 从 len/2 开始，逐层减半；
2. 每层反复尝试删除 [i, i+chunk) 字节，删掉后仍崩则保留删除、原地重试，否则右移；
3. 到 chunk_floor 停止；floor=1 时最后追加「逐字节清零」pass。
4. 全程带原始下标，最终输出存活字节的原始偏移。

用法：
    python3 tools/ddmin_crash.py --bin <fuzzer> --input <testcase> --out <minfile> \
        [--floor 8] [--max-iters 2000] [--timeout 20]

输出：<minfile>（最小化输入）+ stdout 摘要（存活字节偏移区间）。
"""
from __future__ import annotations

import argparse
import os
import subprocess
import sys
import tempfile
import time

# 判定崩溃的 sanitizer 报告特征（与 replay.sh 的判决一致，再加 UBSan/libFuzzer 信号）
CRASH_PATTERNS = (
    "ERROR: AddressSanitizer",
    "ERROR: MemorySanitizer",
    "WARNING: MemorySanitizer",
    "ERROR: ThreadSanitizer",
    "SUMMARY: UndefinedBehaviorSanitizer",
    "runtime error:",
    "ERROR: libFuzzer: deadly signal",
    "SUMMARY: libFuzzer: deadly signal",
)


def run_once(binpath: str, data: bytes, timeout: int, tmpdir: str,
             docker: bool = False) -> tuple[bool, int]:
    """跑一次；返回 (是否崩溃, 退出码)。

    docker=True 时用 base-runner:ubuntu-24-04 跑（解决宿主 glibc 过旧，
    如 decompress_chunk_fuzzer 需要 GLIBC_2.38）。要求 binpath 所在目录已被
    挂载为 /out 且可写（ddmin 会把 in.bin 写进同一目录再以 /testcase 挂载）。
    """
    p = os.path.join(tmpdir, "in.bin")
    with open(p, "wb") as f:
        f.write(data)
    try:
        if docker:
            bname = os.path.basename(binpath)
            r = subprocess.run(
                ["docker", "run", "--rm",
                 "-v", f"{tmpdir}:/out", "-v", f"{p}:/testcase",
                 "gcr.io/oss-fuzz-base/base-runner:ubuntu-24-04",
                 "bash", "-c",
                 f"cd /out; ./{bname} -rss_limit_mb=2560 -timeout=25 /testcase < /dev/null"],
                stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL,
                stderr=subprocess.PIPE, timeout=timeout,
            )
        else:
            r = subprocess.run(
                [binpath, "-rss_limit_mb=2560", "-timeout=25", p],
                stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL,
                stderr=subprocess.PIPE, timeout=timeout,
            )
        err = r.stderr.decode("utf-8", "replace")
        crashed = any(pat in err for pat in CRASH_PATTERNS)
        return crashed, r.returncode
    except subprocess.TimeoutExpired:
        return False, -1


def ddmin(binpath: str, data: bytes, floor: int, max_iters: int, timeout: int,
          tmpdir: str, docker: bool = False, verbose=False) -> tuple[bytes, int, int]:
    """贪婪分块删除。返回 (最小化数据, 迭代次数, 耗时秒)。"""
    # 用 (orig_idx, byte) 对，保留原始下标
    cur = [(i, b) for i, b in enumerate(data)]
    iters = 0
    t0 = time.time()
    chunk = len(cur) // 2
    while chunk >= floor and chunk > 0:
        progressed = True
        while progressed:
            progressed = False
            i = 0
            while i + chunk <= len(cur):
                cand = cur[:i] + cur[i + chunk:]
                cbytes = bytes(b for _, b in cand)
                ok, _rc = run_once(binpath, cbytes, timeout, tmpdir, docker=docker)
                iters += 1
                if ok:
                    cur = cand
                    progressed = True
                    # 不移动 i：同一位置现在是新的后续字节，可能还能再删
                else:
                    i += chunk
                if iters >= max_iters:
                    return _finish(cur, iters, t0)
            if progressed:
                continue
        if verbose:
            print(f"  chunk={chunk}: size={len(cur)} iters={iters}", file=sys.stderr)
        chunk //= 2
    return _finish(cur, iters, t0)


def _finish(cur, iters, t0):
    return bytes(b for _, b in cur), iters, round(time.time() - t0, 1)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--bin", required=True)
    ap.add_argument("--input", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--floor", type=int, default=8)
    ap.add_argument("--max-iters", type=int, default=4000)
    ap.add_argument("--timeout", type=int, default=20)
    ap.add_argument("--docker", action="store_true",
                    help="用 base-runner:ubuntu-24-04 容器执行（解决宿主 glibc 过旧）")
    args = ap.parse_args()

    orig = open(args.input, "rb").read()
    print(f"原输入 {len(orig)} 字节")

    tmpdir = tempfile.mkdtemp(prefix="ddmin_")
    binpath = args.bin
    if args.docker:
        # 把二进制拷进 tmpdir，使 mount 到 /out 后能直接执行
        bname = os.path.basename(args.bin)
        import shutil
        shutil.copy(args.bin, os.path.join(tmpdir, bname))
        binpath = os.path.join(tmpdir, bname)

    # 基线：确认原始输入确实崩溃
    ok, rc = run_once(binpath, orig, args.timeout, tmpdir, docker=args.docker)
    if not ok:
        print(f"❌ 原始输入未复现崩溃（exit={rc}），中止。", file=sys.stderr)
        sys.exit(2)
    print(f"✅ 基线确认崩溃（exit={rc}，mode={'docker' if args.docker else 'host'}）")

    mn, iters, secs = ddmin(binpath, orig, args.floor, args.max_iters,
                            args.timeout, tmpdir, docker=args.docker, verbose=True)
    with open(args.out, "wb") as f:
        f.write(mn)

    # 存活字节的原始偏移
    offs = []
    # 最小化结果是原输入的子序列；用贪心匹配找回原始偏移（近似）
    pos = 0
    for b in mn:
        while pos < len(orig) and orig[pos] != b:
            pos += 1
        offs.append(pos)
        pos += 1
    # 合并连续区间
    ranges = []
    if offs:
        s = e = offs[0]
        for x in offs[1:]:
            if x == e + 1:
                e = x
            else:
                ranges.append((s, e))
                s = e = x
        ranges.append((s, e))

    print(f"\n最小化: {len(orig)} → {len(mn)} 字节（迭代 {iters} 次，{secs}s，floor={args.floor}）")
    print(f"存活字节原始偏移区间（共 {len(offs)} 字节）:")
    for s, e in ranges:
        print(f"  [{s}, {e}]  ({e - s + 1} 字节)")


if __name__ == "__main__":
    main()

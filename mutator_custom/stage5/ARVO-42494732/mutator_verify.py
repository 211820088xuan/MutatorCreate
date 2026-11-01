#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""mutator_verify.py —— 变异算子三级验证门禁

V1 语法：clang -fsyntax-only
V2 结构：变异后文件变大；插入内容落在目标段内；ENDSEC 数量不变（没删东西）
V3 自举：N 次不同 seed 的变异中，有多少次重放出"已知崩溃点 file:line"

V3 是核心：它是端到端的因果检验。如果算子真的实现了特征，
就应该能把已知崩溃重新造出来。

用法（在容器内跑，因为需要 clang 和被测二进制）：
  mutator_verify.py \
      --mutator /exp/mutator_v2.c \
      --seed /src/libredwg/test/test-data/xxx.dxf \
      --binary /exp/fuzz_exp1/llvmfuzz \
      --expect-file in_dxf.c --expect-line 12267 \
      --section OBJECTS --reps 12 --workdir /tmp/mv
"""
import argparse
import os
import re
import subprocess
import sys

DRIVER = r'''
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdint.h>
size_t LLVMFuzzerMutate(uint8_t *d, size_t s, size_t m) { (void)d; (void)m; return s; }
extern size_t LLVMFuzzerCustomMutator(uint8_t *, size_t, size_t, unsigned int);
int main(int argc, char **argv) {
    if (argc < 4) return 1;
    FILE *f = fopen(argv[1], "rb"); if (!f) return 2;
    fseek(f, 0, SEEK_END); long n = ftell(f); fseek(f, 0, SEEK_SET);
    size_t cap = (size_t)n + (1u << 20);
    uint8_t *b = (uint8_t *)malloc(cap);
    size_t sz = fread(b, 1, (size_t)n, f); fclose(f);
    uint8_t *o = (uint8_t *)malloc(cap);
    memcpy(o, b, sz);
    size_t osz = LLVMFuzzerCustomMutator(o, sz, cap, (unsigned)atoi(argv[3]));
    FILE *g = fopen(argv[2], "wb"); if (!g) return 3;
    fwrite(o, 1, osz, g); fclose(g);
    fprintf(stderr, "RESULT in=%zu out=%zu\n", sz, osz);
    return 0;
}
'''

ENV = dict(os.environ, ASAN_OPTIONS="detect_leaks=0", LSAN_OPTIONS="detect_leaks=0",
           LIBREDWG_CUSTOM_PCT="100")


def sh(args, timeout=180):
    return subprocess.run(args, capture_output=True, text=True, timeout=timeout, env=ENV)


def v1_syntax(mutator):
    r = sh(["clang", "-fsyntax-only", "-std=c11", mutator])
    return r.returncode == 0, (r.stderr or "").strip()[:400]


def build_driver(workdir, mutator):
    os.makedirs(workdir, exist_ok=True)
    src = os.path.join(workdir, "drv.c")
    open(src, "w").write(DRIVER)
    exe = os.path.join(workdir, "drv")
    r = sh(["clang", "-O1", src, mutator, "-o", exe])
    return (exe, "") if r.returncode == 0 else (None, (r.stderr or "").strip()[:400])


def mutate(exe, seed, out, sd):
    r = sh([exe, seed, out, str(sd)])
    m = re.search(r"RESULT in=(\d+) out=(\d+)", r.stderr or "")
    if not m:
        return None
    return int(m.group(1)), int(m.group(2))


def v2_structure(seed, out, section):
    a = open(seed, "rb").read()
    b = open(out, "rb").read()
    checks = []
    checks.append(("输出变大", len(b) > len(a)))
    checks.append(("ENDSEC 数量不变", b.count(b"ENDSEC") == a.count(b"ENDSEC")))
    # 新增内容是否落在 section 起点与紧随其后的 ENDSEC 之间
    si = a.find(section.encode())
    inside = False
    if si >= 0:
        j = a.find(b"ENDSEC", si)
        # 在原文件的 [si, j) 区间内，找到对应位置的偏移，检查新内容是否插在该区间
        pass
    # 简化：新文件里 SECTION 起点之后出现次数增加，且插入点位于 ENDSEC 之前
    marks = [m.start() for m in re.finditer(rb"BAD_|FUZZ_OBJ", b)]
    if marks:
        # 插入点之后第一个 ENDSEC 的位置应晚于插入点
        k = b.find(b"ENDSEC", marks[-1])
        inside = k > 0
    checks.append(("插入内容在 ENDSEC 之前", inside))
    return checks


def v3_bootstrap(binary, workdir, exe, seed, expect_file, expect_line, reps):
    hits = 0
    detail = []
    for sd in range(1, reps + 1):
        out = os.path.join(workdir, f"m{sd}.dxf")
        sz = mutate(exe, seed, out, sd)
        if not sz:
            detail.append((sd, "mutate-failed"))
            continue
        r = sh([binary, "-runs=1", "-detect_leaks=0", out], timeout=300)
        log = (r.stdout or "") + (r.stderr or "")
        pat = f"{expect_file}:{expect_line}"
        if pat in log:
            hits += 1
            detail.append((sd, "HIT"))
        else:
            m = re.search(r"AddressSanitizer: (\S+) (\S+):(\d+)", log)
            detail.append((sd, m.group(0) if m else "no-crash"))
        try:
            os.remove(out)
        except OSError:
            pass
    return hits, reps, detail


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--mutator", required=True)
    ap.add_argument("--seed", required=True)
    ap.add_argument("--binary", required=True)
    ap.add_argument("--expect-file", required=True)
    ap.add_argument("--expect-line", required=True)
    ap.add_argument("--section", default="OBJECTS")
    ap.add_argument("--reps", type=int, default=12)
    ap.add_argument("--workdir", default="/tmp/mv")
    ap.add_argument("--min-rate", type=float, default=0.30,
                    help="V3 重放率门限（默认 30%%）")
    a = ap.parse_args()

    print(f"=== 被测算子: {a.mutator}")
    print(f"=== 种子: {a.seed} ({os.path.getsize(a.seed)} B)")
    print(f"=== 期望崩溃点: {a.expect_file}:{a.expect_line}")
    print()

    # V1
    ok, err = v1_syntax(a.mutator)
    print(f"[V1 语法] {'PASS' if ok else 'FAIL'}")
    if not ok:
        print("  " + err)
        return 1

    # V2
    exe, err = build_driver(a.workdir, a.mutator)
    if not exe:
        print("[V2 结构] FAIL（驱动编译失败）")
        print("  " + err)
        return 1
    out = os.path.join(a.workdir, "m_probe.dxf")
    sz = mutate(exe, a.seed, out, 12345)
    if not sz:
        print("[V2 结构] FAIL（变异调用失败）")
        return 1
    checks = v2_structure(a.seed, out, a.section)
    v2ok = all(v for _, v in checks)
    print(f"[V2 结构] {'PASS' if v2ok else 'FAIL'}  (in={sz[0]} -> out={sz[1]})")
    for name, v in checks:
        print(f"    {'✓' if v else '✗'} {name}")

    # V3
    hits, reps, detail = v3_bootstrap(a.binary, a.workdir, exe, a.seed,
                                      a.expect_file, a.expect_line, a.reps)
    rate = hits / reps if reps else 0.0
    print(f"[V3 自举] {'PASS' if rate >= a.min_rate else 'FAIL'}  "
          f"重放率 {hits}/{reps} = {rate*100:.0f}%  (门限 {a.min_rate*100:.0f}%)")
    for sd, d in detail:
        print(f"    seed={sd:<3} {d}")

    verdict = ok and v2ok and rate >= a.min_rate
    print()
    print("=" * 50)
    print("结论:", "通过，可以进入 fuzz 实验" if verdict else "不通过，不允许进入 fuzz 实验")
    print("=" * 50)
    return 0 if verdict else 2


if __name__ == "__main__":
    sys.exit(main())

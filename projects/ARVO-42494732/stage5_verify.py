#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""stage5_verify.py —— 五策略变异算子的四级门禁

V1 语法：clang -fsyntax-only -std=c11
V2 结构：每个策略单独强制运行 → 输出不缩小 / 不超过 MaxSize / ENDSEC 数量不变
V3 自举：每个策略单独强制运行 N 次 → 统计重放"已知崩溃点 file:line"的比率
V4 权重：随机 Seed 跑 M 次 → 用 TRACE 文件统计 default 与 5 个策略的分布
        期望 default 60%，每个策略 8%

在容器内运行（需要 clang 与被测二进制）。用法：

  python3 stage5_verify.py \
      --mutator /exp/mutator.c \
      --seed /exp/seeds/seed_object.dxf \
      --binary /exp/fuzz_exp/llvmfuzz \
      --expect-file in_dxf.c --expect-line 12267 \
      --strategies 5 --reps 12 --weight-samples 2000
"""
import argparse
import os
import re
import collections
import subprocess
import sys

DRIVER = r'''
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdint.h>
size_t LLVMFuzzerMutate(uint8_t *d, size_t s, size_t m) { (void)m; return s; }
extern size_t LLVMFuzzerCustomMutator(uint8_t *, size_t, size_t, unsigned int);
int main(int argc, char **argv) {
    if (argc < 4) return 1;
    FILE *f = fopen(argv[1], "rb"); if (!f) return 2;
    fseek(f, 0, SEEK_END); long n = ftell(f); fseek(f, 0, SEEK_SET);
    size_t cap = (size_t)n + (1u << 20);
    uint8_t *b = (uint8_t *)malloc(cap);
    if (!b) return 4;
    size_t sz = fread(b, 1, (size_t)n, f); fclose(f);
    uint8_t *o = (uint8_t *)malloc(cap);
    if (!o) return 4;
    memcpy(o, b, sz);
    size_t osz = LLVMFuzzerCustomMutator(o, sz, cap, (unsigned)atoi(argv[3]));
    if (osz > cap) { fprintf(stderr, "RESULT OVERFLOW %zu > %zu\n", osz, cap); return 5; }
    FILE *g = fopen(argv[2], "wb"); if (!g) return 3;
    fwrite(o, 1, osz, g); fclose(g);
    fprintf(stderr, "RESULT in=%zu out=%zu\n", sz, osz);
    return 0;
}
'''


def sh(args, timeout=300, env_extra=None):
    env = dict(os.environ, ASAN_OPTIONS="detect_leaks=0", LSAN_OPTIONS="detect_leaks=0")
    if env_extra:
        env.update(env_extra)
    return subprocess.run(args, capture_output=True, text=True, timeout=timeout, env=env)


def v1_syntax(mutator):
    r = sh(["clang", "-fsyntax-only", "-std=c11", mutator])
    return r.returncode == 0, (r.stderr or "").strip()[:600]


def build_driver(workdir, mutator):
    os.makedirs(workdir, exist_ok=True)
    src = os.path.join(workdir, "drv.c")
    open(src, "w").write(DRIVER)
    exe = os.path.join(workdir, "drv")
    r = sh(["clang", "-O1", "-std=c11", src, mutator, "-o", exe])
    return (exe, "") if r.returncode == 0 else (None, (r.stderr or "").strip()[:600])


def mutate(exe, seed, out, sd, env_extra=None):
    r = sh([exe, seed, out, str(sd)], env_extra=env_extra)
    m = re.search(r"RESULT in=(\d+) out=(\d+)", r.stderr or "")
    if not m:
        return None
    return int(m.group(1)), int(m.group(2))


def v3_one(exe, binary, seed, workdir, sd, k, expect_file, expect_line):
    out = os.path.join(workdir, f"strat{k}_s{sd}.dxf")
    env = {"LIBREDWG_FORCE_STRATEGY": str(k)}
    sz = mutate(exe, seed, out, sd, env)
    if not sz:
        return "mutate-failed"
    if sz[0] == sz[1] and open(seed, "rb").read() == open(out, "rb").read():
        os.remove(out)
        return "not-applicable"
    r = sh([binary, "-runs=1", "-detect_leaks=0", out], timeout=300)
    log = (r.stdout or "") + (r.stderr or "")
    # 只认 ASan SUMMARY 行里的 top frame，避免任意栈帧命中造成误判
    pat = rf"SUMMARY: AddressSanitizer: \S+ .*{re.escape(expect_file)}:{expect_line}(:|\b)"
    if re.search(pat, log):
        res = "HIT"
    else:
        m = re.search(r"SUMMARY: AddressSanitizer: (\S+) (\S+):(\d+)", log)
        res = f"other:{m.group(2)}:{m.group(3)}" if m else "no-crash"
    try:
        os.remove(out)
    except OSError:
        pass
    return res


def v4_weights(exe, seed, workdir, samples):
    trace = os.path.join(workdir, "trace.txt")
    if os.path.exists(trace):
        os.remove(trace)
    out = os.path.join(workdir, "w_probe.dxf")
    env = {"LIBREDWG_TRACE_FILE": trace}
    for sd in range(1, samples + 1):
        sh([exe, seed, out, str(sd)], env_extra=env)
    if not os.path.exists(trace):
        return None, "未生成 trace 文件（未实现 LIBREDWG_TRACE_FILE？）"
    c = collections.Counter()
    for ln in open(trace, encoding="utf-8", errors="ignore"):
        ln = ln.strip()
        if ln:
            c[ln] += 1
    total = sum(c.values())
    return (c, total), ""


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--mutator", required=True)
    ap.add_argument("--seed", required=True)
    ap.add_argument("--binary", default=None)
    ap.add_argument("--expect-file", default="in_dxf.c")
    ap.add_argument("--expect-line", default="12267")
    ap.add_argument("--strategies", type=int, default=5)
    ap.add_argument("--reps", type=int, default=12)
    ap.add_argument("--weight-samples", type=int, default=2000)
    ap.add_argument("--workdir", default="/tmp/sv")
    ap.add_argument("--min-applicable", type=float, default=0.30,
                    help="每个策略的最低可适用率（默认 30%%）")
    ap.add_argument("--min-hit", type=float, default=0.30,
                    help="必须命中的策略的最低自举命中率（默认 30%%）")
    ap.add_argument("--require-hit", default="0",
                    help="哪些策略必须命中已知崩溃（逗号分隔）。其余策略为探索性，"
                         "只检查可适用性与结构。默认 '0'（只有 strat0 有已知崩溃证据）")
    a = ap.parse_args()

    print(f"=== 算 子: {a.mutator}")
    print(f"=== 种 子: {a.seed} ({os.path.getsize(a.seed)} B)")
    print(f"=== 期望点: {a.expect_file}:{a.expect_line}")
    require_hit = {int(x) for x in a.require_hit.split(",") if x.strip().isdigit()}
    print(f"=== 策略数: {a.strategies}   必须命中: {sorted(require_hit)}")
    print()

    fail = []

    # ── V1 ──
    ok, err = v1_syntax(a.mutator)
    print(f"[V1 语法] {'PASS' if ok else 'FAIL'}")
    if not ok:
        print("  " + err)
        return 1
    exe, err = build_driver(a.workdir, a.mutator)
    if not exe:
        print("[V1 语法] FAIL（驱动链接失败）")
        print("  " + err)
        return 1

    # ── V2 每个策略的结构检查 ──
    print(f"\n[V2 结构] 逐策略检查")
    seed_b = open(a.seed, "rb").read()
    v2_all = True
    for k in range(a.strategies):
        out = os.path.join(a.workdir, f"v2_{k}.dxf")
        sz = mutate(exe, a.seed, out, 100 + k, {"LIBREDWG_FORCE_STRATEGY": str(k)})
        if not sz:
            print(f"  strat{k}: FAIL（变异调用失败）")
            v2_all = False
            continue
        b = open(out, "rb").read()
        c1 = len(b) >= len(seed_b)
        c2 = b.count(b"ENDSEC") == seed_b.count(b"ENDSEC")
        c3 = sz[1] <= sz[0] + (1 << 20)
        tag = "not-applicable" if b == seed_b else ("grown" if len(b) > len(seed_b) else "same-size")
        good = c1 and c2 and c3
        v2_all = v2_all and good
        print(f"  strat{k}: {'PASS' if good else 'FAIL'}  in={sz[0]} out={sz[1]} [{tag}] "
              f"不缩小={'✓' if c1 else '✗'} ENDSEC不变={'✓' if c2 else '✗'} 不超限={'✓' if c3 else '✗'}")
        os.remove(out)
    if not v2_all:
        fail.append("V2")

    # ── V3 每个策略的自举率 ──
    if a.binary and os.path.exists(a.binary):
        print(f"\n[V3 自举] 逐策略，每个 {a.reps} 次")
        for k in range(a.strategies):
            res = [v3_one(exe, a.binary, a.seed, a.workdir, sd, k,
                          a.expect_file, a.expect_line) for sd in range(1, a.reps + 1)]
            hits = sum(1 for r in res if r == "HIT")
            na = sum(1 for r in res if r == "not-applicable")
            appl = (a.reps - na) / a.reps if a.reps else 0.0
            rate = hits / a.reps if a.reps else 0.0
            must = k in require_hit
            good = appl >= a.min_applicable and (rate >= a.min_hit if must else True)
            if not good:
                fail.append(f"V3-strat{k}")
            tag = "必须命中" if must else "探索性（只看可适用性）"
            others = collections.Counter(r for r in res if r.startswith("other:"))
            print(f"  strat{k}: {'PASS' if good else 'FAIL'}  可适用 {a.reps-na}/{a.reps}={appl*100:.0f}%  "
                  f"命中 {hits}/{a.reps}={rate*100:.0f}%  [{tag}]"
                  + (f"  其他崩溃={dict(others)}" if others else ""))
    else:
        print(f"\n[V3 自举] SKIP（未提供可用二进制）")

    # ── V4 权重分布 ──
    print(f"\n[V4 权重] {a.weight_samples} 次随机 Seed")
    w, err = v4_weights(exe, a.seed, a.workdir, a.weight_samples)
    if w is None:
        print(f"  FAIL：{err}")
        fail.append("V4")
    else:
        c, total = w
        exp_default = 60.0
        exp_each = 40.0 / a.strategies
        print(f"  样本 {total}")
        d = c.get("D", 0) / total * 100
        print(f"  default: {c.get('D',0):>5} = {d:5.1f}%  (期望 {exp_default:.0f}%)")
        w_ok = abs(d - exp_default) <= 4.0
        for k in range(a.strategies):
            cnt = c.get(f"S{k}", 0) + c.get(f"F{k}", 0)
            p = cnt / total * 100
            print(f"  strat{k} : {cnt:>5} = {p:5.1f}%  (期望 {exp_each:.0f}%)"
                  f"  [S={c.get(f'S{k}',0)} F={c.get(f'F{k}',0)}]")
            if abs(p - exp_each) > 2.5:
                w_ok = False
        unknown = {k: v for k, v in c.items() if k != "D" and not re.fullmatch(r"[SF]\d", k)}
        if unknown:
            print(f"  ⚠ 未知 trace 标记: {unknown}")
        if not w_ok:
            fail.append("V4")
        print(f"  → {'PASS' if w_ok else 'FAIL'}")

    # ── 结论 ──
    print()
    print("=" * 56)
    if fail:
        print(f"结论：不通过（{', '.join(fail)}）→ 不允许进入 fuzz 实验")
    else:
        print("结论：通过，可以进入 fuzz 实验")
    print("=" * 56)
    return 0 if not fail else 2


if __name__ == "__main__":
    sys.exit(main())

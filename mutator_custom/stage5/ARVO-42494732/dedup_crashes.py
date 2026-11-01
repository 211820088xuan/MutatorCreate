#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""dedup_crashes.py —— 按 ASan 崩溃点去重，统计每个模式的唯一崩溃数与类型分布

libFuzzer 的 `crash-<sha1>` 是按**输入**命名的：同一个 bug 可能产生上百个不同输入。
本脚本把每个崩溃输入重放一次，抽 `SUMMARY: AddressSanitizer: <type> <file>:<line>`，
按 `(type, file:line)` 归并，得到「唯一崩溃」。

用法（容器内）: python3 /exp/dedup_crashes.py [实验根目录，默认 /exp/fuzz_exp]
"""
import collections
import json
import os
import re
import subprocess
import sys

ROOT = sys.argv[1] if len(sys.argv) > 1 else '/exp/fuzz_exp'
BIN = '/exp/fuzz_exp/llvmfuzz'
MODES = ['default_1', 'default_2', 'default_3', 'custom_1', 'custom_2', 'custom_3']
RE_SUMMARY = re.compile(r'SUMMARY: AddressSanitizer: (\S+) (\S+?):(\d+)')

ENV = dict(os.environ, ASAN_OPTIONS='detect_leaks=0', LSAN_OPTIONS='detect_leaks=0')


def classify(path):
    try:
        r = subprocess.run([BIN, '-runs=1', path], capture_output=True,
                           text=True, timeout=120, env=ENV)
    except subprocess.TimeoutExpired:
        return ('TIMEOUT', '?', 0)
    log = (r.stdout or '') + (r.stderr or '')
    m = RE_SUMMARY.search(log)
    if m:
        return (m.group(1), os.path.basename(m.group(2)), int(m.group(3)))
    if 'AddressSanitizer' in log:
        return ('ASAN_OTHER', '?', 0)
    return ('NO_CRASH', '?', 0)


def crash_dir(d):
    """crash 文件可能在 run 根目录，也可能在 crash/ 子目录（新布局）"""
    c = os.path.join(d, "crash")
    return c if os.path.isdir(c) else d


result = {}
for mode in MODES:
    d = os.path.join(ROOT, mode)
    if not os.path.isdir(d):
        continue
    files = sorted(f for f in os.listdir(crash_dir(d)) if f.startswith('crash-'))
    kinds = collections.Counter()
    per = {}
    for i, f in enumerate(files, 1):
        k = classify(os.path.join(crash_dir(d), f))
        kinds[k] += 1
        per.setdefault(f'{k[0]} @ {k[1]}:{k[2]}', []).append(f)
        if i % 20 == 0 or i == len(files):
            print(f'  {mode}: {i}/{len(files)}', flush=True)
    result[mode] = {
        'n_files': len(files),
        'n_unique': len(per),
        'kinds': {f'{k[0]} @ {k[1]}:{k[2]}': v for k, v in
                  sorted(kinds.items(), key=lambda kv: -kv[1])},
        'files': per,
    }
    print(f'{mode}: {len(files)} 个崩溃文件 → {len(per)} 个唯一崩溃点', flush=True)

print('\n' + '=' * 78)
print(f"{'实例':<12}{'崩溃文件':>10}{'唯一崩溃点':>12}")
print('-' * 78)
for m in MODES:
    if m in result:
        print(f"{m:<12}{result[m]['n_files']:>10}{result[m]['n_unique']:>12}")

print('\n=== 各模式唯一的崩溃点集合 ===')
for grp, modes in (('default', ['default_1', 'default_2', 'default_3']),
                   ('custom', ['custom_1', 'custom_2', 'custom_3'])):
    union = set()
    for m in modes:
        if m in result:
            union |= set(result[m]['kinds'])
    print(f'\n[{grp}] 三次运行合并去重后：{len(union)} 个唯一崩溃点')
    cnt = collections.Counter()
    for m in modes:
        if m in result:
            for k in result[m]['kinds']:
                cnt[k] += 1
    for k, c in sorted(cnt.items(), key=lambda kv: (-kv[1], kv[0])):
        print(f'  {c}/3 次出现  {k}')

json.dump(result, open(os.path.join(ROOT, 'crash_dedup.json'), 'w'),
          ensure_ascii=False, indent=1)
print(f"\n已写出 {os.path.join(ROOT, 'crash_dedup.json')}")

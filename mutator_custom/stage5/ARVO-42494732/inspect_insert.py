#!/usr/bin/env python3
# 检查每个策略把字节插到了哪里
import subprocess, os, sys

seed = '/exp/seeds/v.dxf'
drv = '/tmp/sv/drv'
a = open(seed, 'rb').read()

oi = a.find(b'OBJECTS')
oe = a.find(b'ENDSEC', oi) if oi >= 0 else -1
print(f"种子 {len(a)} B   OBJECTS 起点={oi}   其 ENDSEC 起点={oe}")
print()

for k in range(5):
    out = f'/tmp/sv/insp_{k}.dxf'
    env = dict(os.environ, LIBREDWG_FORCE_STRATEGY=str(k))
    subprocess.run([drv, seed, out, '7'], capture_output=True, text=True, env=env)
    if not os.path.exists(out):
        print(f"strat{k}: 未产出文件")
        continue
    b = open(out, 'rb').read()

    i = 0
    while i < min(len(a), len(b)) and a[i] == b[i]:
        i += 1
    extra = len(b) - len(a)
    ins = b[i:i + extra] if extra > 0 else b''

    if i >= oe and oe > 0:
        where = 'OBJECTS 段之后'
    elif oi < i < oe:
        where = 'OBJECTS 段内 ✓'
    else:
        where = 'OBJECTS 之前'

    print(f"strat{k}: in={len(a)} out={len(b)}  插入 {len(ins)}B @ 偏移 {i}  [{where}]")
    print(f"         插入内容: {ins!r}")
    print(f"         插入点前 30B: {a[max(0,i-30):i]!r}")
    print()

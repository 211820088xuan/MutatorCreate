"""用 drv.c 那套驱动，拿 1000 个 seed 生成变异产物（custom 或 default）。"""
import subprocess, sys, os
d = '/tmp/cap'
drv, seed, n, outdir = sys.argv[1], sys.argv[2], int(sys.argv[3]), sys.argv[4]
os.makedirs(outdir, exist_ok=True)
# drv 的用法: drv <seed> <N> <outbin>  只写最后一个产物；改造：逐个 seed 单独调用
ok = 0
for s in range(n):
    dst = os.path.join(outdir, f'm{s:04d}.bin')
    r = subprocess.run([drv, seed, '1', dst], capture_output=True)
    if os.path.isfile(dst) and os.path.getsize(dst) > 0:
        ok += 1
print(f'  生成 {ok}/{n} 个产物 -> {outdir}')

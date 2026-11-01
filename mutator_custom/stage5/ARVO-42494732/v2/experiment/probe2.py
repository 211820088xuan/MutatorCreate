import os, subprocess, time, glob
BIN = "/exp/v2/experiment/llvmfuzz"
ENV = {**os.environ, "ASAN_OPTIONS": "detect_leaks=0"}

def wall(path, runs):
    t0 = time.time()
    subprocess.run([BIN, f"-runs={runs}", path], capture_output=True, text=True,
                   env=ENV, timeout=900)
    return time.time() - t0

def per_exec(path, runs=5000):
    base = wall(path, 1)          # 启动 + 1 次
    tot = wall(path, runs)
    return (tot - base) / (runs - 1) * 1000, os.path.getsize(path)

print("  输入                                    大小     单次执行 ms")
cases = ["/exp/seeds/sample_r14.dxf", "/exp/seeds/v.dxf"]
cases += sorted(glob.glob("/exp/v2/experiment/custom/corpus/*"), key=os.path.getsize)[-3:]
cases += sorted(glob.glob("/exp/v2/experiment/default/corpus/*"), key=os.path.getsize)[-3:]
for p in cases:
    ms, sz = per_exec(p)
    tag = "seed" if "/seeds/" in p else ("custom" if "/custom/" in p else "default")
    print(f"  [{tag:<7}] {os.path.basename(p)[:32]:<34}{sz:>8}  {ms:>10.3f}")

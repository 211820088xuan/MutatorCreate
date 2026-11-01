import os, subprocess, time, glob
BIN = "/exp/v2/experiment/llvmfuzz"
ENV = {**os.environ, "ASAN_OPTIONS": "detect_leaks=0"}

def t(path, runs=200):
    t0 = time.time()
    subprocess.run([BIN, f"-runs={runs}", path], capture_output=True, text=True,
                   env=ENV, timeout=600)
    return (time.time() - t0) / runs * 1000, os.path.getsize(path)

print("  输入                                    大小      每执行 ms")
for p in ["/exp/seeds/sample_r14.dxf", "/exp/seeds/sample_2018.dxf", "/exp/seeds/v.dxf"]:
    ms, sz = t(p); print(f"  {os.path.basename(p):<38}{sz:>8}  {ms:>8.2f}")
print("  --- custom corpus（算子产物）---")
for p in sorted(glob.glob("/exp/v2/experiment/custom/corpus/*"), key=os.path.getsize)[-4:]:
    ms, sz = t(p); print(f"  {os.path.basename(p)[:36]:<38}{sz:>8}  {ms:>8.2f}")
print("  --- default corpus ---")
for p in sorted(glob.glob("/exp/v2/experiment/default/corpus/*"), key=os.path.getsize)[-4:]:
    ms, sz = t(p); print(f"  {os.path.basename(p)[:36]:<38}{sz:>8}  {ms:>8.2f}")

import os, subprocess, time
BIN="/exp/v2/experiment/llvmfuzz"; ENV={**os.environ,"ASAN_OPTIONS":"detect_leaks=0"}
def per(path, runs=3000):
    t0=time.time(); subprocess.run([BIN,f"-runs={runs}",path],capture_output=True,text=True,env=ENV,timeout=900); tot=time.time()-t0
    t0=time.time(); subprocess.run([BIN,"-runs=1",path],capture_output=True,text=True,env=ENV,timeout=900); base=time.time()-t0
    return (tot-base)/(runs-1)*1000
for p in ("probe_seed.dxf","probe_code.dxf","probe_value.dxf"):
    print(f"  {p:<18} {per('/exp/v2/experiment/'+p):>8.3f} ms/exec")

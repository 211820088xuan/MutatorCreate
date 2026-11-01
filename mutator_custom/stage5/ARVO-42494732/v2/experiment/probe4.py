import os, subprocess, time
BIN="/exp/v2/experiment/llvmfuzz"; ENV={**os.environ,"ASAN_OPTIONS":"detect_leaks=0"}
for k in range(3):
    p=f"/exp/v2/experiment/cand{k}.dxf"
    t0=time.time(); subprocess.run([BIN,"-runs=1",p],capture_output=True,text=True,env=ENV); dt=time.time()-t0
    print(f"  cand{k}: {dt*1000:8.1f} ms（含进程启动+ASan 初始化）")

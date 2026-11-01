#!/usr/bin/env python3
# analyze_run_3h.py —— 对单次运行做重放分析：记录覆盖边、覆盖率、全面崩溃信息
# usage: python3 analyze_run_3h.py <mode> <suffix>
import sys, subprocess, glob, os, re

BIN = "/root/gyx/mutator_create/mutator_custom/blosc2_bins/decompress_chunk_nocov"
BASE = "/root/gyx/mutator_create/mutator_custom/fuzz_exp_3h"

mode, suffix = sys.argv[1], sys.argv[2]
run_dir = f"{BASE}/{mode}_{suffix}"
replay_dir = f"{BASE}/replay/{mode}_{suffix}"
os.makedirs(f"{replay_dir}/crash", exist_ok=True)

# ---------- 1. 覆盖边（-merge=1 控制文件，ObservedPCs 口径，无计数器回绕） ----------
cf = f"{replay_dir}/merge_control.cf"
mout = f"/tmp/mout_{mode}_{suffix}"
os.makedirs(mout, exist_ok=True)
subprocess.run([BIN, "-merge=1", f"-merge_control_file={cf}", mout, f"{run_dir}/corpus/"],
               capture_output=True, timeout=1800)
cov = set()
for line in open(cf, errors='ignore'):
    if line.startswith('COV '):
        cov |= {int(x) for x in line.split()[2:] if x.isdigit()}

with open(f"{replay_dir}/edges.txt", "w") as f:
    f.write("\n".join(map(str, sorted(cov))) + "\n")
with open(f"{replay_dir}/coverage.txt", "w") as f:
    f.write(f"covered_edges={len(cov)}\n")
    f.write(f"total_edges=44119\n")
    f.write(f"coverage_rate={len(cov)/44119*100:.4f}%\n")

# ---------- 2. 崩溃信息 ----------
crashes = []
for cf_path in sorted(glob.glob(f"{run_dir}/art/*")):
    if not os.path.isfile(cf_path):
        continue
    name = os.path.basename(cf_path)
    data = open(cf_path, 'rb').read()
    r = subprocess.run([BIN, "-runs=1", cf_path], capture_output=True, text=True, timeout=60)
    log = r.stdout + r.stderr
    with open(f"{replay_dir}/crash/{name}.log", "w") as f:
        f.write(log)

    m_type = re.search(r"ERROR: AddressSanitizer: (\S+)", log)
    m_rw = re.search(r"(READ|WRITE) of size (\d+)", log)
    top = None
    for ln in log.splitlines():
        if re.search(r"#\d+ 0x[0-9a-f]+ in \w+ .*\.(c|h):\d+", ln):
            top = ln.split(' in ', 1)[1] if ' in ' in ln else ln
            break
    crashes.append({
        "name": name,
        "size": len(data),
        "type": m_type.group(1) if m_type else "?",
        "rw": (m_rw.group(1), int(m_rw.group(2))) if m_rw else ("?", "?"),
        "top": top,
        "codec_flag": data[2] if len(data) >= 3 else None,
        "hex_head": data[:16].hex(),
    })

with open(f"{replay_dir}/crash_report.txt", "w") as f:
    f.write(f"crash_count={len(crashes)}\n")
    for i, c in enumerate(crashes):
        f.write(f"\n[{i+1}] {c['name']}\n")
        f.write(f"  type={c['type']}  {c['rw'][0]} size={c['rw'][1]}\n")
        f.write(f"  input_size={c['size']}  codec_flag=0x{c['codec_flag']:02x}\n")
        f.write(f"  hex_head={c['hex_head']}\n")
        f.write(f"  top={c['top']}\n")

print(f"{mode}_{suffix}: edges={len(cov)}  crashes={len(crashes)}")

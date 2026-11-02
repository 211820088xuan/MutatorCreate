#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""analyze_run.py —— 单次运行的重放分析（对应参考实现的 analyze_run_3h.py）

产出（目录结构同参考实现）：
  fuzz_exp/replay/<mode>_<suffix>/coverage.txt       covered_edges / total_edges / coverage_rate
  fuzz_exp/replay/<mode>_<suffix>/edges.txt          每条被覆盖的边
  fuzz_exp/replay/<mode>_<suffix>/merge_control.cf   libFuzzer 的 merge 控制文件
  fuzz_exp/replay/<mode>_<suffix>/crash_report.txt   crash_count + 每个崩溃的详情
  fuzz_exp/replay/<mode>_<suffix>/crash/<name>.log   每个崩溃的重放日志

用法: analyze_run.py <mode> <suffix>
"""
import sys, subprocess, glob, os, re

BIN = "/exp/fuzz_exp2/llvmfuzz"
BASE = "/exp/fuzz_exp2"

mode, suffix = sys.argv[1], sys.argv[2]
run_dir = f"{BASE}/{mode}_{suffix}"
replay_dir = f"{BASE}/replay/{mode}_{suffix}"
os.makedirs(f"{replay_dir}/crash", exist_ok=True)

# ---------- 1. 覆盖边（-merge=1 的 COV 行，ObservedPCs 口径） ----------
cf = f"{replay_dir}/merge_control.cf"
mout = f"/tmp/mout_{mode}_{suffix}"

# 关键：必须清掉旧的 merge 控制文件和输出目录。
# 否则 libFuzzer 会从上次的进度续跑，导致 covered_edges 结果不可复现
# （实测出现过 merge 覆盖 > 进程实际覆盖的荒谬结果）。
for _p in (cf,):
    if os.path.exists(_p):
        os.remove(_p)
        print(f"  [clean] 删除旧控制文件 {_p}")
if os.path.isdir(mout):
    shutil.rmtree(mout)
os.makedirs(mout, exist_ok=True)

SKIP_MERGE = os.environ.get("SKIP_MERGE") == "1" and os.path.exists(f"{replay_dir}/coverage.txt")
if SKIP_MERGE:
    print(f"  [skip merge] 复用已有 coverage.txt")
    r = type("R", (), {"returncode": 0, "stdout": "", "stderr": ""})()
else:
    r = subprocess.run(
        [BIN, "-merge=1", f"-max_len={os.environ.get('MERGE_MAX_LEN', '131072')}",
         f"-merge_control_file={cf}", mout, f"{run_dir}/corpus/"],
        capture_output=True, text=True, timeout=3600)

cov = set()
if os.path.exists(cf):
    for line in open(cf, errors="ignore"):
        if line.startswith("COV "):
            cov |= {int(x) for x in line.split()[2:] if x.isdigit()}

# 总边数：从 libFuzzer 启动行 "(N inline 8-bit counters)" / "(N guards)" 取
total = 0
m = re.search(r"\((\d+)\s+(?:inline 8-bit counters|guards|PCs)\)", r.stderr)
if m:
    total = int(m.group(1))
if not total:
    # 兜底：再跑一次空语料，读启动行
    r2 = subprocess.run([BIN, "-runs=0", mout], capture_output=True, text=True, timeout=300)
    m2 = re.search(r"\((\d+)\s+(?:inline 8-bit counters|guards|PCs)\)", r2.stderr)
    total = int(m2.group(1)) if m2 else 0

with open(f"{replay_dir}/edges.txt", "w") as f:
    f.write("\n".join(map(str, sorted(cov))) + "\n")
with open(f"{replay_dir}/coverage.txt", "w") as f:
    f.write(f"covered_edges={len(cov)}\n")
    f.write(f"total_edges={total}\n")
    f.write(f"coverage_rate={(len(cov)/total*100 if total else 0):.4f}%\n")

# ---------- 2. 崩溃信息 ----------
MAXC = int(os.environ.get("MAX_CRASH_REPLAY", "200"))
arts = sorted(glob.glob(f"{run_dir}/art/*"))
arts_total = len(arts)
if MAXC and len(arts) > MAXC:
    step = len(arts) / MAXC
    arts = [arts[int(i * step)] for i in range(MAXC)]

crashes = []
for art in arts:
    if not os.path.isfile(art):
        continue
    name = os.path.basename(art)
    data = open(art, "rb").read()
    try:
        rr = subprocess.run([BIN, "-runs=1", "-detect_leaks=0", art],
                            capture_output=True, text=True, timeout=120)
    except subprocess.TimeoutExpired:
        rr = None
    log = (rr.stdout + rr.stderr) if rr else "<timeout>\n"
    with open(f"{replay_dir}/crash/{name}.log", "w") as f:
        f.write(log)

    m_type = re.search(r"ERROR: AddressSanitizer: (\S+)", log)
    m_rw = re.search(r"(READ|WRITE) of size (\d+)", log)
    m_sz = re.search(r"region of size (\d+)", log)
    top = None
    for ln in log.splitlines():
        if re.search(r"#\d+ 0x[0-9a-f]+ in \S+ .*\.(c|h|cc|cpp):\d+", ln):
            top = ln.split(" in ", 1)[1] if " in " in ln else ln.strip()
            break
    crashes.append({
        "name": name,
        "size": len(data),
        "type": m_type.group(1) if m_type else "?",
        "rw": (m_rw.group(1), int(m_rw.group(2))) if m_rw else ("?", "?"),
        "region": int(m_sz.group(1)) if m_sz else None,
        "top": top,
        "hex_head": data[:16].hex(),
    })

with open(f"{replay_dir}/crash_report.txt", "w") as f:
    f.write(f"crash_count={len(crashes)}\n")
    f.write(f"crash_artifacts_total={arts_total}\n")
    for i, c in enumerate(crashes):
        f.write(f"\n[{i+1}] {c['name']}\n")
        f.write(f"  type={c['type']}  {c['rw'][0]} size={c['rw'][1]}\n")
        f.write(f"  input_size={c['size']}\n")
        f.write(f"  hex_head={c['hex_head']}\n")
        f.write(f"  top={c['top']}\n")

print(f"{mode}_{suffix}: edges={len(cov)}/{total}  crashes={len(crashes)}")

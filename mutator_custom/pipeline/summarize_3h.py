#!/usr/bin/env python3
# summarize_3h.py —— 汇总 10 次运行（default/custom 各 5 次），生成 summary.md
import glob, os, re, statistics

BASE = "/root/gyx/mutator_create/mutator_custom/fuzz_exp_3h"

def read_cov(run_dir):
    """从 coverage.txt 读覆盖边数"""
    p = f"{BASE}/replay/{run_dir}/coverage.txt"
    if not os.path.exists(p):
        return None
    m = re.search(r"covered_edges=(\d+)", open(p).read())
    return int(m.group(1)) if m else None

def read_crash_count(run_dir):
    p = f"{BASE}/replay/{run_dir}/crash_report.txt"
    if not os.path.exists(p):
        return None
    m = re.search(r"crash_count=(\d+)", open(p).read())
    return int(m.group(1)) if m else None

def read_exec(run_dir):
    p = f"{BASE}/{run_dir}/run.log"
    if not os.path.exists(p):
        return None
    m = re.findall(r"#(\d+): cov:", open(p, errors='ignore').read())
    return int(m[-1]) if m else None

def corpus_count(run_dir):
    d = f"{BASE}/{run_dir}/corpus"
    return len([f for f in os.listdir(d)]) if os.path.isdir(d) else None

rows = {}
for mode in ['default', 'custom']:
    for i in range(1, 6):
        rd = f"{mode}_{i}"
        rows[rd] = {
            'exec': read_exec(rd),
            'corpus': corpus_count(rd),
            'edges': read_cov(rd),
            'crashes': read_crash_count(rd),
        }

lines = []
lines.append("# 3 小时 fork fuzz 重复实验汇总\n")
lines.append("设置：default/custom 各 5 次，seed=1，fork=1，ignore_crashes=1，3 小时。\n")

# 明细表
lines.append("## 1. 每次运行明细\n")
lines.append("| 运行 | 执行次数 | corpus | 覆盖边 | 崩溃数 |")
lines.append("|---|---|---|---|---|")
for mode in ['default', 'custom']:
    for i in range(1, 6):
        rd = f"{mode}_{i}"
        r = rows[rd]
        lines.append(f"| {rd} | {r['exec']} | {r['corpus']} | {r['edges']} | {r['crashes']} |")

# 5 次重复统计
lines.append("\n## 2. 每模式 5 次重复统计\n")
lines.append("| 模式 | 覆盖边均值 | 覆盖边范围 | 崩溃总数 | 崩溃均值 |")
lines.append("|---|---|---|---|---|")
for mode in ['default', 'custom']:
    edges = [rows[f"{mode}_{i}"]['edges'] for i in range(1, 6)]
    edges = [e for e in edges if e is not None]
    crashes = [rows[f"{mode}_{i}"]['crashes'] for i in range(1, 6)]
    crashes = [c for c in crashes if c is not None]
    if edges:
        mean = f"{statistics.mean(edges):.1f}"
        rng = f"{min(edges)}~{max(edges)}"
    else:
        mean, rng = "N/A", "N/A"
    lines.append(f"| {mode} | {mean} | {rng} | {sum(crashes)} | {statistics.mean(crashes):.2f} |")

# 崩溃汇总
lines.append("\n## 3. 崩溃汇总\n")
all_crashes = []
for mode in ['default', 'custom']:
    for i in range(1, 6):
        rd = f"{mode}_{i}"
        p = f"{BASE}/replay/{rd}/crash_report.txt"
        if os.path.exists(p):
            for ln in open(p):
                if ln.startswith('  type='):
                    all_crashes.append((rd, ln.strip().split('type=')[1].split('  ')[0]))

if all_crashes:
    lines.append(f"共 {len(all_crashes)} 个崩溃：")
    for rd, t in all_crashes:
        lines.append(f"- {rd}: {t}")
else:
    lines.append("无崩溃。")

with open(f"{BASE}/summary.md", "w") as f:
    f.write("\n".join(lines) + "\n")

print(f"汇总已写入 {BASE}/summary.md")
print("\n".join(lines))

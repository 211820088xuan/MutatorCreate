#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""summarize.py —— 汇总 N 次运行，生成 summary.md（对应参考实现的 summarize_3h.py）

用法: summarize.py [reps]
默认 reps=5，即 default_1..5 / custom_1..5
"""
import os, re, sys, statistics, collections

BASE = "/exp/fuzz_exp"
REPS = int(sys.argv[1]) if len(sys.argv) > 1 else 5
DUR = os.environ.get("DUR_LABEL", "20 分钟")


def read_cov(rd):
    p = f"{BASE}/{rd}/replay/coverage.txt"
    if not os.path.exists(p):
        return None, None
    t = open(p).read()
    a = re.search(r"covered_edges=(\d+)", t)
    b = re.search(r"total_edges=(\d+)", t)
    return (int(a.group(1)) if a else None, int(b.group(1)) if b else None)


def read_crash_count(rd):
    p = f"{BASE}/{rd}/replay/crash_report.txt"
    if not os.path.exists(p):
        return None
    m = re.search(r"crash_count=(\d+)", open(p).read())
    return int(m.group(1)) if m else None


def read_exec(rd):
    p = f"{BASE}/{rd}/run.log"
    if not os.path.exists(p):
        return None
    m = re.findall(r"#(\d+): cov:", open(p, errors="ignore").read())
    return int(m[-1]) if m else None


def corpus_count(rd):
    d = f"{BASE}/{rd}/corpus"
    return len(os.listdir(d)) if os.path.isdir(d) else None


def read_crash_types(rd):
    p = f"{BASE}/{rd}/replay/crash_report.txt"
    if not os.path.exists(p):
        return []
    return re.findall(r"type=(\S+)", open(p).read())


rows = {}
for mode in ("default", "custom"):
    for i in range(1, REPS + 1):
        rd = f"{mode}_{i}"
        edges, total = read_cov(rd)
        rows[rd] = {
            "exec": read_exec(rd),
            "corpus": corpus_count(rd),
            "edges": edges,
            "total": total,
            "crashes": read_crash_count(rd),
            "types": read_crash_types(rd),
        }

L = []
L.append(f"# fork fuzz 重复实验汇总（libredwg · {DUR}）\n")
L.append(f"设置：default/custom 各 {REPS} 次，seed=1，fork=1，ignore_crashes=1，{DUR}。")
L.append("")
L.append("同一个二进制 `/exp/llvmfuzz`，仅用环境变量 `LIBREDWG_MUTATOR_OFF` 切换：")
L.append("- `LIBREDWG_MUTATOR_OFF=1` → 默认变异器（default）")
L.append("- `LIBREDWG_MUTATOR_OFF=0` → 我们生成的变异器（custom）")
L.append("")

# 1. 明细
L.append("## 1. 每次运行明细\n")
L.append("| 运行 | 执行次数 | corpus | 覆盖边 | 总边数 | 覆盖率 | 崩溃数 |")
L.append("|---|---|---|---|---|---|---|")
for mode in ("default", "custom"):
    for i in range(1, REPS + 1):
        rd = f"{mode}_{i}"
        r = rows[rd]
        rate = f"{r['edges']/r['total']*100:.2f}%" if (r["edges"] and r["total"]) else "-"
        L.append(f"| {rd} | {r['exec']} | {r['corpus']} | {r['edges']} | {r['total']} | {rate} | {r['crashes']} |")

# 2. 重复统计
L.append("\n## 2. 每模式重复统计\n")
L.append("| 模式 | 覆盖边均值 | 覆盖边范围 | 覆盖率均值 | 崩溃总数 | 崩溃均值 |")
L.append("|---|---|---|---|---|---|")
for mode in ("default", "custom"):
    es = [rows[f"{mode}_{i}"]["edges"] for i in range(1, REPS + 1) if rows[f"{mode}_{i}"]["edges"]]
    ts = [rows[f"{mode}_{i}"]["total"] for i in range(1, REPS + 1) if rows[f"{mode}_{i}"]["total"]]
    cs = [rows[f"{mode}_{i}"]["crashes"] for i in range(1, REPS + 1) if rows[f"{mode}_{i}"]["crashes"] is not None]
    if es:
        mean_e = statistics.mean(es)
        rng = f"{min(es)}~{max(es)}"
        mean_rate = f"{mean_e/ts[0]*100:.2f}%" if ts else "-"
    else:
        mean_e = rng = mean_rate = "-"
    L.append(f"| {mode} | {mean_e} | {rng} | {mean_rate} | {sum(cs)} | {statistics.mean(cs):.2f} |" if cs else f"| {mode} | {mean_e} | {rng} | {mean_rate} | - | - |")

# 3. 崩溃汇总
L.append("\n## 3. 崩溃汇总\n")
allc = []
for mode in ("default", "custom"):
    for i in range(1, REPS + 1):
        rd = f"{mode}_{i}"
        for t in rows[rd]["types"]:
            allc.append((rd, t))
L.append(f"共 {len(allc)} 个崩溃：")
if allc:
    for rd, t in allc:
        L.append(f"- {rd}: {t}")
else:
    L.append("- （无）")

# 4. 崩溃类型分布
L.append("\n## 4. 崩溃类型分布\n")
cnt = collections.Counter((rd.rsplit("_", 1)[0], t) for rd, t in allc)
if cnt:
    L.append("| 模式 | 类型 | 数量 |")
    L.append("|---|---|---|")
    for (mode, t), n in sorted(cnt.items()):
        L.append(f"| {mode} | {t} | {n} |")
else:
    L.append("（无崩溃）")

out = f"{BASE}/summary.md"
open(out, "w").write("\n".join(L) + "\n")
print(f"已生成 {out}")
print("\n".join(L))

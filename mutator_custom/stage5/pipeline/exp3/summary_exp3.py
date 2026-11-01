#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""summary_exp3.py —— 读 fuzz_exp3 原始数据，输出机器生成的结果表

只做"读数 + 聚合"，不做解释。解释留给 SUMMARY.md（人工撰写并核验）。

口径说明：
  edges  = -merge=1 重放该 run 的最终 corpus 得到的覆盖边（每个 run 独立 merge，
           控制文件在分析前清空，可复现）
  inrun  = run.log 最后一行 "#N: cov: X" 的 X（fuzz 进程结束时的累积覆盖）
  exec   = run.log 最后一行 "#N" 的 N（总执行次数）
  crash  = run.log 里 "ERROR: AddressSanitizer" 的行数
  target = run.log 里 "pc 0x0000032787d8" 的行数
           （已用 12 个 artifact 验证该 pc 对应 in_dxf.c:12267 in dxf_objects_read）
"""
import os
import re
import statistics
import sys

BASE = os.environ.get("EXP_BASE", "/exp/fuzz_exp3")
REPS = int(os.environ.get("EXP_REPS", "5"))
ARMS = [("default", "default（100% 默认变异）"), ("custom", "custom（80% 默认 + 20% 自定义）")]
TGT_PC = "0x0000032787d8"
TGT_DESC = "in_dxf.c:12267 in dxf_objects_read"


def load(arm, i):
    rd = f"{arm}_{i}"
    cov_p = f"{BASE}/replay/{rd}/coverage.txt"
    log_p = f"{BASE}/{rd}/run.log"
    r = dict(rd=rd, arm=arm)
    if os.path.exists(cov_p):
        t = open(cov_p, errors="ignore").read()
        m = re.search(r"covered_edges=(\d+)", t)
        r["edges"] = int(m.group(1)) if m else None
        m = re.search(r"total_edges=(\d+)", t)
        r["total"] = int(m.group(1)) if m else None
    else:
        r["edges"] = r["total"] = None
    if os.path.exists(log_p):
        log = open(log_p, errors="ignore").read()
        m = re.findall(r"#(\d+): cov: (\d+)", log)
        r["exec"], r["inrun"] = (int(m[-1][0]), int(m[-1][1])) if m else (None, None)
        r["crash"] = log.count("ERROR: AddressSanitizer")
        r["target"] = log.count(f"pc {TGT_PC}")
        r["done"] = "exiting:" in log
    else:
        r["exec"] = r["inrun"] = r["crash"] = r["target"] = None
        r["done"] = False
    return r


rows = [load(a, i) for a, _ in ARMS for i in range(1, REPS + 1)]

L = []
L.append("# fuzz_exp3 原始结果表（机器生成）\n")
L.append(f"目标崩溃点：`{TGT_DESC}`（pc 指纹 `{TGT_PC}`）\n")

L.append("## 1. 逐次明细\n")
L.append("| run | 完成 | 覆盖边(merge) | in-run cov | 执行次数 | 崩溃数 | 目标 UAF | 目标占比 |")
L.append("|---|---|---|---|---|---|---|---|")
for r in rows:
    pct = f"{r['target']/r['crash']*100:.1f}%" if r["crash"] else "-"
    L.append(f"| {r['rd']} | {'✓' if r['done'] else '✗'} | {r['edges']} | {r['inrun']} | "
             f"{r['exec']} | {r['crash']} | {r['target']} | {pct} |")

L.append("\n## 2. 按臂聚合\n")
L.append("| 臂 | 覆盖边 均值 | 中位数 | 范围 | in-run 均值 | 崩溃 均值 | 中位数 | 目标 UAF 总数 |")
L.append("|---|---|---|---|---|---|---|---|")
agg = {}
for arm, label in ARMS:
    g = [r for r in rows if r["arm"] == arm and r["edges"]]
    if not g:
        L.append(f"| {label} | - | - | - | - | - | - | - |")
        continue
    agg[arm] = g
    e = [r["edges"] for r in g]
    ir = [r["inrun"] for r in g if r["inrun"]]
    cr = [r["crash"] for r in g if r["crash"] is not None]
    tg = sum(r["target"] or 0 for r in g)
    L.append(f"| {label} | {statistics.mean(e):.0f} | {statistics.median(e):.0f} | "
             f"{min(e)}~{max(e)} | {statistics.mean(ir):.0f} | {statistics.mean(cr):.0f} | "
             f"{statistics.median(cr):.0f} | {tg} |")

L.append("\n## 3. 配对比较（custom / default，同序号）\n")
L.append("| 序号 | 覆盖边 default | 覆盖边 custom | 比值 | in-run 比值 |")
L.append("|---|---|---|---|---|")
for i in range(1, REPS + 1):
    d = rows[i - 1]
    c = rows[REPS + i - 1]
    if not (d.get("edges") and c.get("edges")):
        continue
    er = c["edges"] / d["edges"]
    ir = (c["inrun"] / d["inrun"]) if (c.get("inrun") and d.get("inrun")) else None
    L.append(f"| {i} | {d['edges']} | {c['edges']} | {er:.3f} | "
             f"{f'{ir:.3f}' if ir else '-'} |")

if len(agg) == 2:
    de = [r["edges"] for r in agg["default"]]
    ce = [r["edges"] for r in agg["custom"]]
    L.append(f"\n- 覆盖边均值差: **{(statistics.mean(ce)/statistics.mean(de)-1)*100:+.2f}%**"
             f"（中位数 {(statistics.median(ce)/statistics.median(de)-1)*100:+.2f}%）")
    di = [r["inrun"] for r in agg["default"] if r["inrun"]]
    ci = [r["inrun"] for r in agg["custom"] if r["inrun"]]
    if di and ci:
        L.append(f"- in-run 均值差: **{(statistics.mean(ci)/statistics.mean(di)-1)*100:+.2f}%**")
    dc = [r["crash"] for r in agg["default"]]
    cc = [r["crash"] for r in agg["custom"]]
    L.append(f"- 崩溃数均值差: **{(statistics.mean(cc)/statistics.mean(dc)-1)*100:+.2f}%**"
             f"（中位数 {(statistics.median(cc)/statistics.median(dc)-1)*100:+.2f}%）")
    dt = sum(r["target"] for r in agg["default"])
    ct = sum(r["target"] for r in agg["custom"])
    L.append(f"- 目标 UAF 总数: default={dt}  custom={ct}  ({(ct/dt-1)*100:+.2f}%)")

out = f"{BASE}/summary_raw.md"
open(out, "w").write("\n".join(L) + "\n")
print("\n".join(L))
print(f"\n已写入 {out}")

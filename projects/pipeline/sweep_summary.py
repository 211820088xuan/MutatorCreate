#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""sweep_summary.py —— 汇总占比扫描结果，输出 summary_sweep.md

用法: sweep_summary.py "0,20,40,60,80,100" [reps]
"""
import os, re, sys, statistics

BASE = "/exp/fuzz_exp"
PCTS = [x for x in sys.argv[1].split(",") if x.strip()]
REPS = int(sys.argv[2]) if len(sys.argv) > 2 else 2


def rd_file(*parts):
    p = os.path.join(BASE, *parts)
    return open(p, errors="ignore").read() if os.path.exists(p) else None


def get_int(txt, pat):
    if not txt:
        return None
    m = re.search(pat, txt)
    return int(m.group(1)) if m else None


rows = []
for pct in PCTS:
    for i in range(1, REPS + 1):
        rd = f"p{pct}_{i}"
        cov_txt = rd_file("replay", rd, "coverage.txt")
        crash_txt = rd_file("replay", rd, "crash_report.txt")
        log = rd_file(rd, "run.log")
        ex = re.findall(r"#(\d+): cov:", log) if log else []
        corpus_dir = os.path.join(BASE, rd, "corpus")
        rows.append(dict(
            rd=rd, pct=int(pct),
            edges=get_int(cov_txt, r"covered_edges=(\d+)"),
            total=get_int(cov_txt, r"total_edges=(\d+)"),
            crashes=get_int(crash_txt, r"crash_count=(\d+)"),
            execs=int(ex[-1]) if ex else None,
            corpus=len(os.listdir(corpus_dir)) if os.path.isdir(corpus_dir) else None,
        ))

L = []
L.append("# 自定义变异占比扫描（libredwg · dxf_objects_read）\n")
L.append("每个占比跑 %d 次；`p0` = 纯默认变异（基线），`p100` = 纯自定义。" % REPS)
L.append("同一个二进制，仅用 `LIBREDWG_CUSTOM_PCT`（0~100）控制自定义占比。\n")

L.append("## 1. 逐次明细\n")
L.append("| 运行 | 自定义占比 | 执行次数 | corpus | 覆盖边 | 覆盖率 | 崩溃数 |")
L.append("|---|---|---|---|---|---|---|")
for r in rows:
    rate = f"{r['edges']/r['total']*100:.2f}%" if (r["edges"] and r["total"]) else "-"
    L.append(f"| {r['rd']} | {r['pct']}% | {r['execs']} | {r['corpus']} | {r['edges']} | {rate} | {r['crashes']} |")

L.append("\n## 2. 按占比聚合\n")
L.append("| 自定义占比 | 覆盖边均值 | 覆盖边范围 | 覆盖率均值 | 执行次数均值 | 崩溃总数 |")
L.append("|---|---|---|---|---|---|")
for pct in PCTS:
    g = [r for r in rows if r["pct"] == int(pct)]
    es = [r["edges"] for r in g if r["edges"]]
    ts = [r["total"] for r in g if r["total"]]
    xs = [r["execs"] for r in g if r["execs"]]
    cs = [r["crashes"] for r in g if r["crashes"] is not None]
    if es:
        mean_e = f"{statistics.mean(es):.0f}"
        rng = f"{min(es)}~{max(es)}"
        rate = f"{mean_e and (statistics.mean(es)/ts[0]*100):.2f}%" if ts else "-"
    else:
        mean_e = rng = rate = "-"
    L.append(f"| {pct}% | {mean_e} | {rng} | {rate} | "
             f"{f'{statistics.mean(xs):.0f}' if xs else '-'} | {sum(cs) if cs else '-'} |")

out = os.path.join(BASE, "summary_sweep.md")
open(out, "w").write("\n".join(L) + "\n")
print(f"已生成 {out}\n")
print("\n".join(L))

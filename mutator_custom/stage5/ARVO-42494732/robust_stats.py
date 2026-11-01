#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""robust_stats.py —— 剔除离群 run 前后的对比统计

离群判据（可复现）：分别对每个臂，计算「到达第 10 个崩溃所需秒数」，
取**偏离该臂中位数最远**的那个 run 作为该臂的离群点。

用法：
    robust_stats.py --root /exp/fuzz_exp2
    robust_stats.py --root /exp/fuzz_exp2 --exclude default_1,custom_4
"""
import argparse
import json
import os
import re
import statistics as st
from datetime import datetime, timezone


def scan(dirpath):
    out = []
    if not os.path.isdir(dirpath):
        return out
    for n in os.listdir(dirpath):
        p = os.path.join(dirpath, n)
        try:
            s = os.stat(p)
        except OSError:
            continue
        if os.path.isfile(p):
            out.append((n, s.st_mtime, s.st_size))
    out.sort(key=lambda x: x[1])
    return out


def cov_of(logpath):
    if not os.path.exists(logpath):
        return None
    m = re.findall(r"cov: (\d+)", open(logpath, errors="ignore").read())
    return int(m[-1]) if m else None


def time_to_k(crashes, t0, k):
    if t0 is None or len(crashes) < k:
        return None
    return int(crashes[k - 1][1] - t0)


def load(root):
    runs = [n for n in sorted(os.listdir(root))
            if os.path.isdir(os.path.join(root, n, "corpus"))]
    data = []
    for run in runs:
        rd = os.path.join(root, run)
        crashes = scan(os.path.join(rd, "crash"))
        corpus = scan(os.path.join(rd, "corpus"))
        cand = [m for _, m, _ in crashes] + [m for _, m, _ in corpus]
        t0 = min(cand) if cand else None
        d = dict(run=run, arm=run.rsplit("_", 1)[0],
                 cov=cov_of(os.path.join(rd, "run.log")),
                 crashes=len(crashes), corpus=len(corpus), t0=t0,
                 hourly=[sum(1 for _, m, _ in crashes if (m - t0) <= h * 3600)
                         for h in range(25)] if t0 else [],
                 tt={k: time_to_k(crashes, t0, k) for k in (10, 25, 50, 100, 200, 400)})
        data.append(d)
    return data


def find_outlier(data, arm, k=10):
    g = [r for r in data if r["arm"] == arm and r["tt"].get(k) is not None]
    if len(g) < 3:
        return None, None
    med = st.median([r["tt"][k] for r in g])
    worst = max(g, key=lambda r: abs(r["tt"][k] - med))
    return worst["run"], med


def agg(data, arm):
    g = [r for r in data if r["arm"] == arm]
    if not g:
        return None
    out = dict(n=len(g),
               cov_mean=st.mean([r["cov"] for r in g if r["cov"]]),
               cov_median=st.median([r["cov"] for r in g if r["cov"]]),
               crash_total=sum(r["crashes"] for r in g),
               crash_mean=st.mean([r["crashes"] for r in g]),
               crash_median=st.median([r["crashes"] for r in g]),
               corpus_mean=st.mean([r["corpus"] for r in g]))
    for k in (10, 25, 50, 100, 200):
        vals = [r["tt"][k] for r in g if r["tt"].get(k) is not None]
        out[f"k{k}"] = st.mean(vals) if vals else None
        out[f"k{k}_n"] = len(vals)
    out["hourly"] = [st.mean([r["hourly"][h] for r in g if r["hourly"]])
                     for h in range(25)] if all(r["hourly"] for r in g) else []
    return out


def paired(data, key, k=None):
    d = {r["run"]: r for r in data if r["arm"] == "default"}
    c = {r["run"]: r for r in data if r["arm"] == "custom"}
    ids = sorted(set(x.rsplit("_", 1)[1] for x in d) & set(x.rsplit("_", 1)[1] for x in c))
    wins = 0
    for i in ids:
        a = d.get(f"default_{i}")
        b = c.get(f"custom_{i}")
        if not (a and b):
            continue
        va = a[key] if k is None else a["tt"].get(k)
        vb = b[key] if k is None else b["tt"].get(k)
        if va is None or vb is None:
            continue
        if key == "tt":
            if vb < va:      # 时间越短越好
                wins += 1
        else:
            if vb > va:
                wins += 1
    return wins, len(ids)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", required=True)
    ap.add_argument("--exclude", default=None)
    a = ap.parse_args()
    root = os.path.abspath(a.root.rstrip("/"))

    data = load(root)

    # 自动判定离群点
    auto = []
    for arm in ("default", "custom"):
        w, med = find_outlier(data, arm)
        if w:
            auto.append(w)
            print(f"[离群判定] {arm}: 中位数 k10={med:.0f}s，偏离最远的是 {w}")
    print(f"[离群判定] 自动选出: {', '.join(auto)}\n")

    excl = a.exclude.split(",") if a.exclude else auto
    keep = [r for r in data if r["run"] not in excl]

    L = ["# 剔除离群 run 前后的对比\n",
         f"根目录：`{root}`",
         f"离群判据：各臂内「到达第 10 个崩溃的秒数」偏离臂中位数最远的 run",
         f"自动判定结果：**{', '.join(auto)}**",
         f"本次统计剔除：**{', '.join(excl)}**\n"]

    L.append("## 1. 逐 run 数据（★ = 被剔除）\n")
    L.append("| run | 覆盖边 | 崩溃工件 | corpus | k10(s) | k50(s) | k100(s) | k200(s) |")
    L.append("|---|---|---|---|---|---|---|---|")
    for r in sorted(data, key=lambda x: (x["arm"], x["run"])):
        mk = " ★" if r["run"] in excl else ""
        f = lambda k: (str(r["tt"].get(k)) if r["tt"].get(k) is not None else "–")
        L.append(f"| {r['run']}{mk} | {r['cov']} | {r['crashes']} | {r['corpus']} | "
                 f"{f(10)} | {f(50)} | {f(100)} | {f(200)} |")

    L.append("\n## 2. 聚合对比（全部 5 次 vs 剔除后）\n")
    L.append("| 指标 | 全部 5 次 | 剔除后 |")
    L.append("|---|---|---|")
    a_all = {arm: agg(data, arm) for arm in ("default", "custom")}
    a_keep = {arm: agg(keep, arm) for arm in ("default", "custom")}

    def line(label, key, fmt="%.0f"):
        def pair(d):
            v0 = d["default"].get(key) if d["default"] else None
            v1 = d["custom"].get(key) if d["custom"] else None
            if v0 is None or v1 is None:
                return "–"
            diff = (v1 / v0 - 1) * 100
            return (f"default {fmt % v0} / custom {fmt % v1} ({diff:+.1f}%)")
        L.append(f"| {label} | {pair(a_all)} | {pair(a_keep)} |")

    line("覆盖边 均值", "cov_mean")
    line("覆盖边 中位数", "cov_median")
    line("崩溃工件 总数", "crash_total")
    line("崩溃工件 均值", "crash_mean")
    line("corpus 均值", "corpus_mean")
    for k in (10, 25, 50, 100, 200):
        line(f"到达第 {k} 个崩溃 (秒)", f"k{k}")

    L.append("\n## 3. 剔除后的逐小时累计崩溃\n")
    L.append("| 小时 | default | custom |")
    L.append("|---|---|---|")
    for h in range(0, 25):
        v0 = a_keep["default"]["hourly"][h] if a_keep["default"] and a_keep["default"]["hourly"] else None
        v1 = a_keep["custom"]["hourly"][h] if a_keep["custom"] and a_keep["custom"]["hourly"] else None
        if v0 is None or v1 is None:
            continue
        L.append(f"| +{h}h | {v0:.1f} | {v1:.1f} |")

    L.append("\n## 4. 配对比较（剔除后，同序号配对）\n")
    L.append("| 指标 | custom 胜出 | 说明 |")
    L.append("|---|---|---|")
    for key, name in (("cov", "覆盖边"), ("crashes", "崩溃工件数")):
        w, n = paired(keep, key)
        L.append(f"| {name} | {w}/{n} | custom 更高才算胜 |")
    for k in (10, 50, 100):
        w, n = paired(keep, "tt", k)
        L.append(f"| 到达第 {k} 个崩溃时间 | {w}/{n} | custom 更短才算胜 |")

    out = os.path.join(root, "robust_stats.md")
    open(out, "w").write("\n".join(L) + "\n")
    print("\n".join(L))
    print(f"\n已写出 {out}")
    json.dump({"excluded": excl, "auto": auto,
               "all": a_all, "keep": a_keep},
              open(os.path.join(root, "robust_stats.json"), "w"), indent=2)


if __name__ == "__main__":
    main()

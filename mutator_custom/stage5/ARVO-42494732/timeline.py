#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""timeline.py —— 崩溃发现的时间线分析

回答的问题：**哪个变异算子更快地触发更多崩溃？**

数据来源（全部来自已完成的 fuzz 运行，不需要重跑）：
  1. run.log   每行 `oom/timeout/crash: a/b/c time: Ts` 给出「截至第 T 秒的累计崩溃数 c」
  2. crash/    每个 crash-<sha1> 工件的 mtime = 该崩溃的发现时刻（精确到秒）
  3. corpus/   每个语料文件的 mtime = 该输入被加入语料的时刻

产出（每个 run 目录下）：
  crash_index.tsv      file / 发现时刻(ISO) / 相对开始秒数 / 大小 / 小时桶
  corpus_index.tsv     file / 入语料时刻(ISO) / 相对开始秒数 / 大小

产出（实验根目录）：
  timeline.json        机器可读
  timeline.md          对比报告
  crash_by_time/       （--link 时）按时间命名的硬链接镜像：
                       <arm>_<rep>/<HHMMSS>_<sha1>.crash

用法：
  timeline.py --root /exp/fuzz_exp2
  timeline.py --root /exp/fuzz_exp2 --link          # 额外建时间命名镜像
"""
import argparse
import json
import os
import re
import statistics as st
import sys
from datetime import datetime, timezone


# ---------------------------------------------------------------- 工具
def scan(dirpath):
    """返回 [(name, mtime, size)]"""
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


def parse_log(logpath):
    """从 run.log 提取 [(t_sec, cum_crash)]"""
    if not os.path.exists(logpath):
        return []
    txt = open(logpath, errors="ignore").read()
    pat = re.compile(r"oom/timeout/crash: (\d+)/(\d+)/(\d+) time: (\d+)s")
    out = []
    for m in pat.finditer(txt):
        out.append((int(m.group(4)), int(m.group(3))))
    # 去重 + 保证时间递增
    seen, res = set(), []
    for t, c in out:
        if t in seen:
            continue
        seen.add(t)
        res.append((t, c))
    return res


def iso(ts):
    return datetime.fromtimestamp(ts, timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def hhmmss(ts):
    return datetime.fromtimestamp(ts, timezone.utc).strftime("%H%M%S")


def t_at(series, k):
    """累计崩溃数首次达到 k 的时刻（秒）；达不到返回 None"""
    for t, c in series:
        if c >= k:
            return t
    return None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", required=True)
    ap.add_argument("--link", action="store_true",
                    help="额外把崩溃工件硬链接到 crash_by_time/<HHMMSS>_<sha1>.crash")
    a = ap.parse_args()

    root = os.path.abspath(a.root.rstrip("/"))
    runs = [n for n in sorted(os.listdir(root))
            if os.path.isdir(os.path.join(root, n, "corpus"))]
    if not runs:
        sys.exit(f"{root} 下没有 run")

    results = []
    for run in runs:
        rd = os.path.join(root, run)
        crashes = scan(os.path.join(rd, "crash"))
        corpus = scan(os.path.join(rd, "corpus"))
        series = parse_log(os.path.join(rd, "run.log"))

        # t0：取语料与崩溃工件的最早 mtime
        cand = [m for _, m, _ in crashes] + [m for _, m, _ in corpus]
        t0 = min(cand) if cand else None

        # crash_index.tsv
        if t0:
            with open(os.path.join(rd, "crash_index.tsv"), "w") as f:
                f.write("file\tfound_utc\tsec_since_start\tsize\thour_bucket\n")
                for n, m, s in crashes:
                    rel = int(m - t0)
                    f.write(f"{n}\t{iso(m)}\t{rel}\t{s}\t{rel // 3600}\n")
            with open(os.path.join(rd, "corpus_index.tsv"), "w") as f:
                f.write("file\tadded_utc\tsec_since_start\tsize\thour_bucket\n")
                for n, m, s in corpus:
                    rel = int(m - t0)
                    f.write(f"{n}\t{iso(m)}\t{rel}\t{s}\t{rel // 3600}\n")

        # 逐小时累计崩溃
        hourly = []
        if t0:
            for h in range(0, 25):
                n = sum(1 for _, m, _ in crashes if (m - t0) <= h * 3600)
                hourly.append(n)

        # time-to-k-th crash（用工件 mtime，精确）
        tt = {}
        for k in (1, 10, 25, 50, 100, 200, 400):
            tt[f"k{k}"] = (int(crashes[k - 1][1] - t0)
                           if t0 and len(crashes) >= k else None)

        # corpus 逐小时增长
        chourly = []
        if t0:
            for h in range(0, 25):
                chourly.append(sum(1 for _, m, _ in corpus if (m - t0) <= h * 3600))

        rec = dict(run=run, arm=run.rsplit("_", 1)[0],
                   crash_artifacts=len(crashes),
                   corpus_files=len(corpus),
                   t0_utc=iso(t0) if t0 else None,
                   span_hours=round((crashes[-1][1] - t0) / 3600, 2) if (t0 and crashes) else None,
                   hourly_cum_crash=hourly,
                   hourly_cum_corpus=chourly,
                   time_to_k=tt,
                   log_points=len(series),
                   log_final_crash=(series[-1][1] if series else None))
        results.append(rec)

        if a.link and t0:
            dst = os.path.join(root, "crash_by_time", run)
            os.makedirs(dst, exist_ok=True)
            for n, m, _ in crashes:
                sha = n.split("-", 1)[1] if "-" in n else n
                tgt = os.path.join(dst, f"{hhmmss(m)}_{sha}.crash")
                if not os.path.exists(tgt):
                    try:
                        os.link(os.path.join(rd, "crash", n), tgt)
                    except OSError:
                        pass

    json.dump(results, open(os.path.join(root, "timeline.json"), "w"), indent=2)

    # ---------------- 报告 ----------------
    L = ["# 崩溃发现时间线\n",
         f"根目录：`{root}`",
         "时间原点 `t0` = 该 run 里 corpus 与崩溃工件的最早 mtime。\n"]

    L.append("## 1. 逐 run：崩溃工件的时间跨度\n")
    L.append("| run | 崩溃工件 | corpus | t0 (UTC) | 最后崩溃 @ +小时 |")
    L.append("|---|---|---|---|---|")
    for r in results:
        L.append(f"| {r['run']} | {r['crash_artifacts']} | {r['corpus_files']} | "
                 f"{r['t0_utc']} | {r['span_hours']} |")

    L.append("\n## 2. 逐小时累计崩溃数（同一臂的 5 次取均值）\n")
    arms = sorted({r["arm"] for r in results}, key=lambda x: (x != "default", x))
    hdr = "| 小时 |" + "|".join(f" {a} " for a in arms) + "|"
    L.append(hdr)
    L.append("|---" * (len(arms) + 1) + "|")
    for h in range(0, 25):
        row = f"| +{h}h |"
        for arm in arms:
            g = [r for r in results if r["arm"] == arm]
            vals = [r["hourly_cum_crash"][h] for r in g if r["hourly_cum_crash"]]
            row += f" {st.mean(vals):.1f} |" if vals else " - |"
        L.append(row)

    L.append("\n## 3. 达到第 k 个崩溃所需时间（秒，同臂取均值）\n")
    L.append("这是回答「谁更快」的核心指标。\n")
    hdr = "| k |" + "|".join(f" {a} " for a in arms) + "|"
    L.append(hdr)
    L.append("|---" * (len(arms) + 1) + "|")
    for k in (1, 10, 25, 50, 100, 200, 400):
        row = f"| {k} |"
        for arm in arms:
            g = [r for r in results if r["arm"] == arm]
            vals = [r["time_to_k"][f"k{k}"] for r in g
                    if r["time_to_k"].get(f"k{k}") is not None]
            row += f" {st.mean(vals):.0f} |" if vals else " 未达到 |"
        L.append(row)

    L.append("\n## 4. corpus 逐小时累计（同臂取均值）\n")
    L.append(hdr)
    L.append("|---" * (len(arms) + 1) + "|")
    for h in range(0, 25, 3):
        row = f"| +{h}h |"
        for arm in arms:
            g = [r for r in results if r["arm"] == arm]
            vals = [r["hourly_cum_corpus"][h] for r in g if r["hourly_cum_corpus"]]
            row += f" {st.mean(vals):.0f} |" if vals else " - |"
        L.append(row)

    L.append("\n## 5. 每个 run 的可复现索引\n")
    L.append("```")
    L.append("<run>/crash_index.tsv    file / found_utc / sec_since_start / size / hour_bucket")
    L.append("<run>/corpus_index.tsv   file / added_utc / sec_since_start / size / hour_bucket")
    L.append("```")
    L.append("")
    L.append("`found_utc` 精确到秒，可直接用于复现「第几分钟发现了什么」。")

    open(os.path.join(root, "timeline.md"), "w").write("\n".join(L) + "\n")
    print("\n".join(L))
    print(f"\n已写出 {os.path.join(root, 'timeline.md')}")
    print(f"已写出 {os.path.join(root, 'timeline.json')}")


if __name__ == "__main__":
    main()

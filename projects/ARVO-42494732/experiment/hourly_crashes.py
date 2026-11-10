#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""hourly_crashes.py —— 按小时统计崩溃发现数，并给 corpus/崩溃工件建时间索引

需求：知道「各个小时发现了多少个崩溃」。

数据来源（全部来自已完成的 fuzz 运行，不需要重放）：
  1. run.log 的 `oom/timeout/crash: a/b/c time: Ts`  → 截至第 T 秒的累计崩溃数
  2. crash-*/oom-*/timeout-* 的 mtime                → 每个工件的精确发现时刻
  3. corpus 文件的 mtime                             → 每个输入进入语料的时刻

产出（每个 run 目录下）：
  crash_index.tsv    file / found_utc / hour / sec_since_start / size
  corpus_index.tsv   file / added_utc / hour / sec_since_start / size

产出（实验根目录）：
  hourly_crashes.md     逐小时表（每臂 3 次取均值）+ JSON
  hourly_crashes.json
  crash_by_time/<run>/<HHMMSS>_<sha1>.crash   按发现时刻命名的硬链接镜像（--link）

用法：
  python3 hourly_crashes.py --root /exp/experiment/reps_24h_3rep [--link]
"""
import argparse
import json
import os
import re
import statistics as st
import sys
from datetime import datetime, timezone


def scan(d):
    out = []
    if not os.path.isdir(d):
        return out
    for n in os.listdir(d):
        p = os.path.join(d, n)
        try:
            s = os.stat(p)
        except OSError:
            continue
        if os.path.isfile(p):
            out.append((n, s.st_mtime, s.st_size))
    out.sort(key=lambda x: x[1])
    return out


def parse_log(p):
    """[(t_sec, cum_crash)]，来自进度行"""
    if not os.path.exists(p):
        return []
    txt = open(p, errors="ignore").read()
    seen, res = set(), []
    for m in re.finditer(r"oom/timeout/crash: (\d+)/(\d+)/(\d+) time: (\d+)s", txt):
        t, c = int(m.group(4)), int(m.group(3))
        if t in seen:
            continue
        seen.add(t)
        res.append((t, c))
    return res


def iso(ts):
    return datetime.fromtimestamp(ts, timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def hhmmss(ts):
    return datetime.fromtimestamp(ts, timezone.utc).strftime("%H%M%S")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", required=True)
    ap.add_argument("--link", action="store_true", help="崩溃工件按时间建硬链接镜像")
    ap.add_argument("--link-corpus", action="store_true", help="corpus 也按时间建硬链接镜像（不额外占空间）")
    ap.add_argument("--hours", type=int, default=24)
    a = ap.parse_args()

    root = os.path.abspath(a.root.rstrip("/"))
    runs = [n for n in sorted(os.listdir(root))
            if os.path.isdir(os.path.join(root, n, "corpus"))]
    if not runs:
        sys.exit(f"{root} 下没有 run")

    H = a.hours
    rows = []
    for run in runs:
        rd = os.path.join(root, run)
        crashes = scan(os.path.join(rd, "crash"))
        corpus = scan(os.path.join(rd, "corpus"))
        series = parse_log(os.path.join(rd, "run.log"))
        cand = [m for _, m, _ in crashes] + [m for _, m, _ in corpus]
        t0 = min(cand) if cand else None

        # 用工件 mtime 统计逐小时「新增」崩溃数（精确到秒）
        hourly_new = [0] * (H + 1)
        if t0:
            for _, m, _ in crashes:
                h = int((m - t0) // 3600)
                if 0 <= h <= H:
                    hourly_new[h] += 1

        # 用日志序列统计逐小时「累计」崩溃数（粗粒度，做交叉校验）
        log_cum = []
        if series:
            for h in range(H + 1):
                v = [c for t, c in series if t <= h * 3600]
                log_cum.append(v[-1] if v else 0)

        # 索引文件
        if t0:
            with open(os.path.join(rd, "crash_index.tsv"), "w") as f:
                f.write("file\tfound_utc\thour\tsec_since_start\tsize\n")
                for n, m, s in crashes:
                    rel = int(m - t0)
                    f.write(f"{n}\t{iso(m)}\t{rel // 3600}\t{rel}\t{s}\n")
            with open(os.path.join(rd, "corpus_index.tsv"), "w") as f:
                f.write("file\tadded_utc\thour\tsec_since_start\tsize\n")
                for n, m, s in corpus:
                    rel = int(m - t0)
                    f.write(f"{n}\t{iso(m)}\t{rel // 3600}\t{rel}\t{s}\n")

        if a.link_corpus and t0:
            dstc = os.path.join(root, "corpus_by_time", run)
            os.makedirs(dstc, exist_ok=True)
            for n, m, _ in corpus:
                tgt = os.path.join(dstc, f"{hhmmss(m)}_{n}")
                if not os.path.exists(tgt):
                    try:
                        os.link(os.path.join(rd, "corpus", n), tgt)
                    except OSError:
                        pass

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

        rows.append(dict(run=run, arm=run.rsplit("_", 1)[0],
                         artifacts=len(crashes), corpus=len(corpus),
                         t0_utc=iso(t0) if t0 else None,
                         last_artifact_hour=round((crashes[-1][1] - t0) / 3600, 2)
                         if (t0 and crashes) else None,
                         hourly_new=hourly_new, log_cum=log_cum))

    arms = sorted({r["arm"] for r in rows}, key=lambda x: (x != "default", x))

    # ---------------- 报告 ----------------
    L = ["# 逐小时崩溃发现统计\n",
         f"根目录：`{root}`",
         "时间原点 `t0` = 该 run 里 corpus 与崩溃工件的最早 mtime。",
         "「新增」来自崩溃工件的 mtime（精确到秒）；「日志累计」来自进度行的 `crash:` 计数（每 job 一次，较粗）。\n"]

    L.append("## 1. 逐 run 概况\n")
    L.append("| run | 崩溃工件 | corpus | t0 (UTC) | 最后崩溃 @ +小时 |")
    L.append("|---|---|---|---|---|")
    for r in rows:
        L.append(f"| {r['run']} | {r['artifacts']} | {r['corpus']} | {r['t0_utc']} | "
                 f"{r['last_artifact_hour']} |")

    L.append("\n## 2. 逐小时「新增」崩溃数（同臂取均值）\n")
    L.append("| 小时 |" + "|".join(f" {a} " for a in arms) + "|")
    L.append("|---" * (len(arms) + 1) + "|")
    for h in range(H + 1):
        line = f"| +{h}h |"
        for arm in arms:
            g = [r for r in rows if r["arm"] == arm]
            line += f" {st.mean([r['hourly_new'][h] for r in g]):.1f} |"
        L.append(line)

    L.append("\n## 3. 逐小时「累计」崩溃数（同臂取均值，日志口径）\n")
    L.append("| 小时 |" + "|".join(f" {a} " for a in arms) + "|")
    L.append("|---" * (len(arms) + 1) + "|")
    for h in range(H + 1):
        if not any(r["log_cum"] for r in rows):
            break
        line = f"| +{h}h |"
        for arm in arms:
            g = [r for r in rows if r["arm"] == arm and r["log_cum"]]
            vals = [r["log_cum"][h] for r in g]
            line += f" {st.mean(vals):.1f} |" if vals else " - |"
        L.append(line)

    L.append("\n## 4. 每个 run 的时间索引\n")
    L.append("```")
    L.append("<run>/crash_index.tsv    file / found_utc / hour / sec_since_start / size")
    L.append("<run>/corpus_index.tsv   file / added_utc / hour / sec_since_start / size")
    L.append("```")
    if a.link:
        L.append("\n另生成 `crash_by_time/<run>/<HHMMSS>_<sha1>.crash` —— 崩溃工件按发现时刻命名的硬链接镜像。")
    if a.link_corpus:
        L.append("另生成 `corpus_by_time/<run>/<HHMMSS>_<sha1>` —— corpus 按入语料时刻命名的硬链接镜像（硬链接，不占额外空间）。")

    out = os.path.join(root, "hourly_crashes.md")
    open(out, "w").write("\n".join(L) + "\n")
    json.dump(rows, open(os.path.join(root, "hourly_crashes.json"), "w"), indent=2)
    print("\n".join(L))
    print(f"\n已写出 {out}")


if __name__ == "__main__":
    main()

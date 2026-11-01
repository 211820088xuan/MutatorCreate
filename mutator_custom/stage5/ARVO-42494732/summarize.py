#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""summarize.py —— default vs custom 对比实验汇总（含可选重放）

用法：
    summarize.py [实验根目录] [--replay none|oneshot|perfile|both] [--jobs N]

  --replay none     只解析 run.log（快，默认）
  --replay oneshot  调 replay.py 做「整 corpus 一个进程」的重放
  --replay perfile  调 replay.py 做「每个文件一个子进程」的重放
  --replay both     两种都做，并给出对比

产出：
    <root>/summary.json      每次运行的日志指标
    <root>/replay_*.md|json 若启用重放（由 replay.py 生成）
"""
import argparse
import json
import os
import re
import statistics as st
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))



def crash_dir(d):
    """crash 文件可能在 run 根目录，也可能在 crash/ 子目录（新布局）"""
    c = os.path.join(d, "crash")
    return c if os.path.isdir(c) else d

def parse(log):
    if not os.path.exists(log):
        return None
    txt = open(log, errors="replace").read()
    # fork 模式进度行：
    #   #<execs>: cov: C ft: F corp: P exec/s S oom/timeout/crash: a/b/c time: Ts job: J
    prog = re.findall(
        r"#(\d+): cov: (\d+) ft: (\d+) corp: (\d+) exec/s (\d+) "
        r"oom/timeout/crash: (\d+)/(\d+)/(\d+) time: (\d+)s", txt)
    if prog:
        e, c, f, p_, es, oom, to, cr, t = prog[-1]
        return {"execs": int(e), "cov_max": int(c), "ft_max": int(f),
                "corpus": int(p_), "exec_per_s": int(es),
                "crashes": int(cr), "time_s": int(t)}
    return {"execs": None, "cov_max": None, "ft_max": None, "corpus": None,
            "exec_per_s": None, "crashes": None, "time_s": None}


def discover(root):
    """扫描 root 下所有含 corpus/ 的子目录，解析成 (arm, rep)。"""
    out = []
    for name in sorted(os.listdir(root)):
        d = os.path.join(root, name)
        if not os.path.isdir(os.path.join(d, "corpus")):
            continue
        arm, _, rep = name.rpartition("_")
        out.append({"name": name, "dir": d, "arm": arm or name, "rep": rep or "?"})
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("root", nargs="?", default="/exp/fuzz_exp")
    ap.add_argument("--replay", choices=["none", "oneshot", "perfile", "both"],
                    default="none", help="重放模式；缺省 none（只解析日志）")
    ap.add_argument("--jobs", type=int, default=10, help="perfile 并行度")
    ap.add_argument("--max-len", default="auto")
    ap.add_argument("--force-replay", action="store_true")
    a = ap.parse_args()

    root = os.path.abspath(a.root.rstrip("/"))

    # ---------- 可选：先跑重放 ----------
    replay_ok = False
    if a.replay != "none":
        cmd = [sys.executable, os.path.join(HERE, "replay.py"),
               "--root", root, "--mode", a.replay,
               "--jobs", str(a.jobs), "--max-len", a.max_len]
        if a.force_replay:
            cmd.append("--force")
        print(f"=== 调用重放: {' '.join(cmd)}")
        r = subprocess.run(cmd)
        replay_ok = (r.returncode == 0)
        if not replay_ok:
            print(f"  [警告] 重放失败（退出码 {r.returncode}），继续只输出日志指标")
        print()

    # ---------- 读日志指标 ----------
    rows = []
    for it in discover(root):
        d = it["dir"]
        r = parse(os.path.join(d, "run.log"))
        if not r:
            continue
        crashes = [f for f in os.listdir(crash_dir(d)) if f.startswith("crash-")]
        r.update(mode=it["arm"], rep=it["rep"], name=it["name"], dir=d,
                 crash_files=len(crashes),
                 corpus_files=len(os.listdir(os.path.join(d, "corpus"))))
        for mode in ("oneshot", "perfile"):
            p = os.path.join(d, "replay", mode, "coverage.json")
            if os.path.exists(p):
                r[mode] = json.load(open(p)).get("covered_edges")
        rows.append(r)

    if not rows:
        print("没有找到任何运行结果")
        return 1

    arms = sorted({r["mode"] for r in rows})
    replay_modes = [m for m in ("oneshot", "perfile") if any(r.get(m) for r in rows)]
    has_replay = bool(replay_modes)

    print("# fork fuzz 对比实验汇总\n")
    print(f"实验根目录：`{root}`")
    print(f"重放模式：`{a.replay}`" +
          ("" if a.replay == "none" else f"（{'成功' if replay_ok else '失败'}）") + "\n")

    # 1. 明细
    print("## 1. 每次运行明细\n")
    hdr = "| 运行 | 执行次数 | corpus | fork `cov:` | 特征数 | 崩溃数 |"
    sep = "|---|---|---|---|---|---|"
    for m in replay_modes:
        hdr += f" {m} |"
        sep += "---|"
    print(hdr)
    print(sep)
    for r in rows:
        line = (f"| {r['name']} | {r['execs'] or 0} | {r['corpus_files']} | "
                f"{r['cov_max'] or 0} | {r['ft_max'] or 0} | {r['crashes']} |")
        for m in replay_modes:
            v = r.get(m)
            line += f" {v if v is not None else '-'} |"
        print(line)

    # 2. 按臂
    print("\n## 2. 按臂统计\n")
    hdr2 = "| 臂 | 次数 | fork `cov:` 均值 | 范围 | 崩溃总数"
    sep2 = "|---|---|---|---|---|"
    for m in replay_modes:
        hdr2 += f" | {m} 均值"
        sep2 += "---|"
    print(hdr2)
    print(sep2)
    for arm in arms:
        g = [r for r in rows if r["mode"] == arm]
        covs = [r["cov_max"] or 0 for r in g]
        line = (f"| {arm} | {len(g)} | {st.mean(covs):.0f} | "
                f"{min(covs)}~{max(covs)} | {sum(r['crashes'] for r in g)} |")
        for m in replay_modes:
            vals = [r[m] for r in g if r.get(m)]
            line += f" {st.mean(vals):.0f} |" if vals else " - |"
        print(line)

    # 3. 两臂差异
    if len(arms) == 2:
        print("\n## 3. 两臂差异\n")
        print(f"基准 `{arms[0]}` vs 对比 `{arms[1]}`\n")
        print("| 口径 | 基准均值 | 对比均值 | 差异 | 配对胜出 |")
        print("|---|---|---|---|---|")
        a0 = [r for r in rows if r["mode"] == arms[0]]
        a1 = [r for r in rows if r["mode"] == arms[1]]
        metrics = [("cov_max", "fork `cov:`")] + [(m, m) for m in replay_modes]
        for key, name in metrics:
            v0 = [r.get(key) for r in a0 if r.get(key)]
            v1 = [r.get(key) for r in a1 if r.get(key)]
            if not (v0 and v1):
                continue
            m0, m1 = st.mean(v0), st.mean(v1)
            wins = sum(1 for i in range(min(len(v0), len(v1))) if v1[i] > v0[i])
            print(f"| {name} | {m0:.0f} | {m1:.0f} | {(m1/m0-1)*100:+.2f}% | "
                  f"{wins}/{min(len(v0), len(v1))} |")

    # 4. 崩溃文件
    print("\n## 4. 崩溃文件\n")
    found = False
    for r in rows:
        if r["crash_files"]:
            found = True
            print(f"### {r['name']}（{r['crash_files']} 个）\n")
            for f in sorted(os.listdir(crash_dir(r["dir"]))):
                if f.startswith("crash-"):
                    print(f"- `{f}` ({os.path.getsize(os.path.join(crash_dir(r['dir']), f))} B)")
    if not found:
        print("（无崩溃文件）")

    json.dump(rows, open(os.path.join(root, "summary.json"), "w"), indent=1)
    print(f"\n已写出 `{os.path.join(root, 'summary.json')}`")
    if has_replay:
        print(f"重放明细见 `{os.path.join(root, 'replay_summary.md')}`")
    return 0


if __name__ == "__main__":
    sys.exit(main())

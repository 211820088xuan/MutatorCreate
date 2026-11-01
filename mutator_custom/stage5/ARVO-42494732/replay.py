#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""replay.py —— 统一的两种重放机制（供 fuzz 实验调用）

两种模式：

  oneshot : 整个 corpus 放进**一个进程**跑完（`-merge=1`）
            · 可复现，与 fork 模式的 in-run 覆盖率最接近
            · 适合作为两臂对比的主指标

  perfile : corpus 里**每个文件单独起一个子进程**，各取其边集后求并集
            · 可复现，衡量「单输入从零开始」能覆盖多少（下界）
            · 由于跨输入状态预热，数值明显低于 oneshot（实测约 50%）
            · 适合单输入可达性分析 / 崩溃归因

用法：
    replay.py --root /exp/fuzz_exp --mode oneshot
    replay.py --root /exp/fuzz_exp --mode perfile --jobs 10
    replay.py --root /exp/fuzz_exp --mode both
    replay.py --root /exp/fuzz_exp --mode oneshot --runs default_1,custom_1

产出（每个 run 目录下）：
    replay/oneshot/coverage.json
    replay/perfile/coverage.json   （含 per_file.tsv / edges.txt）

汇总：
    <root>/replay_summary.md
    <root>/replay_results.json
"""
import argparse
import json
import os
import re
import shutil
import statistics
import subprocess
import sys
import tempfile
from concurrent.futures import ThreadPoolExecutor

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from replay_perfile import replay_one, total_edges_of  # noqa: E402


# ---------------------------------------------------------------- 工具
def find_runs(root):
    """找出所有含 corpus/ 与 run.log 的子目录，按名字排序。"""
    out = []
    for name in sorted(os.listdir(root)):
        d = os.path.join(root, name)
        if os.path.isdir(os.path.join(d, "corpus")):
            out.append(name)
    return out


def run_max_len(corpus):
    """用 corpus 里最大的文件尺寸作为 max_len，避免截断、也不放大。"""
    m = 0
    for f in os.listdir(corpus):
        p = os.path.join(corpus, f)
        if os.path.isfile(p):
            m = max(m, os.path.getsize(p))
    return max(m, 1)


def find_binary(root):
    for cand in (os.path.join(root, "llvmfuzz"),
                 os.path.join(os.path.dirname(root.rstrip("/")), "llvmfuzz")):
        if os.path.exists(cand):
            return cand
    return None


# ---------------------------------------------------------------- oneshot
def oneshot(run_dir, binary, max_len, force=False):
    cache = os.path.join(run_dir, "replay", "oneshot", "coverage.json")
    if os.path.exists(cache) and not force:
        d = json.load(open(cache))
        if d.get("covered_edges") is not None:
            return d
    corpus = os.path.join(run_dir, "corpus")
    outdir = os.path.dirname(cache)
    os.makedirs(outdir, exist_ok=True)
    work = tempfile.mkdtemp(prefix="oneshot_")
    try:
        out = os.path.join(work, "out")
        os.makedirs(out)
        cf = os.path.join(work, "cf")
        r = subprocess.run(
            [binary, "-merge=1", f"-max_len={max_len}",
             f"-merge_control_file={cf}", out, corpus],
            capture_output=True, text=True, timeout=7200,
            env=dict(os.environ, ASAN_OPTIONS="detect_leaks=0",
                     LSAN_OPTIONS="detect_leaks=0"))
        log = (r.stdout or "") + (r.stderr or "")
        m = re.findall(r"(\d+) new coverage edges", log)
        covered = int(m[-1]) if m else None
        total = total_edges_of(log) or 0
        # 同时存一份 PC 集合（来自控制文件），便于与 perfile 交叉核对
        pcs = set()
        if os.path.exists(cf):
            for line in open(cf, errors="ignore"):
                if line.startswith("COV "):
                    pcs.update(int(t) for t in line.split()[2:] if t.isdigit())
        if pcs:
            open(os.path.join(outdir, "edges.txt"), "w").write(
                "\n".join(map(str, sorted(pcs))) + "\n")
        d = {"run": os.path.basename(run_dir.rstrip("/")), "mode": "oneshot",
             "files": len(os.listdir(corpus)),
             "covered_edges": covered,
             "covered_from_cf": len(pcs),
             "total_edges": total,
             "coverage_rate": round(covered / total * 100, 4) if (covered and total) else 0.0}
        json.dump(d, open(cache, "w"), indent=2)
        return d
    finally:
        shutil.rmtree(work, ignore_errors=True)


# ---------------------------------------------------------------- perfile
def perfile(run_dir, binary, max_len, jobs, force=False):
    cache = os.path.join(run_dir, "replay", "perfile", "coverage.json")
    if os.path.exists(cache) and not force:
        d = json.load(open(cache))
        if d.get("files", 0) > 0:
            return d
    corpus = os.path.join(run_dir, "corpus")
    files = sorted(os.listdir(corpus))
    outdir = os.path.dirname(cache)
    os.makedirs(outdir, exist_ok=True)
    work = tempfile.mkdtemp(prefix="perfile_")
    all_pcs, rows, total = set(), [], None
    try:
        with ThreadPoolExecutor(max_workers=jobs) as ex:
            futs = {ex.submit(replay_one, binary, os.path.join(corpus, f),
                              max_len, work): f for f in files}
            for fut, fn in futs.items():
                pcs, status, log = fut.result()
                if total is None and log:
                    total = total_edges_of(log)
                all_pcs |= pcs
                rows.append((fn, len(pcs), status))
    finally:
        shutil.rmtree(work, ignore_errors=True)

    rows.sort()
    open(os.path.join(outdir, "edges.txt"), "w").write(
        "\n".join(map(str, sorted(all_pcs))) + "\n")
    with open(os.path.join(outdir, "per_file.tsv"), "w") as f:
        f.write("file\tedges\tstatus\n")
        for r in rows:
            f.write(f"{r[0]}\t{r[1]}\t{r[2]}\n")

    failed = [r for r in rows if r[2] != "ok"]
    detail = {}
    for r in failed:
        detail[r[2]] = detail.get(r[2], 0) + 1
    total = total or 0
    d = {"run": os.path.basename(run_dir.rstrip("/")), "mode": "perfile",
         "files": len(files),
         "files_ok": len(rows) - len(failed), "files_failed": len(failed),
         "failed_detail": detail,
         "covered_edges": len(all_pcs), "total_edges": total,
         "coverage_rate": round(len(all_pcs) / total * 100, 4) if total else 0.0}
    json.dump(d, open(cache, "w"), indent=2)
    return d


# ---------------------------------------------------------------- main
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", required=True, help="fuzz 实验根目录（含 default_1/ custom_1/ 等）")
    ap.add_argument("--mode", choices=["oneshot", "perfile", "both"], default="oneshot")
    ap.add_argument("--jobs", type=int, default=10, help="perfile 并行度")
    ap.add_argument("--max-len", default="auto", help="'auto' 取 corpus 最大文件尺寸，或给具体数字")
    ap.add_argument("--runs", default=None, help="逗号分隔的 run 名，缺省全部")
    ap.add_argument("--force", action="store_true", help="忽略缓存重算")
    a = ap.parse_args()

    root = os.path.abspath(a.root.rstrip("/"))
    binary = find_binary(root)
    if not binary:
        sys.exit(f"在 {root} 或其上级找不到 llvmfuzz")
    runs = a.runs.split(",") if a.runs else find_runs(root)
    modes = ["oneshot", "perfile"] if a.mode == "both" else [a.mode]

    print(f"root   = {root}")
    print(f"binary = {binary}")
    print(f"modes  = {modes}")
    print(f"runs   = {len(runs)} 个\n")

    results = []
    for run in runs:
        rd = os.path.join(root, run)
        corpus = os.path.join(rd, "corpus")
        if not os.path.isdir(corpus):
            print(f"[skip] {run}: 没有 corpus/")
            continue
        ml = run_max_len(corpus) if a.max_len == "auto" else int(a.max_len)
        rec = {"run": run, "files": len(os.listdir(corpus)), "max_len": ml}
        for mode in modes:
            fn = oneshot if mode == "oneshot" else (
                lambda *args, **kw: perfile(*args, jobs=a.jobs, **kw))
            d = fn(rd, binary, ml, force=a.force)
            rec[mode] = d.get("covered_edges")
            rec[mode + "_rate"] = d.get("coverage_rate")
            rec[mode + "_fail"] = d.get("files_failed", 0)
            print(f"  {run:<11} {mode:<8} covered={d.get('covered_edges')} "
                  f"({d.get('coverage_rate')}%)")
        # fork 模式 in-run cov，便于三方对照
        log = os.path.join(rd, "run.log")
        if os.path.exists(log):
            m = re.findall(r"cov: (\d+)", open(log, errors="ignore").read())
            rec["fork"] = int(m[-1]) if m else None
        results.append(rec)

    json.dump(results, open(os.path.join(root, "replay_results.json"), "w"), indent=2)

    # ---- 汇总文档 ----
    L = ["# 重放覆盖率结果\n",
         f"根目录：`{root}`", f"模式：{', '.join(modes)}\n"]

    hdr = "| run | corpus 文件数 | max_len | fork `cov:` |"
    sep = "|---|---|---|---|"
    for m in modes:
        hdr += f" {m} |"
        sep += "---|"
    if len(modes) == 2:
        hdr += " perfile/oneshot |"
        sep += "---|"
    L.append(hdr)
    L.append(sep)
    for r in results:
        line = f"| {r['run']} | {r['files']} | {r['max_len']} | {r.get('fork')} |"
        for m in modes:
            line += f" {r.get(m)} |"
        if len(modes) == 2 and r.get("oneshot") and r.get("perfile"):
            line += f" {r['perfile']/r['oneshot']*100:.1f}% |"
        L.append(line)

    # 按臂聚合（run 名形如 default_1 / custom_1）
    def arm_of(name):
        return name.rsplit("_", 1)[0] if "_" in name else name

    arms = sorted({arm_of(r["run"]) for r in results},
                  key=lambda x: (x != "default", x))
    if len(arms) > 1:
        L.append("\n## 按臂聚合\n")
        hdr2 = "| 臂 | 次数 |"
        sep2 = "|---|---|"
        for m in modes:
            hdr2 += f" {m} 均值 |"
            sep2 += "---|"
        L.append(hdr2)
        L.append(sep2)
        for arm in arms:
            g = [r for r in results if arm_of(r["run"]) == arm]
            line = f"| {arm} | {len(g)} |"
            for m in modes:
                vals = [r[m] for r in g if r.get(m)]
                line += f" {statistics.mean(vals):.0f} |" if vals else " - |"
            L.append(line)

        L.append("\n## 两臂差异\n")
        if len(arms) == 2:
            a0 = [r for r in results if arm_of(r["run"]) == arms[0]]
            a1 = [r for r in results if arm_of(r["run"]) == arms[1]]
            L.append(f"基准臂 `{arms[0]}`，对比臂 `{arms[1]}`\n")
            L.append("| 口径 | 基准均值 | 对比均值 | 差异 |")
            L.append("|---|---|---|---|")
            for key, name in [("fork", "fork `cov:`")] + [(m, m) for m in modes]:
                v0 = [r[key] for r in a0 if r.get(key)]
                v1 = [r[key] for r in a1 if r.get(key)]
                if v0 and v1:
                    m0, m1 = statistics.mean(v0), statistics.mean(v1)
                    L.append(f"| {name} | {m0:.0f} | {m1:.0f} | {(m1/m0-1)*100:+.2f}% |")

    out = os.path.join(root, "replay_summary.md")
    open(out, "w").write("\n".join(L) + "\n")
    print(f"\n已写出 {out}")
    print(f"已写出 {os.path.join(root, 'replay_results.json')}")


if __name__ == "__main__":
    main()

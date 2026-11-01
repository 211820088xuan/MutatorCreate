#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""compare_cov.py —— 三种覆盖率口径对比

1. fork   : libFuzzer fork 模式运行时报告的 cov:（run.log 最后一行）
2. oneshot: 一次性重放，整个 corpus 在一个进程里跑完（-merge=1）
3. perfile: 逐文件重放，每个文件一个子进程，取边集求并集

用法：
    compare_cov.py <fuzz_exp_dir> [--jobs N] [--force]

产出：
    <fuzz_exp_dir>/coverage_compare.json   机器可读
    <fuzz_exp_dir>/COVERAGE_COMPARISON.md  对比文档
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

RUNS = [f"default_{i}" for i in range(1, 6)] + [f"custom_{i}" for i in range(1, 6)]


def in_run_cov(run_dir):
    log = os.path.join(run_dir, "run.log")
    if not os.path.exists(log):
        return None
    txt = open(log, errors="ignore").read()
    m = re.findall(r"cov: (\d+)", txt)
    return int(m[-1]) if m else None


def oneshot_cov(binary, corpus, max_len, cache):
    if os.path.exists(cache):
        return json.load(open(cache)).get("covered")
    d = tempfile.mkdtemp(prefix="oneshot_")
    try:
        out = os.path.join(d, "out")
        os.makedirs(out)
        cf = os.path.join(d, "cf")
        r = subprocess.run(
            [binary, "-merge=1", f"-max_len={max_len}",
             f"-merge_control_file={cf}", out, corpus],
            capture_output=True, text=True, timeout=3600,
            env=dict(os.environ, ASAN_OPTIONS="detect_leaks=0",
                     LSAN_OPTIONS="detect_leaks=0"))
        log = (r.stdout or "") + (r.stderr or "")
        m = re.findall(r"(\d+) new coverage edges", log)
        covered = int(m[-1]) if m else None
        total = total_edges_of(log)
        json.dump({"covered": covered, "total": total}, open(cache, "w"))
        return covered
    finally:
        shutil.rmtree(d, ignore_errors=True)


def perfile_cov(run_dir, binary, max_len, jobs):
    p = os.path.join(run_dir, "replay", "perfile", "coverage.json")
    if os.path.exists(p):
        d = json.load(open(p))
        if d.get("files", 0) > 0:
            return d
    corpus = os.path.join(run_dir, "corpus")
    files = sorted(os.listdir(corpus))
    outdir = os.path.join(run_dir, "replay", "perfile")
    os.makedirs(outdir, exist_ok=True)
    root = tempfile.mkdtemp(prefix="pf_")
    all_pcs, rows, total = set(), [], None
    try:
        with ThreadPoolExecutor(max_workers=jobs) as ex:
            futs = {ex.submit(replay_one, binary, os.path.join(corpus, f),
                              max_len, root): f for f in files}
            for fut, fn in futs.items():
                pcs, st, log = fut.result()
                if total is None and log:
                    total = total_edges_of(log)
                all_pcs |= pcs
                rows.append((fn, len(pcs), st))
    finally:
        shutil.rmtree(root, ignore_errors=True)
    open(os.path.join(outdir, "edges.txt"), "w").write(
        "\n".join(map(str, sorted(all_pcs))) + "\n")
    with open(os.path.join(outdir, "per_file.tsv"), "w") as f:
        f.write("file\tedges\tstatus\n")
        for r in rows:
            f.write(f"{r[0]}\t{r[1]}\t{r[2]}\n")
    failed = [r for r in rows if r[2] != "ok"]
    d = {"run": os.path.basename(run_dir), "files": len(files),
         "files_ok": len(rows) - len(failed), "files_failed": len(failed),
         "covered_edges": len(all_pcs), "total_edges": total or 0}
    json.dump(d, open(os.path.join(outdir, "coverage.json"), "w"), indent=2)
    return d


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("dir")
    ap.add_argument("--jobs", type=int, default=10)
    ap.add_argument("--max-len", default="131072")
    ap.add_argument("--force", action="store_true")
    a = ap.parse_args()

    base = os.path.abspath(a.dir.rstrip("/"))
    binary = os.path.join(base, "llvmfuzz")
    if not os.path.exists(binary):
        sys.exit(f"找不到二进制: {binary}")

    rows = []
    for run in RUNS:
        rd = os.path.join(base, run)
        if not os.path.isdir(rd):
            print(f"[skip] {run} 不存在")
            continue
        corpus = os.path.join(rd, "corpus")
        nfiles = len(os.listdir(corpus)) if os.path.isdir(corpus) else 0
        cache = os.path.join(rd, "oneshot.json")
        if a.force and os.path.exists(cache):
            os.remove(cache)
        ir = in_run_cov(rd)
        os1 = oneshot_cov(binary, corpus, a.max_len, cache)
        pf = perfile_cov(rd, binary, a.max_len, a.jobs)
        rows.append(dict(run=run, arm=run.split("_")[0], files=nfiles,
                         in_run=ir, oneshot=os1, perfile=pf["covered_edges"],
                         perfile_ok=pf["files_ok"], perfile_fail=pf["files_failed"],
                         total=pf["total_edges"]))
        print(f"  {run:<10} files={nfiles:<5} in-run={ir} oneshot={os1} perfile={pf['covered_edges']}")

    json.dump(rows, open(os.path.join(base, "coverage_compare.json"), "w"), indent=2)

    # ---------- 生成文档 ----------
    L = []
    L.append("# 三种覆盖率口径对比\n")
    L.append("被测目标：libredwg `dxf_objects_read` UAF（ARVO-42494732），仓库 commit `ff69eeda66`。")
    L.append("数据：`fuzz_exp3`，2 臂 × 5 次 × 3 小时（10,800 秒）fork 模式 fuzz。\n")

    L.append("## 1. 三种口径的定义\n")
    L.append("| 口径 | 含义 | 如何得到 |")
    L.append("|---|---|---|")
    L.append("| **fork** | fuzz 运行时 libFuzzer 自己报的 `cov:` | `run.log` 最后一行 `cov: N` |")
    L.append("| **oneshot** | 把 corpus 全部输入放**同一个进程**里跑一遍的并集 | `-merge=1` 整个 corpus，读 `N new coverage edges` |")
    L.append("| **perfile** | corpus 里**每个文件单独起一个子进程**，各取其边集后求并集 | 逐文件 `-merge=1`，读控制文件 `COV` 行，求并集 |")
    L.append("")

    L.append("## 2. 逐 run 结果\n")
    L.append("| run | corpus 文件数 | fork `cov:` | oneshot | perfile | perfile/fork | perfile/oneshot |")
    L.append("|---|---|---|---|---|---|---|")
    for r in rows:
        fr = f"{r['perfile']/r['in_run']*100:.1f}%" if r["in_run"] else "-"
        fo = f"{r['perfile']/r['oneshot']*100:.1f}%" if r["oneshot"] else "-"
        L.append(f"| {r['run']} | {r['files']} | {r['in_run']} | {r['oneshot']} | "
                 f"{r['perfile']} | {fr} | {fo} |")
    L.append("")

    L.append("## 3. 按臂聚合\n")
    L.append("| 臂 | 次数 | fork 均值 | oneshot 均值 | perfile 均值 | perfile/fork | perfile/oneshot |")
    L.append("|---|---|---|---|---|---|---|")
    for arm in ("default", "custom"):
        g = [r for r in rows if r["arm"] == arm]
        if not g:
            continue
        f_ = statistics.mean(r["in_run"] for r in g)
        o_ = statistics.mean(r["oneshot"] for r in g)
        p_ = statistics.mean(r["perfile"] for r in g)
        L.append(f"| {arm} | {len(g)} | {f_:.0f} | {o_:.0f} | {p_:.0f} | "
                 f"{p_/f_*100:.1f}% | {p_/o_*100:.1f}% |")
    L.append("")

    d = [r for r in rows if r["arm"] == "default"]
    c = [r for r in rows if r["arm"] == "custom"]
    if d and c:
        L.append("## 4. 两臂差异（custom vs default）\n")
        L.append("| 口径 | default 均值 | custom 均值 | 差异 | 配对胜出 |")
        L.append("|---|---|---|---|---|")
        for key, name in (("in_run", "fork"), ("oneshot", "oneshot"), ("perfile", "perfile")):
            dv = [r[key] for r in d]
            cv = [r[key] for r in c]
            dm, cm = statistics.mean(dv), statistics.mean(cv)
            wins = sum(1 for i in range(min(len(dv), len(cv))) if cv[i] > dv[i])
            L.append(f"| {name} | {dm:.0f} | {cm:.0f} | {(cm/dm-1)*100:+.2f}% | {wins}/{len(dv)} |")
        L.append("")

    L.append("## 5. 口径之间的关系与成因\n")
    L.append("### oneshot ≈ fork（差 3~5%）")
    L.append("两者都是「多个输入在同一个进程里连续执行」，全局/静态状态会被前面的输入预热，")
    L.append("所以能走到冷启动走不到的路径。")
    L.append("")
    L.append("### perfile < oneshot（约 50~60%）")
    L.append("**跨输入状态效应**。实测（`fuzz_exp3/corpus` 的 6 个原始种子）：")
    L.append("")
    L.append("| 种子 | 单独执行 `cov:` |")
    L.append("|---|---|")
    L.append("| sample_2013.dxf | 4,788 |")
    L.append("| sample_2018.dxf | 4,760 |")
    L.append("| sample_r14.dxf | 3,760 |")
    L.append("| v.dxf | 3,123 |")
    L.append("| Constraints.dxf | 1,680 |")
    L.append("| Leader.dxf | 1,494 |")
    L.append("")
    L.append("| 同一批 6 个文件 | 覆盖 |")
    L.append("|---|---|")
    L.append("| 逐文件冷启动并集 | **5,981** |")
    L.append("| 放一个进程跑（`-runs=0`） | **9,774** |")
    L.append("| 放一个进程跑（`-merge=1`） | **9,774** |")
    L.append("")
    L.append("同样 6 个文件、同样内容，一个进程能到 9,774，逐个冷启动只有 5,981（差 63%）。")
    L.append("6 个种子均**没有崩溃**（`crash=0`），所以不是解析被截断，而是状态预热。")
    L.append("")
    L.append("### 为什么 fork 的 `cov:` 略高于 oneshot")
    L.append("fork 模式下 `cov:` 是 `FuzzFork::Cov` 这个**只增不减的累积器**")
    L.append("（`FuzzerFork.cpp:205`，只由每次 job 结束时 `CrashResistantMerge` 的 `NewCov` 追加），")
    L.append("而 oneshot 是对最终 corpus 做的单次全量 merge。两者不完全等价。")
    L.append("")

    L.append("## 6. 结论与建议\n")
    L.append("| 口径 | 可复现 | 反映什么 | 建议用途 |")
    L.append("|---|---|---|---|")
    L.append("| fork `cov:` | ❌ 不可从存档数据重算 | fuzzer 实际探索量（含累积器误差） | 参考 |")
    L.append("| oneshot | ✅ 可复现 | 「这些输入在同进程连续执行」的覆盖 | **两臂对比主指标** |")
    L.append("| perfile | ✅ 可复现 | 「单输入从零开始能达到」的覆盖（下界） | 单输入可达性 / 崩溃归因 |")
    L.append("")
    L.append("**要点**：perfile 系统性低估，不能直接与 fuzzer 覆盖率比较；")
    L.append("但三者在两臂之间的对比结论应当一致——若不一致，说明差异本身不稳定。")
    L.append("")

    out = os.path.join(base, "COVERAGE_COMPARISON.md")
    open(out, "w").write("\n".join(L) + "\n")
    print(f"\n已生成 {out}")
    print(f"已生成 {os.path.join(base, 'coverage_compare.json')}")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""replay_perfile.py —— 逐文件子进程重放，取边集后求并集

方法（按要求）：
  · 对 corpus 里的**每一个文件**单独起一个子进程
  · 子进程用 `-merge=1`（空的输出目录 + 空的候选目录），控制文件里
    `COV <idx> <pc1> <pc2> ...` 就是该文件覆盖到的 PC 集合
  · 把所有文件的 PC 集合求并集 → 该 run 的最终覆盖

相比一次性 `-merge=1` 整目录的好处：
  · 某个文件崩溃只影响它自己那个子进程，不会中断整批重放
  · 每个文件的结果可单独审计（失败/崩溃的会记录状态）

用法（容器内）：
    replay_perfile.py <run_dir> [--jobs N] [--max-len N]
示例：
    replay_perfile.py /exp/fuzz_exp/default_1 --jobs 8

产出：
    <run_dir>/replay_perfile/edges.txt       排序后的 PC 列表
    <run_dir>/replay_perfile/coverage.json   {covered_edges,total_edges,files_ok,files_failed,...}
    <run_dir>/replay_perfile/per_file.tsv    每个文件: 文件名 / 边数 / 状态
"""
import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from concurrent.futures import ThreadPoolExecutor

DEFAULT_BIN = None  # 由 --binary 指定，缺省用 run_dir 同级的 llvmfuzz


def parse_pcs(control_file):
    """从 merge 控制文件里取 COV 行。格式: COV <idx> <pc> <pc> ..."""
    pcs = set()
    if not os.path.exists(control_file):
        return pcs
    with open(control_file, errors="ignore") as f:
        for line in f:
            if line.startswith("COV "):
                for tok in line.split()[2:]:
                    if tok.isdigit():
                        pcs.add(int(tok))
    return pcs


def total_edges_of(log_text):
    m = re.search(r"\((\d+)\s+inline 8-bit counters\)", log_text)
    return int(m.group(1)) if m else None


def replay_one(binary, path, max_len, workroot):
    """给单个文件起一个子进程，返回 (pcs, status)。"""
    d = tempfile.mkdtemp(dir=workroot)
    try:
        indir = os.path.join(d, "in")
        outdir = os.path.join(d, "out")
        os.makedirs(indir)
        os.makedirs(outdir)
        # 硬链接优先（同文件系统），失败则复制
        dst = os.path.join(indir, os.path.basename(path))
        try:
            os.link(path, dst)
        except OSError:
            shutil.copy2(path, dst)
        cf = os.path.join(d, "cf")
        r = subprocess.run(
            [binary, "-merge=1", f"-max_len={max_len}",
             f"-merge_control_file={cf}", outdir, indir],
            capture_output=True, text=True, timeout=180,
            env=dict(os.environ, ASAN_OPTIONS="detect_leaks=0",
                     LSAN_OPTIONS="detect_leaks=0"),
        )
        log = (r.stdout or "") + (r.stderr or "")
        pcs = parse_pcs(cf)
        if pcs:
            return pcs, "ok", log
        if "AddressSanitizer" in log or "ERROR:" in log:
            return set(), "crash-or-error", log
        return set(), "no-cov", log
    except subprocess.TimeoutExpired:
        return set(), "timeout", ""
    except Exception as e:  # noqa: BLE001
        return set(), f"exception:{e}", ""
    finally:
        shutil.rmtree(d, ignore_errors=True)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("run_dir")
    ap.add_argument("--jobs", type=int, default=8)
    ap.add_argument("--max-len", default="131072")
    ap.add_argument("--binary", default=None,
                    help="被测二进制，缺省 <run_dir>/../llvmfuzz")
    a = ap.parse_args()

    binary = a.binary or os.path.join(
        os.path.dirname(os.path.abspath(a.run_dir.rstrip("/"))), "llvmfuzz")
    if not os.path.exists(binary):
        sys.exit(f"找不到被测二进制: {binary}")

    corpus = os.path.join(a.run_dir, "corpus")
    files = sorted(os.listdir(corpus)) if os.path.isdir(corpus) else []
    if not files:
        sys.exit(f"corpus 为空或不存在: {corpus}")

    outdir = os.path.join(a.run_dir, "replay_perfile")
    os.makedirs(outdir, exist_ok=True)
    workroot = tempfile.mkdtemp(prefix="perfile_")
    print(f"[{os.path.basename(a.run_dir)}] {len(files)} 个文件, {a.jobs} 路并行")

    all_pcs = set()
    total = None
    rows = []
    done = 0
    try:
        with ThreadPoolExecutor(max_workers=a.jobs) as ex:
            futs = {
                ex.submit(replay_one, binary, os.path.join(corpus, f),
                          a.max_len, workroot): f
                for f in files
            }
            for fut, fname in futs.items():
                pcs, status, log = fut.result()
                if total is None and log:
                    total = total_edges_of(log)
                all_pcs |= pcs
                rows.append((fname, len(pcs), status))
                done += 1
                if done % 200 == 0:
                    print(f"  {done}/{len(files)} ... 并集 {len(all_pcs)} 边")
    finally:
        shutil.rmtree(workroot, ignore_errors=True)

    rows.sort()
    with open(os.path.join(outdir, "edges.txt"), "w") as f:
        f.write("\n".join(map(str, sorted(all_pcs))) + "\n")
    with open(os.path.join(outdir, "per_file.tsv"), "w") as f:
        f.write("file\tedges\tstatus\n")
        for r in rows:
            f.write(f"{r[0]}\t{r[1]}\t{r[2]}\n")

    failed = [r for r in rows if r[2] != "ok"]
    summary = {
        "run": os.path.basename(a.run_dir.rstrip("/")),
        "files": len(files),
        "files_ok": len(rows) - len(failed),
        "files_failed": len(failed),
        "failed_detail": {r[2]: sum(1 for x in failed if x[2] == r[2]) for r in failed} or {},
        "covered_edges": len(all_pcs),
        "total_edges": total and int(total) or 0,
        "coverage_rate": round(len(all_pcs) / total * 100, 4) if total else 0.0,
    }
    with open(os.path.join(outdir, "coverage.json"), "w") as f:
        json.dump(summary, f, indent=2)

    print(f"  完成: 覆盖 {summary['covered_edges']}/{summary['total_edges']} "
          f"({summary['coverage_rate']}%)  成功 {summary['files_ok']} 失败 {summary['files_failed']}")
    if failed:
        print(f"  失败类型: {summary['failed_detail']}")
    print(f"  产出: {outdir}")


if __name__ == "__main__":
    main()

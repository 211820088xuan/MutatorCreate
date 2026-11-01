#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""arvo_repro.py —— 批量复现 ARVO 崩溃，输出格式与 reproduce_crash 完全一致。

对每条 case：
  1. docker pull n132/arvo:<id>-vul
  2. 抠 /tmp/poc、/out、/src
  3. docker run 验证崩溃（捕获输出）
  4. 解析 crash_type + 帧
  5. 建 CPG（c2cpg，按 (project, src_head) 去重）
  6. 落盘，与 reproduce_crash 同构：
       artifacts/by_crash_type/<type>/<project>/<san>/<commit>/<id>/
         ├── testcase      输入
         ├── report.log    崩溃输出（带头部）
         ├── INFO.txt      元数据
         └── replay.sh     重放脚本
       artifacts/binaries/<project>/<san>/<commit>/<target>
       artifacts/logs/reproduce/<id>.log
       repro_dataset.jsonl（追加一行，同 schema）
  7. docker rmi（镜像不保留）
"""
from __future__ import annotations
import hashlib, json, os, re, shutil, subprocess, sys, time
from concurrent.futures import ThreadPoolExecutor, as_completed

BASE = "/root/gyx/mutator_create"
RC = os.path.join(BASE, "reproduce_crash")
ART = os.path.join(RC, "artifacts")
BY_TYPE = os.path.join(ART, "by_crash_type")
BINS = os.path.join(ART, "binaries")
LOGS = os.path.join(ART, "logs", "reproduce")
CPG = os.path.join(BASE, "cpg_files")
LEDGER = os.path.join(RC, "repro_dataset.jsonl")
WORK = "/tmp/arvo_work"
C2CPG = "/usr/local/lib/python3.10/dist-packages/pyjoern/bin/joern-cli/frontends/c2cpg/bin/c2cpg"

sys.path.insert(0, RC)
from repro_common import normalize_crash_type  # noqa: E402

FRAME_RE = re.compile(r"^\s*#\d+\s+0x[0-9a-f]+\s+in\s+(\S+)\s+(\S+):(\d+)")
TYPE_RE = re.compile(r"(ERROR: AddressSanitizer: [\w-]+|runtime error: [\w -]+|SUMMARY: \w+Sanitizer: [\w -]+)")


def sh(cmd, timeout=1800, **kw):
    return subprocess.run(cmd, capture_output=True, text=True, errors="replace",
                          timeout=timeout, stdin=subprocess.DEVNULL, **kw)


def parse_report(out: str):
    """从崩溃输出里取 crash_type + 帧（file:line）。"""
    ctype = None
    m = re.search(r"ERROR: AddressSanitizer: ([\w-]+)", out)
    if m:
        ctype = {"heap-buffer-overflow": "Heap-buffer-overflow", "stack-buffer-overflow": "Stack-buffer-overflow",
                 "global-buffer-overflow": "Global-buffer-overflow", "heap-use-after-free": "Heap-use-after-free",
                 "stack-use-after-return": "Stack-use-after-return", "heap-double-free": "Heap-double-free",
                 "use-after-poison": "Use-after-poison"}.get(m.group(1))
        w = re.search(r"(READ|WRITE) of size (\d+)", out)
        if w:
            ctype = f"{ctype} {w.group(1)} {w.group(2)}"
    if not ctype:
        m = re.search(r"runtime error: .*index (-?\d+) out of bounds", out)
        if m: ctype = "Index-out-of-bounds"
    if not ctype:
        m = re.search(r"runtime error: ([\w -]+)", out)
        if m: ctype = m.group(1).strip()
    if not ctype:
        m = re.search(r"SUMMARY: UndefinedBehaviorSanitizer", out)
        if m: ctype = "UndefinedBehaviorSanitizer"
    frames = []
    for ln in out.splitlines():
        fm = FRAME_RE.match(ln)
        if fm: frames.append(fm.group(1))
    return ctype, frames


def process(case: dict) -> dict:
    lid = str(case["arvo"])
    project = case["project"]
    san = case.get("arvo_san") or "address"
    img = f"n132/arvo:{lid}-vul"
    work = os.path.join(WORK, lid)
    rec = {
        "osv_id": f"ARVO-{lid}", "arvo_id": lid, "project": project,
        "project_ossfuzz_dir": project, "language": case.get("language"),
        "osv_year": None,
        "fuzz_target": case.get("fuzz_target"), "target_inferred": False,
        "sanitizer": san, "sanitizer_inferred": False,
        "fuzzing_engine": None, "job_type": None, "job_arch": "x86_64",
        "crash_type_expected": case.get("ctype"),
        "crash_type_full_expected": case.get("ctype"),
        "crash_type_norm": None, "crash_cluster_id": None,
        "introducing_commit": None, "fixed_commit": case.get("fix_commit"),
        "fixed_parent": None, "fixed_real": case.get("fix_commit"),
        "pin_commit": None, "walkback_depth": None, "fixed_misattributed": None,
        "static_check_verdict": None, "static_check_why": None,
        "expected_repro_version": "arvo", "osv_degenerate_range": None,
        "degenerate_resolved": None, "commit_source": "arvo_src_head",
        "fixed_rule": None, "n_osv_pairs": None, "repo_url": case.get("repo_addr"),
        "repo_path": None, "repo_path_confidence": None, "repo_path_candidates": None,
        "testcase_path": None, "testcase_sha256": None, "testcase_size": None,
        "input_magic": None, "testcase_is_minimized": None,
        "recovered_frames": case.get("state"), "recovered_is_file_frame": None,
        "issue_id": lid, "report_url": f"https://issues.oss-fuzz.com/issues/{lid}",
        "testcase_url": None, "skip_reason": None, "notes": ["arvo"],
        "build_status": "arvo_prebuilt", "build_stage": None, "build_error_class": None,
        "build_seconds": None, "binary_dir": None, "binary_sha256": None,
        "oss_fuzz_commit": None, "pinned_commit": None, "base_builder_digest": None,
        "era_commit": None, "era_cache_hit": None,
        "reproduced_any": False, "observed_crash_type": None, "observed_frames": [],
        "exit_code": None, "signal": None, "retry_count": 0,
        "runtime_limits": "timeout=25:rss_limit_mb=2560:symbolize=1:dedup_token_length=3",
        "raw_log_path": None, "walkback_depth_actual": None,
        "verification_tier": None, "frame_match_score": None, "crash_type_match": None,
        "score_pos": None, "score_subseq": None, "score_set": None, "score_set_top3": None,
        "score_subseq_frac": None, "commit_source_prior": None, "run_status": "run",
        "repro_version": "arvo", "run_id": "arvo-repro", "run_ts": int(time.time()),
        "src_head": None, "cpg": None, "case_dir": None, "ok": False,
    }
    try:
        # 1. pull
        r = sh(["docker", "pull", img], timeout=3600)
        if r.returncode != 0:
            rec["error"] = "pull_failed"
            return rec
        # 2. create + cp
        os.makedirs(work, exist_ok=True)
        r = sh(["docker", "create", img])
        cid = r.stdout.strip()
        if not cid:
            rec["error"] = "create_failed"; return rec
        for src, dst in [("/tmp/poc", "poc"), ("/out", "out"), ("/src", "src")]:
            rr = sh(["docker", "cp", f"{cid}:{src}", os.path.join(work, dst)], timeout=900)
            if rr.returncode != 0 and dst == "poc":
                rec["error"] = "no_poc"; sh(["docker", "rm", cid]); return rec
        sh(["docker", "rm", cid])
        # 3. run
        t0 = time.time()
        rr = sh(["docker", "run", "--rm", img, "arvo"], timeout=900)
        out = (rr.stdout or "") + "\n" + (rr.stderr or "")
        secs = round(time.time() - t0, 2)
        rec["exit_code"] = rr.returncode
        # 4. parse
        ctype, frames = parse_report(out)
        rec["observed_crash_type"] = ctype
        rec["observed_frames"] = frames[:12]
        rec["crash_type_norm"] = normalize_crash_type(ctype or case.get("ctype"))
        rec["reproduced_any"] = bool(ctype or rr.returncode != 0)
        rec["seconds"] = secs
        # 5. src head + cpg
        src_root = os.path.join(work, "src")
        proj_dir = None
        if os.path.isdir(src_root):
            cands = [d for d in os.listdir(src_root)
                     if os.path.isdir(os.path.join(src_root, d)) and d not in ("afl", "libfuzzer")]
            proj_dir = next((d for d in cands if d.lower() == project.lower()), cands[0] if cands else None)
        head = ""
        if proj_dir:
            r = sh(["git", "-C", os.path.join(src_root, proj_dir), "rev-parse", "HEAD"], timeout=60)
            head = r.stdout.strip() if r.returncode == 0 else ""
        rec["src_head"] = head
        rec["fix_commit"] = case.get("fix_commit")
        if head and proj_dir:
            cpg_out = os.path.join(CPG, f"{project}_{head[:12]}.cpg")
            if not os.path.isfile(cpg_out):
                sh([C2CPG, os.path.join(src_root, proj_dir), "-o", cpg_out], timeout=1800)
            rec["cpg"] = cpg_out if os.path.isfile(cpg_out) else None
        # 6. 落盘（与 reproduce_crash 同构）
        commit = head or "unknown"
        case_dir = os.path.join(BY_TYPE, rec["crash_type_norm"] or "unknown", project, san, commit, f"ARVO-{lid}")
        os.makedirs(case_dir, exist_ok=True)
        # testcase
        poc_src = os.path.join(work, "poc")
        if os.path.isfile(poc_src):
            shutil.copy2(poc_src, os.path.join(case_dir, "testcase"))
            data = open(poc_src, "rb").read()
            rec["testcase_path"] = os.path.join(case_dir, "testcase")
            rec["testcase_sha256"] = hashlib.sha256(data).hexdigest()
            rec["testcase_size"] = len(data)
        # report.log（带头部）
        hdr = (f"# cmd: docker run --rm {img} arvo\n"
               f"# image: {img}\n# project: {project}\n# target: {case.get('fuzz_target')}\n"
               f"# sanitizer: {san}\n# exit: {rr.returncode}\n# seconds: {secs}\n"
               f"# ts: {time.strftime('%Y-%m-%dT%H:%M:%S')}\n\n===== stdout =====\n")
        open(os.path.join(case_dir, "report.log"), "w", encoding="utf-8").write(hdr + out)
        rec["raw_log_path"] = os.path.join(case_dir, "report.log")
        # binary（默认不存：replay.sh 用 ARVO 镜像；磁盘实测 407 条就占 14G）
        SAVE_BINARY = os.environ.get("ARVO_SAVE_BINARY", "0") == "1"
        out_dir = os.path.join(work, "out")
        target = case.get("fuzz_target") or ""
        if SAVE_BINARY and os.path.isdir(out_dir):
            files = [f for f in os.listdir(out_dir) if os.path.isfile(os.path.join(out_dir, f))]
            exe = next((f for f in files if f == target), files[0] if files else None)
            if exe:
                bdir = os.path.join(BINS, project, san, commit)
                os.makedirs(bdir, exist_ok=True)
                shutil.copy2(os.path.join(out_dir, exe), os.path.join(bdir, exe))
                rec["binary_dir"] = bdir
                rec["fuzz_target"] = exe
        # INFO.txt
        info = (f"ARVO-{lid}   {project} / {san}\n"
                f"唯一可执行文件  = {rec.get('fuzz_target')}\n"
                f"一条命令重放    = docker run --rm {img} arvo\n"
                f"crash_type 期望 = {case.get('ctype')}\n"
                f"crash_type 实测 = {ctype}\n"
                f"src_head        = {head}\n"
                f"fix_commit      = {case.get('fix_commit')}\n"
                f"reproduced      = {rec['reproduced_any']}\n"
                f"报告            = report.log\n"
                f"输入            = testcase\n")
        open(os.path.join(case_dir, "INFO.txt"), "w", encoding="utf-8").write(info)
        # replay.sh
        replay = ("#!/bin/sh\n"
                  f"# 重放 ARVO-{lid}（{project}/{san}）\n"
                  "HERE=$(cd \"$(dirname \"$0\")\" && pwd)\n"
                  f"docker run --rm -v \"$HERE\":/out -v \"$HERE/testcase\":/testcase \\\n"
                  f"  {img} arvo\n")
        rp = os.path.join(case_dir, "replay.sh")
        open(rp, "w", encoding="utf-8").write(replay)
        os.chmod(rp, 0o755)
        # 日志
        os.makedirs(LOGS, exist_ok=True)
        open(os.path.join(LOGS, f"ARVO-{lid}.log"), "w", encoding="utf-8").write(out)
        # 清理
        sh(["docker", "rmi", img], timeout=300)
        shutil.rmtree(work, ignore_errors=True)
        rec["case_dir"] = case_dir
        rec["ok"] = True
    except Exception as e:
        rec["error"] = f"{type(e).__name__}: {e}"
        rec["ok"] = False
    finally:
        # 无论成功/失败都清理：临时源码/二进制 + 拉下来的镜像，避免磁盘被残留撑满
        try:
            sh(["docker", "rmi", img], timeout=120)
        except Exception:
            pass
        try:
            shutil.rmtree(work, ignore_errors=True)
        except Exception:
            pass
    return rec


def main():
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--jobs", type=int, default=4)
    a = ap.parse_args()
    cases = json.load(open("/tmp/repro_1000.json"))
    # 断点续跑：跳过复现记录表里已成功的
    done = set()
    if os.path.isfile(LEDGER):
        for ln in open(LEDGER, encoding="utf-8"):
            try:
                d = json.loads(ln)
                if d.get("arvo_id") and d.get("ok"): done.add(str(d["arvo_id"]))
            except Exception:
                pass
    cases = [c for c in cases if str(c["arvo"]) not in done]
    if a.limit: cases = cases[:a.limit]
    print(f"续跑：已完成 {len(done)}，本次待跑 {len(cases)}，并发 {a.jobs}")
    # 补 fix_commit / fuzz_target
    import sqlite3
    con = sqlite3.connect("/root/gyx/arvo/data/arvo.db"); cur = con.cursor()
    for c in cases:
        cur.execute("SELECT fix_commit, fuzz_target, sanitizer FROM arvo WHERE localId=?", (str(c["arvo"]),))
        r = cur.fetchone()
        if r:
            c["fix_commit"], c["fuzz_target"] = r[0], r[1]
            c["arvo_san"] = "address" if r[2] == "asan" else r[2]
    print(f"待复现 {len(cases)} 条")
    results = []
    with ThreadPoolExecutor(max_workers=a.jobs) as ex:
        futs = {ex.submit(process, c): c for c in cases}
        for i, f in enumerate(as_completed(futs), 1):
            r = f.result()
            results.append(r)
            if i % 10 == 0 or i == len(cases):
                ok = sum(1 for x in results if x.get("ok"))
                print(f"  [{i}/{len(cases)}] ok={ok} err={i-ok}", flush=True)
            # 追加复现记录表
            with open(LEDGER, "a", encoding="utf-8") as fh:
                fh.write(json.dumps(r, ensure_ascii=False) + "\n")


if __name__ == "__main__":
    main()

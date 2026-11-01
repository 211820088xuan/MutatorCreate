#!/usr/bin/env python3
"""[N73 恢复] 重生成 221 条交付条目的 `report.log`。

**为什么需要**：`artifacts/logs/`（报告源）被当作"历史日志"删除，而 `show_repro.py:294`
的 `build_index()` 会 `shutil.rmtree(INDEX_DIR)` 整目录重建 → `_select_report()` 找不到源
→ 返回 `None` → **221 条 report.log 全部静默丢失**。审计的 N53 红线抓到了（设计有效）。
盘上无副本、复现记录表 221 条 `raw_log_path` 全部失效 → **只能重生成**。

**为什么重生成是可信的**：交付目录里的 ELF 是 `artifacts/binaries/<...>` 的**硬链接
（同一 inode、同一字节）**，testcase 也是复现记录表那一份 → `replay.sh` 跑出来的报告，
与当初 `_select_report()` 挑中的「binary_dir 一致且 exit==1」那份**同源**。

**写回位置**：`artifacts/logs/reproduce/<OSV>.log`，并补齐 `_select_report()` 要解析的
`# binary_dir:` / `# exit:` 头 → 之后任何一次 `build_index()` 都能自然选回，不会再丢。
另加 `# provenance:` 头标明是重生成的，**不冒充**原始冻结副本。
"""
from __future__ import annotations

import argparse
import concurrent.futures as cf
import json
import os
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
ART = os.path.join(HERE, "artifacts")
INDEX = os.path.join(ART, "by_crash_type")
REPRO_LOGS = os.path.join(ART, "logs", "reproduce")
DATASET = os.path.join(HERE, "repro_dataset.jsonl")
VERIFIED = ("strict", "medium", "loose")


def log(m: str) -> None:
    print(m, flush=True)


def latest_ledger() -> dict:
    """复现记录表 append-only → 同一 osv_id 取最后一行。"""
    lat: dict[str, dict] = {}
    with open(DATASET, encoding="utf-8") as f:
        for ln in f:
            ln = ln.strip()
            if not ln:
                continue
            try:
                r = json.loads(ln)
            except json.JSONDecodeError:
                continue
            if r.get("osv_id"):
                lat[r["osv_id"]] = r
    return lat


def find_entries() -> list[tuple[str, str]]:
    """→ [(osv_id, 条目目录)]，只取 verified 的交付条目。"""
    out = []
    for root, dirs, _files in os.walk(INDEX):
        dirs[:] = [d for d in dirs if not d.startswith(".")]
        base = os.path.basename(root)
        if base.startswith("OSV-") and os.path.isfile(os.path.join(root, "replay.sh")):
            out.append((base, root))
    return sorted(out)


def regenerate(osv: str, entry: str, ledger: dict, timeout: int = 1800,
               retries: int = 1) -> dict:
    """跑 `replay.sh`，把输出写成 `artifacts/logs/reproduce/<OSV>.log`。

    **[N73②] 必须重试**：历史 `replay_verification.json` 已记录 flaky 条目 ——
    `OSV-2023-948` 崩溃率仅 **12%**（加测到第 8 次才崩）、`OSV-2023-48` 需 3 次，
    且「flaky 集中在 libavc 的 ABRT/global-buffer-overflow(svc_enc_fuzzer) 与 MSAN 条目」。
    首版只跑一次 → 221 条里误判 5 条失败（实测重跑 2 次，其中 3 条就崩了）。
    """
    r = ledger.get(osv) or {}
    rp = os.path.join(entry, "replay.sh")
    t0 = time.time()
    out, rc, hit, attempt = "", 0, False, 0
    while attempt < max(1, retries):
        attempt += 1
        try:
            p = subprocess.run(["bash", rp], capture_output=True, text=True,
                               timeout=timeout, stdin=subprocess.DEVNULL, cwd=entry)
            out, rc = (p.stdout or "") + (p.stderr or ""), p.returncode
        except subprocess.TimeoutExpired:
            return dict(osv=osv, ok=False, why="replay_timeout", attempt=attempt,
                        secs=round(time.time() - t0, 1))
        except OSError as e:
            return dict(osv=osv, ok=False, why=f"replay_error:{e}", attempt=attempt, secs=0.0)
        # replay.sh 约定：**退出码 1 = 复现成功**（判决按报告内容，N47）
        hit = ("ERROR: AddressSanitizer" in out or "ERROR: MemorySanitizer" in out
               or "WARNING: MemorySanitizer" in out
               or "SUMMARY: UndefinedBehaviorSanitizer" in out or "runtime error:" in out
               # [N74] 与 repro_common.py:74-76 对齐：deadly signal 是真崩溃
               or "libFuzzer: deadly signal" in out)
        if hit:
            break
    bd = (r.get("binary_dir") or "").rstrip("/")
    hdr = [
        f"# osv_id: {osv}",
        f"# project: {r.get('project')}",
        f"# sanitizer: {r.get('sanitizer')}",
        f"# verification_tier: {r.get('verification_tier')}",
        # ↓ `_select_report()` 靠这两行选中本报告：binary_dir 要与复现记录表一致、exit 要为 1
        f"# binary_dir: {bd}",
        f"# exit: {1 if hit else rc}",
        f"# fuzz_target: {r.get('fuzz_target')}",
        f"# commit: {r.get('commit') or r.get('pinned_commit')}",
        f"# provenance: **regenerated-by-replay**（N73 恢复；原 artifacts/logs 被误删，"
        f"本报告由 {time.strftime('%Y-%m-%d %H:%M:%S')} 跑 {rp} 重新产生；"
        f"ELF 是 binaries/ 的硬链接、testcase 是复现记录表那一份 → 与原冻结副本同源）",
        f"# replay_attempts: {attempt}（flaky 条目需重试，见 N73②）",
        f"# replay_exit_code: {rc}",
        f"# replay_seconds: {round(time.time() - t0, 1)}",
        "# ---- replay.sh 输出原文 ----",
    ]
    os.makedirs(REPRO_LOGS, exist_ok=True)
    dst = os.path.join(REPRO_LOGS, f"{osv}.log")
    with open(dst, "w", encoding="utf-8") as f:
        f.write("\n".join(hdr) + "\n" + out)
    return dict(osv=osv, ok=bool(hit), why=None if hit else "no_sanitizer_report",
                attempt=attempt, rc=rc, secs=round(time.time() - t0, 1), path=dst, entry=entry)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=0, help="只跑前 N 条（0=全部）")
    ap.add_argument("--par", type=int, default=6, help="并发数（docker 容器数）")
    ap.add_argument("--only", default=None, help="逗号分隔 OSV-ID")
    ap.add_argument("--retries", type=int, default=1,
                    help="每条最多重放几次（flaky 条目需要；历史最高 8 次才崩）")
    ap.add_argument("--redo-failed", default=None,
                    help="只重跑上次失败的那些（读该 jsonl 里 ok=false 的 osv）")
    ap.add_argument("--out", default=os.path.join(ART, "n73_report_recovery.jsonl"))
    a = ap.parse_args()

    ledger = latest_ledger()
    ver = {k for k, v in ledger.items() if v.get("verification_tier") in VERIFIED}
    entries = find_entries()
    log(f"复现记录表 verified {len(ver)} 条；交付条目 {len(entries)} 个")
    todo = [(o, d) for o, d in entries if o in ver]
    if a.redo_failed and os.path.isfile(a.redo_failed):
        prev = {json.loads(l)["osv"] for l in open(a.redo_failed, encoding="utf-8")
                if l.strip() and not json.loads(l).get("ok")}
        todo = [(o, d) for o, d in todo if o in prev]
        log(f"[redo-failed] 上次失败 {len(prev)} 条 → 本次只重跑这些")
    if a.only:
        want = {x.strip() for x in a.only.split(",") if x.strip()}
        todo = [(o, d) for o, d in todo if o in want]
    if a.limit:
        todo = todo[:a.limit]
    log(f"待重生成 **{len(todo)}** 条，并发 {a.par}")
    if not todo:
        log("⚠ 无可做条目")
        return 1

    ok = bad = 0
    t0 = time.time()
    with open(a.out, "w", encoding="utf-8") as fo:
        with cf.ThreadPoolExecutor(max_workers=a.par) as ex:
            futs = {ex.submit(regenerate, o, d, ledger, 1800, a.retries): o for o, d in todo}
            for i, fu in enumerate(cf.as_completed(futs), 1):
                r = fu.result()
                fo.write(json.dumps(r, ensure_ascii=False) + "\n")
                fo.flush()
                if r["ok"]:
                    ok += 1
                else:
                    bad += 1
                    log(f"  ❌ {r['osv']:<16} {r['why']}  ({r['secs']}s / {r.get('attempt')} 次)")
                if i % 20 == 0 or i == len(todo):
                    el = time.time() - t0
                    log(f"  … {i}/{len(todo)}  成功 {ok} 失败 {bad}  "
                        f"用时 {el/60:.1f}分  预计剩 {el/i*(len(todo)-i)/60:.1f}分")
    log(f"\n═══ N73 恢复完成：成功 {ok} / 失败 {bad}（共 {len(todo)}），"
        f"用时 {(time.time()-t0)/60:.1f} 分 ═══")
    log(f"  报告写回 {REPRO_LOGS}/")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())

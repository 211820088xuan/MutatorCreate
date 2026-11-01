#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""⑤ `annotate_dataset.py` — 四流合并 → `repro_dataset.jsonl`（DELIVERY §1.3⑤）。

**追加语义（append-only）**：每条盖 `run_id`（本轮唯一）+ `run_ts` 后**追加**，不就地改、不删旧；
同 `osv_id` 跨轮/`--force` 重跑会有多条，**下游按 `osv_id` 分组取 `run_ts` 最新一条**
（保留历史可审计，避免下游按 tier 重复计数）。

**不归档二进制**（归档只在 ②——⑤ 时机太晚、临时 `build/out` 已被同项目下次构建
`rm -rf /out/*` 覆盖；✅ W2 实证 md4c 的 HEAD 二进制被随后的钉版构建覆盖）。

字段 = ⓪ `MANIFEST_FIELDS`（①，46）+ ⓪ `RUNTIME_FIELDS`（②③④⑤，31），**顺序由 ⓪ 定义**
（[实现 W2 Phase0d] 在 ⓪ 里先定好，⑤ 不自行发明）。同名字段以运行期实际值覆盖 ① 的先验
（如 `commit_source`：① 先验 → ② 实际）。
"""
from __future__ import annotations

import argparse
import collections
import datetime
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import repro_common as rc  # noqa: E402

DATASET = os.path.join(rc.REPRO_DIR, "repro_dataset.jsonl")
GUARD_LOG = os.path.join(rc.ARTIFACTS, "dataset_guard.jsonl")
VERIFIED_TIERS = ("strict", "medium", "loose")


def tier_history(path):
    """[实现 W4 Phase1a(i)] 扫 dataset **全部历史行** → {osv_id: 曾达到过的 verified tier 集合}。

    为什么要这道防御：`repro_dataset.jsonl` 是 append-only 复现记录表、**下游按「同 osv_id 取 run_ts
    最新一行」读**，所以「最新一行」就是当前状态 —— 任何写入方的 bug 都能**静默作废一个已交付
    结论**。✅ W3 实测事故：⑤ 的 scope bug 把 W2 的 2 条 `strict` 覆盖成 `not_run`/tier=null，
    连带触发 N20（裁剪据此判定「无人引用」→ **不可逆删掉 4 个 verified 归档**）。
    N20 的修法（保护集扫全部行）治的是裁剪侧；**根因在写入侧**，故加单调性校验。
    """
    hist = {}
    if not os.path.exists(path):
        return hist
    for line in open(path, encoding="utf-8"):
        line = line.strip()
        if not line:
            continue
        try:
            d = json.loads(line)
        except json.JSONDecodeError:
            continue
        oid, t = d.get("osv_id"), d.get("verification_tier")
        if oid and t in VERIFIED_TIERS:
            hist.setdefault(oid, set()).add(t)
    return hist


def log(*a):
    print(*a, file=sys.stderr, flush=True)


def _load_jsonl(path, key="osv_id", latest=True):
    """读 jsonl → {key: rec}（latest=True 时同键取**文件里最后一条** = 最新）。"""
    out = {}
    if not path or not os.path.exists(path):
        return out
    for line in open(path, encoding="utf-8"):
        line = line.strip()
        if not line:
            continue
        try:
            d = json.loads(line)
        except json.JSONDecodeError:
            continue
        k = d.get(key)
        if k is None:
            continue
        if latest or k not in out:
            out[k] = d
    return out


def _load_build_index(path):
    """build_records.jsonl → 两个索引：按 osv_id、按 binary_dir（③ 把 binary_dir 抄进 observation，
    故可按归档位反查到那次构建的完整记录）。"""
    by_osv, by_dir = {}, {}
    if not path or not os.path.exists(path):
        return by_osv, by_dir
    for line in open(path, encoding="utf-8"):
        line = line.strip()
        if not line:
            continue
        try:
            d = json.loads(line)
        except json.JSONDecodeError:
            continue
        if d.get("osv_id"):
            by_osv[d["osv_id"]] = d            # 钉版记录带 osv_id，后者覆盖前者（最新）
        bd = d.get("binary_dir")
        if bd:
            by_dir[bd] = d
        for oid in (d.get("osv_ids") or []):   # HEAD 记录带 osv_ids（一次服务多条）
            by_osv.setdefault(oid, d)
    return by_osv, by_dir


def derive_repro_version(obs, brec, man):
    """`repro_version`（§1.5 enum）：head / fixed_parent / fixed_ancestor / introducing_commit / none。

    未复现 → `none`（**不混淆「已修复」与「不可复现」**：靠 `commit_source`+`build_status` 区分，
    ✅ P0：md4c HEAD 判 none 是**正确**结果，因为 bug 已在 HEAD 修复）。
    """
    if not (obs or {}).get("reproduced_any"):
        return "none"
    path = (brec or {}).get("path")
    pinned = (brec or {}).get("pinned_commit")
    if path == "head":
        return "head"
    intro = man.get("introducing_commit")
    if pinned and intro and (pinned.startswith(intro[:12]) or intro.startswith(pinned[:12])):
        return "introducing_commit"
    d = obs.get("walkback_depth_actual")
    if isinstance(d, int) and d >= 2:
        return "fixed_ancestor"
    if man.get("commit_source") == "introducing":
        return "introducing_commit"
    return "fixed_parent"


def merge(man, obs, ver, brec, run_id, run_ts):
    """一条 crash → 一条 dataset 记录（字段顺序 = MANIFEST_FIELDS + RUNTIME_FIELDS）。"""
    r = {}
    for k in rc.MANIFEST_FIELDS:
        r[k] = man.get(k)
    # ② 构建
    if brec:
        r["build_status"] = brec.get("build_status")
        r["build_stage"] = brec.get("build_stage")
        r["build_error_class"] = brec.get("build_error_class")
        r["build_seconds"] = brec.get("build_seconds")
        r["binary_dir"] = brec.get("binary_dir")
        r["binary_sha256"] = brec.get("binary_sha256")
        r["oss_fuzz_commit"] = brec.get("oss_fuzz_commit")
        r["pinned_commit"] = brec.get("pinned_commit")
        r["base_builder_digest"] = brec.get("base_builder_digest")   # ⓘ gcloud 不可用 → None
        r["era_commit"] = brec.get("era_commit")
        r["era_cache_hit"] = brec.get("era_cache_hit")
        if brec.get("path") == "head" and brec.get("pinned_commit"):
            # ② 实际构建的 commit 覆盖 ① 的先验（§1.5：commit_source「①先验→②实际」）
            r["commit_source"] = "head"
    # ③ 复现
    if obs:
        r["reproduced_any"] = obs.get("reproduced_any")
        r["observed_crash_type"] = obs.get("observed_crash_type")
        r["observed_frames"] = obs.get("observed_frames")
        r["exit_code"] = obs.get("exit_code")
        r["signal"] = obs.get("signal")
        r["retry_count"] = obs.get("retry_count")
        r["runtime_limits"] = obs.get("runtime_limits")
        r["raw_log_path"] = obs.get("raw_log_path")
        r["walkback_depth_actual"] = obs.get("walkback_depth_actual")
        # [实现 W3] N12/N17 的逐格结果
        # [实现 W5] 加 `walkback_stop_reason`：⑥ 已记（tier 停 / frac 停），但**dataset 是交付物、
        # trace 只是中间产物** → 不透传就等于「复现记录表上看不出哪些行是提前停的」，
        # 而 N12 翻转默认值时要审计的正是这个。✅ W5 实测抓到该缺陷（自测 [A] 2 项红）。
        # [实现 W5] 加 `binary_pruned`：逐条回收后 `binary_dir` 会指向已删目录，
        # **必须显式标注**，否则就是无声的悬空指针（N25/N26 同族）。
        # `binary_sha256` 取自 build_records（不随目录删除而丢）→ 仍可验证重建是否 bit 一致。
        for k in ("walkback_best_depth", "walkback_best_tier", "walkback_depths_tried",
                  "walkback_n_build_fail", "walkback_exhausted", "walkback_stop_reason",
                  "binary_pruned"):
            if obs.get(k) is not None:
                r[k] = obs.get(k)
        r["_obs_extra"] = {k: obs.get(k) for k in
                           ("observed_crash_type_raw", "observed_crash_type_norm",
                            "observed_frames_full", "dedup_token", "scariness",
                            "scariness_label", "ubsan_stderr_detected", "cmd_line",
                            "run_seconds", "attempts", "binary_source", "runner_error",
                            "docker_error") if obs.get(k) is not None}
        if not r.get("binary_dir"):
            r["binary_dir"] = obs.get("binary_dir")
        # [实现 W5] `binary_dir` 指向的目录**已不存在** → ⑤ 自己兜底标注 `binary_pruned`。
        # 为什么不能只靠 ⑥ 标：⑥ 只标**本轮逐条回收**的那些；**W3 的轮末裁剪**删掉的从来没人标
        # → ✅ W5 实测复现记录表里有 **60 条**行的 `binary_dir` 指向已删目录却毫无标记（无声悬空指针），
        # 消费者照着路径去取二进制会扑空、且无从判断是"删了"还是"写错了"。
        # 全部 60 条都是 `none` 档（按 §1.6 本就只交付 verified 子集）→ 无交付损失，
        # 但**标记本身是复现记录表的责任**，故在写入侧兜底。已有的显式标记不覆盖。
        if r.get("binary_dir") and r.get("binary_pruned") is None \
           and not os.path.exists(r["binary_dir"]):
            r["binary_pruned"] = True
        if not r.get("pinned_commit"):
            r["pinned_commit"] = obs.get("pinned_commit")
    # ④ 分级
    if ver:
        r["verification_tier"] = ver.get("verification_tier")
        r["frame_match_score"] = ver.get("frame_match_score")
        r["crash_type_match"] = ver.get("crash_type_match")
        r["score_pos"] = ver.get("score_pos")
        r["score_subseq"] = ver.get("score_subseq")
        r["score_set"] = ver.get("score_set")
        # [实现 W2 修 H] 漏抄了两个 ④ 新字段 → dataset 里恒为 null（本轮自查抓到）
        r["score_set_top3"] = ver.get("score_set_top3")
        r["score_subseq_frac"] = ver.get("score_subseq_frac")
        r["_ver_extra"] = {k: ver.get(k) for k in
                           ("tier_why", "n_recovered_frames", "non_crash_diagnostic",
                            "n_observed_frames", "recovered_norm", "observed_norm",
                            "t_strict", "details") if ver.get(k) is not None}
        # **[N46] ④ 判为「资源上限诊断不是崩溃」时，⑤ 不得盲抄 ⑥ 的过期 `reproduced_any`。**
        # observation 记的是**历史事实**（当时 ⑥ 把 libFuzzer `timeout` 当成了崩溃证据），
        # 但复现记录表要表达**当前最优判断**；否则会出现「tier=none 却 reproduced_any=True」的
        # 自相矛盾行 —— ✅ 本轮审计当场抓到（红线 2 条）。append-only 不改写旧行，
        # 而是让**新追加的更正行**自洽。
        if ver.get("non_crash_diagnostic"):
            r["reproduced_any"] = False
            r["_n46_correction"] = (
                "⑥ 原判 crashed（libFuzzer timeout/OOM 命中 evidence）；④ 按 N46 判为**资源上限"
                f"诊断、非所报漏洞的崩溃** → tier=none。实测类型={r.get('observed_crash_type')}；"
                "原始 observation 与 report.log 都保留，可复核。")
    # [实现 W2] 显式区分「本轮跑过」与「本轮没跑」（manifest 在范围内但无 observation，
    # 例如 testcase 磁盘缺失）——不得让未跑的记录冒充 tier=none。
    # [实现 W3] **保留 ① 的先验**：`commit_source` 会被 ② 的实际值覆盖（§1.5「①先验→②实际」），
    # W2 因此丢了先验（109/129 条 dataset 与 manifest 不一致）→ 跨轮分析必须回 join manifest。
    r["commit_source_prior"] = man.get("commit_source")
    r["run_status"] = "run" if obs else "not_run"
    r["repro_version"] = derive_repro_version(obs, brec, man) if obs else None
    r["run_id"] = run_id
    r["run_ts"] = run_ts
    return r


def main():
    ap = argparse.ArgumentParser(description="⑤ 四流合并 → repro_dataset.jsonl（append-only）")
    ap.add_argument("--manifest", default=rc.MANIFEST_OUT)
    ap.add_argument("--build-records", default=os.path.join(rc.ARTIFACTS, "build_records.jsonl"))
    ap.add_argument("--observations", default=os.path.join(rc.ARTIFACTS, "observations.jsonl"))
    ap.add_argument("--verifications", default=os.path.join(rc.ARTIFACTS, "verifications.jsonl"))
    ap.add_argument("--out", default=DATASET)
    ap.add_argument("--run-id", default=None)
    ap.add_argument("--force", action="store_true",
                    help="[W4 Phase1a(i)] 允许把曾达 verified 的 osv_id 写成无结论行"
                         "（会标 `tier_downgraded=true` + 原因，并记 dataset_guard.jsonl）")
    ap.add_argument("--only-observed", action=argparse.BooleanOptionalAction, default=True,
                    help="**默认开**：只写本轮**真有 observation** 的 crash。"
                         "[实现 W3 修] 原来默认关（写 manifest 范围内全部行、未跑的标 not_run）→ "
                         "配 `--skip-manifest` 复用大 manifest 时，⑤ 会把**没跑过**的 crash 也写一条 "
                         "not_run/tier=null；而 dataset 是「同 osv_id 取 run_ts 最新」→ **把上一轮的真实"
                         "结果覆盖掉**。✅ W3 实测中招：`w3-p5-cb` 那轮 manifest 有 199 条、只跑了 8 条，"
                         "结果 W2 的 OSV-2020-2183 / OSV-2021-1663 两条 **strict** 被覆盖成 not_run。"
                         "`--no-only-observed` 可恢复旧行为（写全范围 + not_run 标记）。")
    ap.add_argument("--include-unrun", action="store_true",
                    help="= --no-only-observed 的别名（连同没跑过的 manifest 行一起写）")
    a = ap.parse_args()

    run_id = a.run_id or f"w2-{datetime.datetime.now().strftime('%Y%m%d-%H%M%S')}"
    run_ts = int(time_now())
    mans = _load_jsonl(a.manifest)
    obs = _load_jsonl(a.observations)
    ver = _load_jsonl(a.verifications)
    b_by_osv, b_by_dir = _load_build_index(a.build_records)
    log(f"[⑤] manifest {len(mans)} / observations {len(obs)} / verifications {len(ver)} / "
        f"build_records(osv 索引 {len(b_by_osv)}, binary_dir 索引 {len(b_by_dir)})")
    log(f"    run_id={run_id} run_ts={run_ts}")

    only_obs = a.only_observed and not a.include_unrun
    ids = sorted(obs) if only_obs else sorted(mans)
    os.makedirs(os.path.dirname(os.path.abspath(a.out)), exist_ok=True)
    hist = tier_history(a.out)
    n = 0
    n_refused = n_forced = n_changed = 0
    tiers = collections.Counter()
    with open(a.out, "a", encoding="utf-8") as f:      # **append-only**
        for oid in ids:
            man = mans.get(oid)
            if not man:
                log(f"  ⚠ {oid} 有 observation 但 manifest 里没有 → 跳过（不造记录）")
                continue
            o = obs.get(oid)
            v = ver.get(oid)
            # **[N45] 连接键的优先级原先是反的。** `by_osv` 是「同 osv_id 后者覆盖前者」→ 拿到的是
            # 该 OSV **最后一次**构建；而 walk-back 对 loose 档会「继续下探」，最后一格往往**不是
            # 崩的那格**。observation 里的 `binary_dir` 是 ③ 从**真正重放并崩掉的那一格**抄来的，
            # 它才是权威连接键 → 先按 dir 反查，查不到才退回 osv_id。
            # ✅ 实测受害 2 条：OSV-2020-1016（c-blosc2/memory，复现记录表记 dca55210 而真相是 b7d25a74）、
            #   OSV-2023-48（libavc/address，复现记录表记 bb0f31cb 而真相是 e14ee149）。
            #   两条的 `binary_sha256` 都因此**不含自己的 fuzz_target** → 按 INFO.txt 的命令重放
            #   得 `./svc_enc_fuzzer: No such file or directory`、**exit=127**。
            #   而 build_records 里正确记录一直在（含 decompress_fuzzer / svc_enc_fuzzer）。
            b = b_by_dir.get(o["binary_dir"]) if (o and o.get("binary_dir")) else None
            if not b:
                b = b_by_osv.get(oid)
            rec = merge(man, o, v, b, run_id, run_ts)
            # ---- [实现 W4 Phase1a(i)] 单调性校验：verified 不得被降级成「无结论」----
            prev = hist.get(oid)
            new_tier = rec.get("verification_tier")
            no_conclusion = (rec.get("run_status") != "run") or (new_tier is None)
            if prev and no_conclusion:
                why = (f"历史行曾达 verified={sorted(prev)}，本行 tier={new_tier} "
                       f"run_status={rec.get('run_status')}（无结论）")
                if not a.force:
                    n_refused += 1
                    log(f"  ❌ 拒写 {oid}：{why}")
                    log(f"     → append-only 复现记录表里最新行即当前状态，写入无结论行会**静默作废已交付结论**。"
                        f"确需覆盖请显式加 --force（会标 tier_downgraded=true）")
                    _guard(a.out, dict(ts=run_ts, run_id=run_id, osv_id=oid, action="refused",
                                       prev_verified=sorted(prev), new_tier=new_tier,
                                       run_status=rec.get("run_status"), why=why))
                    continue
                n_forced += 1
                rec["tier_downgraded"] = True
                rec["tier_downgrade_reason"] = why
                log(f"  ⚠ --force 降级写入 {oid}：{why} → 标 tier_downgraded=true")
                _guard(a.out, dict(ts=run_ts, run_id=run_id, osv_id=oid, action="forced_downgrade",
                                   prev_verified=sorted(prev), new_tier=new_tier, why=why))
            elif prev and new_tier in VERIFIED_TIERS and set(prev) != {new_tier}:
                # verified → 另一个 verified：是**真重跑得到的新结论**，允许，但留痕
                n_changed += 1
                rec["tier_changed_from"] = sorted(prev)
                log(f"  ⓘ {oid}: tier {sorted(prev)} → {new_tier}（真重跑的新结论，已留痕）")
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")
            n += 1
            tiers[(v or {}).get("verification_tier") if o else "not_run"] += 1
    log(f"[⑤] 追加 {n} 条 → {a.out}")
    log(f"    tier 分布: {dict(tiers)}")
    if n_refused or n_forced or n_changed:
        log(f"    [单调性校验] 拒写 **{n_refused}** 条、--force 降级 {n_forced} 条、"
            f"verified→verified 变更 {n_changed} 条（审计 → {GUARD_LOG}）")
    return 0


def _guard(dataset_path, rec):
    os.makedirs(os.path.dirname(GUARD_LOG), exist_ok=True)
    with open(GUARD_LOG, "a", encoding="utf-8") as f:
        f.write(json.dumps(rec, ensure_ascii=False) + "\n")


def time_now():
    return datetime.datetime.now().timestamp()


if __name__ == "__main__":
    sys.exit(main())

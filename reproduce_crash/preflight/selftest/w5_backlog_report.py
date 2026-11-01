#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""W5 积压重跑的逐块核查 + 累积汇总（可重复跑）。

用法：python3 preflight/w5_backlog_report.py [run_id ...]
核查四件事：
  1. 本轮 tier / repro_version / static_check_verdict / walkback 分布；
  2. **逐条回收的完整性契约**：binary_pruned=true 的行必须仍留住 sha256 + 重建配方；
  3. **无声悬空指针**：binary_dir 指向已删目录、却没标 binary_pruned 的行（必须为 0）；
  4. 两条预注册判据的进度：not_located 累积数、N12 shadow 的 distinct-crash 数。
"""
import collections
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DATASET = os.path.join(ROOT, "repro_dataset.jsonl")
RUNS = os.path.join(ROOT, "artifacts", "runs")


def main():
    runs = sys.argv[1:]
    rows = [json.loads(l) for l in open(DATASET, encoding="utf-8")]
    lat = {}
    for r in rows:
        lat[r["osv_id"]] = r

    for rid in runs:
        c = [r for r in rows if r["run_id"] == rid]
        if not c:
            print(f"\n═══ {rid}: 尚无数据 ═══")
            continue
        print(f"\n═══ {rid}：{len(c)} 条 ═══")
        cnt = lambda k: dict(collections.Counter(str(r.get(k)) for r in c).most_common())
        print(f"  tier              : {cnt('verification_tier')}")
        print(f"  复现              : {sum(1 for r in c if r.get('reproduced_any'))}/{len(c)}")
        print(f"  repro_version     : {cnt('repro_version')}")
        print(f"  static_check      : {cnt('static_check_verdict')}")
        print(f"  walkback_stop     : {cnt('walkback_stop_reason')}")
        print(f"  walkback_best_depth: {cnt('walkback_best_depth')}")
        print(f"  binary_pruned     : {cnt('binary_pruned')}")
        print(f"  sha256 留住       : {sum(1 for r in c if r.get('binary_sha256'))}/{len(c)}")
        print(f"  配方 pinned_commit: {sum(1 for r in c if r.get('pinned_commit'))}/{len(c)}")
        arch = collections.Counter(str(r.get("job_arch")) for r in c)
        print(f"  job_arch          : {dict(arch)}")
        ia = [r for r in c if r.get("job_arch") == "i386"]
        if ia:
            print(f"  └ i386 的 {len(ia)} 条 tier: "
                  f"{dict(collections.Counter(str(r.get('verification_tier')) for r in ia))}")

    print(f"\n═══ 累积 ═══")
    print(f"  dataset {len(rows)} 行 / {len(lat)} 条唯一 / {len(set(r['run_id'] for r in rows))} 个 run")
    print(f"  tier  : {dict(collections.Counter(str(r.get('verification_tier')) for r in lat.values()).most_common())}")
    rep = [r for r in lat.values() if r.get("reproduced_any")]
    print(f"  复现  : {len(rep)}/{len(lat)} = {len(rep)/len(lat):.1%}")
    print(f"  按项目: {dict(collections.Counter(r.get('project') for r in rep).most_common())}")
    print(f"  按san : {dict(collections.Counter(str(r.get('sanitizer')) for r in rep).most_common())}")

    print(f"\n═══ 逐条回收的完整性契约 ═══")
    pr = [r for r in lat.values() if r.get("binary_pruned")]
    bad_sha = [r["osv_id"] for r in pr if not r.get("binary_sha256")]
    bad_rec = [r["osv_id"] for r in pr if not r.get("pinned_commit")]
    dangling = [r for r in lat.values()
                if r.get("binary_dir") and not r.get("binary_pruned")
                and not os.path.isdir(r["binary_dir"])]
    dv = [r for r in dangling if r.get("verification_tier") in ("strict", "medium", "loose")]
    print(f"  已标 binary_pruned 的行 : {len(pr)}")
    print(f"  其中缺 sha256           : {len(bad_sha)} {bad_sha[:4]}   ← 必须为 0")
    print(f"  其中缺重建配方          : {len(bad_rec)} {bad_rec[:4]}   ← 必须为 0")
    # ⚠ [W5 修判据] 原来这里写「悬空必须为 0」，是**错的**：
    #   ⑥ 的顺序是 ⑤ annotate → **轮末 prune**，所以 prune 删掉的归档必然留下一行
    #   「⑤ 写时目录还在、之后才被删」的未标记悬空指针。这类行**全是 `none` 档**
    #   （prune 只删未被 verified 引用的归档），而 §1.6 本就只交付 verified 子集
    #   → 属**设计内**，不该报成违约。真正的红线是 **verified 行悬空 = 0**。
    print(f"  悬空 binary_dir         : {len(dangling)} 条"
          f"（tier={dict(collections.Counter(str(r.get('verification_tier')) for r in dangling).most_common())}）")
    print(f"  ├─ 其中 **verified**    : {len(dv)} {[r['osv_id'] for r in dv][:4]}  ← **红线，必须为 0**")
    print(f"  └─ 其中 none 档         : {len(dangling) - len(dv)} 条 = 设计内（轮末 prune 在 ⑤ 之后跑；"
          f"§1.6 只交付 verified 子集）")
    if len(dangling) - len(dv):
        print(f"     残留缺陷（已记 §5）：⑤ 的兜底只看「写行时目录是否存在」，救不了之后才被 prune 删的行；"
              f"根治要么把 prune 提到 ⑤ 之前（但保护集得改成本轮 verifications），"
              f"要么让 prune 回写标记（append-only 下代价高）")

    print(f"\n═══ 剩余积压的**正确**分类（W5 修：只看 `commit_source` 会误报） ═══")
    # ⚠ 原口径「最新行 commit_source=head 且有 fixed_commit 且未复现 = 积压」是**错的**：
    #   ① 钉版**试过但每格都构建失败**的 crash 不产生 observation → ⑤ 不写新行 →
    #      它的最新行仍是旧的 HEAD 行，于是被当成「从没试过钉版」（✅ 实测 3 条 flatbuffers
    #      就是这样：18 次格构建全 `dockerfile_drift`、早停触发，却被报成积压）；
    #   ② **N6 退化 range**（`introduced==fixed`）按设计**禁止钉版**（钉了只会得到假 none）→
    #      它是**终止性 HEAD-only**，不是待办（✅ 实测 OSV-2017-126，且它正是唯一的 UBSAN 候选）。
    # 正确口径要查 build_records 里有没有 stage=2 的尝试，并排除 degenerate。
    pinned_tried = set()
    brs = os.path.join(ROOT, "artifacts", "build_records.jsonl")
    for l in open(brs, encoding="utf-8"):
        b = json.loads(l)
        if b.get("build_stage") == 2 and b.get("osv_id"):
            pinned_tried.add(b["osv_id"])
        for o in (b.get("osv_ids") or []):
            pinned_tried.add(o)
    man = {}
    mp = os.path.join(ROOT, "artifacts", "repro_manifest.jsonl")
    for l in open(mp, encoding="utf-8"):
        m = json.loads(l)
        man[m["osv_id"]] = m
    cand = [r for r in lat.values()
            if not r.get("reproduced_any") and r.get("commit_source") == "head"
            and (man.get(r["osv_id"]) or {}).get("fixed_commit") and not r.get("skip_reason")]
    degen, tried, true_back = [], [], []
    for r in cand:
        o = r["osv_id"]
        m = man.get(o) or {}
        if m.get("static_check_verdict") == "degenerate" or (
                m.get("osv_degenerate_range") and not m.get("degenerate_resolved")):
            degen.append(o)
        elif o in pinned_tried:
            tried.append(o)
        else:
            true_back.append(o)
    print(f"  旧口径会报 {len(cand)} 条「积压」，正确拆分：")
    print(f"    ▸ 终止性 HEAD-only（N6 退化，禁钉版）: {len(degen)} {degen[:4]}")
    print(f"    ▸ 钉版已试过、每格构建都失败        : {len(tried)} {tried[:4]}")
    print(f"    ▸ **真·积压（从没在钉版上试过）**    : {len(true_back)} {true_back[:6]}")

    print(f"\n═══ 两条预注册判据的进度 ═══")
    nl = [r for r in lat.values() if r.get("static_check_verdict") == "not_located"]
    print(f"  not_located 累积 : {len(nl)} 条（判据要 ≥30，还差 {max(0, 30 - len(nl))}）")
    tot = set()
    per = {}
    for d in sorted(os.listdir(RUNS)) if os.path.isdir(RUNS) else []:
        f = os.path.join(RUNS, d, "walkback_trace.jsonl")
        if not os.path.exists(f):
            continue
        for l in open(f, encoding="utf-8"):
            r = json.loads(l)
            cells = r.get("results") or []
            hit = any(c.get("frac_stop_would_fire") for c in cells)
            if not hit:                       # 老 trace 没有该字段 → 用 tier/frac 重算
                ok = [c for c in cells if c.get("build") == "ok"]
                for i, c in enumerate(ok):
                    if (c.get("score_subseq_frac") or 0) >= 0.6 and c.get("reproduced") \
                       and str(c.get("tier")) in ("loose", "none") and ok[i + 1:]:
                        hit = True
                        break
            if hit:
                tot.add(r["osv_id"])
                per.setdefault(d, set()).add(r["osv_id"])
    print(f"  N12 shadow distinct-crash: {len(tot)} 条（翻转判据要 ≥10，还差 {max(0, 10 - len(tot))}）")
    for k, v in sorted(per.items()):
        print(f"     {k:<18}{len(v)} 条")


if __name__ == "__main__":
    main()

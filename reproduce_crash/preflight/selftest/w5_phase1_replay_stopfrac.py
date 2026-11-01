#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""W5 Phase 1：`frac≥阈值 即停`（N12 的 🅗 改进）的**离线回放** —— 0 次构建。

为什么可以离线定论：W3/W4 的 walk-back 跑的是「不达 medium 就继续下探」策略，
所以**更深格的结果都已经被观测到了** → 停止规则的反事实是**完全可观测**的
（off-policy evaluation，不需要重跑）。每格数据在 `artifacts/runs/*/walkback_trace.jsonl`。

三个输出：
  1. 阈值扫描 0.5/0.6/0.7/0.8/1.0：各会触发几次、省几次构建、**tier 损失几次**、涉及几条 crash；
  2. **交叉校验**：W3+W4 子集必须等于内联算出的冻结值（5 触发 / 7 省 / 0 损失 / **3 条**不同 crash）
     —— 脚本若与当时的计算漂移，这里会红；
  3. **预注册翻转判据**的判定：distinct-crash n≥10 且 tier 损失 0 → 建议把 `--stop-frac` 默认改 0.6。

⚠ 计数口径（W5 纠正）：一次下探里同一条 crash 可能在 depth1、depth2 各触发一次
   （嵌套），**「触发次数」不等于独立样本数** → 决策只看 `distinct_crashes`。

复算：python3 preflight/w5_phase1_replay_stopfrac.py [--json 输出路径]
"""
import argparse
import collections
import glob
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
RUNS = os.path.join(ROOT, "artifacts", "runs")
RANK = {"strict": 3, "medium": 2, "loose": 1, "none": 0, None: -1}
THRESHOLDS = (0.5, 0.6, 0.7, 0.8, 1.0)
# 冻结的期望值：W5 定稿时内联算出（W3+W4 共 5 个 trace 文件、24 条 crash、43 格）
FROZEN = {"runs": ("w3-", "w4-"), "fires": 5, "saved": 7, "loss": 0, "distinct": 3}


def load_cells(run_prefixes=None):
    """→ [(run_id, osv_id, project, [cell, …])]，cell 只取构建成功的格（失败格无 tier/frac）。"""
    out = []
    for path in sorted(glob.glob(os.path.join(RUNS, "*", "walkback_trace.jsonl"))):
        run = os.path.basename(os.path.dirname(path))
        if run_prefixes and not run.startswith(run_prefixes):
            continue
        for line in open(path, encoding="utf-8"):
            r = json.loads(line)
            cells = [c for c in (r.get("results") or []) if c.get("build") == "ok"]
            out.append((run, r.get("osv_id"), r.get("project"), cells))
    return out


def replay(crashes, th):
    """在给定阈值下重放停止规则，与实际发生的下探对比。"""
    fires = saved = loss = 0
    hit = set()
    loss_ids = []
    for run, oid, proj, cells in crashes:
        for i, c in enumerate(cells):
            deeper = cells[i + 1:]
            tier_now = RANK.get(c.get("tier"), 0)
            would = (c.get("score_subseq_frac") is not None and c.get("reproduced")
                     and c["score_subseq_frac"] >= th and tier_now < 2)
            if not (would and deeper):
                continue
            fires += 1
            saved += len(deeper)
            hit.add(oid)
            best_deep = max([RANK.get(x.get("tier"), 0) for x in deeper] + [0])
            if best_deep > tier_now:                       # 更深格本来能升档 → 真损失
                loss += 1
                loss_ids.append(f"{oid}@{run}(d{c.get('depth')}→{best_deep})")
    return {"threshold": th, "fires": fires, "builds_saved": saved, "tier_loss": loss,
            "distinct_crashes": len(hit), "loss_ids": loss_ids,
            "crashes": sorted(hit)}


def main():
    ap = argparse.ArgumentParser(description="N12 `frac≥阈值即停` 的离线回放")
    ap.add_argument("--json", default=os.path.join(HERE, "w5_phase1_replay_stopfrac.json"))
    a = ap.parse_args()

    allc = load_cells()
    sub = load_cells(tuple(FROZEN["runs"]))
    n_cells = sum(len(c) for _, _, _, c in allc)
    print("═" * 78)
    print("W5 Phase 1：`frac≥阈值 即停` 离线回放（0 次构建）")
    print("═" * 78)
    print(f"trace：{len({r for r, _, _, _ in allc})} 个 run / {len(allc)} 条 crash / "
          f"{n_cells} 个构建成功的格")
    fr = collections.Counter(round(c["score_subseq_frac"], 4) if c.get("score_subseq_frac")
                             is not None else None
                             for _, _, _, cs in allc for c in cs)
    print(f"frac 取值分布：{dict(sorted(fr.items(), key=lambda x: (x[0] is None, x[0])))}")

    print(f"\n{'阈值':<7}{'触发':<7}{'省构建':<8}{'tier损失':<9}{'不同crash':<10}反例")
    rows = []
    for th in THRESHOLDS:
        r = replay(allc, th)
        rows.append(r)
        print(f"{th:<9}{r['fires']:<9}{r['builds_saved']:<10}{r['tier_loss']:<11}"
              f"{r['distinct_crashes']:<12}{','.join(r['loss_ids']) or '—'}")

    # ── 交叉校验：W3+W4 子集必须等于冻结值 ──
    frozen_run = replay(sub, 0.6)
    print("\n[交叉校验] W3+W4 子集 @0.6 vs 定稿时内联算出的冻结值")
    ok = True
    for k, want in (("fires", FROZEN["fires"]), ("builds_saved", FROZEN["saved"]),
                    ("tier_loss", FROZEN["loss"]), ("distinct_crashes", FROZEN["distinct"])):
        got = frozen_run[k]
        good = got == want
        ok &= good
        print(f"  {'✅' if good else '❌'} {k:<18}= {got}（冻结期望 {want}）")
    print(f"  说明：{frozen_run['fires']} 次触发只来自 **{frozen_run['distinct_crashes']} 条**"
          f"不同 crash（{', '.join(frozen_run['crashes'])}）—— 同一条在 depth1/depth2 各触发一次")

    # ── 阈值是否有信息量 ──
    same = len({(r["fires"], r["builds_saved"], r["tier_loss"]) for r in rows}) == 1
    print(f"\n[阈值扫描] 五个阈值结果{'**完全相同** → 扫描无信息量，沿用预注册的 0.6' if same else '有差异 → 需按数据选阈值'}")
    print(f"  （原因：frac 只取 {sorted(k for k in fr if k is not None)} 这几个离散值，0.5–1.0 之间没有可分辨的样本）")

    # ── 预注册翻转判据 ──
    r06 = rows[list(THRESHOLDS).index(0.6)]
    n, loss = r06["distinct_crashes"], r06["tier_loss"]
    flip = (n >= 10 and loss == 0)
    proj = collections.Counter(p for _, _, p, _ in allc)
    print("\n[预注册翻转判据] distinct-crash n≥10 且 tier 损失 0 → `--stop-frac` 默认改 0.6")
    print(f"  当前 n={n}（阈值 0.6）、tier 损失={loss} → **{'建议翻转默认 ON' if flip else '维持默认 OFF'}**"
          f"；还差 {max(0, 10 - n)} 条不同 crash")
    print(f"  ⚠ 样本集中度：{dict(proj.most_common())} → 结论被单一项目主导的风险")
    print(f"  ⚠ 默认 OFF 的代价：一轮多花 ~{r06['builds_saved']}/{n_cells} "
          f"= {r06['builds_saved'] / max(n_cells, 1):.0%} 的格构建；"
          f"**换来的是测量通道不被摧毁**（一停就再也观察不到更深格）")

    with open(a.json, "w", encoding="utf-8") as f:
        json.dump({"n_runs": len({r for r, _, _, _ in allc}), "n_crashes": len(allc),
                   "n_cells_ok": n_cells, "frac_distribution": {str(k): v for k, v in fr.items()},
                   "sweep": rows, "frozen_crosscheck": {"expect": FROZEN, "got": frozen_run,
                                                         "ok": ok},
                   "thresholds_indistinguishable": same,
                   "flip_criterion": {"n_distinct": n, "tier_loss": loss, "flip": flip,
                                      "need_more": max(0, 10 - n)},
                   "project_mix": dict(proj)}, f, ensure_ascii=False, indent=1)
    print(f"\n→ 落盘 {os.path.relpath(a.json, ROOT)}")
    print("\n" + ("✅ 交叉校验通过" if ok else "❌ 交叉校验未通过（脚本与定稿时的计算漂移了）"))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())

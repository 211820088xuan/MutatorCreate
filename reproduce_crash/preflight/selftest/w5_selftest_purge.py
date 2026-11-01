#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""W5：**复现完立即删归档**（purge-on-verify）+ 排序默认值修正 的自测。

为什么要「立即删」而不是沿用「轮末裁剪」：
  ✅ 实测 92 条积压一轮的归档峰值 ≈ 92 × 50MB ≈ **4.6GB**，而磁盘只有 7.7G
  → 轮末才裁剪会中途撞 `--min-free-gb` 护栏而**中止整轮**。逐条回收后峰值 ≈ 1–2 个归档。

为什么**连 verified 的也删**是安全的（用户已批准该策略）：
  W4 已实测归档重建是**逐字节一致的 20/20**（4 commit × 5 文件）→ 删除是**可恢复**的，
  损失只是重建时间、不是信息。前提是 dataset 行必须留住「配方 + 指纹」：
  `binary_sha256`（来自 build_records，删目录不影响）+ `pinned_commit`/sanitizer/arch/era，
  并标 **`binary_pruned=true`** —— 否则 `binary_dir` 会变成**无声的悬空指针**
  （这正是 N25/N26 那一族问题：产物没了而记录还指着它）。

**HEAD 归档永不删**：它按 (project,sanitizer) 被同组全部 crash 共享，且负对照（§1.7 I）要用。
`_shared` 目录同理。

复算：python3 preflight/w5_selftest_purge.py
"""
import json
import os
import shutil
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, ROOT)
import annotate_dataset as A         # noqa: E402
import build_orchestrator as B       # noqa: E402
import run_repro as RR               # noqa: E402
import manifest_builder as M         # noqa: E402

FAILS = []


def ck(cond, msg):
    print(("  ✅ " if cond else "  ❌ ") + msg)
    if not cond:
        FAILS.append(msg)


def rec(path_kind, d):
    return {"path": path_kind, "binary_dir": d, "build_status": "ok"}


def main():
    print("═" * 78)
    print("W5 自测：purge-on-verify（逐条回收）+ 排序默认值 + ⑤ binary_pruned 透传")
    print("═" * 78)

    print("\n[A] select_purge_dirs：只挑钉版、去重、跳过空值")
    got = B.select_purge_dirs([rec("pinned", "/x/a"), rec("pinned", "/x/a"),
                               rec("pinned", "/x/b"), rec("head", "/x/head"),
                               {"path": "pinned"}, {"binary_dir": "/x/c"}])
    ck(got == ["/x/a", "/x/b"], f"钉版去重后 = {got}（期望 ['/x/a','/x/b']）")
    ck("/x/head" not in got, "**HEAD 归档被排除**（共享 + 负对照要用）")
    ck(B.select_purge_dirs([]) == [] and B.select_purge_dirs(None) == [],
       "空输入 / None → 空列表（不抛异常）")
    ck(B.select_purge_dirs([rec("head", "/x/h")], keep_head=False) == [os.path.normpath("/x/h")],
       "负对照：keep_head=False 时 HEAD 会被选中 → 证明 [A] 的排除确实由该开关生效")

    print("\n[B] purge_archives：真删 + 失效 state 缓存键 + 写审计")
    td = tempfile.mkdtemp()
    d1 = os.path.join(td, "proj", "address", "c1")
    d2 = os.path.join(td, "proj", "address", "c2")
    shared = os.path.join(td, "_shared", "x")
    for d in (d1, d2, shared):
        os.makedirs(d, exist_ok=True)
        with open(os.path.join(d, "fuzz"), "wb") as f:
            f.write(b"\0" * 4096)
    sp = os.path.join(td, "state.json")
    ap_ = os.path.join(td, "audit.jsonl")
    with open(sp, "w", encoding="utf-8") as f:
        json.dump({"builds": {"k1": {"binary_dir": d1}, "k2": {"binary_dir": d2},
                              "k3": {"binary_dir": shared}}}, f)
    saved_audit = B.PRUNE_AUDIT
    B.PRUNE_AUDIT = ap_
    try:
        # dry-run：报告回收量但一个都不删
        r0 = B.purge_archives([d1], state_path=sp, why="t-dry", dry=True)
        ck(r0["n_deleted"] == 0 and os.path.isdir(d1) and r0["freed_bytes"] > 0,
           f"dry-run：n_deleted={r0['n_deleted']}、目录仍在、freed={r0['freed_bytes']}B（会报告）")
        # 真删
        r = B.purge_archives([d1, d2, os.path.join(td, "not-exist")], state_path=sp,
                             why="t-real")
        ck(r["n_deleted"] == 2 and not os.path.isdir(d1) and not os.path.isdir(d2),
           f"真删 2 个（n_deleted={r['n_deleted']}），不存在的目录被容忍不报错")
        st = json.load(open(sp, encoding="utf-8"))
        ck(set(st["builds"]) == {"k3"},
           f"state 缓存键：指向已删目录的 k1/k2 被删、k3（_shared 仍在）保留 → {sorted(st['builds'])}")
        ck(any(h.get("action") == "purge_on_verify" for h in st.get("prune_history", [])),
           "prune_history 里留了 purge_on_verify 痕迹")
        lines = [json.loads(x) for x in open(ap_, encoding="utf-8")]
        ck(any(l["action"] == "purge_on_verify" and l.get("why") == "t-real" for l in lines),
           f"审计写了 action=purge_on_verify + why（{len(lines)} 条）")
        # _shared 永不删（即使被显式要求）
        r2 = B.purge_archives([shared], state_path=sp, why="t-shared")
        ck(os.path.isdir(shared) and r2["n_deleted"] == 0,
           f"**`_shared` 拒绝删除**（n_deleted={r2['n_deleted']}，目录仍在）")
    finally:
        B.PRUNE_AUDIT = saved_audit
        shutil.rmtree(td, ignore_errors=True)

    print("\n[C] ⑤ 必须把 binary_pruned 透传进 dataset（否则 binary_dir 是无声悬空指针）")
    man = {"osv_id": "OSV-X", "project": "p", "crash_type": "Heap-buffer-overflow"}
    brec = {"build_status": "ok", "binary_dir": "/gone/p/address/c1",
            "binary_sha256": "ab" * 32, "path": "pinned", "pinned_commit": "c1" * 20}
    obs = {"osv_id": "OSV-X", "reproduced_any": True, "binary_pruned": True,
           "walkback_best_depth": 1, "walkback_best_tier": "strict"}
    row = A.merge(man, obs, {}, brec, "w5-t", 1)
    ck(row.get("binary_pruned") is True, f"binary_pruned = {row.get('binary_pruned')!r}（期望 True）")
    ck(row.get("binary_sha256") == "ab" * 32,
       "**sha256 仍在**（删目录不影响指纹 → 可验证重建是否 bit 一致）")
    ck(row.get("pinned_commit") == "c1" * 20, "**重建配方 pinned_commit 仍在**")
    # ⚠ [W5 修测试夹具] 原来这条用的是**不存在**的路径 `/gone/p/address/c1`，
    # 却又断言「未删时行为不变（None）」——加了 ⑤ 的**按目录存在性兜底**之后，
    # 那条路径会被正确标成 True，于是本条自相矛盾地红了。
    # 「未删」这个前提**要求目录真的存在**，所以夹具必须换成存在的路径。
    live_brec = dict(brec, binary_dir=os.path.dirname(os.path.abspath(__file__)))
    ck(A.merge(man, {**obs, "binary_pruned": None}, {}, live_brec, "w5-t", 1).get("binary_pruned") is None,
       "目录**存在**且 ⑥ 未标记 → 保持 None（不误标活证据）")
    ck(A.merge(man, {**obs, "binary_pruned": None}, {}, brec, "w5-t", 1).get("binary_pruned") is True,
       "目录不存在 → ⑤ 兜底标 True（`/gone/...` 这条现在测的是**兜底**，与 [C] 分工明确）")

    print("\n[F] purge **必须**尊重 dataset 保护集（W5 实测事故：删掉了 W4 已交付的 strict 证据）")
    # ✅ 事故形态：OSV-2021-1663 / OSV-2021-1712（都是 w4-stratA 的 **strict** 行）的归档，
    #    被 `purge_on_verify:OSV-2021-1676` 删掉了 —— 因为**钉到同一 commit 的 crash 共享归档目录**，
    #    而 purge 完全没查 dataset 保护集（prune_archive 有查，还有 pinned_commit 交叉校验）。
    td2 = tempfile.mkdtemp()
    keep = os.path.join(td2, "proj", "address", "shared-commit")
    drop = os.path.join(td2, "proj", "address", "only-mine")
    for d in (keep, drop):
        os.makedirs(d, exist_ok=True)
        with open(os.path.join(d, "fuzz"), "wb") as f:
            f.write(b"\0" * 2048)
    dsp = os.path.join(td2, "dataset.jsonl")
    with open(dsp, "w", encoding="utf-8") as f:
        f.write(json.dumps({"osv_id": "OSV-OLD", "verification_tier": "strict",
                            "binary_dir": keep, "binary_sha256": "cd" * 32}) + "\n")
        f.write(json.dumps({"osv_id": "OSV-NONE", "verification_tier": "none",
                            "binary_dir": drop}) + "\n")
    sp2 = os.path.join(td2, "state.json")
    with open(sp2, "w", encoding="utf-8") as f:
        json.dump({"builds": {}}, f)
    saved_audit = B.PRUNE_AUDIT
    B.PRUNE_AUDIT = os.path.join(td2, "audit.jsonl")
    try:
        r = B.purge_archives([keep, drop], state_path=sp2, dataset_path=dsp, why="t-protect")
        ck(os.path.isdir(keep), "**被历史 verified 行引用的目录必须保住**（共享归档事故的正解）")
        ck(not os.path.isdir(drop), "只被 none 行引用的目录照删（不影响回收效果）")
        ck(r["n_deleted"] == 1 and keep in [os.path.normpath(x) for x in r.get("protected", [])],
           f"n_deleted={r['n_deleted']}、protected 里点明保住的那个（{r.get('protected')}）")
        # 不给 dataset_path 时 = 旧行为（无保护）→ 必须显式记录，避免静默绕过
        r2 = B.purge_archives([keep], state_path=sp2, why="t-nodataset")
        ck(not os.path.isdir(keep) and r2["n_deleted"] == 1,
           "未传 dataset_path → 无保护（照删）：所以 ⑥ 必须传，且这里证明该参数确实起作用")
    finally:
        B.PRUNE_AUDIT = saved_audit
        shutil.rmtree(td2, ignore_errors=True)

    print("\n[D] CLI 默认值：排序根因修正 + **purge 默认关（W5 第十一轮反转）**")
    a6 = RR.build_argparser().parse_args([])
    ck(a6.sort == "fixed_first",
       f"⑥ `--sort` 默认 = {a6.sort!r}（**根因修正**：no_fixed_first 把 45.7% 复现率的 has_fixed "
       f"排到队尾，92 条积压因此三轮没被碰到）")
    # [W5 **第十一轮反转**] 原断言是 `is True`（当时默认开）。改成 `is False` 的理由必须写在这：
    #   ① **重放必须有二进制** —— 「可 bit 级重建」只证明**信息没丢**，不证明**能力没丢**；
    #      对「反复重放」这个下游用法，重建代价是每次都要付的（我此前用前者偷换了后者）；
    #   ② ✅ 实测重建成本 **64 归档 / 72 条 / ≈1.7h / ≈2.8GB / 缺镜像 0 个** → 留着付得起；
    #   ③ 当初「非删不可」的依据（3,093 × 48MB ≈ **145GB** > 100G 磁盘）**只在跑满队列时成立**，
    #      而新项目 6 试 0 中、五个老项目池已榨干 → 跑不满（实际规模 1.3GB / 磁盘 11G）；
    #   ④ 这条路径已出过 **N30**（绕过保护集删掉已交付 strict 证据）与 **N41**
    #      （保护集字符串比对、路径一有别名就静默失配 → 会删光 verified 归档）两次事故
    #      → **默认关掉最危险的那条路径本身就是护栏**。
    ck(a6.purge_on_verify is False,
       f"⑥ `--purge-on-verify` 默认 = {a6.purge_on_verify}（**第十一轮反转**：重放要二进制在场，"
       f"且实测重建成本付得起；满队列 145GB 的前提已不可达）")
    a6b = RR.build_argparser().parse_args(["--purge-on-verify", "--sort", "no_fixed_first"])
    ck(a6b.purge_on_verify is True and a6b.sort == "no_fixed_first",
       "**负对照**：仍能显式打开 purge（跑满大队列且磁盘吃紧时要用），且 --sort 也能退回旧值")
    am = M.build_argparser().parse_args([]) if hasattr(M, "build_argparser") else None
    if am is None:
        ck(True, "① 未抽 build_argparser（其 --sort 由 ⑥ 显式传入，不影响轮次）")
    else:
        ck(am.sort == "fixed_first", f"① `--sort` 默认 = {am.sort!r}（与 ⑥ 一致）")

    print("\n" + (f"❌ {len(FAILS)} 项未通过：{FAILS}" if FAILS else "✅ 全部通过"))
    return 1 if FAILS else 0


if __name__ == "__main__":
    sys.exit(main())

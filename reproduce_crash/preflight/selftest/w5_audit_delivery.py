#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""W5：**交付面审计** —— 对 `repro_dataset.jsonl` 的 verified 子集做不变量检查。

为什么要有它：W5 一路查出的缺陷（⑤ 白名单漏字段、悬空 `binary_dir`、N30 删掉已交付证据、
度量口径误报积压）**没有一个会被现有自测发现** —— 那些自测测的是"模块行为对不对"，
而这些都是"**交付出去的复现记录表自不自洽**"。所以补一个直接审复现记录表的护栏。

不变量分两类：
  **[硬]** 违反即交付有错（红线）：tier 与评分自相矛盾、verified 行缺证据指纹、
       verified 行悬空且未标记、`run_status` 非 run、同一 osv_id 的最新行不唯一。
  **[软]** 违反要能解释（记下来但不算失败）：`none` 档悬空 `binary_dir`（轮末 prune 在 ⑤ 之后跑，
       §1.6 本就只交付 verified 子集）、`recovered` 0 帧导致降档（④ 的既有规则）。

tier 判据取自 ④ `verify_one()` 的**实际代码**（不是我的转述）：
  not reproduced → none；reproduced 且 recovered 0 帧 → (medium if crash_type_match else loose)；
  `score_subseq ≥ T_strict` 且 crash_type 一致 → strict；仅 crash_type 一致 → medium；否则 loose。

复算：python3 preflight/w5_audit_delivery.py [--verbose]
"""
import argparse
import collections
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, ROOT)
import repro_common as rc  # noqa: E402   ← NON_CRASH_DIAGNOSTICS 的**单一真源**，不在此复制一份
DATASET = os.path.join(ROOT, "repro_dataset.jsonl")
VERIFIED = ("strict", "medium", "loose")
T_STRICT = 1.0

HARD = []      # 红线：违反即失败
SOFT = []      # 可解释：记录但不失败


def hard(msg):
    HARD.append(msg)
    print("  ❌ [硬] " + msg)


def soft(msg):
    SOFT.append(msg)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--verbose", action="store_true")
    ap.add_argument("--dataset", default=DATASET,
                    help="审计哪份复现记录表（默认真复现记录表；**牙齿测试**用变异副本，绝不碰真数据）")
    a = ap.parse_args()
    rows = [json.loads(l) for l in open(a.dataset, encoding="utf-8")]
    print("═" * 88)
    print("W5 交付面审计：repro_dataset.jsonl 的不变量检查")
    print("═" * 88)
    print(f"复现记录表 {a.dataset.split('/')[-1]}：{len(rows)} 行；字段数 {len(rows[0])}")

    # ── 1. 最新行唯一性 + run_status ──
    print("\n[1] append-only 复现记录表的基本性质")
    lat, order = {}, collections.defaultdict(list)
    for i, r in enumerate(rows):
        order[r["osv_id"]].append(i)
        lat[r["osv_id"]] = r
    dup = [o for o, ix in order.items() if len(ix) > 1]
    print(f"  唯一 crash {len(lat)} 条；其中有多行历史的 {len(dup)} 条（append-only 正常）")
    bad_status = [o for o, r in lat.items() if r.get("run_status") not in (None, "run")]
    if bad_status:
        hard(f"最新行 run_status 非 run：{len(bad_status)} 条 {bad_status[:4]}")
    else:
        print(f"  ✅ 全部最新行 run_status ∈ {{run}}（无 not_run 覆盖）")
    down = [o for o, r in lat.items() if r.get("tier_downgraded")]
    if down:
        hard(f"存在被强制降级的行（tier_downgraded）：{len(down)} 条 {down[:4]}")
    else:
        print("  ✅ 无 verified→无结论 的降级行（⑤ 单调性护栏未被 --force 绕过）")

    ver = [r for r in lat.values() if r.get("verification_tier") in VERIFIED]
    rep = [r for r in lat.values() if r.get("reproduced_any")]
    print(f"\n[2] 交付子集规模：verified {len(ver)} 条 / 复现 {len(rep)} 条 / 共 {len(lat)} 条")
    print(f"  tier 分布 {dict(collections.Counter(str(r.get('verification_tier')) for r in lat.values()).most_common())}")
    if len(ver) != len(rep):
        hard(f"verified 行数({len(ver)}) ≠ reproduced_any 行数({len(rep)}) —— 两者应完全一致")
    else:
        print(f"  ✅ verified 与 reproduced_any 一一对应（{len(ver)} 条）")

    # ── 3. tier 与评分/crash_type 的自洽（④ 的实际判据）──
    print("\n[3] tier ↔ 评分自洽（判据取自 ④ verify_one 的实际代码）")
    n_bad = 0
    for r in lat.values():
        t = r.get("verification_tier")
        repro = bool(r.get("reproduced_any"))
        ctm = r.get("crash_type_match")
        sub = r.get("frame_match_score")
        nrec = r.get("n_recovered_frames")
        if t == "none" and repro:
            hard(f"{r['osv_id']}: tier=none 但 reproduced_any=True"); n_bad += 1
        elif t in VERIFIED and not repro:
            hard(f"{r['osv_id']}: tier={t} 但 reproduced_any=False"); n_bad += 1
        elif t == "strict":
            if not ctm:
                hard(f"{r['osv_id']}: strict 但 crash_type_match 非真"); n_bad += 1
            elif sub is None or sub < T_STRICT:
                # recovered 0 帧时 ④ 最高只给 medium → strict 必须有 sub≥T_strict
                hard(f"{r['osv_id']}: strict 但 score_subseq={sub} < {T_STRICT}"); n_bad += 1
        # [W5 修：去掉 `nrec` 前置条件] 重读 ④ 的分支后发现：无论 recovered 帧是否为 0，
        # `medium ⇒ crash_type_match` 与 `loose ⇒ ¬crash_type_match` **都成立**
        #   （R 为空时：`medium if ct_match else loose`；R 非空时：`strict / medium(ctm) / loose`）。
        # 原来加 `and nrec` 反而**漏检** R 为空的那些行 —— 是牙齿测试抓出来的（注入 3 类违规只报 2 类）。
        elif t == "medium" and ctm is False:
            hard(f"{r['osv_id']}: medium 但 crash_type_match=False（④ 此时应判 loose；"
                 f"recovered {nrec} 帧）"); n_bad += 1
        elif t == "loose" and ctm is True:
            hard(f"{r['osv_id']}: loose 但 crash_type_match=True（④ 此时至少 medium；"
                 f"recovered {nrec} 帧）"); n_bad += 1
    if not n_bad:
        print(f"  ✅ {len(lat)} 条全部自洽（strict⇒crash_type一致∧subseq≥{T_STRICT}；"
              f"medium⇒crash_type一致；loose⇒不一致；none⇒没崩）")

    # ── 4. verified 行的证据完整性 ──
    print("\n[4] verified 行的证据完整性（指纹 + 配方 + 指针）")
    no_sha = [r["osv_id"] for r in ver if not r.get("binary_sha256")]
    no_rec = [r["osv_id"] for r in ver
              if not (r.get("pinned_commit") or r.get("commit_source") == "head")]
    dang_ver = [r["osv_id"] for r in ver
                if r.get("binary_dir") and not r.get("binary_pruned")
                and not os.path.isdir(r["binary_dir"])]
    dang_all = [r for r in lat.values()
                if r.get("binary_dir") and not r.get("binary_pruned")
                and not os.path.isdir(r["binary_dir"])]
    if no_sha:
        hard(f"verified 行缺 binary_sha256：{len(no_sha)} 条 {no_sha[:4]}")
    else:
        print(f"  ✅ {len(ver)} 条 verified 全部有 binary_sha256（可验证重建是否 bit 一致）")
    if no_rec:
        hard(f"verified 行缺重建配方：{len(no_rec)} 条 {no_rec[:4]}")
    else:
        print(f"  ✅ 全部有重建配方（pinned_commit 或 commit_source=head）")
    if dang_ver:
        hard(f"**verified 行悬空且未标记**：{len(dang_ver)} 条 {dang_ver[:4]}")
    else:
        print(f"  ✅ verified 行悬空指针 = 0（红线）")
    n_none_dang = len(dang_all) - len(dang_ver)
    if n_none_dang:
        soft(f"{n_none_dang} 条 none 档行的 binary_dir 悬空未标记（轮末 prune 在 ⑤ 之后跑；"
             f"§1.6 只交付 verified 子集 → 设计内，见 §5 item 27）")
        print(f"  ⓘ [软] none 档悬空 {n_none_dang} 条 = 设计内（已记 §5 item 27）")
    pruned = [r for r in lat.values() if r.get("binary_pruned")]
    bad_p = [r["osv_id"] for r in pruned if not r.get("binary_sha256")]
    if bad_p:
        hard(f"已标 binary_pruned 却丢了 sha256：{len(bad_p)} 条 {bad_p[:4]}")
    else:
        print(f"  ✅ 已回收的 {len(pruned)} 条全部留住 sha256（删除可恢复的前提）")

    # ── 4b. [W5 第十四轮 · N45/N46/N47 新增] 「verified = 可重放」的**实质**检验 ──
    # 旧审计只查 `binary_dir` 是不是目录 → N45/N46 躺在里面却报「0 条红线」。
    # 用户一句「一个 OSV 为什么有这么多二进制」把这条线头拽了出来。三条红线：
    print("\n[4b] 「可重放」的实质检验（N45 driver 在不在 / N46 超时算不算崩 / N47 exit_code）")
    # ① 复现记录表自证：`binary_sha256` 的键必须含它自己的 fuzz_target
    sha_no_tgt = [(r["osv_id"], r.get("fuzz_target"), list((r.get("binary_sha256") or {}))[:3])
                  for r in ver if r.get("fuzz_target")
                  and r.get("binary_sha256")
                  and r["fuzz_target"] not in r["binary_sha256"]]
    if sha_no_tgt:
        hard(f"**[N45] verified 行的 binary_sha256 不含自己的 fuzz_target**（落账那刻归档里就没有该 "
             f"driver → 不可重放）：{len(sha_no_tgt)} 条 {[(a, b) for a, b, _ in sha_no_tgt][:4]}")
    else:
        print(f"  ✅ [N45] {len(ver)} 条 verified 的 binary_sha256 都含自己的 fuzz_target")
    # ② 盘上实测：binary_dir 里必须有那个可执行文件
    disk_no_tgt = []
    for r in ver:
        bd, t = r.get("binary_dir"), r.get("fuzz_target")
        if not (bd and t and os.path.isdir(bd)):
            continue
        p = os.path.join(bd, t)
        if not (os.path.isfile(p) and os.access(p, os.X_OK)):
            disk_no_tgt.append((r["osv_id"], t, sorted(os.listdir(bd))[:4]))
    if disk_no_tgt:
        hard(f"**[N45] verified 行的 binary_dir 里没有它自己的可执行 driver**（实测重放会得到 "
             f"exit=127）：{len(disk_no_tgt)} 条 {[(a, b) for a, b, _ in disk_no_tgt][:4]}")
    else:
        print(f"  ✅ [N45] 盘上每条 verified 的 driver 都在（可直接重放）")
    # ③ 资源上限诊断不得算复现（N46）
    tolv = [r["osv_id"] for r in ver
            if str(r.get("observed_crash_type") or "").strip().lower() in rc.NON_CRASH_DIAGNOSTICS]
    if tolv:
        hard(f"**[N46] verified 行的实测类型是 libFuzzer 资源上限诊断（timeout/OOM），不是所报漏洞的"
             f"崩溃**：{len(tolv)} 条 {tolv[:4]}")
    else:
        print(f"  ✅ [N46] 没有 verified 行是靠 timeout/OOM 判成的（资源上限 ≠ 崩溃）")
    # ④ N47：exit_code 与「判成复现」不一致 —— **软性**（⑥ 按报告内容判崩是正确设计，
    #    exit_code 只是不可作判据；✅ 实测 3 条 libwebp exit=0 却有真 ASan 报告）
    ex_odd = [(r["osv_id"], r.get("exit_code")) for r in ver
              if r.get("exit_code") not in (1, None)]
    if ex_odd:
        soft(f"[N47] {len(ex_odd)} 条 verified 的 exit_code 不是 1（{ex_odd[:4]}）。⑥ 按**报告内容**"
             f"判崩而非退出码 → 这些是真崩溃（report 里有 sanitizer 报告）；但 exit_code 字段"
             f"**不可作判据**，已在 §4.58 记明")
        print(f"  ⓘ [软][N47] exit_code≠1 的 verified 行 {len(ex_odd)} 条 → 内容判崩救了它们"
              f"（若按退出码判，libwebp 会是 0/10）")
    else:
        print(f"  ✅ [N47] 所有 verified 行 exit_code==1")

    # ── 4c. [W5 第十五轮 · N53] 交付视图：**每条恰好 1 个 ELF** ──
    # 这条性质是**用户两次指出**的（「一个 OSV 为什么有这么多二进制」）：N49 把 `binary` 收窄成
    # 单文件却仍留 `out/` 指向整棵构建树 → 文件夹里照样有 2～17 个兄弟 fuzz target。
    # **应该由测试守着，而不是靠人眼看交付目录。**
    print("\n[4c] 交付视图 by_crash_type/：一个 OSV = 一次复现 = **一个**二进制")
    idx = os.path.join(ROOT, "artifacts", "by_crash_type")
    if not os.path.isdir(idx):
        soft("[N53] 交付视图尚未生成（python3 show_repro.py --build-index）→ 本项跳过")
        print("  ⓘ [软] 交付视图未生成，跳过")
    else:
        ents = [os.path.dirname(os.path.join(dp, f))
                for dp, _, fs in os.walk(idx) for f in fs if f == "INFO.txt"]
        need = ("testcase", "report.log", "replay.sh", "INFO.txt")
        multi, missi, nelf = [], [], collections.Counter()
        for d in ents:
            files = [f for f in os.listdir(d) if os.path.isfile(os.path.join(d, f))]
            k = 0
            for f in files:
                try:
                    if open(os.path.join(d, f), "rb").read(4) == b"\x7fELF":
                        k += 1
                except OSError:
                    pass
            nelf[k] += 1
            if k != 1:
                multi.append((d.split(os.sep)[-1], k, sorted(files)[:6]))
            for f in need:
                if not os.path.exists(os.path.join(d, f)):
                    missi.append((d.split(os.sep)[-1], f))
        if multi:
            hard(f"**[N53] 交付视图里有 {len(multi)} 个条目的 ELF 个数 ≠ 1**（一个 OSV 必须只对应"
                 f"一个二进制）：{[(a, b) for a, b, _ in multi][:4]}")
        else:
            print(f"  ✅ [N53] {len(ents)} 个条目**每条恰好 1 个 ELF**（分布 {dict(nelf)}）")
        if missi:
            hard(f"**[N53] 交付条目缺件**：{len(missi)} 处 {missi[:4]}")
        else:
            print(f"  ✅ [N53] {len(ents)} 个条目四件齐全（testcase/report.log/replay.sh/INFO.txt）")
        n_ev = len([1 for dp, _, fs in os.walk(idx) for f in fs
                    if os.path.islink(os.path.join(dp, f))
                    and not os.path.exists(os.path.join(dp, f))])
        if n_ev:
            hard(f"**[N53] 交付视图有 {n_ev} 个断链**")
        else:
            print(f"  ✅ [N53] 断链 0")
        # **[N60]** 两条补牙：① 交付条目数必须等于 verified 行数（少一条就是有 verified 行
        # 没被交付出去）；② purge 默认已关（§4.55），verified 行的归档**不该**处于「已回收」态
        # —— 原先 `dang_ver` 带 `not binary_pruned` 豁免，等于「自己回收了就免检」。
        if len(ents) != len(ver):
            hard(f"**[N60] 交付条目数 {len(ents)} ≠ verified 行数 {len(ver)}**（差 "
                 f"{len(ver)-len(ents)} 条 → 有 verified 行没被交付出去，或多出了幽灵条目）")
        else:
            print(f"  ✅ [N60] 交付条目数 {len(ents)} == verified 行数 {len(ver)}")
        pr_miss = [r["osv_id"] for r in ver
                   if r.get("binary_pruned") and not os.path.isdir(r.get("binary_dir") or "")]
        if pr_miss:
            hard(f"**[N60] verified 行标着 binary_pruned 且归档确实不在盘**（= 交付出去却不可重放；"
                 f"purge 默认已关，不该出现）：{len(pr_miss)} 条 {pr_miss[:4]}")
        else:
            print(f"  ✅ [N60] 无「已回收且不在盘」的 verified 行（purge 默认关 → 交付即可重放）")

    # ── 5. 溯源字段 ──
    print("\n[5] 溯源字段（能否从复现记录表追到原始 crash 与二进制）")
    miss = collections.Counter()
    for r in ver:
        for k in ("osv_id", "project", "sanitizer", "crash_type_expected", "fuzz_target",
                  "testcase_path", "run_id", "verification_tier"):
            if not r.get(k):
                miss[k] += 1
    if miss:
        hard(f"verified 行溯源字段缺失：{dict(miss)}")
    else:
        print(f"  ✅ 8 个溯源字段在 {len(ver)} 条 verified 行里全部非空")
    tc_missing = [r["osv_id"] for r in ver
                  if r.get("testcase_path") and not os.path.exists(r["testcase_path"])]
    if tc_missing:
        hard(f"testcase_path 指向不存在的文件：{len(tc_missing)} 条 {tc_missing[:3]}")
    else:
        print(f"  ✅ 全部 testcase_path 实际存在（复算输入可用）")

    # ── 6. 集中度（不是错误，但影响外推，必须显式报）──
    print("\n[6] 外推警示（不构成失败，但结论必须带这个前提）")
    byp = collections.Counter(r.get("project") for r in ver)
    top, topn = byp.most_common(1)[0]
    print(f"  verified 按项目：{dict(byp.most_common())}")
    print(f"  ⚠ 最大项目 {top} 占 {topn}/{len(ver)} = {topn/len(ver):.0%} → "
          f"复现率**不能当全局估计**（§4.43）")
    bys = collections.Counter(str(r.get("sanitizer")) for r in ver)
    print(f"  verified 按 sanitizer：{dict(bys.most_common())} → "
          f"{'⚠ UBSAN 为 0，未覆盖' if not bys.get('undefined') else 'UBSAN 有覆盖'}")

    if a.verbose and SOFT:
        print("\n[软性提示明细]")
        for s in SOFT:
            print("  ⓘ " + s)

    print("\n" + "═" * 88)
    if HARD:
        print(f"❌ 审计未通过：{len(HARD)} 条红线违反")
        for h in HARD[:10]:
            print("   - " + h)
        return 1
    print(f"✅ 审计通过：0 条红线违反；{len(SOFT)} 条软性提示（均可解释）")
    return 0


if __name__ == "__main__":
    sys.exit(main())

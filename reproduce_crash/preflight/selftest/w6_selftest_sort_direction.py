#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""W6：`manifest_builder --sort` 的**方向**自测（新发现 N75）。

✅ W6 实测：`--sort` 的两个取值**语义与名字相反**。

    对 `--projects matio,lcms --languages c,c++`（全量 87 条，其中 79 条有 fixed_commit）：

    | --sort 取值          | 前 6 条有 fixed_commit | commit_source            |
    |---------------------|----------------------|--------------------------|
    | fixed_first（默认）  | **0/6**              | introducing 5, head 1    |
    | no_fixed_first      | **6/6**              | fixed_parent 6           |
    | osv_id              | 6/6                  | fixed_parent 6           |

    全量口径下 79 条有修复者位于**第 9–87 位**，前 8 位全是无修复的。

根因（`manifest_builder.py` 的 `sort_key`）：
    has = 0 if fixed else 1        # 有修复→0；升序排 → 有修复在前（本就是 fixed_first）
    if args.sort == "fixed_first":
        has = 1 - has              # 反转 → 有修复→1；升序 → **有修复排到队尾**
    sel.sort(key=sort_key)         # 升序，无 reverse

即 `has = 1 - has` 这行把已经正确的顺序又翻了回去。

影响：`fixed_first` 是**默认值**，且 W5 的 help 文本声称已把默认从 no_fixed_first
改为 fixed_first（理由：has_fixed 走钉版的复现率 **45.7%** vs HEAD **6.7%**）。
但该反转使默认行为实际等于 no_fixed_first → 配 `--limit N` 时**系统性挑中最差的 N 条**。
按 45.7%/6.7% 折算，前 6 条的预期产出从 **2.7 条掉到 0.4 条（≈7×）**。
W5 help 里"92 条积压位于默认序第 196–2996 位、历轮 --limit ≤30 三轮都没碰到"
的现象与此完全一致 —— 说明 W5 那次修正并未真正生效。

判据：对同一 filter，`--sort fixed_first` 取前 K 条，其中**有 fixed_commit 的比例**
必须 ≥ `--sort no_fixed_first` 取前 K 条的比例；且当数据里同时存在两类时，
fixed_first 的前 K 条应**全部**有 fixed_commit（K ≤ 有修复者总数时）。

复算：python3 preflight/selftest/w6_selftest_sort_direction.py
"""
import json
import os
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, ROOT)

FAILS = []

# 固定用这一组作被测样本：✅ 实测全量 87 条 / 有 fixed_commit 79 条 / 无 8 条
# —— 两类都存在且比例悬殊，足以让方向错误暴露，又不至于跑太久。
PROJECTS = "matio,lcms"
K = 6


def ck(cond, msg):
    print(("  ✅ " if cond else "  ❌ ") + msg)
    if not cond:
        FAILS.append(msg)


def build(sort, limit=None, projects=None):
    """真跑 manifest_builder（不走 mock），返回 manifest 记录列表。"""
    tmp = tempfile.mkdtemp(prefix="w6_sort_")
    out = os.path.join(tmp, "manifest.jsonl")
    bg = os.path.join(tmp, "build_groups.json")
    cmd = [sys.executable, os.path.join(ROOT, "manifest_builder.py"),
           "--projects", projects or PROJECTS, "--languages", "c,c++",
           "--sort", sort, "--no-regression",
           "--out", out, "--build-groups", bg]
    if limit:
        cmd += ["--limit", str(limit)]
    p = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True, timeout=1800)
    if p.returncode != 0:
        print(f"     ⚠ manifest_builder rc={p.returncode}: {p.stderr[-300:]}")
        return None
    if not os.path.exists(out):
        return []
    with open(out, encoding="utf-8") as f:
        return [json.loads(l) for l in f if l.strip()]


def n_fixed(rows):
    return sum(1 for r in rows if r.get("fixed_commit"))


def main():
    print("=" * 78)
    print("W6 / N75：--sort 方向自测")
    print("=" * 78)

    print(f"\n[A] 全量口径（不截断）—— 确认样本里两类都存在，否则本测无意义")
    full = build("fixed_first")
    if full is None:
        print("  ❌ manifest_builder 执行失败，无法继续")
        return 1
    tot, fix = len(full), n_fixed(full)
    nofix = tot - fix
    print(f"     全量 {tot} 条：有 fixed_commit {fix} 条 / 无 {nofix} 条")
    ck(tot > 0, f"全量非空（{tot} 条）")
    ck(fix > 0 and nofix > 0,
       f"两类都存在（有修复 {fix} / 无修复 {nofix}）→ 方向错误可被检出")
    if not (fix > 0 and nofix > 0):
        print("\n  ⚠ 样本不具备区分力，后续断言无意义 → 判失败")
        print(f"\n❌ {len(FAILS)} 项未通过：{FAILS}")
        return 1

    print(f"\n[B] --sort fixed_first --limit {K} → 前 {K} 条应**全部**有 fixed_commit")
    ff = build("fixed_first", K)
    ck(ff is not None and len(ff) == K, f"确实产出 {K} 条（实得 {len(ff) if ff else 0}）")
    ck(ff is not None and n_fixed(ff) == K,
       f"fixed_first 的前 {K} 条全有修复提交（实得 {n_fixed(ff) if ff else 0}/{K}）"
       f"　← N75 的核心断言")

    print(f"\n[C] --sort no_fixed_first --limit {K} → 前 {K} 条应**尽量无** fixed_commit")
    nf = build("no_fixed_first", K)
    ck(nf is not None and len(nf) == K, f"确实产出 {K} 条（实得 {len(nf) if nf else 0}）")
    # 无修复者共 nofix 条；K ≤ nofix 时应一条都没有
    if nofix >= K:
        ck(nf is not None and n_fixed(nf) == 0,
           f"no_fixed_first 的前 {K} 条全无修复提交（实得 {n_fixed(nf) if nf else 0}/{K}）")
    else:
        ck(nf is not None and n_fixed(nf) <= K - nofix,
           f"无修复者仅 {nofix} 条 < K={K}，故至多 {K - nofix} 条有修复"
           f"（实得 {n_fixed(nf) if nf else 0}）")

    print(f"\n[D] 两个方向的产出必须**互不相同**（否则说明 sort 根本没生效）")
    ck(ff is not None and nf is not None and
       [r["osv_id"] for r in ff] != [r["osv_id"] for r in nf],
       "fixed_first 与 no_fixed_first 的前 K 条 osv_id 序列不同")

    print(f"\n[E] 负对照：sort 只改顺序，不得改**集合**")
    ck(ff is not None and nf is not None and
       {r["osv_id"] for r in ff} <= {r["osv_id"] for r in full} and
       {r["osv_id"] for r in nf} <= {r["osv_id"] for r in full},
       "两种排序取到的 osv_id 都属于全量集合（没有凭空多出/丢失记录）")
    ff_all = build("fixed_first")
    nf_all = build("no_fixed_first")
    ck(ff_all is not None and nf_all is not None and
       {r["osv_id"] for r in ff_all} == {r["osv_id"] for r in nf_all},
       f"不截断时两种排序的记录**集合相同**（各 {len(ff_all or [])} / {len(nf_all or [])} 条）")

    print(f"\n[F] 负对照：证明 [B] 不是恒真（用 osv_id 排序应介于两者之间或不同）")
    oi = build("osv_id", K)
    ck(oi is not None and len(oi) == K, f"osv_id 排序也产出 {K} 条（实得 {len(oi) if oi else 0}）")
    print(f"     参考：osv_id 前 {K} 条有修复 {n_fixed(oi) if oi else '?'}/{K}"
          f"（此值不参与判定，仅供人工比对方向是否合理）")

    # ── [N77] 可跑性必须参与排序 ────────────────────────────────────────────
    # ✅ W6 实测：`file` 项目 32 条崩溃中 17 条可跑（有 fuzz_target），
    #   但 `--sort fixed_first --limit 12` 取到的 **12/12 全部无 fuzz_target**
    #   → 该组「0 条可跑、0 次构建、4 秒结束、本轮无记录落盘」。
    #   根因：`fixed_first` 的次级键是 osv_id **升序** → 最老的崩溃排最前，
    #   而老崩溃恰恰最常缺 fuzz_target 元数据（全量口径无 target 者仅 11%，
    #   但按 fixed_first 取前 96 条时无 target 者高达 **55%**）。
    #   无 target 的记录不触发构建、成本近零，但它们**占满 --limit 名额**，
    #   等于把整轮预算浪费掉。
    print(f"\n[G] [N77] 可跑者优先：--limit 名额不得被「无 fuzz_target」的记录占满")
    FILE_K = 12
    f_full = build("fixed_first", None, projects="file")
    if f_full is None:
        ck(False, "file 项目 manifest 构建失败，无法判定 [G]")
    else:
        f_act = [r for r in f_full if not r.get("skip_reason")]
        f_no = [r for r in f_full if r.get("skip_reason")]
        print(f"     file 全量 {len(f_full)} 条：可跑 {len(f_act)} / 不可跑 {len(f_no)}")
        ck(len(f_act) > 0 and len(f_no) > 0,
           f"file 同时存在可跑({len(f_act)})与不可跑({len(f_no)})记录 → [G] 有区分力")
        f_top = build("fixed_first", FILE_K, projects="file")
        ck(f_top is not None and len(f_top) == FILE_K,
           f"取前 {FILE_K} 条（实得 {len(f_top) if f_top else 0}）")
        n_act = sum(1 for r in (f_top or []) if not r.get("skip_reason"))
        ck(n_act == min(FILE_K, len(f_act)),
           f"[N77] 前 {FILE_K} 条应**全部可跑**（可跑者共 {len(f_act)} 条，"
           f"故期望 {min(FILE_K, len(f_act))}；实得 {n_act}）")

    print(f"\n[H] [N77] 负对照：可跑者优先不得改变**不截断时**的记录集合")
    a_full = build("fixed_first", None, projects="file")
    ck(a_full is not None and f_full is not None and
       {r["osv_id"] for r in a_full} == {r["osv_id"] for r in f_full},
       "两次不截断构建的 osv_id 集合一致（排序改动只影响顺序，不影响取舍）")
    ck(f_full is not None and
       sum(1 for r in f_full if not r.get("skip_reason")) ==
       sum(1 for r in (a_full or []) if not r.get("skip_reason")),
       "可跑条数在排序改动前后不变（不得靠「丢弃不可跑记录」来通过 [G]）")

    print("\n" + "=" * 78)
    if FAILS:
        print(f"❌ {len(FAILS)} 项未通过：")
        for m in FAILS:
            print(f"   - {m}")
        return 1
    print("✅ 全部通过")
    return 0


if __name__ == "__main__":
    sys.exit(main())

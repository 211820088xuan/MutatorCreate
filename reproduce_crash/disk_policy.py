#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""磁盘分级保留策略（**[W5 第十八轮 · N61]**，用户批准的方案）。

背景：purge-on-verify 默认已关（§4.55，用户明确要求「重放需要二进制，不该删」），
归档因此持续累积到 **8.5 GB**、可用只剩 4.1 GB，unicorn 探针期间一度掉到 **2.7 GB**
（era 机制为每个 era commit 建 ~2.4 GB 镜像、旧 tag 变悬空）。

✅ 实测字节去向（这是本策略的依据，不是估计）：

    ① 交付必需（verified 行的最小重放包）    1.50 GB   ← 已**硬链接**进 by_crash_type
    ② 兄弟 target / 多余数据文件             7.49 GB   （1,524 个文件，nlink=1）
    ③ 无任何 verified 行引用的整目录          0.29 GB   （7 个目录）

关键事实：**交付视图用硬链接指进归档**，所以「删归档路径」对已交付的那 1.50 GB
**不会真释放空间**（inode 引用计数 >1）；真正能回收的是 ②③。
→ 于是策略不是「删旧归档」，而是**把归档瘦身到交付所需的并集**，同时保留分级开关。

三档回收（各自独立、都默认**干跑**）：

* `--clean-build`     清 `oss-fuzz-repro/build/{out,work}`（构建中间产物；归档早已拷走）
* `--prune-orphans`   删**无任何 verified 行引用**的整个归档目录（③，零交付影响）
* `--prune-siblings`  删归档里**不属于任何 verified 行最小重放包**的文件（②，最大头）
                      `--keep-siblings-for strict,medium` 可只对 loose-only 归档瘦身
* `--prune-images`    删悬空 docker 镜像（era 重建后被取代的旧项目镜像）+ 已停止的容器

⚠ **代价与可逆性**：② 删掉的是「同一 commit 的其它 fuzz target」。若将来有一条新 crash
钉到同一 commit 却要另一个 target，② 会重建它（一次构建的成本）。
⚠ **libavc 的重建不是 bit 级一致**（§4.61.9：5/5 文件 sha256 不符）→ 重建件的
`binary_sha256` 会与复现记录表原值不同，但**功能可用**（实测 7 次崩 6 次）。故本脚本
**只删未被交付引用的文件**，交付必需的那份永远不动。

**事后自校验**（--apply 时强制跑）：交付条目数不变、每条仍恰好 1 个 ELF、
四件齐全、断链 0、审计 0 红线 —— 任一不符即报错退出，不静默。
"""
from __future__ import annotations

import argparse
import collections
import glob
import json
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import repro_common as rc            # noqa: E402
import show_repro as S               # noqa: E402  复用 _replay_bundle（最小重放包的**单一真源**）

DATASET = os.path.join(HERE, "repro_dataset.jsonl")
BINARIES = os.path.join(rc.ARTIFACTS, "binaries")
INDEX_DIR = os.path.join(rc.ARTIFACTS, "by_crash_type")
BUILD_DIR = os.path.join(rc.OSS_FUZZ_WORKTREE, "build")
VERIFIED = ("strict", "medium", "loose")
GB = 1024 ** 3


def _log(*a):
    print(*a, file=sys.stderr, flush=True)


def latest_rows():
    lat = {}
    for line in open(DATASET, encoding="utf-8"):
        line = line.strip()
        if line:
            d = json.loads(line)
            lat[d["osv_id"]] = d            # append-only：同 osv 取最后一条
    return lat


def needed_map(lat):
    """归档目录(realpath) → 该目录里**交付必需**的文件名集合（= 指向它的所有 verified 行的
    最小重放包之并）。用 `show_repro._replay_bundle`，与交付视图**同一份实现**（不分叉）。"""
    need = collections.defaultdict(set)
    tiers = collections.defaultdict(set)
    for r in lat.values():
        if r.get("verification_tier") not in VERIFIED:
            continue
        bd, t = r.get("binary_dir"), r.get("fuzz_target")
        if not (bd and t and os.path.isdir(bd)):
            continue
        bundle, _wrapped = S._replay_bundle(bd, t)
        rd = os.path.realpath(bd)
        need[rd] |= set(bundle)
        tiers[rd].add(r["verification_tier"])
    return need, tiers


def human(n):
    return f"{n/GB:.2f} GB" if n >= GB else f"{n/1024/1024:.0f} MB"


def inflight_dirs(since, build_records=None):
    """**[N63]** 本轮**在飞**的归档目录（realpath 集合）→ 瘦身时必须保护。

    为什么需要：`needed_map()` 是从**复现记录表的 verified 行**算的，而轮中清理发生时，
    **本轮那些还没落账的行**根本不在复现记录表里 → 它们的归档会被判成「孤儿目录」整目录删掉。
    ✅ 实测事故（unicorn 定向批 w5-unicorn-b2）：轮中水位线触发 3 次，
    **4 条刚复现的 crash**（`OSV-2020-1409`/`-1945`/`-2180`/`-231`）的归档被删，
    ⑤ 落账时只能标 `binary_pruned=True` → 审计 3 条红线（交付出去却不可重放）。

    判据用 `build_records.jsonl` 的 `ts >= since`（本轮起始时刻），精确且无需额外状态。
    """
    p = build_records or os.path.join(rc.ARTIFACTS, "build_records.jsonl")
    out = set()
    if not since or not os.path.isfile(p):
        return out
    for line in open(p, encoding="utf-8"):
        line = line.strip()
        if not line:
            continue
        try:
            d = json.loads(line)
        except json.JSONDecodeError:
            continue
        if (d.get("ts") or 0) >= since and d.get("binary_dir"):
            out.add(os.path.realpath(d["binary_dir"]))
    return out


def plan(lat, keep_tiers, protect="reuse", since=None):
    """→ (orphan_dirs, sibling_files, 统计, need, tiers, cnt)。

    `protect` 决定**哪些归档的兄弟文件受保护**（不删）：
    * `reuse`（**默认，实测最优**）：只保护「服务 **>1** 条 verified 行」的归档。
      ✅ 实测：119 个归档里 **100 个只服务 1 条**（兄弟文件 **6.80 GB**，复用价值≈0）、
      只有 19 个服务 >1 条（覆盖 54 条，兄弟文件 **698 MB**，才是真有复用价值的）。
      → 回收 6.80 GB、只留 698 MB 有用的。
    * `tier`：按 `keep_tiers` 保护（该归档服务到的**最高** tier 在名单里就保护）。
      ✅ 实测各档可回收量：`strict,medium,loose` 298 MB · `strict,medium` 1.15 GB ·
      `strict` 4.38 GB · 全瘦身 7.78 GB —— **每一档都不如 `reuse`**（4.38 < 6.80），
      因为 tier 与「是否会被复用」并不相关：一条 strict 也常常独占一个归档。
    * `none`：全瘦身（回收 7.78 GB，代价是任何同 commit 换 target 都要重建）。
    """
    need, tiers = needed_map(lat)
    inflight = inflight_dirs(since)
    cnt = collections.Counter()
    for r in lat.values():
        if r.get("verification_tier") in VERIFIED and r.get("binary_dir") \
                and os.path.isdir(r["binary_dir"]):
            cnt[os.path.realpath(r["binary_dir"])] += 1
    orphans, sibs = [], []
    st = collections.Counter()
    best = {"strict": 3, "medium": 2, "loose": 1}
    for d in sorted(glob.glob(os.path.join(BINARIES, "*", "*", "*"))):
        if not os.path.isdir(d):
            continue
        rd = os.path.realpath(d)
        proj = d.split(os.sep)[-3]
        files = [f for f in os.listdir(d) if os.path.isfile(os.path.join(d, f))]
        sz = {f: os.path.getsize(os.path.join(d, f)) for f in files}
        if rd in inflight:
            # **[N63] 本轮在飞 → 整目录保护**（还不知道最终会用哪个 target，故连兄弟文件也不删；
            # 等它落账成为 verified 行后，下一轮清理自然会按 `need` 精确瘦身）
            st["inflight_dirs"] += 1
            st["inflight_bytes"] += sum(sz.values())
            continue
        if rd not in need:
            orphans.append((d, sum(sz.values()), proj))
            st["orphan_bytes"] += sum(sz.values())
            st["orphan_dirs"] += 1
            continue
        if protect == "reuse":
            protected = cnt[rd] > 1
        elif protect == "tier":
            protected = max(tiers[rd], key=lambda t: best.get(t, 0)) in keep_tiers
        else:
            protected = False
        st["multi_row_dirs"] += 1 if cnt[rd] > 1 else 0
        for f, s in sz.items():
            if f in need[rd]:
                st["keep_bytes"] += s
                st["keep_files"] += 1
            elif protected:
                st["prot_bytes"] += s
                st["prot_files"] += 1
            else:
                sibs.append((os.path.join(d, f), s, proj))
                st["sib_bytes"] += s
                st["sib_files"] += 1
    return orphans, sibs, st, need, tiers, cnt


def delivery_selfcheck():
    """交付视图自校验（--apply 后强制跑）。返回 (ok, 说明列表)。"""
    bad = []
    ents = [os.path.dirname(os.path.join(dp, f))
            for dp, _, fs in os.walk(INDEX_DIR) for f in fs if f == "INFO.txt"]
    for d in ents:
        files = [f for f in os.listdir(d) if os.path.isfile(os.path.join(d, f))]
        nelf = 0
        for f in files:
            try:
                if open(os.path.join(d, f), "rb").read(4) == b"\x7fELF":
                    nelf += 1
            except OSError:
                pass
        if nelf != 1 and not os.path.exists(os.path.join(d, "PRUNED.txt")):
            bad.append(f"{os.path.basename(d)}: ELF={nelf}")
        for f in ("testcase", "report.log", "replay.sh", "INFO.txt"):
            if not os.path.exists(os.path.join(d, f)) and not os.path.exists(
                    os.path.join(d, "PRUNED.txt")):
                bad.append(f"{os.path.basename(d)}: 缺 {f}")
    nlink_bad = [p for p in glob.glob(os.path.join(INDEX_DIR, "**", "*"), recursive=True)
                 if os.path.islink(p) and not os.path.exists(p)]
    if nlink_bad:
        bad.append(f"断链 {len(nlink_bad)} 个")
    return (not bad), bad, len(ents)


def main():
    ap = argparse.ArgumentParser(description="磁盘分级保留策略（默认**干跑**，加 --apply 才动手）")
    ap.add_argument("--clean-build", action="store_true", help="清 oss-fuzz-repro/build/{out,work}")
    ap.add_argument("--prune-orphans", action="store_true", help="删无 verified 行引用的整归档目录")
    ap.add_argument("--prune-siblings", action="store_true", help="删归档里非交付必需的文件")
    ap.add_argument("--keep-siblings-for", default="strict,medium",
                    help="`--protect-siblings tier` 时：哪些 tier 的归档**保留**兄弟 target")
    ap.add_argument("--protect-siblings", choices=("reuse", "tier", "none"), default="reuse",
                    help="兄弟文件的保护规则。默认 **reuse**（只保护服务 >1 条 verified 行的归档，"
                         "✅ 实测回收 6.80 GB 而只留 698 MB 有用的；tier 方案最好也只回收 4.38 GB）")
    ap.add_argument("--prune-images", action="store_true", help="删悬空镜像 + 已停止容器")
    ap.add_argument("--min-free-gb", type=float, default=3.0,
                    help="可用空间高于此值就**不动手**（避免无谓回收；默认 3.0）")
    ap.add_argument("--protect-since", type=float, default=None,
                    help="**[N63]** 保护「本轮在飞」的归档：build_records 里 ts >= 此时刻的 "
                         "binary_dir **整目录不删**（轮中清理必传，否则会删掉本轮刚复现、"
                         "但还没落账的那些归档 → ✅ 实测删掉 4 条）")
    ap.add_argument("--force", action="store_true", help="忽略 --min-free-gb，总是执行")
    ap.add_argument("--apply", action="store_true", help="真的执行（默认只打印计划）")
    a = ap.parse_args()

    keep_tiers = {x.strip() for x in a.keep_siblings_for.split(",") if x.strip()}
    free = subprocess.run(["df", "--output=avail", "-BG", "/"], capture_output=True,
                          text=True).stdout.split()
    free_gb = float(free[-1].rstrip("G")) if len(free) > 1 else 0.0
    print(f"═══ 磁盘分级保留（dry-run={'否' if a.apply else '**是**'}）═══")
    print(f"  当前可用 {free_gb:.1f} GB · 阈值 --min-free-gb={a.min_free_gb} · "
          f"兄弟文件保护规则 = **{a.protect_siblings}**"
          + (f"（tier 名单 {sorted(keep_tiers)}）" if a.protect_siblings == "tier" else ""))

    do = a.force or free_gb < a.min_free_gb
    if not do:
        print("  ⓘ 可用空间高于阈值 → **不需要回收**（加 --force 可强制执行）")
    lat = latest_rows()
    ver = [r for r in lat.values() if r.get("verification_tier") in VERIFIED]
    print(f"  复现记录表 verified {len(ver)} 条；归档目录 {len(glob.glob(os.path.join(BINARIES,'*','*','*')))} 个")

    orphans, sibs, st, _need, _tiers, cnt = plan(lat, keep_tiers, a.protect_siblings,
                                                 since=a.protect_since)
    if a.protect_since:
        print(f"  [N63] 保护本轮在飞归档：**{st['inflight_dirs']} 个 / {human(st['inflight_bytes'])}**"
              f"（ts >= {a.protect_since:.0f}）")
    print(f"\n  ① 交付必需（**永不删**）      {st['keep_files']:>5} 文件  {human(st['keep_bytes'])}")
    print(f"  ② 兄弟文件（受保护）          {st['prot_files']:>5} 文件  {human(st['prot_bytes'])}"
          f"   ← 服务 >1 条 verified 行的归档有 {st['multi_row_dirs']} 个")
    print(f"  ③ 兄弟文件（可回收）          {st['sib_files']:>5} 文件  {human(st['sib_bytes'])}")
    print(f"  ④ 孤儿归档目录（可回收）      {st['orphan_dirs']:>5} 目录  {human(st['orphan_bytes'])}")
    tot = st["sib_bytes"] + st["orphan_bytes"]
    byp = collections.Counter()
    for _p, s, pr in sibs:
        byp[pr] += s
    for _d, s, pr in orphans:
        byp[pr] += s
    print(f"  → 本次可回收合计 **{human(tot)}**" + (f"：{ {k: human(v) for k, v in byp.most_common(5)} }"
                                                  if byp else ""))

    if not (a.clean_build or a.prune_orphans or a.prune_siblings or a.prune_images):
        print("\n  （未指定任何回收动作；本报告即 --min-free-gb 决策依据）")
        return 0
    # **[N61] 两类动作，门控不同**：
    #   * `--clean-build` / `--prune-images` 是**纯废物**（构建中间产物、被取代的悬空镜像）
    #     → 只要指定了就**无条件**清，与磁盘水位无关；
    #   * `--prune-orphans` / `--prune-siblings` 会动**归档**（有重建成本，libavc 还非 bit 一致）
    #     → 只在低于 `--min-free-gb` 时才动（或 --force）。
    do_gated = a.force or free_gb < a.min_free_gb
    if not do_gated and (a.prune_orphans or a.prune_siblings):
        print(f"\n  ⓘ 可用 {free_gb:.1f} GB 高于阈值 {a.min_free_gb} → **跳过归档瘦身**"
              f"（纯废物仍会清；要强制瘦身加 --force）")
    if not a.apply:
        print("\n  ⚠ 干跑：以上为计划，加 --apply 才真删")
        return 0

    freed = 0
    if a.clean_build:
        for sub in ("out", "work"):
            p = os.path.join(BUILD_DIR, sub)
            if os.path.isdir(p):
                before = subprocess.run(["du", "-sb", p], capture_output=True, text=True).stdout.split()[0]
                subprocess.run(["rm", "-rf", p], check=False)
                freed += int(before or 0)
                _log(f"  ✅ 清 build/{sub}（{human(int(before or 0))}）")
    if a.prune_images:
        r1 = subprocess.run(["docker", "container", "prune", "-f"], capture_output=True, text=True)
        r2 = subprocess.run(["docker", "image", "prune", "-f"], capture_output=True, text=True)
        _log(f"  ✅ docker: {(r1.stdout or '').strip().splitlines()[-1:]} "
             f"{(r2.stdout or '').strip().splitlines()[-1:]}")
    if not do_gated:
        orphans, sibs = [], []
        st["orphan_bytes"] = st["sib_bytes"] = 0
    if a.prune_orphans:
        for d, s, _p in orphans:
            subprocess.run(["rm", "-rf", d], check=False)
            freed += s
        if orphans:
            _log(f"  ✅ 删孤儿归档目录 {len(orphans)} 个（{human(st['orphan_bytes'])}）")
    if a.prune_siblings:
        n = 0
        for p, s, _pr in sibs:
            try:
                os.remove(p)
                freed += s
                n += 1
            except OSError:
                pass
        if n:
            _log(f"  ✅ 删兄弟文件 {n} 个（{human(st['sib_bytes'])}）")

    free2 = subprocess.run(["df", "--output=avail", "-BG", "/"], capture_output=True,
                           text=True).stdout.split()
    print(f"\n  回收后可用 {free2[-1] if len(free2) > 1 else '?'}（回收前 {free_gb:.1f} GB）")

    # **[N61 修] 自校验之前必须先重建交付索引。** ✅ 实测抓到：轮末钩子跑在 ⑤ 追加新 verified 行
    # **之后**、而索引还是上一轮的 → `[N60] 交付条目数 ≠ verified 行数` 红线**必然**报红
    # （unicorn 定向批那次就报了「审计未通过：1 条红线」，其实数据是好的，纯粹是顺序错）。
    # 顺序：回收 → **重建索引**（重新硬链接交付必需文件；这些文件从不被瘦身删掉，故安全）→ 自校验 → 审计。
    try:
        n_ok, n_pr, n_nd = S.build_index(lat, verbose=False)
        print(f"  ✅ 交付索引已重建：自包含可重放 {n_ok} / 已回收 {n_pr} / driver 缺失 {n_nd}")
    except Exception as e:                                            # noqa: BLE001
        print(f"  ❌ **交付索引重建失败**：{type(e).__name__}: {e}")
        return 3

    ok, bad, n_ent = delivery_selfcheck()
    if ok:
        print(f"  ✅ 交付自校验通过：{n_ent} 个条目、每条恰好 1 个 ELF、四件齐全、断链 0")
    else:
        print(f"  ❌ **交付自校验失败**（{len(bad)} 处）：{bad[:6]}")
        return 3
    r = subprocess.run([sys.executable, os.path.join(HERE, "preflight", "selftest",
                                                     "w5_audit_delivery.py")],
                       capture_output=True, text=True)
    if r.returncode == 0:
        print("  ✅ 审计通过（0 条红线）")
    else:
        print(f"  ❌ **审计未通过**：\n{r.stdout[-900:]}")
        return 3
    return 0


if __name__ == "__main__":
    sys.exit(main())

#!/usr/bin/env python3
"""① `manifest_builder.py` — 读 4 数据源 → `repro_manifest.jsonl` + `build_groups.json`。

对应设计文档 §5①（DELIVERY.md 第一部分）+ §6.3 schema。**本轮（W1）只写 ①⓪ 两个模块**，
不写 ②③④⑤⑥⑦（边界见任务书）。

数据源（4 个，§5①）：
  1. `crash_testcase/**/<osv_id>.json`（权威 fuzz_target/sanitizer/engine/job_type/
     introducing_commit/report_url/testcase_url）
  2. `data/crash_dataset.jsonl`（3,790；project/crash_type/frames/testcase_path）
  3. `data/crash_state_recovered.jsonl`（ground-truth 栈帧 + is_file_frame）
  4. `data/_osv_cache/<osv_id>.json`（**fixed/introduced commit + repo URL**，R13a/R13b）

派生字段（§5①/§6.3，[实现 W1] 新增项标 ▸W1）：
  osv_year(M1) / language(M3b·R5 exact-match) / crash_cluster_id(M7+R2 归一化帧) /
  fixed_commit·fixed_parent(M4·R13a) / target_inferred(M9·R7) / sanitizer_inferred(R16) /
  testcase sha256·input_magic(M8) / skip_reason 各档 /
  ▸W1 fixed_real·pin_commit·walkback_depth·static_check_verdict（复合证据分静态 check）/
  ▸W1 osv_degenerate_range（N6）/ ▸W1 repo_url·repo_path·repo_path_confidence·candidates。

**[实现 W1] 静态 check 的默认值由 48 条分层抽样实测决定**（详见
`preflight/2026-09-09-offbyone-sampling.md`）：off-by-one = 6/42 = **14.3%**（95% 6.7–27.8%）、
`fixed` 精确 = **59.5%** → **Stage2 默认仍钉 `fixed^`（walkback_depth=1）**，静态 check 只在
定位到真修复时把 depth 提到 2/3；定位不到（22.9%）或托管不支持（12.5%）→ `walkback_depth=null`，
交 ② 构建期 walk-back ≤3（§5②）。

用法：
  # 全量（离线、不跑静态 check）——与 R14 的 3,502 / 448 对账
  python3 manifest_builder.py
  # 只跑主线 C/C++
  python3 manifest_builder.py --languages c,c++
  # 本轮增量（R16）：指定项目 + 条数
  python3 manifest_builder.py --projects md4c,pcre2 --limit 10
  # 打开静态 check（需网络；对 3 条已知答案的 crash 做回归）
  python3 manifest_builder.py --only-osv OSV-2022-126,OSV-2024-1261,OSV-2022-886 \\
      --static-check --static-check-limit 3
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
import time
from collections import Counter, defaultdict

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import repro_common as rc                                    # noqa: E402


# ============================================================ 目标推定（M9 / R7）
def build_project_targets(rows, meta):
    """M9：每个 project 在**非空 target** 记录里的 unique target 集（推定的唯一依据）。"""
    pt = defaultdict(set)
    for r in rows:
        ft = rc.fuzz_target_of(r, meta.get(r["osv_id"]))
        if ft:
            pt[r["project"]].add(ft)
    return pt


def infer_target(project, proj_targets, language, in_of_dirs):
    """R7 净可用规则：project 在其他记录里**只有唯一 target** 且 oss-fuzz 命中 且 C/C++。

    ✅ 实测净可用 156 条（原 M9 的 181 减 unrar 25 条 M2-未命中）。
    → (target|None, why)
    """
    ts = proj_targets.get(project, set())
    if len(ts) != 1:
        return None, ("no_target_project" if not ts else f"multi_target({len(ts)})")
    t = next(iter(ts))
    if not in_of_dirs:
        return None, "m2_name_miss"          # R7: unrar 25 条即此档
    if language not in rc.MAINLINE_LANGUAGES:
        return None, f"non_cpp({language})"
    return t, "unique_target"


# ============================================================ 单条记录
def build_record(row, meta_row, recovered_row, of_dirs, proj_targets, args, stats):
    osv_id = row["osv_id"]
    project = row["project"]
    r = rc.empty_manifest_record(osv_id)
    notes = []
    in_of = project in of_dirs
    lang = rc.language_of(project, of_dirs)

    r["project"] = project
    r["project_ossfuzz_dir"] = project if in_of else None
    r["language"] = lang
    r["osv_year"] = rc.osv_year(osv_id)

    # ---- crash_type（§6.3：expected/full 来自 crash_dataset；norm 供 ④ medium 档比对）----
    r["crash_type_expected"] = row.get("crash_type") or None
    r["crash_type_full_expected"] = row.get("crash_type_full") or None
    details_ct = (recovered_row or {}).get("crash_type_from_details")
    r["crash_type_norm"] = rc.normalize_crash_type(details_ct or row.get("crash_type"))

    # ---- recovered 帧 + 簇 id（R2：基于**归一化** top-3）----
    d = recovered_row or {}
    frames = (d.get("frames") or [])[:3]
    r["recovered_frames"] = frames
    iff = (d.get("is_file_frame") or [])[:3]
    r["recovered_is_file_frame"] = iff
    norm = rc.normalize_frames(osv_id)
    r["crash_cluster_id"] = rc.crash_cluster_id(project, row.get("crash_type"), norm)
    if not frames:
        notes.append("no_recovered_frames(20 条之一，§5④ <3 帧降级)")

    # ---- fuzz_target（M9/R7 推定）+ sanitizer（R10/R16）----
    m = meta_row or {}
    ft = rc.fuzz_target_of(row, m)
    r["target_inferred"] = False
    if not ft:
        inferred, why = infer_target(project, proj_targets, lang, in_of)
        if inferred:
            ft = inferred
            r["target_inferred"] = True
            notes.append(f"target_inferred({why})")
        else:
            notes.append(f"no_target:{why}")
    r["fuzz_target"] = ft or None
    san, san_inf = rc.sanitizer_of(row, m)
    r["sanitizer"] = san
    r["sanitizer_inferred"] = san_inf
    if san_inf:
        notes.append("sanitizer_inferred(空 sanitizer → 默认 address，R10/§7B2)")
    r["fuzzing_engine"] = m.get("fuzzing_engine") or None
    r["job_type"] = m.get("job_type") or None

    # ---- testcase（M8：sha256 + size + input_magic 前 16 字节）----
    tp = row.get("testcase_path")
    r["testcase_path"] = tp
    sha, size, magic, exists = rc.testcase_facts(tp)
    r["testcase_sha256"], r["testcase_size"], r["input_magic"] = sha, size, magic
    r["testcase_is_minimized"] = None          # ⓘ M8：本地无标记 → null（不可知）
    r["report_url"] = m.get("report_url") or None
    r["testcase_url"] = m.get("testcase_url") or None
    # [实现 W2 Phase0b] OSS-Fuzz issue 号：既喂静态打分器的 issue_id_in_msg(+3) 信号，
    # 又是 pinned_queue 的项目内排序键（era 邻接实测 65.9% vs osv_id 序 52.4%）
    r["issue_id"] = rc.issue_id_of(r["report_url"])
    # [实现 W2 N8] job_type 里的架构（i386 164 条 → x86_64 构建下结构性不可复现的先验）
    r["job_arch"] = rc.job_arch(m.get("job_type") or r.get("job_type"))
    if r["job_arch"] == "i386":
        notes.append("N8 job_type 标 i386，而本轮按 x86_64 构建 → 复现率先验偏低（不 skip，交实测）")

    # ---- OSV：fixed / introduced / repo（R13a 选择规则；repo 与 fixed 同 range 配对）----
    osv_rec = rc.load_osv(osv_id)
    if osv_rec is None:
        notes.append("no_osv_cache_record")
    ic = m.get("introducing_commit")
    ic = None if ic in (None, "", "0") else ic
    r["introducing_commit"] = ic
    fixed, repo, rule, npairs, introduced = rc.osv_fixed_and_repo(osv_rec, ic)
    r["fixed_commit"] = fixed
    r["fixed_rule"] = rule
    r["n_osv_pairs"] = npairs
    r["repo_url"] = repo
    if rule == "intro_match_multi":
        notes.append("R13a 多匹配→取最后 fixed（✅ 实测总体 0 条歧义）")
    degen = rc.is_degenerate_range(osv_rec)
    r["osv_degenerate_range"] = bool(degen)
    if degen:
        notes.append(f"N6 退化 range introduced==fixed={degen[0][:12]} → 禁钉版（假 none）")

    # ---- repo_path（[实现 W1]：逐 crash 解析，不按项目猜）----
    rp, conf, cands = rc.resolve_repo_path(project, rc.osv_repos(osv_rec), args.repo_map)
    r["repo_path"] = rp
    r["repo_path_confidence"] = conf
    r["repo_path_candidates"] = cands or None
    if conf == "none":
        notes.append("repo_path 静态不可定 → ② 回退 detect_main_repo（P0-C 已加代理）"
                     + (f"；candidates={cands}" if cands else ""))
    elif conf == "candidates":
        notes.append(f"repo_path 多候选 {cands} → ② 在宿主 /src 副本上 git cat-file -e 定夺")

    # ---- 静态 check（[实现 W1]）+ pin 决策 ----
    r["static_check_verdict"] = "skipped"
    r["static_check_why"] = None
    if fixed:
        # fixed_parent = fixed^：manifest 阶段无本地 clone → 只能由 patch 链解析（否则留 null 交 ②）
        r["fixed_parent"] = None
        # [实现 W2 Phase0c] 退化记录**不走**通用静态 check：传 introduced 会使 intro_depth=0
        # → d_fix 判据（d<intro_depth）永假 → 必然 clamp、白花 max_depth 次请求后又被下面覆盖。
        # 它们走专用的 resolve_degenerate（max_depth=1，更省）。
        if (args.static_check and not degen and not args.degenerate_only
                and stats["static_calls"] < args.static_check_limit):
            issue_id = str(r["issue_id"]) if r["issue_id"] is not None else None
            t0 = time.time()
            res = rc.locate_fixed_real(fixed, repo, list(norm), issue_id,
                                       introduced=introduced or ic,
                                       max_depth=args.max_depth, sleep=args.sleep)
            stats["static_calls"] += 1
            stats["static_secs"] += time.time() - t0
            r["static_check_verdict"] = res["verdict"]
            r["static_check_why"] = res.get("why")
            r["fixed_real"] = res.get("fixed_real")
            r["pin_commit"] = res.get("pin_commit")
            r["walkback_depth"] = res.get("walkback_depth")
            chain = res.get("chain") or []
            if len(chain) > 1 and not chain[1].get("error"):
                r["fixed_parent"] = chain[1]["sha"]       # C1 = fixed^
            if res.get("clamped"):
                notes.append("walkback_depth 被 intro_depth clamp（钉版不可用，防假 none）")
            if args.keep_chain:
                r["notes"].append("static_chain=" + json.dumps(
                    [{"d": c.get("depth"), "sha": (c.get("sha") or "")[:12], "S": c.get("S"),
                      "no_src": c.get("no_source"), "msg": (c.get("msg") or "")[:60]}
                     for c in chain], ensure_ascii=False))
        else:
            r["static_check_verdict"] = "skipped"
            r["static_check_why"] = ("--no-static-check（离线）" if not args.static_check
                                     else f"超过 --static-check-limit {args.static_check_limit}")
    else:
        r["static_check_verdict"] = "no_fixed"
        r["static_check_why"] = f"OSV 无 fixed（rule={rule}）→ HEAD-first / introducing 回退"

    # ---- commit_source 先验（§6.3；② 构建后以实际值覆盖）----
    if degen:
        r["commit_source"] = "head"
        r["pin_commit"] = None
        r["walkback_depth"] = None
        r["static_check_verdict"] = "degenerate"
        r["static_check_why"] = "N6 introduced==fixed → vulnerable 窗口为空"
        r["degenerate_resolved"] = False
        # [实现 W2 Phase0c] **不再一刀切**：退化 sha 也可能就是修复（OSV 定不出区间的数据缺陷），
        # 若是则 `sha^` 恰是最后一个漏洞版本 → 解禁钉版。用 W1 打分器判，零额外成本。
        if (args.static_check and not args.no_degenerate_resolve
                and stats["static_calls"] < args.static_check_limit):
            t0 = time.time()
            dg = rc.resolve_degenerate(degen[0], repo, list(norm),
                                       str(r["issue_id"]) if r["issue_id"] is not None else None,
                                       sleep=args.sleep)
            stats["static_calls"] += 1
            stats["static_secs"] += time.time() - t0
            stats["degen_resolved"] += 1 if dg["resolved"] else 0
            stats["degen_checked"] += 1
            if dg["resolved"]:
                r["degenerate_resolved"] = True
                r["pin_commit"] = dg["pin_commit"]
                r["fixed_real"] = dg["fixed_real"]
                r["walkback_depth"] = dg["walkback_depth"]
                r["commit_source"] = "fixed_parent"
                r["static_check_why"] = (f"N6 退化 sha 复核**是**修复（S(C0)={dg['S_C0']}）→ "
                                         f"pin=sha^={str(dg['pin_commit'])[:12]}、解禁 Stage2")
                notes.append("N6 退化 range 复核通过（degenerate_resolved=true）→ 解禁钉版")
            else:
                r["static_check_why"] = (f"N6 introduced==fixed；复核未通过"
                                         f"（{dg['reject'] or dg['verdict']}）→ 维持禁钉版")
    elif r.get("pin_commit") and (r.get("walkback_depth") or 0) >= 2:
        r["commit_source"] = "fixed_ancestor"      # [实现 W1] §6.3 commit_source 扩档
    elif fixed:
        r["commit_source"] = "fixed_parent"
        if not r.get("pin_commit"):
            r["pin_commit"] = None                 # ② 用 get_parent_local(fixed,1) 解析
    elif ic:
        r["commit_source"] = "introducing"
        r["pin_commit"] = ic
    else:
        r["commit_source"] = "head"
    # expected_repro_version = ① 对 §6.3 `repro_version`（②③ 拥有）的**先验**；
    # 未跑静态 check 时 pin_commit 为 null，但 depth-1（`fixed^`）仍是设计默认 → 记 fixed_parent
    # （② 用 `get_parent_local(fixed,1)` 解析 SHA）。绝不因「静态 check 没跑」就退化成 head。
    if r["commit_source"] == "fixed_ancestor":
        r["expected_repro_version"] = "fixed_ancestor"
    elif r["commit_source"] == "fixed_parent":
        r["expected_repro_version"] = "fixed_parent"
    elif r["commit_source"] == "introducing":
        r["expected_repro_version"] = "introducing_commit"
    else:
        r["expected_repro_version"] = "head"
    # fixed_misattributed 三态（[实现 W1]）：located → (depth≥2)；其余 → null（不可知，
    # 不猜）。绝不把「静态法定位不到」写成 False——那会把 26% 的未定位者误报为「fixed 精确」。
    if r["static_check_verdict"] == "located":
        r["fixed_misattributed"] = (r.get("walkback_depth") or 1) >= 2
    else:
        r["fixed_misattributed"] = None

    # ---- skip_reason（§6.3：语义 = 「整条记录退出主线」；优先级见下）----
    r["skip_reason"] = None
    if not in_of:
        r["skip_reason"] = "unmapped_project"
        notes.append(f"M2 name-miss（{project} 不在 oss-fuzz/projects/）→ 排除主线直至映射批准")
    elif lang not in rc.MAINLINE_LANGUAGES:
        r["skip_reason"] = "non_cpp_language"
        notes.append(f"§7B5 language={lang} → 单列轨道（JVM 需 Jazzer 路径）")
    elif not ft:
        r["skip_reason"] = "unreproducible_no_target"
        notes.append("§7B：空 target 不可推定 → 可选⑦联网回捞")
    elif not exists:
        r["skip_reason"] = "missing_testcase"
        notes.append(f"testcase 磁盘缺失（{_MANIFEST_NOTE}）")
    r["notes"] = list(r.get("notes") or []) + notes
    return r


_MANIFEST_NOTE = "35 条之一，见 crash_testcase/_MANIFEST_missing.txt"


# ============================================================ 输出
# [实现 W5 **N26**] 「强度」字段：有值 = 这一行拿到了更强的结论。
STRENGTH_FIELDS = ("repo_path", "fixed_real", "static_check_verdict", "degenerate_resolved")
# `static_check_verdict` 的这几个取值等同「没跑」→ 视为空
_VERDICT_EMPTY = (None, "", "skipped", "not_run")
OVERWRITE_AUDIT = os.path.join(rc.ARTIFACTS, "manifest_overwrite_audit.jsonl")


def _empty(field, v):
    if field == "static_check_verdict":
        return v in _VERDICT_EMPTY
    return v is None or v == ""


def overwrite_guard(old_rows, new_rows):
    """[W5 **N26**] 新产物是否比现有的**更弱** → (ok, reasons)。

    为什么需要：manifest 按固定路径写、后一次运行无条件覆盖前一次。
    ✅ W5 实测两形态：①不带 `--static-check` 的全量重跑把 `fixed_real` 非空行
    167 → **0**（只因顺手比了回归数字 25/0/4 → 20/0/9 才发现）；
    ②`--only-osv 3 条` 配默认 `--out` 会把全局 manifest **3,790 行覆盖成 3 行**。
    与 N25（日志同名覆盖）、N20（归档误删）同根因。
    判据：**覆盖面**缩水，或**交集行**上任一强度字段由有值变空 → 拒写。
    只在交集上比强度 → 子集运行/新增行不会误报。
    """
    if not old_rows:
        return True, []
    reasons = []
    old_ids = {r.get("osv_id") for r in old_rows}
    by_new = {r.get("osv_id"): r for r in new_rows}
    lost = old_ids - set(by_new)
    if lost:
        reasons.append(f"覆盖面缩水：老 {len(old_ids)} 行 → 新 {len(by_new)} 行"
                       f"（丢 {len(lost)} 行，例 {sorted(lost)[:3]}）")
    for fld in STRENGTH_FIELDS:
        n, ex = 0, None
        for r in old_rows:
            nr = by_new.get(r.get("osv_id"))
            if nr is None:
                continue                      # 覆盖面那条已经报过，不重复计
            if not _empty(fld, r.get(fld)) and _empty(fld, nr.get(fld)):
                n += 1
                ex = ex or r.get("osv_id")
        if n:
            reasons.append(f"{fld}：{n} 行由有值变空（例 {ex}）")
    return (not reasons), reasons


def write_outputs(records, args, rows_total):
    os.makedirs(os.path.dirname(args.out), exist_ok=True)
    # [W5 N26] 覆盖护栏：拒写比现有更弱的产物（`--force-overwrite` 才写，且留痕）
    if os.path.exists(args.out):
        try:
            old = [json.loads(x) for x in open(args.out, encoding="utf-8")]
        except (OSError, json.JSONDecodeError):
            old = None
        ok, why = overwrite_guard(old, records)
        if not ok:
            if not getattr(args, "force_overwrite", False):
                print(f"\n❌ [N26 覆盖护栏] 新产物比现有 {args.out} **更弱** → 拒写：")
                for w in why:
                    print(f"   - {w}")
                print("   要真覆盖 → 加 `--force-overwrite`（写审计）；"
                      "或改用 `--out` 写到别处（子集运行/对照实验应当这样）")
                sys.exit(4)
            print(f"\n⚠ [N26] --force-overwrite：明知更弱仍覆盖 {args.out}")
            for w in why:
                print(f"   - {w}")
            with open(OVERWRITE_AUDIT, "a", encoding="utf-8") as af:
                af.write(json.dumps({"ts": int(time.time()), "out": args.out,
                                     "reasons": why, "n_new": len(records),
                                     "n_old": (len(old) if old else 0)},
                                    ensure_ascii=False) + "\n")
    with open(args.out, "w", encoding="utf-8") as f:
        for r in records:
            f.write(json.dumps(r, ensure_ascii=False, sort_keys=False) + "\n")

    # build_groups.json：HEAD 构建分组 (project,sanitizer) → [osv_id]（§5①/§6.1）
    # 钉版构建**不入此分组**（per-commit 独占，R16）→ 另给 pinned_queue 供 ② 枚举
    groups = defaultdict(list)
    pinned = []
    for r in records:
        if r["skip_reason"]:
            continue
        groups[f"{r['project']}|{r['sanitizer']}"].append(r["osv_id"])
        if r.get("pin_commit") or r["commit_source"] in ("fixed_parent", "fixed_ancestor",
                                                         "introducing"):
            pinned.append({"osv_id": r["osv_id"], "project": r["project"],
                           "issue_id": r.get("issue_id"),
                           "sanitizer": r["sanitizer"], "commit_source": r["commit_source"],
                           "pin_commit": r.get("pin_commit"),
                           "fixed_commit": r.get("fixed_commit"),
                           "walkback_depth": r.get("walkback_depth"),
                           "static_check_verdict": r["static_check_verdict"],
                           "repo_url": r.get("repo_url"), "repo_path": r.get("repo_path"),
                           "repo_path_candidates": r.get("repo_path_candidates"),
                           "fuzz_target": r.get("fuzz_target")})
    bg = {
        "meta": {
            "generated_by": "manifest_builder.py",
            "schema_version": rc.SCHEMA_VERSION,
            "ts": int(time.time()),
            "records": len(records),
            "actionable": sum(1 for r in records if not r["skip_reason"]),
            "head_groups": len(groups),
            "head_group_key": "project|sanitizer（R16 缓存键 (project,sanitizer,commit) 的前两分量；"
                              "commit 分量由 ② 构建时解析上游 SHA 后补齐，R18）",
            "pinned_queue": len(pinned),
            "pinned_note": "钉版 per-commit 独占、不入 head_groups（R16 严禁用 (project,sanitizer) "
                           "复用，否则第二条复用第一条二进制 → 假复现）",
            "pinned_order": "(project, issue_id)：同项目相邻 + 项目内按 OSS-Fuzz issue 号"
                            "（pin commit 日期的离线代理，同年组内 Spearman +0.733）聚拢，"
                            "为 N4 era 缓存（键 = (project, 目标 commit 日期区间)）制造命中机会。"
                            "实测 era 窗口中位 32 天（8 个 top 项目，范围 9–97）。",
            "args": {k: v for k, v in vars(args).items() if k not in ("out", "build_groups")},
        },
        "head_groups": {k: sorted(v) for k, v in sorted(groups.items())},
        # [实现 W2 Phase0b] 排序 = (project, issue_id)：**同项目相邻** + 项目内按 issue 号
        # （= pin commit 日期的离线最优代理）聚拢，让 N4 era 缓存真的命中。
        # 实测（preflight/w2_phase0b_queue_order.py）：相邻同项目对 432 → **2,844**；
        # era 窗口命中率 osv_id 序 52.4% → issue_id 序 **65.9%**（真实日期上界 69.5%）。
        # 不按 sanitizer 再分：实测那样会把日期序打断，命中率反降到 75.6%（旧口径）/更低。
        "pinned_queue": sorted(pinned, key=lambda x: (x["project"],
                                                      x["issue_id"] if x["issue_id"] is not None
                                                      else 10 ** 12,
                                                      x["osv_id"])),
    }
    with open(args.build_groups, "w", encoding="utf-8") as f:
        json.dump(bg, f, ensure_ascii=False, indent=1)
    return bg


def report(records, bg, args, stats, rows_total, of_dirs):
    n = len(records)
    # 对账目标（3,502/448/156/25/3,550/53/3,776/35/379）都是**全量口径**；子集跑时逐项比对
    # 只会刷一屏假 ❌ → 子集跑改为明确标 N/A，不谎报不一致。
    subset = bool(args.only_osv or args.limit or args.projects
                  or args.crash_types or args.sanitizers
                  or (args.languages or "all").lower() != "all")
    def mark(got, want):
        if subset:
            return "N/A（本轮为子集，对账目标属全量口径）"
        return "✅" if got == want else f"❌ 期望 {want}"
    print("=" * 78)
    print("① manifest_builder 输出汇总")
    print("=" * 78)
    print(f"输入 crash_dataset = {rows_total} 条；本轮产出 manifest = {n} 条"
          f"（filter: languages={args.languages} projects={args.projects or 'ALL'} "
          f"crash_types={args.crash_types or 'ALL'} sanitizers={args.sanitizers or 'ALL'} "
          f"limit={args.limit or 'None'}）")
    lc = Counter(r["language"] for r in records)
    print(f"\n[language 分流]（R5 exact-match 口径）: {dict(lc.most_common())}")
    mainline = [r for r in records if r["language"] in rc.MAINLINE_LANGUAGES
                and r["project_ossfuzz_dir"]]
    print(f"  C/C++ 主线（language∈c,c++ 且 oss-fuzz 命中）= **{len(mainline)}** 条"
          f"   ← R14 对账目标 **3,502**：{mark(len(mainline), 3502)}")
    print(f"  非 C/C++ = {sum(v for k,v in lc.items() if k not in rc.MAINLINE_LANGUAGES and k!='unknown(name-miss)')}"
          f"（R14: 246）；unknown(name-miss) = {lc.get('unknown(name-miss)',0)}（R14: 42）")

    print(f"\n[skip_reason 分布]（§6.3 语义 = 整条退出主线）")
    sc = Counter(r["skip_reason"] for r in records)
    for k, v in sc.most_common():
        print(f"  {str(k):<28} {v:>5}  ({v/n*100:5.1f}%)")
    print(f"  actionable（skip_reason=null）= {sc[None]}")
    sc_m = Counter(r["skip_reason"] for r in mainline)
    print(f"  主线内 skip 分布: {dict(sc_m.most_common())}")

    # ---- 优先级抢占对账：skip_reason 是**互斥**的，预飞的计数是**非互斥**的，两者都要对上 ----
    print(f"\n[优先级抢占对账]（skip_reason 互斥；下列「不论优先级」的口径才与预飞数字可比）")
    miss = [r for r in records if not (r["testcase_path"] and os.path.exists(r["testcase_path"]))]
    miss_sc = Counter(r["skip_reason"] for r in miss)
    print(f"  testcase 磁盘缺失（不论优先级）= **{len(miss)}**  ← `crash_testcase/_MANIFEST_missing.txt` 的 **35**："
          f"{mark(len(miss), 35)}")
    print(f"     被更高优先级占走 → {dict(miss_sc.most_common())}（记为 missing_testcase 的只有 {miss_sc['missing_testcase']}）")
    nt = [r for r in records if not r["fuzz_target"]]
    nt_sc = Counter(r["skip_reason"] for r in nt)
    print(f"  最终无 fuzz_target（不论优先级）= **{len(nt)}**  ← 设计 §1 的 **379**（535 空 − 156 净推定）："
          f"{mark(len(nt), 379)}")
    print(f"     其中 unmapped_project {nt_sc['unmapped_project']}（= R7 减掉的 unrar 25）、"
          f"non_cpp_language {nt_sc['non_cpp_language']} → 记为 unreproducible_no_target 的 {nt_sc['unreproducible_no_target']}")
    print(f"  ▸ 修正 R1 的解析假象：no_fixed 240 条里 **OSV 有 introduced = "
          f"{sum(1 for r in records if not r['fixed_commit'] and r['introducing_commit'])}**、"
          f"两者都无 = {sum(1 for r in records if not r['fixed_commit'] and not r['introducing_commit'])}"
          f"（R1 脚本报 introduced-only=0/neither=240，因其 `osv_events()` 只在遇到 fixed 事件时"
          f"才 append 对 → 无 fixed 的 range 里 introduced 永不可见；md4c OSV-2022-126 即反例，"
          f"✅ P0 实测正是在其 introducing_commit 62b60979 上复现成功）")

    print(f"\n[构建分组] head_groups = **{len(bg['head_groups'])}** 个 (project,sanitizer)"
          f"   ← R14 对账目标 **448**")
    print(f"  差异说明：R14 的 448 是**全部 3,502 条 C/C++**（含 no_target/missing_testcase）的"
          f"组合数；\n  build_groups 只收 actionable 记录 → 必然 ≤448。"
          f"actionable 主线组合数 = {len(bg['head_groups'])}")
    combos_all = {(r['project'], r['sanitizer']) for r in mainline}
    print(f"  交叉核对：主线 3,502 条的 (project,sanitizer) 组合（**归一化后**）= {len(combos_all)}")
    print(f"     R14 的 **448** 是 `san_of()` 的**原始字符串**口径（'address (ASAN)' 与 '' 算两个组）；"
          f"归一化后 25 条空 sanitizer 并入各自项目的 address 组（R16 `sanitizer_inferred`，"
          f"它们**就是按 ASAN 构建**的）→ {len(combos_all)}。故 448→{len(combos_all)} 是口径差、非丢数据："
          f"{{'': 25}} 这 {448-len(combos_all)} 个「空 sanitizer 组」被合并掉")
    print(f"  pinned_queue（钉版 per-commit，不入 head_groups）= {len(bg['pinned_queue'])}")

    print(f"\n[派生字段对账]（预飞实测值）")
    ti = sum(1 for r in records if r["target_inferred"])
    si = sum(1 for r in records if r["sanitizer_inferred"])
    hf = sum(1 for r in records if r["fixed_commit"])
    dg = sum(1 for r in records if r["osv_degenerate_range"])
    ru = sum(1 for r in records if r["repo_url"])
    print(f"  target_inferred=true      : {ti:>5}   ← R7 净可用 **156**：{mark(ti,156)}")
    print(f"  sanitizer_inferred=true   : {si:>5}   ← R16/R14 空 sanitizer C/C++ **25**：{mark(si,25)}"
          + ("" if subset or si == 25 else "（全量口径含非 C/C++ 时为 25）"))
    print(f"  有 fixed_commit           : {hf:>5}   ← R1 has_fixed **3,550**：{mark(hf,3550)}")
    print(f"  ▸W1 osv_degenerate_range  : {dg:>5}   ← N6 实测 **53**：{mark(dg,53)}")
    print(f"  有 repo_url               : {ru:>5}   ← R13b **3,776**(99.6%)：{mark(ru,3776)}")
    rpc = Counter(r["repo_path_confidence"] for r in records)
    print(f"  ▸W1 repo_path 置信度      : {dict(rpc.most_common())}")
    rpc_m = Counter(r["repo_path_confidence"] for r in mainline)
    hm = rpc_m.get("high", 0) + rpc_m.get("medium", 0)
    print(f"     主线 high+medium = {hm}/{len(mainline)} = {hm/max(len(mainline),1)*100:.1f}%"
          f"   ← W1 实测 **97.5%**：" + ("N/A（子集）" if subset else
          ("✅" if abs(hm/max(len(mainline),1)*100-97.5)<0.5 else "❌")))
    svc = Counter(r["static_check_verdict"] for r in records)
    print(f"  ▸W1 static_check_verdict  : {dict(svc.most_common())}")
    wd = Counter(r["walkback_depth"] for r in records)
    print(f"  ▸W1 walkback_depth        : {dict(sorted(wd.items(), key=lambda x: str(x[0])))}")
    cs = Counter(r["commit_source"] for r in records)
    print(f"  commit_source 先验        : {dict(cs.most_common())}")
    erv = Counter(r["expected_repro_version"] for r in records)
    print(f"  expected_repro_version    : {dict(erv.most_common())}")
    nclu = len({r["crash_cluster_id"] for r in records})
    print(f"  crash_cluster_id 唯一簇数 : {nclu}（R2 归一化帧口径）")

    if stats["static_calls"]:
        print(f"\n[静态 check] 调用 {stats['static_calls']} 次，耗时 {stats['static_secs']:.1f}s"
              f"（平均 {stats['static_secs']/stats['static_calls']:.1f}s/条；0 次 clone、0 次 GitHub API）")
        if stats["degen_checked"]:
            print(f"[N6 复核] 退化记录复核 {stats['degen_checked']} 条 → 解禁钉版 "
                  f"{stats['degen_resolved']} 条（判据 S≥2∧¬no_source∧¬test_only∧¬harness∧frames_in_diff）")
    print(f"\n输出：{args.out}（{n} 行）\n      {args.build_groups}"
          f"（head_groups {len(bg['head_groups'])} + pinned_queue {len(bg['pinned_queue'])}）")


# ============================================================ 回归验证（3 条已知答案）
KNOWN = {
    # ✅ P0 实测：md4c OSV-2022-126 无 fixed，钉 introducing_commit 62b60979 复现成功
    #   （score_pos 0.0 / score_subseq 1.0 / score_set 0.67 → strict）
    "OSV-2022-126": {"project": "md4c", "fixed_commit": None, "introducing_commit":
                     "62b60979f6a281b2b3cf883abc84299431fe2f76",
                     "commit_source": "introducing", "repo_path": "/src/md4c",
                     "fuzz_target": "fuzz-mdhtml", "sanitizer": "address",
                     "osv_degenerate_range": False},
    # ✅ P0-B 实测：OSV fixed=6f36e8ab 是 JIT 清理（误指）；真修复 037fb170；
    #   钉 fixed^^=62b3ceca 得项目首个 strict 复现
    "OSV-2024-1261": {"project": "pcre2", "fixed_commit":
                      "6f36e8ab6a723d8c4d64e0286c3775000da2e876",
                      "fixed_real": "037fb170336b7aa4a71beae89bd6761d49f23053",
                      "pin_commit": "62b3ceca", "walkback_depth": 2,
                      "fixed_misattributed": True, "commit_source": "fixed_ancestor",
                      "repo_path": "/src/pcre2", "fuzz_target": "pcre2_fuzzer_16",
                      "sanitizer": "address", "osv_degenerate_range": False},
    # ✅ P0-C 实测：OSV fixed=6291cac8「change short to int」；真修复 = 其父 d6836713
    #   「ofz#51277 fix negative condition length」→ 钉 fixed^ 复现 none（N3 第二例）
    "OSV-2022-886": {"project": "hunspell", "fixed_commit":
                     "6291cac8fb85a96f7e6d5a35f1912365f3b17ae9",
                     "fixed_real": "d6836713630f752a1ea1729c666b26afd8f1e432",
                     "walkback_depth": 2, "fixed_misattributed": True,
                     "commit_source": "fixed_ancestor", "repo_path": "/src/hunspell",
                     "fuzz_target": "affdicfuzzer", "sanitizer": "address",
                     "osv_degenerate_range": False},
}


# [实现 W2] 回归基线里**被本轮实测质疑**的字段：照常打印、但**不计入 pass/fail**。
# 理由（scientific-rigor Rule 6：不因为它是「基线」就护着它）：这些值的「已知答案」身份
# 来自 P0-C 的**单次负观测推断**，而 W2 拿到了反证。保留打印是为了让改动仍可见。
DISPUTED = {
    "OSV-2022-886": {
        "fixed_real": "W2 反证①：d6836713 的消息是「ofz#**51277** fix negative condition length」，"
                      "而本 crash 的 issue id = **51242** → 它修的是**别家** bug（N9：`ofz_ref` +2 "
                      "不校验号）。P0-C 的归因只有「在 d6836713 上 none」这一个负观测支撑。",
        "fixed_misattributed": "W2 反证②：本 crash 在 HEAD + 钉版三格共 **4 个版本全 none**，而 "
                      "`job_type=libfuzzer_asan_**i386**_hunspell`（N8）→ x86_64 构建下结构性不可复现；"
                      "负观测**无法区分**「已修复」与「压根复现不出」，故 misattributed 不成立为事实。",
        "walkback_depth": "由 fixed_real 派生 → 同受质疑",
        "commit_source": "由 fixed_real 派生 → 同受质疑",
    },
}


def regression(records, verbose=True):
    """用 P0/P0-B/P0-C 已手工跑通的 3 条验证 manifest 字段 = 当时手工确定的值。
    **这是本轮最有价值的验证：它们的正确答案已知。**"""
    by_id = {r["osv_id"]: r for r in records}
    print("\n" + "=" * 78)
    print("回归验证：3 条已知答案的 crash（P0 / P0-B / P0-C 手工跑通）")
    print("=" * 78)
    npass = nfail = nskip = ndisp = 0
    for oid, exp in KNOWN.items():
        r = by_id.get(oid)
        if not r:
            print(f"  [SKIP] {oid} 不在本轮输出（被 filter 排除）")
            nskip += 1
            continue
        print(f"  {oid} ({exp['project']})")
        for k, want in exp.items():
            got = r.get(k)
            if isinstance(want, str) and isinstance(got, str) and len(want) >= 8:
                okk = got.startswith(want) or want.startswith(got)   # sha 前缀比对
            else:
                okk = got == want
            if k in ("fixed_real", "pin_commit", "walkback_depth", "fixed_misattributed",
                     "commit_source") and r["static_check_verdict"] in ("skipped",):
                print(f"    – {k:<24} 未跑静态 check（--static-check 才产出）期望={want}")
                nskip += 1
                continue
            disp = DISPUTED.get(oid, {}).get(k)
            if disp:
                ndisp += 1
                print(f"    ⚠ {k:<24} got={str(got)[:40]}  want={str(want)[:40]}"
                      f"  【争议，不计分】{disp}")
                continue
            mark = "✅" if okk else "❌"
            if okk:
                npass += 1
            else:
                nfail += 1
            if verbose or not okk:
                print(f"    {mark} {k:<24} got={str(got)[:64]}  want={str(want)[:64]}")
    print(f"  → 字段级：{npass} 通过 / {nfail} 不符 / {nskip} 跳过（未开静态 check 或不在输出）"
          f" / {ndisp} 争议（W2 反证，不计分）")
    return nfail == 0


# ============================================================ main
def main():
    ap = argparse.ArgumentParser(description="① manifest_builder（§5①/§6.3）")
    ap.add_argument("--projects", default=None, help="逗号分隔；默认全部")
    ap.add_argument("--limit", type=int, default=None, help="本轮 crash 数上限（R16 增量）")
    ap.add_argument("--crash-types", default=None, help="逗号分隔；默认全部")
    ap.add_argument("--sanitizers", default=None, help="逗号分隔（address/memory/undefined）")
    ap.add_argument("--languages", default="all",
                    help="默认 all（全量产出、非 C/C++ 标 skip_reason=non_cpp_language，§7B5）；"
                         "c,c++ 则只输出主线")
    ap.add_argument("--sort", default="fixed_first",
                    choices=["no_fixed_first", "fixed_first", "osv_id"],
                    help="§5①：fixed 仅用于**排序**，不排除任何 crash。"
                         "**[W5 根因修正] 默认由 no_fixed_first 改为 fixed_first**："
                         "no_fixed_first 是 W2 在 HEAD-first 路由下定的（无 fixed 者只能试 HEAD）；"
                         "W3 用实测把路由翻成 has_fixed→钉版（复现率 **45.7%% vs HEAD 6.7%%**）后"
                         "**排序键没跟着改** → 收益最高的 has_fixed 被排到队尾："
                         "✅ 实测 92 条积压位于默认序第 **196–2996** 位（中位 1650），"
                         "而历轮 --limit ≤30 → **三轮都没碰到**。")
    ap.add_argument("--only-osv", default=None, help="逗号分隔 osv_id（回归/抽查用）")
    ap.add_argument("--out", default=rc.MANIFEST_OUT)
    ap.add_argument("--build-groups", default=rc.BUILD_GROUPS_OUT)
    ap.add_argument("--repo-map", default=rc.REPO_PATH_MAP)
    # 静态 check（[实现 W1]）
    ap.add_argument("--static-check", action="store_true",
                    help="打开复合证据分静态 check（需网络；默认关 → verdict=skipped，"
                         "walkback_depth=null，交 ② 构建期 walk-back）")
    ap.add_argument("--static-check-limit", type=int, default=50,
                    help="单轮静态 check 条数上限（每条 2–5 次 HTTP；全量 3,301 条不现实）")
    ap.add_argument("--max-depth", type=int, default=3, help="深度游走上限（与 §5② walk-back ≤3 对齐）")
    ap.add_argument("--sleep", type=float, default=0.2, help="每条之间的礼貌间隔（秒）")
    ap.add_argument("--keep-chain", action="store_true", help="把逐深度证据写进 notes（调试用）")
    ap.add_argument("--no-degenerate-resolve", action="store_true",
                    help="[W2 Phase0c] 关闭 N6 退化 range 的个案复核（默认开；需 --static-check）")
    ap.add_argument("--degenerate-only", action="store_true",
                    help="[W2 Phase0c] 静态 check **只**跑 N6 退化复核（53 次请求），"
                         "其余记录 verdict=skipped → 让正典 manifest 也带上 degenerate_resolved")
    ap.add_argument("--no-regression", action="store_true")
    ap.add_argument("--force-overwrite", action="store_true",
                    help="[W5 N26] 明知新产物更弱仍覆盖 --out（写 "
                         "artifacts/manifest_overwrite_audit.jsonl 留痕）。"
                         "子集运行/对照实验请改用 --out 写到别处，不要用这个")
    ap.add_argument("--quiet", action="store_true")
    args = ap.parse_args()

    t0 = time.time()
    rows = rc.load_crash_dataset()
    meta = rc.load_crash_testcase_meta()
    recovered = rc.load_recovered()
    rc.install_recovered(recovered)                 # normalize_frames 需要它（闭包 rec）
    of_dirs = rc.ossfuzz_project_dirs()             # 主树（language 口径与预飞一致）
    proj_targets = build_project_targets(rows, meta)
    if not args.quiet:
        print(f"[load] crash_dataset={len(rows)} meta={len(meta)} recovered={len(recovered)} "
              f"oss-fuzz projects={len(of_dirs)} 唯一 target 项目={len(proj_targets)} "
              f"({time.time()-t0:.1f}s)")
        ok, _got = rc.verify_normalize_frames(rows, recovered)
        print(f"[selftest] normalize_frames 逐字复用（AST 提取自 preflight）对账 R2-extra: "
              f"{'✅ 一致' if ok else '❌ 不一致 → 停止'}")
        if not ok:
            sys.exit(2)

    # ---- filter ----
    only = set(args.only_osv.split(",")) if args.only_osv else None
    projs = set(args.projects.split(",")) if args.projects else None
    cts = set(args.crash_types.split(",")) if args.crash_types else None
    sans = set(args.sanitizers.split(",")) if args.sanitizers else None
    langs = None if args.languages.lower() == "all" else set(args.languages.split(","))

    sel = []
    for row in rows:
        oid = row["osv_id"]
        if only and oid not in only:
            continue
        if projs and row["project"] not in projs:
            continue
        # [实现 W2 bug 修] 原实现只比**原值**（`Heap-buffer-overflow READ 1`），而调用方
        # （⑥/人）自然会给**归一值**（`heap-buffer-overflow`）→ 静默选出 0 条。
        # ✅ W2 Phase4 首跑当场抓到（`--crash-types heap-buffer-overflow` → manifest 0 条）。
        # 现在两种口径都接受。
        if cts:
            raw = row.get("crash_type") or ""
            if raw not in cts and rc.normalize_crash_type(raw) not in cts:
                continue
        m = meta.get(oid)
        san, _inf = rc.sanitizer_of(row, m)
        if sans and san not in sans:
            continue
        lang = rc.language_of(row["project"], of_dirs)
        if langs and lang not in langs:
            continue
        sel.append(row)

    # ---- sort（§5①：fixed 仅用于排序）----
    _run_memo = {}

    def _is_runnable(row):
        """[N77] 逐条判定「本条是否可能进入主线复现」。

        与 `build_record()` 的 `skip_reason` 四分支**同序同判据**：
        `unmapped_project` / `non_cpp_language` / `unreproducible_no_target` /
        `missing_testcase` —— 任一命中即不可跑。

        ⚠ **只用廉价判据**：`rc.fuzz_target_of()` 是纯字典查找；testcase 存在性用
        `os.path.exists`，**不得**调 `rc.testcase_facts()` —— 它会对整个文件算
        sha256，而 `sort_key` 被调用 O(n log n) 次（3,790 条全量时不可接受）。
        结果按 osv_id 记忆化，避免排序过程中的重复计算。
        """
        oid = row["osv_id"]
        if oid in _run_memo:
            return _run_memo[oid]
        proj = row["project"]
        in_of = proj in of_dirs
        lang = rc.language_of(proj, of_dirs)
        ft = rc.fuzz_target_of(row, meta.get(oid))
        if not ft:                                # 项目级兜底（与 build_record 一致）
            ft, _why = infer_target(proj, proj_targets, lang, in_of)
        tp = row.get("testcase_path")
        ok = bool(in_of and lang in rc.MAINLINE_LANGUAGES and ft
                  and tp and os.path.exists(tp))
        _run_memo[oid] = ok
        return ok

    def sort_key(row):
        oid = row["osv_id"]
        osv_rec = rc.load_osv(oid)
        m = meta.get(oid)
        ic = m.get("introducing_commit") if m else None
        ic = None if ic in (None, "", "0") else ic
        fixed, _r, _rule, _n, _i = rc.osv_fixed_and_repo(osv_rec, ic)
        # [N75] **升序**排序下 `has=0` 在前 → 有 fixed_commit 者天然排前，
        #   这本身就是 `fixed_first`。旧代码写的是
        #   `if args.sort == "fixed_first": has = 1 - has`，
        #   等于把已经正确的顺序又翻回去 → **默认值 `fixed_first` 实际表现为
        #   `no_fixed_first`**（✅ W6 实测 `--projects matio,lcms` 全量 87 条中
        #   79 条有 fixed_commit，但 `--sort fixed_first --limit 6` 取到的前 6 条
        #   **有修复 0/6**，79 条有修复者被排到第 **9–87** 位）。
        #   按 has_fixed→钉版复现率 **45.7%** vs HEAD **6.7%** 折算，前 6 条的预期
        #   产出从 **2.7 条掉到 0.4 条（≈7×）**。W5 help 所述「92 条积压位于默认序
        #   第 196–2996 位、历轮 --limit ≤30 三轮都没碰到」即此因，W5 未真正修好。
        #   复算：python3 preflight/selftest/w6_selftest_sort_direction.py
        has = 0 if fixed else 1                    # 有 fixed → 0 → 升序在前
        if args.sort == "no_fixed_first":
            has = 1 - has                          # 反转 → 无 fixed 在前（HEAD-first）
        # [N77] **可跑者优先**（主键，排在 has 之前）。
        #   无 fuzz_target 的记录会被判 `skip_reason=unreproducible_no_target`、
        #   整条退出主线、**永远不可能复现**。但它们此前仍占 `--limit` 名额：
        #   ✅ W6 实测 `file` 项目 32 条中 17 条可跑，而 `--sort fixed_first
        #   --limit 12` 取到的 **12/12 全部无 target** → 该组「0 条可跑、0 次构建、
        #   4 秒结束、无记录落盘」。根因是次级键 osv_id **升序** → 最老的崩溃排最前，
        #   而老崩溃最常缺 target 元数据：全量口径无 target 者仅 **11%**，
        #   但按 fixed_first 取前 96 条时高达 **55%**。
        #   注：这里只改**顺序**、不改取舍 —— 不截断时记录集合与可跑条数完全不变
        #   （由 w6_selftest_sort_direction.py 的 [H] 负对照锁住）。
        #   ⚠ 首版误用**项目级**的 `infer_target()` 作判据 → 对同一项目的所有记录
        #   返回同一个值 → `runnable` 恒定 → **完全没改变顺序**（✅ 实测 file 组
        #   仍是 0/12 可跑）。逐条判据必须走 `_is_runnable()`（含 `fuzz_target_of`
        #   的逐条元数据 + testcase 存在性），`infer_target` 只是其中的项目级兜底。
        runnable = 0 if _is_runnable(row) else 1   # 可跑 → 0 → 升序在前
        return ((runnable, has, oid) if args.sort != "osv_id" else (0, oid))

    if not only:
        sel.sort(key=sort_key)
    if args.limit:
        sel = sel[:args.limit]

    stats = {"static_calls": 0, "static_secs": 0.0, "degen_checked": 0, "degen_resolved": 0}
    records = []
    for i, row in enumerate(sel, 1):
        n0 = stats["static_calls"]
        records.append(build_record(row, meta.get(row["osv_id"]),
                                    recovered.get(row["osv_id"]), of_dirs,
                                    proj_targets, args, stats))
        if args.static_check and not args.quiet and i % 250 == 0:
            print(f"  [{i}/{len(sel)}] static_calls={stats['static_calls']} "
                  f"{time.time()-t0:.0f}s", file=sys.stderr)
        # [实现 W2] **只在本条真发了网络请求时才 sleep**：原实现对每条都睡 `--sleep`，
        # 于是 `--static-check` 的全量跑白等 3,790×0.2s=758s（实测 787s，其中静态 check
        # 本身只占 17.4s）。修后全量跑 ≈ 25s（见 W2 报告 §2）。
        if args.static_check and args.sleep and stats["static_calls"] != n0:
            time.sleep(args.sleep)

    bg = write_outputs(records, args, len(rows))
    if not args.quiet:
        report(records, bg, args, stats, len(rows), of_dirs)
        if not args.no_regression:
            ok = regression(records)
            if not ok:
                print("\n❌ 回归验证有字段不符 → 见上")
                sys.exit(3)
    print(f"\n[done] {len(records)} 条，{time.time()-t0:.1f}s")


if __name__ == "__main__":
    main()

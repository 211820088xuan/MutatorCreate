#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""④ `verify_tiered.py` — Tiered 验证分级（DELIVERY §1.3④）。

判定规则（**现行**版本，P0-B 后定稿）
----------------------------------
设 R = recovered top-3（ground truth，归一化后）、O = observed **完整**归一化栈（**不截断**）：

| 量 | 定义 | 用途 |
|---|---|---|
| `score_pos` | `Σ[R[i]==O[i]] / |R|` | 最严；跨版本脆弱（✅ P0：md4c 顶部多一帧 → 0/3） |
| **`score_subseq`** | R 是否为 O 的**有序子序列** → 1.0/0.0 | **strict 用此** |
| `score_set` | `|R∩O| / |R|` | 最松 |

* `strict`  = `score_subseq ≥ T_strict`（当前 **1.0**）**且** crash_type 归一一致
* `medium`  = crash_type 一致但帧不齐
* `loose`   = 崩了但 crash_type 不一致
* `none`    = 没崩

**归一化不重写**：R 用 ⓪ `normalize_frames(osv_id)`（AST 逐字提取自
`preflight/r2_r5_r6_r7_recompute.py`，以 R2-extra 10 项计数对账）；O 用 ⓪
`normalize_observed()`（逐帧同一份 `normalize_one_frame` + observed 独有的 `main`/模块帧过滤）。

**off-by-one 两型，步骤 1 与步骤 3 各治一型、缺一不可**（✅ P0/P0-B）：
① 拦截器帧假象（pcre2 raw DEDUP_TOKEN 顶帧 `__asan_memmove`，剔内部帧后即对齐，`score_pos` 0→1.0）；
② 真实项目帧移位（md4c 顶部多一个**项目函数** `md_resolve_links`，剔内部帧后仍 `score_pos=0`，
   须靠子序列规则保 strict）。

⚠ **`T_strict=1.0` 目前无区分力**：两个标定点 `score_subseq` 都是 1.0 → 取 0.5 还是 1.0 结果相同
= **未被证伪、不是被验证**。要判它是否过严，需要「确实复现但帧对不齐（subseq<1.0）」的样本。
→ **保持 1.0，每条存三量原值备日后重标定**（Phase 5(b) 就是找这个样本）。

<3 帧降级（§1.3④ 步骤 6）：R 为 0 帧（20 条）→ strict 不可用，降 medium/loose；
1–2 帧（192 条）→ 按实际帧数比。
"""
from __future__ import annotations

import argparse
import collections
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import repro_common as rc  # noqa: E402

VERIFICATIONS = os.path.join(rc.ARTIFACTS, "verifications.jsonl")
T_STRICT_DEFAULT = 1.0


def log(*a):
    print(*a, file=sys.stderr, flush=True)


def is_subsequence(r, o):
    """R 是否为 O 的**有序子序列**（元素可重复，按出现顺序消耗）。"""
    it = iter(o)
    return all(any(x == y for y in it) for x in r)


def lcs_len(a, b):
    """最长**公共子序列**长度（DP；|a|≤3、|b|≤几十 → 开销可忽略）。"""
    if not a or not b:
        return 0
    prev = [0] * (len(b) + 1)
    for x in a:
        cur = [0]
        for j, y in enumerate(b, 1):
            cur.append(prev[j - 1] + 1 if x == y else max(prev[j], cur[j - 1]))
        prev = cur
    return prev[-1]


def _set_score(R, O):
    """集合分：按**重数**取交（避免同名帧重复计数虚高）/ |R|。"""
    cnt = collections.Counter(O)
    inter = sum(min(cnt[x], n) for x, n in collections.Counter(R).items())
    return round(inter / len(R), 4)


def score_three(R, O):
    """→ (score_pos, score_subseq, score_set, score_set_top3)。|R|=0 时全为 None。

    **[实现 W2] 两个集合分并存**（DELIVERY 自身有一处规格/实测不一致，不静默选边）：
      * `score_set`      = 对 **observed 完整归一化栈**（§1.3④ 表头明写 O=完整栈）
      * `score_set_top3` = 对 **observed top-3**（= ✅ P0 报告 :194 记的「集合 2/3」口径，
        也是 §1.3④ 标定点「md4c … set 0.67」唯一能复现的口径）
    → 用完整栈时 `subseq=1.0 ⟹ set=1.0`（子序列必含于集合），故 `score_set` 只在
      「帧都在但顺序不对」时提供额外信息；`score_set_top3` 才与已发布标定点可比。
    """
    if not R:
        return None, None, None, None, None
    pos = round(sum(1 for i in range(min(len(R), len(O))) if R[i] == O[i]) / len(R), 4)
    sub = 1.0 if is_subsequence(R, O) else 0.0
    # [实现 W2] **score_subseq 是二值的**（子序列要么全中要么不中）→ 任何 T_strict∈(0,1]
    # 给出**完全相同**的分级，阈值在结构上就是空的（✅ W2 实测：7 条 libtsm 样本
    # crash_type 一致但 subseq=0.0，把阈值降到 0.5 一条也不会变 strict）。
    # 故另存**分数化**版本 `score_subseq_frac = LCS(R,O)/|R|`，让阈值真有刻度；
    # 不改 `score_subseq` 本身（两个标定点 md4c/pcre2 的 1.0 与已发布结论保持不变）。
    subfrac = round(lcs_len(R, O) / len(R), 4)
    return pos, sub, _set_score(R, O), _set_score(R, list(O)[:3]), subfrac


def verify_one(obs, t_strict, topk):
    """单条 → verification 记录。"""
    oid = obs["osv_id"]
    R = list(rc.normalize_frames(oid, topk=topk))
    O = rc.normalize_observed(obs.get("observed_frames") or [])
    repro = bool(obs.get("reproduced_any"))
    exp_norm = (obs.get("crash_type_norm_expected") or "").strip()
    got_norm = (obs.get("observed_crash_type_norm") or "").strip()
    ct_match = bool(exp_norm and got_norm and exp_norm == got_norm)

    # **[N46 防线②] 资源上限诊断不是复现** —— 即使旧 observation 里 `reproduced_any=True`
    # （⑥ 修复前落的账），只要实测类型是 timeout/OOM 就判 none。放在分级之前，
    # 于是**重跑 ④⑤ 即可纠正历史数据**，不必手改 append-only 复现记录表。
    # ⚠ 只在「没有 sanitizer 报告」时翻转：真崩溃顺带超时不算。
    _raw = str(obs.get("observed_crash_type_raw") or "")
    # ⚠ **[W7 修 N67] 原来用 `"sanitizer" not in _raw.lower()` 判「有没有真报告」，
    #   但 espeak-ng 的报告里有 `DEDUP_TOKEN: __sanitizer_print_stack_trace--…` —— **含
    #   "sanitizer" 子串** → 防线**不触发**，4 条 exit=77 的假复现被记成 tier=loose。
    #   改为匹配**真正的 sanitizer 报告特征**（`ERROR: AddressSanitizer:` 等），
    #   `ERROR: libFuzzer: …` / `SUMMARY: libFuzzer: …` / DEDUP_TOKEN 都不算。
    non_crash = (bool(repro) and got_norm.lower() in rc.NON_CRASH_DIAGNOSTICS
                 and not RE_SAN_REPORT.search(_raw))
    if non_crash:
        repro = False

    pos, sub, st, st3, subfrac = score_three(R, O)
    rec = {
        "osv_id": oid, "project": obs.get("project"), "sanitizer": obs.get("sanitizer"),
        "reproduced_any": repro,
        "non_crash_diagnostic": non_crash,
        "crash_type_match": ct_match,
        "crash_type_expected_norm": exp_norm, "crash_type_observed_norm": got_norm,
        "frame_match_score": sub,                 # §1.3④：记 score_subseq
        "score_pos": pos, "score_subseq": sub, "score_set": st, "score_set_top3": st3,
        "score_subseq_frac": subfrac,
        "frames_aligned": bool(sub is not None and sub >= t_strict),
        "n_recovered_frames": len(R), "n_observed_frames": len(O),
        "recovered_norm": R, "observed_norm": O[:40],
        "dedup_token": obs.get("dedup_token"),
        "binary_dir": obs.get("binary_dir"), "pinned_commit": obs.get("pinned_commit"),
        "commit_source": obs.get("commit_source"),
        "walkback_depth_actual": obs.get("walkback_depth_actual"),
        "t_strict": t_strict,
    }
    # ---- 分级 ----
    if not repro:
        rec["verification_tier"] = "none"
        rec["tier_why"] = (
            f"**[N46] 实测是 libFuzzer 资源上限诊断（`{got_norm}`），不是所报漏洞的崩溃** → 判 none"
            if non_crash else "reproduced_any=false（没崩）")
    elif not R:
        # §1.3④ 步骤 6：recovered 0 帧（全量 20 条）→ strict 不可用
        rec["verification_tier"] = "medium" if ct_match else "loose"
        rec["tier_why"] = f"recovered 0 帧 → strict 不可用，按 crash_type 降档（match={ct_match}）"
    elif sub is not None and sub >= t_strict and ct_match:
        rec["verification_tier"] = "strict"
        rec["tier_why"] = f"score_subseq={sub} ≥ T_strict={t_strict} 且 crash_type 一致"
    elif ct_match:
        rec["verification_tier"] = "medium"
        rec["tier_why"] = (f"crash_type 一致但帧不齐（score_subseq={sub} < {t_strict}，"
                           f"score_pos={pos}，score_set={st}，set_top3={st3}）")
    else:
        rec["verification_tier"] = "loose"
        rec["tier_why"] = (f"崩了但 crash_type 不一致（期望 {exp_norm or '-'} vs 实测 "
                           f"{got_norm or '-'}；score_subseq={sub}）")
    rec["details"] = {"R": R, "O_len": len(O), "O_head": O[:6],
                      "scores": {"pos": pos, "subseq": sub, "set": st, "set_top3": st3,
                                 "subseq_frac": subfrac},
                      "degraded_no_recovered_frames": not R,
                      "n_recovered_lt3": 0 < len(R) < 3}
    return rec


# **[N67] 真 sanitizer 报告的特征**（用于「资源上限/自行退出」防线的例外判断）。
# ⚠ 不能用 `"sanitizer" in raw` 这种子串判断：`DEDUP_TOKEN: __sanitizer_print_stack_trace--…`
#   会让它误判成"有报告"（✅ 实测 espeak-ng 4 条正中此坑）。
RE_SAN_REPORT = re.compile(
    r"(?:ERROR|WARNING):\s*(?:Address|Memory|Thread|Undefined)Sanitizer"
    r"|SUMMARY:\s*(?:Address|Memory|Thread)Sanitizer"
    r"|runtime error:", re.I)


def selftest():
    """三量 + LCS 的已知答案自测（P0/P0-B 标定点 + W2 libtsm 实测形态）。"""
    cases = [
        # (R, O, pos, subseq, set, set_top3, subseq_frac, 说明)
        (["a", "b", "c"], ["x", "a", "b", "c", "y"], 0.0, 1.0, 1.0, 0.6667, 1.0,
         "✅ P0 md4c 形态：顶部多一帧 → pos=0 但子序列全中；set_top3=2/3（O[:3] 少一帧）"),
        (["a", "b", "c"], ["a", "b", "c", "d"], 1.0, 1.0, 1.0, 1.0, 1.0,
         "✅ P0-B pcre2 形态：完全对齐"),
        (["a", "b", "c"], ["a", "z"], 0.3333, 0.0, 0.3333, 0.3333, 0.3333,
         "✅ W2 libtsm 形态：只顶帧对上 → subseq=0 而 frac=1/3（阈值这才有刻度）"),
        ([], ["a"], None, None, None, None, None, "recovered 0 帧 → 三量不可用"),
    ]
    bad = 0
    for R, O, p_, sb, st, st3, sf, note in cases:
        got = score_three(R, O)
        want = (p_, sb, st, st3, sf)
        ok = all((g is None and w is None) or (g is not None and w is not None
                                              and abs(g - w) < 1e-3)
                 for g, w in zip(got, want))
        bad += 0 if ok else 1
        print(f"  {'✅' if ok else '❌'} {note}")
        print(f"      got={got} want={want}")
    print(f"  → {len(cases)-bad}/{len(cases)} 通过")

    # **[N46] `verify_one` 的资源上限防线**。
    # ⚠ 必须用**真实 osv_id**：`rc.normalize_frames` 走的是恢复帧缓存（AST 逐字复用 preflight 的
    #   权威实现），传合成 id 会在 `r2_r5_r6_r7_recompute.py` 里 NameError（✅ 本轮实测撞到）。
    #   这里 `observed_frames=[]` → O 为空 → `score_subseq=0.0`，于是分级只由 `repro` 与
    #   `ct_match` 决定，正好隔离出要测的那道防线。
    print("\n[N46] verify_one：libFuzzer timeout/OOM 不得算复现")
    rc.install_recovered(rc.load_recovered())   # ← normalize_frames 的闭包依赖（main 里也这么做）
    _oid = "OSV-2025-796"          # 有 3 个恢复帧（AddGreenToBlueAndRed_AVX2 等）
    _cases = [
        # (observed_crash_type_norm, observed_crash_type_raw, 期望 tier, 期望 non_crash, 说明)
        ("timeout", "==7== ERROR: libFuzzer: timeout after 25 seconds", "none", True,
         "纯超时、无 sanitizer 报告 → **判 none**（✅ 真实受害者 OSV-2023-1206）"),
        ("out-of-memory", "==7== ERROR: libFuzzer: out-of-memory", "none", True,
         "OOM 同属资源上限 → 判 none"),
        # **[W7 N67]** 真实受害者：espeak-ng 4 条曾被记成 tier=loose，报告原文如下
        # （根因是归档缺 `espeak-ng-data/` → 目标初始化失败 exit(77)，见 build_orchestrator N66）
        ("fuzz-target-exited",
         "Error processing file '/out/phontab': No such file or directory.\n"
         "==7== ERROR: libFuzzer: fuzz target exited\n"
         "DEDUP_TOKEN: __sanitizer_print_stack_trace--fuzzer::PrintStackTrace()"
         "--fuzzer::Fuzzer::ExitCallback()\nSUMMARY: libFuzzer: fuzz target exited",
         "none", True,
         "**[N67] 目标自行 exit(77)、无 sanitizer 段 → 判 none**（✅ 真实受害者 espeak-ng 4 条）"),
        ("fuzz-target-exited",
         "ERROR: AddressSanitizer: heap-buffer-overflow …\n"
         "==7== ERROR: libFuzzer: fuzz target exited",
         "loose", False,
         "**反向对照**：若同时有真 ASan 报告（raw 含 `sanitizer`）→ 防线不得触发"),
        ("timeout", "ERROR: AddressSanitizer: heap-buffer-overflow …\nSUMMARY: libFuzzer: timeout",
         "loose", False,
         "**反向对照**：同时有真 ASan 报告 → 防线不得触发（crash_type 不一致 → loose）"),
        ("heap-buffer-overflow", "ERROR: AddressSanitizer: heap-buffer-overflow", "medium", False,
         "普通崩溃且 crash_type 一致、但 O 为空帧不齐（subseq=0.0）→ medium，不受防线影响"),
    ]
    for _n, _raw, _wt, _wn, _note in _cases:
        _o = {"osv_id": _oid, "project": "libwebp", "sanitizer": "address",
              "reproduced_any": True, "observed_frames": [],
              "crash_type_norm_expected": "heap-buffer-overflow",
              "observed_crash_type_norm": _n, "observed_crash_type_raw": _raw}
        _r = verify_one(_o, 1.0, 10)
        _ok = _r["verification_tier"] == _wt and bool(_r.get("non_crash_diagnostic")) == _wn
        bad += 0 if _ok else 1
        print(f"  {'✅' if _ok else '❌'} {_note}")
        print(f"      got tier={_r['verification_tier']!r} non_crash={_r.get('non_crash_diagnostic')}"
              f" R={_r['n_recovered_frames']}帧 subseq={_r['score_subseq']}"
              f"  want tier={_wt!r} non_crash={_wn}")
    print(f"  → {len(cases)+len(_cases)-bad}/{len(cases)+len(_cases)} 通过")

    # **[N39] C++ 参数签名剥离**（已知答案全部取自复现记录表里的**真实** observed 帧）
    # 为什么要有这组：observed 是 ASan/MSan 的符号化输出（带参数类型），recovered 是
    # ClusterFuzz 的 DEDUP_TOKEN（只有函数名）→ 不剥签名则逐字比对必然失败，
    # ✅ 实测 17 条 hunspell 因此只能拿 `score_subseq=0.0` → 被压在 medium。
    print("\n[N39] strip_cpp_signature：observed 侧剥 C++ 参数签名")
    _n39 = [
        ("AffixMgr::cpdcase_check(std::__1::basic_string<char, std::__1::allocator<char>> const&, "
         "char const*) const", "AffixMgr::cpdcase_check", "真实帧：模板参数 + 尾缀 const"),
        ("HunspellImpl::spell_internal(std::__1::basic_string<char, std::__1::allocator<char>> const&)",
         "HunspellImpl::spell_internal", "真实帧：嵌套模板"),
        ("SfxEntry::test_condition(char const*, char const*)", "SfxEntry::test_condition",
         "真实帧：多指针参数"),
        ("fuzzer::Fuzzer::ExecuteCallback(unsigned char const*, unsigned long)",
         "fuzzer::Fuzzer::ExecuteCallback", "引擎帧（后续仍会被 INTERNAL_PREFIXES 剔掉）"),
        ("ihevce_enc_frm_proc_slave_thrd", "ihevce_enc_frm_proc_slave_thrd", "**C 帧不受影响**"),
        ("AddGreenToBlueAndRed_AVX2", "AddGreenToBlueAndRed_AVX2", "无签名 → 原样"),
        ("A::operator()", "A::operator", "`operator()` 的括号是函数名本身，不能当签名剥"),
        ("A::operator()(int)", "A::operator", "operator 后再接参数列表"),
        ("foo<int>::bar(int)", "foo<int>::bar", "**模板实参里的尖括号不受影响**"),
    ]
    for _src, _want, _note in _n39:
        _got = rc.strip_cpp_signature(_src)
        _ok = _got == _want
        bad += 0 if _ok else 1
        print(f"  {'✅' if _ok else '❌'} {_note}")
        print(f"      got={_got!r} want={_want!r}")
    # 端到端：复现记录表里那条真实的 hunspell medium，剥签名后必须升到 strict
    _oid = "OSV-2022-1260"
    _R = list(rc.normalize_frames(_oid, topk=10))
    _O = rc.normalize_observed([
        "AffixMgr::cpdcase_check(std::__1::basic_string<char, std::__1::allocator<char>> const&, "
        "char const*) const",
        "AffixMgr::compound_check(std::__1::basic_string<char, std::__1::allocator<char>> const&, "
        "int, char const*, char const*, char const*, char const*, int, int, int)",
        "HunspellImpl::checkword(std::__1::basic_string<char, std::__1::allocator<char>> const&, "
        "int, char const*, int, int*, int*)"])
    _p, _sb, _st, _st3, _sf = score_three(_R, _O)
    _ok = (_sb == 1.0 and _p == 1.0)
    bad += 0 if _ok else 1
    print(f"  {'✅' if _ok else '❌'} 端到端：{_oid} 的 R 必须是 O 的子序列（score_subseq=1.0 → strict）")
    print(f"      R={_R}")
    print(f"      O={_O}")
    print(f"      score_pos={_p} score_subseq={_sb}（旧值都是 0.0 → 只能判 medium）")
    _tot = len(cases) + len(_cases) + len(_n39) + 1
    print(f"  → {_tot-bad}/{_tot} 通过")
    return bad == 0


def main():
    ap = argparse.ArgumentParser(description="④ Tiered 验证分级（DELIVERY §1.3④）")
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--observations", default=os.path.join(rc.ARTIFACTS, "observations.jsonl"))
    ap.add_argument("--out", default=VERIFICATIONS)
    ap.add_argument("--t-strict", type=float, default=T_STRICT_DEFAULT)
    ap.add_argument("--recovered-topk", type=int, default=3, help="ClusterFuzz dedup_token_length=3")
    ap.add_argument("--only-osv", default=None)
    ap.add_argument("--latest-only", action=argparse.BooleanOptionalAction, default=True,
                    help="同 osv_id 多条 observation 只取最后一条（默认开；--no-latest-only 全评）")
    a = ap.parse_args()

    print("=" * 78); print("④ 打分器自测（已知答案）"); print("=" * 78)
    if not selftest():
        return 3
    if a.selftest:
        return 0
    rc.install_recovered(rc.load_recovered())      # normalize_frames 的闭包依赖
    rows = rc.load_crash_dataset()
    recovered = rc.load_recovered()
    ok, _got = rc.verify_normalize_frames(rows, recovered)
    log(f"[selftest] normalize_frames 对账 R2-extra: {'✅ 一致' if ok else '❌ 不一致 → 停止'}")
    if not ok:
        return 3

    obs = [json.loads(l) for l in open(a.observations, encoding="utf-8")]     # noqa: E741
    if a.only_osv:
        want = set(x.strip() for x in a.only_osv.split(",") if x.strip())
        obs = [o for o in obs if o["osv_id"] in want]
    if a.latest_only:
        latest = {}
        for o in obs:
            latest[o["osv_id"]] = o          # 文件顺序 = 时间顺序，后者覆盖前者
        obs = list(latest.values())
    log(f"[④ 范围] {len(obs)} 条 observation；T_strict={a.t_strict}；recovered topk={a.recovered_topk}")

    os.makedirs(os.path.dirname(a.out), exist_ok=True)
    tiers = collections.Counter()
    subs = collections.Counter()
    n_degraded = 0
    with open(a.out, "w", encoding="utf-8") as f:
        for o in obs:
            v = verify_one(o, a.t_strict, a.recovered_topk)
            f.write(json.dumps(v, ensure_ascii=False) + "\n")
            tiers[v["verification_tier"]] += 1
            subs[str(v["score_subseq"])] += 1
            if v["details"]["degraded_no_recovered_frames"]:
                n_degraded += 1
    log(f"\n[④ 汇总] tier 分布 {dict(tiers)}")
    log(f"  score_subseq 分布 {dict(subs)}")
    log(f"  recovered 0 帧降级 {n_degraded} 条")
    # Phase 5(b)：T_strict 有没有区分力 = 是否存在「复现了、crash_type 一致、但 subseq<1.0」的样本
    vs = _last(a.out) or []
    discrim = [v for v in vs if v["reproduced_any"] and v["crash_type_match"]
               and v["score_subseq"] is not None and v["score_subseq"] < 1.0]
    log(f"  ⚠ T_strict 区分力：「复现 ∧ crash_type 一致 ∧ score_subseq<1.0」的样本 = {len(discrim)} 条"
        + (f"（{[v['osv_id'] for v in discrim][:5]}）" if discrim else
           " → 阈值 1.0 仍**无区分力**（未被证伪 ≠ 被验证）"))
    log(f"  → {a.out}")
    return 0


def _last(path):
    if not os.path.exists(path):
        return None
    return [json.loads(l) for l in open(path, encoding="utf-8")]      # noqa: E741


if __name__ == "__main__":
    sys.exit(main())

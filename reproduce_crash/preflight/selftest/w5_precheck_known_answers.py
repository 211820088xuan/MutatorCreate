#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""W5：② 构建前预检的**已知答案回归**（把 W4 当时内联跑的验证固化成可复算 artifact）。

为什么必须固化：W4 报告里写着「harfbuzz 6/6、pcapplusplus 3/3 命中、已知能建的 6 条 0 误报」，
但那是内联 heredoc 跑的 → §6 声称可复算、实际不可复算（与 ② 分类器自测同一个毛病，W5 已记为
自查纪律④）。**而 W5 刚改过预检的两处归一化/前置条件**（`sha=None` 放行、去 `./` 前缀），
改完必须重跑已知答案，否则「修一个误报、放跑一个真报」是看不出来的。

已知答案全部取自**真实产物**（`build_records.jsonl` 的实际成败 + `repro_manifest.jsonl` 的
repo_url/repo_path），不是手写期望：
  * 该报缺失的：harfbuzz（N19 形态①，`ninja: unknown target`）、
    pcapplusplus（N23 形态②，build.sh 执行不存在的脚本）、libspng（W5 新增，同形态②）
  * 不许误报的：c-blosc2 / pcre2 / hunspell / md4c / libtsm 里**实测构建成功**的那些 commit

网络开销：走 `raw` 端点（0 次 API、0 次 clone），每条 1–4 次 GET，全部有 /tmp 缓存。
复算：python3 preflight/w5_precheck_known_answers.py [--max-each 4]
"""
import argparse
import collections
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, ROOT)
import repro_common as rc            # noqa: E402
import build_orchestrator as B       # noqa: E402

RECORDS = os.path.join(rc.ARTIFACTS, "build_records.jsonl")
MANIFEST = os.path.join(rc.ARTIFACTS, "repro_manifest.jsonl")
FAILS = []


def ck(cond, msg):
    print(("  ✅ " if cond else "  ❌ ") + msg)
    if not cond:
        FAILS.append(msg)


def load():
    man = {}
    for line in open(MANIFEST, encoding="utf-8"):
        r = json.loads(line)
        man[r["osv_id"]] = r
    recs = []
    for line in open(RECORDS, encoding="utf-8"):
        r = json.loads(line)
        k = (r.get("key") or "").split("|")
        if len(k) < 3:
            continue
        recs.append({"project": k[0], "san": k[1], "commit": k[2],
                     "ok": r.get("build_status") == "ok",
                     "cls": r.get("build_error_class"), "osv": r.get("osv_id"),
                     "log": r.get("build_log"),        # [W5] 判「缺路径」形态要读日志
                     # **[N73③] 兜底证据源**：`artifacts/logs/build/` 被误删后 `log` 全部失效
                     #   → harfbuzz/pcapplusplus 两个已知答案被**静默跳过**（本测试第 132 行的
                     #   「跳过必须为零」断言抓住了它）。`build_error_detail` 是复现记录表里**幸存**的
                     #   错误摘要，pcapplusplus 的 3 行含 `No such file or directory` 标记 →
                     #   可据此恢复。**不放宽断言，只换证据源**，并打印用的是哪一种。
                     "detail": r.get("build_error_detail")})
    return man, recs


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--max-each", type=int, default=4, help="每个项目最多验几个 commit")
    ap.add_argument("--sleep", type=float, default=0.1)
    a = ap.parse_args()
    man, recs = load()

    def meta(proj):
        for oid, r in man.items():
            if r.get("project") == proj and r.get("repo_url"):
                return r.get("repo_url"), (r.get("repo_path") or f"/src/{proj}")
        return None, f"/src/{proj}"

    # ── 该报缺失的（实测钉版全败于 buildscript 类）──
    should_block = {"harfbuzz": "N19 形态①（ninja unknown target）",
                    "pcapplusplus": "N23 形态②（build.sh 执行不存在的脚本）",
                    "libspng": "W5 实测 6 次形态②（tests/ossfuzz.sh 不在老 commit 树里）"}
    # ── 不许误报的（实测构建成功过）──
    by_proj = collections.defaultdict(list)
    for r in recs:
        by_proj[r["project"]].append(r)
    allow = {p: [r for r in v if r["ok"]] for p, v in by_proj.items()}
    allow = {p: v for p, v in allow.items() if v and p not in should_block}

    print("═" * 88)
    print("W5 ② 预检已知答案回归（真报不许放跑、误报不许新增）")
    print("═" * 88)

    n_block_checked = 0
    skipped_proj = set()
    print("\n[A] 该报缺失的项目（**只取「缺路径」形态的失败**）")
    # ⚠ [W5 修测试期望] 原先把 `toolchain_drift`/`compile_error` 也算作「预检该拦」，
    # 结果 libspng 报 3/4：被「放跑」的那条 `f47ed26affe9` 实测类是 **toolchain_drift**
    # —— 路径存在性检查**在构造上就预测不了工具链漂移**，预检放行是对的（checked=1、missing=[]）。
    # 判据改成非循环的两条：①类已是 `buildscript_mismatch`；②类是 `compile_error` 但日志里
    # 确有 `ninja: error: unknown target`（harfbuzz 的历史误分类形态，W2 当时还没这个类）。
    def is_missing_path_form(r):
        if r["cls"] == "buildscript_mismatch":
            return True
        # 形态①（N19）`ninja: error: unknown target` / 形态②（N23）`…: No such file or directory`
        # ⚠ [W5 修] 原先只认形态① → **pcapplusplus 被静默跳过**（它的失败是形态②，
        # 且当年被分类成 compile_error/toolchain_drift），而 [A] 的防空过断言因为
        # harfbuzz+libspng 凑够 8 条**照样通过** → 又一个「跳过与 0 候选不可区分」的实例。
        if r["cls"] in ("compile_error", "toolchain_drift"):
            MARK = ("unknown target", "No such file or directory", "can't open file")
            # 优先读完整日志（原证据源）
            if r.get("log"):
                try:
                    txt = open(r["log"], encoding="utf-8", errors="replace").read()
                    if any(m in txt for m in MARK):
                        r["_ev"] = "log"
                        return True
                except OSError:
                    pass                        # 日志已不存在 → 落到下面的兜底
            # **[N73③] 兜底**：复现记录表 `build_error_detail`（截断摘要）
            d = str(r.get("detail") or "")
            if any(m in d for m in MARK):
                r["_ev"] = "detail"
                return True
            r["_ev"] = None
            return False
        return False

    for proj, why in should_block.items():
        rows = [r for r in by_proj.get(proj, []) if not r["ok"] and is_missing_path_form(r)]
        rows = rows[:a.max_each]
        if not rows:
            print(f"  ⓘ {proj}: 无「缺路径」形态的失败记录，跳过（不等于该项目没失败）")
            skipped_proj.add(proj)
            continue
        url, rp = meta(proj)
        hit = 0
        n_block_checked += len(rows)
        for r in rows:
            res = B.precheck_buildscript(proj, url, r["commit"], sleep=a.sleep,
                                         verbose=False, repo_path=rp)
            hit += 0 if res["ok"] else 1
        ev = collections.Counter(r.get("_ev") for r in rows)
        ck(hit == len(rows),
           f"{proj:<14} {hit}/{len(rows)} 命中（{why}）· 证据源 {dict(ev)}"
           + ("" if hit == len(rows) else f" ← 有 {len(rows)-hit} 条被放跑了"))

    ck(n_block_checked > 0,
       f"[A] 节确实验到了 {n_block_checked} 条「缺路径」失败")
    ck(not skipped_proj,
       f"**每个**声明的已知答案项目都真验到了（被跳过的：{sorted(skipped_proj) or '无'}）"
       " —— 跳过必须为零，否则「已知答案回归」名不副实")

    print("\n[B] 实测能构建的项目：预检**不许误报**（误报会跳过本能成功的构建，比漏报更糟）")
    for proj, rows in sorted(allow.items()):
        rows = rows[:a.max_each]
        url, rp = meta(proj)
        fp, und = 0, 0
        for r in rows:
            res = B.precheck_buildscript(proj, url, r["commit"], sleep=a.sleep,
                                         verbose=False, repo_path=rp)
            if not res["ok"]:
                fp += 1
            if res.get("reason") in ("no_candidate_paths", "no_sha", "no_build_sh") \
               or res.get("undecidable"):
                und += 1
        ck(fp == 0, f"{proj:<14} {len(rows)} 个已成功 commit → 误报 {fp}"
                    f"（无法判定/无候选 {und} 条，属正常放行）")

    print("\n[C] 契约：无法判定时一律放行（W5 修的 bug①）")
    url, rp = meta("libredwg")
    res = B.precheck_buildscript("libredwg", url, None, verbose=False, repo_path=rp)
    ck(res["ok"] and res["reason"] == "no_sha" and not res["missing"],
       f"sha=None → 放行、reason={res['reason']!r}、missing={res['missing']}")
    res = B.path_exists_at(url, None, "autogen.sh")
    ck(res is None, f"path_exists_at(sha=None) = {res!r}（None=无法判定，不是 False=确定缺失）")

    print("\n[D] N71：形态① 必须剥 `$SRC/<repo>/` 前缀（icu 假阴性回归）")
    # ✅ 已知答案（GitHub contents API 逐树核对过）：`icu4c/source/test/fuzzer/locale_util.cpp`
    #   在下面两个 commit 的树里**都存在**；修复前候选被抓成带 `icu/` 前缀 → 必然 404 →
    #   误判 `buildscript_mismatch`，**一次挡死 icu 整个钉版池**。
    icu_url = "https://github.com/unicode-org/icu.git"
    for sha in ("906093f31b44316ba7da24972f95a0510355e61d",
                "7cec4a9308b0d693b08f0bc35a2a08ce6d5f4646"):
        res = B.precheck_buildscript("icu", icu_url, sha, verbose=False, repo_path="/src/icu")
        ck(res["ok"] and not res["missing"],
           f"icu@{sha[:12]} → ok={res['ok']} checked={res['checked']} missing={res['missing']}")
    # **负对照**：`repo_path` 给错（basename 与被引路径首段不符）时**不得**误剥，
    #   仍应判缺失 —— 证明剥离是按 `repo_path` 精确驱动的，不是无条件砍第一段。
    res = B.precheck_buildscript("icu", icu_url,
                                 "906093f31b44316ba7da24972f95a0510355e61d",
                                 verbose=False, repo_path="/src/noticu")
    ck(not res["ok"] and any(x.startswith("icu/") for x in res["missing"]),
       f"负对照 repo_path=/src/noticu → ok={res['ok']} missing={res['missing']}")

    print("\n" + (f"❌ {len(FAILS)} 项未通过：{FAILS}" if FAILS else "✅ 全部通过"))
    return 1 if FAILS else 0


if __name__ == "__main__":
    sys.exit(main())

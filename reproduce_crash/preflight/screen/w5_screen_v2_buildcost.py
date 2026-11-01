#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""W5 v2：选下一个项目的离线筛选 —— 只用**实测证明有区分力**的维度。

v1（`w5_screen_next_projects.py`）漏了「构建成本」这一维，导致推荐 libredwg 而它 30min+/次构建
且 `make check-prep` 撑爆磁盘；v1 也**没法**预测 opensc 的 `-Werror` 失败（预检照样 ✅ 通过）。

⚠ **本轮被实测否证的维度（不要再用了）**：「crash 年份越新越可构建」。
   反例：libtsm 年份中位 **2017**、2023+ 仅 9% → 可构建率 **100%**；
        pcapplusplus 年份中位 **2023**、2023+ 占 53% → **0/3**。
   → 年份与可构建率**无单调关系**，v2 不把它当预测因子（只作为描述性信息打印）。

**v2 用的四个维度（每个都对应一次实测失败）**：
  ① 第三方外链（`dead_external_url`）—— libspng 11/19 的死因（N28）
  ② build.sh 引用的仓库内路径是否存在（`buildscript_mismatch`）—— harfbuzz 0/7、pcapplusplus 0/3（N19/N23）
  ③ **构建体量**：build.sh 是否编测试套件（libredwg `make check-prep` → 磁盘/时间爆）+ repo 体量（构建耗时代理，
     校准点：hunspell 10MB=快、libredwg 93MB=30min+、radare2 204MB、php 640MB）
  ④ **无法离线判定的**：`-Werror` 工具链漂移（opensc 0/3 的死因）→ 只能靠**探针构建**（3 条、~10min）

结论口径：**离线筛选只能排除已知失败模式，不能保证可构建** → 排序后必须先跑探针再决定整池。

复算：python3 preflight/w5_screen_v2_buildcost.py [--min-pool 20]
"""
import argparse
import collections
import json
import os
import re
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, ROOT)
import repro_common as rc            # noqa: E402
import build_orchestrator as B       # noqa: E402

MANIFEST = os.path.join(rc.ARTIFACTS, "repro_manifest.jsonl")
DATASET = os.path.join(rc.REPRO_DIR, "repro_dataset.jsonl")
WT = rc.OSS_FUZZ_WORKTREE
# 已实测过的项目（含**已证不可行**的，避免重复推荐 → 每个都是 2.3–2.9GB 镜像 + 一次探针的成本）
TRIED = {"c-blosc2", "hunspell", "pcre2", "md4c", "libtsm", "flatbuffers", "harfbuzz",
         "pcapplusplus", "libspng", "libtiff", "opensc", "libredwg", "openh264"}
TRIED_WHY = {"harfbuzz": "0/7 buildscript_mismatch", "pcapplusplus": "0/3 N23②",
             "libspng": "1/19 dead_external_url 11 + mismatch 6", "flatbuffers": "5/28 compile_error",
             "libredwg": "不可行：make check-prep 撑爆磁盘 + 30min/次构建（N31）",
             "opensc": "0/3 -Werror 工具链漂移", "openh264": "0/3 dockerfile_drift（N33）+ #include 缺头文件（N34）"}
# ③ 构建体量：**精确**模式（v1 用 `/tests?/` 太松 → opensc 的 `$SRC/opensc/src/tests/fuzzing/`
#    是 fuzzer 源码本身，被误判成"编测试套件"。教训：判据要能区分「测试套件」与「fuzzer 目录」）
TESTSUITE_RE = re.compile(r"make\s+(?:\S+\s+)*(?:check|check-prep|test|tests)\b|"
                          r"make\s+-C\s+\S*test|ctest\b|ninja\s+test\b", re.I)
FETCH_RE = re.compile(r"\b(?:wget|curl\s+-[^\s]*[Oo]|git\s+clone|svn\s+(?:co|checkout)|hg\s+clone)\b")
URL_RE = re.compile(r"https?://[^\s'\";$)]+")


def local_images():
    try:
        out = subprocess.run(["docker", "images", "--format", "{{.Repository}}:{{.Tag}}"],
                             capture_output=True, text=True, timeout=60).stdout
    except Exception:                                      # noqa: BLE001
        return set()
    return {l.split("/")[-1].split(":")[0] for l in out.splitlines() if "oss-fuzz/" in l}


def scan_build_sh(project):
    """①③：外链与测试套件（精确模式）。"""
    third, testsuite, lines = [], [], 0
    for fn in ("build.sh", "Dockerfile"):
        p = os.path.join(WT, "projects", project, fn)
        if not os.path.exists(p):
            continue
        for line in open(p, encoding="utf-8", errors="replace"):
            lines += 1
            st = line.strip()
            if st.startswith("#"):
                continue
            if FETCH_RE.search(line):
                for u in URL_RE.findall(line):
                    if project.replace("-", "").lower() not in u.replace("-", "").lower():
                        third.append(f"{fn}:{u[:58]}")
            m = TESTSUITE_RE.search(line)
            if m:
                testsuite.append(f"{fn}: {st[:60]}")
    return {"n_third_party": len(third), "third_party": third[:3],
            "testsuite": testsuite[:3], "n_lines": lines}


def repo_size_mb(repo_url):
    """③ 构建耗时代理：GitHub 报的 repo 体量（MB）。非 github / 失败 → None（**不当 0**）。"""
    kind, a, b = rc.classify_repo(repo_url)
    if kind != "github":
        return None
    txt, code = rc.http_get(f"https://api.github.com/repos/{a}/{b}", tries=1, timeout=20)
    try:
        return round(json.loads(txt).get("size", 0) / 1024, 1)
    except Exception:                                      # noqa: BLE001
        return None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--min-pool", type=int, default=20)
    ap.add_argument("--sample-commits", type=int, default=2)
    ap.add_argument("--top", type=int, default=14)
    ap.add_argument("--include-commits", type=int, default=1,
                    help="[W5 N34③] 每个项目用几个 commit 查 fuzzer 源码的 #include（0=跳过；"
                         "每个 include 最多 24 次 HTTP，故默认只查 1 个 commit）")
    ap.add_argument("--json", default=os.path.join(HERE, "w5_screen_v2_buildcost.json"))
    a = ap.parse_args()

    man = [json.loads(l) for l in open(MANIFEST, encoding="utf-8")]
    done = {json.loads(l)["osv_id"] for l in open(DATASET, encoding="utf-8")}
    imgs = local_images()
    pool = collections.defaultdict(list)
    for r in man:
        if r.get("skip_reason") or r["osv_id"] in done or not r.get("fixed_commit"):
            continue
        pool[r["project"]].append(r)

    cands = [(p, rs) for p, rs in pool.items() if p not in TRIED and len(rs) >= a.min_pool]
    cands.sort(key=lambda kv: -len(kv[1]))
    cands = cands[:a.top]

    print("═" * 104)
    print("W5 v2 筛选：只用实测有区分力的维度（外链 / 路径错配 / 构建体量）+ 标注离线判不了的部分")
    print("═" * 104)
    print(f"候选：未试过、池 ≥{a.min_pool} 的项目 {len(cands)} 个；本地已有镜像 {len(imgs)} 个")
    print(f"已排除（实测过）：{len(TRIED)} 个 → " + "; ".join(f"{k}={v}" for k, v in sorted(TRIED_WHY.items())))
    print("⚠ 已否证的维度：crash 年份（libtsm 中位 2017→100% 可构建；pcapplusplus 中位 2023→0/3）\n")
    hdr = (f"{'项目':<16}{'池':>4}{'UBSAN':>6}{'MSAN':>5}{'镜像':>6}{'第三方外链':>10}"
           f"{'测试套件':>9}{'repo MB':>9}{'错配':>7}{'inc缺':>9}  判定")
    print(hdr)
    print("─" * 104)
    rows = []
    for proj, recs in cands:
        sc = scan_build_sh(proj)
        size = repo_size_mb(recs[0].get("repo_url"))
        pc = {"n": 0, "bad": 0, "checked": 0, "undecidable": 0, "why": []}
        for r in recs[:a.sample_commits]:
            sha = r.get("fixed_parent") or r.get("pin_commit") or r.get("fixed_commit")
            if not sha:
                continue
            res = B.precheck_buildscript(proj, r.get("repo_url"), sha, verbose=False,
                                         repo_path=r.get("repo_path") or f"/src/{proj}")
            pc["n"] += 1
            pc["checked"] += res.get("checked") or 0
            pc["undecidable"] += res.get("undecidable") or 0
            if res.get("reason") in ("no_candidate_paths", "no_build_sh", "no_sha"):
                pc["why"].append(res["reason"])
            elif not res.get("ok"):
                pc["bad"] += 1
                pc["why"].append(f"{sha[:10]}:缺{res.get('missing')}")
        # ⑤ [W5 N34③] fuzzer 源码的 #include 是否在该 commit 存在（openh264 的真凶）
        ic = {"n": 0, "bad": 0, "missing": [], "why": []}
        if a.include_commits:
            for r in recs[:a.include_commits]:
                sha2 = r.get("fixed_parent") or r.get("pin_commit") or r.get("fixed_commit")
                if not sha2:
                    continue
                r2 = B.precheck_includes(proj, r.get("repo_url"), sha2, verbose=False)
                ic["n"] += 1
                if r2.get("reason") in ("no_sha", "no_repo_url", "no_project_dir",
                                        "no_sources", "no_includes"):
                    ic["why"].append(r2["reason"])
                elif not r2.get("ok"):
                    ic["bad"] += 1
                    ic["missing"] += r2.get("missing", [])[:3]
                elif r2.get("undecidable") and not r2.get("checked"):
                    ic["why"].append("undecidable")
        # ⚠ [W5 N29] `n` 是「尝试了几个 commit」，其中查不了的记在 why 里 →
        #   **真正有效的检查数 = n − len(why)**。实测 8 个候选**全部**是 no_sources/no_includes
        #   （它们的 Dockerfile 不像 openh264 那样把 fuzzer 源码 COPY 进 $SRC，而是直接编仓库里的），
        #   → 该维度对它们**不适用**，必须显示成「不适用」而不是 `0/1`（那会被读成"查了、干净"）。
        ic["effective"] = ic["n"] - len(ic["why"])
        san = collections.Counter(r.get("sanitizer") for r in recs)
        # 判定：⛔ 出局 / ⚠ 高风险 / ✅ 值得探针 / ⓘ 证据不足
        if ic["n"] and ic["bad"] == ic["n"]:
            verdict, rank = f"⛔ #include 缺失（openh264 同型）：{ic['missing'][:2]}", -1
        elif pc["n"] and pc["bad"] == pc["n"]:
            verdict, rank = "⛔ 路径错配全中（harfbuzz 同型）", -1
        elif sc["testsuite"]:
            verdict, rank = "⛔ build.sh 编测试套件（libredwg 同型：磁盘/时间爆）", -1
        elif sc["n_third_party"] >= 2:
            verdict, rank = "⚠ 第三方外链多（libspng/N28 同型风险）", 0
        elif size and size > 150:
            verdict, rank = f"⚠ repo {size}MB 偏大（构建耗时风险，radare2 204MB 量级）", 0
        elif pc["checked"] > 0 and pc["bad"] == 0 and sc["n_third_party"] == 0:
            verdict, rank = "✅ 值得探针（路径实测在、无第三方外链）", 2
        else:
            verdict, rank = f"ⓘ 证据不足（{','.join(sorted(set(pc['why']))) or 'undecidable'}）→ 只能探针", 1
        rows.append({"project": proj, "pool": len(recs), "ubsan": san.get("undefined", 0),
                     "msan": san.get("memory", 0), "image_local": proj in imgs,
                     "repo_mb": size, **sc, "precheck": pc, "include_check": ic,
                     "verdict": verdict, "rank": rank})
        print(f"{proj:<16}{len(recs):>4}{san.get('undefined', 0):>6}{san.get('memory', 0):>5}"
              f"{'本地' if proj in imgs else '需建':>6}{sc['n_third_party']:>10}"
              f"{('有' if sc['testsuite'] else '无'):>9}{str(size if size else '—'):>9}"
              f"{(str(pc['bad']) + '/' + str(pc['n'])) if pc['n'] else '—':>7}"
              f"{((str(ic['bad']) + '/' + str(ic['effective'])) if ic.get('effective') else '不适用'):>7}"
              f"  {verdict}")

    print("\n── 推荐序（✅ 优先，其次 ⓘ；⛔ 出局；⚠ 需人工权衡）──")
    ok = [r for r in rows if r["rank"] == 2]
    ok.sort(key=lambda r: (-r["pool"], r["repo_mb"] or 9e9))
    for i, r in enumerate(ok[:5], 1):
        print(f"  {i}. {r['project']:<16}池 {r['pool']:>3} | repo {r['repo_mb']}MB | "
              f"UBSAN {r['ubsan']} / MSAN {r['msan']} | 镜像{'已在本地' if r['image_local'] else '需建 ~2.3GB'}")
    if not ok:
        print("  （无 ✅ 级候选 → 见 ⓘ/⚠ 名单，需人工权衡）")
    for r in rows:
        if r["testsuite"]:
            print(f"     ⛔ {r['project']}: {r['testsuite'][0]}")
        if r["n_third_party"]:
            print(f"     外链 {r['project']}: {r['third_party'][0] if r['third_party'] else ''}")
    print("\n⚠ 无论排第几，**都必须先跑 3 条探针**（~10min）再决定整池："
          "opensc 的预检 ✅ 通过却 0/3 构建失败（-Werror），离线判不了这一类。")
    with open(a.json, "w", encoding="utf-8") as f:
        json.dump({"falsified_dimension": "crash 年份（libtsm 2017→100% vs pcapplusplus 2023→0/3）",
                   "tried": sorted(TRIED), "rows": rows,
                   "recommend": [r["project"] for r in ok[:5]]}, f, ensure_ascii=False, indent=1)
    print(f"→ 落盘 {os.path.relpath(a.json, ROOT)}")


if __name__ == "__main__":
    main()

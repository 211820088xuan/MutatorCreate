#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""静态数据流规模化 —— 对每条已复现 crash，在**漏洞版源码**上跑 Joern CPG 查询。

为什么做（补 M8 的空白）
  M8 是动态的「故障时刻读寄存器 + 几何对齐」，只能给出**值**，给不出**来源链**。
  本脚本回答的是：**故障点那个量，是从哪来的？** —— 函数参数？全局？局部计算？
  以及：**有没有一个"容量类"参数参与过比较**（即有没有边界检查）。
  这两条都是**项目无关**的结构特征，适合按崩溃类型分组找共性。

已验证的靶子（§REPORT 4.1）
  OSV-2022-55 / c-blosc2 / `ndlz4x4.c:544`：
    `input` → `(uint8_t*)input` → `ip` → …(532,537,538,539) → `&blockshape[1]` → `blockshape[1]`
    共 9 跳；含 `output_len` 的比较数 = **0**（漏洞版）vs **1**（修复版）。

成本（实测）
  c2cpg 建**整个 c-blosc2**（503 文件）= **13s / 5.8MB**；目录级（10 文件）= 5s / 148KB。
  → 按 (仓库, 漏洞版 commit) 建整项目 CPG 并**缓存复用**，同 commit 的多条 crash 共享一次构建。

⚠ Joern API 两个坑（本会话实测踩过，务必保留）
  1. **Traversal 是一次性迭代器**：`val t = …; t.l; t.code.l` 第二次起返回空。
     实测 `sink.l.size=2` 之后 `sink.code.l` 就空了，导致 `reachableBy` 全 0 的**假阴性**。
     → **一律用 `def`**，每次重新构造。
  2. 对 **Traversal** 调 `.parameter` / `.ast` 返回空，必须先 `.head` 取到 **节点**。
"""
from __future__ import annotations

import argparse
import collections
import json
import os
import re
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)   # pattern_analysis/
TOP = os.path.dirname(ROOT)    # mutator_create/
RC = os.path.join(TOP, "reproduce_crash")
WORK = "/tmp/opencode/cpg_cache"
CPGDIR = "/root/gyx/mutator_create/cpg_files"
SRCDIR = os.path.join(WORK, "src")
JL = "/usr/local/lib/python3.10/dist-packages/pyjoern/bin/joern-cli"
C2CPG = os.path.join(JL, "frontends/c2cpg/bin/c2cpg")
JOERN = os.path.join(JL, "joern")
# 容量类参数的名字特征（跨项目同义词，含匈牙利前缀）
SIZELIKE = re.compile(r"(len|size|sz|count|cnt|num|cap|max|limit|nbytes|cbytes|width|height|"
                      r"ofst|offset)", re.I)


def sh(cmd, timeout=1800, cwd=None):
    return subprocess.run(cmd, capture_output=True, text=True, errors="replace",
                          timeout=timeout, cwd=cwd, stdin=subprocess.DEVNULL)


REPRODUCED = os.path.join(ROOT, "artifacts", "reproduced_crashes.jsonl")


def load_reproduced():
    """加载已复现崩溃数据集，返回 {osv_id: 记录}。

    字段名保持与旧复现日志（repro_dataset.jsonl）兼容，便于现有脚本直接使用。
    """
    out = {}
    with open(REPRODUCED, encoding="utf-8") as fh:
        for ln in fh:
            ln = ln.strip()
            if not ln:
                continue
            d = json.loads(ln)
            out[d["osv_id"]] = {
                "cpg": d.get("cpg_path"),
                "report": d.get("report_path"),
                "raw_log_path": d.get("report_path"),
                "report_dir": d.get("report_dir"),
                "repo_url": d.get("repo_url"),
                "pin_commit": d.get("pin_commit"),
                "pinned_commit": d.get("pin_commit"),
                "src_head": d.get("pin_commit"),
                "project": d.get("project"),
                "crash_type": d.get("crash_type"),
                "crash_type_norm": d.get("crash_type_norm"),
                "fuzz_target": d.get("fuzz_target"),
                "sanitizer": d.get("sanitizer"),
                "testcase_size": d.get("testcase_size"),
                "verification_tier": d.get("verification_tier"),
                "fixed_real": d.get("fix_commit"),
                "ok": True,
                "reproduced_any": True,
            }
    return out


def project_of(url: str) -> str:
    """从仓库 URL 提取项目名（用于 CPG 文件/目录命名）。"""
    slug = re.sub(r"[^A-Za-z0-9_.-]+", "_",
                  (url or "").replace("https://", "").replace("git://", ""))[:64]
    proj = slug.split("_")[-1]
    return proj[:-4] if proj.endswith(".git") else proj


def repo_dir(url: str) -> str | None:
    slug = re.sub(r"[^A-Za-z0-9_.-]+", "_",
                  (url or "").replace("https://", "").replace("git://", ""))[:64]
    d = os.path.join("/tmp/opencode/src_local", slug)
    return d if os.path.isdir(d) else None


def vuln_commit(repodir: str, fixed_real: str, pin: str | None) -> tuple[str | None, str]:
    """漏洞版 commit：优先复现记录表的 `pin_commit`（构建时真正用的），否则 `fixed_real^1`。"""
    if pin:
        r = sh(["git", "-C", repodir, "cat-file", "-e", pin + "^{commit}"])
        if r.returncode == 0:
            return pin, "pin_commit"
    if fixed_real:
        r = sh(["git", "-C", repodir, "rev-parse", "--verify", "-q", fixed_real + "^1^{commit}"])
        if r.returncode == 0 and r.stdout.strip():
            return r.stdout.strip(), "fixed_real^1"
    return None, "unresolved"


def ensure_src(repodir: str, commit: str) -> str | None:
    d = os.path.join(SRCDIR, f"{os.path.basename(repodir)}_{commit[:12]}")
    if os.path.isdir(d) and os.listdir(d):
        return d
    os.makedirs(d, exist_ok=True)
    p1 = subprocess.Popen(["git", "-C", repodir, "archive", commit], stdout=subprocess.PIPE)
    p2 = subprocess.run(["tar", "-x", "-C", d], stdin=p1.stdout, capture_output=True)
    p1.wait()
    if p1.returncode != 0 or p2.returncode != 0:
        return None
    return d


def ensure_cpg(srcdir: str, key: str) -> str | None:
    out = os.path.join(CPGDIR, key + ".cpg")
    if os.path.isfile(out) and os.path.getsize(out) > 1000:
        return out
    os.makedirs(CPGDIR, exist_ok=True)
    r = sh([C2CPG, srcdir, "-o", out], timeout=2700)
    return out if (r.returncode == 0 and os.path.isfile(out)) else None


SCALA_TMPL = r'''
importCpg("__CPG__")
case class T(fn: String, line: Int, osv: String)
val targets = List(__TARGETS__)

// ⚠ Joern/replpp 两个实测坑：
//   ① Traversal 是**一次性迭代器** → 一律用 def 重新构造，不要 val 缓存
//   ② `cpg.ast` / `cpg.methodRETURN` **不存在**（正确是 `cpg.all` / `cpg.methodReturn`）；
//      `reachableBy` 只能用在 **Traversal** 上，不能用在单个节点上
def methodAt(fn: String, line: Int) = {
  // ① 先按函数名精确匹配：修复「仅按行号跨文件匹配」的 bug
  //    （同一行号可能存在于别的文件，line-based 会选错，如 bitunshuffle2_neon:544）
  val byName = cpg.method.nameExact(fn).l
  if (byName.nonEmpty) byName.head
  else {
    val byCall = cpg.call.lineNumber(line).method.l
    if (byCall.nonEmpty) byCall.head
    else {
      val byId = cpg.identifier.lineNumber(line).method.l
      if (byId.nonEmpty) byId.head
      else {
        val byLit = cpg.literal.lineNumber(line).method.l
        if (byLit.nonEmpty) byLit.head
        else {
          val byRet = cpg.methodReturn.lineNumber(line).method.l
          if (byRet.nonEmpty) byRet.head else null
        }
      }
    }
  }
}

val SIZE_RE = ".*(len|size|sz|count|cnt|num|cap|max|limit|nbytes|cbytes|width|height|ofst|offset|ndim|shape).*"
val CMP_RE  = "<operator>.comparison|<operator>.lessThan|<operator>.greaterThan|<operator>.lessEqualsThan|<operator>.greaterEqualsThan|<operator>.notEquals|<operator>.equals"

for (t <- targets) {
  println(s"@@OSV ${t.osv}")
  val m = methodAt(t.fn, t.line)
  if (m == null) { println("@@METHOD_MISSING") }
  else {
    println(s"@@METHOD ${m.name}")
    println(s"@@NPARAMS ${m.parameter.l.size}")
    println(s"@@PARAMS ${m.parameter.name.l.mkString(",")}")
    println(s"@@CALLS_AT_LINE ${m.ast.isCall.lineNumber(t.line).l.size}")
    println(s"@@CALL_CODES ${m.ast.isCall.lineNumber(t.line).code.l.take(4).map(_.take(56)).mkString(" | ")}")
    println(s"@@ID_CODES ${m.ast.isIdentifier.lineNumber(t.line).code.l.take(6).map(_.take(28)).mkString(",")}")
    println(s"@@LINE_NODES ${m.ast.isCall.lineNumber(t.line).l.size + m.ast.isIdentifier.lineNumber(t.line).l.size}")
    val sizeParams = m.parameter.name.l.filter(_.matches(SIZE_RE))
    println(s"@@SIZE_PARAMS ${sizeParams.mkString(",")}")
    val cmps = m.ast.isCall.name(CMP_RE).l
    println(s"@@N_CMP ${cmps.size}")
    val cmpSize = cmps.filter(c => c.argument.isIdentifier.name.l.exists(_.matches(SIZE_RE)))
    println(s"@@N_CMP_SIZE ${cmpSize.size}")
    println(s"@@CMP_SIZE_CODES ${cmpSize.map(_.code.take(66)).take(3).mkString(" | ")}")
    // ⭐ **精确判别式**：比较里涉及的量，必须**与故障行用的是同一个**。
    //   为什么不能用「任何容量类名字」：漏洞版有 `if (input_len <= 0)`，`input_len` 也匹配
    //   容量类正则 → 实测 n_cmp_size=3 而非 0，判别式**失效**。
    //   改成「比较涉及的标识符 ∩ 故障行的标识符 ≠ ∅」后：漏洞版 = 0（没有任何比较用到
    //   `blockshape`），修复版 = 1（`output_len < blockshape[0]*blockshape[1]`）。
    val lineIds = m.ast.isIdentifier.lineNumber(t.line).name.l.toSet
    println(s"@@LINE_IDS ${lineIds.mkString(",")}")
    val cmpGuard = cmps.filter(c => c.argument.isIdentifier.name.l.exists(n => lineIds.contains(n)))
    println(s"@@N_CMP_GUARD ${cmpGuard.size}")
    println(s"@@CMP_GUARD_CODES ${cmpGuard.map(_.code.take(70)).take(3).mkString(" | ")}")
    // 数据流：每个参数 → 故障行上的表达式
    // ⚠ **必须从 `cpg` 起手**：`m.ast`（m 是节点）返回的是 **Iterator**，
    //   没有 `reachableBy` / `reachableByFlows`（实测编译错误：
    //   `value reachableBy is not a member of Iterator[...AstNode]`）。
    //   从 `cpg.method.nameExact(...)` 起手才是 Traversal。仍用 def（一次性迭代器）。
    // ⚠ **必须在 `.lineNumber` 之前先加节点类型步**：实测 `M.ast.lineNumber(x)` 返回 Iterator
    //   （无 reachableBy），而 `M.ast.isCall.lineNumber(x)` 是 Traversal（8 种写法逐一实测过）。
    def lineTrav = m.ast.isCall.lineNumber(t.line) ++ m.ast.isIdentifier.lineNumber(t.line)
    for (pn <- m.parameter.name.l) {
      def src = cpg.method.nameExact(m.name).parameter.nameExact(pn)
      val reached = lineTrav.reachableBy(src).l.size
      if (reached > 0) {
        val flows = lineTrav.reachableByFlows(src).l
        println(s"@@PARAM_REACHES ${pn} nodes=${reached} paths=${flows.size}")
        if (flows.nonEmpty) {
          println(s"@@PATHLEN_${pn} ${flows.head.elements.size}")
          println(s"@@PATH_${pn} " + flows.head.elements.map(e => e.code.take(24)).take(12).mkString(" => "))
        }
      }
    }
    val inLoop = (m.ast.isCall.lineNumber(t.line).inAst.isControlStructure
                    .controlStructureType("DO|WHILE|FOR").l.nonEmpty) ||
                 (m.ast.isIdentifier.lineNumber(t.line).inAst.isControlStructure
                    .controlStructureType("DO|WHILE|FOR").l.nonEmpty)
    println(s"@@IN_LOOP $inLoop")
  }
}
'''


def build_script(cpg: str, targets: list[tuple]) -> str:
    tl = ", ".join(f'T("{fn}", {ln}, "{osv}")' for fn, ln, osv in targets)
    return SCALA_TMPL.replace("__CPG__", cpg).replace("__TARGETS__", tl)


def parse_out(txt: str) -> dict:
    out = {}
    cur = None
    for ln in txt.split("\n"):
        s = ln.strip()
        if s.startswith("@@OSV "):
            cur = s[6:].strip()
            out[cur] = {}
            continue
        if not cur or "@@" not in s:
            continue
        body = s[2:]
        k, _, v = body.partition(" ")
        d = out[cur]
        if k == "PARAM_REACHES":
            d.setdefault("reachability", []).append(v.split()[0])
            d["n_paths"] = d.get("n_paths", 0) + int(re.search(r"paths=(\d+)", v).group(1))
        elif k.startswith("PATHLEN_"):
            d.setdefault("path_lens", {})[k[8:]] = int(v)
        elif k.startswith("PATH_"):
            d.setdefault("paths", {})[k[5:]] = v[:300]
        elif k == "N_CMP_GUARD":
            d["guard"] = int(v) if v.isdigit() else None
        elif k in ("NPARAMS", "N_CMP", "N_CMP_SIZE", "CALLS_AT_LINE", "LINE_NODES"):
            d[k.lower()] = int(v) if v.isdigit() else None
        elif k == "IN_LOOP":
            d["in_loop"] = (v == "true")
        elif k == "METHOD_MISSING":
            d["method_missing"] = True
        else:
            d[k.lower()] = v
    return out


def selftest() -> int:
    """已知答案：OSV-2022-55 / c-blosc2 / `ndlz4x4.c:544`，本轮已人工在 Joern 里逐项确认过：
       input → memset 尺寸 **可达**、路径 **9 跳**、含 `output_len` 的比较数 **0**（漏洞版）。"""
    print("═══ 已知答案自测（OSV-2022-55，c-blosc2 ndlz4x4.c:544，漏洞版）═══")
    cpg = "/tmp/opencode/bake/vuln.cpg"
    if not os.path.isfile(cpg):
        print("  ⓘ 靶子 CPG 不在（/tmp 已清），跳过 —— 需先重建：见 REPORT §8")
        return 0
    sp = os.path.join(WORK, "q_selftest.scala")
    os.makedirs(WORK, exist_ok=True)
    open(sp, "w", encoding="utf-8").write(
        build_script(cpg, [("ndlz4_decompress", 544, "SELFTEST")]))
    r = sh([JOERN, "--script", sp], timeout=1800)
    d = parse_out(r.stdout + "\n" + r.stderr).get("SELFTEST") or {}
    bad = 0
    checks = [
        ("方法定位成功（按行号找所属方法）", d.get("method") == "ndlz4_decompress", str(d.get("method"))),
        ("参数数 = 6", d.get("nparams") == 6, str(d.get("nparams"))),
        ("**input 参数可到达故障行**", "input" in (d.get("reachability") or []),
         str(d.get("reachability"))),
        # ⚠ 路径长度**取决于 sink 的定义**：靶子实验里 sink = `memset` 第 3 实参 → 9 跳；
        #   这里 sink 放宽成「故障行上的所有 call+identifier」→ 实测 13 跳。故只断言 ≥1 且已记录。
        ("input → 故障行 有可用路径（长度随 sink 定义而变，此处 13 跳）",
         (d.get("path_lens") or {}).get("input", 0) >= 1, str(d.get("path_lens"))),
        ("容量类参数被识别（含 output_len）", "output_len" in (d.get("size_params") or ""),
         str(d.get("size_params"))),
        # **精确判别式**：与故障行共用变量的比较数。漏洞版必须为 0
        #   （`n_cmp_size`=3 是**宽松口径**，会被 `if (input_len <= 0)` 这类无关检查污染）
        ("**精确判别式 guard = 0**（漏洞版没有任何比较用到 blockshape）",
         d.get("guard") == 0,
         f"n_cmp={d.get('n_cmp')} 宽松 n_cmp_size={d.get('n_cmp_size')} **精确 guard={d.get('guard')}**"),
        ("宽松口径确实会误判（证明精确化是必要的）", (d.get("n_cmp_size") or 0) > 0,
         f"n_cmp_size={d.get('n_cmp_size')} ← 若用它当判别式就会漏掉这个漏洞"),
        ("故障行**不在**循环体内（memset 是直线语句）", d.get("in_loop") is False,
         str(d.get("in_loop"))),
    ]
    for note, ok, det in checks:
        bad += 0 if ok else 1
        print(f"  {'✅' if ok else '❌'} {note}\n      {det}")
    print(f"\n{'✅ 全部通过' if bad == 0 else f'❌ {bad} 项未通过'}")
    return 1 if bad else 0


def load_rows(projects=None) -> list[dict]:
    feat = {}
    with open(os.path.join(ROOT, "artifacts", "crash_report_features.jsonl"), encoding="utf-8") as fh:
        for ln in fh:
            r = json.loads(ln)
            feat[r["osv_id"]] = r
    lat = load_reproduced()
    ov = {}
    for p in ("fixed_real_backfill.jsonl", "fixed_real_backfill_local.jsonl"):
        fp = os.path.join(ROOT, "artifacts", p)
        if os.path.isfile(fp):
            with open(fp, encoding="utf-8") as fh:
                for ln in fh:
                    x = json.loads(ln)
                    if x.get("fixed_real"):
                        ov[x["osv_id"]] = x["fixed_real"]
    rows = []
    for osv, f in sorted(feat.items()):
        l = lat.get(osv, {})
        if l.get("verification_tier") not in ("strict", "medium", "loose"):
            continue
        if not (f.get("fault_site_file") and f.get("fault_site_line")):
            continue
        if projects and f.get("project") not in projects:
            continue
        fr = l.get("fixed_real") or ov.get(osv)
        rows.append({"osv_id": osv, "project": f.get("project"),
                     "crash_type_norm": f.get("crash_type_norm"),
                     "repo_url": l.get("repo_url"), "fixed_real": fr,
                     # 主分析版本 = 崩溃发生时的 commit：优先 pin_commit，其次 pinned_commit（239/239 都有）
                     "pin_commit": l.get("pin_commit") or l.get("pinned_commit") or l.get("src_head"),
                     "fault_site_file": f["fault_site_file"],
                     "fault_site_line": f["fault_site_line"],
                     "fault_site_fn": f.get("fault_site_fn"),
                     "access_dir": f.get("access_dir"),
                     "access_width": f.get("access_width")})
    return rows


def run(limit: int, out: str, keep: bool, projects=None) -> int:
    rows = load_rows(projects)
    if limit:
        rows = rows[:limit]
    print(f"═══ 静态数据流：{len(rows)} 条候选（有故障点坐标 + 已复现）═══")
    os.makedirs(WORK, exist_ok=True)
    # 按 (仓库, 漏洞版 commit) 分组，共享一次 CPG 构建
    groups = collections.defaultdict(list)
    skip = collections.Counter()
    for r in rows:
        rd = repo_dir(r["repo_url"])
        if not rd:
            skip["仓库未克隆"] += 1
            continue
        if not r["fixed_real"] and not r["pin_commit"]:
            skip["无 fixed_real/pin_commit"] += 1
            continue
        vc, how = vuln_commit(rd, r["fixed_real"], r["pin_commit"])
        if not vc:
            skip["漏洞版 commit 不可解析"] += 1
            continue
        r["_repodir"], r["_vuln"], r["_how"] = rd, vc, how
        groups[(rd, vc)].append(r)
    print(f"  分组 {len(groups)} 个 (仓库,漏洞版commit)；跳过 {dict(skip.most_common())}")
    results = []
    if os.path.isfile(out):
        results = [json.loads(l) for l in open(out, encoding="utf-8")]
    done = {x["osv_id"] for x in results}
    t0 = time.time()
    for gi, ((rd, vc), items) in enumerate(sorted(groups.items(), key=lambda kv: -len(kv[1])), 1):
        items = [x for x in items if x["osv_id"] not in done]
        if not items:
            continue
        src = ensure_src(rd, vc)
        if not src:
            for x in items:
                results.append({**{k: v for k, v in x.items() if not k.startswith("_")},
                                "error": "git_archive_failed"})
            continue
        key = f"{project_of(os.path.basename(rd))}_{vc[:12]}"
        cpg = ensure_cpg(src, key)
        if not cpg:
            for x in items:
                results.append({**{k: v for k, v in x.items() if not k.startswith("_")},
                                "error": "c2cpg_failed"})
            continue
        tg = [(x["fault_site_fn"] or "", x["fault_site_line"], x["osv_id"]) for x in items]
        sp = os.path.join(WORK, f"q_{key}.scala")
        open(sp, "w", encoding="utf-8").write(build_script(cpg, tg))
        r = sh([JOERN, "--script", sp], timeout=2700)
        parsed = parse_out(r.stdout + "\n" + r.stderr)
        for x in items:
            base = {k: v for k, v in x.items() if not k.startswith("_")}
            base["vuln_commit"] = vc
            base["commit_source"] = x["_how"]
            d = parsed.get(x["osv_id"])
            if not d:
                base["error"] = "joern_no_output"
                base["joern_tail"] = (r.stdout or r.stderr)[-200:]
            else:
                base.update(d)
            results.append(base)
        with open(out, "w", encoding="utf-8") as fh:
            for z in results:
                fh.write(json.dumps(z, ensure_ascii=False, sort_keys=True) + "\n")
        el = time.time() - t0
        print(f"  [{gi}/{len(groups)}] {os.path.basename(rd)[:26]:<28}{vc[:10]} "
              f"{len(items)} 条  解析 {len(parsed)}  累计 {el:.0f}s")
        if not keep:
            sh(["rm", "-rf", src])
    summarize(results)
    return 0


def summarize(results: list[dict]) -> None:
    ok = [r for r in results if not r.get("error") and not r.get("method_missing")]
    print(f"\n═══ 汇总 ═══")
    print(f"  成功 {len(ok)}/{len(results)}   失败 {dict(collections.Counter(str(r.get('error') or 'method_missing') for r in results if r.get('error') or r.get('method_missing')).most_common(6))}")
    if not ok:
        return
    pr = [r for r in ok if r.get("reachability")]
    print(f"  **故障行表达式可由某个函数参数到达**: {len(pr)}/{len(ok)} = {len(pr)/len(ok):.1%}")
    print(f"  到达的参数名 Top10: {dict(collections.Counter(p for r in pr for p in r['reachability']).most_common(10))}")
    pl = [v for r in ok for v in (r.get('path_lens') or {}).values()]
    if pl:
        pl.sort()
        print(f"  污点路径长度: 中位 {pl[len(pl)//2]} / 最小 {pl[0]} / 最大 {pl[-1]}")
    hs = [r for r in ok if r.get("size_params")]
    print(f"  方法有「容量类」参数: {len(hs)}/{len(ok)} = {len(hs)/len(ok):.1%}")
    guarded = [r for r in hs if (r.get("guard") or 0) > 0]
    print(f"  ⭐ **有容量类参数、且它参与过比较**（= 有边界检查）: {len(guarded)}/{len(hs)}"
          f" = {len(guarded)/max(len(hs),1):.1%}")
    print(f"     → 即 **{len(hs)-len(guarded)}/{len(hs)} 条：有容量参数却从未参与比较**（缺失检查）")
    print(f"  故障行在循环体内: {sum(1 for r in ok if r.get('in_loop'))}/{len(ok)}")
    print(f"\n  ── 按崩溃类型：「有容量参数但未参与比较」占比 ──")
    bt = collections.defaultdict(list)
    for r in hs:
        bt[r.get("crash_type_norm")].append(r)
    for t, v in sorted(bt.items(), key=lambda x: -len(x[1])):
        bad = sum(1 for r in v if (r.get("n_cmp_size") or 0) == 0)
        pj = len({r["project"] for r in v})
        pjb = len({r["project"] for r in v if (r.get("n_cmp_size") or 0) == 0})
        print(f"    {str(t):<28} n={len(v):<3} 项目{pj}  未检查 {bad}/{len(v)} = {bad/len(v):>4.0%}"
              f"  （涉及 {pjb} 个项目）")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--keep-src", action="store_true", help="保留解出的源码树（默认用完即删，省磁盘）")
    ap.add_argument("--projects", default="", help="逗号分隔项目名（用于并行分片）")
    ap.add_argument("--out", default=os.path.join(ROOT, "artifacts", "dataflow_features.jsonl"))
    a = ap.parse_args()
    if a.selftest:
        return selftest()
    projs = set(x for x in a.projects.split(",") if x) or None
    return run(a.limit, a.out, a.keep_src, projs)


if __name__ == "__main__":
    sys.exit(main())

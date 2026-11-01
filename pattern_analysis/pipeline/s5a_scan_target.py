#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""s5a_scan_target.py —— 阶段5①：为静态审计生成「worklist」（分段清单）

这一步是**纯机械的，不调用任何 LLM**。

为什么需要它
  `src/in_dxf.c` 有 492 KB / 12,884 行。一次 agent 调用的上下文装不下整个文件，
  实测（盲测）agent 只读了 18.8% 就收工，连已知的崩溃点都没看到。
  所以必须先把文件按**函数边界**切成小块，每块交给一个 agent —— 这就是 worklist。

它产出什么
  `audit_worklist.json`：
    functions[]  每个"含风险操作"的函数（名字 / 文件 / 起止行 / 风险标签 / 字符数）
    chunks[]     按字符预算打包好的批次，每批给一个 agent
  风险标签来自 CPG 的函数体内调用名：
    free    free / destroy / release
    alloc   alloc / malloc / calloc / realloc
    mem     memcpy / memmove / memset / strlen / strcpy / strcat / sprintf
    index   <operator>.indirectIndexAccess（即 a[i]）

它的自检
  如果 source_context.json 里有已知崩溃行（fault_line），会检查 worklist 是否**覆盖**它。
  覆盖不了就报警——这是"清单是否可信"的唯一硬判据。

用法
  python3 s5a_scan_target.py --osv ARVO-42494732                # 生成
  python3 s5a_scan_target.py --osv ARVO-42494732 --dry-run      # 只看统计
  python3 s5a_scan_target.py --osv ARVO-42494732 --depth 2      # 调用图展开深度
  python3 s5a_scan_target.py --osv ARVO-42494732 --max-chunk-chars 30000
"""
from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)                     # pattern_analysis/
TOP = os.path.dirname(ROOT)                      # mutator_create/
CPGDIR = os.path.join(TOP, "cpg_files")
OUT = os.path.join(TOP, "mutator_custom", "stage5")
JOERN = "/usr/local/lib/python3.10/dist-packages/pyjoern/bin/joern-cli/joern"

# 风险标签 ← 函数体内出现的调用名（一律小写匹配）
RISK_RULES = [
    ("free",  r".*(free|destroy|release).*"),
    ("alloc", r".*(alloc|malloc|calloc|realloc).*"),
    ("mem",   r".*(memcpy|memmove|memset|strlen|strcpy|strcat|sprintf).*"),
    ("index", r".*indexaccess.*"),          # <operator>.indirectIndexAccess
]

SCALA = r'''
importCpg("__CPG__")
cpg.method.l.foreach { m =>
  println(s"@@M\t${m.filename}\t${m.name}\t${m.lineNumber.getOrElse(0)}\t${m.lineNumberEnd.getOrElse(0)}\t${if (m.isExternal) 1 else 0}")
}
cpg.call.l.foreach { c =>
  val cs = c.callee.l.map(_.name).distinct.mkString("|")
  if (cs.nonEmpty) {
    val cm = c.method
    println(s"@@C\t${cm.filename}\t${cm.name}\t${cs}")
  }
}
'''


# ────────────────────────── CPG dump ──────────────────────────

def find_cpg(project: str, commit: str) -> str | None:
    if not os.path.isdir(CPGDIR):
        return None
    exact = os.path.join(CPGDIR, f"{project}_{commit[:12]}.cpg")
    if os.path.isfile(exact):
        return exact
    cands = [f for f in os.listdir(CPGDIR)
             if f.startswith(project + "_") and f.endswith(".cpg")]
    return os.path.join(CPGDIR, cands[0]) if cands else None


def dump_cpg(cpg: str, cache: str) -> tuple[list[dict], list[tuple]]:
    """返回 (methods, call_edges)。结果缓存到 cache（TSV），避免重复跑 Joern。"""
    if os.path.exists(cache) and os.path.getsize(cache) > 1000:
        print(f"  复用 CPG dump: {cache}")
    else:
        print(f"  跑 Joern 导出 CPG（约 1~3 分钟）…", flush=True)
        sc = cache + ".scala"
        open(sc, "w", encoding="utf-8").write(SCALA.replace("__CPG__", cpg))
        r = subprocess.run([JOERN, "--script", sc], capture_output=True, text=True, timeout=1800)
        lines = [ln for ln in (r.stdout or "").split("\n") if ln.startswith("@@")]
        if not lines:
            raise SystemExit(f"Joern 没有输出（stderr 前 500 字）:\n{(r.stderr or '')[:500]}")
        open(cache, "w", encoding="utf-8").write("\n".join(lines))
        print(f"  已导出 {len(lines)} 行 → {cache}")

    methods, edges = [], []
    for ln in open(cache, encoding="utf-8"):
        p = ln.rstrip("\n").split("\t")
        if p[0] == "@@M" and len(p) >= 6:
            methods.append({"file": p[1], "name": p[2],
                            "start": int(p[3] or 0), "end": int(p[4] or 0),
                            "external": p[5] == "1"})
        elif p[0] == "@@C" and len(p) >= 4:
            edges.append((p[1], p[2], p[3]))
    return methods, edges


# ────────────────────────── 分析 ──────────────────────────

def risk_tags(calls: set[str]) -> list[str]:
    low = [c.lower() for c in calls]
    return [tag for tag, rx in RISK_RULES if any(re.fullmatch(rx, c) for c in low)]


def bfs_functions(methods: list[dict], edges: list[tuple], depth: int) -> tuple[dict, dict]:
    """从 LLVMFuzzerTestOneInput 按**函数调用图**展开，返回 ({函数名: 深度}, {(文件,函数名): 被调集合})。

    注意：不能按"文件"展开——那会把 API 所在文件里的所有函数都算进来（实测 libredwg
    会从 162 个膨胀到 391 个）。
    """
    callees: dict[tuple, set] = {}
    for cf, cn, cs in edges:
        callees.setdefault((cf, cn), set()).update(cs.split("|"))

    name2: dict[str, dict] = {}
    for m in methods:
        if not m["external"] and m["name"] != "<global>":
            name2.setdefault(m["name"], m)

    seen: dict[str, int] = {}
    cur = {"LLVMFuzzerTestOneInput"}
    for d in range(1, depth + 1):
        nxt = set()
        for nm in cur:
            for (cf, cn), cs in callees.items():
                if cn != nm:
                    continue
                for c in cs:
                    if c.startswith("<operator>") or not re.match(r"^[A-Za-z_]", c):
                        continue
                    if c in seen or c not in name2:
                        continue
                    seen[c] = d
                    nxt.add(c)
        cur = nxt
    return seen, callees


def size_of(root: str, rel: str, start: int, end: int, cache: dict) -> int:
    if rel not in cache:
        p = os.path.join(root, rel)
        if not os.path.isfile(p):
            cache[rel] = None
        else:
            cache[rel] = open(p, encoding="utf-8", errors="replace").read().split("\n")
    lines = cache[rel]
    if lines is None:
        return 0
    return sum(len(x) + 1 for x in lines[max(0, start - 1):end])


def main():
    ap = argparse.ArgumentParser(description="阶段5①：生成静态审计 worklist")
    ap.add_argument("--osv", required=True)
    ap.add_argument("--depth", type=int, default=2,
                    help="从 harness 按调用图展开几层（默认 2：API + 它们的直接被调用者）")
    ap.add_argument("--max-chunk-chars", type=int, default=30000,
                    help="单批字符上限（默认 3 万，约 8k token）")
    ap.add_argument("--functions-per-chunk", type=int, default=1,
                    help="每批几个函数（默认 1：实测一个 agent 只审一个函数才找得到 UAF）")
    ap.add_argument("--no-risk-sort", action="store_true",
                    help="不按风险操作排序（默认把含 free/alloc/mem/index 的排前面，但不排除任何函数）")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    ctxp = os.path.join(OUT, args.osv, "source_context.json")
    if not os.path.exists(ctxp):
        raise SystemExit(f"缺少 {ctxp}（先跑 s5_fetch_source.py {args.osv}）")
    ctx = json.load(open(ctxp, encoding="utf-8"))
    root, commit = ctx.get("repo_local"), ctx.get("commit_used") or ctx.get("pin_commit")
    project = ctx.get("project")
    if not (root and os.path.isdir(root)):
        raise SystemExit(f"仓库不存在: {root}")

    cpg = find_cpg(project, commit)
    if not cpg:
        raise SystemExit(f"找不到 CPG：{CPGDIR}/{project}_{str(commit)[:12]}.cpg\n"
                         f"（若要从当前 commit 新建，先跑 s2a_build_facts.py 让 ensure_cpg 建图）")
    print(f"=== {args.osv} worklist ===")
    print(f"  仓库 : {root} @ {commit}")
    print(f"  CPG  : {os.path.basename(cpg)}")

    cache = os.path.join(OUT, args.osv, "cpg_dump.tsv")
    methods, edges = dump_cpg(cpg, cache)
    print(f"  方法 : {len(methods)} 个（外部 {sum(1 for m in methods if m['external'])}）；调用边 {len(edges)} 条")

    depths, callees = bfs_functions(methods, edges, args.depth)
    print(f"  depth={args.depth} 调用图内用户定义函数: {len(depths)} 个")

    funcs = []
    size_cache = {}
    for name, d in depths.items():
        m = next((x for x in methods if x["name"] == name and not x["external"]), None)
        if not m or m["name"] == "<global>":
            continue
        tags = risk_tags(callees.get((m["file"], name), set()))
        funcs.append({"name": name, "file": m["file"],
                      "lines": [m["start"], m["end"]], "depth": d,
                      "risk": tags,
                      "chars": size_of(root, m["file"], m["start"], m["end"], size_cache)})

    # 排序（不是过滤）：含风险操作的优先，其次深度浅的，再其次大的
    funcs.sort(key=lambda f: (1 if args.no_risk_sort else (0 if f["risk"] else 1),
                              f["depth"], -f["chars"], f["file"], f["lines"][0]))
    n_risk = sum(1 for f in funcs if f["risk"])
    print(f"  入表函数（不过滤，仅排序）: {len(funcs)} 个，其中含风险操作 {n_risk} 个")

    # 打包成批
    per = max(1, args.functions_per_chunk)
    chunks, cur, bufsz = [], [], 0
    for f in funcs:
        if cur and (len(cur) >= per or bufsz + f["chars"] > args.max_chunk_chars):
            chunks.append({"id": len(chunks), "file": cur[0]["file"],
                           "functions": [x["name"] for x in cur], "chars": bufsz})
            cur, bufsz = [], 0
        cur.append(f); bufsz += f["chars"]
    if cur:
        chunks.append({"id": len(chunks), "file": cur[0]["file"],
                       "functions": [x["name"] for x in cur], "chars": bufsz})
    for c in chunks:
        c["lines"] = [min(x["lines"][0] for x in funcs if x["name"] in c["functions"]),
                      max(x["lines"][1] for x in funcs if x["name"] in c["functions"])]

    # 自检：是否覆盖已知崩溃行
    fault_line = ctx.get("fault_line")
    cov = None
    if fault_line:
        cov = any(f["file"].endswith((ctx.get("fault_file") or "#").split("/")[-1]) and
                  f["lines"][0] <= fault_line <= f["lines"][1] for f in funcs)

    out = {"_meta": {"osv_id": args.osv, "project": project, "commit": commit,
                     "cpg": os.path.basename(cpg), "depth": args.depth,
                     "max_chunk_chars": args.max_chunk_chars,
                     "method": "CPG 调用图展开(depth) + 风险标签排序(不排除) + 按函数边界切块（0 LLM）",
                     "functions_per_chunk": args.functions_per_chunk,
                     "harness": ctx.get("fuzz_target"),
                     "fault_line": fault_line, "fault_file": ctx.get("fault_file"),
                     "covers_fault_line": cov},
           "functions": funcs, "chunks": chunks,
           "summary": {"methods_total": len(methods),
                        "functions_in_scope": len(funcs),
                        "functions_with_risk": n_risk,
                        "files_in_scope": len({f["file"] for f in funcs}),
                       "chunks": len(chunks),
                       "chunk_chars": [c["chars"] for c in chunks]}}

    print()
    print(f"  入表函数（不过滤，仅排序）: {len(funcs)} 个，其中含风险操作 {n_risk} 个")
    from collections import Counter
    tagc = Counter(t for f in funcs for t in f["risk"])
    print(f"  标签分布: {dict(tagc)}")
    print(f"  批次: {len(chunks)} 个，字符预算 {args.max_chunk_chars}"
          f"，实际 {[c['chars'] for c in chunks[:8]]}{'…' if len(chunks) > 8 else ''}")
    if fault_line is not None:
        print(f"  自检：已知崩溃行 {ctx.get('fault_file')}:{fault_line} "
              f"{'✅ 已被 worklist 覆盖' if cov else '❌ 未被覆盖（清单不可信！）'}")

    if args.dry_run:
        print("\n  [dry-run] 不写出")
        return
    p = os.path.join(OUT, args.osv, "audit_worklist.json")
    json.dump(out, open(p, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(f"\n  写出 {p}")


if __name__ == "__main__":
    main()

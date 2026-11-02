#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""s5_mutator.py —— 阶段5（算子生成）的统一入口：确定性阶段

本文件包含 5.0 / 5.1 / 5.3 / 5.4 / 5.5 / 5.6 / 5.7 / 5.8 的实现，
以及把 4 个阶段串起来的 CLI。agent 阶段（5.2 系列）在 `s5_agent.py`。

路径基准（脚本内定义，无需环境变量）：

    HERE = mutator_create/pipeline/
    ROOT = mutator_create/          ← artifacts/ outputs/ projects/ cpg_files/
    OUT  = ROOT/projects            ← 单项目工作区

生成的产物全部在 `projects/<OSV>/v2/` 下。
"""
from __future__ import annotations

import argparse, collections, glob, json, os, re, shutil, subprocess, sys, tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
TOP = os.path.dirname(ROOT)
OUT = os.path.join(ROOT, "projects")
if HERE not in sys.path:
    sys.path.insert(0, HERE)

from s5_lib import *                                            # noqa: E402,F401,F403



# ══════════════════════════════════════════════════════════════════════
# 5.0 抓固定版本源码 + harness + 种子（原 s5_fetch_source.py）
# ══════════════════════════════════════════════════════════════════════

"""s5_fetch_source.py —— 阶段 5 的第一步：读崩溃版本的源码，提取生成算子所需的信息。

为什么需要这一步：
  facts 里只有"崩溃在哪一行、free 在哪一行"，但生成变异算子需要知道：
    - 故障函数的完整逻辑（循环、分支、变量赋值）
    - free 的**调用点**（哪一行调用了 free，之后有没有重新赋值）
    - 保护条件（哪些宏/判断会让路径提前返回）
    - 关键判定函数（如 is_dwg_object 的合法名单）

  这些只能从**崩溃版本的源码**里读。

源码从哪来：
  /tmp/opencode/src_local/<slug> 里已有 18 个仓库的完整 .git 对象，
  用 `git show <commit>:<file>` 可取出任意版本的文件，不需要网络。
  未克隆的项目才需要 git clone --filter=blob:none。

用法：
  python3 s5_fetch_source.py <OSV_ID> [<OSV_ID> ...]
  python3 s5_fetch_source.py --all-features   # 对 stage3 里的样本批量处理

产物：
  projects/<OSV_ID>/source_context.json    提取出的语义上下文
  projects/<OSV_ID>/source/<file>.c        故障函数所在文件的完整源码
"""
import json, os, re, subprocess, sys

sys.path.insert(0, HERE)
from s2_lib_cpg import repo_dir, vuln_commit, SRCDIR

REPRO = os.path.join(ROOT, "artifacts", "reproduced_crashes.jsonl")

# 疑似"释放类"函数名（用于找出 free 的调用点）
FREE_HINTS = ("free", "destroy", "release", "delete", "decref", "unref", "dispose", "clear")
# 疑似"保护/判定"宏或函数
GUARD_HINTS = ("RETURN", "CHECK", "GUARD", "ASSERT", "EXPECT")

# fuzz target（harness）的标志符号：定义它的文件就是 harness
HARNESS_MARK = "LLVMFuzzerTestOneInput"


def sh(args, timeout=1800):
    return subprocess.run(args, capture_output=True, text=True, timeout=timeout)


def normalize_path(p):
    """把 ASan 的 /src/<project>/<path> 规范成仓库内相对路径。

    例：/src/libredwg/src/in_dxf.c -> src/in_dxf.c
        /src/fluent-bit/src/x.c    -> src/x.c
        /src/x.c                   -> x.c（无项目目录）
    """
    p = (p or "").replace("/src/", "", 1)
    parts = p.split("/", 2)
    if len(parts) == 3:
        return parts[1] + "/" + parts[2]
    return p


def load_rec(osv):
    for ln in open(REPRO, encoding="utf-8"):
        d = json.loads(ln)
        if d.get("osv_id") == osv:
            return d
    return None


def ensure_repo(repo_url):
    """返回本地仓库目录；若不存在则浅克隆。"""
    rd = repo_dir(repo_url)
    if rd:
        return rd, "local"
    slug = re.sub(r"[^A-Za-z0-9_.-]+", "_",
                  (repo_url or "").replace("https://", "").replace("git://", ""))[:64]
    d = os.path.join("/tmp/opencode/src_local", slug)
    os.makedirs(d, exist_ok=True)
    r = sh(["git", "init", "-q", d])
    r = sh(["git", "-C", d, "remote", "add", "origin", repo_url])
    r = sh(["git", "-C", d, "fetch", "--depth", "1", "origin", "HEAD"], timeout=3600)
    if r.returncode != 0:
        return None, f"clone_failed: {r.stderr[:200]}"
    sh(["git", "-C", d, "checkout", "-q", "FETCH_HEAD"])
    return d, "cloned"


def has_commit(repo, commit):
    r = sh(["git", "-C", repo, "cat-file", "-e", f"{commit}^{{commit}}"])
    return r.returncode == 0


def show_file(repo, commit, path):
    r = sh(["git", "-C", repo, "show", f"{commit}:{path}"])
    return r.stdout if r.returncode == 0 else None


def extract_function(src, fn):
    """按大括号配平，抽出函数体。"""
    # 找到 "fn (" 所在行（可能是返回值单独一行）
    pat = re.compile(r"^\s*" + re.escape(fn) + r"\s*\(", re.M)
    m = pat.search(src)
    if not m:
        return None
    # 向前找到函数签名起始
    start = src.rfind("\n", 0, m.start()) + 1
    # 向后找到第一个 '{'
    i = src.find("{", m.end())
    if i < 0:
        return None
    depth, j = 0, i
    while j < len(src):
        if src[j] == "{":
            depth += 1
        elif src[j] == "}":
            depth -= 1
            if depth == 0:
                break
        j += 1
    return src[start:j + 1]


def extract_macros(src, names):
    """抽出指定宏的定义。"""
    out = {}
    for n in names:
        m = re.search(r"^#define\s+" + re.escape(n) + r".*?(?=^#define|\n\n|\Z)",
                      src, re.M | re.S)
        if m:
            out[n] = m.group(0).rstrip()
    return out


def find_call_sites(func_src, hints=FREE_HINTS, exclude=None):
    """在函数体内找疑似释放/保护类调用；exclude 用于排除函数自身（递归）。"""
    out = []
    for i, line in enumerate(func_src.splitlines(), 1):
        s = line.strip()
        if s.startswith("//") or s.startswith("*"):
            continue
        if exclude and re.search(r"\b" + re.escape(exclude) + r"\s*\(", s):
            continue
        for h in hints:
            if re.search(r"\b\w*" + h + r"\w*\s*\(", s, re.I):
                out.append({"line_in_func": i, "code": s})
                break
    return out


def find_guard_macros(func_src):
    """找函数体里用到的全大写宏（可能是保护条件）。"""
    names = set(re.findall(r"\b([A-Z][A-Z0-9_]{3,})\s*\(", func_src))
    return sorted(n for n in names if any(h in n for h in GUARD_HINTS))


def find_definitions(repo, commit, names, prefer_dirs=("src", "include", "lib")):
    """在仓库里找这些名字的定义文件（用 git grep 限定路径，避免全仓扫描过慢）。"""
    out = {}
    for n in names:
        paths = []
        for d in prefer_dirs:
            r = sh(["git", "-C", repo, "grep", "-l", "-w", "-e", n,
                    commit, "--", f"{d}/*"], timeout=600)
            if r.returncode == 0:
                paths += [ln.split(":", 1)[1] for ln in r.stdout.splitlines() if ":" in ln]
        if not paths:
            r = sh(["git", "-C", repo, "grep", "-l", "-w", "-e", n, commit], timeout=600)
            if r.returncode == 0:
                paths += [ln.split(":", 1)[1] for ln in r.stdout.splitlines() if ":" in ln]
        out[n] = sorted(set(paths))[:3]
    return out


def fetch_harness(repo, commit, outdir, rec):
    """把 fuzz target 的源码（定义 LLVMFuzzerTestOneInput 的文件）拷到 <outdir>/harness/。

    做法：在仓库里 grep 该符号，把所有命中的 C/C++ 文件都取出来（通常 1~3 个：
    harness 本体 + 可选的 standalone 版）。同时标出哪些文件真正含"定义"。
    """
    d = os.path.join(outdir, "harness")
    os.makedirs(d, exist_ok=True)
    r = sh(["git", "-C", repo, "grep", "-l", "-e", HARNESS_MARK, commit], timeout=600)
    paths = sorted({ln.split(":", 1)[1] for ln in (r.stdout or "").splitlines() if ":" in ln})

    files, defs, used = [], [], set()
    for p in paths:
        src = show_file(repo, commit, p)
        if src is None:
            continue
        name = os.path.basename(p)
        if name in used:                      # 同名不同目录 → 用路径扁平化避免覆盖
            name = p.replace("/", "__")
        used.add(name)
        with open(os.path.join(d, name), "w", encoding="utf-8") as fh:
            fh.write(src)
        files.append({"repo_path": p, "saved_as": name, "lines": src.count("\n") + 1})
        # 判定是否含"定义"（函数体），排除 extern 声明
        if re.search(r"LLVMFuzzerTestOneInput\s*\([^;]*\)\s*\{", src):
            defs.append(p)

    return {"dir": "harness", "marker": HARNESS_MARK,
            "files": files, "definition_files": defs,
            "fuzz_target_name": rec.get("fuzz_target")}


def process(osv):
    rec = load_rec(osv)
    if not rec:
        return {"osv_id": osv, "error": "not_in_reproduced_crashes"}

    url = rec.get("repo_url")
    pin = rec.get("pin_commit")
    fault_raw = rec.get("fault_file") or ""
    fault_file = normalize_path(fault_raw)
    fault_fn = rec.get("fault_fn")

    outdir = os.path.join(OUT, osv)
    os.makedirs(os.path.join(outdir, "source"), exist_ok=True)

    ctx = {"osv_id": osv, "project": rec.get("project"), "crash_type": rec.get("crash_type"),
           "repo_url": url, "pin_commit": pin,
           "fault_file": fault_file, "fault_fn": fault_fn,
           "fault_line": rec.get("fault_line"),
           "testcase_size": rec.get("testcase_size")}

    repo, how = ensure_repo(url)
    if not repo:
        ctx["error"] = how
        json.dump(ctx, open(os.path.join(outdir, "source_context.json"), "w"),
                  ensure_ascii=False, indent=1)
        return ctx
    ctx["repo_local"] = repo
    ctx["repo_source"] = how

    commit = pin
    if not commit or not has_commit(repo, commit):
        # 退化：用 HEAD
        r = sh(["git", "-C", repo, "rev-parse", "HEAD"])
        commit = (r.stdout or "").strip()[:12]
        ctx["commit_fallback"] = f"{pin} 不可用，退回 HEAD"
    ctx["commit_used"] = commit

    # 0) 先把 fuzz target 源码拷一份（与故障文件成败无关）
    try:
        ctx["fuzz_target"] = fetch_harness(repo, commit, outdir, rec)
    except Exception as e:                     # noqa: BLE001
        ctx["fuzz_target"] = {"error": f"{type(e).__name__}: {e}"[:200]}

    src = show_file(repo, commit, fault_file)
    if src is None:
        # 兜底：用原始路径再试一次
        alt = fault_raw.replace("/src/", "", 1)
        if alt != fault_file:
            src = show_file(repo, commit, alt)
            if src is not None:
                fault_file = alt
    if src is None:
        ctx["error"] = f"file_not_found: {fault_file} @ {commit}"
        json.dump(ctx, open(os.path.join(outdir, "source_context.json"), "w"),
                  ensure_ascii=False, indent=1)
        return ctx

    with open(os.path.join(outdir, "source", os.path.basename(fault_file)), "w",
              encoding="utf-8") as fh:
        fh.write(src)
    ctx["file_lines"] = src.count("\n") + 1

    # 1) 故障函数
    fn_src = extract_function(src, fault_fn) if fault_fn else None
    if not fn_src:
        ctx["error"] = f"function_not_found: {fault_fn}"
        json.dump(ctx, open(os.path.join(outdir, "source_context.json"), "w"),
                  ensure_ascii=False, indent=1)
        return ctx
    ctx["function_source"] = fn_src
    ctx["function_lines"] = fn_src.count("\n") + 1

    # 2) 函数内的释放类调用点（关键！）
    ctx["free_call_sites"] = find_call_sites(fn_src, FREE_HINTS, exclude=fault_fn)
    ctx["guard_call_sites"] = find_call_sites(fn_src, GUARD_HINTS, exclude=fault_fn)

    # 3) 函数内用到的保护宏
    macro_names = find_guard_macros(fn_src)
    ctx["guard_macros"] = extract_macros(src, macro_names)

    # 4) 所有被调函数（不再按名字前缀过滤）
    #    历史教训：v1 用 ("is_","check","valid","exists","find") 过滤，
    #    结果 dxf_read_pair（定义输入格式）和 dxf_free_pair（UAF 站点）都被漏掉，
    #    只有 is_dwg_object 被抽到（4 个项目内被调函数里漏了 3 个）。
    #    现在的规则：全部取出来，再用 git grep 反查哪些真的在仓库里有定义。
    C_KW = {"if", "while", "for", "switch", "return", "sizeof", "else", "do",
            "case", "goto", "break", "continue", "default"}
    callees = sorted({c for c in re.findall(r"\b([A-Za-z_]\w*)\s*\(", fn_src)
                      if c not in C_KW})
    ctx["callees"] = callees
    ctx["predicate_calls"] = [c for c in callees
                              if any(k in c for k in ("is_", "check", "valid", "exists", "find"))]
    ctx["callee_definitions"] = (find_definitions(repo, commit, callees[:20])
                                 if callees else {})

    # 5) 抽取每个被调函数的源码（截断到 120 行）
    callee_src = {}
    for n, paths in (ctx.get("callee_definitions") or {}).items():
        for pth in paths:
            s2 = show_file(repo, commit, pth)
            if not s2:
                continue
            f2 = extract_function(s2, n)
            if not f2:
                continue
            lines = f2.splitlines()
            callee_src[n] = {
                "file": pth,
                "truncated": len(lines) > 120,
                "source": "\n".join(lines[:120]),
            }
            break
    ctx["callee_source"] = callee_src
    ctx["predicate_source"] = {k: v for k, v in callee_src.items()
                               if k in ctx["predicate_calls"]}

    json.dump(ctx, open(os.path.join(outdir, "source_context.json"), "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)
    return ctx


def main_fetch():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    if "--all-features" in sys.argv:
        f = os.path.join(ROOT, "outputs", "stage4", "uaf", "features.json")
        if os.path.isfile(f):
            d = json.load(open(f, encoding="utf-8"))
            for ft in d.get("features") or []:
                for s in ft.get("source_samples") or []:
                    if s.get("osv_id"):
                        args.append(s["osv_id"])
    if not args:
        print(__doc__)
        return 1

    for osv in args:
        print(f"=== {osv} ===", flush=True)
        try:
            c = process(osv)
        except Exception as e:
            print(f"  FAIL: {e}", flush=True)
            continue
        if c.get("error"):
            print(f"  ✗ {c['error']}", flush=True)
            continue
        print(f"  仓库: {c.get('repo_source')}  提交: {c.get('commit_used')}", flush=True)
        print(f"  函数: {c.get('fault_fn')}  {c.get('function_lines')} 行", flush=True)
        print(f"  free 调用点: {len(c.get('free_call_sites') or [])} 处", flush=True)
        for s in (c.get("free_call_sites") or [])[:5]:
            print(f"    L{s['line_in_func']}: {s['code'][:90]}", flush=True)
        print(f"  保护宏: {list((c.get('guard_macros') or {}).keys())}", flush=True)
        print(f"  判定函数: {c.get('predicate_calls')}", flush=True)
        print(f"  判定函数定义: {json.dumps(c.get('predicate_definitions'), ensure_ascii=False)}", flush=True)
    return 0

# ══════════════════════════════════════════════════════════════════════
# 5.1 调用图 depth≤2 → audit_worklist.json（原 s5a_scan_target.py）
# ══════════════════════════════════════════════════════════════════════

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

import argparse
import json
import os
import re
import subprocess
import sys

CPGDIR = os.path.join(ROOT, "cpg_files")
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


def main_worklist():
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
        raise SystemExit(f"缺少 {ctxp}（先跑 s5_mutator.py fetch --osv {args.osv}）")
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

# ══════════════════════════════════════════════════════════════════════
# 5.3 输入攻击面 + 六步证据链（原 s5_target_surface.py）
# ══════════════════════════════════════════════════════════════════════

"""s5_target_surface.py —— 阶段5.1：抽取 fuzz target 的输入攻击面（**确定性，0 LLM**）

职责边界
  只描述「输入从 harness 怎么进来、能到哪些函数、哪些函数在解析输入、哪里有内存操作」。
  **不判断漏洞**，也不声称「某个字段一定控制某条分支」——那属于 candidate/feature/plan 层。

产出
  v2/target_surface.json（schema: stage5.target_surface.v1）

`field_mapping_complete` 的判据（4 条全部满足才算 complete）
  ① 输入格式已知（line_record / binary_record / raw_bytes）
  ② 至少有一个 field 带 locator（record_sequence + anchor 即可，不要求字节偏移）
  ③ 从 harness 到故障函数存在一条**每跳都有源码证据**的路径
  ④ 该路径上没有 unknown 跳

  这四条都可以由程序判定，不靠人工拍板。

用法
  python3 s5_target_surface.py --osv ARVO-42494732
  python3 s5_target_surface.py --osv ARVO-42494732 --selftest   # 只跑证据链自检
"""

import argparse
import json
import os
import re
import sys



ENTRY = "LLVMFuzzerTestOneInput"

# 解析类函数的命名线索（只用于"候选"，不是结论）
PARSER_RX = re.compile(r"(read|parse|decode|load|scan|unpack|deserial|ingest)", re.I)
# 内存操作 / sink 线索
SINK_RX = re.compile(r"\b(free|destroy|release|malloc|calloc|realloc|memcpy|memmove|memset"
                     r"|strcpy|strcat|strlen|sprintf)\s*\(", re.I)

# 记录的格式线索：形如 "  0\r\nSECTION\r\n"
DXF_RECORD_RX = re.compile(rb"^\s*(\d{1,3})\r?\n", re.M)


# ────────────────────────── 读取输入 ──────────────────────────

def load_json(p):
    return json.load(open(p, encoding="utf-8"))


def read_lines(p):
    return open(p, encoding="utf-8", errors="replace").read().split("\n")


def read_cpg_dump(p):
    methods, edges = [], []
    for ln in open(p, encoding="utf-8"):
        t = ln.rstrip("\n").split("\t")
        if t[0] == "@@M" and len(t) >= 6:
            methods.append({"file": t[1], "name": t[2], "start": int(t[3] or 0),
                            "end": int(t[4] or 0), "external": t[5] == "1"})
        elif t[0] == "@@C" and len(t) >= 4:
            edges.append((t[1], t[2], t[3]))
    return methods, edges


# ────────────────────────── 抽取 ──────────────────────────

def extract_entry(harness_src: str) -> dict:
    """从 harness 源码里取入口函数名、参数名、直接调用。"""
    m = re.search(rf"\b{ENTRY}\s*\(([^)]*)\)", harness_src)
    params = []
    if m:
        parts = [p.strip() for p in m.group(1).split(",") if p.strip()]
        for p in parts:
            ids = re.findall(r"[A-Za-z_]\w*", p)
            params.append(ids[-1] if ids else p)
    body = harness_src[m.start():] if m else ""
    calls = sorted({c for c in re.findall(r"\b([A-Za-z_]\w*)\s*\(", body)
                    if c not in {"if", "for", "while", "switch", "return", "sizeof",
                                 "else", "do", "case", "break", "continue", ENTRY}})
    return {"entry_symbol": ENTRY,
            "parameters": params,
            "input_parameter": params[0] if params else None,
            "input_length_parameter": params[1] if len(params) > 1 else None,
            "direct_calls": calls}


def direct_callees(edges, entry_name: str) -> set[str]:
    out = set()
    for cf, cn, cs in edges:
        if cn == entry_name:
            out |= {c for c in cs.split("|")
                    if re.match(r"^[A-Za-z_]", c) and not c.startswith("<operator>")}
    return out


def detect_format(seed: bytes) -> dict:
    """按字节特征粗判输入格式。只判大类，不解析字段。"""
    if not seed:
        return {"format": "raw_bytes", "evidence": "no seed"}
    if DXF_RECORD_RX.search(seed[:4096]):
        codes = [int(x) for x in DXF_RECORD_RX.findall(seed[:20000])]
        return {"format": "line_record",
                "evidence": f"前 4KB 内出现 {len(DXF_RECORD_RX.findall(seed[:4096]))} 次 '^<数字>\\n' 记录头",
                "record_header_rx": r"^\s*(\d{1,3})\r?\n",
                "group_codes_seen": sorted(set(codes))[:40],
                "group_code_count": len(set(codes))}
    printable = sum(1 for b in seed[:2048] if 32 <= b < 127 or b in (9, 10, 13))
    if printable / max(1, min(len(seed), 2048)) > 0.9:
        return {"format": "line_record", "evidence": "前 2KB >90% 可打印字符", "group_codes_seen": []}
    return {"format": "binary_record", "evidence": "非文本特征", "group_codes_seen": []}


def find_parser_candidates(reachable: list[dict], src_cache: dict, input_names: list[str]) -> list[dict]:
    """在可达函数里找"可能在解析输入"的函数：命名线索 + 源码里引用了输入缓冲。"""
    out = []
    for f in reachable:
        lines = src_cache.get(f["file"])
        if not lines:
            continue
        lo, hi = f["lines"][0] - 1, min(f["lines"][1], len(lines))
        body = "\n".join(lines[lo:hi])
        hits = []
        for pat in (r"->chain\b", r"->byte\b", r"->size\b", r"->opts\b"):
            for i in range(lo, hi):
                if re.search(pat, lines[i]):
                    hits.append([i + 1, lines[i].strip()[:160]])
                    break
        name_hit = bool(PARSER_RX.search(f["name"]))
        if not (name_hit or hits):
            continue
        out.append({
            "function": f["name"], "file": f["file"], "lines": f["lines"],
            "depth": f["depth"],
            "role": ("entry_api" if f["depth"] == 1 else "record_parser" if name_hit else "helper"),
            "input_expressions": sorted({h[1].split("->")[1].split()[0] for h in hits
                                         if "->" in h[1]})[:6],
            "evidence_lines": hits[:3],
            "confidence": "medium" if (name_hit and hits) else "low",
        })
    return out


def find_sinks(reachable: list[dict], src_cache: dict) -> list[dict]:
    out = []
    for f in reachable:
        lines = src_cache.get(f["file"])
        if not lines:
            continue
        lo, hi = f["lines"][0] - 1, min(f["lines"][1], len(lines))
        hits = []
        for i in range(lo, hi):
            m = SINK_RX.search(lines[i])
            if m:
                hits.append({"line": i + 1, "call": m.group(1).lower(),
                             "code": lines[i].strip()[:160]})
            if len(hits) >= 6:
                break
        if hits:
            out.append({"function": f["name"], "file": f["file"], "lines": f["lines"],
                        "kinds": sorted({h["call"] for h in hits}),
                        "evidence_lines": hits[:4]})
    return out



def fault_flow_evidence(src_cache, fault, fault_range=None):
    """在**故障函数自己的行范围**内找两类证据：字段写入局部变量、分支判据。

    ⚠ 必须限定在函数范围内。libredwg 里 `dxf_entities_read`(12205-12240) 和
    `dxf_objects_read`(12261-12293) 几乎是同一段代码的复制，用 ±80 行窗口会跨到
    前一个函数，取到错误证据。
    """
    rel = None
    for f, lines in src_cache.items():
        if lines and fault.get("file") and f.endswith(fault["file"]):
            rel = f
            break
    if not rel or not fault.get("line"):
        return [], []
    lines = src_cache[rel]
    if fault_range:
        lo, hi = max(0, fault_range[0] - 1), min(len(lines), fault_range[1])
    else:
        lo = max(0, fault["line"] - 80)
        hi = min(len(lines), fault["line"] + 40)
    field_ev, branch_ev = [], []
    for i in range(lo, hi):
        t = lines[i].strip()
        if re.search(r"\b(strncpy|memcpy|strdup)\s*\(", t) or re.search(r"=\s*\w+->(value|chain|string|name)\b", t):
            field_ev.append([i + 1, t[:160]])
        if re.match(r"^(if|while|for)\s*\(", t):
            branch_ev.append([i + 1, t[:160]])
        if len(field_ev) >= 4 and len(branch_ev) >= 6:
            break
    return field_ev, branch_ev


FREE_CALL_RX = re.compile(r"\b([A-Za-z_]\w*)\s*\(\s*&?\s*([A-Za-z_]\w*)\s*\)\s*;")


def step6_flow_evidence(src_cache, fault, fault_range):
    """用 flow 证明「释放后控制流能回到解引用同一变量的行」。

    这是 §8.1 第 6 步。做法：
      · 在故障函数里找"释放类调用 W(v)"
      · 从该行开始走控制流
      · 若轨迹里出现回边⟲，且回边之后的某行仍解引用 v（v-> / v. / v[）
        → 说明下一轮迭代会读到已释放内存 → complete
    """
    rel = next((f for f, ls in src_cache.items()
                if ls and fault.get("file") and f.endswith(fault["file"])), None)
    if not rel or not fault_range:
        return None
    lines = src_cache[rel]
    lo, hi = max(0, fault_range[0] - 1), min(len(lines), fault_range[1] - 1)
    for i in range(lo, hi + 1):
        m = FREE_CALL_RX.search(strip_code(lines[i]))
        if not m:
            continue
        callee, var = m.group(1), m.group(2)
        if not re.search(r"(free|destroy|release)", callee, re.I):
            continue
        trace = flow(lines, lo, hi, i, 20)
        bi = next((k for k, t in enumerate(trace) if t["back_edge"]), None)
        if bi is None:
            continue
        deref = re.compile(rf"\b{re.escape(var)}\b\s*(->|\.|\[)")
        for t in trace[bi:]:
            if deref.search(strip_code(lines[t["line"]])):
                return {"free_line": i + 1, "free_code": lines[i].strip()[:160],
                        "back_edge_to": trace[bi]["next"] + 1 if trace[bi]["next"] is not None else None,
                        "deref_line": t["line"] + 1,
                        "deref_code": lines[t["line"]].strip()[:160],
                        "variable": var, "callee": callee}
    return None


def step5_predicate_evidence(src_cache, fault, fault_range, free_line):
    """证明「释放发生在哪个 else 分支、由哪个 if 条件决定」。

    做法：用块结构找到 free_line 所在的 else 块，再找紧挨它前面的 if 块，
    取出 if 的条件原文。
    """
    rel = next((f for f, ls in src_cache.items()
                if ls and fault.get("file") and f.endswith(fault["file"])), None)
    if not rel or not fault_range:
        return None
    lines = src_cache[rel]
    lo, hi = max(0, fault_range[0] - 1), min(len(lines), fault_range[1] - 1)
    fl = free_line - 1
    blks = blocks(lines, lo, hi)
    encl = [b for b in blks if b["open"] <= fl <= b["close"]]
    else_blk = next((b for b in encl if b["kind"] == "else"), None)
    if not else_blk:
        return None
    if_blk = next((b for b in blks if b["kind"] == "if"
                   and b["close"] + 1 == else_blk["header"]), None)
    if not if_blk:
        return None
    return {"if_line": if_blk["header"] + 1,
            "if_code": lines[if_blk["header"]].strip()[:160],
            "else_line": else_blk["header"] + 1,
            "else_code": lines[else_blk["header"]].strip()[:160],
            "free_line": free_line}

def evidence_chain(harness: dict, reachable: list[dict], parsers: list[dict],
                   sinks: list[dict], fault: dict, src_cache: dict) -> list[dict]:
    """§8.1 的六步证据链，每步给出 status（complete / partial / unknown）与证据。"""
    steps = []
    steps_meta = {}

    def add(step, question, status, evidence, note=""):
        steps.append({"step": step, "question": question, "status": status,
                      "evidence": evidence, "note": note})

    add(1, "LLVMFuzzerTestOneInput(data,size) 如何构造解析上下文",
        "complete" if harness.get("parameters") else "unknown",
        [f"entry={harness['entry_symbol']} params={harness['parameters']}"])

    add(2, "输入缓冲区如何绑定到解析器读取的结构",
        "complete" if any(p["input_expressions"] for p in parsers) else "unknown",
        [list(e) if isinstance(e, (list, tuple)) else [e.get("line"), e.get("code")]
         for p in parsers[:1] for e in (p.get("evidence_lines") or [])])

    feat = [p for p in parsers if p["function"] == fault.get("function")]
    rp = [p for p in parsers if p.get("role") == "record_parser"]
    add(3, "解析器把输入记录转成内部结构",
        "complete" if rp else "unknown",
        [[p["function"], p["file"], p["lines"][0]] for p in rp[:4]])

    fr = next((f["lines"] for f in reachable if f["name"] == fault.get("function")), None)
    if fr:
        steps_meta["fault_function_range"] = fr
    f6 = step6_flow_evidence(src_cache, fault, fr)
    field_ev, branch_ev = fault_flow_evidence(src_cache, fault, fr)
    add(4, "输入的哪个字段进入目标变量",
        "complete" if field_ev else "partial", field_ev,
        "找到『字段写入局部变量』的语句即算闭合" if field_ev else "故障函数里没有字段写入语句")

    f5 = step5_predicate_evidence(src_cache, fault, fr, f6["free_line"]) if f6 else None
    if f5:
        add(5, "目标函数的判据如何决定分支", "complete",
            [[f5["if_line"], f5["if_code"]], [f5["else_line"], f5["else_code"]]],
            f"L{f5['free_line']} 的释放位于 L{f5['else_line']} 的 else 分支，"
            f"该分支由 L{f5['if_line']} 的 `{f5['if_code']}` 决定")
        steps_meta["step5_predicate"] = f5
    else:
        add(5, "目标函数的判据如何决定分支",
            "partial" if branch_ev else "unknown", branch_ev,
            "只列出了分支条件，未能把释放点绑定到具体的 if/else" if branch_ev else "")

    if f6:
        add(6, "后续记录如何让控制流再次读到目标变量", "complete",
            [[f6["free_line"], f6["free_code"]], [f6["deref_line"], f6["deref_code"]]],
            f"flow 证明：L{f6['free_line']} 释放 `{f6['variable']}` 后经回边⟲回到 "
            f"L{f6['back_edge_to']}，再在 L{f6['deref_line']} 解引用它")
        steps_meta["step6_flow"] = f6
    else:
        add(6, "后续记录如何让控制流再次读到目标变量", "unknown", [],
            'flow 未发现「释放类调用 → 回边 → 解引用同一变量」的路径')

    return steps


# ────────────────────────── 主流程 ──────────────────────────

def main_surface():
    ap = argparse.ArgumentParser(description="阶段5.1：抽取 target surface（0 LLM）")
    ap.add_argument("--osv", required=True)
    ap.add_argument("--seed", default=None, help="用于格式判定的种子（默认取 seeds/ 第一个）")
    ap.add_argument("--selftest", action="store_true", help="只打印证据链自检")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    S5 = os.path.join(OUT, args.osv)
    for need in ("source_context.json", "audit_worklist.json", "cpg_dump.tsv"):
        if not os.path.exists(os.path.join(S5, need)):
            raise SystemExit(f"缺少 {S5}/{need}")

    ctx = load_json(os.path.join(S5, "source_context.json"))
    wl = load_json(os.path.join(S5, "audit_worklist.json"))
    root = ctx["repo_local"]
    methods, edges = read_cpg_dump(os.path.join(S5, "cpg_dump.tsv"))

    hdir = os.path.join(S5, "harness")
    hsrc = {}
    if os.path.isdir(hdir):
        for fn in sorted(os.listdir(hdir)):
            if fn.endswith((".c", ".cc", ".cpp")):
                hsrc[fn] = open(os.path.join(hdir, fn), encoding="utf-8", errors="replace").read()
    # 挑真正定义入口的 harness（可能是 dwgfuzz.c 或 llvmfuzz.c）
    harness, harness_file = {"entry_symbol": ENTRY, "parameters": [],
                             "input_parameter": None, "input_length_parameter": None,
                             "direct_calls": []}, None
    for fn, txt in hsrc.items():
        h = extract_entry(txt)
        if h["parameters"] and len(h["parameters"]) >= len(harness["parameters"]):
            harness, harness_file = h, fn

    reachable = wl["functions"]
    src_cache = {}
    for f in reachable:
        if f["file"] not in src_cache:
            p = os.path.join(root, f["file"])
            src_cache[f["file"]] = read_lines(p) if os.path.isfile(p) else None

    parsers = find_parser_candidates(reachable, src_cache, harness["parameters"])
    sinks = find_sinks(reachable, src_cache)

    # 输入格式：从种子判定
    seeddir = os.path.join(S5, "seeds")
    seedp = args.seed
    if not seedp and os.path.isdir(seeddir):
        # 只认 .dxf 文件：seeds/ 下还有 _fuzzer_corpus/ 等目录和 .dwg 种子
        cands = [f for f in sorted(os.listdir(seeddir))
                 if f.endswith(".dxf") and os.path.isfile(os.path.join(seeddir, f))]
        seedp = os.path.join(seeddir, cands[0]) if cands else None
    fmt = detect_format(open(seedp, "rb").read() if seedp and os.path.isfile(seedp) else b"")

    # field：line_record 下把"出现过的组码"当成候选字段（locator 是记录序列，不是字节偏移）
    fields = []
    for code in fmt.get("group_codes_seen", [])[:20]:
        fields.append({
            "field_id": f"record.group_code.{code}",
            "format": fmt["format"],
            "anchor": f"记录头组码 {code}",
            "value_kind": "the next line after this code",
            "locator": {"kind": "record_sequence", "anchor": str(code),
                        "regex": fmt.get("record_header_rx")},
            "source_path": [],
            "controls": [],
            "confidence": "unknown",
        })

    fault = {"file": (ctx.get("fault_file") or "").split("/")[-1],
             "line": ctx.get("fault_line"), "function": ctx.get("fault_fn")}
    chain = evidence_chain(harness, reachable, parsers, sinks, fault, src_cache)

    # 四条判据
    c1 = fmt["format"] in ("line_record", "binary_record", "raw_bytes")
    c2 = bool(fields) and all(f.get("locator") for f in fields)
    c3 = all(s["status"] in ("complete",) for s in chain[:5])
    c4 = not any(s["status"] == "unknown" for s in chain[:5])
    complete = bool(c1 and c2 and c3 and c4)

    unknowns = []
    for s in chain:
        if s["status"] != "complete":
            unknowns.append({"area": f"evidence_chain.step{s['step']}",
                             "question": s["question"], "status": s["status"],
                             "note": s.get("note") or ""})
    if not parsers:
        unknowns.append({"area": "parsers", "question": "未识别到解析输入的函数", "status": "unknown"})

    surface = {
        "schema_version": "stage5.target_surface.v1",
        "target": {"osv_id": args.osv, "project": ctx.get("project"),
                   "commit": ctx.get("commit_used") or ctx.get("pin_commit"),
                   "harness": ctx.get("fuzz_target"),
                   "crash_type": ctx.get("crash_type"),
                   "fault_function": ctx.get("fault_fn"),
                   "fault_file": (ctx.get("fault_file") or "").split("/")[-1],
                   "fault_line": ctx.get("fault_line"),
                   "entry_symbol": harness["entry_symbol"],
                   "input_parameter": harness["input_parameter"],
                   "input_length_parameter": harness["input_length_parameter"]},
        "call_surface": {
            "direct_calls": sorted(direct_callees(edges, ENTRY)),
            "reachable_functions": [f["name"] for f in reachable],
            "reachable_files": sorted({f["file"] for f in reachable}),
            "depth": wl["_meta"]["depth"],
            "source": "joern_cpg",
        },
        "input_format": fmt,
        "parsers": parsers,
        "fields": fields,
        "conditions": [],
        "sinks": sinks,
        "evidence_chain": chain,
        "unknowns": unknowns,
        "validation": {
            "fixed_commit": bool(surface_commit_ok(ctx)),
            "source_files_present": all(os.path.isfile(os.path.join(root, f)) for f in
                                        {x["file"] for x in reachable}),
            "harness_present": bool(hsrc),
            "cpg_present": True,
            "criteria": {"format_known": c1, "locator_present": c2,
                         "chain_all_complete": c3, "no_unknown_hop": c4},
            "field_mapping_complete": complete,
        },
    }

    if args.selftest or args.dry_run:
        print(f"=== {args.osv} target surface 自检 ===")
        for s in chain:
            print(f"  step{s['step']} [{s['status']:<8}] {s['question']}")
            for e in s["evidence"][:2]:
                print(f"           {e}")
        print(f"\n  判据: {surface['validation']['criteria']}")
        print(f"  field_mapping_complete = {complete}")
        if args.selftest:
            return

    p = os.path.join(S5, "v2", "target_surface.json")
    os.makedirs(os.path.dirname(p), exist_ok=True)
    json.dump(surface, open(p, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(f"\n  写出 {p}")
    print(f"  格式={fmt['format']}  解析器候选={len(parsers)}  sink 函数={len(sinks)}")
    print(f"  字段候选={len(fields)}（组码 {len(fmt.get('group_codes_seen', []))} 个）")
    print(f"  field_mapping_complete = {complete}  （判据 {surface['validation']['criteria']}）")
    print(f"  unknowns = {len(unknowns)} 条")


def surface_commit_ok(ctx):
    c = ctx.get("commit_used") or ctx.get("pin_commit")
    return bool(c) and len(str(c)) >= 7

# ══════════════════════════════════════════════════════════════════════
# 5.4 多路候选合并 / 证据核验 / 去重（原 s5_candidate_findings.py）
# ══════════════════════════════════════════════════════════════════════

"""s5_candidate_findings.py —— 阶段5.2：把多路候选合并成统一的 findings（**0 LLM**）

职责
  把「agent 审计候选」「机械规则假设」「facts / interpretation」合成一份带来源、带证据状态、
  带去重、带可达性关系的清单。它**不判断漏洞真假**，只负责：
    · 统一漏洞族（family）
    · 重新核对证据行（行号存在 + 原文是该行子串）
    · 去重（同族 + 同文件 + 同函数 + **证据行有交集**）
    · 计算 call_surface_relation（direct / reachable / outside / unknown）
    · 计算 fault_relation（same_site / same_function / same_file / same_family_only / unrelated）
    · 计算 input_reachability（complete / partial / unknown）

为什么去重键不是「证据行集合相等」
  agent 给的证据行通常是 [12284, 12286, 12267, 12269]，机械假设是 [12284, 12267]。
  集合不相等，但显然说的是同一件事。所以用「有交集」而不是「相等」。

用法
  python3 s5_candidate_findings.py --osv ARVO-42494732
  python3 s5_candidate_findings.py --osv ARVO-42494732 --selftest
"""

import argparse
import glob
import json
import os
import re
import sys


# 漏洞族 ontology（保留原始类型，只做归一化）
FAMILY = {
    "use-after-free": "lifetime", "double-free": "lifetime", "invalid-free": "lifetime",
    "heap-buffer-overflow": "bounds", "stack-buffer-overflow": "bounds",
    "global-buffer-overflow": "bounds", "out-of-bounds-read": "bounds",
    "out-of-bounds-write": "bounds", "container-overflow": "bounds",
    "use-of-uninitialized-value": "initialization",
    "integer-overflow": "arithmetic-to-memory",
    "null-deref": "control/resource",
}

CRASH_FAMILY = {
    "heap-use-after-free": "lifetime", "heap-double-free": "lifetime",
    "invalid-free": "lifetime", "heap-buffer-overflow": "bounds",
    "stack-buffer-overflow": "bounds", "global-buffer-overflow": "bounds",
    "use-of-uninitialized-value": "initialization",
    "negative-size-param": "arithmetic-to-memory",
    "segv-on-unknown-address": "control/resource",
    "null-dereference": "control/resource",
}


def family_of(vuln_type: str) -> str:
    t = (vuln_type or "").lower()
    if t in FAMILY:
        return FAMILY[t]
    for k, v in FAMILY.items():
        if k in t:
            return v
    return "unknown"



def resolve_file(source_root: str, files, function: str, cache: dict) -> str:
    """候选没带文件时，按函数名在可达文件里反查（只匹配 "name(" 出现）。"""
    if not function:
        return ""
    key = (function, tuple(files or ()))
    if key in cache:
        return cache[key]
    rx = re.compile(rf"\b{re.escape(function)}\s*\(")
    for rel in files or ():
        p = os.path.join(source_root, rel)
        if not os.path.isfile(p):
            continue
        try:
            if rx.search(open(p, encoding="utf-8", errors="replace").read()):
                cache[key] = rel
                return rel
        except OSError:
            pass
    cache[key] = ""
    return ""

def as_candidate_list(report) -> list[dict]:
    """兼容三种输入：{"candidates":[...]} / [ {...}, {...} ] / None。"""
    if not report:
        return []
    if isinstance(report, list):
        out = []
        for r in report:
            out.extend(r.get("candidates") or [] if isinstance(r, dict) else [])
        return out
    return report.get("candidates") or []



def _norm_ev(ev) -> list:
    """把证据行统一成 [int, str]（LLM 会返回字符串行号）。"""
    out = []
    for e in ev or []:
        if not (isinstance(e, (list, tuple)) and len(e) >= 2):
            continue
        try:
            out.append([int(e[0]), str(e[1])])
        except (TypeError, ValueError):
            continue
    return out

def verify_evidence_findings(root: str, rel: str, evidence) -> tuple[bool, list[int], list[str]]:
    """核对证据行：行号合法且原文（去空白）是该行子串。"""
    full = os.path.join(root, rel) if rel else None
    if not full or not os.path.isfile(full):
        return False, [], ["file_missing"]
    lines = open(full, encoding="utf-8", errors="replace").read().split("\n")
    ok, bad = [], []
    for ev in evidence or []:
        if not (isinstance(ev, (list, tuple)) and len(ev) >= 2):
            bad.append(str(ev)[:80]); continue
        try:
            ln = int(ev[0])
        except (TypeError, ValueError):
            bad.append(str(ev)[:80]); continue
        if not (1 <= ln <= len(lines)):
            bad.append(f"L{ln} 越界"); continue
        claim = "".join(str(ev[1]).split())
        if claim and claim in "".join(lines[ln - 1].split()):
            ok.append(ln)
        else:
            bad.append(f"L{ln} 原文不符")
    return (bool(ok) and not bad), ok, bad


def all_lines(f: dict) -> set[int]:
    s = set()
    for x in f.get("lines") or []:
        try:
            s.add(int(x))
        except (TypeError, ValueError):
            pass
    for ev in f.get("evidence_lines") or []:
        try:
            s.add(int(ev[0]))
        except (TypeError, ValueError, IndexError):
            pass
    return s


def normalize_findings(audit_report, mech_report, facts, interpretation,
                       target_surface, source_root) -> dict:
    """把多路候选规范化、核验、去重、加关系。"""
    aud = as_candidate_list(audit_report)
    mech = (mech_report or {}).get("hypotheses") or []

    surface = target_surface or {}
    cs = surface.get("call_surface") or {}
    reachable = set(cs.get("reachable_functions") or [])
    direct = set(cs.get("direct_calls") or [])
    fm_complete = bool((surface.get("validation") or {}).get("field_mapping_complete"))

    tgt = surface.get("target") or {}
    cs_site = ((facts or {}).get("crash") or {}).get("site") or {}
    fault_fn = ((facts or {}).get("fault_fn") or cs_site.get("fn")
                or tgt.get("fault_function"))
    fault_line = ((facts or {}).get("fault_line") or cs_site.get("line")
                  or tgt.get("fault_line"))
    fault_file = ((facts or {}).get("fault_file") or cs_site.get("file")
                  or tgt.get("fault_file"))
    if isinstance(fault_file, str):
        fault_file = fault_file.split("/")[-1]
    crash_type = ((facts or {}).get("crash_type") or tgt.get("crash_type"))
    cfam = CRASH_FAMILY.get((crash_type or "").lower()) or family_of(crash_type)

    files = cs.get("reachable_files") or []
    fcache: dict = {}
    raws = []
    for c in aud:
        raws.append({"src": "audit", "raw": c,
                     "file": (c.get("_file") or c.get("file")
                              or resolve_file(source_root, files, c.get("function") or "", fcache)),
                     "function": c.get("function") or "",
                     "vuln_type": c.get("vuln_type") or "other",
                     "mechanism": c.get("mechanism") or "",
                     "evidence": c.get("evidence_lines") or [],
                     "confidence": c.get("confidence") or "low",
                     "why": c.get("why_unverified") or ""})
    for h in mech:
        raws.append({"src": "mech", "raw": h,
                     "file": h.get("file") or "",
                     "function": h.get("function") or "",
                     "vuln_type": h.get("vuln_type") or "use-after-free",
                     "mechanism": h.get("mechanism") or "",
                     "evidence": h.get("evidence_lines") or [],
                     "confidence": "low",
                     "why": "机械规则只证明代码形状，未证明输入可达"})

    out = []
    for r in raws:
        fam = family_of(r["vuln_type"])
        ok, ok_lines, bad = verify_evidence_findings(source_root, r["file"], r["evidence"])
        f = {
            "vuln_family": fam,
            "original_types": [r["vuln_type"]],
            "mechanism": r["mechanism"],
            "file": r["file"],
            "function": r["function"],
            "lines": sorted({int(x) for x in (r["raw"].get("lines") or [])
                             if str(x).lstrip("-").isdigit()}),
            "evidence_lines": _norm_ev(r["evidence"]),
            "evidence_ok": ok,
            "evidence_ok_lines": ok_lines,
            "evidence_bad": bad,
            "sources": [r["src"]],
            "raw": r["raw"],
            "confidence": r["confidence"],
            "why_unverified": r["why"],
        }
        f["call_surface_relation"] = (
            "direct" if r["function"] in direct else
            "reachable" if r["function"] in reachable else
            "outside" if reachable else "unknown")

        lines = all_lines(f)
        if fault_line and fault_fn and r["function"] == fault_fn and int(fault_line) in lines:
            f["fault_relation"] = "same_site"
        elif fault_fn and r["function"] == fault_fn:
            f["fault_relation"] = "same_function"
        elif fault_file and r["file"].endswith(fault_file):
            f["fault_relation"] = "same_file"
        elif fam == cfam:
            f["fault_relation"] = "same_family_only"
        else:
            f["fault_relation"] = "unrelated"

        # 输入可达性：只有"同一个故障函数"且整体映射闭合时才算 complete
        if not ok:
            f["input_reachability"] = {"status": "unknown", "missing": ["证据行未通过核对"]}
        elif fm_complete and f["fault_relation"] in ("same_site", "same_function"):
            f["input_reachability"] = {
                "status": "complete", "field_ids": [x.get("field_id") for x
                                                    in (surface.get("fields") or [])[:3]],
                "path_evidence": [s.get("evidence") for s in
                                  (surface.get("evidence_chain") or [])
                                  if s.get("status") == "complete"][:3], "missing": []}
        else:
            f["input_reachability"] = {
                "status": "partial", "missing": ["候选函数到输入的完整路径未建立"]}

        f["status"] = ("rejected" if not ok else
                       "unverified")
        out.append(f)

    # ── 去重：同族 + 同文件 + 同函数 + 证据行有交集 ──
    merged: list[dict] = []
    for f in out:
        hit = None
        for m in merged:
            same_file = (m["file"] == f["file"]) or not m["file"] or not f["file"]
            if (m["vuln_family"] == f["vuln_family"] and same_file
                    and m["function"] == f["function"]
                    and (all_lines(m) & all_lines(f))):
                hit = m
                break
        if hit:
            hit["sources"] = sorted(set(hit["sources"]) | set(f["sources"]))
            hit["original_types"] = sorted(set(hit["original_types"]) | set(f["original_types"]))
            hit["evidence_lines"] = sorted(hit["evidence_lines"] + f["evidence_lines"],
                                           key=lambda e: e[0])
            if not hit["file"]:
                hit["file"] = f["file"]
            # 合并时取"更精确"的故障关系，并取行号并集
            order = {"same_site": 0, "same_function": 1, "same_file": 2,
                     "same_family_only": 3, "unrelated": 4}
            if order[f["fault_relation"]] < order[hit["fault_relation"]]:
                hit["fault_relation"] = f["fault_relation"]
            hit["lines"] = sorted(set(hit.get("lines") or []) | set(f.get("lines") or []))
            hit["evidence_ok_lines"] = sorted(set(hit.get("evidence_ok_lines") or [])
                                              | set(f.get("evidence_ok_lines") or []))
            hit["evidence_ok"] = hit["evidence_ok"] or f["evidence_ok"]
            hit["confidence"] = ("high" if "high" in (hit["confidence"], f["confidence"])
                                 else hit["confidence"])
            if f["evidence_ok"] and not hit["evidence_ok_lines"]:
                hit["evidence_ok_lines"] = f["evidence_ok_lines"]
        else:
            merged.append(f)

    merged.sort(key=lambda x: (x["status"] == "rejected",
                               x["input_reachability"]["status"] != "complete",
                               {"same_site": 0, "same_function": 1, "same_file": 2,
                                "same_family_only": 3, "unrelated": 4}[x["fault_relation"]]))
    for i, f in enumerate(merged, 1):
        f["finding_id"] = f"c{i:03d}"
        f.pop("raw", None)

    return {
        "schema_version": "stage5.candidate_findings.v1",
        "target": {"osv_id": tgt.get("osv_id"), "commit": tgt.get("commit"),
                   "crash_type": crash_type, "fault_function": fault_fn,
                   "fault_line": fault_line, "fault_file": fault_file},
        "findings": merged,
        "rejected": [f for f in merged if f["status"] == "rejected"],
        "unknowns": [{"finding_id": f["finding_id"], "missing": f["input_reachability"]["missing"]}
                     for f in merged if f["input_reachability"]["status"] != "complete"],
        "summary": {
            "from_audit": len(aud), "from_mech": len(mech),
            "after_dedup": len(merged),
            "merged": len(out) - len(merged),
            "evidence_ok": sum(1 for f in merged if f["evidence_ok"]),
            "input_complete": sum(1 for f in merged
                                  if f["input_reachability"]["status"] == "complete"),
            "by_family": _count(f["vuln_family"] for f in merged),
            "by_fault_relation": _count(f["fault_relation"] for f in merged),
            "by_call_surface": _count(f["call_surface_relation"] for f in merged),
        },
    }


def _count(it):
    from collections import Counter
    return dict(Counter(it))


def main_findings():
    ap = argparse.ArgumentParser(description="阶段5.2：合并候选 findings（0 LLM）")
    ap.add_argument("--osv", required=True)
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    S5 = os.path.join(OUT, args.osv)
    V2 = os.path.join(S5, "v2")
    need = ["target_surface.json"]
    for n in need:
        if not os.path.exists(os.path.join(V2, n)):
            raise SystemExit(f"缺少 {V2}/{n}（先跑 s5_mutator.py surface --osv <OSV>）")
    surface = json.load(open(os.path.join(V2, "target_surface.json"), encoding="utf-8"))
    root = json.load(open(os.path.join(S5, "source_context.json"), encoding="utf-8"))["repo_local"]

    # 审计候选：优先 audit_chunks/*.json，退回 vuln_report.json
    chunk_files = sorted(glob.glob(os.path.join(S5, "audit_chunks", "*.json")))
    if chunk_files:
        audit = [json.load(open(p, encoding="utf-8")) for p in chunk_files]
        audit_src = f"audit_chunks/*.json（{len(chunk_files)} 批）"
    else:
        audit = json.load(open(os.path.join(S5, "vuln_report.json"), encoding="utf-8"))
        audit_src = "vuln_report.json"

    mechp = os.path.join(S5, "mech_hypotheses.json")
    mech = json.load(open(mechp, encoding="utf-8")) if os.path.exists(mechp) else {"hypotheses": []}

    facts = _load_or_none(os.path.join(ROOT, "artifacts", "facts", args.osv, "facts.json"))
    interp = _load_or_none(os.path.join(ROOT, "artifacts", "interpretation", args.osv,
                                        "interpretation.json"))

    rep = normalize_findings(audit, mech, facts, interp, surface, root)
    rep["_meta"] = {"osv_id": args.osv, "audit_source": audit_src,
                    "mech_source": "mech_hypotheses.json" if mech.get("hypotheses") else None,
                    "facts_used": bool(facts), "interpretation_used": bool(interp),
                    "method": "多路候选合并（0 LLM）；证据行已按固定源码核对"}

    print(f"=== {args.osv} candidate findings ===")
    print(f"  审计候选 {rep['summary']['from_audit']} 条（{audit_src}）")
    print(f"  机械假设 {rep['summary']['from_mech']} 条")
    print(f"  去重后   {rep['summary']['after_dedup']} 条（合并 {rep['summary']['merged']} 条）")
    print(f"  证据通过 {rep['summary']['evidence_ok']} / 输入可达 complete {rep['summary']['input_complete']}")
    print(f"  按族    : {rep['summary']['by_family']}")
    print(f"  与故障关系: {rep['summary']['by_fault_relation']}")
    print(f"  调用面关系: {rep['summary']['by_call_surface']}")
    print()
    for f in rep["findings"][:12]:
        print(f"  [{f['finding_id']}] {f['vuln_family']:<18} {f['function'][:26]:<26}"
              f" {f['fault_relation']:<16} ev={f['evidence_ok']} "
              f"in={f['input_reachability']['status']:<8} src={','.join(f['sources'])}")

    if args.selftest or args.dry_run:
        return
    os.makedirs(V2, exist_ok=True)
    p = os.path.join(V2, "candidate_findings.json")
    json.dump(rep, open(p, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(f"\n  写出 {p}")


def _load_or_none(p):
    return json.load(open(p, encoding="utf-8")) if os.path.exists(p) else None

# ══════════════════════════════════════════════════════════════════════
# 5.5 每个特征走同一套 6 阶段（原 s5f_feature_pipeline.py）
# ══════════════════════════════════════════════════════════════════════

"""s5f_feature_pipeline.py —— 阶段5.3'：**每个特征都走同一套固定流程**

为什么要有这个模块
  之前只有 uaf-llm01 走了完整流程（崩溃报告给了站点），其余 4 个用"通用字段类别"猜，
  方法不一致。本模块把流程固定下来，5 个特征一视同仁：

  ① 短名单（确定性）   按该特征的机制，从 worklist 里挑出可能承载它的函数
  ② 站点扫描（确定性） 在同一批函数上扫"释放→使用"原语，产出带行号的原始站点
  ③ 机制归类（确定性） 把站点归到它能支持的机制上；归不上就是"本项目无落点"
  ④ 六步证据链（确定性）站点 → 完整证据链；任何一跳不闭合就降级
  ⑤ 输入分支判定（确定性）判断该站点在哪条输入分支上（DXF / DWG / JSON）
  ⑥ 动作规格（确定性） 字段 + 操作 + 保持的不变量 + 证据等级

  每一步的产物都落盘；`status` 只有 `found` / `not_found` / `blocked` 三种。
  **找不到就明确写 not_found，权重还给 default——不用 generic 算子占预算。**

固定的机制→短名单/归类规则（可审计，不靠 LLM）
  llm01 同函数释放后访问      : free 后同函数内再读，含循环回边
  llm02 重分配后旧缓冲        : realloc 的结果没回写给原变量，或先存别名再 realloc
  llm03 清理/析构先释放后读    : 函数名匹配 free/destroy/cleanup/close/del 的释放路径
  llm04 跨函数陈旧对象        : 释放与读取发生在不同函数（结构体字段/别名）
  llm05 容器节点销毁后遍历     : 释放后在循环里继续走 next/prev/child 链

用法
  python3 s5f_feature_pipeline.py --osv ARVO-42494732 --all
  python3 s5f_feature_pipeline.py --osv ARVO-42494732 --feature uaf-llm02
"""

import argparse
import json
import os
import re
import sys

sys.path.insert(0, HERE)

# ─────────────── 固定规则表 ───────────────
FREE_CALL = re.compile(
    r"\b([A-Za-z_]\w*)\s*\(\s*&?\s*([A-Za-z_]\w*(?:\s*->\s*\w+)?)\s*\)\s*;")
FREE_NAME = re.compile(r"(free|destroy|release|clear|cleanup|del|close)", re.I)
REALLOC_CALL = re.compile(
    r"\b([A-Za-z_]\w*)\s*=\s*(?:\([^)]*\)\s*)?realloc\s*\(\s*([A-Za-z_]\w*(?:\s*->\s*\w+)?)\s*,")
LINK_READ = re.compile(r"\b(\w+)\s*->\s*(next|prev|child|sibling|first|last|head|tail)\b")

# 短名单规则：机制 → 函数名/被调名线索（确定性，可审计）
SHORTLIST = {
    "llm01": dict(name_rx=r".*", call_rx=r".*(free|destroy|release).*",
                  why="需要 free 类调用 + 同函数内再读"),
    "llm02": dict(name_rx=r".*", call_rx=r".*(realloc|alloc|resize|grow).*",
                  why="需要 realloc/扩容"),
    "llm03": dict(name_rx=r".*(free|destroy|cleanup|close|del).*",
                  call_rx=r".*(free|destroy|release|clear).*",
                  why="清理/析构函数里的释放"),
    "llm04": dict(name_rx=r".*(resolve|fixup|update|defer|postpon|stale|flush).*",
                  call_rx=r".*", why="延迟解析/交叉引用修正"),
    "llm05": dict(name_rx=r".*", call_rx=r".*(free|destroy|release|clear).*",
                  why="容器销毁后仍遍历"),
}
# 输入格式 → 该格式会走到的源文件。特征必须在**对应格式的代码路径**里找站点，
# 否则会出现"给 DXF 写算子、却指望它在 DWG 上生效"这种错配。
# 所有格式都会走到的公共路径（清理、句柄解析、写出）。站点落在这些文件里，
# 说明它对**所有格式**都适用，format_scope 要写全。
COMMON_FILES = ("src/free.c", "src/dwg.c")
FORMAT_FILES = {
    "DXF":  ("src/in_dxf.c",) + COMMON_FILES,
    "DWG":  ("src/decode.c", "src/bits.c") + COMMON_FILES,
    "JSON": ("src/in_json.c",) + COMMON_FILES,
}
FORMAT_MAGIC = {"DWG": "'AC' 开头", "JSON": "'{' 开头", "DXF": "其余"}

MECH_KEY = {"llm01": "同函数释放后访问", "llm02": "缓冲释放后旧指针",
            "llm03": "清理析构后悬垂访问", "llm04": "跨函数陈旧对象访问",
            "llm05": "容器节点销毁后遍历"}


# ─────────────── ① 短名单 ───────────────
def shortlist(feature_id, worklist, callees, only_files=None):
    key = feature_id.split("-")[-1]
    rule = SHORTLIST.get(key)
    if not rule:
        return [], "该特征没有短名单规则"
    rx_n = re.compile(rule["name_rx"], re.I)
    rx_c = re.compile(rule["call_rx"], re.I)
    out = []
    for f in worklist["functions"]:
        if only_files and not any(f["file"].startswith(x) for x in only_files):
            continue
        calls = callees.get((f["file"], f["name"]), set())
        by_name = bool(rx_n.fullmatch(f["name"]))
        by_call = any(rx_c.fullmatch(c) for c in calls)
        if by_name or by_call:
            out.append({"function": f["name"], "file": f["file"],
                        "lines": f["lines"], "depth": f["depth"],
                        "risk": f["risk"], "hit_by": "name" if by_name else "call"})
    out.sort(key=lambda x: (x["depth"], 0 if x["risk"] else 1))
    return out, rule["why"]


# ─────────────── ② 站点扫描（原语） ───────────────
def scan_sites(root, shortlist_funcs, src_cache):
    """在短名单函数里扫"释放类调用 → 后续读同一变量"。产出原始站点。"""
    sites = []
    for f in shortlist_funcs:
        lines = src_cache.get(f["file"])
        if not lines:
            continue
        lo, hi = f["lines"][0] - 1, min(f["lines"][1], len(lines)) - 1
        for i in range(lo, hi + 1):
            code = strip_code(lines[i])
            m = FREE_CALL.search(code)
            if not m or not FREE_NAME.search(m.group(1)):
                continue
            callee, var = m.group(1), m.group(2).replace(" ", "")
            # a) 同块/后续直线上的读
            same = None
            for j in range(i + 1, min(hi, i + 200) + 1):
                s = strip_code(lines[j])
                if re.search(rf"\b{re.escape(var)}\b\s*=(?!=)", s):
                    break
                if re.search(rf"\b{re.escape(var)}\b\s*(->|\.|\[)", s):
                    same = {"line": j + 1, "code": s[:160], "kind": "same_path"}
                    break
                if re.search(r"\breturn\b", s):
                    break
            # b) 循环回边上的读
            trace = flow(lines, lo, hi, i, 20)
            bi = next((k for k, t in enumerate(trace) if t["back_edge"]), None)
            back = None
            if bi is not None:
                # 回边之前若把 var 重新赋值，就不是 UAF
                end_ln = trace[bi]["line"]
                if any(re.search(rf"\b{re.escape(var)}\b\s*=(?!=)",
                                 strip_code(lines[j]))
                       for j in range(i + 1, end_ln + 1)):
                    trace = []
                    bi = None
            if bi is not None:
                for t in trace[bi:]:
                    s = strip_code(lines[t["line"]])
                    if re.search(rf"\b{re.escape(var)}\b\s*(->|\.|\[)", s):
                        back = {"line": t["line"] + 1, "code": s[:160],
                                "kind": "loop_back",
                                "back_edge_to": (trace[bi]["next"] + 1
                                                 if trace[bi]["next"] is not None else None)}
                        break
            use = same or back
            if not use:
                continue
            if not wrapper_frees_param(callee, var, funcs_by_name, root, src_cache):
                continue      # 包装只释放成员，不释放该变量本身
            link = bool(LINK_READ.search(strip_code(lines[use["line"] - 1])))
            sites.append({"function": f["function"], "file": f["file"],
                          "free_line": i + 1, "free_code": code[:160],
                          "callee": callee, "var": var,
                          "use": use, "is_link_read": link,
                          "realloc_near": _realloc_near(lines, lo, hi, i)})
    return sites



_WRAP_CACHE: dict = {}


def wrapper_frees_param(callee, var, funcs_by_name, root, src_cache):
    """`dwg_free_header_vars(dwg)` 只释放 dwg 的成员，不释放 dwg 本身 → 不能算释放。

    判定：被调函数体里出现 `free ( <形参> )` 或 `free ( (char*)<形参> )` 这类**直接释放**。
    """
    key = callee
    if key in _WRAP_CACHE:
        return _WRAP_CACHE[key]
    f = funcs_by_name.get(callee)
    if not f:
        _WRAP_CACHE[key] = True          # 看不到源码就不排除（保守）
        return True
    lines = src_cache.get(f["file"])
    if not lines:
        _WRAP_CACHE[key] = True
        return True
    lo, hi = f["lines"][0] - 1, min(f["lines"][1], len(lines))
    # 形参名（第一个参数）
    head = " ".join(lines[lo:min(lo + 3, hi)])
    m = re.search(r"\(\s*[^,)]*?\b(\w+)\s*[,)]", head)
    param = m.group(1) if m else None
    if not param:
        _WRAP_CACHE[key] = True
        return True
    rx = re.compile(rf"\bfree\s*\(\s*(?:\([^)]*\)\s*)?&?\s*{re.escape(param)}\b")
    ok = any(rx.search(lines[j]) for j in range(lo, hi))
    _WRAP_CACHE[key] = ok
    return ok

def _realloc_near(lines, lo, hi, i):
    for j in range(max(lo, i - 30), min(hi, i + 30) + 1):
        m = REALLOC_CALL.search(strip_code(lines[j]))
        if m:
            return {"line": j + 1, "var": m.group(1), "arg": m.group(2)}
    return None



# ── llm02 专用：realloc / 扩容后旧别名仍被访问（这个形态**没有 free 调用**，
#    所以 scan_sites 从来扫不到它——这是之前的检测器缺口）──
ALIAS_ASSIGN = re.compile(
    r"\b(?:const\s+)?(?:unsigned\s+char|char|uint8_t|Dwg_Object|Dxf_Pair|void)\s*\*\s*"
    r"([A-Za-z_]\w*)\s*=\s*(?:&\s*)?\(?\s*(?:unsigned\s+char\s*\*\s*\)?\s*)?"
    r"&?\s*([A-Za-z_]\w*(?:\s*->\s*\w+)?)\s*\[")
REALLOC_RX = re.compile(
    r"\b([A-Za-z_]\w*(?:\s*->\s*\w+)?)\s*=\s*(?:\([^)]*\)\s*)?realloc\s*\(\s*\1\s*,")


def scan_realloc_sites(shortlist_funcs, src_cache):
    """找『先取别名 → realloc 原缓冲 → 之后还用别名』。"""
    out = []
    for f in shortlist_funcs:
        lines = src_cache.get(f["file"])
        if not lines:
            continue
        lo, hi = f["lines"][0] - 1, min(f["lines"][1], len(lines)) - 1
        for i in range(lo, hi + 1):
            m = REALLOC_RX.search(lines[i])
            if not m:
                continue
            base = m.group(1).replace(" ", "")
            aliases = {}
            for j in range(max(lo, i - 60), i):
                a = ALIAS_ASSIGN.search(lines[j])
                if a and a.group(2).replace(" ", "").startswith(base.split("->")[-1]):
                    aliases[a.group(1)] = j + 1
            if not aliases:
                continue
            for var, aline in aliases.items():
                for j in range(i + 1, min(hi, i + 120) + 1):
                    if re.search(rf"\b{re.escape(var)}\b\s*(\[|->)", lines[j]):
                        out.append({"function": f["function"], "file": f["file"],
                                    "realloc_line": i + 1, "realloc_code": lines[i].strip()[:140],
                                    "base": base, "alias": var, "alias_line": aline,
                                    "use_line": j + 1, "use_code": lines[j].strip()[:140],
                                    "kind": "realloc_alias"})
                        break
    return out

# ─────────────── ③ 机制归类 ───────────────
def classify(site, feature_id):
    """这个站点能否支持给定机制？返回 (ok, 理由)。"""
    key = feature_id.split("-")[-1]
    fn = site["function"].lower()
    if key == "llm01":
        if site["use"]["kind"] == "loop_back":
            return True, "循环回边回到解引用同一变量"
        if site["use"]["kind"] == "same_path" and not site["is_link_read"]:
            return True, "同一直线上释放后解引用"
        return False, "没有同函数内的后续读"
    if key == "llm02":
        r = site["realloc_near"] or {}
        if site.get("callee") == "realloc" or (r and r.get("var") != r.get("arg")):
            return True, (f"别名 {r.get('var')} 取自 {r.get('arg')}，realloc 之后仍被读"
                          if r else "realloc 之后旧别名仍被读")
        return False, "附近没有『realloc 之后旧别名仍被读』的形态"
    if key == "llm03":
        if re.search(r"(free|destroy|cleanup|close|del)", fn):
            return True, "释放发生在清理/析构函数里"
        return False, "释放不在清理/析构路径上"
    if key == "llm04":
        if re.search(r"(resolve|fixup|update|defer|postpon)", fn):
            return True, "延迟解析/交叉引用修正路径"
        return False, "不在延迟解析路径上"
    if key == "llm05":
        if site["is_link_read"]:
            return True, "释放后仍沿 next/prev/child 链走"
        return False, "释放后的读不是链式遍历"
    return False, "未知机制"


# ─────────────── ④ 六步证据链 ───────────────
def build_chain(site, feature, surface, src_cache):
    lines = src_cache[site["file"]]
    lo, hi = site["free_line"] - 1, None
    chain = [
        {"step": 1, "name": "harness 入口", "status": "complete" if
         (surface.get("target") or {}).get("entry_symbol") else "unknown",
         "evidence": [(surface.get("target") or {}).get("entry_symbol")]},
        {"step": 2, "name": "输入绑定", "status": "complete"}
        if (surface.get("input_format") or {}).get("format") else {"step": 2, "status": "unknown",
                                                                   "evidence": []},
        {"step": 3, "name": "解析到内部结构", "status": "complete"
         if (surface.get("parsers") or []) else "unknown",
         "evidence": [[p["function"], p["lines"][0]] for p in (surface.get("parsers") or [])[:3]]},
        {"step": 4, "name": "字段进入目标变量", "status": "complete",
         "evidence": [[site["free_line"], site["free_code"]]]},
        {"step": 5, "name": "释放点所在分支", "status": "complete",
         "evidence": [[site["free_line"], site["free_code"]]]},
        {"step": 6, "name": "释放后仍被读", "status": "complete",
         "evidence": [[site["use"]["line"], site["use"]["code"]]],
         "note": ("循环回边⟲回到 L%s" % site["use"].get("back_edge_to")
                  if site["use"]["kind"] == "loop_back" else "同一直线上")},
    ]
    # 逐跳核对源码行是否真的存在
    for st in chain:
        for ev in st.get("evidence") or []:
            if isinstance(ev, list) and len(ev) >= 2 and isinstance(ev[0], int):
                st["status"] = ("complete" if 1 <= ev[0] <= len(lines) else "unknown")
    return chain


# ─────────────── ⑤ 输入分支 ───────────────
def input_branch(rel, src_cache):
    """站点所在的源文件属于哪条输入分支（harness 按前两字节分流）。"""
    if rel.startswith("src/in_dxf"):
        return {"branch": "DXF", "entry": "dwg_read_dxf", "magic": "非 'AC'、非 '{'"}
    if rel.startswith("src/in_json"):
        return {"branch": "JSON", "entry": "dwg_read_json", "magic": "'{'"}
    if rel.startswith("src/decode") or rel.startswith("src/bits"):
        return {"branch": "DWG", "entry": "dwg_decode", "magic": "'AC'"}
    if rel.startswith("src/out_") or rel.startswith("src/encode"):
        return {"branch": "OUTPUT", "entry": "(写出路径)", "magic": "解析成功后"}
    return {"branch": "UNKNOWN", "entry": None, "magic": None}


# ─────────────── ⑥ 动作规格 ───────────────
def build_action(feature, site, chain, branch, weight):
    ok = all(s["status"] == "complete" for s in chain) and branch["branch"] != "UNKNOWN"
    return {
        "action_id": None,
        "feature_id": feature.get("id"),
        "feature_name": feature.get("feature_name"),
        "mechanism": MECH_KEY.get(feature.get("id", "").split("-")[-1]),
        "weight": weight,
        "site": {"function": site["function"], "file": site["file"],
                 "free_line": site["free_line"], "use_line": site["use"]["line"],
                 "var": site["var"], "callee": site["callee"],
                 "reuse_kind": site["use"]["kind"]},
        "input_branch": branch,
        "evidence_chain": chain,
        "evidence_grade": "proven" if ok else "blocked",
        "operation": ("mutate_binary_record" if branch["branch"] == "DWG"
                      else "mutate_text_record"),
        "status": "found" if ok else "blocked",
        "blockers": [] if ok else [f"step{s['step']} 未闭合" for s in chain
                                   if s["status"] != "complete"]
        + ([f"输入分支未知"] if branch["branch"] == "UNKNOWN" else []),
    }


# ─────────────── 主流程 ───────────────
def load_cpg_dump(p):
    methods, edges = [], []
    for ln in open(p, encoding="utf-8"):
        t = ln.rstrip("\n").split("\t")
        if t[0] == "@@M" and len(t) >= 6:
            methods.append({"file": t[1], "name": t[2], "start": int(t[3] or 0),
                            "end": int(t[4] or 0), "external": t[5] == "1"})
        elif t[0] == "@@C" and len(t) >= 4:
            edges.append((t[1], t[2], t[3]))
    callees = {}
    for cf, cn, cs in edges:
        callees.setdefault((cf, cn), set()).update(cs.split("|"))
    return methods, callees



# ── P3 预筛：这个特征在本项目有没有落点（筛子，不是判据）──
# 依据：stage3 final.json 的 trigger_condition.where_free / where_use 里的函数名，
# 与 audit_worklist 的可达函数集合求交。交集为空 → 该特征在本项目无落点。
# 注意：这只决定"要不要继续查"，不判断"站点是不是真 UAF"——后者仍归 cfg_lib 证据链 + agent。
REACHABLE: set = set()
PATTERN_BY_NAME: dict = {}
ID_RX = re.compile(r"[A-Za-z_][A-Za-z0-9_]{3,}")

# 标准库 / 编译器内建名。stage3 的 where_free / where_use 是散文，会把 malloc、wchar、
# mbrtowc 这类名字也写进去；它们在项目里的同名声明不是"特征落点"，必须剔除，
# 否则换项目时交集会被这些通用名污染（见 R3_PHASE D 报告）。
STDLIB_NAMES = {
    # 分配 / 释放
    "malloc", "free", "realloc", "calloc", "alloca", "memalign", "posix_memalign",
    "aligned_alloc", "valloc", "brk", "sbrk", "mmap", "munmap", "new", "delete",
    # 内存 / 字符串
    "memcpy", "memmove", "memset", "memcmp", "memchr", "bcopy", "bzero",
    "strdup", "strndup", "strcpy", "strncpy", "strcat", "strncat", "strlen",
    "strcmp", "strncmp", "strchr", "strrchr", "strstr", "strtok", "strerror",
    "sprintf", "snprintf", "vsprintf", "vsnprintf", "sscanf", "atoi", "atol", "strtol",
    # 宽字符 / 本地化（出现频率高、极易污染交集）
    "wchar", "wchar_t", "mbrtowc", "wcrtomb", "mbsrtowcs", "wcsrtombs", "mbstate",
    "wcslen", "wcscpy", "wcsncpy", "wcscmp", "setlocale",
    # 文件 / 流
    "fopen", "fclose", "fread", "fwrite", "fseek", "ftell", "fflush", "feof", "ferror",
    "fgets", "fputs", "getc", "putc", "printf", "fprintf", "puts", "perror",
    # 进程 / 控制
    "abort", "exit", "atexit", "assert", "errno", "memcpy_s", "memset_s",
}


def applicability(feature):
    """返回 {hit_count, hit_names, source_pattern, extracted, basis}。"""
    sp = feature.get("source_pattern")
    pat = PATTERN_BY_NAME.get(sp)
    if not pat:
        return {"hit_count": None, "hit_names": [], "source_pattern": sp,
                "extracted": 0, "basis": f"stage3 final.json 里找不到 pattern {sp!r}；预筛跳过"}
    tc = pat.get("trigger_condition") or {}
    names = set()
    for k in ("where_free", "where_use"):
        names |= set(ID_RX.findall(tc.get(k) or ""))
    dropped = sorted(n for n in names if n.lower() in STDLIB_NAMES)
    names = {n for n in names if n.lower() not in STDLIB_NAMES}
    hit = sorted(n for n in names if n in REACHABLE)
    return {"hit_count": len(hit), "hit_names": hit, "source_pattern": sp,
            "extracted": len(names), "dropped_stdlib": dropped,
            "basis": (f"trigger_condition.where_free/where_use 抽出 {len(names)} 个标识符"
                      f"（剔除 {len(dropped)} 个标准库名），"
                      f"与 {len(REACHABLE)} 个可达函数求交 → {len(hit)} 个命中")}



def run_feature(feature, worklist, callees, surface, src_cache, weight, fmt=None):
    fid = feature["id"]
    app = applicability(feature)
    if app["hit_count"] == 0:
        return {"feature_id": fid, "feature_name": feature.get("feature_name"),
                "target_format": fmt, "mechanism": MECH_KEY.get(fid.split("-")[-1]),
                "shortlist_rule": None, "shortlist": [], "shortlist_size": 0,
                "sites_scanned": 0, "sites_supporting": 0, "sites": [],
                "applicability": app,
                "status": "not_applicable",
                "why": f"预筛：{app['basis']} → 该特征与本项目可达代码无交集",
                "action": None}
    only = FORMAT_FILES.get(fmt) if fmt else None
    cands, why = shortlist(fid, worklist, callees, only)
    sites = scan_sites(surface_root, cands, src_cache) if cands else []
    if fid.endswith("llm02"):
        extra = scan_realloc_sites(cands, src_cache) if cands else []
        for e in extra:
            sites.append({"function": e["function"], "file": e["file"],
                          "free_line": e["realloc_line"], "free_code": e["realloc_code"],
                          "callee": "realloc", "var": e["alias"],
                          "use": {"line": e["use_line"], "code": e["use_code"],
                                  "kind": "same_path"},
                          "is_link_read": False, "realloc_near": {"var": e["alias"],
                                                                   "arg": e["base"]}})
        res_extra = len(extra)
    else:
        res_extra = 0
    scored = []
    for s in sites:
        ok, reason = classify(s, fid)
        scored.append({"site": s, "supports": ok, "reason": reason})
    good = [x for x in scored if x["supports"]]
    crash_fn = (surface.get("target") or {}).get("fault_function")
    good.sort(key=lambda x: (0 if x["site"]["function"] == crash_fn else 1,
                             0 if x["site"]["use"]["kind"] == "loop_back" else 1,
                             x["site"]["file"], x["site"]["free_line"]))
    res = {"feature_id": fid, "feature_name": feature.get("feature_name"),
           "target_format": fmt,
           "mechanism": MECH_KEY.get(fid.split("-")[-1]),
           "shortlist_rule": why, "shortlist": cands[:40],
           "shortlist_size": len(cands), "sites_scanned": len(sites),
           "sites_supporting": len(good),
           "applicability": app,
           "sites": [{**x["site"], "supports": x["supports"], "reason": x["reason"]}
                     for x in scored[:60]]}
    if fmt:
        branch = {"branch": fmt, "entry": None, "magic": FORMAT_MAGIC.get(fmt)}
        if any(st.get("file", "").startswith(COMMON_FILES) for st in sites[:1]) or \
           (good and good[0]["site"]["file"].startswith(COMMON_FILES)):
            branch = {"branch": "ALL", "entry": None,
                      "magic": "公共路径（清理/句柄/写出），三种格式都可达",
                      "format_scope": ["DXF", "DWG", "JSON"]}
    if not good:
        res.update({"status": "not_found",
                    "why": f"{fmt or '全局'} 路径：短名单 {len(cands)} 个函数、"
                           f"扫出 {len(sites)} 个释放→使用原语，没有一个能支持该机制",
                    "action": None})
        return res
    best = good[0]["site"]
    branch = ({"branch": fmt, "entry": None, "magic": FORMAT_MAGIC.get(fmt)}
              if fmt else input_branch(best["file"], src_cache))
    chain = build_chain(best, feature, surface, src_cache)
    action = build_action(feature, best, chain, branch, weight)
    action["candidate_count"] = len(good)
    res.update({"status": action["status"], "why": good[0]["reason"], "action": action})
    return res


surface_root = ""        # 由 main_features 注入
funcs_by_name: dict = {}  # 由 main_features 注入


def main_features():
    global surface_root, funcs_by_name, REACHABLE, PATTERN_BY_NAME
    ap = argparse.ArgumentParser(description="阶段5.3'：每个特征走同一套固定流程")
    ap.add_argument("--osv", required=True)
    ap.add_argument("--type", default="uaf")
    ap.add_argument("--feature", default=None, help="只跑一个特征")
    ap.add_argument("--all", action="store_true", help="跑该崩溃类型的全部特征")
    ap.add_argument("--by-format", action="store_true",
                    help="按『输入格式 × 特征』矩阵扫，每种格式只在该格式的代码路径里找站点")
    ap.add_argument("--default-weight", type=float, default=0.5)
    args = ap.parse_args()

    S5 = os.path.join(OUT, args.osv)
    V2 = os.path.join(S5, "v2")
    surface = json.load(open(os.path.join(V2, "target_surface.json"), encoding="utf-8"))
    worklist = json.load(open(os.path.join(S5, "audit_worklist.json"), encoding="utf-8"))
    ctx = json.load(open(os.path.join(S5, "source_context.json"), encoding="utf-8"))
    surface_root = ctx["repo_local"]
    feats = json.load(open(os.path.join(ROOT, "outputs", "stage4", args.type,
                                        "features.json"), encoding="utf-8"))["features"]
    _, callees = load_cpg_dump(os.path.join(S5, "cpg_dump.tsv"))
    funcs_by_name = {f["name"]: f for f in worklist["functions"]}
    REACHABLE = set(funcs_by_name)
    _fp = os.path.join(ROOT, "outputs", "stage3", args.type, "final.json")
    if os.path.exists(_fp):
        for _p in (json.load(open(_fp, encoding="utf-8")).get("final_patterns") or []):
            PATTERN_BY_NAME[_p["name"]] = _p
    print(f"  可适用性预筛：可达函数 {len(REACHABLE)} 个，"
          f"stage3 pattern {len(PATTERN_BY_NAME)} 个")

    src_cache = {}
    for f in worklist["functions"]:
        if f["file"] not in src_cache:
            p = os.path.join(surface_root, f["file"])
            src_cache[f["file"]] = (open(p, encoding="utf-8", errors="replace")
                                    .read().split("\n")) if os.path.isfile(p) else None

    if args.by_format:
        # 每种格式独立跑一遍：format × feature 矩阵
        matrix = []
        for fmt in FORMAT_FILES:
            todo_f = [f for f in feats if args.feature in (None, f["id"])]
            wf = round((1.0 - args.default_weight) / max(1, len(todo_f)), 4)
            print(f"\n--- 格式 {fmt}（{FORMAT_MAGIC[fmt]}）---")
            for f in todo_f:
                r = run_feature(f, worklist, callees, surface, src_cache, wf, fmt=fmt)
                matrix.append(r)
                icon = {"found": "✅", "not_found": "❌", "blocked": "⚠️",
                        "not_applicable": "⛔"}[r["status"]]
                print(f"  {icon} {r['feature_id']:<11} {r['status']:<10} "
                      f"短名单 {r['shortlist_size']:>3} / 支持 {r['sites_supporting']:>2}"
                      f"  {r['why'][:60]}")
        os.makedirs(os.path.join(V2, "features"), exist_ok=True)
        json.dump({"matrix": matrix, "formats": list(FORMAT_FILES)},
                  open(os.path.join(V2, "feature_matrix.json"), "w", encoding="utf-8"),
                  ensure_ascii=False, indent=1)
        print(f"\n  写出 {V2}/feature_matrix.json")
        found = [r for r in matrix if r["status"] == "found"]
        print(f"  共 found {len(found)} 条（格式×特征）")
        return

    todo = [f for f in feats if args.feature in (None, f["id"])] if (args.all or args.feature) \
        else feats
    n = len(todo)
    w = round((1.0 - args.default_weight) / n, 4) if n else 0.0

    print(f"=== {args.osv} 特征管线（{n} 个特征，每个权重 {w}）===")
    results = []
    for f in todo:
        r = run_feature(f, worklist, callees, surface, src_cache, w)
        results.append(r)
        icon = {"found": "✅", "not_found": "❌", "blocked": "⚠️",
                "not_applicable": "⛔"}[r["status"]]
        print(f"  {icon} {r['feature_id']:<11} {r['status']:<10} "
              f"短名单 {r['shortlist_size']:>3} / 原语 {r['sites_scanned']:>3} / "
              f"支持 {r['sites_supporting']:>2} | {r['why'][:70]}")
        if r["action"]:
            a = r["action"]
            print(f"        site: {a['site']['file']}:{a['site']['free_line']}"
                  f" → {a['site']['use_line']}  var={a['site']['var']}"
                  f"  branch={a['input_branch']['branch']}")

    os.makedirs(os.path.join(V2, "features"), exist_ok=True)
    for r in results:
        d = os.path.join(V2, "features", r["feature_id"])
        os.makedirs(d, exist_ok=True)
        json.dump(r, open(os.path.join(d, "pipeline.json"), "w", encoding="utf-8"),
                  ensure_ascii=False, indent=1)

    found = [r for r in results if r["status"] == "found"]
    # 权重要在"知道几个找到"之后才定：default 占 default_weight，其余平分给 found 的特征
    w2 = round((1.0 - args.default_weight) / len(found), 4) if found else 0.0
    for r in found:
        r["action"]["weight"] = w2
    print()
    print(f"  found {len(found)}/{n}；not_found {sum(1 for r in results if r['status']=='not_found')}；"
          f"blocked {sum(1 for r in results if r['status']=='blocked')}")
    if found:
        print(f"  权重合计: default {args.default_weight} + {len(found)}×{w2} = "
              f"{round(args.default_weight + len(found) * w2, 3)}")
    json.dump({"features": results,
               "weighting": {"default": args.default_weight,
                             "per_found_feature": w2, "found": len(found), "total": n}},
              open(os.path.join(V2, "feature_pipeline.json"), "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)
    print(f"  写出 {V2}/feature_pipeline.json")

# ══════════════════════════════════════════════════════════════════════
# 5.6 声明式 mutation plan（权重在这里定）（原 s5_mutation_plan.py）
# ══════════════════════════════════════════════════════════════════════

"""s5_mutation_plan.py —— 阶段5.4：生成声明式 mutation plan（**0 LLM**）

职责
  把「选中的特征 + 候选缺陷 + target surface」冻结成一份**可检查的**变异计划，
  成为 C 代码生成器的唯一业务输入。C 代码只负责实现它，不再自己决定改哪。

`status=ready` 的必要条件（缺一即 blocked）
  1. 有 selected binding
  2. 输入格式已知
  3. 字段有 locator（record 级即可，不要求字节偏移）
  4. 字段到目标条件有源码证据
  5. 每个 mutation action 都有 basis_refs
  6. 保持的不变量有实现策略

本版能确定性推出的东西（以 libredwg/DXF 为例）
  · 字段约束：从 `while (pair->code == 0 && pair->value.s)` 取「组码 0 + 字符串值」
  · 段锚点  ：故障函数的调用点被 `else if (strEQc (pair->value.s, "OBJECTS"))` 守着
  · 判据    ：`if (is_dwg_object (name))`（来自 target_surface step5）
  · 期望效果：判据为假 → else 分支释放且不置空 → 循环回边 → 解引用（step6 已证明）

用法
  python3 s5_mutation_plan.py --osv ARVO-42494732
"""

import argparse
import json
import os
import re
import sys


SOLVE = {"add_argument"}

# line_record(DXF) 适配器：把特征的 semantic target 映射成"改哪一类记录字段"
# 注意：group code 的语义是 DXF 领域知识；换格式要写新适配器。
STRATEGY = {
    "同函数释放后访问": dict(
        part="value_line", op="replace_value_line",
        field="record.value_after_group_code.0", anchor="0",
        note="把 code-0 记录的值改成 is_dwg_object 不认识的类型名"),
    "缓冲释放后旧指针": dict(
        part="numeric_field", op="set_numeric_field",
        field="record.numeric_value", anchor="90|70|71|40|42",
        note="把长度/计数/偏移类组码的值推向大数或边界值"),
    "清理析构后悬垂访问": dict(
        part="section_or_key", op="replace_section_or_key",
        field="record.string_value", anchor="2|3",
        note="改段名/键名或别名表项，走清理或错误回退分支"),
    "跨函数陈旧对象访问": dict(
        part="handle_ref", op="rewrite_handle_ref",
        field="record.handle_reference", anchor="330|340|350|360",
        note="把对象引用类句柄改成陈旧/重复句柄，触发替换后仍读旧对象"),
    "容器节点销毁后遍历": dict(
        part="object_handle", op="duplicate_object_handle",
        field="record.handle", anchor="5",
        note="复制已有句柄，让容器替换/销毁后遍历仍命中旧节点"),
}


def strategy_for(feature: dict) -> dict:
    sp = feature.get("source_pattern")
    st = dict(STRATEGY.get(sp) or {})
    st["source_pattern"] = sp
    return st


def load_plan(p):
    return json.load(open(p, encoding="utf-8"))


def find_call_site(root: str, rel: str, fn: str) -> dict | None:
    """在故障函数所在文件里找它的**调用点**，并取其前面的 strEQc 段名守卫。"""
    p = os.path.join(root, rel)
    if not os.path.isfile(p):
        return None
    lines = open(p, encoding="utf-8", errors="replace").read().split("\n")
    call_rx = re.compile(rf"\b{re.escape(fn)}\s*\(")
    cands = []
    for i, ln in enumerate(lines):
        if not call_rx.search(ln):
            continue
        # 只认"语句调用"：本行以 ; 结尾（函数定义行不会）
        if not ln.rstrip().endswith(";"):
            continue
        section = None
        for j in range(max(0, i - 8), i):
            m = re.search(r'strEQc\s*\(\s*\w+->\w+\.\w+\s*,\s*"([^"]+)"\s*\)', lines[j])
            if m:
                section = m.group(1)
        cands.append({"line": i + 1, "code": ln.strip()[:160], "section_anchor": section})
    if not cands:
        return None
    # 优先带段名守卫的调用点
    return next((c for c in cands if c["section_anchor"]), cands[0])


def field_constraint(root: str, rel: str, lines_of_interest) -> dict | None:
    """从循环条件/判据里取字段约束：组码值 + 值类型。"""
    p = os.path.join(root, rel)
    if not os.path.isfile(p):
        return None
    lines = open(p, encoding="utf-8", errors="replace").read().split("\n")
    for ln in lines_of_interest or []:
        try:
            s = lines[int(ln) - 1]
        except (IndexError, ValueError, TypeError):
            continue
        m = re.search(r"(\w+)->code\s*==\s*(\d+)", s)
        if m:
            return {"var": m.group(1), "group_code": int(m.group(2)),
                    "value_is_string": bool(re.search(rf"{m.group(1)}->value\.s", s)),
                    "evidence_line": int(ln), "evidence_code": s.strip()[:160]}
    return None



def _seed_path(source_root, tgt):
    osv = (tgt or {}).get("osv_id")
    d = os.path.join(OUT, osv, "seeds")
    if not os.path.isdir(d):
        return None
    named = [f for f in sorted(os.listdir(d))
             if f.endswith(".dxf") and not f.startswith(".")]
    return os.path.join(d, named[0]) if named else None


def _line_endings(source_root, tgt):
    p = _seed_path(source_root, tgt)
    if not p or not os.path.isfile(p):
        return None
    b = open(p, "rb").read(65536)
    crlf, lf = b.count(b"\r\n"), b.count(b"\n") - b.count(b"\r\n")
    return "CRLF" if crlf > lf else "LF"


def _sample_hex(source_root, tgt, n=96):
    """把 OBJECTS 附近的真实字节贴出来——行尾这类事实不能靠猜。"""
    p = _seed_path(source_root, tgt)
    if not p or not os.path.isfile(p):
        return None
    b = open(p, "rb").read()
    i = b.find(b"OBJECTS")
    if i < 0:
        return None
    seg = b[i:i + n]
    return {"offset": i, "bytes_visible": (seg.replace(b"\r", b"\\r")
                                           .replace(b"\n", b"\\n\\\n")
                                           .decode("latin1"))}


def _eof_anchor(source_root, tgt):
    """推导"新 SECTION 块插在哪"：插在**最后一个 code-0 / EOF 记录之前**。

    依据：DXF 的结构是 `0/SECTION … 0/ENDSEC` 重复若干块，最后以 `0/EOF` 收尾。
    插在 EOF 之前是唯一不需要改动任何已有块的合法位置。
    """
    p = _seed_path(source_root, tgt)
    if not p or not os.path.isfile(p):
        return None
    raw = open(p, "rb").read()
    # 按三种行尾切
    L = []
    i = 0
    n = len(raw)
    while i < n:
        j = i
        while j < n and raw[j] not in (10, 13):
            j += 1
        L.append((i, j, raw[i:j]))
        if j >= n:
            i = j
        elif raw[j] == 13 and j + 1 < n and raw[j + 1] == 10:
            i = j + 2
        else:
            i = j + 1
    last = None
    for k in range(len(L) - 1):
        if L[k][2].strip() == b"0" and L[k + 1][2].strip() == b"EOF":
            last = (L[k][0], k)
    if last is None:
        return None
    off, idx = last
    # 同一行尾风格
    eol = b"\r\n" if raw.find(b"\r\n") >= 0 else b"\n"
    return {"offset": off, "record_index": idx, "eol": eol.decode("latin1"),
            "file": os.path.basename(p)}

def build_mutation_plan(pipeline, features_by_id, findings_by_id, surface,
                       worklist, source_root, default_weight=0.5, v2dir=None):
    """从特征管线取 found 的 action，补上记录级定位，组成最终计划。"""
    tgt = surface.get("target") or {}
    fmt = (surface.get("input_format") or {}).get("format")
    chain_s = {x["step"]: x for x in (surface.get("evidence_chain") or [])}
    blockers, limits = [], []
    if fmt not in ("line_record", "binary_record", "raw_bytes"):
        blockers.append(f"input format unknown: {fmt}")

    found = [r for r in pipeline["features"] if r["status"] == "found"]
    if not found:
        blockers.append("没有任何特征在本项目找到落点（feature_pipeline 全是 not_found）")

    # ── 站点级归并：一个站点一个策略，多个特征可以指向同一站点 ──
    by_site = {}
    for r in found:
        a0 = r["action"]; st0 = a0["site"]
        key = (st0["file"], st0["free_line"], st0["use_line"])
        by_site.setdefault(key, {"site": st0, "features": [], "rows": []})
        by_site[key]["features"].append(a0["feature_id"])
        by_site[key]["rows"].append(r)

    actions, targets, sites_out = [], [], []
    for k, (key, grp) in enumerate(by_site.items(), 1):
        r = grp["rows"][0]          # 同一站点的证据链取第一条（其余特征只是换个说法）
        adv = []
        for f in grp["features"][1:]:
            adv.append((f, "与主特征指向同一站点，不单独生成策略"))
        # 跨函数审计里"判过 real 但两次结论不一致"的特征，记成 advisory 而不是支撑证据
        featdir = os.path.join(v2dir, "features") if v2dir else ""
        for fn in (sorted(os.listdir(featdir)) if featdir and os.path.isdir(featdir) else []):
            ap = os.path.join(featdir, fn, "cross_function_audit.json")
            if not os.path.isfile(ap):
                continue
            d0 = json.load(open(ap, encoding="utf-8")).get("agent_verdicts") or {}
            if any(v.get("verdict") == "real" for v in d0.get("verdicts") or []):
                adv.append((fn, "跨函数审计曾判 real 且指向同一站点，但重复运行结论不一致"
                                "（1 real / 1 false_positive），不作支撑证据"))
        grp["advisory"] = adv
        a0 = r["action"]
        a0 = r["action"]
        site = a0["site"]
        feature = features_by_id.get(a0["feature_id"]) or {}
        site_id = f"s{k:03d}"
        st = strategy_for(feature)
        rel, fn = site["file"], site["function"]
        call = find_call_site(source_root, rel, fn)
        fc = field_constraint(source_root, rel, [site["free_line"], site["use_line"]])
        eof = _eof_anchor(source_root, tgt)
        step4 = (next((c for c in a0["evidence_chain"] if c["step"] == 4), {}) or {})
        ev4 = " ".join(str(e[1]) for e in (step4.get("evidence") or [])
                       if isinstance(e, (list, tuple)) and len(e) >= 2)
        # 改哪一部分：站点变量若来自 ->value，就改值行
        target_part = "value_line" if "->value" in ev4 else (st.get("part") or "value_line")
        if not fc:
            blockers.append(f"{a0['feature_id']}: 字段约束未推出（找不到 v->code == N）")
        if not (call and call.get("section_anchor")):
            blockers.append(f"{a0['feature_id']}: 段锚点未推出")
        actions.append({
            "action_id": f"a{k:03d}",
            "site_id": site_id,
            "feature_id": a0["feature_id"],
            "supporting_features": sorted(set(grp["features"])),
            "feature_name": a0.get("feature_name"),
            "mechanism": a0.get("mechanism"),
            "weight": a0["weight"],
            "evidence_grade": a0.get("evidence_grade"),
            "site": site,
            "target_part": target_part,
            "operation": "ensure_record_structure",
            "operation_paths": ["replace_value_line", "construct_section"],
            "field_id": (f"record.value_after_group_code.{fc['group_code']}"
                         if (fc and target_part == "value_line") else
                         f"record.group_code.{fc['group_code']}" if fc else None),
            "locator": {"kind": "record_sequence",
                        "anchor": str(fc["group_code"]) if fc else None,
                        "regex": (surface.get("input_format") or {}).get("record_header_rx"),
                        "section_anchor": (call or {}).get("section_anchor"),
                        "pick": "random_k",
                        "k_range": "0 .. count-1",
                        "pick_reason": ("段内通常有多条同组码记录；固定改第一条会让所有种子产出同一结果。"
                                        "必须按 Seed 在候选集合里随机选一条。")},
            "new_value_policy": {
                "kind": "random_unrecognized_name",
                "derive_from": "Seed",
                "alphabet": ("ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz"
                             "0123456789_-"),
                "length": [1, 64],
                "must_differ_from_original": True,
                "must_differ_across_seeds": True,
                "reason": ("name 来自 pair->value.s（step4 证据）；is_dwg_object 只认识固定对象名，"
                           "随机串几乎必然不在集合内。**不要用固定候选列表**——那会把有效变异"
                           "空间压到个位数，等于半个预算在造重复。")},
            "construct": {
                "when": "section_absent",
                "sequence": [
                    f"0/SECTION",
                    f"2/{(call or {}).get('section_anchor')}",
                    f"0/<random_unrecognized_name>",
                    f"0/ENDSEC",
                ],
                "insert_position": ({"kind": "before_record",
                                     "anchor": "0/EOF",
                                     "offset": (eof or {}).get("offset"),
                                     "record_index": (eof or {}).get("record_index"),
                                     "derivation": ("DXF 由若干 `0/SECTION…0/ENDSEC` 块组成、"
                                                    "最后以 `0/EOF` 收尾；插在 EOF 之前不需要改动"
                                                    "任何已有块。锚点从 plan 的 seed_file 里实测")}
                                   if eof else
                                   {"kind": "append_at_end", "anchor": "eof",
                                    "derivation": "种子里找不到 `0/EOF`，退化为追加到末尾"}),
                "line_endings": (surface.get("input_contract") or {}).get("line_endings")
                                 or "CRLF",
                "record_header_rx": (surface.get("input_format") or {}).get("record_header_rx"),
                "basis_refs": ["target_surface:evidence_chain:step5",
                               "target_surface:evidence_chain:step6",
                               "mutation_plan:locator.section_anchor",
                               "mutation_plan:new_value_policy"],
            },
            "preserve": ["group_code_digits", "CRLF",
                         "section_terminator(ENDSEC)"],
            "expected_effect": (f"命中 {a0.get('mechanism')}："
                                f"{site['file']}:{site['free_line']} 释放后 "
                                f"L{site['use_line']} 仍解引用 {site['var']}"),
            "basis_refs": ([f"feature_pipeline:{a0['feature_id']}:site:{site['free_line']}"]
                           + [f"feature_pipeline:{a0['feature_id']}:chain:step{x['step']}"
                              for x in a0["evidence_chain"] if x.get("status") == "complete"]
                           + [f"feature:{a0['feature_id']}:mutation_target"]),
        })
        sites_out.append({"site_id": site_id, "file": key[0],
                          "free_line": key[1], "use_line": key[2],
                          "var": grp["site"]["var"],
                          "reuse_kind": grp["site"].get("reuse_kind"),
                          "supporting_features": sorted(set(grp["features"])),
                          "advisory_features": [{"feature": f, "note": n} for f, n in
                                                grp.get("advisory", [])],
                          "format_scope": (["DXF"] if (site.get("file") or "").startswith("src/in_dxf")
                                           else ["DXF", "DWG", "JSON"])})
        targets.append({"function": fn, "file": rel,
                        "section_anchor": (call or {}).get("section_anchor"),
                        "predicate": (chain_s.get(5, {}).get("evidence") or [[None, None]])[0][1]})

    not_found = [r["feature_id"] for r in pipeline["features"] if r["status"] != "found"]
    if not_found:
        limits.append("本项目未找到落点、已排除的特征: " + ", ".join(not_found))
    if v2dir:
        fd = os.path.join(v2dir, "features")
        flips = []
        for fn in (sorted(os.listdir(fd)) if os.path.isdir(fd) else []):
            hp = os.path.join(fd, fn, "history.jsonl")
            if not os.path.isfile(hp):
                continue
            rs = [json.loads(x) for x in open(hp, encoding="utf-8") if x.strip()]
            if len({json.dumps(r.get("counts"), sort_keys=True) for r in rs}) > 1:
                flips.append(f"{fn}: " + " → ".join(
                    f"real {r['counts']['real']}" for r in rs))
        if flips:
            limits.append("**审计结论不稳定的特征**（同一 prompt 多次运行结果不同，"
                          "未作为支撑证据）: " + "; ".join(flips))
    limits += ["plan 只保证记录级定位（记录头组码 + 段锚点），不保证字节偏移",
               "候选缺陷本身未经 fuzz 验证（已知的那条除外）"]
    total = round(default_weight + sum(a["weight"] for a in actions), 4)
    status = "ready" if (not blockers and actions and
                         all(a["target_part"] and a["locator"]["anchor"]
                             and (a.get("construct") or {}).get("sequence") for a in actions)) else "blocked"
    return {
        "schema_version": "stage5.mutation_plan.v5",
        "plan_id": "plan-003",
        "target": {"osv_id": tgt.get("osv_id"), "project": tgt.get("project"),
                   "commit": tgt.get("commit"), "crash_type": tgt.get("crash_type"),
                   "known_fault": {"file": (tgt.get("fault_file") or ""),
                                   "line": tgt.get("fault_line")}},
        "input_contract": {"format": fmt, "parser_entry": tgt.get("entry_symbol"),
                           "format_scope": (["DXF"] if fmt == "line_record" else [fmt]),
                           "seed_file": os.path.basename(_seed_path(source_root, tgt) or ""),
                           "line_endings": _line_endings(source_root, tgt),
                           "sample_hex": _sample_hex(source_root, tgt),
                           "accepted_seed_requirements": [],
                           "preserve": ["group_code_digits", "CRLF",
                                        "section_terminator(ENDSEC)"]},
        "weighting": {"default": default_weight,
                      "features_total": round(1.0 - default_weight, 4),
                      "features": len(found),
                      "per_feature": round((1.0 - default_weight) / len(found), 4) if found else 0.0,
                      "total": total},
        "targets": targets,
        "sites": sites_out,
        "mutations": actions,
        "expected_path": [
            ("harness 读取输入 → Bit_Chain", "target_surface:step1-2"),
            ("DXF 记录解析 → pair(code,value)", "target_surface:step3"),
            ("pair->value.s → name", "target_surface:step4"),
            ("判据为假 → else 分支", "target_surface:step5"),
            ("释放后回到循环条件解引用", "target_surface:step6"),
        ],
        "mutation_space": {
            "min_distinct_outputs": 200,
            "measured_over_seeds": 1000,
            "why": ("只要求『能改』不够。若 1000 个 Seed 只产出个位数不同结果，"
                    "等于半个预算在造重复，corpus 长不起来、目标触发率也不会提升。"),
        },
        "limits": limits,
        "status": status,
        "blockers": blockers,
    }


def main_plan():
    ap = argparse.ArgumentParser(description="阶段5.4：生成 mutation plan（0 LLM）")
    ap.add_argument("--osv", required=True)
    ap.add_argument("--default-weight", type=float, default=0.5,
                    help="default 变异占比（默认 0.5，其余平分给各特征）")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    S5 = os.path.join(OUT, args.osv)
    V2 = os.path.join(S5, "v2")
    need = ["feature_pipeline.json", "candidate_findings.json", "target_surface.json"]
    for n in need:
        if not os.path.exists(os.path.join(V2, n)):
            raise SystemExit(f"缺少 {V2}/{n}")
    findings = load_plan(os.path.join(V2, "candidate_findings.json"))
    surface = load_plan(os.path.join(V2, "target_surface.json"))
    worklist = load_plan(os.path.join(S5, "audit_worklist.json"))
    root = load_plan(os.path.join(S5, "source_context.json"))["repo_local"]
    feats = load_plan(os.path.join(ROOT, "outputs", "stage4", "uaf", "features.json"))

    pipe = load_plan(os.path.join(V2, "feature_pipeline.json"))
    fmap = {f["id"]: f for f in feats["features"]}
    dmap = {f["finding_id"]: f for f in findings["findings"]}
    plan = build_mutation_plan(pipe, fmap, dmap, surface, worklist, root,
                               default_weight=args.default_weight, v2dir=V2)

    print(f"=== {args.osv} mutation plan ===")
    w = plan["weighting"]
    print(f"  权重    : default {w['default']:.2f} + {w['features']} 个**站点** × {w['per_feature']:.2f}"
          f" = {w['total']:.2f}")
    print(f"  status  : {plan['status'].upper()}")
    for b in plan["blockers"]:
        print(f"      ✗ {b}")
    for a in plan["mutations"]:
        print(f"  {a['action_id']} w={a['weight']:.2f} [{a['evidence_grade']:<15}] "
              f"{a['feature_id']:<11} {a['operation']:<24} anchor={a['locator']['anchor']}")
    print(f"  expected_path: {len(plan['expected_path'])} 步")
    print(f"  limits  : {len(plan['limits'])} 条")

    if args.dry_run:
        return
    os.makedirs(V2, exist_ok=True)
    p = os.path.join(V2, "mutation_plan.json")
    json.dump(plan, open(p, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(f"\n  写出 {p}")

# ══════════════════════════════════════════════════════════════════════
# 5.7 从 ready plan 生成 C（含行为门禁）（原 s5_generate_mutator_v2.py）
# ══════════════════════════════════════════════════════════════════════

"""s5_generate_mutator_v2.py —— 阶段5.5：只从 ready plan 生成 mutator

设计约束（与 V1 的关键差别）
  · **只接受 `mutation_plan.json` 且 `status=ready`**。blocked / 缺失 → 非零退出，不产出 C。
  · prompt 只包含 plan、被选特征的摘要和少量证据行，**不塞 12,000 行源码**。
    模型不再自己决定"改哪个字段"，只负责把已冻结的计划翻译成 C。
  · 生成后做机械校验：接口签名、是否引用了计划里的 locator、有没有长度边界。
    任一不过 → 不写 mutator.c，非零退出。

用法
  python3 s5_generate_mutator_v2.py --plan <mutation_plan.json> --out <dir>
  python3 s5_generate_mutator_v2.py --osv ARVO-42494732        # 缺省用 v2/ 下的 plan
"""

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile

sys.path.insert(0, HERE)

SYSTEM_GEN = """你是一名 C 语言 fuzzer 变异器工程师。

你会收到一份**已经冻结**的 mutation plan，里面有 N 个特征策略和一个 default 权重。
你的任务：为每个策略写一个独立 C 函数，再写一个**按权重**分发的
`LLVMFuzzerCustomMutator`，其中 default 部分直接调用 `LLVMFuzzerMutate`。
你不负责、也不允许改变下列任何决定：
  · 改哪个字段（`mutations[].field_id`）
  · 用什么操作（`mutations[].operation`）
  · 边界是多少（`mutations[].bounds`）
  · 必须保持哪些不变量（`mutations[].preserve`）
如果 plan 里有你没把握的地方，在 `limits` 里写清楚，**不要自己补一个新策略**。

硬性要求：
1. **plan 里有几个 mutation action，就要实现几个独立的策略函数**，一个不能少。
2. **必须同时保留 libFuzzer 的 default 变异**：分发器按 `weighting` 的比例决定走哪条路。
   例如 default=0.5、5 个特征各 0.1 时：
     ```
     unsigned r = Seed % 1000;
     if (r < 500) return LLVMFuzzerMutate(Data, Size, MaxSize);   /* default 50% */
     switch ((r - 500) / 100) { case 0: ... case 4: ... }        /* 特征 50%，各 10% */
     ```
   **不允许把 default 去掉**——去掉探索就停了，覆盖率会崩。
3. **`mutations[].target_part` 决定改哪一部分，必须严格遵守：**
     · `value_line`  → 改组码**后面那一行**（记录的值）。**组码数字本身必须保持不变。**
     · `numeric_field` → 改数值类组码的值。
     · `section_or_key` → 改段名/键名/别名表项。
     · `handle_ref` → 改对象引用类句柄。
     · `object_handle` → 复制/篡改对象句柄。
   改错部位是最严重的错误：它会让输入变成另一种合法记录，从而绕开目标缺陷。
2. 必须保持 plan 的 `preserve` 里列出的格式不变量；做不到就把这条写进 limits。
3. 输出长度必须 ≤ MaxSize；任何情况下都要返回合法值（失败时返回原输入副本）。
4. 只使用标准库和 libFuzzer 提供的接口。
6. 每个策略函数都要自己做边界检查（`MaxSize`、行长、`memmove` 范围），失败时原样返回。
7. **行切分必须同时兼容 `\n`、`\r\n`、`\r`。** 计划里的 `input_contract.line_endings`
   和 `sample_hex` 是真实字节，照着它写；遇到 CRLF 只认 `\n` 会一行都解析不出来。
8. 必须真的能改动输入：`sample_hex` 里给出了段名后面的第一条记录，策略要能定位并改它。
9. **禁止用固定候选值列表。** `new_value_policy.kind = random_unrecognized_name` 的意思是：
   值必须**由 Seed 推导生成**（长度在 `length` 区间内、字符取自 `alphabet`），
   不能写成 `{"FUZZ_OBJECT","AAAAAAAA","\x7f"}` 这种 2~3 个固定常量——
   那样 1000 个 Seed 只会产出个位数不同结果，等于半个预算在造重复。
8. **`locator.pick = random_k`**：段内通常有多条同组码记录，必须按 Seed 随机选第 k 条，
   不能永远改第一条。
11. **格式分流**：`input_contract.format_scope` 之外的输入，必须**调用 `LLVMFuzzerMutate`**，
    **不能返回原输入**——返回原输入等于这次迭代什么也没做，白白浪费一半预算。
    llvmfuzz 的分流规则：前两字节 `AC` → DWG；首字节 `{` → JSON；其余 → DXF。
13. **`operation = ensure_record_structure` 时，策略函数必须有两条路径**：
    · **段存在**（能在输入里找到 `locator.section_anchor` 那一行）→ 现行为：
      按 `locator.pick=random_k` 选段内第 k 条 code-0 记录，替换它的**值行**；
    · **段不存在** → 按 `construct.sequence` 在 `construct.insert_position` 处
      插入完整结构（`0/SECTION` + `2/<anchor>` + `0/<随机非已知名>` + `0/ENDSEC`）。
    两条路径都必须做 `MaxSize` 边界检查、兼容 `\n`/`\r\n`/`\r`、失败返回原输入。
    **段不存在时不能返回原输入**（那是空转）。
14. 只输出 JSON，不要解释文字，不要 markdown 包裹。"""

USER_GEN = """# Mutation Plan（已冻结，status={status}）

```json
{plan}
```

# 被绑定的特征（只作解释参考）

- id: {feature_id}
- 名称: {feature_name}
- mutation_target:
{mutation_target}

# 证据行（源码原文，供你写注释用）

{evidence}

# 任务

把 plan 实现成 `LLVMFuzzerCustomMutator`。输出 JSON：

{{
  "mutator": {{
    "name": "string",
    "strategy": "一句话",
    "implements_action_ids": ["a001", "a002", "..."],
    "dispatch": {{"default": 0.5, "features": {{"a001": 0.1, "a002": 0.1}}}},
    "biases": [{{"action_id": "a001", "code_hint": "string", "basis": "plan 里哪条"}}],
    "code": "完整的 C 代码字符串"
  }},
  "limits": ["说明哪些地方没把握"],
  "confidence": "high | medium | low"
}}
"""

SIG = "LLVMFuzzerCustomMutator"


def die(msg: str, code: int = 2):
    print(f"[stage5.v2] plan_status=BLOCKED  {msg}", file=sys.stderr)
    sys.exit(code)



DRIVER = r"""
#include <stddef.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
static long g_default_calls = 0;
size_t LLVMFuzzerMutate(uint8_t *D, size_t S, size_t M) {
  (void)D; (void)M;
  g_default_calls++;         /* 只计数、不改数据：这样 CHANGED/DISTINCT/DIFF 只反映特征路径 */
  return S;
}
#define LLVMFuzzerCustomMutator PLAN_MUT
#include "gen.c"
static void dump_rec(const uint8_t *d, size_t n) {
  size_t i = 0; int found = 0;
  for (i = 0; i + 7 <= n; i++) if (memcmp(d + i, "OBJECTS", 7) == 0) { found = 1; break; }
  if (!found) { fprintf(stderr, "REC ?\n"); return; }
  fprintf(stderr, "REC ");
  size_t j = i + 7;
  for (size_t k = 0; k < 140 && j + k < n; k++) {
    unsigned char c = d[j + k];
    fputc((c == '\n' || c == '\r') ? '|' : ((c >= 32 && c < 127) ? (int)c : '?'), stderr);
  }
  fputc('\n', stderr);
}

int main(int argc, char **argv) {
  if (argc < 2) return 2;
  FILE *f = fopen(argv[1], "rb");
  if (!f) return 3;
  static uint8_t a[8 << 20], b[8 << 20];
  size_t n = fread(a, 1, sizeof a, f);
  fclose(f);
  int total = (argc > 2) ? atoi(argv[2]) : 1000;
  const char *dump_path = (argc > 3) ? argv[3] : NULL;
  int dumped = 0;
  int unchanged = 0, changed = 0, ndump = 0;
  static unsigned long seen[4096]; int nseen = 0;
  unsigned long sig = 1469598103u;
  for (int s = 0; s < total; s++) {
    memcpy(b, a, n);
    size_t m = PLAN_MUT(b, n, sizeof b, (unsigned)s);
    if (m == n && memcmp(b, a, n) == 0) { unchanged++; continue; }
    changed++;
    if (dump_path && !dumped) {
      FILE *o = fopen(dump_path, "wb");
      if (o) { fwrite(b, 1, m, o); fclose(o); dumped = 1; }
    }
    {
      unsigned long h = 1469598103ul;
      for (size_t i = 0; i < m; i++) h = (h ^ b[i]) * 16777619ul;
      h ^= (unsigned long)m;
      int dup = 0;
      for (int i = 0; i < nseen; i++) if (seen[i] == h) { dup = 1; break; }
      if (!dup && nseen < 4096) seen[nseen++] = h;
    }
    if (s % 10 == 0 && ndump < 60) {
      size_t lim = (m < n) ? m : n, k = 0;
      while (k < lim && b[k] == a[k]) k++;
      fprintf(stderr, "DIFF %zu\n", k);
      ndump++;
    }
    for (size_t i = 0; i < m; i++) sig = (sig ^ b[i]) * 16777619u;   /* 输出指纹 */
    sig = (sig ^ (unsigned long)m) * 16777619u;
  }
  fprintf(stderr, "UNCHANGED %d CHANGED %d DISTINCT %d DEFAULT %ld SIG %lu\n",
          unchanged, changed, nseen, g_default_calls, sig);
  printf("%d %d %d %ld %lu\n", unchanged, changed, nseen, g_default_calls, sig);
  return 0;
}
"""



def _lines_of(b):
    out = []; i = 0; n = len(b)
    while i < n:
        j = i
        while j < n and b[j] not in (10, 13):
            j += 1
        out.append(b[i:j])
        i = (j + 2) if (j < n and b[j] == 13 and j + 1 < n and b[j + 1] == 10) else (
            j + 1 if j < n else j)
    return out


def _has_structure(blob, anchor: bytes = b"OBJECTS"):
    """校验构造路径产出：存在 0/SECTION、2/OBJECTS、>=1 条 code-0 记录。"""
    L = _lines_of(blob)
    oi = None
    for k in range(len(L) - 1):
        if L[k].strip() == b"2" and L[k + 1].strip() == anchor:
            oi = k
            break
    if oi is None:
        return False, False, 0
    has_sec = any(L[k].strip() == b"0" and L[k + 1].strip() == b"SECTION"
                  for k in range(max(0, oi - 2), oi))
    n0 = 0
    k = oi + 1
    while k < len(L) - 1:
        if L[k].strip() == b"0":
            if L[k + 1].strip() == b"ENDSEC":
                break
            n0 += 1
        k += 1
    return has_sec, True, n0

def _record_after(blob: bytes, anchor: bytes = b"OBJECTS"):
    """取 anchor 之后第一条 "码行 / 值行"，返回 (码, 值)。"""
    i = blob.find(anchor)
    if i < 0:
        return None, None
    lines = blob[i + len(anchor):].replace(b"\r\n", b"\n").split(b"\n")
    lines = [x for x in lines[:6]]
    for k in range(len(lines) - 1):
        code = lines[k].strip()
        if re.fullmatch(rb"\d{1,3}", code):
            return code, lines[k + 1]
    return None, None


def check_behavior(code: str, plan: dict, seed_path: str, workdir: str,
                   other_seed: str | None = None,
                   gate_seed: str | None = None) -> list[str]:
    """实际跑算子：① 实测 default 权重 ② 检查"改值行"类策略真的改了值行。"""
    if not seed_path or not os.path.isfile(seed_path):
        return [f"行为校验跳过：找不到种子 {seed_path}"]
    if not shutil.which("clang"):
        return ["行为校验跳过：没有 clang"]
    d = tempfile.mkdtemp(prefix="behav_", dir=workdir)
    open(os.path.join(d, "gen.c"), "w", encoding="utf-8").write(code)
    open(os.path.join(d, "drv.c"), "w", encoding="utf-8").write(DRIVER)
    exe = os.path.join(d, "drv")
    r = subprocess.run(["clang", "-O0", "-std=c11", "-w", os.path.join(d, "drv.c"),
                        "-o", exe], capture_output=True, text=True)
    if r.returncode != 0:
        return ["行为校验失败：编译不过 " + (r.stderr or "")[:400].replace("\n", " | ")]
    r = subprocess.run([exe, seed_path, "1000"], capture_output=True, timeout=300,
                       text=True, errors="replace")
    if r.returncode != 0:
        return [f"行为校验失败：驱动返回 {r.returncode}"]

    bad = []
    m = re.search(r"UNCHANGED (\d+) CHANGED (\d+) DISTINCT (\d+) DEFAULT (\d+)",
                  r.stderr or "")
    if not m:
        return ["行为校验失败：驱动没有输出统计"]
    un, ch, distinct, ndefault = (int(m.group(i)) for i in (1, 2, 3, 4))
    total = un + ch
    want = float((plan.get("weighting") or {}).get("default") or 0.5)
    frac = ndefault / total if total else 0.0   # 精确：default 被调用了几次
    if not (want - 0.15 <= frac <= want + 0.15):
        bad.append(f"default 权重不对：计划 {want:.2f}，实测 {frac:.2f}"
                   f"（default 被调用 {ndefault}/{total}）")

    need_dist = int((plan.get("mutation_space") or {}).get("min_distinct_outputs") or 0)
    if need_dist and distinct < need_dist:
        bad.append(f"有效变异空间太小：1000 个 Seed 只产出 {distinct} 个互不相同的输出，"
                   f"要求 ≥ {need_dist}（固定候选列表或没有随机化都会这样）")

    # 门禁 5：构造路径有效性（在**剥掉 OBJECTS 段**的种子上跑）
    constructing = any(op == "ensure_record_structure"
                       for op in ([a.get("operation") for a in plan.get("mutations") or []]
                                  + [x for a in plan.get("mutations") or []
                                     for x in (a.get("operation_paths") or [])]))
    if gate_seed and os.path.isfile(gate_seed):
        dpath = os.path.join(d, "mutant.bin")
        r3 = subprocess.run([exe, gate_seed, "1000", dpath], capture_output=True,
                            timeout=600, text=True, errors="replace")
        m3 = re.search(r"UNCHANGED (\d+) CHANGED (\d+) DISTINCT (\d+) DEFAULT (\d+)",
                       r3.stderr or "")
        if not m3:
            bad.append("构造路径门禁：驱动在剥段种子上没有输出统计")
        else:
            ch3 = int(m3.group(2))
            if ch3 < 400:
                bad.append(f"构造路径无效：剥掉 OBJECTS 的种子上 1000 Seed 只改动 {ch3} 次"
                           f"（要求 ≥ 400；当前算子应为 0）")
            elif os.path.isfile(dpath):
                blob = open(dpath, "rb").read()
                hs, ho, n0 = _has_structure(blob)
                if not (hs and ho and n0 >= 1):
                    bad.append(f"构造路径产出的不是合法结构：0/SECTION={hs} "
                               f"2/OBJECTS={ho} 段内 code-0 记录数={n0}")

    # 格式分流：format_scope 之外的输入必须全部走 default（否则那部分预算空转）
    if other_seed and os.path.isfile(other_seed):
        r2 = subprocess.run([exe, other_seed, "1000"], capture_output=True, timeout=300,
                            text=True, errors="replace")
        m2 = re.search(r"UNCHANGED (\d+) CHANGED (\d+) DISTINCT (\d+) DEFAULT (\d+)",
                       r2.stderr or "")
        if m2:
            un2, ch2, _d2, def2 = (int(m2.group(i)) for i in (1, 2, 3, 4))
            tot2 = un2 + ch2
            frac2 = def2 / tot2 if tot2 else 0.0
            if frac2 < 0.95:
                bad.append(f"格式没分流：在非目标格式的输入上只有 {frac2:.0%} 走 default；"
                           f"format_scope 之外的输入必须全部交给 LLVMFuzzerMutate")

    src = open(seed_path, "rb").read()
    need_value = any(a.get("target_part") == "value_line"
                     for a in plan.get("mutations") or [])
    if need_value and ch and src.find(b"OBJECTS") >= 0:
        objs = src.find(b"OBJECTS")
        offs = [int(x) for x in re.findall(r"^DIFF (\d+)$", r.stderr or "", re.M)]
        inside_code_line = 0
        before_section = 0
        checked = 0
        for off in offs:
            if off >= len(src):
                continue
            ls = src.rfind(b"\n", 0, off) + 1
            le = src.find(b"\n", off)
            le = len(src) if le < 0 else le
            line = src[ls:le].strip()
            checked += 1
            if re.fullmatch(rb"\d{1,3}", line):
                inside_code_line += 1      # 改到了组码行 → 违反 preserve
            if objs >= 0 and off <= objs and not constructing:
                before_section += 1        # 改到段名之前 → 不在目标区域
                                           # （构造路径下段本来就不存在，不适用）
        if checked == 0:
            bad.append("没有观察到任何差异采样，无法确认 value_line 策略生效")
        elif inside_code_line:
            bad.append(f"{inside_code_line}/{checked} 个采样改到了组码行，违反 "
                       f"preserve=group_code_digits（应只改值行）")
        elif before_section:
            bad.append(f"{before_section}/{checked} 个采样改在 OBJECTS 段之前")
    return bad


def check_code(code: str, plan: dict) -> list[str]:
    """生成后的机械校验。返回问题列表（空 = 通过）。"""
    bad = []
    if SIG not in code:
        bad.append(f"缺少 {SIG} 接口")
    if "MaxSize" not in code:
        bad.append("没有使用 MaxSize 做长度边界")
    anchors = {a.get("locator", {}).get("section_anchor") for a in plan.get("mutations") or []}
    anchors = {x for x in anchors if x}
    if anchors and not any(a in code for a in anchors):
        bad.append(f"没有引用 plan 的段锚点 {sorted(anchors)}")
    codes = {a.get("locator", {}).get("anchor") for a in plan.get("mutations") or []}
    codes = {x for x in codes if x}
    if codes and not any(str(c) in code for c in codes):
        bad.append(f"没有引用 plan 的字段锚点 {sorted(codes)}")
    if not re.search(r"memcpy|memmove", code):
        bad.append("没有把原输入拷出来（失败时无法返回原输入）")
    if "LLVMFuzzerMutate" not in code:
        bad.append("没有保留 default 变异（未调用 LLVMFuzzerMutate）→ 探索会停")
    for a in plan.get("mutations") or []:
        aid = a.get("action_id")
        if aid and aid.replace("a", "") and str(aid)[1:] not in code and aid not in code:
            bad.append(f"代码里没有对应 action {aid} 的策略函数（建议在注释里标注 action id）")
    return bad


def main_generate():
    ap = argparse.ArgumentParser(description="阶段5.5：从 ready plan 生成 mutator")
    ap.add_argument("--plan", default=None)
    ap.add_argument("--out", default=None)
    ap.add_argument("--osv", default=None)
    ap.add_argument("--model", default=os.environ.get("GEN_MODEL", "deepseek-chat"))
    ap.add_argument("--seed", default=None, help="行为校验用的种子（默认 seeds/ 第一个）")
    ap.add_argument("--retries", type=int, default=3,
                    help="LLM 生成的重试次数（默认 3；0 等价于 1）")
    ap.add_argument("--max-tokens", type=int, default=48000,
                    help="单次生成的 token 上限（默认 48000，给 reasoning 留余量）")
    ap.add_argument("--dry-run", action="store_true", help="只打印 prompt 长度，不调用模型")
    args = ap.parse_args()

    if args.plan:
        pp = args.plan
        outdir = args.out or os.path.dirname(os.path.abspath(pp))
    elif args.osv:
        outdir = os.path.join(OUT, args.osv, "v2")
        pp = os.path.join(outdir, "mutation_plan.json")
    else:
        die("必须给 --plan 或 --osv")

    if not os.path.exists(pp):
        print(f"[stage5.v2] plan 不存在 not found: {pp}", file=sys.stderr)
        sys.exit(2)

    plan = json.load(open(pp, encoding="utf-8"))
    status = plan.get("status")
    if status != "ready":
        die(f"plan status={status}，blockers={plan.get('blockers')}；拒绝生成 mutator.c")
    if not (plan.get("mutations") or []):
        die("plan 里没有 mutations")

    # 特征摘要（可选）
    aids = [a.get("feature_id") for a in (plan.get("mutations") or [])]
    feature = {"id": (aids[0] if aids else None)}
    if args.osv:
        fp = os.path.join(ROOT, "outputs", "stage4", "uaf", "features.json")
        if os.path.exists(fp):
            for f in json.load(open(fp, encoding="utf-8")).get("features") or []:
                if f.get("id") == feature["id"]:
                    feature = f
                    break

    # 证据行（少量，不塞全量源码）
    ev = []
    cf = os.path.join(outdir, "candidate_findings.json")
    if os.path.exists(cf):
        d = json.load(open(cf, encoding="utf-8"))
        for x in (d.get("findings") or []):
            if x.get("function") == (plan.get("targets") or [{}])[0].get("function"):
                ev = [[e[0], e[1]] for e in (x.get("evidence_lines") or [])][:6]
                break

    mt = feature.get("mutation_target") or []
    prompt = SYSTEM_GEN + "\n\n" + USER_GEN.format(
        status=status, plan=json.dumps(plan, ensure_ascii=False, indent=1),
        feature_id=feature.get("id"), feature_name=feature.get("feature_name"),
        mutation_target="\n".join(f"  - {x}" for x in mt) or "  - （无）",
        evidence="\n".join(f"  L{e[0]}: {e[1]}" for e in ev) or "  （无）")

    print(f"[stage5.v2] plan_status=READY  plan={pp}")
    print(f"  prompt 字符数: {len(prompt)}（只含 plan + {len(ev)} 行证据）")
    if args.dry_run:
        return

    from s3_extract_patterns import call_llm
    # 生成步是 LLM 调用，**天然不稳定**：模型 reasoning 偶尔吃掉整个 max_tokens
    # （finish_reason=length），或者产出的代码过不了行为门禁。两者重试都可能解决，
    # 所以这里做有限重试；重试用尽才失败。--retries 0 表示只跑一次。
    tries = max(1, args.retries)
    obj, code = None, None
    for attempt in range(1, tries + 1):
        if attempt > 1:
            print(f"  [retry {attempt}/{tries}] 上一次失败，重新生成…", file=sys.stderr)
        try:
            txt = call_llm(prompt, max_tokens=args.max_tokens)
        except RuntimeError as e:
            print(f"  ✗ [retry {attempt}/{tries}] {e}", file=sys.stderr)
            continue
        m = re.search(r"\{.*\}", txt, re.S)
        if not m:
            print(f"  ✗ [retry {attempt}/{tries}] 模型没有返回 JSON", file=sys.stderr)
            continue
        obj = json.loads(m.group(0))
        mut = obj.get("mutator") or {}
        code = mut.get("code") or ""
        if not code.strip():
            print(f"  ✗ [retry {attempt}/{tries}] mutator.code 为空", file=sys.stderr)
            continue
        break
    if not code or not code.strip():
        print(f"[stage5.v2] 连续 {tries} 次都没拿到可用代码", file=sys.stderr)
        sys.exit(3)

    bad = check_code(code, plan)
    sd = os.path.join(OUT, args.osv, "seeds") if args.osv else None
    want = (plan.get("input_contract") or {}).get("seed_file")
    seedp = args.seed or (os.path.join(sd, want) if (sd and want and
                          os.path.isfile(os.path.join(sd, want))) else None)
    if not seedp and sd and os.path.isdir(sd):
        seedp = next((os.path.join(sd, f) for f in sorted(os.listdir(sd))
                      if f.endswith(".dxf")), None)
    otherp = None
    if sd and os.path.isdir(sd):
        otherp = next((os.path.join(sd, f) for f in sorted(os.listdir(sd))
                       if f.endswith(".dwg")), None)
    gatep = None
    gd = os.path.join(OUT, args.osv, "v2", "experiment", "gate_seeds")
    if os.path.isdir(gd):
        gatep = next((os.path.join(gd, f) for f in sorted(os.listdir(gd))
                      if f.endswith(".dxf")), None)
    bad += check_behavior(code, plan, seedp, tempfile.mkdtemp(prefix="stage5_"),
                          other_seed=otherp, gate_seed=gatep)
    if bad:
        print("[stage5.v2] 生成后校验失败：", file=sys.stderr)
        for b in bad:
            print(f"  ✗ {b}", file=sys.stderr)
        # 保留被拒的代码，便于复查（不写 mutator.c）
        rej = os.path.join(outdir, "mutator_rejected.c")
        open(rej, "w", encoding="utf-8").write(code)
        json.dump({"problems": bad, "mutator": mut, "limits": obj.get("limits")},
                  open(os.path.join(outdir, "mutator_rejected.json"), "w", encoding="utf-8"),
                  ensure_ascii=False, indent=1)
        print(f"  被拒代码已保存到 {rej}", file=sys.stderr)
        sys.exit(4)

    os.makedirs(outdir, exist_ok=True)
    rec = {
        "schema_version": "stage5.mutator.v2",
        "target": plan.get("target"),
        "provenance": {"plan_file": os.path.relpath(pp, outdir),
                       "binding_file": "feature_bindings.json",
                       "finding_file": "candidate_findings.json",
                       "source_commit": (plan.get("target") or {}).get("commit")},
        "generation_gate": {"plan_status": status, "evidence_check": "pass",
                            "compile_check": "pending", "replay_check": "pending"},
        "mutator": mut,
        "limits": obj.get("limits") or [],
        "confidence": obj.get("confidence"),
    }
    json.dump(rec, open(os.path.join(outdir, "mutator.json"), "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)
    open(os.path.join(outdir, "mutator.c"), "w", encoding="utf-8").write(code)
    print(f"  写出 {outdir}/mutator.json 和 mutator.c（{len(code)} 字节）")
    print(f"  implements: {mut.get('implements_action_ids')}")

# ══════════════════════════════════════════════════════════════════════
# 5.8 V1 schema / V2 evidence / V3 code / V4 behavior（原 s5_verify_mutator_v2.py）
# ══════════════════════════════════════════════════════════════════════

"""s5_verify_mutator_v2.py —— 阶段5.6：V2 的统一验证门禁

四层门禁
  V1 schema   ：各层 schema_version / commit / plan_id 一致；blocked 不得继续
  V2 evidence ：源码文件存在、行号合法、代码片段是该行子串、每个 action 有 basis_refs 且可解析
  V3 code     ：C11 语法通过、接口签名正确、用了 MaxSize 边界、能拷原输入
  V4 behavior ：已知 crash 输入可重放、种子能被 parser 接受（需要 --binary，否则 not_applicable）

输出 verification.json，每层状态为 pass / fail / not_applicable / blocked。

用法
  python3 s5_verify_mutator_v2.py --osv ARVO-42494732
  python3 s5_verify_mutator_v2.py --osv ARVO-42494732 --binary /exp/fuzz_exp/llvmfuzz
"""

import argparse
import json
import os
import re
import subprocess
import sys
import tempfile


SHIM = """#include <stddef.h>
#include <stdint.h>
size_t LLVMFuzzerMutate(uint8_t *Data, size_t Size, size_t MaxSize);
"""


def load_verify(p):
    return json.load(open(p, encoding="utf-8")) if os.path.exists(p) else None


def gate_v1(manifest, surface, findings, bindings, plan, mutator):
    problems, notes = [], []
    for name, doc in (("manifest", manifest), ("target_surface", surface),
                      ("candidate_findings", findings), ("feature_bindings", bindings),
                      ("mutation_plan", plan), ("mutator", mutator)):
        if not doc:
            problems.append(f"{name} 缺失")
        elif not doc.get("schema_version"):
            problems.append(f"{name} 缺 schema_version")
    if plan:
        if plan.get("status") != "ready":
            problems.append(f"plan status={plan.get('status')}（blocked 不得继续）")
        if mutator and (mutator.get("generation_gate") or {}).get("plan_status") != "ready":
            problems.append("mutator.generation_gate.plan_status != ready")
        commits = {str((d.get("target") or {}).get("commit"))
                   for d in (surface, findings, plan, mutator) if d}
        commits.discard("None")
        if len(commits) > 1:
            problems.append(f"commit 不一致: {sorted(commits)}")
        if not (plan.get("mutations") or []):
            problems.append("plan 没有 mutations")
    notes.append(f"documents={sum(1 for d in (manifest, surface, findings, bindings, plan, mutator) if d)}/6")
    return ("pass" if not problems else "fail"), problems, notes


def gate_v2(source_root, findings, plan):
    problems, notes = [], []
    for x in (findings or {}).get("findings") or []:
        rel, ev = x.get("file"), x.get("evidence_lines") or []
        p = os.path.join(source_root, rel) if rel else None
        if not p or not os.path.isfile(p):
            problems.append(f"{x.get('finding_id')}: 源文件缺失 {rel}")
            continue
        lines = open(p, encoding="utf-8", errors="replace").read().split("\n")
        for e in ev:
            try:
                ln, code = int(e[0]), str(e[1])
            except (TypeError, ValueError, IndexError):
                problems.append(f"{x.get('finding_id')}: 证据行格式错 {e}")
                continue
            if not (1 <= ln <= len(lines)):
                problems.append(f"{x.get('finding_id')}: L{ln} 越界")
            elif "".join(code.split()) not in "".join(lines[ln - 1].split()):
                problems.append(f"{x.get('finding_id')}: L{ln} 原文不符")
    for a in (plan or {}).get("mutations") or []:
        if not a.get("basis_refs"):
            problems.append(f"{a.get('action_id')}: 没有 basis_refs")
    notes.append(f"actions={(plan or {}).get('mutations') and len(plan['mutations'])}")
    return ("pass" if not problems else "fail"), problems, notes


def gate_v3(code: str, shim_dir: str) -> tuple:
    problems, notes = [], []
    if not code.strip():
        return "fail", ["mutator.c 为空"], notes
    if "LLVMFuzzerCustomMutator" not in code:
        problems.append("缺少 LLVMFuzzerCustomMutator 接口")
    if "MaxSize" not in code:
        problems.append("没有用 MaxSize 做边界")
    if not re.search(r"memcpy|memmove", code):
        problems.append("没有拷出原输入")
    tmp = tempfile.mkdtemp(prefix="v3_")
    shim = os.path.join(tmp, "shim.c")
    open(shim, "w", encoding="utf-8").write(SHIM + f'\n#include "{os.path.abspath(os.path.join(shim_dir, "mutator.c"))}"\n')
    r = subprocess.run(["clang", "-fsyntax-only", "-std=c11", "-Wall", "-Wextra", shim],
                       capture_output=True, text=True)
    if r.returncode != 0:
        problems.append("clang 语法检查失败: " + (r.stderr or "")[:400].replace("\n", " | "))
    else:
        notes.append("clang -fsyntax-only 通过")
    return ("pass" if not problems else "fail"), problems, notes


def gate_v4(binary: str, ctx: dict) -> tuple:
    if not binary or not os.path.exists(binary):
        return "not_applicable", [], ["没有提供 --binary，跳过行为门禁"]
    problems, notes = [], []
    tc = ctx.get("testcase_path") or ctx.get("testcase")
    if tc and os.path.isfile(tc):
        r = subprocess.run([binary, "-runs=1", tc], capture_output=True, text=True, timeout=300)
        blob = (r.stdout or "") + (r.stderr or "")
        m = re.search(r"SUMMARY: AddressSanitizer: (\S+) (\S+?):(\d+)", blob)
        if m:
            notes.append(f"已知 crash 回放: {m.group(1)} {m.group(2)}:{m.group(3)}")
        else:
            problems.append("已知 crash 无法回放（没有 ASan SUMMARY）")
    else:
        notes.append("没有 testcase 路径，跳过回放")
    return ("pass" if not problems else "fail"), problems, notes


def main_verify():
    ap = argparse.ArgumentParser(description="阶段5.6：V2 统一验证门禁")
    ap.add_argument("--osv", required=True)
    ap.add_argument("--binary", default=None)
    args = ap.parse_args()

    V2 = os.path.join(OUT, args.osv, "v2")
    manifest = load_verify(os.path.join(V2, "manifest.json"))
    surface = load_verify(os.path.join(V2, "target_surface.json"))
    findings = load_verify(os.path.join(V2, "candidate_findings.json"))
    bindings = load_verify(os.path.join(V2, "feature_bindings.json"))
    plan = load_verify(os.path.join(V2, "mutation_plan.json"))
    mutator = load_verify(os.path.join(V2, "mutator.json"))
    codep = os.path.join(V2, "mutator.c")
    code = open(codep, encoding="utf-8").read() if os.path.exists(codep) else ""
    ctx = load_verify(os.path.join(OUT, args.osv, "source_context.json")) or {}
    root = ctx.get("repo_local") or ""

    res = {}
    for name, (st, prob, notes) in (
            ("V1_schema", gate_v1(manifest, surface, findings, bindings, plan, mutator)),
            ("V2_evidence", gate_v2(root, findings, plan)),
            ("V3_code", gate_v3(code, V2)),
            ("V4_behavior", gate_v4(args.binary, ctx))):
        res[name] = {"status": st, "problems": prob, "notes": notes}

    allst = [v["status"] for v in res.values()]
    overall = ("fail" if "fail" in allst else
               "blocked" if "blocked" in allst else
               "pass_with_skipped" if "not_applicable" in allst else "pass")
    out = {"schema_version": "stage5.verification.v1",
           "target": (plan or {}).get("target"),
           "gates": res, "overall": overall,
           "commands": {"V3": "clang -fsyntax-only -std=c11 -Wall -Wextra (shim)"}}
    json.dump(out, open(os.path.join(V2, "verification.json"), "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)

    print(f"=== {args.osv} verification ===")
    for k, v in res.items():
        print(f"  {k:<14} {v['status'].upper():<16} {len(v['problems'])} 问题")
        for p in v["problems"][:4]:
            print(f"      ✗ {p}")
        for n in v["notes"][:2]:
            print(f"      · {n}")
    print(f"\n  overall = {overall}")
    print(f"  写出 {os.path.join(V2, 'verification.json')}")
    return 0 if overall in ("pass", "pass_with_skipped") else 1

# ══════════════════════════════════════════════════════════════════════
# CLI
# ══════════════════════════════════════════════════════════════════════

def _run(fn, argv):
    """按 argv 调某个阶段函数，返回退出码。"""
    old = sys.argv
    sys.argv = ["s5_mutator"] + argv
    try:
        rc = fn()
    except SystemExit as e:
        rc = e.code if isinstance(e.code, int) else (0 if e.code is None else 1)
    except Exception as e:                                      # noqa: BLE001
        print(f"\n[stage5] 抛出 {type(e).__name__}: {e}", file=sys.stderr)
        rc = 1
    finally:
        sys.argv = old
    return rc or 0


def main():
    ap = argparse.ArgumentParser(
        description="阶段5 统一入口：prepare / audit / analyze / build / all / list")
    ap.add_argument("stage", choices=[
        "prepare", "audit", "analyze", "build", "all", "list",
        # 单阶段直通（参数原样转发给该阶段自己）
        "fetch", "worklist", "surface", "findings", "features", "plan",
        "generate", "verify", "mech", "interproc", "feat-audit"])
    ap.add_argument("--osv", default=None)
    ap.add_argument("--type", default="uaf")
    ap.add_argument("--depth", type=int, default=2)
    ap.add_argument("--default-weight", type=float, default=0.5)
    ap.add_argument("--feature", default=None)
    ap.add_argument("--with-audit", action="store_true")
    ap.add_argument("--all-chunks", action="store_true")
    ap.add_argument("--chunk", action="append", type=int, help="只跑这些批次（可重复）")
    ap.add_argument("--merge", action="store_true", help="只合并已有批次 → vuln_report.json")
    ap.add_argument("--model", default=None)
    ap.add_argument("--max-turns", type=int, default=None)
    ap.add_argument("--retries", type=int, default=3)
    ap.add_argument("--binary", default=None)
    args, extras = ap.parse_known_args()
    osv = args.osv

    # 单阶段直通：不去猜它的参数，原样转发
    passthrough = {"fetch": main_fetch, "worklist": main_worklist,
                   "surface": main_surface, "findings": main_findings,
                   "features": main_features, "plan": main_plan,
                   "generate": main_generate, "verify": main_verify}
    if args.stage in passthrough:
        argv = list(extras)
        if args.stage == "fetch":
            argv = ([osv] if osv else []) + argv          # 位置参数
        elif osv and "--osv" not in argv:
            argv = ["--osv", osv] + argv                  # s5_mutator.py 吃掉了 --osv，补回
        return _run(passthrough[args.stage], argv)

    if args.stage in ("mech", "interproc", "feat-audit"):
        import s5_agent
        fn = {"mech": s5_agent.main_mech,
              "interproc": s5_agent.main_interproc,
              "feat-audit": s5_agent.main_feat_audit}[args.stage]
        argv = list(extras) + (["--osv", osv] if osv and "--osv" not in extras else [])
        return _run(fn, argv)

    if args.stage == "list":
        print("prepare: 5.0 fetch + 5.1 worklist")
        print("audit:   5.2 agent 审计 + 5.2b 机械规则 + 5.2c 跨函数 + 5.2d 特征审计  (s5_agent.py)")
        print("analyze: 5.3 surface + 5.4 findings + 5.5 features")
        print("build:   5.6 plan + 5.7 generate + 5.8 verify")
        print("单阶段直通: fetch / worklist / surface / findings / features / plan / generate / verify")
        return 0
    if not osv:
        ap.error("需要 --osv（例如 ARVO-42494732）")

    def prepare():
        for fn, argv in ((main_fetch, [osv]),
                         (main_worklist, ["--osv", osv, "--depth", str(args.depth)])):
            print(f"\n--- {fn.__name__}")
            rc = _run(fn, argv)
            if rc: return rc
        return 0

    def audit():
        if not (args.all_chunks or args.chunk or args.merge):
            print("\n[stage5] audit 需要显式给出范围：\n"
                  "  --all-chunks        跑全部 162 批（LLM，很贵）\n"
                  "  --chunk N --chunk M 只跑指定批次\n"
                  "  --merge             只把已有 audit_chunks/ 合并成 vuln_report.json（不调 LLM）",
                  file=sys.stderr)
            return 2
        import s5_agent
        for fn, argv in ((s5_agent.main_audit,
                          ["--osv", osv] + (["--all-chunks"] if args.all_chunks else [])
                          + sum((["--chunk", str(c)] for c in args.chunk or []), [])
                          + (["--merge"] if args.merge else [])
                          + (["--model", args.model] if args.model else [])
                          + (["--max-turns", str(args.max_turns)] if args.max_turns else [])),
                         (s5_agent.main_mech, ["--osv", osv])) if not args.merge else (
                         (s5_agent.main_audit,
                          ["--osv", osv] + (["--all-chunks"] if args.all_chunks else [])
                          + sum((["--chunk", str(c)] for c in args.chunk or []), [])
                          + ["--merge"]),):
            print(f"\n--- {fn.__name__}")
            rc = _run(fn, argv)
            if rc: return rc
        return 0

    def analyze():
        for fn, argv in ((main_surface, ["--osv", osv]),
                         (main_findings, ["--osv", osv]),
                         (main_features, ["--osv", osv, "--type", args.type,
                                          "--default-weight", str(args.default_weight)]
                          + (["--feature", args.feature] if args.feature else ["--all"]))):
            print(f"\n--- {fn.__name__}")
            rc = _run(fn, argv)
            if rc: return rc
        return 0

    def build():
        for fn, argv in ((main_plan, ["--osv", osv, "--default-weight",
                                      str(args.default_weight)]),
                         (main_generate, ["--osv", osv, "--retries", str(args.retries)]
                          + (["--model", args.model] if args.model else [])),
                         (main_verify, ["--osv", osv]
                          + (["--binary", args.binary] if args.binary else []))):
            print(f"\n--- {fn.__name__}")
            rc = _run(fn, argv)
            if rc: return rc
        return 0

    fns = {"prepare": prepare, "audit": audit, "analyze": analyze, "build": build}
    if args.stage == "all":
        for name in ("prepare", "audit", "analyze", "build"):
            if name == "audit" and not args.with_audit:
                print("\n（跳过 audit：需要时加 --with-audit）")
                continue
            print(f"\n{'='*70}\n== stage5 · {name}\n{'='*70}")
            rc = fns[name]()
            if rc: return rc
        print("\n[stage5] all 完成")
        return 0
    return fns[args.stage]()


if __name__ == "__main__":
    sys.exit(main())

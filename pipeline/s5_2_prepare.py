#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""s5_2_prepare.py —— stage5 · prepare：5.0 抓源码 + 5.1 生成 worklist"""
from __future__ import annotations

import argparse, collections, glob, json, os, re, shutil, subprocess, sys, tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
TOP = os.path.dirname(ROOT)
OUT = os.path.join(ROOT, "projects")
if HERE not in sys.path:
    sys.path.insert(0, HERE)

from s5_6_lib import *                                          # noqa: E402,F401,F403


from s2_1_lib_cpg import SRCDIR, repo_dir, vuln_commit, ensure_src   # noqa: E402
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
from s2_1_lib_cpg import repo_dir, vuln_commit, SRCDIR, ensure_src

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
    """按大括号配平，抽出函数体。

    签名有两种常见写法，都要支持（2026-11-03 修正）：
      (a) 返回类型独占一行：`static void\n dxf_free_pair (...)`   （libredwg 风格）
      (b) 返回类型与函数名同行：`static int h2_session_send(...)`   （curl 风格）
    旧实现只认 (a)，遇到 (b) 会报 function_not_found。
    """
    cands = []
    for _pat in (re.compile(r"^\s*" + re.escape(fn) + r"\s*\(", re.M),
                 re.compile(r"^[A-Za-z_][\w \t\*]*\b" + re.escape(fn) + r"\s*\(", re.M)):
        cands.extend(_pat.finditer(src))
    if not cands:
        return None
    cands.sort(key=lambda x: x.start())

    m = None
    i = -1
    for _c in cands:
        _i = src.find("{", _c.end())
        if _i < 0:
            continue
        # 从签名末尾到 '{' 之间若出现 ';'，说明这是声明或调用，不是定义
        if ";" in src[_c.end():_i]:
            continue
        m, i = _c, _i
        break
    if m is None:
        return None
    # 向前找到函数签名起始
    start = src.rfind("\n", 0, m.start()) + 1
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

    # 已经手工放好的 harness 优先（有些项目的 fuzz target 在 submodule 或别的仓库里，
    # 只能人工取。预置文件的来源要记进 INTERVENTIONS.md）。
    pre = []
    for fn in sorted(os.listdir(d)):
        fp = os.path.join(d, fn)
        if not os.path.isfile(fp):
            continue
        try:
            t = open(fp, encoding="utf-8", errors="replace").read()
        except Exception:
            continue
        if re.search(r"LLVMFuzzerTestOneInput\s*\([^;]*\)\s*\{", t):
            pre.append({"repo_path": f"(preplaced) {fn}", "saved_as": fn,
                        "lines": t.count("\n") + 1})
    if pre:
        print(f"  harness: 使用已预置的 {[x['saved_as'] for x in pre]}（来源见 INTERVENTIONS.md）")
        return {"dir": "harness", "marker": HARNESS_MARK, "files": pre,
                "definition_files": [x["repo_path"] for x in pre],
                "source": "preplaced", "fuzz_target_name": rec.get("fuzz_target")}

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

    # 2026-11-03：搜不到就明确报错，不再静默留一个空目录
    # （空目录会让 input_format 悄悄退化成 raw_bytes，看起来像"这个项目就是二进制"）。
    if not defs:
        sub = ""
        gm = show_file(repo, commit, ".gitmodules")
        if gm:
            subs = re.findall(r"url\s*=\s*(\S+)", gm)
            if subs:
                sub = ("\n  该仓库有 submodule（" + ", ".join(subs[:3]) +
                       "）。harness 可能在其中：git grep 不会进入未初始化的 submodule，"
                       "需要单独去那些仓库里找。")
        raise SystemExit(
            f"harness_not_found: 在 {rec.get('project')}@{commit} 里找不到含 "
            f"{HARNESS_MARK} **定义**的文件（grep 到 {len(paths)} 个候选，0 个是定义）。\n"
            f"  没有 harness 就无法判断输入格式与分流，input_format 会退化成 raw_bytes。{sub}\n"
            f"  处理办法：把该 fuzz target 的源码手工放进 {d}/ 后再跑（记进 INTERVENTIONS.md）。")

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
    # 2026-11-06（R16）修：原来 `repo_local = repo`——那是**克隆的 HEAD**，
    # 而 CPG 是**按 pin 预建**的。两者版本不一致时，扫描器会拿 HEAD 的源码去套 pin 的行号。
    # 实测：leptonica 的 pin `90ec70fd` 里 `src/pix1.c:1665` 是
    #   `if (!valid) return ERROR_INT("colormap is not valid"…)`，
    # 而 HEAD 的同一行是 `pixFreeData(pix); pix->data = data;` —— 完全不同的代码。
    # 改成用 `ensure_src()` 把**该 commit** 的源码提取到独立目录。
    # 提取失败才退回克隆（并显式警告，不静默）。
    _pin = pin
    _src = None
    if _pin and has_commit(repo, _pin):
        try:
            _src = ensure_src(repo, _pin)
        except Exception as e:
            print(f"  ⚠️ 提取 pin 源码失败（{type(e).__name__}: {e}），退回克隆", flush=True)
    if _src:
        ctx["repo_local"] = _src
        ctx["repo_source"] = how + "+pin_src"
    else:
        ctx["repo_local"] = repo
        ctx["repo_source"] = how + "+HEAD(源码非 pin，行号可能错位)"
        print("  ⚠️ 源码用的是克隆 HEAD，不是 pin —— 行号可能与 CPG 错位", flush=True)

    commit = pin
    if not commit or not has_commit(repo, commit):
        # 先尝试补全历史（2026-11-03：原来直接静默退回 HEAD，会用错版本的源码）
        if not commit or not has_commit(repo, commit):
            print(f"  本地仓库缺 commit {pin}，尝试 fetch 补全…", flush=True)
            sh(["git", "-C", repo, "fetch", "--quiet", "--tags", "origin",
                "+refs/heads/*:refs/remotes/origin/*"], timeout=1800)
        if commit and has_commit(repo, commit):
            ctx["commit_fetched"] = f"{pin} 通过 fetch 补全"
        elif ALLOW_HEAD_FALLBACK:
            r = sh(["git", "-C", repo, "rev-parse", "HEAD"])
            commit = (r.stdout or "").strip()[:12]
            ctx["commit_fallback"] = f"{pin} 不可用，退回 HEAD（--allow-head-fallback）"
            print("\n  " + "!" * 70)
            print(f"  ⚠️  警告：pin {pin} 不可用，已按 --allow-head-fallback 退回 HEAD {commit}")
            print(f"  ⚠️  这意味着后续所有分析用的**不是**崩溃对应的那版源码！")
            print("  " + "!" * 70 + "\n", flush=True)
        else:
            raise SystemExit(
                f"commit_not_found: 要求 {pin}，本地仓库 {repo} 没有，"
                f"已尝试 fetch --tags 仍失败。\n"
                f"  拒绝退回 HEAD（那会用错版本的源码做分析）。\n"
                f"  人工排查可加 --allow-head-fallback。")
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
    ap.add_argument("--fault-anchor", action="store_true",
                    help="把故障函数（及其一层邻居）直接塞进清单。默认关闭："
                         "这是诊断开关，启用后结果不能用于论证『流程自己找到了站点』")
    args = ap.parse_args()

    ctxp = os.path.join(OUT, args.osv, "source_context.json")
    if not os.path.exists(ctxp):
        raise SystemExit(f"缺少 {ctxp}（先跑 s5_1_main.py fetch --osv {args.osv}）")
    ctx = json.load(open(ctxp, encoding="utf-8"))
    root, commit = ctx.get("repo_local"), ctx.get("commit_used") or ctx.get("pin_commit")
    project = ctx.get("project")
    if not (root and os.path.isdir(root)):
        raise SystemExit(f"仓库不存在: {root}")

    cpg = find_cpg(project, commit)
    if not cpg:
        raise SystemExit(f"找不到 CPG：{CPGDIR}/{project}_{str(commit)[:12]}.cpg\n"
                         f"（若要从当前 commit 新建，先跑 s2_2_facts.py 让 ensure_cpg 建图）")
    print(f"=== {args.osv} worklist ===")
    print(f"  仓库 : {root} @ {commit}")
    print(f"  CPG  : {os.path.basename(cpg)}")

    cache = os.path.join(OUT, args.osv, "cpg_dump.tsv")
    methods, edges = dump_cpg(cpg, cache)
    print(f"  方法 : {len(methods)} 个（外部 {sum(1 for m in methods if m['external'])}）；调用边 {len(edges)} 条")

    # CPG 覆盖校验（2026-11-03）：find_cpg() 只按文件名匹配，可能选到一个不含故障文件的图。
    # curl 实测：3625 个方法里 lib/http2.c 一条都没有，文件名匹配照样通过。
    fault_base = (ctx.get("fault_file") or "").split("/")[-1]
    if fault_base:
        file_hit = [m for m in methods if m["file"].endswith(fault_base)]
        if not file_hit:
            raise SystemExit(
                f"cpg_missing_fault_file: {os.path.basename(cpg)} 完全不覆盖 {fault_base}。\n"
                f"  该 CPG 建图时没有解析到这个文件，需重建（先跑 s2_2_facts.py 让 ensure_cpg 重建）。")
        print(f"  CPG 文件覆盖：{fault_base} 有 {len(file_hit)} 个方法")
        # 更关键的一条：故障函数本身在不在图里。锚点靠它，没有就锚不住。
        fn_hit = [m for m in file_hit
                  if m["name"] == ctx.get("fault_fn") and not m["external"]]
        if not fn_hit:
            names = sorted({m["name"] for m in file_hit})
            raise SystemExit(
                f"cpg_missing_fault_fn: {os.path.basename(cpg)} 的 {fault_base} 里没有 "
                f"{ctx.get('fault_fn')}（该文件只有 {len(file_hit)} 个方法：{names[:8]}）。\n"
                f"  常见原因：故障函数是 static、CPG 建图时没解析到它。\n"
                f"  没有它就无法 fault_anchor，站点扫描永远看不到该函数 → 需重建 CPG。")
        print(f"  CPG 故障函数：{ctx.get('fault_fn')} @ "
              f"{fn_hit[0]['file']}:{fn_hit[0]['start']}-{fn_hit[0]['end']} ✅")

    # 另一条独立告警：BFS 的根在不在图里（不在的话 depth 闭包必然为空）
    entry = HARNESS_MARK
    if not any(m["name"] == entry for m in methods):
        print(f"  ⚠️ CPG 里没有 {entry}（BFS 根缺失）→ depth<={args.depth} 闭包必然为空；"
              f"清单将完全依赖 fault_anchor")

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
                      "risk": tags, "source": "callgraph",
                      "chars": size_of(root, m["file"], m["start"], m["end"], size_cache)})

    # ── 故障锚点：无条件把故障函数及其一层邻居加进清单（2026-11-03 新增）──
    # 为什么：从 LLVMFuzzerTestOneInput 正向展开 depth≤2 会漏掉故障函数本身
    # （gpac 实测只展开到 12 个 isomedia/utils 函数，故障函数在两个模块之外）。
    # 这是**方法局限**，不是修复——入表的函数不在 depth≤2 闭包里，必须显式标注。
    fault_fn = ctx.get("fault_fn")
    fault_base = (ctx.get("fault_file") or "").split("/")[-1]
    anchor_added, neighbor_added = [], []
    # "故障函数在不在闭包里"是事实，与开关无关 → 永远算
    anchor_in_closure = bool(fault_fn) and any(
        f["name"] == fault_fn and (not fault_base or f["file"].endswith(fault_base))
        for f in funcs)
    if args.fault_anchor and fault_fn:
        have = {(f["file"], f["name"]) for f in funcs}
        am = next((x for x in methods
                   if x["name"] == fault_fn and not x["external"]
                   and x["name"] != "<global>"
                   and (not fault_base or x["file"].endswith(fault_base))), None)
        if am and (am["file"], am["name"]) not in have:
            tags = risk_tags(callees.get((am["file"], am["name"]), set()))
            funcs.append({"name": am["name"], "file": am["file"],
                          "lines": [am["start"], am["end"]], "depth": None,
                          "risk": tags, "source": "fault_anchor",
                          "chars": size_of(root, am["file"], am["start"], am["end"], size_cache)})
            have.add((am["file"], am["name"]))
            anchor_added.append(f'{am["name"]} ({am["file"]}:{am["start"]}-{am["end"]})')

        # 只在锚点**真正补位**（故障函数不在闭包里）时才追加邻居。
        # 否则闭包本身已包含它的邻域，追加会改变清单（实测 libredwg 162→165），
        # 违反"锚点应幂等"的要求。
        if am and anchor_added:
            # 一层邻居：直接被调用者 + 直接调用者
            neigh = set(callees.get((am["file"], am["name"]), set()))
            for cf, cn, cs in edges:
                if fault_fn in cs.split("|"):
                    neigh.add(cn)
            for nm in sorted(neigh):
                if nm.startswith("<operator>") or not re.match(r"^[A-Za-z_]", nm):
                    continue
                mm = next((x for x in methods
                           if x["name"] == nm and not x["external"]
                           and x["name"] != "<global>"), None)
                if not mm or (mm["file"], mm["name"]) in have:
                    continue
                tags = risk_tags(callees.get((mm["file"], mm["name"]), set()))
                funcs.append({"name": mm["name"], "file": mm["file"],
                              "lines": [mm["start"], mm["end"]], "depth": None,
                              "risk": tags, "source": "fault_neighbor",
                              "chars": size_of(root, mm["file"], mm["start"], mm["end"],
                                               size_cache)})
                have.add((mm["file"], mm["name"]))
                neighbor_added.append(mm["name"])

    # 排序（不是过滤）：含风险操作的优先，其次深度浅的，再其次大的
    funcs.sort(key=lambda f: (1 if args.no_risk_sort else (0 if f["risk"] else 1),
                              f["depth"] if f["depth"] is not None else 99,
                              -f["chars"], f["file"], f["lines"][0]))
    n_risk = sum(1 for f in funcs if f["risk"])
    src_cnt = {}
    for f in funcs:
        src_cnt[f.get("source")] = src_cnt.get(f.get("source"), 0) + 1
    print(f"  入表函数（不过滤，仅排序）: {len(funcs)} 个，其中含风险操作 {n_risk} 个")
    print(f"  来源分布: {src_cnt}")
    if args.fault_anchor:
        print("\n  " + "!" * 78)
        print("  ⚠️  fault_anchor 已启用：故障函数是被直接塞进清单的，**不是流程自己找到的**。")
        print("      此次结果不能用于论证「能在新项目上自主发现站点」。")
        print("  " + "!" * 78 + "\n", flush=True)
    if anchor_added:
        print(f"  ⚠️ 故障函数通过 fault_anchor 入表（**不在 depth<={args.depth} 闭包内**）："
              f"{', '.join(anchor_added)}")
        print(f"     直接邻居 fault_neighbor 追加 {len(neighbor_added)} 个：{neighbor_added[:8]}")
        print(f"     → 这是方法局限：闭包本身覆盖不到故障函数，清单靠锚点补上。")
    elif fault_fn and anchor_in_closure:
        print(f"  故障函数 {fault_fn} 已在 depth<={args.depth} 闭包内（无需锚点）")
    elif fault_fn and not args.fault_anchor:
        print(f"  ⚠️ 故障函数 {fault_fn} 不在 depth<={args.depth} 闭包里"
              f"（未启用 --fault-anchor；这正是「流程没能自己走到它」的情况）")
    elif fault_fn:
        print(f"  ⚠️ 故障函数 {fault_fn} 既不在 depth<={args.depth} 闭包里，也没能锚定"
              f"（CPG 里找不到名称+文件都匹配的方法）")

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
                     "fault_fn": fault_fn,
                     "covers_fault_line": cov,
                     "fault_fn_in_closure": anchor_in_closure,
                     "fault_anchor_enabled": bool(args.fault_anchor),
                     "fault_anchor_added": anchor_added,
                     "fault_neighbor_added": neighbor_added,
                     "source_counts": src_cnt},
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
        if not cov:
            # 覆盖不到已知崩溃行的清单不可信：不写出去让下游当成有效输入。
            raise SystemExit(
                f"worklist_does_not_cover_fault: 清单没有覆盖已知崩溃行 "
                f"{ctx.get('fault_file')}:{fault_line}。\n"
                f"  从 {HARNESS_MARK} 展开 depth<={args.depth} 得到 {len(funcs)} 个函数，够不到故障函数。\n"
                f"  可能原因：\n"
                f"    ① 故障函数经函数指针/分派表调用（静态调用图没有这条边）——gpac 实测就是这种；\n"
                f"    ② depth 不够（--depth N 调深；v7 起该参数才真正生效）；\n"
                f"    ③ harness 入口不在 CPG 里。\n"
                f"  人工排查可加 --fault-anchor（会打印醒目警告，结果不能用于论证自主发现）。")

    if args.dry_run:
        print("\n  [dry-run] 不写出")
        return
    p = os.path.join(OUT, args.osv, "audit_worklist.json")
    json.dump(out, open(p, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(f"\n  写出 {p}")



# ══════════════════════════════════════════════════════════════════════
# 阶段入口
# ══════════════════════════════════════════════════════════════════════

def main(argv=None):
    ap = argparse.ArgumentParser(description="stage5 · prepare（5.0 fetch + 5.1 worklist）")
    ap.add_argument("--osv", required=True)
    ap.add_argument("--depth", type=int, default=2)
    a = ap.parse_args(sys.argv[1:] if argv is None else list(argv))
    for fn, av in ((main_fetch,    [a.osv]),                       # 位置参数
                   (main_worklist, ["--osv", a.osv, "--depth", str(a.depth)])):
        print(f"\n--- {fn.__name__}")
        rc = run_fn(fn, av)
        if rc:
            return rc
    return 0


if __name__ == "__main__":
    sys.exit(main())

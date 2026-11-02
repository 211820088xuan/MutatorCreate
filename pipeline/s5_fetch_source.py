#!/usr/bin/env python3
# -*- coding: utf-8 -*-
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
from __future__ import annotations
import json, os, re, subprocess, sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)   # mutator_create/
TOP = os.path.dirname(ROOT)    # mutator_create/
sys.path.insert(0, HERE)
from s2_lib_cpg import repo_dir, vuln_commit, SRCDIR

REPRO = os.path.join(ROOT, "artifacts", "reproduced_crashes.jsonl")
OUT = os.path.join(ROOT, "projects")

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


def main():
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


if __name__ == "__main__":
    sys.exit(main())

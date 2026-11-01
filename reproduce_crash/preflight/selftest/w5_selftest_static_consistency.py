#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""**[W5 第十八轮 · N62]** 静态一致性自测：Python **不报错**、只静默生效的那几类缺陷。

动机（✅ 本轮真实事故）：给 `run_repro.py` 加 N62 水位线时，我在模块顶部新写了一个
`free_gb()`（带 `except OSError` 容错），而文件里**第 132 行本来就有一份**（W3 Phase2 的）。
Python 的规则是**后定义者胜** → 我那份被静默覆盖，容错**根本没生效**。
直到我拿 `free_gb('/nonexistent')` 去测，看它抛 `FileNotFoundError` 才发现。

这类缺陷的特点：**语法检查过、导入不报错、单测也可能碰不到**（只有走到那个分支才炸），
所以必须用 AST 静态扫。三项：

1. **重复的顶层函数/类定义**（后者静默覆盖前者）
2. **重复的模块级常量赋值**（同名单调覆盖，如两个 `TIER_RANK = …`）
3. **`except` 里引用了未定义的名字**（拼错异常类名 → 运行时才 NameError）
"""
from __future__ import annotations

import ast
import collections
import glob
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
FAILS = []
N = [0]


def ck(cond, msg):
    N[0] += 1
    print(f"  {'✅' if cond else '❌'} {msg}")
    if not cond:
        FAILS.append(msg)


def targets():
    pats = [os.path.join(ROOT, "*.py"),
            os.path.join(ROOT, "preflight", "**", "*.py")]
    out = []
    for p in pats:
        out += [f for f in glob.glob(p, recursive=True)
                if "__pycache__" not in f and os.path.isfile(f)]
    return sorted(set(out))


def main():
    files = targets()
    print("=" * 78)
    print(f"N62 静态一致性自测：扫描 {len(files)} 个 .py（专抓 Python 静默生效的缺陷）")
    print("=" * 78)

    dup_fn, dup_const, bad_except = [], [], []
    for f in files:
        try:
            tree = ast.parse(open(f, encoding="utf-8").read())
        except (SyntaxError, OSError) as e:
            dup_fn.append((f, f"解析失败: {e}"))
            continue
        rel = os.path.relpath(f, ROOT)
        # ① 重复的顶层函数/类定义
        c = collections.Counter(n.name for n in tree.body
                                if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef,
                                                  ast.ClassDef)))
        for k, v in c.items():
            if v > 1:
                dup_fn.append((rel, f"{k} ×{v}"))
        # ② 重复的模块级常量赋值（全大写名）
        cc = collections.Counter()
        for n in tree.body:
            if isinstance(n, ast.Assign):
                for t in n.targets:
                    if isinstance(t, ast.Name) and t.id.isupper():
                        cc[t.id] += 1
        for k, v in cc.items():
            if v > 1:
                dup_const.append((rel, f"{k} ×{v}"))
        # ③ except 里引用了本文件未定义、也不是内建的名字（拼错异常类）
        defined = {n.name for n in ast.walk(tree)
                   if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef))}
        defined |= {t.id for n in tree.body if isinstance(n, ast.Assign)
                    for t in n.targets if isinstance(t, ast.Name)}
        imported = set()
        for n in ast.walk(tree):
            if isinstance(n, ast.Import):
                imported |= {(al.asname or al.name).split(".")[0] for al in n.names}
            elif isinstance(n, ast.ImportFrom):
                imported |= {(al.asname or al.name) for al in n.names}
        for n in ast.walk(tree):
            if isinstance(n, ast.ExceptHandler) and isinstance(n.type, ast.Name):
                nm = n.type.id
                if nm not in defined and nm not in imported and nm not in dir(__builtins__):
                    bad_except.append((rel, f"except {nm}（第 {n.lineno} 行）"))

    print("\n[1] 重复的顶层函数/类定义（**后者静默覆盖前者**）")
    ck(not dup_fn, f"无重复定义（{len(files)} 个文件）" if not dup_fn else f"发现 {dup_fn[:5]}")

    print("\n[2] 重复的模块级常量赋值")
    ck(not dup_const,
       f"无重复常量（{len(files)} 个文件）" if not dup_const else f"发现 {dup_const[:5]}")

    print("\n[3] except 引用了未定义/未导入的异常名")
    ck(not bad_except,
       f"无悬空异常名" if not bad_except else f"发现 {bad_except[:5]}")

    print("\n[4] 已知答案：本轮真实事故的那个形态必须被抓到")
    _src = ("def free_gb(p='/'):\n    return 1\n\n\n"
            "def free_gb(p='/'):          # ← 后定义者胜，前一份被静默覆盖\n"
            "    import os\n    return os.statvfs(p).f_bavail\n")
    _t = ast.parse(_src)
    _c = collections.Counter(n.name for n in _t.body if isinstance(n, ast.FunctionDef))
    ck(_c.get("free_gb") == 2, f"合成样例确实检出 `free_gb ×2`（got={dict(_c)}）")

    # ④ **[N64] 每个带 argparse 的脚本，`--help` 必须能正常渲染。**
    # ✅ 本轮真实事故：我在 `--disk-hard-floor-gb` 的 help 里写了「100% 满」，而 argparse 会对
    #   help 串做 `%` 格式化 → `ValueError: unsupported format character '?' (0x6ee1)`，
    #   **整个 `--help` 崩掉**（必须写成 `100%%`）。这类错误 `ast.parse` 查不出、导入也不报，
    #   只有真去渲染 help 才炸 → 所以这里**直接跑**，而不是静态猜。
    print("\n[4b] 每个脚本的 `--help` 必须能正常渲染（argparse 会格式化 help 串）")
    import subprocess
    n_help = 0
    for f in files:
        base = os.path.basename(f)
        if base.startswith("w5_selftest") or base == os.path.basename(__file__):
            continue
        src = open(f, encoding="utf-8").read()
        if "add_argument(" not in src:
            continue
        n_help += 1
        r = subprocess.run([sys.executable, f, "--help"], capture_output=True, text=True,
                           timeout=180, cwd=ROOT)
        ok = (r.returncode == 0 and "usage:" in (r.stdout or "").lower())
        ck(ok, f"`{os.path.relpath(f, ROOT)} --help` 退出 {r.returncode}"
               + ("" if ok else f" → {(r.stderr or '').strip().splitlines()[-1:]}"))
    if not n_help:
        ck(False, "没找到任何带 argparse 的脚本（扫描逻辑可能失效）")

    print("\n" + (f"❌ {len(FAILS)} 项未通过：{FAILS}" if FAILS
                  else f"✅ 全部通过（{N[0]} 项）"))
    return 1 if FAILS else 0


if __name__ == "__main__":
    sys.exit(main())

"""R19 步骤 1：量 F4（裸指针）里「同名 / 别名 / 经字段」的分布。

## 为什么

R12 的分布里 F4 裸指针占 55%（60/110）。但 R18 发现 F4 里**"换了名字"**的那部分
（`t` 被释放 → 另一个名字 `v` 被读）**数据流做不了**——`reachableByFlows` 是值流，不做别名分析。
**所以能力 A 覆盖的不是 55%，而是 55% 里"没换名字"的那部分。这个比例不知道。**

## 判据

| 类别 | 判据 |
|---|---|
| **同名** | 释放实参与使用表达式的**根标识符相同** |
| **经字段** | 根不同，且使用表达式是**多跳字段访问**（`a->b->c` / `a[i]->b`）—— 被释放对象经字段传递 |
| **别名** | 根不同，且使用表达式是**裸变量或单跳**（`v` / `v->end`）—— 同一对象的另一个名字 |
| **判不出** | 缺 `free.code` / `crash.code`，或根提取失败 |

**这是启发式，不是证明。** 每条都附上原始表达式，供人工复核。
"""
import json
import glob
import re
import os
import collections
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "docs", "runs", "r19")

sys.path.insert(0, os.path.join(ROOT, "tools"))
import backfill_free_code as BF   # 复用 R12 的 raw HTTP 取单文件（GitHub / GitLab / googlesource）


def src_line(rec, path, line):
    """按 pin 取**那一行**源码。path 是仓库相对路径，line 是 1-based。"""
    if not (path and line):
        return None
    rel = BF.repo_rel(path)
    txt = BF.fetch((rec or {}).get("repo_url"), (rec or {}).get("pin_commit"), rel)
    if txt is None:
        return None
    L = txt.split("\n")
    return L[int(line) - 1].strip() if 1 <= int(line) <= len(L) else None

# F4（裸指针）判定 —— 与 R12/R16 的口径一致
ALLCAP = re.compile(r"^[A-Z][A-Z0-9_]{3,}$")
FAM = re.compile(r"\b(\w*(?:[Ff][Rr][Ee][Ee]|FREE|Free|[Dd]estroy|[Cc]lear|[Rr]elease|[Dd]el)\w*)\s*\(", re.I)


def first_arg(code, start):
    i = code.index("(", start)
    d = 0
    for k in range(i, len(code)):
        if code[k] == "(":
            d += 1
        elif code[k] == ")":
            d -= 1
            if d == 0:
                return code[i + 1:k].strip()
    return ""


def fshape(code):
    if not code:
        return "F5 未知", ""
    m = re.search(r"\b\w*[Rr]ealloc\w*\s*\(", code)
    if m:
        arg = first_arg(code, m.start())
        return ("F7 realloc(字段)" if "->" in arg else "F7 realloc(裸指针)"), arg
    m = re.search(r"\bdelete\b\s*(\[\])?\s*([\w\.\->]+)", code)
    if m:
        return "F8 C++ delete", m.group(2)
    if re.search(r"\(\s*\w+\s*\)\s*\(", code) or re.search(r"\w+\s*\[[^\]]*\]\s*\(", code) \
       or re.search(r"\w+\s*->\s*\w+\s*\(", code):
        return "F6 间接/函数指针调用", ""
    m = FAM.search(code)
    if not m:
        return "F9 判不出(取错行?)", ""
    arg = first_arg(code, m.start())
    if not arg:
        return "F9 判不出(取错行?)", ""
    if "[" in arg:
        return "F3 容器元素", arg
    if "->" in arg:
        return "F1 结构体字段", arg
    base = re.sub(r"^\([^)]*\)", "", arg).strip()
    if ALLCAP.match(base):
        return "F2 全局/常量", arg
    return "F4 裸指针(局部/形参)", arg


ID = re.compile(r"[A-Za-z_]\w*")
NOT_VAR = {"const", "struct", "unsigned", "signed", "char", "int", "long", "short",
           "void", "float", "double", "size_t", "NULL", "sizeof", "return", "if",
           "else", "while", "for", "static", "unsigned", "uint32_t", "int32_t"}


def roots(expr):
    """表达式里的根标识符（去重，保持顺序）。跳过类型名/关键字/函数名。"""
    e = re.sub(r'"[^"]*"', "", expr)
    # 去掉明显是函数调用的名字（`foo(`）
    calls = set(re.findall(r"([A-Za-z_]\w*)\s*\(", e))
    out = []
    for m in ID.finditer(e):
        t = m.group(0)
        if t in NOT_VAR or t in calls:
            continue
        if t not in out:
            out.append(t)
    return out


def hops(expr):
    """字段访问的跳数：`a->b` = 1，`a->b->c` = 2，`a[i]->b` = 1。"""
    return len(re.findall(r"->", expr))


def classify(free_arg, use_expr):
    rf, ru = roots(free_arg), roots(use_expr)
    if not rf or not ru:
        return "判不出", rf, ru, ""
    # 使用的根：取表达式里**第一个**根标识符（最外层对象）
    u0 = ru[0]
    if u0 in rf:
        return "同名", rf, ru, f"使用根 `{u0}` 在释放实参里"
    h = hops(use_expr)
    if h >= 2:
        return "经字段", rf, ru, f"使用根 `{u0}` 与释放根 {rf} 不同，且多跳（{h} 个 `->`）"
    return "别名", rf, ru, f"使用根 `{u0}` 与释放根 {rf} 不同，{h} 跳"


def main():
    os.makedirs(OUT, exist_ok=True)
    # 用 R12 的口径重建 110 条候选的形态
    cpgmap = {}
    for ln in open(os.path.join(ROOT, "artifacts", "reproduced_crashes.jsonl"), encoding="utf-8"):
        ln = ln.strip()
        if ln:
            d = json.loads(ln)
            cpgmap[d.get("osv_id")] = d
    rows = json.load(open("/tmp/r11_cands.json"))
    # A/B/C 用调用图方向（R11 口径）；这里只需要 F4 集合，方向不影响形态统计
    detail = []
    for r in rows:
        fp = os.path.join(ROOT, "artifacts", "facts", r["osv"], "facts.json")
        if not os.path.isfile(fp):
            continue
        f = json.load(open(fp, encoding="utf-8"))
        fs = [x for x in (f.get("sites") or []) if x.get("kind") == "free"]
        fcode = (fs[0].get("code") if fs else None)
        kind, arg = fshape(fcode)
        if kind != "F4 裸指针(局部/形参)":
            continue
        crash = f.get("crash") or {}
        cs = crash.get("site") or {}
        rec = cpgmap.get(r["osv"]) or {}
        fsrc = src_line(rec, (fs[0].get("file") if fs else None),
                        (fs[0].get("line") if fs else None))
        usrc = src_line(rec, cs.get("file"), cs.get("line"))
        # 用**源码那一行**当释放/使用表达式（`crash.code` 是候选子表达式集合，不可靠）
        fexpr = fsrc or fcode or ""
        uexpr = usrc or ""
        verdict, rf, ru, why = classify(arg, uexpr) if uexpr else ("判不出", [], [], "拿不到使用行源码")
        detail.append(dict(
            osv=r["osv"], project=r["proj"], free_src=fsrc, use_src=usrc,
            free_file=(fs[0].get("file") if fs else None),
            free_line=(fs[0].get("line") if fs else None),
            free_code=fcode, free_arg=arg,
            use_file=cs.get("file"), use_line=cs.get("line"),
            use_fn=cs.get("fn"), use_code=uexpr,
            roots_free=rf, roots_use=ru, verdict=verdict, why=why,
            pin=(cpgmap.get(r["osv"]) or {}).get("pin_commit"),
        ))
    n = len(detail)
    c = collections.Counter(d["verdict"] for d in detail)
    out = dict(total_f4=n, counts=dict(c),
               pct={k: round(100.0 * v / n, 1) for k, v in c.items()} if n else {},
               pct_of_110={k: round(100.0 * v / 110, 1) for k, v in c.items()},
               detail=detail)
    json.dump(out, open(os.path.join(OUT, "f4_alias.json"), "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)
    print(f"  F4 共 {n} 条")
    for k, v in c.most_common():
        print(f"    {k:<8} {v:>3}  ({100.0*v/n:.0f}% of F4, {100.0*v/110:.0f}% of 110)")


if __name__ == "__main__":
    main()

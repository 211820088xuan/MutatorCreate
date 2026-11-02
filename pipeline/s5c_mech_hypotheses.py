#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""s5c_mech_hypotheses.py —— 阶段5③：用机械规则提出「可能崩溃点」的假设

为什么要有这一步
  agent 能读懂代码，但**判断不可靠**：实测两次把真实的 UAF 判成 clean，
  第二次还编了错误理由（"释放后立即重新赋值"）。所以不能让 agent 当判定器。
  这一步用**确定性规则**提出假设，agent 只负责补上下文（输入怎么控制、有没有守卫）。

规则（针对"释放后继续使用"这一类，数据流可判）
  R1 循环内释放后未重新赋值
       在循环体 L = [loop_start, loop_end] 内有一次调用释放包装函数 W(v)
       · 在 (call_line, loop_end] 内**没有**对 v 的赋值
       · 在 [loop_start, call_line) 内**读**过 v（`v->` / `v.` / `v[` / `v ==` / `v !=` …）
       → 下一轮迭代读到已释放的 v ⇒ 候选 UAF
       （这正是 in_dxf.c:12284 → 12267 的形态：释放后回到 while 条件读 pair->code）
  R2 同一基本块内释放后继续用
       在 (call_line, block_end] 内没有赋值 v，但读到了 v
       → 候选 UAF

  "释放包装函数" = 名字匹配 free/destroy/release/clear/cleanup 的**仓库内**函数。
  之所以要看包装函数：`dxf_free_pair (pair)` 里的 `pair = NULL` 只置空形参，
  调用方的 `pair` 仍然悬垂 —— 这是最容易漏的一类。

它产出什么
  <OSV>/mech_hypotheses.json：每条假设带 规则名 / 变量 / 释放行 / 使用行 / 证据原文。
  **这是"假设"，不是结论**：后续用 fuzz 或人工验证。

用法
  python3 s5c_mech_hypotheses.py --osv ARVO-42494732
  python3 s5c_mech_hypotheses.py --osv ARVO-42494732 --rules R1
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
TOP = os.path.dirname(ROOT)
OUT = os.path.join(ROOT, "projects")

FREE_WRAPPER = re.compile(r"\b\w*(free|destroy|release|cleanup|clear)\w*\s*$", re.I)
CALL_RX = re.compile(r"\b([A-Za-z_]\w*)\s*\(\s*&?\s*([A-Za-z_]\w*)\s*\)\s*;")
LOOP_RX = re.compile(r"\b(while|for)\s*\(")


# ────────────────────────── 基础工具 ──────────────────────────

def strip_code(line: str) -> str:
    """去掉行内字符串与注释（粗略，够用）。"""
    line = re.sub(r'"(?:\\.|[^"\\])*"', '""', line)
    line = re.sub(r"'(?:\\.|[^'\\])*'", "''", line)
    return line.split("//")[0]


def match_brace(lines: list[str], start: int) -> int:
    """从 start 行开始找第一个 '{'，返回配对的 '}' 所在行（0-based，闭区间）。越界返回 -1。"""
    depth, i, seen = 0, start, False
    while i < len(lines):
        for ch in strip_code(lines[i]):
            if ch == "{":
                depth += 1; seen = True
            elif ch == "}":
                depth -= 1
                if seen and depth == 0:
                    return i
        i += 1
        if i - start > 4000:
            break
    return -1


def find_loops(lines: list[str], lo: int, hi: int) -> list[tuple[int, int]]:
    """在 [lo, hi] 行内找 while/for 块，返回 (起始行, 结束行)（0-based）。"""
    out = []
    for i in range(lo, hi + 1):
        if LOOP_RX.search(strip_code(lines[i])):
            j = i
            while j <= hi and "{" not in strip_code(lines[j]) and j < i + 3:
                j += 1
            end = match_brace(lines, j)
            if end > 0 and end <= hi:
                out.append((i, end))
    return out


def reads_of(lines: list[str], lo: int, hi: int, var: str) -> int | None:
    """在 [lo, hi] 行内找第一次"读" var 的行；赋值不算读。"""
    # 只认"解引用"：v-> / v. / v[] ；`if (v)` / `if (!v)` 只是判空，不算 UAF
    pat_read = re.compile(rf"\b{re.escape(var)}\b\s*(->|\.|\[)")
    pat_assign = re.compile(rf"^\s*\b{re.escape(var)}\b\s*=[^=]")
    for i in range(lo, hi + 1):
        s = strip_code(lines[i])
        if pat_assign.search(s):
            continue
        if pat_read.search(s):
            return i
    return None


def assigned_in(lines: list[str], lo: int, hi: int, var: str) -> bool:
    pat = re.compile(rf"\b{re.escape(var)}\b\s*=(?!=)|\b{re.escape(var)}\b\s*=(?!=)\s*[^=]")
    for i in range(lo, hi + 1):
        s = strip_code(lines[i])
        if re.search(rf"(^|[;{{(])\s*&?\s*\b{re.escape(var)}\b\s*=(?!=)", s):
            return True
        if re.search(rf"\b{re.escape(var)}\b\s*=(?!=)", s) and not re.search(
                rf"{re.escape(var)}\s*(==|!=|>=|<=)", s):
            if pat.search(s):
                return True
    return False



def param_name(lines: list[str], lo: int, hi: int, fname: str) -> str | None:
    """从函数源码里取第一个形参的名字。"""
    sig = " ".join(strip_code(x) for x in lines[lo:min(hi, lo + 3) + 1])
    m = re.search(rf"\b{re.escape(fname)}\s*\(([^)]*)\)", sig)
    if not m:
        return None
    first = m.group(1).split(",")[0].strip()
    if not first or first == "void":
        return None
    ids = re.findall(r"[A-Za-z_]\w*", first)
    return ids[-1] if ids else None


def frees_param_itself(lines: list[str], lo: int, hi: int, fname: str) -> bool:
    """W(v) 到底是不是释放 v 本身？（而不是释放 v->member）

    判据：函数体里出现 `free (<param>)` / `free(<param>)`，而不是 `free(<param>->x)`。
    这条过滤很关键：`dwg_free_appinfo (dwg)` 释放的是 dwg->appinfo，
    dwg 本身仍然有效，不该被当成悬垂。
    """
    p = param_name(lines, lo, hi, fname)
    if not p:
        return False
    body = "\n".join(strip_code(x) for x in lines[lo:hi + 1])
    if re.search(rf"\bfree\s*\(\s*{re.escape(p)}\s*\)", body):
        return True
    if re.search(rf"\b(kfree|g_free|sdsfree)\s*\(\s*{re.escape(p)}\s*\)", body):
        return True
    return False


# ────────────────────────── 规则 ──────────────────────────

def candidate_from(lines: list[str], rel: str, fn: str, var: str, call_i: int,
                   use_i: int, loop: tuple[int, int] | None, rule: str) -> dict:
    return {
        "rule": rule,
        "vuln_type": "use-after-free",
        "file": rel,
        "function": fn,
        "variable": var,
        "free_line": call_i + 1,
        "use_line": use_i + 1,
        "loop": [loop[0] + 1, loop[1] + 1] if loop else None,
        "evidence_lines": [[call_i + 1, lines[call_i].strip()],
                           [use_i + 1, lines[use_i].strip()]],
        "mechanism": (
            f"`{var}` 在第 {call_i+1} 行被释放包装函数释放后，"
            + (f"循环 [L{loop[0]+1}-L{loop[1]+1}] 内没有重新赋值，"
               if loop else "同一块内没有重新赋值，")
            + f"而第 {use_i+1} 行仍会读它"
            + ("（下一轮迭代回到循环开头时读到已释放内存）" if loop else "")
        ),
        "status": "hypothesis_unverified",
    }


def scan_function(lines: list[str], rel: str, fn: str, lo: int, hi: int,
                  wrappers: set[str], rules: set[str]) -> list[dict]:
    out = []
    loops = find_loops(lines, lo, hi) if "R1" in rules else []

    for i in range(lo, hi + 1):
        m = CALL_RX.search(strip_code(lines[i]))
        if not m:
            continue
        callee, var = m.group(1), m.group(2)
        if callee not in wrappers or callee == var:
            continue

        # R1：所在的循环（取最内层包含该行的）
        encl = [L for L in loops if L[0] <= i <= L[1]]
        if encl and "R1" in rules:
            loop = max(encl, key=lambda L: L[0])       # 最内层
            if not assigned_in(lines, i + 1, loop[1], var):
                u = reads_of(lines, loop[0], i - 1, var)
                if u is not None:
                    out.append(candidate_from(lines, rel, fn, var, i, u, loop, "R1"))
                    continue

        # R2：同一块内（用函数体 [i+1, hi] 作粗略基本块）
        if "R2" in rules:
            if not assigned_in(lines, i + 1, hi, var):
                u = reads_of(lines, i + 1, min(hi, i + 120), var)
                if u is not None:
                    out.append(candidate_from(lines, rel, fn, var, i, u, None, "R2"))
    return out


# ────────────────────────── 主流程 ──────────────────────────

def main():
    ap = argparse.ArgumentParser(description="阶段5③：机械规则提假设")
    ap.add_argument("--osv", required=True)
    ap.add_argument("--rules", nargs="*", default=["R1", "R2"])
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()
    rules = set(args.rules)

    ctxp = os.path.join(OUT, args.osv, "source_context.json")
    wlp = os.path.join(OUT, args.osv, "audit_worklist.json")
    for p in (ctxp, wlp):
        if not os.path.exists(p):
            raise SystemExit(f"缺少 {p}")
    ctx = json.load(open(ctxp, encoding="utf-8"))
    wl = json.load(open(wlp, encoding="utf-8"))
    root = ctx["repo_local"]

    # 释放包装函数候选：名字匹配 free/destroy/release/clear/cleanup
    cand_wrappers = {f["name"] for f in wl["functions"] if FREE_WRAPPER.search(f["name"])}

    # 预读源码（后面既要用它过滤包装函数，也要扫描）
    src_cache: dict[str, list[str]] = {}
    for f in wl["functions"]:
        rel = f["file"]
        if rel not in src_cache:
            p = os.path.join(root, rel)
            src_cache[rel] = (open(p, encoding="utf-8", errors="replace").read().split("\n")
                              if os.path.isfile(p) else [])

    # 只保留"直接释放第一个形参本身"的包装函数（排除 dwg_free_appinfo(dwg) 这类
    # 只释放成员的）；这能大幅降低假阳性
    wrappers, rejected = set(), []
    for f in wl["functions"]:
        if f["name"] not in cand_wrappers:
            continue
        lines = src_cache[f["file"]]
        lo, hi = f["lines"][0] - 1, f["lines"][1] - 1
        if lines and 0 <= lo <= hi < len(lines) and frees_param_itself(lines, lo, hi, f["name"]):
            wrappers.add(f["name"])
        else:
            rejected.append(f["name"])

    print(f"=== {args.osv} 机械规则提假设 ===")
    print(f"  规则        : {sorted(rules)}")
    print(f"  包装函数候选 : {len(cand_wrappers)} 个 → 直接释放形参的 {len(wrappers)} 个"
          f"（排除 {len(rejected)} 个只释放成员的）")
    print(f"  保留         : {sorted(wrappers)[:6]}{'…' if len(wrappers) > 6 else ''}")

    funcs = wl["functions"]
    hyps = []
    skipped = 0
    for f in funcs:
        rel = f["file"]
        lines = src_cache.get(rel, [])
        lo, hi = f["lines"][0] - 1, f["lines"][1] - 1
        if not lines or hi >= len(lines) or lo < 0:
            skipped += 1
            continue
        for h in scan_function(lines, rel, f["name"], lo, hi, wrappers, rules):
            h["chars"] = f["chars"]
            hyps.append(h)

    hyps.sort(key=lambda h: (h["rule"], h["file"], h["free_line"]))
    for i, h in enumerate(hyps, 1):
        h["id"] = f"h{i:03d}"

    # 自检：已知崩溃行是否被某条假设的 use_line 覆盖
    fl, ff = ctx.get("fault_line"), (ctx.get("fault_file") or "").split("/")[-1]
    cov = [h for h in hyps if ff and h["file"].endswith(ff) and
           min(h["free_line"], h["use_line"]) <= (fl or -1) <= max(h["free_line"], h["use_line"])]

    print(f"  扫描函数    : {len(funcs)} 个（跳过 {skipped}）")
    print(f"  假设        : {len(hyps)} 条")
    from collections import Counter
    print(f"  按规则      : {dict(Counter(h['rule'] for h in hyps))}")
    print(f"  按文件      : {dict(Counter(h['file'] for h in hyps).most_common(8))}")
    if fl is not None:
        print(f"  自检：已知崩溃行 {ff}:{fl} "
              f"{'✅ 被假设覆盖' if cov else '❌ 未被覆盖'}")
        for h in cov[:3]:
            print(f"      {h['id']} {h['rule']} {h['function']} "
                  f"释放L{h['free_line']} → 使用L{h['use_line']}")

    out = {"_meta": {"osv_id": args.osv, "project": ctx.get("project"),
                     "commit": ctx.get("commit_used"), "rules": sorted(rules),
                     "free_wrappers": sorted(wrappers),
                     "method": "确定性源码规则（0 LLM），产出的是**未验证假设**",
                     "fault_file": ctx.get("fault_file"), "fault_line": fl,
                     "covers_fault_line": bool(cov)},
           "hypotheses": hyps}
    if args.dry_run:
        print("\n  [dry-run] 不写出")
        return
    p = os.path.join(OUT, args.osv, "mech_hypotheses.json")
    json.dump(out, open(p, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(f"\n  写出 {p}")


if __name__ == "__main__":
    main()

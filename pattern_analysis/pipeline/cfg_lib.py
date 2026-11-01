#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""cfg_lib.py —— 行级控制流：给 agent 一个"单步执行"的能力

为什么需要它
  agent 能读到源码，但它是**从上往下线性读**的。而 UAF 常常是：
      使用在源码里出现在释放**之前**，靠循环回边才连起来。
  例（libredwg in_dxf.c）:
      12267  while (pair != NULL && pair->code == 0 && pair->value.s)   ← 使用
      12284      dxf_free_pair (pair);                                  ← 释放
      12286    }                                                        ← 回到 12267
  线性阅读永远连不起来。给它一个"从这里执行，下一步去哪"的工具，
  它就能自己看到 12284 → 12285 → 12286 → **12267（循环回边）**。

能力
  flow(lines, lo, hi, line, steps) → 一行行的执行轨迹，回边会被标记
  只处理语句级控制流，不做表达式求值；保守、可解释。

支持
  * 顺序执行（下一非空行）
  * 块结束：`}` 之后 → 普通块跳到块后；循环块跳回循环头（回边）
  * return → 终止
  * break / continue → 跳到所在循环之后 / 循环头
  * if / else / switch 不做分支枚举（会按"块结束 → 块后"处理）
"""
from __future__ import annotations

import re

LOOP_KW = ("while", "for")
_KW = ("while", "for", "if", "else", "switch", "do")


def strip_code(line: str) -> str:
    line = re.sub(r'"(?:\\.|[^"\\])*"', '""', line)
    line = re.sub(r"'(?:\\.|[^'\\])*'", "''", line)
    return line.split("//")[0]


def _prev_code_line(lines: list[str], i: int, lo: int) -> int:
    j = i - 1
    while j >= lo:
        if strip_code(lines[j]).strip():
            return j
        j -= 1
    return -1


def blocks(lines: list[str], lo: int, hi: int) -> list[dict]:
    """返回块列表：{open, close, kind, header}（全部 0-based）。

    kind ∈ loop / if / else / switch / plain
    header = 构造这个块的那一行（`while (...)` / `if (...)` / `else` …）
    """
    stack: list[int] = []
    pairs: dict[int, int] = {}
    for i in range(lo, hi + 1):
        for ch in strip_code(lines[i]):
            if ch == "{":
                stack.append(i)
            elif ch == "}" and stack:
                pairs[stack.pop()] = i

    out = []
    for o, c in pairs.items():
        h = _prev_code_line(lines, o, lo)
        head = strip_code(lines[h]) if h >= 0 else ""
        # `{` 和头部同一行的情况
        if "{" in head:
            head = head.split("{")[0]
        hs = head.strip()
        if re.match(r"^(else\s*)?(if|while|for|switch)\b", hs) or hs.startswith("else"):
            if hs.startswith(("while", "for")):
                kind = "loop"
            elif hs.startswith("switch"):
                kind = "switch"
            elif hs.startswith("else") and "if" not in hs:
                kind = "else"
            else:
                kind = "if"
        else:
            kind = "plain"
        out.append({"open": o, "close": c, "kind": kind, "header": h})
    return sorted(out, key=lambda b: b["open"])


def step(lines: list[str], lo: int, hi: int, blks: list[dict], line: int) -> tuple[int | None, str]:
    """执行 line 这一行之后，下一行去哪。返回 (下一行, 说明)。"""
    s = strip_code(lines[line])
    enclosing = [b for b in blks if b["open"] <= line <= b["close"]]
    loops = [b for b in enclosing if b["kind"] == "loop"]
    loop = max(loops, key=lambda b: b["open"]) if loops else None

    if re.search(r"\breturn\b", s):
        return None, "return（离开本函数）"

    if re.search(r"\bcontinue\b", s) and loop:
        return loop["header"], f"continue → 回到循环头 L{loop['header']+1}（回边）"
    if re.search(r"\bbreak\b", s) and loop:
        return loop["close"] + 1, f"break → 跳出循环到 L{loop['close']+2}"

    closers = [b for b in enclosing if b["close"] == line]
    if closers:
        b = max(closers, key=lambda x: x["open"])
        if b["kind"] == "loop":
            return b["header"], f"循环体结束 → 回到 L{b['header']+1}（**回边**）"
        return b["close"] + 1, f"{b['kind']} 块结束 → 继续 L{b['close']+2}"

    nxt = line + 1
    while nxt <= hi and not strip_code(lines[nxt]).strip():
        nxt += 1
    return (nxt if nxt <= hi else None), "顺序执行"


def flow(lines: list[str], lo: int, hi: int, start: int, steps: int = 8) -> list[dict]:
    """从 start 行开始走，返回轨迹 [{line, code, next, note, back_edge}]。"""
    blks = blocks(lines, lo, hi)
    out, cur, seen = [], start, set()
    for _ in range(max(1, steps)):
        if cur is None or cur < lo or cur > hi:
            break
        if cur in seen:
            out.append({"line": cur, "code": strip_code(lines[cur]).strip()[:120],
                        "next": None, "note": "重复进入（已见过的行）", "back_edge": False})
            break
        seen.add(cur)
        nxt, note = step(lines, lo, hi, blks, cur)
        back = bool(nxt is not None and nxt <= cur)
        out.append({"line": cur, "code": strip_code(lines[cur]).strip()[:120],
                    "next": nxt, "note": note, "back_edge": back})
        cur = nxt
    return out


def loops_of(lines: list[str], lo: int, hi: int, line: int) -> list[dict]:
    """返回包含 line 的循环块（由外到内）。"""
    return [b for b in blocks(lines, lo, hi)
            if b["kind"] == "loop" and b["open"] <= line <= b["close"]]


def render(trace: list[dict]) -> str:
    rows = []
    for t in trace:
        arrow = f"→ L{t['next']+1}" if t["next"] is not None else "→ (结束)"
        mark = "  ⟲ **回边**" if t["back_edge"] else ""
        rows.append(f"  L{t['line']+1:<6} {t['code']:<64} {arrow:<12} {t['note']}{mark}")
    return "\n".join(rows)

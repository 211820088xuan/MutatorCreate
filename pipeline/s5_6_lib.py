#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""s5_6_lib.py —— stage5 的共享底座（原 cfg_lib.py + agent_runtime.py）

两部分：
  1. 行级 CFG：`blocks` / `step` / `flow` / `loops_of` / `render` / `strip_code`
     —— 用来回答"这一行执行完之后控制流去哪"，循环回边会被显式标出。
  2. 自实现的 agent 循环：`Agent` / `Tool` / `read_file_tool` / `grep_tool` /
     `list_dir_tool` —— 工具调用、路径沙箱、轮次与字符预算、重复调用缓存、
     停滞后三级 nudge、最后一轮强制 finish。

被 `s5_1_main.py`（确定性阶段）和 `s5_3_audit.py`（agent 阶段）共同 import。
"""
from __future__ import annotations

import sys

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

# ══════════════════════════════════════════════════════════════════════
# 自实现 agent 循环（原 agent_runtime.py）
# ══════════════════════════════════════════════════════════════════════

"""agent_runtime.py —— 自实现的最小 LLM Agent 运行时（不依赖任何外部 CLI）

为什么要自己实现
  静态审计需要"边读源码边判断"，一次性把几万行塞进 prompt 不现实。
  这里给 LLM 一组**只读工具**，让它自己决定读哪个文件、看哪几行、grep 什么，
  循环多轮直到它调用 `finish` 交出结构化报告。

组成
  Tool    工具：名字 / 描述 / JSON Schema / 执行函数
  Agent   循环：LLM(tools) → tool_calls → 执行 → 回灌 → 直到 finish() 或超预算

安全与预算
  * **路径沙箱**：所有读操作只能落在 root 之下（`..` 逃逸会被拒绝）
  * **单次上限**：一次最多读 400 行 / grep 最多 40 条
  * **总预算**：最多 max_turns 轮、累计读取 max_chars 字符
  * **审计日志**：每轮的工具调用与结果摘要都写进 transcript，可复查

用法
  from agent_runtime import Agent, Tool, read_file_tool, grep_tool, list_dir_tool

  agent = Agent(
      name="vuln_audit",
      root="/path/to/repo",
      system="你是静态审计员…",
      tools=[read_file_tool(), grep_tool(), list_dir_tool()],
      finish_schema={...},          # finish 工具的参数 schema = 报告 schema
      max_turns=60,
  )
  report = agent.run("审计 src/in_dxf.c 里所有 free 之后的指针使用")
"""

import json
import os
import re
import ssl
import time
import urllib.error
import urllib.request
from dataclasses import dataclass, field
from typing import Any, Callable

API = os.environ.get("AGENT_API", "https://api.deepseek.com/v1/chat/completions")
DEFAULT_MODEL = os.environ.get("AGENT_MODEL", "deepseek-chat")
RETRY = 3

MAX_LINES_PER_READ = 400
MAX_GREP_HITS = 60
MAX_LINE_CHARS = 400


# ────────────────────────────── 凭据 ──────────────────────────────

def get_key() -> str:
    k = os.environ.get("DEEPSEEK_API_KEY")
    if k:
        return k
    for ln in open("/root/.bashrc", encoding="utf-8", errors="ignore"):
        if ln.startswith("export DEEPSEEK_API_KEY="):
            return ln.split("=", 1)[1].strip().strip('"').strip("'")
    raise RuntimeError("找不到 DEEPSEEK_API_KEY")


# ────────────────────────────── 工具 ──────────────────────────────

@dataclass
class Tool:
    name: str
    description: str
    schema: dict            # JSON Schema（parameters）
    fn: Callable[[dict, "Agent"], str]

    def as_api(self) -> dict:
        return {"type": "function",
                "function": {"name": self.name,
                             "description": self.description,
                             "parameters": self.schema}}


def _safe_path(root: str, p: str) -> str:
    """把 p 解析到 root 之下；越界则拒绝。"""
    root = os.path.realpath(root)
    full = os.path.realpath(os.path.join(root, p))
    if full != root and not full.startswith(root + os.sep):
        raise ValueError(f"路径越界（只允许读 {root} 之内）: {p}")
    return full


def read_file_tool() -> Tool:
    def run(a: dict, ag: "Agent") -> str:
        p = _safe_path(ag.root, a["path"])
        if not os.path.isfile(p):
            return f"[错误] 不是文件: {a['path']}"
        start = max(1, int(a.get("start_line") or a.get("offset") or 1))
        end = int(a.get("end_line") or a.get("limit") or 0)
        if end and end < start:
            end = start + int(a.get("limit") or 400) - 1
        elif end and not a.get("end_line") and a.get("limit"):
            end = start + end - 1          # limit 是"读多少行"，不是结束行号
        rows = []
        with open(p, encoding="utf-8", errors="replace") as fh:
            for i, ln in enumerate(fh, 1):
                if i < start:
                    continue
                if end and i > end:
                    break
                if len(rows) >= MAX_LINES_PER_READ:
                    rows.append(f"…（超过单次上限 {MAX_LINES_PER_READ} 行，请分段读）")
                    break
                rows.append(f"{i:>6}\t{ln.rstrip()[:MAX_LINE_CHARS]}")
        ag.spent_chars += sum(len(r) for r in rows)
        return "\n".join(rows) if rows else f"[空] {a['path']} 第 {start} 行起没有内容"

    return Tool(
        name="read_file",
        description="读一个源文件的指定行区间（返回带行号的内容，便于引用证据行）。",
        schema={"type": "object", "properties": {
            "path": {"type": "string", "description": "相对 root 的文件路径"},
            "start_line": {"type": "integer", "description": "起始行（1-based，默认 1；也接受 offset）"},
            "end_line": {"type": "integer", "description": "结束行（含；也接受 limit=读多少行）"},
            "offset": {"type": "integer", "description": "start_line 的别名"},
            "limit": {"type": "integer", "description": "读多少行（与 end_line 二选一）"},
        }, "required": ["path"]},
        fn=run,
    )


def grep_tool() -> Tool:
    def run(a: dict, ag: "Agent") -> str:
        pat = a["pattern"]
        try:
            rx = re.compile(pat)
        except re.error as e:
            return f"[错误] 正则不合法: {e}"
        root = _safe_path(ag.root, a.get("path") or ".")
        glob_hint = a.get("glob") or ""
        cap = min(int(a.get("max_hits") or MAX_GREP_HITS), 200)
        hits = []
        files = [root] if os.path.isfile(root) else []
        if not files:
            for dp, _, fns in os.walk(root):
                for fn in fns:
                    if glob_hint and not fn.endswith(glob_hint.lstrip("*")):
                        continue
                    files.append(os.path.join(dp, fn))
        for f in files:
            if len(hits) >= cap:
                break
            try:
                with open(f, encoding="utf-8", errors="replace") as fh:
                    for i, ln in enumerate(fh, 1):
                        if rx.search(ln):
                            rel = os.path.relpath(f, ag.root)
                            hits.append(f"{rel}:{i}\t{ln.rstrip()[:MAX_LINE_CHARS]}")
                            if len(hits) >= cap:
                                break
            except (OSError, UnicodeError):
                continue
        ag.spent_chars += sum(len(h) for h in hits)
        if not hits:
            return "[无命中]"
        head = "\n".join(hits)
        return head + (f"\n…（已截断到 {cap} 条，可缩小 path/放宽 max_hits 再搜）"
                       if len(hits) >= cap else "")

    return Tool(
        name="grep",
        description="在 root 下按正则搜索源码，返回 相对路径:行号\\t内容。",
        schema={"type": "object", "properties": {
            "pattern": {"type": "string", "description": "Python 正则"},
            "path": {"type": "string", "description": "相对 root 的目录或文件（默认 .）"},
            "glob": {"type": "string", "description": "文件名后缀过滤，如 .c"},
            "max_hits": {"type": "integer", "description": "最多返回多少条（默认 60，上限 200）"},
        }, "required": ["pattern"]},
        fn=run,
    )


def list_dir_tool() -> Tool:
    def run(a: dict, ag: "Agent") -> str:
        p = _safe_path(ag.root, a.get("path") or ".")
        if not os.path.isdir(p):
            return f"[错误] 不是目录: {a.get('path')}"
        es = sorted(os.listdir(p))
        out = []
        for e in es[:200]:
            full = os.path.join(p, e)
            out.append(("[dir]  " if os.path.isdir(full) else "       ") + e)
        ag.spent_chars += sum(len(x) for x in out)
        return "\n".join(out) or "[空目录]"

    return Tool(
        name="list_dir",
        description="列目录内容（最多 200 项）。",
        schema={"type": "object", "properties": {
            "path": {"type": "string", "description": "相对 root 的目录（默认 .）"}},
            "required": []},
        fn=run,
    )


# ────────────────────────────── Agent ──────────────────────────────

@dataclass
class Agent:
    name: str
    root: str
    system: str
    tools: list[Tool]
    finish_schema: dict
    model: str = DEFAULT_MODEL
    max_turns: int = 60
    max_chars: int = 600_000
    temperature: float = 0.0
    log_path: str | None = None

    spent_chars: int = 0
    transcript: list[dict] = field(default_factory=list)

    def __post_init__(self):
        self.finish = Tool(
            name="finish",
            description="提交最终报告。调用它即结束本次任务。",
            schema=self.finish_schema,
            fn=lambda a, ag: "[已结束]",
        )

    # ── LLM 调用 ──
    def _chat(self, messages: list[dict], force_finish: bool = False) -> dict:
        key = get_key()
        body = json.dumps({
            "model": self.model,
            "messages": messages,
            "tools": [t.as_api() for t in self.tools] + [self.finish.as_api()],
            "tool_choice": ({"type": "function", "function": {"name": "finish"}}
                            if force_finish else "auto"),
            "temperature": self.temperature,
            "max_tokens": 8000,
        }, ensure_ascii=False).encode("utf-8")
        last = None
        for attempt in range(RETRY):
            req = urllib.request.Request(API, data=body, headers={
                "Authorization": f"Bearer {key}",
                "Content-Type": "application/json",
            })
            try:
                with urllib.request.urlopen(req, timeout=300,
                                            context=ssl.create_default_context()) as r:
                    return json.loads(r.read().decode("utf-8"))["choices"][0]["message"]
            except urllib.error.HTTPError as e:
                try:
                    detail = e.read().decode("utf-8", "replace")[:600]
                except Exception:
                    detail = ""
                last = RuntimeError(f"HTTP {e.code}: {detail}")
            except (urllib.error.URLError, TimeoutError, OSError, KeyError, json.JSONDecodeError) as e:
                last = e
                time.sleep(2 * (attempt + 1))
        raise RuntimeError(f"LLM 调用失败 {RETRY} 次: {type(last).__name__}: {last}")

    def _log(self, rec: dict):
        self.transcript.append(rec)
        if self.log_path:
            os.makedirs(os.path.dirname(self.log_path), exist_ok=True)
            with open(self.log_path, "a", encoding="utf-8") as fh:
                fh.write(json.dumps(rec, ensure_ascii=False) + "\n")

    # ── 主循环 ──
    def run(self, task: str) -> dict:
        if self.log_path and os.path.exists(self.log_path):
            os.remove(self.log_path)
        messages = [{"role": "system", "content": self.system},
                    {"role": "user", "content": task}]
        by_name = {t.name: t for t in self.tools}
        by_name["finish"] = self.finish

        seen: dict[str, int] = {}          # (工具,参数) -> 次数
        cache: dict[str, str] = {}         # 相同调用直接复用，省 token 也防死循环
        stall = 0                         # 连续"无新信息"的轮数

        for turn in range(1, self.max_turns + 1):
            if self.spent_chars > self.max_chars:
                raise RuntimeError(f"超预算：已读 {self.spent_chars} 字符 > {self.max_chars}")

            left = self.max_turns - turn
            msg = self._chat(messages, force_finish=(left == 0))
            calls = msg.get("tool_calls") or []
            messages.append({"role": "assistant",
                             "content": msg.get("content") or "",
                             **({"tool_calls": calls} if calls else {})})

            if not calls:
                # 模型没调工具，直接给文字 → 让它必须用 finish
                self._log({"turn": turn, "type": "text_only",
                           "content": (msg.get("content") or "")[:800]})
                messages.append({"role": "user", "content":
                                 "请不要只用文字回答。必须调用 finish 工具提交结构化报告。"})
                continue

            for c in calls:
                fn = (c.get("function") or {}).get("name")
                raw = (c.get("function") or {}).get("arguments") or "{}"
                try:
                    args = json.loads(raw)
                except json.JSONDecodeError as e:
                    # 2026-11-04：原来 `args = {}` —— 模型发出的参数坏了，工具会拿空参数跑，
                    # 产出"看起来正常但没查对东西"的结果（例如 read_file 没带路径）。
                    # 改成不执行、把错误回喂给模型。
                    self._log({"turn": turn, "type": "bad_tool_args",
                               "fn": fn, "raw": str(raw)[:200], "error": str(e)[:120]})
                    msgs.append({"role": "tool", "tool_call_id": c.get("id"),
                                 "content": f"[错误] 调用 {fn} 的 arguments 不是合法 JSON："
                                            f"{str(e)[:120]}。请重新发一次，确保 arguments 是 JSON 对象。"})
                    continue

                if fn == "finish":
                    self._log({"turn": turn, "type": "finish", "args": args})
                    return args

                tool = by_name.get(fn)
                ck = f"{fn}\u0000{json.dumps(args, sort_keys=True, ensure_ascii=False)}"
                seen[ck] = seen.get(ck, 0) + 1

                if ck in cache:
                    stall += 1
                    result = (f"[重复调用，已返回上次结果]\n{cache[ck]}"
                              if seen[ck] >= 2 else cache[ck])
                elif not tool:
                    result = f"[错误] 没有工具 {fn}"
                else:
                    try:
                        result = tool.fn(args, self)
                        stall = 0
                        cache[ck] = result
                    except Exception as e:            # noqa: BLE001
                        result = f"[错误] {type(e).__name__}: {e}"
                self._log({"turn": turn, "type": "tool", "name": fn, "args": args,
                           "result_head": result[:300], "chars": len(result),
                           "repeated": seen[ck] > 1})
                messages.append({"role": "tool", "tool_call_id": c.get("id"),
                                 "content": result})

            # 每轮结束：按情况注入提醒（这是防死循环的关键）
            rep = max([v for k, v in seen.items()] or [0])
            hint = None
            if rep >= 3 and stall >= 2:
                hint = ("⛔ 你已多次重复相同的工具调用，且没有获得新信息。"
                        "立刻停止检索，基于**已经读到的内容**调用 finish 提交报告；"
                        "读不到的部分写进 notes，不要继续找。")
            elif stall >= 4:
                hint = ("⛔ 连续多轮没有获得新信息。请立即调用 finish，"
                        "把不确定的地方写进 notes。")
            elif left <= 3:
                hint = (f"⏰ 只剩 {left} 轮。请立刻调用 finish 提交**当前**结论，"
                        "不要开始新的检索。")
            if hint:
                messages.append({"role": "user", "content": hint})
                self._log({"turn": turn, "type": "nudge", "text": hint})

        raise RuntimeError(f"达到最大轮数 {self.max_turns} 仍未调用 finish")


def strip_fences(s: str) -> str:
    """去掉 ```json ... ``` 包裹（有些模型即使要求纯 JSON 也会加）。"""
    s = s.strip()
    m = re.match(r"^```[a-zA-Z]*\s*\n(.*?)\n```$", s, re.S)
    return m.group(1).strip() if m else s

# ══════════════════════════════════════════════════════════════════════
# 阶段间调用辅助
# ══════════════════════════════════════════════════════════════════════

def run_fn(fn, argv):
    """按给定 argv 调某个阶段函数（它自己用 argparse 读 sys.argv），返回退出码。

    异常一律转成非零退出码，不把 traceback 甩给调用方。
    """
    old = sys.argv
    sys.argv = [getattr(fn, "__name__", "stage")] + list(argv)
    try:
        rc = fn()
    except SystemExit as e:
        rc = e.code if isinstance(e.code, int) else (0 if e.code is None else 1)
    except Exception as e:                                      # noqa: BLE001
        print(f"\n[stage5] {getattr(fn, '__name__', 'stage')} 抛出 "
              f"{type(e).__name__}: {e}", file=sys.stderr)
        rc = 1
    finally:
        sys.argv = old
    return rc or 0

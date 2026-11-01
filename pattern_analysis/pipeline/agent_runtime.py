#!/usr/bin/env python3
# -*- coding: utf-8 -*-
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
from __future__ import annotations

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
        start = max(1, int(a.get("start_line") or 1))
        end = int(a.get("end_line") or 0)
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
            "start_line": {"type": "integer", "description": "起始行（1-based，默认 1）"},
            "end_line": {"type": "integer", "description": "结束行（含；默认自动截断）"},
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
        files = [root] if os.path.isfile(root) else None
        if files is None:
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
                except json.JSONDecodeError:
                    args = {}

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

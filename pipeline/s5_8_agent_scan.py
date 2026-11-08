"""R36 改动 ③：把 agent 扫描接进 pipeline。

## 为什么

`run_feature()` 原来只调两个扫描器（`scan_sites` 正则 + `scan_cross_function_sites`）。
R25–R27 做了三轮 agent 扫描（libredwg 42 / leptonica 56 / libxml2 77 / igraph 14 条候选），
那套代码一直在 `tools/r2x_*.py`，**从没被 `run_feature` 调过**。

## 配置（照 R26b 实测过的那套，一个都不改）

| 项 | 值 | 依据 |
|---|---|---|
| 调用方式 | **单次 LLM 调用**，不要 agent 工具循环 | 工具循环 142 分钟 / 18.9M 字符；单次 2.6 分钟 / 502k，核对通过率还从 76.5% 升到 100% |
| 喂什么 | **只喂函数体** | — |
| 输出 | **纯 JSON** | — |
| 预过滤 | 按崩溃类型查表 | libredwg 滤 72% / leptonica 83% / igraph 95% |
| schema | **`use_lines` 数组，最多 3 个** | R27 实测：单值时标尺那条被丢（`why` 写着 12267，字段填了 12287） |
| 实例数 | **两个独立实例** | 都圈到 = high。**算重合度，不是投票判真假** |

## 不做（都试过失败）

- 让 agent 判"是不是同一块内存"（R23 正例 1/9）
- 多 agent 投票 / agent 审查 agent（没有独立信息源）
- 用 agent 做核对层（**核对必须是程序**）
"""
from __future__ import annotations

import json
import os
import re
import ssl
import sys
import time
import urllib.error
import urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "pipeline"))

API = os.environ.get("SCAN_API", "https://api.deepseek.com/v1/chat/completions")
MODEL = os.environ.get("SCAN_MODEL", "deepseek-chat")
MAX_USE_LINES = 3
RUNS = 2

CRASH_FILTERS = {
    "uaf": dict(desc="释放后使用 / double free",
                triggers=[r"\b\w*(?:free|Free|FREE)\w*\s*\(", r"\bdelete\b", r"\brealloc\s*\("]),
    "hbo": dict(desc="堆缓冲区溢出",
                triggers=[r"\b(memcpy|memmove|strcpy|strncpy|strcat|sprintf|snprintf|vsprintf|alloca)\s*\(",
                          r"\b\w+\s*\[[^\]]*\]"]),
    "stack": dict(desc="栈溢出 / 深递归",
                  triggers=[r"\balloca\s*\(", r"\b\w+\s+\w+\s*\[\s*\d{3,}\s*\]"]),
    "global": dict(desc="全局缓冲区越界",
                   triggers=[r"^\s*(?:static\s+)?[A-Za-z_]\w*\s+\w+\s*\[[^\]]*\]\s*;"]),
}

SYSTEM = """你是 C 代码审计员。只输出 JSON 数组，不要任何解释文字。

任务：在给定的函数里找出**可能出现"释放后使用"**的位置。**可疑就报，不要求确定。**
注意：释放和使用可以在不同语句、可以换了变量名、可以经结构体字段传递。

输出格式（纯 JSON 数组，没有候选就输出 []）：
[{"free_line": <int>,
  "object": "<被释放的变量名或字段路径>",
  "use_lines": [{"line": <int>}, ...],
  "why": "<一两句，必须提到行号>",
  "confidence": "high|medium|low"}]

规则：
- 行号必须是给定代码里真实存在的行号。
- `free_line` 必须是**真正有释放调用**的那一行。
- **`use_lines` 是数组，最多 3 个，按可疑程度排序。**
  一个释放点后面如果有多处可疑使用，**都列出来，不要只挑一个**。
  **特别地：如果释放之后循环回边又回到某一行读了这个对象（比如 while 条件里的判断），
  那一行也要列出来** —— 它常常比"紧接着的下一行"更关键。
- 不要编造。给不出行号就不要报。"""


def _triggers(type_):
    return [re.compile(p, re.M) for p in CRASH_FILTERS[type_]["triggers"]]


def _key():
    from s5_6_lib import get_key
    return get_key()


def _call(prompt, retry=3):
    key = _key()
    body = json.dumps({"model": MODEL,
                       "messages": [{"role": "system", "content": SYSTEM},
                                    {"role": "user", "content": prompt}],
                       "temperature": 0.0, "max_tokens": 4000},
                      ensure_ascii=False).encode("utf-8")
    last = None
    for _ in range(retry):
        req = urllib.request.Request(API, data=body, headers={
            "Authorization": f"Bearer {key}", "Content-Type": "application/json"})
        try:
            with urllib.request.urlopen(req, timeout=300,
                                        context=ssl.create_default_context()) as r:
                d = json.loads(r.read().decode("utf-8"))
                return d["choices"][0]["message"].get("content") or ""
        except urllib.error.HTTPError as e:
            last = RuntimeError(f"HTTP {e.code}: {e.read().decode('utf-8','replace')[:200]}")
        except Exception as e:
            last = e
        time.sleep(2)
    raise last


def _parse_array(text):
    t = (text or "").strip()
    m = re.search(r"```(?:json)?\s*(.*?)```", t, re.S)
    if m:
        t = m.group(1).strip()
    i, j = t.find("["), t.rfind("]")
    if i < 0 or j <= i:
        return None
    try:
        v = json.loads(t[i:j + 1])
        return v if isinstance(v, list) else None
    except json.JSONDecodeError:
        return None


def _expand(c):
    """use_line -> use_lines（最多 3 个）。"""
    fl = c.get("free_line")
    uls = c.get("use_lines")
    if not isinstance(uls, list):
        uls = [c.get("use_line")] if c.get("use_line") is not None else []
    out = []
    for u in uls[:MAX_USE_LINES]:
        ln = u.get("line") if isinstance(u, dict) else u
        if isinstance(ln, int) and ln != fl:
            out.append(ln)
    return fl, out


def _verify(L, fl, ul, type_):
    """核对层（**程序**）：两行存在、非空、free 行真有该类型的触发调用。"""
    if not isinstance(fl, int) or not isinstance(ul, int):
        return False, "bad_fields"
    if not (1 <= fl <= len(L)) or not (1 <= ul <= len(L)):
        return False, "bad_line"
    a, b = L[fl - 1], L[ul - 1]
    if not a.strip() or not b.strip():
        return False, "empty_line"
    if a.strip().startswith(("//", "/*", "*")):
        return False, "comment_line"
    if not any(rx.search(a) for rx in _triggers(type_)):
        return False, "no_trigger_call"
    return True, "ok"


def agent_scan_sites(shortlist_funcs, src_cache, crash_type="uaf", root=None,
                     runs=RUNS, progress=None):
    """agent 圈可疑位置 → 程序核对 → 配对 → 返回 site 列表（标 source="agent"）。

    返回的每条：
      {file, free_line, use_line, object, why, confidence(high/medium/low),
       site_id, source="agent", n_runs, verify_reason}
    """
    if not root:
        return []
    rxs = _triggers(crash_type)
    # ① 预过滤：只送含触发调用的函数
    kept = []
    for f in shortlist_funcs:
        lines = src_cache.get(f["file"])
        if not lines:
            continue
        lo, hi = f["lines"][0] - 1, min(f["lines"][1], len(lines)) - 1
        body = "\n".join(f"{i+1}: {lines[i]}" for i in range(lo, hi))
        if not any(rx.search(body) for rx in rxs):
            continue
        kept.append((f, body, lines))

    # ② 两个独立实例
    raw = []
    for f, body, lines in kept:
        fn_name = f.get("function") or f.get("name") or "?"
        prompt = (f"文件 `{f['file']}`，函数 `{fn_name}`，"
                  f"第 {f['lines'][0]}–{f['lines'][1]} 行。\n\n```c\n{body}\n```\n\n"
                  f"找出可能出现「{CRASH_FILTERS[crash_type]['desc']}」的位置，"
                  f"按系统提示要求的 JSON 数组输出。")
        for run in range(1, runs + 1):
            try:
                arr = _parse_array(_call(prompt)) or []
            except Exception:
                arr = []
            for c in arr:
                fl, uls = _expand(c)
                for ul in uls:
                    ok, why = _verify(lines, fl, ul, crash_type)
                    if not ok:
                        continue
                    raw.append(dict(file=f["file"].lstrip("./"), free_line=fl, use_line=ul,
                                    object=(c.get("object") or "").strip(),
                                    why=(c.get("why") or "")[:300],
                                    self_conf=c.get("confidence"),
                                    run=run, source="agent",
                                    verify_reason=why, function=fn_name))
            if progress and run == runs:
                progress(f, len(raw))

    # ③ 配对 + 重合度（按 (file, free, use) 合并）
    groups = {}
    for r in raw:
        k = (r["file"], r["free_line"], r["use_line"])
        groups.setdefault(k, []).append(r)
    out = []
    for k, rs in groups.items():
        runs_seen = len({x["run"] for x in rs})
        best = max(rs, key=lambda x: len(x.get("why") or ""))
        out.append(dict(best, site_id="", n_runs=runs_seen,
                        confidence=("high" if runs_seen >= runs else
                                    ("medium" if runs_seen == 1 else "low"))))
    out.sort(key=lambda x: (x["confidence"] != "high", x["file"], x["free_line"]))
    for i, s in enumerate(out, 1):
        s["site_id"] = f"ag{i:03d}"
    return out

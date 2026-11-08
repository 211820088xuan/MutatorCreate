"""R26b：单次 LLM 调用扫描（去掉 agent 工具循环）。

## 为什么

R26 的办法 A（每批 1 函数）花了 **18,889,553 chars**，而 libredwg 的 162 个函数体总共只有
**418,723 chars** —— **45 倍**。查日志（`docs/runs/r26/a/log_b*.jsonl`）发现：

- 一批单函数的任务，agent 跑了 **35 轮**、调了 **read_file 25 次 + grep 26 次**；
- 它读的是**整文件的大段**（`1700-2078` = 379 行）——**而 prompt 里已经有函数体了**；
- 每一轮都把**整个历史**重发一遍 → 平方级增长。

## 改法（用户给的顺序）

1. **去掉工具循环，改单次调用** —— 源码已经在 prompt 里
2. **只喂函数体**，不喂整文件
3. **输出纯 JSON 数组**，不要解释性文字
4. **预过滤**：按崩溃类型的查表，先筛掉不含触发调用的函数

## 崩溃类型查表（架构要能切，不只 uaf）

`outputs/stage3/{uaf,hbo,stack,global}` 四个类型，每类一套触发正则。
"""
import argparse
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
from s5_6_lib import get_key  # noqa: E402

API = os.environ.get("SCAN_API", "https://api.deepseek.com/v1/chat/completions")

# ── 【一】崩溃类型查表 ─────────────────────────────────────────────────
# `triggers` 用于**预过滤**（函数里没有任何触发点 → 不送 agent）；
# 对 uaf，同一组正则也用作**核对层**的"释放行必须真有释放调用"。
CRASH_FILTERS = {
    "uaf": dict(
        desc="释放后使用 / double free",
        triggers=[
            r"\b\w*(?:free|Free|FREE)\w*\s*\(",     # free / kfree / LEPT_FREE / dxf_free_pair …
            r"\bdelete\b", r"\brealloc\s*\(",
        ],
    ),
    "hbo": dict(
        desc="堆缓冲区溢出",
        triggers=[
            r"\b(memcpy|memmove|strcpy|strncpy|strcat|sprintf|snprintf|vsprintf|alloca)\s*\(",
            r"\b\w+\s*\[[^\]]*\]",                  # 数组下标
            r"\b\w+\s*\+\s*\w+\s*\)",               # 指针算术的常见形态
        ],
    ),
    "stack": dict(
        desc="栈溢出 / 深递归",
        triggers=[
            r"\balloca\s*\(", r"\b\w+\s+\w+\s*\[\s*\d{3,}\s*\]",   # 大局部数组
            r"\b(\w+)\s*\([^)]*\)\s*\{",                            # 递归候选（按名字再判）
        ],
    ),
    "global": dict(
        desc="全局缓冲区越界",
        triggers=[r"^\s*(?:static\s+)?[A-Za-z_]\w*\s+\w+\s*\[[^\]]*\]\s*;"],
    ),
}


def triggers(type_):
    return [re.compile(p, re.M) for p in CRASH_FILTERS[type_]["triggers"]]


# ── 单次调用 ──────────────────────────────────────────────────────────
SYSTEM = """你是 C 代码审计员。只输出 JSON 数组，不要任何解释文字。

任务：在给定的函数里找出**可能出现"释放后使用"**的位置。**可疑就报，不要求确定。**
注意：释放和使用可以在不同语句、可以换了变量名、可以经结构体字段传递。

输出格式（纯 JSON 数组，没有候选就输出 []）：
[{"free_line": <int>, "use_lines": [<int>, ...], "object": "<变量名或字段路径>",
  "why": "<一两句，必须提到行号>", "confidence": "high|medium|low"}]

规则：
- 行号必须是给定代码里真实存在的行号。
- `free_line` 必须是**真正有释放调用**的那一行。
- **`use_lines` 是数组，最多 3 个，按可疑程度排序。**
  一个释放点后面如果有多处可疑使用，**都列出来，不要只挑一个**。
  **特别地：如果释放之后循环回边又回到某一行读了这个对象（比如 while 条件里的判断），
  那一行也要列出来** —— 它常常比"紧接着的下一行"更关键。
- 不要编造。给不出行号就不要报。"""


def call(prompt, model, temperature=0.0, retry=3):
    key = get_key()
    body = json.dumps({
        "model": model,
        "messages": [{"role": "system", "content": SYSTEM},
                     {"role": "user", "content": prompt}],
        "temperature": temperature,
        "max_tokens": 4000,
    }, ensure_ascii=False).encode("utf-8")
    last = None
    for _ in range(retry):
        req = urllib.request.Request(API, data=body, headers={
            "Authorization": f"Bearer {key}", "Content-Type": "application/json"})
        try:
            with urllib.request.urlopen(req, timeout=300,
                                        context=ssl.create_default_context()) as r:
                d = json.loads(r.read().decode("utf-8"))
                return d["choices"][0]["message"].get("content") or "", d.get("usage") or {}
        except urllib.error.HTTPError as e:
            last = RuntimeError(f"HTTP {e.code}: {e.read().decode('utf-8', 'replace')[:300]}")
        except Exception as e:
            last = e
        time.sleep(2)
    raise last


def parse_json_array(text):
    """从回复里抠出 JSON 数组（模型有时仍会包 ```json）。"""
    t = text.strip()
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


def func_body(root, f):
    p = os.path.join(root, f["file"])
    if not os.path.isfile(p):
        return None, None
    L = open(p, encoding="utf-8", errors="replace").read().split("\n")
    lo, hi = max(0, f["lines"][0] - 1), min(f["lines"][1], len(L))
    body = "\n".join(f"{i + 1}: {L[i]}" for i in range(lo, hi))
    return body, L


MAX_USE_LINES = 3


def expand_uses(c):
    """把一条候选展开成若干条 (free_line, use_line) —— use_lines 最多取前 3 个。"""
    fl = c.get("free_line")
    uls = c.get("use_lines")
    if not isinstance(uls, list):
        uls = [c.get("use_line")] if c.get("use_line") is not None else []
    out = []
    for u in uls[:MAX_USE_LINES]:
        if isinstance(u, int) and u != fl:
            out.append(u)
    return fl, out


def verify_line(L, c, type_, ul=None):
    """核对层（程序）：释放行必须真有该类型的触发调用。"""
    fl = c.get("free_line")
    ul = ul if ul is not None else c.get("use_line")
    if not isinstance(fl, int) or not isinstance(ul, int):
        return False, "bad_fields"
    if not (1 <= fl <= len(L)) or not (1 <= ul <= len(L)):
        return False, "bad_line"
    a, b = L[fl - 1], L[ul - 1]
    if not a.strip() or not b.strip():
        return False, "empty_line"
    if a.strip().startswith(("//", "/*", "*")):
        return False, "comment_line"
    if not any(rx.search(a) for rx in triggers(type_)):
        return False, "no_trigger_call"
    return True, "ok"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--osv", default="ARVO-42494732")
    ap.add_argument("--type", default="uaf", choices=list(CRASH_FILTERS))
    ap.add_argument("--runs", type=int, default=2)
    ap.add_argument("--out", default="")
    ap.add_argument("--prefilter", action="store_true", help="按类型查表先筛函数")
    ap.add_argument("--model", default=os.environ.get("SCAN_MODEL", "deepseek-chat"))
    ap.add_argument("--limit", type=int, default=0)
    a = ap.parse_args()
    OUT = a.out or os.path.join(ROOT, "docs", "runs", "r26b", f"{a.type}")
    os.makedirs(OUT, exist_ok=True)

    P = os.path.join(ROOT, "projects", a.osv)
    wl = json.load(open(os.path.join(P, "audit_worklist.json"), encoding="utf-8"))
    root = json.load(open(os.path.join(P, "source_context.json"), encoding="utf-8"))["repo_local"]
    funcs = [f for f in wl["functions"] if f.get("file") and f.get("lines")]
    funcs.sort(key=lambda f: (f["file"], f["lines"][0]))

    rxs = triggers(a.type)
    kept, skipped = [], 0
    for f in funcs:
        body, L = func_body(root, f)
        if body is None:
            continue
        if a.prefilter and not any(rx.search(body) for rx in rxs):
            skipped += 1
            continue
        kept.append((f, body, L))

    print(f"  {a.osv} / {a.type}: worklist {len(funcs)} 个函数，"
          f"预过滤掉 {skipped}，送 agent {len(kept)}", flush=True)
    if a.limit:
        kept = kept[:a.limit]

    tot_in = tot_out = 0
    tot_sec = 0.0
    for idx, (f, body, L) in enumerate(kept, 1):
        for run in range(1, a.runs + 1):
            p = os.path.join(OUT, f"f_{idx:04d}_r{run}.json")
            if os.path.isfile(p):
                continue
            prompt = (f"文件 `{f['file']}`，函数 `{f['name']}`，"
                      f"第 {f['lines'][0]}–{f['lines'][1]} 行。\n\n```c\n{body}\n```\n\n"
                      f"找出可能出现「{CRASH_FILTERS[a.type]['desc']}」的位置，"
                      f"按系统提示要求的 JSON 数组输出。")
            t0 = time.time()
            try:
                txt, usage = call(prompt, a.model)
                arr = parse_json_array(txt)
                err = "" if arr is not None else "unparsable"
                arr = arr or []
            except Exception as e:
                txt, usage, arr, err = "", {}, [], f"{type(e).__name__}: {e}"[:150]
            cands = []
            for c in arr:
                fl, uls = expand_uses(c)
                for ul in uls:
                    cc = dict(c, free_line=fl, use_line=ul)
                    cc.pop("use_lines", None)
                    ok, why = verify_line(L, cc, a.type, ul=ul)
                    cc["verified"], cc["verify_reason"] = ok, why
                    cands.append(cc)
            el = round(time.time() - t0, 1)
            tot_in += len(prompt)
            tot_out += len(txt)
            tot_sec += el
            open(p, "w", encoding="utf-8").write(json.dumps(dict(
                osv=a.osv, type=a.type, func=f["name"], file=f["file"],
                lines=f["lines"], run=run, prompt_chars=len(prompt),
                out_chars=len(txt), usage=usage, elapsed=el,
                error=err, candidates=cands), ensure_ascii=False))
            if idx % 20 == 0 or idx == len(kept):
                print(f"  {idx}/{len(kept)} 行{f['name']} r{run}: "
                      f"{len(cands)} 处  {el}s", flush=True)
    print(f"  完成：输入 {tot_in:,} chars，输出 {tot_out:,} chars，耗时 {tot_sec/60:.1f} 分钟",
          flush=True)


if __name__ == "__main__":
    main()

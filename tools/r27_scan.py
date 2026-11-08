"""R27：让程序能核对「使用行真的读了那个对象」。

## 根因（R26b 诊断）

agent 的 `use_lines` 填的是"释放点附近看着危险的行"，不是"真的又读了那块内存的行"。
程序只拿到行号，**看不到那一行写了什么**，所以挡不住：
- `tree.c:1165→1166`（1166 里根本没有 `cur`）
- `tree.c:3612→3617`（`&(cur->properties)` 取地址不是解引用）
- `hash.c:252→258`（先释放字段再释放结构体，正常顺序）

## 改法（用户决定：选 C）

`use_lines` 每项从「行号」扩成 `{line, code, access, expr}`：
- `code`：那一行的**源码原文**（不改写、不省略）
- `expr`：那一行里**哪个表达式**读了这块内存
- `access`：`deref` / `addr_of` / `assign_only` / `call_arg` / `other`

**仍然只要事实，不要判断。**

## 程序五道核对（本轮核心）

| # | 核对 | 不通过 |
|---|---|---|
| 1 | `code` 和 pin 源码那一行一致（去空白） | `code_mismatch` |
| 2 | `expr` 在 `code` 里出现 | `expr_not_in_code` |
| 3 | `expr` 里有 `object`（或宿主，全词） | `expr_no_object` |
| 4 | `access` 是 `deref` | `addr_of`/`assign_only` → 丢 |
| 5 | `access` 是 `call_arg` → 保留但低置信 | — |
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
sys.path.insert(0, os.path.join(ROOT, "tools"))
from s5_6_lib import get_key  # noqa: E402
from r26b_scan import CRASH_FILTERS, triggers, func_body, parse_json_array  # noqa: E402

API = os.environ.get("SCAN_API", "https://api.deepseek.com/v1/chat/completions")
MAX_USE = 3

SYSTEM = """你是 C 代码审计员。只输出 JSON 数组，不要任何解释文字。

任务：在给定函数里找出**可能出现"释放后使用"**的位置。**可疑就报，不要求确定。**
注意：释放和使用可以在不同语句、可以换了变量名、可以经结构体字段传递。

输出格式（纯 JSON 数组，没有候选就输出 []）：
[{"free_line": <int>,
  "object": "<被释放的变量名或字段路径>",
  "use_lines": [
    {"line": <int>, "code": "<那一行的源码原文>", "access": "deref|addr_of|assign_only|call_arg|other",
     "expr": "<那一行里哪个表达式读了这块内存>"}
  ],
  "why": "<一两句，必须提到行号>",
  "confidence": "high|medium|low"}]

**use_lines 的每一项是一个事实，不是判断：**
- `code`：把那一行的**源码原文抄下来**，不要改写、不要省略、不要补全。
- `expr`：那一行里**具体是哪个表达式**读了这块内存（如 `pair->code`、`array[j]`）。
- `access`：这次访问是什么性质
  - `deref` = 解引用读写（`p->x`、`p[i]`、`*p`）
  - `addr_of` = 只取地址（`&p->x`）
  - `assign_only` = 只是被赋值、没有读（`p = NULL`、`*pp = NULL`）
  - `call_arg` = 作为实参传给别的函数
  - `other` = 其他
- **如果那一行里找不到这块内存被读到，就不要报这一行。**

**use_lines 最多 3 个，按可疑程度排序。** 如果释放之后循环回边又回到某一行读了它，那一行也要列。
`free_line` 必须是真正有释放调用的那一行。不要编造。"""


def call(prompt, model, retry=3):
    key = get_key()
    body = json.dumps({"model": model,
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
                return d["choices"][0]["message"].get("content") or "", d.get("usage") or {}
        except urllib.error.HTTPError as e:
            last = RuntimeError(f"HTTP {e.code}: {e.read().decode('utf-8','replace')[:300]}")
        except Exception as e:
            last = e
        time.sleep(2)
    raise last


def norm(s):
    return re.sub(r"\s+", "", s or "")


def has_word(text, obj):
    """全词匹配（`pboxa` 不算 `boxa`）。"""
    if not obj:
        return False
    return bool(re.search(rf"(?<![\w.>]){re.escape(obj)}(?![\w])", text))


def check_use(L, u, obj, type_):
    """五道核对。返回 (ok, reason, access)。"""
    ln = u.get("line")
    if not isinstance(ln, int) or not (1 <= ln <= len(L)):
        return False, "bad_line", None
    src = L[ln - 1]
    if not src.strip():
        return False, "empty_line", None
    if src.strip().startswith(("//", "/*", "*")):
        return False, "comment_line", None
    # ① code 和 pin 源码逐字一致（去空白）
    if norm(u.get("code")) != norm(src):
        return False, "code_mismatch", None
    # ② expr 在 code 里
    expr = (u.get("expr") or "").strip()
    if not expr or norm(expr) not in norm(src):
        return False, "expr_not_in_code", None
    # ③ expr 里有 object（或宿主，全词）
    host = re.split(r"->|\.", obj)[0] if ("->" in obj or "." in obj) else obj
    if not (has_word(expr, obj) or (host and has_word(expr, host))):
        return False, "expr_no_object", None
    # ④ access 必须是 deref（call_arg 保留但低置信）
    acc = (u.get("access") or "").strip()
    if acc in ("addr_of", "assign_only"):
        return False, "access_" + acc, acc
    if acc == "other":
        return False, "access_other", acc
    if acc == "call_arg":
        return True, "call_arg_lowconf", acc
    if acc != "deref":
        return False, "access_bad", acc
    return True, "ok", acc


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--osv", default="ARVO-42494732")
    ap.add_argument("--type", default="uaf", choices=list(CRASH_FILTERS))
    ap.add_argument("--runs", type=int, default=2)
    ap.add_argument("--out", default="")
    ap.add_argument("--model", default=os.environ.get("SCAN_MODEL", "deepseek-chat"))
    a = ap.parse_args()
    OUT = a.out or os.path.join(ROOT, "docs", "runs", "r27", a.osv)
    os.makedirs(OUT, exist_ok=True)

    P = os.path.join(ROOT, "projects", a.osv)
    wl = json.load(open(os.path.join(P, "audit_worklist.json"), encoding="utf-8"))
    root = json.load(open(os.path.join(P, "source_context.json"), encoding="utf-8"))["repo_local"]
    funcs = [f for f in wl["functions"] if f.get("file") and f.get("lines")]
    funcs.sort(key=lambda f: (f["file"], f["lines"][0]))

    rxs = triggers(a.type)
    kept = []
    for f in funcs:
        body, L = func_body(root, f)
        if body is None:
            continue
        if any(rx.search(body) for rx in rxs):
            kept.append((f, body, L))
    print(f"  {a.osv}: worklist {len(funcs)}，预过滤后 {len(kept)}", flush=True)

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
                fl = c.get("free_line")
                obj = (c.get("object") or "").strip()
                if not isinstance(fl, int) or not (1 <= fl <= len(L)):
                    continue
                # 释放行必须真有触发调用
                if not any(rx.search(L[fl - 1]) for rx in rxs):
                    cands.append(dict(c, use_line=None, verified=False,
                                      verify_reason="no_trigger_call"))
                    continue
                uls = c.get("use_lines") or []
                if not isinstance(uls, list):
                    uls = []
                for u in uls[:MAX_USE]:
                    if not isinstance(u, dict):
                        continue
                    ok, why, acc = check_use(L, u, obj, a.type)
                    cands.append(dict(free_line=fl, use_line=u.get("line"), object=obj,
                                      code=u.get("code"), expr=u.get("expr"), access=acc,
                                      why=c.get("why"), confidence=c.get("confidence"),
                                      verified=ok, verify_reason=why))
            el = round(time.time() - t0, 1)
            tot_in += len(prompt)
            tot_out += len(txt)
            tot_sec += el
            open(p, "w", encoding="utf-8").write(json.dumps(dict(
                osv=a.osv, func=f["name"], file=f["file"], lines=f["lines"], run=run,
                prompt_chars=len(prompt), out_chars=len(txt), usage=usage,
                elapsed=el, error=err, candidates=cands), ensure_ascii=False))
            if idx % 20 == 0 or idx == len(kept):
                print(f"  {idx}/{len(kept)} {f['name']} r{run}: {len(cands)} 处 {el}s", flush=True)
    print(f"  完成：输入 {tot_in:,} / 输出 {tot_out:,} / {tot_sec/60:.1f} 分钟", flush=True)


if __name__ == "__main__":
    main()

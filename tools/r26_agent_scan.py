"""R25：把正则扫描器换成 agent —— 只圈位置，报事实，不下判断。

## 为什么换

`scan_sites()` 找的是 `free(X)` 后面出现 `X->` —— 实测这种写法在真实 UAF 里只占 **13%**（R19），
另外 87% 是换名字（57%）或经字段中转（25%）。

R4（从头找 UAF、下判断）失败：独有发现 0 条。
R23（判"是不是同一块内存"、下判断）失败：正例 1/9、同一 prompt 两个相反答案。
**但 R23 也测出：它报事实的准确率 99.3%（816 处引用只编了 6 处）。**

→ **只圈位置、只报事实、不下判断。**

## 三层

| 层 | 谁 | 做什么 |
|---|---|---|
| 1 扫描 | **agent ×2 独立实例** | 圈可疑位置，报事实 |
| 2 核对 | **程序** | 行号存在？非空？释放行真有释放调用？→ 核不上**丢弃** |
| 3 重合 | 程序 | 两实例都圈到 → high；只有一个 → medium（**仍然收下**） |

## 增量落盘 / 可续跑

`docs/runs/r25/batch_<key>_<run>.json`，一行一批；重跑跳过已完成的 (batch, run)。
"""
import argparse
import json
import os
import re
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "pipeline"))
from s5_3_audit import read_file_tool, grep_tool, list_dir_tool  # noqa: E402
from s5_6_lib import Agent  # noqa: E402

OUT = os.path.join(ROOT, "docs", "runs", "r25")   # 可被 --out 覆盖

SYSTEM = """你是一个 C 代码审计员。你的任务是**圈出可疑位置**，不是下判断。

规则：
- 你只能看**当前项目源码树**。不要猜。
- **"可疑"就够了，不要求确定。** 这个项目要的是"可能有问题的地方"，宁可多报一点。
- 但**不许编造**：每一处都要能对上真实的行号。给不出行号就不要报。
- 不要读与这批函数无关的文件。
"""

FINISH = {
    "type": "object",
    "properties": {
        "candidates": {
            "type": "array",
            "description": "可疑的「释放后使用」位置。没有就返回空数组。",
            "items": {
                "type": "object",
                "properties": {
                    "file": {"type": "string", "description": "相对项目根的路径"},
                    "free_line": {"type": "integer", "description": "释放发生在哪一行"},
                    "use_line": {"type": "integer", "description": "使用发生在哪一行"},
                    "object": {"type": "string", "description": "变量名或字段路径"},
                    "why": {"type": "string", "description": "为什么可疑（必须引用行号）"},
                    "confidence": {"type": "string", "enum": ["high", "medium", "low"]},
                },
                "required": ["file", "free_line", "use_line", "object", "why"],
            },
        }
    },
    "required": ["candidates"],
}

# 释放调用的识别（核对层用：free_line 那行必须真的有释放）
# R25 修：原来只认**以** free/Free/FREE **结尾**的名字 -> 把项目自己的包装函数全判死了。
# 实测 `no_free_call` 的 144 条里 ~102 条是真释放：
#   dxf_free_pair 49 / dwg_free_object_private 17 / dwg_free_object 8 / dwg_free_eed 7 /
#   free_array_hdls 6 / FREE_IF 9 / freea 5 …
# 改成 **free/Free/FREE 出现在名字里任意位置**都算（这些确实都是释放）。
FREE_RX = re.compile(
    r"\b(free|kfree|cfree|delete|realloc)\s*\(|\b\w*(?:free|Free|FREE)\w*\s*\(")


def log(m):
    print(f"[{time.strftime('%H:%M:%S')}] {m}", flush=True)


# ── 批 ────────────────────────────────────────────────────────────────
def load_batches(osv, size):
    P = os.path.join(ROOT, "projects", osv)
    wl = json.load(open(os.path.join(P, "audit_worklist.json"), encoding="utf-8"))
    ctx = json.load(open(os.path.join(P, "source_context.json"), encoding="utf-8"))
    root = ctx["repo_local"]
    funcs = [f for f in wl["functions"] if f.get("file") and f.get("lines")]
    funcs.sort(key=lambda f: (f["file"], f["lines"][0]))
    out = []
    for i in range(0, len(funcs), size):
        out.append(funcs[i:i + size])
    return root, out


def read_func(root, f):
    p = os.path.join(root, f["file"])
    if not os.path.isfile(p):
        return None
    L = open(p, encoding="utf-8", errors="replace").read().split("\n")
    lo, hi = max(0, f["lines"][0] - 1), min(f["lines"][1], len(L))
    body = "\n".join(f"{i + 1}: {L[i]}" for i in range(lo, hi))
    return body


def build_task(root, batch):
    parts = []
    for f in batch:
        body = read_func(root, f)
        if body is None:
            continue
        parts.append(f"### 文件 `{f['file']}`，函数 `{f['name']}`（第 {f['lines'][0]}–{f['lines'][1]} 行）\n\n"
                     f"```c\n{body}\n```")
    return f"""下面是 {len(parts)} 个函数的源码（行号已标在每行开头）。

找出**可能出现「释放后使用」**的地方。**不要求确定，可疑就报。**

每处给出：
- `file` / `free_line`：释放发生在哪
- `use_line`：使用发生在哪
- `object`：涉及什么对象（变量名或字段路径）
- `why`：为什么可疑（一两句，**必须引用行号**）
- `confidence`：high / medium / low

**注意：释放和使用可以在不同函数、可以换了变量名、可以经结构体字段传递。
这些正是现有工具看不见的，请重点关注。**

判不出就不报，**不要为了凑数编造**。

---

{chr(10).join(parts)}
"""


# ── 核对层（程序，不是 agent）────────────────────────────────────────
def verify(root, c):
    """返回 (ok, reason)。"""
    f = (c.get("file") or "").lstrip("./")
    fl, ul = c.get("free_line"), c.get("use_line")
    if not f or not isinstance(fl, int) or not isinstance(ul, int):
        return False, "bad_fields"
    p = os.path.join(root, f)
    if not os.path.isfile(p):
        return False, "bad_file"
    L = open(p, encoding="utf-8", errors="replace").read().split("\n")
    if not (1 <= fl <= len(L)) or not (1 <= ul <= len(L)):
        return False, "bad_line"
    a, b = L[fl - 1], L[ul - 1]
    if not a.strip() or not b.strip():
        return False, "empty_line"
    if a.strip().startswith(("//", "/*", "*")) and b.strip().startswith(("//", "/*", "*")):
        return False, "comment_line"
    # 释放行必须真有释放调用
    if not FREE_RX.search(a):
        return False, "no_free_call"
    # object 出现与否**不丢弃**
    obj = (c.get("object") or "").strip()
    found = bool(obj) and (obj in a or obj in b)
    return True, ("ok" if found else "object_not_found")


def one(root, batch, run, model, max_turns):
    ag = Agent(name=f"scan::r{run}", root=root, system=SYSTEM,
               tools=[read_file_tool(), grep_tool(), list_dir_tool()],
               finish_schema=FINISH, model=model, max_turns=max_turns,
               max_chars=700_000,
               log_path=os.path.join(OUT, f"log_b{run}.jsonl"))
    t0 = time.time()
    try:
        res = ag.run(build_task(root, batch))
    except Exception as e:
        return dict(candidates=[], error=f"{type(e).__name__}: {e}"[:200],
                    elapsed=round(time.time() - t0, 1), spent=ag.spent_chars)
    cands = res.get("candidates") or []
    out = []
    for c in cands:
        ok, why = verify(root, c)
        c = dict(c)
        c["verified"] = ok
        c["verify_reason"] = why
        out.append(c)
    return dict(candidates=out, elapsed=round(time.time() - t0, 1), spent=ag.spent_chars)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--osv", default="ARVO-42494732")
    ap.add_argument("--size", type=int, default=6, help="每批函数数（5–10）")
    ap.add_argument("--runs", type=int, default=2, help="独立实例数")
    ap.add_argument("--model", default=os.environ.get("SCAN_MODEL", "deepseek-chat"))
    ap.add_argument("--max-turns", type=int, default=25)
    ap.add_argument("--limit", type=int, default=0, help="只跑前 N 批（调试）")
    ap.add_argument("--out", default="", help="输出目录（默认 docs/runs/r25）")
    a = ap.parse_args()
    global OUT
    if a.out:
        OUT = a.out
    os.makedirs(OUT, exist_ok=True)
    root, batches = load_batches(a.osv, a.size)
    if a.limit:
        batches = batches[:a.limit]
    log(f"{a.osv}: {len(batches)} 批 × {a.runs} 实例，根={root}")
    tot = 0
    for bi, batch in enumerate(batches, 1):
        for run in range(1, a.runs + 1):
            p = os.path.join(OUT, f"batch_{a.osv}_{bi:03d}_r{run}.json")
            if os.path.isfile(p):
                continue
            r = one(root, batch, run, a.model, a.max_turns)
            r.update(osv=a.osv, batch=bi, run=run,
                     funcs=[f["name"] for f in batch])
            open(p, "w", encoding="utf-8").write(json.dumps(r, ensure_ascii=False))
            n = len(r.get("candidates") or [])
            nok = sum(1 for c in (r.get("candidates") or []) if c.get("verified"))
            tot += n
            log(f"  b{bi:03d} r{run}: {n} 处（核对通过 {nok}）{r.get('elapsed')}s")
    log(f"完成，累计 {tot} 处")


if __name__ == "__main__":
    main()

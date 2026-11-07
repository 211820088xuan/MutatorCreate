"""R23 第二部分：验证「agent 只回答一个判断题」可不可行。

## 为什么不从头找

R4 试过"让 agent 从头找 UAF"，**162 个函数、独有且被采纳的发现 0 条**，
同一个 prompt 跑两次结论相反。**注意力粒度太粗。**

## 本轮换法

**工具找候选，agent 只回答一个判断题：**

> 函数 A 的第 X 行有 `free(P)`，函数 B 的第 Y 行读了 `Q`。
> 1. P 和 Q 是不是同一块内存？怎么关联的（哪一行赋值/传参/存字段）？
> 2. 存在一条真实路径让 A 的释放先于 B 的读取吗？
> 3. `real` / `false_positive` / `unclear`

## 三道防线（对着 R4 的三个坑）

| R4 的坑 | 本轮 |
|---|---|
| **它会编** | 每一跳的 `文件:行` **程序自动核对**（行存在、非空、行内有那个标识符）；核不上记 `fabricated` |
| **不可复现** | 同一条候选跑 **3 次**，三次一致才采纳；不一致记 `unstable`，**不计入准确率** |
| **注意力散** | 一次只问一条 |

## 增量落盘 / 可续跑

结果写 `docs/runs/r23/results.jsonl`（一行 = 一次运行），重跑会跳过已完成的 (key, rep)。
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

OUT = os.path.join(ROOT, "docs", "runs", "r23")
RESULTS = os.path.join(OUT, "results.jsonl")

# ── 样本 ────────────────────────────────────────────────────────────────
# 正例：R19 的 F4「别名 / 经字段」（都是 reproduced crash，答案确定）
POS = [
    dict(key="P1", osv="ARVO-42486883", proj="libxml2", pin="00ed736eecf9",
         root="/tmp/opencode/cpg_cache/src/gitlab.gnome.org_GNOME_libxml2.git_00ed736eecf9",
         free_file="xmlreader.c", free_line=507, use_file="xmlreader.c", use_line=1484,
         note="别名"),
    dict(key="P2", osv="ARVO-42487244", proj="libxml2", pin="f0fd1b67fc88",
         root="/tmp/opencode/cpg_cache/src/gitlab.gnome.org_GNOME_libxml2.git_f0fd1b67fc88",
         free_file="xmlreader.c", free_line=569, use_file="xpath.c", use_line=3760,
         note="别名"),
    dict(key="P3", osv="ARVO-42487785", proj="libxml2", pin="f0fd1b67fc88",
         root="/tmp/opencode/cpg_cache/src/gitlab.gnome.org_GNOME_libxml2.git_f0fd1b67fc88",
         free_file="xmlreader.c", free_line=481, use_file="tree.c", use_line=4197,
         note="别名"),
    dict(key="P4", osv="ARVO-42491546", proj="igraph", pin="883bd139af37",
         root="/tmp/opencode/cpg_cache/src/github.com_igraph_igraph_883bd139af37",
         free_file="src/io/gml-tree.c", free_line=189,
         use_file="src/core/vector_ptr.c", use_line=264, note="经字段/别名"),
    dict(key="P5", osv="ARVO-42531532", proj="libxml2", pin="e45a4d711500",
         root="/tmp/opencode/cpg_cache/src/gitlab.gnome.org_GNOME_libxml2.git_e45a4d711500",
         free_file="valid.c", free_line=2503, use_file="valid.c", use_line=2745, note="经字段"),
    dict(key="P6", osv="ARVO-42532360", proj="libxml2", pin="e45a4d711500",
         root="/tmp/opencode/cpg_cache/src/gitlab.gnome.org_GNOME_libxml2.git_e45a4d711500",
         free_file="xmlreader.c", free_line=421, use_file="valid.c", use_line=5937,
         note="别名"),
    dict(key="P7", osv="ARVO-42532747", proj="libxml2", pin="e45a4d711500",
         root="/tmp/opencode/cpg_cache/src/gitlab.gnome.org_GNOME_libxml2.git_e45a4d711500",
         free_file="valid.c", free_line=2503, use_file="valid.c", use_line=2745, note="经字段"),
    dict(key="P8", osv="ARVO-42533922", proj="libxml2", pin="d4d1f3f33d6d",
         root="/tmp/opencode/cpg_cache/src/gitlab.gnome.org_GNOME_libxml2.git_d4d1f3f33d6d",
         free_file="tree.c", free_line=794, use_file="tree.c", use_line=8454, note="经字段"),
    dict(key="P9", osv="ARVO-42533950", proj="libxml2", pin="d4d1f3f33d6d",
         root="/tmp/opencode/cpg_cache/src/gitlab.gnome.org_GNOME_libxml2.git_d4d1f3f33d6d",
         free_file="tree.c", free_line=794, use_file="tree.c", use_line=3938, note="经字段"),
]

# 负例：docs/verified_sites.json 里核实为 **false** 的（有效条目）
NEG = [
    dict(key="N1", osv="ARVO-42494732", proj="libredwg", pin="ff69eeda6658",
         root="/tmp/opencode/cpg_cache/src/github.com_LibreDWG_libredwg_ff69eeda6658",
         free_file="src/encode.c", free_line=1271, use_file="src/encode.c", use_line=1272,
         note="dwg_free_object_private 只释放类型私有数据，不释放 obj"),
    dict(key="N2", osv="ARVO-42494732", proj="libredwg", pin="ff69eeda6658",
         root="/tmp/opencode/cpg_cache/src/github.com_LibreDWG_libredwg_ff69eeda6658",
         free_file="src/encode.c", free_line=1308, use_file="src/encode.c", use_line=1313,
         note="同上；obj->type = … 是往活对象写字段"),
    dict(key="N3", osv="ARVO-42494732", proj="libredwg", pin="ff69eeda6658",
         root="/tmp/opencode/cpg_cache/src/github.com_LibreDWG_libredwg_ff69eeda6658",
         free_file="src/in_json.c", free_line=4201, use_file="src/in_json.c", use_line=4216,
         note="free(tokens.tokens); exit(1); —— 使用不可达"),
    dict(key="N4", osv="ARVO-42488049", proj="leptonica", pin="90ec70fd4322",
         root="/tmp/opencode/cpg_cache/src/github.com_DanBloomberg_leptonica.git_90ec70fd4322",
         free_file="src/pix4.c", free_line=3053, use_file="src/pix4.c", use_line=3064,
         note="if/else 互斥分支"),
    dict(key="N5", osv="ARVO-42488049", proj="leptonica", pin="90ec70fd4322",
         root="/tmp/opencode/cpg_cache/src/github.com_DanBloomberg_leptonica.git_90ec70fd4322",
         free_file="src/pix4.c", free_line=3065, use_file="src/pix4.c", use_line=3064,
         note="下一轮外层循环头重新赋值 array"),
]

SYSTEM = """你是一个 C 代码审查员。你的任务只有一个：判断"两处代码是不是同一块内存的 UAF"。

规则：
- 你只能用 read_file / grep / list_dir 读**当前项目源码树**。不要猜。
- **每一个结论都要给 `文件:行` 作为依据。** 给不出就不要说。
- 如果读了之后仍然判不出，**必须**填 unclear，不要为了让答案好看而猜。
- 不要读与这个问题无关的文件；一次只回答这一个问题。
"""

FINISH = {
    "type": "object",
    "properties": {
        "same_memory": {"type": "string", "enum": ["yes", "no", "unclear"]},
        "same_memory_how": {"type": "string",
                            "description": "如果是 yes：哪一行赋值/传参/存字段把 P 和 Q 关联起来（给 文件:行）"},
        "path": {"type": "array", "description": "真实执行路径上的每一跳，每跳给 文件:行 和一句话说明",
                 "items": {"type": "object",
                           "properties": {"file": {"type": "string"},
                                          "line": {"type": "integer"},
                                          "what": {"type": "string"}},
                           "required": ["file", "line", "what"]}},
        "verdict": {"type": "string", "enum": ["real", "false_positive", "unclear"]},
        "reason": {"type": "string"},
        "citations": {"type": "array", "description": "所有作为依据的 文件:行",
                      "items": {"type": "object",
                                "properties": {"file": {"type": "string"},
                                               "line": {"type": "integer"},
                                               "expect": {"type": "string",
                                                          "description": "这一行应该包含的标识符/片段"}},
                                "required": ["file", "line"]}},
    },
    "required": ["same_memory", "verdict", "reason"],
}


def log(m):
    print(f"[{time.strftime('%H:%M:%S')}] {m}", flush=True)


def done():
    s = set()
    if os.path.isfile(RESULTS):
        for ln in open(RESULTS, encoding="utf-8"):
            ln = ln.strip()
            if ln:
                try:
                    d = json.loads(ln)
                    s.add((d["key"], d["rep"]))
                except Exception:
                    pass
    return s


def verify_citations(root, cites):
    """防线 1：每一跳的 `文件:行` 程序自动核对。"""
    ok, bad = [], []
    for c in cites or []:
        f, ln = c.get("file"), c.get("line")
        if not f or not ln:
            bad.append(dict(c, why="缺 file/line"))
            continue
        # 只允许相对路径
        f = f.lstrip("./")
        p = os.path.join(root, f)
        if not os.path.isfile(p):
            bad.append(dict(c, why="文件不存在"))
            continue
        try:
            L = open(p, encoding="utf-8", errors="replace").read().split("\n")
        except Exception:
            bad.append(dict(c, why="读不了"))
            continue
        if not (1 <= int(ln) <= len(L)):
            bad.append(dict(c, why=f"行号越界（{len(L)} 行）"))
            continue
        text = L[int(ln) - 1]
        exp = (c.get("expect") or "").strip()
        if exp and exp not in text:
            bad.append(dict(c, why=f"行内没有 `{exp[:30]}`", text=text[:120]))
            continue
        if not text.strip():
            bad.append(dict(c, why="空行"))
            continue
        ok.append(c)
    return ok, bad


def build_task(s):
    return f"""项目：{s['proj']}（pin `{s['pin']}`，源码树已给你）

一条候选：
- **释放**：`{s['free_file']}` 第 **{s['free_line']}** 行（这里有一次释放）
- **使用**：`{s['use_file']}` 第 **{s['use_line']}** 行（这里读了一块内存）

请回答三件事：

1. **释放的是哪块内存、使用读的是哪块？它们是不是同一块？**
   如果是，说清楚**怎么关联起来的** —— 哪一行赋值 / 传参 / 存进结构体字段 / 赋给另一个变量。
   每一步都要给 `文件:行`。

2. **存在一条真实的执行路径，让"释放"先于"使用"吗？**
   把路径上的每一跳列出来（`文件:行` + 一句话）。注意：
   - 释放和使用之间有没有 `return` / `break` / `continue` / `goto` / `exit` 让使用**不可达**？
     （**`break` 在 `switch` 里只跳出 switch，后面的代码仍然可达**）
   - 释放和使用是不是分属**互斥**的 `if` / `else` 两个分支？
   - 如果是循环回边：**下一轮会不会重新赋值**那个指针（在循环头）？

3. 结论：`real` / `false_positive` / `unclear`

**判不出就写 `unclear`，不要猜。** 所有依据都要给 `文件:行`。
"""


def one(s, rep, model, max_turns):
    ag = Agent(name=f"judge::{s['key']}::{rep}", root=s["root"], system=SYSTEM,
               tools=[read_file_tool(), grep_tool(), list_dir_tool()],
               finish_schema=FINISH, model=model, max_turns=max_turns,
               max_chars=300_000,
               log_path=os.path.join(OUT, f"log_{s['key']}_{rep}.jsonl"))
    t0 = time.time()
    try:
        res = ag.run(build_task(s))
    except Exception as e:
        return dict(key=s["key"], rep=rep, osv=s["osv"], group=("pos" if s["key"].startswith("P") else "neg"),
                    error=f"{type(e).__name__}: {e}"[:200], elapsed_sec=round(time.time() - t0, 1))
    cites = list(res.get("citations") or [])
    for h in (res.get("path") or []):
        cites.append({"file": h.get("file"), "line": h.get("line"), "expect": ""})
    ok, bad = verify_citations(s["root"], cites)
    return dict(key=s["key"], rep=rep, osv=s["osv"], project=s["proj"],
                group=("pos" if s["key"].startswith("P") else "neg"),
                note=s.get("note"), free=f"{s['free_file']}:{s['free_line']}",
                use=f"{s['use_file']}:{s['use_line']}",
                same_memory=res.get("same_memory"), same_memory_how=res.get("same_memory_how"),
                verdict=res.get("verdict"), reason=(res.get("reason") or "")[:500],
                n_cites=len(cites), n_ok=len(ok), n_bad=len(bad),
                bad=bad[:5], n_path=len(res.get("path") or []),
                elapsed_sec=round(time.time() - t0, 1), spent_chars=ag.spent_chars)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", default=os.environ.get("JUDGE_MODEL", "deepseek-chat"))
    ap.add_argument("--reps", type=int, default=3)
    ap.add_argument("--max-turns", type=int, default=40)
    ap.add_argument("--only", default=None, help="只跑某条 key（调试）")
    a = ap.parse_args()
    os.makedirs(OUT, exist_ok=True)
    d = done()
    todo = [s for s in (POS + NEG) if not a.only or s["key"] == a.only]
    log(f"续跑：已完成 {len(d)} 次运行；待测 {len(todo)} 条 × {a.reps} 次")
    for s in todo:
        for rep in range(1, a.reps + 1):
            if (s["key"], rep) in d:
                continue
            r = one(s, rep, a.model, a.max_turns)
            open(RESULTS, "a", encoding="utf-8").write(json.dumps(r, ensure_ascii=False) + "\n")
            log(f"  {s['key']} rep{rep}: verdict={r.get('verdict')} cites={r.get('n_ok')}/{r.get('n_cites')} "
                f"bad={r.get('n_bad')} {r.get('elapsed_sec')}s")
    log("完成")


if __name__ == "__main__":
    main()

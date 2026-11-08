"""R28 步骤 1：候选排序 + 选前 N。

## 排序依据（用户定的，从强到弱）

1. **已知崩溃点**（模式 A 专有）—— `facts` 的 `crash.site` 命中 → **排第一**
2. **两实例重合度** —— high > medium > low
3. **调用图距离** —— 离 `LLVMFuzzerTestOneInput` 越近越靠前
4. **agent 自报 confidence** —— 最弱，只做 tie-break

## 已知崩溃点的用法（用户明确过）

> 「不是改变变异算子里面的策略，而是**提高这个崩溃点在后续站点转化成变异策略
> 应用到变异算子这个过程的被使用概率**。」

**优势在"挑哪些候选做成策略"这一步，不是在算子里占多少权重。**
"""
import argparse
import collections
import glob
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

CONF_ORDER = {"high": 0, "medium": 1, "low": 2}


def load_known_crash_lines(osv):
    """该项目的已知崩溃 (文件名 -> 行号集合)，以及 free 栈涉及的文件。"""
    P = os.path.join(ROOT, "artifacts", "facts")
    out = collections.defaultdict(set)
    for fp in glob.glob(os.path.join(P, "*", "facts.json")):
        try:
            f = json.load(open(fp, encoding="utf-8"))
        except Exception:
            continue
        proj = str(f.get("project") or "").lower()
        if proj != osv[0].lower():
            continue
        c = f.get("crash") or {}
        s = c.get("site") or {}
        if s.get("file") and s.get("line"):
            out[os.path.basename(str(s["file"]))].add(int(s["line"]))
        for x in f.get("sites") or []:
            if x.get("kind") == "free" and x.get("line"):
                out[os.path.basename(str(x.get("file") or ""))].add(int(x["line"]))
    return out


def load_depths(osv):
    """worklist 里的调用图深度（离 fuzz entry 几跳）。"""
    p = os.path.join(ROOT, "projects", osv, "audit_worklist.json")
    wl = json.load(open(p, encoding="utf-8"))
    d = {}
    for f in wl.get("functions") or []:
        key = (f.get("file", "").lstrip("./"), f.get("name"))
        d[key] = f.get("depth")
    return d


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--osv", required=True)
    ap.add_argument("--proj", required=True, help="facts 里的 project 名（小写）")
    ap.add_argument("--pairs", required=True, help="paired.json")
    ap.add_argument("--top", type=int, default=5)
    a = ap.parse_args()

    known = load_known_crash_lines((a.proj,))
    depths = load_depths(a.osv)
    pairs = json.load(open(a.pairs, encoding="utf-8"))["pairs"]

    def dist(p):
        # 用 free_line 所在函数的深度；找不到就当作很深
        best = None
        for (f, name), d in depths.items():
            if f == p["file"].lstrip("./") and isinstance(d, int):
                best = d if best is None else min(best, d)
        return best if best is not None else 99

    scored = []
    for p in pairs:
        fn = os.path.basename(p["file"])
        hit_use = p["use_line"] in known.get(fn, set())
        hit_free = p["free_line"] in known.get(fn, set())
        hit = 2 if hit_use else (1 if hit_free else 0)
        scored.append(dict(p, known_hit=hit, depth=dist(p)))

    scored.sort(key=lambda x: (-x["known_hit"], CONF_ORDER.get(x["confidence"], 9),
                               x["depth"], x["file"], x["free_line"], x["use_line"]))

    print(f"  {a.proj}: {len(scored)} 条候选，已知崩溃行 {sum(len(v) for v in known.values())} 个")
    print(f"  命中已知崩溃的: {sum(1 for x in scored if x['known_hit'])}")
    print()
    print("  前 10:")
    for i, x in enumerate(scored[:10], 1):
        tag = "★UAF行" if x["known_hit"] == 2 else ("★free行" if x["known_hit"] == 1 else "     ")
        print(f"    {i:>2}. {tag} {x['file']}:{x['free_line']}→{x['use_line']}  "
              f"{x['kind']}/{x['confidence']}  depth={x['depth']}  obj={x['object'][:30]}")
    out = os.path.join(os.path.dirname(a.pairs), "ranked.json")
    json.dump(scored, open(out, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(f"\n  写出 {out}")
    print(f"  前 {a.top} 将进入证据链")


if __name__ == "__main__":
    main()

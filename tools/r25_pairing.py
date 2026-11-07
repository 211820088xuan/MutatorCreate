"""R25b（步骤 5 改）：配对交给程序。

## 为什么

R25 第一版让 agent **配对**（`12284 → 12287`、`12275 → 12267`），
但它把 `12284` 配给了另一处 `dxf_free_pair(12287)`、把 `12267` 配给了 `12275`。

**配对本身就是一种判断** —— 正是 R23 证明它不可靠的那类判断。

## 改法

1. 把已有候选拆成**两个列表**：释放点、使用点（不重跑 agent，零额外成本）
2. 程序做配对：**同一个 object** 的 释放 × 使用 笛卡尔积
3. 用 `blocks()` / `flow()` 过滤控制流不可达的（R21/R22 刚修好 blocks 的 K&R 识别）
4. 套现有守卫：重赋值、`return`/`exit`、if/else 互斥、switch 里的 break
5. `object` 不同但可能是别名的 → **单独一类，不丢**

用法：
    python3 tools/r25_pairing.py --osv ARVO-42494732
"""
import argparse
import collections
import glob
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "pipeline"))
sys.path.insert(0, os.path.join(ROOT, "tools"))
from s5_6_lib import blocks  # noqa: E402
from r25_agent_scan import verify as verify_cand  # noqa: E402

OUT = os.path.join(ROOT, "docs", "runs", "r25")


def load_raw(osv):
    rows = []
    for fn in sorted(glob.glob(os.path.join(OUT, f"batch_{osv}_*.json"))):
        d = json.load(open(fn, encoding="utf-8"))
        for c in d.get("candidates") or []:
            c = dict(c, run=d["run"], batch=d["batch"])
            ok, why = verify_cand(_root(osv), c)
            c["verified"], c["verify_reason"] = ok, why
            rows.append(c)
    return rows


_R = {}


def _root(osv):
    if osv not in _R:
        P = os.path.join(ROOT, "projects", osv, "source_context.json")
        _R[osv] = json.load(open(P, encoding="utf-8"))["repo_local"]
    return _R[osv]


def load_funcs(osv):
    P = os.path.join(ROOT, "projects", osv, "audit_worklist.json")
    wl = json.load(open(P, encoding="utf-8"))
    out = []
    for f in wl["functions"]:
        if f.get("file") and f.get("lines"):
            out.append(f)
    return out


def func_of(funcs, file, line):
    for f in funcs:
        if f["file"].lstrip("./") == file and f["lines"][0] <= line <= f["lines"][1]:
            return f
    return None


def _innermost(blks, line):
    c = [b for b in blks if b["open"] <= line <= b["close"]]
    return max(c, key=lambda b: b["open"]) if c else None


def _enclosing_ie(blks, line):
    return [b for b in blks if b["kind"] in ("if", "else") and b["open"] <= line <= b["close"]]


def exclusive_if_else(blks, i, j):
    for a in _enclosing_ie(blks, i):
        for b in _enclosing_ie(blks, j):
            if a is b or {a["kind"], b["kind"]} != {"if", "else"}:
                continue
            x, y = sorted((a, b), key=lambda t: t["open"])
            if x["kind"] == "if" and y["kind"] == "else" and 0 <= y["header"] - x["close"] <= 4:
                return True
    return False


GUARD_RX = re.compile(r"\b(return|exit|abort|longjmp|_Exit)\b")


def guard_block(L, blks, fl, ul, var):
    """fl/ul 是 **0-based** 行号。返回 None（通过）或守卫名字。

    释放 → 使用（直线方向）；如果 ul < fl，按 loop_back 处理。
    """
    lo, hi = min(fl, ul), max(fl, ul)
    body = [L[k] for k in range(lo, hi + 1) if L[k].strip()]

    # ① 重赋值：`var = ...`（两行之间）
    for k in range(fl + 1, ul + 1) if ul > fl else range(ul, fl):
        s = L[k]
        if re.search(rf"\b{re.escape(var)}\b\s*=(?!=)", s):
            return "reassign"
    # ② return / exit / abort / longjmp（两行之间，不含释放行本身）
    for k in (range(fl + 1, ul) if ul > fl else range(ul, fl)):
        s = L[k]
        if "goto" in s and var in s:
            continue
        m = GUARD_RX.search(s)
        if m:
            return "unreachable_" + m.group(1)
        # ③ break：在循环里才终止
        if re.search(r"\bbreak\b", s):
            b = _innermost(blks, k)
            if b is None or b["kind"] != "switch":
                return "unreachable_break"
    # ④ if/else 互斥
    if exclusive_if_else(blks, fl, ul):
        return "if_else_exclusive"
    # ⑤ loop_back 的下一轮重赋值
    if ul < fl:
        for k in range(ul, fl):
            if re.search(rf"\b{re.escape(var)}\b\s*=(?!=)", L[k]):
                return "loop_reassign"
    return None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--osv", default="ARVO-42494732")
    a = ap.parse_args()
    root = _root(a.osv)
    funcs = load_funcs(a.osv)

    rows = load_raw(a.osv)
    ok = [r for r in rows if r["verified"]]
    print(f"  原始 {len(rows)} 处，核对通过 {len(ok)}")

    # ── 拆成两个列表 ──
    free_pts = collections.defaultdict(set)   # (file,line) -> {object}
    use_pts = collections.defaultdict(set)
    for r in ok:
        f = r["file"].lstrip("./")
        free_pts[(f, r["free_line"])].add((r.get("object") or "").strip())
        use_pts[(f, r["use_line"])].add((r.get("object") or "").strip())
    print(f"  释放点 {len(free_pts)} 个（去重后）、使用点 {len(use_pts)} 个")

    # ── 两实例在两个列表上的重合率（**分开报**）──
    def overlap(pts, field):
        seen = collections.defaultdict(set)
        for r in ok:
            f = r["file"].lstrip("./")
            k = (f, r[field])
            seen[k].add(r["run"])
        n = len(seen)
        both = sum(1 for v in seen.values() if len(v) >= 2)
        return n, both

    nf, bf = overlap(ok, "free_line")
    nu, bu = overlap(ok, "use_line")
    print(f"  释放点重合：{bf}/{nf} = {100.0 * bf / max(nf, 1):.0f}%")
    print(f"  使用点重合：{bu}/{nu} = {100.0 * bu / max(nu, 1):.0f}%")

    # ── 程序配对 ──
    pairs = []
    rejected = collections.Counter()
    for f in {k[0] for k in free_pts}:
        L = None
        p = os.path.join(root, f)
        if os.path.isfile(p):
            L = open(p, encoding="utf-8", errors="replace").read().split("\n")
        if L is None:
            continue
        for (ff, fl), fobjs in free_pts.items():
            if ff != f:
                continue
            for (uf, ul), uobjs in use_pts.items():
                if uf != f or ul == fl:
                    continue
                same = fobjs & uobjs
                alias = not same and any(
                    (x and y and (x in y or y in x)) for x in fobjs for y in uobjs)
                objs = same or (set() if not alias else {next(iter(fobjs))})
                if not (same or alias):
                    continue
                fn = func_of(funcs, f, fl)
                fn2 = func_of(funcs, f, ul)
                if not fn or not fn2 or fn["name"] != fn2["name"]:
                    rejected["cross_function"] += 1
                    continue
                lo, hi = fn["lines"][0] - 1, min(fn["lines"][1], len(L)) - 1
                blks = blocks(L, lo, hi)
                var = sorted(same)[0] if same else sorted(fobjs)[0]
                g = guard_block(L, blks, fl - 1, ul - 1, var)
                if g:
                    rejected[g] += 1
                    continue
                pairs.append(dict(file=f, free_line=fl, use_line=ul, object=var,
                                  kind=("same_object" if same else "alias"),
                                  confidence=("high" if (bf and nf and (f, fl) in
                                                         {(x["file"].lstrip("./"), x["free_line"]) for x in ok if x["run"] == 1}
                                                         and (f, fl) in
                                                         {(x["file"].lstrip("./"), x["free_line"]) for x in ok if x["run"] == 2})
                                              else "medium"),
                                  source="program_paired"))
    # 去掉完全重复
    seen = set()
    uniq = []
    for p_ in sorted(pairs, key=lambda x: (x["file"], x["free_line"], x["use_line"])):
        k = (p_["file"], p_["free_line"], p_["use_line"], p_["object"])
        if k in seen:
            continue
        seen.add(k)
        uniq.append(p_)

    print(f"\n  配对后 {len(uniq)} 处（同 object {sum(1 for x in uniq if x['kind'] == 'same_object')} / "
          f"别名 {sum(1 for x in uniq if x['kind'] == 'alias')}）")
    print(f"  过滤掉：{dict(rejected)}")

    T = ("src/in_dxf.c", 12284, 12267)
    hit = [x for x in uniq if (x["file"], x["free_line"], x["use_line"]) == T]
    print(f"\n  ⭐ 配对后 {T[0]}:{T[1]}→{T[2]}: "
          f"{'✅ 出来了（' + str(hit[0]['kind']) + ' / ' + str(hit[0]['confidence']) + '）' if hit else '❌ 还是没有'}")
    # 两个端点分别被几个实例报过
    for field, val in (("free_line", 12284), ("use_line", 12267)):
        runs = sorted({r["run"] for r in ok if r["file"].lstrip("./") == "src/in_dxf.c" and r[field] == val})
        print(f"    端点 {field}={val}: 实例 {runs or '无'}")

    json.dump(dict(osv=a.osv, n_raw=len(rows), n_ok=len(ok),
                   free_points=len(free_pts), use_points=len(use_pts),
                   free_overlap=[bf, nf], use_overlap=[bu, nu],
                   pairs=uniq, rejected=dict(rejected), target_hit=bool(hit)),
              open(os.path.join(OUT, f"paired_{a.osv}.json"), "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)
    print(f"\n  写出 {os.path.join(OUT, f'paired_{a.osv}.json')}")


if __name__ == "__main__":
    main()

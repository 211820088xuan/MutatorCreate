"""R30 步骤 1–2：42 条站点全部走证据链 + 按产物归并（多对一）。

## 为什么要归并（用户诊断）

> 「不能单纯地选择前 5，不然就会出现现在的情况，多个站点改的一个位置，这个应该属于一种策略。
>  所以中间应该加上一步，就是**从站点到变异策略，可能是多对 1 的关系**。」

R29 的教训：2 个站点的变异方案本来就是同一种（"改 DXF 记录的值行"），
LLM 只能换个 salt 糊弄 —— **因为本来就没有第二种改法**。不是 LLM 的错，是输入给错了。

## 证据链（静态，不调 LLM）

每条站点产出：
- `derivable` / `part` / `op` / `anchor` / `constraint` / `basis_refs`

## 归并键

**(part, op, anchor)** —— 三者都相同就是同一种策略。**程序做机械比对，不用 agent 判断。**
"""
import argparse
import collections
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def enclosing_guards(L, fn_lo, site_line, max_back=400):
    """从函数开头到站点之间，倒着收集 `if`/`while`/`else if` 的条件行。"""
    out = []
    lo = max(fn_lo - 1, site_line - 1 - max_back)
    for k in range(site_line - 2, lo - 1, -1):
        s = L[k].strip()
        if not s:
            continue
        if re.match(r"^(if|else if|while|switch)\b", s) or s.startswith("else if"):
            out.append((k + 1, s[:200]))
        if len(out) >= 6:
            break
    return list(reversed(out))


STR_CMP = re.compile(r'(?:strEQc|strcmp|strncmp|strEQ)\s*\([^,]+,\s*"([^"]{1,40})"')
ASSIGN_STR = re.compile(r'strcmp\s*\([^,]+,\s*"([^"]{1,40})"')
FIELD_EQ = re.compile(r"(\w+(?:->\w+)+)\s*==\s*(0x[0-9A-Fa-f]+|\d+)")
CODE_EQ = re.compile(r"(\w+)->code\s*==\s*(\d+)")
SECTION = re.compile(r'"([A-Z][A-Z_]{2,20})"')


def derive(root, p, fn_line_range):
    """从站点所在函数的守卫里抽证据链。"""
    path = os.path.join(root, p["file"].lstrip("./"))
    if not os.path.isfile(path):
        return dict(derivable=False, reason="source_missing")
    L = open(path, encoding="utf-8", errors="replace").read().split("\n")
    fn_lo = (fn_line_range or [1])[0]
    guards = enclosing_guards(L, fn_lo, p["free_line"])
    anchor, constraint, basis = None, [], []
    for ln, s in guards:
        m = STR_CMP.search(s)
        if m and not anchor:
            anchor = m.group(1)
            basis.append({"line": ln, "code": s[:160], "why": "字符串锚点"})
        m2 = SECTION.search(s)
        if m2 and not anchor and m2.group(1) not in ("NULL",):
            anchor = m2.group(1)
            basis.append({"line": ln, "code": s[:160], "why": "段名锚点"})
        for m3 in FIELD_EQ.finditer(s):
            constraint.append(f"{m3.group(1)} == {m3.group(2)}")
            basis.append({"line": ln, "code": s[:160], "why": "字段相等"})
        for m4 in CODE_EQ.finditer(s):
            constraint.append(f"组码 {m4.group(2)}")
            basis.append({"line": ln, "code": s[:160], "why": "组码判据"})
    if not anchor and not constraint:
        return dict(derivable=False, reason="no_guard_derivable", guards=guards)
    # part：DXF 走"记录段"，其余按文件/函数判
    ext = os.path.splitext(p["file"])[1]
    part = "DXF 记录段" if ext in (".dxf", ".c") and "dxf" in p["file"].lower() else f"{ext or 'unknown'} 输入"
    if anchor and anchor.isupper():
        part = f"{anchor} 段"
    # op：按 reuse_kind 分
    op = {"loop_back": "替换值行（覆盖回边上的判断）",
          "same_path": "替换值行",
          "same_func_field": "替换字段路径的值"}.get(p.get("kind") or p.get("reuse_kind") or "", "替换值行")
    return dict(derivable=True, part=part, op=op, anchor=anchor or "(无字符串锚点)",
                constraint=sorted(set(constraint)), basis_refs=basis[:6])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--osv", default="ARVO-42494732")
    ap.add_argument("--ranked", default="docs/runs/r26b/post2/ranked.json")
    a = ap.parse_args()
    P = os.path.join(ROOT, "projects", a.osv)
    wl = json.load(open(os.path.join(P, "audit_worklist.json"), encoding="utf-8"))
    root = json.load(open(os.path.join(P, "source_context.json"), encoding="utf-8"))["repo_local"]
    ranked = json.load(open(os.path.join(ROOT, a.ranked), encoding="utf-8"))
    fn_ranges = {}
    for f in wl["functions"]:
        fn_ranges.setdefault((f["file"].lstrip("./"), f["name"]), f["lines"])
    # 站点 -> 所在函数（用 free_line 落点）
    def fn_of(f, line):
        best = None
        for (ff, name), lines in fn_ranges.items():
            if ff == f and lines[0] <= line <= lines[1]:
                if best is None or (lines[0] > best[1][0]):
                    best = (name, lines)
        return best
    out = []
    for p in ranked:
        f = p["file"].lstrip("./")
        hit = fn_of(f, p["free_line"])
        p2 = dict(p, file=f)
        ev = derive(root, p2, hit[1] if hit else None) if hit else dict(derivable=False, reason="fn_not_in_worklist")
        ev["function"] = hit[0] if hit else None
        out.append(dict(p2, **ev))
    ok = [x for x in out if x["derivable"]]
    bad = [x for x in out if not x["derivable"]]
    print(f"  {len(out)} 条站点：能推 {len(ok)}，推不出 {len(bad)}")
    print(f"  推不出的原因: {dict(collections.Counter(x['reason'] for x in bad))}")
    print()
    # ── 归并（机械比对）──
    groups = collections.defaultdict(list)
    for x in ok:
        groups[(x["part"], x["op"], x["anchor"])].append(x)
    print(f"  归并成 {len(groups)} 种策略（键 = part + op + anchor）:")
    for i, (k, xs) in enumerate(sorted(groups.items(), key=lambda kv: -len(kv[1])), 1):
        known = sum(1 for x in xs if x.get("known_hit"))
        hi = sum(1 for x in xs if x.get("confidence") == "high")
        print(f"    s{i:03d} [{len(xs):>2} 站点, high {hi}, 已知崩溃 {known}]")
        print(f"          part={k[0]!r} op={k[1]!r} anchor={k[2]!r}")
        for x in xs[:3]:
            print(f"            {x['file']}:{x['free_line']}→{x['use_line']}")
    # 标尺属于哪一种
    T = ("src/in_dxf.c", 12284, 12267)
    for i, (k, xs) in enumerate(sorted(groups.items(), key=lambda kv: -len(kv[1])), 1):
        if any((x["file"], x["free_line"], x["use_line"]) == T for x in xs):
            print(f"\n  ⭐ 标尺属于 s{i:03d}，那种一共挂 {len(xs)} 个站点")
    single = [k for k, v in groups.items() if len(v) == 1]
    print(f"  只挂 1 个站点的策略: {len(single)} 种")
    json.dump(dict(sites=out, groups=[dict(strategy_id=f"s{i:03d}", part=k[0], op=k[1], anchor=k[2],
                                          site_count=len(v),
                                          is_known_crash=any(x.get("known_hit") for x in v),
                                          avg_conf_high=sum(1 for x in v if x.get("confidence") == "high"),
                                          sites=[dict(file=x["file"], free=x["free_line"], use=x["use_line"],
                                                      is_known_crash=bool(x.get("known_hit")),
                                                      confidence=x.get("confidence")) for x in v])
                                     for i, (k, v) in enumerate(sorted(groups.items(), key=lambda kv: -len(kv[1])), 1)]),
              open(os.path.join(ROOT, "docs", "runs", "r30", "merged.json"), "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)


if __name__ == "__main__":
    os.makedirs(os.path.join(ROOT, "docs", "runs", "r30"), exist_ok=True)
    main()

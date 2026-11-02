#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""s5g_interproc.py —— 跨函数证据工具（补上 llm04/llm05 缺的那一环）

问题
  `s5f_feature_pipeline.py` 是**行级**扫描器。它能判定"同函数释放后使用"（llm01/llm03），
  但建立不了"函数 A 释放、函数 B 读取"的关系——所以 llm04（跨函数陈旧对象）和
  llm05（容器销毁后遍历）只能报 `not_found`，而那是**方法局限，不是项目里没有**。

本模块提供的三个原语
  · `callers(fn)`  谁调用了它
  · `callees(fn)`  它调用了谁
  · `field_uses(field)`  结构体字段 `->field` 在**所有可达函数**里的写点 / 释放点 / 读点

  有了 field_uses，就能拼出 llm04 的形状：
      写点(存指针) ——释放点——> 读点，且释放与读不在同一函数
  以及 llm05 的形状：
      容器销毁点 ——> 遍历点，遍历点读的是 next/prev/child 链

用法
  python3 s5g_interproc.py --osv ARVO-42494732 --field obj_hdls
  python3 s5g_interproc.py --osv ARVO-42494732 --callers resolve_postponed_object_refs
  python3 s5g_interproc.py --osv ARVO-42494732 --callees resolve_postponed_object_refs
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
TOP = os.path.dirname(ROOT)
OUT = os.path.join(TOP, "mutator_custom", "stage5")


def load_dump(p):
    methods, edges = [], {}
    for ln in open(p, encoding="utf-8"):
        t = ln.rstrip("\n").split("\t")
        if t[0] == "@@M" and len(t) >= 6:
            methods.append({"file": t[1], "name": t[2], "start": int(t[3] or 0),
                            "end": int(t[4] or 0), "external": t[5] == "1"})
        elif t[0] == "@@C" and len(t) >= 4:
            edges.setdefault((t[1], t[2]), set()).update(t[3].split("|"))
    return methods, edges


class Interproc:
    def __init__(self, root, methods, edges, worklist):
        self.root = root
        self.methods = methods
        self.edges = edges
        self.by_name = {}
        for m in methods:
            if not m["external"] and m["name"] != "<global>":
                self.by_name.setdefault(m["name"], m)
        self.reachable = {f["name"] for f in worklist["functions"]}
        self._src = {}

    # ── 调用关系 ──
    def callers(self, fn):
        out = []
        for (cf, cn), cs in self.edges.items():
            if fn in cs and cn in self.by_name:
                out.append({"function": cn, "file": cf,
                            "reachable": cn in self.reachable})
        return sorted(out, key=lambda x: (not x["reachable"], x["file"]))

    def callees(self, fn):
        m = self.by_name.get(fn)
        if not m:
            return []
        return sorted(c for c in self.edges.get((m["file"], fn), set())
                      if re.match(r"^[A-Za-z_]", c) and not c.startswith("<operator>"))

    # ── 字段级 def-use ──
    def lines(self, rel):
        if rel not in self._src:
            p = os.path.join(self.root, rel)
            self._src[rel] = (open(p, encoding="utf-8", errors="replace").read().split("\n")
                              if os.path.isfile(p) else None)
        return self._src[rel]

    def field_uses(self, field, only_reachable=True):
        """在所有可达函数里找 `->field` 的写 / 释放 / 读。"""
        rx = re.compile(rf"->\s*{re.escape(field)}\b")
        free_rx = re.compile(r"\b\w*(free|destroy|release|clear)\w*\s*\(")
        write_rx = re.compile(rf"->\s*{re.escape(field)}\s*=(?!=)")
        out = {"writes": [], "frees": [], "reads": []}
        for name, m in self.by_name.items():
            if only_reachable and name not in self.reachable:
                continue
            lines = self.lines(m["file"])
            if not lines:
                continue
            lo, hi = m["start"] - 1, min(m["end"], len(lines))
            for i in range(lo, hi):
                # 同时处理 `free(x->f)` 和 `FREE_IF(x->f)` 两种形态
                if not rx.search(lines[i]):
                    continue
                rec = {"function": name, "file": m["file"], "line": i + 1,
                       "code": lines[i].strip()[:140]}
                if free_rx.search(lines[i]):
                    out["frees"].append(rec)
                elif write_rx.search(lines[i]):
                    out["writes"].append(rec)
                else:
                    out["reads"].append(rec)
        return out


def cross_function_shape(ip, field, min_gap=1):
    """llm04/llm05 的判定形状：同名字段上存在 写点/释放点/读点，且释放与读**不同函数**。"""
    u = ip.field_uses(field)
    fns_free = {r["function"] for r in u["frees"]}
    fns_read = {r["function"] for r in u["reads"]}
    fns_write = {r["function"] for r in u["writes"]}
    pairs = []
    for f in u["frees"]:
        for r in u["reads"]:
            if f["function"] != r["function"]:
                pairs.append({"free": f, "use": r,
                              "gap_functions": [f["function"], r["function"]]})
    return {
        "field": field,
        "counts": {k: len(v) for k, v in u.items()},
        "free_functions": sorted(fns_free),
        "read_functions": sorted(fns_read),
        "write_functions": sorted(fns_write),
        "cross_function_pairs": pairs[:12],
        "verdict": ("cross_function_free_then_use_candidate" if pairs
                    else "no_cross_function_shape"),
    }


def main():
    ap = argparse.ArgumentParser(description="跨函数证据工具")
    ap.add_argument("--osv", required=True)
    ap.add_argument("--field", help="结构体字段名（不带 ->）")
    ap.add_argument("--callers")
    ap.add_argument("--callees")
    ap.add_argument("--json-out", default=None)
    args = ap.parse_args()

    S5 = os.path.join(OUT, args.osv)
    root = json.load(open(os.path.join(S5, "source_context.json"),
                         encoding="utf-8"))["repo_local"]
    worklist = json.load(open(os.path.join(S5, "audit_worklist.json"), encoding="utf-8"))
    methods, edges = load_dump(os.path.join(S5, "cpg_dump.tsv"))
    ip = Interproc(root, methods, edges, worklist)

    res = {}
    if args.callers:
        res["callers"] = ip.callers(args.callers)
        print(f"=== callers({args.callers}) ===")
        for c in res["callers"]:
            print(f"  {'●' if c['reachable'] else '·'} {c['function']:<34} {c['file']}")
    if args.callees:
        res["callees"] = ip.callees(args.callees)
        print(f"=== callees({args.callees}) ===")
        for c in res["callees"]:
            m = ip.by_name.get(c)
            print(f"  {c:<34} " + (f"{m['file']}:{m['start']}" if m else "(外部)"))
    if args.field:
        res["field"] = cross_function_shape(ip, args.field)
        f = res["field"]
        print(f"=== field_uses(->{args.field}) ===")
        print(f"  写点 {f['counts']['writes']}  释放点 {f['counts']['frees']}  "
              f"读点 {f['counts']['reads']}")
        print(f"  释放所在函数: {f['free_functions'][:5]}")
        print(f"  读取所在函数: {f['read_functions'][:5]}")
        print(f"  判定: {f['verdict']}")
        for p in f["cross_function_pairs"][:4]:
            print(f"    释放 {p['free']['function']}:{p['free']['line']} "
                  f"→ 读取 {p['use']['function']}:{p['use']['line']}")

    if args.json_out:
        json.dump(res, open(args.json_out, "w", encoding="utf-8"),
                  ensure_ascii=False, indent=1)
        print(f"\n写出 {args.json_out}")


if __name__ == "__main__":
    main()

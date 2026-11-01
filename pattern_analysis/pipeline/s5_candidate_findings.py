#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""s5_candidate_findings.py —— 阶段5.2：把多路候选合并成统一的 findings（**0 LLM**）

职责
  把「agent 审计候选」「机械规则假设」「facts / interpretation」合成一份带来源、带证据状态、
  带去重、带可达性关系的清单。它**不判断漏洞真假**，只负责：
    · 统一漏洞族（family）
    · 重新核对证据行（行号存在 + 原文是该行子串）
    · 去重（同族 + 同文件 + 同函数 + **证据行有交集**）
    · 计算 call_surface_relation（direct / reachable / outside / unknown）
    · 计算 fault_relation（same_site / same_function / same_file / same_family_only / unrelated）
    · 计算 input_reachability（complete / partial / unknown）

为什么去重键不是「证据行集合相等」
  agent 给的证据行通常是 [12284, 12286, 12267, 12269]，机械假设是 [12284, 12267]。
  集合不相等，但显然说的是同一件事。所以用「有交集」而不是「相等」。

用法
  python3 s5_candidate_findings.py --osv ARVO-42494732
  python3 s5_candidate_findings.py --osv ARVO-42494732 --selftest
"""
from __future__ import annotations

import argparse
import glob
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
TOP = os.path.dirname(ROOT)
OUT = os.path.join(TOP, "mutator_custom", "stage5")

# 漏洞族 ontology（保留原始类型，只做归一化）
FAMILY = {
    "use-after-free": "lifetime", "double-free": "lifetime", "invalid-free": "lifetime",
    "heap-buffer-overflow": "bounds", "stack-buffer-overflow": "bounds",
    "global-buffer-overflow": "bounds", "out-of-bounds-read": "bounds",
    "out-of-bounds-write": "bounds", "container-overflow": "bounds",
    "use-of-uninitialized-value": "initialization",
    "integer-overflow": "arithmetic-to-memory",
    "null-deref": "control/resource",
}

CRASH_FAMILY = {
    "heap-use-after-free": "lifetime", "heap-double-free": "lifetime",
    "invalid-free": "lifetime", "heap-buffer-overflow": "bounds",
    "stack-buffer-overflow": "bounds", "global-buffer-overflow": "bounds",
    "use-of-uninitialized-value": "initialization",
    "negative-size-param": "arithmetic-to-memory",
    "segv-on-unknown-address": "control/resource",
    "null-dereference": "control/resource",
}


def family_of(vuln_type: str) -> str:
    t = (vuln_type or "").lower()
    if t in FAMILY:
        return FAMILY[t]
    for k, v in FAMILY.items():
        if k in t:
            return v
    return "unknown"



def resolve_file(source_root: str, files, function: str, cache: dict) -> str:
    """候选没带文件时，按函数名在可达文件里反查（只匹配 "name(" 出现）。"""
    if not function:
        return ""
    key = (function, tuple(files or ()))
    if key in cache:
        return cache[key]
    rx = re.compile(rf"\b{re.escape(function)}\s*\(")
    for rel in files or ():
        p = os.path.join(source_root, rel)
        if not os.path.isfile(p):
            continue
        try:
            if rx.search(open(p, encoding="utf-8", errors="replace").read()):
                cache[key] = rel
                return rel
        except OSError:
            pass
    cache[key] = ""
    return ""

def as_candidate_list(report) -> list[dict]:
    """兼容三种输入：{"candidates":[...]} / [ {...}, {...} ] / None。"""
    if not report:
        return []
    if isinstance(report, list):
        out = []
        for r in report:
            out.extend(r.get("candidates") or [] if isinstance(r, dict) else [])
        return out
    return report.get("candidates") or []



def _norm_ev(ev) -> list:
    """把证据行统一成 [int, str]（LLM 会返回字符串行号）。"""
    out = []
    for e in ev or []:
        if not (isinstance(e, (list, tuple)) and len(e) >= 2):
            continue
        try:
            out.append([int(e[0]), str(e[1])])
        except (TypeError, ValueError):
            continue
    return out

def verify_evidence(root: str, rel: str, evidence) -> tuple[bool, list[int], list[str]]:
    """核对证据行：行号合法且原文（去空白）是该行子串。"""
    full = os.path.join(root, rel) if rel else None
    if not full or not os.path.isfile(full):
        return False, [], ["file_missing"]
    lines = open(full, encoding="utf-8", errors="replace").read().split("\n")
    ok, bad = [], []
    for ev in evidence or []:
        if not (isinstance(ev, (list, tuple)) and len(ev) >= 2):
            bad.append(str(ev)[:80]); continue
        try:
            ln = int(ev[0])
        except (TypeError, ValueError):
            bad.append(str(ev)[:80]); continue
        if not (1 <= ln <= len(lines)):
            bad.append(f"L{ln} 越界"); continue
        claim = "".join(str(ev[1]).split())
        if claim and claim in "".join(lines[ln - 1].split()):
            ok.append(ln)
        else:
            bad.append(f"L{ln} 原文不符")
    return (bool(ok) and not bad), ok, bad


def all_lines(f: dict) -> set[int]:
    s = set()
    for x in f.get("lines") or []:
        try:
            s.add(int(x))
        except (TypeError, ValueError):
            pass
    for ev in f.get("evidence_lines") or []:
        try:
            s.add(int(ev[0]))
        except (TypeError, ValueError, IndexError):
            pass
    return s


def normalize_findings(audit_report, mech_report, facts, interpretation,
                       target_surface, source_root) -> dict:
    """把多路候选规范化、核验、去重、加关系。"""
    aud = as_candidate_list(audit_report)
    mech = (mech_report or {}).get("hypotheses") or []

    surface = target_surface or {}
    cs = surface.get("call_surface") or {}
    reachable = set(cs.get("reachable_functions") or [])
    direct = set(cs.get("direct_calls") or [])
    fm_complete = bool((surface.get("validation") or {}).get("field_mapping_complete"))

    tgt = surface.get("target") or {}
    cs_site = ((facts or {}).get("crash") or {}).get("site") or {}
    fault_fn = ((facts or {}).get("fault_fn") or cs_site.get("fn")
                or tgt.get("fault_function"))
    fault_line = ((facts or {}).get("fault_line") or cs_site.get("line")
                  or tgt.get("fault_line"))
    fault_file = ((facts or {}).get("fault_file") or cs_site.get("file")
                  or tgt.get("fault_file"))
    if isinstance(fault_file, str):
        fault_file = fault_file.split("/")[-1]
    crash_type = ((facts or {}).get("crash_type") or tgt.get("crash_type"))
    cfam = CRASH_FAMILY.get((crash_type or "").lower()) or family_of(crash_type)

    files = cs.get("reachable_files") or []
    fcache: dict = {}
    raws = []
    for c in aud:
        raws.append({"src": "audit", "raw": c,
                     "file": (c.get("_file") or c.get("file")
                              or resolve_file(source_root, files, c.get("function") or "", fcache)),
                     "function": c.get("function") or "",
                     "vuln_type": c.get("vuln_type") or "other",
                     "mechanism": c.get("mechanism") or "",
                     "evidence": c.get("evidence_lines") or [],
                     "confidence": c.get("confidence") or "low",
                     "why": c.get("why_unverified") or ""})
    for h in mech:
        raws.append({"src": "mech", "raw": h,
                     "file": h.get("file") or "",
                     "function": h.get("function") or "",
                     "vuln_type": h.get("vuln_type") or "use-after-free",
                     "mechanism": h.get("mechanism") or "",
                     "evidence": h.get("evidence_lines") or [],
                     "confidence": "low",
                     "why": "机械规则只证明代码形状，未证明输入可达"})

    out = []
    for r in raws:
        fam = family_of(r["vuln_type"])
        ok, ok_lines, bad = verify_evidence(source_root, r["file"], r["evidence"])
        f = {
            "vuln_family": fam,
            "original_types": [r["vuln_type"]],
            "mechanism": r["mechanism"],
            "file": r["file"],
            "function": r["function"],
            "lines": sorted({int(x) for x in (r["raw"].get("lines") or [])
                             if str(x).lstrip("-").isdigit()}),
            "evidence_lines": _norm_ev(r["evidence"]),
            "evidence_ok": ok,
            "evidence_ok_lines": ok_lines,
            "evidence_bad": bad,
            "sources": [r["src"]],
            "raw": r["raw"],
            "confidence": r["confidence"],
            "why_unverified": r["why"],
        }
        f["call_surface_relation"] = (
            "direct" if r["function"] in direct else
            "reachable" if r["function"] in reachable else
            "outside" if reachable else "unknown")

        lines = all_lines(f)
        if fault_line and fault_fn and r["function"] == fault_fn and int(fault_line) in lines:
            f["fault_relation"] = "same_site"
        elif fault_fn and r["function"] == fault_fn:
            f["fault_relation"] = "same_function"
        elif fault_file and r["file"].endswith(fault_file):
            f["fault_relation"] = "same_file"
        elif fam == cfam:
            f["fault_relation"] = "same_family_only"
        else:
            f["fault_relation"] = "unrelated"

        # 输入可达性：只有"同一个故障函数"且整体映射闭合时才算 complete
        if not ok:
            f["input_reachability"] = {"status": "unknown", "missing": ["证据行未通过核对"]}
        elif fm_complete and f["fault_relation"] in ("same_site", "same_function"):
            f["input_reachability"] = {
                "status": "complete", "field_ids": [x.get("field_id") for x
                                                    in (surface.get("fields") or [])[:3]],
                "path_evidence": [s.get("evidence") for s in
                                  (surface.get("evidence_chain") or [])
                                  if s.get("status") == "complete"][:3], "missing": []}
        else:
            f["input_reachability"] = {
                "status": "partial", "missing": ["候选函数到输入的完整路径未建立"]}

        f["status"] = ("rejected" if not ok else
                       "unverified")
        out.append(f)

    # ── 去重：同族 + 同文件 + 同函数 + 证据行有交集 ──
    merged: list[dict] = []
    for f in out:
        hit = None
        for m in merged:
            same_file = (m["file"] == f["file"]) or not m["file"] or not f["file"]
            if (m["vuln_family"] == f["vuln_family"] and same_file
                    and m["function"] == f["function"]
                    and (all_lines(m) & all_lines(f))):
                hit = m
                break
        if hit:
            hit["sources"] = sorted(set(hit["sources"]) | set(f["sources"]))
            hit["original_types"] = sorted(set(hit["original_types"]) | set(f["original_types"]))
            hit["evidence_lines"] = sorted(hit["evidence_lines"] + f["evidence_lines"],
                                           key=lambda e: e[0])
            if not hit["file"]:
                hit["file"] = f["file"]
            # 合并时取"更精确"的故障关系，并取行号并集
            order = {"same_site": 0, "same_function": 1, "same_file": 2,
                     "same_family_only": 3, "unrelated": 4}
            if order[f["fault_relation"]] < order[hit["fault_relation"]]:
                hit["fault_relation"] = f["fault_relation"]
            hit["lines"] = sorted(set(hit.get("lines") or []) | set(f.get("lines") or []))
            hit["evidence_ok_lines"] = sorted(set(hit.get("evidence_ok_lines") or [])
                                              | set(f.get("evidence_ok_lines") or []))
            hit["evidence_ok"] = hit["evidence_ok"] or f["evidence_ok"]
            hit["confidence"] = ("high" if "high" in (hit["confidence"], f["confidence"])
                                 else hit["confidence"])
            if f["evidence_ok"] and not hit["evidence_ok_lines"]:
                hit["evidence_ok_lines"] = f["evidence_ok_lines"]
        else:
            merged.append(f)

    merged.sort(key=lambda x: (x["status"] == "rejected",
                               x["input_reachability"]["status"] != "complete",
                               {"same_site": 0, "same_function": 1, "same_file": 2,
                                "same_family_only": 3, "unrelated": 4}[x["fault_relation"]]))
    for i, f in enumerate(merged, 1):
        f["finding_id"] = f"c{i:03d}"
        f.pop("raw", None)

    return {
        "schema_version": "stage5.candidate_findings.v1",
        "target": {"osv_id": tgt.get("osv_id"), "commit": tgt.get("commit"),
                   "crash_type": crash_type, "fault_function": fault_fn,
                   "fault_line": fault_line, "fault_file": fault_file},
        "findings": merged,
        "rejected": [f for f in merged if f["status"] == "rejected"],
        "unknowns": [{"finding_id": f["finding_id"], "missing": f["input_reachability"]["missing"]}
                     for f in merged if f["input_reachability"]["status"] != "complete"],
        "summary": {
            "from_audit": len(aud), "from_mech": len(mech),
            "after_dedup": len(merged),
            "merged": len(out) - len(merged),
            "evidence_ok": sum(1 for f in merged if f["evidence_ok"]),
            "input_complete": sum(1 for f in merged
                                  if f["input_reachability"]["status"] == "complete"),
            "by_family": _count(f["vuln_family"] for f in merged),
            "by_fault_relation": _count(f["fault_relation"] for f in merged),
            "by_call_surface": _count(f["call_surface_relation"] for f in merged),
        },
    }


def _count(it):
    from collections import Counter
    return dict(Counter(it))


def main():
    ap = argparse.ArgumentParser(description="阶段5.2：合并候选 findings（0 LLM）")
    ap.add_argument("--osv", required=True)
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    S5 = os.path.join(OUT, args.osv)
    V2 = os.path.join(S5, "v2")
    need = ["target_surface.json"]
    for n in need:
        if not os.path.exists(os.path.join(V2, n)):
            raise SystemExit(f"缺少 {V2}/{n}（先跑 s5_target_surface.py）")
    surface = json.load(open(os.path.join(V2, "target_surface.json"), encoding="utf-8"))
    root = json.load(open(os.path.join(S5, "source_context.json"), encoding="utf-8"))["repo_local"]

    # 审计候选：优先 audit_chunks/*.json，退回 vuln_report.json
    chunk_files = sorted(glob.glob(os.path.join(S5, "audit_chunks", "*.json")))
    if chunk_files:
        audit = [json.load(open(p, encoding="utf-8")) for p in chunk_files]
        audit_src = f"audit_chunks/*.json（{len(chunk_files)} 批）"
    else:
        audit = json.load(open(os.path.join(S5, "vuln_report.json"), encoding="utf-8"))
        audit_src = "vuln_report.json"

    mechp = os.path.join(S5, "mech_hypotheses.json")
    mech = json.load(open(mechp, encoding="utf-8")) if os.path.exists(mechp) else {"hypotheses": []}

    facts = _load_or_none(os.path.join(ROOT, "artifacts", "facts", args.osv, "facts.json"))
    interp = _load_or_none(os.path.join(ROOT, "artifacts", "interpretation", args.osv,
                                        "interpretation.json"))

    rep = normalize_findings(audit, mech, facts, interp, surface, root)
    rep["_meta"] = {"osv_id": args.osv, "audit_source": audit_src,
                    "mech_source": "mech_hypotheses.json" if mech.get("hypotheses") else None,
                    "facts_used": bool(facts), "interpretation_used": bool(interp),
                    "method": "多路候选合并（0 LLM）；证据行已按固定源码核对"}

    print(f"=== {args.osv} candidate findings ===")
    print(f"  审计候选 {rep['summary']['from_audit']} 条（{audit_src}）")
    print(f"  机械假设 {rep['summary']['from_mech']} 条")
    print(f"  去重后   {rep['summary']['after_dedup']} 条（合并 {rep['summary']['merged']} 条）")
    print(f"  证据通过 {rep['summary']['evidence_ok']} / 输入可达 complete {rep['summary']['input_complete']}")
    print(f"  按族    : {rep['summary']['by_family']}")
    print(f"  与故障关系: {rep['summary']['by_fault_relation']}")
    print(f"  调用面关系: {rep['summary']['by_call_surface']}")
    print()
    for f in rep["findings"][:12]:
        print(f"  [{f['finding_id']}] {f['vuln_family']:<18} {f['function'][:26]:<26}"
              f" {f['fault_relation']:<16} ev={f['evidence_ok']} "
              f"in={f['input_reachability']['status']:<8} src={','.join(f['sources'])}")

    if args.selftest or args.dry_run:
        return
    os.makedirs(V2, exist_ok=True)
    p = os.path.join(V2, "candidate_findings.json")
    json.dump(rep, open(p, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(f"\n  写出 {p}")


def _load_or_none(p):
    return json.load(open(p, encoding="utf-8")) if os.path.exists(p) else None


if __name__ == "__main__":
    main()

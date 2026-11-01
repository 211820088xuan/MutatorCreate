#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""s5_feature_binding.py —— 阶段5.3：把 stage4 特征绑到项目候选上

职责
  回答一个问题：**某个通用特征，是否适合这个项目里的某条候选缺陷？**
  硬门禁全部由程序判定；LLM 只能填 `satisfied_preconditions` / `missing_preconditions`
  和 `rationale`，不能改 hard_checks、不能改 status。

六条硬门禁
  1. same_vulnerability_family   特征族 == 候选族（UAF 特征不能接受 bounds 候选）
  2. free_or_reclaim_evidence    候选里有释放/回收证据（free/destroy/release/realloc/clear）
  3. post_free_use_evidence      有"释放后仍使用"的证据（回边回到解引用同一变量）
  4. input_reachability_complete 候选的输入可达性为 complete
  5. fault_relation_available    与已知故障有交集（same_site / same_function / same_file）
  6. no_contrary_evidence        没有相反证据：
                                 · 释放后、回边之前对同一变量重新赋值
                                 · 释放后提前 return
                                 ⚠ `dxf_free_pair` 里的 `pair = NULL` **不算**相反证据——
                                   它只置空形参，调用方的指针仍然悬垂。

选择规则（只在 accepted 里选）
  hard checks 全过 → 按 score 排序（同分取 locator 更明确、证据更短的）。

用法
  python3 s5_feature_binding.py --osv ARVO-42494732
  python3 s5_feature_binding.py --osv ARVO-42494732 --type uaf
  python3 s5_feature_binding.py --osv ARVO-42494732 --with-llm   # 额外要一段解释
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

sys.path.insert(0, HERE)
import cfg_lib  # noqa: E402

FREE_RX = re.compile(r"\b(\w*(?:free|destroy|release|realloc|clear)\w*)\s*\(\s*&?\s*([A-Za-z_]\w*)\s*\)\s*;")
DEREF_RX = r"\b{}\b\s*(->|\.|\[)"
ASSIGN_RX = r"(^|[;{(])\s*&?\s*\b%s\b\s*=(?!=)"

FEATURE_FAMILY = {  # stage4 的 uaf 目录 → lifetime
    "uaf": "lifetime", "hbo": "bounds", "stack": "bounds", "global": "bounds",
}


def load(p):
    return json.load(open(p, encoding="utf-8"))


def func_range(worklist: dict, function: str):
    for f in worklist.get("functions") or []:
        if f["name"] == function:
            return f["file"], f["lines"]
    return None, None


def contrary_evidence(source_root: str, finding: dict, worklist: dict,
                      only_free_line: int | None = None) -> dict:
    """检查"释放后重新赋值 / 提前 return"这类相反证据。

    ⚠ 只看**候选自己的函数体**。包装函数里的 `p = NULL` 只影响形参，不算相反证据。
    """
    rel, rng = func_range(worklist, finding.get("function") or "")
    if not rel or not rng:
        return {"checked": False, "contrary": [], "note": "函数范围未知"}
    p = os.path.join(source_root, rel)
    if not os.path.isfile(p):
        return {"checked": False, "contrary": [], "note": "源文件缺失"}
    lines = open(p, encoding="utf-8", errors="replace").read().split("\n")
    lo, hi = max(0, rng[0] - 1), min(len(lines), rng[1])

    out = []
    for i in range(lo, hi):
        m = FREE_RX.search(cfg_lib.strip_code(lines[i]))
        if not m:
            continue
        if only_free_line and (i + 1) != int(only_free_line):
            continue      # 只审"真正导致释放后使用"的那个释放点
        var = m.group(2)
        loops = [b for b in cfg_lib.blocks(lines, lo, hi - 1)
                 if b["kind"] == "loop" and b["open"] <= i <= b["close"]]
        loop = max(loops, key=lambda b: b["open"]) if loops else None
        end = loop["close"] if loop else min(hi - 1, i + 200)
        for j in range(i + 1, end + 1):
            s = cfg_lib.strip_code(lines[j])
            if re.search(ASSIGN_RX % re.escape(var), s):
                out.append({"kind": "reassign_after_free", "var": var,
                            "free_line": i + 1, "assign_line": j + 1,
                            "code": lines[j].strip()[:140]})
                break
            if re.search(r"\breturn\b", s):
                out.append({"kind": "return_after_free", "var": var,
                            "free_line": i + 1, "return_line": j + 1,
                            "code": lines[j].strip()[:140]})
                break
    return {"checked": True, "contrary": out,
            "note": "只看候选自己的函数体；包装函数里的置空不算相反证据"}


def post_free_use_evidence(source_root: str, finding: dict, worklist: dict) -> dict:
    """证明"释放后仍解引用同一变量"（含循环回边）。"""
    rel, rng = func_range(worklist, finding.get("function") or "")
    if not rel or not rng:
        return {"found": False, "note": "函数范围未知"}
    p = os.path.join(source_root, rel)
    if not os.path.isfile(p):
        return {"found": False, "note": "源文件缺失"}
    lines = open(p, encoding="utf-8", errors="replace").read().split("\n")
    lo, hi = max(0, rng[0] - 1), min(len(lines), rng[1] - 1)
    for i in range(lo, hi + 1):
        m = FREE_RX.search(cfg_lib.strip_code(lines[i]))
        if not m:
            continue
        var = m.group(2)
        trace = cfg_lib.flow(lines, lo, hi, i, 20)
        bi = next((k for k, t in enumerate(trace) if t["back_edge"]), None)
        if bi is None:
            continue
        dr = re.compile(DEREF_RX.format(re.escape(var)))
        for t in trace[bi:]:
            if dr.search(cfg_lib.strip_code(lines[t["line"]])):
                return {"found": True, "free_line": i + 1, "var": var,
                        "back_edge_to": (trace[bi]["next"] + 1
                                         if trace[bi]["next"] is not None else None),
                        "use_line": t["line"] + 1,
                        "note": f"flow 证明 L{i+1} 释放 {var} 后经回边⟲回到 "
                                f"L{(trace[bi]['next'] or 0)+1}，再在 L{t['line']+1} 解引用"}
    return {"found": False, "note": "flow 未发现「释放→回边→解引用同一变量」"}


def preferred_patterns(osv: str, type_dir: str) -> set[str]:
    """这个崩溃被 stage3 聚到了哪些 pattern（用于并列时的区分依据）。"""
    p = os.path.join(ROOT, "outputs", "stage3", type_dir, "final.json")
    if not os.path.exists(p):
        return set()
    d = json.load(open(p, encoding="utf-8"))
    out = set()
    for pat in d.get("final_patterns") or []:
        if osv in (pat.get("sample_ids") or []):
            out.add(pat.get("name"))
    return out


def bind_features(features, findings, surface, worklist, source_root, type_dir="uaf",
                  prefer: set[str] | None = None):
    fam = FEATURE_FAMILY.get(type_dir, "lifetime")
    prefer = prefer or set()
    bindings = []
    for feat in features.get("features") or []:
        fid = feat.get("id")
        on_pattern = (feat.get("source_pattern") in prefer)
        for f in findings.get("findings") or []:
            if f.get("status") == "rejected":
                continue
            cfam = f.get("vuln_family")
            free_ev = bool(re.search(r"(free|destroy|release|realloc|clear)",
                                     json.dumps(f.get("evidence_lines") or [], ensure_ascii=False),
                                     re.I)) or "mech" in (f.get("sources") or [])
            pfu = post_free_use_evidence(source_root, f, worklist)
            ce = contrary_evidence(source_root, f, worklist,
                                   pfu.get("free_line") if pfu.get("found") else None)
            checks = {
                "same_vulnerability_family": cfam == fam,
                "free_or_reclaim_evidence": free_ev,
                "post_free_use_evidence": pfu["found"],
                "input_reachability_complete":
                    (f.get("input_reachability") or {}).get("status") == "complete",
                "fault_relation_available":
                    f.get("fault_relation") in ("same_site", "same_function", "same_file"),
                "no_contrary_evidence": ce["checked"] and not ce["contrary"],
            }
            ok = all(checks.values())
            missing = []
            if not checks["same_vulnerability_family"]:
                missing.append(f"机制族不一致（特征 {fam} vs 候选 {cfam}）")
            if not checks["free_or_reclaim_evidence"]:
                missing.append("缺少释放/回收证据")
            if not checks["post_free_use_evidence"]:
                missing.append("缺少释放后使用证据")
            if not checks["input_reachability_complete"]:
                missing.append("输入可达性不是 complete")
            if not checks["fault_relation_available"]:
                missing.append(f"与已知故障无交集（{f.get('fault_relation')}）")
            if not checks["no_contrary_evidence"]:
                missing.append("存在相反证据或无法确认")
            ev_n = len(f.get("evidence_ok_lines") or [])
            dist = {"same_site": 1.0, "same_function": 0.7,
                    "same_file": 0.4}.get(f.get("fault_relation"), 0.0)
            score = round(0.4 * min(1.0, ev_n / 4.0)
                          + 0.4 * (1.0 if checks["input_reachability_complete"] else 0.0)
                          + 0.2 * dist, 4)
            bindings.append({
                "binding_id": None,
                "feature_id": fid,
                "feature_name": feat.get("feature_name"),
                "finding_ids": [f.get("finding_id")],
                "hard_checks": checks,
                "satisfied_preconditions": [],
                "missing_preconditions": missing,
                "evidence_refs": [f"{f.get('finding_id')}:evidence_lines",
                                  f"{f.get('finding_id')}:{pfu.get('free_line')}-{pfu.get('use_line')}"]
                                 if pfu.get("found") else [f"{f.get('finding_id')}:evidence_lines"],
                "llm_rationale": None,
                "score": score,
                "on_crash_pattern": on_pattern,
                "status": "accepted" if ok else "blocked",
                "_detail": {"post_free_use": pfu, "contrary": ce,
                            "evidence_ok_lines": f.get("evidence_ok_lines")},
            })
    bindings.sort(key=lambda b: (b["status"] != "accepted", not b["on_crash_pattern"],
                                 -b["score"], len(b["missing_preconditions"])))
    for i, b in enumerate(bindings, 1):
        b["binding_id"] = f"b{i:03d}"
    accepted = [b for b in bindings if b["status"] == "accepted"]
    sel = accepted[0] if accepted else None
    reason = ("硬门禁全过；并列时优先选『来自该崩溃所属 pattern』的特征"
              if sel and sel["on_crash_pattern"] else
              "硬门禁全过；按 score 选最高" if sel else
              "没有 accepted binding：字段/证据/可达性未闭合")
    return {"schema_version": "stage5.feature_bindings.v1",
            "target": findings.get("target"),
            "bindings": bindings,
            "selected_binding_id": accepted[0]["binding_id"] if accepted else None,
            "selection_reason": reason,
            "preferred_patterns": sorted(prefer),
            "summary": {"features": len(features.get("features") or []),
                        "findings": len(findings.get("findings") or []),
                        "bindings": len(bindings),
                        "accepted": len(accepted),
                        "blocked": len(bindings) - len(accepted)}}


def main():
    ap = argparse.ArgumentParser(description="阶段5.3：feature binding")
    ap.add_argument("--osv", required=True)
    ap.add_argument("--type", default="uaf")
    ap.add_argument("--with-llm", action="store_true",
                    help="额外让 LLM 填 satisfied/missing/rationale（不改 hard checks）")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    S5 = os.path.join(OUT, args.osv)
    V2 = os.path.join(S5, "v2")
    featp = os.path.join(ROOT, "outputs", "stage4", args.type, "features.json")
    for p in (featp, os.path.join(V2, "candidate_findings.json"),
              os.path.join(V2, "target_surface.json"),
              os.path.join(S5, "audit_worklist.json")):
        if not os.path.exists(p):
            raise SystemExit(f"缺少 {p}")

    features = load(featp)
    findings = load(os.path.join(V2, "candidate_findings.json"))
    surface = load(os.path.join(V2, "target_surface.json"))
    worklist = load(os.path.join(S5, "audit_worklist.json"))
    root = load(os.path.join(S5, "source_context.json"))["repo_local"]

    prefer = preferred_patterns(args.osv, args.type)
    if prefer:
        print(f"  该崩溃所属 pattern: {sorted(prefer)}")
    rep = bind_features(features, findings, surface, worklist, root, args.type, prefer)

    print(f"=== {args.osv} feature binding（type={args.type}）===")
    print(f"  特征 {rep['summary']['features']} × 候选 {rep['summary']['findings']}"
          f" → 绑定 {rep['summary']['bindings']} 条"
          f"（accepted {rep['summary']['accepted']} / blocked {rep['summary']['blocked']}）")
    print()
    for b in rep["bindings"][:14]:
        flags = "".join("✓" if v else "✗" for v in b["hard_checks"].values())
        print(f"  [{b['binding_id']}] {b['feature_id']:<11} {b['finding_ids']} "
              f"{b['status']:<8} score={b['score']:<6} {flags}")
        if b["missing_preconditions"]:
            print(f"       缺: {'; '.join(b['missing_preconditions'])[:120]}")
    print()
    print(f"  selected = {rep['selected_binding_id']}  （{rep['selection_reason']}）")

    if args.dry_run:
        return
    os.makedirs(V2, exist_ok=True)
    p = os.path.join(V2, "feature_bindings.json")
    json.dump(rep, open(p, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(f"\n  写出 {p}")


if __name__ == "__main__":
    main()

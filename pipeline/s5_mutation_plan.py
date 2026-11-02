#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""s5_mutation_plan.py —— 阶段5.4：生成声明式 mutation plan（**0 LLM**）

职责
  把「选中的特征 + 候选缺陷 + target surface」冻结成一份**可检查的**变异计划，
  成为 C 代码生成器的唯一业务输入。C 代码只负责实现它，不再自己决定改哪。

`status=ready` 的必要条件（缺一即 blocked）
  1. 有 selected binding
  2. 输入格式已知
  3. 字段有 locator（record 级即可，不要求字节偏移）
  4. 字段到目标条件有源码证据
  5. 每个 mutation action 都有 basis_refs
  6. 保持的不变量有实现策略

本版能确定性推出的东西（以 libredwg/DXF 为例）
  · 字段约束：从 `while (pair->code == 0 && pair->value.s)` 取「组码 0 + 字符串值」
  · 段锚点  ：故障函数的调用点被 `else if (strEQc (pair->value.s, "OBJECTS"))` 守着
  · 判据    ：`if (is_dwg_object (name))`（来自 target_surface step5）
  · 期望效果：判据为假 → else 分支释放且不置空 → 循环回边 → 解引用（step6 已证明）

用法
  python3 s5_mutation_plan.py --osv ARVO-42494732
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
OUT = os.path.join(ROOT, "projects")

SOLVE = {"add_argument"}

# line_record(DXF) 适配器：把特征的 semantic target 映射成"改哪一类记录字段"
# 注意：group code 的语义是 DXF 领域知识；换格式要写新适配器。
STRATEGY = {
    "同函数释放后访问": dict(
        part="value_line", op="replace_value_line",
        field="record.value_after_group_code.0", anchor="0",
        note="把 code-0 记录的值改成 is_dwg_object 不认识的类型名"),
    "缓冲释放后旧指针": dict(
        part="numeric_field", op="set_numeric_field",
        field="record.numeric_value", anchor="90|70|71|40|42",
        note="把长度/计数/偏移类组码的值推向大数或边界值"),
    "清理析构后悬垂访问": dict(
        part="section_or_key", op="replace_section_or_key",
        field="record.string_value", anchor="2|3",
        note="改段名/键名或别名表项，走清理或错误回退分支"),
    "跨函数陈旧对象访问": dict(
        part="handle_ref", op="rewrite_handle_ref",
        field="record.handle_reference", anchor="330|340|350|360",
        note="把对象引用类句柄改成陈旧/重复句柄，触发替换后仍读旧对象"),
    "容器节点销毁后遍历": dict(
        part="object_handle", op="duplicate_object_handle",
        field="record.handle", anchor="5",
        note="复制已有句柄，让容器替换/销毁后遍历仍命中旧节点"),
}


def strategy_for(feature: dict) -> dict:
    sp = feature.get("source_pattern")
    st = dict(STRATEGY.get(sp) or {})
    st["source_pattern"] = sp
    return st


def load(p):
    return json.load(open(p, encoding="utf-8"))


def find_call_site(root: str, rel: str, fn: str) -> dict | None:
    """在故障函数所在文件里找它的**调用点**，并取其前面的 strEQc 段名守卫。"""
    p = os.path.join(root, rel)
    if not os.path.isfile(p):
        return None
    lines = open(p, encoding="utf-8", errors="replace").read().split("\n")
    call_rx = re.compile(rf"\b{re.escape(fn)}\s*\(")
    cands = []
    for i, ln in enumerate(lines):
        if not call_rx.search(ln):
            continue
        # 只认"语句调用"：本行以 ; 结尾（函数定义行不会）
        if not ln.rstrip().endswith(";"):
            continue
        section = None
        for j in range(max(0, i - 8), i):
            m = re.search(r'strEQc\s*\(\s*\w+->\w+\.\w+\s*,\s*"([^"]+)"\s*\)', lines[j])
            if m:
                section = m.group(1)
        cands.append({"line": i + 1, "code": ln.strip()[:160], "section_anchor": section})
    if not cands:
        return None
    # 优先带段名守卫的调用点
    return next((c for c in cands if c["section_anchor"]), cands[0])


def field_constraint(root: str, rel: str, lines_of_interest) -> dict | None:
    """从循环条件/判据里取字段约束：组码值 + 值类型。"""
    p = os.path.join(root, rel)
    if not os.path.isfile(p):
        return None
    lines = open(p, encoding="utf-8", errors="replace").read().split("\n")
    for ln in lines_of_interest or []:
        try:
            s = lines[int(ln) - 1]
        except (IndexError, ValueError, TypeError):
            continue
        m = re.search(r"(\w+)->code\s*==\s*(\d+)", s)
        if m:
            return {"var": m.group(1), "group_code": int(m.group(2)),
                    "value_is_string": bool(re.search(rf"{m.group(1)}->value\.s", s)),
                    "evidence_line": int(ln), "evidence_code": s.strip()[:160]}
    return None



def _seed_path(source_root, tgt):
    osv = (tgt or {}).get("osv_id")
    d = os.path.join(OUT, osv, "seeds")
    if not os.path.isdir(d):
        return None
    named = [f for f in sorted(os.listdir(d))
             if f.endswith(".dxf") and not f.startswith(".")]
    return os.path.join(d, named[0]) if named else None


def _line_endings(source_root, tgt):
    p = _seed_path(source_root, tgt)
    if not p or not os.path.isfile(p):
        return None
    b = open(p, "rb").read(65536)
    crlf, lf = b.count(b"\r\n"), b.count(b"\n") - b.count(b"\r\n")
    return "CRLF" if crlf > lf else "LF"


def _sample_hex(source_root, tgt, n=96):
    """把 OBJECTS 附近的真实字节贴出来——行尾这类事实不能靠猜。"""
    p = _seed_path(source_root, tgt)
    if not p or not os.path.isfile(p):
        return None
    b = open(p, "rb").read()
    i = b.find(b"OBJECTS")
    if i < 0:
        return None
    seg = b[i:i + n]
    return {"offset": i, "bytes_visible": (seg.replace(b"\r", b"\\r")
                                           .replace(b"\n", b"\\n\\\n")
                                           .decode("latin1"))}


def _eof_anchor(source_root, tgt):
    """推导"新 SECTION 块插在哪"：插在**最后一个 code-0 / EOF 记录之前**。

    依据：DXF 的结构是 `0/SECTION … 0/ENDSEC` 重复若干块，最后以 `0/EOF` 收尾。
    插在 EOF 之前是唯一不需要改动任何已有块的合法位置。
    """
    p = _seed_path(source_root, tgt)
    if not p or not os.path.isfile(p):
        return None
    raw = open(p, "rb").read()
    # 按三种行尾切
    L = []
    i = 0
    n = len(raw)
    while i < n:
        j = i
        while j < n and raw[j] not in (10, 13):
            j += 1
        L.append((i, j, raw[i:j]))
        if j >= n:
            i = j
        elif raw[j] == 13 and j + 1 < n and raw[j + 1] == 10:
            i = j + 2
        else:
            i = j + 1
    last = None
    for k in range(len(L) - 1):
        if L[k][2].strip() == b"0" and L[k + 1][2].strip() == b"EOF":
            last = (L[k][0], k)
    if last is None:
        return None
    off, idx = last
    # 同一行尾风格
    eol = b"\r\n" if raw.find(b"\r\n") >= 0 else b"\n"
    return {"offset": off, "record_index": idx, "eol": eol.decode("latin1"),
            "file": os.path.basename(p)}

def build_mutation_plan(pipeline, features_by_id, findings_by_id, surface,
                       worklist, source_root, default_weight=0.5, v2dir=None):
    """从特征管线取 found 的 action，补上记录级定位，组成最终计划。"""
    tgt = surface.get("target") or {}
    fmt = (surface.get("input_format") or {}).get("format")
    chain_s = {x["step"]: x for x in (surface.get("evidence_chain") or [])}
    blockers, limits = [], []
    if fmt not in ("line_record", "binary_record", "raw_bytes"):
        blockers.append(f"input format unknown: {fmt}")

    found = [r for r in pipeline["features"] if r["status"] == "found"]
    if not found:
        blockers.append("没有任何特征在本项目找到落点（feature_pipeline 全是 not_found）")

    # ── 站点级归并：一个站点一个策略，多个特征可以指向同一站点 ──
    by_site = {}
    for r in found:
        a0 = r["action"]; st0 = a0["site"]
        key = (st0["file"], st0["free_line"], st0["use_line"])
        by_site.setdefault(key, {"site": st0, "features": [], "rows": []})
        by_site[key]["features"].append(a0["feature_id"])
        by_site[key]["rows"].append(r)

    actions, targets, sites_out = [], [], []
    for k, (key, grp) in enumerate(by_site.items(), 1):
        r = grp["rows"][0]          # 同一站点的证据链取第一条（其余特征只是换个说法）
        adv = []
        for f in grp["features"][1:]:
            adv.append((f, "与主特征指向同一站点，不单独生成策略"))
        # 跨函数审计里"判过 real 但两次结论不一致"的特征，记成 advisory 而不是支撑证据
        featdir = os.path.join(v2dir, "features") if v2dir else ""
        for fn in (sorted(os.listdir(featdir)) if featdir and os.path.isdir(featdir) else []):
            ap = os.path.join(featdir, fn, "cross_function_audit.json")
            if not os.path.isfile(ap):
                continue
            d0 = json.load(open(ap, encoding="utf-8")).get("agent_verdicts") or {}
            if any(v.get("verdict") == "real" for v in d0.get("verdicts") or []):
                adv.append((fn, "跨函数审计曾判 real 且指向同一站点，但重复运行结论不一致"
                                "（1 real / 1 false_positive），不作支撑证据"))
        grp["advisory"] = adv
        a0 = r["action"]
        a0 = r["action"]
        site = a0["site"]
        feature = features_by_id.get(a0["feature_id"]) or {}
        site_id = f"s{k:03d}"
        st = strategy_for(feature)
        rel, fn = site["file"], site["function"]
        call = find_call_site(source_root, rel, fn)
        fc = field_constraint(source_root, rel, [site["free_line"], site["use_line"]])
        eof = _eof_anchor(source_root, tgt)
        step4 = (next((c for c in a0["evidence_chain"] if c["step"] == 4), {}) or {})
        ev4 = " ".join(str(e[1]) for e in (step4.get("evidence") or [])
                       if isinstance(e, (list, tuple)) and len(e) >= 2)
        # 改哪一部分：站点变量若来自 ->value，就改值行
        target_part = "value_line" if "->value" in ev4 else (st.get("part") or "value_line")
        if not fc:
            blockers.append(f"{a0['feature_id']}: 字段约束未推出（找不到 v->code == N）")
        if not (call and call.get("section_anchor")):
            blockers.append(f"{a0['feature_id']}: 段锚点未推出")
        actions.append({
            "action_id": f"a{k:03d}",
            "site_id": site_id,
            "feature_id": a0["feature_id"],
            "supporting_features": sorted(set(grp["features"])),
            "feature_name": a0.get("feature_name"),
            "mechanism": a0.get("mechanism"),
            "weight": a0["weight"],
            "evidence_grade": a0.get("evidence_grade"),
            "site": site,
            "target_part": target_part,
            "operation": "ensure_record_structure",
            "operation_paths": ["replace_value_line", "construct_section"],
            "field_id": (f"record.value_after_group_code.{fc['group_code']}"
                         if (fc and target_part == "value_line") else
                         f"record.group_code.{fc['group_code']}" if fc else None),
            "locator": {"kind": "record_sequence",
                        "anchor": str(fc["group_code"]) if fc else None,
                        "regex": (surface.get("input_format") or {}).get("record_header_rx"),
                        "section_anchor": (call or {}).get("section_anchor"),
                        "pick": "random_k",
                        "k_range": "0 .. count-1",
                        "pick_reason": ("段内通常有多条同组码记录；固定改第一条会让所有种子产出同一结果。"
                                        "必须按 Seed 在候选集合里随机选一条。")},
            "new_value_policy": {
                "kind": "random_unrecognized_name",
                "derive_from": "Seed",
                "alphabet": ("ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz"
                             "0123456789_-"),
                "length": [1, 64],
                "must_differ_from_original": True,
                "must_differ_across_seeds": True,
                "reason": ("name 来自 pair->value.s（step4 证据）；is_dwg_object 只认识固定对象名，"
                           "随机串几乎必然不在集合内。**不要用固定候选列表**——那会把有效变异"
                           "空间压到个位数，等于半个预算在造重复。")},
            "construct": {
                "when": "section_absent",
                "sequence": [
                    f"0/SECTION",
                    f"2/{(call or {}).get('section_anchor')}",
                    f"0/<random_unrecognized_name>",
                    f"0/ENDSEC",
                ],
                "insert_position": ({"kind": "before_record",
                                     "anchor": "0/EOF",
                                     "offset": (eof or {}).get("offset"),
                                     "record_index": (eof or {}).get("record_index"),
                                     "derivation": ("DXF 由若干 `0/SECTION…0/ENDSEC` 块组成、"
                                                    "最后以 `0/EOF` 收尾；插在 EOF 之前不需要改动"
                                                    "任何已有块。锚点从 plan 的 seed_file 里实测")}
                                   if eof else
                                   {"kind": "append_at_end", "anchor": "eof",
                                    "derivation": "种子里找不到 `0/EOF`，退化为追加到末尾"}),
                "line_endings": (surface.get("input_contract") or {}).get("line_endings")
                                 or "CRLF",
                "record_header_rx": (surface.get("input_format") or {}).get("record_header_rx"),
                "basis_refs": ["target_surface:evidence_chain:step5",
                               "target_surface:evidence_chain:step6",
                               "mutation_plan:locator.section_anchor",
                               "mutation_plan:new_value_policy"],
            },
            "preserve": ["group_code_digits", "CRLF",
                         "section_terminator(ENDSEC)"],
            "expected_effect": (f"命中 {a0.get('mechanism')}："
                                f"{site['file']}:{site['free_line']} 释放后 "
                                f"L{site['use_line']} 仍解引用 {site['var']}"),
            "basis_refs": ([f"feature_pipeline:{a0['feature_id']}:site:{site['free_line']}"]
                           + [f"feature_pipeline:{a0['feature_id']}:chain:step{x['step']}"
                              for x in a0["evidence_chain"] if x.get("status") == "complete"]
                           + [f"feature:{a0['feature_id']}:mutation_target"]),
        })
        sites_out.append({"site_id": site_id, "file": key[0],
                          "free_line": key[1], "use_line": key[2],
                          "var": grp["site"]["var"],
                          "reuse_kind": grp["site"].get("reuse_kind"),
                          "supporting_features": sorted(set(grp["features"])),
                          "advisory_features": [{"feature": f, "note": n} for f, n in
                                                grp.get("advisory", [])],
                          "format_scope": (["DXF"] if (site.get("file") or "").startswith("src/in_dxf")
                                           else ["DXF", "DWG", "JSON"])})
        targets.append({"function": fn, "file": rel,
                        "section_anchor": (call or {}).get("section_anchor"),
                        "predicate": (chain_s.get(5, {}).get("evidence") or [[None, None]])[0][1]})

    not_found = [r["feature_id"] for r in pipeline["features"] if r["status"] != "found"]
    if not_found:
        limits.append("本项目未找到落点、已排除的特征: " + ", ".join(not_found))
    if v2dir:
        fd = os.path.join(v2dir, "features")
        flips = []
        for fn in (sorted(os.listdir(fd)) if os.path.isdir(fd) else []):
            hp = os.path.join(fd, fn, "history.jsonl")
            if not os.path.isfile(hp):
                continue
            rs = [json.loads(x) for x in open(hp, encoding="utf-8") if x.strip()]
            if len({json.dumps(r.get("counts"), sort_keys=True) for r in rs}) > 1:
                flips.append(f"{fn}: " + " → ".join(
                    f"real {r['counts']['real']}" for r in rs))
        if flips:
            limits.append("**审计结论不稳定的特征**（同一 prompt 多次运行结果不同，"
                          "未作为支撑证据）: " + "; ".join(flips))
    limits += ["plan 只保证记录级定位（记录头组码 + 段锚点），不保证字节偏移",
               "候选缺陷本身未经 fuzz 验证（已知的那条除外）"]
    total = round(default_weight + sum(a["weight"] for a in actions), 4)
    status = "ready" if (not blockers and actions and
                         all(a["target_part"] and a["locator"]["anchor"]
                             and (a.get("construct") or {}).get("sequence") for a in actions)) else "blocked"
    return {
        "schema_version": "stage5.mutation_plan.v5",
        "plan_id": "plan-003",
        "target": {"osv_id": tgt.get("osv_id"), "project": tgt.get("project"),
                   "commit": tgt.get("commit"), "crash_type": tgt.get("crash_type"),
                   "known_fault": {"file": (tgt.get("fault_file") or ""),
                                   "line": tgt.get("fault_line")}},
        "input_contract": {"format": fmt, "parser_entry": tgt.get("entry_symbol"),
                           "format_scope": (["DXF"] if fmt == "line_record" else [fmt]),
                           "seed_file": os.path.basename(_seed_path(source_root, tgt) or ""),
                           "line_endings": _line_endings(source_root, tgt),
                           "sample_hex": _sample_hex(source_root, tgt),
                           "accepted_seed_requirements": [],
                           "preserve": ["group_code_digits", "CRLF",
                                        "section_terminator(ENDSEC)"]},
        "weighting": {"default": default_weight,
                      "features_total": round(1.0 - default_weight, 4),
                      "features": len(found),
                      "per_feature": round((1.0 - default_weight) / len(found), 4) if found else 0.0,
                      "total": total},
        "targets": targets,
        "sites": sites_out,
        "mutations": actions,
        "expected_path": [
            ("harness 读取输入 → Bit_Chain", "target_surface:step1-2"),
            ("DXF 记录解析 → pair(code,value)", "target_surface:step3"),
            ("pair->value.s → name", "target_surface:step4"),
            ("判据为假 → else 分支", "target_surface:step5"),
            ("释放后回到循环条件解引用", "target_surface:step6"),
        ],
        "mutation_space": {
            "min_distinct_outputs": 200,
            "measured_over_seeds": 1000,
            "why": ("只要求『能改』不够。若 1000 个 Seed 只产出个位数不同结果，"
                    "等于半个预算在造重复，corpus 长不起来、目标触发率也不会提升。"),
        },
        "limits": limits,
        "status": status,
        "blockers": blockers,
    }


def main():
    ap = argparse.ArgumentParser(description="阶段5.4：生成 mutation plan（0 LLM）")
    ap.add_argument("--osv", required=True)
    ap.add_argument("--default-weight", type=float, default=0.5,
                    help="default 变异占比（默认 0.5，其余平分给各特征）")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    S5 = os.path.join(OUT, args.osv)
    V2 = os.path.join(S5, "v2")
    need = ["feature_pipeline.json", "candidate_findings.json", "target_surface.json"]
    for n in need:
        if not os.path.exists(os.path.join(V2, n)):
            raise SystemExit(f"缺少 {V2}/{n}")
    findings = load(os.path.join(V2, "candidate_findings.json"))
    surface = load(os.path.join(V2, "target_surface.json"))
    worklist = load(os.path.join(S5, "audit_worklist.json"))
    root = load(os.path.join(S5, "source_context.json"))["repo_local"]
    feats = load(os.path.join(ROOT, "outputs", "stage4", "uaf", "features.json"))

    pipe = load(os.path.join(V2, "feature_pipeline.json"))
    fmap = {f["id"]: f for f in feats["features"]}
    dmap = {f["finding_id"]: f for f in findings["findings"]}
    plan = build_mutation_plan(pipe, fmap, dmap, surface, worklist, root,
                               default_weight=args.default_weight, v2dir=V2)

    print(f"=== {args.osv} mutation plan ===")
    w = plan["weighting"]
    print(f"  权重    : default {w['default']:.2f} + {w['features']} 个**站点** × {w['per_feature']:.2f}"
          f" = {w['total']:.2f}")
    print(f"  status  : {plan['status'].upper()}")
    for b in plan["blockers"]:
        print(f"      ✗ {b}")
    for a in plan["mutations"]:
        print(f"  {a['action_id']} w={a['weight']:.2f} [{a['evidence_grade']:<15}] "
              f"{a['feature_id']:<11} {a['operation']:<24} anchor={a['locator']['anchor']}")
    print(f"  expected_path: {len(plan['expected_path'])} 步")
    print(f"  limits  : {len(plan['limits'])} 条")

    if args.dry_run:
        return
    os.makedirs(V2, exist_ok=True)
    p = os.path.join(V2, "mutation_plan.json")
    json.dump(plan, open(p, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(f"\n  写出 {p}")


if __name__ == "__main__":
    main()

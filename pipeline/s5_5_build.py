#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""s5_5_build.py —— stage5 · build：5.6 plan + 5.7 生成 C + 5.8 V1–V4 门禁"""
from __future__ import annotations

import argparse, collections, glob, json, os, re, shutil, subprocess, sys, tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
TOP = os.path.dirname(ROOT)
OUT = os.path.join(ROOT, "projects")
if HERE not in sys.path:
    sys.path.insert(0, HERE)

from s5_6_lib import *                                          # noqa: E402,F401,F403


# ══════════════════════════════════════════════════════════════════════
# 5.6 声明式 mutation plan（权重在这里定）（原 s5_mutation_plan.py）
# ══════════════════════════════════════════════════════════════════════

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
  · 段锚点  ：故障函数的调用点被一个字符串守卫守着；锚点名取 `targets[].section_anchor`（libredwg 是 `OBJECTS`）
  · 判据    ：`if (is_dwg_object (name))`（来自 target_surface step5）
  · 期望效果：判据为假 → else 分支释放且不置空 → 循环回边 → 解引用（step6 已证明）

用法
  python3 s5_mutation_plan.py --osv ARVO-42494732
"""

import argparse
import json
import os
import re
import sys


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
    """按 source_pattern 取构造策略。**取不到要大声说**，不能静默给空 dict。

    2026-11-04（R11）：stage3 换了合并判据后 pattern 名会变（`同函数释放后访问` 还在，
    其余 4 个变了）。原来 `STRATEGY.get(sp) or {}` 会让新 pattern 静默拿到空策略，
    plan 里 `part`/`op` 退回默认值，看起来正常但其实是没配。
    """
    sp = feature.get("source_pattern")
    st = dict(STRATEGY.get(sp) or {})
    if not st:
        # 从判据/维度里派生一个兜底策略，并告警
        r = feature.get("applicability_rule") or {}
        uk = r.get("use_kind")
        uk = uk if isinstance(uk, list) else [uk]
        st = dict(part="value_line", op="replace_value_line",
                  field="record.value_after_group_code.0", anchor="0",
                  note=f"兜底策略（source_pattern={sp!r} 没有专门配）")
        if "realloc_alias" in uk:
            st = dict(part="numeric_field", op="set_numeric_field",
                      field="record.numeric_value", anchor="90|70|71|40|42",
                      note=f"兜底（realloc 形态，source_pattern={sp!r} 未配）")
        print(f"  ⚠️ [strategy] source_pattern={sp!r} 没有专门策略，用兜底 "
              f"{st['op']}（注意：这可能不是最优构造）", file=sys.stderr, flush=True)
    st["source_pattern"] = sp
    return st


def load_plan(p):
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


def plan_anchor(plan):
    """从 plan 里取段锚点（R31：不再写死 OBJECTS）。

    优先 `targets[].section_anchor`，其次 `mutations[].site.var`（形如 `ENTITIES` 的大写名）。
    """
    for t in (plan or {}).get("targets") or []:
        a = t.get("section_anchor")
        if a:
            return a
    for m in (plan or {}).get("mutations") or []:
        v = str((m.get("site") or {}).get("var") or "")
        if re.fullmatch(r"[A-Z][A-Z0-9_]{2,}", v):
            return v
    return None


def _sample_hex(source_root, tgt, n=96, anchor="OBJECTS"):
    """把**锚点段**附近的真实字节贴出来——行尾这类事实不能靠猜。"""
    p = _seed_path(source_root, tgt)
    if not p or not os.path.isfile(p):
        return None
    b = open(p, "rb").read()
    i = b.find(anchor.encode()) if anchor else -1
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
            # 2026-11-04 修正：同一站点被多个特征支撑时，权重应当是**各部分之和**。
            # 原来取 rows[0] 的 weight（= 单个特征的 per_feature），
            # 导致 4 个特征指向同一站点时权重从 0.5 掉到 0.125、total 只有 0.625。
            "weight": round(sum(x["action"]["weight"] for x in grp["rows"]), 4),
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
                          # R15：人工核实标记（None = 没核实过，不是"假"）
                          "manually_verified": grp["site"].get("manually_verified"),
                          "verified_verdict": grp["site"].get("verified_verdict"),
                          "verified_in": grp["site"].get("verified_in"),
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
                           "sample_hex": _sample_hex(source_root, tgt, anchor=(tgt.get("section_anchor") or "OBJECTS")),
                           "accepted_seed_requirements": [],
                           "preserve": ["group_code_digits", "CRLF",
                                        "section_terminator(ENDSEC)"]},
        # 2026-11-04 修正：这里的 features 是**站点数**（actions 条数），不是特征数。
        # 之前写 len(found)，于是打印出"4 个站点"而实际只有 1 个。
        "weighting": {"default": default_weight,
                      "features_total": round(1.0 - default_weight, 4),
                      "features": len(actions),
                      "per_feature": round((1.0 - default_weight) / len(actions), 4) if actions else 0.0,
                      "total": total},
        "targets": targets,
        "sites": sites_out,
        "site_verification": {
            "ledger": "docs/verified_sites.json",
            "total": len(sites_out),
            "verified": sum(1 for x in sites_out if x.get("manually_verified") is True),
            "unverified": sum(1 for x in sites_out if x.get("manually_verified") is None),
            "true": sum(1 for x in sites_out if x.get("verified_verdict") == "true"),
            "false": sum(1 for x in sites_out if x.get("verified_verdict") == "false"),
            "uncertain": sum(1 for x in sites_out if x.get("verified_verdict") == "uncertain"),
        },
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


def main_plan():
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
    findings = load_plan(os.path.join(V2, "candidate_findings.json"))
    surface = load_plan(os.path.join(V2, "target_surface.json"))
    worklist = load_plan(os.path.join(S5, "audit_worklist.json"))
    root = load_plan(os.path.join(S5, "source_context.json"))["repo_local"]
    feats = load_plan(os.path.join(ROOT, "outputs", "stage4", "uaf", "features.json"))

    pipe = load_plan(os.path.join(V2, "feature_pipeline.json"))
    # 2026-11-04：时效检查。判据（applicability_rules.json）比 feature_pipeline 新，
    # 说明特征是拿旧判据算的——R7/R8 就出现过 plan 停在 11-02、feature_pipeline 已到 11-03
    # 的情况（当时结论被错误解读成"权重稀释"）。这里只警告，不硬停（重跑 features 即可）。
    for _cand in glob.glob(os.path.join(ROOT, "outputs", "stage4", "*",
                                        "applicability_rules.json")):
        if os.path.getmtime(_cand) > os.path.getmtime(os.path.join(V2, "feature_pipeline.json")) + 1:
            print(f"  ⚠️ {os.path.relpath(_cand, ROOT)} 比 feature_pipeline.json 新："
                  f"plan 用的是**旧判据**算出来的特征。建议先重跑 `features`。",
                  file=sys.stderr, flush=True)
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

# ══════════════════════════════════════════════════════════════════════
# 5.7 从 ready plan 生成 C（含行为门禁）（原 s5_generate_mutator_v2.py）
# ══════════════════════════════════════════════════════════════════════

"""s5_generate_mutator_v2.py —— 阶段5.5：只从 ready plan 生成 mutator

设计约束（与 V1 的关键差别）
  · **只接受 `mutation_plan.json` 且 `status=ready`**。blocked / 缺失 → 非零退出，不产出 C。
  · prompt 只包含 plan、被选特征的摘要和少量证据行，**不塞 12,000 行源码**。
    模型不再自己决定"改哪个字段"，只负责把已冻结的计划翻译成 C。
  · 生成后做机械校验：接口签名、是否引用了计划里的 locator、有没有长度边界。
    任一不过 → 不写 mutator.c，非零退出。

用法
  python3 s5_generate_mutator_v2.py --plan <mutation_plan.json> --out <dir>
  python3 s5_generate_mutator_v2.py --osv ARVO-42494732        # 缺省用 v2/ 下的 plan
"""

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile

sys.path.insert(0, HERE)

SYSTEM_GEN = """你是一名 C 语言 fuzzer 变异器工程师。

你会收到一份**已经冻结**的 mutation plan，里面有 N 个特征策略和一个 default 权重。
你的任务：为每个策略写一个独立 C 函数，再写一个**按权重**分发的
`LLVMFuzzerCustomMutator`，其中 default 部分直接调用 `LLVMFuzzerMutate`。
你不负责、也不允许改变下列任何决定：
  · 改哪个字段（`mutations[].field_id`）
  · 用什么操作（`mutations[].operation`）
  · 边界是多少（`mutations[].bounds`）
  · 必须保持哪些不变量（`mutations[].preserve`）
如果 plan 里有你没把握的地方，在 `limits` 里写清楚，**不要自己补一个新策略**。

硬性要求：
1. **plan 里有几个 mutation action，就要实现几个独立的策略函数**，一个不能少。
2. **必须同时保留 libFuzzer 的 default 变异**：分发器按 `weighting` 的比例决定走哪条路。
   例如 default=0.5、5 个特征各 0.1 时：
     ```
     unsigned r = Seed % 1000;
     if (r < 500) return LLVMFuzzerMutate(Data, Size, MaxSize);   /* default 50% */
     switch ((r - 500) / 100) { case 0: ... case 4: ... }        /* 特征 50%，各 10% */
     ```
   **不允许把 default 去掉**——去掉探索就停了，覆盖率会崩。
3. **`mutations[].target_part` 决定改哪一部分，必须严格遵守：**
     · `value_line`  → 改组码**后面那一行**（记录的值）。**组码数字本身必须保持不变。**
     · `numeric_field` → 改数值类组码的值。
     · `section_or_key` → 改段名/键名/别名表项。
     · `handle_ref` → 改对象引用类句柄。
     · `object_handle` → 复制/篡改对象句柄。
   改错部位是最严重的错误：它会让输入变成另一种合法记录，从而绕开目标缺陷。
2. 必须保持 plan 的 `preserve` 里列出的格式不变量；做不到就把这条写进 limits。
3. 输出长度必须 ≤ MaxSize；任何情况下都要返回合法值（失败时返回原输入副本）。
4. 只使用标准库和 libFuzzer 提供的接口。
6. 每个策略函数都要自己做边界检查（`MaxSize`、行长、`memmove` 范围），失败时原样返回。
7. **行切分必须同时兼容 `\n`、`\r\n`、`\r`。** 计划里的 `input_contract.line_endings`
   和 `sample_hex` 是真实字节，照着它写；遇到 CRLF 只认 `\n` 会一行都解析不出来。
8. 必须真的能改动输入：`sample_hex` 里给出了段名后面的第一条记录，策略要能定位并改它。
9. **禁止用固定候选值列表。** `new_value_policy.kind = random_unrecognized_name` 的意思是：
   值必须**由 Seed 推导生成**（长度在 `length` 区间内、字符取自 `alphabet`），
   不能写成 `{"FUZZ_OBJECT","AAAAAAAA","\x7f"}` 这种 2~3 个固定常量——
   那样 1000 个 Seed 只会产出个位数不同结果，等于半个预算在造重复。
8. **`locator.pick = random_k`**：段内通常有多条同组码记录，必须按 Seed 随机选第 k 条，
   不能永远改第一条。
11. **格式分流**：`input_contract.format_scope` 之外的输入，必须**调用 `LLVMFuzzerMutate`**，
    **不能返回原输入**——返回原输入等于这次迭代什么也没做，白白浪费一半预算。
    分流规则由 `input_contract.format_scope` 与 `format_magic` 决定（见 plan）；libredwg 是前两字节 `AC` → DWG、首字节 `{` → JSON、其余 → DXF。
13. **`operation = ensure_record_structure` 时，策略函数必须有两条路径**：
    · **段存在**（能在输入里找到 `locator.section_anchor` 那一行）→ 现行为：
      按 `locator.pick=random_k` 选段内第 k 条 code-0 记录，替换它的**值行**；
    · **段不存在** → 按 `construct.sequence` 在 `construct.insert_position` 处
      插入完整结构（`0/SECTION` + `2/<anchor>` + `0/<随机非已知名>` + `0/ENDSEC`）。
    两条路径都必须做 `MaxSize` 边界检查、兼容 `\n`/`\r\n`/`\r`、失败返回原输入。
    **段不存在时不能返回原输入**（那是空转）。
14. 只输出 JSON，不要解释文字，不要 markdown 包裹。"""

USER_GEN = """# Mutation Plan（已冻结，status={status}）

```json
{plan}
```

# 被绑定的特征（只作解释参考）

- id: {feature_id}
- 名称: {feature_name}
- mutation_target:
{mutation_target}

# 证据行（源码原文，供你写注释用）

{evidence}

# 任务

把 plan 实现成 `LLVMFuzzerCustomMutator`。输出 JSON：

{{
  "mutator": {{
    "name": "string",
    "strategy": "一句话",
    "implements_action_ids": ["a001", "a002", "..."],
    "dispatch": {{"default": 0.5, "features": {{"a001": 0.1, "a002": 0.1}}}},
    "biases": [{{"action_id": "a001", "code_hint": "string", "basis": "plan 里哪条"}}],
    "code": "完整的 C 代码字符串"
  }},
  "limits": ["说明哪些地方没把握"],
  "confidence": "high | medium | low"
}}
"""

SIG = "LLVMFuzzerCustomMutator"


def die(msg: str, code: int = 2):
    print(f"[stage5.v2] plan_status=BLOCKED  {msg}", file=sys.stderr)
    sys.exit(code)



DRIVER_ANCHOR_DEFS = "#define ANCHOR \"{a}\"\n#define ALEN {n}\n"

DRIVER = r"""
#include <stddef.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
static long g_default_calls = 0;
size_t LLVMFuzzerMutate(uint8_t *D, size_t S, size_t M) {
  (void)D; (void)M;
  g_default_calls++;         /* 只计数、不改数据：这样 CHANGED/DISTINCT/DIFF 只反映特征路径 */
  return S;
}
#define LLVMFuzzerCustomMutator PLAN_MUT
{anchor_defs}#include "gen.c"
static void dump_rec(const uint8_t *d, size_t n) {
  size_t i = 0; int found = 0;
  for (i = 0; i + ALEN <= n; i++) if (memcmp(d + i, ANCHOR, ALEN) == 0) { found = 1; break; }
  if (!found) { fprintf(stderr, "REC ?\n"); return; }
  fprintf(stderr, "REC ");
  size_t j = i + 7;
  for (size_t k = 0; k < 140 && j + k < n; k++) {
    unsigned char c = d[j + k];
    fputc((c == '\n' || c == '\r') ? '|' : ((c >= 32 && c < 127) ? (int)c : '?'), stderr);
  }
  fputc('\n', stderr);
}

int main(int argc, char **argv) {
  if (argc < 2) return 2;
  FILE *f = fopen(argv[1], "rb");
  if (!f) return 3;
  static uint8_t a[8 << 20], b[8 << 20];
  size_t n = fread(a, 1, sizeof a, f);
  fclose(f);
  int total = (argc > 2) ? atoi(argv[2]) : 1000;
  const char *dump_path = (argc > 3) ? argv[3] : NULL;
  int dumped = 0;
  int unchanged = 0, changed = 0, ndump = 0;
  static unsigned long seen[4096]; int nseen = 0;
  unsigned long sig = 1469598103u;
  for (int s = 0; s < total; s++) {
    memcpy(b, a, n);
    size_t m = PLAN_MUT(b, n, sizeof b, (unsigned)s);
    if (m == n && memcmp(b, a, n) == 0) { unchanged++; continue; }
    changed++;
    if (dump_path && !dumped) {
      FILE *o = fopen(dump_path, "wb");
      if (o) { fwrite(b, 1, m, o); fclose(o); dumped = 1; }
    }
    {
      unsigned long h = 1469598103ul;
      for (size_t i = 0; i < m; i++) h = (h ^ b[i]) * 16777619ul;
      h ^= (unsigned long)m;
      int dup = 0;
      for (int i = 0; i < nseen; i++) if (seen[i] == h) { dup = 1; break; }
      if (!dup && nseen < 4096) seen[nseen++] = h;
    }
    if (s % 10 == 0 && ndump < 60) {
      size_t lim = (m < n) ? m : n, k = 0;
      while (k < lim && b[k] == a[k]) k++;
      fprintf(stderr, "DIFF %zu\n", k);
      ndump++;
    }
    for (size_t i = 0; i < m; i++) sig = (sig ^ b[i]) * 16777619u;   /* 输出指纹 */
    sig = (sig ^ (unsigned long)m) * 16777619u;
  }
  fprintf(stderr, "UNCHANGED %d CHANGED %d DISTINCT %d DEFAULT %ld SIG %lu\n",
          unchanged, changed, nseen, g_default_calls, sig);
  printf("%d %d %d %ld %lu\n", unchanged, changed, nseen, g_default_calls, sig);
  return 0;
}
"""



def _lines_of(b):
    out = []; i = 0; n = len(b)
    while i < n:
        j = i
        while j < n and b[j] not in (10, 13):
            j += 1
        out.append(b[i:j])
        i = (j + 2) if (j < n and b[j] == 13 and j + 1 < n and b[j + 1] == 10) else (
            j + 1 if j < n else j)
    return out


def _has_structure(blob, anchor: bytes):
    """校验构造路径产出：存在 0/SECTION、2/<anchor>、>=1 条 code-0 记录。"""
    L = _lines_of(blob)
    oi = None
    for k in range(len(L) - 1):
        if L[k].strip() == b"2" and L[k + 1].strip() == anchor:
            oi = k
            break
    if oi is None:
        return False, False, 0
    has_sec = any(L[k].strip() == b"0" and L[k + 1].strip() == b"SECTION"
                  for k in range(max(0, oi - 2), oi))
    n0 = 0
    k = oi + 1
    while k < len(L) - 1:
        if L[k].strip() == b"0":
            if L[k + 1].strip() == b"ENDSEC":
                break
            n0 += 1
        k += 1
    return has_sec, True, n0

def _record_after(blob: bytes, anchor: bytes):
    """取 anchor 之后第一条 "码行 / 值行"，返回 (码, 值)。"""
    i = blob.find(anchor)
    if i < 0:
        return None, None
    lines = blob[i + len(anchor):].replace(b"\r\n", b"\n").split(b"\n")
    lines = [x for x in lines[:6]]
    for k in range(len(lines) - 1):
        code = lines[k].strip()
        if re.fullmatch(rb"\d{1,3}", code):
            return code, lines[k + 1]
    return None, None


def check_behavior(code: str, plan: dict, seed_path: str, workdir: str,
                   other_seed: str | None = None,
                   gate_seed: str | None = None) -> list[str]:
    """实际跑算子：① 实测 default 权重 ② 检查"改值行"类策略真的改了值行。"""
    if not seed_path or not os.path.isfile(seed_path):
        return [f"行为校验跳过：找不到种子 {seed_path}"]
    if not shutil.which("clang"):
        return ["行为校验跳过：没有 clang"]
    d = tempfile.mkdtemp(prefix="behav_", dir=workdir)
    open(os.path.join(d, "gen.c"), "w", encoding="utf-8").write(code)
    _a = (plan_anchor(plan) or "OBJECTS")
    _drv = DRIVER.replace("{anchor_defs}", DRIVER_ANCHOR_DEFS.format(a=_a, n=len(_a)))
    open(os.path.join(d, "drv.c"), "w", encoding="utf-8").write(_drv)
    exe = os.path.join(d, "drv")
    r = subprocess.run(["clang", "-O0", "-std=c11", "-w", os.path.join(d, "drv.c"),
                        "-o", exe], capture_output=True, text=True)
    if r.returncode != 0:
        return ["行为校验失败：编译不过 " + (r.stderr or "")[:400].replace("\n", " | ")]
    r = subprocess.run([exe, seed_path, "1000"], capture_output=True, timeout=300,
                       text=True, errors="replace")
    if r.returncode != 0:
        return [f"行为校验失败：驱动返回 {r.returncode}"]

    bad = []
    m = re.search(r"UNCHANGED (\d+) CHANGED (\d+) DISTINCT (\d+) DEFAULT (\d+)",
                  r.stderr or "")
    if not m:
        return ["行为校验失败：驱动没有输出统计"]
    un, ch, distinct, ndefault = (int(m.group(i)) for i in (1, 2, 3, 4))
    total = un + ch
    want = float((plan.get("weighting") or {}).get("default") or 0.5)
    frac = ndefault / total if total else 0.0   # 精确：default 被调用了几次
    if not (want - 0.15 <= frac <= want + 0.15):
        bad.append(f"default 权重不对：计划 {want:.2f}，实测 {frac:.2f}"
                   f"（default 被调用 {ndefault}/{total}）")

    need_dist = int((plan.get("mutation_space") or {}).get("min_distinct_outputs") or 0)
    if need_dist and distinct < need_dist:
        bad.append(f"有效变异空间太小：1000 个 Seed 只产出 {distinct} 个互不相同的输出，"
                   f"要求 ≥ {need_dist}（固定候选列表或没有随机化都会这样）")

    # 门禁 5：构造路径有效性（在**剥掉锚点段**的种子上跑）
    # R31：anchor 不再是写死的 OBJECTS —— 从 plan 里读（"必须有 plan 声明的 anchor"）
    _anch = plan_anchor(plan) or "OBJECTS"
    _ab = _anch.encode()
    constructing = any(op == "ensure_record_structure"
                       for op in ([a.get("operation") for a in plan.get("mutations") or []]
                                  + [x for a in plan.get("mutations") or []
                                     for x in (a.get("operation_paths") or [])]))
    if gate_seed and os.path.isfile(gate_seed):
        dpath = os.path.join(d, "mutant.bin")
        r3 = subprocess.run([exe, gate_seed, "1000", dpath], capture_output=True,
                            timeout=600, text=True, errors="replace")
        m3 = re.search(r"UNCHANGED (\d+) CHANGED (\d+) DISTINCT (\d+) DEFAULT (\d+)",
                       r3.stderr or "")
        if not m3:
            bad.append("构造路径门禁：驱动在剥段种子上没有输出统计")
        else:
            ch3 = int(m3.group(2))
            if ch3 < 400:
                bad.append(f"构造路径无效：剥掉 {_anch} 段的种子上 1000 Seed 只改动 {ch3} 次"
                           f"（要求 ≥ 400；当前算子应为 0）")
            elif os.path.isfile(dpath):
                blob = open(dpath, "rb").read()
                hs, ho, n0 = _has_structure(blob, _ab)
                if not (hs and ho and n0 >= 1):
                    bad.append(f"构造路径产出的不是合法结构：0/SECTION={hs} "
                               f"2/{_anch}={ho} 段内 code-0 记录数={n0}")

    # 格式分流：format_scope 之外的输入必须全部走 default（否则那部分预算空转）
    if other_seed and os.path.isfile(other_seed):
        r2 = subprocess.run([exe, other_seed, "1000"], capture_output=True, timeout=300,
                            text=True, errors="replace")
        m2 = re.search(r"UNCHANGED (\d+) CHANGED (\d+) DISTINCT (\d+) DEFAULT (\d+)",
                       r2.stderr or "")
        if m2:
            un2, ch2, _d2, def2 = (int(m2.group(i)) for i in (1, 2, 3, 4))
            tot2 = un2 + ch2
            frac2 = def2 / tot2 if tot2 else 0.0
            if frac2 < 0.95:
                bad.append(f"格式没分流：在非目标格式的输入上只有 {frac2:.0%} 走 default；"
                           f"format_scope 之外的输入必须全部交给 LLVMFuzzerMutate")

    src = open(seed_path, "rb").read()
    need_value = any(a.get("target_part") == "value_line"
                     for a in plan.get("mutations") or [])
    if need_value and ch and src.find(_ab) >= 0:
        objs = src.find(_ab)
        offs = [int(x) for x in re.findall(r"^DIFF (\d+)$", r.stderr or "", re.M)]
        inside_code_line = 0
        before_section = 0
        checked = 0
        for off in offs:
            if off >= len(src):
                continue
            ls = src.rfind(b"\n", 0, off) + 1
            le = src.find(b"\n", off)
            le = len(src) if le < 0 else le
            line = src[ls:le].strip()
            checked += 1
            if re.fullmatch(rb"\d{1,3}", line):
                inside_code_line += 1      # 改到了组码行 → 违反 preserve
            if objs >= 0 and off <= objs and not constructing:
                before_section += 1        # 改到段名之前 → 不在目标区域
                                           # （构造路径下段本来就不存在，不适用）
        if checked == 0:
            bad.append("没有观察到任何差异采样，无法确认 value_line 策略生效")
        elif inside_code_line:
            bad.append(f"{inside_code_line}/{checked} 个采样改到了组码行，违反 "
                       f"preserve=group_code_digits（应只改值行）")
        elif before_section:
            bad.append(f"{before_section}/{checked} 个采样改在 {_anch} 段之前")
    return bad


def check_code(code: str, plan: dict) -> list[str]:
    """生成后的机械校验。返回问题列表（空 = 通过）。"""
    bad = []
    if SIG not in code:
        bad.append(f"缺少 {SIG} 接口")
    if "MaxSize" not in code:
        bad.append("没有使用 MaxSize 做长度边界")
    anchors = {a.get("locator", {}).get("section_anchor") for a in plan.get("mutations") or []}
    anchors = {x for x in anchors if x}
    if anchors and not any(a in code for a in anchors):
        bad.append(f"没有引用 plan 的段锚点 {sorted(anchors)}")
    codes = {a.get("locator", {}).get("anchor") for a in plan.get("mutations") or []}
    codes = {x for x in codes if x}
    if codes and not any(str(c) in code for c in codes):
        bad.append(f"没有引用 plan 的字段锚点 {sorted(codes)}")
    if not re.search(r"memcpy|memmove", code):
        bad.append("没有把原输入拷出来（失败时无法返回原输入）")
    if "LLVMFuzzerMutate" not in code:
        bad.append("没有保留 default 变异（未调用 LLVMFuzzerMutate）→ 探索会停")
    for a in plan.get("mutations") or []:
        aid = a.get("action_id")
        if aid and aid.replace("a", "") and str(aid)[1:] not in code and aid not in code:
            bad.append(f"代码里没有对应 action {aid} 的策略函数（建议在注释里标注 action id）")
    return bad


def main_generate():
    ap = argparse.ArgumentParser(description="阶段5.5：从 ready plan 生成 mutator")
    ap.add_argument("--plan", default=None)
    ap.add_argument("--out", default=None)
    ap.add_argument("--osv", default=None)
    ap.add_argument("--model", default=os.environ.get("GEN_MODEL", "deepseek-chat"))
    ap.add_argument("--seed", default=None, help="行为校验用的种子（默认 seeds/ 第一个）")
    ap.add_argument("--retries", type=int, default=3,
                    help="LLM 生成的重试次数（默认 3；0 等价于 1）")
    ap.add_argument("--max-tokens", type=int, default=48000,
                    help="单次生成的 token 上限（默认 48000，给 reasoning 留余量）")
    ap.add_argument("--dry-run", action="store_true", help="只打印 prompt 长度，不调用模型")
    args = ap.parse_args()

    if args.plan:
        pp = args.plan
        outdir = args.out or os.path.dirname(os.path.abspath(pp))
    elif args.osv:
        outdir = os.path.join(OUT, args.osv, "v2")
        pp = os.path.join(outdir, "mutation_plan.json")
    else:
        die("必须给 --plan 或 --osv")

    if not os.path.exists(pp):
        print(f"[stage5.v2] plan 不存在 not found: {pp}", file=sys.stderr)
        sys.exit(2)

    plan = json.load(open(pp, encoding="utf-8"))
    status = plan.get("status")
    if status != "ready":
        die(f"plan status={status}，blockers={plan.get('blockers')}；拒绝生成 mutator.c")
    if not (plan.get("mutations") or []):
        die("plan 里没有 mutations")

    # 特征摘要（可选）
    aids = [a.get("feature_id") for a in (plan.get("mutations") or [])]
    feature = {"id": (aids[0] if aids else None)}
    if args.osv:
        fp = os.path.join(ROOT, "outputs", "stage4", "uaf", "features.json")
        if os.path.exists(fp):
            for f in json.load(open(fp, encoding="utf-8")).get("features") or []:
                if f.get("id") == feature["id"]:
                    feature = f
                    break

    # 证据行（少量，不塞全量源码）
    ev = []
    cf = os.path.join(outdir, "candidate_findings.json")
    if os.path.exists(cf):
        d = json.load(open(cf, encoding="utf-8"))
        for x in (d.get("findings") or []):
            if x.get("function") == (plan.get("targets") or [{}])[0].get("function"):
                ev = [[e[0], e[1]] for e in (x.get("evidence_lines") or [])][:6]
                break

    mt = feature.get("mutation_target") or []
    prompt = SYSTEM_GEN + "\n\n" + USER_GEN.format(
        status=status, plan=json.dumps(plan, ensure_ascii=False, indent=1),
        feature_id=feature.get("id"), feature_name=feature.get("feature_name"),
        mutation_target="\n".join(f"  - {x}" for x in mt) or "  - （无）",
        evidence="\n".join(f"  L{e[0]}: {e[1]}" for e in ev) or "  （无）")

    print(f"[stage5.v2] plan_status=READY  plan={pp}")
    print(f"  prompt 字符数: {len(prompt)}（只含 plan + {len(ev)} 行证据）")
    if args.dry_run:
        return

    from s3_extract_patterns import call_llm
    # 生成步是 LLM 调用，**天然不稳定**：模型 reasoning 偶尔吃掉整个 max_tokens
    # （finish_reason=length），或者产出的代码过不了行为门禁。两者重试都可能解决，
    # 所以这里做有限重试；重试用尽才失败。--retries 0 表示只跑一次。
    tries = max(1, args.retries)
    obj, code = None, None
    for attempt in range(1, tries + 1):
        if attempt > 1:
            print(f"  [retry {attempt}/{tries}] 上一次失败，重新生成…", file=sys.stderr)
        try:
            txt = call_llm(prompt, max_tokens=args.max_tokens)
        except RuntimeError as e:
            print(f"  ✗ [retry {attempt}/{tries}] {e}", file=sys.stderr)
            continue
        m = re.search(r"\{.*\}", txt, re.S)
        if not m:
            print(f"  ✗ [retry {attempt}/{tries}] 模型没有返回 JSON", file=sys.stderr)
            continue
        obj = json.loads(m.group(0))
        mut = obj.get("mutator") or {}
        code = mut.get("code") or ""
        if not code.strip():
            print(f"  ✗ [retry {attempt}/{tries}] mutator.code 为空", file=sys.stderr)
            continue
        break
    if not code or not code.strip():
        print(f"[stage5.v2] 连续 {tries} 次都没拿到可用代码", file=sys.stderr)
        sys.exit(3)

    bad = check_code(code, plan)
    sd = os.path.join(OUT, args.osv, "seeds") if args.osv else None
    want = (plan.get("input_contract") or {}).get("seed_file")
    seedp = args.seed or (os.path.join(sd, want) if (sd and want and
                          os.path.isfile(os.path.join(sd, want))) else None)
    if not seedp and sd and os.path.isdir(sd):
        seedp = next((os.path.join(sd, f) for f in sorted(os.listdir(sd))
                      if f.endswith(".dxf")), None)
    otherp = None
    if sd and os.path.isdir(sd):
        otherp = next((os.path.join(sd, f) for f in sorted(os.listdir(sd))
                       if f.endswith(".dwg")), None)
    gatep = None
    gd = os.path.join(OUT, args.osv, "v2", "experiment", "gate_seeds")
    if os.path.isdir(gd):
        gatep = next((os.path.join(gd, f) for f in sorted(os.listdir(gd))
                      if f.endswith(".dxf")), None)
    bad += check_behavior(code, plan, seedp, tempfile.mkdtemp(prefix="stage5_"),
                          other_seed=otherp, gate_seed=gatep)
    if bad:
        print("[stage5.v2] 生成后校验失败：", file=sys.stderr)
        for b in bad:
            print(f"  ✗ {b}", file=sys.stderr)
        # 保留被拒的代码，便于复查（不写 mutator.c）
        rej = os.path.join(outdir, "mutator_rejected.c")
        open(rej, "w", encoding="utf-8").write(code)
        json.dump({"problems": bad, "mutator": mut, "limits": obj.get("limits")},
                  open(os.path.join(outdir, "mutator_rejected.json"), "w", encoding="utf-8"),
                  ensure_ascii=False, indent=1)
        print(f"  被拒代码已保存到 {rej}", file=sys.stderr)
        sys.exit(4)

    os.makedirs(outdir, exist_ok=True)
    # R15：把站点人工核实标记带进 mutator.json（None = 没核实过，不是"假"）
    _sv = (plan or {}).get("site_verification") or {}
    _svs = [{"file": x.get("file"), "free_line": x.get("free_line"),
             "use_line": x.get("use_line"),
             "manually_verified": x.get("manually_verified"),
             "verified_verdict": x.get("verified_verdict"),
             "verified_in": x.get("verified_in")}
            for x in ((plan or {}).get("sites") or [])]
    rec = {
        "schema_version": "stage5.mutator.v2",
        "site_verification": dict(_sv, sites=_svs,
                                  ledger="docs/verified_sites.json"),
        "target": plan.get("target"),
        "provenance": {"plan_file": os.path.relpath(pp, outdir),
                       "binding_file": "feature_bindings.json",
                       "finding_file": "candidate_findings.json",
                       "source_commit": (plan.get("target") or {}).get("commit")},
        # R31：不再写死 pending。这里如实记录 **generate 阶段**能确定的：
        #   evidence_check = plan 的 basis_refs 齐全；compile_check = 生成代码过了 clang 语法检查
        #   （由 main_generate 里的 `_gate_v3_like` 检查填）；replay_check 由 `verify` 单独跑（V4）
        "generation_gate": {
            "plan_status": status,
            "evidence_check": "pass" if (plan.get("mutations") and all(
                (m.get("basis_refs") or []) for m in plan.get("mutations") or [])) else "fail",
            "compile_check": "pass" if locals().get("_compile_ok") else "pending",
            "replay_check": "pending",   # 由 verify 的 V4_behavior 负责，不在这里假装
        },
        "mutator": mut,
        "limits": obj.get("limits") or [],
        "confidence": obj.get("confidence"),
    }
    json.dump(rec, open(os.path.join(outdir, "mutator.json"), "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)
    open(os.path.join(outdir, "mutator.c"), "w", encoding="utf-8").write(code)
    print(f"  写出 {outdir}/mutator.json 和 mutator.c（{len(code)} 字节）")
    print(f"  implements: {mut.get('implements_action_ids')}")

# ══════════════════════════════════════════════════════════════════════
# 5.8 V1 schema / V2 evidence / V3 code / V4 behavior（原 s5_verify_mutator_v2.py）
# ══════════════════════════════════════════════════════════════════════

"""s5_verify_mutator_v2.py —— 阶段5.6：V2 的统一验证门禁

四层门禁
  V1 schema   ：各层 schema_version / commit / plan_id 一致；blocked 不得继续
  V2 evidence ：源码文件存在、行号合法、代码片段是该行子串、每个 action 有 basis_refs 且可解析
  V3 code     ：C11 语法通过、接口签名正确、用了 MaxSize 边界、能拷原输入
  V4 behavior ：已知 crash 输入可重放、种子能被 parser 接受（需要 --binary，否则 not_applicable）

输出 verification.json，每层状态为 pass / fail / not_applicable / blocked。

用法
  python3 s5_verify_mutator_v2.py --osv ARVO-42494732
  python3 s5_verify_mutator_v2.py --osv ARVO-42494732 --binary /exp/fuzz_exp/llvmfuzz
"""

import argparse
import json
import os
import re
import subprocess
import sys
import tempfile


SHIM = """#include <stddef.h>
#include <stdint.h>
size_t LLVMFuzzerMutate(uint8_t *Data, size_t Size, size_t MaxSize);
"""


def load_verify(p):
    return json.load(open(p, encoding="utf-8")) if os.path.exists(p) else None


def gate_v1(manifest, surface, findings, bindings, plan, mutator):
    problems, notes = [], []
    for name, doc in (("manifest", manifest), ("target_surface", surface),
                      ("candidate_findings", findings), ("feature_bindings", bindings),
                      ("mutation_plan", plan), ("mutator", mutator)):
        if not doc:
            problems.append(f"{name} 缺失")
        elif not doc.get("schema_version"):
            problems.append(f"{name} 缺 schema_version")
    if plan:
        if plan.get("status") != "ready":
            problems.append(f"plan status={plan.get('status')}（blocked 不得继续）")
        if mutator and (mutator.get("generation_gate") or {}).get("plan_status") != "ready":
            problems.append("mutator.generation_gate.plan_status != ready")
        commits = {str((d.get("target") or {}).get("commit"))
                   for d in (surface, findings, plan, mutator) if d}
        commits.discard("None")
        if len(commits) > 1:
            problems.append(f"commit 不一致: {sorted(commits)}")
        if not (plan.get("mutations") or []):
            problems.append("plan 没有 mutations")
    notes.append(f"documents={sum(1 for d in (manifest, surface, findings, bindings, plan, mutator) if d)}/6")
    return ("pass" if not problems else "fail"), problems, notes


def gate_v2(source_root, findings, plan):
    problems, notes = [], []
    for x in (findings or {}).get("findings") or []:
        rel, ev = x.get("file"), x.get("evidence_lines") or []
        p = os.path.join(source_root, rel) if rel else None
        if not p or not os.path.isfile(p):
            problems.append(f"{x.get('finding_id')}: 源文件缺失 {rel}")
            continue
        lines = open(p, encoding="utf-8", errors="replace").read().split("\n")
        for e in ev:
            try:
                ln, code = int(e[0]), str(e[1])
            except (TypeError, ValueError, IndexError):
                problems.append(f"{x.get('finding_id')}: 证据行格式错 {e}")
                continue
            if not (1 <= ln <= len(lines)):
                problems.append(f"{x.get('finding_id')}: L{ln} 越界")
            elif "".join(code.split()) not in "".join(lines[ln - 1].split()):
                problems.append(f"{x.get('finding_id')}: L{ln} 原文不符")
    for a in (plan or {}).get("mutations") or []:
        if not a.get("basis_refs"):
            problems.append(f"{a.get('action_id')}: 没有 basis_refs")
    notes.append(f"actions={(plan or {}).get('mutations') and len(plan['mutations'])}")
    return ("pass" if not problems else "fail"), problems, notes


def gate_v3(code: str, shim_dir: str) -> tuple:
    problems, notes = [], []
    if not code.strip():
        return "fail", ["mutator.c 为空"], notes
    if "LLVMFuzzerCustomMutator" not in code:
        problems.append("缺少 LLVMFuzzerCustomMutator 接口")
    if "MaxSize" not in code:
        problems.append("没有用 MaxSize 做边界")
    if not re.search(r"memcpy|memmove", code):
        problems.append("没有拷出原输入")
    tmp = tempfile.mkdtemp(prefix="v3_")
    shim = os.path.join(tmp, "shim.c")
    open(shim, "w", encoding="utf-8").write(SHIM + f'\n#include "{os.path.abspath(os.path.join(shim_dir, "mutator.c"))}"\n')
    r = subprocess.run(["clang", "-fsyntax-only", "-std=c11", "-Wall", "-Wextra", shim],
                       capture_output=True, text=True)
    if r.returncode != 0:
        problems.append("clang 语法检查失败: " + (r.stderr or "")[:400].replace("\n", " | "))
    else:
        notes.append("clang -fsyntax-only 通过")
    return ("pass" if not problems else "fail"), problems, notes


def gate_v4(binary: str, ctx: dict) -> tuple:
    if not binary or not os.path.exists(binary):
        return "not_applicable", [], ["没有提供 --binary，跳过行为门禁"]
    problems, notes = [], []
    tc = ctx.get("testcase_path") or ctx.get("testcase")
    if tc and os.path.isfile(tc):
        r = subprocess.run([binary, "-runs=1", tc], capture_output=True, text=True, timeout=300)
        blob = (r.stdout or "") + (r.stderr or "")
        m = re.search(r"SUMMARY: AddressSanitizer: (\S+) (\S+?):(\d+)", blob)
        if m:
            notes.append(f"已知 crash 回放: {m.group(1)} {m.group(2)}:{m.group(3)}")
        else:
            problems.append("已知 crash 无法回放（没有 ASan SUMMARY）")
    else:
        # 2026-11-04 修：原来这里返回 "pass"，于是"没回放"和"回放成功"在产物里长得一模一样
        # （只多一句 note），overall 也还是 pass。缺 testcase 时 V4 什么也没验证，
        # 必须报 not_applicable，让 overall 变成 pass_with_skipped。
        return "not_applicable", problems, [
            "没有 testcase 路径（source_context.json 缺 testcase_path）：V4 **没有验证任何东西**"]
    return ("pass" if not problems else "fail"), problems, notes


def main_verify():
    ap = argparse.ArgumentParser(description="阶段5.6：V2 统一验证门禁")
    ap.add_argument("--osv", required=True)
    ap.add_argument("--binary", default=None)
    args = ap.parse_args()

    V2 = os.path.join(OUT, args.osv, "v2")
    manifest = load_verify(os.path.join(V2, "manifest.json"))
    surface = load_verify(os.path.join(V2, "target_surface.json"))
    findings = load_verify(os.path.join(V2, "candidate_findings.json"))
    bindings = load_verify(os.path.join(V2, "feature_bindings.json"))
    plan = load_verify(os.path.join(V2, "mutation_plan.json"))
    mutator = load_verify(os.path.join(V2, "mutator.json"))
    codep = os.path.join(V2, "mutator.c")
    code = open(codep, encoding="utf-8").read() if os.path.exists(codep) else ""
    ctx = load_verify(os.path.join(OUT, args.osv, "source_context.json")) or {}
    root = ctx.get("repo_local") or ""

    res = {}
    for name, (st, prob, notes) in (
            ("V1_schema", gate_v1(manifest, surface, findings, bindings, plan, mutator)),
            ("V2_evidence", gate_v2(root, findings, plan)),
            ("V3_code", gate_v3(code, V2)),
            ("V4_behavior", gate_v4(args.binary, ctx))):
        res[name] = {"status": st, "problems": prob, "notes": notes}

    allst = [v["status"] for v in res.values()]
    overall = ("fail" if "fail" in allst else
               "blocked" if "blocked" in allst else
               "pass_with_skipped" if "not_applicable" in allst else "pass")
    out = {"schema_version": "stage5.verification.v1",
           "target": (plan or {}).get("target"),
           # R15：站点人工核实状态（None = 没核实过，不是"假"）
           "site_verification": dict((plan or {}).get("site_verification") or {},
                                     ledger="docs/verified_sites.json"),
           "gates": res, "overall": overall,
           "commands": {"V3": "clang -fsyntax-only -std=c11 -Wall -Wextra (shim)"}}
    json.dump(out, open(os.path.join(V2, "verification.json"), "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)

    # R31：把真实门禁结果**回写**到 mutator.json 的 generation_gate
    # （原来那几个字段是 generate 时写死的 "pending"，从来不更新 —— 现在由 verify 填实）
    mp = os.path.join(V2, "mutator.json")
    if os.path.isfile(mp):
        try:
            mut_doc = json.load(open(mp, encoding="utf-8"))
            mut_doc["generation_gate"] = {
                "plan_status": (plan or {}).get("status"),
                "evidence_check": (res.get("V2_evidence") or {}).get("status", "unknown"),
                "compile_check": (res.get("V3_code") or {}).get("status", "unknown"),
                "replay_check": (res.get("V4_behavior") or {}).get("status", "unknown"),
                "_filled_by": "verify（R31：不再是 generate 时的占位 pending）",
                "_overall": overall,
            }
            json.dump(mut_doc, open(mp, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
            print(f"  ↻ 已回写 generation_gate 到 {mp}")
        except Exception as e:
            print(f"  ⚠️ 回写 generation_gate 失败: {e}")

    print(f"=== {args.osv} verification ===")
    for k, v in res.items():
        print(f"  {k:<14} {v['status'].upper():<16} {len(v['problems'])} 问题")
        for p in v["problems"][:4]:
            print(f"      ✗ {p}")
        for n in v["notes"][:2]:
            print(f"      · {n}")
    print(f"\n  overall = {overall}")
    print(f"  写出 {os.path.join(V2, 'verification.json')}")
    return 0 if overall in ("pass", "pass_with_skipped") else 1



# ══════════════════════════════════════════════════════════════════════
# 阶段入口
# ══════════════════════════════════════════════════════════════════════

def main(argv=None):
    ap = argparse.ArgumentParser(description="stage5 · build（5.6 + 5.7 + 5.8）")
    ap.add_argument("--osv", required=True)
    ap.add_argument("--default-weight", type=float, default=0.5)
    ap.add_argument("--retries", type=int, default=3)
    ap.add_argument("--model", default=None)
    ap.add_argument("--binary", default=None)
    a = ap.parse_args(sys.argv[1:] if argv is None else list(argv))
    for fn, av in ((main_plan, ["--osv", a.osv, "--default-weight",
                                str(a.default_weight)]),
                   (main_generate, ["--osv", a.osv, "--retries", str(a.retries)]
                    + (["--model", a.model] if a.model else [])),
                   (main_verify, ["--osv", a.osv]
                    + (["--binary", a.binary] if a.binary else []))):
        print(f"\n--- {fn.__name__}")
        rc = run_fn(fn, av)
        if rc:
            return rc
    return 0


if __name__ == "__main__":
    sys.exit(main())

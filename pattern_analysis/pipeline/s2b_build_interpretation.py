#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""s2f_build_interpretation.py —— 从 facts 派生 interpretation（按崩溃类型解读）。

输入：artifacts/facts/<OSV>/facts.json
输出：artifacts/interpretation/<OSV>/interpretation.json
      artifacts/interpretation.jsonl

原则：只对 facts 做筛选/排序/比较/判断，不产生新事实。
"""
from __future__ import annotations
import collections, json, os

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)   # pattern_analysis/
TOP = os.path.dirname(ROOT)    # mutator_create/
A = os.path.join(ROOT, "artifacts")
FACTS = os.path.join(A, "facts")

BUFFER_TYPES = {
    "heap-buffer-overflow", "stack-buffer-overflow", "global-buffer-overflow",
    "heap-buffer-underflow", "stack-buffer-underflow",
}
FREE_TYPES = {"heap-use-after-free", "heap-double-free", "invalid-free"}


def _free_sites(f):
    return sorted({s.get("line") for s in f.get("sites") or []
                   if s.get("kind") == "free" and s.get("line")})


def _crash_line(f):
    return (f.get("crash") or {}).get("site", {}).get("line")


def _alloc_size(f):
    a = f.get("alloc") or {}
    if a.get("size_bytes") is not None:
        return a["size_bytes"], "report.region_size"
    if a.get("size_expr"):
        return a["size_expr"], "cpg.alloc_arg"
    return None, None


def _width(f):
    w = (f.get("crash") or {}).get("access", {}).get("width")
    return w


def _free_arg(f):
    """解析 free 的实参名。优先用 deep 从 CPG 补的 args，其次用 code。"""
    import re as _re
    for s in (f.get("sites") or []):
        if s.get("kind") != "free":
            continue
        a = s.get("args")
        if a:
            first = str(a).split(" ;; ")[0].strip()
            m = _re.match(r'&?\s*([A-Za-z_]\w*)', first)
            if m:
                return m.group(1)
        if s.get("code"):
            m = _re.search(r'free\s*\(\s*([A-Za-z_]\w*)', str(s["code"]))
            if m:
                return m.group(1)
    return None


def _reassign_between(f, a, b):
    """free 行与 crash 行之间是否有对该变量的赋值。
    优先用 P0 补的 entity.assignments；没有则回退到 free_related。"""
    deep = f.get("deep") or {}
    assigns = deep.get("entity_assignments") or (f.get("entity") or {}).get("assignments") or []
    if assigns:
        return any(a < (x.get("line") or 0) < b for x in assigns)
    fr = f.get("free_related") or {}
    if "reassign_between" in fr:
        return bool(fr["reassign_between"])
    return None


def _missing_common(f):
    m = []
    if not f.get("entity", {}).get("decl"):
        m.append("entity.decl")
    if not f.get("types", {}).get("entity_type"):
        m.append("types.entity_type")
    return m


# ── 各类型派生 ───────────────────────────────────────────────────────────────

def interp_buffer_overflow(f):
    size, size_src = _alloc_size(f)
    w = _width(f)
    guards = (f.get("context") or {}).get("guards") or ""
    findings = {
        "buffer_obj": f.get("entity", {}).get("name"),
        "buffer_size": size,
        "buffer_size_source": size_src,
        "extent_bytes": w,
        "bound_check_exists": bool(guards.strip()),
        "bound_check_code": guards.strip() or None,
        "overflow_mode": None,
        "crosses_by_bytes": (w - size) if (isinstance(w, int) and isinstance(size, int)) else None,
        "buffer_size_expr": (f.get("alloc") or {}).get("size_expr_cpg"),
    }
    code = str((f.get("crash") or {}).get("line_code")
               or (f.get("crash") or {}).get("code") or "")
    if "memcpy" in code or "memset" in code:
        findings["overflow_mode"] = "size"
    elif "[" in code:
        findings["overflow_mode"] = "index"
    elif "+" in code or "-" in code:
        findings["overflow_mode"] = "pointer"
    miss = _missing_common(f)
    if size is None: miss.append("buffer_size")
    if w is None: miss.append("extent_bytes")
    conf = "high" if not miss else ("medium" if len(miss) <= 2 else "low")
    return {
        "type": (f.get("crash_type") or "buffer-overflow"),
        "confidence": conf,
        "key_facts": {"buffer_obj": findings["buffer_obj"], "buffer_size": size,
                      "extent_bytes": w, "crash_line": _crash_line(f)},
        "findings": findings,
        "missing": miss,
        "reasoning": f"访问宽度 {w} 字节 vs 缓冲区大小 {size}，"
                     + ("存在边界检查" if findings["bound_check_exists"] else "未发现边界检查"),
    }


def interp_double_free(f):
    frees = _free_sites(f)
    crash = _crash_line(f)
    # 报告给的"上一次释放"优先（更可靠）
    prev_from_report = None
    for s in f.get("sites") or []:
        if s.get("origin") == "report:freed_by":
            prev_from_report = s.get("line")
    in_loop = (f.get("context") or {}).get("in_loop")
    findings = {
        "free_sites_in_func": frees,
        "crash_free_site": crash,
        "previous_free_site": prev_from_report,
        "previous_free_source": "report:freed_by" if prev_from_report else None,
        "free_count": len(frees),
        "reassign_between": None,          # 需 P2：两次 free 之间的赋值
        "remalloc_between": None,          # 需 P2
        "in_loop": in_loop,
    }
    miss = _missing_common(f)
    if findings["reassign_between"] is None: miss.append("reassign_between")
    if findings["remalloc_between"] is None: miss.append("remalloc_between")
    conf = "high" if not miss else ("medium" if len(miss) <= 2 else "low")
    return {
        "type": "heap-double-free",
        "confidence": conf,
        "key_facts": {"freed_ptr": f.get("entity", {}).get("name"),
                      "free_sites": frees, "crash_free_site": crash,
                      "previous_free_site": prev_from_report, "in_loop": in_loop},
        "findings": findings,
        "missing": miss,
        "reasoning": f"同函数内 {len(frees)} 处 free；报告中上一次释放位于 {prev_from_report}，"
                     f"崩溃在 {crash}；"
                     + ("位于循环内，疑似迭代重复释放" if in_loop else "不在循环内"),
    }


def interp_use_after_free(f):
    frees = _free_sites(f)
    crash = _crash_line(f)
    frees_before = [x for x in frees if crash and x < crash]
    free_arg = _free_arg(f)
    ent = (f.get("entity") or {}).get("name")
    alias = None
    if free_arg and ent:
        alias = (free_arg != ent)      # free 的实参 ≠ 崩溃处变量名 → 用了别名
    reassigned = None
    if frees_before:
        reassigned = _reassign_between(f, max(frees_before), crash)
    findings = {
        "free_sites": frees,
        "use_site": crash,
        "crash_after_free": bool(frees_before),
        "reassigned_between": reassigned,
        "alias_used": alias,
        "free_arg": free_arg,
        "free_cross_function": bool(free_arg and ent and free_arg != ent) if False else None,
    }
    # free 与崩溃是否跨函数：从 sites 的 fn 判断
    free_fns = {s.get("fn") for s in (f.get("sites") or []) if s.get("kind") == "free" and s.get("fn")}
    crash_fn = (f.get("crash") or {}).get("site", {}).get("fn")
    if free_fns and crash_fn:
        findings["free_cross_function"] = (crash_fn not in free_fns)
    miss = _missing_common(f)
    if not frees: miss.append("free_sites")
    if findings["reassigned_between"] is None: miss.append("reassigned_between")
    if findings["alias_used"] is None: miss.append("alias_used")
    conf = "high" if not miss else ("medium" if len(miss) <= 2 else "low")
    return {
        "type": "heap-use-after-free",
        "confidence": conf,
        "key_facts": {"freed_ptr": f.get("entity", {}).get("name"),
                      "free_sites": frees, "use_site": crash},
        "findings": findings,
        "missing": miss,
        "reasoning": (f"崩溃点 {crash} 之前已有 free 于 {frees_before}" if frees_before
                      else f"未在 facts 中找到崩溃点之前的 free，需补 free 栈"),
    }


def interp_invalid_free(f):
    e = f.get("entity") or {}
    a = f.get("alloc")
    findings = {
        "free_arg": e.get("name"),
        "arg_storage": e.get("storage"),
        "has_matching_alloc": bool(a),
        "ptr_arith_before_free": None,     # 需 P2
        "free_arg_is_offset": None,        # 需 P2
    }
    miss = _missing_common(f)
    if findings["arg_storage"] is None: miss.append("arg_storage")
    if findings["ptr_arith_before_free"] is None: miss.append("ptr_arith_before_free")
    conf = "high" if not miss else ("medium" if len(miss) <= 2 else "low")
    return {
        "type": "invalid-free",
        "confidence": conf,
        "key_facts": {"free_arg": findings["free_arg"], "arg_storage": findings["arg_storage"],
                      "has_matching_alloc": findings["has_matching_alloc"]},
        "findings": findings,
        "missing": miss,
        "reasoning": f"free 的参数 {findings['free_arg']} 存储区为 {findings['arg_storage']}，"
                     + ("存在匹配的分配点" if findings["has_matching_alloc"] else "未找到匹配的分配点"),
    }


def interp_uninit(f):
    e = f.get("entity") or {}
    findings = {
        "uninit_var": e.get("name"),
        "def_sites": [],                   # 需 P2：该变量的赋值点
        "def_in_branch": None,
        "uninit_path": None,
        "partial_init": None,
    }
    miss = _missing_common(f)
    miss += ["def_sites", "def_in_branch", "uninit_path"]
    return {
        "type": "use-of-uninitialized-value",
        "confidence": "low",
        "key_facts": {"uninit_var": findings["uninit_var"]},
        "findings": findings,
        "missing": miss,
        "reasoning": "当前 facts 不含变量的赋盘点，无法判断哪条分支漏赋值；需补充定义-使用链查询",
    }


def interp_invalid_deref(f):
    e = f.get("entity") or {}
    guards = (f.get("context") or {}).get("guards") or ""
    findings = {
        "ptr_expr": e.get("name"),
        "ptr_origin": None,                # 需 P2：声明节点种类
        "null_checked_before": bool(guards.strip()),
        "deref_offset": None,
        "ptr_type": (f.get("types") or {}).get("entity_type"),
    }
    miss = _missing_common(f)
    if findings["ptr_origin"] is None: miss.append("ptr_origin")
    conf = "high" if not miss else ("medium" if len(miss) <= 2 else "low")
    return {
        "type": f.get("crash_type") or "segv-on-unknown-address",
        "confidence": conf,
        "key_facts": {"ptr_expr": findings["ptr_expr"], "null_checked": findings["null_checked_before"]},
        "findings": findings,
        "missing": miss,
        "reasoning": ("崩溃前存在比较，可能已判空" if findings["null_checked_before"]
                      else "崩溃前未发现与指针相关的比较，可能是未判空直接解引用"),
    }


def interp_negative_size(f):
    findings = {
        "size_expr": (f.get("crash") or {}).get("code"),
        "size_src_type": None,             # 需 P2
        "size_signed": (f.get("types") or {}).get("is_signed"),
        "has_explicit_cast": (f.get("types") or {}).get("cast_present"),
        "size_from_param": None,
    }
    miss = _missing_common(f)
    miss += [k for k, v in findings.items() if v is None]
    return {
        "type": "negative-size-param",
        "confidence": "low",
        "key_facts": {"size_expr": findings["size_expr"]},
        "findings": findings,
        "missing": miss,
        "reasoning": "需要 size 表达式的类型信息判断是否有符号；当前仅拿到崩溃行代码",
    }


def interp_memcpy_overlap(f):
    code = str((f.get("crash") or {}).get("line_code")
               or (f.get("crash") or {}).get("code") or "")
    findings = {"dst_expr": None, "src_expr": None, "size_expr": None,
                "same_origin": None, "same_variable": None, "code": code}
    miss = ["dst_expr", "src_expr", "size_expr", "same_origin"]
    return {"type": "memcpy-param-overlap", "confidence": "low",
            "key_facts": {"code": code}, "findings": findings, "missing": miss,
            "reasoning": "需要 memcpy 三个实参的源码，当前 CPG 查询未提取"}


def interp_generic(f):
    return {"type": f.get("crash_type") or "unknown", "confidence": "low",
            "key_facts": {"crash_line": _crash_line(f), "entity": (f.get("entity") or {}).get("name")},
            "findings": {}, "missing": ["该类型尚未定义解读规则"],
            "reasoning": f"崩溃类型 {f.get('crash_type')} 暂无专用解读器"}


DISPATCH = {
    "heap-buffer-overflow": interp_buffer_overflow,
    "stack-buffer-overflow": interp_buffer_overflow,
    "global-buffer-overflow": interp_buffer_overflow,
    "heap-buffer-underflow": interp_buffer_overflow,
    "stack-buffer-underflow": interp_buffer_overflow,
    "heap-double-free": interp_double_free,
    "heap-use-after-free": interp_use_after_free,
    "invalid-free": interp_invalid_free,
    "use-of-uninitialized-value": interp_uninit,
    "segv-on-unknown-address": interp_invalid_deref,
    "null-dereference": interp_invalid_deref,
    "negative-size-param": interp_negative_size,
    "memcpy-param-overlap": interp_memcpy_overlap,
}


def main():
    out_dir = os.path.join(A, "interpretation")
    os.makedirs(out_dir, exist_ok=True)
    by_type = collections.Counter()
    conf = collections.Counter()
    n = 0
    with open(os.path.join(A, "interpretation.jsonl"), "w", encoding="utf-8") as fh:
        for osv in sorted(os.listdir(FACTS)):
            p = os.path.join(FACTS, osv, "facts.json")
            if not os.path.isfile(p):
                continue
            f = json.load(open(p, encoding="utf-8"))
            fn = DISPATCH.get(f.get("crash_type") or "", interp_generic)
            it = fn(f)
            it["osv_id"] = osv
            it["project"] = f.get("project")
            it["crash_type"] = f.get("crash_type")
            os.makedirs(os.path.join(out_dir, osv), exist_ok=True)
            with open(os.path.join(out_dir, osv, "interpretation.json"), "w", encoding="utf-8") as g:
                json.dump(it, g, ensure_ascii=False, indent=2)
                g.write("\n")
            fh.write(json.dumps(it, ensure_ascii=False, sort_keys=True) + "\n")
            by_type[it.get("type")] += 1
            conf[it.get("confidence")] += 1
            n += 1
    print(f"写出 {n} 个 interpretation")
    print("类型分布:", dict(by_type.most_common()))
    print("置信度:", dict(conf))


if __name__ == "__main__":
    main()

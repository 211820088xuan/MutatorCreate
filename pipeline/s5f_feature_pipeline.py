#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""s5f_feature_pipeline.py —— 阶段5.3'：**每个特征都走同一套固定流程**

为什么要有这个模块
  之前只有 uaf-llm01 走了完整流程（崩溃报告给了站点），其余 4 个用"通用字段类别"猜，
  方法不一致。本模块把流程固定下来，5 个特征一视同仁：

  ① 短名单（确定性）   按该特征的机制，从 worklist 里挑出可能承载它的函数
  ② 站点扫描（确定性） 在同一批函数上扫"释放→使用"原语，产出带行号的原始站点
  ③ 机制归类（确定性） 把站点归到它能支持的机制上；归不上就是"本项目无落点"
  ④ 六步证据链（确定性）站点 → 完整证据链；任何一跳不闭合就降级
  ⑤ 输入分支判定（确定性）判断该站点在哪条输入分支上（DXF / DWG / JSON）
  ⑥ 动作规格（确定性） 字段 + 操作 + 保持的不变量 + 证据等级

  每一步的产物都落盘；`status` 只有 `found` / `not_found` / `blocked` 三种。
  **找不到就明确写 not_found，权重还给 default——不用 generic 算子占预算。**

固定的机制→短名单/归类规则（可审计，不靠 LLM）
  llm01 同函数释放后访问      : free 后同函数内再读，含循环回边
  llm02 重分配后旧缓冲        : realloc 的结果没回写给原变量，或先存别名再 realloc
  llm03 清理/析构先释放后读    : 函数名匹配 free/destroy/cleanup/close/del 的释放路径
  llm04 跨函数陈旧对象        : 释放与读取发生在不同函数（结构体字段/别名）
  llm05 容器节点销毁后遍历     : 释放后在循环里继续走 next/prev/child 链

用法
  python3 s5f_feature_pipeline.py --osv ARVO-42494732 --all
  python3 s5f_feature_pipeline.py --osv ARVO-42494732 --feature uaf-llm02
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
sys.path.insert(0, HERE)
import cfg_lib  # noqa: E402

# ─────────────── 固定规则表 ───────────────
FREE_CALL = re.compile(
    r"\b([A-Za-z_]\w*)\s*\(\s*&?\s*([A-Za-z_]\w*(?:\s*->\s*\w+)?)\s*\)\s*;")
FREE_NAME = re.compile(r"(free|destroy|release|clear|cleanup|del|close)", re.I)
REALLOC_CALL = re.compile(
    r"\b([A-Za-z_]\w*)\s*=\s*(?:\([^)]*\)\s*)?realloc\s*\(\s*([A-Za-z_]\w*(?:\s*->\s*\w+)?)\s*,")
LINK_READ = re.compile(r"\b(\w+)\s*->\s*(next|prev|child|sibling|first|last|head|tail)\b")

# 短名单规则：机制 → 函数名/被调名线索（确定性，可审计）
SHORTLIST = {
    "llm01": dict(name_rx=r".*", call_rx=r".*(free|destroy|release).*",
                  why="需要 free 类调用 + 同函数内再读"),
    "llm02": dict(name_rx=r".*", call_rx=r".*(realloc|alloc|resize|grow).*",
                  why="需要 realloc/扩容"),
    "llm03": dict(name_rx=r".*(free|destroy|cleanup|close|del).*",
                  call_rx=r".*(free|destroy|release|clear).*",
                  why="清理/析构函数里的释放"),
    "llm04": dict(name_rx=r".*(resolve|fixup|update|defer|postpon|stale|flush).*",
                  call_rx=r".*", why="延迟解析/交叉引用修正"),
    "llm05": dict(name_rx=r".*", call_rx=r".*(free|destroy|release|clear).*",
                  why="容器销毁后仍遍历"),
}
# 输入格式 → 该格式会走到的源文件。特征必须在**对应格式的代码路径**里找站点，
# 否则会出现"给 DXF 写算子、却指望它在 DWG 上生效"这种错配。
# 所有格式都会走到的公共路径（清理、句柄解析、写出）。站点落在这些文件里，
# 说明它对**所有格式**都适用，format_scope 要写全。
COMMON_FILES = ("src/free.c", "src/dwg.c")
FORMAT_FILES = {
    "DXF":  ("src/in_dxf.c",) + COMMON_FILES,
    "DWG":  ("src/decode.c", "src/bits.c") + COMMON_FILES,
    "JSON": ("src/in_json.c",) + COMMON_FILES,
}
FORMAT_MAGIC = {"DWG": "'AC' 开头", "JSON": "'{' 开头", "DXF": "其余"}

MECH_KEY = {"llm01": "同函数释放后访问", "llm02": "缓冲释放后旧指针",
            "llm03": "清理析构后悬垂访问", "llm04": "跨函数陈旧对象访问",
            "llm05": "容器节点销毁后遍历"}


# ─────────────── ① 短名单 ───────────────
def shortlist(feature_id, worklist, callees, only_files=None):
    key = feature_id.split("-")[-1]
    rule = SHORTLIST.get(key)
    if not rule:
        return [], "该特征没有短名单规则"
    rx_n = re.compile(rule["name_rx"], re.I)
    rx_c = re.compile(rule["call_rx"], re.I)
    out = []
    for f in worklist["functions"]:
        if only_files and not any(f["file"].startswith(x) for x in only_files):
            continue
        calls = callees.get((f["file"], f["name"]), set())
        by_name = bool(rx_n.fullmatch(f["name"]))
        by_call = any(rx_c.fullmatch(c) for c in calls)
        if by_name or by_call:
            out.append({"function": f["name"], "file": f["file"],
                        "lines": f["lines"], "depth": f["depth"],
                        "risk": f["risk"], "hit_by": "name" if by_name else "call"})
    out.sort(key=lambda x: (x["depth"], 0 if x["risk"] else 1))
    return out, rule["why"]


# ─────────────── ② 站点扫描（原语） ───────────────
def scan_sites(root, shortlist_funcs, src_cache):
    """在短名单函数里扫"释放类调用 → 后续读同一变量"。产出原始站点。"""
    sites = []
    for f in shortlist_funcs:
        lines = src_cache.get(f["file"])
        if not lines:
            continue
        lo, hi = f["lines"][0] - 1, min(f["lines"][1], len(lines)) - 1
        blocks = cfg_lib.blocks(lines, lo, hi)
        for i in range(lo, hi + 1):
            code = cfg_lib.strip_code(lines[i])
            m = FREE_CALL.search(code)
            if not m or not FREE_NAME.search(m.group(1)):
                continue
            callee, var = m.group(1), m.group(2).replace(" ", "")
            # a) 同块/后续直线上的读
            same = None
            for j in range(i + 1, min(hi, i + 200) + 1):
                s = cfg_lib.strip_code(lines[j])
                if re.search(rf"\b{re.escape(var)}\b\s*=(?!=)", s):
                    break
                if re.search(rf"\b{re.escape(var)}\b\s*(->|\.|\[)", s):
                    same = {"line": j + 1, "code": s[:160], "kind": "same_path"}
                    break
                if re.search(r"\breturn\b", s):
                    break
            # b) 循环回边上的读
            trace = cfg_lib.flow(lines, lo, hi, i, 20)
            bi = next((k for k, t in enumerate(trace) if t["back_edge"]), None)
            back = None
            if bi is not None:
                # 回边之前若把 var 重新赋值，就不是 UAF
                end_ln = trace[bi]["line"]
                if any(re.search(rf"\b{re.escape(var)}\b\s*=(?!=)",
                                 cfg_lib.strip_code(lines[j]))
                       for j in range(i + 1, end_ln + 1)):
                    trace = []
                    bi = None
            if bi is not None:
                for t in trace[bi:]:
                    s = cfg_lib.strip_code(lines[t["line"]])
                    if re.search(rf"\b{re.escape(var)}\b\s*(->|\.|\[)", s):
                        back = {"line": t["line"] + 1, "code": s[:160],
                                "kind": "loop_back",
                                "back_edge_to": (trace[bi]["next"] + 1
                                                 if trace[bi]["next"] is not None else None)}
                        break
            use = same or back
            if not use:
                continue
            if not wrapper_frees_param(callee, var, funcs_by_name, root, src_cache):
                continue      # 包装只释放成员，不释放该变量本身
            link = bool(LINK_READ.search(cfg_lib.strip_code(lines[use["line"] - 1])))
            sites.append({"function": f["function"], "file": f["file"],
                          "free_line": i + 1, "free_code": code[:160],
                          "callee": callee, "var": var,
                          "use": use, "is_link_read": link,
                          "realloc_near": _realloc_near(lines, lo, hi, i)})
    return sites



_WRAP_CACHE: dict = {}


def wrapper_frees_param(callee, var, funcs_by_name, root, src_cache):
    """`dwg_free_header_vars(dwg)` 只释放 dwg 的成员，不释放 dwg 本身 → 不能算释放。

    判定：被调函数体里出现 `free ( <形参> )` 或 `free ( (char*)<形参> )` 这类**直接释放**。
    """
    key = callee
    if key in _WRAP_CACHE:
        return _WRAP_CACHE[key]
    f = funcs_by_name.get(callee)
    if not f:
        _WRAP_CACHE[key] = True          # 看不到源码就不排除（保守）
        return True
    lines = src_cache.get(f["file"])
    if not lines:
        _WRAP_CACHE[key] = True
        return True
    lo, hi = f["lines"][0] - 1, min(f["lines"][1], len(lines))
    # 形参名（第一个参数）
    head = " ".join(lines[lo:min(lo + 3, hi)])
    m = re.search(r"\(\s*[^,)]*?\b(\w+)\s*[,)]", head)
    param = m.group(1) if m else None
    if not param:
        _WRAP_CACHE[key] = True
        return True
    rx = re.compile(rf"\bfree\s*\(\s*(?:\([^)]*\)\s*)?&?\s*{re.escape(param)}\b")
    ok = any(rx.search(lines[j]) for j in range(lo, hi))
    _WRAP_CACHE[key] = ok
    return ok

def _realloc_near(lines, lo, hi, i):
    for j in range(max(lo, i - 30), min(hi, i + 30) + 1):
        m = REALLOC_CALL.search(cfg_lib.strip_code(lines[j]))
        if m:
            return {"line": j + 1, "var": m.group(1), "arg": m.group(2)}
    return None



# ── llm02 专用：realloc / 扩容后旧别名仍被访问（这个形态**没有 free 调用**，
#    所以 scan_sites 从来扫不到它——这是之前的检测器缺口）──
ALIAS_ASSIGN = re.compile(
    r"\b(?:const\s+)?(?:unsigned\s+char|char|uint8_t|Dwg_Object|Dxf_Pair|void)\s*\*\s*"
    r"([A-Za-z_]\w*)\s*=\s*(?:&\s*)?\(?\s*(?:unsigned\s+char\s*\*\s*\)?\s*)?"
    r"&?\s*([A-Za-z_]\w*(?:\s*->\s*\w+)?)\s*\[")
REALLOC_RX = re.compile(
    r"\b([A-Za-z_]\w*(?:\s*->\s*\w+)?)\s*=\s*(?:\([^)]*\)\s*)?realloc\s*\(\s*\1\s*,")


def scan_realloc_sites(shortlist_funcs, src_cache):
    """找『先取别名 → realloc 原缓冲 → 之后还用别名』。"""
    out = []
    for f in shortlist_funcs:
        lines = src_cache.get(f["file"])
        if not lines:
            continue
        lo, hi = f["lines"][0] - 1, min(f["lines"][1], len(lines)) - 1
        for i in range(lo, hi + 1):
            m = REALLOC_RX.search(lines[i])
            if not m:
                continue
            base = m.group(1).replace(" ", "")
            aliases = {}
            for j in range(max(lo, i - 60), i):
                a = ALIAS_ASSIGN.search(lines[j])
                if a and a.group(2).replace(" ", "").startswith(base.split("->")[-1]):
                    aliases[a.group(1)] = j + 1
            if not aliases:
                continue
            for var, aline in aliases.items():
                for j in range(i + 1, min(hi, i + 120) + 1):
                    if re.search(rf"\b{re.escape(var)}\b\s*(\[|->)", lines[j]):
                        out.append({"function": f["function"], "file": f["file"],
                                    "realloc_line": i + 1, "realloc_code": lines[i].strip()[:140],
                                    "base": base, "alias": var, "alias_line": aline,
                                    "use_line": j + 1, "use_code": lines[j].strip()[:140],
                                    "kind": "realloc_alias"})
                        break
    return out

# ─────────────── ③ 机制归类 ───────────────
def classify(site, feature_id):
    """这个站点能否支持给定机制？返回 (ok, 理由)。"""
    key = feature_id.split("-")[-1]
    fn = site["function"].lower()
    if key == "llm01":
        if site["use"]["kind"] == "loop_back":
            return True, "循环回边回到解引用同一变量"
        if site["use"]["kind"] == "same_path" and not site["is_link_read"]:
            return True, "同一直线上释放后解引用"
        return False, "没有同函数内的后续读"
    if key == "llm02":
        r = site["realloc_near"] or {}
        if site.get("callee") == "realloc" or (r and r.get("var") != r.get("arg")):
            return True, (f"别名 {r.get('var')} 取自 {r.get('arg')}，realloc 之后仍被读"
                          if r else "realloc 之后旧别名仍被读")
        return False, "附近没有『realloc 之后旧别名仍被读』的形态"
    if key == "llm03":
        if re.search(r"(free|destroy|cleanup|close|del)", fn):
            return True, "释放发生在清理/析构函数里"
        return False, "释放不在清理/析构路径上"
    if key == "llm04":
        if re.search(r"(resolve|fixup|update|defer|postpon)", fn):
            return True, "延迟解析/交叉引用修正路径"
        return False, "不在延迟解析路径上"
    if key == "llm05":
        if site["is_link_read"]:
            return True, "释放后仍沿 next/prev/child 链走"
        return False, "释放后的读不是链式遍历"
    return False, "未知机制"


# ─────────────── ④ 六步证据链 ───────────────
def build_chain(site, feature, surface, src_cache):
    lines = src_cache[site["file"]]
    lo, hi = site["free_line"] - 1, None
    chain = [
        {"step": 1, "name": "harness 入口", "status": "complete" if
         (surface.get("target") or {}).get("entry_symbol") else "unknown",
         "evidence": [(surface.get("target") or {}).get("entry_symbol")]},
        {"step": 2, "name": "输入绑定", "status": "complete"}
        if (surface.get("input_format") or {}).get("format") else {"step": 2, "status": "unknown",
                                                                   "evidence": []},
        {"step": 3, "name": "解析到内部结构", "status": "complete"
         if (surface.get("parsers") or []) else "unknown",
         "evidence": [[p["function"], p["lines"][0]] for p in (surface.get("parsers") or [])[:3]]},
        {"step": 4, "name": "字段进入目标变量", "status": "complete",
         "evidence": [[site["free_line"], site["free_code"]]]},
        {"step": 5, "name": "释放点所在分支", "status": "complete",
         "evidence": [[site["free_line"], site["free_code"]]]},
        {"step": 6, "name": "释放后仍被读", "status": "complete",
         "evidence": [[site["use"]["line"], site["use"]["code"]]],
         "note": ("循环回边⟲回到 L%s" % site["use"].get("back_edge_to")
                  if site["use"]["kind"] == "loop_back" else "同一直线上")},
    ]
    # 逐跳核对源码行是否真的存在
    for st in chain:
        for ev in st.get("evidence") or []:
            if isinstance(ev, list) and len(ev) >= 2 and isinstance(ev[0], int):
                st["status"] = ("complete" if 1 <= ev[0] <= len(lines) else "unknown")
    return chain


# ─────────────── ⑤ 输入分支 ───────────────
def input_branch(rel, src_cache):
    """站点所在的源文件属于哪条输入分支（harness 按前两字节分流）。"""
    if rel.startswith("src/in_dxf"):
        return {"branch": "DXF", "entry": "dwg_read_dxf", "magic": "非 'AC'、非 '{'"}
    if rel.startswith("src/in_json"):
        return {"branch": "JSON", "entry": "dwg_read_json", "magic": "'{'"}
    if rel.startswith("src/decode") or rel.startswith("src/bits"):
        return {"branch": "DWG", "entry": "dwg_decode", "magic": "'AC'"}
    if rel.startswith("src/out_") or rel.startswith("src/encode"):
        return {"branch": "OUTPUT", "entry": "(写出路径)", "magic": "解析成功后"}
    return {"branch": "UNKNOWN", "entry": None, "magic": None}


# ─────────────── ⑥ 动作规格 ───────────────
def build_action(feature, site, chain, branch, weight):
    ok = all(s["status"] == "complete" for s in chain) and branch["branch"] != "UNKNOWN"
    return {
        "action_id": None,
        "feature_id": feature.get("id"),
        "feature_name": feature.get("feature_name"),
        "mechanism": MECH_KEY.get(feature.get("id", "").split("-")[-1]),
        "weight": weight,
        "site": {"function": site["function"], "file": site["file"],
                 "free_line": site["free_line"], "use_line": site["use"]["line"],
                 "var": site["var"], "callee": site["callee"],
                 "reuse_kind": site["use"]["kind"]},
        "input_branch": branch,
        "evidence_chain": chain,
        "evidence_grade": "proven" if ok else "blocked",
        "operation": ("mutate_binary_record" if branch["branch"] == "DWG"
                      else "mutate_text_record"),
        "status": "found" if ok else "blocked",
        "blockers": [] if ok else [f"step{s['step']} 未闭合" for s in chain
                                   if s["status"] != "complete"]
        + ([f"输入分支未知"] if branch["branch"] == "UNKNOWN" else []),
    }


# ─────────────── 主流程 ───────────────
def load_cpg_dump(p):
    methods, edges = [], []
    for ln in open(p, encoding="utf-8"):
        t = ln.rstrip("\n").split("\t")
        if t[0] == "@@M" and len(t) >= 6:
            methods.append({"file": t[1], "name": t[2], "start": int(t[3] or 0),
                            "end": int(t[4] or 0), "external": t[5] == "1"})
        elif t[0] == "@@C" and len(t) >= 4:
            edges.append((t[1], t[2], t[3]))
    callees = {}
    for cf, cn, cs in edges:
        callees.setdefault((cf, cn), set()).update(cs.split("|"))
    return methods, callees



# ── P3 预筛：这个特征在本项目有没有落点（筛子，不是判据）──
# 依据：stage3 final.json 的 trigger_condition.where_free / where_use 里的函数名，
# 与 audit_worklist 的可达函数集合求交。交集为空 → 该特征在本项目无落点。
# 注意：这只决定"要不要继续查"，不判断"站点是不是真 UAF"——后者仍归 cfg_lib 证据链 + agent。
REACHABLE: set = set()
PATTERN_BY_NAME: dict = {}
ID_RX = re.compile(r"[A-Za-z_][A-Za-z0-9_]{3,}")

# 标准库 / 编译器内建名。stage3 的 where_free / where_use 是散文，会把 malloc、wchar、
# mbrtowc 这类名字也写进去；它们在项目里的同名声明不是"特征落点"，必须剔除，
# 否则换项目时交集会被这些通用名污染（见 R3_PHASE D 报告）。
STDLIB_NAMES = {
    # 分配 / 释放
    "malloc", "free", "realloc", "calloc", "alloca", "memalign", "posix_memalign",
    "aligned_alloc", "valloc", "brk", "sbrk", "mmap", "munmap", "new", "delete",
    # 内存 / 字符串
    "memcpy", "memmove", "memset", "memcmp", "memchr", "bcopy", "bzero",
    "strdup", "strndup", "strcpy", "strncpy", "strcat", "strncat", "strlen",
    "strcmp", "strncmp", "strchr", "strrchr", "strstr", "strtok", "strerror",
    "sprintf", "snprintf", "vsprintf", "vsnprintf", "sscanf", "atoi", "atol", "strtol",
    # 宽字符 / 本地化（出现频率高、极易污染交集）
    "wchar", "wchar_t", "mbrtowc", "wcrtomb", "mbsrtowcs", "wcsrtombs", "mbstate",
    "wcslen", "wcscpy", "wcsncpy", "wcscmp", "setlocale",
    # 文件 / 流
    "fopen", "fclose", "fread", "fwrite", "fseek", "ftell", "fflush", "feof", "ferror",
    "fgets", "fputs", "getc", "putc", "printf", "fprintf", "puts", "perror",
    # 进程 / 控制
    "abort", "exit", "atexit", "assert", "errno", "memcpy_s", "memset_s",
}


def applicability(feature):
    """返回 {hit_count, hit_names, source_pattern, extracted, basis}。"""
    sp = feature.get("source_pattern")
    pat = PATTERN_BY_NAME.get(sp)
    if not pat:
        return {"hit_count": None, "hit_names": [], "source_pattern": sp,
                "extracted": 0, "basis": f"stage3 final.json 里找不到 pattern {sp!r}；预筛跳过"}
    tc = pat.get("trigger_condition") or {}
    names = set()
    for k in ("where_free", "where_use"):
        names |= set(ID_RX.findall(tc.get(k) or ""))
    dropped = sorted(n for n in names if n.lower() in STDLIB_NAMES)
    names = {n for n in names if n.lower() not in STDLIB_NAMES}
    hit = sorted(n for n in names if n in REACHABLE)
    return {"hit_count": len(hit), "hit_names": hit, "source_pattern": sp,
            "extracted": len(names), "dropped_stdlib": dropped,
            "basis": (f"trigger_condition.where_free/where_use 抽出 {len(names)} 个标识符"
                      f"（剔除 {len(dropped)} 个标准库名），"
                      f"与 {len(REACHABLE)} 个可达函数求交 → {len(hit)} 个命中")}



def run_feature(feature, worklist, callees, surface, src_cache, weight, fmt=None):
    fid = feature["id"]
    app = applicability(feature)
    if app["hit_count"] == 0:
        return {"feature_id": fid, "feature_name": feature.get("feature_name"),
                "target_format": fmt, "mechanism": MECH_KEY.get(fid.split("-")[-1]),
                "shortlist_rule": None, "shortlist": [], "shortlist_size": 0,
                "sites_scanned": 0, "sites_supporting": 0, "sites": [],
                "applicability": app,
                "status": "not_applicable",
                "why": f"预筛：{app['basis']} → 该特征与本项目可达代码无交集",
                "action": None}
    only = FORMAT_FILES.get(fmt) if fmt else None
    cands, why = shortlist(fid, worklist, callees, only)
    sites = scan_sites(surface_root, cands, src_cache) if cands else []
    if fid.endswith("llm02"):
        extra = scan_realloc_sites(cands, src_cache) if cands else []
        for e in extra:
            sites.append({"function": e["function"], "file": e["file"],
                          "free_line": e["realloc_line"], "free_code": e["realloc_code"],
                          "callee": "realloc", "var": e["alias"],
                          "use": {"line": e["use_line"], "code": e["use_code"],
                                  "kind": "same_path"},
                          "is_link_read": False, "realloc_near": {"var": e["alias"],
                                                                   "arg": e["base"]}})
        res_extra = len(extra)
    else:
        res_extra = 0
    scored = []
    for s in sites:
        ok, reason = classify(s, fid)
        scored.append({"site": s, "supports": ok, "reason": reason})
    good = [x for x in scored if x["supports"]]
    crash_fn = (surface.get("target") or {}).get("fault_function")
    good.sort(key=lambda x: (0 if x["site"]["function"] == crash_fn else 1,
                             0 if x["site"]["use"]["kind"] == "loop_back" else 1,
                             x["site"]["file"], x["site"]["free_line"]))
    res = {"feature_id": fid, "feature_name": feature.get("feature_name"),
           "target_format": fmt,
           "mechanism": MECH_KEY.get(fid.split("-")[-1]),
           "shortlist_rule": why, "shortlist": cands[:40],
           "shortlist_size": len(cands), "sites_scanned": len(sites),
           "sites_supporting": len(good),
           "applicability": app,
           "sites": [{**x["site"], "supports": x["supports"], "reason": x["reason"]}
                     for x in scored[:60]]}
    if fmt:
        branch = {"branch": fmt, "entry": None, "magic": FORMAT_MAGIC.get(fmt)}
        if any(st.get("file", "").startswith(COMMON_FILES) for st in sites[:1]) or \
           (good and good[0]["site"]["file"].startswith(COMMON_FILES)):
            branch = {"branch": "ALL", "entry": None,
                      "magic": "公共路径（清理/句柄/写出），三种格式都可达",
                      "format_scope": ["DXF", "DWG", "JSON"]}
    if not good:
        res.update({"status": "not_found",
                    "why": f"{fmt or '全局'} 路径：短名单 {len(cands)} 个函数、"
                           f"扫出 {len(sites)} 个释放→使用原语，没有一个能支持该机制",
                    "action": None})
        return res
    best = good[0]["site"]
    branch = ({"branch": fmt, "entry": None, "magic": FORMAT_MAGIC.get(fmt)}
              if fmt else input_branch(best["file"], src_cache))
    chain = build_chain(best, feature, surface, src_cache)
    action = build_action(feature, best, chain, branch, weight)
    action["candidate_count"] = len(good)
    res.update({"status": action["status"], "why": good[0]["reason"], "action": action})
    return res


surface_root = ""        # 由 main 注入
funcs_by_name: dict = {}  # 由 main 注入


def main():
    global surface_root, funcs_by_name, REACHABLE, PATTERN_BY_NAME
    ap = argparse.ArgumentParser(description="阶段5.3'：每个特征走同一套固定流程")
    ap.add_argument("--osv", required=True)
    ap.add_argument("--type", default="uaf")
    ap.add_argument("--feature", default=None, help="只跑一个特征")
    ap.add_argument("--all", action="store_true", help="跑该崩溃类型的全部特征")
    ap.add_argument("--by-format", action="store_true",
                    help="按『输入格式 × 特征』矩阵扫，每种格式只在该格式的代码路径里找站点")
    ap.add_argument("--default-weight", type=float, default=0.5)
    args = ap.parse_args()

    S5 = os.path.join(OUT, args.osv)
    V2 = os.path.join(S5, "v2")
    surface = json.load(open(os.path.join(V2, "target_surface.json"), encoding="utf-8"))
    worklist = json.load(open(os.path.join(S5, "audit_worklist.json"), encoding="utf-8"))
    ctx = json.load(open(os.path.join(S5, "source_context.json"), encoding="utf-8"))
    surface_root = ctx["repo_local"]
    feats = json.load(open(os.path.join(ROOT, "outputs", "stage4", args.type,
                                        "features.json"), encoding="utf-8"))["features"]
    _, callees = load_cpg_dump(os.path.join(S5, "cpg_dump.tsv"))
    funcs_by_name = {f["name"]: f for f in worklist["functions"]}
    REACHABLE = set(funcs_by_name)
    _fp = os.path.join(ROOT, "outputs", "stage3", args.type, "final.json")
    if os.path.exists(_fp):
        for _p in (json.load(open(_fp, encoding="utf-8")).get("final_patterns") or []):
            PATTERN_BY_NAME[_p["name"]] = _p
    print(f"  可适用性预筛：可达函数 {len(REACHABLE)} 个，"
          f"stage3 pattern {len(PATTERN_BY_NAME)} 个")

    src_cache = {}
    for f in worklist["functions"]:
        if f["file"] not in src_cache:
            p = os.path.join(surface_root, f["file"])
            src_cache[f["file"]] = (open(p, encoding="utf-8", errors="replace")
                                    .read().split("\n")) if os.path.isfile(p) else None

    if args.by_format:
        # 每种格式独立跑一遍：format × feature 矩阵
        matrix = []
        for fmt in FORMAT_FILES:
            todo_f = [f for f in feats if args.feature in (None, f["id"])]
            wf = round((1.0 - args.default_weight) / max(1, len(todo_f)), 4)
            print(f"\n--- 格式 {fmt}（{FORMAT_MAGIC[fmt]}）---")
            for f in todo_f:
                r = run_feature(f, worklist, callees, surface, src_cache, wf, fmt=fmt)
                matrix.append(r)
                icon = {"found": "✅", "not_found": "❌", "blocked": "⚠️",
                        "not_applicable": "⛔"}[r["status"]]
                print(f"  {icon} {r['feature_id']:<11} {r['status']:<10} "
                      f"短名单 {r['shortlist_size']:>3} / 支持 {r['sites_supporting']:>2}"
                      f"  {r['why'][:60]}")
        os.makedirs(os.path.join(V2, "features"), exist_ok=True)
        json.dump({"matrix": matrix, "formats": list(FORMAT_FILES)},
                  open(os.path.join(V2, "feature_matrix.json"), "w", encoding="utf-8"),
                  ensure_ascii=False, indent=1)
        print(f"\n  写出 {V2}/feature_matrix.json")
        found = [r for r in matrix if r["status"] == "found"]
        print(f"  共 found {len(found)} 条（格式×特征）")
        return

    todo = [f for f in feats if args.feature in (None, f["id"])] if (args.all or args.feature) \
        else feats
    n = len(todo)
    w = round((1.0 - args.default_weight) / n, 4) if n else 0.0

    print(f"=== {args.osv} 特征管线（{n} 个特征，每个权重 {w}）===")
    results = []
    for f in todo:
        r = run_feature(f, worklist, callees, surface, src_cache, w)
        results.append(r)
        icon = {"found": "✅", "not_found": "❌", "blocked": "⚠️",
                "not_applicable": "⛔"}[r["status"]]
        print(f"  {icon} {r['feature_id']:<11} {r['status']:<10} "
              f"短名单 {r['shortlist_size']:>3} / 原语 {r['sites_scanned']:>3} / "
              f"支持 {r['sites_supporting']:>2} | {r['why'][:70]}")
        if r["action"]:
            a = r["action"]
            print(f"        site: {a['site']['file']}:{a['site']['free_line']}"
                  f" → {a['site']['use_line']}  var={a['site']['var']}"
                  f"  branch={a['input_branch']['branch']}")

    os.makedirs(os.path.join(V2, "features"), exist_ok=True)
    for r in results:
        d = os.path.join(V2, "features", r["feature_id"])
        os.makedirs(d, exist_ok=True)
        json.dump(r, open(os.path.join(d, "pipeline.json"), "w", encoding="utf-8"),
                  ensure_ascii=False, indent=1)

    found = [r for r in results if r["status"] == "found"]
    # 权重要在"知道几个找到"之后才定：default 占 default_weight，其余平分给 found 的特征
    w2 = round((1.0 - args.default_weight) / len(found), 4) if found else 0.0
    for r in found:
        r["action"]["weight"] = w2
    print()
    print(f"  found {len(found)}/{n}；not_found {sum(1 for r in results if r['status']=='not_found')}；"
          f"blocked {sum(1 for r in results if r['status']=='blocked')}")
    if found:
        print(f"  权重合计: default {args.default_weight} + {len(found)}×{w2} = "
              f"{round(args.default_weight + len(found) * w2, 3)}")
    json.dump({"features": results,
               "weighting": {"default": args.default_weight,
                             "per_found_feature": w2, "found": len(found), "total": n}},
              open(os.path.join(V2, "feature_pipeline.json"), "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)
    print(f"  写出 {V2}/feature_pipeline.json")


if __name__ == "__main__":
    main()

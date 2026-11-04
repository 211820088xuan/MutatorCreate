#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""s4_abstract_features.py —— 把 stage3 的 1 个 pattern 归纳成 1 个通用特征。

输入：
  outputs/stage3/<type>/final.json    stage3 的 pattern
  artifacts/facts/<OSV>/facts.json    每样本的 facts

输出：
  outputs/stage4/<type>/features_<pattern>.json

用法：
  python3 s4_abstract_features.py --type uaf --pattern 同函数释放后访问
  python3 s4_abstract_features.py --type uaf --all
"""
from __future__ import annotations
import argparse, glob, json, os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)   # mutator_create/
TOP = os.path.dirname(ROOT)    # mutator_create/
sys.path.insert(0, HERE)
from s3_extract_patterns import call_llm, parse_json

OUT = os.path.join(ROOT, "outputs", "stage4")
FACTS = os.path.join(ROOT, "artifacts", "facts")

SYSTEM = """你是模糊测试机制归纳专家。

你的任务：把一组"同类崩溃样本"归纳成 1 个**项目无关**的通用特征。
这个特征后续会被用来为具体项目编写自定义变异算子（mutator），
所以它必须回答清楚：什么样的代码会出这类问题，以及该改输入的哪类字段。

归纳的要求：

1. 抽象到"机制"层面，不要描述单个样本。
2. 同一机制下的差异（数据结构、释放位置等）放进 parameterization，不要拆成多个特征。
3. mutation_target 写"字段类别"，但**每一条必须在括号里给出 1-3 个具体体现**，例如：
   "控制容器元素个数（列表长度 / 遍历项数 / 记录条数）"
   · 括号里的东西必须能在样本里找到依据（函数参数、崩溃代码里的字段名、遍历/切分函数等）
   · 宁可只写 2-3 条扎实的，不要堆砌抽象名词
     像"所有权、引用计数、触发标志、保留/删除/错误/清理/析构/回收"这种拼接式写法不算具体，禁止出现
   · 如果某个维度在样本里找不到依据，写进 limitations，不要写进 mutation_target
4. 禁止出现项目名、函数名、行号、变量名。
5. 从样本推不出来的东西，写进 limitations，不要编造。
6. 除上面那套描述性字段外，还要填 `applicability_rule`：一个**能被程序判定**的判据，
   用来回答"某段代码里的某个『释放→使用』站点，算不算本特征"。
   **它只能由下面 4 个字段组成，每个字段从给定词表里取值，禁止自由文本、禁止函数名/文件名/项目名。**

   | 字段 | 词表 | 含义 |
   |---|---|---|
   | `use_kind` | `loop_back` / `same_path` / `cross_function` / `realloc_alias` / `any` / 或它们的列表 | 释放后那次读是怎么到达的：循环回边 / 同一直线 / **跨函数（释放后把同一变量作为实参传给下一个函数，在那边读）** / realloc 别名 / 不限 |
   | `free_kind` | `direct_free` / `realloc_self_assign` / `alias_before_realloc` / `nearby_realloc_alias` / `any` / 或列表 | 释放的形态：直接 free / realloc 回写自身 / realloc 前留了别名 / 附近有 realloc 且别名为旧值 / 不限 |
   | `reassigned_between` | `true` / `false` / `any` | 释放与使用之间变量是否被重新赋值 |
   | `is_link_read` | `true` / `false` / `any` | 释放后那次读是否沿 next/prev/child 这类链式指针走 |

   `why` 用一个短句说明判据的依据。
   **必须给出 `differentiator`**：这条特征与其他每一条的区别落在**哪个可判定字段**上、取值各是什么。
   只能引用 dimensions 或判据四字段（`alloc_kind`/`free_before_use`/`free_and_use_same_function`/
   `reassigned_between`/`in_loop`/`access_kind`/`free_cross_function`/`cross_frame_count`/
   `use_kind`/`free_kind`/`is_link_read`），**不能写散文**。
   **如果你发现这条特征其实是另一条的子集（它的前置条件已经包含了这条的情形），
   直接写 `merge_into: <另一条的 feature_name>`。合并成 2-3 条是合法结果，
   比硬凑 5 条互相重叠的特征有价值。**

   **判据里的每个字段都必须真的能排除掉一些站点。** 如果某个字段在扫描器的产出里
   **只能取一个值**（例如 `reassigned_between` 恒为 `false`），写它等于没写，**不计入区分力**。

   **判据必须能把一部分站点排除掉。** 把所有字段都写 `any`、或把词表里所有取值都列上，
   等于"所有站点都算"——这种恒真判据会被校验拒绝。
   如果你认为这个机制在现有字段下**无法**用一个有区分力的判据表达，就设 `expressible: false`
   并在 `limitations` 写明缺什么字段——**这比给一个恒真判据有价值。**

   `use_kind` 现在**支持 `cross_function`**（v7 起）：扫描器会找
   "A 里释放 V → 之后调用 G(V) → G 里读形参"这种形态，且能证明释放先于使用。
   目前**只覆盖这一种**跨函数形态（实参传递），其它跨函数形态（结构体字段、全局、回调）
   仍表达不了——那种情况把 `expressible` 设为 `false` 并写清原因。

只输出 JSON，不要任何解释文字，不要用 markdown 包裹。"""

USER = """## 待归纳的崩溃类别

```json
{pattern_json}
```

## 该类别的全部样本（共 {n} 条）

{samples}

## 任务

把这 {n} 条样本归纳成 **1 个**通用特征。

## 输出 JSON schema

{{
  "feature_name": "一句话说清机制（不超过 25 字）",
  "precondition": ["什么样的代码形态会导致这类崩溃，3-5 条"],
  "trigger_path": ["输入要造成什么，才能从进入脆弱代码走到崩溃，3-5 步"],
  "mutation_target": [
    "2-4 条，每条格式：字段类别（具体体现 / 具体体现）"
  ],
  "parameterization": {{
    "维度名": ["该维度下的取值"]
  }},
  "limitations": ["从这批样本推不出来的东西"],
  "differentiator": [
    {{"vs": "另一条特征的 feature_name", "field": "可判定字段名", "this": "本条取值", "other": "那条取值"}}
  ],
  "merge_into": "（可选）如果这条其实是另一条的子集，写那条的 feature_name",
  "applicability_rule": {{
    "use_kind": "loop_back | same_path | realloc_alias | any | 或它们的列表",
    "free_kind": "direct_free | realloc_self_assign | alias_before_realloc | nearby_realloc_alias | any | 或列表",
    "reassigned_between": "true | false | any",
    "is_link_read": "true | false | any",
    "why": "一句短话说明判据依据",
    "expressible": true
  }},
  "sample_ids": ["本条特征覆盖了哪些样本"]
}}

`applicability_rule.expressible` 为 `false` 时，其余判据字段可以省略，但 `limitations` 必须写清原因。

直接输出 JSON。"""


def load_facts():
    """读 facts/<OSV>/facts.json（唯一存储）"""
    out = {}
    for p in sorted(glob.glob(os.path.join(FACTS, "*", "facts.json"))):
        try:
            d = json.load(open(p, encoding="utf-8"))
        except Exception:
            continue
        out[d["osv_id"]] = d
    return out


def fmt_sample(f):
    """把一条 facts 压成约 10 行结构化文本。"""
    c = f.get("crash") or {}
    s = c.get("site") or {}
    acc = c.get("access") or {}
    e = f.get("entity") or {}
    decl = e.get("decl") or {}
    a = f.get("alloc") or {}
    asite = a.get("site") or {}
    dp = f.get("deep") or {}
    ctx = f.get("context") or {}

    def frees():
        r = [(x.get("fn"), x.get("line")) for x in (f.get("sites") or []) if x.get("kind") == "free"]
        return ", ".join(f"{fn}:{ln}" for fn, ln in r) or "无"

    def cpg_calls():
        r = [f"{x.get('line')}:{x.get('callee')}({x.get('args')})"
             for x in (dp.get("sites") or []) if x.get("line")]
        return " | ".join(r[:8]) or "无"

    def params():
        fp = dp.get("func_params") or {}
        ns = fp.get("names") or []
        ts = fp.get("types") or []
        return ", ".join(f"{n}:{t}" for n, t in zip(ns, ts)) or "无"

    def line_calls():
        r = [f"{x.get('name')}({x.get('code')})" for x in (dp.get("line_calls") or [])]
        return " | ".join(r[:8]) or "无"

    def guards():
        r = [f"{x.get('line')}:{x.get('code')}" for x in (dp.get("guards") or [])]
        return " | ".join(r[:8]) or "无"

    def assigns():
        r = [f"{x.get('line')} {x.get('code')}" for x in (dp.get("entity_assignments") or [])]
        return " | ".join(r[:6]) or "无"

    lines = [
        f"[{f['osv_id']}] {f.get('project')}",
        f"  类型: {f.get('crash_type')}",
        f"  崩溃代码: {str(c.get('code') or '无')[:160]}",
        f"  崩溃访问: {acc.get('dir')} 宽 {acc.get('width')} 字节，区域 {acc.get('region_bytes')} 字节",
        f"  核心变量: {e.get('name')} ({decl.get('type')})",
        f"  分配: {a.get('api')} @ {asite.get('fn')}，{a.get('size_bytes')} 字节，跨函数={a.get('cross_function')}",
        f"  报告给的释放点: {frees()}",
        f"  函数内调用: {cpg_calls()}",
        f"  变量赋值: {assigns()}",
        f"  函数参数: {params()}",
        f"  崩溃行表达式分解: {line_calls()}",
        f"  守卫条件: {guards()}",
        f"  上下文: in_loop={ctx.get('in_loop')} | 守卫={str(ctx.get('guards') or '无')[:80]}",
        f"  输入可达: {f.get('input_reachability')}",
    ]
    return "\n".join(lines)


def build_blacklist(samples):
    words = set()
    for f in samples:
        for v in [f.get("project")]:
            if v:
                words.add(str(v))
        e = f.get("entity") or {}
        if e.get("name"):
            words.add(str(e["name"]))
        decl = e.get("decl") or {}
        if decl.get("type"):
            words.add(re.sub(r"[^A-Za-z_]", "", str(decl["type"])))
        for x in (f.get("sites") or []):
            if x.get("fn"):
                words.add(str(x["fn"]))
            ln = x.get("line")
            if isinstance(ln, int) and ln > 99:
                words.add(str(ln))
        a = f.get("alloc") or {}
        if (a.get("site") or {}).get("fn"):
            words.add(str(a["site"]["fn"]))
        for x in (f.get("deep") or {}).get("sites") or []:
            if x.get("callee"):
                words.add(str(x["callee"]))
        cs = (f.get("crash") or {}).get("site") or {}
        if cs.get("fn"):
            words.add(str(cs["fn"]))
        if isinstance(cs.get("line"), int):
            words.add(str(cs["line"]))
    skip = {"null", "true", "false", "free", "malloc", "calloc", "realloc", "unknown", "operator"}
    return sorted(w for w in words if len(w) >= 4 and w.lower() not in skip)


RULE_VOCAB = {
    "use_kind": {"loop_back", "same_path", "cross_function", "realloc_alias", "any"},
    "free_kind": {"direct_free", "realloc_self_assign", "alias_before_realloc",
                  "nearby_realloc_alias", "any"},
    "reassigned_between": {"true", "false", "any"},
    "is_link_read": {"true", "false", "any"},
}



# ─────────────── 可证伪性检查（语义版，2026-11-04）───────────────
# R8 的版本只数"这个字段写了词表的真子集"，但语法上的真子集不一定能排除任何站点：
# `scan_sites()` 产出的站点 `reassigned_between` **恒为 false**，所以写
# `reassigned_between: false` 看起来"具体"，实际排除不了任何站点。
# 现在改成：拿**真实扫出来的站点**当试金石，逐个字段去掉看命中集合变不变。
#
# 注意：这里**没有**重写匹配逻辑，而是复用 s5_4_analyze 的 `_match_conjunct`
# （通过构造一个能还原出同样四元组的合成 site 来喂它）。
FALSIFIABILITY_MODE = "structural"    # structural（默认门禁）/ semantic（诊断）/ syntactic
# 扫描器能力声明：这些字段在 scan_sites() 的产出里**只能取一个值**，写进判据等于没写。
#   reassigned_between —— 回边/直线扫描碰到重新赋值就截断（见 scan_sites 的注释），
#                         跨函数站点更是直接硬编码 False。所以它恒为 False。
# 一致性检查：如果将来扫描器真能产出别的值，下面的 load_touchstone 会报 stale。
STRUCTURALLY_FIXED = {"reassigned_between": False}
TOUCHSTONE_SOURCES: list = []


def _synthetic_site(fields):
    """把归一化的四个字段还原成一个能被 `_match_conjunct` 消费的 site。"""
    fk = fields.get("free_kind")
    if fk == "realloc_self_assign":
        callee, rn = "realloc", {"var": "x", "arg": "x"}
    elif fk == "alias_before_realloc":
        callee, rn = "realloc", {"var": "x", "arg": "y"}
    elif fk == "nearby_realloc_alias":
        callee, rn = "free", {"var": "x", "arg": "y"}
    else:
        callee, rn = "free", None
    return {"use": {"kind": fields.get("use_kind")}, "callee": callee,
            "realloc_near": rn,
            "reassigned_between": fields.get("reassigned_between"),
            "is_link_read": fields.get("is_link_read")}


def load_touchstone():
    """收集所有项目已扫出的站点，归一化成四字段。返回 (sites, sources)。"""
    global FALSIFIABILITY_MODE
    try:
        from s5_4_analyze import _site_free_kind
    except Exception:
        return [], []
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    sites, srcs = [], []
    for fp in sorted(glob.glob(os.path.join(root, "projects", "*", "v2",
                                            "feature_pipeline.json"))):
        try:
            d = json.load(open(fp, encoding="utf-8"))
        except Exception:
            continue
        n0 = len(sites)
        for f in d.get("features") or []:
            for s in f.get("sites") or []:
                sites.append({"use_kind": (s.get("use") or {}).get("kind"),
                              "free_kind": _site_free_kind(s),
                              "reassigned_between": bool(s.get("reassigned_between")),
                              "is_link_read": bool(s.get("is_link_read"))})
        if len(sites) > n0:
            srcs.append(os.path.relpath(fp, root))
    # 一致性检查：声明的结构性单值字段，实测是不是真的只有一个值
    for k, v in STRUCTURALLY_FIXED.items():
        vals = {str(t[k]) for t in sites}
        if len(vals) > 1:
            print(f"  ⚠️ STRUCTURALLY_FIXED[{k}]={v} 已过期：实测取值 {sorted(vals)}")
    # 去重（同一站点在多个特征下重复出现）
    seen, uniq = set(), []
    for t in sites:
        k = (t["use_kind"], t["free_kind"], t["reassigned_between"], t["is_link_read"])
        if k not in seen:
            seen.add(k); uniq.append(t)
    return uniq, srcs


def _conjunct_hits(c, touch):
    from s5_4_analyze import _match_conjunct
    return {i for i, t in enumerate(touch) if _match_conjunct(_synthetic_site(t), c)}


def _conjunct_real_fields(c, touch):
    """这个分支里**真的能排除站点**的字段（去掉后命中集合变大）。"""
    base = _conjunct_hits(c, touch)
    real = []
    for k in c:
        c2 = {kk: vv for kk, vv in c.items() if kk != k}
        if not c2:
            if len(base) < len(touch):      # 只剩这一个字段且它排除了东西
                real.append(k)
            continue
        if _conjunct_hits(c2, touch) - base:
            real.append(k)
    return real, base


def _conjunct_strength(c):
    """这个合取分支在几个字段上做了**真子集**限制（0 = 恒真）。"""
    n = 0
    for k, allowed in RULE_VOCAB.items():
        if k not in c:
            continue
        if k in STRUCTURALLY_FIXED:
            continue      # 结构性单值：语法上是真子集，语义上排除不了任何站点
        v = c[k]
        vals = v if isinstance(v, list) else [v]
        s_set = {str(x).lower() for x in vals}
        full = {str(x).lower() for x in allowed}
        # 写成 any，或者把词表里所有非 any 的值都列上 → 等价于"不限"
        if s_set == {"any"} or s_set >= (full - {"any"}):
            continue
        n += 1
    return n


TOUCHSTONE_SITES: list = []


def check_rule(rule):
    """校验 applicability_rule：字段名在册、取值在词表内、无自由文本、无名单泄漏。

    返回 (ok, reason)。
    """
    if not isinstance(rule, dict):
        return False, "applicability_rule 缺失或不是对象"
    if rule.get("expressible") is False:
        return False, "rule_missing：模型声明该机制在现有词表里表达不了"
    branches = rule.get("any_of") or [rule]      # 允许 any_of，也允许扁平单合取
    if not isinstance(branches, list) or not branches:
        return False, "any_of 为空"
    for b in branches:
        if not isinstance(b, dict):
            return False, f"分支不是对象: {b!r}"
        used = 0
        for k, allowed in RULE_VOCAB.items():
            if k not in b:
                continue
            used += 1
            v = b[k]
            vals = v if isinstance(v, list) else [v]
            for x in vals:
                sv = str(x).lower() if not isinstance(x, bool) else str(x).lower()
                if sv not in allowed:
                    return False, f"{k} 取值 {x!r} 不在词表 {sorted(allowed)} 内"
        if used == 0:
            return False, "分支里没有任何词表字段"
        extra = set(b) - set(RULE_VOCAB) - {"why", "expressible"}
        if extra:
            return False, f"出现词表外字段 {sorted(extra)}（禁止自由文本字段）"
        # 2026-11-04：可证伪性。一个把整个词表都列上的分支等于"所有站点都算"，
        # 它不是判据，是空话。每个分支至少要在**一个**字段上做真子集限制。
        if _conjunct_strength(b) < 1:
            return False, ("判据不可证伪：所有字段都等价于『不限』"
                           "（写 any，或把词表里所有取值都列上）。"
                           "它会把所有站点都判成命中，等于没有判据。"
                           "如果这个机制在现有字段下无法表达出区分力，"
                           "请设 expressible: false 并在 limitations 里写清缺哪个字段。")
        # 语义校验：这个分支至少要有一个字段**真的能排除站点**
        if FALSIFIABILITY_MODE == "semantic" and TOUCHSTONE_SITES:
            real, base = _conjunct_real_fields(b, TOUCHSTONE_SITES)
            if not real:
                return False, (
                    f"判据不可证伪（语义）：这个分支的字段没有一个能真的排除站点"
                    f"（在 {len(TOUCHSTONE_SITES)} 个真实站点上，逐个去掉都不改变命中集合 "
                    f"{sorted(base)}）。"
                    f"常见原因是某个字段在所有站点上取值都相同"
                    f"（例如 `reassigned_between` 恒为 false），写它等于没写。"
                    f"如果这个机制在现有字段下无法表达出区分力，"
                    f"请设 expressible: false 并在 limitations 里写清缺哪个字段。")
    return True, "ok"


# 可判定字段：stage3 的 dimensions + applicability_rule 的四字段。
# `differentiator` 只能引用这些，不能写散文。
DECIDABLE_FIELDS = {
    "alloc_kind", "free_before_use", "free_and_use_same_function", "reassigned_between",
    "in_loop", "access_kind", "free_cross_function", "cross_frame_count",
    "use_kind", "free_kind", "is_link_read",
}


def check_differentiator(feat):
    """`differentiator` 必填，且每条都要引用至少一个可判定字段。"""
    d = feat.get("differentiator")
    if isinstance(d, str):
        return False, "differentiator 不能是散文，必须是 [{vs, field, this, other}] 列表"
    if not isinstance(d, list) or not d:
        return False, "differentiator 必填（至少一条）"
    for i, x in enumerate(d):
        if not isinstance(x, dict):
            return False, f"differentiator[{i}] 不是对象"
        f = str(x.get("field") or "").strip()
        if f not in DECIDABLE_FIELDS:
            return False, (f"differentiator[{i}].field={f!r} 不是可判定字段；"
                           f"可选 {sorted(DECIDABLE_FIELDS)}")
        if x.get("this") is None or x.get("other") is None:
            return False, f"differentiator[{i}] 缺 this/other 取值"
    return True, "ok"


def validate(feat, samples):
    # 排除元数据与样本号（样本号里含数字，会和行号黑名单误撞）
    text = json.dumps({k: v for k, v in feat.items()
                       if k != "sample_ids" and not k.startswith("_")},
                      ensure_ascii=False)
    hits = [w for w in build_blacklist(samples) if w.lower() in text.lower()]
    return {
        "is_single_object": isinstance(feat, dict),
        "project_leaks": hits,
        "mutation_target_count": len(feat.get("mutation_target") or []),
        "precondition_count": len(feat.get("precondition") or []),
        "trigger_path_count": len(feat.get("trigger_path") or []),
        "rule": check_rule(feat.get("applicability_rule")),
        "rule_ok": check_rule(feat.get("applicability_rule"))[0],
        "differentiator": check_differentiator(feat),
        "differentiator_ok": check_differentiator(feat)[0],
        "merge_into": feat.get("merge_into"),
    }


def run_one(typ, pat, facts_all, tag):
    ids = [i for i in (pat.get("sample_ids") or []) if i in facts_all]
    samples = [facts_all[i] for i in ids]
    if not samples:
        print(f"  ✗ {pat.get('name')}: 无可用样本")
        return None

    prompt = SYSTEM + "\n\n" + USER.format(
        pattern_json=json.dumps(
            {k: pat.get(k) for k in ("name", "support", "narrative", "trigger_condition", "dimensions")},
            ensure_ascii=False, indent=1),
        n=len(samples),
        samples="\n\n".join(fmt_sample(f) for f in samples),
    )
    print(f"  {pat.get('name')}：{len(samples)} 条样本，prompt {len(prompt)} 字符，调用模型…",
          flush=True)

    last = None
    for attempt in range(3):
        try:
            feat = parse_json(call_llm(prompt, max_tokens=40000))
        except Exception as e:
            last = str(e)[:160]
            print(f"    重试：{last}", flush=True)
            continue
        ok, why = check_rule(feat.get("applicability_rule"))
        if ok:
            # 判据过了还要查 differentiator（必填、必须引用可判定字段）
            dok, dwhy = check_differentiator(feat)
            if dok:
                break
            ok, why = False, dwhy
            last = why
            print(f"    differentiator 不合法（第 {attempt + 1} 次）：{why}", flush=True)
            continue
        last = why
        import tempfile
        dbg = os.path.join("/tmp", f"s4_raw_{tag}_{attempt + 1}.json")
        try:
            json.dump(feat, open(dbg, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
            dbg = f"（原始输出见 {dbg}）"
        except Exception:
            dbg = ""
        print(f"    判据不合法（第 {attempt + 1} 次）：{why} {dbg}", flush=True)
    else:
        # 2026-11-04：失败时必须留下标记，否则 emit_rules 会去读**上次运行残留**的
        # feature_*.json，把旧判据当成这次的结果（实测 uaf-llm04 就这样"复活"过一次）。
        print(f"  ✗ 失败：{last}")
        d = os.path.join(OUT, typ)
        os.makedirs(d, exist_ok=True)
        json.dump({"_source_pattern": pat.get("name"), "reason": last},
                  open(os.path.join(d, f"feature_{tag}.no_rule.json"), "w",
                       encoding="utf-8"), ensure_ascii=False, indent=1)
        return None

    feat["_source_pattern"] = pat.get("name")
    feat["_source_support"] = pat.get("support")
    feat["_input_sample_ids"] = ids
    if not feat.get("sample_ids"):
        feat["sample_ids"] = ids

    v = validate(feat, samples)
    if not v["rule_ok"]:
        # 不判死：保留特征，但把规则标成缺失，下游会据此判 not_found 并写清原因
        feat["_rule_missing_reason"] = v["rule"][1]
        print(f"    ⚠️ 判据缺失：{v['rule'][1]}")
    feat["_validation"] = v

    d = os.path.join(OUT, typ)
    os.makedirs(d, exist_ok=True)
    no_rule = os.path.join(d, f"feature_{tag}.no_rule.json")
    if os.path.isfile(no_rule):
        os.remove(no_rule)
    fp = os.path.join(d, f"feature_{tag}.json")
    json.dump(feat, open(fp, "w", encoding="utf-8"), ensure_ascii=False, indent=1)

    print(f"    ✓ 已写出 {fp}")
    print(f"      feature_name: {feat.get('feature_name')}")
    print(f"      mutation_target: {v['mutation_target_count']} 条")
    print(f"      项目信息泄漏: {'❌ ' + str(v['project_leaks']) if v['project_leaks'] else '✅ 0 处'}")
    return feat


_RUN_STARTED_AT = 0.0
import time



# ─────────────── features.json 由 stage4 自己生成（R11）───────────────
# 以前 `features.json` 是 `run_stage3.py`（已不存在）组装的手写产物，
# `source_pattern` 硬引用 stage3 的分类名。stage3 换判据后 4/5 悬空，判据被丢弃。
# 现在改成：**从本次运行写出的 `feature_p_*.json` 组装**，`feature_id` 由 pattern 顺序派生。
def _legacy_by_pattern(typ):
    """旧 features.json 的 {pattern: id}，只用于追溯（legacy_id）。"""
    fp = os.path.join(OUT, typ, "features.legacy.json")
    if not os.path.isfile(fp):
        return {}
    try:
        d = json.load(open(fp, encoding="utf-8"))
    except Exception:
        return {}
    return {f.get("source_pattern"): f.get("id") for f in (d.get("features") or [])
            if f.get("source_pattern") and f.get("id")}


def emit_features(typ):
    """把本次运行的 feature_p_*.json 汇总成 features.json。返回特征列表。"""
    fin = os.path.join(ROOT, "outputs", "stage3", typ, "final.json")
    order = []
    if os.path.isfile(fin):
        order = [p.get("name") for p in
                 (json.load(open(fin, encoding="utf-8")).get("final_patterns") or [])]
    legacy = _legacy_by_pattern(typ)

    by_pat = {}
    for fp in sorted(glob.glob(os.path.join(OUT, typ, "feature_p_*.json"))):
        if os.path.getmtime(fp) < (_RUN_STARTED_AT - 1):
            continue          # 上次运行的残留
        try:
            d = json.load(open(fp, encoding="utf-8"))
        except Exception:
            continue
        pat = d.get("_source_pattern")
        if pat:
            by_pat[pat] = d

    feats = []
    # 先按 stage3 的顺序编号，剩下的（stage3 里已没有的）排在后面
    ordered = [p for p in order if p in by_pat] + [p for p in by_pat if p not in order]
    for i, pat in enumerate(ordered, 1):
        d = by_pat[pat]
        # 有 legacy_id 就优先沿用它（保住下游按 id 硬编码的规则，如 SHORTLIST）；
        # 新 pattern 才用 pNN。
        fid = legacy.get(pat) or f"{typ}-p{i:02d}"
        f = {
            "id": fid,
            "source_pattern": pat,
            "source_support": d.get("_source_support"),
            "source_samples": d.get("_input_sample_ids") or d.get("sample_ids") or [],
            "feature_name": d.get("feature_name"),
            "precondition": d.get("precondition") or [],
            "trigger_path": d.get("trigger_path") or [],
            "mutation_target": d.get("mutation_target") or [],
            "parameterization": d.get("parameterization") or {},
            "limitations": d.get("limitations") or [],
            "differentiator": d.get("differentiator"),
            "merge_into": d.get("merge_into"),
            "validation": d.get("_validation"),
            "applicability_rule": d.get("applicability_rule"),
        }
        if legacy.get(pat):
            f["legacy_id"] = legacy[pat]
        feats.append(f)

    out = {"_meta": {"crash_type": typ,
                     "generated_by": "pipeline/s4_abstract_features.py::emit_features",
                     "generated_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
                     "n": len(feats),
                     "note": "由本次运行的 feature_p_*.json 组装；feature_id 由 stage3 pattern 顺序派生，"
                             "legacy_id 指向上一个手写版本里的 id（仅追溯用）"},
           "features": feats}
    json.dump(out, open(os.path.join(OUT, typ, "features.json"), "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)
    print(f"  写出 features.json：{len(feats)} 条"
          + (f"（{sum(1 for f in feats if f.get('legacy_id'))} 条有 legacy_id）" if feats else ""))
    return feats

def emit_rules(typ):
    """把 5 个 feature_*.json 的 applicability_rule 汇总成 outputs/stage4/<type>/applicability_rules.json。

    feature_id 来自 features.json 的 source_pattern 映射（features.json 由遗留脚本组装，
    这里只负责把判据按同一个 id 对齐）。
    """
    fpath = os.path.join(OUT, typ, "features.json")
    if not os.path.isfile(fpath):
        print(f"  ⚠️ 找不到 {fpath}，无法对齐 feature_id")
        return None
    id_by_pattern = {(f.get("source_pattern") or ""): f.get("id")
                     for f in json.load(open(fpath, encoding="utf-8"))["features"]}
    rules, missing, unmapped = {}, {}, []
    # 先收集"这次跑失败"的标记，避免把上次残留的 feature_*.json 当成新结果
    failed_pat = {}
    for np_ in sorted(glob.glob(os.path.join(OUT, typ, "feature_*.no_rule.json"))):
        nd = json.load(open(np_, encoding="utf-8"))
        if nd.get("_source_pattern"):
            failed_pat[nd["_source_pattern"]] = nd.get("reason") or "rule_missing"

    # 2026-11-04：加 mtime 时效检查。R8 已经用 sidecar 挡了"本次失败但上次成功"的情况，
    # 但如果 pattern 被改名/换 tag，残留文件仍会被当成这次的结果。这里直接按运行起点过滤。
    _start = globals().get("_RUN_STARTED_AT", 0.0)
    stale = []
    for fp in sorted(glob.glob(os.path.join(OUT, typ, "feature_*.json"))):
        if _start and os.path.getmtime(fp) < _start - 1:
            stale.append(os.path.basename(fp))
            continue
        f = json.load(open(fp, encoding="utf-8"))
        pat = f.get("_source_pattern") or ""
        fid = id_by_pattern.get(pat)
        if not fid:
            # 2026-11-04：原来这里静默 `continue` —— stage3 换了分类法之后，
            # 4 条判据因为 features.json 的 source_pattern 悬空而被丢掉，日志里看不出来。
            unmapped.append(pat)
            continue
        if pat in failed_pat:
            missing[fid] = {"rule_id": fid, "source_pattern": pat, "kind": "rule_missing",
                            "reason": failed_pat[pat]}
            continue
        ok, why = check_rule(f.get("applicability_rule"))
        if ok:
            rules[fid] = {**f["applicability_rule"], "kind": "structural",
                          "source_pattern": pat}
        else:
            missing[fid] = {"rule_id": fid, "source_pattern": pat, "kind": "rule_missing",
                            "reason": why}
    out = {"schema_version": "stage4.applicability_rules.v1",
           "crash_type": typ,
           "_comment": "由 pipeline/s4_abstract_features.py 自动产出；判据由模型从词表里选值，不含函数名/文件名/项目名。",
           "field_vocab": {k: sorted(v) for k, v in RULE_VOCAB.items()},
           "rules": rules,
           "rule_missing": missing,
           # 用的是哪种可证伪校验，引用时必须连这个一起看
           "falsifiability_check": {
               "mode": FALSIFIABILITY_MODE,
               "touchstone_sites": len(TOUCHSTONE_SITES),
               "touchstone_sources": TOUCHSTONE_SOURCES,
               "structurally_fixed": STRUCTURALLY_FIXED,
               "note": ("structural = '字段写了词表真子集' + 不把结构性单值字段计入区分力；"
                        "semantic = 拿真实站点当试金石逐字段去掉看命中集合变不变"
                        "（**只作诊断**：试金石只有正例，会杀掉 llm01）；"
                        "syntactic = 没有试金石时的退化"),
           },
           "provenance": {"emitted_by": "pipeline/s4_abstract_features.py::emit_rules",
                          "emitted_at": __import__("datetime").datetime.now().isoformat(timespec="seconds")}}
    op = os.path.join(OUT, typ, "applicability_rules.json")
    json.dump(out, open(op, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    if unmapped:
        print(f"  ⚠️ {len(unmapped)} 条判据找不到对应的 feature（features.json 的 source_pattern 已过期）: "
              f"{unmapped}", file=sys.stderr, flush=True)
    if stale:
        print(f"  ⚠️ 跳过 {len(stale)} 个上次运行残留的 feature_*.json（mtime 早于本次运行）: {stale}")
    print(f"\n  判据汇总：{len(rules)} 条可用，{len(missing)} 条 rule_missing → {op}")
    for fid, r in rules.items():
        print(f"    ✅ {fid:<12} {json.dumps({k: v for k, v in r.items() if k not in ('kind','source_pattern')}, ensure_ascii=False)[:140]}")
    for fid, r in missing.items():
        print(f"    ⚠️ {fid:<12} rule_missing：{r['reason'][:100]}")
    return out


def main():
    global _RUN_STARTED_AT
    # 2026-11-04 修：原来这一行放在 run_one 循环**之后**，于是本次刚写的 feature_*.json
    # 全部比"运行起点"旧，被当成上次残留跳过 —— 判据汇总变成 0 条。
    import time as _t
    _RUN_STARTED_AT = _t.time()
    ap = argparse.ArgumentParser()
    ap.add_argument("--type", default="uaf")
    ap.add_argument("--pattern", default=None, help="pattern 名（子串匹配）")
    ap.add_argument("--all", action="store_true")
    a = ap.parse_args()

    fin = os.path.join(ROOT, "outputs", "stage3", a.type, "final.json")
    pats = json.load(open(fin, encoding="utf-8")).get("final_patterns") or []
    facts_all = load_facts()

    if a.all:
        targets = pats
    elif a.pattern:
        targets = [p for p in pats if a.pattern in (p.get("name") or "")]
    else:
        print("需要 --pattern 或 --all")
        return 1

    if not targets:
        print(f"找不到匹配的 pattern：{a.pattern}")
        return 1

    for p in targets:
        import hashlib
        tag = re.sub(r"[^0-9A-Za-z]+", "_", p.get("name") or "p").strip("_")[:30] \
              or "p_" + hashlib.md5((p.get("name") or "").encode()).hexdigest()[:6]
        run_one(a.type, p, facts_all, tag)

    # 跑完全部 pattern 后汇总判据（只汇总，不再调模型）
    # 语义可证伪性：先收集所有项目已扫出的站点当试金石
    global TOUCHSTONE_SITES, FALSIFIABILITY_MODE, TOUCHSTONE_SOURCES
    TOUCHSTONE_SITES, TOUCHSTONE_SOURCES = load_touchstone()
    # 门禁默认 structural（= R8 的语法校验 + 不把"结构性单值字段"计入区分力）。
    # semantic 只作为诊断：试金石只有正例（都是扫描器已经筛过的 UAF 形态），
    # 所以任何**正确描述**这批站点的判据都会被判"排除不了东西"——实测 llm01 与 llm05
    # 会被杀掉，而 llm01 是唯一能落地的特征。用 --falsifiability semantic 可复现那个结果。
    FALSIFIABILITY_MODE = "structural" if TOUCHSTONE_SITES else "syntactic"
    if TOUCHSTONE_SITES:
        print(f"  可证伪校验：{FALSIFIABILITY_MODE}（试金石 {len(TOUCHSTONE_SITES)} 个站点，来自 "
              f"{len(TOUCHSTONE_SOURCES)} 个项目；结构性单值字段不计入：{sorted(STRUCTURALLY_FIXED)}）")
    else:
        print("  可证伪校验：syntactic（没有试金石站点，退化）")

    emit_features(a.type)      # 先由本次运行的 feature_p_*.json 组装 features.json
    emit_rules(a.type)
    return 0


if __name__ == "__main__":
    sys.exit(main())

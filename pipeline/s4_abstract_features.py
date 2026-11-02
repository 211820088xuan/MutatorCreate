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
  "sample_ids": ["本条特征覆盖了哪些样本"]
}}

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
    for _ in range(3):
        try:
            feat = parse_json(call_llm(prompt, max_tokens=40000))
            break
        except Exception as e:
            last = str(e)[:160]
            print(f"    重试：{last}", flush=True)
    else:
        print(f"  ✗ 失败：{last}")
        return None

    feat["_source_pattern"] = pat.get("name")
    feat["_source_support"] = pat.get("support")
    feat["_input_sample_ids"] = ids
    if not feat.get("sample_ids"):
        feat["sample_ids"] = ids

    v = validate(feat, samples)
    feat["_validation"] = v

    d = os.path.join(OUT, typ)
    os.makedirs(d, exist_ok=True)
    fp = os.path.join(d, f"feature_{tag}.json")
    json.dump(feat, open(fp, "w", encoding="utf-8"), ensure_ascii=False, indent=1)

    print(f"    ✓ 已写出 {fp}")
    print(f"      feature_name: {feat.get('feature_name')}")
    print(f"      mutation_target: {v['mutation_target_count']} 条")
    print(f"      项目信息泄漏: {'❌ ' + str(v['project_leaks']) if v['project_leaks'] else '✅ 0 处'}")
    return feat


def main():
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
    return 0


if __name__ == "__main__":
    sys.exit(main())

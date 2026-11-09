#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""s3_extract_patterns.py —— 阶段 3：切批 + 调用 LLM + 校验 + 跨批合并。

模型：deepseek-flash（DeepSeek-V4.1-Flash，1M 上下文）
API ：https://api.deepseek.com/v1/chat/completions

用法：
  python3 s3_extract_patterns.py prepare    # 切批，生成每批的完整 prompt（样本内联）
  python3 s3_extract_patterns.py run        # 并发调用 LLM，产出 batch_*.json
  python3 s3_extract_patterns.py check      # 校验 batch_*.json
  python3 s3_extract_patterns.py merge      # 汇总每类的批级结果 -> merge_input.json
  python3 s3_extract_patterns.py runmerge   # 调用 LLM 做跨批合并 -> final.json
  python3 s3_extract_patterns.py all        # prepare -> run -> check -> merge -> runmerge

产物：
  outputs/stage3/<type>/input/batch_NNN.json   每批样本
  outputs/stage3/<type>/prompt/batch_NNN.md    每批完整 prompt
  outputs/stage3/<type>/batch_NNN.json         每批 LLM 输出
  outputs/stage3/<type>/merge_input.json       跨批合并的输入
  outputs/stage3/<type>/final.json             类型级最终形态
  outputs/stage3/manifest.json                 批次清单
"""
from __future__ import annotations
import json, os, ssl, sys, time, glob, threading, collections
import urllib.request, urllib.error
from concurrent.futures import ThreadPoolExecutor, as_completed

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)   # mutator_create/
TOP = os.path.dirname(ROOT)    # mutator_create/
A = os.path.join(ROOT, "artifacts")
OUT = os.path.join(ROOT, "outputs", "stage3")
BATCH = 15
API = "https://api.deepseek.com/v1/chat/completions"
MODEL = os.environ.get("STAGE2_MODEL", "deepseek-flash")
MAXW = int(os.environ.get("STAGE2_WORKERS", "5"))
RETRY = 2
LOCK = threading.Lock()

TYPES = {
    "heap-use-after-free": "uaf",
    "heap-buffer-overflow": "hbo",
    "stack-buffer-overflow": "stack",
    "global-buffer-overflow": "global",
}

MECHANISM = {
"heap-use-after-free": """UAF 的必要条件链：
- N1 对象是堆分配
- N2 存在 free(p) 调用
- N3 p 在 free 之后被解引用（执行顺序）
- N4 free 与解引用之间 p 未被重新赋值
- N5 free 与解引用之间 p 未重新 malloc
- N6 free 的实参是 p 本身（非 p+off）
- N7 解引用对象与 free 对象是同一对象（含别名）
- N8 free 与解引用在同一可达路径上
- N9 p 解引用时未被置空
- N10 解引用发生在 free 生效后（非同一语句）""",

"heap-buffer-overflow": """HBO 的必要条件链：
- N1 访问对象是堆分配
- N2 一次访问的字节宽度
- N3 缓冲区大小 S
- N4 是否存在边界检查
- N5 访问基址是 B 还是 B+off
- N6 下标/长度表达式及其来源
- N7 元素类型（int* vs char*）
- N8 下标运算是否有整数溢出（i*4）
- N9 下标有无符号
- N10 分配大小是否输入控制
- N11 是否循环内多次访问累积越界""",

"stack-buffer-overflow": """stack-BOF 的必要条件链：
- N1 对象是函数内栈数组
- N2 数组声明维度
- N3 访问宽度
- N4 是否 VLA（char buf[n]，n 来自输入）
- N5 数组所在栈帧
- N6 写入形式：memcpy 还是逐字节循环
- N7 栈增长方向 + 覆盖对象
- N8 是否经由 alloca / 变长分配""",

"global-buffer-overflow": """global-BOF 的必要条件链：
- N1 访问对象是全局数组/表
- N2 访问宽度
- N3 下标表达式及其来源
- N4 常量表 vs 可变全局缓冲区
- N5 下标是单字节还是多字节
- N6 表长是否是 2 的幂（256/512）
- N7 同一输入索引是否访问多个全局表""",
}

SYSTEM = """你是一名内存安全崩溃分析专家，专门研究模糊测试发现的崩溃的成因机制。
你的读者是后续要设计"变异策略"的工程师——他们需要知道：这类崩溃是怎么被触发的，以及哪个输入字段控制触发的关键环节。

你的任务：从一批同类型的崩溃样本中，提取它们共享的"机制形态"（pattern）。

严格遵守以下规则：
1. 只使用输入数据中存在的字段，绝对不要推测或编造。
2. 如果某个条件在样本中为 null（数据缺失），在该 pattern 的 evidence 中标注 "unknown:<字段名>"，不要当作 false。
3. 每个 pattern 必须给出 support（该 pattern 的样本数）和 sample_ids（具体样本 ID）。
4. 无法归入任何 pattern 的样本，必须原样列在 unclassified 中，不要强行归类。
5. 输出的 JSON 必须严格符合给定 schema，不要添加额外字段，不要用 markdown 包裹。
6. pattern 数量控制在 2-5 个。
7. 每个 pattern 的 name 用中文，不超过 12 个字。
8. narrative 用 2-4 句话说清"这个 pattern 的崩溃是怎么发生的"，必须引用具体样本的函数名、行号或字段值作为依据。
9. trigger_condition 必须回答"改哪个输入、让什么条件成立，就能触发"，如果数据不足以回答，写 "unknown" 并说明缺什么。
10. 当 support > 1 时：narrative 要描述这 N 条的共同机制（可用 2-3 条做例证）；evidence 要用跨样本统计的写法（如 "7/7 样本..."、"5/7 样本...（例外：xxx、yyy）"）；dimensions 取多数值并注明例外。"""

SCHEMA = """{
  "crash_type": "string",
  "batch_id": "string",
  "sample_count": number,
  "patterns": [
    {
      "name": "string",
      "narrative": "string",
      "support": number,
      "sample_ids": ["string"],
      "trigger_condition": {
        "where_alloc": "string",
        "where_free": "string",
        "where_use": "string",
        "what_input_controls": "string",
        "minimal_requirement": "string"
      },
      "dimensions": {
        "alloc_kind": "heap | stack | global | unknown",
        "free_before_use": "true | false | unknown",
        "free_and_use_same_function": "true | false | unknown",
        "reassigned_between": "true | false | unknown",
        "in_loop": "true | false | unknown",
        "access_kind": "read | write | call | unknown",
        "free_cross_function": "true | false | unknown",
        "cross_frame_count": "number | unknown"
      },
      "dimension_distributions": {"维度名": {"取值": "样本数"}},
      "evidence": ["string"],
      "confidence": "high | medium | low"
    }
  ],
  "unclassified": [{"sample_id": "string", "reason": "string", "missing_fields": ["string"]}],
  "batch_observations": "string"
}"""

USER_TMPL = """## 崩溃类型
{crash_type}

## 该类型的机制背景
{mechanism}

## 样本（共 {n} 条，完整 facts + interpretation）

{samples_json}

## 任务
1. 阅读全部样本，按"崩溃在成因链上的形态"分组。
2. 每组给出：name、narrative、trigger_condition、support、sample_ids、dimensions、evidence、confidence。
   **样本里的 `measured_dims` 是 stage2 实测出来的值，不是让你猜的**：
   `reassigned_between` / `cross_frame_count` 直接照抄（`null` 才写 unknown），
   `cross_frame_exact=false` 表示跳数算不出精确值，此时 `cross_frame_count` 写 unknown。
3. 无法归类的样本放入 unclassified，并说明缺什么数据。

## 输出 JSON schema
{schema}

直接输出 JSON，不要任何解释文字。"""

MERGE_SYSTEM = """你是一名内存安全崩溃分析的汇总专家。

你的任务：把多份"批级分析结果"合并成一份"类型级最终形态清单"。

严格遵守以下规则：
1. 【合并原则】语义相同的 pattern 必须合并。判断相同看三件事：
   a) 触发链相同（分配→释放→使用 发生在哪类代码结构里）
   b) 机制维度相同。**判据只能用有区分力的维度**：
      `free_and_use_same_function`、`reassigned_between`、`in_loop`、`free_cross_function`。
      **不要用 `free_before_use` 当判据**（它对 UAF 恒为 true，等于没有约束）；
      **也不要主要靠 `cross_frame_count`**（它有大量 unknown，把 unknown 当成一个"值"
      去比较，会把互不相关的样本错误地归到一起）。
   c) narrative 描述的是同一类机制
2. 【合并后处理】support = 被合并 pattern 的 support 之和；sample_ids = 并集；
   dimensions 取多数值，例外写进 evidence；evidence 用跨样本统计写法。
   **除了众数，还要给出每个维度的分布**，放在 `dimension_distributions` 里，
   形如 `{"access_kind": {"read": 3, "write": 1}}`。只给众数会把
   "3 个读 1 个写" 压成 "read"，信息就丢了。
3. 【丢弃原则】合并后 support < 2 的形态放进 low_support（不删除，单独列出）。
4. 【保留原样】无法判断是否相同的 pattern，不要强行合并，单独保留。
5. 【不许编造】只用输入里有的信息。
6. 最终形态数控制在 2-6 个（不含 low_support）。
7. 输出必须是严格 JSON，不要用 markdown 包裹。
8. name 用中文，≤12 字。"""

MERGE_SCHEMA = """{
  "crash_type": "string",
  "total_batches": number,
  "total_input_patterns": number,
  "final_patterns": [
    {
      "name": "string",
      "narrative": "string",
      "support": number,
      "sample_ids": ["string"],
      "merged_from": ["string"],
      "trigger_condition": {
        "where_alloc": "string", "where_free": "string", "where_use": "string",
        "what_input_controls": "string", "minimal_requirement": "string"
      },
      "dimensions": {
        "alloc_kind": "heap | stack | global | unknown",
        "free_before_use": "true | false | unknown",
        "free_and_use_same_function": "true | false | unknown",
        "reassigned_between": "true | false | unknown",
        "in_loop": "true | false | unknown",
        "access_kind": "read | write | call | unknown",
        "free_cross_function": "true | false | unknown",
        "cross_frame_count": "number | unknown"
      },
      "evidence": ["string"],
      "confidence": "high | medium | low"
    }
  ],
  "low_support": [{"name": "string", "support": number, "sample_ids": ["string"], "reason": "string"}],
  "unclassified": [{"sample_id": "string", "reason": "string"}],
  "merge_notes": "string"
}"""

MERGE_USER = """## 崩溃类型
{crash_type}

## 批级分析结果（共 {n} 批，合计 {m} 个 pattern）

{merge_json}

## 任务
1. 把所有批次里的 pattern 收集起来，按语义合并。
2. 合并后重新计算 support 和 sample_ids。
3. support < 2 的形态放进 low_support。
4. 输出 2-6 个最终形态。

## 输出 JSON schema
{schema}

直接输出 JSON，不要任何解释文字。"""


# ── 基础工具 ──────────────────────────────────


# ─────────────── 合并后硬校验（R10 步骤 3）───────────────
# 判据换掉之后仍可能有两组维度向量完全相同——那说明它们本来就是一回事。
# 强制合并（而不是当成两条输出），并记下 merged_from。
_DEDUP_DIMS = ("free_and_use_same_function", "reassigned_between",
               "in_loop", "free_cross_function")


def dedupe_vectors(patterns, dims=_DEDUP_DIMS):
    """维度向量完全相同的 pattern 强制合并。返回 (patterns, merged_groups)。"""
    groups, order = {}, []
    for p in patterns or []:
        d = p.get("dimensions") or {}
        key = tuple(str(d.get(k, "unknown")).lower() for k in dims)
        if key not in groups:
            groups[key] = []
            order.append(key)
        groups[key].append(p)
    out, merged = [], []
    for key in order:
        g = groups[key]
        if len(g) == 1:
            out.append(g[0])
            continue
        base = dict(g[0])
        base["support"] = sum(x.get("support") or 0 for x in g)
        ids = []
        for x in g:
            for i in (x.get("sample_ids") or []):
                if i not in ids:
                    ids.append(i)
        base["sample_ids"] = ids
        base["merged_from"] = [x.get("name") for x in g]
        ev = []
        for x in g:
            for e in (x.get("evidence") or []):
                if e not in ev:
                    ev.append(e)
        base["evidence"] = ev
        base["name"] = " / ".join(x.get("name") or "?" for x in g)
        out.append(base)
        merged.append({"dims": dict(zip(dims, key)), "names": base["merged_from"],
                       "support": base["support"]})
    return out, merged


def get_key():
    k = os.environ.get("DEEPSEEK_API_KEY")
    if k:
        return k
    try:
        for ln in open("/root/.bashrc", encoding="utf-8", errors="ignore"):
            if ln.startswith("export DEEPSEEK_API_KEY="):
                return ln.split("=", 1)[1].strip().strip('"').strip("'")
    except Exception:
        pass
    raise RuntimeError("找不到 DEEPSEEK_API_KEY")


def call_llm(prompt, max_tokens=40000, temperature=0.1, model=None):
    key = get_key()
    body = json.dumps({
        "model": model or MODEL,
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": max_tokens,
        "temperature": temperature,
    }, ensure_ascii=False).encode("utf-8")
    req = urllib.request.Request(API, data=body, headers={
        "Authorization": f"Bearer {key}",
        "Content-Type": "application/json",
    })
    ctx = ssl.create_default_context()
    with urllib.request.urlopen(req, timeout=900, context=ctx) as r:
        d = json.loads(r.read().decode("utf-8"))
    ch = d["choices"][0]
    msg = ch.get("message") or {}
    content = msg.get("content") or ""
    fr = ch.get("finish_reason")
    if fr == "length":
        raise RuntimeError(f"finish_reason=length（max_tokens 被耗尽），"
                           f"reasoning 占 {len(msg.get('reasoning_content') or '')} 字符")
    if not content.strip():
        raise RuntimeError(f"content 为空（finish_reason={fr}，"
                           f"reasoning 占 {len(msg.get('reasoning_content') or '')} 字符）")
    return content


def strip_fence(txt):
    t = txt.strip()
    if t.startswith("```"):
        t = t.split("\n", 1)[1] if "\n" in t else t
        if t.rstrip().endswith("```"):
            t = t.rstrip()[:-3]
    return t.strip()


def parse_json(txt):
    t = strip_fence(txt)
    try:
        return json.loads(t)
    except Exception:
        i, j = t.find("{"), t.rfind("}")
        if i >= 0 and j > i:
            return json.loads(t[i:j + 1])
        raise



# ─────────────── 实测维度（R10 步骤 2）───────────────
# stage3 原来让模型**猜** dimensions，但其中两个维度 stage2 已经算出来了：
#   · reassigned_between  —— `s2_3_interpretation._reassign_between()` 的结果，
#                            121 条 UAF 里 41 条有确定值（True 25 / False 16 / None 80）
#   · cross_frame_count   —— 释放函数与使用函数之间隔几跳调用边
# 这里把实测值放进样本上下文（键名 `measured_dims`），并明确告诉模型"这是实测的，不要猜"。
# **不重算 stage2 的逻辑**：直接读 interpretation.findings。
_GRAPH_CACHE = {}


def _call_graphs():
    """{project: {(caller, callee)}} —— 只有有 cpg_dump.tsv 的项目才有。"""
    if _GRAPH_CACHE:
        return _GRAPH_CACHE
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    # ① 批量抓好的调用边缓存（artifacts/call_edges/<project>_<pin>.tsv，按项目合并）
    for tsv in glob.glob(os.path.join(root, "artifacts", "call_edges", "*.tsv")):
        proj = os.path.basename(tsv).rsplit("_", 1)[0]
        edges = _GRAPH_CACHE.setdefault(proj, set())
        try:
            for ln in open(tsv, encoding="utf-8", errors="replace"):
                t = ln.rstrip("\n").split("\t")
                if len(t) >= 3 and t[0] == "@@E":
                    edges.add((t[1], t[2]))
        except Exception:
            continue
    # ② 单项目工作区里的 dump（更权威，覆盖同名键）
    for ctxp in glob.glob(os.path.join(root, "projects", "*", "source_context.json")):
        d = os.path.join(os.path.dirname(ctxp), "cpg_dump.tsv")
        if not os.path.isfile(d):
            continue
        try:
            proj = json.load(open(ctxp, encoding="utf-8")).get("project")
        except Exception:
            continue
        edges = set()
        try:
            for ln in open(d, encoding="utf-8", errors="replace"):
                t = ln.rstrip("\n").split("\t")
                if t[0] == "@@C" and len(t) >= 4:
                    for c in t[3].split("|"):
                        if c:
                            edges.add((t[2], c))
        except Exception:
            continue
        if proj:
            _GRAPH_CACHE[proj] = edges
    return _GRAPH_CACHE


def _hops(proj, a, b, limit=8):
    """a 与 b 在**调用图上的最短距离**（无向）；判不出返回 None。

    为什么是无向：UAF 的"释放"和"使用"通常在**兄弟函数**里（都由更上层调用），
    有向 BFS 从 free_fn 出发根本到不了 use_fn（实测 121 条里只有 16 条能到）。
    无向距离回答的是"这两个函数在调用图上隔多远"，是个有定义的结构量。
    """
    edges = _call_graphs().get(proj)
    if not edges or not a or not b:
        return None
    if a == b:
        return 0
    # 邻接索引（第一次用时建，缓存到图里；边数上万时全表扫描太慢）
    key = ("_adj", id(edges))
    adj = _GRAPH_CACHE.get(key)
    if adj is None:
        adj = {}
        for (x, y) in edges:
            adj.setdefault(x, set()).add(y)
            adj.setdefault(y, set()).add(x)      # 无向
        _GRAPH_CACHE[key] = adj
    nxt, seen, d = {a}, {a}, 0
    while nxt and d < limit:
        d += 1
        cur = set()
        for x in nxt:
            for y in adj.get(x, ()):  # noqa: E501
                if y in seen:
                    continue
                if y == b:
                    return d
                seen.add(y)
                cur.add(y)
        nxt = cur
    return None


def measure_dims(f):
    """从 stage2 的产物里取实测维度（0 LLM）。"""
    osv = f.get("osv_id") or ""
    interp = {}
    ip = os.path.join(A, "interpretation", osv, "interpretation.json")
    if os.path.isfile(ip):
        try:
            interp = json.load(open(ip, encoding="utf-8"))
        except Exception:
            interp = {}
    fi = interp.get("findings") or {}

    # 只用 interpretation.findings 这一个来源：121 条 UAF 上是 None 80 / True 25 / False 16。
    # （另外还有一个 free_related.reassign_between 回退源，挂上会把一条 None 变成 False，
    #   变成 79/25/17 —— 不挂，保持与 stage2 的正式产物一致。）
    rb = fi.get("reassigned_between")
    rb = None if rb is None else bool(rb)

    free = [x for x in (f.get("sites") or []) if x.get("kind") == "free"]
    free_fn = (free[0].get("fn") if free else None) or fi.get("free_fn")
    use_fn = ((f.get("crash") or {}).get("site") or {}).get("fn")
    xfunc = fi.get("free_cross_function")

    if free_fn and use_fn and free_fn == use_fn:
        cfc, exact = 0, True
    elif xfunc is False:
        cfc, exact = 0, True
    else:
        h = _hops(f.get("project"), free_fn, use_fn)
        cfc, exact = (h, True) if h is not None else (None, False)
    return {"reassigned_between": rb, "cross_frame_count": cfc,
            "cross_frame_exact": exact, "free_cross_function": xfunc,
            "free_fn": free_fn, "use_fn": use_fn}


def load_facts():
    """读 facts/<OSV>/facts.json（唯一存储，步骤5 会回写 deep/report_extra）"""
    out = []
    for p in sorted(glob.glob(os.path.join(A, "facts", "*", "facts.json"))):
        try:
            out.append(json.load(open(p, encoding="utf-8")))
        except Exception:
            continue
    return out


def load_manifest():
    fp = os.path.join(OUT, "json", "manifest.json")
    if not os.path.isfile(fp):
        return None
    return json.load(open(fp, encoding="utf-8"))


# ── prepare ──────────────────────────────────

def prepare():
    facts = load_facts()
    by = collections.defaultdict(list)
    for f in facts:
        t = f.get("crash_type")
        if t in TYPES:
            by[t].append(f)

    manifest = []
    for t, tag in TYPES.items():
        rows = by.get(t) or []
        if not rows:
            print(f"  {t}: 无样本，跳过", flush=True)
            continue
        rows.sort(key=lambda r: r.get("osv_id") or "")
        d_in = os.path.join(OUT, tag, "input")
        d_pr = os.path.join(OUT, tag, "prompt")
        os.makedirs(d_in, exist_ok=True)
        os.makedirs(d_pr, exist_ok=True)

        nb = (len(rows) + BATCH - 1) // BATCH
        for i in range(nb):
            chunk = []
            for r in rows[i * BATCH:(i + 1) * BATCH]:
                r = dict(r)
                r["measured_dims"] = measure_dims(r)   # 实测，不是模型猜的
                chunk.append(r)
            bid = f"{tag}-{i+1:03d}"
            fp_in = os.path.join(d_in, f"batch_{i+1:03d}.json")
            with open(fp_in, "w", encoding="utf-8") as fh:
                json.dump(chunk, fh, ensure_ascii=False, indent=1)
            prompt = SYSTEM + "\n\n" + USER_TMPL.format(
                crash_type=t, mechanism=MECHANISM[t],
                n=len(chunk),
                samples_json=json.dumps(chunk, ensure_ascii=False, indent=1),
                schema=SCHEMA)
            fp_pr = os.path.join(d_pr, f"batch_{i+1:03d}.md")
            with open(fp_pr, "w", encoding="utf-8") as fh:
                fh.write(prompt)
            manifest.append({
                "batch_id": bid, "crash_type": t, "type_tag": tag,
                "index": i + 1, "n_samples": len(chunk),
                "samples_file": os.path.abspath(fp_in),
                "prompt_file": os.path.abspath(fp_pr),
                "output_file": os.path.abspath(
                    os.path.join(OUT, tag, f"batch_{i+1:03d}.json")),
                "sample_ids": [r.get("osv_id") for r in chunk],
            })
        print(f"  {t}: {len(rows)} 条 → {nb} 批", flush=True)

    os.makedirs(OUT, exist_ok=True)
    fp = os.path.join(OUT, "json", "manifest.json")
    with open(fp, "w", encoding="utf-8") as fh:
        json.dump(manifest, fh, ensure_ascii=False, indent=1)
    print(f"\n共 {len(manifest)} 批 → {fp}", flush=True)
    return 0


# ── run ──────────────────────────────────

def run():
    m = load_manifest()
    if not m:
        print("没有 manifest，先跑 prepare")
        return 1
    todo = [x for x in m if not os.path.isfile(x["output_file"])]
    print(f"待跑 {len(todo)} / {len(m)} 批，并发 {MAXW}，模型 {MODEL}", flush=True)
    if not todo:
        return 0

    def work(x):
        prompt = open(x["prompt_file"], encoding="utf-8").read()
        last = None
        for attempt in range(RETRY + 1):
            try:
                txt = call_llm(prompt, max_tokens=40000)
                d = parse_json(txt)
                d.setdefault("batch_id", x["batch_id"])
                with open(x["output_file"], "w", encoding="utf-8") as fh:
                    json.dump(d, fh, ensure_ascii=False, indent=1)
                return True, None
            except Exception as e:
                last = str(e)[:200]
                time.sleep(3 * (attempt + 1))
        return False, last

    ok = fail = 0
    t0 = time.time()
    with ThreadPoolExecutor(max_workers=MAXW) as ex:
        futs = {ex.submit(work, x): x for x in todo}
        for i, fut in enumerate(as_completed(futs), 1):
            x = futs[fut]
            good, err = fut.result()
            with LOCK:
                if good:
                    ok += 1
                else:
                    fail += 1
            print(f"  [{i}/{len(todo)}] {x['batch_id']:<12}"
                  f"{'OK' if good else 'FAIL: ' + str(err)}"
                  f"  用时 {(time.time()-t0)/60:.1f}分", flush=True)
    print(f"\n完成: 成功 {ok} / 失败 {fail}", flush=True)
    return 0 if fail == 0 else 2


# ── check ──────────────────────────────────

def check():
    m = load_manifest()
    if not m:
        print("没有 manifest，先跑 prepare")
        return 1
    ok = bad = missing = 0
    problems = []
    for x in m:
        f = x["output_file"]
        if not os.path.isfile(f):
            missing += 1
            continue
        try:
            d = json.load(open(f, encoding="utf-8"))
        except Exception as e:
            bad += 1
            problems.append((x["batch_id"], f"JSON 解析失败: {e}"))
            continue
        errs = []
        pats = d.get("patterns") or []
        unc = d.get("unclassified") or []
        if not (1 <= len(pats) <= 5):
            errs.append(f"pattern 数 {len(pats)} 不在 1-5")
        tot = sum(p.get("support") or 0 for p in pats) + len(unc)
        if tot != x["n_samples"]:
            errs.append(f"覆盖 {tot} != 样本数 {x['n_samples']}")
        ids = set(x["sample_ids"])
        for p in pats:
            if len(p.get("name") or "") > 12:
                errs.append(f"name 过长: {p.get('name')}")
            if len(p.get("narrative") or "") < 30:
                errs.append(f"narrative 过短: {p.get('name')}")
            tc = p.get("trigger_condition") or {}
            for k in ("where_alloc", "where_free", "where_use",
                      "what_input_controls", "minimal_requirement"):
                if not tc.get(k):
                    errs.append(f"{p.get('name')} 缺 trigger_condition.{k}")
            for sid in (p.get("sample_ids") or []):
                if sid not in ids:
                    errs.append(f"非法 sample_id {sid}")
                    break
        if errs:
            bad += 1
            problems.append((x["batch_id"], "; ".join(errs[:3])))
        else:
            ok += 1
    print(f"校验: 通过 {ok} / 失败 {bad} / 缺失 {missing}（共 {len(m)}）", flush=True)
    for bid, msg in problems[:20]:
        print(f"  ✗ {bid}: {msg}", flush=True)
    return 0 if (bad == 0 and missing == 0) else 2


# ── merge ──────────────────────────────────

def merge():
    m = load_manifest()
    if not m:
        print("没有 manifest，先跑 prepare")
        return 1
    by = collections.defaultdict(list)
    for x in m:
        if os.path.isfile(x["output_file"]):
            try:
                by[x["crash_type"]].append(json.load(open(x["output_file"], encoding="utf-8")))
            except Exception:
                pass
    for t, tag in TYPES.items():
        if not by.get(t):
            continue
        d = os.path.join(OUT, tag)
        fp2 = os.path.join(d, "merge_input.json")
        with open(fp2, "w", encoding="utf-8") as fh:
            json.dump(by[t], fh, ensure_ascii=False, indent=1)
        n_pat = sum(len(b.get("patterns") or []) for b in by[t])
        print(f"  {t}: {len(by[t])} 批 → {n_pat} 个 pattern → {fp2}", flush=True)
    return 0


def runmerge():
    for t, tag in TYPES.items():
        fp = os.path.join(OUT, tag, "merge_input.json")
        out = os.path.join(OUT, tag, "final.json")
        if not os.path.isfile(fp):
            print(f"  {t}: 无 merge_input，跳过", flush=True)
            continue
        if os.path.isfile(out):
            print(f"  {t}: final.json 已存在，跳过", flush=True)
            continue
        batches = json.load(open(fp, encoding="utf-8"))
        n_pat = sum(len(b.get("patterns") or []) for b in batches)
        prompt = MERGE_SYSTEM + "\n\n" + MERGE_USER.format(
            crash_type=t, n=len(batches), m=n_pat,
            merge_json=json.dumps(batches, ensure_ascii=False, indent=1),
            schema=MERGE_SCHEMA)
        last = None
        for attempt in range(RETRY + 1):
            try:
                txt = call_llm(prompt, max_tokens=40000)
                d = parse_json(txt)
                # 合并后硬校验：维度向量仍完全相同的，强制合并（不许当成两条输出）
                pats, merged = dedupe_vectors(d.get("final_patterns") or [])
                n_before = len(d.get("final_patterns") or [])
                d["final_patterns"] = pats
                d["_dedupe"] = {"before": n_before, "after": len(pats),
                                "merged_groups": merged,
                                "dims_used": list(_DEDUP_DIMS)}
                with open(out, "w", encoding="utf-8") as fh:
                    json.dump(d, fh, ensure_ascii=False, indent=1)
                print(f"  {t}: {len(batches)} 批 / {n_pat} pattern → "
                      f"{n_before} 个最终形态 → 去重后 {len(pats)} 个"
                      + (f"（强制合并 {len(merged)} 组）" if merged else ""), flush=True)
                last = None
                break
            except Exception as e:
                last = str(e)[:200]
                time.sleep(5 * (attempt + 1))
        if last:
            print(f"  {t}: FAIL {last}", flush=True)
    return 0


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "prepare"
    fns = {"prepare": prepare, "run": run, "check": check,
           "merge": merge, "runmerge": runmerge}
    if cmd == "all":
        for c in ["prepare", "run", "check", "merge", "runmerge"]:
            print(f"\n===== {c} =====", flush=True)
            rc = fns[c]()
            if c == "check" and rc != 0:
                print("校验未通过，仍继续 merge/runmerge（结果需人工复核）", flush=True)
        sys.exit(0)
    if cmd not in fns:
        print(__doc__)
        sys.exit(1)
    sys.exit(fns[cmd]())

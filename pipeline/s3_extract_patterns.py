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
        "cross_frame_count": "number | unknown"
      },
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
3. 无法归类的样本放入 unclassified，并说明缺什么数据。

## 输出 JSON schema
{schema}

直接输出 JSON，不要任何解释文字。"""

MERGE_SYSTEM = """你是一名内存安全崩溃分析的汇总专家。

你的任务：把多份"批级分析结果"合并成一份"类型级最终形态清单"。

严格遵守以下规则：
1. 【合并原则】语义相同的 pattern 必须合并。判断相同看三件事：
   a) 触发链相同（分配→释放→使用 发生在哪类代码结构里）
   b) 机制维度相同（至少 free_before_use、free_and_use_same_function 一致）
   c) narrative 描述的是同一类机制
2. 【合并后处理】support = 被合并 pattern 的 support 之和；sample_ids = 并集；
   dimensions 取多数值，例外写进 evidence；evidence 用跨样本统计写法。
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
    fp = os.path.join(OUT, "manifest.json")
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
            chunk = rows[i * BATCH:(i + 1) * BATCH]
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
    fp = os.path.join(OUT, "manifest.json")
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
                with open(out, "w", encoding="utf-8") as fh:
                    json.dump(d, fh, ensure_ascii=False, indent=1)
                print(f"  {t}: {len(batches)} 批 / {n_pat} pattern → "
                      f"{len(d.get('final_patterns') or [])} 个最终形态", flush=True)
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

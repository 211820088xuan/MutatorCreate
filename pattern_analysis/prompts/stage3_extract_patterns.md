# Stage 3 Prompt：从同类崩溃中提取共性形态

> v2 相对 v1 的两处改动：
> 1. **输入**：改用完整 facts（14 字段）+ 完整 interpretation（findings/missing/reasoning/confidence）
> 2. **输出**：新增 `narrative`（自由描述）和 `trigger_condition`（触发条件），原 7 个维度降为辅助索引
>
> 调用模型：`provider=deepseek, model=deepseek-flash`

---

## System Prompt

```
你是一名内存安全崩溃分析专家，专门研究模糊测试发现的崩溃的成因机制。
你的读者是后续要设计"变异策略"的工程师——他们需要知道：这类崩溃是怎么被触发的，
以及哪个输入字段控制触发的关键环节。

你的任务：从一批同类型的崩溃样本中，提取它们共享的"机制形态"（pattern）。

严格遵守以下规则：

1. 只使用输入数据中存在的字段，绝对不要推测或编造。
2. 如果某个条件在样本中为 null（数据缺失），在该 pattern 的 evidence 中标注
   "unknown:<字段名>"，不要当作 false。
3. 每个 pattern 必须给出 support（该 pattern 的样本数）和 sample_ids（具体样本 ID）。
4. 无法归入任何 pattern 的样本，必须原样列在 unclassified 中，不要强行归类。
5. 输出的 JSON 必须严格符合给定 schema，不要添加额外字段，不要用 markdown 包裹。
6. pattern 数量控制在 2-5 个。如果只发现 1 种，就输出 1 种；不要为了凑数拆分。
7. 每个 pattern 的 name 用中文，不超过 12 个字。
8. narrative 用 2-4 句话说清"这个 pattern 的崩溃是怎么发生的"，必须引用具体样本的
   函数名、行号或字段值作为依据。
9. trigger_condition 必须回答"改哪个输入、让什么条件成立，就能触发"，
   如果数据不足以回答，写 "unknown" 并说明缺什么。
```

---

## User Prompt 模板

```
## 崩溃类型
{{CRASH_TYPE}}

## 该类型的机制背景
{{MECHANISM_BACKGROUND}}

## 样本（共 {{N}} 条，每条包含完整 facts 和 interpretation）

{{SAMPLES_JSON}}

## 任务

1. 阅读全部样本，按"崩溃在成因链上的形态"分组。
2. 每组给出：
   - name：形态名称（中文，≤12 字）
   - narrative：2-4 句话描述这个形态的崩溃是怎么发生的（必须引用具体函数名/行号/字段值）
   - trigger_condition：触发这个形态需要满足什么（见 schema）
   - support / sample_ids / evidence / confidence
   - dimensions：7 个固定维度的取值（作为辅助索引）
3. 无法归类的样本放入 unclassified，并说明缺什么数据。

## 输出 JSON schema

{
  "crash_type": "string",
  "batch_id": "{{BATCH_ID}}",
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
  "unclassified": [
    {"sample_id": "string", "reason": "string", "missing_fields": ["string"]}
  ],
  "batch_observations": "string"
}
```

---

## 字段含义

### trigger_condition 的 5 个字段

| 字段 | 要回答的问题 | 数据来源 |
|---|---|---|
| `where_alloc` | 对象在哪里分配（哪个阶段/哪个函数） | `alloc.api` / `alloc.site.fn` / `call_chain` |
| `where_free` | 在哪里被释放 | `sites(kind=free).fn` / `call_chain` |
| `where_use` | 在哪里被（错误地）使用 | `crash.site` / `call_chain` |
| `what_input_controls` | 哪个输入参数控制了这个路径 | `input_reachability` + 推断 |
| `minimal_requirement` | 最小触发条件是什么 | 综合上述 |

### dimensions 的 7 个字段（辅助索引）

| 维度 | 从哪个字段取 |
|---|---|
| `alloc_kind` | `entity.storage` / `alloc.api` |
| `free_before_use` | `interpretation.findings.crash_after_free` |
| `free_and_use_same_function` | `interpretation.findings.free_cross_function` 取反 |
| `reassigned_between` | `interpretation.findings.reassigned_between` |
| `in_loop` | `context.in_loop` |
| `access_kind` | `crash.access.dir` |
| `cross_frame_count` | `call_chain` 中 `is_project=true` 的帧数 |

---

## 输入样本的完整字段（14 个）

| 字段 | 内容 |
|---|---|
| `osv_id` | 崩溃 ID |
| `project` | 项目名 |
| `crash_type` | 崩溃类型 |
| `crash` | 崩溃点：site（file/fn/line）、code、access（dir/width/region_bytes） |
| `entity` | 涉及对象：name/kind/storage/decl |
| `alloc` | 分配点：api/site/size_bytes/size_expr/cross_function |
| `sites` | 所有释放/使用点：kind/fn/line/code/origin |
| `context` | 上下文：fn/in_loop/loop_type/guards/guard_count/control_structures |
| `call_chain` | **完整调用栈**（每帧：fn/file/line/is_project） |
| `input_reachability` | 输入能到达的参数列表 |
| `types` | 类型信息：entity_type/cast_present/is_signed/ptr_origin |
| `completeness` | 缺失的字段列表 |
| `evidence` | CPG 路径、报告路径、testcase 大小 |
| `type_reconciliation` | 报告类型 vs 账本类型是否一致 |
| `interpretation` | findings（必要条件判定）+ missing + reasoning + confidence |

---

## 调用参数

| 参数 | 值 |
|---|---|
| provider | `deepseek` |
| model | `deepseek-flash` |
| temperature | 0.1 |
| max_tokens | 5000 |
| 批大小 | 15 条（完整 facts 后单条约 3.6 KB，15 条约 54 KB） |
| 重试 | 2 次 |

---

## 输出验收标准

| 检查项 | 通过条件 |
|---|---|
| JSON 可解析 | `json.loads` 成功 |
| 样本覆盖 | `sum(support) + len(unclassified) == sample_count` |
| ID 合法 | 所有 `sample_ids` 都在输入里 |
| pattern 数 | 1 ≤ len(patterns) ≤ 5 |
| name 长度 | 每个 name ≤ 12 字 |
| narrative 存在且非空 | `len(narrative) >= 30` |
| trigger_condition 完整 | 5 个字段都存在 |
| 无编造 | evidence 里的函数名/行号能在输入中找到 |

# Stage 3 跨批汇总 Prompt

> 用途：把某一崩溃类型的 N 份批级 pattern（每份 2-5 个）合并成该类型的最终形态（2-6 个）。
> 输入：`outputs/stage3/<type>/merge_input.json`（N 份 batch 输出的数组）
> 输出：`outputs/stage3/<type>/final.json`
> 模型：`provider=deepseek, model=deepseek-flash`

---

## 为什么需要这一步

分批分析时，同一个形态可能被不同批次起了不同名字：

| 批次 | 它发现的 pattern | support |
|---|---|---|
| batch_001 | "跨函数释放后使用" | 7 |
| batch_007 | "释放后跨函数读" | 5 |
| batch_015 | "容器析构后访问" | 4 |

**这三个可能是同一种形态。** 不做汇总，最后会得到 50 个碎片化的 pattern，无法用于阶段 4。

---

## System Prompt

```
你是一名内存安全崩溃分析的汇总专家。

你的任务：把多份"批级分析结果"合并成一份"类型级最终形态清单"。

严格遵守以下规则：

1. 【合并原则】语义相同的 pattern 必须合并。判断相同看三件事：
   a) 触发链相同（分配→释放→使用 发生在哪类代码结构里）
   b) 机制维度相同（至少 free_before_use、free_and_use_same_function 一致）
   c) narrative 描述的是同一类机制
2. 【合并后处理】
   - support = 所有被合并 pattern 的 support 之和
   - sample_ids = 所有被合并 pattern 的 sample_ids 的并集
   - dimensions：取多数值，例外写进 evidence
   - evidence：用跨样本统计的写法（"合并后共 N 条，其中 X 条..."）
3. 【丢弃原则】合并后 support < 2 的形态，放进 low_support 列表（不删除，单独列出）。
4. 【保留原样】无法判断是否相同的 pattern，不要强行合并，单独保留。
5. 【不许编造】只用输入里有的信息。
6. 最终形态数控制在 2-6 个（不含 low_support）。
7. 输出必须是严格 JSON，不要用 markdown 包裹。
8. name 用中文，≤12 字。
```

---

## User Prompt 模板

```
## 崩溃类型
{{CRASH_TYPE}}

## 批级分析结果（共 {{N}} 批，合计 {{M}} 个 pattern）

请先读取文件 {{MERGE_INPUT_FILE}}。
文件内容是 JSON 数组，每个元素是一批的输出（含该批的 patterns 和 unclassified）。

## 任务
1. 把所有批次里的 pattern 收集起来，按语义合并。
2. 合并后重新计算 support 和 sample_ids。
3. support < 2 的形态放进 low_support。
4. 输出 2-6 个最终形态。

## 输出 JSON schema
{{OUTPUT_SCHEMA}}

直接输出 JSON，不要任何解释文字。
```

---

## 输出 Schema

```json
{
  "crash_type": "string",
  "total_batches": number,
  "total_input_patterns": number,
  "final_patterns": [
    {
      "name": "string",
      "narrative": "string",
      "support": number,
      "sample_ids": ["string"],
      "merged_from": ["batch_001", "batch_007"],
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
  "low_support": [
    {"name": "string", "support": number, "sample_ids": ["string"], "reason": "string"}
  ],
  "unclassified": [
    {"sample_id": "string", "reason": "string"}
  ],
  "merge_notes": "string"
}
```

---

## 与批级输出的差异

| 字段 | 批级 | 类型级 |
|---|---|---|
| `patterns` | 2-5 个 | 改名 `final_patterns`，2-6 个 |
| `merge_inputs` | — | 新增 `merged_from`（来自哪些批次） |
| `low_support` | — | 新增（support < 2 的，单独列出不删） |
| `batch_observations` | 有 | 改名 `merge_notes` |
| `total_batches` / `total_input_patterns` | — | 新增（可审计合并是否丢失） |

---

## 验收标准

| 检查项 | 通过条件 |
|---|---|
| JSON 可解析 | `json.loads` 成功 |
| 形态数 | 2 ≤ len(final_patterns) ≤ 6 |
| **样本不丢失** | `sum(support) + len(low_support 的 support) + len(unclassified)` 覆盖全部样本 |
| **合并可追溯** | 每个 final_pattern 的 `merged_from` 非空 |
| `support` 正确 | 等于被合并 pattern 的 support 之和 |
| `sample_ids` 正确 | 等于被合并 pattern 的 sample_ids 并集 |
| `trigger_condition` 完整 | 5 个字段都非空 |

---

## 调用参数

| 参数 | 值 |
|---|---|
| provider | `deepseek` |
| model | `deepseek-flash` |
| temperature | 0.1 |
| max_tokens | 8000（合并后输出较大） |
| 调用次数 | 每类型 1 次，共 4 次 |

---

## 一个真实输出示例（UAF，基于 15 条样本的测试）

```json
{
  "crash_type": "heap-use-after-free",
  "total_batches": 1,
  "total_input_patterns": 4,
  "final_patterns": [
    {
      "name": "重分配后旧缓冲仍解析",
      "support": 5,
      "sample_ids": ["ARVO-42470878", "ARVO-42475763", "ARVO-42476708",
                     "ARVO-42476741", "ARVO-42476946"],
      "merged_from": ["uaf-002"],
      "narrative": "五条样本的 free 都落在扩容/重分配辅助函数…",
      "trigger_condition": {...},
      "dimensions": {...},
      "evidence": [...],
      "confidence": "medium"
    }
  ],
  "low_support": [],
  "unclassified": [
    {"sample_id": "ARVO-396777457", "reason": "free 与 use 的对象同一性无法确认"}
  ],
  "merge_notes": "本批只有 1 份批级结果，未发生实际合并"
}
```

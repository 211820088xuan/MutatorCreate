# LLM 分析流程（Stage 3）

> 本文档说明：LLM 在项目中做什么、怎么调用、输入输出是什么、prompt 怎么写。
> 当前只实现 Stage 3；Stage 4/5 尚未开始。
>
> **模型**：`provider=deepseek, model=deepseek-flash`

---

# 一、整体位置

```
已知崩溃数据（facts + interpretation）
        ↓
   ┌─────────────────────────────────────┐
   │ Stage 3：从同类崩溃中提取共性形态   │  ← 本文档
   └─────────────────────────────────────┘
        ↓
   Stage 4：把共性形态抽象成通用特征（不含项目信息）
        ↓
   Stage 5：把通用特征落到具体项目，生成 mutator
        ↓
   验证：跑 fuzz，看是否撞出新崩溃
```

---

# 二、Stage 3 的流程

## 2.1 为什么要分两步

| 类型 | 样本数 | 单条数据量 | 总数据量 | 能否一次喂给 LLM |
|---|---|---|---|---|
| UAF | 121 | ~3.5 KB | ~420 KB | 勉强 |
| HBO | 601 | ~3.5 KB | ~2.1 MB | **不能** |
| stack | 110 | ~3.5 KB | ~385 KB | 勉强 |
| global | 51 | ~3.5 KB | ~180 KB | 可以 |

**HBO 必须分批。为统一处理，所有类型都走分批。**

## 2.2 两步流程

```
┌─────────────────────────────────────────────────────┐
│ 第 1 步：分批提取（每批 15 条样本）                  │
│                                                      │
│  样本 1-15   → LLM → 批 1 的 pattern                 │
│  样本 16-30  → LLM → 批 2 的 pattern                 │
│  ...                                                 │
│  样本 586-601 → LLM → 批 41 的 pattern               │
│                                                      │
│  输出：41 份批级 pattern                             │
└─────────────────────────────────────────────────────┘
                        ↓
┌─────────────────────────────────────────────────────┐
│ 第 2 步：跨批汇总                                    │
│                                                      │
│  41 份批级 pattern → LLM → 该类型的最终 pattern      │
│                                                      │
│  输出：2-6 种机制形态 + 各自的 support               │
└─────────────────────────────────────────────────────┘
```

**调用次数**：UAF 9 次、HBO 42 次、stack 9 次、global 5 次（含汇总各 1 次）

---

# 三、输入

## 3.1 单条样本的完整字段（15 个）

每条样本 = **完整 facts（14 字段）+ 完整 interpretation**。

| 字段 | 内容 | 为什么重要 |
|---|---|---|
| `osv_id` | 崩溃 ID | 标识 |
| `project` | 项目名 | 判断是否跨项目 |
| `crash_type` | 崩溃类型 | 分类 |
| `crash` | site（file/fn/line）、code、access（dir/width/region_bytes） | 使用点 |
| `entity` | name / kind / storage / decl（file/line/type/size） | 被操作的对象 |
| `alloc` | api / site / size_bytes / size_expr / cross_function | 分配点 |
| `sites` | 所有释放/使用点：kind/fn/line/code/origin | 释放点 |
| `context` | fn / in_loop / loop_type / guards / guard_count / control_structures | 控制流位置 |
| **`call_chain`** | **完整调用栈**（每帧 fn/file/line/is_project） | **判断跨几帧、分配/释放是否在不同调用路径** |
| **`input_reachability`** | 输入能到达的参数列表 | **判断哪个输入控制崩溃** |
| `types` | entity_type / cast_present / is_signed / ptr_origin | 类型相关越界 |
| `completeness` | 缺失的字段列表 | LLM 直接知道数据缺口 |
| `evidence` | CPG 路径 / 报告路径 / testcase 大小 | 规模与可追溯性 |
| `type_reconciliation` | 报告类型 vs 账本类型是否一致 | 数据可信度 |
| **`interpretation`** | findings + missing + reasoning + confidence | **必要条件判定结果** |

## 3.2 真实样本（ARVO-372547409，完整内容）

```json
{
  "osv_id": "ARVO-372547409",
  "project": "libxml2",
  "crash_type": "heap-use-after-free",
  "crash": {
    "site": {"file": "/src/libxml2/valid.c", "fn": "xmlValidateOneElement", "line": 5992},
    "code": "xmlStrEqual(cur->prefix, prefix) | cur->prefix",
    "access": {"dir": "READ", "width": 4, "region_bytes": 64}
  },
  "entity": {
    "name": "cur", "kind": "struct", "storage": "heap",
    "decl": {"file": "/src/libxml2/valid.c", "line": 5952, "type": "xmlNsPtr", "size": null}
  },
  "alloc": {
    "api": "malloc", "cross_function": true,
    "site": {"file": "/src/libxml2/fuzz/fuzz.c", "fn": "xmlFuzzMalloc", "line": 81},
    "size_bytes": 64, "size_expr": null
  },
  "sites": [
    {"kind": "free", "fn": "xmlFreeAttribute", "line": 1625, "code": null, "origin": "report:freed_by"},
    {"kind": "unknown", "fn": "xmlValidateOneElement", "line": 5992,
     "code": "xmlStrEqual(cur->prefix, prefix) | cur->prefix", "origin": "report:crash"}
  ],
  "context": {
    "fn": "xmlSearchNsSafe", "in_loop": true, "loop_type": null, "loop_range": null,
    "guard_count": 6,
    "guards": "prefix != NULL | cur == NULL | cur != NULL",
    "control_structures": "IF:5957,IF:5964,IF:5966,WHILE:5972,IF:5974,WHILE:5980"
  },
  "call_chain": [
    {"fn": "xmlValidateOneElement", "file": null, "line": null, "is_project": true},
    {"fn": "xmlValidateElement", "file": null, "line": null, "is_project": true},
    {"fn": "LLVMFuzzerTestOneInput", "file": null, "line": null, "is_project": false},
    {"fn": "main", "file": null, "line": null, "is_project": false},
    {"fn": "free", "file": null, "line": null, "is_project": true},
    {"fn": "xmlFreeAttribute", "file": null, "line": null, "is_project": true},
    {"fn": "xmlFreeAttributeTableEntry", "file": null, "line": null, "is_project": true},
    {"fn": "xmlHashFree", "file": null, "line": null, "is_project": true},
    {"fn": "xmlFreeAttributeTable", "file": null, "line": null, "is_project": true},
    {"fn": "xmlFreeDtd", "file": null, "line": null, "is_project": true},
    {"fn": "xmlFreeNode", "file": null, "line": null, "is_project": true},
    {"fn": "dropNode", "file": null, "line": null, "is_project": true}
  ],
  "input_reachability": ["node", "prefix", "out"],
  "types": {"entity_type": "xmlNsPtr", "cast_present": null, "is_signed": null, "ptr_origin": "assignment"},
  "completeness": ["alloc.size_expr"],
  "evidence": {"cpg": ".../libxml2_d4d1f3f33d6d.cpg", "report": ".../report.log", "testcase_size": 26},
  "type_reconciliation": {"diverged": false, "ledger_crash_type": "heap-use-after-free", "report_fault_kind": "heap-use-after-free"},
  "interpretation": {
    "type": "heap-use-after-free",
    "confidence": "medium",
    "key_facts": {"freed_ptr": "cur", "free_sites": [1625], "use_site": 5992},
    "findings": {
      "free_sites": [1625], "use_site": 5992, "crash_after_free": true,
      "reassigned_between": null, "alias_used": null, "free_arg": null,
      "free_cross_function": true
    },
    "missing": ["reassigned_between"],
    "reasoning": "崩溃点 5992 之前已有 free 于 [1625]"
  }
}
```

## 3.3 批次输入格式

15 条样本的 JSON 数组，约 54 KB。

---

# 四、Prompt

## 4.1 System Prompt（固定）

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

## 4.2 User Prompt 模板

```
## 崩溃类型
{{CRASH_TYPE}}

## 该类型的机制背景
{{MECHANISM_BACKGROUND}}

## 样本
请先用 read 工具读取文件 {{SAMPLES_FILE}}（{{N}} 条完整样本，共 {{SIZE}} KB）。
文件内容是 JSON 数组，每个元素是一条样本。

## 任务
1. 阅读全部样本，按"崩溃在成因链上的形态"分组。
2. 每组给出：name、narrative、trigger_condition、support、sample_ids、dimensions、evidence、confidence。
3. 无法归类的样本放入 unclassified，并说明缺什么数据。

## 输出 JSON schema
{{OUTPUT_SCHEMA}}

直接输出 JSON，不要任何解释文字。
```

## 4.3 机制背景变量（以 UAF 为例）

```
UAF 的必要条件链：
- N1 对象是堆分配
- N2 存在 free(p) 调用
- N3 p 在 free 之后被解引用（执行顺序）
- N4 free 与解引用之间 p 未被重新赋值
- N5 free 与解引用之间 p 未重新 malloc
- N6 free 的实参是 p 本身（非 p+off）
- N7 解引用对象与 free 对象是同一对象（含别名）
- N8 free 与解引用在同一可达路径上
- N9 p 解引用时未被置空
- N10 解引用发生在 free 生效后（非同一语句）
```

## 4.4 调用参数

| 参数 | 值 | 理由 |
|---|---|---|
| provider | `deepseek` | 与项目环境一致 |
| model | `deepseek-flash` | 按要求指定 |
| temperature | 0.1 | 分析任务要稳定 |
| max_tokens | 5000 | 输出 JSON 约 2500-4000 token |
| 批大小 | 15 条 | 约 54 KB 输入 |
| 重试 | 2 次 | JSON 解析失败时重试 |

---

# 五、输出

## 5.1 输出 Schema

```json
{
  "crash_type": "string",
  "batch_id": "string",
  "sample_count": number,
  "patterns": [
    {
      "name": "string",                    // 中文，≤12 字
      "narrative": "string",               // 2-4 句，必须引用具体函数名/行号/字段值
      "support": number,
      "sample_ids": ["string"],

      "trigger_condition": {               // 核心：怎么触发
        "where_alloc": "string",           // 在哪里分配
        "where_free": "string",            // 在哪里释放
        "where_use": "string",             // 在哪里被错误使用
        "what_input_controls": "string",   // 哪个输入字段控制
        "minimal_requirement": "string"    // 最小触发条件
      },

      "dimensions": {                      // 辅助索引（7 个固定维度）
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
}
```

## 5.2 为什么这样设计输出

| 输出部分 | 回答什么问题 | 对后续的作用 |
|---|---|---|
| `narrative` | 这个形态的崩溃**怎么发生** | Stage 4 抽象的原材料 |
| `trigger_condition.where_*` | 分配/释放/使用**分别在哪** | 定位 mutator 要影响的代码位置 |
| `trigger_condition.what_input_controls` | **哪个输入字段**控制 | 直接告诉 mutator 改哪个字节 |
| `trigger_condition.minimal_requirement` | **最小触发条件** | mutator 的目标 |
| `dimensions` | 7 个固定维度的取值 | 便于统计和跨类型比较 |
| `evidence` | 依据 | 可审计，防止编造 |
| `unclassified` | 哪些样本归不了类 | 提示数据缺口 |

**关键：`trigger_condition` 的 5 个字段直接对应 Stage 4/5 需要的输入。**

---

# 六、测试结果

## 6.1 v1 vs v2 对比（同样 4 条 UAF 样本）

| 项 | v1（压缩输入 + 固定 7 维度） | v2（完整输入 + narrative） |
|---|---|---|
| 识别出的形态数 | 2 种（跨函数 / 同函数） | **4 种，互不重叠** |
| 形态名称 | "跨函数释放后使用"、"同函数释放后立即读取" | **"循环内缓存指针跨函数失效"、"测试框架缓冲区提前回收"、"扩容重分配后旧指针悬空"、"引用计数释放后同帧复用"** |
| 能否看出触发机制 | ❌ 只能看出调用关系 | ✅ 能说出 realloc 迁移、引用计数归零、harness 缓冲区回收 |
| 是否用上 `call_chain` | ❌ 被裁掉 | ✅ 引用 `dropNode→xmlFreeNode→xmlFreeDtd` 链 |
| 是否用上 `testcase_size` | ❌ 被裁掉 | ✅ 指出 `0/12/26/328` 跨度，建议按两极设计变异 |
| `trigger_condition` | ❌ 无 | ✅ 5 个字段全部给出 |
| 对 mutator 的指导 | ❌ 无法使用 | ✅ `minimal_requirement` 直接可用 |

## 6.2 v2 发现的、v1 完全看不到的事实

**openvswitch 那条（ARVO-42470878）**：

```
alloc.api = realloc
free 站点 = xrealloc（lib/util.c:134）  ← 和 alloc 是同一行！
```

**这是 UAF 的一个独立子类：realloc 迁移导致的悬空指针。**

v1 只会说"跨函数释放后使用"，完全看不到这个机制。v2 说：

> 扩容链 `ofpbuf_put→ofpbuf_put_uninit→ofpbuf_resize__→xrealloc` 在 `parse_odp_action`
> 仍持有指向旧缓冲区的指针时发生，随后 `odp-util.c:2246` 读取该指针。
> **12 字节的 action 串只要让 ofpbuf 在解析途中扩容，旧指针即指向已回收内存。**

**这句话直接就是 mutator 的设计目标。**

## 6.3 v2 的真实输出节选（4 种形态）

| 形态 | support | 触发条件摘要 |
|---|---|---|
| 循环内缓存指针跨函数失效 | 1（libxml2） | 26 字节输入先触发 DTD 拆除（`dropNode→xmlFreeDtd`）释放 64 字节，再在 `xmlSearchNsSafe` 循环里读 |
| 测试框架缓冲区提前回收 | 1（net-snmp） | 328 字节输入让参数解析多阶段之间发生 harness 缓冲区回收，hex 转换阶段继续读 |
| 扩容重分配后旧指针悬空 | 1（openvswitch） | 12 字节 action 串让 ofpbuf 在解析途中扩容（realloc 迁移 64 字节），旧指针悬空 |
| 引用计数释放后同帧复用 | 1（radare2） | **0 字节输入**，走到 teardown 链 `r_core_free→r_list_free→r_core_task_decref`，248 行释放后 250 行读 |

**`batch_observations` 的结论**：

> testcase_size 跨度为 0/12/26/328，说明本批既包含纯 teardown 触发（0 字节、输入无关），
> 也包含需构造结构/参数串的触发，**变异策略应按这两极分别设计**。

## 6.4 完整真实输出

> 完整文件：`outputs/stage3_uaf_test_v2.json`（4 种形态全量，约 8 KB）
>
> 下面以第 1 个 pattern 为例展示完整结构（其余 3 个字段相同，内容不同）

```json
{
  "crash_type": "heap-use-after-free",
  "batch_id": "uaf-batch-001",
  "sample_count": 4,
  "patterns": [
    {
      "name": "循环内缓存指针跨函数失效",
      "narrative": "释放点是 xmlValidateOneElement 之外的 xmlFreeAttribute（valid.c:1625，sites.kind=free，origin=report:freed_by，free_cross_function=true），由 dropNode→xmlFreeNode→xmlFreeDtd→xmlFreeAttributeTable→xmlHashFree→xmlFreeAttribute 链在属性表/DTD 拆除时完成；被释放的是 xmlNsPtr 类型的 cur（entity.storage=heap，entity.decl=valid.c:5952，由 fuzz.c:81 的 xmlFuzzMalloc 分配 64 字节）。使用侧 xmlValidateOneElement（valid.c:5992）在 xmlSearchNsSafe 的循环里读 cur->prefix（access.dir=READ，width=4，region_bytes=64），context.in_loop=true，而 guards 只有 \"prefix != NULL | cur == NULL | cur != NULL\"，不含 cur 是否已被释放的有效性判断。同一次 26 字节输入内，拆除属性/DTD 使循环缓存的命名空间指针悬空，后续 prefix 比较即命中已释放内存。",
      "support": 1,
      "sample_ids": ["ARVO-372547409"],
      "trigger_condition": {
        "where_alloc": "fuzz/fuzz.c:81 xmlFuzzMalloc（alloc.api=malloc，size_bytes=64，cross_function=true）",
        "where_free": "valid.c:1625 xmlFreeAttribute（sites.kind=free，origin=report:freed_by），经 dropNode→xmlFreeNode→xmlFreeDtd→xmlFreeAttributeTable→xmlHashFree→xmlFreeAttribute 链",
        "where_use": "valid.c:5992 xmlValidateOneElement，读 cur->prefix（width=4，region_bytes=64），循环上下文 xmlSearchNsSafe",
        "what_input_controls": "input_reachability=[node, prefix, out]：输入中的节点树与命名空间前缀决定是否进入 xmlSearchNsSafe 的 prefix 比较循环，以及同一次校验中是否走到 dropNode→xmlFreeDtd 的拆除路径（testcase_size=26）；两个分支的相对先后无法从字段进一步细分",
        "minimal_requirement": "一次输入处理内先经 dropNode→xmlFreeNode→xmlFreeDtd 释放掉 cur 所指的 xmlNsPtr 区域（64 字节），随后仍处于 xmlSearchNsSafe 循环（in_loop=true）的 xmlValidateOneElement:5992 以 cur->prefix 做 4 字节读"
      },
      "dimensions": {
        "alloc_kind": "heap",
        "free_before_use": "true",
        "free_and_use_same_function": "false",
        "reassigned_between": "unknown",
        "in_loop": "true",
        "access_kind": "read",
        "cross_frame_count": "unknown"
      },
      "evidence": [
        "alloc.api=malloc, alloc.site=/src/libxml2/fuzz/fuzz.c:81 xmlFuzzMalloc, size_bytes=64, cross_function=true",
        "free site=xmlFreeAttribute line=1625, origin=report:freed_by; free_cross_function=true",
        "use site=/src/libxml2/valid.c:5992 xmlValidateOneElement, crash.code=\"xmlStrEqual(cur->prefix, prefix) | cur->prefix\", access.dir=READ, width=4, region_bytes=64",
        "entity.name=cur, entity.entity_type=xmlNsPtr, entity.storage=heap, entity.decl=/src/libxml2/valid.c:5952",
        "context.fn=xmlSearchNsSafe, context.in_loop=true, guard_count=6, guards=\"prefix != NULL | cur == NULL | cur != NULL\"",
        "input_reachability=[node, prefix, out], testcase_size=26",
        "unknown:reassigned_between (interpretation.findings.reassigned_between=null)",
        "unknown:alias_used (interpretation.findings.alias_used=null，N7 别名关系未确认)",
        "unknown:free_arg (interpretation.findings.free_arg=null，N6 释放实参形式未记录)",
        "unknown:cross_frame_count (call_chain 中释放链与使用链并列，无同一栈内帧距信息)"
      ],
      "confidence": "medium"
    }
  ],
  "unclassified": [],
  "batch_observations": "..."
}
```

**注意 evidence 的最后 4 条**：LLM 主动把每个 null 字段列成 `unknown:<字段名>`，并说明它导致哪条必要条件无法验证。**这是防止把"数据缺失"误当成"条件不成立"的关键机制。**

## 6.5 这些输出后续怎么用

### 输出的哪一部分被哪一步使用

| 输出字段 | Stage 4 用来做什么 | Stage 5 用来做什么 |
|---|---|---|
| `narrative` | 抽象的原材料（读出机制链） | — |
| `trigger_condition.where_alloc` | 判断"分配阶段"是否是共性 | 定位需要影响的上游代码 |
| `trigger_condition.where_free` | 判断"释放时机"是否是共性 | **定位 mutator 要提前触发的动作** |
| `trigger_condition.where_use` | 判断"使用点"是否固定 | 定位崩溃点，验证变异是否命中 |
| `trigger_condition.what_input_controls` | 判断"输入控制点"是否一致 | **直接决定 mutator 改哪个字节** |
| `trigger_condition.minimal_requirement` | 抽象成通用特征的骨架 | **mutator 的目标条件** |
| `dimensions` | 跨类型统计、形态聚类 | 粗筛（如只对 `in_loop=true` 的形态做循环变异） |
| `evidence` | 审计抽象是否偏离原始数据 | 调试（变异后崩溃点是否一致） |
| `unclassified` | 提示数据缺口 | — |

### Stage 4 会做什么

**输入**：Stage 3 输出的全部 pattern（一个类型可能有 4-6 种形态）

**任务**：把每种形态的 `narrative` + `trigger_condition` 抽象成**不含项目信息的通用特征**。

**抽象示例**（以"扩容重分配后旧指针悬空"为例）：

```
输入（Stage 3 的输出）：
  where_alloc:   lib/util.c:134 xrealloc（realloc，64 字节）
  where_free:    同一站点 xrealloc（realloc 迁移导致旧块回收）
  where_use:     odp-util.c:2246 parse_odp_action，width=2
  minimal_req:   输入需让 ofpbuf_put 在 parse_odp_action 使用旧指针期间
                 触发 ofpbuf_resize__→xrealloc

输出（Stage 4 的通用特征）：
  name: 动态缓冲区扩容导致旧指针失效
  precondition:
    - 存在一块动态分配的缓冲区，被指针 P 引用
    - 存在扩容操作（realloc / 二次分配 + 拷贝 + 释放）
  trigger_path:
    - 扩容发生时，P 仍指向旧缓冲区
    - 扩容后 P 未被更新为新地址
    - 后续仍通过 P 读写
  mutation_target:
    - 控制缓冲区初始大小的输入字段（让扩容提前发生）
    - 控制"读取旧指针"路径的输入字段
  parameters:
    - 扩容触发条件：容量不足
    - 扩容方式：realloc / 手动分配
  limitations:
    - 无法确定旧指针是否被更新（N4 数据缺失）
```

**关键约束**：这个特征里**不能出现 `ofpbuf`、`parse_odp_action`、`xrealloc` 这些项目名**——否则无法迁移到别的项目。

### Stage 5 会做什么

**输入**：Stage 4 的通用特征 + 目标项目的代码信息（CPG）

**任务**：在目标项目里找到符合该特征的代码位置，生成 mutator。

**示例**（把"动态缓冲区扩容"特征落到某个项目）：

```
1. 用 CPG 查：目标项目里有哪些 realloc 调用？
2. 筛选：哪些 realloc 之后，旧指针仍被使用？（用数据流判断）
3. 定位：这些点的上游输入字段是什么？
4. 生成 mutator：
   - 找到控制缓冲区初始大小的输入字段（如长度前缀）
   - 变异策略：把该字段改大，使首次分配就够用 → 不扩容 → 不崩溃
   - 或：把该字段改小，使扩容提前发生 → 旧指针悬空 → 崩溃
```

### 4 种形态对应的 mutator 方向（直接可用）

| 形态 | 触发条件 | mutator 要做什么 |
|---|---|---|
| **循环内缓存指针跨函数失效** | 先触发 DTD 拆除释放，再在循环里读 | 构造输入让"拆除"和"读取"在同一次执行内都发生 |
| **测试框架缓冲区提前回收** | 参数解析多阶段之间发生 harness 回收 | 构造输入走两个阶段的参数解析 |
| **扩容重分配后旧指针悬空** | 解析途中触发 realloc 迁移 | **让缓冲区初始容量偏小，迫使扩容提前发生** |
| **引用计数释放后同帧复用** | 走到 teardown 链 | **无需输入，空输入即可（0 字节）** |

**最后一行是重要发现**：radare2 那条的 `testcase_size=0`，说明它跟输入无关，**mutator 对它无能为力**——这类样本应该从 mutator 的适用范围内排除。

### 一个完整的使用链路示例

```
Stage 3 输出（本文档 6.4）
   ↓
pattern: "扩容重分配后旧指针悬空"
  minimal_requirement: 输入需让 ofpbuf_put 在 parse_odp_action 使用旧指针期间触发扩容
   ↓
Stage 4 抽象
   ↓
通用特征: "动态缓冲区扩容导致旧指针失效"
  mutation_target: 控制缓冲区初始大小的输入字段
   ↓
Stage 5 落地到某个项目
   ↓
mutator: 把输入里的长度字段改小，使首次分配不够、扩容提前发生
   ↓
验证: 跑 fuzz，看是否撞出同类崩溃
```

## 6.6 多样本 pattern 的真实输出（15 条 UAF，已确认采用）

用 15 条真实 UAF 样本跑出的结果，验证了"一个 pattern 被多条崩溃共享"时的输出形态。

### 整体结构

| 形态 | support | 样本 ID |
|---|---|---|
| 清理函数内释放后读 | **3** | ARVO-42471500、ARVO-42474100、ARVO-42477951 |
| 容器释放子对象后读取 | **2** | ARVO-372547409、ARVO-42474969 |
| 重分配后旧缓冲仍解析 | **5** | ARVO-42470878、ARVO-42475763、ARVO-42476708、ARVO-42476741、ARVO-42476946 |
| 解码器缓冲释放后访问 | **3** | ARVO-42473818、ARVO-42474468、ARVO-42479359 |
| （未归类） | — | ARVO-396777457、ARVO-42478101 |

**校验：3 + 2 + 5 + 3 + 2 = 15** ✓

### support=5 的完整 pattern

```json
{
  "name": "重分配后旧缓冲仍解析",
  "support": 5,
  "sample_ids": ["ARVO-42470878", "ARVO-42475763", "ARVO-42476708",
                 "ARVO-42476741", "ARVO-42476946"],

  "narrative": "五条样本的 free 都落在扩容/重分配辅助函数：openvswitch 在 xrealloc（lib/util.c:134）realloc 64 字节时释放旧块，parse_odp_action 随后在 odp-util.c:2246 读 2 字节；libspng 在 read_data（spng.c:292）搬移后，read_chunks_before_idat 1321/1454 与 read_chunks_after_idat 1560 分别读 2/8224/8289 字节；radare2 在 r_num_tail（unum.c:742）释放 14 字节后 cin_get（calc.c:216）读 1 字节。call_chain 中出现 realloc←xrealloc、realloc←read_data，说明旧块由重分配释放，而旧的数据指针没有被回写到新块。",

  "trigger_condition": {
    "where_alloc": "openvswitch xrealloc lib/util.c:134（api=realloc，64 字节，与 free 同址）；libspng 分配记为 spng_set_png_stream spng.c:2382（api=unknown:interceptor_skipped，region 8192 字节或 null），扩容在 read_data；radare2 r_num_tail unum.c:731（14 字节）",
    "where_free": "openvswitch xrealloc lib/util.c:134；libspng read_data spng.c:292（3 条）；radare2 r_num_tail unum.c:742",
    "where_use": "parse_odp_action odp-util.c:2246（READ 2 字节）；read_chunks_before_idat spng.c:1321（READ 2 字节）、spng.c:1454（memcpy 8224 字节）；read_chunks_after_idat spng.c:1560（memcpy 8289 字节）；cin_get calc.c:216（READ 1 字节）",
    "what_input_controls": "unknown:input_reachability —— 5/5 为空数组，未被记录的是「哪个输入字段驱动扩容次数」；仅 testcase_size 可用：libspng 8472/8471/24604 字节、radare2 3995 字节、openvswitch 12 字节",
    "minimal_requirement": "在一次解析中让同一缓冲被 realloc 搬移（旧块释放）后旧指针未更新，随后仍用旧指针解析后续 chunk / action / token；openvswitch 仅需 12 字节，说明触发不依赖超长输入"
  },

  "dimensions": {
    "alloc_kind": "heap",
    "free_before_use": "true",
    "free_and_use_same_function": "false",
    "reassigned_between": "unknown",
    "in_loop": "unknown",
    "access_kind": "read",
    "cross_frame_count": "unknown"
  },

  "evidence": [
    "5/5 free 站点位于扩容/重分配辅助函数（xrealloc:134、read_data:292、r_num_tail:742），call_chain 中显式出现 realloc←xrealloc、realloc←read_data",
    "5/5 findings.free_cross_function=true，free 与 use 不同函数（util.c→odp-util.c、spng.c 的 read_data→read_chunks_*、unum.c→calc.c）",
    "4/5 crash_after_free=true；例外 42475763 为 false，reasoning 写「未找到崩溃点之前的 free，需补 free 栈」，按 unknown 处理",
    "5/5 access.dir=READ；宽度分布 2/8224/8289/2/1，其中 42476946、42476741 的 width 为 8224/8289（memcpy 整块搬移）",
    "reassigned_between 5/5 为 null、in_loop 5/5 为 null → unknown",
    "alloc api：realloc 1 条、unknown:interceptor_skipped 4 条；分配与释放同函数的仅 2/5"
  ],
  "confidence": "medium"
}
```

### 和 support=1 的差异（这是关键）

| 部分 | support=1 | support=5 |
|---|---|---|
| `narrative` | 只讲一条 | **用 3 条做例证，讲共同机制** |
| `where_alloc` | 一个位置 | **列 3 个不同位置，分号分隔** |
| `where_use` | 一个位置 | **5 条各列一遍** |
| `what_input_controls` | 单条判断 | **`unknown:input_reachability —— 5/5 为空数组`**（连"5 条都没有"这个事实也写出） |
| `dimensions` | 单值 | **取多数值 + 注明例外** |
| `evidence` | 列举字段值 | **`5/5`、`4/5`、`2/5` 的统计 + 例外点名** |

**最关键的变化在 evidence**：从"这个字段是什么"变成"**N 条里有几条满足、哪几条是例外**"。

### 未归类的样本（同样有价值）

```json
{
  "sample_id": "ARVO-396777457",
  "reason": "free（af_gb_cleanup:56）与 use（netsnmp_hex_to_binary tools.c:581）之间的对象同一性无法确认：findings.freed_ptr=null、entity.decl=null、types.entity_type=null，free 又位于 fuzz 包装层的缓冲清理，无法排除 N7 不成立或被释放的并非同一缓冲",
  "missing_fields": ["entity.decl", "types.entity_type", "interpretation.findings.freed_ptr",
                     "interpretation.findings.alias_used", "interpretation.findings.free_arg"]
}
```

**不是所有样本都能归类，而"为什么归不了"本身就是信息——它精确指出了缺哪几个字段。**

### 从这批数据得出的两条结论

**① 字段缺失高度一致**

> `reassigned_between` 14/15 为 null、`alias_used` 14/15 为 null、`free_arg` 14/15 为 null，**只有 opensc 样本（ARVO-42477951）具备完整同一性证据**（`reassign_sites=[]`、`remalloc_between=false`、`alias_used=false`、`free_arg=obj`）

→ 直接验证了 P0 补字段的必要性。

**② 输入规模的真实分布**

> `testcase_size` 跨度 0–24604 字节，**10/15 不超过 400 字节**，其中 ARVO-42471500 为空输入（0 字节）

→ 多数 UAF 不需要大输入，**mutator 应朝"小输入、多次解析/多次扩容"方向设计**，而不是"堆长度"。

---

# 七、验收标准（脚本自动检查）

| 检查项 | 通过条件 |
|---|---|
| JSON 可解析 | `json.loads` 成功 |
| 样本覆盖 | `sum(support) + len(unclassified) == sample_count` |
| ID 合法 | 所有 `sample_ids` 都在输入里 |
| pattern 数 | 1 ≤ len(patterns) ≤ 5 |
| name 长度 | 每个 name ≤ 12 字 |
| narrative 非空 | `len(narrative) >= 30` |
| trigger_condition 完整 | 5 个字段都存在且非空 |
| 无编造 | evidence 里的函数名/行号能在输入中找到 |

---

# 八、待改进

| # | 问题 | 现状 | 计划 |
|---|---|---|---|
| 1 | 跨批汇总 prompt 还没写 | 未开始 | 分批跑通后写 |
| 2 | 每个类型的机制背景文本还没定稿 | 部分 | 从 `ANALYSIS_PLAN.md` 提取 |
| 3 | 批量调用脚本还没写 | 未开始 | 用 workflow 编排 |
| 4 | 验收脚本还没写 | 未开始 | 同上 |
| 5 | 4 条样本全是不同形态，无法验证"同一形态多样本"的分组能力 | 已知 | 数据齐后跑 15 条/批验证 |
| 6 | `cross_frame_count` 有 3 条是 unknown | 已知 | P0 补 call_chain 的帧距信息 |

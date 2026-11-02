# facts 与 interpretation 详解

以崩溃 **ARVO-42494732（libredwg，heap-use-after-free）** 为例，逐个字段对照 JSON 解释，
然后说明这两份数据分别是**怎么提取出来的**。

---

## 0. 先认识这个崩溃

| 项 | 值 |
|---|---|
| 崩溃 ID | `ARVO-42494732` |
| 项目 | libredwg（用 C 写的 DWG/DXF 解析库） |
| 崩溃类型 | `heap-use-after-free`（堆上已释放的内存又被读） |
| 崩溃位置 | `src/in_dxf.c` 的 `dxf_objects_read`，第 **12267** 行 |
| 触发输入大小 | 256 字节 |
| 源码版本 | `ff69eeda` |

崩溃报告的原文（`report.log`）关键三行：

```
==7==ERROR: AddressSanitizer: heap-use-after-free on address 0x6020000001d0
READ of size 2 at 0x6020000001d0 thread T0
    #0 0x3278197 in dxf_objects_read /src/libredwg/src/in_dxf.c:12267:36
...
0x6020000001d0 is located 0 bytes inside of 16-byte region [0x6020000001d0,0x6020000001e0)
freed by thread T0 here:
    #0 0x5232f2 in free ... 
    #1 ... dxf_free_pair /src/libredwg/src/in_dxf.c:515
previously allocated by thread T0 here:
    #0 0x5236f2 in calloc ...
    #1 ... xcalloc /src/libredwg/src/in_dxf.c:216
```

**翻译成人话**：

> 程序在 12267 行读了 2 个字节，但 ASan 发现这块地址所在的 16 字节区域
> **已经被释放过了**；释放发生在 `dxf_free_pair` 的 515 行；
> 这块区域最初是 `xcalloc` 在 216 行分配的。

---

## 1. facts 是什么

**一句话**：facts 是把"崩溃报告 + 源码结构"里**能被直接观测到的事实**，整理成固定字段的 JSON。
它**不做推断**，只记录"哪里分配了、哪里释放了、哪里崩了、涉及哪个变量"。

文件位置：`artifacts/facts.jsonl`（1 个崩溃 1 行，共 1,139 行）

### 1.1 顶层 15 个字段

```
osv_id · project · crash_type · entity · alloc · sites · crash · context
call_chain · types · input_reachability · evidence · type_reconciliation
completeness · deep · report_extra
```

下面按"是什么 / 这个崩溃的值 / 哪来的"三列说明。

---

#### `osv_id` — 崩溃唯一标识

| | |
|---|---|
| 值 | `"ARVO-42494732"` |
| 来源 | records 的主键 |

---

#### `project` — 项目名

| | |
|---|---|
| 值 | `"libredwg"` |
| 来源 | 崩溃报告头部的项目名 |

---

#### `crash_type` — 崩溃类型

| | |
|---|---|
| 值 | `"heap-use-after-free"` |
| 来源 | **优先用报告里实测的类型**（`rep.fault_kind`），而不是记录表里声明的类型 |

**为什么要优先用报告的**：ARVO 记录表里的类型是数据集维护者标注的，
报告里的 `ERROR: AddressSanitizer: xxx` 才是这次运行真正触发的。两者不一致时以实测为准，
这个选择被记录在 `type_reconciliation` 字段里（见下文）。

---

#### `entity` — 崩溃处的核心变量

```json
"entity": {
  "name": "pair",
  "kind": "pointer",
  "storage": "heap",
  "decl": {"file": "/src/libredwg/src/in_dxf.c", "line": 12264,
           "size": null, "type": "Dxf_Pair*"}
}
```

| 字段 | 值 | 含义 | 来源 |
|---|---|---|---|
| `name` | `pair` | 出问题的变量名 | 崩溃行代码里的标识符（CPG 提取） |
| `kind` | `pointer` | 它是个指针 | 类型是 `Dxf_Pair*` |
| `storage` | `heap` | 指向堆内存 | 崩溃类型是 UAF，必然是堆 |
| `decl.type` | `Dxf_Pair*` | 声明类型 | CPG 里该变量的声明节点 |
| `decl.line` | 12264 | 声明在第 12264 行 | 同上 |

**通俗解释**：这个崩溃的核心是一个叫 `pair` 的指针，它指向一块 16 字节的堆内存。

---

#### `alloc` — 这块内存是怎么分配的

```json
"alloc": {
  "api": "calloc",
  "site": {"file": "/src/libredwg/src/in_dxf.c", "fn": "xcalloc", "line": 216},
  "size_bytes": 16,
  "size_expr": null,
  "size_expr_cpg": "80",
  "size_expr_cpg_callee": "<operator>.alloc",
  "cross_function": true
}
```

| 字段 | 值 | 含义 |
|---|---|---|
| `api` | `calloc` | 用了 `calloc` 分配 |
| `site.fn` | `xcalloc` | 分配发生在 `xcalloc` 函数里 |
| `site.line` | 216 | 第 216 行 |
| `size_bytes` | 16 | 分配了 16 字节 |
| `size_expr` | `null` | **分配时的表达式没拿到**（记为缺失） |
| `size_expr_cpg` | `"80"` | CPG 里找到的相邻分配表达式是 `name[80]`——**但这是另一个变量，不是 `pair`** |
| `cross_function` | `true` | 分配和崩溃不在同一个函数（`xcalloc` vs `dxf_objects_read`） |

**通俗解释**：

> `pair` 指向的内存是 `xcalloc` 在 216 行分配的，大小 16 字节。
> **但"分配时传的参数是什么"没查到**——这是数据的一个缺口，被记进了 `completeness`。

`size_expr_cpg: "80"` 这一项要特别注意：它是 CPG 在同一行附近找到的
`name[80]` 这个数组声明的长度，**与 `pair` 无关**。这就是为什么它单独成字段而不是直接填进
`size_expr`——避免张冠李戴。

---

#### `sites` — 关键操作点（分配/释放/崩溃/拷贝）

```json
"sites": [
  {"kind": "free", "fn": "dxf_free_pair", "line": 515, "origin": "report:freed_by"},
  {"kind": "unknown", "fn": "dxf_objects_read", "line": 12267,
   "code": "pair != NULL && pair->code == 0 && pair->value.s | ...", "origin": "report:crash"},
  {"kind": "strdup", "fn": "dxf_objects_read", "line": 12274,
   "args": "pair->value.s", "code": "strdup (pair->value.s)", "origin": "cpg"}
]
```

| 条目 | `kind` | `line` | 含义 | `origin`（哪来的） |
|---|---|---|---|---|
| 1 | `free` | 515 | **释放点**：`dxf_free_pair` 第 515 行 | `report:freed_by`（报告里的 "freed by" 栈） |
| 2 | `unknown` | 12267 | **崩溃点**：读 `pair->code` 那一行 | `report:crash`（报告的 `#0` 帧） |
| 3 | `strdup` | 12274 | 崩溃行之后的另一处拷贝操作 | `cpg`（从源码里扫出来的） |

**通俗解释**：`sites` 是一张"这条内存的一生"的时间线：
**515 行被释放 → 12267 行又被读**。

第 3 条（12274 的 `strdup`）是 CPG 额外补充的，用来观察"释放之后还有没有别的操作"。

---

#### `crash` — 崩溃点的细节

```json
"crash": {
  "site": {"file": "/src/libredwg/src/in_dxf.c", "fn": "dxf_objects_read", "line": 12267},
  "code": "pair != NULL && pair->code == 0 && pair->value.s | ...",
  "access": {"dir": "READ", "region_bytes": 16, "width": 2}
}
```

| 字段 | 值 | 含义 | 来源 |
|---|---|---|---|
| `site.line` | 12267 | 崩在第 12267 行 | 报告 `#0` 帧 |
| `site.fn` | `dxf_objects_read` | 崩溃函数 | 同上 |
| `code` | `pair != NULL && pair->code == 0 && ...` | 崩溃那一行的表达式（逐步简化后拼起来） | CPG 对该行做表达式分解 |
| `access.dir` | `READ` | 是**读**操作 | 报告 `READ of size 2` |
| `access.width` | 2 | 读了 **2 字节**（`pair->code` 是 `short`/`int16`） | 同上 |
| `access.region_bytes` | 16 | 这块内存总大小 16 字节 | 报告 `16-byte region` |

**通俗解释**：`pair->code` 是个 2 字节字段，读它的时候落在了已释放的 16 字节块上。

---

#### `context` — 崩溃点的代码上下文

```json
"context": {
  "fn": "dxf_objects_read",
  "in_loop": true,
  "loop_type": null,
  "loop_range": null,
  "guards": "pair != NULL | pair != NULL | pair != NULL",
  "guard_count": 4,
  "control_structures": "WHILE:12265,WHILE:12267,IF:12272,IF:12277,ELSE:12281,IF:12282,..."
}
```

| 字段 | 值 | 含义 |
|---|---|---|
| `in_loop` | `true` | **崩溃点在循环里** |
| `guards` | `pair != NULL \| ...` | 崩溃行上的条件判断（这里全是空指针检查） |
| `guard_count` | 4 | 有 4 处守卫条件 |
| `control_structures` | `WHILE:12265,WHILE:12267,IF:...` | 整个函数的控制结构清单（循环/分支都在哪行） |
| `loop_type` | `null` | 循环类型没识别出来（`while` 还是 `for`） |

**通俗解释**：崩溃发生在**双层 while 循环**里（12265 和 12267），
而且崩溃行只做了空指针检查，**没有做"是否已释放"的检查**。

`in_loop: true` 是一个很重要的信号——它说明这个崩溃跟"循环迭代"有关。

---

#### `call_chain` — 调用链

```json
"call_chain": [
  {"fn": "dxf_objects_read", "is_project": true},
  {"fn": "dwg_read_dxf",     "is_project": true},
  {"fn": "LLVMFuzzerTestOneInput", "is_project": false},
  {"fn": "main",             "is_project": false},
  {"fn": "free",             "is_project": true},
  {"fn": "dxf_free_pair",    "is_project": true},
  {"fn": "calloc",           "is_project": true},
  {"fn": "xcalloc",          "is_project": true}
]
```

**通俗解释**：从 fuzz 入口 `LLVMFuzzerTestOneInput` 一路调到崩溃函数 `dxf_objects_read`。

`is_project` 标记这个函数是"项目自己的代码"还是"框架代码"（fuzzer/`main`/`free`/`calloc`）。

**注意**：这个链表里混了三条栈（崩溃栈 + 释放栈 + 分配栈），是按报告的
`observed_frames` 去重后拼起来的。所以你会看到 `free`、`dxf_free_pair`、`calloc`、
`xcalloc` 这些**不在同一条调用路径上**的函数。

---

#### `types` — 类型信息

```json
"types": {
  "entity_type": "Dxf_Pair*",
  "cast_present": null,
  "is_signed": null,
  "ptr_origin": "unknown"
}
```

| 字段 | 值 | 含义 |
|---|---|---|
| `entity_type` | `Dxf_Pair*` | 变量的完整类型 |
| `cast_present` | `null` | 有没有强制类型转换（没查到） |
| `is_signed` | `null` | 是否是有符号类型（对 UAF 不重要） |
| `ptr_origin` | `unknown` | 指针从哪来（函数返回值/参数/全局）没判定 |

---

#### `input_reachability` — 输入怎么影响到这个变量

```json
"input_reachability": ["dat"]
```

**通俗解释**：`dxf_objects_read(dat, dwg)` 的**第一个参数 `dat`** 是输入数据流，
`pair` 最终是从 `dat` 里解析出来的。

**这是最关键的字段之一**：它告诉你"要改哪个输入"。
这里只追到了参数级（`dat`），**没追到具体的字节偏移**。

---

#### `evidence` — 证据文件位置

```json
"evidence": {
  "report": ".../ARVO-42494732/report.log",
  "cpg": "/root/gyx/mutator_create/cpg_files/libredwg_ff69eeda6658.cpg",
  "testcase_size": 256
}
```

| 字段 | 含义 |
|---|---|
| `report` | 崩溃报告原文路径 |
| `cpg` | 该版本的代码属性图（Code Property Graph，Joern 生成） |
| `testcase_size` | 触发输入 256 字节 |

**作用**：所有结论都能回查。说"515 行释放"，你可以打开 `report.log` 第 34 行核对。

---

#### `type_reconciliation` — 类型的一致性核对

```json
"type_reconciliation": {
  "report_fault_kind": "heap-use-after-free",
  "ledger_crash_type": "heap-use-after-free",
  "used": "heap-use-after-free",
  "diverged": false
}
```

| 字段 | 含义 |
|---|---|
| `report_fault_kind` | 报告里实测的类型 |
| `ledger_crash_type` | 记录表里标注的类型 |
| `used` | 实际采用的类型 |
| `diverged` | 两者是否分歧（这里 `false`，一致） |

**为什么需要这个字段**：如果报告实测和记录表标注不一致，必须有据可查用了哪个。

---

#### `completeness` — 缺失了哪些字段

```json
"completeness": ["alloc.size_expr"]
```

**通俗解释**：这份 facts 里唯一缺的是"分配时传的大小表达式"。
其他字段都拿到了。

**这个字段非常重要**：它明确了"哪些结论是有依据的、哪些是空的"，
避免后续分析把 `null` 当成"没有分配"。

---

#### `deep` — 从 CPG 深挖出的代码细节

```json
"deep": {
  "func_lines": [12260, 12293],
  "func_params": {"names": ["dat", "dwg"], "types": ["Bit_Chain*restrict", "Dwg_Data*restrict"]},
  "entity_decl": {"line": 12264, "type": "Dxf_Pair*"},
  "entity_name_cpg": "pair",
  "entity_assignments": [
    {"code": "*pair = dxf_read_pair (dat)", "line": 12264},
    {"code": "pair = new_object (...)",       "line": 12276},
    {"code": "pair = dxf_read_pair (dat)",    "line": 12288},
    {"code": "pair = NULL",                   "line": 12289}
  ],
  "guards": [{"code": "pair != NULL", "line": 12265}, ...],
  "line_calls": [{"code": "pair->code", "name": "<operator>.indirectFieldAccess", "nargs": 2}, ...],
  "line_call_count": 7,
  "line_ids": ["pair", "NULL"],
  "sites": [
    {"line": 12275, "callee": "dxf_free_pair", "args": "pair", "code": "dxf_free_pair (pair)"},
    {"line": 12282, "callee": "dxf_free_pair", "args": "pair", "code": "dxf_free_pair(pair)"},
    {"line": 12284, "callee": "dxf_free_pair", "args": "pair", "code": "dxf_free_pair (pair)"},
    {"line": 12287, "callee": "dxf_free_pair", "args": "pair", "code": "dxf_free_pair (pair)"},
    {"line": 12289, "callee": "dxf_free_pair", "args": "pair", "code": "dxf_free_pair(pair)"},
    {"line": 12291, "callee": "dxf_free_pair", "args": "pair", "code": "dxf_free_pair (pair)"},
    {"line": 12263, "callee": "<operator>.alloc", "args": "80", "code": "name[80]"},
    {"line": 12274, "callee": "strdup", "args": "pair->value.s", "code": "strdup (pair->value.s)"}
  ]
}
```

这一块是**最有价值的部分**，逐项解释：

**① `func_lines: [12260, 12293]`**
函数 `dxf_objects_read` 从 12260 行到 12293 行，共 34 行。

**② `func_params`**
函数参数是 `(Bit_Chain* restrict dat, Dwg_Data* restrict dwg)`。
这就是输入入口。

**③ `entity_assignments` — `pair` 被赋值的所有位置**

这是**判断 UAF 的核心证据**：

```
12264:  *pair = dxf_read_pair(dat)      ← 第一次从输入读
12276:  pair = new_object(...)          ← 重新指向新对象
12288:  pair = dxf_read_pair(dat)       ← 再从输入读
12289:  pair = NULL                     ← 置空
```

**关键**：515 行的 free 之后，在 **12267 行的再次读取之前**，
`pair` **没有**被重新赋值（12264 在 12267 之前，不是"free 之后"）。

**④ `guards` — 每个守卫条件所在的行**

```
12265: pair != NULL
12267: pair != NULL          ← 崩溃行
12267: pair->code == 0       ← 崩溃行
12282: pair != NULL
12282: pair->code == 0
12289: pair == NULL
12289: pair->code == 0
```

**看出来了吗**：12267 行只检查了 `pair != NULL`，
**没有任何"这块内存是否已释放"的检查**。这正是 UAF 能发生的原因。

**⑤ `line_calls` — 崩溃行表达式是怎么组合出来的**

```
pair != NULL && pair->code == 0 && pair->value.s    ← 最外层 logicalAnd
├── pair != NULL && pair->code == 0                 ← 内层 logicalAnd
│   ├── pair != NULL                                ← notEquals
│   └── pair->code == 0                             ← equals
│       └── pair->code                              ← indirectFieldAccess  ★
└── pair->value.s
    └── pair->value                                 ← indirectFieldAccess
```

**★ 这一行就是真正读内存的地方**：`pair->code`（读 2 字节）。这和报告的
`READ of size 2` 完全对得上。

**⑥ `deep.sites` — 函数内所有释放点**

```
12275: dxf_free_pair(pair)
12282: dxf_free_pair(pair)
12284: dxf_free_pair(pair)
12287: dxf_free_pair(pair)
12289: dxf_free_pair(pair)
12291: dxf_free_pair(pair)
```

**函数里有 6 处释放 `pair`！**

这一项**极其关键**，因为它和 `report` 给的"515 行释放"结合起来才能推出真正的机制：

- 报告说：`pair` 在 `dxf_free_pair` 的 **515 行**被 `free`
- CPG 说：`dxf_objects_read` 里有 **6 个地方**调用了 `dxf_free_pair(pair)`

**结合起来**：这 6 个调用点中任何一个执行了，`pair` 指向的内存就被释放；
之后如果循环再回到 12267 行读 `pair->code`，就是 UAF。

---

#### `report_extra` — 从报告 ASan 输出里直接解析的补充字段

```json
"report_extra": {
  "loc_kind": "region",
  "loc_offset": 0,
  "loc_size": 16,
  "region_size": 16,
  "shadow_byte": "fd",
  "shadow_legend_size": 21,
  "dedup_token": "dxf_objects_read--dwg_read_dxf--LLVMFuzzerTestOneInput"
}
```

| 字段 | 值 | 含义 | 报告原文 |
|---|---|---|---|
| `loc_kind` | `region` | 崩溃地址落在一块"区域"里 | `is located 0 bytes inside of` |
| `loc_offset` | 0 | 落在这块区域的**偏移 0**（即开头） | `0 bytes inside of` |
| `loc_size` | 16 | 这块区域 16 字节 | `16-byte region` |
| `region_size` | 16 | 同上（冗余字段） | — |
| `shadow_byte` | `fd` | ASan 影子字节值 | 报告影子内存里的 `[fd]` |
| `shadow_legend_size` | 21 | 报告里影子字节图例有 21 项 | `Shadow byte legend` 段落 |
| `dedup_token` | `dxf_objects_read--dwg_read_dxf--...` | 崩溃去重用的指纹（函数栈） | 从栈帧拼出来 |

**`shadow_byte = fd` 是什么意思**：

ASan 用"影子内存"记录每 8 字节的真实状态，`fd` 在图例里的含义是
**"Freed heap region"（已释放的堆区域）**。报告原文里能看到：

```
=>0x0c047fff8030: fa fa fd fd fa fa fd fd fa fa[fd]fd fa fa fd fa
                                          ↑
                                     崩溃地址对应的影子字节
```

**这是 UAF 最直接的证据**：ASan 明确告诉你"这块被标记为已释放"。

**为什么要存 `loc_offset` / `loc_size`**：它们能反推"访问是否越过边界"。
这里 `offset=0`、`size=16`、`width=2`，说明读的是区域开头 2 字节，**没有越界**——
因此这不是 buffer-overflow，而是纯粹的 UAF。

---

## 2. interpretation 是什么

**一句话**：interpretation 是在 facts 的基础上**做判断**——
把"事实"变成"这个 UAF 是怎么发生的"的结论。

文件位置：`artifacts/interpretation/<osv_id>/interpretation.json`

```json
{
  "type": "heap-use-after-free",
  "confidence": "medium",
  "key_facts": {
    "freed_ptr": "pair",
    "free_sites": [515],
    "use_site": 12267
  },
  "findings": {
    "free_sites": [515],
    "use_site": 12267,
    "crash_after_free": true,
    "reassigned_between": null,
    "alias_used": null,
    "free_arg": null,
    "free_cross_function": true
  },
  "missing": ["reassigned_between", "alias_used"],
  "reasoning": "崩溃点 12267 之前已有 free 于 [515]",
  "osv_id": "ARVO-42494732",
  "project": "libredwg",
  "crash_type": "heap-use-after-free"
}
```

### 2.1 九个字段

#### `type` — 判定的崩溃类型

值：`"heap-use-after-free"`

和 facts 的 `crash_type` 一致。但 interpretation 的 `type` 是**按类型选了一套判定逻辑**
之后产出的，比如 UAF 走 `interp_use_after_free()`，HBO 走 `interp_buffer_overflow()`。

---

#### `confidence` — 置信度

值：`"medium"`（中等）

**怎么算的**：

```python
conf = "high" if not miss else ("medium" if len(miss) <= 2 else "low")
```

`miss` 是缺失项列表。这里 `missing` 有 2 项 → `medium`。

| 缺失数 | 置信度 |
|---|---|
| 0 | high |
| 1–2 | medium |
| ≥3 | low |

**通俗解释**：有 2 个关键判断做不了，所以只能给"中等"。

---

#### `key_facts` — 三个最核心的数字

```json
"key_facts": {
  "freed_ptr": "pair",     ← 哪个指针
  "free_sites": [515],     ← 在哪释放（行号）
  "use_site": 12267        ← 在哪被用（行号）
}
```

**这是整个 UAF 的最小描述**：`pair` 在 515 行释放，在 12267 行被用。

**`free_sites` 只算了 515**，注意——这是**报告给的那一个**。
`deep.sites` 里那 6 个调用点没有被合并进来（这是当前实现的一个局限）。

---

#### `findings` — 判定结果明细

| 字段 | 值 | 含义 | 怎么算的 |
|---|---|---|---|
| `free_sites` | `[515]` | 所有释放行号 | 从 `facts.sites` 里挑 `kind=="free"` 的 |
| `use_site` | `12267` | 崩溃行 | `facts.crash.site.line` |
| **`crash_after_free`** | **`true`** | **崩溃发生在释放之后** | 存在 `free_line < crash_line` |
| **`reassigned_between`** | **`null`** | **释放与崩溃之间有没有重新赋值** | **查不到** |
| `alias_used` | `null` | 释放的是不是别名指针 | 查不到（`free_arg` 为空） |
| `free_arg` | `null` | free 的实参名 | 报告给的 free 点没有代码文本 |
| `free_cross_function` | `true` | 释放和崩溃是否跨函数 | `dxf_free_pair` ≠ `dxf_objects_read` |

**最重要的两个**：

**① `crash_after_free: true`**
这是 UAF 成立的**必要条件**：释放（515）在崩溃（12267）之前。判定逻辑很简单：

```python
frees_before = [x for x in frees if crash and x < crash]
"crash_after_free": bool(frees_before)
```

**② `reassigned_between: null`**
这是**最关键但没算出来**的项。它想问的是：

> 515 行释放之后、12267 行使用之前，`pair` 有没有被重新赋值？

如果**有** → 那不是 UAF（指针已经指向新对象了）
如果**没有** → 确认是 UAF

判定逻辑本来是这样：

```python
def _reassign_between(f, a, b):
    assigns = f["deep"]["entity_assignments"]
    if assigns:
        return any(a < x["line"] < b for x in assigns)
    return None
```

现在 `entity_assignments` 是有的（4 条：12264、12276、12288、12289），
**但都不在 515 和 12267 之间**（515 < 12267，而 12264 在 12267 之前、515 之后？

等一下——12264 确实落在 (515, 12267) 这个区间里！

**但 12264 是 `*pair = dxf_read_pair(dat)`，是给 `*pair` 赋值（写指针指向的内容），
不是给 `pair` 赋值。** 这段逻辑没能区分 `pair` 和 `*pair`，所以直接返回 `null` 更安全。

---

#### `missing` — 缺失的判据

```json
"missing": ["reassigned_between", "alias_used"]
```

| 缺失项 | 影响 |
|---|---|
| `reassigned_between` | 无法 100% 确认"释放后没重新赋值" |
| `alias_used` | 无法判断是否有别名指针 |

**通俗解释**：这两项没法判定，所以 `confidence` 只能是 `medium`。

---

#### `reasoning` — 一句话结论

```
"崩溃点 12267 之前已有 free 于 [515]"
```

**这就是可读版的核心结论**。它由代码直接拼出来：

```python
"reasoning": (f"崩溃点 {crash} 之前已有 free 于 {frees_before}" if frees_before
              else f"未在 facts 中找到崩溃点之前的 free，需补 free 栈")
```

---

#### `osv_id` / `project` / `crash_type`

从 facts 直接复制，便于单独使用 interpretation 时不丢上下文。

---

## 3. facts 是怎么提取出来的

### 3.1 三份输入

```
build_facts.py 的 build(osv, rep, df, led)
                              │    │   └── records（记录表）
                              │    └────── crash_report_features（报告解析结果）
                              └─────────── deep（CPG 深挖结果）
```

| 简称 | 文件 | 内容 |
|---|---|---|
| `rep` | `crash_report_features.jsonl` | 从 `report.log` 用正则解析出的 66 个字段 |
| `df` | `deep_fields.jsonl` | 从 CPG（Joern）查出的代码结构 |
| `led` | `reproduced_crashes.jsonl` | 记录表（项目/提交/CPG 路径/输入大小） |

### 3.2 逐字段的来源映射

| facts 字段 | 来自 | 具体怎么取 |
|---|---|---|
| `osv_id` | 参数 | 直接传入 |
| `project` | `rep` / `led` | 先取报告里的，没有就取记录表 |
| `crash_type` | `rep.fault_kind` | 归一化后查别名表 |
| `entity.name` | `df.ids` | 取崩溃行表达式里的第一个标识符 |
| `entity.decl` | `deep.entity_decl` | CPG 的变量声明节点 |
| `alloc` | `rep` | `alloc_fn` / `alloc_file` / `alloc_line` / `region_size` |
| `sites[free]` | `rep` | 报告 "freed by" 栈的 `free_fn` / `free_line` |
| `sites[crash]` | `rep` + `df` | 报告的 `fault_site_*` + CPG 的 `call_codes` |
| `sites[cpg]` | `deep.sites` | CPG 扫出的释放/拷贝调用 |
| `crash.code` | `df.call_codes` | CPG 对该行的表达式分解 |
| `crash.access` | `rep` | `access_dir` / `access_width` / `region_size` |
| `context.in_loop` | `df.in_loop` | CPG 判断该行是否在循环内 |
| `context.guards` | `df.cmp_guard_codes` | CPG 提取的守卫条件 |
| `context.control_structures` | `deep` | CPG 的循环/分支位置清单 |
| `call_chain` | `led.observed_frames` | 报告里 recover 的栈帧，去重后加 `is_project` 标记 |
| `types` | `deep` | CPG 的类型信息 |
| `input_reachability` | `df.reachability` | CPG 的反向可达分析 |
| `evidence` | `led` / `rep` | 报告路径、CPG 路径、输入大小 |
| `type_reconciliation` | `rep` + `led` | 两边类型对比 |
| `completeness` | **算出** | 检查哪些字段还是 `null` |
| `deep` | `deep_fields` | CPG 原始结果合并 |
| `report_extra` | `rep` | 报告的 ASan 输出解析 |

### 3.3 两个关键设计

**① `crash_type` 以报告实测为准**

```python
fk = rep.get("fault_kind")
ctype = TYPE_ALIAS.get(_norm(fk), _norm(fk)) if fk else None
if not ctype:
    ctype = rep.get("crash_type_norm") or led.get("crash_type_norm")
```

记录表里可能是 ARVO 标注的"预期类型"，报告里才是"实际触发的类型"。
两者不一致时以实测为准，并把分歧记进 `type_reconciliation.diverged`。

**② `completeness` 是自动算出来的**

```python
miss = []
if not facts["entity"]["decl"]: miss.append("entity.decl")
if facts["entity"]["storage"] is None: miss.append("entity.storage")
if alloc and not alloc["size_expr"]: miss.append("alloc.size_expr")
if not alloc and storage == "heap": miss.append("alloc")
...
facts["completeness"] = miss
```

**这个字段的价值**：后续任何分析都能先问一句"这个字段缺不缺"，避免把 `null`
误读成"不存在"。

---

## 4. interpretation 是怎么提取出来的

### 4.1 核心特点：**不读原始数据，只读 facts**

```
interpret.py 只输入 facts.json
              ↓
      按 crash_type 选一个派生函数
              ↓
      输出 interpretation.json
```

**这保证了**：interpretation 的每个结论都能追溯到 facts 的某个字段，
不会凭空出现 facts 里没有的信息。

### 4.2 按类型分派

```python
DISPATCH = {
  "heap-use-after-free":    interp_use_after_free,
  "heap-buffer-overflow":   interp_buffer_overflow,
  "stack-buffer-overflow":  interp_buffer_overflow,
  "global-buffer-overflow": interp_buffer_overflow,
  "double-free":            interp_double_free,
  "invalid-free":           interp_invalid_free,
  ...
}
```

我们这个崩溃走 `interp_use_after_free()`。

### 4.3 UAF 判定的五步

```python
def interp_use_after_free(f):
    # ① 找出所有 free 的行号
    frees = _free_sites(f)                    # → [515]

    # ② 找出崩溃的行号
    crash = _crash_line(f)                    # → 12267

    # ③ 判断：有没有 free 在崩溃之前
    frees_before = [x for x in frees if crash and x < crash]
    # → [515]，所以 True

    # ④ 判断：free 的实参是不是别名
    free_arg = _free_arg(f)                   # → None（报告没给代码）
    alias = (free_arg != ent) if free_arg and ent else None
    # → None（算不了）

    # ⑤ 判断：free 和 crash 之间有没有重新赋值
    reassigned = _reassign_between(f, max(frees_before), crash)
    # → None（见 2.1 的解释）

    # 汇总
    findings = {
        "free_sites": frees,
        "use_site": crash,
        "crash_after_free": bool(frees_before),   # True
        "reassigned_between": reassigned,         # None
        "alias_used": alias,                      # None
        "free_arg": free_arg,                     # None
        "free_cross_function": <fn 不同?>          # True
    }
```

### 4.4 置信度怎么算

```python
miss = _missing_common(f)          # 常见缺失：entity.decl、types.entity_type
if not frees: miss.append("free_sites")
if findings["reassigned_between"] is None: miss.append("reassigned_between")
if findings["alias_used"] is None: miss.append("alias_used")

conf = "high" if not miss else ("medium" if len(miss) <= 2 else "low")
```

本例：`entity.decl` 有（12264）、`types.entity_type` 有（`Dxf_Pair*`）、
`free_sites` 有（515）→ 只缺 `reassigned_between` 和 `alias_used` 两项 → **medium**。

### 4.5 一句话结论怎么生成

```python
reasoning = (f"崩溃点 {crash} 之前已有 free 于 {frees_before}" if frees_before
             else f"未在 facts 中找到崩溃点之前的 free，需补 free 栈")
```

→ `"崩溃点 12267 之前已有 free 于 [515]"`

---

## 5. facts 与 interpretation 的分工

| 维度 | facts | interpretation |
|---|---|---|
| **性质** | 事实（可观测） | 判断（推断） |
| **是否读原始数据** | 读（报告 + CPG + 记录表） | **不读**，只读 facts |
| **能否编造** | 不能（每个值都能回查报告/CPG） | 不能（每个结论都引用 facts 字段） |
| **产物** | 1,139 条 × 15 字段 | 1,139 条 × 9 字段 |
| **缺失处理** | 记进 `completeness` | 记进 `missing` + 降 `confidence` |

**打个比方**：

- **facts** = 案发现场的勘查记录（在哪里、什么时间、什么东西）
- **interpretation** = 根据勘查记录写出的初步结论（"先被释放，后被使用，所以是 UAF"）

**interpretation 不能比 facts 知道得更多**。比如 facts 没查到"释放后有没有重新赋值"，
interpretation 就只能是 `null`，并且降低置信度——而不是猜一个值。

---

## 6. 一条完整链路示例

以 `free_cross_function` 这个字段为例，从原始数据到最终结论：

```
① 报告原文
   freed by thread T0 here:
       #1 ... dxf_free_pair /src/libredwg/src/in_dxf.c:515

② extract_crash_features.py 正则解析
   free_fn   = "dxf_free_pair"
   free_line = 515

③ build_facts.py 组装
   sites = [{"kind": "free", "fn": "dxf_free_pair", "line": 515,
             "origin": "report:freed_by"}]

④ interpret.py 判定
   free_fns  = {"dxf_free_pair"}
   crash_fn  = "dxf_objects_read"
   findings["free_cross_function"] = (crash_fn not in free_fns) = True

⑤ 输出
   "free_cross_function": true
```

**每一步都能验证**：你可以打开 `report.log` 看到 515 行，
打开 `facts.jsonl` 看到 `sites`，打开 `interpretation.json` 看到 `true`。

---

## 7. 这份数据的局限（如实说明）

| 局限 | 影响 | 当前状态 |
|---|---|---|
| `alloc.size_expr` 缺 | 不知道分配大小的表达式 | 记在 `completeness` |
| `reassigned_between` 算不出 | 不能 100% 确认"释放后没重新赋值" | 记在 `missing`，降置信度 |
| `free_arg` 为空 | 不知道 free 的是不是别名 | 记在 `missing` |
| `deep.sites` 的 6 个释放点没进 `free_sites` | `free_sites` 只有报告的 515，漏掉函数内其它 6 处 | **已知缺口** |
| `input_reachability` 只到参数级 | 不知道具体是哪几个字节控制 | 停在 `["dat"]` |
| `call_chain` 混了三条栈 | 看起来像"调用顺序"但其实不是 | 已知，需按 `origin` 区分 |

**最后一条尤其要注意**：`call_chain` 里 `dxf_objects_read → dwg_read_dxf →
LLVMFuzzerTestOneInput` 是崩溃栈，
而 `free → dxf_free_pair → calloc → xcalloc` 是释放栈和分配栈拼进来的。
**它们不是一条调用路径**，阅读时不要误解。

---

## 附：文件位置

| 内容 | 路径 |
|---|---|
| facts | `artifacts/facts.jsonl` |
| interpretation | `artifacts/interpretation/<osv_id>/interpretation.json` |
| 报告解析结果 | `artifacts/crash_report_features.jsonl` |
| CPG 深挖结果 | `artifacts/deep_fields.jsonl` |
| 构建脚本 | `build_facts.py`（249 行） |
| 解释脚本 | `interpret.py`（367 行） |
| 报告原文 | `reproduce_crash/artifacts/by_crash_type/<type>/<project>/<sanitizer>/<commit>/<osv_id>/report.log` |

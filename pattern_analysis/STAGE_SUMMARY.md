# 基于已知崩溃的模糊测试变异器增强 — 阶段性总结

**文档版本**：v1.0
**编写日期**：2026-10-27
**覆盖阶段**：崩溃复现 → 信息提取 → 事实整合 → LLM 共性提取（阶段 3）

---

# 目录

- [一、复现崩溃的基本情况](#一复现崩溃的基本情况)
- [二、从崩溃报告与代码属性图（CPG）中获取的信息](#二从崩溃报告与代码属性图cpg中获取的信息)
- [三、facts 与 interpretation 的生成](#三facts-与-interpretation-的生成)
- [四、LLM 分析阶段（阶段 3）](#四llm-分析阶段阶段-3)
- [五、阶段性结论与后续工作](#五阶段性结论与后续工作)
- [附录 A：文件与目录索引](#附录-a文件与目录索引)

---

# 一、复现崩溃的基本情况

## 1.1 数据来源

本项目使用两个公开的崩溃数据集，合并存放在同一张复现记录表中。

### 1.1.1 ARVO 数据集

ARVO 是一个可复现的漏洞数据集，每条记录包含：

| 字段 | 含义 |
|---|---|
| `localId` | 数据集内唯一编号 |
| `project` | 开源项目名 |
| `repo_addr` | 代码仓库地址 |
| `fuzz_target` | 模糊测试目标程序 |
| `sanitizer` | 使用的检测器（ASan / UBSan / MSan） |
| `crash_type` | 崩溃类型 |
| `crash_output` | 崩溃时的原始输出 |
| `fix_commit` | 修复该漏洞的提交 |

**数据规模**：6,138 条崩溃记录，覆盖 **311 个开源项目**。

数据库位置：`/root/gyx/arvo/data/arvo.db`（SQLite，表名 `arvo`）

### 1.1.2 OSV 数据集

OSV（Open Source Vulnerabilities）是 Google 维护的开源漏洞数据库。本项目用它补充 ARVO 未覆盖的模糊测试崩溃。

**记录位置**：与 ARVO 合并存放在同一张复现记录表中。

### 1.1.3 已复现崩溃的数据集

**文件**：`/root/gyx/mutator_create/pattern_analysis/artifacts/reproduced_crashes.jsonl`

**内容**：每个已复现的崩溃一行，共 **1,154 条**（ARVO 915 + OSV 239），已按 `osv_id` 去重。

**字段说明**：

| 字段 | 内容 | 覆盖率 |
|---|---|---|
| `osv_id` | 崩溃唯一标识 | 100% |
| `source` | 来源（ARVO / OSV） | 100% |
| `project` | 项目名 | 100% |
| `fuzz_target` | 模糊测试目标程序 | — |
| `sanitizer` | 检测器（address / undefined 等） | — |
| `crash_type` | 崩溃类型 | — |
| `repo_url` | 代码仓库地址 | **100%** |
| `pin_commit` | 漏洞版本提交（前 12 位） | **98%** |
| `fix_commit` | 修复提交 | **98%** |
| `fault_file` / `fault_fn` / `fault_line` | 崩溃位置 | 97% |
| `testcase_size` | 触发所需的输入字节数 | — |
| `cpg_path` | 对应的 CPG 文件路径 | **80%** |
| `report_path` | 崩溃报告文件路径 | **99%** |
| `has_facts` | 是否已生成 facts | 1,139 / 1,154 |
| `has_deep` | 是否有深度查询结果 | 756 / 1,154 |
| `has_interpretation` | 是否已生成 interpretation | 1,139 / 1,154 |

**一条记录的真实内容**：

```json
{
  "osv_id": "ARVO-368076871",
  "source": "ARVO",
  "project": "mruby",
  "fuzz_target": "mruby_fuzzer",
  "sanitizer": "address",
  "crash_type": "segv-on-unknown-address",
  "repo_url": "https://github.com/mruby/mruby",
  "pin_commit": "f6caf0d78854",
  "fix_commit": "11cff8fa7d25f6d114a0784ce478643586a8af5f",
  "fault_file": "/src/mruby/mrbgems/mruby-bigint/core/bigint.c",
  "fault_fn": "udiv",
  "fault_line": 499,
  "testcase_size": 286,
  "cpg_path": "/root/gyx/mutator_create/cpg_files/mruby_f6caf0d78854.cpg",
  "report_path": "/root/gyx/mutator_create/reproduce_crash/artifacts/.../report.log",
  "has_facts": true,
  "has_deep": false,
  "has_interpretation": true
}
```

**这份数据与后续产物的关系**：

```
reproduced_crashes.jsonl（1,154 条，已去重的崩溃清单）
        │
        ├── facts.jsonl            1,139 条（15 条因报告缺失未生成）
        ├── interpretation/        1,139 条
        └── deep_fields.jsonl        756 条
```

**说明**：生成这份数据的原始输入是复现过程的执行日志（`reproduce_crash/repro_dataset.jsonl`），那份日志按"尝试"记行、存在重复；本文件已按 `osv_id` 去重并补齐仓库地址、提交、CPG 路径等字段，是后续所有分析的起点。

## 1.3 崩溃类型分布

对上述 932 条成功复现的记录进行报告解析后，得到 **1,139 条**可用于分析的事故记录（脚本：`/root/gyx/mutator_create/pattern_analysis/extract_crash_features.py`）。

**类型分布**（完整表）：

| 崩溃类型 | 数量 |
|---|---|
| heap-buffer-overflow | **601** |
| segv-on-unknown-address | 158 |
| heap-use-after-free | **121** |
| stack-buffer-overflow | **110** |
| global-buffer-overflow | **51** |
| heap-double-free | 19 |
| negative-size-param | 14 |
| use-of-uninitialized-value | 14 |
| use-after-poison | 13 |
| stack-use-after-return | 12 |
| invalid-free | 8 |
| memcpy-param-overlap | 6 |
| stack-buffer-underflow | 3 |
| dynamic-stack-buffer-overflow | 2 |
| container-overflow | 2 |
| abrt | 2 |
| ill | 1 |
| ubsan-runtime-error | 1 |
| unknown | 1 |
| **合计** | **1,139** |

**分析重点**：选择样本数超过 50 的 **4 个类型**作为分析对象：

| 类型 | 数量 | 选择理由 |
|---|---|---|
| heap-buffer-overflow | 601 | 样本最多，机制最典型 |
| heap-use-after-free | 121 | 机制链条清晰，易于验证 |
| stack-buffer-overflow | 110 | 与堆溢出机制不同，值得对比 |
| global-buffer-overflow | 51 | 多为查表类越界，机制独特 |
| **合计** | **883** | 占全部样本的 77.5% |

## 1.4 项目分布

1,139 条记录覆盖 **60 个开源项目**，前 10 位：

| 项目 | 记录数 |
|---|---|
| c-blosc2 | 100 |
| ndpi | 80 |
| opensc | 63 |
| harfbuzz | 56 |
| libavc | 56 |
| mruby | 46 |
| libredwg | 44 |
| hdf5 | 38 |
| fluent-bit | 36 |
| libxml2 | 34 |

---

# 二、从崩溃报告与代码属性图（CPG）中获取的信息

本项目的信息来源有两条独立通道：

```
崩溃报告（ASan/UBSan 输出文本）  ──┐
                                    ├──→ facts（事实层）
代码属性图（CPG，Joern 生成）    ──┘
```

两者提供的信息互补：**崩溃报告给出"发生了什么"，CPG 给出"代码长什么样"**。

## 2.1 崩溃报告解析

**目的**：从 ASan/UBSan 的文本输出中提取崩溃的客观特征。

**脚本**：`/root/gyx/mutator_create/pattern_analysis/extract_crash_features.py`

**解析方法**：

ASan 的输出是有固定格式的文本，例如：

```
==12345==ERROR: AddressSanitizer: heap-buffer-overflow on address 0x6020000000f4
READ of size 4 at 0x6020000000f4 thread T0
    #0 0x4f2a1b in process_page_ /src/flac/src/libFLAC/ogg_decoder_aspect.c:130:12
    ...
0x6020000000f4 is located 0 bytes to the right of 64-byte region
allocated by thread T0 here:
    #0 0x4d8b0f in malloc (...)
    #1 0x4f1a2c in xmlFuzzMalloc /src/libxml2/fuzz/fuzz.c:81:20
```

解析器按行匹配以下模式：

| 目标信息 | 匹配模式 | 提取结果 |
|---|---|---|
| 崩溃类型 | `ERROR: AddressSanitizer: (\S+)` | `heap-buffer-overflow` |
| 访问方向 | `(READ|WRITE) of size (\d+)` | `READ`, `4` |
| 故障地址 | `on address (0x[0-9a-f]+)` | `0x6020000000f4` |
| 故障位置 | `#0 .* in (\S+) (\S+):(\d+)` | 函数名、文件、行号 |
| 区域大小 | `(\d+)-byte region` | `64` |
| 分配栈 | `allocated by thread .* here:` 之后的 `#N` 行 | 分配调用链 |
| 释放栈 | `freed by thread .* here:` 之后的 `#N` 行 | 释放调用链 |
| 影子字节 | `Shadow bytes around the buggy address:` 段的字节 | 用于推算边界 |
| 全局变量 | `is located .* in (\S+) global variable` | 全局对象名、大小 |

**提取结果**：每条崩溃产出 **66 个字段**，输出到：

- 汇总文件：`artifacts/crash_report_features.jsonl`
- 单崩溃文件：`artifacts/crash_report/<OSV_ID>/crash_report.json`

**字段分组**：

| 分组 | 代表字段 | 数量 |
|---|---|---|
| 崩溃定位 | `fault_file` / `fault_fn` / `fault_line` / `fault_col` | 6 |
| 访问特征 | `access_dir` / `access_width` / `shadow_byte` / `shadow_fault_addr` | 8 |
| 分配信息 | `alloc_file` / `alloc_fn` / `alloc_line` / `region_size` / `has_alloc_stack` | 9 |
| 释放信息 | `free_file` / `free_fn` / `free_line` / `free_n_frames` / `has_free_stack` | 8 |
| 全局对象 | `loc_dir` / `loc_global_file` / `loc_global_var` / `loc_kind` / `loc_offset` / `loc_size` | 6 |
| 调用链 | `n_frames` / `n_project_frames` / `harness_idx` | 4 |
| 类型归一 | `crash_type_norm` / `observed_crash_type` / `fault_kind` | 3 |
| 其他 | `dedup_token` / `scariness` / `testcase_size` / `sanitizer` | 若干 |

**关键覆盖率实测**（4 个重点类型）：

| 字段 | HBO (601) | UAF (121) | stack (110) | global (51) |
|---|---|---|---|---|
| `shadow_byte` | 86% | 90% | 91% | 92% |
| `region_size` | 1% | 95% | 0% | 0% |
| `loc_size` | 22% | 98% | 0% | 22% |
| `loc_global_var` | 0% | 0% | 0% | 22% |
| `dedup_token` | 100% | 100% | 100% | 100% |

**实现要点**：

- ASan 与 UBSan 的输出格式不同，需分别处理；
- 崩溃类型存在别名（如 `SEGV` → `segv-on-unknown-address`），需归一化；
- 分配/释放栈可能包含 harness 自身的帧，需用 `project` 字段判断哪些帧属于被测项目。

## 2.2 代码属性图（CPG）构建

**目的**：把源码解析成可查询的图结构，用于后续的语法与数据流查询。

**工具**：Joern 4.0.150 + `c2cpg`（C/C++ 前端）

**构建方式**：在复现容器内执行

```bash
c2cpg /src -o /out/cpg.bin
```

**构建结果**：

| 项 | 数值 |
|---|---|
| CPG 文件数 | **689** |
| 总大小 | **9.8 GB** |
| 位置 | `/root/gyx/mutator_create/cpg_files/<项目>_<提交前12位>.cpg` |

**说明**：

- CPG 按"项目 + 提交"生成，多个崩溃可能共享同一个 CPG；
- 792 条崩溃对应约 470 个唯一 CPG；
- 有 83 条崩溃因源码缺失/编译失败无法生成 CPG。

**CPG 的节点类型**（本项目的查询只用到以下几种）：

| 节点标签 | 含义 |
|---|---|
| `METHOD` | 函数 |
| `CALL` | 函数调用 / 运算符 |
| `IDENTIFIER` | 变量引用 |
| `LITERAL` | 字面量 |
| `LOCAL` | 局部变量声明 |
| `PARAMETER` | 函数参数 |
| `CONTROL_STRUCTURE` | 控制结构（if/for/while/switch） |
| `TYPE_DECL` / `MEMBER` | 类型与成员声明 |

## 2.3 CPG 数据流查询

**目的**：从 CPG 中提取与崩溃点相关的代码结构信息。

**脚本**：`/root/gyx/mutator_create/pattern_analysis/analyze_cpg_par.py`（4 进程并行）

**查询方法**：

对每条崩溃，定位到故障函数与故障行，然后在 CPG 上执行 Scala 查询：

```scala
val m = cpg.method.nameExact(fault_fn).l.head
// 1) 该行的所有调用
m.ast.isCall.lineNumber(fault_line).l
// 2) 该行的所有变量
m.ast.isIdentifier.lineNumber(fault_line).l
// 3) 与变量相关的比较（边界检查）
m.ast.isCall.name("<operator>.lessThan|...").l
// 4) 变量能否由函数参数到达
m.ast.isIdentifier.name(变量).reachableBy(cpg.parameter).l
// 5) 是否在循环内
m.ast.isControlStructure.controlStructureType("FOR|WHILE")
```

**提取结果**：每条崩溃产出 **27 个字段**，输出到：

- 汇总文件：`artifacts/dataflow_features.jsonl`
- 单崩溃文件：`artifacts/dataflow/<OSV_ID>/dataflow.json`

**字段分组**：

| 分组 | 字段 | 用途 |
|---|---|---|
| 位置 | `fault_site_fn` / `fault_site_line` / `method` | 定位 |
| 语法 | `ids` / `line_ids` / `calls` / `call_codes` / `calls_at_line` | 该行有哪些变量与调用 |
| 类型 | `params` / `nparams` | 函数签名 |
| 控制流 | `in_loop` / `guard` / `cmp_guard_codes` | 是否在循环内、有哪些比较 |
| 可达性 | `reachability` | 哪些参数能到达该变量 |
| 元素级 | `line_nodes` | 该行的 CPG 节点编号 |
| 元信息 | `vuln_commit` / `fix_commit` / `src_head` / `commit_source` | 版本追溯 |

**工程要点**：

- 单进程串行耗时过长，改为 4 进程并行；
- 单个 CPG 超过 40 MB 时跳过（如 wireshark 的 162 MB CPG 会导致 JVM 内存溢出）；
- 单次查询超时 1800 秒；
- 支持断点续跑（已处理的样本跳过）。

## 2.4 深度查询

**目的**：补齐前两步遗漏的字段，特别是分配函数的实参、变量赋值历史、函数参数。

**两个脚本**：

| 脚本 | 内容 |
|---|---|
| `/root/gyx/mutator_create/pattern_analysis/deepen_facts_par.py` | 释放点关系（多次 free 之间的重赋值、重分配） |
| `/root/gyx/mutator_create/pattern_analysis/add_deep_fields.py` | 故障行完整代码、变量赋值历史、分配/释放调用（含包装函数）、比较表达式、函数参数 |

**`add_deep_fields.py` 的查询内容**：

| 查询 | 输出字段 | 用途 |
|---|---|---|
| 故障行所有调用 | `line_calls`（名称/代码/实参数） | 还原故障语句 |
| 故障行所有变量 | `line_ids` | 定位被操作对象 |
| 变量声明 | `entity_decl`（类型/行号） | 判断是数组还是指针 |
| 变量赋值历史 | `entity_assignments` | 判断释放后是否被重赋值 |
| 分配/释放调用 | `sites`（含 `callee` / `line` / `code` / `args`） | **含包装函数**（如 `xmlFuzzMalloc`） |
| 比较表达式 | `guards` | 判断是否有边界检查 |
| 函数参数 | `func_params`（名称/类型） | 判断输入入口 |

**结果**：`artifacts/deep_fields.jsonl`，**756 条**（覆盖率 756/902 = 84%）

**未覆盖的 146 条**：
- 83 条无 CPG；
- 63 条查询失败（函数名在 CPG 中匹配不到，或 CPG 过大被跳过）。

## 2.5 两条通道的分工

| 信息 | 崩溃报告 | CPG |
|---|---|---|
| 崩溃发生在哪个函数/行 | ✅ | ✅ |
| 访问方向与宽度 | ✅ | ❌ |
| 分配区域大小 | 部分 | ❌ |
| 影子字节（边界提示） | ✅ | ❌ |
| 全局变量名 | 部分 | ✅ |
| 分配/释放的完整调用栈 | ✅ | ❌ |
| 故障行的完整代码 | ❌ | ✅ |
| 该行有哪些变量 | ❌ | ✅ |
| 变量是否被重新赋值 | ❌ | ✅ |
| 分配函数的实参 | ❌ | ✅ |
| 是否有边界检查 | 部分 | ✅ |
| 输入能否到达 | ❌ | ✅ |

**结论：两条通道缺一不可。**

---

# 三、facts 与 interpretation 的生成

## 3.1 两层设计的由来

最初的方案是把所有信息塞进一个文件。实践中发现两个问题：

1. **字段含义混杂**：既有"客观事实"（崩溃在第几行），又有"主观判断"（是否满足某条件）；
2. **类型差异大**：UAF 关心"释放后是否重赋值"，HBO 关心"缓冲区多大"，字段需求完全不同。

因此拆成两层：

```
┌──────────────────────────────────────────────┐
│ facts（事实层）                               │
│  · 所有崩溃共用同一套字段结构                  │
│  · 只记录客观事实，不做判断                     │
│  · 与崩溃类型无关                              │
└──────────────────────────────────────────────┘
                    ↓ 派生
┌──────────────────────────────────────────────┐
│ interpretation（解释层）                      │
│  · 按崩溃类型分别生成                          │
│  · 对每类崩溃的"必要条件"逐条给出判定           │
│  · 判定结果可以是 true / false / null（数据缺失）│
└──────────────────────────────────────────────┘
```

## 3.2 facts 的结构

**生成脚本**：`/root/gyx/mutator_create/pattern_analysis/build_facts.py`

**输出**：

- 汇总文件：`artifacts/facts.jsonl`（1,139 行）
- 单崩溃文件：`artifacts/facts/<OSV_ID>/facts.json`（1,139 个）

**字段结构**（15 个顶层字段）：

| 字段 | 内容 | 来源 |
|---|---|---|
| `osv_id` | 崩溃唯一标识 | ARVO |
| `project` | 项目名 | ARVO |
| `crash_type` | 归一化后的崩溃类型 | 报告解析 |
| `crash` | 崩溃点：`site`（文件/函数/行）、`code`（该行代码）、`access`（方向/宽度/区域大小） | 报告 + CPG |
| `entity` | 被操作对象：`name` / `kind` / `storage`（堆/栈/全局）/ `decl`（声明类型与行号） | 报告 + CPG |
| `alloc` | 分配点：`api` / `site` / `size_bytes` / `size_expr` / `cross_function` | 报告 + CPG |
| `sites` | 所有释放/使用点：`kind` / `fn` / `line` / `code` / `args` / `origin` | 报告 + CPG |
| `context` | 上下文：`fn` / `in_loop` / `loop_type` / `guards` / `guard_count` / `control_structures` | CPG |
| `call_chain` | 完整调用栈（每帧：函数/文件/行/是否属于被测项目） | 报告 |
| `input_reachability` | 输入能到达的参数列表 | CPG |
| `types` | 类型信息：`entity_type` / `cast_present` / `is_signed` / `ptr_origin` | 报告 + CPG |
| `completeness` | 缺失字段列表 | 计算 |
| `evidence` | 证据路径：`cpg` / `report` / `testcase_size` | 记录 |
| `type_reconciliation` | 报告类型与账本类型是否一致 | 计算 |
| `report_extra` | 崩溃报告中的补充字段（影子字节、全局变量名等 9 项） | 报告 |

**设计原则**：

1. **只填空不覆盖**：后续的深度查询结果只填补空缺字段，不覆盖已有值；
2. **保留原始证据**：`evidence` 记录 CPG 与报告文件的绝对路径，便于追溯；
3. **缺失显式化**：`completeness` 明确列出缺了哪些字段，而不是用默认值填充。

## 3.3 facts 的生成流程

```
复现记录表（repro_dataset.jsonl）
        │
        ├── 崩溃报告 ──→ crash_report_features.jsonl
        │                       │
        └── CPG ─────→ dataflow_features.jsonl
                                │
                                ↓
                        build_facts.py（合并 + 归一 + 计算）
                                │
                                ↓
                          facts.jsonl
                                │
                    ┌───────────┴───────────┐
                    ↓                       ↓
          deepen_facts_par.py      add_deep_fields.py
          （释放点关系）            （深度代码信息）
                    │                       │
                    └───────────┬───────────┘
                                ↓
                    merge_deep_fields.py（合并，只填空）
                                │
                                ↓
                        facts.jsonl（最终）
```

**关键工程决策**：

- `build_facts.py` 必须**合并**已有字段，不能整体重建（曾因整体重建丢失 235 组深度查询结果）；
- `merge_deep_fields.py` 使用 `f.get("alloc") or {}` 而不是 `setdefault`，因为部分 facts 的 `alloc` 值为 `null`。

## 3.4 interpretation 的结构

**生成脚本**：`/root/gyx/mutator_create/pattern_analysis/interpret.py`

**输出**：

- 汇总文件：`artifacts/interpretation.jsonl`（1,139 行）
- 单崩溃文件：`artifacts/interpretation/<OSV_ID>/interpretation.json`（1,139 个）

**字段结构**（9 个顶层字段）：

| 字段 | 内容 |
|---|---|
| `osv_id` / `project` / `crash_type` | 标识 |
| `type` | 该条解释所依据的崩溃类型 |
| `confidence` | 置信度（high / medium / low，由缺失字段数量决定） |
| `key_facts` | 该类型最关键的事实（如 UAF 的 `freed_ptr` / `free_sites` / `use_site`） |
| `findings` | **必要条件逐条判定**（true / false / null） |
| `missing` | 哪些条件因数据缺失无法判定 |
| `reasoning` | 判定理由（一句话） |

**以 UAF 为例的 `findings` 结构**：

| 字段 | 含义 | 数据来源 |
|---|---|---|
| `free_sites` | 释放点行号列表 | `facts.sites` |
| `use_site` | 使用点行号 | `facts.crash.site.line` |
| `crash_after_free` | 释放是否早于使用 | 行号比较 + `in_loop` |
| `reassigned_between` | 中间是否被重新赋值 | `deep.entity_assignments` |
| `alias_used` | 是否通过别名使用 | `sites[].args` 与 `entity.name` 比较 |
| `free_arg` | free 的实参名 | `sites[].args` |
| `free_cross_function` | 释放与使用是否跨函数 | `sites[].fn` 与 `crash.site.fn` 比较 |

## 3.5 两层的对应关系（以 UAF 为例）

| 必要条件 | 判定字段 | 实测覆盖率 |
|---|---|---|
| N1 对象是堆分配 | `entity.storage = heap` | 100% |
| N2 存在 free 调用 | `free_sites` 非空 | 100% |
| N3 free 早于使用 | `crash_after_free` | 100% |
| N4 中间无重赋值 | `reassigned_between` | 约 25%（依赖深度查询） |
| N5 中间无重新分配 | 同上 | 同上 |
| N6 free 实参是对象本身 | `free_arg` | 约 30% |
| N7 使用与释放是同一对象 | `alias_used` | 约 30% |

## 3.6 数据质量的已知边界

| 限制 | 数量 | 原因 |
|---|---|---|
| 无 CPG | 83 条 | 源码缺失或编译失败 |
| 深度查询失败 | 63 条 | 函数名不匹配或 CPG 过大 |
| 无 `region_size`（HBO） | 约 99% | 报告格式中无此行 |
| 无 `loc_global_var` | 约 78% | 报告未给出全局变量名 |

**以上为当前数据质量的实际边界。**

---

# 四、LLM 分析阶段（阶段 3）

> 本章的配套文件：
> - `/root/gyx/mutator_create/pattern_analysis/LLM_ANALYSIS.md`（完整流程说明，630 行）
> - `/root/gyx/mutator_create/pattern_analysis/prompts/stage3_extract_patterns.md`（分批提取 prompt）
> - `/root/gyx/mutator_create/pattern_analysis/prompts/stage3_merge_patterns.md`（跨批汇总 prompt）
> - `/root/gyx/mutator_create/pattern_analysis/ANALYSIS_PLAN.md`（必要条件的完整枚举）
> - `/root/gyx/mutator_create/pattern_analysis/run_stage3.py`（执行脚本）

## 4.1 阶段 3 在整体流程中的位置

整个项目的目标链如下：

```
已知崩溃数据（facts + interpretation）
        ↓
   ┌───────────────────────────────────────────────┐
   │ 阶段 3：从同类崩溃中提取共性形态（pattern）    │  ← 本章
   └───────────────────────────────────────────────┘
        ↓
   阶段 4：把共性形态抽象成通用特征（不含项目信息）
        ↓
   阶段 5：把通用特征落到具体项目，生成 mutator
        ↓
   验证：运行模糊测试，观察是否触发同类崩溃
```

**阶段 3 的目标**：把 N 条同类崩溃归纳成 2-6 种"机制形态"，每种形态附上触发条件，作为阶段 4 的输入。

## 4.2 为什么需要 LLM

facts 与 interpretation 是**逐条**的客观记录，无法直接回答"这一类崩溃有什么共同点"。

这个归纳过程需要三项能力：

| 能力 | 说明 |
|---|---|
| 理解代码语义 | 例如识别"`realloc` 迁移导致旧指针失效"这种机制 |
| 跨样本比较 | 判断哪些样本属于同一种机制 |
| 生成自然语言描述 | 产出供后续阶段使用的 `narrative` 与 `trigger_condition` |

**规则引擎难以完成这类语义归纳，因此引入 LLM。**

## 4.3 输入设计

### 4.3.1 单条样本的 15 个字段

每条样本 = 完整 facts（15 字段）+ 完整 interpretation（9 字段），约 3.5 KB。

| 字段 | 内容 | 为什么对 LLM 重要 |
|---|---|---|
| `osv_id` | 崩溃唯一标识 | 用于 `sample_ids` 引用 |
| `project` | 项目名 | 判断样本是否跨项目 |
| `crash_type` | 崩溃类型 | 分组依据 |
| `crash` | 崩溃点：`site`（文件/函数/行）、`code`（该行代码）、`access`（方向/宽度/区域大小） | 定位"使用点" |
| `entity` | 被操作对象：`name` / `kind` / `storage`（堆/栈/全局）/ `decl`（声明类型与行号） | 判断对象性质与分布位置 |
| `alloc` | 分配点：`api`（malloc/realloc/new/自定义） / `site`（函数+行号） / `size_bytes` / `size_expr` / `cross_function` | **判断分配函数家族**，这是区分机制的关键 |
| `sites` | 所有释放/使用点：`kind` / `fn` / `line` / `code` / `args`（实参） / `origin` | 定位"释放点"及其实参 |
| `context` | 上下文：`fn` / `in_loop` / `loop_type` / `guards`（比较表达式） / `guard_count` / `control_structures` | 判断是否有边界检查、是否在循环内 |
| `call_chain` | 完整调用栈（每帧：函数名/文件/行号/是否属于被测项目） | **判断跨几个栈帧、分配与释放是否在不同调用路径** |
| `input_reachability` | 输入能到达的参数列表 | **判断哪个输入参数控制崩溃路径** |
| `types` | 类型信息：`entity_type` / `cast_present`（是否有强制转换） / `is_signed`（是否有符号） / `ptr_origin` | 判断类型相关越界 |
| `completeness` | 缺失的字段列表 | 让 LLM 直接知道数据缺口 |
| `evidence` | 证据路径：`cpg`（CPG 文件路径） / `report`（崩溃报告路径） / `testcase_size`（输入字节数） | 可追溯性；`testcase_size` 反映触发规模 |
| `type_reconciliation` | 报告类型与账本类型是否一致 | 数据可信度 |
| `report_extra` | 崩溃报告中的补充字段（9 项）：`shadow_byte` / `shadow_legend_size` / `loc_size` / `loc_global_var` / `loc_offset` / `loc_kind` / `dedup_token` / `overshoot_ratio` / `region_size` | 影子字节可推算缓冲区边界，全局变量名可定位全局对象 |
| `deep` | 深度查询结果：`line_calls` / `line_ids` / `entity_decl` / `entity_assignments` / `sites` / `guards` / `func_params` / `func_lines` | **`entity_assignments` 判断释放后是否被重赋值；`sites.args` 提供 free 的实参** |
| `interpretation` | 必要条件判定：`findings`（true/false/null） + `missing` + `reasoning` + `confidence` | **直接告诉 LLM 哪些条件成立、哪些因数据缺失无法判定** |

### 4.3.2 一条真实样本的完整内容

以下为 `ARVO-372547409`（libxml2，UAF）的真实数据：

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
    "name": "cur",
    "kind": "struct",
    "storage": "heap",
    "decl": {"file": "/src/libxml2/valid.c", "line": 5952, "type": "xmlNsPtr", "size": null}
  },

  "alloc": {
    "api": "malloc",
    "cross_function": true,
    "site": {"file": "/src/libxml2/fuzz/fuzz.c", "fn": "xmlFuzzMalloc", "line": 81},
    "size_bytes": 64,
    "size_expr": null
  },

  "sites": [
    {"kind": "free", "fn": "xmlFreeAttribute", "line": 1625, "code": null,
     "origin": "report:freed_by"},
    {"kind": "unknown", "fn": "xmlValidateOneElement", "line": 5992,
     "code": "xmlStrEqual(cur->prefix, prefix) | cur->prefix", "origin": "report:crash"}
  ],

  "context": {
    "fn": "xmlSearchNsSafe",
    "in_loop": true,
    "loop_type": null,
    "loop_range": null,
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

  "types": {"entity_type": "xmlNsPtr", "cast_present": null, "is_signed": null,
            "ptr_origin": "assignment"},

  "completeness": ["alloc.size_expr"],

  "evidence": {
    "cpg": ".../libxml2_d4d1f3f33d6d.cpg",
    "report": ".../report.log",
    "testcase_size": 26
  },

  "type_reconciliation": {"diverged": false,
                          "ledger_crash_type": "heap-use-after-free",
                          "report_fault_kind": "heap-use-after-free"},

  "report_extra": {"shadow_byte": 4, "shadow_legend_size": 8, "loc_size": 64,
                   "dedup_token": "...", "overshoot_ratio": null},

  "deep": {
    "line_calls": [...],
    "line_ids": ["cur"],
    "entity_decl": {"type": "xmlNsPtr", "line": 5952},
    "entity_assignments": [...],
    "sites": [...],
    "guards": [...],
    "func_params": {"names": [...], "types": [...]},
    "func_lines": [5940, 6020]
  },

  "interpretation": {
    "type": "heap-use-after-free",
    "confidence": "medium",
    "key_facts": {"freed_ptr": "cur", "free_sites": [1625], "use_site": 5992},
    "findings": {
      "free_sites": [1625],
      "use_site": 5992,
      "crash_after_free": true,
      "reassigned_between": null,
      "alias_used": null,
      "free_arg": null,
      "free_cross_function": true
    },
    "missing": ["reassigned_between", "alias_used", "free_arg"],
    "reasoning": "崩溃点 5992 之前已有 free 于 [1625]"
  }
}
```

## 4.4 Prompt 设计

### 4.4.1 System Prompt（固定）

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
6. pattern 数量控制在 2-5 个。
7. 每个 pattern 的 name 用中文，不超过 12 个字。
8. narrative 用 2-4 句话说清"这个 pattern 的崩溃是怎么发生的"，必须引用具体样本的
   函数名、行号或字段值作为依据。
9. trigger_condition 必须回答"改哪个输入、让什么条件成立，就能触发"，
   如果数据不足以回答，写 "unknown" 并说明缺什么。
10. 当 support > 1 时：narrative 要描述这 N 条的共同机制（可用 2-3 条做例证）；
    evidence 要用跨样本统计的写法（如 "7/7 样本..."、"5/7 样本...（例外：xxx、yyy）"）；
    dimensions 取多数值并注明例外。
```

**规则的三个核心目的**：

| 规则 | 目的 |
|---|---|
| 第 1、2 条 | **防止幻觉**：只用输入数据；缺数据标 `unknown`，不能当作"不成立" |
| 第 3、4 条 | **保证可追溯**：每个 pattern 必须给出具体的样本 ID；归不了类的不能强行归类 |
| 第 8、9、10 条 | **保证可操作性**：`narrative` 要引用具体函数/行号；`trigger_condition` 要回答"改哪个输入" |

### 4.4.2 User Prompt（变量部分）

```
**崩溃类型**
`{{CRASH_TYPE}}`

**该类型的机制背景**
`{{MECHANISM_BACKGROUND}}`

**样本（共 {{N}} 条，完整 facts + interpretation）**
`{{SAMPLES_JSON}}`

**任务**
1. 阅读全部样本，按"崩溃在成因链上的形态"分组。
2. 每组给出：name、narrative、trigger_condition、support、sample_ids、
   dimensions、evidence、confidence。
3. 无法归类的样本放入 unclassified，并说明缺什么数据。

**输出 JSON schema**
`{{OUTPUT_SCHEMA}}`

直接输出 JSON，不要任何解释文字。
```

## 4.5 输出设计

### 4.5.1 输出 Schema

```json
{
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
  "unclassified": [
    {"sample_id": "string", "reason": "string", "missing_fields": ["string"]}
  ],
  "batch_observations": "string"
}
```

### 4.5.2 各字段的含义与作用

| 字段 | 回答什么问题 | 对后续阶段的作用 |
|---|---|---|
| `name` | 这个形态叫什么 | 便于引用 |
| `narrative` | 这个形态的崩溃**怎么发生** | **阶段 4 抽象的原材料** |
| `support` | 该形态包含几条样本 | 判断该形态是否值得关注 |
| `sample_ids` | 具体是哪几条 | 可追溯、可抽查 |
| `trigger_condition.where_alloc` | 在哪里分配 | 阶段 5 定位上游代码 |
| `trigger_condition.where_free` | 在哪里释放 | 阶段 5 定位要提前触发的动作 |
| `trigger_condition.where_use` | 在哪里被错误使用 | 阶段 5 定位崩溃点，验证变异是否命中 |
| `trigger_condition.what_input_controls` | **哪个输入字段控制** | **阶段 5 直接决定改哪个字节** |
| `trigger_condition.minimal_requirement` | **最小触发条件** | **阶段 5 的变异目标** |
| `dimensions` | 7 个固定维度的取值 | 跨类型统计、聚类、粗筛 |
| `evidence` | 判断依据 | 可审计，防止编造 |
| `unclassified` | 哪些样本归不了类 | 提示数据缺口 |

### 4.5.3 为什么这样设计

| 设计 | 理由 |
|---|---|
| 用 `narrative` 自由描述 | 固定维度无法表达"跨阶段失效"这类机制；自由描述能让 LLM 说清全过程 |
| `trigger_condition` 拆成 5 个字段 | 直接对应阶段 5 需要的信息：在哪里分配/释放/使用、改哪个输入、最小条件 |
| 保留 `dimensions` 但降为辅助 | 便于统计，但不作为唯一判据（实测发现它对同一类型往往恒等） |
| 强制 `unclassified` | 不强行归类，避免把不同机制硬塞进一个 pattern |
| 强制 `evidence` | 每条判断必须能追溯到具体字段值 |

### 4.5.4 一条真实输出（节选）

以 `ARVO-372547409` 所在的批为例，LLM 输出的一个 pattern：

```json
{
  "name": "循环内缓存指针跨函数失效",
  "narrative": "释放点是 xmlValidateOneElement 之外的 xmlFreeAttribute（valid.c:1625，
    sites.kind=free，origin=report:freed_by，free_cross_function=true），由
    dropNode→xmlFreeNode→xmlFreeDtd→xmlFreeAttributeTable→xmlHashFree→xmlFreeAttribute
    链在属性表/DTD 拆除时完成；被释放的是 xmlNsPtr 类型的 cur（entity.storage=heap，
    entity.decl=valid.c:5952，由 fuzz.c:81 的 xmlFuzzMalloc 分配 64 字节）。使用侧
    xmlValidateOneElement（valid.c:5992）在 xmlSearchNsSafe 的循环里读 cur->prefix
    （access.dir=READ，width=4，region_bytes=64），context.in_loop=true，而 guards 只有
    \"prefix != NULL | cur == NULL | cur != NULL\"，不含 cur 是否已被释放的有效性判断。
    同一次 26 字节输入内，拆除属性/DTD 使循环缓存的命名空间指针悬空，后续 prefix 比较
    即命中已释放内存。",
  "support": 1,
  "sample_ids": ["ARVO-372547409"],
  "trigger_condition": {
    "where_alloc": "fuzz/fuzz.c:81 xmlFuzzMalloc（alloc.api=malloc，size_bytes=64）",
    "where_free": "valid.c:1625 xmlFreeAttribute（经 dropNode→xmlFreeNode→xmlFreeDtd 链）",
    "where_use": "valid.c:5992 xmlValidateOneElement，读 cur->prefix（width=4）",
    "what_input_controls": "input_reachability=[node, prefix, out]：输入中的节点树与
      命名空间前缀决定是否进入 xmlSearchNsSafe 的 prefix 比较循环，以及同一次校验中
      是否走到 dropNode→xmlFreeDtd 的拆除路径（testcase_size=26）",
    "minimal_requirement": "一次输入处理内先经 dropNode→xmlFreeNode→xmlFreeDtd 释放掉
      cur 所指的 xmlNsPtr 区域（64 字节），随后仍处于 xmlSearchNsSafe 循环
      （in_loop=true）的 xmlValidateOneElement:5992 以 cur->prefix 做 4 字节读"
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
    "alloc.api=malloc, alloc.site=/src/libxml2/fuzz/fuzz.c:81 xmlFuzzMalloc, size_bytes=64",
    "free site=xmlFreeAttribute line=1625, origin=report:freed_by; free_cross_function=true",
    "use site=/src/libxml2/valid.c:5992 xmlValidateOneElement, access.dir=READ, width=4",
    "entity.name=cur, entity.entity_type=xmlNsPtr, entity.storage=heap",
    "context.fn=xmlSearchNsSafe, context.in_loop=true, guard_count=6",
    "input_reachability=[node, prefix, out], testcase_size=26",
    "unknown:reassigned_between (interpretation.findings.reassigned_between=null)",
    "unknown:alias_used (interpretation.findings.alias_used=null，N7 别名关系未确认)",
    "unknown:free_arg (interpretation.findings.free_arg=null，N6 释放实参形式未记录)",
    "unknown:cross_frame_count (call_chain 中释放链与使用链并列，无同一栈内帧距信息)"
  ],
  "confidence": "medium"
}
```

**`evidence` 最后 4 条是关键**：LLM 主动把每个 null 字段列成 `unknown:<字段名>`，并说明它导致哪条必要条件无法验证。**这是防止把"数据缺失"误当成"条件不成立"的机制。**

## 4.6 执行结果

**执行脚本**：`/root/gyx/mutator_create/pattern_analysis/run_stage3.py`

**执行时间**：2026-10-27 00:13 — 00:35（22 分钟）

**各阶段结果**：

| 阶段 | 结果 |
|---|---|
| prepare | 62 批 |
| run | **61/61 成功，0 失败** |
| check | **62/62 通过** |
| merge | 37 + 177 + 31 + 18 = **263 个批级 pattern** |
| runmerge | **22 个最终形态** |

**各类型的最终形态**：

### heap-use-after-free（5 个，覆盖 107/121，未归类 14）

| support | 形态名 |
|---|---|
| 34 | 缓冲释放后旧指针 |
| 31 | 清理析构后悬垂访问 |
| 26 | 容器节点销毁后遍历 |
| 11 | 跨函数陈旧对象访问 |
| 5 | 同函数释放后访问 |

### heap-buffer-overflow（5 个，覆盖 504/601，未归类 97）

| support | 形态名 |
|---|---|
| 215 | 长度偏移校验缺失 |
| 102 | 索引游标越界 |
| 78 | 字符串扫描越界 |
| 74 | 输出写容量越界 |
| 35 | 对象状态字段越界 |

### stack-buffer-overflow（6 个，覆盖 85/110）

| support | 形态名 |
|---|---|
| 25 | 栈索引指针越界读 |
| 21 | 库函数长度写越界 |
| 18 | 栈索引指针越界写 |
| 14 | 库函数长度读越界 |
| 5 | 格式化字符串越界 |
| 2 | 释放路径访问栈元素 |

### global-buffer-overflow（6 个，覆盖 34/51）

| support | 形态名 |
|---|---|
| 12 | 输入字符串扫描越界读 |
| 7 | VTE调试串越界读 |
| 5 | 定长整数读取越界 |
| 5 | 语音引擎全局数组越界读 |
| 3 | 全局表索引越界读 |
| 2 | 协议解析全局越界读 |

## 4.7 阶段 3 的相关文件

| 文件 | 路径 |
|---|---|
| 执行脚本 | `pattern_analysis/run_stage3.py` |
| 分批 prompt | `pattern_analysis/prompts/stage3_extract_patterns.md` |
| 汇总 prompt | `pattern_analysis/prompts/stage3_merge_patterns.md` |
| 流程说明文档 | `pattern_analysis/LLM_ANALYSIS.md` |
| 必要条件枚举 | `pattern_analysis/ANALYSIS_PLAN.md` |
| 批次清单 | `outputs/stage3/manifest.json` |
| 批级结果 | `outputs/stage3/<类型>/batch_NNN.json`（62 个） |
| 跨批汇总输入 | `outputs/stage3/<类型>/merge_input.json`（4 个） |
| 最终形态 | `outputs/stage3/<类型>/final.json`（4 个） |
| 运行日志 | `/tmp/stage2_auto.log` |
| 假设检验 A 的结果 | `/tmp/exp_A_nocap.json` |
| 假设检验 B 的结果 | `/tmp/exp_B.json` |

---

# 五、阶段性结论与后续工作

## 5.1 已完成的工作

| # | 工作 | 产物 |
|---|---|---|
| 1 | 崩溃复现 | 932 条成功复现，61 个仓库 |
| 2 | 崩溃报告解析 | 1,139 条记录 × 66 字段 |
| 3 | CPG 构建 | 689 个 CPG，9.8 GB |
| 4 | CPG 数据流查询 | 926 条记录 × 27 字段 |
| 5 | 深度查询 | 756 条记录 × 7 类字段 |
| 6 | facts 生成 | 1,139 条 × 15 字段 |
| 7 | interpretation 生成 | 1,139 条 × 9 字段 |
| 8 | 分批 LLM 分析 | 62 批，61 批成功 |
| 9 | 跨批汇总 | 22 个最终形态 |

## 5.2 数据质量的客观评估

| 指标 | 数值 | 说明 |
|---|---|---|
| facts 总数 | 1,139 | 覆盖 4 个重点类型 883 条 |
| 有 CPG 的比例 | 92.7%（756/815） | 83 条无 CPG |
| `report_extra` 覆盖 | 100% | 影子字节等 9 个字段 |
| UAF 的 `free_arg` | 约 30% | 依赖 CPG 实参提取 |
| HBO 的 `buffer_size` | 约 1% | 报告无 region 大小，靠影子字节替代 |

**结论：事实层的覆盖已满足"提取共性"的最低要求，但部分必要条件（N8/N9/N10）仍无法判定。**

## 5.3 已知问题

| # | 问题 | 影响 | 状态 |
|---|---|---|---|
| 1 | LLM 输出粒度为"业务领域级"而非"机制级" | `trigger_condition` 偏泛 | 已验证，暂不处理 |
| 2 | `batch_id` 被 LLM 覆盖 | 合并时无法追溯到具体批次 | 已知，未修复 |
| 3 | HBO 的缓冲区大小覆盖率极低 | N3 无法判定 | 已用影子字节部分替代 |
| 4 | 146 条记录缺深度查询 | 这些样本的条件判定不完整 | 已知 |
| 5 | 阶段 4/5 未开始 | — | 待启动 |

## 5.4 后续工作

### 5.4.1 阶段 3 输出字段的用途

| 输出字段 | 阶段 4 用来做什么 | 阶段 5 用来做什么 |
|---|---|---|
| `narrative` | 抽象的原材料 | — |
| `trigger_condition.where_alloc` | 判断"分配阶段"是否是共性 | 定位需要影响的上游代码 |
| `trigger_condition.where_free` | 判断"释放时机"是否是共性 | **定位 mutator 要提前触发的动作** |
| `trigger_condition.where_use` | 判断"使用点"是否固定 | 定位崩溃点，验证变异是否命中 |
| `trigger_condition.what_input_controls` | 判断"输入控制点"是否一致 | **直接决定 mutator 改哪个字节** |
| `trigger_condition.minimal_requirement` | 抽象成通用特征的骨架 | **mutator 的目标条件** |
| `dimensions` | 跨类型统计、形态聚类 | 粗筛（如只对 `in_loop=true` 的形态做循环变异） |
| `evidence` | 审计抽象是否偏离原始数据 | 调试（变异后崩溃点是否一致） |
| `unclassified` | 提示数据缺口 | — |

### 5.4.2 阶段 4：抽象成通用特征

**输入**：4 个 `final.json` 里的 22 个形态

**任务**：把每个形态的 `narrative` + `trigger_condition` 抽象成**不含项目信息的通用特征**。

**示例**（以 UAF 的"扩容重分配后旧指针悬空"为例）：

```
输入（阶段 3 的输出）：
  where_alloc:   lib/util.c:134 xrealloc（realloc，64 字节）
  where_free:    同一站点 xrealloc（realloc 迁移导致旧块回收）
  where_use:     odp-util.c:2246 parse_odp_action，width=2
  minimal_req:   输入需让 ofpbuf_put 在 parse_odp_action 使用旧指针期间
                 触发 ofpbuf_resize__→xrealloc

输出（阶段 4 的通用特征）：
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
  limitations:
    - 无法确定旧指针是否被更新（相关数据缺失）
```

**关键约束**：这个特征里**不能出现项目名、函数名、行号**——否则无法迁移到别的项目。

### 5.4.3 阶段 5：生成 mutator

**输入**：阶段 4 的通用特征 + 目标项目的代码信息（CPG）

**任务**：在目标项目里找到符合该特征的代码位置，生成 mutator。

**示例**（把"动态缓冲区扩容"特征落到某个项目）：

```
1. 用 CPG 查：目标项目里有哪些 realloc 调用？
2. 筛选：哪些 realloc 之后，旧指针仍被使用？（用数据流判断）
3. 定位：这些点的上游输入字段是什么？
4. 生成 mutator：
   - 找到控制缓冲区初始大小的输入字段（如长度前缀）
   - 变异策略：把该字段改小，使扩容提前发生 → 旧指针悬空 → 崩溃
```

### 5.4.4 四种形态对应的 mutator 方向（示例）

以阶段 3 早期 15 条 UAF 样本的测试结果为参考：

| 形态 | 触发条件 | mutator 要做什么 |
|---|---|---|
| 循环内缓存指针跨函数失效 | 先触发析构释放，再在循环里读 | 构造输入让"释放"和"读取"在同一次执行内都发生 |
| 测试框架缓冲区提前回收 | 参数解析多阶段之间发生缓冲区回收 | 构造输入走两个阶段的参数解析 |
| 扩容重分配后旧指针悬空 | 解析途中触发 realloc 迁移 | **让缓冲区初始容量偏小，迫使扩容提前发生** |
| 引用计数释放后同帧复用 | 走到析构链 | **无需输入，空输入即可（0 字节）** |

**最后一行是一个重要发现**：radare2 那条的 `testcase_size=0`，说明它跟输入无关，**mutator 对它无能为力**——这类样本应从 mutator 的适用范围内排除。

### 5.4.5 阶段 4 需要先回答的问题

如 5.3 中"已知问题"第 1 条所述，阶段 3 目前输出的形态粒度是"业务领域级"。阶段 4 开始前必须先确认：

> **领域级形态（如"解码器内存池释放后使用"）能否抽象出足够具体的变异策略？**
>
> - 如果能 → 阶段 3 的粒度可接受，继续推进；
> - 如果不能 → 需要回头细化粒度为"机制级"，并先解决精确化导致的样本丢失问题。

# 附录 A：文件与目录索引

## A.1 数据目录

```
/root/gyx/mutator_create/pattern_analysis/artifacts/
├── facts.jsonl                      1,139 条（15 字段）
├── facts/<OSV>/facts.json           1,139 个
├── interpretation.jsonl             1,139 条（9 字段）
├── interpretation/<OSV>/            1,139 个
├── crash_report_features.jsonl      1,139 条（66 字段）
├── crash_report/<OSV>/              1,139 个
├── dataflow_features.jsonl          926 条（27 字段）
├── dataflow/<OSV>/                  926 个
├── deep_fields.jsonl                756 条（7 类字段）
└── semantic_fields.jsonl            123 条（下标/类型查询，部分完成）
```

## A.2 脚本目录

```
/root/gyx/mutator_create/pattern_analysis/
├── extract_crash_features.py        崩溃报告解析
├── analyze_cpg_par.py               CPG 数据流查询（并行）
├── analyze_cpg.py                   CPG 查询模板
├── deepen_facts_par.py              深度查询：释放点关系
├── deepen_facts.py                  深度查询模板
├── add_deep_fields.py               深度查询：代码细节
├── merge_deep_fields.py             合并深度字段进 facts
├── build_facts.py                   生成 facts
├── interpret.py                     生成 interpretation
├── split_artifacts.py               拆分为单崩溃文件
├── run_stage3.py                    阶段 3 执行脚本
├── static_dataflow.py               公共模块
├── auto_chain.sh                    数据补充阶段自动链
├── run_all.sh                       串行总脚本
└── wait_and_stage3.sh               阶段 3 自动触发
```

## A.3 输出目录

```
/root/gyx/mutator_create/pattern_analysis/outputs/stage3/
├── manifest.json                    62 批清单
├── uaf/  (9 批)  → final.json       5 个形态
├── hbo/  (41 批) → final.json       5 个形态
├── stack/(8 批)  → final.json       6 个形态
└── global/(4 批) → final.json       6 个形态
```

## A.4 CPG 目录

```
/root/gyx/mutator_create/cpg_files/
└── <项目>_<提交前12位>.cpg          689 个，9.8 GB
```

## A.5 文档目录

```
/root/gyx/mutator_create/pattern_analysis/
├── ANALYSIS_PLAN.md                 必要条件枚举 + Mutator 设计
├── LLM_ANALYSIS.md                  LLM 分析流程完整说明
├── STAGE_SUMMARY.md                 本文档
└── prompts/
    ├── stage3_extract_patterns.md   分批提取 prompt
    └── stage3_merge_patterns.md     跨批汇总 prompt
```

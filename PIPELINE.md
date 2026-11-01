# 五阶段流水线：从已知崩溃到定制变异算子

> 本文描述一条完整的数据通路：**用已复现的崩溃，反推出「这类崩溃的共性」，再把它变成能提高 fuzz 命中率的变异算子。**
>
> 阅读方式：如果只想了解全貌，看第 0、1 节；想了解某一步，跳到对应章节；想知道一个具体崩溃怎么走完全程，看第 7 节。

---

# 0. 一页看懂

## 0.1 这条流水线在解决什么问题

传统 fuzz 靠"随机变异 + 覆盖率引导"撞崩溃。它的问题是对**深层、结构性**的 bug 效率极低：
比如"解析器在错误分支里释放了对象却没置空指针，下一轮循环又去读它"——随机字节几乎不可能同时凑齐
"进入错误分支"和"还有下一轮"这两个条件。

本流水线的思路是：

```
已知崩溃（真实发生过）
      ↓ 归纳：这类崩溃在代码上长什么样？触发它需要输入的什么形状？
通用特征（项目无关）
      ↓ 落地：这个项目的代码里，哪一处符合这个形状？改输入的哪个字节能让它发生？
变异算子（项目相关）
      ↓ 验证：算子真的有效吗？
A/B 实验（同一二进制，只切换变异器）
```

**一句话：把"人工分析崩溃得到的经验"变成"可执行、可验证的变异策略"。**

## 0.2 五个阶段

| 阶段 | 一句话 | 手段 | 核心产物 |
|---|---|---|---|
| **stage1** 漏洞复现 | 把 ARVO / OSV 的崩溃在 Docker 里真跑出来 | 代码执行 | 崩溃清单 + `report.log` + CPG |
| **stage2** 数据抽取 | 从报告和图里抽出结构化事实，再派生判断 | 正则 + CPG 查询 | `facts` + `interpretation` |
| **stage3** 共性提取 | 把同类崩溃聚成「机制形态」 | LLM 批处理 | 22 个 pattern |
| **stage4** 特征抽象 | 把每个 pattern 归纳成 1 个项目无关特征 | LLM | `features.json`（UAF 5 个） |
| **stage5** 算子生成 | 把特征落到具体项目，生成并验证变异算子 | LLM + 读源码 + 编译 + fuzz | `mutator.c` + 实验报告 |

## 0.3 全景图

```
                    ┌──────────────────────────────────────────────┐
   ARVO / OSV 元数据 │  stage1  漏洞复现                             │
   + Docker 镜像     │  跑崩溃 → report.log / testcase / .cpg        │
                    └───────────────────┬──────────────────────────┘
                                        │  report.log(1,148) + .cpg(689) + 清单(1,154)
                                        ▼
                    ┌──────────────────────────────────────────────┐
                    │  stage2  数据抽取                             │
                    │  ① 解析报告 → ② 查 CPG 数据流 → ③ 合成 facts  │
                    │  → ④ 查 CPG 深度字段 → ⑤ 合并 → ⑥ 派生判断    │
                    └───────────────────┬──────────────────────────┘
                                        │  facts(1,139) + interpretation(1,139)
                                        ▼
                    ┌──────────────────────────────────────────────┐
                    │  stage3  LLM 聚类 → pattern                   │
                    └───────────────────┬──────────────────────────┘
                                        │  stage3/<type>/final.json（22 个 pattern）
                                        ▼
                    ┌──────────────────────────────────────────────┐
                    │  stage4  LLM 归纳 → 通用特征                  │
                    └───────────────────┬──────────────────────────┘
                                        │  stage4/<type>/features.json（UAF 5 个）
                                        ▼
                    ┌──────────────────────────────────────────────┐
                    │  stage5  落到具体项目 → mutator.c → A/B 实验   │
                    └──────────────────────────────────────────────┘
```

---

# 1. 数据血缘：每个产物从哪来、到哪去

这张表是全流程的"账本"。**任何一份产物，都能在这里查到它是谁生成的、被谁消费。**

| # | 产物 | 生成者 | 生成方式 | 规模 | 消费者 |
|---|---|---|---|---|---|
| 1 | `reproduced_crashes.jsonl` | stage1 | 复现时逐条登记 | **1,154 条 × 23 字段** | stage2 全部步骤 |
| 2 | `report.log` | stage1 | 崩溃时的 ASan 完整输出 | 1,148 份 | stage2 步骤1 |
| 3 | `cpg_files/<project>_<commit>.cpg` | stage2 步骤2/4 按需 | Joern `c2cpg` 建图 | **689 个**（9.2 GB） | stage2 步骤2、4；stage5 |
| 4 | `testcase`（触发输入） | stage1 | 复现时保存的 crash 输入 | 1,148 份 | 仅参考（stage5 不用） |
| 5 | `_cache/crash_report_features.jsonl` | stage2 步骤1 | 正则解析 `report.log` | **1,139 条 × 63 字段** | 步骤2、3 |
| 6 | `_cache/dataflow_features.jsonl` | stage2 步骤2 | Joern 查询 CPG（数据流 + AST） | 926 条 × 27 字段 | 步骤3 |
| 7 | `_cache/deep_fields.jsonl` | stage2 步骤4 | Joern 查询 CPG（代码结构） | 756 条 × 11 字段 | 步骤5 |
| 8 | `facts/<OSV>/facts.json` | stage2 步骤3（步骤5 **就地回写**） | 三源合并 | **1,139 个文件**（15 基础字段 + 可选 `deep` 756 条、`free_related` 22 条） | stage3、stage4、interpretation |
| 9 | `interpretation/<OSV>/interpretation.json` | stage2 步骤6 | 只读 facts 做确定性比较 | **1,139 条 × 9 字段** | stage3 |
| 10 | `outputs/stage3/<type>/final.json` | stage3 | LLM 两轮聚类 | **22 个 pattern** | stage4 |
| 11 | `outputs/stage4/<type>/features.json` | stage4 | LLM 归纳（每 pattern 1 次） | UAF **5 个特征** | stage5 |
| 12 | `mutator_custom/stage5/<OSV>/mutator.c` | stage5 | LLM 读源码 + 生成 + 门禁 + 审查 | 2 个 mutator | fuzz 实验 |

## 1.1 衔接校验（上一环的输出 = 下一环的输入）

| 衔接 | 上游产出 | 下游读取 | 是否闭合 |
|---|---|---|---|
| stage1 → stage2 | `report.log`(1,148) + `.cpg`(689) + 清单(1,154) | 步骤1 读 report.log；步骤2/4 读 cpg；全步骤读清单 | ✅ |
| stage2 内部 | 步骤1 → 步骤2 → 步骤3 → 步骤4 → 步骤5 → 步骤6 | 见第 3 节逐步说明 | ✅ |
| stage2 → stage3 | `facts`(1,139) + `interpretation`(1,139) | stage3 两者一起读 | ✅ |
| stage3 → stage4 | `final.json` 的 `final_patterns[].sample_ids` | stage4 按 `sample_ids` 取样本 facts | ✅ |
| stage4 → stage5 | `features.json` 的 `features[].mutation_target` | stage5 逐特征落地 | ✅ |
| stage5 → 实验 | `mutator.c` + 项目源码 + 种子 | `build_fuzzer.sh` 编译，`run_all.sh` 跑 | ✅ |


# 2. stage1：漏洞复现

## 2.1 目的

**把"数据集里写着有崩溃"变成"我手上有一份真实的崩溃报告和对应的源码图"。**

类比：数据集只是一张"病历索引"，stage1 是真正去把病人（崩溃）找到、做检查（跑出 ASan 报告）、拍片子（建 CPG）。

## 2.2 输入从哪来

| 数据集 | 规模 | 元数据内容 | 存放位置 |
|---|---|---|---|
| **ARVO** | **6,138 条 / 311 项目** | `localId`、项目、sanitizer、`fuzz_target`、`reproducer_vul`、`crash_type` | `arvo/data/arvo.db`（表 `arvo`） |
| **OSS-Fuzz（OSV）** | **1,598 个 issue / 76 项目**（3,019 条尝试记录） | OSV ID、项目、`fix_commit`、`fuzz_target`、`testcase_url` | `reproduce_crash/repro_dataset.jsonl` |

**复现结果与图覆盖**（实测）：

| | 数据集 | 复现成功 | 有 CPG（知识图谱） | 唯一 CPG 文件 |
|---|---|---|---|---|
| ARVO | 6,138 | **915**（14.9%，54 项目） | **890 / 915 = 97.3%** | 552 |
| OSS-Fuzz | 1,598 | **239**（15.0%，16 项目） | 124 / 239 = 51.9% | 82 |
| 合计 | 7,736 | **1,154** | **1,014 / 1,154 = 87.9%** | 631 |

ARVO 那 25 条缺 CPG 的分布：`libvips` 18、`arrow` 5、`wasm3` 1、`wireshark` 1。

## 2.3 怎么做

两条路径，判定标准不同：

| 数据集 | 复现方式 | 判定 |
|---|---|---|
| **ARVO** | 直接拉 `n132/arvo:<localId>-vul` 镜像（**镜像里已经编好了漏洞版二进制**），跑 `/out/<target> <testcase>` | `ok = true`（复现出**原始那个**崩溃） |
| **OSV** | OSV 只给 `fix_commit`，没有现成镜像 → 自己 `git clone` → checkout `fix_commit^1`（漏洞版）→ 按 OSS-Fuzz 的 `build.sh` 编译 → 跑 | `reproduced_any = true`（跑出**任意**崩溃即可，不要求与原始一致） |

**为什么 OSV 的标准更松**：OSV 没有提供"崩溃长什么样"的基准，只能退而求其次。

**关键脚本**（在 `reproduce_crash/`）：

| 脚本 | 职责 |
|---|---|
| `run_repro.py` | 总编排：①清单 → ②构建 → ③复现 → ④验证 → ⑤walk-back → ⑥分层 |
| `build_orchestrator.py` | 构建二进制。分"HEAD 构建"和"钉版 commit 构建"两个**构建阶段** |
| `arvo_repro.py` / `repro_runner.py` | 单条崩溃的复现执行 |
| `verify_tiered.py` | 分层验证：`strict` / `medium` / `loose`（判断这次复现可不可信） |
| `manifest_builder.py` / `recover_report_logs.py` | 生成清单 / 回收报告 |

> ⚠️ **命名陷阱**：这些脚本里的 `--stage 1` / `--stage 2` 指的是**构建阶段**（HEAD 构建 vs 钉版构建），
> 与本文的流程阶段**完全无关**。看到 `--stage` 不要往流程阶段上想。

## 2.4 输出（3 类）+ 每类怎么来的

### 输出① `reproduced_crashes.jsonl` —— 崩溃清单（1,154 条 × 23 字段）

**怎么来的**：复现时逐条登记。每条记录回答"这个崩溃是什么、在哪、可不可信"。

| 字段组 | 字段 | 含义 |
|---|---|---|
| **身份** | `osv_id`、`project`、`source`（ARVO/OSV）、`sanitizer`、`fuzz_target` | 这是哪条崩溃 |
| **复现结果** | `ok`（ARVO 复现原始崩溃）、`reproduced_any`（OSV 跑出任意崩溃） | 成没成功 |
| **版本** | `repo_url`、`pin_commit`、`fix_commit`、`src_head` | 漏洞版在哪 |
| **崩溃位置** | `fault_file`、`fault_fn`、`fault_line` | 崩在哪个文件/函数/行 |
| **类型** | `crash_type`、`crash_type_norm`、`observed_crash_type` | 数据集标注 vs 实测 |
| **证据位置** | `report_path`、`report_dir`、`testcase_size`、`cpg_path` | 报告/输入/CPG 在哪 |
| **可信度** | `verification_tier`、`has_facts`/`has_deep`/`has_interpretation`/`report_dir` | 这条数据有多可靠 |

**这是全流程的"主键表"**：后面每一步都靠 `osv_id` 把不同来源的数据 join 起来。

### 输出② `report.log` —— 崩溃报告（1,148 份）

**怎么来的**：崩溃发生时 AddressSanitizer（ASan，一种内存错误检测器）打印的完整文本。

**它为什么重要**：里面包含**只有在运行时才知道**的事实，静态分析永远得不到：

| 报告里的段落 | 提供什么 |
|---|---|
| `ERROR: AddressSanitizer: heap-use-after-free` | 崩溃类型（实测） |
| `READ of size 2 at 0x…` | 读/写、访问宽度 |
| `#0 … in dxf_objects_read /src/in_dxf.c:12267:36` | 崩溃栈的 top frame（文件:行:列） |
| `0x… is located 0 bytes inside of 16-byte region` | 这块内存多大、崩在区域内的偏移 |
| `freed by thread T0 here: … #1 dxf_free_pair :515` | **谁释放的**（UAF 的关键证据） |
| `previously allocated by thread T0 here: … #1 xcalloc :216` | **谁分配的** |
| `=>0x…: fa fa fd fd … [fd] …` | ASan 影子内存（`fd` = 已释放的堆区域） |
| `Shadow byte legend` | 影子字节的图例（不同 ASan 版本会变，所以**从报告里解析而不是硬编码**） |

### 输出③ `.cpg` —— 代码属性图（689 个）

**怎么来的**：用 `c2cpg`（Joern 4.0.150 的 C/C++ 前端）把漏洞版源码解析成一张图。

**它是什么**：把源码变成"图"——

```
节点：函数、方法、变量、参数、调用点、字面量、控制结构
边  ：调用关系、数据流（谁赋值给谁）、AST 父子、控制依赖
```

**为什么需要它**：`report.log` 只告诉你"515 行释放了、12267 行读了"，
但**不告诉你两件事**：
1. 这 12267 行里的 `pair` 是什么类型的变量？
2. 从 515 到 12267 之间，`pair` 有没有被重新赋值？

这两个问题只能靠**读代码的静态结构**回答，也就是 CPG。

**命名规则**：`cpg_files/<project>_<commit前12位>.cpg`（同一个 project+commit 的多个崩溃共用一个图）。

### 输出④（严格说是 stage2 步骤1 执行，但属于 stage1 的范畴）

`_cache/crash_report_features.jsonl`（1,139 条 × 63 字段）—— **报告解析结果**。

**怎么来的**：正则解析 `report.log`。之所以放在 stage2 的入口里跑，是因为它是纯文本解析（几秒就跑完），
和 facts 的生成放在一起更方便；但从**语义**上说，它是"把 stage1 的报告变成可查询的结构"。

**为什么单独存**：解析规则很脏（6 种 "is located…" 措辞、16 种首错误行形态、MemorySanitizer 用 `WARNING:` 而不是 `ERROR:`、UBSan 完全是另一种格式）。
把它固化成文件后，下游不必重复踩这些坑。

## 2.5 交接给 stage2

| stage2 需要什么 | stage1 给了什么 |
|---|---|
| "这个崩溃是什么类型" | `crash_type_norm`（清单）+ `fault_kind`（报告解析） |
| "在哪崩的" | `fault_file` / `fault_fn` / `fault_line` |
| "怎么崩的" | `report.log` 的完整栈 + 影子字节 |
| "代码长什么样" | `.cpg` |
| "输入是什么格式、多大" | `testcase` + `testcase_size` |

---

# 3. stage2：数据抽取（facts + interpretation）

## 3.1 目的

**把"非结构化的报告文本 + 巨大的代码图"压缩成"每条崩溃一页结构化档案"，再做一层确定性判断。**

类比：
- `facts` = 案发现场勘查记录（在哪里、什么时间、什么东西、谁碰过）
- `interpretation` = 根据勘查记录做出的初步判断（"先被释放，后被使用，所以是 UAF"）

## 3.2 入口与内部步骤

**两个入口 + 一个共享库**（都在 `pattern_analysis/pipeline/`）：

```bash
python3 s2a_build_facts.py            # 入口①：内含 5 个步骤 → facts/<OSV>/facts.json
python3 s2b_build_interpretation.py   # 入口②：facts → interpretation/
```

| 文件 | 行数 | 角色 |
|---|---|---|
| `s2_lib_cpg.py` | 481 | **共享库**：CPG 访问 + Joern 查询封装（被步骤2/4 和 stage5 用） |
| `s2a_build_facts.py` | 1,456 | **入口①**：内含 5 个步骤 |
| `s2b_build_interpretation.py` | 369 | **入口②** |

### 入口① 的 5 个步骤（输入 → 做法 → 输出）

| 步 | 输入 | 做法 | 输出 | 贵否 |
|---|---|---|---|---|
| **1** | `report.log`(1,148) + 清单 | **正则解析**。逐段匹配 ASan 报告（错误行 / 访问描述 / 栈帧 / 分配栈 / 释放栈 / 影子字节） | `_cache/crash_report_features.jsonl`（1,139 × 63） | 便宜 |
| **2** | 上一步输出 + `.cpg`(689) | **Joern 查询**。按 CPG 分组（一个图只查一次），查三件事：故障点的量从哪个参数来 / 附近有没有比较表达式 / 是否在循环里 | `_cache/dataflow_features.jsonl`（926 × 27） | **贵**（几十分钟） |
| **3** | 步骤1 + 步骤2 + 清单 | **三源合并**。以 `osv_id` 为主键 join，把"报告事实 + 静态事实 + 元数据"归到一条记录 | `facts/<OSV>/facts.json`（1,139 个文件） | 便宜（<1 s） |
| **4** | `.cpg` + `facts` | **Joern 再查一次**，这次查"代码结构"：故障行表达式、变量声明、变量所有赋值点、函数内所有释放调用、函数签名、守卫条件 | `_cache/deep_fields.jsonl`（756 × 11） | **贵** |
| **5** | 步骤4 的输出 + 全部 per-file | **只填空缺、不覆盖**。把深度字段挂到 `facts["deep"]`，并给个别字段补值 | **就地回写** `facts/<OSV>/facts.json` | 便宜 |

**为什么步骤2 和步骤4 要分两次查 CPG？** 因为它们回答的是两类问题：

| | 步骤2（数据流） | 步骤4（代码结构） |
|---|---|---|
| 问什么 | 这个量**从哪来**？有没有边界检查？ | 这行**长什么样**？变量在哪赋过值？ |
| 典型字段 | `reachability`、`guard`、`in_loop` | `line_calls`、`entity_assignments`、`sites`、`func_params` |
| 谁需要 | 判断"输入能不能控制到这里" | 判断"释放后有没有重新赋值"（UAF 的核心） |

**增量与缓存**：中间产物都在 `artifacts/_cache/`。步骤2/4 的产物已存在时会**自动跳过**（因为它们最贵），
`--refresh` 强制重跑；`--steps 3,5` 只跑指定步骤。

## 3.3 facts 的 15 个基础字段（另有 2 个可选字段）

**性质：只记录"观测到的事实"，不做任何推断。**

| 字段 | 装什么 | 从哪来 |
|---|---|---|
| `osv_id` | 主键 | 清单 |
| `project` | 项目名 | 清单 / 报告 |
| `crash_type` | 崩溃类型（**以报告实测为准**，不是数据集标注） | `report.fault_kind` 归一化 |
| `entity` | 出问题的变量：名字、指针/数组、堆/栈、声明类型与行号 | 崩溃行标识符（CPG）+ 深度字段 |
| `alloc` | 这块内存怎么分配的：API、函数、行号、字节数、是否跨函数 | 报告的 `allocated by` 栈 |
| `sites` | **关键操作点的时间线**：`kind`(free/alloc/crash/strdup) + 函数 + 行号 + 代码 + 实参 + `origin`(哪来的) | 报告的 `freed by` 栈 + CPG 扫描 |
| `crash` | 崩溃点：文件/函数/行、该行代码、访问方向、宽度、区域大小 | 报告 `#0` 帧 + CPG |
| `context` | 代码上下文：是否在循环、守卫条件、控制结构清单 | CPG |
| `call_chain` | 调用链（注意：混了崩溃栈/释放栈/分配栈三条，**不是一条路径**） | 报告的 `observed_frames` 去重 |
| `types` | 类型信息：变量完整类型、有无强转、是否带符号、指针来源 | CPG |
| `input_reachability` | **输入从哪个函数参数进来**（例 `["dat"]`） | CPG 反向切片 |
| `evidence` | 证据位置：报告路径、CPG 路径、输入大小 | 清单 |
| `type_reconciliation` | 数据集标注 vs 报告实测是否一致 | 清单 + 报告 |
| `completeness` | **这份 facts 缺了哪些字段**（例 `["alloc.size_expr"]`） | 自动算出 |
| `report_extra` | 报告里额外有用的字段（`loc_kind`/`loc_offset`/`shadow_byte`/`dedup_token`…） | 步骤5 从报告解析结果补 |
| `deep` | **CPG 深挖出的原始记录**（整体挂载，保留全部证据） | 步骤4 |
| `free_related` | 释放相关的补充信息 | 步骤5 |

**`deep` 里的 11 个字段**：

| 字段 | 装什么 | 为什么关键 |
|---|---|---|
| `line_calls` | 故障行所有调用 + 实参个数 | 崩溃那一行的表达式分解 |
| `line_ids` | 故障行所有标识符 | 定位变量 |
| `line_call_count` | 调用个数 | — |
| `entity_name_cpg` | 变量名（CPG 视角） | 补 facts 没抓到的 |
| `entity_decl` | 声明类型 + 行号 | — |
| `entity_assignments` | **该变量在函数内的所有赋值** | **判断 UAF 的唯一依据**（释放后有没有重新赋值） |
| `sites` | 函数内所有分配/释放调用（含包装函数）+ 代码 + 实参 | 知道"释放有几种方式" |
| `guards` | 函数内所有比较表达式 | 有没有保护 |
| `func_params` | 参数名 + 类型 | 输入入口 |
| `func_lines` | 函数起止行 | — |
| `osv_id` | 主键 | — |

> **`completeness` 的价值**：它把"这份数据缺什么"显式写出来。下游看到 `alloc.size_expr` 在
> `completeness` 里，就知道"分配大小未知"，而不是把 `null` 误读成"没有分配"。

## 3.4 interpretation 的 9 个字段

**性质：只对 facts 做"比较两个字段"这种机械推断，不引入任何外部数据。**

```json
{
  "type": "heap-use-after-free",
  "confidence": "medium",
  "key_facts": {"freed_ptr": "pair", "free_sites": [515], "use_site": 12267},
  "findings": { …按崩溃类型不同，见下表… },
  "missing": ["reassigned_between", "alias_used"],
  "reasoning": "崩溃点 12267 之前已有 free 于 [515]",
  "osv_id": "...", "project": "...", "crash_type": "..."
}
```

固定 9 个字段里，**只有 `findings` 的内容随崩溃类型变化**：

| 字段 | 是否随类型变化 |
|---|---|
| `type` / `osv_id` / `project` / `crash_type` | 否（照抄 facts） |
| `confidence` | 规则固定：`missing` 为空 → `high`；≤2 → `medium`；更多 → `low`（4 个类型直接硬编码 `low`） |
| `key_facts` | **是**（挑该类型最关键的 2–5 个值） |
| `findings` | **是**（核心差异） |
| `missing` | **是**（该类型算不出的项） |
| `reasoning` | **是**（一句话结论） |

### 9 个解读器与各自的核心问题

| 解读器 | 覆盖的崩溃类型 | 核心问题 | 主要读的 facts 字段 | 产出的 `findings` |
|---|---|---|---|---|
| `interp_buffer_overflow` | heap / stack / global buffer-overflow、buffer-underflow（5 种） | **访问宽度 vs 缓冲区大小**：越界多少？哪种越界方式（下标 / 指针 / 长度）？有没有边界检查？ | `alloc.size_bytes`、`alloc.size_expr`、`alloc.size_expr_cpg`、`crash.access.width`、`crash.line_code`、`context.guards`、`entity.name` | `buffer_obj`、`buffer_size`+来源、`extent_bytes`、`crosses_by_bytes`、`overflow_mode`、`bound_check_exists`、`bound_check_code` |
| `interp_use_after_free` | heap-use-after-free | **释放与使用的先后**：崩溃前有 free 吗？之间有没有重新赋值？释放的是别名吗？跨函数吗？ | `sites[kind=free].line`、`crash.site.line`、**`deep.entity_assignments`**、`sites.args`/`code`/`fn`、`crash.site.fn` | `crash_after_free`、`reassigned_between`、`alias_used`、`free_arg`、`free_cross_function` |
| `interp_double_free` | heap-double-free | **两次释放的定位**：崩溃这次 free 在哪？上一次 free 在哪（报告给的）？是否在循环里？ | `sites[kind=free]`、`sites[origin=report:freed_by]`、`context.in_loop` | `free_sites_in_func`、`crash_free_site`、`previous_free_site`+来源、`free_count`、`in_loop`、`reassign_between` / `remalloc_between`（均未实现） |
| `interp_invalid_free` | invalid-free | **free 的实参是否合法**：参数是什么存储区？有没有匹配的分配点？free 前有没有指针运算？ | `entity.name`、`entity.storage`、`alloc` | `free_arg`、`arg_storage`、`has_matching_alloc`、`ptr_arith_before_free` / `free_arg_is_offset`（未实现） |
| `interp_invalid_deref` | segv-on-unknown-address、null-dereference | **指针来源与判空**：解引用前有没有比较（疑似判空）？指针类型是什么？ | `context.guards`、`entity.name`、`types.entity_type` | `ptr_expr`、`null_checked_before`、`ptr_type`、`ptr_origin` / `deref_offset`（未实现） |
| `interp_uninit` | use-of-uninitialized-value | **漏赋值在哪条分支** | （current facts 不够） | 全部未实现 |
| `interp_negative_size` | negative-size-param | **size 表达式的符号性**：是否有符号？有没有显式强转？ | `crash.code`、`types.is_signed`、`types.cast_present` | `size_expr`、`size_signed`、`has_explicit_cast` |
| `interp_memcpy_overlap` | memcpy-param-overlap | **memcpy 三个实参是否同源** | `crash.code` | 全部未实现 |
| `interp_generic` | 其余（stack-use-after-return、use-after-poison、container-overflow、abrt、ill…） | 无 | `crash.site.line`、`entity.name` | `{}`（空） |

### 三个分组层面的取舍

| 分组 | 做法 | 理由 |
|---|---|---|
| buffer 类 **5 种 → 1 个**解读器 | 共用 `interp_buffer_overflow` | 机制问题相同（宽度 vs 大小），只是存储区不同——所以输出 `type` 用 facts 的原始值，不硬编码 |
| free 类 **3 种 → 3 个**解读器 | UAF / double-free / invalid-free 各自独立 | 机制问题**完全不同**：先后顺序 / 两次释放位置 / 实参合法性 |
| deref 类 **2 种 → 1 个** | segv + null-dereference 共用 `interp_invalid_deref` | 都是"指针能不能解引用"，判据都是"崩溃前有没有比较" |

### 实测：哪些分析点真的算得出来

`findings` 里各键"真正取到非空值"的比例（按类型）：

| 类型 | 条数 | high/med/low | `missing` 均值 | 真正算出的分析点 |
|---|---|---|---|---|
| heap-buffer-overflow | 601 | 0 / 405 / 196 | 1.8 | `extent_bytes` 100%、`bound_check_exists` 100%、`buffer_obj` 78.5%、`overflow_mode` 61.2%、`bound_check_code` 31.8%、**`buffer_size` 仅 0.2%** |
| stack-buffer-overflow | 110 | 0 / 79 / 31 | 1.7 | `extent_bytes` 100%、`bound_check_exists` 100%、`buffer_obj` 84.5%、`overflow_mode` 53.6%、`buffer_size` **0%** |
| global-buffer-overflow | 51 | 0 / 31 / 20 | 1.9 | `extent_bytes` 100%、`bound_check_exists` 100%、`buffer_obj` 68.6%、`buffer_size` **0%** |
| heap-use-after-free | 121 | 2 / 69 / 50 | 2.5 | `crash_after_free` 100%、`free_cross_function` 100%、`free_sites` 97.5%、`reassigned_between` **33.9%**、`alias_used` 5.8% |
| heap-double-free | 19 | 0 / 8 / 11 | 2.9 | `free_count` 100%、`free_sites_in_func` 89.5%、`previous_free_site` 84.2%、`in_loop` 68.4% |
| invalid-free | 8 | 0 / 5 / 3 | 2.8 | `has_matching_alloc` 100%、`free_arg` 75% |
| segv-on-unknown-address | 158 | 0 / 58 / 100 | 2.3 | `null_checked_before` 100%、`ptr_expr` 57%、`ptr_type` 36.7% |
| negative-size-param | 14 | 0 / 0 / 14 | 5.3 | `size_expr` 71.4% |
| use-of-uninitialized-value | 14 | 0 / 0 / 14 | 4.6 | `uninit_var` 50% |
| stack-use-after-return | 12 | 0 / 0 / 12 | 1.0 | **无**（走 generic） |
| use-after-poison | 13 | 0 / 0 / 13 | 1.0 | **无**（走 generic） |
| memcpy-param-overlap | 6 | 0 / 0 / 6 | 4.0 | 只有 `code` |

**最值得注意的一行**：buffer-overflow 有 762 条（601+110+51），`extent_bytes`（访问宽度）100% 拿得到，
但 **`buffer_size`（缓冲区大小）几乎全是空**（601 条里只有 1 条）。
原因是分配大小常常不是字面量（`calloc(n, 16)`、`malloc(len+1)`），而 `alloc.size_expr` 的 CPG 提取只覆盖 28%。
**所以 buffer-overflow 的 `crosses_by_bytes`（越界多少字节）实际算不出来** —— 这也是 HBO 特征质量差的根源。

### 一条结论

| 类型组 | facts 能否支撑解释 | 实测 |
|---|---|---|
| UAF、double-free、invalid-free | **能**（`crash_after_free`/`free_sites`/`previous_free_site` 都是 100% 或接近） | ✅ 有效 |
| buffer-overflow（3 种） | **部分能**（宽度有、大小几乎没有） | ⚠️ 只能判"有没有边界检查"，判不了"越界多少" |
| segv / null-deref | **部分能**（判空与否 100%，指针来源没有） | ⚠️ 只能判"有没有比较" |
| uninit / negative-size / memcpy-overlap | **不能** | ❌ 全部 `confidence=low` |

---

## 3.5 facts 与 interpretation 的区别与互补

### 区别

| 维度 | facts | interpretation |
|---|---|---|
| **性质** | 观测值 | 判断（"确定性判断"） |
| **来源** | 报告 + CPG + 清单 | **只读 facts**，不读任何原始数据 |
| **内容** | 位置、变量、类型、大小、控制结构 | 先后顺序、是否重赋值、是否别名、是否跨函数、越界多少 |
| **是否含推断** | 否 | 是，但只做机械比较 |
| **缺失标记** | `completeness`（哪些字段空） | `missing`（哪些比较做不了）+ `confidence` |

### 互补：interpretation 把"确定性推理"预先算好了

**如果只喂 facts 给 LLM**，它得自己回答这些问题：

| LLM 需要自己算的 | 容易出错的地方 |
|---|---|
| 释放行 515 在崩溃行 12267 之前吗？ | 简单比较，但**在循环里不可靠** |
| 释放后有没有重新赋值？ | 要区分 `pair = ...`（写指针本身）和 `*pair = ...`（写指针指向的内容） |
| 释放的是同一个对象吗？ | 要看 `free` 的实参，可能缺失 |

**interpretation 把这些预先算完了**，并且**算不出来的时候明确标 `null` + 记进 `missing`**。

### 三个实例

**例 1：ARVO-42494732（正常）**

| | 内容 |
|---|---|
| facts 说 | `sites` 有 free@515、crash@12267；`entity_assignments` 有 4 条（12264/12276/12288/12289） |
| interpretation 说 | `crash_after_free=true`；`reassigned_between=null`（比不出——`*pair=` 与 `pair=` 无法区分）；`free_cross_function=true` |
| **价值** | LLM 不用自己比行号；知道"重赋值"这一项不可信 |

**例 2：ARVO-42483440（暴露伪样本）**

| | 内容 |
|---|---|
| facts 说 | free@292，crash@292（行号一样，**容易误读成"先放后用"**） |
| interpretation 说 | **`crash_after_free=false`** |
| **价值** | 直接判定"不是先释放后使用" |

**例 3：OSV-2024-380（暴露循环陷阱）**

| | 内容 |
|---|---|
| facts 说 | crash@985，free@988（行号反序） |
| interpretation 说 | **`crash_after_free=false`** |
| **价值** | 不会误判成"先放后用"（虽然实际可能是循环上一轮，但至少不误判） |

### 一个量化证据

`同函数释放后访问` 这 5 条样本的判断：

| 样本 | `crash_after_free` | 结论 |
|---|---|---|
| ARVO-42483214 | True | 符合 |
| **ARVO-42483440** | **False** | **不符合该机制** |
| ARVO-42488143 | True | 符合 |
| ARVO-42494732 | True | 符合 |
| **OSV-2024-380** | **False** | **不符合该机制** |

**5 条里 2 条其实不属于这个 pattern。这个信号 facts 里没有，只有 interpretation 能给。**

### 所以为什么要一起喂

```
facts           →  原料：哪里分配、哪里释放、哪里崩、变量是什么类型
interpretation  →  已经算好的中间结论：先后顺序、是否重赋值、可靠性如何
                    ↓  合起来喂给 LLM
  LLM 不用浪费算力做机械比较（省 token、少出错）
  并且能直接看到"哪些样本不可靠"（避免基于坏样本归纳）
```

**一句话：facts 是素材，interpretation 是已经算好的算术结果 + 错题标记。**

## 3.6 交接给 stage3

| stage3 需要什么 | stage2 给了什么 |
|---|---|
| "按崩溃类型分组" | `facts.crash_type`（1,139 条，19 种类型） |
| "这条崩溃的机制线索" | `facts.sites` / `entity.deep.assignments` / `input_reachability` / `context.in_loop` |
| "哪些样本可疑" | `interpretation.confidence` + `missing` |
| "能不能只看某几个字段" | `interpretation.key_facts` + `findings`（已压缩成 9 个字段） |

---

# 4. stage3：共性提取 → pattern

## 4.1 目的

**把同一类型的几百条崩溃，按"机制"聚成若干组（pattern）。**

类比：把一堆病历按"致病机理"分科室——不是按症状（那太粗），也不是按病例（那太细）。

## 4.2 输入

| 输入 | 来源 | 规模 |
|---|---|---|
| `facts`（每条压成精简块） | stage2 入口① | 1,139 条 |
| `interpretation`（9 字段） | stage2 入口② | 1,139 条 |

**先按 `crash_type` 分组**，同类型才可能同机制：

| 类型 | 样本数 |
|---|---|
| heap-buffer-overflow | 601 |
| segv-on-unknown-address | 158 |
| heap-use-after-free | 121 |
| stack-buffer-overflow | 110 |
| global-buffer-overflow | 51 |
| 其余 14 种 | 98 |

## 4.3 怎么做（两轮 LLM）

```
第 1 轮：切批（每批 15 条，最多 5 并发）
         每批问 LLM："这些崩溃在机制上是否同类？分成几组？"
         → 每批产出若干"批内 pattern"

第 2 轮：把所有批内 pattern 再喂给 LLM
         问："这些碎片化的形态，哪些其实是同一种？"
         → 合并成类型级的最终 pattern
```

**为什么必须两轮**：单轮只有 15 条视野，会把同一机制在不同批次里重复命名为不同 pattern；
只有第二轮才能看到全局，做合并。


## 4.4 输出

`outputs/stage3/<type>/final.json`，顶层 7 个字段：

| 字段 | 内容 |
|---|---|
| `crash_type` | 本类型 |
| `final_patterns` | pattern 数组（核心） |
| `unclassified` | 没能归入任何 pattern 的样本 |
| `low_support` | 样本数过少、置信度低的 pattern |
| `merge_notes` | 第二轮合并时做了什么 |
| `total_batches` / `total_input_patterns` | 批次数 / 合并前的碎片数 |

**单个 pattern 的 7 个字段**：

| 字段 | 装什么 | 对下游的作用 |
|---|---|---|
| `name` | 机制名（如"同函数释放后访问"） | 人读 |
| `support` | 这条 pattern 有几条样本 | 判断可信度 |
| `narrative` | 这个机制**怎么发生** | **stage4 抽象的原材料** |
| `trigger_condition.where_alloc` | 在哪里分配 | stage5 定位上游代码 |
| `trigger_condition.where_free` | 在哪里释放 | stage5 定位要提前触发的动作 |
| `trigger_condition.where_use` | 在哪里被错误使用 | stage5 定位崩溃点 |
| `trigger_condition.what_input_controls` | **哪个输入字段控制** | **stage5 决定改哪个字节** |
| `trigger_condition.minimal_requirement` | 最小触发条件 | stage5 的变异目标 |
| `dimensions` | 变体维度 | stage4 的 `parameterization` |
| `sample_ids` | 覆盖了哪些崩溃 | **stage4 按这个取样本** |

**实测规模**：22 个 pattern

| 类型 | pattern 数 |
|---|---|
| UAF | 5 |
| HBO | 5 |
| stack | 6 |
| global | 6 |

## 4.5 交接给 stage4

**stage4 的输入 = 1 个 pattern + 该 pattern 的 `sample_ids` 对应的 facts。**

这是全流程最重要的一次"对接"：pattern 只提供"机制描述"，**样本 facts 才是抽象的原料**。

---

# 5. stage4：特征抽象 → features.json

## 5.1 目的

**把一个 pattern（可能覆盖几十条样本）归纳成 1 个"项目无关"的通用特征。**

**"项目无关"是硬要求**：特征里不能出现项目名、函数名、行号、变量名。否则它只能用在那个项目上。

类比：把"libredwg 的 `dxf_objects_read` 在 12267 行读了已释放的 `pair`"，
抽象成"**同一函数内释放对象后，后续或循环路径继续访问该对象**"——
后者才能拿去问"libxml2 有没有这种代码？"

## 5.2 输入

| 输入 | 来源 | 规模 |
|---|---|---|
| 1 个 pattern 的文本 | `stage3/<type>/final.json` 的 `final_patterns[i]` | `name`/`support`/`narrative`/`trigger_condition`/`dimensions` |
| 该 pattern **全部**样本的 facts | `artifacts/facts/<OSV>/facts.json` 按 `sample_ids` 过滤 | 每条压成 14 行 |

**每条样本压成的 14 行**（以 ARVO-42494732 为例）：

```
[ARVO-42494732] libredwg
  类型: heap-use-after-free
  崩溃代码: pair != NULL && pair->code == 0 && pair->value.s | ...
  崩溃访问: READ 宽 2 字节，区域 16 字节
  核心变量: pair (Dxf_Pair*)
  分配: calloc @ xcalloc，16 字节，跨函数=True
  报告给的释放点: dxf_free_pair:515
  函数内调用: 12263:<operator>.alloc(80) | 12274:strdup(...) | 12275:dxf_free_pair(pair) | ...
  变量赋值: 12264 *pair = dxf_read_pair (dat) | 12276 pair = new_object (...) | ...
  函数参数: dat:Bit_Chain*restrict, dwg:Dwg_Data*restrict
  崩溃行表达式分解: <operator>.logicalAnd(...) | <operator>.indirectFieldAccess(pair->code) | ...
  守卫条件: 12265:pair != NULL | 12267:pair->code == 0 | ...
  上下文: in_loop=True | 守卫=pair != NULL | ...
  输入可达: ['dat']
```

**决定 LLM 能否推出机制的三行**：

| 行 | 回答什么 |
|---|---|
| `函数内调用` | **释放有几种方式**（6 处 `dxf_free_pair(pair)`） |
| `变量赋值` | **释放后有没有重新赋值**（这是 UAF 的核心判据） |
| `输入可达` | **输入从哪个参数进来** |

## 5.3 怎么做

**每个 pattern 调一次 LLM**。Prompt 三部分：

```
① System：你是机制归纳专家。把同类崩溃归纳成 1 个项目无关的通用特征。
           mutation_target 要写"字段类别"，但每条必须在括号里给出 1-3 个具体体现。
           禁止出现项目名/函数名/行号/变量名。推不出来的写进 limitations。
② User：  pattern 的 JSON  +  全部样本的 14 行块
③ 输出 schema：feature_name / precondition / trigger_path / mutation_target /
                parameterization / limitations / sample_ids
```

**核心约束**（都是踩过坑之后加的）：

| 约束 | 为什么 |
|---|---|
| 每条 `mutation_target` 必须在括号里给具体体现 | 否则会输出"控制生命周期分支的条件字段"这种废话 |
| 禁止堆砌抽象名词 | 试过给更多 facts，结果输出变成"所有权、引用计数、保留/删除/错误/清理/析构/回收"这种拼接，更难用 |
| 禁止项目专有名字 | 否则无法迁移到别的项目 |
| 推不出来的写 `limitations` | 不许编造 |

**脚本**：`pipeline/s4_abstract_features.py`

```bash
python3 s4_abstract_features.py --type uaf --pattern "同函数释放后访问"
python3 s4_abstract_features.py --type uaf --all
```

**脚本内自动校验**：

| 检查 | 判据 |
|---|---|
| 无项目信息泄漏 | 用样本的 project/fn/line/变量名建黑名单，搜特征文本 → 必须 0 命中 |
| `mutation_target` 至少 2 条 | 长度检查 |
| `precondition` / `trigger_path` 至少 3 条 | 长度检查 |

## 5.4 输出

`outputs/stage4/<type>/features.json`

```json
{
  "_meta": {
    "crash_type": "heap-use-after-free",
    "method": "LLM 归纳（deepseek-flash）",
    "script": "s4_abstract_features.py",
    "prompt": "prompts/stage4_abstract_feature.md"
  },
  "features": [
    {
      "id": "uaf-llm01",
      "source_pattern": "同函数释放后访问",
      "source_support": 5,
      "feature_name": "同函数内释放后继续解引用",
      "precondition": ["…4-5 条：什么样的代码会长这样…"],
      "trigger_path": ["…3-5 步：输入要造成什么才能崩溃…"],
      "mutation_target": [
        "控制对象生命周期分支的条件字段（布尔状态标志 / 嵌套层级 / 记录类型码）",
        "控制容器元素个数与遍历规模（链表节点数 / 遍历项数 / 记录条数）",
        "控制待释放对象成员或数组的规模与内容（成员数组长度 / 字符串值长度 / 块链表项数）"
      ],
      "parameterization": {"维度名": ["取值"]},
      "source_samples": ["ARVO-42483214", "…"],
      "limitations": ["…推不出来的东西…"],
      "validation": {"project_leaks": [], "mutation_target_count": 3}
    }
  ]
}
```

**每个字段的用途**：

| 字段 | 给谁用 |
|---|---|
| `feature_name` | 人看，一句话认机制 |
| `precondition` | **stage5 判断"这个项目里有没有这种代码形态"** |
| `trigger_path` | **stage5 判断"输入要走到哪一步"** |
| `mutation_target` | **stage5 直接据此决定改哪个字段** |
| `parameterization` | stage5 落地时选择具体变体 |
| `limitations` | 人看，知道这条特征不可靠在哪 |
| `source_samples` | 可追溯 |

**实测规模**：UAF 5 个特征（1 pattern → 1 feature）

| ID | 来源 pattern | 样本 | 特征名 |
|---|---|---|---|
| `uaf-llm01` | 同函数释放后访问 | 5 | 同函数内释放后继续解引用 |
| `uaf-llm02` | 缓冲释放后旧指针 | 34 | 重分配或释放后旧缓冲指针仍被访问 |
| `uaf-llm03` | 清理析构后悬垂访问 | 31 | 清理或析构先释放后仍读取旧指针 |
| `uaf-llm04` | 跨函数陈旧对象访问 | 11 | 跨函数释放后仍访问陈旧对象 |
| `uaf-llm05` | 容器节点销毁后遍历 | 26 | 容器节点销毁后旧指针遍历访问 |

## 5.5 交接给 stage5

**stage5 的输入 = `features.json`（N 个特征）+ 目标项目的源码 + 该项目已有的崩溃清单（用来定位源码版本）。**

---

# 6. stage5：算子生成与验证

## 6.1 目的

**把项目无关的特征，落到某个项目的具体代码上，写成可编译的变异算子，并用实验验证它有没有用。**

## 6.2 输入

| 输入 | 来源 | 说明 |
|---|---|---|
| `features.json` | stage4 | 含 N 个特征，**每个特征要变成 1 种策略** |
| 目标项目的漏洞版源码 | git 仓库（`pin_commit`） | 从清单的 `repo_url` + `pin_commit` 定位 |
| 该项目的崩溃信息 | 清单里该项目的一条崩溃 | 提供 `fault_file`/`fault_fn`/`fault_line` |

## 6.3 两个子步骤

### 6.3.1 `s5_fetch_source.py` —— 读源码

```bash
python3 s5_fetch_source.py ARVO-42494732
```

**做什么**：

| 动作 | 输出 |
|---|---|
| 从清单取 `repo_url` + `pin_commit` | — |
| 定位本地仓库（没有就从 `repo_url` clone） | `repo_local` |
| `git show <commit>:<file>` 取出崩溃版本的完整文件 | `source/in_dxf.c`（492 KB / 12,885 行） |
| **grep `LLVMFuzzerTestOneInput`，把 fuzz target 源码也拷一份** | **`harness/llvmfuzz.c`（277 行）+ `dwgfuzz.c`（786 行）** |
| 抽出故障函数 | `function_source`（33 行） |
| 扫函数内所有释放类调用 | `free_call_sites`（4 处） |
| 抽出保护宏的完整定义 | `guard_macros`（`DXF_RETURN_ENDSEC`） |
| 找判定函数的定义并抽取 | `predicate_source`（`is_dwg_object`） |

**输出**：`mutator_custom/stage5/<OSV>/source_context.json` + `source/<file>.c` + **`harness/`（fuzz target 源码）**

> ⚠️ **必须用崩溃版本的 commit**，不能用 HEAD。实测：HEAD 上 `dxf_objects_read` 的行号已经变了（14632 vs 12267）。

### 6.3.2 `s5_generate_mutator.py` —— 生成算子

```bash
python3 s5_generate_mutator.py --feature uaf-llm01 --osv ARVO-42494732 --type uaf
```

**输入**：`features.json` 里的 1 个特征 + `source_context.json` + 该项目的崩溃信息

**输出**：`mutator_custom/stage5/<OSV>/mutator.json`（结构化记录）+ `mutator.c`（可编译代码）

## 6.4 核心规则：1 个特征 = 1 种策略

```
features.json（N 个特征）
    │
    ├─ 特征 1  ──→  变异策略 1
    ├─ 特征 2  ──→  变异策略 2
    ├─ 特征 3  ──→  变异策略 3
    ├─ 特征 4  ──→  变异策略 4
    └─ 特征 5  ──→  变异策略 5
                        │
                        ▼
        ┌──────────────────────────────────────┐
        │  mutator.c                           │
        │  5 种策略 + libFuzzer 自带 default    │
        └──────────────────────────────────────┘
```

## 6.5 权重：default 60% + N 个策略平分 40%

| 来源 | 权重（N=5） |
|---|---|
| **libFuzzer 自带 default** | **60%** |
| 策略 1–5 | **8% each** |

**为什么要给 default 60%**：自定义算子只覆盖"某一类机制"，如果让它独占 100%，会把
"其他类型 bug" 的探索能力挤掉（实测上一版 100% 自定义导致覆盖率只有 default 的 37%）。

**权重实现**（整数运算，精确 8%）：

```c
unsigned r = rng_next(&s) % 100u;
if (r < 60u) return LLVMFuzzerMutate(Data, Size, MaxSize);
unsigned k = (r - 60u) * 5u / 40u;      /* r=60..99 → k=0..4，每个 k 恰好 8 个取值 */
```

## 6.6 测试钩子（4 个环境变量）

这些不是给生产用的，是给"验证"用的：

| 变量 | 作用 |
|---|---|
| `LIBREDWG_MUTATOR_OFF=1` | **100% 走 default**（A/B 对照用，同一个二进制） |
| `LIBREDWG_CUSTOM_PCT=<0..100>` | 覆盖自定义比例，默认 40 |
| `LIBREDWG_FORCE_STRATEGY=<0..4>` | 强制某个策略，**不回退 default**（用来测单个策略） |
| `LIBREDWG_TRACE_FILE=<path>` | 每次调用追加一行 `D` / `S<k>` / `F<k>`（用来统计权重） |

## 6.7 四级门禁（进 fuzz 前的体检）

脚本 `stage5_verify.py`。**它不是"效果评判"，它只保证"实现没写错"**：

| 级别 | 查什么 | 为什么需要 |
|---|---|---|
| **V1 语法** | `clang -fsyntax-only -Wall -Wextra` | 编译不过直接出局 |
| **V2 结构** | 逐策略：变异后不缩小、不超 `MaxSize`、`ENDSEC` 数量不变 | 防止算子把输入搞坏 |
| **V3 自举** | 反复变异，看能否重放已知崩溃点 `in_dxf.c:12267` | **端到端因果检验**：算子真实现了机制就该能造出原崩溃 |
| **V4 权重** | 用 trace 统计 1000~2000 次，比对 60% / 8%×5 | 防止权重写错导致某策略饿死 |

**V3 的判据要分清"必须命中"和"探索性"**：只有 `strat0`（特征 `uaf-llm01`，在本项目有已知崩溃）必须命中；
其余 4 个策略是为**其他机制**设计的，在 libredwg 里没有已知实例，所以只看"可适用性"。
这就是 `--require-hit 0` 参数的含义。

## 6.8 输出与实验

**产物目录**：`mutator_custom/stage5/<OSV>/`

| 文件/目录 | 内容 |
|---|---|
| `mutator.c` | 算子代码 |
| `mutator.json` | 结构化记录（策略说明、依据、限制） |
| `source/` + `source_context.json` | 6.3.1 的产物 |
| `design/` | `MUTATOR_CONTRACT.md`（接口契约）/ `landing_plan.json`（落地设计）/ `review.json`（审查结论） |
| `seeds/` | 6 个真实 DXF 种子 |
| `fuzz_exp/` | 实验：6 次运行 × 30 分钟 |

**实验设计**：

| 项 | 值 |
|---|---|
| 二进制 | **同一个**，只靠 `LIBREDWG_MUTATOR_OFF` 切换模式 |
| 两种模式 | 100% default vs 60% default + 5×8% 自定义 |
| 重复 | 3 次 |
| 并行 | **6 个实例同时跑**（同一时刻、同一机器、同一 `-seed=1`） |
| 时长 | 每次 30 分钟 |

**每次运行的目录结构**（统一约定）：

```
fuzz_exp/<mode>_<rep>/
├── corpus/           语料（种子 + 演化出的输入）
├── crash/            libFuzzer 产物：crash-* / timeout-* / oom-*
├── replay/           重放与覆盖
│   ├── oneshot/      coverage.json + edges.txt（整包一个进程，主指标）
│   └── perfile/      coverage.json + edges.txt + per_file.tsv（逐文件下界）
├── run.log           libFuzzer 输出
└── run_one.out       本次运行的 stdout
```

**⚠️ 崩溃必须去重**：`crash-<sha1>` 的 sha1 是**输入内容**的哈希，不是崩溃点的哈希。
同一个 bug 会产生上百个不同输入。实测：`default_1` 的 88 个文件其实只是 **2 个** bug。
所以必须用 `dedup_crashes.py` 按 `SUMMARY: AddressSanitizer: <type> <file>:<line>` 归并。

## 6.9 实验结果

### ① 先说清"为什么必须去重"

**「唯一崩溃点」的定义**：`<ASan 错误类型> @ <文件名>:<行号>`，即**崩溃位置**，不是接口、不是整个文件、也不是根因。

推导过程（`dedup_crashes.py`）：对每个 `crash-*` 文件跑一次 `llvmfuzz -runs=1`，
从输出抓 `SUMMARY` 行再用 `r'SUMMARY: AddressSanitizer: (\S+) (\S+?):(\d+)'` 提取：

```
SUMMARY: AddressSanitizer: heap-use-after-free /src/libredwg/src/in_dxf.c:12267:36 in dxf_objects_read
                              ↓ 正则
                    ('heap-use-after-free', 'in_dxf.c', 12267)
                              ↓
              键 = "heap-use-after-free @ in_dxf.c:12267"
```

**注意它丢了三样东西**：
1. **列号**（`12267:36` → `12267`）→ 同一行不同列的崩溃会合并
2. **函数名**（`in dxf_objects_read` 不参与键）
3. **根因**——同根因崩在不同行会被**拆成多个点**（实测见下）

本次实验的 7 个点：

```
heap-use-after-free    @ in_dxf.c:12267     ← 目标 UAF
heap-buffer-overflow   @ in_dxf.c:11947
heap-buffer-overflow   @ in_dxf.c:11942     ← 以下三个都在 dxf_tables_read 的同一段 6 行内
SEGV                   @ in_dxf.c:11948     ← （_ctrl->num_entries 在 if(_ctrl) 判空之前被读）
heap-buffer-overflow   @ dwg.spec:6304
SEGV                   @ in_dxf.c:971
SEGV                   @ sanitizer_libc.cpp:167
```

**所以「5 vs 4」是"崩溃位置数"，会偏高，不能当成 bug 数。**



libFuzzer 的产物文件名是 `crash-<sha1>`，**这个 sha1 是「输入内容」的哈希，不是「崩溃点」的哈希**。
同一个 bug，只要输入有细微差别就会存成另一个文件。

实测（default_1）：

```
88 个 crash-<sha1> 文件
  ├── 83 个 → heap-use-after-free @ in_dxf.c:12267   ← 同一个 bug
  └──  5 个 → heap-buffer-overflow @ in_dxf.c:11947  ← 另一个 bug
```

**88 个文件其实只是 2 个 bug。** 如果直接数文件，会把"同一 bug 的输入多样性"误当成"发现了更多 bug"。
所以必须按 `SUMMARY: AddressSanitizer: <type> <file>:<line>` 归并。

### ② 目标类型（UAF）的触发情况

这是本项目真正关心的问题——`strat0` 就是针对 UAF 的。

| 运行 | 执行次数 | UAF 崩溃文件 | 每 10 万次执行 |
|---|---|---|---|
| default_1 | 1,028,977 | 83 | 8.07 |
| default_2 | 1,017,501 | 14 | 1.38 |
| default_3 | 868,845 | 19 | 2.19 |
| custom_1 | 1,254,884 | 96 | 7.65 |
| custom_2 | 945,058 | 156 | **16.51** |
| custom_3 | 668,821 | 137 | **20.48** |

| 汇总口径 | default | custom | 倍数 |
|---|---|---|---|
| UAF 崩溃文件总数 | 116 | **389** | **3.35×** |
| 合并触发率（总 UAF / 总执行 ×10 万） | 3.98 | **13.56** | **3.41×** |
| 逐次均值 | 3.88 | 14.88 | 3.84× |
| 逐次中位数 | 2.19 | 16.51 | 7.55× |
| **UAF 唯一崩溃点** | **1** | **1** | 相同 |

**逐次成对比较：9 对里 custom 有 8 对更高**（default_1 的 8.07 略高于 custom_1 的 7.65）。
精确 Mann-Whitney：`U_custom = 8/9`，单侧 `p = 0.100`，双侧 `p = 0.200`。

> **必须注明**：`n = 3 vs 3` 时双侧 p 的**理论下限就是 0.10**，数据再干净也到不了 0.05。
> 所以这里只能说"方向一致（8/9）"，**不能声称统计显著**。

**结论**：两种模式都 3/3 次触发同一个 UAF（`in_dxf.c:12267`），
但 custom **单位执行次数触发这个 UAF 的密度是 default 的 3.4 倍**，
且它触发的是**同一个** bug——不是新 bug。

### ③ 所有类型的总览

| 指标 | default | custom |
|---|---|---|
| 覆盖边均值 | **14,064** | 13,483（**95.9%**） |
| 特征数均值 | 35,093 | 30,884（88.0%） |
| 执行次数均值 | 971,774 | 956,254（98.4%） |
| 崩溃文件总数 | 131 | 395（3.0×） |
| 去重后唯一崩溃点 | 5 | 4 |

**去重后 5 vs 4** 的具体构成：

| 崩溃点 | default | custom |
|---|---|---|
| `heap-use-after-free @ in_dxf.c:12267`（目标） | 3/3 | 3/3 |
| `heap-buffer-overflow @ in_dxf.c:11947` | 3/3 | 2/3 |
| `SEGV @ in_dxf.c:11948` | 1/3 | — |
| `SEGV @ sanitizer_libc.cpp:167` | 1/3 | — |
| `heap-buffer-overflow @ in_dxf.c:11942` | 1/3 | — |
| `SEGV @ in_dxf.c:971` | — | 2/3 |
| `heap-buffer-overflow @ dwg.spec:6304` | — | 1/3 |

**这 7 个点里，只有 1 个是目标 UAF，其余 6 个是"顺带发现的别的 bug"**——因为 fuzz 跑的是整个 libredwg，
而自定义算子只占 40% 的变异（60% 仍是 libFuzzer 默认），所以语料演化会摸到解析器的其他位置。

| 崩溃点 | 所在函数 | 性质 |
|---|---|---|
| `in_dxf.c:12267` UAF | `dxf_objects_read` | **目标**：释放后未置空 |
| `in_dxf.c:11942/11947/11948` | `dxf_tables_read` | **同一个 bug**（`_ctrl->num_entries` 在 `if(_ctrl)` 判空之前被读） |
| `in_dxf.c:971` SEGV | `dxf_read_CMC` ← `add_AcDbDetailViewStyle` | 另一个解析器（CMC 颜色） |
| `dwg.spec:6304` HBO | `dwg_free_CELLSTYLEMAP_private` | **在 free 路径**，不是解析 |
| `sanitizer_libc.cpp:167` SEGV | `__sanitizer::internal_strlen` ← `printf_common` | **误归因**：崩在 ASan 自己的 printf 里，真实 bug 是 libredwg 传了非法 `%s` |

| 模式 | 全部崩溃文件 | 目标 UAF | 其他 bug |
|---|---|---|---|
| default | 131 | 116（88.5%） | 15（11.5%） |
| custom | 395 | 389（98.5%） | 6（1.5%） |

**所以「唯一崩溃点数 5 vs 4」不能用来评价目标算子的效果**——它统计的是"这个项目有多少 bug"，
与算子无关，而且 `11942/11947/11948` 三个点其实是同一个根因。
**评价目标算子应该看目标 bug 的触发密度（3.41×），见 §6.9②。**


### ④ 怎么读这组结果

| 看什么 | 结论 |
|---|---|
| **覆盖率** | custom 是 default 的 95.9% → 自定义算子**没有损害**探索能力（这是 60% default 权重的作用） |
| **目标类型（UAF）触发密度** | custom 是 default 的 **3.4 倍**（3.41×合并率），8/9 成对比较更高 |
| **发现了几个不同的 bug** | default 5 个、custom 4 个 → **没有增加** |
| **有没有发现新 bug** | custom 独家 2 个，default 独家 3 个 → 整体打平 |

**所以**：自定义算子确实让它**更密集地回到目标 UAF**，但**没有扩展 bug 的种类**。
这与"5 个策略里只有 `strat0` 在本项目有机制对应，其余 4 个是为别的机制设计的"一致——
`strat0` 起了作用，另外 4 个在 libredwg 的 DXF 路径里没有可触发的实例。

**局限（不掩饰）**：
1. 重复只有 3 次，UAF 触发密度的差异**不具统计显著性**（p=0.200）。
2. 5 个通用特征全落在同一个项目上，本实验只证明"这种落法没有增强 bug 多样性"，
   **不能证明"特征提取方法无效"**。

---

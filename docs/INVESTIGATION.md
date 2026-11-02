# mutator_create 调查记录（Q1–Q12）

> **文件名说明（2026-11-02）**：本文是调查当时的记录，文中的脚本名是**合并前**的布局。
> 之后 stage5 的 12 个脚本 + 2 个库按 4 个阶段拆成 s5_1_main.py / s5_2_prepare.py / s5_3_audit.py / s5_4_analyze.py / s5_5_build.py / s5_6_lib.py，
> 对应关系见 `docs/GENERATION_PIPELINE.md`。

---

调查日期：2026-11-02
约束遵守情况：默认只读；修改仅限白名单（见 §13）；未重跑 stage1–4、未重跑 A/B、未调用 LLM、未改 v2/ 产物（`verification.json` 由白名单动作 #1 的脚本自身写入，见 §13.2）、未改 `mutator.c`、未动 V1 基线。
调查脚本全部落在 `/tmp/audit/`。

---

## Q1 a001 在无 OBJECTS 段的种子上到底做了什么

**结论**：判断成立。`pm003_mutate_a001` 在找不到 OBJECTS 段、或段内无 code-0 记录时，**直接返回原输入**（不是返回 `LLVMFuzzerMutate`）。因此「去掉含 OBJECTS 的种子」会让 custom 臂的 50% 特征路径变成 100% 空转，该方案不可用。

**证据**

失败路径 1（找不到 OBJECTS 段）—— `v2/mutator.c:129`：

```c
127: static size_t pm003_mutate_a001(uint8_t *Data, size_t Size, size_t MaxSize, unsigned int Seed) {
128:   size_t section_start = 0;
129:   if (!pm003_find_objects_start(Data, Size, &section_start)) return Size;
```

失败路径 2（段内无 code-0 记录）—— `v2/mutator.c:131`：

```c
130:   size_t total = pm003_scan_candidates(Data, Size, section_start, -1, NULL, NULL);
131:   if (total == 0) return Size;
```

`pm003_find_objects_start` 的匹配条件（`v2/mutator.c:77-95`）：必须先出现一行 group code = **2**，且其下一行 trim 后**恰好等于** `OBJECTS`。`pm003_scan_candidates`（97-125）从段起点扫到 `0/ENDSEC` 为止，只统计 code == 0 的记录。

**剥段副本**（`/tmp/audit/strip.py`，逻辑：删掉从 `  0\r\nSECTION\r\n` 到 `  2\r\nOBJECTS\r\n` 之后第一个 `  0\r\nENDSEC\r\n` 的整段）

```
  Constraints.dxf: 127870 -> 20625 字节  (删除 [16617, 123862) 共 107245 字节)
     OBJECTS 残留次数: 0   SECTION: 9   ENDSEC: 6
  sample_r14.dxf: 38271 -> 12543 字节  (删除 [12533, 38261) 共 25728 字节)
     OBJECTS 残留次数: 0   SECTION: 5   ENDSEC: 5
  sample_2018.dxf: 89031 -> 19331 字节  (删除 [15518, 85218) 共 69700 字节)
     OBJECTS 残留次数: 0   SECTION: 9   ENDSEC: 6
```

`grep -c OBJECTS` 全部为 0。副本落在 `/tmp/audit/seeds/`，未写入 `seeds/`。

**数据**：`diversity.c`（1000 个 Seed）

| 种子 | 大小 | CHANGED | UNCHANGED | DISTINCT |
|---|---|---|---|---|
| `/exp/seeds/Constraints.dxf`（含 OBJECTS） | 127,870 | 500 | 500 | **500** |
| `/tmp/audit_seeds/stripped_Constraints.dxf` | 20,625 | **0** | **1000** | **0** |
| `/exp/seeds/sample_r14.dxf` | 38,271 | 500 | 500 | **500** |
| `/tmp/audit_seeds/stripped_sample_r14.dxf` | 12,543 | **0** | **1000** | **0** |
| `/exp/seeds/sample_2018.dxf` | 89,031 | 500 | 500 | **500** |
| `/tmp/audit_seeds/stripped_sample_2018.dxf` | 19,331 | **0** | **1000** | **0** |

原始输出：

```
  Constraints.dxf                total=1000  CHANGED=500  UNCHANGED=500  DISTINCT=500
  stripped_Constraints.dxf       total=1000  CHANGED=0  UNCHANGED=1000  DISTINCT=0
```

**附带的探路数据**（单臂、非 A/B，仅用于判断剥段后默认臂还有没有空间）：剥段种子跑 60 s

```
#46999: cov: 10264 ft: 19657 corp: 633 exec/s 726 oom/timeout/crash: 0/0/0 time: 59s job: 9
```

→ 60 s / 46,999 execs，**0 崩溃**。

**存疑**：无。

---

## Q2 default 的 96/100k 是通过什么路径命中目标的

**结论**：部分成立、部分查不出来。10 个命中输入里 **9 个是目标 UAF、1 个是 SEGV@971**（replay 已确认）。default 的输入**不是单次小改**（最大 164,002 字节 > 最大种子 127,870，说明发生了插入），且有 3 个输入含**确定的非已知 code-0 值**（与 a001 同机制族）；但另外 7 个输入无法定位触发点。

**证据 1：replay 确认**

```
  crash-4b3f7a303ba9          32906  SUMMARY: AddressSanitizer: SEGV /src/libredwg/src/in_dxf.c:971:13
  crash-716492562312          80546  SUMMARY: AddressSanitizer: heap-use-after-free /src/libredwg/src/in_dxf.c:12267:36
  crash-a6e67318dda8          62967  SUMMARY: AddressSanitizer: heap-use-after-free /src/libredwg/src/in_dxf.c:12267:36
  crash-a76f163c55a0          93511  SUMMARY: AddressSanitizer: heap-use-after-free /src/libredwg/src/in_dxf.c:12267:36
  crash-a903a5c755bc          93511  SUMMARY: AddressSanitizer: heap-use-after-free /src/libredwg/src/in_dxf.c:12267:36
  crash-b4a40a68b92f         146346  SUMMARY: AddressSanitizer: heap-use-after-free /src/libredwg/src/in_dxf.c:12267:36
  crash-bdf724e8dc61          91423  SUMMARY: AddressSanitizer: heap-use-after-free /src/libredwg/src/in_dxf.c:12267:36
  crash-c3edb630ceb5         164002  SUMMARY: AddressSanitizer: heap-use-after-free /src/libredwg/src/in_dxf.c:12267:36
  crash-d7d5290293aa          71544  SUMMARY: AddressSanitizer: heap-use-after-free /src/libredwg/src/in_dxf.c:12267:36
  crash-f953a824dc94          78557  SUMMARY: AddressSanitizer: heap-use-after-free /src/libredwg/src/in_dxf.c:12267:36
```

（`rep01/default/crash/` 共 10 个文件；上面是 `docker exec ... llvmfuzz -runs=1 <file> | grep SUMMARY` 的原始输出，已去掉空行）

**证据 2：与最近种子的差异（按最长公共前缀选最近种子）**

| 输入 | 大小 | 最近种子 | 公共前缀 | 与种子同长 | 首次差异@ | 差异处段 |
|---|---|---|---|---|---|---|
| 4b3f7a303ba9 | 32,906 | sample_2013.dxf | 21,130 | 否 | 21,130 | 340 |
| 716492562312 | 80,546 | sample_2013.dxf | 45,614 | 否 | 45,614 | 176 |
| a6e67318dda8 | 62,967 | sample_2013.dxf | 16,582 | 否 | 16,582 | 100 |
| a76f163c55a0 | 93,511 | sample_2013.dxf | 71,904 | **是** | 71,904 | Thicken |
| a903a5c755bc | 93,511 | sample_2013.dxf | 32,724 | **是** | 32,724 | 62 |
| b4a40a68b92f | 146,346 | sample_2013.dxf | 3,887 | 否 | 3,887 | 9 |
| bdf724e8dc61 | 91,423 | sample_2013.dxf | 37,399 | 否 | 37,399 | 176 |
| c3edb630ceb5 | 164,002 | sample_2013.dxf | 9,001 | 否 | 9,001 | AcDbSectionViewStyle |
| d7d5290293aa | 71,544 | sample_2013.dxf | 11,336 | 否 | 11,336 | 6 |
| f953a824dc94 | 78,557 | sample_2013.dxf | 20,153 | 否 | 20,153 | 0 |

**关键观察**：8/10 与种子**不同长**；`b4a40a68b92f`（146,346）和 `c3edb630ceb5`（164,002）**比最大种子 127,870 还大**。→ default 做了**插入**，不是只替换。a001 的替换最多只能增长 63 字节（`new_len ≤ 64`，`v2/mutator.c:150`）。

**证据 3：触发点（用 libredwg 自己的 `is_dwg_object` 判定）**

探针 `/tmp/audit/isobj/probe.c`，链接 `src/.libs/libredwg.a`，`is_dwg_object` 声明取自 `src/dynapi.c:13637`：

```
1	DICTIONARY
0	ACDBDICTIONARYWDFLT
0	ACAD_PROXY_OBJECT
0	ACDBDETAILVIEWSTYLE
1	LAYOUT
1	XRECORD
0	ACDBPLACEHOLDER
0	POLYLINXRECORD
0	DICTIMNARY
1	GROUP
1	MLINESTYLE
```

10 个崩溃输入里，**第一條 code-0 值全部仍是 `DICTIONARY`**（已知对象），所以触发点不在第一条。全段扫描后，有 3 个输入含**确定的非已知 code-0 值**：

| 输入 | 非已知 code-0 值（下标, 值） |
|---|---|
| a6e67318dda8 | (5, `POLYLINXRECORD`) |
| c3edb630ceb5 | (17, `DICTIMNARY`) |
| f953a824dc94 | (22, `DICTIONARY\x10`)、另有 `ACDSSCHEMA`×2 |

这 3 个都是**字节级拼接/损坏**的产物（`POLYLINXRECORD` = `POLYLINE`+`XRECORD` 的混合），与 a001 的"换成非已知名"属于同一机制族。

**存疑（查不出来 + 卡在哪）**

其余 7 个输入，我用"提取 OBJECTS 段内全部 code-0 值 + `is_dwg_object` 判定"的方法**没找到唯一的触发点**。卡在两点：

1. **记录配对不可靠**：DXF 里同一行 `     0`（6 空格，是**值**）与 `  0`（2 空格，是**代码**）strip 后都是 `0`。`sample_r14.dxf` 里 `\r\n     0\r\n` 出现 **172** 次、`\r\n  0\r\n` 出现 **188** 次。任何"strip 后是数字就当代码行"的解析都会把它们混为一谈——包括 a001 自己的 `pm003_parse_code`（`v2/mutator.c:44-61`：只剥前导空格、要求行内无其他字符，所以 `     0` 会被判为 code 0）。
2. **种子里也有大量 `is_dwg_object=0` 的 code-0 值**（用同一套提取，`sample_2013.dxf` 有 29 个），但种子**不崩**。所以"存在非已知值"不是充分条件，我这个提取无法定出真正的门控谓词。

要定位需要**instrument libredwg 的 `dxf_read_pair` 循环**打印每次 (code, value) 与对应偏移，超出自助调查范围。

---

## Q3 语料里 49% 的 DWG 是从哪来的

**结论**：判断成立。DWG 语料**几乎全部来自 `Arc.dwg`**：default 臂 364 个 DWG 条目里 **356 个与 `Arc.dwg` 完全同尺寸（173,717 字节）**；只有 1 个等于 `Constraints.dwg` 的尺寸。去掉这两个 DWG 种子可以把有效特征权重从约 25% 推向 50%（零代码改动）。

**数据：格式分布（`reps/rep01`）**

| 臂 | 条目数 | DWG | DXF | JSON |
|---|---|---|---|---|
| default | 745 | **364 (48.9%)** | 381 (51.1%) | 0 |
| custom | — | **350** | — | 0 |

**数据：DWG 条目的大小分布（default 臂）**

```
  大小分布 top5: [(173717, 356), (111020, 1), (29062, 1), (76286, 1), (6969, 1)]
  = 173717 (Arc.dwg) 的: 356 个
  = 28932  (Constraints.dwg) 的: 1 个
  其他大小: 7 个
```

custom 臂：

```
  大小分布 top5: [(173717, 346), (71859, 1), (20377, 1), (142526, 1), (28932, 1)]
  = 173717 (Arc.dwg) 的: 346 个
  = 28932  (Constraints.dwg) 的: 1 个
  其他大小: 3 个
```

**数据：与 DWG 种子的前缀相似度**

| 臂 | 中位 | max | >=0.99 | >=0.9 | >=0.5 | >=0.1 |
|---|---|---|---|---|---|---|
| default | 0.0664 | 1.0000 | 2 | 2 | 7 | 162 |
| custom | 0.1540 | 1.0000 | 3 | 5 | 17 | 214 |

**前缀相似度低但同尺寸**：DWG 是二进制（头部字段靠前），libFuzzer 在头部改动会让"公共前缀"迅速塌到 0。所以**同尺寸是更强的证据**：356/364 = **97.8%** 与 `Arc.dwg` 同尺寸。

**存疑**：无法从 libFuzzer 日志直接证明这 356 个都是 `Arc.dwg` 的后代（没有父系记录）。同尺寸 + `>=0.1` 前缀占 45% 是间接证据链。

---

## Q4 121 条 UAF 里有哪些是「正向谓词」目标

**结论**：**查不出来**（用现有数据无法可靠分类）。`facts.sites[].code` 给的是**崩溃行上全部守卫片段的析取**（用 `|` 分隔多个候选表达式），不是"决定该漏洞的那一条谓词"；48/121 连守卫文本都没有。需要逐个崩溃读源码才能判定"等于某值"还是"不等于某集合"。

**数据：可用性**

| 项 | 数量 |
|---|---|
| UAF 总数 | **121** |
| 有 facts | 121 |
| 有崩溃行守卫文本（`sites[].origin` 以 `report` 开头且 `code` 非空，或回退到 `context.guards`） | **73** |
| 无守卫文本 | 48 |

**数据：按正则粗分类（不是结论）**

规则：positive = 出现 `strEQc`/`strcmp`/`strncmp`/`memcmp`/`== "…"`/`== 数字`；negative = 出现 `!= "…"`/`!= 标识符`/`!(标识符(`。

| 形态 | 数量 |
|---|---|
| other（既不匹配 positive 也不匹配 negative） | **60** |
| empty（无守卫文本） | **48** |
| negative | 6 |
| positive | 4 |
| mixed（两者都有） | 3 |

**4 条"positive"原文**

| osv_id | project | fault_fn:line | 守卫文本 |
|---|---|---|---|
| ARVO-42484314 | ndpi | ndpi_http_check_content:14xx | `strncmp((const char*)&packet->content_disposition_line.p…` |
| ARVO-42484479 | ndpi | ndpi_http_check_content:14xx | 同上 |
| ARVO-42485276 | libxml2 | xmlParserPrintFileContextI… | `(*(cur) == '\n') \|\| (*(cur) == '\r') \| *(cur) == '\n' \| *(cur) \| *(cur) == '\r'` |
| ARVO-42485599 | libxml2 | xmlParserPrintFileContextI… | 同上 |

后两条的"谓词"是**字符是否等于换行**——虽然形式上是"等于某值"，但随机变异极易满足，按用户判据应归入"不要"的一组。

**libredwg（ARVO-42494732）的归类**：`!is_dwg_object(name)`（`src/in_dxf.c:12272`），属**否定式**，属用户所说"不要"的一组——与"default 已经很容易"一致。

**存疑（卡在哪）**

要给出可信的 121 条分类，最小可行做法是：对每条崩溃取**故障函数的完整源码**（`cpg_path` 非空的有 121 条中的多数）+ 逐条读崩溃行所在分支的 `if` 条件。这需要：
1. 从 CPG 或 `in_*.c`/`decode*.c` 源码按 `fault_file:line` 取行（本调查未做，因为涉及 121 个仓库/CPG 的读取）；
2. 判断"这条 if 条件的哪一支导致 free 后不置空"——这是人工/agent 判定，不是正则能做的。

`facts.sites[].code` 之所以不能用：它把崩溃行上的多个守卫候选并列（例：libredwg 的 `"pair != NULL && pair->code == 0 && pair->value.s | pair != NULL && pair->code == 0 | pair != NULL | pair->code == 0"`），既含 `!=` 也含 `== 0`，粗分类只能落到 `mixed`/`other`。

---

## Q5 agent 全量审计（162 函数 × 1 函数/agent）的独有贡献

**结论**：**agent 独有且被采用的候选数 = 0**。被采用的唯一站点（`dxf_objects_read` 12284→12267）机械路（`s5c_mech_hypotheses.py` 的 R1）**单独也能找到**。

**证据**

`v2/candidate_findings.json` 6 条候选的来源归属：

| id | function | sources | fault_relation | evidence_ok | input_reachability | status |
|---|---|---|---|---|---|---|
| **c001** | `dxf_objects_read` | **audit, mech** | **same_site** | True | **complete** | unverified |
| c002 | `dxf_thumbnail_read` | audit | same_file | True | partial | unverified |
| c003 | `dxf_tables_read` | audit | same_file | True | partial | unverified |
| c004 | `resolve_postponed_object_r…` | audit | same_file | True | partial | unverified |
| c005 | `resolve_postponed_eed_refs` | audit | same_file | True | partial | unverified |
| c006 | `dwg_read_dxf` | mech | same_file | True | partial | unverified |

`summary`: `{"from_audit":6,"from_mech":2,"after_dedup":6,"merged":2,"evidence_ok":6,"input_complete":1,...}`

**反向核对（机械路单独能不能找到 c001 的站点）** —— `mech_hypotheses.json` 共 **2** 条：

```
  R1 dxf_objects_read 释放L12284 → 使用L12267      ← 就是 c001 的站点
  R1 dwg_read_dxf 释放L12839 → 使用L12707
```

→ **机械路单独就能命中**。所以 `sources` 只含 `audit` 的 4 条（c002–c005）**全部没有被 plan 采用**：

```
plan sites: [(s001, ['uaf-llm01'])]
plan mutations: [(a001, 'uaf-llm01', ['feature_pipeline:uaf-llm01:site:12284',
                                     'feature_pipeline:uaf-llm01:chain:step1'])]
```

plan 的 `basis_refs` **全部指向 `feature_pipeline` / `target_surface`，没有一条指向 `candidate_findings`**。

**成本**（`audit_logs/*.jsonl`，8 个文件）

| 日志 | turns | LLM 调用（= distinct turn） | 工具回传字符 | 工具分布 |
|---|---|---|---|---|
| chunk_026.jsonl | 26 | 26 | 9,488 | read_file 9, grep 4, flow 20 |
| chunk_9000.jsonl | 11 | 11 | 2,489 | read_file 4, grep 7, flow 2 |
| feat_uaf-llm02.jsonl | 28 | 28 | 7,594 | field_uses 5, read_file 16, grep 12, callers 3, callees 2 |
| feat_uaf-llm03.jsonl | 31 | 31 | 12,512 | field_uses 5, read_file 27, grep 15 |
| feat_uaf-llm04.jsonl | 28 | 28 | 7,021 | field_uses 5, read_file 14, grep 10, callers 3, callees 1 |
| feat_uaf-llm05.jsonl | 38 | 38 | 13,606 | grep 21, read_file 31 |
| src__free.c.jsonl | 15 | 15 | 4,368 | grep 15, read_file 6 |
| src__in_dxf.c.jsonl | 11 | 11 | 6,000 | grep 4, read_file 16 |
| **合计** | **188** | **188** | **63,078** | |

**存疑**：无法给出墙钟时长（日志无时间戳字段）。"LLM 调用 = distinct turn" 是推断，不是直接计数（日志里没有 `llm_call` 类型的事件）。

---

## Q6 s5_feature_binding.py 与 s5f_feature_pipeline.py 是否分叉

**结论**：**已分叉**。`feature_bindings.json` 唯一的"功能性"消费者是 `s5_verify_mutator_v2.py` 的 V1 schema 门禁（只检查存在 + 有 `schema_version`）；`mutator.json` 的 `binding_file` 是**字符串常量**。两者的选中特征一致（都是 `uaf-llm01`），但**权重来源完全不同**：binding 中没有 weight 字段，plan 的 0.5 来自 pipeline。

**证据 1：`feature_bindings.json` 的全部读取点**

| 位置 | 性质 |
|---|---|
| `s5_feature_binding.py:229` | 写出（schema_version 字符串） |
| `s5_feature_binding.py:288` | 写出（`json.dump` 到 `v2/feature_bindings.json`） |
| `s5_generate_mutator_v2.py:421` | **只写进 provenance 的字符串常量** `"binding_file": "feature_bindings.json"` |
| `s5_verify_mutator_v2.py:45` | V1 schema 门禁的文档清单里的名字 |
| `s5_verify_mutator_v2.py:143` | V1 门禁 `load(v2/feature_bindings.json)`，只用于检查 `schema_version` |

**证据 2：两者的一致性**

```
binding: selected = b001 | accepted = 5 / 30
  选中 feature = uaf-llm01  score = 1.0  （binding 里没有 weight 字段）
pipeline: found = ['uaf-llm01'] | weighting = {'default':0.5,'per_found_feature':0.5,'found':1,'total':5}
plan:     weighting = {'default':0.5,'features_total':0.5,'features':1,'per_feature':0.5,'total':1.0}
```

| 项 | binding | pipeline | 一致？ |
|---|---|---|---|
| 选中特征 | `uaf-llm01` | `uaf-llm01` | ✅ |
| 站点 | binding 里没有站点字段 | `s001` = `in_dxf.c:12284→12267` | ❌ 不可比 |
| 权重 | **无 weight 字段** | 0.5 | ❌ 分叉 |
| 候选数 | 30 条绑定 / 5 accepted | 5 特征 × 3 格式 = 15 格 / 1 found | ❌ 计数口径不同 |

**结论：删掉 `s5_feature_binding.py` 会不会破坏现有链路？**

**会，但只是让 V1 门禁失败**，不影响算子本身：

`gate_v1`（`s5_verify_mutator_v2.py:41-45`）要求 6 个文档都存在：

```python
for name, doc in (("manifest", manifest), ("target_surface", surface),
                  ("candidate_findings", findings), ("feature_bindings", bindings),
                  ("mutation_plan", plan), ("mutator", mutator)):
    if not doc: problems.append(f"{name} 缺失")
```

删掉脚本后 `feature_bindings.json` 不会再生成；若手工删掉该 JSON，`bindings = load(...)` 返回 `None` → `V1_schema` 报 `feature_bindings 缺失` → `overall = fail`。
**但它不参与** plan 生成、不参与 mutator 生成、不参与实验。

---

## Q7 stage3 的 dimensions 是否真有下游消费

**结论**：**HANDOFF/02 §8 的耦合说法是假的**。7 个维度名在整个 stage5 里**没有任何真读取**；它们的出现位置全部是"生产端"或"prompt 文本"。

**证据：7 个维度名的全部出现点（`grep -n` 于 `pipeline/*.py`）**

| 文件:行 | 性质 |
|---|---|
| `s2_3_interpretation.py:140,149,160,165` | **生产** `in_loop`（写进 interpretation） |
| `s2_3_interpretation.py:185,197` | **生产** `reassigned_between`（写进 interpretation） |
| `s4_abstract_features.py:146` | 读 `facts.context.in_loop` 只为拼 prompt 文本 |
| `s2_1_lib_cpg.py:270,311,312,453` | 生产 `in_loop`（数据流查询结果） |
| `s2_2_facts.py:652,904,961,991` | 生产 `facts.context.in_loop` |
| `s3_extract_patterns.py:129-135` | **SCHEMA 字符串**（给 LLM 的字段说明） |
| `s3_extract_patterns.py:199-205` | **MERGE_SCHEMA 字符串** |
| `s3_extract_patterns.py:172` | **MERGE_SYSTEM 提示词**：「机制维度相同（至少 free_before_use、free_and_use_same_function 一致）」 |
| `README.md:64,115` | 文档 |

**stage5 里 0 个读取点**：`s5f_feature_pipeline.py` 的 `classify()`（`s5f_feature_pipeline.py:253-283`）读的是 `site["function"]`、`site["use"]["kind"]`、`site["is_link_read"]`、`site["realloc_near"]` 和三个函数名正则，**不碰 dimensions**；`s5h_feature_audit.py` 读的是 `field_uses` 的结果，也不碰。

**结论**：`HANDOFF/02_STAGE1_TO_4_SCRIPTS.md` §8 的
> 改 stage3 的 `dimensions` 键名 → 必须同时检查 `s5f_feature_pipeline.py` 的 `classify()`、`s5h_feature_audit.py`

**是假的**。改 dimensions 键名只会影响 stage3 自身的合并轮（提示词里的一致性判据）和 stage4 的 prompt（若用到了）。

**附带发现**：`interpretation` 里 `reassigned_between` **已经有确定值**（121 条 UAF：`None` 80 / `True` 25 / `False` 16），但 stage3 的 5 个 pattern 全写 `unknown`。其中 `跨函数陈旧对象访问` 的 per-sample 分布是 **`True` 6 / `None` 5（多数 True）**，按 stage3 自己定的"dimensions 取多数值"规则（`s3_extract_patterns.py:175`）应当是 `true`，实际却是 `unknown`。

---

## Q8 CPG（689 个 / 9.2 GB）的实际消费面

**结论**：CPG 有两条消费链——① `s5a` 产出的 `cpg_dump.tsv`（方法清单 + 调用边）被 **4 个 stage5 脚本**消费；② `s2a` 自己的 Scala 脚本产出 `dataflow_features.jsonl`，经 facts 进入 interpretation 与 stage4 prompt。**如果只保留调用图 dump，会丢掉 ② 整条链。**

**证据：CPG 生产者**

| 位置 | 做什么 |
|---|---|
| `s2_1_lib_cpg.py:42,46,136-140` | `CPGDIR`/`JOERN`/`ensure_cpg()`（建图） |
| `s2_1_lib_cpg.py:239` | `build_script(cpg, targets)`（按 (函数名, 行号) 定位方法） |
| `s2_2_facts.py:31,558,1004` | 导入 `CPGDIR, JOERN, sh` |
| `s2_2_facts.py:687,723` 与 `1170,1207` | **自建 Scala 脚本 + `sh([JOERN,"--script",sp])` 两次** |
| `s5a_scan_target.py:74-81` | `find_cpg(project, commit)` |
| `s5a_scan_target.py:92,196` | `dump_cpg()` → 写 `cpg_dump.tsv` |

**证据：`cpg_dump.tsv` 的消费者（4 个）**

| 位置 | 取什么 |
|---|---|
| `s5_target_surface.py:61,344,351` | `read_cpg_dump`：`direct_callees` + `reachable_files` |
| `s5f_feature_pipeline.py:355,452` | `load_cpg_dump`：`callees`（短名单的 `call_rx` 匹配） |
| `s5g_interproc.py:152` | `load_dump`：`callers` / `callees` |
| `s5h_feature_audit.py:211` | 同上 |

→ 四个人都只用 **methods + edges**（方法清单 + 调用边），**没有人读数据流**。

**证据：数据流链**

```
s2_2_facts.py:561  OUT_DF = artifacts/_cache/dataflow_features.jsonl
s2_2_facts.py:646,648  d["reachability"] / d["guard"]
s2_2_facts.py:907,908  facts.context.guards / guard_count
s2_2_facts.py:916      facts.input_reachability
        ↓
s2_3_interpretation.py:96-103    bound_check_exists / bound_check_code
s2_3_interpretation.py:261-265   null_checked_before
s4_abstract_features.py:146-147       拼进 prompt：守卫= / 输入可达=
```

**数据流字段的覆盖率**（121 条 UAF）：`context.guards` 有值 **41/121**；`context.control_structures` 有值 **55/121**。

**结论：如果只保留调用图 dump，会丢掉的"现在真正在用"的信息**

| 丢掉的东西 | 谁在用 | 覆盖 |
|---|---|---|
| `facts.context.guards` / `guard_count` | `s2b`（`bound_check_exists`、`null_checked_before`）、`s4` 的 prompt | 41/121 |
| `facts.input_reachability` | `s4` 的 prompt（`输入可达: …`） | 未统计全量 |
| `facts.context.in_loop` | `s2b` 的 UAF 解释、`s4` 的 prompt | 见 `s2a:961` 完整性统计 |
| `facts.context.control_structures` | 本调查 Q4 的守卫文本回退来源 | 55/121 |

---

## Q9 §8.4 三配置横向对比的可信度

**结论**：**不可信**。三配置都是 180 s 单跑；配置 A/B 的原始日志**已不存在**（被 `rm -rf`）；n=5 实验里 **rep05 的日志已被覆盖**（`summary.json` 记 1391 execs，现存 `run.log` 记 12178）。0.60× 和 1.33× 无法与纯波动区分开。

**证据 1：现存日志对应哪个配置**

```
  default/run.log  Nov  1 23:22  exec/s 82
  custom/run.log   Nov  1 23:26  exec/s 45
```

→ 与 `README.md` 里配置 C 的 `exec/s 82 / 45` 一致。**配置 A、B 的日志不在**（`run_matrix.sh` 每次 `rm -rf default custom`）。

**证据 2：三配置的 default 臂密度 vs n=5 的 5 个 default 密度**

| 来源 | default 目标密度（/100k） | 备注 |
|---|---|---|
| 配置 A（100% a001） | 5.03 | 仅 README 记录；日志已删 |
| 配置 B（50%+5×10%） | 10.88 | 仅 README 记录；日志已删 |
| 配置 C（50%+1×50%） | **137.94** | 日志在（11-01 23:22） |
| n=5 rep01/default | 63.71 | 日志与 summary 一致 |
| n=5 rep02/default | 125.04 | 一致 |
| n=5 rep03/default | 103.47 | 一致 |
| n=5 rep04/default | 71.87 | 一致 |
| n=5 rep05/default | **359.45**（summary） | **现存 run.log 是 12178 execs，与 summary 的 1391 不符** |

同一 default 配置在 n=5 里的密度范围：**63.71 – 359.45（5.6 倍）**。

**证据 3：rep05 被覆盖的具体表现**

```
  rep01..rep04  default/custom  summary == 当前 run.log  一致=是
  rep05   default  summary=  1391  当前 run.log=12178  一致=**否**
  rep05   custom   summary=  8420  当前 run.log=None（无进度行）
```

**回答问题：配置 B 的 0.60× 和配置 C 的 1.33× 能否与纯波动区分开？**

**不能。**
- 0.60×（B）的分子分母都是单次；default 臂本身的波动是 5.6 倍，0.60 落在波动内。
- 1.33×（C）的点估计本身 95% CI 就是 `[0.64, 2.76]`（`README.md:31` 自己写了"含 1 → 不显著"），也落在波动内。
- 更严重的是：**rep05 这条最影响 pooled RR 的数据点已经无法从现存文件复核**（`summary.json` 是唯一来源）。

**存疑**：配置 A/B 的 default 密度（5.03 / 10.88）我无法用现存日志复核——只能引用 `README.md` 的记录。

---

## Q10 stage3 合并轮的信息损失量化

**结论**：损失很大且可量化。uaf 的 37 个输入 pattern 里 `trigger_condition` **完整保留只有 9/37（24%）**；**per-sample 计数的 evidence 从 114 条降到 0 条（100% 丢失）**；5 个 final pattern 在 7 维空间里只有 4 个可区分点。hbo 更严重：5 个 pattern 里 3 个（395/504 = 78% 样本）维度向量完全相同。

**数据 1：`trigger_condition` 完整保留率**

判据：对每个 final pattern 的 `merged_from` 里列出的每个输入 pattern，抽出其 `where_free` 里所有 ≥4 字符的标识符，检查是否全部仍出现在 final pattern 的 `where_free` 里。

| 类型 | 输入 pattern | final pattern | 完整保留 | 未完整保留 |
|---|---|---|---|---|
| **uaf** | 37 | 5 | **9/37（24%）** | 28 |
| hbo | 177 | 5 | **0/0**（映射失败，见存疑） | — |
| stack | 31 | 6 | 0/0（同上） | — |
| global | 18 | 6 | 0/0（同上） | — |

uaf 未完整保留的例子：`('重分配后旧缓冲访问', 8 个标识符, 6 个丢失)`、`('解码图像缓冲释放', 6, 4)`、`('解码器重置后旧指针', 6, 4)`。

**数据 2：per-sample 计数的 evidence（形如 `2/3 为 READ`）**

| 类型 | batch 层条数 | final 层条数 | 保留率 |
|---|---|---|---|
| **uaf** | **114** | **0** | **0%** |
| hbo | 429 | 0 | 0% |
| stack | 65 | 6 | 9.2% |
| global | 30 | 13 | 43.3% |

**数据 3：7 维向量两两比对**

| 类型 | final pattern 数 | 可区分点数 | 完全相同的组（name, support） |
|---|---|---|---|
| **uaf** | 5 | **4** | `[(清理析构后悬垂访问, 31), (容器节点销毁后遍历, 26)]` = 57/107 = **53%** |
| **hbo** | 5 | **3** | `[(长度偏移校验缺失, 215), (索引游标越界, 102), (字符串扫描越界, 78)]` = 395/504 = **78%** |
| stack | 6 | 5 | `[(栈索引指针越界读, 25), (格式化字符串越界, 5)]` |
| global | 6 | **4** | `[(全局表索引越界读, 3), (协议解析全局越界读, 2), (语音引擎全局数组越界读, 5)]` |

**存疑**：hbo/stack/global 的 `merged_from` 格式与 uaf 不同，我的 `batchN:name` 映射对它们失败（`0/0`），所以只有 uaf 的 `trigger_condition` 保留率可信。要算另外 3 个需要先看它们的 `merged_from` 实际写法。

---

## Q11 trigger_condition 做适用性判定（P3）的可行性

**结论**：**可行，且能复现现有 VERDICTS**。`trigger_condition` 当前**没有任何下游消费者**；用它做"`where_free`/`where_use` 的函数名 ∩ 项目可达函数"判定，5 个 uaf pattern 里只有 `同函数释放后访问` 有命中（2 个），与 `features/VERDICTS.json` 的实际判定**完全一致**。成本是一次 JSON 读取 + 一次 set 交集。

**证据 1：`trigger_condition` 的消费者**

`grep -n "trigger_condition" pipeline/*.py` → **无匹配**。唯一出现位置是 `outputs/stage3/*/final.json` 自身，以及 `s3_extract_patterns.py` 的 SCHEMA 字符串。

**证据 2：交集结果**

可达函数集合取自 `audit_worklist.json` 的 `functions`，**162 个**。

| pattern | 从 where_alloc/where_free/where_use 抽出的标识符 | 命中 162 个可达函数 | 命中的名字 |
|---|---|---|---|
| 缓冲释放后旧指针 | 47 | **0** | — |
| 清理析构后悬垂访问 | 35 | **0** | — |
| 容器节点销毁后遍历 | 46 | **0** | — |
| **同函数释放后访问** | 11 | **2** | `dxf_free_pair`, `dxf_objects_read` |
| 跨函数陈旧对象访问 | 22 | **0** | — |

原始输出：

```
  缓冲释放后旧指针               抽出函数名  47  命中可达 0  []
  清理析构后悬垂访问              抽出函数名  35  命中可达 0  []
  容器节点销毁后遍历              抽出函数名  46  命中可达 0  []
  同函数释放后访问                抽出函数名  11  命中可达 2  ['dxf_free_pair', 'dxf_objects_read']
  跨函数陈旧对象访问              抽出函数名  22  命中可达 0  []
```

**证据 3：与 VERDICTS 对照**

`v2/features/VERDICTS.json` 的实际判定：`llm01 found`（DXF）、`llm02/03/04 not_found`、`llm05` 不稳定。

| pattern | 交集判据 | VERDICTS 实际 | 一致？ |
|---|---|---|---|
| 同函数释放后访问（llm01） | 命中 2 | found（DXF） | ✅ |
| 缓冲释放后旧指针（llm02） | 命中 0 | not_found | ✅ |
| 清理析构后悬垂访问（llm03） | 命中 0 | not_found | ✅ |
| 跨函数陈旧对象访问（llm04） | 命中 0 | not_found | ✅ |
| 容器节点销毁后遍历（llm05） | 命中 0 | 不稳定（曾判 real，指向 llm01 的站点） | ✅（交集为 0，不支持 real） |

**证据 4：成本**

- 读 `outputs/stage3/uaf/final.json`（**18,515 字节**）
- 读 `audit_worklist.json`（取 162 个函数名）
- 一次 set 交集，脚本 `/tmp/audit/q1011.py` 总耗时 < 1 s（含加载 4 个类型的 final.json 与全部 batch 文件）
- 对比：现有做法是 `s5f` 扫 162 个函数（读 19 个源文件）+ `s5h` 对 4 个特征各 5 个候选跑 agent（**合计 125 turns**，见 Q5 表：llm02 28 + llm03 31 + llm04 28 + llm05 38）

**存疑**：交集判据只能判"有没有落点"，**不能判"落点是不是真的 UAF"**——llm01 的命中里 `dxf_free_pair` 也可能只是普通调用。要判真伪仍需 `s5f` 的站点扫描 + 证据链（对 1 个 pattern 而言成本可接受）。

---

## Q12 llm05 结论翻转的实际频次

**结论**：**查不出来**。`history.jsonl` 是在两次相反结论**之后**才加进 `s5h_feature_audit.py` 的，所以翻转本身**没有被持久化**。现存只有 `uaf-llm05` 一个 history 文件、**1 条记录**（`real 0 / false_positive 5 / unclear 0`），且其余 4 个特征没有 history 文件。

**证据**

```
=== Q12: features/*/history.jsonl ===
  --- v2/features/uaf-llm05/history.jsonl ---
    运行次数: 1
      2026-11-02T13:37:43+08:00 counts= {'real': 0, 'false_positive': 5, 'unclear': 0} sites= None
```

`ls v2/features/` → `uaf-llm01 … uaf-llm05` + `VERDICTS.json`；只有 `uaf-llm05` 目录下有 `history.jsonl`。

**卡在哪**

- 第 1 次运行（判 `->value` = real，指出 12284→12267）发生在 `history.jsonl` 逻辑加入**之前**；那次运行的产物 `cross_function_audit.json` 被第 2 次运行**整体覆盖**。
- 其他 4 个特征（llm02/03/04 的跨函数审计，llm01 的 pipeline）也在 history 逻辑加入前跑的，同样没有记录。
- `cross_function_audit.json` 里也没有时间戳或运行序号字段（只有 `feature_id` / `candidates` / `agent_verdicts` / `spent_chars`）。

**要能统计翻转，最小改动**（不在本次白名单内，仅建议）：给每次运行写 `ts` + `counts` + `sites` 到一个**不覆盖**的文件——这正是 `s5h_feature_audit.py` 现在做的事，但只对**新**运行生效。

**可佐证的旁证**：`HANDOFF/03_STAGE5_V2.md` §10.8 记录了两次运行的结论（1 real → 0 real），但那是本次会话的人工记录，不是持久化产物。`VERDICTS.json` 的 `unique_sites[0].features` 里含 `uaf-llm05`，说明当时确实有过一次 `real` 判定被采纳进合并结果。

---

# 13 白名单执行结果

## 13.1 备份

`cp mutator_custom/stage5/ARVO-42494732/source_context.json /tmp/audit/backup/source_context.json.bak` ✅

## 13.2 白名单项 1：补 V4 闭环

给 `source_context.json` 加 `testcase_path`：

```
/root/gyx/mutator_create/reproduce_crash/artifacts/by_crash_type/heap-use-after-free/
libredwg/address/ff69eeda665843f1a73f42b6ba82dad46dfde07c/ARVO-42494732/testcase
```

（256 字节，`os.path.getsize` 确认）

然后：

```
python3 s5_verify_mutator_v2.py --osv ARVO-42494732 \
    --binary /root/gyx/mutator_create/mutator_custom/stage5/ARVO-42494732/v2/experiment/llvmfuzz
```

原始输出：

```
  V1_schema      PASS             0 问题
      · documents=6/6
  V2_evidence    PASS             0 问题
      · actions=1
  V3_code        PASS             0 问题
      · clang -fsyntax-only 通过
  V4_behavior    PASS             0 问题
      · 已知 crash 回放: heap-use-after-free /src/libredwg/src/in_dxf.c:12267

  overall = pass
```

**V4：`not_applicable` → `PASS`；`overall`：`pass_with_skipped` → `pass`。**

说明：实验二进制能在**主机**直接运行（`file` 显示 ELF 64-bit x86-64；实测打印了 libFuzzer banner），所以不需要进容器跑验证脚本。

**副作用（需声明）**：`s5_verify_mutator_v2.py` 会写 `v2/verification.json`。这是白名单动作的脚本自身行为，不是我手工改的。`mtime` 对比确认**只有**两个文件变了：

```
  11-02_15:27    mutator_custom/stage5/ARVO-42494732/source_context.json
  11-02_15:27    mutator_custom/stage5/ARVO-42494732/v2/verification.json
  （其余 v2/*.json、v2/mutator.c 均为 11-01 或 11-02 13:xx，未被本次触碰）
```

## 13.3 白名单项 2：基线测试

```
$ python3 -m pytest pattern_analysis/tests/test_stage5_v2.py -q
....                                                                     [100%]
4 passed in 0.14s
```

✅ 预期 4 passed，未改动测试。

## 13.4 白名单项 3：调查脚本

全部落在 `/tmp/audit/`：

```
/tmp/audit/strip.py       剥 OBJECTS 段的脚本
/tmp/audit/seeds/         4 个剥段副本
/tmp/audit/build/         diversity.c + gen.c（供容器编译）
/tmp/audit/isobj/probe.c  is_dwg_object 探针（stdin 逐行）
/tmp/audit/q2.py q2b.py q2c.py q2d.py   Q2 的四种提取尝试
/tmp/audit/q3.py          Q3
/tmp/audit/q1011.py       Q10 + Q11
/tmp/audit/backup/        source_context.json 备份
```

## 13.5 未做的（明确禁止）

- 未删除 `s5_feature_binding.py`（等 Q6 结论 → Q6 已给：删了会让 V1 门禁 fail）
- 未删除 `run_matrix.sh`、未删 `dimensions` 字段、未删 `s5_verify` 的 V3
- 未回写 `mutator.json` 的 `compile_check` / `replay_check`
- 未修改 `mutation_plan.json`、`mutator.c`、`target_surface.json`

---

# 14 与交接文档不符之处

| # | 文档 | 文档说法 | 实测 |
|---|---|---|---|
| 1 | `HANDOFF/02` §8 耦合表 | 「改 stage3 的 `dimensions` 键名 → 必须同时检查 `s5f_feature_pipeline.py` 的 `classify()`、`s5h_feature_audit.py`」 | **假**。stage5 里 7 个维度名 **0 个真读取**（Q7）。`classify()` 读的是站点属性与函数名正则 |
| 2 | `HANDOFF/04` §8.5 / `REPS.md` 的 rep05 行 | rep05/default = 1,391 execs、密度 359.45；custom = 8,420 | **无法从现存文件复核**：rep05/default 的 `run.log` 现在是 12,178 execs；rep05/custom 的 `run.log` 没有进度行。只有 `reps/summary.json` 保留旧值（Q9） |
| 3 | `HANDOFF/01` §3.3 | 「`reproduced_crashes.jsonl`（23 字段）」 | 实际**不均匀**：23 字段 159 条、24 字段 757 条、25 字段 238 条 |
| 4 | `HANDOFF/03` §12.7 / `HANDOFF/05` §3.6 | 「V4 缺 `testcase_path`，`V4 = not_applicable`」 | **已过期**：白名单动作补上后 V4 = PASS，`overall = pass` |
| 5 | `HANDOFF/04` §8.1 | 配置 A 的 default 目标密度 5.03 /100k、exec/s 760 | 该次实验的日志**已被 `rm -rf`**，无法复核；只剩 `README.md` 的记录 |
| 6 | `HANDOFF/04` §8.2 | 配置 B 的 default 10.88 /100k、custom 6.50 | 同上，日志已删，只有 `README.md` 记录 |
| 7 | `HANDOFF/03` §10.8 / §12.6 | 记录 llm05 两次结论相反（1 real → 0 real） | 翻转**没有持久化**：`history.jsonl` 只有 1 条（0 real），且是翻转之后才加的（Q12） |
| 8 | `HANDOFF/01` §3.7 | 「`reassigned_between` 在 batch 层就是 unknown」 | **部分不符**：`interpretation` 里 121 条 UAF 有 41 条是确定的（True 25 / False 16）；stage3 的 `unknown` 是 LLM 自己写的，不是数据没有 |
| 9 | `HANDOFF/05` §1.2 / B12 | 「按有释放操作过滤 worklist 会漏 llm02/llm04」 | 成立，但**补充**：`scan_realloc_sites`（llm02 专用）在 libredwg 也是 **0 命中**，因为 10 处 realloc 全回写自身 |
| 10 | `HANDOFF/05` §1.16 / B16 | 「`PROG_RX.finditer(text, re.M)` 把 flag 当 pos」 | 成立；本次调查用同一正则（把 `re.M` 放进 `compile`）能正确解析，反证该修法有效 |
| 11 | `HANDOFF/00` §1.5 陷阱 1 | 「门禁会误拒正确代码：校验种子按字母序选到了 `Arc.dwg`」 | 成立；本次调查额外确认 `seeds/` 里 `Arc.dwg` 确实排在 `Constraints.dxf` 之前（`A`=0x41 < `C`=0x43） |
| 12 | `HANDOFF/03` §8.11 | 「权重 = (1-default)/found 数」 | 成立；`feature_bindings.json` 里**没有 weight 字段**，plan 的 0.5 完全来自 pipeline（Q6） |
| 13 | `HANDOFF/03` §14.2 | 「`run_reps.sh` 所有 run 同时启动」 | 成立；但**副作用**：`job_kill` 没杀干净串行版时，`rep05` 被后来的残留进程覆盖（Q9）——这是一个未被文档记录的运维风险 |

---

# 15 一页速查

| Q | 结论 | 关键数 |
|---|---|---|
| Q1 | 无 OBJECTS → 返回原输入，特征路径空转 | `stripped: CHANGED=0/1000`；`原种子: 500/1000` |
| Q2 | 部分成立：9/10 是目标崩溃；default 不只改值行（有插入、有拼接） | 最大输入 164,002 > 最大种子 127,870；3/10 含确定非已知 code-0 值 |
| Q3 | DWG 语料几乎全来自 `Arc.dwg` | 356/364 = 97.8% 与 `Arc.dwg` 同尺寸 173,717 |
| Q4 | **查不出来**：`sites[].code` 是守卫片段的析取，不是门控谓词 | 121 条里只有 73 条有守卫文本；positive 4 / negative 6 / other 60 / empty 48 |
| Q5 | **agent 独有且被采用的候选 = 0** | 机械路单独就有 `R1 dxf_objects_read 12284→12267`；成本 188 turns / 63,078 chars |
| Q6 | 已分叉；binding 唯一功能消费者是 V1 schema 门禁 | 删脚本 → V1 fail；不影响算子 |
| Q7 | **HANDOFF/02 §8 的耦合是假的** | stage5 里 7 个维度名 0 个真读取 |
| Q8 | 两条链；只留调用图会丢数据流链 | `cpg_dump.tsv` 4 个消费者；`dataflow_features.jsonl` → guards(41/121) / in_loop / control_structures(55/121) |
| Q9 | **不可信**；rep05 日志已被覆盖 | default 密度 63.71–359.45（5.6×）；rep05 summary 1391 vs 现存 12178 |
| Q10 | 损失大 | uaf `trigger_condition` 保留 9/37；per-sample evidence 114→0；hbo 5 pattern 只有 3 个可区分点（78% 同点） |
| Q11 | **可行且能复现 VERDICTS** | 交集：llm01 命中 2，其余 0；成本 < 1 s vs agent 125 turns |
| Q12 | **查不出来**：翻转未持久化 | 只有 llm05 有 history，1 条（0 real） |

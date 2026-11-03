# 项目架构（as-built）

> 核对日期：**2026-11-04**（R8）。本文只写**当前状态**，不做考古。
> 每个路径、行数、文件数都在当前工作树上实测过。

---

## 0 一句话

从已复现的崩溃出发 → 按崩溃类型归纳 **pattern**（stage3）→ 抽象为项目无关的 **特征**（stage4）
→ 把特征落到具体项目的**真实代码站点**（stage5）→ 生成 C 自定义 mutator → 用 A/B 对照验证。

**唯一的验收口径**：custom 臂 vs default 臂的 A/B。不是"找到新 bug"，不是"覆盖率涨了"。

---

## 1 目录与数据策略

| 目录/文件 | 进 git | 作用 |
|---|:---:|---|
| `pipeline/` | ✅ | **11 个 .py + 1 个 .sh，共 9,392 行** |
| `prompts/` | ✅ | 4 个 LLM prompt 模板 |
| `tools/` | ✅ | 8 个独立工具（清单构建、ddmin、敏感性扫描） |
| `tests/test_stage5_v2.py` | ✅ | 契约测试（4 passed） |
| `docs/` | ✅ | 规格 / 各轮报告（`docs/runs/`） |
| `artifacts/` | ✅ | stage2 产物：`facts/` `interpretation/` `reproduced_crashes.jsonl` |
| `outputs/stage3/<type>/` | ✅ | pattern（`final.json` + `batch_*.json` + `prompt/`） |
| `outputs/stage4/<type>/` | ✅ | `features.json` + **`applicability_rules.json`** |
| `projects/<OSV>/` | 部分 | 单项目工作区（六层产物 + 实验） |
| `reproduce_crash/artifacts/` | ❌ | 崩溃复现日志/样本（401 MB） |
| `cpg_files/` | ❌ | Joern CPG 图（9.2 GB，可重建） |
| `crash_testcase/` | ❌ | 按崩溃类型导出的 testcase（135 MB） |
| `**/corpus/`、`**/crash/`、`**/llvmfuzz` | ❌ | fuzz 语料、崩溃输入、二进制（可由种子+算子+seed 重放重建） |

---

## 2 五个阶段

| 阶段 | 文件 | 行数 | 输入 | 输出 | 调 LLM？ |
|---|---|---:|---|---|:---:|
| **s1** 复现 | `s1_reproduce.sh` | 31 | ARVO 镜像 | `reproduce_crash/artifacts/by_crash_type/.../<OSV>/{testcase,report.log}` | ❌ |
| **s2a** CPG 底座 | `s2_1_lib_cpg.py` | 481 | 源码 | CPG 图、Joern 查询、数据流辅助（共享库） | ❌ |
| **s2b** facts | `s2_2_facts.py` | 1,464 | report + CPG + deep 字段 | `artifacts/facts/<OSV>/facts.json` | ❌ |
| **s2c** 解释 | `s2_3_interpretation.py` | 369 | facts | `artifacts/interpretation/<OSV>/interpretation.json` | ❌ |
| **s3** pattern | `s3_extract_patterns.py` | 548 | interpretation | `outputs/stage3/<type>/final.json` + `batch_*.json` | ✅ |
| **s4** 特征 | `s4_abstract_features.py` | 467 | pattern | `outputs/stage4/<type>/{features.json, applicability_rules.json, feature_*.json}` | ✅ |

**只有 s3 / s4 / s5 调 LLM**。s1、s2a–s2c、s5_1、s5_2、s5_4、s5_6 全是确定性的。

---

## 3 stage5：4 个阶段 / 6 个文件

| 阶段 | 实现文件 | 行数 | 做什么 | 调 LLM？ |
|---|---|---:|---|:---:|
| 入口 | `s5_1_main.py` | 200 | CLI 调度 + 单步直通 | ❌ |
| **prepare** | `s5_2_prepare.py` | 872 | 5.0 抓源码/harness + 5.1 worklist | ❌ |
| **audit** | `s5_3_audit.py` | 1,306 | 5.2 agent 审计 + 5.2b 机械规则 + 5.2c 跨函数 + 5.2d 特征审计 | ✅ |
| **analyze** | `s5_4_analyze.py` | 1,900 | 5.3 证据链 + 5.4 候选 + 5.5 每特征 6 阶段 + **站点扫描** + **判据匹配** | ❌ |
| **build** | `s5_5_build.py` | 1,207 | 5.6 plan + 5.7 生成 C + 5.8 门禁 | ✅（生成 C 那步） |
| 共享底座 | `s5_6_lib.py` | 547 | 行级 CFG + 自实现 agent 循环 | ❌ |

```bash
python3 pipeline/s5_1_main.py prepare --osv X    # 5.0 + 5.1
python3 pipeline/s5_1_main.py audit   --osv X --all-chunks   # 5.2（LLM）
python3 pipeline/s5_1_main.py analyze --osv X    # 5.3 + 5.4 + 5.5
python3 pipeline/s5_1_main.py build   --osv X    # 5.6 + 5.7 + 5.8
python3 pipeline/s5_1_main.py all     --osv X    # 四步（默认跳过 audit）
```

单步直通：`fetch / worklist / surface / findings / features / plan / generate / verify / mech / interproc / feat-audit`
（`s5_1_main.py` 的 `STEP_FN`；**直通会转发完整 argv**——v7 之前只转发 `extras`，
`--depth` / `--type` / `--feature` 会被入口吃掉）。

---

## 4 六层产物与依赖顺序

都写在 `projects/<OSV>/v2/` 下，**缺一层就停**。

```
source_context.json / audit_worklist.json / cpg_dump.tsv / harness/   ← prepare
        ↓
target_surface.json         输入攻击面 + 六步证据链 + 输入分支
        ↓
candidate_findings.json     多路候选（agent + 机械规则）合并/核验/去重
        ↓
feature_pipeline.json       5 个特征各自过 6 阶段的结果（found / not_found / blocked）
        ↓
mutation_plan.json          声明式计划：sites + mutations + construct 规格
        ↓
mutator.c + mutator.json    生成的算子 + 元数据
        ↓
verification.json           V1–V4
```

**旁支产物**（不参与主链）：

| 产物 | 谁读 |
|---|---|
| `feature_bindings.json` | 只有 `s5_verify` 的 V1 schema 门禁（只校验存在与 `schema_version`） |
| `feature_matrix.json` | 无下游 |
| `applicability_rules.json` | **判据体系**（见 §5） |
| `features/<fid>/pipeline.json` | 每特征单独的结果副本 |

---

## 5 判据体系

**判据是数据，不是代码里的 if 分支。**

```
outputs/stage4/uaf/applicability_rules.json          ← stage4 自产（s4_abstract_features.py::emit_rules）
        ↓  load_applicability_rules()
s5_4_analyze.py::APPLICABILITY_RULES（模块全局）
        ↓  classify(site, feature_id) → match_rule(site, rule)
每个站点的 found / not_found
```

**词表**（只能取 `scan_sites()` / `scan_realloc_sites()` 实际算得出的量）：

| 字段 | 取值 |
|---|---|
| `use_kind` | `loop_back` / `same_path` / `cross_function` / `realloc_alias` / `any` |
| `free_kind` | `direct_free` / `realloc_self_assign` / `alias_before_realloc` / `nearby_realloc_alias` / `any` |
| `reassigned_between` | `true` / `false` / `any` |
| `is_link_read` | `true` / `false` / `any` |

**规则形态**：`{"kind":"structural", "any_of":[{合取}, …], "why":"…"}`，
或扁平单合取（`match_rule` 两种都认）。`kind="name_regex"` 是遗留形态（按函数名猜语义），
v8 之后模型给的都是 structural。

**可证伪性校验**（`s4_abstract_features.py::check_rule`）：每个合取分支至少要在**一个**字段上
是真子集；写 `any` 或把词表里所有取值都列上 = 恒真 = 拒绝。
`expressible: false` 是合法结果（模型声明"现有字段表达不了"）。

**已知漏洞**：`reassigned_between` 对现存站点**恒为 false**（`scan_sites` 构造时就过滤了重赋值），
所以写 `reassigned_between: false` 是**真空约束**，排除不了任何站点。

---

## 6 门禁

### 6.1 生成门禁（`s5_5_build.py`）

| 函数 | 检查 |
|---|---|
| `check_code()` | 静态：只用 `Data/Size/MaxSize/Seed`、无 malloc、无全局可变状态、必须有 `LLVMFuzzerMutate` 回退、MaxSize 边界、引用 plan 的段锚点/字段锚点、把原输入拷出来 |
| `check_behavior()` | 行为 **5 项**：① default 权重与 plan 一致 ② 变异空间 ≥ `min_distinct_outputs`（1000 seed 下 ≥200 distinct）③ **构造路径有效**（剥段种子上 CHANGED ≥ 400 且产出能被解析出 `0/SECTION`+`2/OBJECTS`+≥1 条 code-0）④ 格式分流 ≥95% default（非目标格式）⑤ 位置正确（首个差异不能落在组码行；构造路径下不要求 `off > OBJECTS`） |

任一不过 → **不写出 `mutator.c`**，落 `mutator_rejected.*`。

### 6.2 `s5_verify` 的 V1–V4

| 门禁 | 查什么 |
|---|---|
| `V1_schema` | 6 个文档都在且 `schema_version` 齐全 |
| `V2_evidence` | 证据行号能在源码里对上 |
| `V3_code` | `clang -fsyntax-only` 通过 |
| `V4_behavior` | 回放已知崩溃（读 `source_context.json` 的 `testcase_path`）→ 确认还是 `heap-use-after-free @ in_dxf.c:12267` |

**注意**：`testcase_path` 缺失时 V4 会**跳过回放**并仍判 pass——这是"静默降级"，已踩过一次。

---

## 7 实验设施与指标口径

`projects/<OSV>/v2/experiment/`：

| 文件 | 作用 |
|---|---|
| `build.sh` | 把 `v2/mutator.c` 编进 `llvmfuzz`（`-fsanitize=address,fuzzer`） |
| `dispatch.c` | 分发层：`LIBREDWG_MUTATOR_OFF` 控制走 default 还是 custom |
| `run_reps.sh` | n=5 配对 A/B，10 个 run 同时启动，**逐 rep 变 seed**（`-seed=$((SEED_BASE + r))`） |
| `analyze_reps.py` | 读 `run.log` + `crash/`，输出率/100k、Poisson RR + 95% CI、配对、覆盖率比 |
| `summarize.py` | 单次运行汇总 |
| `run_matrix.sh` | 权重矩阵（`rm -rf default custom` 后重建） |
| `diversity.c` / `one.c` / `bench.c` | 纯测量程序（变异空间 / 单次调用 / 耗时） |
| `gate_seeds/stripped_*.dxf` | **门禁固件**：剥掉 OBJECTS 段的种子（4 个）。不在 `seeds/` 里 |

**指标口径**：目标崩溃次数 / 100k **exec**（按执行次数，不按秒）。
default 命中 0 时**率比无定义**，只报原始计数。

**两条踩过的坑**：

1. **`-seed=1` 硬编码**（v7 修）：曾导致 5 个 rep 是同一次确定性运行的重放
   （675 个崩溃文件只有 136 个唯一 sha1）。现在逐 rep 变 seed。
2. **`rm -rf "$ROOT"`**：每次重跑先清空 `reps/`，所以**跑完必须立刻 `mv reps reps_<tag>`**，
   分析只针对快照。

---

## 8 `fault_anchor` 标记

`audit_worklist` 默认从 `LLVMFuzzerTestOneInput` 正向展开 depth≤2。
**有些项目的故障函数在这个闭包外**（gpac 实测：经函数指针分派，零调用者）。
`--fault-anchor` 会把故障函数（+ 一层邻居）**直接塞进清单**——这是**喂答案**。

标记的传播链：

```
s5_2_prepare.py:810   audit_worklist.json  _meta.fault_anchor_enabled
        ↓
s5_4_analyze.py:472   target_surface.json  validation.fault_anchor_enabled
s5_4_analyze.py:1868  feature_pipeline.json 顶层 fault_anchor_enabled
```

**`fault_anchor_enabled = true` 的含义**：这份结果的"故障函数进入待扫描清单"这一步不是流程自己做的。
引用时必须同时带上 `fault_fn_in_closure`（false = 闭包确实够不到它）。

**未接通的地方**：这个标记**没有**传到 `mutation_plan.json` / `mutator.json` / `verification.json`。

---

## 9 当前实测状态（ARVO-42494732 / libredwg）

| 项 | 值 |
|---|---|
| 六层产物 | 6/6 齐 |
| `found` | **1/5**（只有 `uaf-llm01`） |
| 站点 | `src/in_dxf.c:12284 → 12267`，`var=pair`，`branch=DXF` |
| plan | 1 site / 1 mutation / `weight 0.5` / `total 1.0` / `status=ready` |
| 算子 | 294 行，`r = Seed % 1000; if (r < 500) default; else mutate_a001`（50%） |
| 生成门禁 | 5 道全过 |
| V1–V4 | 全 **pass**，`overall = pass` |
| `pytest tests -q` | **4 passed** |
| `fault_anchor_enabled` | **False**（libredwg 不依赖锚点） |
| 路径 B A/B | `default 0 / 1,048,238 execs` vs `custom 731 / 508,682`（`reps_pathB_r3`，731 个崩溃全唯一、两两交集 0） |

**gpac（ARVO-42518828）**：`found 1/5`（`gf_odf_vvc_cfg_read_bs:1400 → 1404`，`branch=ISOM`），
但 **`fault_anchor_enabled = True`**、`fault_fn_in_closure = False`——**喂过答案的**。

---

## 10 纪律

1. 跑完任何 `run_reps.sh` **立刻** `mv reps reps_<tag>`；跑前 `ps aux | grep [l]lvmfuzz` 确认无残留。
2. 磁盘紧：**只 `mv` 不 `cp`**。
3. 不动 V1 基线（顶层 `mutator.c`、`fuzz_exp/`、`fuzz_exp2/`）。
4. 改代码后 `python3 -m pytest tests -q`（仓库根，应 4 passed）。
5. agent 自己实现，不许 shell 出去调 `claude` 之类的 CLI agent。

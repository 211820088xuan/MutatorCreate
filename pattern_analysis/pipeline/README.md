# pipeline —— 五个阶段的脚本

所有流程脚本集中在本目录。命名规则：`s<阶段号><子步>_<动作>.py`。

**路径基准**（脚本内已定义，无需设置环境变量）：

```
HERE = pattern_analysis/pipeline/
ROOT = pattern_analysis/            ← artifacts/ 、outputs/
TOP  = mutator_create/              ← reproduce_crash/ 、mutator_custom/
```

---

## 阶段总览

| 阶段 | 做什么 | 产物 |
|---|---|---|
| **s1** 漏洞复现 | 在 Docker 里把 ARVO/OSV 崩溃跑出来 | `reproduce_crash/`：崩溃报告、CPG、清单 |
| **s2** 数据抽取 | 从报告与图里抽 facts，再从 facts 派生 interpretation | `pattern_analysis/artifacts/` |
| **s3** 共性提取 | LLM 按崩溃类型聚类 → pattern | `outputs/stage3/<type>/final.json` |
| **s4** 特征抽象 | LLM 把每个 pattern 归纳成 1 个通用特征 | `outputs/stage4/<type>/features.json` |
| **s5** 算子生成 | LLM 把特征落到具体项目 → 变异算子 | `mutator_custom/stage5/<OSV>/mutator.c` |

---

## s1 漏洞复现

**本阶段的实现是一个自成一体的子项目**（有自己的 `state.json`、`artifacts/`、`binaries/` 目录树，
内部 14 个脚本互相 import），所以**不搬动**，只在此目录留一个入口：

```bash
# 入口在 reproduce_crash/
cd ../../reproduce_crash
python3 run_repro.py --projects <list> --limit <n> [--stage1-only]
```

| 脚本（在 `reproduce_crash/`） | 职责 |
|---|---|
| `run_repro.py` | 总编排：①manifest → ②build → ③repro → ④verify → ⑤walk-back → ⑥分层 |
| `build_orchestrator.py` | 构建被测二进制（HEAD 构建 / 钉版 commit 构建） |
| `arvo_repro.py`、`repro_runner.py` | 单条崩溃的复现执行 |
| `verify_tiered.py` | 分层验证（复现是否可信） |
| `manifest_builder.py`、`recover_report_logs.py` | 清单生成、报告回收 |
| `repro_common.py`、`disk_policy.py` | 公共函数、磁盘策略 |

> ⚠️ 这些脚本里的 `--stage 1` / `--stage 2` 指的是**构建阶段**（HEAD 构建 / 钉版构建），
> 与本文的流程阶段**无关**。

---

## s2 数据抽取（2 个入口 + 1 个共享库）

```bash
python3 s2a_build_facts.py           # 入口①：→ facts/<OSV>/facts.json
python3 s2b_build_interpretation.py  # 入口②：→ interpretation/
```

### `s2a_build_facts.py`（1,456 行，单文件含 5 个步骤）

| 步 | 做什么 | 产物 | 贵不贵 |
|---|---|---|---|
| 1 | 解析 ASan 报告（66 字段） | `_cache/crash_report_features.jsonl` | 便宜（纯文本） |
| 2 | CPG 数据流查询（`reachability`/`guard`/`in_loop`） | `_cache/dataflow_features.jsonl` | **贵（Joern）** |
| 3 | 三源合成 facts | `facts/<OSV>/facts.json` | 便宜 |
| 4 | CPG 深度查询（10 类代码结构字段） | `_cache/deep_fields.jsonl` | **贵（Joern）** |
| 5 | 深度字段合并进 facts（只填空缺、不覆盖） | **就地回写** `facts/<OSV>/facts.json` | 便宜 |

- 中间产物全在 **`artifacts/_cache/`**；`artifacts/` 根部只剩 **`facts/`** 与 **`interpretation/`**
- 步骤 2/4 的产物已存在时**自动跳过**；`--refresh` 强制重跑（很慢）
- `--steps 3,5` 只跑指定步骤；`--dry-run` 只看计划

### `s2b_build_interpretation.py`（369 行）

读 `facts/<OSV>/facts.json`（**步骤5 已把 `deep` 回写进去**），按崩溃类型分派到 8 个判定函数，产出
`interpretation/<OSV>/interpretation.json` + `interpretation.jsonl`。
**只对 facts 做筛选/排序/比较/判断，不产生新事实。**

### `s2_lib_cpg.py`（481 行，共享库）

`load_reproduced()` / `project_of()` / `repo_dir()` / `vuln_commit()`（定位漏洞版 commit）/
`ensure_src()` / `ensure_cpg()` / `build_script()` / `parse_out()`。
被 `s2a_build_facts.py` 与 `s5_fetch_source.py` 共用。**它自带的 `main()` 是遗留入口，当前流程不用。**

### facts 与 interpretation 的分工

| | facts | interpretation |
|---|---|---|
| 性质 | 观测值 | 对观测值的**确定性比较**结论 |
| 内容 | 分配/释放/崩溃位置、变量类型、访问宽度、控制结构 | 先后顺序、是否重赋值、是否别名、是否跨函数、越界多少 |
| 缺失标记 | `completeness` | `missing` + `confidence` |

### facts 的唯一存储（2026-10-28 修正）

**只有一个：`facts/<OSV>/facts.json`（1,139 个文件）。`facts.jsonl` 已删除。**

| 步骤 | 对 facts 做什么 |
|---|---|
| 步骤3 | 写 `facts/<OSV>/facts.json`（缩进 JSON，一崩溃一文件） |
| 步骤5 | **读全部 per-file → 合并 deep/report_extra → 就地回写 per-file** |

**三个消费者全部读同一份**：

| 消费者 | 用途 |
|---|---|
| `s3_extract_patterns.py` | 切批喂 LLM |
| `s4_abstract_features.py` | 按 `sample_ids` 取样本 |
| `s2b_build_interpretation.py` | 派生判断 |

**修复前后对比（实测）**：

| 指标 | 修复前 | 修复后 |
|---|---|---|
| `interpretation` 变化条数 | — | **358 / 1,139** |
| `reassigned_between` | `None:1138, False:1` | **`None:1098, True:25, False:16`** |
| `confidence=low` | 615 | **482** |
| `confidence=high` | 1 | **2** |

原因：修复前步骤5 只回写 `facts.jsonl`，而 interpretation 读的是 `facts/<OSV>/facts.json` ——
`deep.entity_assignments` 到不了 interpretation，`_reassign_between()` 恒为 `null`。

---

### 另一处待决定：`_cache` 比 ledger 旧

`_cache/crash_report_features.jsonl` 生成于 10-26，而 `artifacts/reproduced_crashes.jsonl` 更新于 10-27。
实测重跑步骤1 后，**约 60 个报告解析字段完全一致**，只有 4 个 ledger 派生字段变化
（`observed_crash_type` 983 条、`crash_type_norm` 141 条、`verification_tier` 16 条、`testcase_size` 1 条）。
当前保留了旧缓存，以维持 `facts` / `stage3` / `stage4` / mutator 的链条一致。

---

## s3 共性提取 → pattern

```bash
python3 s3_extract_patterns.py prepare     # 切批，生成 prompt
python3 s3_extract_patterns.py run         # 并发调 LLM
python3 s3_extract_patterns.py check       # 校验
python3 s3_extract_patterns.py merge       # 汇总批级结果
python3 s3_extract_patterns.py runmerge    # 跨批合并 → final.json
python3 s3_extract_patterns.py all         # 全跑
```

**注意：不带参数会默认执行 `prepare`**（会重写 `outputs/stage3/manifest.json`）。

输入：`artifacts/facts/<OSV>/facts.json` + `artifacts/interpretation/`
输出：`outputs/stage3/<type>/{input,prompt,batch_NNN.json,merge_input.json,final.json}`

---

## s4 特征抽象 → features.json

```bash
python3 s4_abstract_features.py --type uaf --pattern "同函数释放后访问"
python3 s4_abstract_features.py --type uaf --all
```

输入：`outputs/stage3/<type>/final.json`（1 个 pattern）+ 该 pattern 全部样本的 facts
输出：`outputs/stage4/<type>/features.json`

**约束**：每个 pattern 归纳成 **1 个**特征；输出不得含项目名/函数名/行号（脚本会做泄漏校验）。

---

## s5 算子生成 → mutator.c

```bash
python3 s5_fetch_source.py ARVO-42494732        # 5.1 读崩溃版本源码
python3 s5_generate_mutator.py --feature uaf-llm01 --osv ARVO-42494732 --type uaf
```

| 脚本 | 输入 | 输出 |
|---|---|---|
| `s5_fetch_source.py` | 记录表 + git 仓库 | `mutator_custom/stage5/<OSV>/source_context.json` + `source/<file>.c` |
| `s5_generate_mutator.py` | `outputs/stage4/<type>/features.json` + `source_context.json` | `mutator_custom/stage5/<OSV>/{mutator.json,mutator.c}` |

### 算子侧的脚本（**随具体崩溃走**，不在本目录）

它们依赖具体项目的源码与种子，所以放在 `mutator_custom/stage5/<OSV>/`：

| 脚本 | 职责 |
|---|---|
| `design/MUTATOR_CONTRACT.md` | 算子接口契约（权重、环境变量、不变量） |
| `design/landing_plan.json` | 每个特征在本项目里的落地设计 |
| `design/review.json` | 独立审查结论 |
| `stage5_verify.py` | **四级门禁**：V1 语法 / V2 结构 / V3 自举 / V4 权重 |
| `build_fuzzer.sh` | 构建带算子的 `llvmfuzz` |
| `run_one.sh` | 单次 fuzz |
| `run_all.sh` | 对比实验编排（default vs custom，交错重复） |
| `summarize.py` | 汇总实验结果 |
| `measure_strategy_cov.py` | 逐策略独立覆盖率 |
| `inspect_insert.py` | 检查每个策略把字节插到了哪里 |

完整跑法：

```bash
# 构建
docker exec libredwg-exp bash /exp/build_fuzzer.sh
# 门禁
docker exec libredwg-exp python3 /exp/stage5_verify.py \
    --mutator /exp/mutator.c --seed /exp/seeds/sample_r14.dxf \
    --binary /exp/fuzz_exp/llvmfuzz \
    --expect-file in_dxf.c --expect-line 12267 --require-hit 0
# 实验（3 轮 × 30 分钟 × 2 模式）
docker exec libredwg-exp bash /exp/run_all.sh 1800 3
# 汇总
python3 summarize.py /exp/fuzz_exp
```

---

## 已知的坑

| 现象 | 原因 |
|---|---|
| `s2b_build_interpretation.py`、`s3_extract_patterns.py` **没有 `--help`**，参数缺失时会直接执行 | 早期脚本没做 argparse 保护。好在它们是幂等的（重跑结果一致） |
| `s5_fetch_source.py` 的 `SRCDIR=/tmp/opencode/cpg_cache/src` 可能不存在 | clone 缓存目录，`/tmp` 被清后需重新 clone |
| `s5_fetch_source.py` 依赖的 `repo_local` 指向 `/tmp/opencode/src_local/...` | 同上；仓库不在了只能从 `repo_url` 重新 clone |
| 归档脚本 import 不到 `s2_lib_cpg` | 它们在 `../archived_scripts/`，库在 `pipeline/`；需 `export PYTHONPATH="$PWD/../pipeline"` |

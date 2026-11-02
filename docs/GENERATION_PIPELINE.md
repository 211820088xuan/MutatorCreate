# 生成 pipeline —— 五个阶段

所有流程脚本集中在 `pipeline/`。命名规则：`s<阶段号><子步>_<动作>.py`。

规格的当前实现见 `pipeline/README.md` 的文件索引；实验流程见 `EXPERIMENT_PIPELINE.md`。

**路径基准**（脚本内已定义，无需设置环境变量）：

```
HERE = pipeline/
ROOT = mutator_create/           ← artifacts/ outputs/ projects/ cpg_files/
TOP  = /root/gyx                  （仅跨出 mutator_create 时用）
```

---

## 阶段总览

| 阶段 | 做什么 | 产物 |
|---|---|---|
| **s1** 漏洞复现 | 在 Docker 里把 ARVO/OSV 崩溃跑出来 | `reproduce_crash/`：崩溃报告、CPG、清单 |
| **s2** 数据抽取 | 从报告与图里抽 facts，再从 facts 派生 interpretation | `artifacts/` |
| **s3** 共性提取 | LLM 按崩溃类型聚类 → pattern | `outputs/stage3/<type>/final.json` |
| **s4** 特征抽象 | LLM 把每个 pattern 归纳成 1 个通用特征 | `outputs/stage4/<type>/features.json` |
| **s5** 算子生成 | LLM 把特征落到具体项目 → 变异算子 | `projects/<OSV>/mutator.c` |

---

## s1 漏洞复现（只从 ARVO）

**唯一数据源是 ARVO**：`docker pull n132/arvo:<localId>-vul` → 抠 `/tmp/poc`、`/out`、`/src`
→ 跑一遍确认崩溃 → 解析 `crash_type` 与栈帧 → 建 CPG → 落盘。

```bash
bash pipeline/s1_reproduce.sh --limit 20 --jobs 4
```

`pipeline/s1_reproduce.sh` 只是一层「切目录 + 转发」，真正实现在
`reproduce_crash/arvo_repro.py`（该子项目自带 `artifacts/`、`binaries/` 目录树，
路径全部基于 `__file__`，所以不搬进 `pipeline/`）。

产物与既有结构同构：

```
artifacts/by_crash_type/<type>/<project>/<san>/<commit>/<id>/
  ├── testcase     输入
  ├── report.log   崩溃输出
  ├── INFO.txt     元数据
  └── replay.sh    重放脚本
artifacts/logs/reproduce/<id>.log
reproduce_crash/repro_dataset.jsonl     追加一行（同 schema）
```

**已移除的路径**：原来还有一条「从 OSS-Fuzz 源码在 HEAD / 钉版 commit 上构建，再跑 testcase」
的复现路径（`run_repro.py`、`build_orchestrator.py`、`repro_runner.py`、`manifest_builder.py`、
`repro_common.py`、`verify_tiered.py`、`disk_policy.py`、`preflight/` 等 13 个脚本 + 28 个自测文件）。
2026-11-02 起不再纳入 stage1；需要时从 commit `f31ba99e` 取回。它已产出的 239 条 OSS-Fuzz
复现结果仍在 `artifacts/reproduced_crashes.jsonl` 里，交付过程记录见
`docs/history/DELIVERY_OSSFUZZ.md`。

> ⚠️ 旧脚本里的 `--stage 1` / `--stage 2` 指的是**构建阶段**（HEAD 构建 / 钉版构建），
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

## s5 算子生成 → mutator.c（V2，当前版本）

V2 与 V1 的根本差别：**先把"哪个特征落在哪个真实站点"用证据链冻结成 plan，再让模型只做翻译**。
没有证据就输出 `blocked`，不生成代码。

```bash
python3 pipeline/s5.py prepare --osv ARVO-42494732
python3 pipeline/s5.py audit   --osv ARVO-42494732 --all-chunks
python3 pipeline/s5.py analyze --osv ARVO-42494732
python3 pipeline/s5.py build   --osv ARVO-42494732
python3 pipeline/s5.py all     --osv ARVO-42494732          # 四步连跑
```

9 个子步收成 **4 个阶段**，底层脚本不变、仍可单独调用：

| 阶段 | 子步 | 底层脚本 | 输出（都在 `projects/<OSV>/v2/`） |
|---|---|---|---|
| `prepare` | 5.0 | `s5_fetch_source.py` | `source_context.json`、`source/`、`harness/`、`seeds/` |
| | 5.1 | `s5a_scan_target.py` | `audit_worklist.json`、`cpg_dump.tsv`（0 LLM） |
| `audit` | 5.2 | `s5b_audit_agent.py` | `audit_chunks/*.json`、`audit_logs/*.jsonl` |
| `analyze` | 5.3 | `s5_target_surface.py` | `target_surface.json`（0 LLM） |
| | 5.4 | `s5_candidate_findings.py` | `candidate_findings.json`（0 LLM） |
| | 5.5 | `s5f_feature_pipeline.py` | `feature_pipeline.json`（0 LLM） |
| `build` | 5.6 | `s5_mutation_plan.py` | `mutation_plan.json`（0 LLM） |
| | 5.7 | `s5_generate_mutator_v2.py` | `mutator.c` + `mutator.json` |
| | 5.8 | `s5_verify_mutator_v2.py` | `verification.json` |

`all` 默认**不跑 audit**（LLM、较贵、可离线补）；加 `--with-audit` 才包含。

### 5.5 的六阶段固定流程（每个特征一视同仁）

```
① 短名单（按该特征的机制挑候选函数）
② 站点扫描（释放类调用 → 后续读同一变量）
③ 机制归类（能否支持该机制？归不上就是 not_applicable / not_found）
④ 六步证据链（harness → 输入绑定 → 解析 → 字段 → 判据分支 → 释放后使用）
⑤ 输入分支判定（DXF / DWG / JSON——决定算子写文本级还是二进制级）
⑥ 动作规格（字段 + 操作 + 保持的不变量 + 证据等级）
```

### 权重

`default` 固定 50%；其余 50% **平分给真正找到落点的特征**。
5 个特征只找到 1 个时，就是 `default 50% + 该特征 50%`。
找不到落点的特征一律 `not_found`，**不分配权重**，也不会用"通用字段类别"顶替。

### 门禁（V1–V4）

| 层 | 检查 |
|---|---|
| V1 schema | 六层产物齐全、commit 一致、`blocked` 不得继续 |
| V2 evidence | 证据行号合法且原文匹配、每个 action 有 `basis_refs` |
| V3 code | C11 语法、接口签名、`MaxSize` 边界、拷出原输入 |
| V4 behavior | 编译并**实跑**算子、diff 它实际改的记录、实测 default 权重 |

### 已归档的 V1 脚本

`s5_feature_binding.py`（被 `s5f_feature_pipeline.py` 取代）与
`s5_generate_mutator.py`（被 `s5_generate_mutator_v2.py` 取代）已移到
`/root/gyx/_archive_mutator_create/20261102/scripts/`。

---

## 已知的坑

| 现象 | 原因 |
|---|---|
| `s2b_build_interpretation.py`、`s3_extract_patterns.py` **没有 `--help`**，参数缺失时会直接执行 | 早期脚本没做 argparse 保护。好在它们是幂等的（重跑结果一致） |
| `s5_fetch_source.py` 的 `SRCDIR=/tmp/opencode/cpg_cache/src` 可能不存在 | clone 缓存目录，`/tmp` 被清后需重新 clone |
| `s5_fetch_source.py` 依赖的 `repo_local` 指向 `/tmp/opencode/src_local/...` | 同上；仓库不在了只能从 `repo_url` 重新 clone |
| 归档脚本 import 不到 `s2_lib_cpg` | 归档脚本在 `_archive_mutator_create/`；需要时 `export PYTHONPATH=/root/gyx/mutator_create/pipeline` |

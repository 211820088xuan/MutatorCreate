# MutatorCreate —— 错误型激发的模糊测试增强（mutator 生成）

从已复现的崩溃出发，归纳同类型崩溃的共性特征，再把特征落到具体项目的**真实站点**上，
生成能提高目标崩溃触发概率的自定义 mutator。

## 目录

```
mutator_create/
├── docs/                    文档
│   ├── GENERATION_PIPELINE.md   生成 pipeline 规格（s1–s5 全流程）
│   ├── EXPERIMENT_PIPELINE.md   实验 pipeline 规格（A/B 对照的要求与口径）
│   ├── DESIGN_V2.md             V2 设计文档（数据契约、门禁、任务分解）
│   ├── ACCEPTANCE.md            验收标准
│   ├── ANALYSIS_REPORT.md       漏洞分析总报告
│   ├── INVESTIGATION.md         mutator_create 调查记录（2026-11-02）
│   ├── ARCHITECTURE.md          **as-built 架构：当前布局 / 门禁 / 现状（先读这份）**
│   └── libfuzzer_custom_mutator_survey.md
├── pipeline/                生成 mutator 的代码（11 个 .py + 1 个 .sh）
├── tests/                   V2 契约与负例测试
├── artifacts/               stage2 产物：facts / interpretation
├── outputs/                 stage3/4 产物：pattern / features
├── prompts/                 LLM prompt 模板
├── projects/<OSV>/          单项目工作区（六层产物 + 实验结果）
├── manifests/               ARVO 复现状态清单（6,138 条）
├── reproduce_crash/         崩溃复现（只从 ARVO，`arvo_repro.py`）
├── tools/                   通用工具
├── cpg_files/               Joern CPG 图（不进 git，9.2 GB）
├── crash_testcase/          按崩溃类型导出的 testcase（不进 git，135 MB）
└── data/                    原始数据集缓存（不进 git）
```

## 两个 pipeline

### 1. 生成 pipeline（`docs/GENERATION_PIPELINE.md` + `pipeline/`）

```
s1 复现崩溃 → s2 facts/解释 → s3 pattern → s4 特征 → s5 落地成 mutator
```

**s1 只从 ARVO 复现**（`docker pull n132/arvo:<id>-vul` → 抠 poc/out/src → 验证崩溃）。
原先那条「从 OSS-Fuzz 源码构建再跑 testcase」的路径已于 2026-11-02 移除，
其已产出的 239 条结果仍在 `artifacts/reproduced_crashes.jsonl` 中。

stage5 有 9 个子步，收成 **4 个阶段**（`prepare` / `audit` / `analyze` / `build`，外加 `all`），
实现是 **6 个文件**（`s5_1_main.py` 入口 + 4 个阶段各一个 + `s5_6_lib.py` 共享底座）。
六层产物、层层有门禁：

```
target_surface → candidate_findings → feature_pipeline
→ mutation_plan → mutator.c → verification
```

**每个特征都走同一套 6 阶段固定流程**（短名单 → 站点扫描 → 机制归类 → 六步证据链 →
输入分支判定 → 动作规格）。找不到落点就写 `not_found`，**不分配权重**，
不会用"通用字段类别"顶替。

### 2. 实验 pipeline（`docs/EXPERIMENT_PIPELINE.md`）

同一二进制、`LIBREDWG_MUTATOR_OFF` 切换，两臂对照，记录
`execs / exec_s / cov / ft / corpus / 唯一崩溃点 / 目标触发密度`。
参考实现在 `projects/<OSV>/v2/experiment/`。

## 权重

`default` 固定 **50%**；其余 50% **平分给真正找到落点的特征**。
5 个特征只找到 1 个时就是 `default 50% + 该特征 50%`。

## 单项目结果（ARVO-42494732 / libredwg / heap-use-after-free）

5 个 UAF 特征走同一套流程后：

| 特征 | 状态 | 站点 |
|---|---|---|
| uaf-llm01 同函数释放后访问 | **found** | `src/in_dxf.c:12284 → 12267` |
| uaf-llm02..05 | not_applicable（预筛交集为 0） | 见 `projects/ARVO-42494732/v2/feature_pipeline.json` |

**数字的现状（2026-11-02 实测修正）**：本节原先引用的 **1.33×（CI [0.64, 2.76]）已作废**——
三配置都是单次运行，配置 A/B 的日志已被 `rm -rf` 删除无法复算，同一 default 配置的密度波动达 5.6 倍。
`v2/experiment/REPS.md` 的 **0.954（CI [0.61, 1.48]）同样作废**（含一次 `exec/s` 塌陷的损坏运行）。

**另一个必须知道的口径问题**：`run_reps.sh` 原本对所有 run 硬编码 `-seed=1`，导致 5 个 rep
不是独立样本 —— 实测各组崩溃文件跨 rep 重复 10–539 个（`reps_pathB` 的 675 个崩溃文件只有
136 个唯一 sha1）。现已改为逐 rep 变 seed；目前**只有 `reps_pathB_r2` 是真正独立的**
（646 个崩溃文件 646 个唯一 sha1，两两交集全 0）。

完整清单见 `docs/ARCHITECTURE.md` §8。

## 数据策略

| 进 git | 不进 git（体积大或可重建） |
|---|---|
| 全部脚本、文档、测试 | `cpg_files/`（9.2 GB，Joern 重建） |
| facts / interpretation / pattern / features | `data/`（原始数据集缓存） |
| 单项目六层产物（JSON） | `reproduce_crash/artifacts/`（日志/样本，401 MB） |
| 实验的 run.log / summary / 索引 | `crash_testcase/`（135 MB testcase） |
| ARVO 复现清单 | fuzz 语料与 `crash/` 崩溃输入（可重放重建） |

## 快速开始

```bash
python3 -m pytest tests -q                                  # 契约测试

bash pipeline/s1_reproduce.sh --limit 20 --jobs 4           # s1（ARVO）
python3 pipeline/s2_2_facts.py                         # s2
python3 pipeline/s3_extract_patterns.py                     # s3
python3 pipeline/s4_abstract_features.py                    # s4
python3 pipeline/s5_1_main.py prepare --osv ARVO-42494732   # 5.0 抓源码 + 5.1 worklist
python3 pipeline/s5_1_main.py audit   --osv ARVO-42494732 --all-chunks  # 5.2 agent 审计（可选）
python3 pipeline/s5_1_main.py analyze --osv ARVO-42494732   # 5.3 证据链 + 5.4 候选 + 5.5 特征
python3 pipeline/s5_1_main.py build   --osv ARVO-42494732   # 5.6 plan + 5.7 生成 + 5.8 门禁
# 或者一条命令跑完全部（默认跳过 audit）
python3 pipeline/s5_1_main.py all     --osv ARVO-42494732

python3 tools/build_arvo_manifest.py                        # 重建 ARVO 清单
```

## 历史

整理前的结构里 `pattern_analysis/` 与 `mutator_custom/` 是两棵独立目录树，
已于 2026-11-02 合并为 `pipeline/` + `artifacts/` + `outputs/` + `projects/`；
stage5 也从 14 个文件按 4 个阶段拆成 6 个文件（最后一次提交 `1dbc6c45`）。
旧路径仍留在 `.gitignore` 里（`pattern_analysis/`、`mutator_custom/`），
仓库里**没有** `_archive_mutator_create/` 目录。

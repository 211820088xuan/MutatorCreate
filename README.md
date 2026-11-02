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
│   ├── INVESTIGATION.md         mutator_create 调查记录
│   └── libfuzzer_custom_mutator_survey.md
├── pipeline/                生成 mutator 的代码（22 个脚本 + 2 个库）
├── tests/                   V2 契约与负例测试
├── artifacts/               stage2 产物：facts / interpretation
├── outputs/                 stage3/4 产物：pattern / features
├── prompts/                 LLM prompt 模板
├── projects/<OSV>/          单项目工作区（六层产物 + 实验结果）
├── manifests/               ARVO 复现状态清单（6,138 条）
├── reproduce_crash/         崩溃复现子项目（代码 + 索引）
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

stage5 是核心，六层产物、层层有门禁：

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
| uaf-llm02..05 | not_found / not_applicable | 见 `projects/ARVO-42494732/v2/feature_pipeline.json` |

对照实验：目标触发密度 **1.33×**（95% CI [0.64, 2.76]，单次运行不显著），
覆盖率 99.9%。详见 `projects/ARVO-42494732/v2/experiment/README.md`。

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

python3 pipeline/s5_fetch_source.py  --osv ARVO-42494732    # 5.0
python3 pipeline/s5a_scan_target.py  --osv ARVO-42494732    # 5.1
python3 pipeline/s5_target_surface.py --osv ARVO-42494732   # 5.3
python3 pipeline/s5_candidate_findings.py --osv ARVO-42494732  # 5.4
python3 pipeline/s5f_feature_pipeline.py --osv ARVO-42494732 --all  # 5.5
python3 pipeline/s5_mutation_plan.py --osv ARVO-42494732    # 5.6
python3 pipeline/s5_generate_mutator_v2.py --osv ARVO-42494732  # 5.7
python3 pipeline/s5_verify_mutator_v2.py --osv ARVO-42494732    # 5.8

python3 tools/build_arvo_manifest.py                        # 重建 ARVO 清单
```

## 历史

整理前的结构里 `pattern_analysis/` 与 `mutator_custom/` 是两棵独立目录树，
已于 2026-11-02 合并为 `pipeline/` + `artifacts/` + `outputs/` + `projects/`。
被淘汰的文档与脚本移到了 `_archive_mutator_create/20261102/`（未删除）。

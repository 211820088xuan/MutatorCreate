# pipeline —— 生成 mutator 的完整流程

- **规格说明**：`../docs/GENERATION_PIPELINE.md`
- **实验规格**：`../docs/EXPERIMENT_PIPELINE.md`

路径基准（脚本内已定义，无需设环境变量）：

```
HERE = mutator_create/pipeline/
ROOT = mutator_create/     ← artifacts/ outputs/ projects/ cpg_files/ reproduce_crash/
```

## 文件索引

| 阶段 | 脚本 | 作用 |
|---|---|---|
| 1 | `s1_reproduce.sh` | 用 ARVO 镜像复现崩溃（实现主体在 `../reproduce_crash/`） |
| 2 | `s2_lib_cpg.py` | Joern CPG 建图/查询与数据流辅助 |
| 2 | `s2a_build_facts.py` | 报告 + CPG + 深度字段 → `artifacts/facts/<OSV>/facts.json` |
| 2 | `s2b_build_interpretation.py` | facts → 确定性解释 |
| 3 | `s3_extract_patterns.py` | 解释 → 按崩溃类型归纳 pattern（LLM） |
| 4 | `s4_abstract_features.py` | pattern → 项目无关特征 → `outputs/stage4/<type>/features.json` |
| **5** | **`s5.py`** | **stage5 统一入口：4 个阶段 / 9 个子步**（见下） |
| 辅助 | `s5c_mech_hypotheses.py` | 机械规则找"释放→使用"形态（可选离线自检） |
| 辅助 | `s5g_interproc.py`, `s5h_feature_audit.py` | 跨函数视野（补 llm04/llm05） |
| 库 | `agent_runtime.py`, `cfg_lib.py` | 自实现 agent 循环；行级 CFG |

## stage5 的 4 个阶段（`s5.py`）

```bash
python3 s5.py prepare --osv ARVO-42494732     # 5.0 抓源码 + 5.1 worklist
python3 s5.py audit   --osv ARVO-42494732 --all-chunks   # 5.2 agent 审计（LLM，可选）
python3 s5.py analyze --osv ARVO-42494732    # 5.3 证据链 + 5.4 候选 + 5.5 每特征 6 阶段
python3 s5.py build   --osv ARVO-42494732    # 5.6 plan + 5.7 生成 C + 5.8 V1–V4 门禁
python3 s5.py all     --osv ARVO-42494732    # 上面四步（默认跳过 audit，加 --with-audit 才跑）
python3 s5.py list                            # 看阶段与底层脚本的对应
```

| 阶段 | 子步 | 底层脚本 | 做什么 |
|---|---|---|---|
| `prepare` | 5.0 | `s5_fetch_source.py` | 固定版本源码 + harness + 种子 |
| | 5.1 | `s5a_scan_target.py` | 调用图 depth≤2 → `audit_worklist.json` |
| `audit` | 5.2 | `s5b_audit_agent.py` | 每批一个 agent 静态审计（带 `flow`） |
| `analyze` | 5.3 | `s5_target_surface.py` | 输入攻击面 + 六步证据链 |
| | 5.4 | `s5_candidate_findings.py` | 多路候选合并 / 核验 / 去重 |
| | 5.5 | `s5f_feature_pipeline.py` | 每个特征走同一套 6 阶段 |
| `build` | 5.6 | `s5_mutation_plan.py` | 声明式 plan（权重在这里定） |
| | 5.7 | `s5_generate_mutator_v2.py` | 从 ready plan 生成 C（含行为门禁） |
| | 5.8 | `s5_verify_mutator_v2.py` | V1–V4 门禁 |

底层脚本**没有合并**：仍可单独调用（`python3 s5a_scan_target.py --osv ...`），
`s5.py` 只做顺序驱动，某一步失败立刻停下。

## 产物链

```
target_surface.json → candidate_findings.json → feature_pipeline.json
→ mutation_plan.json → mutator.c + mutator.json → verification.json
```

都写在 `projects/<OSV>/v2/` 下。

# MutatorCreate —— 错误型激发的模糊测试增强（mutator 生成）

从已复现的崩溃出发，归纳同类型崩溃的共性特征，再把特征落到具体项目的真实站点上，
生成**能提高目标崩溃触发概率**的自定义 mutator。

## 四阶段

```
stage1  复现崩溃      reproduce_crash/            1,154 条已复现崩溃
stage2  facts + 解释   pattern_analysis/pipeline/s2a_build_facts.py
                      pattern_analysis/pipeline/s2b_build_interpretation.py
stage3  LLM → pattern  pattern_analysis/pipeline/s3_extract_patterns.py
stage4  pattern → 特征 pattern_analysis/pipeline/s4_abstract_features.py
stage5  特征 → mutator pattern_analysis/pipeline/s5*.py
```

## stage5 的固定流程（每个特征都走同一套）

```
① 短名单      按该特征的机制，从 fuzz target 的调用图里挑候选函数
② 站点扫描    扫「释放类调用 → 后续读同一变量」原语
③ 机制归类    站点能否支持该机制？归不上就是 not_found
④ 六步证据链  harness → 输入绑定 → 解析 → 字段 → 判据分支 → 释放后使用
⑤ 输入分支    DXF / DWG / JSON（决定算子写文本级还是二进制级）
⑥ 动作规格    字段 + 操作 + 保持的不变量 + 证据等级 + 权重
```

**找不到落点就写 `not_found`，权重还给 default**——不用通用算子占预算。

产物链：

```
target_surface.json → candidate_findings.json → feature_pipeline.json
→ mutation_plan.json → mutator.c → verification.json
```

## 权重

`default` 占 50%，其余 50% **平分给真正找到落点的特征**。
如果 5 个特征只有 1 个找到，那就是 `default 50% + 该特征 50%`。

## 目录

| 目录 | 内容 |
|---|---|
| `pattern_analysis/pipeline/` | 全部脚本（s1–s5、特征管线、生成器、门禁） |
| `pattern_analysis/tests/` | V2 契约与负例测试 |
| `pattern_analysis/outputs/stage3,4/` | pattern 与特征 JSON |
| `mutator_custom/stage5/<OSV>/v2/` | 单个项目的六层产物与实验结果 |
| `docs/` | 设计文档与实施计划 |

## 不进仓库的大数据

`cpg_files/`（9.2 GB CPG 图）、`reproduce_crash/artifacts/`（401 MB 日志/样本）、
fuzz 语料与二进制——见 `.gitignore`。

## 复现

```bash
pip install -r requirements.txt          # 若存在
python3 -m pytest pattern_analysis/tests -q
python3 pattern_analysis/pipeline/s5f_feature_pipeline.py --osv <OSV> --all
python3 pattern_analysis/pipeline/s5_mutation_plan.py --osv <OSV>
python3 pattern_analysis/pipeline/s5_generate_mutator_v2.py --osv <OSV>
python3 pattern_analysis/pipeline/s5_verify_mutator_v2.py --osv <OSV>
```

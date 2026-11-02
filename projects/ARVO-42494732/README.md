# ARVO-42494732 —— 单项目工作区

**目标崩溃**：libredwg / `heap-use-after-free` / `src/in_dxf.c:12267`（`dxf_objects_read`）。

本目录是「把通用特征落到这个项目的真实站点，生成算子，再跑 A/B 对照」的完整工作区。
**整个目录挂载到容器的 `/exp`**（`docker run -v <此目录>:/exp`）。

---

## 目录地图

### 当前（V2）产物

| 路径 | 是什么 | 谁产出 |
|---|---|---|
| `source_context.json` | 固定版本、故障函数、fuzz target 等上下文 | `s5_1_main.py prepare` |
| `source/` | 故障函数所在文件全文（`in_dxf.c`） | `s5_1_main.py prepare` |
| `harness/` | fuzz target 源码：`llvmfuzz.c`（入口）+ `dwgfuzz.c` | `s5_1_main.py prepare` |
| `seeds/` | 8 个真实种子：6 个 DXF + 2 个 DWG（`AC` 开头才走二进制分支） | `s5_1_main.py prepare` |
| `cpg_dump.tsv` | CPG 的方法表 + 调用边（22 MB，`s5a` 从 CPG 导出，**必需**） | `s5_1_main.py worklist` |
| `audit_worklist.json` | 调用图 depth ≤2 的函数清单（162 个 / 162 批） | `s5_1_main.py worklist` |
| `audit_chunks/`、`audit_logs/` | agent 审计的分批结果与完整 transcript | `s5_3_audit.py audit` |
| `vuln_report.json` | 审计合并结果（`audit_chunks/` 缺失时的回退输入） | `s5_3_audit.py audit` |
| `mech_hypotheses.json` | 机械规则找到的「释放 → 使用」形态 | `s5_3_audit.py mech` |
| **`v2/`** | **六层产物 + 实验结果**（见下） | `s5_1_main.py analyze` … `s5_1_main.py build` |

### `v2/` 里的六层产物

```
target_surface.json     输入攻击面 + 六步证据链
candidate_findings.json 多路候选合并/核验/去重
feature_pipeline.json   5 个 UAF 特征各自过 6 阶段的结果
mutation_plan.json      声明式计划（default 0.5 + found 特征平分 0.5）
mutator.c / mutator.json 生成的算子 + 元数据
verification.json       V1 schema / V2 evidence / V3 code / V4 behavior
experiment/             A/B 对照的结果（crash/、replay/、run.log、README.md）
features/               每个特征单独的 pipeline.json
```

### V1 基线（保留作对照，不再维护）

| 路径 | 是什么 |
|---|---|
| `mutator.c` | V1 算子：5 个策略 + 60% default（被 `v2/mutator.c` 取代） |
| `fuzz_exp/`、`fuzz_exp2/` | V1 的 fuzz 结果（corpus 已清理，保留 `crash/`、`replay/`、`run.log`、索引） |
| `run_all.sh`、`run_one.sh`、`summarize.py`、`replay.py`、`dedup_crashes.py`、`compare_cov.py`、`robust_stats.py`、`timeline.py`、`measure_strategy_cov.py`、`inspect_insert.py`、`mutator_verify.py`、`stage5_verify.py`、`build_fuzzer.sh` | V1 的实验编排与门禁 |
| `REPLAY.md` | V1 的两套重放机制说明 |

二进制（`llvmfuzz`）、原始 corpus、`design/`、`v2_snapshot_r1/` 已清理；
脚本本身在 git 里，需要时 `git checkout` 取回。

---

## 运行环境

实验需要一个已构建好 libredwg 的容器，本目录挂到 `/exp`：

```bash
docker run -d --name libredwg-exp -w /src \
  -v /root/gyx/mutator_create/projects/ARVO-42494732:/exp \
  libredwg-exp:with-libredwg-20261102 sleep infinity
```

镜像里有 `/src/libredwg/src/.libs/libredwg.a`（154 MB）+ clang 12。
（2026-11-02 目录改名后重建过一次容器；旧容器保留为 `libredwg-exp-old`。）

## 跑法

```bash
# 生成链（在 mutator_create/ 下）—— 4 个阶段
python3 pipeline/s5_1_main.py prepare --osv ARVO-42494732
python3 pipeline/s5_1_main.py audit   --osv ARVO-42494732 --all-chunks   # 可选
python3 pipeline/s5_1_main.py analyze --osv ARVO-42494732
python3 pipeline/s5_1_main.py build   --osv ARVO-42494732
```

```bash
# 实验（容器内）
docker exec libredwg-exp bash /exp/v2/experiment/build.sh
docker exec libredwg-exp bash /exp/v2/experiment/run_matrix.sh 180
docker exec libredwg-exp python3 /exp/v2/experiment/summarize.py \
    /exp/v2/experiment --binary /exp/v2/experiment/llvmfuzz
```

---

## 结论（截至 2026-11-02）

| 特征 | 状态 | 站点 |
|---|---|---|
| uaf-llm01 同函数释放后访问 | **found** | `src/in_dxf.c:12284 → 12267` |
| uaf-llm02 缓冲区释放后旧指针 | not_found | 8 处 realloc 全部回写同一变量 |
| uaf-llm03 清理析构后悬垂访问 | not_found | 包装函数只释放成员 |
| uaf-llm04/05 跨函数 / 容器 | not_applicable | 行级扫描器建不了跨函数关系 |

对照实验：目标触发密度 **1.33×**（95% CI [0.64, 2.76]，单次运行不显著），覆盖率 99.9%。
详见 `v2/experiment/README.md`。

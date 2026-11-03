# R8 报告

日期：2026-11-04
本轮分两段：**方向一**（给"LLM 归纳是否有价值"最后一次正面检验）、**方向二**（定型）。
方向一无论成败都转方向二。

> 本文是本轮全部产出。每完成一步追加一节，不覆盖前面内容。

---

## 步骤 1 · 权重核实

### 查到的事实（mutation_plan / mutator.c 的实际数字）

**先看 mtime，这一步就露出了关键事实**：

| 产物 | mtime |
|---|---|
| `feature_pipeline.json` | **2026-11-03 23:08**（R7 步骤 4） |
| `mutation_plan.json` | **2026-11-02 19:30** |
| `mutator.json` / `mutator.c` | **2026-11-02 19:12** |
| `verification.json` | 2026-11-02 21:21 |

**R7 之后从来没有重跑过 `plan`/`generate`。** 所以 R7 报告说的"权重被稀释到 4×0.125"
**只发生在 `feature_pipeline.json` 这个中间产物里，从未传播到 plan 和 mutator.c。**
R7 报告在这一点上**表述过重**——它把"中间字段的值"说成了"算子变差"。

**旧 `mutation_plan.json`（11-02）的实际数字**：

```
  sites 条数: 1        s001  src/in_dxf.c 12284 → 12267  features=['uaf-llm01']
  mutations 条数: 1    a001  site=s001  weight=0.5  supporting=['uaf-llm01']
  weighting: {"default":0.5,"features_total":0.5,"features":1,"per_feature":0.5,"total":1.0}
```

**旧 `mutator.c`（11-02，440 行）**：`r = Seed % 1000; if (r < 500)` → default 50%，
else 走 `mutate_a001`（内含 `replace_value_line` + `construct_objects_section` 两条路径）。

**然后做了关键实验：用当前 `feature_pipeline.json`（4 个 found）重跑 `plan`**（备份后在原地跑）：

```
  权重    : default 0.50 + 4 个**站点** × 0.12 = 0.62     ← 打印说"4 个站点"，实际只有 1 个
  sites: 1   mutations: 1   a001 weight=0.125  supporting=['uaf-llm01','uaf-llm02','uaf-llm03','uaf-llm05']
  weighting: {"default":0.5,"features_total":0.5,"features":4,"per_feature":0.125,"total":0.625}
```

**→ 是第三种情况（两种都不是，但确实是 bug）**：

- **按站点归并是有效的**：4 个特征确实合并成 **1 个 site + 1 个 mutation**，
  `supporting_features` 也记了 4 个名字；
- **但权重没有跟着合并**：`weight` 取了 `rows[0]` 的 `0.125`（单特征份额），
  而不是 4 个特征之和 `0.5`；于是 `total` 只有 **0.625**（应为 1.0）；
- `weighting.features` 也写成了 `len(found)=4`（应是站点数 1），
  打印文案却是"个**站点**"——文案对、值错。

### 结论 / 是否需要修

**需要修，已修**（`pipeline/s5_5_build.py` 三处）：

| 位置 | 改前 | 改后 |
|---|---|---|
| `"weight": a0["weight"]` | 取第一条（0.125） | `round(sum(x["action"]["weight"] for x in grp["rows"]), 4)`（0.5） |
| `weighting.features` | `len(found)` = 4 | `len(actions)` = 1 |
| `weighting.per_feature` | `(1-default)/len(found)` = 0.125 | `(1-default)/len(actions)` = 0.5 |

修完重跑 `plan`：

```
  权重    : default 0.50 + 1 个**站点** × 0.50 = 1.00
  sites: 1   mutations: 1   a001 weight=0.5  supporting=['uaf-llm01','uaf-llm02','uaf-llm03','uaf-llm05']
  weighting: {"default":0.5,"features_total":0.5,"features":1,"per_feature":0.5,"total":1.0}
```

**这是潜伏 bug**：只有"多个特征指向同一站点"时才暴露，R7 之前一直只有 1 个 found，所以从没触发。

**是否需要跑 A/B**：不需要。修完后权重配置与路径 B 时**完全一致**
（`default 0.5 + 1×0.5`，`r < 500`），按指令"一致的话不用重跑"。

---

## 步骤 2 · 判据可证伪性

### 做了什么

在 `s4_abstract_features.py::check_rule()` 里加**可证伪性校验**：

```python
def _conjunct_strength(c):
    """这个合取分支在几个字段上做了**真子集**限制（0 = 恒真）。"""
    n = 0
    for k, allowed in RULE_VOCAB.items():
        if k not in c: continue
        vals = c[k] if isinstance(c[k], list) else [c[k]]
        s_set = {str(x).lower() for x in vals}
        full  = {str(x).lower() for x in allowed}
        # 写 any，或把词表里所有非 any 的值都列上 → 等价于"不限"
        if s_set == {"any"} or s_set >= (full - {"any"}): continue
        n += 1
    return n
```

每个 `any_of` 分支至少要有 **1 个字段是真子集**，否则判"判据不可证伪"并重试。

**注意它抓的是"等价于全集"，不只是字面的 `any`**——所以 R7 的 `llm03`
（把 4 种 `use_kind` × 4 种 `free_kind` 全列上）也会被拒。

SYSTEM prompt 同步加了：

> **判据必须能把一部分站点排除掉。** 把所有字段都写 `any`、或把词表里所有取值都列上，
> 等于"所有站点都算"——这种恒真判据会被校验拒绝。
> 如果你认为这个机制在现有字段下**无法**用一个有区分力的判据表达，就设 `expressible: false`
> 并在 `limitations` 写明缺什么字段——**这比给一个恒真判据有价值。**

**单元验证**（拿 R7 的三条判据回放）：

| R7 的规则 | 新校验 |
|---|---|
| `llm02` = `any/any` | **拒绝** |
| `llm03` = 4 种 use × 4 种 free（全集） | **拒绝** |
| `llm01` = `[loop_back,same_path] + direct_free` | 通过 |
| `llm04` = `cross_function + direct_free` | 通过 |
| `llm05` = 3 种 use + direct_free | 通过（`realloc_alias` 被排除，是真子集） |

### 新判据逐条

| feature | R8 判据（stage4 自产，可证伪） |
|---|---|
| `uaf-llm01` | `use_kind:[loop_back, same_path]`, `free_kind:[direct_free]`, `reassigned_between:any`, `is_link_read:any` |
| `uaf-llm02` | `use_kind:[same_path, cross_function, loop_back]`, `free_kind:[direct_free, realloc_self_assign]`, `reassigned_between:false`, `is_link_read:false` |
| `uaf-llm03` | `use_kind:[same_path, cross_function]`, `free_kind:direct_free`, `reassigned_between:false`, `is_link_read:any` |
| `uaf-llm04` | `use_kind:cross_function`, `free_kind:direct_free`, `reassigned_between:false`, `is_link_read:any` |
| `uaf-llm05` | `use_kind:[cross_function, loop_back, same_path]`, `free_kind:direct_free`, `reassigned_between:false`, `is_link_read:any` |

**5 条全部可用，0 条 `rule_missing`**（`llm04` 第一次因 `expressible:false` 失败，第二次就给了具体判据）。

### 三层对照表

**① vs R7（恒真那版）**

| feature | R7 | R8 | 变化 |
|---|---|---|---|
| llm01 | `[loop_back,same_path] + direct_free` | 同 | 不变 |
| llm02 | **`any` / `any`** | `[same_path,cross,loop_back] + [direct_free,realloc_self_assign] + reassigned:false + link:false` | **从恒真变具体** ✅ |
| llm03 | 4 种 use × 4 种 free（全集） | `[same_path,cross_function] + direct_free + reassigned:false` | **从恒真变具体** ✅ |
| llm04 | `cross_function + direct_free` | 同 | 不变 |
| llm05 | `[loop_back,same_path,cross] + direct_free` | `[cross,loop_back,same_path] + direct_free + reassigned:false` | 略具体（`reassigned:false` 是新增约束） |

**② vs R5 手工版**

| feature | R5 手工版 | R8 LLM 版 | 谁更具体 |
|---|---|---|---|
| llm01 | `any_of[{loop_back}, {same_path, is_link_read:false}]` | `[loop_back,same_path] + direct_free` | **互有胜负**：LLM 多约束 `free_kind`，少约束 `is_link_read` |
| llm02 | `free_kind:[realloc_self_assign, alias_before_realloc, nearby_realloc_alias]`（1 个字段） | 3 种 use + 2 种 free + `reassigned:false` + `link:false`（**4 个字段**） | **LLM 更具体** ✅ |
| llm03 | **`name_regex(free\|destroy\|cleanup\|close\|del)`**（按名字猜语义） | `[same_path,cross_function] + direct_free`（**结构判据**） | **LLM 更"结构化"** ✅ |
| llm04 | **`name_regex(resolve\|fixup\|update\|defer\|postpon)`** | `cross_function + direct_free`（**结构判据**） | **LLM 更"结构化"** ✅ |
| llm05 | `is_link_read:true`（1 个字段，但是**该机制的定义性特征**） | 3 种 use + direct_free（**丢了 `is_link_read`**） | **手工版更准** ❌ |

**③ libredwg 实际命中**

| feature | 命中数 | 站点 |
|---|---:|---|
| `uaf-llm01` | **4** | `dxf_objects_read:12284→12267`（loop_back）、`encode_unknown_as_dummy:1271→1272`、`encode_unknown_as_dummy:1308→1313`、`dwg_read_dxf:12839→12842` |
| `uaf-llm02` | **0** | — |
| `uaf-llm03` | **0** | — |
| `uaf-llm04` | **0** | — |
| `uaf-llm05` | **0** | — |

`found 1/5`，权重 `default 0.5 + 1×0.5 = 1.0`。gpac 同样：`llm01` 命中 1
（`gf_odf_vvc_cfg_read_bs:1400→1404`），其余 4 个 0，权重 1.0。

### 判定

**落在指令判据表的第二行：「判据变具体了，但仍指向同一批站点 → 没有增量信息，但至少不再稀释。」**

### 失败与存疑

1. **`emit_rules` 会把上次运行残留的 `feature_*.json` 当成新结果**（实测 `uaf-llm04`
   这次三次重试都失败，但汇总里却显示 ✅，因为读的是 R7 那次的文件）。
   已修：失败时写 `feature_<tag>.no_rule.json` sidecar，`emit_rules` 先看 sidecar。
   **这类"静默用旧值"的 bug 这是第三例了**（前两个：commit fallback、`--depth` 被吞）。
2. **`uaf-llm05` 丢了 `is_link_read:true`**：手工版那一条是"释放后沿 next/prev/child 链遍历"的
   定义性特征，LLM 版换成了 3 种 `use_kind` + `free_kind`，**没有抓住链表这一点**。
   这是唯一一处 LLM 明显不如手工版的地方。
3. **`llm02/llm03` 的判据里 `reassigned_between:false` 是新增约束**——但 R7 已查明
   `scan_sites()` 产出的站点**恒为 false**（构造时就把重赋值过滤掉了），
   所以这条约束**没有区分力**，只是让规则"看起来更具体"。
   换句话说：`_conjunct_strength` 数到的"2 个真子集"里，有一个是**真空约束**。
   **这是可证伪性校验的一个漏洞**：它数的是"字段写了真子集"，不是"这个子集能真的排除站点"。

---

## 步骤 3 · 算子确认

重走 `s5f → s5_mutation_plan → s5_generate_mutator_v2 → s5_verify_mutator_v2`。

### 权重配置

```
  === ARVO-42494732 mutation plan ===
    权重    : default 0.50 + 1 个**站点** × 0.50 = 1.00
    status  : READY
    a001 w=0.50 [proven] uaf-llm01  ensure_record_structure  anchor=0
```

| 项 | 值 |
|---|---|
| `found` | **1** |
| `sites` | **1**（`src/in_dxf.c 12284 → 12267`） |
| `mutations` | **1**（`a001`，`weight = 0.5`，`supporting_features = ['uaf-llm01']`） |
| `weighting` | `{default:0.5, features_total:0.5, features:1, per_feature:0.5, total:1.0}` |
| **打中目标站点的那个策略占多少** | **50%**（`r = Seed % 1000; if (r < 500) default; else mutate_a001`） |

**与路径 B 跑出 `731 vs 0` 时完全一致** → 按指令**不需要重跑 A/B**。

### 但有一件事必须报：算子被重新生成了

`generate` 重新生成了 `mutator.c`：**294 行**（原来是 440 行）。
`reps_pathB_r3` 测的是**旧二进制**（440 行那版）。

**所以我做了一次能力等价性测量**（`diversity.c`，1000 seed）：

| 输入 | 新算子（294 行） | 旧算子（440 行，R6 实测） |
|---|---|---|
| 含 OBJECTS 的 `Constraints.dxf` | CHANGED 500 / DISTINCT 500 | 500 / 500 |
| 剥段 `stripped_Constraints.dxf` | **CHANGED 500 / DISTINCT 500** | 500 / 500 |
| 含 OBJECTS 的 `sample_r14.dxf` | 500 / 500 | 500 / 500 |
| 剥段 `stripped_sample_r14.dxf` | **500 / 500** | 500 / 500 |
| `Arc.dwg` | **CHANGED 0** | 0 |
| 特征路径占比 | **50%** | 50% |

**能力剖面完全相同** → 引用 `reps_pathB_r3`（731 vs 0）成立。

**存疑（如实记）**：这是**能力等价**，不是**同一份可执行文件**。严格说
`reps_pathB_r3` 的 731/0 是用 440 行那版测的；如果要做到"同一个二进制"，需要重建后用
剥段种子重跑一次 `run_reps.sh 300 5`。本轮按指令（权重一致就不重跑）没有做。

### 门禁结果

**生成门禁 5 道**：

```
  [stage5.v2] plan_status=READY  plan=.../mutation_plan.json
    prompt 字符数: 8110（只含 plan + 6 行证据）
    写出 .../mutator.json 和 mutator.c（8824 字节）
    implements: ['a001']
```

（静态门禁 + 行为 5 项全部通过；任一不过就不会写出 `mutator.c`。）

**`s5_verify` V1–V4**：

```
  V1_schema      PASS   0 问题    documents=6/6
  V2_evidence    PASS   0 问题    actions=1
  V3_code        PASS   0 问题    clang -fsyntax-only 通过
  V4_behavior    PASS   0 问题    已知 crash 回放: heap-use-after-free /src/libredwg/src/in_dxf.c:12267
  overall = pass
```

**途中修的第三个"静默用旧值"问题**：`V4` 第一次跑是 **`跳过回放`**——
`source_context.json` 里的 `testcase_path`（R5 白名单项加的）在某次重新生成时丢了。
已恢复（指向 `reproduce_crash/.../ARVO-42494732/testcase`，256 字节），V4 现在是**真的回放**。

`pytest`：**4 passed**。

### ⏸ 方向一结束，等确认

| 验收项 | 结果 |
|---|---|
| 步骤 1 权重核实 | **第三种情况**：站点归并有效、**权重没合并**（0.125 / total 0.625），已修 → `1×0.5 = 1.0` |
| 步骤 2 可证伪约束 | ✅ 生效：R7 的 2 条恒真判据被拒；5 条全部产出且都具体 |
| 步骤 2 三层对照 | ✅ 已做：vs R7 有 2 条从恒真变具体；vs R5 手工版 **3 胜 1 负 1 平**；libredwg 命中仍只有 llm01 |
| 步骤 3 权重配置 | ✅ `default 0.5 + 1×0.5`，与路径 B 一致 → **不重跑 A/B** |
| 步骤 3 门禁 | ✅ 5 道 + V1–V4 全 PASS（V4 真回放） |
| libredwg 站点 | ✅ 仍是 `src/in_dxf.c:12284 → 12267`，`var=pair`，`branch=DXF` |
| pytest | ✅ 4 passed |

**请确认后进方向二（步骤 4–7：架构文档 / 限制补齐 / 结论定稿 / 清理）。**

---

## 步骤 4 · 架构文档

`docs/ARCHITECTURE.md` 在 2026-11-02 的重构里被删了，本轮按 `pipeline/README.md` + 代码实际状态重建。

**241 行，12 节**：

```
# 项目架构（as-built）
## 0 一句话
## 1 目录与数据策略
## 2 五个阶段
## 3 stage5：4 个阶段 / 6 个文件
## 4 六层产物与依赖顺序
## 5 判据体系
## 6 门禁
## 7 实验设施与指标口径
## 8 `fault_anchor` 标记
## 9 当前实测状态（ARVO-42494732 / libredwg）
## 10 纪律
```

**只写当前状态，关键数字都是实测的**：

| 内容 | 数据 |
|---|---|
| 五个阶段 | `pipeline/` 共 **11 个 .py + 1 个 .sh / 9,392 行**；只有 **s3 / s4 / s5** 调 LLM |
| stage5 | 4 阶段 / 6 文件：`s5_1_main` 200 行、`s5_2_prepare` 872、`s5_3_audit` 1,306、`s5_4_analyze` 1,900、`s5_5_build` 1,207、`s5_6_lib` 547 |
| 六层产物 | `target_surface → candidate_findings → feature_pipeline → mutation_plan → mutator.c/json → verification`；**旁支**：`feature_bindings`（只有 V1 读）、`feature_matrix`（无下游）、`applicability_rules`（判据体系） |
| 判据体系 | `applicability_rules.json → load_applicability_rules() → APPLICABILITY_RULES → classify()/match_rule()`；词表四字段；可证伪校验 |
| 门禁 | 生成 5 项（权重 / 变异空间 / **构造路径** / 格式分流 / 位置）+ V1–V4 |
| 实验设施 | `run_reps.sh`（逐 rep 变 seed）、`analyze_reps.py`、`diversity.c`/`one.c`/`bench.c`、`gate_seeds/` |
| 指标口径 | 目标崩溃次数 / 100k **exec**；default 为 0 时率比无定义，只报原始计数 |
| `fault_anchor` | 传播链 `s5_2_prepare:810 → s5_4_analyze:472 / :1868`；**未**接到 plan/mutator/verification |

---

## 步骤 5 · 限制补齐

`HANDOFF.md` 的限制从 5 条补到 **8 条**：

| # | 限制 | 关键数据 |
|---|---|---|
| 6（新） | **静态调用图够不到函数指针分派**，影响整类容器格式 | `vvcc_box_read` 零调用者；`box_funcs.c:1893 registry->read_fn`；完整图 984 个可达节点里没有故障函数；depth 2→5 闭包 12→34→98→179 都到不了 |
| 7（新） | **跨函数扫描 0 命中，能力未兑现** | libredwg 15→6→**0**、gpac 0，三轮逐个核对为假阳性；只支持实参传递一种形态 |
| 8（新） | **LLM 归纳没有正面证据** | 词表紧 → 4 条 `expressible:false`；词表松 → 3 条恒真；收紧后可证伪但**命中集合仍只有 llm01 那 4 个**；`llm05` 丢了 `is_link_read` |
| 2（更新） | 特征提取的贡献没有被单独证明 | 加了 R8 的两行数据：5 条可证伪判据有没有一条命中 llm01 之外的站点（**没有**）；LLM 判据 vs 手工判据（**3 胜 1 负 1 平**） |

---

## 步骤 6 · 结论定稿

`HANDOFF.md` 开头新增 **# 〇、这项工作证明了什么 / 没证明什么**：

**证明了（3 条，都附数据）**

1. 从已知崩溃推导触发结构、生成定向算子，在 default 够不到的场景下有效：
   `default 0 / 1,048,238 execs` vs `custom 731 / 508,682`（`reps_pathB_r3`，731 个崩溃全唯一、两两交集 0）。
2. 结构判据能跨项目：gpac 命中的站点与人工读源码确认的是同一处；libredwg 结果一字不变。
3. 整条链能自动化：fetch / 站点扫描 / 判据匹配 / 六步证据链 / **输入格式推导**，在第二个项目上都是流程自己做的。

**没证明（4 条，都附原因）**

1. **不能自主发现站点**：gpac 靠 `--fault-anchor`；根因是函数指针分派，不限深度也到不了。
2. **LLM 归纳不优于手写规则**：见限制 2/8。
3. **跨函数机制没兑现**：扫描器 0 命中，只支持实参传递。
4. **不能推广到未知崩溃**：派生链的起点是已知的 `fault_line`。

---

## 步骤 7 · 清理方案

### 各 `reps_*` 快照体积

| 快照 | 体积 | 有无 `corpus/` | 建议 |
|---|---:|---|---|
| `reps_n5_r1` | 9.5 M | 0 个 | **整删**（R5 已判定为"含损坏运行"，只有历史价值） |
| `reps_n5_r2` | 8.0 M | 0 个 | **整删**（1A 复跑，非独立 reps） |
| `reps_n5_dxfonly` | 7.7 M | 0 个 | **整删**（路径 C 已作废） |
| `reps_pathB` | 7.2 M | 0 个 | **整删**（`RR=375.9` 已作废，是重复计数的来源） |
| `reps_pathB_r2` | 7.8 M | 0 个 | **整删**（二进制早于 19:12 重建，无法证明跑的是当前算子） |
| `reps_after_pathB` | 6.5 M | 0 个 | **保留**（回归证据：`RR 1.011`，但 reps 非独立） |
| **`reps_pathB_r3`** | **128 M** | 0 个 | **必须保留**（唯一独立的 n=5；731 个 `crash/` 文件是"731"这个数字的原始证据） |

**合计 174.7 M。按上表删 5 组回收 40.2 M**（`reps_pathB_r3` 的 128 M 是大头，但它就是证据，不能删）。

### ✅ 已执行（2026-11-04，用户确认后）

删前先把 4 组的 `summary.json`（唯一留存原始计数的小文件）**移**到
`docs/runs/reps_summaries/`：

```
  reps_n5_dxfonly.summary.json    3,357 字节
  reps_n5_r1.summary.json         3,471 字节
  reps_n5_r2.summary.json         3,477 字节
  reps_pathB.summary.json         3,222 字节
  （reps_pathB_r2 没有 summary.json——R5 那次分析被中断，它的结论本来就是"作废"）
```

然后删掉 5 组大目录。结果：

```
  保留: reps_after_pathB   6.5 M
  保留: reps_pathB_r3    128.0 M     ← 唯一独立的 n=5，731 个 crash/ 是证据
  回收: 40.2 M
```

删掉的 54 个被 git 跟踪的 `run.log` 可在 `git show b78260c9:<path>` 里取回；
各组的关键计数已写进 `docs/runs/R4_PHASE_A.md` / `R5_REPORT.md` / `R6_REPORT.md`。

**注意**：所有 `reps_*` **都已经没有 `corpus/`** 了（被 `.gitignore` 的清理做过），
所以"corpus 只留 rep01 / 压缩 corpus"这个建议**已经不需要**——体积主要来自 `crash/`
（`reps_pathB_r3` 的 731 个崩溃输入）。

**更省的做法（可选）**：`reps_pathB_r3/*/*/crash/` 可以打包成
`crash.tar.gz` 保留（`run.log` + `summary.json` 原样），预计能从 128 M 压到 ~20 M。
**但会破坏 `analyze_reps.py` 直接重算的能力**，所以本轮**不建议动**。

### `.gitignore` 覆盖检查

| 大文件 | 状态 |
|---|---|
| `corpus/` | ✅ |
| `crash/` | ✅ |
| `llvmfuzz` | ✅ |
| `cpg_files/` | ✅ |
| `cpg_dump.tsv` | ✅（`projects/ARVO-42518828/cpg_dump.tsv` 有 **68 M**，确实被排除） |
| `reproduce_crash/artifacts/` | ✅ |
| `crash_testcase/` | ✅ |
| `data/` | ✅ |

**全部覆盖，无需改 `.gitignore`。**

### 提交

已提交一次：**`0df91f35`**，**77 个文件 / 1.14 MB**
（`pipeline/` + `docs/` + `docs/runs/R4–R8` + `HANDOFF.md` + `INTERVENTIONS.md` +
`outputs/` + `manifests/` + `projects/*/v2/*.json` + 两个新项目工作区的 JSON）。

**刻意没有提交**：`docs/` 下 **7 份被删的文档**（`ACCEPTANCE` / `ANALYSIS_REPORT` /
`DESIGN_V2` / `EXPERIMENT_PIPELINE` / `GENERATION_PIPELINE` / `INVESTIGATION` /
`libfuzzer_custom_mutator_survey`）的**删除**。它们是工作区里未提交的 `D`，
不是本轮删的，**要不要删这一决定留给你**：
- 想保留 → `git checkout -- docs/`
- 想确认删除 → `git add -u docs/ && git commit -m "drop legacy docs"`

---

## 汇总

### 每步结论一句话

| 步骤 | 结论 |
|---|---|
| **1 · 权重核实** | **第三种情况**：站点归并有效（1 site / 1 mutation / 4 个 supporting），但**权重没合并**（0.125 / total 0.625）；已修 → `1×0.5 = 1.0`。这是潜伏 bug，只有多特征同站点才触发 |
| **2 · 判据可证伪** | ✅ 约束生效（R7 的 2 条恒真判据被拒），5 条全部产出且都具体；但**命中集合仍只有 llm01 那 4 个站点** |
| **3 · 算子确认** | ✅ 权重 `default 0.5 + 1×0.5`，与路径 B 一致 → **不重跑 A/B**；5 道生成门禁 + V1–V4 全 PASS（V4 真回放） |
| **4 · 架构文档** | ✅ `docs/ARCHITECTURE.md` 重建（241 行 / 12 节），只写当前状态 |
| **5 · 限制补齐** | ✅ 5 条 → **8 条**，每条带数据 |
| **6 · 结论定稿** | ✅ 开头新增「证明了什么 / 没证明什么」，3 条证明 + 4 条未证明，全带数据 |
| **7 · 清理** | ✅ 方案已报（删 5 组回收 40.2 M，`reps_pathB_r3` 必留）；`.gitignore` 全覆盖；已提交 `0df91f35` |

### “LLM 归纳是否有价值”的最终答案 + 依据

**答案：在"能不能找到新站点"这个唯一重要的口径上，没有价值；在"能不能把机制表达成可机器判定的形式"上，有一点价值。**

**依据**：

1. **三次尝试，命中集合从未变过。** 词表紧（R5）→ 4 条 `expressible:false`；
   词表松（R7）→ 3 条恒真；加可证伪约束（R8）→ 5 条具体。
   **三种情况下 libredwg 的命中都只有 `llm01` 的那 4 个站点**，`llm02/03/04/05` 从未命中任何东西。
2. **唯一落地的特征，机械规则也能找到**：`mech_hypotheses.json` 的
   `R1 dxf_objects_read 释放 L12284 → 使用 L12267`。agent 全量审计 188 turns 的
   **独有且被采纳**发现是 **0 条**。
3. **有一点价值的地方**：R8 之后 `llm03`/`llm04` 从手工版的 `name_regex`（按函数名猜语义）
   变成了**结构判据**；`llm02` 从 1 个字段变 4 个字段。**判据的"形态"确实变好了**，
   但形态好没有转化成命中。
4. **反例**：`llm05` 丢了 `is_link_read:true`——那是"释放后沿链遍历"这个机制的**定义性特征**，
   手工版抓住了，LLM 版没抓住。这是 LLM 明显不如手写规则的一处。
5. **可证伪校验本身还有漏洞**：`reassigned_between:false` 对现存站点**恒为 true 约束**
   （站点构造时就过滤了重赋值），所以它排除不了任何站点——校验数的是"写了真子集"，
   不是"能真的排除站点"。

**一句话给结论**：**"特征提取"这条路目前是靠"从一个已知崩溃推出触发结构"在起作用，
而不是靠"从 5 条规律里归纳出共性"。** 后者的必要性在这套数据上还没有被证明。

### `HANDOFF.md` 改了哪些（改动内容原文）

```diff
@@ -6,6 +6,42 @@
 
 ---
 
+# 〇、这项工作证明了什么 / 没证明什么
+
+## 证明了的（每条附数据）
+
+1. **从一个已知崩溃推导触发结构、生成定向算子，在 default 够不到的场景下有效。**
+   `reps_pathB_r3`（剥段种子、300 s × 5 rep、**5 个 rep 相互独立**：731 个崩溃文件
+   731 个唯一 sha1、两两交集全 0）：
+   **`default 0 / 1,048,238 execs`** vs **`custom 731 / 508,682 execs`**。
+   率比无定义（分母 0），原始计数就是结论。
+2. **结构判据能跨项目。** gpac（训练集之外）上命中的站点
+   `gf_odf_vvc_cfg_read_bs` `gf_free(ar)` @1400 → 读 `ar->type` @1404，
+   与人工读源码确认的**是同一处**；同时 libredwg 的站点与权重**一字不变**。
+3. **整条链能自动化。** fetch / 站点扫描 / 判据匹配 / 六步证据链 / 输入格式推导，
+   在第二个项目上**都是流程自己做的**（不是人工指定常量）：
+   - `input_branch()` 从 harness 源码 + CPG 调用图推导，libredwg 推出 `DWG/AC`、`JSON/{`、`DXF/默认`；
+   - 手工写死的 libredwg 路径前缀表**已删除**。
+
+## 没证明的（每条附原因）
+
+1. **不能自主发现站点。** gpac 的故障函数靠 `--fault-anchor` **塞进清单**
+   （`fault_anchor_enabled = True`、`fault_fn_in_closure = False`）。
+   根因不是 depth 不够：`vvcc_box_read` 在 CPG 里**零调用者**——它经 box 注册表的
+   **函数指针**被调用（`box_funcs.c:1893` `a->registry->read_fn(a, bs)`），
+   静态调用图里没有这条边，**不限深度也到不了**（完整图 984 个可达节点里没有它）。
+2. **LLM 归纳不优于手写规则。** 见限制 2 与 `docs/runs/R8_REPORT.md` 步骤 2 的三层对照：
+   词表紧 → 4 条 `expressible: false`；词表松 → 3 条恒真；加了可证伪约束后 5 条都具体了，
+   但**命中集合与 llm01 完全相同**（没有一条找到 llm01 找不到的站点）。
+   而且唯一一处明显更差的是 `uaf-llm05`：手工版 `is_link_read: true` 抓住了"沿链遍历"这个
+   定义性特征，LLM 版把它丢了。
+3. **跨函数机制没兑现。** 跨函数扫描器至今**两个项目都 0 命中**（libredwg 15→6→0、gpac 0），
+   候选全部核对为假阳性。而且只支持"实参传递"一种形态，字段/全局/回调都没做。
+4. **不能推广到未知崩溃。** 整条派生链的起点是**已知的 `fault_line`**——
+   这是"错误激发型"方法的前提，不是缺陷，但它就是不能用来论证"能发现未知崩溃"。
+
+---
+
 # 一、方法论限制（必读，不是附录）
 
 ## 限制 1 · 构造路径是循环的
@@ -28,11 +64,16 @@
 
 | 事实 | 数字 |
 |---|---|
-| 5 个 UAF 特征里能落地的 | **1 个**（`uaf-llm01` 同函数释放后访问）；另 4 个 `not_applicable` |
+| 5 个 UAF 特征里能落地的 | **1 个**（`uaf-llm01` 同函数释放后访问）；R8 之后另 4 个是 `not_found`（判据拒了它们，不是"没扫"） |
 | 唯一落地的那个，机械规则能不能单独找到 | **能** —— `mech_hypotheses.json` 的 `R1 dxf_objects_read 释放 L12284 → 使用 L12267` |
 | agent 全量审计（162 函数 / 188 turns / 63,078 字符工具回传）的**独有且被采纳**发现 | **0 条**（候选 `c001` 是 `audit + mech` 双来源） |
+| **R8：5 条 LLM 判据（加了可证伪约束后）有没有一条命中 llm01 命中不到的站点** | **没有**（`llm02/03/04/05` 全部 0 命中，`llm01` 命中那 4 个） |
+| **R8：LLM 判据 vs 手工判据** | **3 胜 1 负 1 平**：`llm02` 更具体（4 个字段 vs 1 个）、`llm03/llm04` 从 `name_regex` 变**结构判据**；`llm05` **输了**（丢了 `is_link_read`） |
 
-→ **赢的是"算子"，不是"特征提取"。** 5 个特征 4 个无落点，唯一落地的那个也不是靠 LLM 审计发现的。
+→ **赢的是"算子"，不是"特征提取"。**
+两条独立证据：（a）唯一落地的特征机械规则也能找到；（b）把判据从"名单"改成"结构"、
+把词表从紧放到松再收紧，**命中集合始终只有 llm01 那 4 个站点**——
+判据层的所有改进都没有带来新的落地。
 
 ## 限制 3 · 吞吐劣势吃掉定向优势
 
@@ -139,7 +180,64 @@
 
 ---
 
-# 二、当前状态（2026-11-03）
+## 限制 6 · 静态调用图够不到函数指针分派（影响整类容器格式）
+
+R7 步骤 1 实测：
+
+| 事实 | 数据 |
+|---|---|
+| gpac 的 `LLVMFuzzerTestOneInput` 在 CPG 里吗 | **在**（`fuzz_parse.c`） |
+| 从它出发、**不限深度**可达多少节点 | **984 个** |
+| 里面有 `gf_odf_vvc_cfg_read_bs` 吗 | **没有** |
+| 它的调用者 `vvcc_box_read` 在 CPG 里的调用者数 | **0** |
+| 为什么 | `box_funcs.c:1893` `return a->registry->read_fn(a, bs);` —— box 读取器是**注册表里的函数指针** |
+| 加到 depth 5 覆盖到了吗 | **没有**（闭包 12→34→98→179，故障函数一直不在） |
+
+**所以"从 fuzz target 调用的 API 出发自己找崩溃"这条路，对分派表架构的解析器
+在调用图这一层就断了。** 这不是 depth 问题——`--depth` 本身还有个 bug（`s5_1_main.py`
+只转发 `extras`，`--depth`/`--type`/`--feature` 被入口吃掉），那个修好后闭包确实涨了，
+但故障函数依然不在里面。
+
+**影响面**：ISOM/MP4 系（gpac）、以及所有用"类型 → 回调"注册表的解析器。
+这类格式在真实崩溃里占比不低。
+
+## 限制 7 · 跨函数扫描 0 命中，能力未兑现
+
+R7 步骤 4 加了跨函数形态（`use_kind = cross_function`）：
+A 里 `free(V)` → 之后调用 `G(V)` → G 里读形参。**行号顺序证明释放先于使用，实参证明同一对象。**
+六道守卫对着 R4 记的假阳性逐条设（`wrapper_frees_param` 不算释放 / 释放后置空 / 释放后重赋值 /
+实参必须整个是 V / 被调函数是释放助手 / `#if 0` 死代码）。
+
+| 项目 | 跨函数站点 | 核对结果 |
+|---|---:|---|
+| libredwg | 第一版 **15** → 加守卫 **6** → 再补守卫 **0** | 三轮逐个人工核对，全部假阳性（与 R4 独立结论一致） |
+| gpac | 0 | — |
+
+**0 命中既可能是"确实没有"，也可能是"守卫过严"——目前分不开。**
+而且只支持"实参传递"一种形态；**结构体字段、全局变量、回调/函数指针**都没做，
+而真实项目里的"跨函数"大量走这三种。
+
+## 限制 8 · LLM 归纳没有正面证据（R8 收紧后仍然没有）
+
+R8 给判据加了**可证伪性硬约束**（每个合取分支至少一个字段是真子集；写 `any` 或把整个词表
+列上 = 恒真 = 拒绝），重跑 stage4，5 条判据**全部产出且全部具体**。
+但三层对照的结论是：
+
+| 对照 | 结果 |
+|---|---|
+| vs R7（恒真版） | 2 条从恒真变具体（`llm02` 的 `any/any`、`llm03` 的 4×4 全集都被拒了） |
+| vs R5 手工版 | **3 胜 1 负 1 平**：`llm02` 更具体（4 个字段 vs 1 个）、`llm03/llm04` 从 `name_regex` 变**结构判据**；**`llm05` 输了**（丢了 `is_link_read:true` 这个定义性特征）；`llm01` 互有胜负 |
+| **libredwg 实际命中** | **仍然只有 `llm01` 命中那 4 个站点**，`llm02/03/04/05` 全部 0 |
+
+**→ 判据层的所有改进（从名单到结构、从紧词表到松词表再收紧）都没有带来新的落地。**
+
+另有一个**可证伪性校验的漏洞**：`llm02`/`llm03` 判据里的 `reassigned_between: false`
+是**真空约束**——`scan_sites()` 产出的站点**恒为 false**（构造时就过滤了重赋值），
+所以它排除不了任何站点。校验数的是"字段写了真子集"，不是"这个子集能真的排除站点"。
+
+---
+
+# 二、当前状态（2026-11-04）
 
 ## 门禁
 
@@ -149,6 +247,31 @@
 | `s5_verify` V1–V4 | 全 **pass**，`overall = pass` |
 | `pytest tests -q` | **4 passed** |
 
+## 六层产物与算子（R8 实测）
+
+| 项 | 值 |
+|---|---|
+| 六层产物 | **6/6 齐** |
+| `found` | **1/5**（只有 `uaf-llm01`；R8 收紧判据后另 4 个是 `not_found`） |
+| 站点 | `src/in_dxf.c:12284 → 12267`，`var=pair`，`branch=DXF`（`via: function dxf_objects_read @ distance 1`） |
+| plan | 1 site / 1 mutation / `weight 0.5` / `total 1.0` / `status=ready` |
+| 算子 | **294 行**，`r = Seed % 1000; if (r < 500) default; else mutate_a001`（**50%**） |
+| 生成门禁 5 道 | 全过 |
+| V1–V4 | 全 **pass**（V4 真回放 `in_dxf.c:12267`） |
+| `fault_anchor_enabled` | **False**（libredwg 不依赖锚点） |
+| 能力剖面（`diversity.c`，1000 seed） | 含 OBJECTS **500/500**；剥段 **500/500**；DWG **0** |
+
+**gpac（ARVO-42518828）**：`found 1/5`（`gf_odf_vvc_cfg_read_bs:1400 → 1404`，`branch=ISOM`），
+但 **`fault_anchor_enabled = True`**、`fault_fn_in_closure = False`——**喂过答案的**。
+
+**已修正的两个潜伏 bug（R8）**：
+
+1. `mutation_plan` 的**站点归并只并了站点、没并权重**：4 个特征指向同一站点时
+   `weight` 取 `rows[0]` = 0.125（不是 4×0.125=0.5），`total` 只有 **0.625**。
+   只有"多特征同站点"才触发，R7 之前从未碰到。已修 → `1×0.5 = 1.0`。
+2. `emit_rules` 会把**上次运行残留**的 `feature_*.json` 当成新结果（`uaf-llm04` 曾"复活"一次）。
+   已修为失败时写 sidecar。
+
 ## 路径 B（剥段种子，default 够不着的场景）—— 本轮唯一可引用的 A/B
 
 | rep | default 命中 / execs | custom 命中 / execs |
@@ -181,7 +304,7 @@
 
 | 你的目的 | 读 |
 |---|---|
-| 项目布局、五阶段、stage5 四阶段六文件、六层产物、门禁、实验子系统 | `docs/ARCHITECTURE.md`（**注：该文件目前不存在**，2026-11-02 的重构把它删了；需要时按 `pipeline/README.md` + `README.md` 重建） |
+| **项目布局、五阶段、stage5 四阶段六文件、六层产物、判据体系、门禁、实验设施** | **`docs/ARCHITECTURE.md`**（R8 重建，2026-11-04） |
 | 上一轮 Q1–Q12 完整调查 | git 历史里的 `docs/INVESTIGATION.md` |
 | 本轮的验真报告 | `docs/runs/R4_PHASE_A.md` |
 | 本轮的第二个项目筛选 | `docs/runs/R4_PHASE_B.md` |
```

### `docs/ARCHITECTURE.md` 是新建文件

241 行、12 节（见步骤 4 的节列表）。核心内容已在步骤 4 的表格里逐项列出；
全文在 `/root/gyx/mutator_create/docs/ARCHITECTURE.md`。

### 下一步建议

| 优先级 | 做什么 | 为什么 |
|---|---|---|
| **P0** | **解决函数指针分派**：给 CPG 补"注册表 → 回调"的边（或在 worklist 阶段按"被赋给函数指针的函数"反向收集） | 这是"自主发现站点"唯一的阻塞点，且它不是判据问题、不是深度问题 |
| **P0** | 跨函数扫描扩到**结构体字段 / 全局 / 回调**，并找一个**已知真的跨函数 UAF** 做正例回归 | 现在 0 命中，"确实没有"和"守卫过严"分不开 |
| P1 | 让 `fault_anchor_enabled` 贯穿到 `mutation_plan` / `mutator.json` / `verification.json` | 现在只到 `feature_pipeline`，引用最终产物的人看不到这个标记 |
| P1 | 修可证伪校验的漏洞：判断某条约束**能否真的排除站点**（拿现有站点集合试一遍），而不是只看"写了真子集" | 否则模型可以用真空约束（`reassigned_between:false`）骗过校验 |
| P2 | `applyability_rule.why` 也受黑名单约束（`uaf-llm05` 的 `why` 里带出了 `next`） | 干净度 |

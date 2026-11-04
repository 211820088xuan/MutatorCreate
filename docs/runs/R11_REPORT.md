# R11 报告

日期：2026-11-04
本轮两件事：**让 `features.json` 可由 stage3 重新生成**（步骤 1–2）、
**用已知真跨函数 UAF 做正例回归**（步骤 3）。

> 本文是本轮全部产出。每完成一步追加一节，不覆盖前面内容。

---

## 步骤 1 · `features.json` 的来源

### 查到的事实

**① `run_stage3.py` 不存在。**

`s4_abstract_features.py:546` 的注释写着"features.json 由遗留脚本组装"，
`features.json` 自己的 `_meta` 里写着 `"script": "run_stage3.py"`、
`"prompt": "prompts/stage4_abstract_feature.md"`——**这两个文件都不在了**：

```
$ ls pipeline/*.py | grep -c run_stage3
0
$ ls prompts/ | grep stage4_abstract_feature
（无）
```

`git log --follow outputs/stage4/uaf/features.json` 显示它来自
`f42cae18` / `73c8309b` 两次重构之前的一次运行，**之后被冻结在仓库里**。

**② `s4` 只读不写 `features.json`。**

```
$ grep -c 'open(fpath, "w"' pipeline/s4_abstract_features.py
0
```

它真正**写**的是 `feature_p_<tag>.json`（每个 pattern 一个），
而 `features.json` 是那份产物**曾经**的汇总。

**③ `feature_p_*.json` 是 `features.json` 的超集。**

| 字段 | `feature_p_*.json` | `features.json` | 来源 |
|---|:---:|:---:|---|
| `feature_name` / `precondition` / `trigger_path` / `mutation_target` / `parameterization` / `limitations` | ✅ | ✅ | **LLM（s4 每次运行产出）** |
| `applicability_rule` | ✅ | ❌ | **LLM（s4）**，但旧 `features.json` 里没有——只在 `applicability_rules.json` 里 |
| `differentiator` | ✅ | ❌ | **LLM（s4，R10 加的）** |
| `sample_ids` / `_input_sample_ids` | ✅ | `source_samples` | 从 stage3 pattern 抄 |
| `_source_support` | ✅ | `source_support` | 从 stage3 抄 |
| `_source_pattern` | ✅ | `source_pattern` | 从 stage3 抄 |
| `id` | ❌ | ✅ | **手写**（`uaf-llm01`…`uaf-llm05`） |
| `validation` / `_validation` | ✅ | ✅ | 脚本算（黑名单、计数） |

**结论**：`features.json` 里**唯一的"手写"内容就是 `id`**（`uaf-llm01`…`05`）。
其余字段全部可以从 `feature_p_*.json` + `final.json` 重建。

### `source_pattern` 的消费者清单

| 位置 | 用途 | 改名后会怎样 |
|---|---|---|
| `s4_abstract_features.py:553` `id_by_pattern` | 把判据映射到 `feature_id` | **悬空 → 判据被丢弃**（R10 的 bug） |
| `s5_5_build.py:82` `strategy_for()` → `STRATEGY[sp]` | 取构造策略（`part`/`op`/`field`/`anchor`） | **静默拿空 dict**，`part`/`op` 退回默认值 |
| `s5_5_build.py:84` | 把 `source_pattern` 写进 plan 的 stage 说明 | 只是记录 |

**还有一个隐藏的硬编码耦合（步骤 2 才发现）**：

| 位置 | 用途 | 改名后会怎样 |
|---|---|---|
| `s5_4_analyze.py::shortlist()` 的 `feature_id.split("-")[-1]` → `SHORTLIST[key]` | 每个特征一个**短名单过滤规则**（`name_rx`/`call_rx`），键是 `llm01`…`llm05` | **短名单变 0 个函数** → 下游报"扫出 0 个原语"，**看起来像"这个项目没有站点"** |

### `feature_id` 是怎么分配的

**手写的**：`uaf-llm01`…`uaf-llm05`，写在 `features.json` 里，没有任何脚本生成它。
`s4` 从 pattern 名反查这张表；`s5_4_analyze` 再从 id 反查 `SHORTLIST`。
**整条链都靠这两个字符串（pattern 名 / id）对齐，任一端改名就断。**

### 回答：重跑 stage3 之后，要让 stage4 跟上，必须人工做哪几件事？

**改之前**必须人工做 **3 件**：

1. 手工把 `features.json` 的 5 条 `source_pattern` 改成新的 pattern 名（**而且 5→5 的映射不一定存在**——R10 实测新的 5 条与旧的 5 条不是一一对应）；
2. 如果 `id` 也改了，要同步改 `s5_4_analyze.SHORTLIST` 的键（`llm01`…`05`）；
3. 要同步改 `s5_5_build.STRATEGY` 的键（旧 pattern 名）。

**三件都是纯人工、无提示、无校验的。** 这正是 R10 里"4/5 判据白做"的根因。

---

## 步骤 2 · 让 stage4 跟着 stage3 走

### 做法：`features.json` 由 `s4` 自己生成

按步骤 1 的结论选**"按 pattern 生成特征"**（而不是保留手写特征 + 容错匹配），
因为 `features.json` 里唯一手写的只有 `id`，其余都能重建。

新增 `s4_abstract_features.py::emit_features(typ)`：

- 读本次运行的 `feature_p_*.json`（按 `_RUN_STARTED_AT` 过滤掉上次残留）；
- **顺序**取 `stage3/final.json` 的 `final_patterns`；
- `feature_id`：**有 `legacy_id` 就沿用**（保住 `uaf-llm01`，下游硬编码的东西不断），
  否则用 `f"{typ}-p{i:02d}"`；
- `legacy_id` 从 `features.legacy.json`（旧文件的留档）按 pattern 名查；
- 把 `applicability_rule` / `differentiator` / `merge_into` 一并写进 `features.json`
  （旧版没有）。`_meta` 记 `generated_by` / `generated_at` / `n`。

`main()` 的顺序变成：`run_one` 循环 → **`emit_features`** → `emit_rules`。

### 另外两处硬编码耦合也修了

| 位置 | 改法 |
|---|---|
| `s5_4_analyze::shortlist()` | 没有专门规则时**退回全量 worklist 并打 stderr 告警**（原来返回空 → 假空） |
| `s5_5_build::strategy_for()` | 没有专门策略时**从判据派生兜底策略 + 打 stderr 告警**（原来静默给空 dict） |

### 5 条判据是否都接上

```
  写出 features.json：5 条（1 条有 legacy_id）
  判据汇总：5 条可用，0 条 rule_missing
```

| feature_id | legacy_id | source_pattern | 判据 |
|---|---|---|---|
| `uaf-llm01` | `uaf-llm01` | 同函数释放后访问 | `use_kind:[same_path,loop_back,realloc_alias] + direct_free` |
| `uaf-p02` | — | 别名重赋值跨函数访问 | `cross_function + direct_free + reassigned:true + link:false` |
| `uaf-p03` | — | 解码池释放后写入 | `cross_function + direct_free` |
| `uaf-p04` | — | 循环回调释放后读取 | `cross_function + direct_free + reassigned:false` |
| `uaf-p05` | — | 清理销毁释放后读取 / 解析拷贝释放后读取 | `cross_function + direct_free + reassigned:false + link:false` |

**0 条因 `source_pattern` 悬空被丢。** ✅

### libredwg 回归

```
  ✅ uaf-llm01   found    短名单 162 / 原语 4 / 支持 4
       站点 src/in_dxf.c:12284 → 12267  var=pair  branch=DXF     ← 未变
  ❌ uaf-p02/03/04/05  not_found
       短名单 162 / 原语 4 / 支持 0
       "短名单 162 个函数、扫出 4 个释放→使用原语，没有一个满足结构判据"
  found 1/5；权重 default 0.5 + 1×0.5 = 1.0
```

**另 4 条仍然 0 命中，而且理由是"162 个函数扫出 4 个原语但都不满足判据"**——
不是 R10 那种"短名单 0 个函数"的假空。**这是预期的**（libredwg 没有跨函数站点），
没有去调判据让它们命中。

### 新增测试

`test_renamed_stage3_pattern_does_not_drop_rules`：造一个"stage3 5 条 pattern 全改名"的场景
（旧 `features.legacy.json` 是 `旧形态-1..5`，本次产出 `新形态-1..5`），断言：

- `emit_features` 产出 **5** 条（不是 0）；
- 每条都带 `applicability_rule`；
- `source_pattern` 是新的 5 个；
- 新 pattern 用 `uaf-pNN` 而不是悬空。

**变异检验**：把 `emit_features` 的 `for fp in ...` 改成 `for fp in []`（模拟旧行为）→
该测试**变红**（`1 failed, 21 passed`）。✅ 证明测试不是摆设。

`pytest tests -q` → **26 passed**。

### 失败与存疑

1. **`emit_features` 的一个坑是我自己的测试踩出来的**：新加的
   `test_main_sets_run_start_before_running` 只 monkeypatch 了 `emit_rules`，
   没 patch `emit_features` → 它真的去写了 `outputs/stage4/uaf/features.json`，
   而当时 `_RUN_STARTED_AT` 是"现在"，本次文件比它旧 → **写成 0 条**，
   把真实产物清空了。已修测试（也 patch `emit_features`）。
   **教训：测试不能有写真实产物的副作用。**
2. **`SHORTLIST` 现在 4 条走"全量 worklist"**。能跑，但慢（162 个函数 × 每特征）。
   要给它配专门规则，需要按新的 4 条 pattern 重新写 `name_rx`/`call_rx`——
   那是**新的手写规则**，本轮没做（也不该为了让它"看起来对"而编）。
3. **`features.legacy.json` 现在多了一个文件**（旧的 `features.json` 留档，用于 `legacy_id`）。
   它不是产物，是**追溯用的输入**。

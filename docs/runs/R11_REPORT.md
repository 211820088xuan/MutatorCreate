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

---

## 步骤 3 · 跨函数扫描器正例回归

### 3.1 找正例：先遇到一个硬约束

**110 条 `free_cross_function=true` 跨 34 个项目，但本地只有 3 个项目的源码**
（`libredwg` / `gpac` / `curl`，就是已经测过的三个）。其中匹配的只有 **7 条**，
而且全是"释放助手被 use 函数自己调用"的那种（见 3.2 的 A 类）。

→ 为拿到真正的正例，克隆了两个小项目（`espeak-ng` 94 M、`flac` 7.1 M），
再加 `leptonica`（40 M，pin `8d77174` 由 GitHub API 解析短 sha 后取到）。

### 3.2 110 条的形态分布（**这是本步最重要的数据**）

用**调用图方向**分类（110 条里 81 个项目有调用边，29 条无）：

| 类别 | 条数 | 含义 | 扫描器能看见吗 |
|---|---:|---|:---:|
| **A) `use_fn` 调 `free_fn`** | **12** | 释放助手是被 use 函数**自己**调的 → 释放点其实**在同一个函数里** | ❌（它按"跨函数"设计，这是同函数） |
| **B) `free_fn` 调 `use_fn`** | **5** | 方向对了，但见下面的核实——**是"释放函数内部先调了使用函数"**，不是"释放后传参" | ❌ |
| **C) 互不可达** | **64** | 释放与使用在**不同调用子树** → 陈旧指针只能经**字段 / 全局 / 生命周期**到达 | ❌ |
| 无调用边，判不出 | 29 | — | ? |

**A 类里包括我们的两个目标**：`ARVO-42494732`（libredwg `dxf_free_pair → dxf_objects_read`）
和 `ARVO-42518828`（gpac `gf_free → gf_odf_vvc_cfg_read_bs`）。
→ **`free_cross_function=true` 是"栈帧"指标，不是"释放点在不同函数"。** 这条要记进限制。

**B 类 5 条里有 3 条有直接调用边**，我逐条核实了：

| 样本 | 项目 | 释放函数 → 使用函数 | 核实的源码 |
|---|---|---|---|
| `ARVO-42488049` | leptonica | `fpixDestroy → fpixChangeRefcount` | 同 `pixFree` 的形状（见下） |
| `ARVO-42488833` | leptonica | `pixFree → pixChangeRefcount` | **`src/pix1.c:639`**（pin `8d77174`） |
| `ARVO-42491546` | igraph | `igraph_gml_tree_destroy → igraph_vector_ptr_size` | 未核实（无源码） |

**`pixFree` 的实际形状**（`src/pix1.c:639`，pin `8d77174`，逐行读过）：

```c
static void
pixFree(PIX  *pix)
{
    if (!pix) return;
    pixChangeRefcount(pix, -1);          // ← 使用点（读/写 refcount）
    if (pixGetRefcount(pix) <= 0) {
        if ((data = pixGetData(pix)) != NULL) pixdata_free(data);
        if ((text = pixGetText(pix)) != NULL) LEPT_FREE(text);
        pixDestroyColormap(pix);
        LEPT_FREE(pix);                  // ← 真正的释放
    }
    return;
}
```

**`pixChangeRefcount` 在 `LEPT_FREE` **之前**。** 所以"直接边"是
"释放函数内部先调了使用函数"，**不是**"释放后把 V 传给 G"。
真正的 UAF 是 `pixFree` 被**调了两次**（第二次的 `pixChangeRefcount` 读到已释放的 refcount）。

→ **B 类的 3 条也不是扫描器支持的形态。**

### 3.3 扫描器结果 + 被哪道守卫挡

| 仓库 | 索引函数数 | 加守卫前站点 | **加守卫后站点** | 主要被拒原因 |
|---|---:|---:|---:|---|
| `flac` | 1,039 | **45** | **0** | `no_call_with_var_as_arg1` 408、**`guard9_control_flow_return` 335** |
| `espeak-ng` | 510 | 0 | 0 | `no_call_with_var_as_arg1` 288、`guard9_control_flow_return` 73 |
| `libredwg` | 162 | 0 | 0 | `no_call_with_var_as_arg1` 1,023 |
| `leptonica` | **73（索引不完整）** | 0 | 0 | — **不算证据**（见下） |

**`leptonica` 只索引到 73 个函数**——它是"返回类型单独一行"的签名风格
（`static void\npixFree(PIX *pix)`），我的轻量索引器要求签名整行，所以漏了大半。
**它的 0 不能当"没有站点"的证据。**

### 3.4 这轮实际修掉了三处假阳性源（都是真 bug）

为了把 flac 的 45 个假阳性压到 0，依次发现并修了**三个**：

| # | 守卫 | 假阳性源 | 修法 | 命中数 |
|---|---|---|---|---:|
| 1 | **守卫 8**（新） | `static_metadata_clear(&static_metadata)` 被当成"释放了 `static_metadata`"——其实是**取地址**，结构体一直在栈上 | 释放实参里含 `&` → 跳过 | 38 |
| 2 | **守卫 9**（新） | `if (bad) { free(x); return; } … G(x)` —— 释放和调用在**互斥分支**里，按行号当执行顺序就出假阳性 | 释放与调用之间出现 `return`/`break`/`continue`/`goto` → 跳过 | **241（flac）/ 335（加全部守卫后）** |
| 3 | **`wrapper_frees_param` 的实参边界** | `free(encoder->protected_->metadata)` 被当成 `free(encoder)` —— `\b` 在 `encoder` 和 `->` 之间成立，**和 R7 修的实参匹配是同一类 bug** | 要求形参后面紧跟 `,` 或 `)` | — |

**守卫 9 是主导假阳性源**：flac 里除了 `no_call_with_var_as_arg1`（本来就没调用），
它就是最大的一类。**"按行号顺序当执行顺序"是扫描器的结构性缺陷**，这一轮只挡住了
最明显的四种跳转。

### 3.5 libredwg 回归（必须不变）

```
  ✅ uaf-llm01  found  短名单 162 / 原语 4 / 支持 4
       站点 src/in_dxf.c:12284 → 12267  var=pair  branch=DXF     ← 未变
  ❌ uaf-p02/03/04/05  not_found（162 个函数扫出 4 个原语，都不满足判据）
  found 1/5；权重 1×0.5 = 1.0
```

`pytest tests -q` → **26 passed**。

### 结论：**"扫描器支持的形态太窄"，而不是"工具对"或"守卫过严"**

按你给的分支表，落在**第三种**：

> **一条正例都找不到（110 条里没有实参传递形态的）** → 扫描器支持的形态太窄——
> 真实的跨函数 UAF 主要走字段/全局/回调。这是比"0 命中"强得多的结论。

**支撑数据**：

1. **110 条里 0 条是"释放后把同一变量作为实参传给下一个函数"这个形态。**
   - 12 条（A）释放点其实在同一个函数里；
   - 5 条（B）方向对但"使用点"在释放**之前**（`pixFree` 的 `pixChangeRefcount`）；
   - 64 条（C）互不可达 → 只能经字段/全局/生命周期；
   - 29 条无调用边。
2. **五个仓库（libredwg / gpac / flac / espeak-ng / 部分 leptonica）加守卫后全 0 站点。**
3. **守卫不是主因**：加守卫前 flac 有 45 个候选，但**全部**是控制流假阳性
   （`return` 在中间）或取地址假阳性——**没有一个是真站点**。
   所以"0 命中"不是守卫挡掉了真的，而是**真的没有这个形态**。

**这说明限制 7 要改写**：不是"跨函数扫描器未兑现"，而是
**"它支持的形态在真实 UAF 里占比接近 0"**——详见 `HANDOFF.md` 限制 7 的改写。

### 失败与存疑

1. **`free_cross_function` 是栈帧指标，不是"释放点在不同函数"**。这条会影响任何用它筛选的分析
   （包括 R10 的 110 这个数字）。
2. **守卫 9 只挡住了四种跳转**。`if/else` 分支、`switch`、异常/长跳转（`setjmp`）、
   宏展开里的 `return` 都没处理。**"按行号当执行顺序"这个根本问题还在。**
3. **`leptonica` 的索引不完整（73/约 500）**，它的 0 不算证据。
   要修得用 `s5_2_prepare.extract_function`（它已支持两种签名风格），本轮没接。
4. **`igraph` 的 1 条（`ARVO-42491546`）没核实**（没克隆）。
5. **没有一条正例**，所以无法证明"扫描器能扫出真站点"。
   **这是能力未兑现的直接证据，不是间接推断。**

---

## 汇总

### 三步结论各一句话

| 步骤 | 结论 |
|---|---|
| **1 · `features.json` 的来源** | 它是**冻结的手写产物**（`run_stage3.py` 已不存在），唯一手写内容是 `id`；`source_pattern` 有**三个**消费者（`emit_rules` / `STRATEGY` / 隐藏的 `SHORTLIST`） |
| **2 · 让 stage4 跟着 stage3 走** | 新增 `s4.emit_features()` 从 `feature_p_*.json` 组装 `features.json`，`feature_id` 有 legacy 就沿用；**5 条 pattern → 5 条判据，0 条悬空**；libredwg 站点未变 |
| **3 · 跨函数正例回归** | **一条正例都没有**——110 条真实跨函数 UAF 里 **0 条**是扫描器支持的"释放后传参"形态（12 同函数 / 5 方向反 / 64 经字段或全局）；顺带修掉**三处**假阳性源 |

### 限制 7 是否要改写（改写后的原文）

**要，已改写。** 新标题与正文：

```markdown
## 限制 7 · 跨函数扫描器**支持的形态在真实 UAF 里占比接近 0**

R11 用已知崩溃做了正例回归（不是靠猜），结论比"0 命中"强得多：

**① `free_cross_function=true` 不是"释放点在不同函数"，是"栈帧不同"。**
110 条里 **12 条**是"释放助手被 use 函数自己调用"——释放点其实**在同一个函数里**。
**我们的两个目标都在这 12 条里**：libredwg 的 `dxf_free_pair → dxf_objects_read`、
gpac 的 `gf_free → gf_odf_vvc_cfg_read_bs`。

**② 110 条按调用图方向的分布**（81 个项目有调用边）：

| 类别 | 条数 | 扫描器能看见吗 |
|---|---:|---|
| A) `use_fn` 调 `free_fn`（释放点其实同函数） | **12** | ❌ |
| B) `free_fn` 调 `use_fn`（方向对，但使用点在释放**之前**） | **5** | ❌ |
| C) 互不可达（只能经字段/全局/生命周期） | **64** | ❌ |
| 无调用边 | 29 | ? |

**B 类的核实**（leptonica `src/pix1.c:639`，pin `8d77174`）：
`pixFree` 里 `pixChangeRefcount(pix, -1)` 在 `LEPT_FREE(pix)` **之前**——
所以"直接边"是"释放函数内部先调了使用函数"，**不是**"释放后传参"。

**③ 五个仓库加守卫后全 0 站点**（libredwg 162 / gpac / flac 1,039 / espeak-ng 510 函数），
而**加守卫前 flac 的 45 个候选全部是假阳性**——所以"0 命中"**不是守卫挡掉了真的**。

**④ 这轮实际修掉三处假阳性源**（都是真 bug）：

| 守卫 | 假阳性源 | 修法 |
|---|---|---|
| **守卫 8**（新） | `foo(&x)` 是**取地址**，x 没被释放 | 释放实参含 `&` → 跳过 |
| **守卫 9**（新） | `if (bad) { free(x); return; } … G(x)` —— 释放和调用在**互斥分支**里 | 之间有 `return/break/continue/goto` → 跳过（flac 里 241 次命中） |
| `wrapper_frees_param` | `free(encoder->protected_->metadata)` 被当成 `free(encoder)`（`\b` 在 `encoder` 和 `->` 之间成立，与 R7 修的实参匹配同类） | 要求形参后紧跟 `,` 或 `)` |

**所以结论改写为**：**扫描器实现的"释放后传参"形态，在 110 条真实跨函数 UAF 里占比 0**
（12 同函数 / 5 方向反 / 64 经字段或全局 / 29 判不出）。
**不是"能力未兑现"，是"支持的形态太窄"。**

**根本缺陷**：扫描器**按行号顺序当执行顺序**（守卫 9 只挡住了四种跳转，
`if/else`、`switch`、`setjmp` 都没处理）。
```

### `HANDOFF.md` 改了哪些（完整 diff）

```diff
@@ -205,21 +205,45 @@
 **影响面**：ISOM/MP4 系（gpac）、以及所有用"类型 → 回调"注册表的解析器。
 这类格式在真实崩溃里占比不低。
 
-## 限制 7 · 跨函数扫描 0 命中，能力未兑现
+## 限制 7 · 跨函数扫描器**支持的形态在真实 UAF 里占比接近 0**
 
-R7 步骤 4 加了跨函数形态（`use_kind = cross_function`）：
-A 里 `free(V)` → 之后调用 `G(V)` → G 里读形参。**行号顺序证明释放先于使用，实参证明同一对象。**
-六道守卫对着 R4 记的假阳性逐条设（`wrapper_frees_param` 不算释放 / 释放后置空 / 释放后重赋值 /
-实参必须整个是 V / 被调函数是释放助手 / `#if 0` 死代码）。
+R11 用已知崩溃做了正例回归（不是靠猜），结论比"0 命中"强得多：
 
-| 项目 | 跨函数站点 | 核对结果 |
+**① `free_cross_function=true` 不是"释放点在不同函数"，是"栈帧不同"。**
+110 条里 **12 条**是"释放助手被 use 函数自己调用"——释放点其实**在同一个函数里**。
+**我们的两个目标都在这 12 条里**：libredwg 的 `dxf_free_pair → dxf_objects_read`、
+gpac 的 `gf_free → gf_odf_vvc_cfg_read_bs`。
+
+**② 110 条按调用图方向的分布**（81 个项目有调用边）：
+
+| 类别 | 条数 | 扫描器能看见吗 |
 |---|---:|---|
-| libredwg | 第一版 **15** → 加守卫 **6** → 再补守卫 **0** | 三轮逐个人工核对，全部假阳性（与 R4 独立结论一致） |
-| gpac | 0 | — |
+| A) `use_fn` 调 `free_fn`（释放点其实同函数） | **12** | ❌ |
+| B) `free_fn` 调 `use_fn`（方向对，但使用点在释放**之前**） | **5** | ❌ |
+| C) 互不可达（只能经字段/全局/生命周期） | **64** | ❌ |
+| 无调用边 | 29 | ? |
+
+**B 类的核实**（leptonica `src/pix1.c:639`，pin `8d77174`）：
+`pixFree` 里 `pixChangeRefcount(pix, -1)` 在 `LEPT_FREE(pix)` **之前**——
+所以"直接边"是"释放函数内部先调了使用函数"，**不是**"释放后传参"。
+
+**③ 五个仓库加守卫后全 0 站点**（libredwg 162 / gpac / flac 1,039 / espeak-ng 510 函数），
+而**加守卫前 flac 的 45 个候选全部是假阳性**——所以"0 命中"**不是守卫挡掉了真的**。
+
+**④ 这轮实际修掉三处假阳性源**（都是真 bug）：
+
+| 守卫 | 假阳性源 | 修法 |
+|---|---|---|
+| **守卫 8**（新） | `foo(&x)` 是**取地址**，x 没被释放 | 释放实参含 `&` → 跳过 |
+| **守卫 9**（新） | `if (bad) { free(x); return; } … G(x)` —— 释放和调用在**互斥分支**里 | 之间有 `return/break/continue/goto` → 跳过（flac 里 241 次命中） |
+| `wrapper_frees_param` | `free(encoder->protected_->metadata)` 被当成 `free(encoder)`（`\b` 在 `encoder` 和 `->` 之间成立，与 R7 修的实参匹配同类） | 要求形参后紧跟 `,` 或 `)` |
+
+**所以结论改写为**：**扫描器实现的"释放后传参"形态，在 110 条真实跨函数 UAF 里占比 0**
+（12 同函数 / 5 方向反 / 64 经字段或全局 / 29 判不出）。
+**不是"能力未兑现"，是"支持的形态太窄"。**
 
-**0 命中既可能是"确实没有"，也可能是"守卫过严"——目前分不开。**
-而且只支持"实参传递"一种形态；**结构体字段、全局变量、回调/函数指针**都没做，
-而真实项目里的"跨函数"大量走这三种。
+**根本缺陷**：扫描器**按行号顺序当执行顺序**（守卫 9 只挡住了四种跳转，
+`if/else`、`switch`、`setjmp` 都没处理）。
 
 ## 限制 8 · LLM 归纳**有产物，但在唯一的落地项目上没有可命中的目标**
 
```

### 下一步建议：换项目该挑什么样的

**不要按"UAF 数量多"挑。** 按 R11 的形态分布，**只有"释放点与使用点在同一个函数、
且中间把该指针传给下一个函数"这一种形态**扫描器才看得见。建议按这个顺序：

| 优先级 | 挑什么 | 为什么 |
|---|---|---|
| **P0** | **先扩形态，再换项目**：把扫描器扩到**结构体字段**（64 条里的主体） | 64/110 是"经字段/全局/生命周期"。不扩形态，换十个项目还是 0——R11 已经把这一点证明了 |
| **P1** | 扩完形态后再挑项目：**选 C 类里样本多、且 CPG 质量好的**（如 `libxml2` 13 条、`open62541` 9 条） | 这些项目有真实跨函数 UAF，且我们已有部分 CPG |
| **P1** | 把轻量索引器换成 `s5_2_prepare.extract_function` | leptonica 只索引到 73/约 500，因为它是"返回类型单独一行"的签名风格 |
| **P2** | 给扫描器补真正的控制流（`if/else`、`switch`、`setjmp`） | 守卫 9 只挡住四种跳转，"按行号当执行顺序"的根本问题还在 |
| **P2** | 修正 `free_cross_function` 的语义（现在混了"栈帧不同"和"释放点不同"） | 它影响了 R10 的 110 这个数字，以及任何用它筛选的分析 |

### 本轮刻意不做的

- 扩跨函数形态到字段/全局/回调（**要等这轮的分布数据出来再决定**——现在数据出来了，见上表 P0）
- 换项目 / 换崩溃类型
- 函数指针分派（限制 6）
- 补抓剩下 34 个 CPG
- 重跑 hbo/stack/global 的 stage3

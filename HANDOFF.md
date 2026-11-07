# mutator_create 交接（入口）

> **⚠️ R4–R17 的轮次报告已按要求删除**（2026-11-07）。
> 现存只有 `R18_REPORT.md` / `R19_REPORT.md` / `R20_REPORT.md`。
>
> **历史报告仍然可恢复**（删除前最后一个提交是 `6891f916`）：
> ```bash
> git show 6891f916:docs/runs/R7_REPORT.md
> git checkout 6891f916 -- docs/runs/R4_PHASE_B.md   # 单个恢复
> ```
> 被删的 15 个：`R4_PHASE_A.md` `R4_PHASE_B.md` `R5_REPORT.md` … `R17_REPORT.md`。
>
> **本文件里对它们的引用（如"详见 R7_REPORT.md"）仍然有效，只是要去 git 历史里看。**

> 目标：从已复现的崩溃归纳**同一类型崩溃的共性特征**，把特征落到具体项目的**真实代码站点**，
> 生成能提高目标崩溃触发概率的 custom mutator。
> **验收标准只有一条**：custom vs default 的 A/B 对照里 custom 更好。不是"找到新 bug"，不是"覆盖率涨了"。

---

# 〇、这项工作证明了什么 / 没证明什么

## 证明了的（每条附数据）

1. **从一个已知崩溃推导触发结构、生成定向算子，在 default 够不到的场景下有效。**
   `reps_r9_final`（2026-11-04 用**当前二进制** `a416b44d` 重跑，剥段种子、300 s × 5 rep、
   **5 个 rep 相互独立**：617 个崩溃文件 617 个唯一 sha1、两两交集全 0、`-seed` 1/2/3/4/5）：
   **`default 0 / 1,102,847 execs`** vs **`custom 617 / 640,359 execs`**。
   （R6 的历史测量 `reps_pathB_r3` 是 `0/1,048,238` vs `731/508,682`，同量级。）
   率比无定义（分母 0），原始计数就是结论。
2. **结构判据能跨项目。** gpac（训练集之外）上命中的站点
   `gf_odf_vvc_cfg_read_bs` `gf_free(ar)` @1400 → 读 `ar->type` @1404，
   与人工读源码确认的**是同一处**；同时 libredwg 的站点与权重**一字不变**。
3. **整条链能自动化。** fetch / 站点扫描 / 判据匹配 / 六步证据链 / 输入格式推导，
   在第二个项目上**都是流程自己做的**（不是人工指定常量）：
   - `input_branch()` 从 harness 源码 + CPG 调用图推导，libredwg 推出 `DWG/AC`、`JSON/{`、`DXF/默认`；
   - 手工写死的 libredwg 路径前缀表**已删除**。

## 没证明的（每条附原因）

1. **不能自主发现站点。** gpac 的故障函数靠 `--fault-anchor` **塞进清单**
   （`fault_anchor_enabled = True`、`fault_fn_in_closure = False`）。
   根因不是 depth 不够：`vvcc_box_read` 在 CPG 里**零调用者**——它经 box 注册表的
   **函数指针**被调用（`box_funcs.c:1893` `a->registry->read_fn(a, bs)`），
   静态调用图里没有这条边，**不限深度也到不了**（完整图 984 个可达节点里没有它）。
2. **LLM 归纳不优于手写规则。** 见限制 2 / 限制 8 与 `docs/runs/R9_REPORT.md` 步骤 2：
   词表紧 → 4 条 `expressible: false`；词表松 → 3 条恒真；加可证伪约束后 5 条都具体了，
   但**命中集合与 llm01 完全相同**（没有一条找到 llm01 找不到的站点）。
   唯一一处明显更差的是 `uaf-llm05`：手工版 `is_link_read: true` 抓住了"沿链遍历"这个
   定义性特征，LLM 版把它丢了。
   **R9 更正了 R8 的一个机制误判**：R8 说 `llm02/03/05` "0 命中"，实际是
   `bool("false") == True` 的解析 bug 把它们判死了；修掉后它们命中**同一批**站点。
   结论（没有增量）不变，理由是"等价"而不是"太严"。
3. **跨函数机制没兑现。** 跨函数扫描器至今**两个项目都 0 命中**（libredwg 15→6→0、gpac 0），
   候选全部核对为假阳性。而且只支持"实参传递"一种形态，字段/全局/回调都没做。
4. **不能推广到未知崩溃。** 整条派生链的起点是**已知的 `fault_line`**——
   这是"错误激发型"方法的前提，不是缺陷，但它就是不能用来论证"能发现未知崩溃"。

---

# 一、方法论限制（必读，不是附录）

## 限制 1 · 构造路径是循环的

改造后的算子会插入 `0/SECTION + 2/OBJECTS + 0/<随机非已知名> + 0/ENDSEC`，
这**正是目标 UAF（`in_dxf.c:12267`）所需要的三段结构**；而实验语料又**正是剥掉该结构的种子**。

派生链本身可追溯（不是手写常量）：

| 片段 | 来源 | 记录位置 |
|---|---|---|
| `section_anchor = OBJECTS` | 站点守卫 `strEQc(pair->value.s, "OBJECTS")` | `construct.basis_refs` → `target_surface:evidence_chain:step5/step6` |
| `0/<随机非已知名>` | 否定式谓词 `!is_dwg_object(name)` 的补集 | `construct.basis_refs` → `new_value_policy` |
| 插入位置（`0/EOF` 之前） | 种子里实测的块边界 | `construct.insert_position.derivation` |

**但整条链的起点是已知的 `fault_line 12267`。** 这是"错误激发型"方法的**前提**（先有已知崩溃，
再提取共性），不是缺陷——但必须写明：**它不能用来论证"我们的特征提取能推广到未知崩溃"。**

## 限制 2 · 特征提取的贡献没有被单独证明

| 事实 | 数字 |
|---|---|
| 5 个 UAF 特征里能落地的 | **1 个**（`uaf-llm01` 同函数释放后访问）；R8 之后另 4 个是 `not_found`（判据拒了它们，不是"没扫"） |
| 唯一落地的那个，机械规则能不能单独找到 | **能** —— `mech_hypotheses.json` 的 `R1 dxf_objects_read 释放 L12284 → 使用 L12267` |
| agent 全量审计（162 函数 / 188 turns / 63,078 字符工具回传）的**独有且被采纳**发现 | **0 条**（候选 `c001` 是 `audit + mech` 双来源） |
| **R8：5 条 LLM 判据（加了可证伪约束后）有没有一条命中 llm01 命中不到的站点** | **没有**（`llm02/03/04/05` 全部 0 命中，`llm01` 命中那 4 个） |
| **R8：LLM 判据 vs 手工判据** | **3 胜 1 负 1 平**：`llm02` 更具体（4 个字段 vs 1 个）、`llm03/llm04` 从 `name_regex` 变**结构判据**；`llm05` **输了**（丢了 `is_link_read`） |

→ **赢的是"算子"，不是"特征提取"。**
两条独立证据：（a）唯一落地的特征机械规则也能找到；（b）把判据从"名单"改成"结构"、
把词表从紧放到松再收紧，**命中集合始终只有 llm01 那 4 个站点**——
判据层的所有改进都没有带来新的落地。

## 限制 3 · 吞吐劣势吃掉定向优势

custom 臂的 execs 一直显著低于 default：

| 组 | default execs | custom execs | custom/default | 备注 |
|---|---:|---:|---:|---|
| 1A 复跑（现种子 150 s） | 42,912 | 32,379 | **75.5%** | reps 非独立（见限制 4 附注） |
| 1B DXF-only（150 s） | 426,076 | 196,522 | **46.1%** | reps 非独立 |
| 路径 B（剥段种子 300 s） | **1,102,847** | **640,359** | **58.1%** | `reps_r9_final`，**独立**（历史 `reps_pathB_r3` 是 48.5%） |
| 路径 B 回归（现种子 150 s） | 45,136 | 33,477 | **74.2%** | reps 非独立 |

**只要目标结构存在，a001 做的事 default 也能做**（改一个字节就命中，default 自身 96/100k）；
这时比的就是"单位时间试多少次"——吞吐劣势把定向优势吃掉了。
这解释了 **1B 为什么配对胜出 0/5 全输**，也解释了**路径 B 为什么必须靠"结构不存在"的场景才赢**。

## 限制 4 · `RR = 0.954` 是被一次损坏运行压出来的

旧 `reps_n5_r1` 的 `rep05/default` 只有 **1,391 execs**（`exec/s` 塌到 9），复跑是 10,622。
用复跑版（`reps_n5_r2`）：**RR = 1.131，95% CI = [0.72, 1.78]**，配对胜出 2/5。

→ 统一表述为：**在目标结构存在的场景里，效应量低于噪声**（两次 CI 都含 1，且点估计方向相反：0.954 → 1.131）。

**附注（2026-11-03 实测）**：所有旧 n=5 组都用了硬编码 `-seed=1`，5 个 rep 不是独立样本——
崩溃文件跨 rep 重复 22–80%。这些组的 CI 都偏窄，引用时必须标注。
**目前唯一独立的 n=5 数据是 `reps_r9_final`（当前二进制）与 `reps_pathB_r3`（历史二进制）。**

## 限制 5 · 第二个项目：判据层已经修好，但**站点枚举层**还走不通

`docs/runs/R5_REPORT.md` 是本轮的完整记录。要点：

### 5.1 适用性判据已经从「名单」改成「结构」（R5 步骤 1–3，**已成立**）

- 旧预筛 `where_free ∩ 可达函数` 本质是**"这个项目在不在训练集里"的成员测试**
  （5 个 pattern 的样本覆盖 33/35 个 UAF 项目），已**整段删除**。
- 判据现在是数据：`outputs/stage4/uaf/applicability_rules.json`，
  字段只有 `use_kind` / `free_kind` / `reassigned_between` / `is_link_read`，
  **判定代码里没有任何按 `llm01`…`llm05` 的 ID 分支、也没有写死的函数名正则**。
- `not_applicable` 这个状态已从 pipeline 里彻底移除。
- 在 libredwg 上复现原结果：`uaf-llm01` `found`（`src/in_dxf.c:12284 → 12267`，`var=pair`，`DXF`），
  其余 4 个 `not_found`，权重 `0.5 + 1×0.5 = 1.0`。
- **stage4 现在自己产出判据**（步骤 3，LLM）：`uaf-llm01` 给出的规则
  `{use_kind:[loop_back, same_path], free_kind:direct_free, is_link_read:any}`
  **能复现**上面的结果。

### 5.2 但 5 个特征里有 4 个被判「表达不了」

stage4 对 `uaf-llm02/03/04/05` 全部返回 `expressible: false`，理由是同一个：
**它们的释放点与使用点在不同函数里，而 `scan_sites()` 只在单个函数体内找"释放→使用"**。
这不是模型偷懒——我在步骤 1 独立核对词表时就发现 `cross_function` **算不出来**。
**所以"跨函数"是扫描器的能力边界，不是判据设计的选择。**

### 5.3 gpac 已经走通到 `found`——但**是喂了答案的**

R6 让 gpac 走到 `blocked`（`input_branch` = UNKNOWN）。R7 又往前推了三步：

| 环节 | 结果 |
|---|---|
| `--depth` | **是个真 bug**：`s5_1_main.py` 只转发 `extras`，`--depth` 等已知参数被入口吃掉。修好后 gpac 闭包 12→34→98→179（depth 2/3/4/5） |
| 但 depth **不是** gpac 需要锚点的原因 | `vvcc_box_read` 在 CPG 里**零调用者**——它经 box 注册表的**函数指针**被调用（`box_funcs.c:1893` `a->registry->read_fn(a, bs)`）。**静态调用图上从 `LLVMFuzzerTestOneInput` 出发（不限深度，984 个可达节点）根本到不了故障函数** |
| `fault_anchor` | 已降级为 `--fault-anchor` 显式开关（默认关），启用时打大字警告；`fault_anchor_enabled` 继承到 `target_surface.json` / `feature_pipeline.json` |
| harness | gpac 的 fuzz target **不在 OSS-Fuzz**，在 gpac 的 **submodule** `gpac/testsuite` 里（`oss-fuzzers/fuzz_parse.c`）。已取并落盘 |
| `input_branch()` | 已从写死的 libredwg 路径前缀表 → **从 harness 源码 + CPG 调用图推导**。libredwg 推导出 `DWG/AC`、`JSON/{`、`DXF/默认`，站点判 `DXF`（**与硬编码版逐项一致**，含 magic 描述） |
| gpac 的 status | `blocked` → **`found`**（`branch=ISOM`，`via: file`，`ambiguous: [ISOM, CONFIG]`） |

**所以 gpac 现在是 `found`，但 `fault_anchor_enabled = True`、`fault_fn_in_closure = False`——
故障函数是 `--fault-anchor` 塞进清单的，不是流程自己走到的。**

### 5.4 R7 的核心结论：判据层放宽后，**LLM 反而更不具体**

R7 给 `scan_sites()` 加了跨函数形态（`use_kind = cross_function`：
A 里 `free(V)` → 之后调用 `G(V)` → G 里读形参，**行号顺序证明释放先于使用、实参证明同一对象**），
并给 stage4 的词表加了 `cross_function`。

结果：**5 条判据全部产出（0 条 `rule_missing`）**，但质量是：

| feature | LLM 判据 | 具体性 |
|---|---|---|
| `uaf-llm01` | `use_kind:[loop_back,same_path], free_kind:direct_free` | 具体 ✅ |
| `uaf-llm02` | `use_kind:any, free_kind:any` | **恒真（空判据）** ❌ |
| `uaf-llm03` | 4 种 use_kind × 4 种 free_kind | 近乎恒真 ❌ |
| `uaf-llm04` | `use_kind:cross_function, free_kind:direct_free` | **具体、可证伪** ✅ 但两项目 0 命中 |
| `uaf-llm05` | 3 种 use_kind × direct_free | 近乎恒真 ❌ |

**后果**：libredwg 从 `found 1/5`（`1×0.5`）变成 `found 4/5`（`4×0.125`），
而四个"命中"指向**同一批 4 个站点**——llm02/03/05 没有找到任何 llm01 看不到的东西，
只是把 llm01 的权重从 50% 稀释到 12.5%。

**对比 R5 手工抽的那套**（`llm02: free_kind:[3 个 realloc 值]`、`llm05: is_link_read:true`…），
**手工版反而更具体**。→ **"LLM 归纳比手写规则强"目前没有正面证据；
把词表放宽之后，模型倾向于选 `any` 来自保。**

### 5.5 跨函数扫描器目前 0 命中（这是正确的，但也是空的）

libredwg 的跨函数候选：第一版 15 个、加守卫后 6 个、再补守卫后 **0 个**——
三轮都逐个人工核对为假阳性（与 R4 的独立结论一致）。gpac 同样 0 个。

6 道守卫（对着 R4 记的假阳性逐条设）：`wrapper_frees_param` 不算释放 / 释放后置空 /
释放后重赋值 / 实参必须整个是 V / 被调函数是释放助手 / 被调函数体直接 free 了形参 /
`#if 0` 死代码。

**所以 `cross_function` 这个能力到今天为止，还没有在一个真站点上兑现过。**
而且 gpac 的故障函数经**函数指针**被调用，本来就是"跨函数"从根上看不见的那种。

---

## 限制 6 · 静态调用图够不到函数指针分派（影响整类容器格式）

R7 步骤 1 实测：

| 事实 | 数据 |
|---|---|
| gpac 的 `LLVMFuzzerTestOneInput` 在 CPG 里吗 | **在**（`fuzz_parse.c`） |
| 从它出发、**不限深度**可达多少节点 | **984 个** |
| 里面有 `gf_odf_vvc_cfg_read_bs` 吗 | **没有** |
| 它的调用者 `vvcc_box_read` 在 CPG 里的调用者数 | **0** |
| 为什么 | `box_funcs.c:1893` `return a->registry->read_fn(a, bs);` —— box 读取器是**注册表里的函数指针** |
| 加到 depth 5 覆盖到了吗 | **没有**（闭包 12→34→98→179，故障函数一直不在） |

**所以"从 fuzz target 调用的 API 出发自己找崩溃"这条路，对分派表架构的解析器
在调用图这一层就断了。** 这不是 depth 问题——`--depth` 本身还有个 bug（`s5_1_main.py`
只转发 `extras`，`--depth`/`--type`/`--feature` 被入口吃掉），那个修好后闭包确实涨了，
但故障函数依然不在里面。

**影响面**：ISOM/MP4 系（gpac）、以及所有用"类型 → 回调"注册表的解析器。
这类格式在真实崩溃里占比不低。

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

## 限制 8 · LLM 归纳**有产物，但在唯一的落地项目上没有可命中的目标**

**先更正 R8/R9 的一处误判**：R8 说"`llm02/03/05` 全部 0 命中 → 没有增量"，
机制是错的——那是 `bool("false") == True` 的解析 bug 把它们判死了（R9 修）。
修掉后它们命中**同一批**站点。

**R10 重做了这一层（换 stage3 合并判据 + 加实测维度 + 强制去重）**：

| | 改前（R9） | **改后（R10）** |
|---|---|---|
| stage3 uaf 规律数 / 可区分点 | 5 / **4** | **5 / 5** |
| 仍完全相同的组 | 2 条（清理析构 ≡ 容器节点） | **无** |
| stage4 `merge_into` | — | **0 条**（分类已互不包含） |
| libredwg 命中 | llm01 的 4 个 | **llm01 的 4 个** |
| **有特征找到 llm01 找不到的站点吗** | 没有 | **没有（一条也没有）** |

**所以结论要分成两层**：

1. **分类重叠是归纳方法的问题，已修。** 8 维空间上 UAF 的规律**可以分开**
   （5 条 support 10/14/5/8/80，`free_and_use_same_function` / `reassigned_between` /
   `in_loop` / `free_cross_function` / `access_kind` 各有用武之地）。
2. **"站点层面没有增量"不是归纳的问题，也不是 UAF 的固有属性，是语料 + 扫描器的限制。**
   其余 4 条 pattern 描述的都是**跨函数**形态（`free_and_use_same_function=false`、
   `free_cross_function=true`），而 **libredwg 的跨函数站点是 0 个**（R7 实测 15→6→0）。
   **没有目标可以命中——不是判据太严。**

→ **要检验"归纳有价值"，必须换一个能扫出跨函数站点的项目，或换崩溃类型。**
在 libredwg 上无论判据怎么改，答案都会是"没有增量"，因为语料里只有一种形状。

**另有一个结构性问题（R10 发现）**：`features.json` 是**手写的 5 条特征**，
`source_pattern` 指向旧分类名。**stage3 的改进不会自动传导到 stage4**——
换判据后 4 条 `source_pattern` 悬空，判据被丢弃（只有 `同函数释放后访问` 还对上）。

## 限制 9 · 引用 A/B 结果必须连 `mutator.c` 的 sha1 一起记

**同一份 plan 每次 `generate` 产出不同的算子实现，这是设计而不是缺陷。**
每次生成是一次独立的 LLM 调用，"能力等价 + 实现不同"完全可以接受。

已观测到的三次（能力剖面完全相同：含 OBJECTS 500/500、剥段 500/500、DWG 0、特征路径 50%）：

| 次 | `mutator.c` | 用在哪 |
|---|---:|---|
| R6 | **440 行** | `reps_pathB_r3`（历史证据） |
| R9 步骤 1 | **294 行**（sha1 `d7913b9e`） | **`reps_r9_final`**（二进制 `a416b44d`，当前可引用） |
| R9 步骤 2 | **243 行**（sha1 `67cc88b0`） | 未用于任何 A/B |

**因此有一条记录要求（不是缺陷声明）**：

> 引用任何 A/B 数字时，**必须同时记 `mutator.c` 的 sha1**。
> 只写"用了 custom mutator"无法证明跑的是哪一版实现。

当前可引用的组合是：**`reps_r9_final` + `mutator.c` sha1 `d7913b9e` + 二进制 sha1 `a416b44d`**。

## 限制 10 · "语义可证伪"在这套数据上不可检验

R9 按设计实现了语义版校验（拿真实扫出的站点当试金石，逐字段去掉看命中集合变不变），
**实测把 `llm01` 判成 `rule_missing`**——而 `llm01` 是唯一能落地的特征。

根因不是实现，是**试金石没有负样本**：

```
  试金石站点: 2 个
    {'use_kind':'same_path', 'free_kind':'direct_free', 'reassigned_between':False, 'is_link_read':False}
    {'use_kind':'loop_back', 'free_kind':'direct_free', 'reassigned_between':False, 'is_link_read':False}
  每个字段的取值域: use_kind 2 个 / free_kind 1 个 / reassigned 1 个 / is_link_read 1 个
```

`scan_sites()` 只产出**已经被筛成 UAF 形态**的站点，所以任何**正确描述**这批站点的判据，
在它们身上都"排除不了任何东西"。

**要真正检验，必须人为构造负样本**（例如合成 `use_kind=cross_function` 的站点）。
那是新工作，本轮没做。**现行门禁是 `structural`**（= 语法真子集 + 不把结构性单值字段计入）。

---

## 限制 11 · 三个"字段名与语义不符"的坑（本项目已吃三次）

这个项目反复栽在同一件事上：**字段被填了，但填的不是名字说的那个东西。**
三次都是"跑了几轮之后才在别处撞到"：

| # | 字段 | 名字说的是 | 实际填的是 | 实测 | 影响 |
|---|---|---|---|---|---|
| 1 | `fixtures` 里的 `free_cross_function` | 释放点跨函数 | **栈帧跨函数** | 110 条里 **12 条**其实是 `use_fn` 自己调了释放助手 → 释放点在同一函数 | R11 用它筛"跨函数候选"，分母掺了 12 条不是跨函数的 |
| 2 | `facts.sites[kind=free].code` | 释放表达式 | **恒为 `None`**（`s2_2_facts.py:861` 硬编码） | 125 个 free 站点里 **116 个是 None** | R11/R12 早期所有"释放的是什么"的分析都是猜的；已由 `tools/backfill_free_code.py` 回填（109/125） |
| 3 | `key_facts.freed_ptr` | **被释放的指针** | **崩溃点的对象名**（`facts.entity.name`） | 79 条里只有 **12 条（15%）** 两者一致；例 `free(tr)` 而 `freed_ptr='n'`、`xmlFree(cur)` 而 `freed_ptr='buf'` | **零消费者**（s3 只读 `findings.reassigned_between`、agent prompt 不含 interpretation、`normalize_findings` 不读 `key_facts`），所以只污染人/agent 的阅读，不影响结论 |

**共同教训**：**光在报告里写不够，要在代码里就看见**——
`freed_ptr` 的两处写入点已加注释（写明 15% 与零消费者），
`code: None` 的写入点也加了注释（写明缺口与回填工具）。

## 限制 12 · `parse_freed_by` 的 `(\S+)` bug：修之前的"释放点"分析可能偏帧

`tools/backfill_free_code.py::parse_freed_by` 原来用 `(\S+)` 抓函数名，
而 ASan 报告里的函数名是**完整签名、含空格**（`WelsDec::DecreasePicBuff(WelsDec::TagWelsDecoderContext*, ...)`），
于是 `#1` 帧被**整帧丢掉**，只剩 `#2`。

**R12 抽验 10 条里 8 条受影响**（帧数差 1–6）。已修（`in\s+(.+?)\s+(/[^\s:]+):(\d+)`）。

**修之前得出的、需要打折的历史结论**：

| 轮次 | 结论 | 是否受影响 |
|---|---|:---:|
| R12 步骤 1 | "F6 包装调用 24 条" | ✅ **受影响**——实际**没有一条**是有名字的包装，是 `realloc`(8) / realloc 包装(5) / `delete`(3) / 间接调用(7) / 取错行(1) |
| R12 步骤 1 | "F4 裸指针 33 条"（初版） | ✅ 受影响（修后变 41 / 60） |
| R12 步骤 2 | 终版分布（F4 60 / F6 7 / F1 6 …） | ❌ 修之后算的 |
| R11 | 110 条的 A/B/C 分布 | ❌ 只依赖调用图方向，不依赖释放表达式 |

---

## 限制 13 · 守卫 1 的保守回退让"只清成员"的包装漏过（R15 已修）

`wrapper_frees_param()` 原来在被调函数**不在 worklist 里**时返回 `True`（"看不到源码就不排除"）。
worklist 只收调用图闭包内的函数，所以 `pixFreeData` / `xmlListClear` / `dwg_free_object_private`
这类**只清成员、不释放变量本身**的包装全部漏过，产生假阳性。

**R15 修法 A（一行）**：三处回退改成 `False`（"找不到源码就拒绝"），并加 `_WRAP_REJECT` 计数。

| 项目 | 修前站点 | 修后站点 | 挡掉的 | 与人工核实 |
|---|---:|---:|---|---|
| libredwg | 4 | **2** | `encode.c:1271`、`encode.c:1308` | ✅ 两条 R14/R15 都判假 |
| leptonica | 2 | **0** | `pix1.c:1665`、`pix4.c:2953` | ✅ R14 判两条全假 |
| libxml2 | 1 | **0** | `list.c:307` | ✅ R14 判假 |

**目标站点 `src/in_dxf.c:12284 → 12267` 活下来了**（它是 A/B 617 次命中的来源）。

**代价（已量化）**：`callee_not_in_worklist` 拒绝 **8（libredwg）/ 3（leptonica）/ 1（libxml2）**
= 共 12 次。这些被调函数都**在项目源码里**，只是不在 worklist。
**不做修法 B（补进可查集合）**——修法 A 的挡掉结果与人工核实 100% 吻合，
说明当前数据上没有误杀；等有具体漏检案例再说，不凭"可能有"去扩。

## 限制 14 · `generate` 是 LLM 生成，**重跑必然产出不同的算子**

同一份 `mutation_plan.json` 重跑 `generate`，`mutator.c` 从 `d7913b9e` 变成 `d256831b`（485 行 diff）。
R15 踩到过，已回滚。

**所以**：
- `mutator.c` 的 sha1 **只能引用你手上那一份**，不能靠"重跑一遍"复现；
- 要给 `mutator.json` / `verification.json` 加字段，**不能靠重跑 generate**，只能事后标注元数据
  （`mutator.c` 一字不动）；
- 任何"A/B 结果可复现"的说法，前提是**同一份 `mutator.c` 文件**。

## 限制 15 · 产品版本对照（避免"重跑得到不同配置且不知道为什么"）

| 产物 | 现在是什么 | 对应哪一版 |
|---|---|---|
| `projects/ARVO-42494732/v2/feature_pipeline.json` | **2 个站点**（`in_dxf.c:12284`、`in_dxf.c:12839`） | **R15 守卫修复后** |
| `projects/ARVO-42494732/v2/mutation_plan.json` | **1 site / 1 mutation / 权重 0.5 / total 1.0** | 同一版（逐字等于 R15 前那版） |
| `projects/ARVO-42494732/v2/mutator.c` | sha1 **`d7913b9e`** | **R9 生成**，`reps_r9_final` 用的就是它 |
| `reps_r9_final` | `default 0 / 1,102,847` vs `custom 617 / 640,359` | 上述 `mutator.c` |

**注意**：`build_mutation_plan` 是**按 action**（每个特征一个）建 mutation 的，**不是按所有站点**。
所以"`feature_pipeline` 有 2 站点、`mutation_plan` 只有 1 site"**不是不一致**——plan 只取 action 选中的那个。
`reps_r9_final` 当时用的 `feature_pipeline` 是 **4 站点**版，但 **action 选中的站点与现在完全相同**
（`12284 → 12267`），所以 plan / 算子 / A/B **全部不变**。

## 限制 16 · 站点人工核实台账：`docs/verified_sites.json`

**为什么**：这个项目反复栽在"看起来成立但没核实过"上（`free_cross_function` 的语义、
`code: None`、`freed_ptr`、R13 的 leptonica 落地）。**产物里必须能看出站点真假。**

**怎么用**：台账按 `(osv_id, file, free_line, use_line)` 匹配，判定三态
`true / false / uncertain`；**没核实过就是 `null`，不是 `false`**。
标记会沿 `feature_pipeline` → `mutation_plan` → `mutator.json` → `verification.json` 传播
（字段 `manually_verified` / `verified_verdict` / `verified_in`，外加 `site_verification` 汇总）。

**它**不是**过滤器**：代码里没有"判假就跳过"。自动排除是守卫的职责，台账只负责让人看见。

---

## 限制 17 · `repo_local` **不是 pin**（R16 已修，但影响过 R14/R15 的核实）

`fetch` 原来把 `ctx["repo_local"]` 设成**克隆的 HEAD**，而 CPG 是**按 pin 预建**的。
实测 3/4 个项目的克隆不在 pin 上：

| 项目 | pin | 克隆 HEAD | 一致？ |
|---|---|---|:---:|
| libredwg | `ff69eeda6658` | `ff69eeda6658` | ✅ |
| leptonica | `90ec70fd4322` | `5914a4330da2` | ❌ |
| libxml2 | `d4d1f3f33d6d` | `febeb5c91fff` | ❌ |
| igraph | `c83b6ecdc3fe` | `22dd6a8ee4c2` | ❌ |

**后果**：扫描器拿 HEAD 的源码去套 pin 的行号。实测同一行**完全不是同一段代码**：

| 项目 | R14 读到的（HEAD） | pin 上同一行 |
|---|---|---|
| leptonica `src/pix1.c:1665` | `pixFreeData(pix); pix->data = data;` | `if (!valid) return ERROR_INT("colormap is not valid"…)` |
| libxml2 `list.c:307` | `xmlListClear(l); xmlFree(l->sentinel);` | `lkNew = (xmlLinkPtr) xmlMalloc(sizeof(xmlLink))` |

**所以 R14/R15 对 leptonica / libxml2 的"逐条读源码核实"是在错版本上做的**，
台账里那 3 条已标 `invalid`。用 pin 源码重跑后，这两个项目 + igraph 的 **`原语` 都是 0** ——
那些站点在 pin 上**根本不存在**。

**修法**：`repo_local = ensure_src(repo, pin)`（按 commit 提取到独立目录），失败才退回克隆并**警告**。
**libredwg 不受影响**（克隆正好在 pin，提取内容逐字相同），站点 / plan / verify / sha1 全不变。

## 限制 18 · `extern "C"` 写在 `.c` 里会让 c2cpg **整个文件丢失**

igraph 的 harness `fuzzing/read_gml_fuzzer.c` 第 27 行是 `extern "C"`。
c2cpg 按 **C** 解析 `.c`，`extern "C"` 不是合法 C → 整个文件解析失败 → CPG 里只剩 `<global>`：

```
  igraph CPG dump 里，fuzzing/ 只有：
    fuzzing/read_gml_fuzzer.c   <global>   L1
  grep -c "LLVMFuzzerTestOneInput" cpg_dump.tsv → 0
```

**这就是 R13 记的"CPG 里没有 `LLVMFuzzerTestOneInput`（BFS 根缺失）"的真因**，
不是"harness 不在仓库"。两个不同 pin 都缺，说明是**系统性解析失败**，不是图过期。

**对照**：libredwg `extern int LLVMFuzzerTestOneInput(...)`（纯 C）✅；
libxml2 裸 `int LLVMFuzzerTestOneInput(...)` ✅；leptonica `.cc`（走 C++ 前端）✅。

**R16 实测：把这一处 `extern "C"` 换成注释后重建 CPG，igraph 的 `depth=2` 闭包从 0 → 40 个函数，
`worklist` 自检通过**（`src/io/gml.c:462 ✅ 已被覆盖`），**不需要 `--fault-anchor`**。

**但这不改变"没有第二个落地项目"的结论**：igraph 的 UAF 是**跨函数形态**，
`features` 扫出 **`原语 0`**（见限制 7）。

---

## 限制 25 · llm04 探测器不值得建：真实覆盖面只有 12.7%

> **⚠️ R20 修订**：本限制原文把"经字段的 25% 做不了"归因于"10,180 条断掉 MEMBER REF 边"。
> **那个因果是错的** —— 见**限制 29**。形态分布与"不值得建"的结论**不变**。

**这是 R19 的收口结论**，也是本项目"跨函数 UAF 形态"这条线走了 R11–R19 九轮之后的终点。

### 核实后的形态分布（60 条 F4 裸指针，逐条读过 pin 源码）

| 类别 | 条数 | 占 F4 | 占 110 | 数据流能做？ | 为什么 |
|---|---:|---:|---:|---|
| **同名**（释放的裸指针在同一函数里被读） | **14** | **23.3%** | **12.7%** | ✅ | — |
| 名字复用（不同函数里的同名变量） | 2 | 3.3% | 1.8% | ❌ | 值经字段/参数传来，不是同一变量 |
| 顺序相反（`use` 先于 `free`） | 2 | 3.3% | 1.8% | ❌ | 根本不是 UAF |
| **释放根不在使用行**（须经别名/字段/参数） | 41 | 68.3% | 37.3% | ❌ | 见下两行 |
| ⤷ 其中**别名** | ~34 | ~57% | ~31% | ❌ | `reachableByFlows` 是**值流**，不做别名分析 |
| ⤷ 其中**经结构体字段** | ~15 | ~25% | ~14% | ❌ | CPG 有 **10,180 条断掉的 `MEMBER` REF 边** |
| 判不出（取不到使用行源码） | 1 | 1.7% | 0.9% | — | `facts` 噪声 |
| **F1 结构体字段**（另一类） | 6 | — | 5.5% | ❌ | 同上，字段级断边 |

### 为什么"不值得建"——不是覆盖面低，是**解锁不了任何项目**

按"10–30% → 边际，看能不能解锁至少一个新项目"的阈值判：

| 项目 | 它的 UAF 属于哪一类 | llm04 能落地吗 |
|---|---|---|
| **igraph** `ARVO-42491546` | `t` 被 `igraph_Free(t)` → **别名** `v` 读 `v->end` | ❌ 别名 |
| **igraph** `ARVO-42491511` | 沿 `finally_stack` 数组 + 函数指针销毁 | ❌ 间接调用 |
| **libxml2** `ARVO-42486565` | **经结构体字段**（`ctxt->incTab[nr]->ref`） | ❌ 字段级断边 |
| **leptonica** `ARVO-42488049` / `42488833` | `pix->refcount` —— **顺序相反**（B 类） | ❌ 不是同一实例的 UAF |

**→ 三个候选项目里没有一个能靠 llm04 落地。**

### 与限制 7 串起来

- **限制 7**（R11/R12）：跨函数扫描器支持的形态在 110 条真实 UAF 里**占 0**；
- **限制 25**（R19）：换成 **Joern 的跨过程数据流**，也只能覆盖 **12.7%**。

**两次都是同一个结论：这些 UAF 的"释放点"和"使用点"之间隔的不是数据流，是别名 / 字段 / 参数。
不是工具选错了，是这类 UAF 的形态本身就不适合静态数据流。**

## 限制 26 · `facts` 的四个噪声（做形态统计前必须知道）

| 噪声 | 例子 | 影响 |
|---|---|---|
| `free_line` 指向的**不是 free 语句** | `ARVO-42479359` 的"释放行"是一个 `}` | 取到的"释放表达式"是错的 |
| `free_code` 为空且 `free_file` 的 raw 取不到 | `ARVO-42488049`、`ARVO-42488833`、`ARVO-42494732` | "释放"一行取不到 |
| 同一 UAF 有**多条报告**（`ARVO-*` 与 `OSV-*`） | `ARVO-42494732` / `OSV-2021-543`、`ARVO-42500437` / `OSV-2021-1157` | **110 条里有重复样本，形态统计会重复计数** |
| **`facts.crash.code` 是 `|` 分隔的候选子表达式集合，不是一行源码** | 全部 121 条 | 拿它当源码用必错（R19 起步时我就错了，把 `ARVO-372547409` 判成"别名"） |

## 限制 27 · 数据流的"第一条路径"不是稳定性质，回归判据要改成"是否存在"

R19 回归实测：同一份图、同一个查询，**三次运行都是 `flows=67`，但第一条路径分别是
`L12291:pair`、`L12291:pair`、`L12284:pair`** —— 引擎的遍历顺序不稳定。

**所以回归判据必须是"是否存在一条 源 X → 汇 Y 的路径"**（`has_expected_path`），
**不能是"第一条路径等于 …"**。R17 报告里那条判据是错的。
---

## 限制 28 · CALL→MEMBER 的 REF 边 95%+ 建不起来（`c2cpg` 类型解析失败，R20）

**实测**（断边**不在图里**，只能从 Joern **加载日志**数；
⚠️ 解析时注意 `stderr` 合并进 `stdout` 会让行首错位，要用 `in` 不能用 `startswith`，
R20 第一版因此全解析成 `None`）：

| CPG | MEMBER 节点 | 成功 CALL→MEMBER | 断掉 | 断占比 |
|---|---:|---:|---:|---:|
| `libxml2_d4d1f3f33d6d` | 1,982 | 73 | 10,180 | **99.29%** |
| `libredwg_ff69eeda6658` | 7,349 | 289 | **113,022** | **99.74%** |
| `leptonica_90ec70fd4322` | 1,033 | 71 | 5,872 | **98.81%** |
| `igraph_c83b6ecdc3fe` | 2,709 | 2,197 | 46,327 | **95.47%** |

**"其它型断边"四个图全是 0** —— 断边**全部**是 CALL→MEMBER 这一类。

**根因：类型解析失败，不是设计行为。**
- 断边的目标键是 `<typedef名>.<字段>`（如 `xmlParserCtxtPtr.input`）；
- 而 MEMBER 节点只有裸 `name`（`input`），**没有 `fullName` / `typeFullName` 属性** → 查不到；
- 另外大量目标名是 `ANY.<字段>`（`ANY.cur` 858 条）—— 类型**根本没推出来**（没做预处理器）。
- **MEMBER 节点是建了的**（1,982 个，名字都对），**只有引用链接失败** → 不是设计行为。

**不能修**：typedef vs struct 名、以及 `ANY`，都在 `c2cpg` 前端里，脚本层改不了。

**但它不影响变量值流** —— libredwg 99.74% 断边仍连出 67 条正确流。
**它只影响"这个字段属于哪个结构体"这类类型查询。**

## 限制 29 · 字段访问的三种形态，只有 (a) 验证过

| 形态 | 例子 | 数据流能做吗 | 证据 |
|---|---|:---:|---|
| **(a) 释放变量、读它自己的字段** | `free(pair)` → `pair->code` | ✅ | libredwg 67 条流里 **57 条的中间跳含 `->`**，字段名只有 `code`/`value`（都是 `pair` 自己的） |
| **(b) 值经字段中转** | `free(cur)` → 存进 `ctxt->incTab[nr]->ref` → 再取出读 | ❌（**未定因**） | `ARVO-42486565` 卡在 **`xinclude.c` 覆盖率 0%**，不是断边 |
| **(c) 释放的就是字段** | `free(obj->buf)` → 别处读 `obj->buf` | **未测** | — |

**关键**：数据流能"穿过" `pair->code` 这个节点，靠的是**语法上的字段访问表达式**，
**不需要 CALL→MEMBER 的 REF 边**。所以"断边"和"能不能穿过字段访问"是**两件不同的事**。

**⚠️ 这条推翻了限制 25 原来的因果**（原文写"经字段的 25% 做不了，因为 10,180 条断边"）。
**正确的因果**：经字段的 UAF 能不能做，取决于
① **那段代码在不在图里**（覆盖率，限制 19/21）；
② **值是不是经堆/字段中转**（那需要 points-to 分析，不是值流）。
---

## 限制 30 · 守卫 1 的**范畴错误**：free 原语被当成"包装函数"

`free(x)` / `LEPT_FREE(x)` / `xmlFree(x)` **本身就是释放**，但它们也被当成"包装函数"
送进守卫 1（`wrapper_frees_param`）—— 进被调函数体里看 `free(<形参>)` 在不在。
R15 又把守卫 1 的回退改成"找不到源码就拒绝"，于是：

**查不到源码 → 拒绝 → 所有直接释放的站点被丢掉。**

**修法（窄）**：只有当被调函数**不在项目里**（worklist / CPG 全部方法 / 源码树都查不到）
**且名字像 free 原语**（`*_free` / `*Free` / `*FREE` / `free` / `kfree`）时才跳过守卫 1。
项目里的 `dwg_free_header_vars` 这种**在**项目里，照旧走守卫 1，不会被跳过。

**效果**：libredwg 原语 2→3、**leptonica 0→1**。

## 限制 31 · R15 的保守策略**没有误杀**（现在有证据）

R21 把守卫 1 的"读源码范围"从 worklist 扩到 **CPG 全部方法 + pin 源码树**
（worklist 162/665/246 vs CPG 全部方法 5129/5309/3709，差 10–30 倍）：

| 项目 | R15 拒绝 | R21 拒绝 |
|---|---:|---:|
| libredwg | 8 | **1** |
| leptonica | 3 | **2** |
| libxml2 | 1 | **1** |
| 合计 | **12** | **4** |

**解开的那 7 个函数，进入函数体后都正确地返回了 `False`**（确实只释放成员，不释放变量本身），
**一个新站点都没多**。**→ R15 的"宁可漏不可错"没有误杀真站点。**

## 限制 32 · `blocks()` 的两个真 bug（R21 修，影响所有 K&R 项目）

`pipeline/s5_6_lib.py::blocks()` 是 `flow()` / `step()` / `loop_back` 的基础。
R21 为加 if/else 互斥守卫去用它，发现两处**假设了特定的代码风格**：

| # | bug | 证据 | 影响 |
|---|---|---|---|
| 1 | **假设 Allman 风格**（`{` 独占一行），永远看**上一行**当头部 | leptonica `pix4.c:3050` 是 K&R 的 `if (array) {` → 整块标成 `plain` | **所有 K&R 项目的 CFG 都是错的** —— 不只是守卫失效，`loop_back` 也全错 |
| 2 | **`} else {` 判不出来** | `pix4.c:3056` = `} else {  /* L_SCAN_VERTICAL */`，`head` 是 `} else`，不匹配 `^else` | else 块丢失 |

**修完后 leptonica 的 `loop_back` 站点从 0 变成 6** —— 说明之前**完全没在扫**。

**又发现 `loop_back` 的一个 bug**：重赋值检查原来只覆盖「free → 回边」，
**没覆盖下一轮从循环头到使用点**。`maze.c:459→403` 就是：459 释放 `elp`，下一轮 **402** 重新赋值，
403 才用。修完 6 个新站点里 5 个被挡掉。

**剩下的 1 个（`pix4.c:3065→3064`）仍是假阳性**：回边是**内层**循环的，
重新赋值在**外层**循环头 —— 窄范围覆盖不到。**要彻底解决需要跨嵌套循环的路径敏感分析**（已列为不做）。

## 限制 33 · 同函数字段形态**不存在**（收口干净）

R19 分类的 6 条 F1（经字段）逐条核 `free_file:line` vs `crash.site.file:line`（两个字段分开取）：

| osv | 释放文件:行 | 使用文件:行 | 同文件？ |
|---|---|---|---|
| `ARVO-42479533` | `decoder/ih264d_utils.c:2252` | `common/x86/ih264_inter_pred_luma_*:3683` | ❌ |
| `ARVO-42481163` | `src/ua_types_encoding_json.c:2994` | `src/ua_types_encoding_json.c:140` | ❌ |
| `ARVO-42484562` | `xmlreader.c:311` | `error.c:501` | ❌ |
| `ARVO-42486724` | `src/server/ua_server_config.c:58` | `plugins/ua_accesscontrol_default.c:447` | ❌ |
| `OSV-2020-370` | `decoder/ih264d_utils.c:2265` | `common/x86/ih264_inter_pred_luma_*:3683` | ❌ |
| `OSV-2023-342` | `decoder/ih264d_utils.c:2337` | `common/x86/ih264_inter_pred_luma_*:650` | ❌ |

**0 / 6 同函数。** 所以"同函数字段形态"在真实 UAF 里**不存在** ——
**不是"有同函数的但扫描器扫不到"**，是这一类本来就没有。
（注意 `ARVO-42481163` 和 `ARVO-42484562` 的**文件名相同/不同**要按规范化后的仓库相对路径比，
不能只看 basename。）

**→ 同函数这一类的天花板就是"同函数 + 裸指针" = 12.7%，收口。**
---

## 限制 34 · `blocks()` 的 bug 影响面：**4/5 个项目是 K&R，之前 CFG 全错**

R21 修了 `blocks()` 的两个 bug（假设 Allman、`} else {`）。R22 量了影响面
（统计 worklist 文件里 `if/for/while/switch` 头部**同行带 `{`** 的比例）：

| 项目 | K&R 比例 | 受影响 |
|---|---:|---|
| **libxml2** | **100.0%** | ❌ |
| gpac | 99.9% | ❌ |
| **igraph** | **98.5%** | ❌ |
| **leptonica** | **97.9%** | ❌ |
| **libredwg** | **0.4%** | ✅ **不受影响** |

**libredwg 是唯一 GNU 风格的项目 —— 这就是这个 bug 藏了二十轮没被发现的原因。**

## 限制 35 · "没有第二个落地项目" **是真的**（用验证过的 CFG 重扫确认）

R22 先用 **9 个回归测试 + 变异检验（退回修复 → 6/9 变红）** 证明 `blocks()` 修对了，
再重扫三个候选：

| 项目 | 修复前站点 | 修复后站点 | **核实为真** |
|---|---:|---:|---:|
| leptonica | 1 | 1 | **0** |
| libxml2 | 0 | 0 | **0** |
| igraph | 0 | 0 | **0** |
| **libredwg** | 2 | 2 | **1**（`12284→12267`） |

**→ 结论成立，而且现在是在正确的 CFG 上得出的。**

**历史结论要"标注"而不是"推翻"**：R13/R16 说 leptonica/libxml2 站点归 0，
当时是"**CFG 坏了没扫**"；R22 是"**CFG 好了，扫了，确实没有真站点**"。**后者才是证据。**

## 限制 36 · ⚠️ gpac 的一个真站点被守卫误杀了（待查）

R7 核过真的 gpac `gf_free(ar)` → `ar->type`（`ARVO-42518828`），
在 R21/R22 加了几道守卫之后 **站点消失了**（1 → 0）。

**它是 R7 人工核实过的真站点。** 可能是被
`use is same` / `if/else 互斥` / `exit` 其中一道**误杀**。

**gpac 靠 `--fault-anchor`，不是候选项目，所以不影响"没有第二个项目"这个结论。
但这是一次真实的误杀，必须单独查** —— 它说明新加的守卫至少有一道**过严**。
---

# 二、当前状态（2026-11-04）

## 门禁

| 项 | 状态 |
|---|---|
| stage5 生成门禁（静态 + 行为 5 项） | PASS |
| `s5_verify` V1–V4 | 全 **pass**，`overall = pass` |
| `pytest tests -q` | **4 passed** |

## 六层产物与算子（R8 实测）

| 项 | 值 |
|---|---|
| 六层产物 | **6/6 齐** |
| `found` | **1/5**（只有 `uaf-llm01`；R8 收紧判据后另 4 个是 `not_found`） |
| 站点 | `src/in_dxf.c:12284 → 12267`，`var=pair`，`branch=DXF`（`via: function dxf_objects_read @ distance 1`） |
| plan | 1 site / 1 mutation / `weight 0.5` / `total 1.0` / `status=ready` |
| 算子 | **294 行**，`r = Seed % 1000; if (r < 500) default; else mutate_a001`（**50%**） |
| 生成门禁 5 道 | 全过 |
| V1–V4 | 全 **pass**（V4 真回放 `in_dxf.c:12267`） |
| `fault_anchor_enabled` | **False**（libredwg 不依赖锚点） |
| 能力剖面（`diversity.c`，1000 seed） | 含 OBJECTS **500/500**；剥段 **500/500**；DWG **0** |

**gpac（ARVO-42518828）**：`found 1/5`（`gf_odf_vvc_cfg_read_bs:1400 → 1404`，`branch=ISOM`），
但 **`fault_anchor_enabled = True`**、`fault_fn_in_closure = False`——**喂过答案的**。

**已修正的两个潜伏 bug（R8）**：

1. `mutation_plan` 的**站点归并只并了站点、没并权重**：4 个特征指向同一站点时
   `weight` 取 `rows[0]` = 0.125（不是 4×0.125=0.5），`total` 只有 **0.625**。
   只有"多特征同站点"才触发，R7 之前从未碰到。已修 → `1×0.5 = 1.0`。
2. `emit_rules` 会把**上次运行残留**的 `feature_*.json` 当成新结果（`uaf-llm04` 曾"复活"一次）。
   已修为失败时写 sidecar。

## 路径 B（剥段种子，default 够不着的场景）—— **唯一可引用的 A/B**

> **数据来源：`reps_r9_final`（2026-11-04 重跑，用当前二进制 `a416b44d`，算子 294 行）**。
> R6 的 `reps_pathB_r3`（731 / 508,682）是**历史证据**，它测的是 440 行那版算子；
> 两者同量级（见下"两次测量对照"），结论不变。

| rep | default 命中 / execs | custom 命中 / execs |
|---|---|---|
| rep01 | **0** / 211,098 | 153 / 130,151 |
| rep02 | **0** / 213,346 | 187 / 139,926 |
| rep03 | **0** / 206,628 | 133 / 63,389 |
| rep04 | **0** / 200,441 | 122 / 106,570 |
| rep05 | **0** / 216,725 | 136 / 68,646 |
| **合并** | **0 / 1,048,238** | **731 / 508,682** |

- **率比无定义**（default 命中 0）；按原始计数报。
- 覆盖率比 custom/default：中位 **0.857**（范围 0.783–0.940）。
- default 的 3 个崩溃**不是目标**（是 `heap-buffer-overflow @ in_dxf.c:11947`）；
  custom 的 731 个**全部**是 `heap-use-after-free @ in_dxf.c:12267`。
- **旧的 `RR = 375.9` 已作废**（5 个 rep 是同一确定性 run 的重放：675 个崩溃文件只有 136 个唯一 sha1）。

### 两次测量对照（同一设计、不同二进制）

| | `reps_r9_final`（当前，294 行，`a416b44d`） | `reps_pathB_r3`（历史，440 行） |
|---|---|---|
| default 命中 / execs | **0 / 1,102,847** | 0 / 1,048,238 |
| custom 命中 / execs | **617 / 640,359** | 731 / 508,682 |
| custom 率 /100k | 96.35 | 143.70 |
| execs 比（custom/default） | 0.581 | 0.485 |
| **每 100k exec 的边覆盖比**（中位） | **2.449** | 1.699 |
| 独立性（崩溃 sha1 唯一数 / 总数） | **617 / 617** | 731 / 731 |
| 两两交集 | **全 0** | 全 0 |
| 5 个 rep 的 `-seed` | **1/2/3/4/5**（逐 rep 变化） | 1/2/3/4/5 |

**结论：同量级，`731 vs 0` 钉死。** default 两次都是 **0** 命中。

## 已作废，不要再提

| 项 | 作废理由 |
|---|---|
| `RR = 375.9`（路径 B 旧数据） | 5 个 rep 非独立（见上） |
| `RR = 0.954`（1A 旧值） | 含一次 `exec/s` 塌到 9 的损坏运行；复跑是 1.131 |
| 目标触发密度 `1.33×`（三配置对比） | 单次运行；配置 A/B 日志已被 `rm -rf`；同一 default 配置波动 5.6 倍 |
| **路径 C（去掉 DWG 种子）** | 1B 实测 **RR = 0.441、CI [0.28, 0.69] 不含 1**，custom 显著更差，配对胜出 **0/5** |

---

# 三、怎么读

| 你的目的 | 读 |
|---|---|
| **项目布局、五阶段、stage5 四阶段六文件、六层产物、判据体系、门禁、实验设施** | **`docs/ARCHITECTURE.md`**（R8 重建，2026-11-04） |
| 上一轮 Q1–Q12 完整调查 | `git show b78260c9:docs/INVESTIGATION.md`（717 行；删除发生在 `013c0307`） |
| 本轮的验真报告 | `docs/runs/R4_PHASE_A.md` |
| 本轮的第二个项目筛选 | `docs/runs/R4_PHASE_B.md` |
| 人工介入台账 | `INTERVENTIONS.md` |
| 生成 pipeline 规格 | `pipeline/README.md`（最新）；`git show b78260c9:docs/GENERATION_PIPELINE.md`（257 行；删除发生在 `013c0307`） |
| 实验口径 | `projects/ARVO-42494732/v2/experiment/README.md` + `REPS.md`（两份都带"数字已过期"banner） |

---

# 四、产物位置

```
mutator_create/
├── pipeline/                     生成 pipeline：11 个 .py + 1 个 .sh
│   ├── s1_reproduce.sh
│   ├── s2_1_lib_cpg.py  s2_2_facts.py  s2_3_interpretation.py
│   ├── s3_extract_patterns.py  s4_abstract_features.py
│   └── s5_1_main.py  s5_2_prepare.py  s5_3_audit.py  s5_4_analyze.py  s5_5_build.py  s5_6_lib.py
├── artifacts/                    facts/ interpretation/ reproduced_crashes.jsonl
├── outputs/                      stage3/{uaf,hbo,stack,global}/  stage4/uaf/
├── projects/ARVO-42494732/
│   ├── seeds/                    6 DXF + 2 DWG（实验前会被临时换成剥段种子，跑完必须移回）
│   ├── source/ harness/          prepare 抓的源码与 fuzz target
│   └── v2/
│       ├── mutator.c             构造型算子（440 行，含 construct_objects_section()）
│       ├── mutation_plan.json    v5：operation=ensure_record_structure + construct
│       ├── target_surface.json / candidate_findings.json / feature_pipeline.json
│       ├── verification.json     V1–V4 全 pass
│       └── experiment/
│           ├── run_reps.sh       ⚠️ 每次 rm -rf reps/；-seed=$((SEED_BASE + r))
│           ├── gate_seeds/       4 个剥段种子（门禁固件，不是实验语料）
│           ├── reps_r9_final/    ★★ 唯一可引用的 A/B（当前二进制 a416b44d，617 个 crash/）
│           ├── reps_pathB_r3/    ★ 历史 A/B（440 行那版，731 个 crash/），同量级，别删
│           └── reps_after_pathB/ 回归证据（RR 1.011，reps 非独立）
│       （reps_n5_r1 / n5_r2 / dxfonly / reps_pathB / reps_pathB_r2 已删，
│         回收 40.2 M；它们的 summary.json 在 docs/runs/reps_summaries/）
├── tests/test_stage5_v2.py       契约测试（4 passed）
└── INTERVENTIONS.md
```

---

# 五、纪律

1. **跑完任何 `run_reps.sh` 立刻 `mv reps reps_<tag>`**，分析只针对快照。
   跑前 `docker exec libredwg-exp ps aux | grep [l]lvmfuzz` 确认无残留（`Z`/defunct 无害）。
2. 磁盘紧张：**只 `mv` 不 `cp`**；`**/corpus/` 与 `**/crash/` 已在 `.gitignore` 里。
3. 不动 V1 基线：顶层 `mutator.c`、`fuzz_exp/`、`fuzz_exp2/`。
4. 改任何代码后跑 `python3 -m pytest tests -q`（在仓库根；应 **4 passed**）。
5. agent 自己实现，不许 shell 出去调 `claude` 之类的 CLI agent（调项目自己的 DeepSeek 管线可以）。
6. `HANDOFF/00–05` + `PROMPT.md` 是用户自己删的，**不要恢复、不要写补丁**。

---

# 六、下一步（优先级）

| 优先级 | 内容 | 依据 |
|---|---|---|
| **P1** | 决定 Phase B 的方向：① 跑 `libxml2` 的 2 条同项目内 holdout（能过预筛、站点是新的）② 或明确接受"放宽预筛"并记为禁止类改动 | 限制 5 |
| P2 | 降构造频率（段不存在时只以 1/4 概率构造），把路径 B 的覆盖率比从 0.857 拉回 ≥0.95 | 限制 3 |
| P3 | 权重按输入格式分配（DWG 仍无策略，49% 语料只有 default） | 限制 3 |
| P4 | 补算 `cross_frame_count`；把 `reassigned_between` 从 `interpretation` 传进 stage3 | 旧调查 Q7 |
| P5 | 清理其余非独立的 `reps_*` 快照（磁盘） | 纪律 2 |

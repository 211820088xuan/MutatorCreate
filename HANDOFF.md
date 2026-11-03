# mutator_create 交接（入口）

> 目标：从已复现的崩溃归纳**同一类型崩溃的共性特征**，把特征落到具体项目的**真实代码站点**，
> 生成能提高目标崩溃触发概率的 custom mutator。
> **验收标准只有一条**：custom vs default 的 A/B 对照里 custom 更好。不是"找到新 bug"，不是"覆盖率涨了"。

---

# 〇、这项工作证明了什么 / 没证明什么

## 证明了的（每条附数据）

1. **从一个已知崩溃推导触发结构、生成定向算子，在 default 够不到的场景下有效。**
   `reps_pathB_r3`（剥段种子、300 s × 5 rep、**5 个 rep 相互独立**：731 个崩溃文件
   731 个唯一 sha1、两两交集全 0）：
   **`default 0 / 1,048,238 execs`** vs **`custom 731 / 508,682 execs`**。
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
2. **LLM 归纳不优于手写规则。** 见限制 2 与 `docs/runs/R8_REPORT.md` 步骤 2 的三层对照：
   词表紧 → 4 条 `expressible: false`；词表松 → 3 条恒真；加了可证伪约束后 5 条都具体了，
   但**命中集合与 llm01 完全相同**（没有一条找到 llm01 找不到的站点）。
   而且唯一一处明显更差的是 `uaf-llm05`：手工版 `is_link_read: true` 抓住了"沿链遍历"这个
   定义性特征，LLM 版把它丢了。
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
| 路径 B（剥段种子 300 s） | 1,048,238 | 508,682 | **48.5%** | `reps_pathB_r3`，**独立** |
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
**目前唯一独立的 n=5 数据是 `reps_pathB_r3`。**

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

## 限制 7 · 跨函数扫描 0 命中，能力未兑现

R7 步骤 4 加了跨函数形态（`use_kind = cross_function`）：
A 里 `free(V)` → 之后调用 `G(V)` → G 里读形参。**行号顺序证明释放先于使用，实参证明同一对象。**
六道守卫对着 R4 记的假阳性逐条设（`wrapper_frees_param` 不算释放 / 释放后置空 / 释放后重赋值 /
实参必须整个是 V / 被调函数是释放助手 / `#if 0` 死代码）。

| 项目 | 跨函数站点 | 核对结果 |
|---|---:|---|
| libredwg | 第一版 **15** → 加守卫 **6** → 再补守卫 **0** | 三轮逐个人工核对，全部假阳性（与 R4 独立结论一致） |
| gpac | 0 | — |

**0 命中既可能是"确实没有"，也可能是"守卫过严"——目前分不开。**
而且只支持"实参传递"一种形态；**结构体字段、全局变量、回调/函数指针**都没做，
而真实项目里的"跨函数"大量走这三种。

## 限制 8 · LLM 归纳没有正面证据（R8 收紧后仍然没有）

R8 给判据加了**可证伪性硬约束**（每个合取分支至少一个字段是真子集；写 `any` 或把整个词表
列上 = 恒真 = 拒绝），重跑 stage4，5 条判据**全部产出且全部具体**。
但三层对照的结论是：

| 对照 | 结果 |
|---|---|
| vs R7（恒真版） | 2 条从恒真变具体（`llm02` 的 `any/any`、`llm03` 的 4×4 全集都被拒了） |
| vs R5 手工版 | **3 胜 1 负 1 平**：`llm02` 更具体（4 个字段 vs 1 个）、`llm03/llm04` 从 `name_regex` 变**结构判据**；**`llm05` 输了**（丢了 `is_link_read:true` 这个定义性特征）；`llm01` 互有胜负 |
| **libredwg 实际命中** | **仍然只有 `llm01` 命中那 4 个站点**，`llm02/03/04/05` 全部 0 |

**→ 判据层的所有改进（从名单到结构、从紧词表到松词表再收紧）都没有带来新的落地。**

另有一个**可证伪性校验的漏洞**：`llm02`/`llm03` 判据里的 `reassigned_between: false`
是**真空约束**——`scan_sites()` 产出的站点**恒为 false**（构造时就过滤了重赋值），
所以它排除不了任何站点。校验数的是"字段写了真子集"，不是"这个子集能真的排除站点"。

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

## 路径 B（剥段种子，default 够不着的场景）—— 本轮唯一可引用的 A/B

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
| 上一轮 Q1–Q12 完整调查 | git 历史里的 `docs/INVESTIGATION.md` |
| 本轮的验真报告 | `docs/runs/R4_PHASE_A.md` |
| 本轮的第二个项目筛选 | `docs/runs/R4_PHASE_B.md` |
| 人工介入台账 | `INTERVENTIONS.md` |
| 生成 pipeline 规格 | `pipeline/README.md`（最新）；`docs/GENERATION_PIPELINE.md`（git 历史里） |
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
│           ├── reps_pathB_r3/    ★ 唯一独立的 n=5 数据
│           └── reps_*/           其余各组（非独立，仅作历史）
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

# R15 报告

日期：2026-11-06
本轮两件事：**修守卫 1**（先试最便宜的修法 A）、**给站点加"是否经人工核实"标记**。

> 范围界定（用户口径）：**主结果完好** —— `reps_r9_final` 的
> `default 0 / 1,102,847` vs `custom 617 / 640,359` 用的是 libredwg 那个经 R4/R5
> 两轮人工核实的真站点，而且 617 次命中**全部**是 `heap-use-after-free @ in_dxf.c:12267`。
> **受影响的只有 R13 那句**"`uaf-llm01` 在两个项目落地了"。

---

## 步骤 1 · 修守卫 1（修法 A：找不到源码就拒绝）

### 改了什么

`wrapper_frees_param()` 的三处回退从 `return True` 改成 `return False`，并加计数：

| 回退点 | 改前 | 改后 | 计数键 |
|---|---|---|---|
| `f = funcs_by_name.get(callee)` 为空 | `True` | **`False`** | `callee_not_in_worklist` |
| 有函数但 `src_cache` 里没源码 | `True` | **`False`** | `callee_source_unavailable` |
| 形参解析不出来 | `True` | **`False`** | `callee_param_unparsable` |

新增 `_WRAP_REJECT` 计数器——**"被拒了多少"是修法 A 的代价，必须能报出来**，不能静默。

### 验收 1：目标站点还在吗 —— **在** ✅

```
  found 1/5；权重 default 0.5 + 1×0.5 = 1.0
  站点数: 2
    dwg_read_dxf:12839→12842 (same_path)
    dxf_objects_read:12284→12267 (loop_back)      ← 目标，还在
  action.site: src/in_dxf.c 12284 → 12267  var=pair  branch=DXF
```

**修法 A 没有杀掉目标站点 → 不需要步骤 1b。** ✅

### 验收 2–4：三个项目的站点数变化

| 项目 | 修前站点数 | 修后站点数 | 被挡掉的是哪几条 | 与 R14 人工核实的对照 |
|---|---:|---:|---|---|
| **libredwg** | 4 | **2** | `encode_unknown_as_dummy:1271→1272`、`encode_unknown_as_dummy:1308→1313` | ✅ `1308` 是 R14 **确认的假阳性**（`dwg_free_object_private` 不释放 `obj`）；`1271` 是"可能真"（见下） |
| **leptonica** | 2 | **0** | `pixSetColormap:1665→1666`、`pixDisplayColorArray:2942→2953` | ✅ R14 核实**两条全假**（`pixFreeData` 只释放 `pix->data`；`if/else` 互斥） |
| **libxml2** | 1 | **0** | `list.c:307→308` | ✅ R14 核实**假**（`xmlListClear(l)` 清链表内容，不释放 `l`） |

**结论：修法 A 的挡掉结果与 R14 的人工核实完全一致**——该挡的全挡了，目标站点留住了。

**`leptonica` 和 `libxml2` 现在 `found 0/5`**（站点从 2/1 掉到 0）。
这是**修正后的正确结果**——它们之前的 `found 1/5` 依赖的是假阳性站点。

### 关于被挡掉的 `encode_unknown_as_dummy:1271→1272`

R14 标的是"◐ 可能真"（`dwg_free_object_private(obj)` 之后 `free(obj->unknown_bits)`）。
再看一眼 `src/free.c:884` 的 `dwg_free_object_private`：它按 `obj->type` 走 `switch`，
调 `dwg_free_<TYPE>_private(dat, dat, dat, obj)` —— **释放的是类型相关的私有数据**。
`unknown_bits` 是 `Dwg_Object` 的**公共字段**，不在这些 `_private` 函数的职责里。

**所以 `1271→1272` 也是假阳性**（`free(obj->unknown_bits)` 在 `dwg_free_object_private` 之后是正常的）。
→ **修法 A 挡掉它是对的。**

### 验收 5：修法 A 的代价（被拒计数）

| 项目 | `callee_not_in_worklist` | 其它 |
|---|---:|---:|
| libredwg | **8** | 0 |
| leptonica | **3** | 0 |
| libxml2 | **1** | 0 |

**共 12 次"因为被调函数不在 worklist 而拒绝"。** 这是修法 A 的代价：
这 12 个 free 调用所在的站点被整条丢掉了——其中**可能有真站点**，本轮无法区分。

**要不要做修法 B（把被 free 家族调用到的函数补进可查集合）？**
它们本来就在**项目源码**里，只是不在 worklist（worklist 只收调用图闭包内的函数）。
补进去的成本是"解析更多源码"，**不需要重跑 Joern**。**等确认。**

### ⚠️ 一个必须提的连带影响：libredwg 的 `plan` 现在会变

站点数 4 → 2 之后，如果重跑 `plan`，`by_site` 会得到 **2 个 mutation**（不是 1 个），
权重变成 `default 0.5 + 2 × 0.25 = 1.0`。

**本轮没有重跑 `plan` / `generate` / `verify`**（步骤 1 只要求报站点数，且铁律要求"不重跑 A/B"）。
所以现在 `projects/ARVO-42494732/v2/mutation_plan.json` 与 `feature_pipeline.json`
**是新旧不一致的**（plan 还是 1 site 那版）。

**这也是 `reps_r9_final` 能继续引用的原因**：A/B 用的是**旧算子**（1 site），
`mutator.c` sha1 仍是 `d7913b9e`。**一旦重跑 plan/generate，那个组合就不再成立。**

→ **要不要用它重跑 libredwg 的 plan/generate（从而得到 2 策略算子）？这是另一个决定，等确认。**

### ⏸ 停止点：等用户确认

| 你要的 | 结果 |
|---|---|
| 1. 目标站点 `12284 → 12267` 还在吗 | ✅ **在** |
| 2. libredwg 站点数 / 挡掉哪几条 | **4 → 2**；挡掉 `1271`、`1308`（`1308` 是 R14 确认假；`1271` 经复核也是假） |
| 3. leptonica 站点数 | **2 → 0** ✅（与 R14 核实一致） |
| 4. libxml2 站点数 | **1 → 0** ✅（与 R14 核实一致） |
| 5. 被拒计数 | `callee_not_in_worklist`：libredwg 8 / leptonica 3 / libxml2 1 |
| pytest | ✅ 26 passed |

**三个需要你定的**：
1. **要不要做修法 B**（把被 free 家族调用的函数补进可查源码集合，找回那 12 次拒绝里可能有的真站点）？
2. **要不要重跑 libredwg 的 plan/generate**（会变成 2 策略算子，但 `reps_r9_final` 的引用组合就失效了）？
3. 确认后进**步骤 2**（站点核实标记）。

---

## 步骤 2 · 站点人工核实标记

### 台账：`docs/verified_sites.json`

**8 条**，每条都是逐行读过源码的判定。匹配键 `(osv_id, file, free_line, use_line)`：

| # | 项目 | 文件:行 | 判定 | 依据 | 核实轮次 |
|---|---|---|---|---|---|
| 1 | libredwg | `src/in_dxf.c:12284 → 12267` | **真** | `dxf_free_pair(pair)` 后经循环回边读 `pair->code` | **R4 / R5 / R15** |
| 2 | libredwg | `src/in_dxf.c:12839 → 12842` | **存疑** | 释放后 `if (pair != NULL && pair->code …)`，**未确认 `dxf_free_pair` 是否置空** | R14 |
| 3 | libredwg | `src/encode.c:1271 → 1272` | **假** | `dwg_free_object_private(obj)`（`free.c:884`）按 `obj->type` 走 `switch` 释放**类型私有数据**；`unknown_bits` 是公共字段，不在其职责内 | R14 / **R15 复核** |
| 4 | libredwg | `src/encode.c:1308 → 1313` | **假** | 同上，不释放 `obj`；`obj->type = …` 是往活对象写字段 | R14 |
| 5 | leptonica | `src/pix1.c:1665 → 1666` | **假** | `pixFreeData(pix)`（`pix1.c:1711`）释放的是 `pix->data`，不释放 `pix` | R14 |
| 6 | leptonica | `src/pix4.c:2942 → 2953` | **假** | `if (array) {…LEPT_FREE(array);} else {…array[j]…}` —— **if/else 互斥** | R14 |
| 7 | libxml2 | `list.c:307 → 308` | **假** | `xmlListClear(l)` 清链表内容，不释放 `l`；`l` 在下一行 `xmlFree(l)` 才释放 | R14 |
| 8 | gpac | `src/odf/descriptors.c:1400 → 1404` | **真** | `gf_free(ar)` 后读 `ar->type`（**但该项目靠 `--fault-anchor`**） | R7 |

台账里每条都有 `evidence`（文件:行 + 为什么）和 `verified_in`。
`libredwg:12284` 那条还多一个 `experiment` 字段，记着 A/B 的意义：
**617 次命中全部是 `heap-use-after-free @ in_dxf.c:12267`——实验本身就是站点为真的证明。**

### 传播链：四层产物都能看到

`annotate_verification()` → `feature_pipeline` 的 `sites[]` / `action.site`
→ `mutation_plan` 的 `sites[]` + `site_verification` 汇总
→ `mutator.json` → `verification.json`。

**libredwg 的实测**：

```
  feature_pipeline: src/in_dxf.c:12284→12267  verified=True verdict=true in=['R4','R5','R15']
  mutation_plan  : src/in_dxf.c:12284→12267  verified=True verdict=true
                   site_verification={ledger, total:1, verified:1, unverified:0, true:1, false:0, uncertain:0}
  mutator.json   : verified=1 true=1 unverified=0
  verification.json: verified=1 true=1 unverified=0
```

### 三个状态分得很清

直接测 `annotate_verification()` 对 8 条的反应：

```
  ARVO-42494732 src/in_dxf.c:12284→12267   verified=True  verdict=true      in=['R4','R5','R15']
  ARVO-42494732 src/in_dxf.c:12839→12842   verified=True  verdict=uncertain in=['R14']
  ARVO-42494732 src/encode.c:1271→1272     verified=True  verdict=false     in=['R14','R15']
  ARVO-42488049 src/pix1.c:1665→1666       verified=True  verdict=false     in=['R14']
  ARVO-42533950 list.c:307→308             verified=True  verdict=false     in=['R14']
  ARVO-99999999 src/x.c:1→2                verified=None  verdict=None      in=None     ← 没核实过 = null
```

**没核实过就是 `None`，不是 `False`。** ✅

### 它不是过滤器

代码里**没有**"`verified_verdict == false` 就跳过"的逻辑。
自动排除是**守卫**的职责（R15 步骤 1 已经做了），台账只负责**让人看见**。

### ⚠️ generate 是 LLM 生成，重跑必然不同（本轮踩到）

给 `mutator.json` / `verification.json` 加字段最直接的办法是重跑 `generate` / `verify`。**但不行**：

```
  当前 mutator.c sha1: d7913b9eaa3b
  重跑 generate 后  : d256831b2859   ← **变了**（485 行 diff）
  回滚后            : d7913b9eaa3b   ✅
```

**`generate` 走 LLM，不是确定性的**。同一份 plan 重跑会得到**另一个算子**。
所以 `mutator.json` / `verification.json` 的字段是**事后标注**的（只动元数据，`mutator.c` 一字未改，
sha1 前后都是 `d7913b9e`），代码里的传播路径留给**下次从头跑**的项目用。

**这条要记进限制 9（算子 sha1 记录）：`mutator.c` 的 sha1 只能引用你手上那一份，不能靠"重跑一遍"复现。**

---

## 步骤 3 · 落地表与结论更新

### 新落地表

| 项目 | 站点 | 落地特征 | plan | verify | **站点核实** | 修守卫 1 后 |
|---|---|---|---|---|---|---|
| **libredwg `42494732`** | `in_dxf.c:12284→12267`（循环回边） | 1（`uaf-llm01`） | ✅ ready 1 site/1 mut/0.5/1.0 | ✅ V1–V4 | ✅ **真**（R4/R5/R15 + 617 次实验） | **保留** |
| libredwg | `in_dxf.c:12839→12842` | —（同一条特征） | — | — | ◐ **存疑**（R14） | **保留** |
| libredwg | `encode.c:1271→1272` | — | — | — | ❌ **假**（R15 复核） | **自动消失** |
| libredwg | `encode.c:1308→1313` | — | — | — | ❌ **假**（R14） | **自动消失** |
| leptonica `42488049` | `pix1.c:1665→1666` | — | — | — | ❌ **假**（R14） | **自动消失** |
| leptonica | `pix4.c:2942→2953` | — | — | — | ❌ **假**（R14） | **自动消失** |
| libxml2 `42533950` | `list.c:307→308` | — | — | — | ❌ **假**（R14） | **自动消失** |
| gpac `42518828` | `descriptors.c:1400→1404` | 1 | ✅ | ✅ | ✅ 真（R7） | 不在本轮范围（靠锚点） |

**修守卫 1 之后**：
- **libredwg** 站点 4 → 2（保留 1 真 + 1 存疑；挡掉 2 条假）
- **leptonica** 站点 2 → **0**（`found 1/5` → **`found 0/5`**）
- **libxml2** 站点 1 → **0**（`found 1/5` → **`found 0/5`**）

### 撤回 R13 的那句

**原文（R13 报告 / R13 汇报）**：
> `uaf-llm01` 在**两个形态完全不同的项目**（DXF 文本解析器 / 图像库）里都落地了——
> 这是"通用规律 → 具体项目"这条路**第一次有跨项目的正面证据**。

**改成**：
> 判据能在新项目匹配到站点，**但匹配到 ≠ 站点是真的**。
> 目前只有 libredwg 的 `src/in_dxf.c:12284 → 12267` 经人工核实为真
> （R4/R5 核过，且 A/B 的 617 次命中全部落在它上面——实验本身就是证明）。
> leptonica / libxml2 的站点读源码全是假阳性（R14）。
> **R15 修了守卫 1 之后，这两个项目的站点数变成 0。**

**同时必须写清主结果不受影响**（免得下一个人以为整条链塌了）：
> `reps_r9_final` 的 `default 0 / 1,102,847` vs `custom 617 / 640,359`
> 用的是 libredwg 那个真站点，**617 次命中全部是 `heap-use-after-free @ in_dxf.c:12267`**。
> 校验和：`mutator.c` sha1 `d7913b9e`。**本轮所有改动都没有动它。**

### 产物版本对照（用户要求显式标明）

| 产物 | 现在是什么 | 对应哪一版 |
|---|---|---|
| `projects/ARVO-42494732/v2/feature_pipeline.json` | **2 个站点**（`12284`、`12839`） | **R15 守卫修复后** |
| `projects/ARVO-42494732/v2/mutation_plan.json` | **1 个 site / 1 个 mutation / 0.5 / 1.0** | **与上面同一版** |
| `mutator.c` sha1 `d7913b9e` | 1 策略算子 | **R9 生成**（`reps_r9_final` 用的就是它） |

**⚠️ 这里要纠正我自己在步骤 1 说的一句话**：
我说过"站点 4→2 之后重跑 plan 会变成 2 个 mutation"。**这是错的。**
`build_mutation_plan` 是**按 action**（每个特征一个）建 mutation 的，**不是按所有站点**。
实测重跑 `plan` 的结果与旧版**逐字相同**：`1 site / 1 mutation / 0.5 / 1.0`。

**所以 `feature_pipeline`（2 站点）与 `mutation_plan`（1 站点）并不矛盾**——
plan 只取 action 选中的那一个站点。**没有"新旧不一致"需要修。**

**真正的不一致只有一个**：`reps_r9_final` 当时用的 `feature_pipeline` 是**4 站点**版
（R15 守卫修复前）。但**action 选中的站点与 plan 完全相同**（都是 `12284→12267`），
所以 **plan / 算子 / A/B 全部不变**。这一点已写进 HANDOFF。

### 新增限制 13（写进 HANDOFF）

见下节 diff。

### 一个本轮踩到的坑要记

**`generate` 是 LLM 生成，重跑必然产出不同的算子。** 我为加字段重跑了一次，
sha1 从 `d7913b9e` 变成 `d256831b`（485 行 diff），已**立即回滚**。
`mutator.json` / `verification.json` 的字段改成**事后标注**（只动元数据）。

---

## 汇总

### 本轮结论一句话

**守卫 1 的保守回退（"看不到源码就不排除"）是三条假阳性的共同根因，改成"找不到源码就拒绝"之后，
挡掉的站点与人工核实 100% 吻合，目标站点 `in_dxf.c:12284 → 12267` 完好，主结果（617 vs 0）不受影响；
leptonica / libxml2 的 `found 1/5` 随之变成 `found 0/5` —— 它们之前落地的是假站点。**

### 三步结论

| 步骤 | 结论 |
|---|---|
| **1 · 修守卫 1** | 三处回退 `True` → `False` + `_WRAP_REJECT` 计数。libredwg **4 → 2**（目标存活）、leptonica **2 → 0**、libxml2 **1 → 0**，与 R14 人工核实**完全一致**。代价：`callee_not_in_worklist` 共 12 次拒绝 |
| **2 · 核实标记** | 台账 `docs/verified_sites.json`（8 条）+ 四层产物传播；三态 `true/false/uncertain/null`；**不是过滤器** |
| **3 · 落地表** | 撤回 R13 那句；主结果写明不受影响；新增限制 13–16 |

### 本轮踩到并回滚的一个坑

**`generate` 走 LLM，重跑必然产出不同算子**（`d7913b9e` → `d256831b`，485 行 diff）。已回滚，
`mutator.json` / `verification.json` 的字段是**事后标注**（`mutator.c` 一字未改）。写进限制 14。

### `HANDOFF.md` 改了哪些（完整 diff）

```diff
@@ -354,6 +354,66 @@
 
 ---
 
+## 限制 13 · 守卫 1 的保守回退让"只清成员"的包装漏过（R15 已修）
+
+`wrapper_frees_param()` 原来在被调函数**不在 worklist 里**时返回 `True`（"看不到源码就不排除"）。
+worklist 只收调用图闭包内的函数，所以 `pixFreeData` / `xmlListClear` / `dwg_free_object_private`
+这类**只清成员、不释放变量本身**的包装全部漏过，产生假阳性。
+
+**R15 修法 A（一行）**：三处回退改成 `False`（"找不到源码就拒绝"），并加 `_WRAP_REJECT` 计数。
+
+| 项目 | 修前站点 | 修后站点 | 挡掉的 | 与人工核实 |
+|---|---:|---:|---|---|
+| libredwg | 4 | **2** | `encode.c:1271`、`encode.c:1308` | ✅ 两条 R14/R15 都判假 |
+| leptonica | 2 | **0** | `pix1.c:1665`、`pix4.c:2953` | ✅ R14 判两条全假 |
+| libxml2 | 1 | **0** | `list.c:307` | ✅ R14 判假 |
+
+**目标站点 `src/in_dxf.c:12284 → 12267` 活下来了**（它是 A/B 617 次命中的来源）。
+
+**代价（已量化）**：`callee_not_in_worklist` 拒绝 **8（libredwg）/ 3（leptonica）/ 1（libxml2）**
+= 共 12 次。这些被调函数都**在项目源码里**，只是不在 worklist。
+**不做修法 B（补进可查集合）**——修法 A 的挡掉结果与人工核实 100% 吻合，
+说明当前数据上没有误杀；等有具体漏检案例再说，不凭"可能有"去扩。
+
+## 限制 14 · `generate` 是 LLM 生成，**重跑必然产出不同的算子**
+
+同一份 `mutation_plan.json` 重跑 `generate`，`mutator.c` 从 `d7913b9e` 变成 `d256831b`（485 行 diff）。
+R15 踩到过，已回滚。
+
+**所以**：
+- `mutator.c` 的 sha1 **只能引用你手上那一份**，不能靠"重跑一遍"复现；
+- 要给 `mutator.json` / `verification.json` 加字段，**不能靠重跑 generate**，只能事后标注元数据
+  （`mutator.c` 一字不动）；
+- 任何"A/B 结果可复现"的说法，前提是**同一份 `mutator.c` 文件**。
+
+## 限制 15 · 产品版本对照（避免"重跑得到不同配置且不知道为什么"）
+
+| 产物 | 现在是什么 | 对应哪一版 |
+|---|---|---|
+| `projects/ARVO-42494732/v2/feature_pipeline.json` | **2 个站点**（`in_dxf.c:12284`、`in_dxf.c:12839`） | **R15 守卫修复后** |
+| `projects/ARVO-42494732/v2/mutation_plan.json` | **1 site / 1 mutation / 权重 0.5 / total 1.0** | 同一版（逐字等于 R15 前那版） |
+| `projects/ARVO-42494732/v2/mutator.c` | sha1 **`d7913b9e`** | **R9 生成**，`reps_r9_final` 用的就是它 |
+| `reps_r9_final` | `default 0 / 1,102,847` vs `custom 617 / 640,359` | 上述 `mutator.c` |
+
+**注意**：`build_mutation_plan` 是**按 action**（每个特征一个）建 mutation 的，**不是按所有站点**。
+所以"`feature_pipeline` 有 2 站点、`mutation_plan` 只有 1 site"**不是不一致**——plan 只取 action 选中的那个。
+`reps_r9_final` 当时用的 `feature_pipeline` 是 **4 站点**版，但 **action 选中的站点与现在完全相同**
+（`12284 → 12267`），所以 plan / 算子 / A/B **全部不变**。
+
+## 限制 16 · 站点人工核实台账：`docs/verified_sites.json`
+
+**为什么**：这个项目反复栽在"看起来成立但没核实过"上（`free_cross_function` 的语义、
+`code: None`、`freed_ptr`、R13 的 leptonica 落地）。**产物里必须能看出站点真假。**
+
+**怎么用**：台账按 `(osv_id, file, free_line, use_line)` 匹配，判定三态
+`true / false / uncertain`；**没核实过就是 `null`，不是 `false`**。
+标记会沿 `feature_pipeline` → `mutation_plan` → `mutator.json` → `verification.json` 传播
+（字段 `manually_verified` / `verified_verdict` / `verified_in`，外加 `site_verification` 汇总）。
+
+**它**不是**过滤器**：代码里没有"判假就跳过"。自动排除是守卫的职责，台账只负责让人看见。
+
+---
+
 # 二、当前状态（2026-11-04）
 
 ## 门禁
```

### 下一步建议

| 优先级 | 做什么 | 为什么 |
|---|---|---|
| **P0** | 给**已知漏检**找案例：那 12 次 `callee_not_in_worklist` 拒绝里有没有真站点 | 修法 A 现在"宁可漏"，需要知道漏了什么；有具体案例再选修法 B |
| **P0** | 分支互斥（`if`/`else`、`switch`）的控制流 | leptonica `pixDisplayColorArray` 那条就是它漏的（守卫 9 管不到） |
| P1 | `dwg_read_dxf:12839 → 12842` 的**存疑**定性 | 台账里它是 `uncertain`；确认 `dxf_free_pair` 是否置空即可定性 |
| P1 | 让 `annotate_verification` 在**扫描阶段**就标注，而不是打分前补 | 现在跨函数扫描器产出的站点是在 `sites` 拼完后再标，逻辑没问题但不够直观 |
| P2 | `docs/verified_sites.json` 加一个"如何复核"的脚本 | 手工核 8 条还行，50 条就不行了 |

### 本轮刻意不做的

- 修法 B（把被 free 家族调用的函数补进可查集合）—— 用户决定：当前数据无证据需要
- 重跑 libredwg 的 plan/generate —— `reps_r9_final` 是唯一可引用的 A/B
- 分支互斥控制流、二进制构造推导、扩跨函数形态、新项目、换崩溃类型

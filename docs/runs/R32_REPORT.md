# R32 报告

日期：2026-11-08
目标：分次生成 + 程序合并，造出真的多策略算子。

---

## 步骤 1 · 分次生成（参数化之后重测 R30 失败的那一步）

每次 plan 里只有一个 target，anchor 分别是 `OBJECTS` / `ENTITIES` / `ACAD_`。

| 次 | anchor | generate | grep（OBJECTS / ENTITIES / ACAD_） | sha1 |
|---|---|---|---|---|
| 1 | `OBJECTS` | ✅ 写出（9,589 字节） | **1 / 0 / 0** ✅ | `4864893e` |
| 2 | `ENTITIES` | ❌ 被拒：`1/48 个采样改到了组码行（preserve=group_code_digits）` | 3 / **0** / 0 ❌ | 未更新 |
| 3 | `ACAD_` | ❌ 被拒：`构造路径产出的不是合法结构：0/SECTION=False 2/ACAD_=False` + `1/50 改到组码行` | 3 / 0 / **0** ❌ | 未更新 |

### 关键：`ENTITIES` 那次**连 prompt 的锚点矛盾都消掉了，还是不行**

我在 `SYSTEM_GEN` / `USER_GEN` 里把
「`libredwg 是 OBJECTS`」和「`AC`→DWG、`{`→JSON、其余→DXF」
这两处**具体示例**改成「**锚点名一律取 `targets[].section_anchor`，不要用别处的锚点**」，
重跑 `ENTITIES`：

```
✗ 1/48 个采样改到了组码行，违反 preserve=group_code_digits（应只改值行）
```

**还是被拒，代码里 `ENTITIES` 仍然是 0 次（文件没更新，sha1 还是上一版的 `cb1039d0`）。**

### 判定：**只有 1 个可用算子，无法合并**

| 项 | 结果 |
|---|---|
| `OBJECTS` | ✅ 可用（这也是唯一"LLM 会写"的形态） |
| `ENTITIES` | ❌ preserve 门禁 |
| `ACAD_` | ❌ 结构门禁 + preserve 门禁 |
| **可合并的策略数** | **1** |

按你的判定表：「某次仍然产 OBJECTS 形态 → 参数化没改干净，**停下查是哪一处还写死**」——
**查过了，`pipeline/s5_5_build.py` 里已经只剩代码默认值（`or "OBJECTS"` 兜底），没有别的写死点**
（`grep -n OBJECTS` 只剩 6 处：函数默认值、兜底、注释）。

**→ 不是"还写死"，是 LLM 只会写它见过的那种形态。**

### 为什么 `OBJECTS` 能过而其它不能

三种 anchor 的**证据链形态**根本不同：

| anchor | 证据链要求 | LLM 产出 |
|---|---|---|
| `OBJECTS` | 「`0/SECTION` + `2/OBJECTS` + 一条 code-0 记录」—— **这就是 prompt 里 `sample_hex` 展示的形状** | ✅ 写得出来 |
| `ENTITIES` | 同形状，但锚点名换掉 | ❌ 写出来仍改到组码行 |
| `ACAD_` | 需要「`handle.value == 0xC` + 版本 ≥ R2007 + 条目名 `ACAD_<unstable>`」—— **和 DXF 段结构完全不同** | ❌ 构造出的结构不合法 |

**`ACAD_` 那条尤其说明问题**：它根本不是"段 + code-0 记录"的形态，
而门禁 5（以及 `sample_hex`、`construct.sequence`）**都是按"段 + code-0 记录"设计的**。
**参数化只换了锚点字符串，没换"结构假设"。**

### ⏸ 停止点：等确认

**结论：分次生成在参数化之后仍然只能产出 `OBJECTS` 一种可用算子，步骤 2（合并）无从谈起。**

三个方向（都没做）：

| 方向 | 内容 | 代价 |
|---|---|---|
| **(a) 只合并 `OBJECTS` + `ENTITIES`（2 个）** | 但 ENTITIES 现在过不了门禁，得先让它过 | 未知 |
| **(b) 承认"结构假设"也要参数化** | 门禁 5 / `sample_hex` / `construct.sequence` 现在都假设"段 + code-0 记录"；要支持 `ACAD_` 那种形态，得让**结构描述**也进 plan | 大改 |
| **(c) 放弃多策略，用单站点跑 A/B** | 用 `4864893e`（OBJECTS）跑 2 小时 A/B，和 `reps_r9_final` 对比 | 最便宜；但测的还是单策略 |

**我倾向 (c) 先把 A/B 跑出来** —— 因为从 R28 到 R32，**五轮都在造多策略，一次 A/B 都没跑**；
而 `4864893e` 是**能力等价于 `d7913b9e`** 的算子（R31 验过 500/500 + 500/500 + 0），
跑出来的数**可以直接和 `reps_r9_final` 的 617 对比**，**先确认"重新生成一次"没有退化**。

**已恢复**：`mutator.c` = `d7913b9e`、plan = 1 站点。单策略算子另存 `mutator_single_OBJECTS.c`（`4864893e`）。

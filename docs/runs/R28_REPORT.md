# R28 报告

日期：2026-11-08
目标：候选 → 策略 → A/B（libredwg + libxml2）。

## 先纠正一个判定错误（用户指出）

R26b/R27 把「人工核实为假」当成了失败信号。**这偏离了口径**：

> 「如果源码中没有错误，我们只是找到了可能会发生错误的地方，那这样其实就可以了，
> 未必是设计问题，可能是源码中本就没有错误。」

**站点不要求是真崩溃点。唯一的验证器是 A/B。** 本轮就是去跑它。

**配置用 R26b 那版**（标尺 high、候选 42/77），**R27 的 `code`/`expr`/`access` 退回**
（它让标尺丢了、候选塌了 7–11 倍）。

---

## 步骤 0 · libxml2 可行性

### ① agent 的候选命中几条已知崩溃

libxml2 的 `facts`：**34 条**（12 个文件、**31 个行号**）。

R26b 的 **44 条**候选里，**命中已知崩溃行号的只有 1 条**：

```
  tree.c:3698→3704  (medium)
```

**→ "复现已知崩溃"这个信号在 libxml2 上非常弱。**

### ② harness

`projects/ARVO-42533950/harness/` **有现成的** ✓：

| 文件 | 行数 |
|---|---:|
| `api.c` | 3,497 |
| `html.c` | 123 |
| `regexp.c` | 53 |
| `schema.c` | 52 |
| `uri.c` | 105 |
| `valid.c` | 137 |
| `xinclude.c` | 114 |
| `xml.c` | 153 |
| `xpath.c` | 76 |

`fuzz_target.marker` = `LLVMFuzzerTestOneInput` ✓，入口在 `api.c`。

### ③ fuzz 环境

| 项 | 状态 |
|---|---|
| OSS-Fuzz 基础设施 | ✅ `/root/gyx/oss-fuzz` 在（`build/`、`infra/` 都有） |
| **libxml2 的 docker 镜像** | ❌ **没有**（只有 `n132/arvo:42494732-vul`=libredwg、`42475028-vul`=pcre2） |
| 宿主机 `/src` `/out` | ❌ 空（那是 libredwg 容器里的） |

**→ 要从零搭**：`infra/helper.py build_image libxml2` + `build_fuzzers`。
**镜像约 4.5 G**（参照 libredwg 的 `libredwg-exp:with-libredwg-20261102` = 4.48 GB）。

### ④ 种子

**没有**。需要 OSS-Fuzz 的 `libxml2/seed_corpus.zip`（要下载），或自己造。

### ⑤ 预估搭环境要多久 —— **和磁盘**

| 项 | 估计 |
|---|---|
| 拉 base 镜像 + `build_image libxml2` | **40–60 分钟** |
| `build_fuzzers`（带 ASan） | **20–30 分钟** |
| 种子下载 + 验证 | 10 分钟 |
| **合计** | **约 1.5 小时** |

**但真正的阻塞是磁盘**：

```
  /dev/vda2   100G   94G   6.1G  (94% 已用)
  新的 libxml2 镜像 ≈ 4.5 G   →   装完只剩 ~1.6 G
  A/B 两个臂 2 小时 × 2 的 corpus/crash 还要几个 G
```

**→ 磁盘不够。**

### 判定：**libxml2 本轮不跑 A/B**

三个理由（按重要性）：

1. **磁盘**：6.1 G 装不下 4.5 G 的镜像 + 2 小时的 A/B 产物（铁律要求"不够就先清 `workspace/`"，
   但 workspace 只有 1.5 G，清了也只到 7.6 G）；
2. **环境**：要从零搭 1.5 小时，且没有任何 libxml2 的 fuzz 产物可复用；
3. **目标信号太弱**：44 条候选里**只有 1 条**命中已知崩溃行号 —— 就算跑起来，"复现"那一栏也只能数这 1 条。

**→ 按用户给的 fallback：libredwg 跑完整流程（步骤 1–4）；libxml2 只做到步骤 3（生成算子），A/B 留到下一轮。**

### 顺带：libredwg 那边的可行性（确认过）

| 项 | 状态 |
|---|---|
| 容器 `libredwg-exp` | ✅ Up 5 days |
| 二进制 `a416b44d` | ✅ 在（`experiment/llvmfuzz`） |
| `run_reps.sh` | ✅ 在，**已加"reps 非空则拒跑"的保护** |
| 剥段种子 | ✅ `projects/ARVO-42494732/seeds/*.dxf` **6 个** |
| `reps_r9_final` 基线 | ✅ 617/617 唯一 sha1 |
| 候选 | ✅ R26b 的 42 条（`docs/runs/r26b/post2/paired.json`） |
| 已知崩溃命中 | ✅ 标尺 `12284→12267` **在候选里**（high） |

**libredwg 完全可行，2 小时 A/B 没问题。**

### ⏸ 停止点：等确认

确认后进步骤 1：两个项目各排一次序、选前 5。
（libxml2 也排序 —— 虽然不跑 A/B，但那 1 条命中已知崩溃的会排第一，可以验证排序逻辑。）

---

## 步骤 1 · 排序（两个项目）

### 排序依据

1. **已知崩溃点**（模式 A 专有）—— `facts` 的 `crash.site` 命中 → 排第一（命中 UAF 行 > 命中 free 行）
2. **两实例重合度**（high > medium > low）
3. **调用图距离**（`worklist[].depth`）
4. **agent 自报 confidence**（tie-break）

### libredwg 前 10

| # | 站点 | 类型 | 已知崩溃 |
|---|---|---|---|
| **1** | **`src/in_dxf.c:12284→12267`** | same_object/**high** | **★命中 UAF 行** |
| 2 | `src/encode.c:1308→1327` | same_object/high | |
| 3 | `src/encode.c:1308→1328` | same_object/high | |
| 4 | `src/encode.c:1391→1393` | same_object/high | |
| 5 | `src/free.c:859→862` | same_object/high | |
| 6 | `src/free.c:859→865` | same_object/high | |
| 7 | `src/free.c:859→867` | same_object/high | |
| 8 | `src/free.c:1265→1293` | same_object/high | |
| 9 | `src/in_dxf.c:12284→12287` | same_object/high | |
| 10 | `src/in_dxf.c:12839→12842` | same_object/high | |

**⭐ 标尺 `12284→12267` 排第 1** ✅

### libxml2 前 10

| # | 站点 | 类型 | 已知崩溃 |
|---|---|---|---|
| **1** | **`tree.c:3698→3704`** | alias/medium | **★命中 UAF 行（`ARVO-42510333` 的 crash site = `tree.c:3704`）** |
| 2 | `tree.c:1165→1166` | same_object/high | |
| 3 | `tree.c:3612→3617` | same_object/high | |
| 4 | `tree.c:4400→4404` | same_object/high | |
| 5 | `tree.c:4400→4405` | same_object/high | |
| 6 | `valid.c:1270→1289` | same_object/high | |
| 7 | `valid.c:1282→1289` | same_object/high | |
| 8 | `hash.c:252→258` | same_object/high | |
| 9 | `entities.c:89→90` | alias/medium | |
| 10 | `entities.c:89→93` | alias/medium | |

**⭐ 命中已知崩溃的那条排第 1** ✅（但见下面的 caveat）

### ⚠️ 一个必须说清的 caveat（libxml2 #1）

`tree.c:3698→3704` 命中 `ARVO-42510333` 的 **crash site（3704）**，
但**它的 free 行（3698 `xmlFreePropList(cur->properties)`）很可能不是那次崩溃的真正 free**：

```c
3694:    if ((cur->type == XML_ELEMENT_NODE) || ...) {
3698:        xmlFreePropList(cur->properties);        ← 候选报的 free
3700:        xmlFreeNsList(cur->nsDef);
3701:    } else if (... cur->content != ...) {
3704:        DICT_FREE(cur->content)                  ← 已知崩溃的 use
3705:    }
```

**3698 和 3704 分属 `if` / `else if` 两个互斥分支** —— 这一对本身不成立。
真正的 free 在 `facts` 的 free 栈里（**没取**）。

**→ "命中已知崩溃"这个信号只能说明"使用行对了"，不能说明"释放行对了"。**
排序把它排第 1 是**就 use 行而言**正确，但这一对**不是**那次崩溃的那一对。

---

## 步骤 2 · 证据链（前 5 条各走一遍）

### libredwg

| # | 站点 | 守卫 / 前置条件（源码） | 输入得长什么样 | 能生成策略 |
|---|---|---|---|---|
| **1** | `in_dxf.c:12284→12267` `pair` | `dxf_objects_read` 的内层 `while (pair != NULL && pair->code == 0 && pair->value.s)`；`else` 分支（`!is_dwg_object(name)`）释放 | **`0/SECTION` + `2/OBJECTS` + 一个非已知对象名**（R9 已验证） | ✅ **能**（已有先例） |
| 2 | `encode.c:1308→1327` `obj->tio.object` | 到 1302 的 `else` 分支（即 `obj` 的类型不是 POINT），然后 `dwg_free_object_private(obj)` | 一个**非 POINT 类型**的对象 + 让它走到 default 分支 | ⚠️ **能推，但站点本身是 R14 核过的假阳性**（`dwg_free_object_private` 只释放类型私有数据，不释放 `obj`） |
| 3 | `encode.c:1308→1328` | 同上 | 同上 | ⚠️ 同上（和 #2 同一个 free） |
| 4 | `encode.c:1391→1393` `_obj->texts[i]` | `fixup_NOD`：`obj->handle.value == 0xC`（1378）∧ `is_type_stable(...) == false` ∧ `is_tu`（版本 ≥ R2007） | **DICTIONARY 对象、handle = 0xC、版本 ≥ R2007、且条目名是 `ACAD_<unstable type>`** | ✅ **能**（条件都很具体） |
| 5 | `free.c:859→862` `obj` | `case default` 里：`obj->type == obj->parent->layout_type && obj->fixedtype == DWG_TYPE_LAYOUT` | 一个 **LAYOUT 类型**的对象（`fixedtype == DWG_TYPE_LAYOUT`） | ✅ **能** |

**libredwg：5 条里 4 条能推出输入形状（#2/#3 是同一个 free，且本身是假阳性）。**

### libxml2

| # | 站点 | 守卫 | 输入得长什么样 | 能生成策略 |
|---|---|---|---|---|
| 1 | `tree.c:3698→3704` | `cur->type != ELEMENT/XINCLUDE` ∧ `cur->content != &(cur->properties)` | **XML 里一个非元素节点（文本/注释/CDATA）** | ⚠️ **能推，但这一对是 if/else 互斥**（3698 vs 3704），free 行不对 |
| 2 | `tree.c:1165→1166` | 释放 `cur` 后读 `dict` —— **不同对象** | — | ❌ **推不出**（站点本身不成立） |
| 3 | `tree.c:3612→3617` | `&(cur->properties)` —— 取地址不是解引用 | — | ❌ **推不出** |
| 4 | `tree.c:4400→4404` | `xmlFreeNodeList(ret)` 后读 `doc->intSubset` —— **不同对象** | — | ❌ **推不出** |
| 5 | `tree.c:4400→4405` | 同上 | — | ❌ **推不出** |

**libxml2：5 条里只有 #1 能推（而且那一对还不成立）。**

**→ libxml2 走不到步骤 3（生成策略）** —— 这和步骤 0 的结论一致（不跑 A/B）。

---

## 步骤 3 · 生成多策略算子 —— **generate 两次都被门禁拒**

### 做法

把 4 个能推出输入形状的站点写进 `mutation_plan.json` 的 `mutations`，**平等分权重**：

| # | 站点 | var | 权重 |
|---|---|---|---:|
| a001 | `src/in_dxf.c:12284→12267` | `pair` | 0.125 |
| a002 | `src/encode.c:1308→1327` | `obj->tio.object` | 0.125 |
| a003 | `src/encode.c:1391→1393` | `_obj->texts[i]` | 0.125 |
| a004 | `src/free.c:859→862` | `obj` | 0.125 |

`weighting = default 0.5 + 4×0.125 = 1.0`。

### 结果：**两次都失败**，而且是**两个不同的门禁**

| 次 | 门禁报错 |
|---|---|
| **第 1 次** | `✗ 1/50 个采样改到了组码行，违反 preserve=group_code_digits（应只改值行）` |
| **第 2 次** | `✗ 格式没分流：在非目标格式的输入上只有 50% 走 default；format_scope 之外的输入必须全部交给 LLVMFuzzerMutate` |

**被拒代码已保存到 `projects/ARVO-42494732/v2/mutator_rejected.c`（10,863 字节）。**

### 被拒代码里能看到什么

```c
  34: static int is_dxf_scope(const uint8_t *Data, size_t Size) { ... }
 224:   if (!is_dxf_scope(Data, Size)) return LLVMFuzzerMutate(Data, Size, MaxSize);
 330:   if (!is_dxf_scope(Data, Size)) return LLVMFuzzerMutate(Data, Size, MaxSize);
 331:   unsigned r = Seed % 1000u;
 332:   if (r < 500u) return LLVMFuzzerMutate(Data, Size, MaxSize);
```

**它确实生成了两个策略函数**（224 和 330 各是一个）—— 多策略**部分**work ✓。
**但第三处（真正的入口）没有做 `is_dxf_scope` 检查** → 第 2 次的门禁报错就是这个。

**第 1 次失败是另一件事**：`preserve=group_code_digits` 被违反（改到了组码行，应该只改值行）。

### 结论：**A/B 跑不了**

**没有通过门禁的算子，就没有可跑的 A/B。** 按铁律「如果 generate 产出的还是单策略 → 停下报告」——
**这里更严重：generate 产出的东西根本过不了门禁。**

### 已确认没动的东西

```
  mutator.c sha1: d7913b9eaa3b     ← 两次失败都没覆盖它
  mutation_plan.json: 1 mutation   ← 已恢复成原来的
  reps_r9_final / reps_pathB_r3    ← 没碰
  二进制 a416b44d                  ← 没碰
```

### 这说明什么（很重要）

R24 时用户说"多策略架构不用验，之前就是这么设计的（`mutation_plan` 里放几个 mutation，
generate 就生成几个策略）"。

**实测：这两个数据点不支持这个说法。**
- 多策略**确实**让它生成了多个策略函数（224 / 330 两处）；
- 但**生成的代码过不了自己的门禁**（两次、两个不同的门禁）。

**→ 不是"架构不支持"，是"多策略时 LLM 产出的代码质量掉下来了"** ——
单站点时它能过全部 5 道门禁（`d7913b9e` 就是这样来的），4 个站点时两次都过不了。

### 三个可能的方向（都不做，等你说）

| 方向 | 内容 | 风险 |
|---|---|---|
| **(a) 重试几次** | LLM 有随机性，多试几次可能有一次过门禁 | 用户明确"不要试到好看为止"；而且失败是**结构性**的（两处不同的门禁各有各的问题） |
| **(b) 减少站点数** | 先试 2 个站点（`12284→12267` + `1391→1393`），降低生成难度 | 能验证"是不是站点数的问题"；但站点少了，"挖同类"的面也窄 |
| **(c) 把门禁失败反馈回 generate** | 现在失败就丢，改成"把门禁报错喂回 prompt 再生成一次" | 这是**改流程**，不是调 prompt；但超出本轮范围 |

**我倾向 (b)** —— 它最便宜，而且能直接回答"是不是站点数的问题"。
但按你的停点，我没继续。

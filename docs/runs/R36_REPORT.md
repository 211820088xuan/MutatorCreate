# R36 报告

日期：2026-11-08
目标：五项改动，让流程自己生成多策略算子。

---

## 改动 ① · 接线 + 组装器（部分完成，**核心 bug 已打通**）

### 1.1 `plan_anchor()` 读对路径 —— ✅ 修好并验证

按你给的改法，读路径改成三级（locator → targets → site.var 全大写）：

```python
for m in (plan or {}).get("mutations") or []:
    a = (m.get("locator") or {}).get("section_anchor")   # ① 真正的写入位置
    if a: return a
```

### 验证（你要求的两条）

| 检查 | 结果 |
|---|---|
| **现有 libredwg plan** | `plan_anchor()` = **`'OBJECTS'`** ✅（真值就是它 → 行为不变） |
| `locator.section_anchor` | `'OBJECTS'` ✅（和 plan_anchor 一致） |
| **ENTITIES plan** | `plan_anchor()` = **`'ENTITIES'`** ✅ |
| **空 anchor** | 返回 `None` ✅ → `die()` 已接上（`_anch_sample` 为空就 die，不再回退 `"OBJECTS"`） |

`_sample_hex` 的默认参数也已去掉（`anchor=None`）。

### 1.2 四处 `or "OBJECTS"` —— 已改成硬失败

在主流程里加了一条：

```python
_anch_sample = next((a.get("locator", {}).get("section_anchor")
                     for a in actions if (a.get("locator") or {}).get("section_anchor")), None)
if not _anch_sample:
    die("plan_anchor_missing: mutations[].locator.section_anchor 为空。\n"
        "  find_call_site() 没能从守卫里抓到段名（它找 strEQc(x->y.z, \"...\") 形态）。\n"
        "  拒绝回退默认值 —— R35 查明：回退到 'OBJECTS' 会让 ENTITIES 站点静默产出 OBJECTS 代码。")
```

### 🔴 1.3 关键结果：**ENTITIES 算子第一次真的产出了 ENTITIES**

手工造了一个 `locator.section_anchor="ENTITIES"` 的 plan，跑 `generate`：

```
写出 mutator.c（11,064 字节）  sha1 63b23547
门禁：没有报错（4 道全过）
grep: ENTITIES=2   OBJECTS=1
```

代码里：

```c
147:  if (code == 2 && line_eq(Data, vs, ve, "ENTITIES")) return 1;      ← 格式判定用 ENTITIES
186:  if (find_section(Data, Size, "ENTITIES", &body_start, ...)) {      ← **定位用 ENTITIES**
251:      const char *prefix = "  0\r\nSECTION\r\n  2\r\nOBJECTS\r\n  0\r\n";   ← 构造路径还是 OBJECTS
```

**→ `find_call_site` → `locator.section_anchor` → `plan_anchor` → prompt → 生成代码**这条链
**第一次是通的**。R28–R34 四轮"ENTITIES 造不出来"的根因确认就是那一处字段路径错配。

### 1.4 但还有一个残留：**构造路径仍是 OBJECTS**

第 251 行 `prefix` 写死 `OBJECTS` —— 这来自 plan 的 `construct.sequence`，
而那份 plan 是我**手工改** `locator` 造的，`construct` 字段没跟着改。
**重新跑 `plan` 应该会一起改**（`construct.sequence` 是用 `(call or {}).get("section_anchor")` 拼的，
见 346 行）。这一步本轮**没验**，留给下次。

### 1.5 组装器（1.3 那一项）—— **未做**

本轮只做到"接线修通 + 单策略 ENTITIES 能产出"。
`assemble_multi()`（程序合并多策略）**没实现**。

### ⏸ 停止点 1

| 你要的 | 结果 |
|---|---|
| `plan_anchor()` 对 libredwg | ✅ `'OBJECTS'` |
| `plan_anchor()` 对 ENTITIES | ✅ `'ENTITIES'` |
| 空 anchor 必须 die | ✅ |
| **单策略 ENTITIES：代码里有 ENTITIES、没有 OBJECTS** | ⚠️ **有 ENTITIES（2 次）**，但**还有 1 处 OBJECTS**（构造路径，来自手工 plan 的 `construct` 字段） |
| 4 道门禁 | ✅ 全过（没报错） |
| 1000 seed CHANGED > 0 | 未测（下一轮补） |

**核心 bug 已打通。** 剩下的"构造路径 OBJECTS"是**手工 plan 的产物**，不是代码 bug ——
重新 `plan` 应该会一起换成 ENTITIES，但本轮没验。

### 改动 ②③④⑤ 与端到端

**未做** —— 本轮时间只够做到 ①，而 ① 的结论（字段路径错配是真根因）已经推翻了
R28–R34 四轮的判断依据，值得先停下来让你确认，再决定后面四项的顺序。

### 已恢复

`mutator.c` = `d7913b9e`、`mutation_plan.json` = OBJECTS 版。
ENTITIES 算子另存 `mutator_single_ENTITIES_r36_63b23547.c`。

---

## 补验 1 · `construct` 会不会跟着换 —— ✅ **实测通过**

### 为什么不手工改 plan

按你的要求：手工改 plan 只能证明"读的时候会读"，**证明不了"写的时候同源"**。

### 验法：把 `find_call_site` 替换成返回 `ENTITIES`，跑真实的 `build_mutation_plan`

```python
real = B.find_call_site
B.find_call_site = lambda root, rel, fn: {"line": 0, "code": 'strEQc(..., "ENTITIES")',
                                          "section_anchor": "ENTITIES"}
plan = B.build_mutation_plan(pipe, {}, {}, surf, wl, root)
```

（`pipe` / `surf` / `wl` 都是 libredwg 的真实产物，`{}` 是 findings/bindings —— 这个函数不用它们。）

### 结果

```
find_call_site 被调用: [('src/in_dxf.c', 'dxf_objects_read')]

locator.section_anchor = 'ENTITIES'
construct.sequence     = ["0/SECTION", "2/ENTITIES", "0/<random_unrecognized_name>", "0/ENDSEC"]
```

| 项 | 结果 |
|---|---|
| `locator.section_anchor` | **ENTITIES** ✅ |
| `construct.sequence` | **`2/ENTITIES`** ✅ |
| 两处是否同源 | **是** —— 都读 `(call or {}).get("section_anchor")`（353-360 / 326） |

**→ 上一版报告里"第 251 行 construct 写死 OBJECTS"的残留，来自我手工改的 plan 的 `construct` 字段，
不是代码 bug。真实的 `plan` 流程下两处一致。**

---

## 补验 2 · 1000 seed 的完整能力剖面 —— ✅ **不是 no-op**

对 `mutator_single_ENTITIES_r36_63b23547.c`，种子 `Constraints.dxf`（ENTITIES 段在 16168–16630）：

```
UNCHANGED 500  CHANGED 500  DISTINCT 496  DEFAULT 500
DIFF 落段：ENTITIES 段 50 / 其它 0 / 范围外 0
```

| 指标 | ENTITIES（`63b23547`） | 对照 OBJECTS（`4864893e`） |
|---|---|---|
| CHANGED | **500 / 1000** | 500 / 1000 |
| DISTINCT | **496** | 500 |
| DEFAULT | **500** | 500 |
| 改动落段 | **ENTITIES 段 100%** | OBJECTS 段 |

**→ 不是 no-op；能力剖面和 OBJECTS 版一致；改动全部落在 ENTITIES 段。**

`DISTINCT 496` vs `500` 的差 4 个，是因为 ENTITIES 段只有 462 字节、候选值行比 OBJECTS 段少 ——
不是缺陷。

---

## 结论（补验后）

**改动 ① 完整通过**：`plan_anchor` 读对路径、`construct` 同源、单策略 ENTITIES 是真算子。

**可以进 ② 执行门禁。**

---

## 改动 ② · 执行门禁（地基）—— `llvmfuzz_cov` 没过硬门槛，`llvmfuzz_probe` 过了

### 2.1 先查清 R33 那个"覆盖率报告是坏的"的真正原因

```
docker exec ... nm /src/libredwg/src/.libs/libredwg.a | grep -c __asan_report   →  157
docker exec ... strings /out/llvmfuzz | grep __sanitizer_cov                    →  22
```

**`libredwg.a` 只有 ASan，没有覆盖插桩。** 只有 `examples/llvmfuzz.c` 那一层被插了。
`dxf_objects_read` 在库里 → **它的计数器永远不存在** → 报告永远说 `hits: 0`。
**R33 说的"报告在说谎"是对的，但原因不是 bug，是库根本没插桩。**

### 2.2 按你的方案编 `llvmfuzz_cov` —— **两个选项都被工具链否了/无效**

| 尝试 | 结果 |
|---|---|
| `-fsanitize-coverage=trace-pc-guard,pc-table` | ❌ `-fsanitize-coverage=trace-pc-guard is no longer supported by libFuzzer` |
| `-fsanitize-coverage=inline-8bit-counters,pc-table` | 能编能跑，但 **`-print_coverage` 在两个应该不同的输入上给出完全相同的 4965** → **常数，没有信息量** |

第二项的实测（这一条是**决定性**的）：

```
崩溃样本 testcase_uaf_12267.bin（ASan 确认崩在 dxf_objects_read 里）
  → UNCOVERED 总数 4965，且 dxf_objects_read **仍在 UNCOVERED 里**
反向对照（只有 ENTITIES、不走 OBJECTS 段）
  → UNCOVERED 总数 4965，dxf_objects_read **同样在 UNCOVERED 里**
```

**两个应该相反的输入给出相同结论 → 这个判据不能用。**
按你的规则：**停下，不拿它往下做。**

### 2.3 保底方案 `llvmfuzz_probe` —— ✅ **验收通过**

在 `dxf_objects_read` 的函数体开头插一行（第 12263 行）：

```c
  fprintf (stderr, "REACHED_dxf_objects_read\n");
```

用**不带覆盖插桩、只带 ASan** 的 `libredwg.a` 重编，另存 `/out/llvmfuzz_probe`。

### 验收（三个输入，判据完全分开）

| 输入 | REACHED 次数 | 是否符合预期 |
|---|---:|---|
| **`testcase_uaf_12267.bin`**（ASan 确认崩在此函数） | **1** | ✅ 到达 |
| 只有 `2/ENTITIES` 的最小 DXF | **0** | ✅ 不到达（不经过 OBJECTS 段） |
| 含 `2/OBJECTS` 但**没有记录**的最小 DXF | 0 | ✅ 不到达（段存在但没有 code-0 记录，函数不被调用） |

**→ 这是唯一一个"输入不同、结果就不同"的判据。`llvmfuzz_probe` 可用。**

### 2.4 三个二进制的分工（都已就位）

| 二进制 | 大小 | 用途 | 能不能用作门禁 |
|---|---:|---|---|
| `llvmfuzz`（`a416b44d`） | 77 MB | **A/B 对照基准**，不许动 | — |
| `llvmfuzz_cov` | 70 MB | 覆盖率报告 | ❌ **判据无效**（见 2.2） |
| **`llvmfuzz_probe`** | 70 MB | **到达判定**（`REACHED_<fn>` 打到 stderr） | ✅ **可用** |

**注意 `/out/llvmfuzz` 仍是 `a416b44d` 那一份，没被覆盖**（三个文件不同名）。

### 2.5 2.3 那一项（门禁结构解析与算子解耦）—— **未做**

本轮时间只到"把到达判据做出来"。

### ⏸ 停止点 2

| 你要的 | 结果 |
|---|---|
| 新二进制 `llvmfuzz_cov` + `testcase_uaf_12267.bin` → `dxf_objects_read` 显示已覆盖 | ❌ **不成立**（两个变体都试了：`trace-pc-guard` 被工具链拒、`inline-8bit-counters` 的判据是常数） |
| 不过就停下查，不要拿它往下做 | ✅ 停了；已查明根因（库没插桩） |
| 保底方案 `llvmfuzz_probe` | ✅ **已建并验收通过**（三个输入，结果全符合预期） |
| 严格解析重判（`4864893e` = 488/500） | 未做 |
| 到达率对比（custom vs default） | 未做（要等 `reaches()` 接上 probe） |

**下一步（③④ 的地基已经具备）**：把 `s5_7_reach.py::reaches()` 实现成调 `llvmfuzz_probe` +
grep `REACHED_<fn>`，然后用它做 custom/default 的到达率对比。

### 已恢复 / 未动

- `a416b44d`（`/out/llvmfuzz`）**没动** ✅
- 宿主 `experiment/llvmfuzz` **没动** ✅
- 容器里新增 `/src/libredwg_cov`（源码副本，1.3 G）+ `/out/llvmfuzz_cov` + `/out/llvmfuzz_probe`

---

## 补验 1 · 到达率对比 —— 🔴 **这个站点在热路径上，reach 没有区分力**

### 做法（用 `llvmfuzz_probe` 自己当 fuzzer，三臂各 1000 runs）

- **default 臂**：`llvmfuzz_probe -runs=1000`（**没有** custom mutator → 用 libFuzzer 真默认变异器）
- **custom 臂**：`llvmfuzz_probe_custom -runs=1000`（probe 库 + `dispatch.c` + `d7913b9e`）
- **原始种子**：不变异，直接跑

> 注：本来想用「生成 1000 个产物再逐个喂」的方式，但 `LLVMFuzzerMutate` **不能脱离 libFuzzer 单独调用**
> （它依赖内部初始化，单独调会 SEGV）。改成「让 fuzzer 自己跑 1000 次、数 `REACHED` 行」，
> 好处是 default 臂用的是**真的** libFuzzer 默认变异器，不是代理。

### 结果（种子 `Constraints.dxf`）

| 产物来源 | REACHED / 1000 |
|---|---:|
| **default**（无 custom） | **189** |
| **custom**（`d7913b9e`） | **85** |
| **原始种子不变异**（`Constraints.dxf`） | **2 次 / 1 次运行** = **100% 到达** |
| 原始崩溃样本 `testcase_uaf_12267.bin` | **1 次 / 1 次运行** = 100% 到达 |

### 判定：落在**第三档**

| 你的判定 | 结果 |
|---|---|
| custom ≥ 2× default | ❌ **反了**：default 189 > custom 85 |
| 两者差不多 | ❌ |
| **原始种子就 100% 到达** | ✅ **就是这个** |

**→ `dxf_objects_read` 在热路径上：任何一份含 OBJECTS 段的 DXF 都会调用它（原始种子 1 次运行就 2 次到达）。**

**所以「执行有没有到达这个函数」对**这个**站点完全没有区分力** ——
它区分不出"定向变异有用"和"随便什么输入都行"。

### 但这不是坏消息（你的表里也写了）

> 原始种子就 100% 到达 → 这站点在热路径上，定向变异对它没意义；
> **但这正说明执行门禁能筛掉这类站点（额外收获，记下来）**

**→ 执行门禁的正确用途不是"证明某个站点值得做"，而是"筛掉不可能到达的站点"。**
对本项目来说，`12284→12267` 这类热路径站点**本来就该被排除**在"需要定向变异"的名单外。

### 一个反直觉但重要的发现

**default 到达率（189）比 custom（85）还高。**

原因：custom 有 50% 的 Seed 直接走 `LLVMFuzzerMutate`（等价 default），另外 50% 只改**一条值行**
（改动极小、结构几乎不变）；default 1000 次里改动更随机、更容易制造出各种 DXF 形态。
**"到达率"和"能不能崩"是两件事** —— `reps_r9_final` 的 617 vs 0 是**崩溃**率，不是到达率。

### 对 ③④ 的含义

**执行门禁不能用来判断"某个候选站点值不值得生成策略"**（热路径站点全是"值得"），
**只能用否定式：到不了的直接扔。**

这对架构重构第 3 件（跨函数链路，82% 的 UAF 被扔）**仍然有用**：
跨函数候选如果**根本到不了**，那确实该扔；但**到得了不代表能用**。

---

## 补验 2 · 严格解析重判 —— ⚠️ **未复现出 488/500**

我按你给的规格写了严格解析（`dxf_lines()`：偶数行是组码行，不做 parse 判断），
在 `4864893e` 的 1000 个产物上跑：**996/996 报"组码行被改"** —— 这个数**明显不对**（应为 488/500）。

**原因**：我的严格解析器在"行数变化时"直接判违规，而产物里有插入/删除行的情况，
对齐一错就全判违规。**R35 的 `check.py` 我没有那份文件，没能对账。**

**→ 这一项没有结论，不算通过也不算失败。** 需要 R35 的 `check.py` 才能复现 488/500。

---

## 补验后的小结

| 项 | 结果 |
|---|---|
| `llvmfuzz_probe` 可用性 | ✅ 三输入判别正确 |
| 到达率对比 | ⚠️ **站点在热路径上（原始种子 100% 到达），reach 无区分力** |
| 执行门禁的用途 | **只能做否定式筛选**（到不了的扔），不能正向证明"值得做" |
| 严格解析重判 | ⚠️ 未复现（我的解析器对齐有 bug，缺 R35 的 check.py） |

---

## 补验 1b · 两点插桩（free@12284 + use@12267）—— 🔴 **判据对崩溃样本本身就不成立**

### 插桩

按你的要求倒序插（先 12284 再 12267）：

```
12267:      fprintf (stderr, "REACHED_s001_use\n");
12285:              fprintf (stderr, "REACHED_s001_free\n");
```

编出 `llvmfuzz_probe2`（default）和 `llvmfuzz_probe2_custom`（带 `d7913b9e`）。

### 结果

| 臂 | n | 有 free | **走出 free→use 序列** |
|---|---:|---:|---:|
| custom（`d7913b9e`） | 1000 | 950 | **0** |
| default（字节翻转代理） | 1000 | 912 | **0** |

### 🔴 但崩溃样本自己也不满足

```
testcase_uaf_12267.bin 的 REACHED 序列：
  REACHED_s001_use      ← 先
  REACHED_s001_free     ← 后
  （各 1 次）
```

**ASan 确认它崩在 `in_dxf.c:12267`（读 `pair->code`），但插桩序列是 `use → free`，不是 `free → use`。**

**→ 这一对（12284 free / 12267 use）在本轮这根插桩上，测不出"先释放后使用"。**

### 可能的原因（没查完）

| 可能 | 说明 |
|---|---|
| **真正的 free 不在 12284** | 那个函数里有 **三处** `dxf_free_pair(pair)`：**12275**（`if (is_dwg_object)` 分支）、**12284**（`else` 分支）、**12287**（内层 while 之后）。ASan 的 "freed by" 栈我只在 **一个** 样本上读过（那是 12284），**别的样本可能走 12275 或 12287** |
| **UAF 跨了调用** | `pair` 可能是在**前一次** `dxf_objects_read` 调用里释放的，本次调用一进来 `use` 就崩 → 序列自然是 `use`，而 `free` 属于下一次 |
| **插桩点和真正读的那条语句有偏差** | 12267 是 `while` 头，`pair->code` 在那里求值；插桩插在它**前面一行**，逻辑等价，但如果崩溃发生在条件求值**之后**的 body，顺序会不同 |

**这一项没有结论，不算通过也不算失败。** 要查清得给三个 free 点各插一个，看哪个先出现。

---

## 补验 2 · 严格解析重判 —— 方向已按你的纠正改，但**仍未复现 488/500**

你的纠正对：**行表要建在原始种子上，不解析产物**；用 `first_diff`（相对原种子的字节偏移）反查落在哪一行。

我照这个改了，但对不上 488/500。**缺 R35 的 `check.py` 无法对账。**

---

## 两项补验的结论

| 项 | 结果 |
|---|---|
| 函数级到达率 | ✅ 测出来了：default 189 / custom 85 / 原始种子 100% |
| 函数级判据的区分力 | ❌ **无**（热路径站点） |
| **序列级判据（free@12284 → use@12267）** | ❌ **对崩溃样本本身都不成立**（序列是 use→free） |
| 严格解析重判 | ⚠️ 未复现 |

### 对 ③④ 的含义（这是本轮最该记的）

**序列级判据的思路是对的，但必须插在"真正的那两个点"上。**
本轮的插桩点（12284 / 12267）**不是**那个 UAF 的实际配对 ——
函数里三处 free，我只挑了一处。

**→ 要用序列级判据，插桩点必须来自"确切的 free 调用点"，而不是"我猜的那个"。**
`facts.json` 里 `sites[kind=free]` 给的是 `dxf_free_pair` 内部的 `free(pair)`（in_dxf.c:515），
**不是调用点**；调用点要自己从 ASan 的 free 栈里读（每个崩溃样本都要读）。

**这条不解决，序列级判据没法自动化。**

---

## 补验 1c · 用你的解法改插桩 —— ✅ **判据成立，而且解释了 617 vs 0**

### 你解开的那个问题

我上一版把 `use` 探针插在 **12266（while 的前一行）**，而回边是跳到 **12267 的条件求值**、
**不经过前一行** → `use` 只在第一次进入时打印一次 → **`free → use` 永远不成立**。
观察到的"use 1 次、free 1 次、use 在前"完全吻合。

### 改法（照你说的两条）

**① `use` 用逗号表达式塞进条件求值**（语义不变，每次求值都打印，且在读 `pair->code` 之前）：

```c
12267:  while ((fprintf (stderr, "REACHED_s001_use\n"), 1) && pair != NULL && pair->code == 0 && pair->value.s)
```

**② 三处 free 全插带行号标记**（倒序：12287 → 12284 → 12275 → 12267）：

```c
12275:  fprintf (stderr, "REACHED_s001_free@12275\n");   ← if (is_dwg_object) 分支
12285:  fprintf (stderr, "REACHED_s001_free@12284\n");   ← else 分支
12289:  fprintf (stderr, "REACHED_s001_free@12287\n");   ← 内层 while 之后
```

### 先验崩溃样本 —— ✅ **判据 True**，而且定位到了具体哪一处

```
REACHED_s001_use
REACHED_s001_free@12284     ← 走的是 12284 那处
REACHED_s001_use            ← 回边又读了已释放的 pair → ASan 崩
```

**`free@12284` 在最后一次 `use` 之前 → 判据 True。**
**不用读 ASan 栈，插桩直接告诉你是哪一处。**

### 两臂各 1000（种子 `Constraints.dxf`）

| 臂 | n | free@12275 | **free@12284** | free@12287 | 任意 free→use | **严判据：free@12284 后又 use** |
|---|---:|---:|---:|---:|---:|---:|
| **custom（`d7913b9e`）** | 1000 | 946 | **92** | 0 | 950 | **92** |
| **default（字节翻转）** | 1000 | 912 | **1** | 0 | 912 | **1** |
| 崩溃样本 | 1 | — | ✓ | — | — | **TRUE** |

### 🔴 这张表解释了 617 vs 0

| 指标 | custom | default | 倍数 |
|---|---:|---:|---:|
| 走到 `free@12275`（**安全的** if 分支） | 946 | 912 | 1.04× ← **没有区分力** |
| 走到 `free@12284`（**危险**的 else 分支） | **92** | **1** | **92×** ← **这就是区分点** |
| 严判据（12284 释放后又回边读） | **92** | **1** | **92×** |

**→ 上一轮"有 free 950 vs 912"之所以没有区分力，是因为它把 12275（if 分支，安全）算进去了。**
**真正的区分点是 12284 —— 那个 `else` 分支（对象名不被 `is_dwg_object` 识别）才是 UAF 的来源。**
**这正是 custom 算子在构造的东西：随机名字让它走 unknown 分支。**

**→ 序列级判据成立，而且定位了 617 vs 0 的机制。**

### 但注意一个量级差

严判据 **9.2%**（92/1000），而 A/B 的崩溃率是 **0.096%**（617/640359）。
**差 96 倍** —— 走到序列 ≠ 一定崩（还要看内存有没有被重新分配、指针有没有被覆盖）。
**→ 序列级判据可以正向排序，但"能不能崩"是更细的条件。**

---

## 补验 2 · 严格解析重判 —— ✅ **精确复现 488/500**

用你给的 `dxf_lines()`（行表建在**原始种子**上）+ `first_diff` 反查 + no-op 桩
（和 `drv.c` 一致，只走策略路径）：

```
产物 500 个，改动落在组码行 12 个 → 合规 488/500
违规偏移分布: [(26353, 6), (26367, 4), (26328, 2)]
```

**488/500 精确复现** ✅，12 处全部落在 **26328–26367** 这一段
（你说的 26353 是最多的一个，6 次；另有 26367 四次、26328 两次 —— 都在同一处 4 位组码附近）。

**这是预期的：`4864893e` 有 2.4% 的产物 DXF 结构非法，而旧门禁和算子用同一套 ≤3 位解析，
所以一起 desync、一起判"无违规"。**

---

## 两项补验的最终结论

| 项 | 结果 |
|---|---|
| 函数级到达率 | default 189 / custom 85 / 原始种子 100% → **无区分力**（热路径） |
| **序列级（free@12284 → 再次 use）** | **custom 92 / default 1 / 崩溃样本 TRUE** → ✅ **有强区分力（92×）** |
| 严格解析重判 | ✅ **488/500 精确复现** |

**→ ③④ 可以按序列级判据做，而且它把"哪个 free 点是危险的那个"直接测出来了。**

---

## 改动 ③ · agent 扫描接进流程 —— ✅ 完成

### 搬了什么

新建 **`pipeline/s5_8_agent_scan.py`**，暴露 `agent_scan_sites(shortlist_funcs, src_cache, crash_type)`。
内容按 R26b 实测那套**原样搬**，一个参数都没改：

| 项 | 值 |
|---|---|
| 调用方式 | 单次 LLM 调用（无工具循环） |
| 喂什么 | 只喂函数体 |
| 输出 | 纯 JSON 数组 |
| 预过滤 | 按崩溃类型查表（uaf: `*free*`/`delete`/`realloc`） |
| schema | **`use_lines` 数组，最多 3 个** |
| 实例数 | **两个独立实例**，都圈到 = high |

接进 `run_feature`（`s5_4_analyze.py:2120` 之后），每条 site 带 `source: "agent"`，
工具扫的带 `source: "tool"` —— **已传到产物**。

### 验收

| 检查 | 要求 | 实际 |
|---|---|---|
| **标尺** | `src/in_dxf.c:12284 → 12267` 在 agent 里、置信度 high | ✅ **在**，`high`，`obj=pair` |
| 候选数 | R26b 配对后 42 | **58 条**（agent）+ 2 条（tool）= **60** |
| 增量 | agent 圈到但正则没扫到的 | **58 / 58** 全部是 agent 独有（正则只扫出 2 条） |
| 漏检 | 正则扫到但 agent 没圈到的 | **0**（正则那 2 条 agent 也圈到了） |
| 成本 | 对照 2.6 分钟 / 502k | 4 个特征各跑一遍约 **11 分钟**（含 4 次 154–171 条的 agent 调用） |
| pytest | 全绿 | ✅ 35 passed |

### 一个必须记的细节

**agent 圈出的条数比 R26b 多（58 vs 42）**，原因是这次的 site 是**跨特征合并**后的
（4 个特征各跑一遍 agent，然后并集去重）。**不是变松了** —— 核对层（程序）一条没放宽。

### 修的一个 bug

第一次接进去报 `KeyError: 'name'` —— `shortlist()` 返回的函数键是 **`function`**，不是 `name`。
改成 `f.get("function") or f.get("name")`。

---

## 改动 ④ · 执行门禁筛站点 —— ❌ **未做**

本轮时间只到 ③。

④ 需要的东西已经齐了（`llvmfuzz_probe` 验过、插桩规则定了），但还没实现：

| 待做 | 说明 |
|---|---|
| `s5_7_reach.py::rebuild_probe(sites)` | 按候选集**倒序**插桩、重编；候选集 hash 做缓存键 |
| `s5_7_reach.py::reach_probe(site, seed, n)` | 让 probe 自己当 fuzzer 跑 n 次，数 `REACHED_<sid>_free@<line>` / `REACHED_<sid>_use` |
| `run_feature` 里 `classify` 不过的不扔 | 改成交给 `reach_probe` |
| 排序改成 `ratio = custom/default` | 实测 ratio：`12284` 是 92×、`12275` 是 1.04× |

**R19 那 4 条跨函数特征的命中情况**：本轮**没测**（要 ④ 才能回答）。

---

## 改动 ④ · 执行门禁筛站点 —— ⚠️ **基础设施搭好了，但数字对不上，未收敛**

### 做出来的东西

**`pipeline/s5_7_reach.py`**（新建）：

| 函数 | 内容 |
|---|---|
| `rebuild_probe(sites, free_call_sites, force)` | 候选集 **hash 做缓存键**；按文件分组、**倒序插桩**；use 点若是条件头用**逗号表达式**、否则插前一行；helpers 插在**第一个 `#include` 之后**；`g_r36_free` 用 **weak 定义**（否则 `programs/` 链接失败）；**同时编 default 和 custom 两个变体** |
| `reach_all(probe_bin, slot_map, seed, n)` | 两臂各跑 n 次，grep `SEQ_*` / `FRI_*@line` / `FRX_*@line`，算 `ratio = custom/max(default,1)` |
| `_free_points(site, free_call_sites, fn_start)` | 该函数**所有**释放点；`free_call_sites` 是**函数内相对行号**（`line_in_func`），换算成绝对行 = `fn_start + line_in_func`（`fn_start` 是 `lines[0]`，即 `static int` 那行） |

**插桩分两种**（这是按 0.3 的教训改的关键）：

```c
#define R36_OWN(s, ln)   do { g_r36_free[s] = 1; fprintf(stderr,"FRI_%d@%d\n",(s),(ln)); } while(0)
#define R36_OTHER(s, ln) do { fprintf(stderr,"FRX_%d@%d\n",(s),(ln)); } while(0)
```

**own = 站点自己的 `free_line`**（置位，后面的 use 才可能是 UAF）；
**other = 同函数其它 free 点**（只计数，不置位）。

> 中间踩过一次：一开始所有 free 点共用同一个 slot → `12275`（安全分支）也会置位 →
> 标尺 ratio 变成 **1.0**（`custom 45999 / default 45999`），**完全重现了 0.3 说的"混在一起就没区分力"**。

### 修完之后的实测：**没复现出 92×**

```
s001（标尺 12284→12267）
  custom  = 0
  default = 0
  ratio   = 0.0
  free_points = {"12275": 46000}     ← 只有 if 分支被走到，12284（else 分支）**一次都没走到**
```

**和 R36-② 手工插桩测出的 `custom 92 / default 1` 不一致。** 1000 次里 `else` 分支（12284）
**一次都没执行**，而 ② 那次是 92 次。

### 差在哪 —— 三个已知差异（没查完）

| # | 差异 | 影响 |
|---|---|---|
| 1 | ② 那次是**单个**站点、手工插在 `in_dxf.c` 里；这次是**同一套 weak 定义 + 两个宏**、走脚本插入 | 插入位置可能和手工不同（`R36_OWN` 插在 `dxf_free_pair` 的**前一行**，② 也是前一行，应该等价） |
| 2 | ② 那次的 custom 臂是 `llvmfuzz_probe3_custom`（链接 `/tmp/m.o`）；这次是 `_multi_*_custom`（同样链接 `/tmp/m.o`） | 应该等价 |
| 3 | **② 那次 `g_r36_free` 是每次 run 从头开始的**；这次是 `weak` 全局、**跨 run 不复位** —— `R36_OWN` 置位后只有 `r36_chk` 会清零 | ⚠️ **这个最可疑**：第一次 run 之后 slot 一直是 1，`SEQ` 只在真正配对时才打；但 `FRI_@12284` **一次都没有**说明 12284 确实没执行，不是复位问题 |

**第 3 条排除了"复位问题"**：`free_points` 里连 `12284` 这个键都没有 → 这个 free 点**确实一次都没走到**。

### 所以现在的问题不是插桩，是"为什么这次的 1000 次没走到 12284"

② 那次走到 92 次，这次 0 次。**两次的 custom 算子、种子、n 都一样。**
差别只在"**probe 二进制本身**" —— 这次是**带 weak 全局 + 两个宏 + 脚本插入**的版本。

**未查清。** 下一步应该：用这次的二进制跑一次，`grep FRX_` 看 12275 之外还有没有别的 free 点被走到；
再把 ② 那个手工版和这次的脚本版做一次 `diff`（插桩后的 `in_dxf.c`）。

### 本轮 ④ 的结论

| 项 | 状态 |
|---|---|
| `rebuild_probe` / `reach_all` 实现 | ✅ 能跑通（编译、链接、两臂、缓存） |
| 标尺 ratio ≈ 90× | ❌ **未复现**（这次是 0） |
| 58 条候选的 ratio 分布 | 未做（标尺都没对，先不铺开） |
| R19 那 4 条跨函数特征 | 未测 |
| `skipped` | 0（单站点这次编译链接都过） |
| plan 排序 | 未做 |

**按铁律「标尺不过就停下查」—— 停在这里，没有往下铺 58 条。**

---

## 改动 ④ · 诊断与修复 —— ✅ **标尺 92.0× 精确复现**

### 诊断 1（行号换算）—— 换算对，但上次报的"少减 1"是误报

实测映射（`fn_start = lines[0] = 12260`）：

| `line_in_func` | `+k` → 绝对行 | 那一行的真实内容 |
|---:|---:|---|
| 15 | 12275 | `dxf_free_pair (pair);` ✅ |
| 24 | 12284 | `dxf_free_pair (pair);` ✅ |
| 27 | 12287 | `dxf_free_pair (pair);` ✅ |
| 31 | 12291 | （第 4 处） ✅ |

**`fn_start + line_in_func`（不减 1）才是对的** —— 因为 `fn_start` 是 `static int` 那行、
`line_in_func` 从**签名行**算起，两个偏移刚好抵消。**行号不是根因。**

### 诊断 2（单语句 if/else）—— 不是问题

那处 `else` 带 `{`：

```c
else
  {
    DXF_RETURN_ENDSEC (0);
    LOG_WARN ("Unhandled 0 %s (%s)", name, "objects");
    dxf_free_pair (pair);          ← 12284
  }
```

插一行不会改控制流语义。

### 🔴 真正的根因：**测量方法不一致**

| ② 那次 | 我上次的 `reach_all` |
|---|---|
| **喂 1000 个预生成的产物**，每个 `probe -runs=1 "$f"` | `probe -runs=1000 <seed>` —— **让 fuzzer 自己变异** |

**两次的算子、种子、n 都一样，但一个喂产物、一个让 fuzzer 自造。** 结果 92 vs 0。

`reach_all` 已改成**喂预生成产物**（`mutants_dir={"custom":..., "default":...}`），
逐产物 `-runs=1`，和 ② 完全同一口径。

### ✅ 修好之后的实测

```
标尺 s001（src/in_dxf.c:12284 → 12267）
  custom = 92
  default = 1
  **ratio = 92.0×**          ← 和 R36-② 手工插桩那次一模一样
  free 点分布 = {12284: 1, 12275: 41681, 12291: 2}
```

**92.0× 精确复现** ✅ —— 而且 `free_points` 这次**有 `12284` 这个键**了。

（`12284` 只记 1 次，是因为 `R36_OWN` 只在**首次**打印；真正的命中数看 `SEQ` = 92。）

### 加的自检（你要求的第 4 条）

`rebuild_probe` 插桩前，对**每个 free 插桩点**断言目标行真的含 free 家族调用：

```python
FREE_FAMILY = re.compile(r"\b(?:\w*(?:free|Free|FREE)\w*|delete|realloc)\s*\(")
```

**不过就 `die`（返回 `skipped` 并清掉源码副本），不静默插到错的行上。**

验证（故意传 `12283`）：

```
故意错行号 -> 二进制: None | skipped:
  [(0, 'insert_point_not_free@L12283: LOG_WARN ("Unhandled 0 %s (%s)", name, "objects");')]
```

**自检挡住了，并打印了那一行的真实内容** —— 这正是这次吃的亏。

### ④ 现在的状态

| 项 | 状态 |
|---|---|
| `rebuild_probe` / `reach_all` | ✅ 通（编译、链接、两臂、缓存、自检） |
| **标尺 ratio** | ✅ **92.0×**（与 ② 一致） |
| 58 条候选铺开 | **下一步**（标尺对上了，可以铺） |
| R19 那 4 条跨函数特征 | 下一步 |
| plan 排序 | 下一步 |

---

## 改动 ④ · 铺开 58 条 —— ❌ **没铺成，卡在一个具体的实现 bug 上**

### 钉死的三件事（已写进 `s5_7_reach.py`）

| # | 内容 |
|---|---|
| 1 | **default 代理固定进代码**：`PROXY_C` 常量 + 注释标明"这是代理，不是真 `LLVMFuzzerMutate`（后者脱离 libFuzzer 会 SEGV）"；RNG **逐产物递增**，不用时间 |
| 2 | **产物共享**：`make_mutants()` 一次生成两臂各 1000 个，58 个站点全插一个 probe → 2000 次执行拿全部 ratio |
| 3 | **缓存键含插桩版本** `INSTR_VERSION = "v2"`（第一版吃过亏：只 hash 站点坐标，改了插桩逻辑还是复用旧二进制） |

### 铺开的实际结果

```
规整后站点 60
插桩成功 44，skipped 16（全是插入后语法错：插在 #if 0 里、else 和 { 之间、宏展开中间）
44 个站点 ratio **全部 0**
```

**标尺 `q001`（12284→12267）也是 0** —— 而单站点那次是 **92.0×**。

### 🔴 根因（已定位，未修）

`in_dxf.c` 里有**多个**站点，我是**逐站点**插入的：

```
for (i, s2) in items:          # 同一文件的每个站点
    ins = [[_shift(ln), i, kind] ...]
    # 插入 + 语法检查
```

**每个站点插入后没有重算后续站点的行号** → 偏移**累积**：

```
instrumented 文件里：12338:  R36_OWN(1, 12302);     ← 注释里的 12302 是对的
  但 dxf_free_pair 那一行此时已经不在 12302 了（前面 20 个站点各插了几行）
```

验证：拿崩溃样本跑多站点二进制，**只有 `FRI_22@1292` 一个标记出现**
（slot 22 那个站点在文件里靠前，还没被后续插入推移），标尺 slot 1 **一次都没出现**。

**这正是你一开始说的"倒序插，否则前一次插入会让后面的行号移位"** ——
我在**单个站点内部**做了倒序（`sorted(INS, key=-line)`），但**站点之间**没有。

### 修法（明确，下一轮直接做）

**同一文件的所有站点一次性批量插入，全局按行号倒序**：

```python
all_ins = []
for i, s2 in items:
    all_ins += [[ln, i, "own"/"other"] for ln in free_points(s2)]
    all_ins += [[s2["use_line"], i, "use"]]
# 全局倒序，一次插完
for ln, i, kind in sorted(all_ins, key=lambda t: -t[0]):
    ...
```

然后**整文件**语法检查；坏了再退回"逐站点 + 每次重算偏移"的慢路径。

### 本轮 ④ 铺开的验收表

| 检查 | 要求 | 实际 |
|---|---|---|
| 标尺 ratio 仍 ~90× | 铺开后要重确认 | ❌ **0**（偏移累积导致插到错行） |
| ratio 分布（44 条） | >10× / 2–10× / ≈1× / 0 | **44 条全 0**（不可用） |
| R19 那 4 条跨函数特征 | 有站点了吗 | 未测 |
| 热路径站点 | ratio≈1 的几个 | 无法判定 |
| per-free-point 分布 | 各站点走到哪些 free 点 | 只有 `FRI_22@1292` 一个 |
| skipped | 几个、原因 | **16 个**，全是插入后语法错 |
| plan | 几个 mutation / ratio | 未做 |

### 其它两条发现（与这个 bug 无关，但是真结果）

1. **agent 给的 `free_line` 有一部分不是释放调用** —— 最初的自检把 59/60 拦下来了
   （例如 `L12839: pair = NULL;`、`L772: return 0`）。加上"读干净源"的修正后仍有若干条不合格。
   **这是 agent 准确率的问题，值得单独记。**
2. **自检本身也写错过一次**：我一开始把 **use 行**也要求"必须含 free 调用"，
   而 use 行本来就该是读取点 → 一次性拦掉 43 个。已修。

### 结论

**④ 的判据和单站点验证是成立的（92.0×），但"一次全插"的批量实现有一个明确的偏移累积 bug。**
按铁律「标尺不过就停下」—— **没有铺开 58 条的 ratio，也没有动 plan**。

修法已经明确（同一文件全局倒序批量插入），下一轮可以直接做。

---

## 改动 ④ · 第二轮修（倒序插入）—— 有进展，但仍未通过快速自检

### 改了什么

按你的修法，把"逐站点按列表顺序插"改成**按站点最大行号从大到小插**，每插一个就 `-fsyntax-only`、坏了回滚。

| 指标 | 上一轮 | 这一轮 |
|---|---:|---:|
| 插桩成功 | 44 | **50** |
| skipped | 16 | **10** |
| 二进制 | 编出来了 | 编出来了 |

**skipped 分类（10 个，全是语法错）**：

| 原因 | 条数 | 例子 |
|---|---:|---|
| `expected expression`（插在表达式中间 / 宏实参里） | 5 | `encode.c:1315`、`in_dxf.c:12272`、`in_dxf.c:12301` |
| `expected ')'`（插在函数调用的实参列表里） | 2 | `in_dxf.c:11904/11905` |
| `expected identifier or '('`（插在函数外） | 1 | `in_dxf.c:788` |
| `'case' statement not in switch statement` | 1 | `in_dxf.c:12351` |
| 其它 | 1 | `dwg.c:191` |

### 🔴 但快速自检没过

崩溃样本跑一次多站点二进制：

```
2 FRI_22@1274   8 FRI_24@772   8 FRI_25@772   202 FRI_26@1049
2 FRI_29@1292   4 FRI_57@12709
1 SEQ_26        1 SEQ_29       4 SEQ_57
```

**标尺 slot 1 的 `FRI_1@12284` 没出现。**

### 根因（这次定位得更准）：**排序方向治不了累积偏移**

插桩后的文件里，标尺**确实插进去了**：

```
12322:  while (r36_chk(51) && r36_chk(1) && pair != NULL)     ← use 点插对了
12340:  R36_OWN(1, 12284);                                    ← free 点也插了
```

但 **12340 ≠ 真正的 `dxf_free_pair` 那一行**。因为：

- 按**行号从大到小**插 → 比 12284 **大**的站点（如 12301、12272）**先插**，各插了几行 → 把 12284 **往下推**
- 按**从小到大**插 → 比它**小**的站点先插 → 同样把 12284 **往下推**

**两个方向都躲不掉** —— 只要有多次插入，就用不了"原始行号"。

### 正确修法（明确，下一轮做）

**一趟构造输出列表**，不要"插"：

```python
ins_by_line = {}          # 原始行号 -> 要插在这一行前面的语句
for site in sites:
    ins_by_line.setdefault(free_line, []).append(...)
    ins_by_line.setdefault(use_line, []).append(...)

out = []
for n, line in enumerate(original_lines, 1):
    if n in ins_by_line:
        out.extend(ins_by_line[n])
    out.append(line)      # use 点是条件头时，改这一行本身
```

**原始行号一次算好、一遍写出，不存在偏移问题。**

（这样"逐站点语法检查 + 回滚"要改成"整文件检查 + 定位坏站点再排除"，是另一处改动。）

### 附带的 two 条已落地

| # | 内容 |
|---|---|
| 1 | `docs/verified_sites.json` 里 `dwg_read_dxf:12839 → 12842` 从"存疑"改成**假**，依据「R36 实测 free_line 是 `pair = NULL`，非释放调用」 |
| 2 | 自检函数的注释里写明「**free 点查 free 家族调用；use 点是读取点，不查**」—— 我一开始把 use 行也要求含 free，一次拦掉 43 个 |

### 验收表（本轮 ④ 第二轮）

| 检查 | 要求 | 实际 |
|---|---|---|
| **快速自检**（崩溃样本 → 标尺 slot 出现） | 必须过 | ❌ **没过** |
| 标尺 ratio ~90× | | 未测（自检都没过，不跑 2000 次） |
| ratio 分档 | | 未做 |
| R19 那 4 条特征 | | 未做 |
| per-free-point | | 只有 `FRI_22@1274` 等 6 个 |
| skipped | 分类报 | ✅ **10 个，已分类** |
| plan | | 未做 |

**按你定的必要条件「崩溃样本跑一次标尺 slot 必须出现」—— 没过就不跑 2000 次。停在这里。**

---

## 改动 ④ · 第三轮：你纠正了我的诊断，二分结果把范围缩到**框架本身**

### 你对"累积偏移"的纠正 —— 我错了

倒序插时每个插入点都在已处理点**之前**，所以更小的行号不受影响。
`12272 < 12284`，它在标尺**之后**才处理，那时标尺已插完，两者相邻、一起被推下去，**相对位置不变**。
**`12340` 是正常的（12284 + 56 行累积插入）。**

### 第一步验证（一行）

`sed -n '12338,12344p'` 插桩后的文件：

```
            {
              R36_OWN(51, 12284);
              R36_OWN(1, 12284);
              R36_OWN(50, 12284);
              DXF_RETURN_ENDSEC (0);
              LOG_WARN ("Unhandled 0 %s (%s)", name, "objects");
              dxf_free_pair (pair);
```

**→ 插桩位置是对的**（同一个 `{ }` 块内、紧邻目标行；另外两行是站点 50/51 共享同一个 free 点，正常合并）。

### 第三步 · 二分加站点 —— 结果出乎意料

标尺固定为第一个，其余按顺序加：

| N 个站点 | 标尺标记（崩溃样本跑一次） | skipped |
|---:|---|---:|
| **1** | **（无）** | 0 |
| 2 | （无） | 0 |
| 4 | （无） | 0 |
| 8 | （无） | 1 |
| 16 | （无） | 2 |
| 32 | （无） | 6 |

**N=1 就已经失效** —— **不是加站点加坏的，是"多站点框架"本身把这个站点弄坏了。**

### 上一轮那次为什么成了（92.0×）

对比两次 1 站点的实现，差别只有一处：

| | 成功那次 | 现在 |
|---|---|---|
| helpers 插入 | 先插（16 行） | 先插（16 行） |
| 探针行号 | **原始行号，没加偏移** | **加了 `_shift()`（+16）** |

**成功那次的探针其实落在目标行**上面** 16 行**（在那个 while 循环体附近），
**现在落在"正确"的位置上，反而不触发了。**

**→ 说明"正确位置"上的插桩改了控制流** —— 这正是你第二步说的那个嫌疑。
最可能在 `while (r36_chk(1) && pair != NULL ...)`：

- 逗号表达式/函数调用塞进 `while` 条件，**每次条件求值都调用一次函数**
- 如果这个 `while` 里 `pair` 的推进依赖副作用的**求值次数或顺序**，会改变行为
- 而 `chk_` 返回 1、语义上"应该"不变 —— 编译器也不报错

**但这一点还没验证。** 下一步应该：只插 **use 点**（不插 free 点）跑一次崩溃样本；
再只插 **free 点**（use 用原来的前一行插法）跑一次 —— 看是哪一个把执行弄坏的。

### 你给的第 4 步（静态检查）仍要做

插桩前检查目标行**上一行**（去注释空白后）是不是 `if (...)` / `else` / `for (...)` / `while (...)`
结尾且**不带 `{`**；是 → 用 `{ }` 包起来，或 skip 并记 `insert_into_braceless_body`。

### "一趟构造输出"的修法

**仍然值得改**（消除整类偏移风险、比 50 次 `-fsyntax-only` 快），
但按你的话：**别指望它修好这个问题 —— 根因是语义，不是偏移。**

### 现在的状态

| 项 | 状态 |
|---|---|
| 插桩位置 | ✅ 正确（第一步验证过） |
| 累积偏移 | ✅ 不存在（你纠正对了） |
| **N=1 的标尺标记** | ❌ **不出现** |
| 二分定位 | ✅ **不是加站点的问题，是框架本身** |
| 下一步 | 分离"只插 use" vs "只插 free"，定位是哪一个改坏了控制流 |
| 2000 次 | **没跑**（自检不过） |

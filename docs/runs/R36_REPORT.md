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

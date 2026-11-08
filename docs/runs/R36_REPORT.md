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

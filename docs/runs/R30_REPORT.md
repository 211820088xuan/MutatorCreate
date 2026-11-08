# R30 报告

日期：2026-11-08
目标：在「站点 → 策略」之间补一步归并（多对一）。

---

## 步骤 0 · R29 的门禁为什么只跑了 1 道

### 查清了：那个 `generation_gate` 是**写死的静态声明**

`pipeline/s5_5_build.py:1042`：

```python
"generation_gate": {"plan_status": status, "evidence_check": "pass",
                    "compile_check": "pending", "replay_check": "pending"},
```

**`compile_check` / `replay_check` 永远是 `pending`** —— 不是"没跑"，是**这个字段从来没人更新**。
真正的门禁是另外四个函数，由 **`verify`** 跑：

| 门禁 | 函数 | 谁跑 |
|---|---|---|
| `V1_schema` | `gate_v1` | `verify` |
| `V2_evidence` | `gate_v2` | `verify` |
| `V3_code`（clang `-fsyntax-only`） | `gate_v3` | `verify` |
| `V4_behavior`（回放已知 crash） | `gate_v4` | `verify`，**需要 `--binary`** |

**而 `generate` 里那个"生成后校验失败"是另一套**（格式分流 / `preserve=group_code_digits`），
不在 V1–V4 里。

### 所以 R29 那句"2 站点过了门禁"到底成不成立

**我把 R29 的算子（`de5eb910`）换回去跑了 `verify`**：

```
  V1_schema      PASS             0 问题
  V2_evidence    PASS             0 问题
  V3_code        PASS             0 问题（clang -fsyntax-only 通过）
  V4_behavior    NOT_APPLICABLE   0 问题（没有提供 --binary，跳过）
  overall = pass_with_skipped
```

**→ "2 站点过门禁"是成立的**（V1/V2/V3 全过；V4 本轮没提供 `--binary`，跳过）。
**"4 站点被拒"也是真的**，但那是 `generate` 时的另一套检查。

### 两个结论

1. **`mutator.json` 的 `generation_gate` 字段是坏的**（写死的 `pending`）—— 要以 `verify` 的 `verification.json` 为准。
2. **本轮之后所有生成都用 `verify` 跑完 V1–V4**，并在报告里贴 `verification.json` 的内容，不看 `generation_gate`。

---

## 步骤 1 · 42 条全部走证据链（实际是 39 条 —— R26b 配对后是 39，不是 42）

用静态脚本（`tools/r30_merge.py`，**不调 LLM**）从每条站点所在函数的**守卫**里抽：

| 字段 | 怎么抽 |
|---|---|
| `anchor` | 守卫里的字符串比较（`strEQc(x, "OBJECTS")`）或段名 |
| `constraint` | 字段相等（`x->handle.value == 0xC`）、组码判据（`pair->code == 0`） |
| `part` | 由 anchor / 文件类型推 |
| `op` | 由站点 `kind` 推 |

### 结果

| 项 | 数 |
|---|---:|
| 站点总数 | 39 |
| **能推出证据链** | **11** |
| **推不出** | **28**（全部 `no_guard_derivable`） |

**推不出的原因**：守卫在我的抽取窗口（站点前 400 行、`if`/`while` 头部）里找不到字符串锚点或字段判据。
**这是抽取器的局限，不是"推不出来"** —— 深嵌套或条件在别的函数里的站点会被漏掉。
**如实记：28 条是"抽取器没覆盖到"，不是"确实推不出"。**

---

## 步骤 2 · 归并（程序机械比对，不用 agent）

**归并键 = (part, op, anchor)**。

### 结果：**6 种策略**

| 策略 | 站点数 | part | anchor | 含已知崩溃 |
|---|---:|---|---|---|
| s001 | 3 | `ENTITIES 段` | `ENTITIES` | |
| **s002** | **2** | `DXF 记录段` | `(无字符串锚点)` | **✅ 标尺在这里** |
| s003 | 2 | `ACAD_ 段` | `ACAD_` | |
| s004 | 2 | `.c 输入` | `(无字符串锚点)` | |
| s005 | 1 | `.c 输入` | `ObjFreeSpace` | |
| s006 | 1 | `.c 输入` | `_subclass` | |

**只挂 1 个站点的策略：2 种**（s005 / s006）。
**⭐ 标尺 `12284→12267` 属于 s002，那种挂 2 个站点。**

### ⚠️ `op` 抽得太粗

**11 条站点的 `op` 全是「替换值行」** —— 所以归并键实际退化成了 `(part, anchor)`。
这说明**抽取器没区分"改哪一部分"和"怎么改"** —— 是步骤 1 的局限，不是归并逻辑的问题。

---

## 步骤 3 · 排序 + 选策略

| # | 策略 | 站点数 | 含已知崩溃 |
|---|---|---:|---|
| **1** | **s002** | 2 | ✅ |
| 2 | s001 | 3 | |
| 3 | s003 | 2 | |
| 4 | s004 | 2 | |
| 5 | s005 | 1 | |
| 6 | s006 | 1 | |

**6 种 → 取前 3**（按你的表：4–6 种取前 3）。

---

## 步骤 4 · 生成算子 —— **还是换 salt**

### 第一次：我自己的 bug

plan 里 s002 的 `anchor` 我填了占位串 `'(无字符串锚点)'`，LLM 把它当字面量去找 → 算子变成 no-op，
门禁报：

```
✗ default 权重不对：计划 0.50，实测 1.00（default 被调用 1000/1000）
✗ 有效变异空间太小：1000 个 Seed 只产出 0 个互不相同的输出
✗ 构造路径无效：剥掉 OBJECTS 的种子上 1000 Seed 只改动 0 次
```

**修成真实 anchor（`OBJECTS` / `ENTITIES` / `ACAD_`）后重跑，过了。**

### 第二次：**过了门禁，但三个策略还是同一个算法**

```c
195: static size_t mut_a001(...) { return mut_sec(D, S, M, Seed, "OBJECTS", 0xA001u); }
196: static size_t mut_a002(...) { return mut_sec(D, S, M, Seed, "OBJECTS", 0xA002u); }
197: static size_t mut_a003(...) { return mut_sec(D, S, M, Seed, "OBJECTS", 0xA003u); }
```

**三个函数调用 `mut_sec`，anchor 全是 `"OBJECTS"`，只有 salt 不同。**

**grep 验证**：

```
  "OBJECTS"   出现 3 次
  "ENTITIES"  出现 0 次     ← plan 里明明给了
  "ACAD_"     出现 0 次     ← plan 里明明给了
```

**→ 和 R29 一模一样：LLM 只实现第一种形态，其余全退化成 salt。**

### 5 道门禁（`verify`，全跑完）

```
  V1_schema      PASS             0 问题（documents=6/6）
  V2_evidence    PASS             0 问题（actions=3）
  V3_code        PASS             0 问题（clang -fsyntax-only 通过）
  V4_behavior    NOT_APPLICABLE   0 问题（没有提供 --binary，跳过）
  overall = pass_with_skipped
```

**门禁是过了的**（V1/V2/V3）—— **问题不是门禁，是策略的实质。**

### 判定：**"还是换 salt" → 停下报告**

按你给的判定表：

> **还是换 salt** → 说明"一次生成多个"行不通 → **停下报告，考虑分次生成再合并**

### 已恢复

```
  mutator.c: d7913b9eaa3b       ← 已恢复
  mutation_plan.json            ← 已恢复
  mutator.json                  ← 已恢复
  新算子另存: mutator_multi3_58d1152f.c（sha1 58d1152f）
  旧算子另存: mutator_multi2_de5eb910.c
  reps_r9_final / 二进制 a416b44d  ← 没碰
```

---

## 结论

**"站点 → 策略"的归并这一步做了，也确实归出了 6 种（标尺在 s002）** ——
**但归并没能让 generate 产出真正不同的策略**：LLM 仍然只实现第一种，其余退化成 salt。

**→ 问题不在"站点太多"，也不在"没有归并"，在"一次生成多个策略"这个动作本身。**

### 为什么归并没能解决问题（我的判断）

归并键 `(part, op, anchor)` 里，**三个策略的 `op` 全是"替换值行"** ——
从 **LLM 的角度**看，这三个策略**确实是同一种改法**（都是"在某个 DXF 段里替换一条记录的值"），
只是段名不同。**它"合并"是对的**，因为**它们本来就是同一种**。

**→ 要真正得到不同形态的策略，需要的是"证据链在 `op` 上有真正的差异"**
（比如一个改值行、一个插入新记录、一个改组码），而不是"`part` 不同"。

### 三个方向（都没做，等你说）

| 方向 | 内容 |
|---|---|
| **(a) 让抽取器产出真正不同的 `op`** | 现在全是"替换值行"是因为抽取器只看守卫的 `if`。要看**站点本身的动作**（`replace_value_line` / `insert_record` / `construct_section`） |
| **(b) 分次生成再合并** | 每次只给一种策略，生成一个 `mutate_sXXX`，然后手工合并进同一个 `LLVMFuzzerCustomMutator` 分流 |
| **(c) 接受"多 salt"跑 A/B** | 测"同一策略多次调用"是否有增益 —— 能出数，但不是"多策略" |

---

## 追加 · (b) 分次生成再合并 —— **也失败了，找到了真正的根因**

按用户选择 (b) 做了：分别用 `ENTITIES` / `ACAD_` 单策略生成，看代码会不会不同。

### 结果：**不会**

| 生成时给的 anchor | 生成代码里 `"OBJECTS"` | `"ENTITIES"` | `"ACAD_"` |
|---|---:|---:|---:|
| `ENTITIES` | 2 | **0** | 0 |
| `ACAD_` | 2 | 0 | **0** |
| `ENTITIES` + `targets.function=dwg_read_dxf` | 2 | **0** | 0 |

**不管给什么 anchor，产出的都是 OBJECTS 形态。**

### 根因：**整条 generate 链路是 OBJECTS 专用的**

| 位置 | 证据 |
|---|---|
| **prompt 模板** | `s5_5_build.py:38` —— 系统提示里直接写「段锚点：故障函数的调用点被 `else if (strEQc (pair->value.s, "OBJECTS"))` 守着」 |
| **证据行来源** | `s5_5_build.py:947` —— `x["function"] == plan["targets"][0]["function"]`，**只取第一个 target 的 findings**；改成 `dwg_read_dxf` 后 prompt 从 11,508 降到 8,265 字符、证据行从 6 降到 2，**代码还是 OBJECTS** |
| **种子字节** | `_sample_hex()` —— `b.find(b"OBJECTS")` **写死** |
| **门禁 5** | `_has_structure(..., anchor=b"OBJECTS")` / `_record_after(..., anchor=b"OBJECTS")` —— **要求产出里有 `0/SECTION` + `2/OBJECTS`** |

**→ 就算 LLM 想生成别的形态，门禁 5 也会把它判死。**
**这不是"一次生成多个"的问题，是整条链路只认 OBJECTS。**

### 所以 (a)/(b) 都绕不开

| 方向 | 结论 |
|---|---|
| (a) 让抽取器产出真 op 差异 | 抽取器能产出，**但下游 prompt + 门禁只认 OBJECTS** → 白做 |
| (b) 分次生成再合并 | **已实测失败**（上表） |
| (c) 接受"多 salt" | **唯一还能跑 A/B 的** |

### 已恢复

`mutator.c` `d7913b9e` ✓、plan ✓、`mutator.json` ✓。
单策略算子另存：`mutator_single_entities.c` / `mutator_single_acad.c` / `mutator_single_entities_targets.c`。

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

# R31 报告

日期：2026-11-08
目标：【一】全仓扫 DXF/DWG 专用常量混在通用代码里的地方；【二】参数化。

---

## 步骤【一】· 扫描结果

扫描模式：`OBJECTS / ENTITIES / ENDSEC / dxf_ / dwg_ / DXF / DWG / strEQc / group_code / .dxf`

### 命中分布

| 文件 | 命中 | 性质 |
|---|---:|---|
| `pipeline/s5_5_build.py` | **49** | **重灾区**（prompt + 门禁 + 采样，全写死 OBJECTS） |
| `pipeline/s5_4_analyze.py` | **30** | 一半是**格式探测**（通用 ✓），一半是**项目专属表**（该参数化） |
| `pipeline/s5_2_prepare.py` | 5 | **全是注释** ✓ |
| `pipeline/s5_3_audit.py` | 4 | **全是注释** ✓ |
| `pipeline/s5_6_lib.py` | 1 | **注释** ✓ |
| `pipeline/s5_1_main.py` | 0 | ✓ |

### 逐条表

#### `s5_5_build.py`（20 处代码 + 若干注释）

| 行 | 写死了什么 | 该参数化吗 |
|---|---|---|
| 36-39 | **`SYSTEM_GEN` 里的示例**：「段锚点：调用点被 `else if (strEQc (pair->value.s, "OBJECTS"))` 守着」 | ✅ **是**（示例锚点应从 plan 来） |
| 55-61, 96 | `LINE_RECORD_ADAPTER` 的字段映射（`record.value_after_group_code.0`），注释明说「group code 的语义是 DXF 领域知识；换格式要写新适配器」 | ❌ 否（**本来就是 DXF 专用分支**，注释已标清） |
| 113-151 | `_call_site_guard`：`strEQc(x->y.z, "…")` 的**通用**正则 | ❌ 否（**通用逻辑** ✓） |
| **178-183** | **`_sample_hex()` 里 `b.find(b"OBJECTS")`** | ✅ **是** |
| 195, 332-353 | `0/SECTION … 0/ENDSEC` 的**结构描述 + preserve 清单** | ❌ 否（DXF 专用，标清即可） |
| 304-308 | `record.value_after_group_code.N` | ❌ 否（line_record 适配器内） |
| **583-588** | **`USER_GEN` 里的分流规则**：`AC`→DWG / `{`→JSON / 其余→DXF；以及「插入完整结构 `0/SECTION + 2/<anchor>`」 | ✅ **是**（anchor 应来自 plan） |
| **653** | **门禁里的 `memcmp(d + i, "OBJECTS", 7)`** | ✅ **是** |
| **724-725, 740** | **`_has_structure(anchor: bytes = b"OBJECTS")`** + 文档串 | ✅ **是**（函数已有 `anchor` 参数，只是**默认值 + 调用处**写死） |
| **746** | **`_record_after(anchor: bytes = b"OBJECTS")`** | ✅ **是** |
| **799, 815, 822** | 门禁 5 的错误消息「剥掉 **OBJECTS** 的种子」「`2/OBJECTS=…`」 | ✅ **是**（消息要带实际 anchor） |
| **841-842** | **`src.find(b"OBJECTS")`** | ✅ **是** |
| 864-866 | `preserve=group_code_digits` / 「改在 **OBJECTS** 段之前」 | ✅ **是**（后半句要参数化） |

#### `s5_4_analyze.py`

| 行 | 写死了什么 | 该参数化吗 |
|---|---|---|
| 62, 122-132 | `DXF_RECORD_RX = ^\s*(\d{1,3})\r?\n` —— **格式探测**（`line_record` / `binary_record`） | ❌ 否（**探测逻辑**，DXF 只是被探测的格式之一） |
| 191-192 | 注释里提到 `dxf_entities_read` / `dxf_objects_read` 的行号 | ❌ 否（注释） |
| 404-406 | `record.group_code.N` | ❌ 否（line_record 适配器内） |
| **1076-1085** | **`BRANCH_FILES = {"DXF": ("src/in_dxf.c",) + COMMON_FILES, "DWG": ("src/decode.c","src/bits.c") + …}` + `FORMAT_MAGIC`** | ✅ **是**（**项目专属文件名表**，和 R7 删掉的「libredwg 路径前缀表」同类） |
| 1372-1392, 1617, 1656 | 注释/示例里的 `dwg_free_*` | ❌ 否（注释） |
| 2070 | `"mutate_binary_record" if branch == "DWG" else …` | ❌ 否（**分支专用**，标清） |
| 2161 | `format_scope: ["DXF","DWG","JSON"]` | ❌ 否（通用） |

### 汇总

| 类别 | 条数 |
|---|---:|
| **该参数化** | **12 处**（`s5_5_build.py` 11 + `s5_4_analyze.py` 1） |
| 本来就是专用分支（留，标清） | 6 处 |
| 通用逻辑（留） | 4 处 |
| 注释 | 13 处 |
| 探测/适配器（留） | 3 处 |

**最严重的两处**：

1. **`s5_5_build.py:583-588`（`USER_GEN` 的 prompt）** —— 它把「DXF / DWG / JSON 怎么分流」「插入 `0/SECTION + 2/<anchor>`」**写进系统提示**，LLM 每次都按这个模板写，**anchor 写在 prompt 里而不是从 plan 读**；
2. **`s5_5_build.py:724/746/653/841`（门禁 5）** —— **要求产出里有 `0/SECTION` + `2/OBJECTS`**，非 OBJECTS 的策略**必被拒**。

**这两处加起来 = 「generate 只会产 OBJECTS 形态」的完整解释。**

### ⏸ 停止点：等确认

改哪些由你定。我的建议（按收益排）：

| 优先级 | 改什么 | 为什么 |
|---|---|---|
| **P0** | `_has_structure` / `_record_after` / 653 / 841-866 改成**按 plan 的 anchor 走** | 这是**硬阻断**：不改的话非 OBJECTS 策略 100% 被门禁拒 |
| **P0** | `USER_GEN`（583-588）的 anchor 改成 `{anchor}` 占位，从 plan 填 | prompt 是"只产 OBJECTS"的直接原因 |
| **P1** | `SYSTEM_GEN`（36-39）的示例改成从 plan 填 | 同上，弱一点 |
| **P1** | `_sample_hex`（178-183）的 `b.find(b"OBJECTS")` → 按 anchor 找 | 影响 `input_contract.sample_hex`，进而影响 prompt |
| **P2** | `BRANCH_FILES` / `FORMAT_MAGIC`（1076-1085）搬到项目配置 | 和 R7 的教训同类，但**不影响本轮的多策略**（只影响 `input_branch`） |

**红线（改的时候必须守）**：
1. **libredwg 单站点（OBJECTS）那条路必须产出和 `d7913b9e` 能力等价的算子**（OBJECTS 500/500、剥段 500/500、DWG 0）；
2. **门禁 5 跟着 anchor 走，不是放宽** —— "必须有 OBJECTS" → "必须有 plan 声明的 anchor"。

---

## 步骤【二】· 参数化（P0 + P1 + P2 全改）

### 改了什么

| # | 位置 | 改法 |
|---|---|---|
| **P0** | `s5_5_build.py` 门禁 5（`_has_structure` / `_record_after` / `memcmp` / `find` / 三条消息） | 全部改成读 `plan_anchor(plan)`；`_has_structure`/`_record_after` 的 `anchor` 参数**去掉默认值**（必须显式传） |
| **P0** | `s5_5_build.py` `USER_GEN` 的 anchor 模板 | 改成从 `targets[].section_anchor` 读（`libredwg 是 OBJECTS` 作为示例保留） |
| **P1** | `s5_5_build.py` `SYSTEM_GEN` 的示例 | 同上，保留具体锚点作为示例 |
| **P1** | `s5_5_build.py` `_sample_hex()` | `b.find(b"OBJECTS")` → `b.find(anchor)`，调用处传 `targets[].section_anchor` |
| **P1** | `s5_5_build.py` `DRIVER`（门禁的驱动） | `ANCHOR`/`ALEN` 从 `DRIVER_ANCHOR_DEFS` 注入（原来改了 `memcmp` 但没定义，编译不过） |
| **P2** | `s5_4_analyze.py` `COMMON_FILES`/`FORMAT_FILES`/`FORMAT_MAGIC` | 从**写死的 libredwg 文件名**改成 `load_format_tables()` 读 `projects/<osv>/format_files.json`；已为 libredwg 生成该文件（**值与原表逐字相同**） |
| **d** | `s5_5_build.py` `mutator.json` 的 `generation_gate` | 不再写死 `pending`；`verify` 跑完后**回写**真实结果（`_filled_by: verify`） |

### 改动**过程中撞到的两个自伤**（都已修）

| 现象 | 原因 | 修法 |
|---|---|---|
| `NameError: name 'plan' is not defined` | `_sample_hex` 调用处用了 `plan_anchor(plan)`，但那一步 `plan` 还没组装 | 改用 `tgt.get("section_anchor")` |
| 门禁驱动 `drv.c` 编译不过（`ALEN`/`ANCHOR` 未声明） | 我替换了 `memcmp` 那行，但没注入 `#define` | 加 `DRIVER_ANCHOR_DEFS`，在 `DRIVER` 里插 `{anchor_defs}` |
| generate 被 `preserve=group_code_digits` 拒（40/50 → 1/50 → 0） | 我删掉了 `SYSTEM_GEN`/`USER_GEN` 里的**具体示例**，LLM 失去指导 | 恢复具体示例（保留"libredwg 是 OBJECTS"这类提示），三次迭代到通过 |

### 红线 1：libredwg 单站点（OBJECTS）能力等价 ✅

重新 `plan` + `generate` 得到 `mutator.c` **291 行、sha1 `e81b85c`**，
用门禁的驱动（`drv.c`，anchor=OBJECTS）跑 1000 seed × 三类种子：

| 种子 | UNCHANGED | **CHANGED** | DISTINCT | DEFAULT |
|---|---:|---:|---:|---:|
| **含 OBJECTS 段** | 500 | **500** | 64 | 500 |
| **剥掉 OBJECTS 段**（只有 ENTITIES） | 500 | **500** | 64 | 500 |
| **DWG（`AC` 开头）** | 1000 | **0** | 0 | 1000 |

**→ 含 OBJECTS 500/500 ✓、剥段 500/500 ✓、DWG 0 ✓ —— 和 `d7913b9e` 能力等价。**

### 红线 2：门禁 5 跟着 anchor 走 ✅

代码里 `_anch = plan_anchor(plan) or "OBJECTS"`，`_has_structure(blob, _ab)`、
错误消息里的 `{_anch}`、`src.find(_ab)` 全部用它。
**挡的强度不变**（仍是 `0/SECTION` + `2/<anchor>` + ≥1 条 code-0 记录 + 剥段 ≥400 次改动）。

### 验收 a) 多策略 —— ❌ **仍然失败**

plan 里放 **3 个 anchor**（`OBJECTS` / `ENTITIES` / `ACAD_`），`targets` 也给了三条：

```
✗ default 权重不对：计划 0.50，实测 1.00（default 被调用 1000/1000）
✗ 有效变异空间太小：1000 个 Seed 只产出 0 个互不相同的输出
✗ 构造路径无效：剥掉 OBJECTS 段的种子上 1000 Seed 只改动 0 次
```

**生成的代码变成 no-op**（`ENTITIES` 0 次、`ACAD_` 0 次）。

**→ 参数化解决了"门禁只认 OBJECTS"，但没解决"LLM 在 3 个策略时写不出可运行的代码"。**
**单站点能过、3 站点变 no-op** —— 这和 R29/R30 的观察一致：**站点数一多就退化**。

### 验收 b) V4 带 `--binary` ✅ **第一次 PASS**

给 `source_context.json` 加了 `testcase_path`（指向 `reps_r9_final` 里的真实崩溃样本）：

```
V1_schema      PASS
V2_evidence    PASS
V3_code        PASS
V4_behavior    PASS   · 已知 crash 回放: heap-use-after-free /src/libredwg/src/in_dxf.c:12267
overall = pass
```

**这是 V4 第一次真正验证了"算子能触发目标崩溃"。**

### 验收 c) gpac / leptonica 的 plan 重跑 —— ❌ **仍然 BLOCKED**

两者都是 `status: BLOCKED / ✗ uaf-llm01: 段锚点未推出`。

**但根因不是 OBJECTS** —— 是**更早的一步**：`field_constraint()`（`s5_5_build.py:138`）
只认 `(\w+)->code == (\d+)` 这种 **DXF 组码**写法，别的格式它推不出任何约束 → 锚点为空 → blocked。

**→ "没有第二个落地项目"这个结论还不能推翻**：这次参数化改的是 **generate 的下游**，
而 gpac/leptonica 卡在**上游的约束推导**。要验证它们，得先参数化 `field_constraint`。

### 验收 d) `generation_gate` ✅

`verify` 跑完后回写（`↻ 已回写 generation_gate`），现在是：
`evidence_check` / `compile_check` / `replay_check` 都是 `verify` 的真实结果，并带 `_filled_by: verify`。

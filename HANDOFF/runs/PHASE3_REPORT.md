# PHASE 3 报告 · 路径 B：a001 从替换型扩成构造型

日期：2026-11-02

---

## 做了什么

### 3.1 `s5_mutation_plan.py` → plan v5

| 字段 | 改前 | 改后 |
|---|---|---|
| `schema_version` | `stage5.mutation_plan.v4` | **`stage5.mutation_plan.v5`** |
| `operation` | `replace_value_line` | **`ensure_record_structure`** |
| 新增 `operation_paths` | — | `["replace_value_line", "construct_section"]` |
| `preserve` | `["group_code_digits","record_line_count","CRLF","section_terminator(ENDSEC)"]` | **`["group_code_digits","CRLF","section_terminator(ENDSEC)"]`**（去掉 `record_line_count`，它禁止插入） |
| 新增 `construct` | — | 见下 |
| `status=ready` 条件 | 有 target_part + locator.anchor | 再加 **`construct.sequence` 非空** |

新增 helper `_eof_anchor()`（`s5_mutation_plan.py:158`）：从 plan 的 `seed_file` 里找**最后一个 code-0 / EOF 记录**，
作为插入锚点。推导理由写进了 `construct.insert_position.derivation`。

实际产出的 `construct`（`v2/mutation_plan.json`）：

```json
"construct": {
  "when": "section_absent",
  "sequence": ["0/SECTION", "2/OBJECTS", "0/<random_unrecognized_name>", "0/ENDSEC"],
  "insert_position": {
    "kind": "before_record",
    "anchor": "0/EOF",
    "offset": 127860,
    "record_index": 13444,
    "derivation": "DXF 由若干 `0/SECTION…0/ENDSEC` 块组成、最后以 `0/EOF` 收尾；插在 EOF 之前不需要改动任何已有块。锚点从 plan 的 seed_file 里实测"
  },
  "line_endings": "CRLF",
  "record_header_rx": "^\\s*(\\d{1,3})\\r?\\n",
  "basis_refs": ["target_surface:evidence_chain:step5", "target_surface:evidence_chain:step6",
                 "mutation_plan:locator.section_anchor", "mutation_plan:new_value_policy"]
}
```

`<random_unrecognized_name>` 复用现有 `new_value_policy`（`kind=random_unrecognized_name`、
`derive_from=Seed`、`alphabet=A-Za-z0-9_-`、`length=[1,64]`），**没有固定候选列表**。

备份：`/tmp/audit/backup/s5_mutation_plan.py.bak`

### 3.2 `s5_generate_mutator_v2.py` 的 SYSTEM prompt

新增第 13 条（原文）：

> 13. **`operation = ensure_record_structure` 时，策略函数必须有两条路径**：
>     · **段存在**（能在输入里找到 `locator.section_anchor` 那一行）→ 现行为：按 `locator.pick=random_k`
>       选段内第 k 条 code-0 记录，替换它的**值行**；
>     · **段不存在** → 按 `construct.sequence` 在 `construct.insert_position` 处插入完整结构
>       （`0/SECTION` + `2/<anchor>` + `0/<随机非已知名>` + `0/ENDSEC`）。
>     两条路径都必须做 `MaxSize` 边界检查、兼容 `\n`/`\r\n`/`\r`、失败返回原输入。
>     **段不存在时不能返回原输入**（那是空转）。

（原第 12 条"只输出 JSON"顺延为第 14 条。）

### 3.3 门禁：`check_behavior` 第 5 项

新增"构造路径有效性"：在一份**剥掉 OBJECTS 段**的种子上跑 1000 Seed，
要求 `CHANGED ≥ 400`，且插入后的字节必须能被解析出 `0/SECTION` + `2/OBJECTS` + ≥1 条 code-0 记录
（`_has_structure()`，`s5_generate_mutator_v2.py`）。

驱动 `DRIVER` 新增可选 `argv[3]`：把**第一个改动后的输出** dump 到该路径，供 Python 侧做结构校验。

"位置正确"那项加了分支：`src.find(b"OBJECTS") < 0`（剥段种子）或 `constructing` 为真时，
**不再要求** `off > OBJECTS 偏移`；组码行校验保留。

门禁固件：

| 文件 | 内容 |
|---|---|
| `v2/experiment/strip.py` | 剥段脚本（从 `/tmp/audit/strip.py` 复制） |
| `v2/experiment/gate_seeds/stripped_{Constraints,sample_2018,sample_r14,v}.dxf` | 4 个剥段种子，均 `grep -c OBJECTS = 0` |

**没有写进 `seeds/`**（避免污染语料）。

备份：`/tmp/audit/backup/s5_generate_mutator_v2.py.bak`

### 3.4 重新生成

```
plan : status = ready，schema = stage5.mutation_plan.v5，blockers = []
mutator.c : 9,717 字节 / 294 行（改前 5,931 字节 / 206 行）
```

生成的算子结构（`v2/mutator.c`）：

| 行 | 内容 |
|---|---|
| 103 | `if (code == 2 && line_eq(&val_ln, "OBJECTS"))` —— 找段 |
| 123 | `if (code == 0 && line_eq(&val_ln, "ENDSEC"))` —— 段边界 |
| 197 / 202 | `memmove(...)` —— **替换路径**（值行改长/改短） |
| **213** | `find_eof_insert_off()` —— 找 `0/EOF` 插入点 |
| **232** | `insert_section_before_eof()` —— **构造路径**：`memmove` 腾位置 + 写 4 条记录 |
| 273 | `mutate_a001()`：`if (find section) 替换; else insert_section_before_eof(...)` |
| 分发器 | `if (!is_dxf_format) return LLVMFuzzerMutate(...)`；`r<500` → default；否则 `mutate_a001` |

### 3.5 决定性 A/B

种子集：`v2/experiment/gate_seeds/stripped_*.dxf`（4 个，**无 OBJECTS、无 DWG**），
搬进 `seeds/` 后跑 `run_reps.sh 300 5`，产物 `reps_pathB/`。
跑完把 `seeds/` 恢复成 6 DXF + 2 DWG。

---

## 报表

### 表 1：plant/门禁验收（3.4）

| 项 | 结果 |
|---|---|
| plan `status` | `ready`，`blockers = []` |
| 静态门禁 `check_code` | **PASS** |
| 行为门禁（权重 / 变异空间 / 格式分流 / 位置 / **构造路径**） | **PASS** |
| `s5_verify` V1_schema | PASS（`documents=6/6`） |
| `s5_verify` V2_evidence | PASS（`actions=1`） |
| `s5_verify` V3_code | PASS（`clang -fsyntax-only 通过`） |
| `s5_verify` V4_behavior | PASS（`已知 crash 回放: heap-use-after-free /src/libredwg/src/in_dxf.c:12267`） |
| `s5_verify` overall | **pass** |
| pytest | **4 passed in 0.14s** |

**门禁 5 对旧算子的拦截（改前验证）**：

```
  行为: ['构造路径无效：剥掉 OBJECTS 的种子上 1000 Seed 只改动 0 次（要求 ≥ 400；当前算子应为 0）']
```

### 表 2：新算子的能力（`diversity.c`，1000 Seed）

| 输入 | 类型 | total | CHANGED | UNCHANGED | DISTINCT |
|---|---|---|---|---|---|
| `Constraints.dxf` | 含 OBJECTS | 1000 | 500 | 500 | **500** |
| `stripped_Constraints.dxf` | **剥段** | 1000 | **500** | 500 | **500** |
| `sample_r14.dxf` | 含 OBJECTS | 1000 | 500 | 500 | **500** |
| `stripped_sample_r14.dxf` | **剥段** | 1000 | **500** | 500 | **500** |
| `Arc.dwg` | DWG | 1000 | **0** | 1000 | 0 |

对照旧算子：剥段种子上 `CHANGED = 0`。**改造后 0 → 500。**

### 表 3：**决定性 A/B（剥段种子，300 s × 5 rep）**

| rep | default 命中/execs | default 率/100k | custom 命中/execs | custom 率/100k | 比值 |
|---|---|---|---|---|---|
| rep01 | **0**/200,338 | 0.00 | 135/121,839 | 110.80 | 无定义 |
| rep02 | **0**/204,424 | 0.00 | 134/121,785 | 110.03 | 无定义 |
| rep03 | **0**/199,655 | 0.00 | 135/121,839 | 110.80 | 无定义 |
| rep04 | **0**/233,430 | 0.00 | 136/122,368 | 111.14 | 无定义 |
| rep05 | **3**/180,605 | 1.66 | 135/121,839 | 110.80 | 66.70× |

- pooled：**default 3 / 1,018,452 = 0.29 / 100k**；**custom 675 / 609,670 = 110.72 / 100k**
- **RR = 375.862，95% CI = [120.92, 1168.34]**（CI 远离 1）
- 配对胜出：**5 个 rep 里 4 个 default=0，比值无定义；唯一可计算的 rep05 为 66.70×**
- 覆盖率比 custom/default：中位 **0.820**，范围 [0.795, 0.841]
- 唯一点数：default [0, 0, 0, 1, 1] / custom [1, 1, 1, 1, 1]
- 所有臂的崩溃点都是 `heap-use-after-free @ in_dxf.c:12267`（每 rep 唯一点数 1）

### 表 4：回归（现种子 6 DXF + 2 DWG，150 s × 5 rep）

| rep | default 命中/execs | default 率/100k | custom 命中/execs | custom 率/100k | 比值 |
|---|---|---|---|---|---|
| rep01 | 12/9,717 | 123.49 | 5/6,255 | 79.94 | 0.65× |
| rep02 | 7/9,159 | 76.43 | 5/6,241 | 80.12 | 1.05× |
| rep03 | 7/7,515 | 93.15 | 7/7,522 | 93.06 | 1.00× |
| rep04 | 3/9,197 | 32.62 | 5/6,910 | 72.36 | 2.22× |
| rep05 | 7/9,548 | 73.31 | 5/6,549 | 76.35 | 1.04× |

- pooled：default 36/45,136 = **79.76/100k**；custom 27/33,477 = **80.65/100k**
- **RR = 1.011，95% CI = [0.61, 1.67]** → CI 含 1
- 配对胜出 3/5，中位比值 1.04×
- 覆盖率比中位 **1.023**，范围 [0.961, 1.059]
- 唯一点数 default [2,2,2,1,1] / custom [1,2,1,1,2]

---

## 失败与存疑

1. **构造路径在 DWG 上仍然无效**：`is_dxf_format()` 把 DWG/JSON 全部路由到 `LLVMFuzzerMutate`，
   所以 DWG 语料上构造路径不生效（`Arc.dwg` 的 `CHANGED = 0`）。这是**设计如此**（`format_scope=["DXF"]`），
   但意味着那张 375× 的效应**只在 DXF 上成立**。
2. **覆盖率下降 18%**：剥段种子上 custom/default 的覆盖率比只有 0.820。
   构造路径每 2 次迭代就往输入里塞一个 `OBJECTS` 段，语料被这类结构主导，
   其他路径的探索被挤掉。**这是构造型的代价，未做优化。**
3. **`RR = 375.9` 的分母只有 3**：default 在 1,018,452 execs 里只命中 3 次，
   CI 的下界 120.92 已经很大，但这个数对 Poisson 假设敏感（3 个事件）。
   **若 default 实际是 0（rep01–04 都是 0），率比无定义**——按指令"直接给 N 和两臂 execs"，
   原始计数是 **3 / 1,018,452 vs 675 / 609,670**。
4. **回归的覆盖率比 1.023 > 1**，说明构造路径没有损害原场景的覆盖——但 reg 的 custom execs
   只有 default 的 74%（33,477 vs 45,136），所以"覆盖率不降"可能是"每 exec 覆盖更高"造成的，
   不完全是好事。
5. **`insert_position.offset = 127860`** 是从 `Constraints.dxf` 这一个种子推导的。
   若门禁用的剥段种子（`stripped_Constraints.dxf`，20,625 字节）与它不同源，
   `offset` 这个绝对值对别的输入没有意义——生成的算子实际是**重新扫描**找 `0/EOF`（`find_eof_insert_off`），
   不是直接用这个偏移。**plan 里的 offset 只是"推导证据"，不是运行时输入**。
6. **`_has_structure()` 是宽松校验**：它只要求"存在一行 `2` 后面跟 `OBJECTS`，且之前两行内有 `0/SECTION`"，
   不校验记录的完整性（例如 `2/OBJECTS` 与 `0/ENDSEC` 之间是否真的有对象）。所以门禁 5 保证的是
   "结构形状对"，不是"结构语义对"。语义对不对由 A/B 的结果间接证明（custom 675 次命中目标）。

---

## 下一阶段（Phase 4 / 后续）的前提是否成立

**成立，且本轮唯一的验收口径已经拿到。**

- 路径 B 的目标（"让算子能造结构"）达成：剥段种子上 `CHANGED` 从 0 变 500，
  A/B 里 default 3 次 vs custom 675 次。
- 代价已量化：覆盖率比 0.820（剥段）、1.023（回归）。
- **未解决**：DWG 上无效（设计限制）、覆盖率下降未优化、`RR` 分母过小。

**下一轮若要继续，最该做的是**：把构造路径的**触发频率**降下来（现在 50% 的特征预算每次都塞一个段），
例如"段不存在时只以 1/4 概率构造"，看能否把覆盖率比从 0.820 拉回 0.95 以上而不损失命中率。

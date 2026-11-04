# R9 报告

日期：2026-11-04
本轮只做三件事：**把唯一能引用的 A/B 结果钉死、修可证伪校验的漏洞、排查"静默用旧值"这一类 bug。**
不扩展任何能力（函数指针分派 / 跨函数扩形态 / 换崩溃类型 三项明确不做）。

> 本文是本轮全部产出。每完成一步追加一节，不覆盖前面内容。

---

## 步骤 0 · 旧文档删除提交

**这一步在上一轮（R8）已经做完了**，本轮只补 `HANDOFF.md` 里的 git 引用。

### commit hash

那 7 份文档的删除包含在 **`013c0307`**（`cleanup: 删除用户确认的 7 份旧文档 + 5 组非独立 reps 快照`）里。
本步开始时 `git status --short` 已经是空的，没有待提交的 `D`。

### 实际删掉的文件（`git show --stat 013c0307 -- docs/`）

```
 docs/ACCEPTANCE.md                   |  201 ----
 docs/ANALYSIS_REPORT.md              |  460 --------
 docs/DESIGN_V2.md                    | 1178 --------------------
 docs/EXPERIMENT_PIPELINE.md          |  150 ---
 docs/GENERATION_PIPELINE.md          |  257 -----
 docs/INVESTIGATION.md                |  717 ------------
 docs/libfuzzer_custom_mutator_survey.md |  164 ---
```

### `HANDOFF.md` 里两处 git 引用补的 hash

**文档内容在删除前的父提交 `b78260c9` 里**，所以取回命令是 `git show <父提交>:<路径>`：

| 位置 | 改前 | 改后 |
|---|---|---|
| 「三、怎么读」调查记录那一行 | `git 历史里的 docs/INVESTIGATION.md` | **`git show b78260c9:docs/INVESTIGATION.md`**（717 行；删除发生在 `013c0307`） |
| 「三、怎么读」生成 pipeline 那一行 | `docs/GENERATION_PIPELINE.md`（git 历史里） | **`git show b78260c9:docs/GENERATION_PIPELINE.md`**（257 行；删除发生在 `013c0307`） |

两条命令都实测跑过，能取回内容（首行分别是 `# mutator_create 调查记录（Q1–Q12）` 与
`# 生成 pipeline —— 五个阶段`）。

---

## 步骤 1 · 用当前二进制重跑 A/B

### 前置确认

| 项 | 值 |
|---|---|
| `v2/mutator.c` | **294 行**，sha1 **`d7913b9eaa3b5afce4cc14b739c480e6c39576a4`** |
| `mutation_plan.json` | `sites 1 / mutations 1 / weight 0.5 / total 1.0 / status ready`；`operation=ensure_record_structure`，站点 `src/in_dxf.c 12284 → 12267` |
| 二进制 | 重建后 sha1 **`a416b44d558a634ab8c333609cb421d35b486c62`**，mtime **2026-11-04 00:29:20** |
| 种子 | 4 个剥段 DXF，逐个 `grep -c OBJECTS = 0` ✅ |
| 跑前残留进程 | **0** |

### 逐 rep 表

| rep | default 命中/execs | custom 命中/execs | default 率/100k | custom 率/100k |
|---|---|---|---|---|
| rep01 | **0** / 222,941 | 168 / 70,924 | 0.00 | 236.87 |
| rep02 | **0** / 214,294 | 96 / 236,098 | 0.00 | 40.66 |
| rep03 | **0** / 211,038 | 71 / 196,605 | 0.00 | 36.11 |
| rep04 | **0** / 223,176 | 142 / 60,148 | 0.00 | 236.08 |
| rep05 | **0** / 231,398 | 140 / 76,584 | 0.00 | 182.81 |

### 合并计数

```
  default: 0 次目标崩溃 / 1,102,847 execs = 0.00 / 100k
  custom : 617 次目标崩溃 /   640,359 execs = 96.35 / 100k
```

- **率比（RR）无定义**（default 命中 0）。按指令只报原始计数。
- 唯一点数：default `[0, 0, 1, 0, 0]` / custom `[1, 1, 1, 1, 1]`。
- 崩溃类型：custom 的 617 次**全部**是 `heap-use-after-free @ in_dxf.c:12267`；
  default 的 1 次是 `heap-buffer-overflow @ in_dxf.c:11947`（**另一个 bug**，不计入目标）。
- `execs` 比（custom/default）：逐 rep `0.318 / 1.102 / 0.932 / 0.270 / 0.331`，**合并 0.581**。

### 覆盖率：**每 100k exec 的边覆盖**（不是 `cov` 绝对值）

| rep | default | custom | 比 |
|---|---:|---:|---:|
| rep01 | 4,799 | 11,753 | **2.449** |
| rep02 | 4,505 | 3,525 | 0.782 |
| rep03 | 4,544 | 4,280 | 0.942 |
| rep04 | 4,311 | 15,281 | **3.545** |
| rep05 | 3,982 | 11,463 | **2.879** |
| **中位** | — | — | **2.449**，范围 [0.782, 3.545] |

**注**：如果用 `cov` 绝对值比，中位是 **0.878**。两个口径差很多——因为 custom 的 execs
经常只有 default 的 27–33%（撞到崩溃就重启），分母小。**按指令以"每 100k exec"为准。**

### 独立性复核

| 检查 | 结果 |
|---|---|
| 5 个 rep 的 `run.log` sha1 | default `30b24362ed / 37672cf4a5 / 97acb35941 / 553ccc70c1 / 185a193a62`（**5 个全不同**）<br>custom `414c6f80c1 / 74bc4ae032 / dbd41088b4 / 2549479358 / 34ae3b6037`（**5 个全不同**） |
| custom 崩溃文件 | 每 rep `168 / 96 / 71 / 142 / 140`，合计 **617** |
| 全局唯一 sha1 | **617**（= 总数） |
| 出现 >1 次的 sha1 | **0** |
| 两两交集 | **10 组全为 0** |
| `-seed` 逐 rep 变化 | **`Seed: 1 / 2 / 3 / 4 / 5`**（从两个臂的 `run.log` 头部读到的） |

**✅ 5 个 rep 是真正独立的。**

### 与 `reps_pathB_r3` 对照

| | **`reps_r9_final`（当前，294 行，`a416b44d`）** | `reps_pathB_r3`（历史，440 行） |
|---|---|---|
| default 命中 / execs | **0 / 1,102,847** | 0 / 1,048,238 |
| custom 命中 / execs | **617 / 640,359** | 731 / 508,682 |
| custom 率 /100k | 96.35 | 143.70 |
| execs 比（custom/default） | 0.581 | 0.485 |
| 每 100k exec 边覆盖比（中位） | **2.449** | 1.699 |
| 崩溃 sha1 唯一数 / 总数 | **617 / 617** | 731 / 731 |
| 两两交集 | 全 0 | 全 0 |
| `-seed` | 1/2/3/4/5 | 1/2/3/4/5 |

### 判定

**✅ 结果钉死（第一行）。** 两次测量同量级：

- **default 两次都是 0 命中**（`0 / 1,048,238` 与 `0 / 1,102,847`）；
- custom 617 次 vs 731 次（差 16%），都在"几百次"这个量级；
- 密度 96.35 vs 143.70 /100k（差 33%，但 default 都是 0，率比无定义，比的只是计数）；
- 独立性两次都成立；
- 覆盖比（每 100k exec）两次都 > 1（2.449 vs 1.699）——**custom 每次执行覆盖更多边**，
  与它吞吐更低（0.581 / 0.485）正好互补。

`HANDOFF.md` 已改为引用 **`reps_r9_final`**，并保留 `reps_pathB_r3` 作为历史证据。
**`reps_pathB_r3` 未删。**

**存疑（三条，都如实记）**：

1. 本轮**没有**去 diff 294 行与 440 行两版算子的具体差异——因为量级一致，按判定表不需要。
   如果将来要对齐到"完全同一个二进制"，需要保留旧的 `mutator.c`
   （当前已被 `generate` 覆盖，只能在 git 历史里找）。
2. **`summary.json` 不记录"哪个二进制测的"**。`analyze_reps.py` 的覆盖率是**重新跑二进制**
   得出的，但产物里只有 `pooled` / `reps` 两个键，**没有 binary sha1 / mtime**。
   两次 summary 的 mtime 分别是 `2026-11-03 12:27:29`（历史，440 行那版）和
   `2026-11-04 00:43:50`（本次，`a416b44d`），所以**这一次**的可比性靠 mtime 推断，
   不是产物自证。→ 列为步骤 3 的候选（"读文件不校验时效"模式）。
3. **覆盖率两个口径差很多**：每 100k exec 的中位 2.449，而 `cov` 绝对值比只有 0.878。
   本报告按指令以"每 100k exec"为准，但引用时**必须写明是哪个口径**，否则会被读成相反结论。

---

### ⏸ 步骤 1 结束，等确认

| 验收项 | 结果 |
|---|---|
| 用当前二进制重跑 | ✅ `a416b44d`，算子 294 行 |
| 逐 rep 表 / 合并计数 | ✅ 已报（default 0/1,102,847 vs custom 617/640,359） |
| 每 100k exec 的边覆盖 | ✅ 中位 2.449（`cov` 绝对值口径是 0.878，已注明两者不同） |
| 独立性复核 | ✅ run.log sha1 全异、崩溃 sha1 617/617、交集全 0、`-seed` 1/2/3/4/5 |
| 与 `reps_pathB_r3` 同量级 | ✅ **钉死** |
| `reps_pathB_r3` 保留 | ✅ 未删 |
| `pytest` | ✅ 4 passed |

**请确认后进步骤 2（修可证伪校验的漏洞）。**

---

## 步骤 2 · 可证伪校验修漏洞

### 先说结果：这一步抓到一个**推翻 R8 结论**的 bug

**`_match_conjunct()` 用 `bool(want)` 比较 `is_link_read` / `reassigned_between`。**

```python
# pipeline/s5_4_analyze.py（改前）
if want != "any" and bool(site.get("is_link_read")) != bool(want):
```

而 `bool("false")` 是 **True**（非空字符串）。判据词表是 `true/false/any`——**字符串**。
所以模型写 `"false"` 时，"要求 false" 被**静默反转成"要求 true"**，规则整体恒假、0 命中。

**实测**：

```
  bool("false") = True    bool("true") = True
```

| feature | R8 判据里的布尔字段 | R8 报告的命中 | 修 `_as_bool` 后的命中 |
|---|---|---:|---:|
| `uaf-llm01` | `any` / `any` | 4 | 4（不受影响） |
| `uaf-llm02` | `reassigned:"false"`, `link:"false"` | **0** | **4** |
| `uaf-llm03` | `reassigned:"false"` | **0** | **3** |
| `uaf-llm04` | `reassigned:"false"`, `link:"false"` | 0 | 0（真不匹配） |
| `uaf-llm05` | `reassigned:"false"` | **0** | **4** |

**所以 R8 报告里"判据变具体了，但 llm02/03/05 全部 0 命中 → 没有增量信息"这句话，
机制是错的**：它们不是"规则太严所以没命中"，而是**被一个字符串/布尔比较 bug 判死了**。
结论（"没有增量"）**仍然成立**——修完后它们命中的就是 llm01 那 4 个站点——但**理由必须改**。

**修法**：加 `_as_bool(v)`（认识 `true/1/yes/y` 为真，其余为假），两处比较都改用它。

### 然后再做本步要求的事：语义可证伪校验

#### 实现

1. `load_touchstone()`：从所有 `projects/*/v2/feature_pipeline.json` 收集已扫出的站点，
   归一化成四字段（`use_kind` / `free_kind` / `reassigned_between` / `is_link_read`），去重。
2. `_conjunct_real_fields(c, touch)`：对分支里**每个字段**单独去掉，
   看命中集合变不变——变了才是**真约束**。
3. 匹配逻辑**没有重写**：复用 `s5_4_analyze._match_conjunct`（通过 `_synthetic_site()`
   把四字段还原成它能消费的 site）。
4. `falsifiability_check` 记进 `applicability_rules.json`：`mode` / `touchstone_sites` /
   `touchstone_sources` / `structurally_fixed`。

#### 试金石只有 2 个站点，而且**全是正例**

```
  站点数: 2  来源: ['projects/ARVO-42494732/v2/feature_pipeline.json',
                    'projects/ARVO-42518828/v2/feature_pipeline.json']
    {'use_kind': 'same_path', 'free_kind': 'direct_free', 'reassigned_between': False, 'is_link_read': False}
    {'use_kind': 'loop_back', 'free_kind': 'direct_free', 'reassigned_between': False, 'is_link_read': False}

  每个字段在试金石上的取值域:
    use_kind             ['loop_back', 'same_path']
    free_kind            ['direct_free']
    reassigned_between   ['False']
    is_link_read         ['False']
```

#### 语义门禁**把 llm01 杀了**——所以它不能当门禁

我按指令真的跑了 `--falsifiability semantic` 那一版（2026-11-04 01:01 完成）：

```
  判据汇总：3 条可用，2 条 rule_missing
    ✅ uaf-llm02 / uaf-llm03 / uaf-llm04
    ❌ uaf-llm01  rule_missing — 判据不可证伪（语义）：这个分支的字段没有一个能真的排除站点
                                  （在 2 个真实站点上，逐个去掉都不改变命中集合 [0, 1]）
    ❌ uaf-llm05  rule_missing — 同上
```

**`uaf-llm01` 被判死 = 唯一能落地的特征消失 = 违反本轮的铁律。**

**为什么必然这样**：`scan_sites()` 只产出**已经被扫描器筛成 UAF 形态**的站点，
所以试金石里**没有反例**。任何**正确描述这批站点**的判据，在它们身上都"排除不了任何东西"。
这不是规则的问题，是**试金石没有负样本**。
→ **"语义可区分性"在这套数据上不可检验**，这是本步最重要的方法学结论。

#### 实际采用的门禁：`structural`

= R8 的语法校验（字段必须是词表真子集）**+ 不把"结构性单值字段"计入区分力**。

```python
STRUCTURALLY_FIXED = {"reassigned_between": False}
# 依据（不是猜的）：scan_sites() 的注释自己写着
#   "回边/直线扫描在碰到重新赋值时已经截断，所以现存站点这里恒为 False"
# 跨函数站点更是直接硬编码 False（s5_4_analyze.py:1284）。
```

并加了**一致性检查**：如果哪天扫描器真能产出别的值，`load_touchstone()` 会打印
`⚠️ STRUCTURALLY_FIXED[reassigned_between] 已过期：实测取值 [...]`。

`semantic` 保留为 `--falsifiability semantic` 可复现的诊断模式。

#### SYSTEM prompt 同步

> **判据里的每个字段都必须真的能排除掉一些站点。** 如果某个字段在扫描器的产出里
> **只能取一个值**（例如 `reassigned_between` 恒为 `false`），写它等于没写，**不计入区分力**。

（原来那句"校验会拿真实扫出来的站点当试金石"已删——因为门禁不是那么做的，不能骗模型。）

### 新判据逐条（R9，`structural` 门禁，5 条可用 / 0 条 rule_missing）

| feature | R9 判据 | 语法真子集字段 | 结构性单值（不计入） |
|---|---|---|---:|
| `uaf-llm01` | `use_kind:[same_path, loop_back]`, `free_kind:direct_free`, `reassigned:false`, `link:any` | 2 | 1 |
| `uaf-llm02` | `use_kind:[cross_function, same_path, loop_back]`, `free_kind:[direct_free, realloc_self_assign]`, `reassigned:false`, `link:false` | 3 | 1 |
| `uaf-llm03` | `use_kind:[cross_function, loop_back]`, `free_kind:[direct_free, realloc_self_assign]`, `reassigned:false`, `link:false` | 3 | 1 |
| `uaf-llm04` | `use_kind:cross_function`, `free_kind:direct_free`, `reassigned:false`, `link:false` | 3 | 1 |
| `uaf-llm05` | `use_kind:[loop_back, same_path, cross_function]`, `free_kind:direct_free`, `reassigned:false`, `link:any` | 2 | 1 |

### 与 R8 对照

| feature | R8 | R9 | 变化 |
|---|---|---|---|
| `llm01` | `[loop_back,same_path] + direct_free` | `[same_path,loop_back] + direct_free` | 等价（顺序不同） |
| `llm02` | `[same_path,cross,loop_back] + [direct_free,realloc_self_assign] + rb:false + link:false` | `[cross_function,same_path,loop_back] + 同` | 等价 |
| `llm03` | `[same_path,cross_function] + direct_free + rb:false` | `[cross_function,loop_back] + [direct_free,realloc_self_assign] + rb:false + link:false` | 略变 |
| `llm04` | `cross_function + direct_free` | `cross_function + direct_free + rb:false + link:false` | 更严 |
| `llm05` | `[cross,loop_back,same_path] + direct_free + rb:false` | 同 | 等价 |

**LLM 是随机的，所以"R9 vs R8"的差异主要是采样噪声，不是校验带来的。**
唯一**系统性**的变化是：R8 里那三条 `reassigned_between: false` 现在**不计入区分力**了；
它们仍然合法（没有别的字段只靠它），但**不再被当成"具体"的证据**。

### libredwg / gpac 实测

| 项目 | `found` | 命中站点 |
|---|---|---|
| libredwg | **4/5**（`llm01/02/03/05`；`llm04` 0 命中） | `llm01` 4 个；`llm02` 4 个；`llm03` **1** 个；`llm05` 4 个——**全部包含在 `llm01` 那 4 个里** |
| gpac | **3/5**（`llm01/02/05`；`llm03/04` 0 命中） | 全部是 `gf_odf_vcc_cfg_read_bs:1400 → 1404` 那一个 |

**`llm01` 的站点未变**：

```json
{"function":"dxf_objects_read","file":"src/in_dxf.c","free_line":12284,"use_line":12267,
 "var":"pair","callee":"dxf_free_pair","reuse_kind":"loop_back"}
branch: {"branch":"DXF","entry":"dwg_read_dxf","magic":"其余（非 'AC'、非 '{'）",
         "via":"function dxf_objects_read @ distance 1"}
```

### 重走 `plan → generate → verify`：权重配置与步骤 1 一致

```
  权重    : default 0.50 + 1 个**站点** × 0.50 = 1.00
  sites 1 / mutations 1 / a001 weight 0.5 / total 1.0
  a001 supporting_features: ['uaf-llm01','uaf-llm02','uaf-llm03','uaf-llm05']
```

**`found` 是 4 不是 1，但 R8 修的"权重按站点求和"把它救回来了**：4 个特征指向同一站点 →
合并成 1 个 action → 权重 4×0.125 = **0.5**。`total = 1.0`。

**与步骤 1 跑 A/B 时的配置完全一致** → 按指令**不重跑 A/B**。

**门禁**：V1–V4 全 PASS（V4 真回放 `in_dxf.c:12267`），`pytest 4 passed`。

### 失败与存疑

1. **`bool("false")` 是本轮最重要的发现，而它只在"顺手核对"时才暴露**。
   这正好证明步骤 3 要查的这类 bug 有多危险：**它产出一个看起来完全正常的结果
   （"这条判据没命中"），错误却完全静默**。
2. **语义可证伪性在这套数据上不可检验**（试金石无负样本）。这不是实现缺陷，
   是"扫描器只产出一类站点"的结构性后果。要真正检验，需要**人为构造负样本**
   （例如把 `use_kind` 改成 `cross_function` 的合成站点），那是新工作，不在本轮预算内。
3. **`generate` 不具可复现性**：三次运行产生三版算子（R6 **440 行** / 步骤 1 **294 行** /
   本步 **243 行**），能力剖面完全相同（500/500、DWG 0、50%），但**不是同一个可执行文件**。
   本步已把工作区恢复成 294 行那版（`git checkout -- v2/mutator.c v2/mutator.json`），
   重建后二进制 sha1 **`a416b44d`，与步骤 1 逐字节相同**，所以 `reps_r9_final` 仍然对得上。
   **但这意味着"算子"这个产物本身不可重生成**——引用 A/B 结果时必须连 `mutator.c` 的
   sha1 一起记。→ 列入步骤 3 的排查项。
4. **R8 报告对应的结论要改**：`docs/runs/R8_REPORT.md` 与 `HANDOFF.md` 里
   "llm02/03/05 0 命中 → 没有增量"的**机制描述**是错的。结论不变，但理由要改成
   "修掉 bug 后它们命中同一批站点"。**本步没有去改 R8 报告正文**（历史文档不改写），
   只在 `HANDOFF.md` 的限制 8 里更正。

---

## 步骤 3 · 静默失败排查

### 范围与计数

| 项 | 数 |
|---|---|
| 扫描的 `.py` 文件 | **11 个**（`pipeline/` 全部） |
| `except` 处理器 | **42 处**，其中静默（`pass` / `continue` / `return 空值`）**23 处** |
| `json.load(open(...))` 直接读产物 | **45 处**，其中**带时效检查的 0 处**（全部靠"文件存在"） |
| 已在前几轮修掉的同类 | 4 处（commit fallback / `--depth` 被吞 / `emit_rules` 残留 / `V4` 跳过回放） |
| **本轮判为高风险** | **5 处**（含本步发现的 `bool("false")`） |
| **修了** | **5 处** |

### 排查表（只列判为**高风险**和**中风险**的；低风险的 30 余处不列）

| 文件:行 | 模式 | 风险 | 失败时会发生什么 | 处理 |
|---|---|---|:---:|---|
| `s5_4_analyze.py:1356,1361`（`_match_conjunct`） | 静默回退/类型错 | **高** | `bool("false")` = **True**，判据里"要求 false"被静默反转成"要求 true" → 规则恒假、0 命中，**报告里只会看到"这条判据没命中"** | ✅ **已修**：加 `_as_bool()` |
| `s2_2_facts.py:1209` | 失败后继续（`return {}, items`） | **高** | Joern deep 分析挂了 → 返回**空 facts**，下游看到"字段缺失"而不是"分析失败"（与 R4 那次 facts 退化的表现相同） | ✅ **已修**：打 stderr + 返回 `{"_failed": True, "_error": ...}` |
| `s5_6_lib.py:470` | 静默回退到默认值（`args = {}`） | **高** | 模型发出的 tool `arguments` 不是合法 JSON → 工具拿**空参数**跑，产出"看起来正常但没查对东西"的结果（如 `read_file` 没带路径） | ✅ **已修**：不执行、记 `bad_tool_args` 日志、把错误回喂给模型 |
| `s4_abstract_features.py::emit_rules` | 读文件不校验时效 | **高** | R8 的 sidecar 只挡"本次失败但上次成功"；若 pattern 改名/换 tag，**上次残留的 `feature_*.json` 仍会被当成这次的结果** | ✅ **已修**：按 `_RUN_STARTED_AT` 过滤 mtime，跳过的文件打印出来 |
| `s5_5_build.py::main_plan` | 读文件不校验时效 | **高** | `applicability_rules.json` 比 `feature_pipeline.json` 新时，plan 用的是**旧判据算出来的特征**（R7/R8 就出现过 plan 停在 11-02、feature_pipeline 已到 11-03，当时被误读成"权重稀释"） | ✅ **已修**：打 stderr 警告（不硬停，重跑 `features` 即可） |
| `s4_abstract_features.py:268` | 失败后继续（`return [], []`） | 中 | `load_touchstone` 导入失败 → 门禁从 `structural` 降级到 `syntactic` | 不改（**模式会打印并写进产物**，不是静默） |
| `s4_abstract_features.py:276` | 吞异常（`continue`） | 中 | 某个 `feature_pipeline.json` 读不了 → 该项目的站点不进试金石 | 不改（`touchstone_sources` 会少一个，可查） |
| `s5_6_lib.py:418` | 吞异常（`detail = ""`） | 低 | HTTP 错误的响应体读不出来 → 错误信息少一段 | 不改 |
| `s5_2_prepare.py:229` | 吞异常（`continue`） | 低 | 预置 harness 读不了 → 跳过，最终触发 `harness_not_found` **硬停** | 不改（已经会硬失败） |
| `s5_5_build.py:127` | 吞异常（`continue`） | 低 | 证据行号越界 → 跳过该行 | 不改 |
| `s2_2_facts.py` 其余 8 处 `pass`/`continue` | 吞异常 | 低 | 都是"某条增强信息拿不到就跳过"，主结论不依赖 | 不改（列清单） |
| `s3_extract_patterns.py` 3 处 `pass`/`continue` | 吞异常 | 低 | 缓存文件/批次读不了 → 跳过该批次，日志有打印 | 不改 |
| `s5_4_analyze.py:584,643,648` | 吞异常（`pass`） | 低 | 缓存文件读不了 / 行号不是 int → 跳过 | 不改 |
| `s5_3_audit.py:227`、`s5_4_analyze.py:626` | 失败后继续（`bad.append(...); continue`） | 低 | **有记录**（进 `bad` 列表） | 不改 |

### 修了哪 5 处（含验证）

1. **`_as_bool`**：`is_link_read` / `reassigned_between` 两处比较。验证见步骤 2（`llm02/03/05` 从 0 命中恢复成 4/3/4）。
2. **Joern deep 失败**：合成验证——把 `_failed` 写进返回 dict，下游可区分"没跑"与"跑失败"。
3. **工具参数坏**：合成验证——不再执行，回喂 `[错误] … arguments 不是合法 JSON`。
4. **`emit_rules` mtime 过滤**：
   ```
   _RUN_STARTED_AT = 0.0 → 5 条可用（不误杀）✅
   _RUN_STARTED_AT = 未来 → ⚠️ 跳过 5 个上次运行残留的 feature_*.json ✅
   ```
   **注意**：做这个合成测试时它把 `applicability_rules.json` 写成了 0 条，已用
   `_RUN_STARTED_AT = 0` 恢复成 5 条。
5. **`main_plan` 时效警告**：合成验证——当前 `feature_pipeline`（12:43:55）比
   `applicability_rules`（12:44:02）旧 → 判定"会触发"；正常流程下 `features` 刚跑完所以不触发。✅

### libredwg 全流程回归

| 项 | 结果 |
|---|---|
| 站点 | **`src/in_dxf.c:12284 → 12267`，`var=pair`，`branch=DXF`，`status=found`** ✅ 未变 |
| `found` | 4/5（`llm01/02/03/05`） |
| plan | **1 site / 1 mutation / weight 0.5 / total 1.0** ✅ 与步骤 1 跑 A/B 时一致 |
| `mutator.c` | **294 行**，sha1 **`d7913b9e`**（= 步骤 1 用的那版，二进制 sha1 `a416b44d` 逐字节一致） |
| V1–V4 | 全 **PASS**，`overall = pass`（V4 真回放 `in_dxf.c:12267`） |
| `pytest` | **4 passed** |

### 失败与存疑

1. **45 处 JSON 读取，0 处有时效检查**——本轮只给最关键的两处（`emit_rules` / `main_plan`）加了。
   其余 43 处仍然"文件存在即当有效"。
2. **低风险的 30 余处没有改**。其中一些（比如 `s3` 的批次跳过）在坏数据下可能让 pattern
   变少而不报——但都有日志，且不在主链的结论路径上。
3. **本轮的"高风险"判定有主观性**。判据是"失败后会不会产出一个看起来正常但实际错误的结果"，
   这个判断我做了 11 个文件 × 42 处，可能有漏。
4. **没有做的事**：没有做"注入故障 → 看下游能不能发现"的**主动测试**。
   那是唯一能证明"这一类 bug 已经清掉"的办法，比人眼扫一遍强得多。**列为下一步 P0。**

---

## 汇总

### 三步结论各一句话

| 步骤 | 结论 |
|---|---|
| **0 · 旧文档删除** | 上一轮（`013c0307`）已提交；本步只把 `HANDOFF.md` 的两处 git 引用补成 `git show b78260c9:<path>`（717 / 257 行），实测可取回 |
| **1 · 重跑 A/B** | ✅ **钉死**：当前二进制 `a416b44d`（算子 294 行）下 `default 0 / 1,102,847` vs `custom 617 / 640,359`；5 个 rep 独立（崩溃 sha1 617/617、两两交集 0、`-seed` 1/2/3/4/5）；与历史 `731 / 508,682` 同量级 |
| **2 · 判据可证伪** | 🟡 **抓到一个推翻 R8 机制的 bug**（`bool("false") == True`）；语义门禁实测**杀掉 llm01**（试金石无负样本）→ 改用 `structural` 门禁；5 条判据全部具体，但 **libredwg 命中仍是 llm01 那 4 个站点** |
| **3 · 静默失败排查** | 扫 11 个文件 / 42 处 `except`（23 处静默）/ 45 处 JSON 读取（0 处时效检查）；**高风险 5 处，全部修了**；libredwg 全流程回归通过 |

### “LLM 归纳是否有价值”的最终答案 + 依据

**答案不变：在"能不能找到新站点"这个唯一重要的口径上，没有价值；在"能不能把机制表达成可机器判定的形式"上有一点价值。**

**依据（R9 更新后）**：

1. **四轮尝试，命中集合从未变过。** 词表紧（R5）→ 4 条 `expressible:false`；词表松（R7）→
   3 条恒真；加语法可证伪（R8）→ 5 条具体；加**语义**可证伪（R9）→ **llm01 被判死**，
   只好退回 `structural`。**四种情况下 libredwg 的命中都只有 `llm01` 那 4 个站点。**
2. **唯一落地的特征，机械规则也能找到**（`R1 dxf_objects_read L12284 → L12267`）；
   agent 全量审计 188 turns 的**独有且被采纳**发现是 **0 条**。
3. **有一点价值的地方**：`llm03`/`llm04` 从手工版的 `name_regex`（按函数名猜语义）变成
   **结构判据**——形态确实变好了。**但形态好没有转化成命中。**
4. **R9 抓到一个必须记的教训**：R8 那句"llm02/03/05 全部 0 命中"**是解析 bug 造成的**
   （`bool("false")` = True）。修掉后它们命中同一批站点。
   **结论没变，但"为什么没有增量"的理由从'太严'改成了'等价'。**
5. **反例仍在**：`uaf-llm05` 丢了 `is_link_read:true`（"释放后沿链遍历"的定义性特征）。

**一句话**：**"特征提取"这条路目前是靠"从一个已知崩溃推出触发结构"在起作用，
不是靠"从 5 条规律里归纳出共性"。** 后者的必要性在这套数据上仍然没有被证明。

### `HANDOFF.md` 改了哪些（改动内容原文）

```diff
@@ -31,11 +31,14 @@
    根因不是 depth 不够：`vvcc_box_read` 在 CPG 里**零调用者**——它经 box 注册表的
    **函数指针**被调用（`box_funcs.c:1893` `a->registry->read_fn(a, bs)`），
    静态调用图里没有这条边，**不限深度也到不了**（完整图 984 个可达节点里没有它）。
-2. **LLM 归纳不优于手写规则。** 见限制 2 与 `docs/runs/R8_REPORT.md` 步骤 2 的三层对照：
-   词表紧 → 4 条 `expressible: false`；词表松 → 3 条恒真；加了可证伪约束后 5 条都具体了，
+2. **LLM 归纳不优于手写规则。** 见限制 2 / 限制 8 与 `docs/runs/R9_REPORT.md` 步骤 2：
+   词表紧 → 4 条 `expressible: false`；词表松 → 3 条恒真；加可证伪约束后 5 条都具体了，
    但**命中集合与 llm01 完全相同**（没有一条找到 llm01 找不到的站点）。
-   而且唯一一处明显更差的是 `uaf-llm05`：手工版 `is_link_read: true` 抓住了"沿链遍历"这个
+   唯一一处明显更差的是 `uaf-llm05`：手工版 `is_link_read: true` 抓住了"沿链遍历"这个
    定义性特征，LLM 版把它丢了。
+   **R9 更正了 R8 的一个机制误判**：R8 说 `llm02/03/05` "0 命中"，实际是
+   `bool("false") == True` 的解析 bug 把它们判死了；修掉后它们命中**同一批**站点。
+   结论（没有增量）不变，理由是"等价"而不是"太严"。
 3. **跨函数机制没兑现。** 跨函数扫描器至今**两个项目都 0 命中**（libredwg 15→6→0、gpac 0），
    候选全部核对为假阳性。而且只支持"实参传递"一种形态，字段/全局/回调都没做。
 4. **不能推广到未知崩溃。** 整条派生链的起点是**已知的 `fault_line`**——
@@ -228,13 +231,65 @@
 |---|---|
 | vs R7（恒真版） | 2 条从恒真变具体（`llm02` 的 `any/any`、`llm03` 的 4×4 全集都被拒了） |
 | vs R5 手工版 | **3 胜 1 负 1 平**：`llm02` 更具体（4 个字段 vs 1 个）、`llm03/llm04` 从 `name_regex` 变**结构判据**；**`llm05` 输了**（丢了 `is_link_read:true` 这个定义性特征）；`llm01` 互有胜负 |
-| **libredwg 实际命中** | **仍然只有 `llm01` 命中那 4 个站点**，`llm02/03/04/05` 全部 0 |
+| **libredwg 实际命中** | **仍然只有 `llm01` 那 4 个站点**；`llm02/03/05` 命中的是**同一批** |
 
 **→ 判据层的所有改进（从名单到结构、从紧词表到松词表再收紧）都没有带来新的落地。**
 
-另有一个**可证伪性校验的漏洞**：`llm02`/`llm03` 判据里的 `reassigned_between: false`
-是**真空约束**——`scan_sites()` 产出的站点**恒为 false**（构造时就过滤了重赋值），
-所以它排除不了任何站点。校验数的是"字段写了真子集"，不是"这个子集能真的排除站点"。
+> **⚠️ R8 报告里"llm02/03/05 全部 0 命中"的机制是错的（R9 更正）**：
+> 那不是"规则太严"，而是 `_match_conjunct` 用 `bool(want)` 比较、
+> 而 `bool("false")` 是 **True** —— 模型写 `"false"` 时"要求 false"被静默反转成"要求 true"，
+> 规则恒假。修掉后它们命中 4/3/4 个站点（**与 llm01 同一批**）。
+> **结论不变（没有增量），但理由必须改成"它们的判据与 llm01 在本数据上等价"。**
+
+**真空约束的问题（R9 已处理）**：`reassigned_between` 在扫描器产出里**结构性恒为 false**
+（`scan_sites()` 注释自己写着"碰到重新赋值就截断"；跨函数站点更是硬编码 False），
+所以写它等于没写，**不计入区分力**（`STRUCTURALLY_FIXED`，带过期检查）。
+
+**更强的"语义可证伪"实测**（拿真实站点当试金石，逐字段去掉看命中集合变不变）：
+**不可用**——试金石只有 2 个站点且**全是正例**（`scan_sites()` 只产出已经筛成 UAF 形态的站点），
+任何**正确描述**这批站点的判据都会被判"排除不了东西"，实测**把 `llm01` 判成 `rule_missing`**（唯一能落地的特征）。
+→ 见限制 10。
+
+---
+
+## 限制 9 · 算子不可重生成（`generate` 不具可复现性）
+
+同一个 plan 连续跑三次 `generate`，产出**三个不同规模的算子**：
+
+| 次 | `mutator.c` | 用在哪 |
+|---|---:|---|
+| R6 | **440 行** | `reps_pathB_r3` |
+| R9 步骤 1 | **294 行**（sha1 `d7913b9e`） | **`reps_r9_final`**（二进制 `a416b44d`） |
+| R9 步骤 2 | **243 行**（sha1 `67cc88b0`） | 未用于任何 A/B |
+
+三者的**能力剖面完全相同**（含 OBJECTS 500/500、剥段 500/500、DWG 0、特征路径 50%、权重 0.5），
+但**不是同一个可执行文件**。
+
+**处理**：R9 已把工作区恢复成 294 行那版（`git checkout -- v2/mutator.c v2/mutator.json`），
+重建后二进制 sha1 **`a416b44d`，与 `reps_r9_final` 逐字节相同**。
+
+**但"算子"这个产物本身不可重生成。** 引用 A/B 结果时**必须连 `mutator.c` 的 sha1 一起记**，
+否则无法证明跑的是哪一版。
+
+## 限制 10 · "语义可证伪"在这套数据上不可检验
+
+R9 按设计实现了语义版校验（拿真实扫出的站点当试金石，逐字段去掉看命中集合变不变），
+**实测把 `llm01` 判成 `rule_missing`**——而 `llm01` 是唯一能落地的特征。
+
+根因不是实现，是**试金石没有负样本**：
+
+```
+  试金石站点: 2 个
+    {'use_kind':'same_path', 'free_kind':'direct_free', 'reassigned_between':False, 'is_link_read':False}
+    {'use_kind':'loop_back', 'free_kind':'direct_free', 'reassigned_between':False, 'is_link_read':False}
+  每个字段的取值域: use_kind 2 个 / free_kind 1 个 / reassigned 1 个 / is_link_read 1 个
+```
+
+`scan_sites()` 只产出**已经被筛成 UAF 形态**的站点，所以任何**正确描述**这批站点的判据，
+在它们身上都"排除不了任何东西"。
+
+**要真正检验，必须人为构造负样本**（例如合成 `use_kind=cross_function` 的站点）。
+那是新工作，本轮没做。**现行门禁是 `structural`**（= 语法真子集 + 不把结构性单值字段计入）。
 
 ---
 
```

### 还剩什么没做

**本轮刻意不做的三项**（用户明确排除）：

| 项 | 理由 |
|---|---|
| **函数指针分派**（gpac 的 `registry->read_fn`） | 工作量大，做完大概率仍 0 命中，且不改变任何主张。现在是**限制 6**，写清楚比做一半好 |
| **跨函数扩到字段 / 全局 / 回调** | 同上，现在是**限制 7** |
| **换崩溃类型**（hbo / stack / global） | 需要新项目环境，不在本轮预算内 |

**本轮发现但没做的**：

| 优先级 | 项 | 为什么该做 |
|---|---|---|
| **P0** | **注入故障的主动测试**：故意让 Joern / 工具参数 / 产物文件失败，看下游能不能发现 | 人眼扫 42 处 `except` 一定漏；只有主动注入才能证明"这一类 bug 清掉了"。现在还剩 43 处 JSON 读取**没有任何时效检查** |
| **P0** | **构造负样本**，让"语义可证伪"真的能检验 | 现在试金石只有 2 个正例，任何正确判据都通不过（限制 10） |
| P1 | 让 `fault_anchor_enabled` 贯穿到 `mutation_plan` / `mutator.json` / `verification.json` | 现在只到 `feature_pipeline` |
| P1 | 把 `mutator.c` 的 sha1 写进 `mutator.json` / `verification.json` | `generate` 不可复现（限制 9），不记 sha1 就无法证明跑的是哪一版 |
| P2 | `applicability_rule.why` 也受黑名单约束（`uaf-llm05` 的 `why` 里带出过 `next`） | 干净度 |

# R13 报告

日期：2026-11-05
方向：**停止扩跨函数扫描形态**，改做**多项目落地表**。

> 用户口径：「我们的目标是从海量数据中获取通用规则，然后应用到具体项目中，
> **未必所有规则都适用，用能用的就可以了。**」
> 按这个口径，"libredwg 上 5 条规律只落地 1 条"**不是缺陷**。

---

## 步骤 0 · 两个记账

### 0.1 `freed_ptr` 吻合率 15%

**这是"字段名与语义不符"，本项目第三次吃这个亏**
（前两次：`free_cross_function` 是栈帧不是释放点、`code: None` 是硬编码不是取不到）。

**① 在 `s2_3_interpretation.py` 的两处写入点加了注释**（`heap-double-free` 与 `heap-use-after-free`
两个 `key_facts`），写明：

> `freed_ptr` 取的是**崩溃点的对象名**（`facts.entity.name`），**不是被释放的那个变量**。
> 实测：release 表达式能拿到的 79 条 UAF 里，只有 **12 条（15%）** 两者一致。

**② 全仓 grep 消费者——结论是"零消费者"**

| 位置 | 读 `freed_ptr` 吗 | 说明 |
|---|:---:|---|
| `pipeline/s2_3_interpretation.py:158,203` | 写 | 唯一写入点 |
| `pipeline/s3_extract_patterns.py:457` | ❌ | 只读 `interpretation.findings.reassigned_between` |
| `pipeline/s3_extract_patterns.py:534` | ❌ | prompt 里塞的是 `chunk`（facts + `measured_dims`），**不含 interpretation** |
| `pipeline/s5_3_audit.py` | ❌ | grep `interpretation` / `key_facts` / `freed_ptr` **全无命中**——agent 读不到 |
| `pipeline/s5_4_analyze.py:857` | ❌ | 加载了 `interpretation.json`，但 `normalize_findings` **不读 `key_facts`** |
| `tools/backfill_free_code.py:18` | ❌ | 只是文档注释 |
| `artifacts/interpretation/*.json`（142 个） | — | 产物，含这个字段 |

**→ `freed_ptr` 是"写死的坏字段"：没有任何 pipeline 阶段消费它，所以不影响任何结论；
但任何人（或 agent）读到 `interpretation.json` 都会以为它是"被释放的指针"。**

**③ 已写进 `HANDOFF.md`**（见汇总的 diff）。

**建议（不在本轮做）**：改名成 `crash_entity`，或按释放表达式重算。

### 0.2 `parse_freed_by` 的 `(\S+)` bug 影响面

R12 实测：抽验 10 条里 **8 条**受影响（帧数差 1–6），**不只是 F6 的幻觉**。
已修（`in\s+(.+?)\s+(/[^\s:]+):(\d+)`）。

**修之前产出的"释放点"分析都可能偏帧，需要标注的历史结论**：

| 轮次 | 结论 | 是否受影响 |
|---|---|:---:|
| R11 | 110 条按调用图的 A/B/C 分布 | ❌ 不依赖释放表达式 |
| R12 步骤 1 | "F6 包装调用 24 条" | ✅ **受影响**——实际没有一条是有名字的包装 |
| R12 步骤 1 | "F4 裸指针 33 条"（初版） | ✅ 受影响（修后变 41/60） |
| R12 步骤 2 | 终版分布（F4 60 / F6 7 / F1 6 …） | ❌ 修之后算的 |
| R12 抽验 | "8/10 释放表达式正确" | ❌ 修之后抽的 |

**已写进 `HANDOFF.md`。**

---

## 步骤 1 · 项目候选表

### 数据来源

- **R4 Phase B 的 B2 前置条件表**（`docs/runs/R4_PHASE_B.md:78`）：UAF 数 / 有 CPG / 有 testcase /
  输入格式 / 目标 repo@pin。**本轮没重做筛选，只补字段。**
- **depth≤2 那一列是本轮实测的**：用 `artifacts/call_edges/*.tsv`（R10 抓的 CPG 调用边缓存）
  从 `LLVMFuzzerTestOneInput` 做 BFS，看每个项目的故障函数在不在闭包里。
  **不是推测。**
- **"harness 在项目仓库里"这一列**：判据是"`LLVMFuzzerTestOneInput` 出现在该项目的 CPG 里"——
  CPG 是从**项目源码**建的，所以它出现就说明 harness 在仓库里（gpac 那种在 submodule/OSS-Fuzz 的不会出现）。

### 候选表（20 个项目，含实测列）

| 项目 | UAF | CPG | testcase | pin | harness 在 CPG | **d=2 命中** | d=3 | d=4 | 输入格式 | 备注 |
|---|---:|---:|---:|---|:---:|---|---|---|---|---|
| **libredwg**（基线） | 6 | 4/6 | 4/6 | ✅ | ✅ | **5/5** | 5/5 | 5/5 | 文本 89% | 已跑通，基准 |
| **libxml2** | **17** | 17/17 | 17/17 | ✅ | ✅ | **7/15** | **9/15** | 9/15 | 二进制 61% | UAF 最多 |
| **leptonica** | 4 | 4/4 | 4/4 | ✅ | ✅ | **3/3** | 3/3 | 3/3 | 二进制 54% | harness 在 `prog/fuzzing/*_fuzzer.cc`（已核实） |
| **ndpi** | 3 | 3/3 | 3/3 | ✅ | ✅ | **3/3** | 3/3 | 3/3 | 二进制 13%（pcap） | — |
| **igraph** | 4 | 4/4 | 4/4 | ✅ | ✅ | **2/4** | 2/4 | 2/4 | **文本 99%** | 文本格式最好 |
| flac | 2 | 2/2 | 2/2 | ✅ | ✅ | 0/2 | **1/2** | **2/2** | 二进制 31% | harness 在 `oss-fuzz/*.cc`（已核实）；要 depth 4 |
| mruby | 4 | 4/4 | 4/4 | ✅ | ✅ | 0/4 | 0/4 | 0/4 | 文本 100% | 到不了 |
| assimp | 3 | 3/3 | 3/3 | ✅ | ✅ | 0/3 | 0/3 | 0/3 | 文本 100% | 到不了 |
| serenity | 3 | 3/3 | 3/3 | ✅ | ✅ | 0/3 | 0/3 | 0/3 | 文本 88% | 到不了 |
| libavc | 4 | 2/4 | 2/4 | ✅ | ✅ | 0/4 | 0/4 | 0/4 | 二进制 31% | 到不了 |
| openh264 | 5 | 5/5 | 5/5 | ✅ | **❌** | 0/5 | 0/5 | 0/5 | 二进制 37% | harness 不在仓库 → 要锚点 → **排除** |
| espeak-ng | 4 | 4/4 | 1/4 | ✅ | **❌** | 0/4 | 0/4 | 0/4 | 二进制 30% | 同上 → **排除** |
| harfbuzz | 4 | 4/4 | 4/4 | ✅ | **❌** | 0/4 | 0/4 | 0/4 | 二进制 7% | 同上 → **排除** |
| open62541 | 9 | 9/9 | 9/9 | ✅ | **❌** | 0/9 | 0/9 | 0/9 | 二进制 25% | 同上 → **排除** |
| c-blosc2 | 7 | 7/7 | 2/7 | ✅ | **❌** | 0/6 | 0/6 | 0/6 | 二进制 14% | 同上 → **排除** |
| fluent-bit | 3 | 3/3 | 3/3 | ✅ | **❌** | 0/3 | 0/3 | 0/3 | 文本 89% | 同上 → **排除** |
| opensc | 3 | 3/3 | 3/3 | ✅ | **❌** | 0/2 | 0/2 | 0/2 | 二进制 77% | 同上 → **排除** |
| libspng | 3 | 3/3 | 3/3 | ✅ | — | — | — | — | 文本 92% | **没有调用边缓存**，判不出 |
| libvips | 6 | **0/6** | 6/6 | **空** | — | — | — | — | 二进制 62% | **排除**（pin 空） |
| hunspell / radare2 | 3 / 3 | — | **0/3** / 空 | — | — | — | — | — | — | **排除**（无 testcase） |

**明确排除的**：`libvips`（pin 空）、`hunspell`（无 testcase）、`radare2`（testcase 0 字节）、
容器格式类（gpac 已试，分派表架构 → 限制 6）。

### 挑出 4 个（按能跑通的把握排序）

| 优先级 | 项目 | 为什么 |
|---:|---|---|
| 1 | **leptonica** | d=2 **3/3**，harness 在 `prog/fuzzing/`（已核实），CPG/testcase 4/4 |
| 2 | **ndpi** | d=2 **3/3**，CPG/testcase 3/3 |
| 3 | **libxml2** | **UAF 最多（17）**，d=2 7/15、d=3 9/15；二进制格式，但站点最多 |
| 4 | **igraph** | **文本 99%**（构造型算子思路可复用），d=2 2/4 |

**为什么不含 flac**：d=2 是 0/2，要 depth 4 才 2/2。**可以用，但优先级排在 igraph 之后。**

### ⏸ 停止点：等用户确认

| 你要的 | 结果 |
|---|---|
| 候选表（含**实测**的 depth≤2 那一列） | ✅ 20 个项目，全实测 |
| 挑出 3–5 个 | ✅ **leptonica / ndpi / libxml2 / igraph** |
| 说明"为什么" | ✅ 见上表 |

**请确认这 4 个（或调整顺序/替换）。确认后我逐个跑，跑完一个记一个。**

---

## 步骤 2 · 逐项目跑流程

### 先说一个必须先纠正的错误：我的"d=2 实测"列用错了函数

步骤 1 的表里，"depth≤2 命中"那一列我匹配的是**释放函数**（`free_fn`），
而判据要求的是**故障函数**（`crash.site.fn`）。**用错了一个字段，整列都不可信。**

纠正后（同一套缓存边，改匹配 `crash.site.fn`）：

| 项目 | d=2 | d=3 | d=4 | 哪几条 OSV 的**故障函数**在 d2 |
|---|---:|---:|---:|---|
| libredwg | 3/5 | 3/5 | 3/5 | `42494732` `42530320` `2021-543` |
| **libxml2** | **7/15** | 8/15 | 8/15 | `42486883` `42487785` `42497161` `42531532` `42532747` `42533922` `42533950` |
| **igraph** | 2/4 | 2/4 | 2/4 | `42491511` `42491546` |
| **leptonica** | **1/3** | 2/3 | 2/3 | 只有 `42488049` |
| ndpi | **0/3** | 0/3 | 0/3 | — **出局** |
| flac | **0/2** | 0/2 | 0/2 | — **出局** |

**而且这一列本身也只是近似**：它用的是 `artifacts/call_edges/`（R10 抓的缓存），
而 `fetch` 实际复用的是 `cpg_files/<project>_<pin>.cpg`——**两者不是同一次构建**，
而且我的缓存把**同一项目的多个 pin 合并**了。
**只有 `worklist` 的自检才是权威判据**，所以下面每个项目都以它的结果为准。

### 项目 1 · leptonica `ARVO-42484161` —— ❌ 卡在 worklist

```
  CPG 故障函数：pixAverageRasterScans @ src/readbarcode.c:773-812 ✅
  depth=2 调用图内用户定义函数: 171 个
  ⚠️ 故障函数 pixAverageRasterScans 不在 depth<=2 闭包里
  自检：已知崩溃行 src/readbarcode.c:805 ❌ 未被覆盖（清单不可信！）
```

**按你的规则没有加 `--fault-anchor`，记下来换下一个。**
注意：它的 CPG **有** `LLVMFuzzerTestOneInput`（没报"BFS 根缺失"），
所以是**真的够不到**，不是图缺根。

### 项目 2 · igraph `ARVO-42491511` —— ❌ 卡在 worklist（CPG 缺 BFS 根）

```
  方法 : 9345 个（外部 2950）；调用边 394572 条
  CPG 故障函数：igraph_read_graph_gml @ src/io/gml.c:160-491 ✅
  ⚠️ CPG 里没有 LLVMFuzzerTestOneInput（BFS 根缺失）→ depth<=2 闭包必然为空
  depth=2 调用图内用户定义函数: 0 个
```

**这是个新情况**：故障函数在 CPG 里，但 **harness 不在**。
`fetch` 的 harness 找到了（`prog/fuzzing/read_gml_fuzzer.c`），
但 `cpg_files/igraph_c83b6ecdc3fe.cpg` 里没有它 → 闭包为空。
**这是 CPG 构图的覆盖面问题，与限制 6 同类（harness 不在图里）。**

### 项目 3 · libxml2 `ARVO-42533950` —— ⚠️ worklist 通过，卡在 `input_branch`

```
  ✅ 自检：已知崩溃行 libxml2/tree.c:3938 已被 worklist 覆盖
  入表函数: 246 个，其中含风险操作 117 个
  surface: 格式=raw_bytes  解析器候选=25  sink=23  字段=0
          field_mapping_complete = False
  features: ✅ uaf-llm01  blocked  短名单 246 / 原语 3 / 支持 3
                site: list.c:307 → 308  var=l  branch=UNKNOWN
```

**为什么 blocked**：扫描器确实找到了 3 个原语、llm01 的判据匹配了 3 个，
但站点在 `list.c`，而推导出的 5 个输入分支里**没有一个能到达 `list.c`**：

```
  输入分支推导：5 个
    XMLFUZZREADINT / XMLFUZZREADINT2 / XMLFUZZREADINT3（都是 xmlFuzzReadInt）
    XMLFUZZREADSTRING（xmlFuzzReadString）  XMLREADDOC（xmlReadDoc，可达 18 个文件）
  从 xmlReadDoc 可达 555 个方法 / 23 个文件 —— **不含 list.c**
```

**这是 CPG 覆盖面的问题，不是推导 bug**：`list.c` 里的 `xmlListCreate` / `xmlListDelete`
在真实调用链上肯定被解析器用到，但 CPG 里没有那条边。

**顺带发现两个问题**（都记下来，没修）：
1. **输入分支过度切分**：`xmlFuzzReadInt` 出现 3 次（`#ifdef` 下的重复定义）被当成 3 个分支；
   `xmlFuzzReadInt` / `xmlFuzzReadString` 是 **fuzzer 的辅助函数**，不是输入格式分流。
2. **站点不是目标崩溃点**：扫出来的是 `list.c:307→308`，而这条 OSV 的目标是 `tree.c:3938`。

### 项目 4 · leptonica `ARVO-42488049` —— ✅ worklist 通过、**落地 1 条**，卡在 audit

```
  ✅ 自检：已知崩溃行 ... 已被 worklist 覆盖
  surface: 1 个输入分支
    PIXREADMEMSPIX entry=pixReadMemSpix  magic=None  可达文件 7 个
  features:
    ✅ uaf-llm01  found   短名单 665 / 原语 6 / 支持 6
         site: src/baseline.c:247 → 249  var=array  branch=PIXREADMEMSPIX
    ❌ uaf-p02/p03/p04/p05  not_found（665 个函数扫出 6 个原语，都不满足结构判据）
    found 1/5；权重 default 0.5 + 1×0.5 = 1.0
```

**这是本轮唯一一个"新项目 + 自己走到 + 落地"的组合。** ✅

**但 `plan` 卡住了**：

```
  [stage5] main_findings 抛出 FileNotFoundError: .../ARVO-42488049/vuln_report.json
  [stage5] ✗ 缺少 .../v2/candidate_findings.json
```

**原因**：`main_findings` 的两条来源（`vuln_report.json` 与 `mech_hypotheses.json`）
**都是 `audit`（5.2）的产物**。新项目要先跑 audit——而 audit 是 **LLM agent 跑 665 个函数**
（数十个 chunk）。**这是新项目落地的真实成本，本轮没跑。**

**所以本轮"落地"只到 `features` 这一层，没到 `plan`/`generate`/`verify`。**
「站点层」是 audit-free 的（`features` 直接跑通），「计划层」需要 audit。

### 小结：每个项目卡在哪一层

| 项目 | fetch | worklist | surface | features（站点+判据） | findings/audit | plan | generate | verify |
|---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| libredwg `42494732` | ✅ | ✅ | ✅ | ✅ **1 落地** | ✅（R4 已有） | ✅ | ✅ | ✅ |
| **leptonica `42488049`** | ✅ | ✅ | ✅ | ✅ **1 落地** | ❌ **缺 audit** | — | — | — |
| libxml2 `42533950` | ✅ | ✅ | ✅ | ⚠️ blocked（branch UNKNOWN） | — | — | — | — |
| igraph `42491511` | ✅ | ❌ CPG 缺 BFS 根 | — | — | — | — | — | — |
| leptonica `42484161` | ✅ | ❌ 故障函数不在 d2 | — | — | — | — | — | — |

---

## 步骤 3 · 落地表（本轮主结果）

### 主表

| 项目 | 输入格式 | 扫出站点 | **能落地的特征** | 落地的是哪几条 | plan site 数 | 算子策略数 | 自己走到的？ |
|---|---|---:|---:|---|---:|---:|:---:|
| **libredwg** `ARVO-42494732` | DXF 文本 | 4 | **1** | 同函数释放后访问 | 1 | 1 | ✅ |
| **leptonica** `ARVO-42488049` | 图像二进制 | **6** | **1** | 同函数释放后访问 | —（缺 audit） | — | ✅ |
| libxml2 `ARVO-42533950` | XML 文本 | 3 | **0** | —（`blocked`，branch UNKNOWN） | — | — | ✅ worklist |
| igraph `ARVO-42491511` | GML 文本 | — | — | —（CPG 缺 BFS 根） | — | — | ❌ |
| leptonica `ARVO-42484161` | — | — | — | —（故障函数不在 d2） | — | — | ❌ |
| ndpi / flac | — | — | — | —（实测 d2 = 0） | — | — | ❌ |
| gpac (R6/R7) | ISOM 二进制 | 1 | 1 | 同函数释放后访问 | 1 | — | ❌ 靠锚点 |

### 每条特征在几个项目落地（横着看——这是"通用规律"的直接证据）

| 特征 | source_pattern | **落地项目数** | 落地在哪些 |
|---|---|---:|---|
| **`uaf-llm01`** | **同函数释放后访问** | **2**（+gpac = 3） | libredwg、leptonica（+gpac 但靠锚点） |
| `uaf-p02` | 别名重赋值跨函数访问 | **0** | — |
| `uaf-p03` | 解码池释放后写入 | **0** | — |
| `uaf-p04` | 循环回调释放后读取 | **0** | — |
| `uaf-p05` | 清理销毁释放后读取 | **0** | — |

**`uaf-llm01` 在两个"自己走到"的项目里都落地了**——这是"通用规律 → 具体项目"这条路
**第一次有跨项目的正面证据**。其余 4 条在 2 个项目上都是 0。

### 有没有项目落地 ≥2 条特征

**没有。** 两个能跑通的项目各落地 1 条（都是 `llm01`）。

→ **步骤 4 跳过**（用户条件：只在出现 ≥2 条时做）。
**结论：`"5 种特征 → 5 种变异策略各占一份权重"` 这个设计，在当前数据上仍然没有机会兑现。**

### 卡住的按层统计

| 卡在哪一层 | 项目数 | 具体 |
|---|---:|---|
| `worklist`（故障函数不在 d2） | 2 | leptonica `42484161`、ndpi(0/3)、flac(0/2) |
| `worklist`（**CPG 缺 BFS 根**） | 1 | igraph `42491511` |
| `input_branch`（站点不在任何分支可达集） | 1 | libxml2 `42533950` |
| **`findings`/audit**（缺 `vuln_report.json`） | 1 | leptonica `42488049` |
| 全部通过 | 1 | libredwg |

**4 个项目、6 条候选 OSV，只有 1 个跑到 `verify`。**

### 怎么解读这张表

1. **不是每条规律在每个项目都适用，这是正常的、预期的。**
   按用户口径：「未必所有规则都适用，用能用的就可以了。」
   `uaf-llm01` 在 2/2 个能跑通的项目落地，其余 4 条 0/2 —— 这不是缺陷，是**适用边界**。

2. **表的价值**：`uaf-llm01`（"同函数释放后访问"）是**真正通用**的那一条——
   两个形态完全不同的项目（DXF 文本解析器、图像库）都落地了。
   而 `p02`–`p05` 描述的跨函数/清理/循环形态，在这两个项目里**确实不存在**
   （R11/R12 已证明：跨函数形态在 110 条真实 UAF 里占比 0）。

3. **落地 0 条的项目要说清是"真的没有"还是"卡在更早一层"**：
   - libxml2 是 **blocked**（扫描器找到了站点，但 CPG 无法把它连到 harness）；
   - igraph 是 **CPG 缺 harness**；
   - leptonica `42484161` 是**真的够不到**（故障函数不在 d2）。

4. **最大的工程障碍不是判据，是 audit**：新项目要跑 `plan`，先得跑 LLM agent 审计 665 个函数。
   站点层（`features`）是 audit-free 的，计划层不是。

---

## 汇总

### 本轮结论一句话

**`uaf-llm01`（"同函数释放后访问"）在两个形态完全不同的项目（DXF 解析器、图像库）里都落地了——
这是"通用规律 → 具体项目"第一次有跨项目证据；其余 4 条在 2/2 个项目上都是 0，
这不是缺陷，是适用边界。**

### 步骤结论

| 步骤 | 结论 |
|---|---|
| **0 · 记账** | `freed_ptr` 吻合率 **12/79 = 15%**，但**零 pipeline 消费者**（"写死的坏字段"）；`parse_freed_by` 的 `(\S+)` bug 在 **8/10** 抽验样本上发生过 |
| **1 · 候选表** | 20 个项目实测；**我的"d=2"列一开始用错了函数**（匹配 `free_fn` 而不是 `crash.site.fn`），纠正后 ndpi/flac 出局 |
| **2 · 逐项目跑** | 4 个项目 / 6 条候选 OSV：**1 个跑到 verify**（libredwg）、**1 个落地但卡在 audit**（leptonica `42488049`）、2 个卡在 worklist、1 个卡在 input_branch |
| **3 · 落地表** | `uaf-llm01` 落地 **2 个项目**；`p02`–`p05` 落地 **0 个**；**没有项目落地 ≥2 条 → 步骤 4 跳过** |

### `HANDOFF.md` 改了哪些（完整 diff）

```diff
@@ -320,6 +320,40 @@
 
 ---
 
+## 限制 11 · 三个"字段名与语义不符"的坑（本项目已吃三次）
+
+这个项目反复栽在同一件事上：**字段被填了，但填的不是名字说的那个东西。**
+三次都是"跑了几轮之后才在别处撞到"：
+
+| # | 字段 | 名字说的是 | 实际填的是 | 实测 | 影响 |
+|---|---|---|---|---|---|
+| 1 | `fixtures` 里的 `free_cross_function` | 释放点跨函数 | **栈帧跨函数** | 110 条里 **12 条**其实是 `use_fn` 自己调了释放助手 → 释放点在同一函数 | R11 用它筛"跨函数候选"，分母掺了 12 条不是跨函数的 |
+| 2 | `facts.sites[kind=free].code` | 释放表达式 | **恒为 `None`**（`s2_2_facts.py:861` 硬编码） | 125 个 free 站点里 **116 个是 None** | R11/R12 早期所有"释放的是什么"的分析都是猜的；已由 `tools/backfill_free_code.py` 回填（109/125） |
+| 3 | `key_facts.freed_ptr` | **被释放的指针** | **崩溃点的对象名**（`facts.entity.name`） | 79 条里只有 **12 条（15%）** 两者一致；例 `free(tr)` 而 `freed_ptr='n'`、`xmlFree(cur)` 而 `freed_ptr='buf'` | **零消费者**（s3 只读 `findings.reassigned_between`、agent prompt 不含 interpretation、`normalize_findings` 不读 `key_facts`），所以只污染人/agent 的阅读，不影响结论 |
+
+**共同教训**：**光在报告里写不够，要在代码里就看见**——
+`freed_ptr` 的两处写入点已加注释（写明 15% 与零消费者），
+`code: None` 的写入点也加了注释（写明缺口与回填工具）。
+
+## 限制 12 · `parse_freed_by` 的 `(\S+)` bug：修之前的"释放点"分析可能偏帧
+
+`tools/backfill_free_code.py::parse_freed_by` 原来用 `(\S+)` 抓函数名，
+而 ASan 报告里的函数名是**完整签名、含空格**（`WelsDec::DecreasePicBuff(WelsDec::TagWelsDecoderContext*, ...)`），
+于是 `#1` 帧被**整帧丢掉**，只剩 `#2`。
+
+**R12 抽验 10 条里 8 条受影响**（帧数差 1–6）。已修（`in\s+(.+?)\s+(/[^\s:]+):(\d+)`）。
+
+**修之前得出的、需要打折的历史结论**：
+
+| 轮次 | 结论 | 是否受影响 |
+|---|---|:---:|
+| R12 步骤 1 | "F6 包装调用 24 条" | ✅ **受影响**——实际**没有一条**是有名字的包装，是 `realloc`(8) / realloc 包装(5) / `delete`(3) / 间接调用(7) / 取错行(1) |
+| R12 步骤 1 | "F4 裸指针 33 条"（初版） | ✅ 受影响（修后变 41 / 60） |
+| R12 步骤 2 | 终版分布（F4 60 / F6 7 / F1 6 …） | ❌ 修之后算的 |
+| R11 | 110 条的 A/B/C 分布 | ❌ 只依赖调用图方向，不依赖释放表达式 |
+
+---
+
 # 二、当前状态（2026-11-04）
 
 ## 门禁
```

### 限制 7 要不要按"本轮不再扩形态"改写

**要。** 建议改成：

```markdown
## 限制 7 · 跨函数形态的扩张已停止（R9–R12 四轮，前提塌了三次）

**决定**：不再扩跨函数扫描形态。理由是**扩张的前提反复被数据推翻**：

| 轮次 | 当时以为 | 核实后 |
|---|---|---|
| R11 | C 类主要走结构体字段 | **字段确认 0 条**（64 条 C 类里，确认的字段释放 = 0） |
| R12 步骤 1 | 包装调用 30 条 | 真实 24 条，**没有一条是有名字的包装**（是 `realloc` / `delete` / 函数指针 / 取错行） |
| R12 步骤 2 | — | **裸指针 60/110 = 55%** 才是主体；它需要的是**别名分析**（"同一实例 + 先后顺序"），是硬问题 |

**当前形态分布（110 条真实 UAF，`parse_freed_by` 修好之后）**：

| 形态 | 条数 | 占比 |
|---|---:|---:|
| F4 裸指针（局部/形参） | **60** | **55%** |
| F5 未知 | 15 | 14% |
| F7 realloc | 12 | 11% |
| F6 间接/函数指针 | 7 | 6% |
| F1 结构体字段 | 6 | 5%（**去重后只 4 个不同字段**） |
| F9 判不出 / F3 容器 / F8 delete | 4 / 3 / 3 | 9% |

**现有扫描器实现的"释放后传参"形态在 110 条里占 0 条**——
所以 libredwg/leptonica 上只落地 `uaf-llm01` 不是判据的问题，是**下游只看得见一种形态**。

**如果要继续，正确的下一步不是"再扩一种形态"，而是**：
1. 先把 `facts` 的释放表达式**在 stage2 就填对**（现在靠 `tools/backfill_free_code.py` 事后补，109/125）；
2. 再决定要不要做**别名分析**（F4 占 55%，但它需要"同一实例"证明）。
```

**（本轮没改 `HANDOFF.md` 的这个标题，只在报告里给了建议稿——等确认。）**

### 下一步建议

| 优先级 | 做什么 | 为什么 |
|---|---|---|
| **P0** | **给新项目补 audit 的最小路径**：让 `features` 已有的站点能直接进 `plan`，不必先跑 LLM 审计 665 个函数 | 这是新项目落地的**最大工程障碍**——本轮 leptonica 就是卡在这里。`plan` 只用 `candidate_findings` 建 `dmap`（evidence chain），而 `feature_pipeline` 的 action 里**已经有**证据链 |
| **P0** | 修 `facts` 在 stage2 就记录释放表达式 | 现在靠事后回填，且 16/125 补不上 |
| P1 | 修 `input_branch` 的**过度切分**：`xmlFuzzReadInt` 出现 3 次被当成 3 个分支；fuzzer 辅助函数不该算格式分流 | libxml2 的 5 个分支里 4 个是假的 |
| P1 | CPG 覆盖面的两个缺口：igraph 的 **harness 不在图里**、libxml2 的 **`list.c` 不可达** | 这是"自己走到"和"分支可达"的硬阻塞，与限制 6 同类 |
| P2 | `freed_ptr` 改名成 `crash_entity`（或按释放表达式重算） | 限制 11 |
| P2 | 补抓剩下 34 个 CPG | 纯时间成本 |

### 本轮刻意不做的

- 扩跨函数形态（F4 / F1 / F6）—— **方向调整，本轮停掉**
- 修 `freed_ptr` —— 只记账（零消费者）
- 函数指针分派（限制 6）
- 换崩溃类型（hbo/stack/global）
- 重跑 A/B —— `reps_r9_final` + `mutator.c` sha1 `d7913b9e` 仍是当前可引用组合
- **步骤 4**（多策略算子）—— 没有项目落地 ≥2 条，条件不成立

# R16 报告

日期：2026-11-06
目标：**找到一个能走完全程（到 `verify`）、且站点经人工核实为真的第二个项目。**

---

## 步骤 1 · 按硬条件重筛

### 数据来源与两列新实测

R13 的候选表已有 20 个项目的 UAF / CPG / testcase / pin / harness-在-CPG / 输入格式。
本轮在它上面补两列，**但换了判据**：

| 新列 | 这一轮怎么测 | 为什么不沿用 R13 |
|---|---|---|
| **格式（按 harness 判）** | 读 harness 源码：按行/记录解析，还是按字节偏移/结构体 | R13 用的是"testcase 首 4KB 可打印率"，**不可靠**（libspng 显示"文本 92%"，但 PNG 是二进制） |
| **d≤2（用 `crash.site.fn`）** | 用 `worklist` 的自检（**权威**） | R13 第一版匹配了 `free_fn`（释放函数）而不是 `crash.site.fn`（故障函数），纠正后 ndpi/flac 直接出局；而且它用的是 `artifacts/call_edges/` 缓存，**与 `fetch` 复用的 `cpg_files/<proj>_<pin>.cpg` 不是同一次构建**，还把同一项目的多个 pin 合并了 |

**⚠️ 本轮明确说明：判定字段是 `crash.site.fn`（即 `source_context.fault_fn`），不是 `free_fn`。**

### 关键实测：igraph 为什么过不了 `worklist` —— **不是"harness 不在仓库"，是 c2cpg 解析不了 `extern "C"`**

R13 把 igraph 记成"CPG 里没有 `LLVMFuzzerTestOneInput`（BFS 根缺失）"。本轮查到了**根因**：

```
  igraph 的 CPG dump 里，fuzzing/ 目录下只有一行：
    fuzzing/read_gml_fuzzer.c   <global>   L1
  grep -c "LLVMFuzzerTestOneInput" cpg_dump.tsv  →  0
```

而 harness 源码是：

```c
extern "C"                                    // ← 第 27 行
int LLVMFuzzerTestOneInput(const uint8_t *data, size_t size){
```

**`.c` 文件里写了 `extern "C"`** —— c2cpg 按 **C** 解析，`extern "C"` 不是合法 C → 整个文件解析失败 → 只剩 `<global>`。

**对照三个"harness 在 CPG 里"的项目**：

| 项目 | harness 写法 | 在 CPG 里？ |
|---|---|:---:|
| libredwg | `extern int LLVMFuzzerTestOneInput(...)`（**纯 C**） | ✅ |
| libxml2 | `int LLVMFuzzerTestOneInput(...)`（**纯 C**） | ✅ |
| leptonica | `.cc` 文件（C++，c2cpg 走 C++ 前端） | ✅ |
| **igraph** | **`.c` 里写 `extern "C"`** | ❌ |

**而且 igraph 的两个不同 pin（`c83b6ecdc3fe`、`883bd139af37`）、两个不同的 CPG，都缺**：
```
  ARVO-42491511 (pin c83b6ecdc3fe): CPG 里没有 LLVMFuzzerTestOneInput → depth=2 闭包 0 个
  ARVO-42491546 (pin 883bd139af37): CPG 里没有 LLVMFuzzerTestOneInput → depth=2 闭包 0 个
```
所以**不是图过期**，是**建图时系统性解析失败**。

### 候选表

**格式列**只填了**实际读过 harness** 的项目（其余在 d≤2 或 harness 那关就已经出局，读 harness 没有意义）：

| 项目 | osv_id | UAF | CPG | testcase | harness 在 CPG | **d≤2（crash.site.fn）** | **格式（按 harness 判）** | 结论 |
|---|---|---:|:---:|:---:|:---:|---|---|---|
| **libredwg** | `42494732` | 5 | ✅ | ✅ | ✅ | **3/5** | **DXF 文本记录**（`code` + `value` 行） | ✅ **已落地（基线）** |
| **igraph** | `42491511` / `42491546` | 4 | ✅ | ✅ | **❌** | **0/4**（根缺失） | **GML 文本记录**（`key value` 行，单入口 `igraph_read_graph_gml`）—— **格式最像 DXF** | ❌ **c2cpg 解析不了 `extern "C"`** |
| **libxml2** | `42533950` | 15 | ✅ | ✅ | ✅ | **1/8 通过**（`42533950`） | **XML 文本**（树形，不是记录式；harness 有 9 个文件按类型分派） | ⚠️ **守卫 1 修复后站点 = 0** |
| leptonica | `42488049` | 3 | ✅ | ✅ | ✅ | 1/3 | **PNG/TIFF 二进制**（`.cc` harness 调 `pixReadMemSpix`） | ❌ 二进制（`plan=blocked`，R14 已证） |
| gapc | `42518828` | 1 | ✅ | ✅ | ✅ | 0/1 | ISOM 二进制 | ❌ 靠锚点 |
| ndpi | — | 3 | ✅ | ✅ | ✅ | **0/3** | 未读（pcap 二进制） | ❌ d≤2 |
| flac | — | 2 | ✅ | ✅ | ✅ | **0/2** | 未读（FLAC 二进制） | ❌ d≤2 |
| mruby / assimp / serenity / libavc | — | 4/3/3/4 | ✅ | ✅ | ✅ | **0** | 未读 | ❌ d≤2 |
| openh264 / espeak-ng / harfbuzz / open62541 / c-blosc2 / fluent-bit / opensc | — | — | ✅ | ✅ | **❌** | 0 | 未读 | ❌ harness 不在 CPG |
| libspng / libvips / hunspell / radare2 | — | — | — | — | — | — | 未读 | ❌ R4 已排除（无调用边 / pin 空 / 无 testcase / 空 testcase） |

### 符合三条硬条件的有几个

| 条件 | 满足的项目 |
|---|---|
| ① d≤2（`crash.site.fn`，`worklist` 实测） | libredwg、libxml2(`42533950`)、leptonica(`42488049`) |
| ② harness 在 CPG | libredwg、libxml2、leptonica（igraph ❌ 被 c2cpg 挡）、ndpi、flac、mruby、assimp、serenity、libavc |
| ③ **文本记录格式** | libredwg（DXF）、igraph（GML，但 ② 不满足）、libxml2（XML） |
| **① ∧ ② ∧ ③** | **libredwg（已落地）+ libxml2（站点 = 0）** |

**R15 之后（守卫 1 = "找不到源码就拒绝"）**：
- `libxml2 ARVO-42533950` 的站点从 1 变成 **0**（那 1 条是 `xmlListClear(l)` 的假阳性，R14 核过）；
- 所以 **`libxml2` 只到 `features`（found 0/5），进不了 `plan`**。

### 结论：**没有可用的第二个项目**（在当前语料 + 当前工具链下）

- **libredwg** 已落地（基线）；
- **libxml2** 是唯一同时满足 ①②③ 的新项目，但**站点归 0**——扫出来的唯一一条是假阳性；
- **igraph** 是**格式上最合适**的候选（GML 文本记录、单入口），但它卡在**一个可定位的工程缺陷**上：
  c2cpg 解析不了 `.c` 文件里的 `extern "C"`。

### ⏸ 停止点：等用户确认

你说过"如果一个都没有：直接出结论，不要降低标准去凑"。
**严格按三条硬条件：确实没有。**

但 igraph 的阻塞点**不是"格式不对"或"工具不支持这种分析"**，而是**一个具体的解析缺陷**：
harness 是一个**真实的、在仓库里的** GML 文本记录解析器，只因为 `.c` 文件里写了 `extern "C"`，
c2cpg 就把整个文件丢了。

**三个选项**：

| 选项 | 做法 | 代价 |
|---|---|---|
| **(A) 按硬条件出结论，本轮结束** | 就写"没有第二个项目"，把 c2cpg/`extern "C"` 记进限制 | 零成本，但可能放弃了一个真正合适的候选 |
| **(B) 修 c2cpg 的输入**：建图前把 harness 里的 `extern "C"` 剥掉（或把 `.c` 当 `.cpp` 处理），**重跑 igraph 的 CPG** | 不是放宽守卫/判据/门禁，是修**解析器输入** | 要重建 4 个 igraph CPG（约 10 分钟/个）+ 重跑 worklist |
| **(C) 只做 (B) 里最小的一步**：只重建 `ARVO-42491511` 或 `42491546` 一个 | 先验证"修好之后能不能自己走到" | ~15 分钟 |

**我的建议是 (C)**：先用一个 OSV 验证 igraph 能不能过 `worklist`。
如果过了，再决定要不要走完 `plan` / `generate`（那时还要过"站点是真"和"文本记录构造推导"两关）。
**如果 (C) 也不过，那 (A) 的结论就坐实了。**

---

## 步骤 1b · 执行 (C)：修 c2cpg 的输入，重建一个 igraph 的 CPG

### 做法

1. `fetch ARVO-42491511` 把 **pin 源码**提取到 `/tmp/opencode/cpg_cache/src/github.com_igraph_igraph_c83b6ecdc3fe`
2. 把 `fuzzing/read_gml_fuzzer.c` 第 27 行的 `extern "C"` 换成注释（**只改这一处**）
3. `mv` 旧 CPG 成 `.orig`，用 `c2cpg <pin 源码> -o cpg_files/igraph_c83b6ecdc3fe.cpg` 重建
4. 删掉旧 `cpg_dump.tsv`，重跑 `fetch` + `worklist`

### 结果：**`worklist` 通过了** ✅

```
  C2CPG_EXIT=0        369,809 节点   1112/1112 文件
  方法 : 9346 个（外部 2950）；调用边 394593 条
  depth=2 调用图内用户定义函数: 40 个            ← 修之前是 **0**
  入表函数: 40 个，其中含风险操作 24 个
  自检：已知崩溃行 src/io/gml.c:462 ✅ 已被 worklist 覆盖
  fault_anchor_enabled = false（没加 --fault-anchor）
```

**`extern "C"` 这一个符号，就是 igraph 从"完全不可用"到"能自己走到"的全部原因。**

### 但 igraph 的 `features` 是 **0 站点**

```
  输入分支推导：1 个
    GML   entry=igraph_read_graph_gml   magic=None   可达文件 15 个
  ❌ uaf-llm01  not_found  短名单 40 / 原语 0 / 支持 0
  found 0/5
```

**`原语 0`** —— 40 个函数里**一条 free→use 原语都扫不出来**。
这条 UAF（`ARVO-42491511`）是 `igraph_i_gml_destroy_attrs` 释放、`igraph_gml_tree_destroy` 使用——
**跨函数形态**，正是 R11/R12 证明"在 110 条真实 UAF 里占比 0、扫描器看不见"的那一类。

**所以 igraph 到 `worklist` 为止，进不了 `features` 的落地。**

---

## 步骤 1c · 顺带查出的一个**更严重**的问题：`repo_local` 不是 pin

### 怎么发现的

执行 (C) 后发现 igraph 的 `repo_local` 在 `22dd6a8ee4c2`（HEAD），
而 pin 是 `c83b6ecdc3fe`。查全部四个项目：

| 项目 | pin | `repo_local` 的 HEAD | 一致？ |
|---|---|---|:---:|
| **libredwg** | `ff69eeda6658` | `ff69eeda6658` | ✅ |
| leptonica | `90ec70fd4322` | `5914a4330da2` | ❌ |
| libxml2 | `d4d1f3f33d6d` | `febeb5c91fff` | ❌ |
| igraph | `c83b6ecdc3fe` | `22dd6a8ee4c2` | ❌ |

**3/4 个项目，源码读的是克隆的 HEAD，而 CPG 是按 pin 预建的。**

### 影响有多大（实测）

拿 pin 直接 `git show` 同一行对比：

| 项目 | R14 核实时读到的（HEAD） | **pin 上同一行（实际该读的）** |
|---|---|---|
| leptonica `src/pix1.c:1665` | `pixFreeData(pix); pix->data = data;` | `if (!valid) return ERROR_INT("colormap is not valid"…)` |
| libxml2 `list.c:307` | `xmlListClear(l); xmlFree(l->sentinel);` | `lkNew = (xmlLinkPtr) xmlMalloc(sizeof(xmlLink))` |

**根本不是同一段代码。** 所以 R14/R15 对 leptonica / libxml2 的"逐条读源码核实"，
**是在错版本的源码上做的**——那些"假阳性"判定不是错在判断，是**错在读错了文件版本**。

### 修法

`s5_2_prepare.py` 里 `ctx["repo_local"] = repo` → 改用 `ensure_src(repo, pin)`，
把**该 commit** 的源码提取到独立目录；提取失败才退回克隆，并**显式警告**（不静默）：

```python
if _pin and has_commit(repo, _pin):
    _src = ensure_src(repo, _pin)
ctx["repo_local"] = _src if _src else repo
ctx["repo_source"] = how + ("+pin_src" if _src else "+HEAD(源码非 pin，行号可能错位)")
```

### 修完之后：**libredwg 完全不变** ✅

`libredwg` 的克隆**正好就在 pin**，所以 `ensure_src` 提取的内容与克隆逐字相同：

```
  repo_local: /tmp/opencode/cpg_cache/src/github.com_LibreDWG_libredwg_ff69eeda6658
  repo_source: local+pin_src   commit_used: ff69eeda6658
  worklist: 162 个函数, 自检 src/in_dxf.c:12267 ✅
  surface : field_mapping_complete = True（20 个字段 / 40 个组码）
  分支    : DWG/AC、JSON/{、DXF/None
  features: uaf-llm01 found, site src/in_dxf.c:12284 → 12267  var=pair  branch=DXF
  plan    : ready 1 mut  total=1.0
  verify  : overall=pass，V1–V4 全 pass
  mutator.c sha1: d7913b9e   ← 未动
```

### 用 pin 源码重跑 leptonica / libxml2：**都是 `原语 0`**

| 项目 | R15 时（HEAD 源码） | **R16 重跑（pin 源码）** |
|---|---|---|
| leptonica `42488049` | `原语 2`（守卫 1 挡掉后 0） | **`原语 0`** |
| libxml2 `42533950` | `原语 1`（挡掉后 0） | **`原语 0`** |

**不是"被守卫拦掉"，是这些站点在 pin 上根本不存在** —— 它们是 HEAD/pin 错配的产物。

### 台账更新：3 条作废

`docs/verified_sites.json` 里 leptonica ×2、libxml2 ×1 标了 `invalid: true` + `invalid_reason`，
`verdict` 从 `false` 改成 `uncertain`（因为**没在 pin 上核过**，不能算"核实为假"）。

```
  libredwg   src/in_dxf.c:12284→12267  true       ✅有效
  libredwg   src/in_dxf.c:12839→12842  uncertain  ✅有效
  libredwg   src/encode.c:1271→1272    false      ✅有效
  libredwg   src/encode.c:1308→1313    false      ✅有效
  gpac       src/odf/descriptors.c:1400→1404  true  ✅有效
  leptonica  src/pix1.c:1665→1666      uncertain  ❌作废（错版本）
  leptonica  src/pix4.c:2942→2953      uncertain  ❌作废（错版本）
  libxml2    list.c:307→308            uncertain  ❌作废（错版本）
```

---

## 步骤 4 · 落地表与结论

| 项目 | 格式 | 站点 | **核实** | 落地特征 | plan | generate | verify | A/B | 自己走到 |
|---|---|---|---:|---|---|---|---|---|---|:---:|
| **libredwg `42494732`** | DXF 文本记录 | 2 | ✅ 真（R4/R5/R15 + 617 次实验） | **1**（`uaf-llm01`） | ✅ ready 1/1/0.5/1.0 | ✅ `d7913b9e` | ✅ pass | ✅ 617 vs 0 | ✅ |
| **igraph `42491511`** | **GML 文本记录** | **0** | —（无站点） | 0 | — | — | — | — | ✅ **（R16 修好后）** |
| leptonica `42488049` | PNG/TIFF 二进制 | **0** | —（R14 的核实已作废） | 0 | — | — | — | — | ✅ |
| libxml2 `42533950` | XML 文本 | **0** | —（同上） | 0 | — | — | — | — | ✅ |
| gpac `42518828` | ISOM 二进制 | 1 | ✅ 真（R7） | 1 | ✅ | — | — | — | ❌ 锚点 |

### 明确回答

1. **跨项目这一栏有没有内容？** —— **没有。到 `verify` 且站点核实为真的，仍然只有 libredwg 一个。**
2. **`uaf-llm01` 在几个格式不同的项目上成立？** —— **1 个**（DXF 文本记录）。
3. **卡在哪一层？**

| 卡在哪一层 | 项目 | 原因 |
|---|---|---|
| `worklist`（故障函数不在 d≤2） | ndpi 0/3、flac 0/2、mruby 0/4、assimp 0/3、serenity 0/3、libavc 0/4、leptonica `42484161` | 真的够不到 |
| `worklist`（CPG 缺 harness） | openh264、espeak-ng、harfbuzz、open62541、c-blosc2、fluent-bit、opensc | harness 不在 CPG（同类：`extern "C"` 或非 C 语法） |
| **`features`（原语 0）** | **igraph**、leptonica、libxml2 | **这条 UAF 是跨函数形态，扫描器看不见** |
| `plan`（blocked） | —（本轮没有项目走到这里） | — |
| 全部通过 | libredwg | — |

### 结论

**"第二个落地项目"在当前语料 + 当前工具能力下不存在**——而且现在知道了**三层原因**：

1. **格式层**：文本记录格式的项目少（libredwg DXF、igraph GML、libxml2 XML），其余是二进制；
2. **工具层**：`extern "C"` 在 `.c` 里会让 c2cpg 整个文件丢失（R16 已定位并验证可修）；
3. **扫描器层（决定性）**：**这三个文本格式项目的 UAF 全是跨函数形态，同函数扫描器扫出 0 条原语**。
   igraph 是活生生的例子——`worklist` 通了、格式对、站点 0。

**第 3 条正是 R11/R12 的结论**：跨函数形态在 110 条真实 UAF 里占比 0 是因为扫描器只认一种形态；
但反过来，**真实 UAF 里大量是跨函数形态，而扫描器只认同函数形态**。
libredwg 那个真站点是**少数**同函数形态。

---

## 汇总

### 本轮结论一句话

**`extern "C"` 写在 `.c` 里会让 c2cpg 丢掉整个 harness 文件——修好之后 igraph 的 `worklist` 通了
（闭包 0 → 40），但它的 UAF 是跨函数形态，`features` 扫出 `原语 0`；同时查出一个更严重的问题：
`repo_local` 原来是克隆的 HEAD 而不是 pin，R14/R15 对 leptonica / libxml2 的核实是在错版本上做的。
所以到 `verify` 且站点核实为真的，仍然只有 libredwg 一个。**

### 四步结论

| 步骤 | 结论 |
|---|---|
| **1 · 重筛** | 三条硬条件（d≤2 / harness 在 CPG / 文本记录）同时满足的只有 libredwg + libxml2（后者站点 0）。查明 igraph 的真实阻塞点是 **c2cpg 解析不了 `.c` 里的 `extern "C"`** |
| **1b · (C)** | ✅ **修好之后 igraph `worklist` 通过**（`depth=2` 闭包 0 → **40**，自检过，不加锚点）；但 `features` = **0 站点**（跨函数形态） |
| **1c · 顺带查出** | 🔴 **`repo_local` 是克隆的 HEAD，不是 pin**（3/4 个项目）。R14/R15 对 leptonica/libxml2 的核实**作废**；用 pin 重跑，三个项目都是 `原语 0`。已修，**libredwg 完全不变** |
| **4 · 落地表** | 到 `verify` + 站点核实为真的，**仍然只有 libredwg**（1 个）。`uaf-llm01` 在 **1 个**格式（DXF 文本记录）上成立 |

### `docs/verified_sites.json` 新增/变更

- **作废 3 条**（`invalid: true` + 原因）：leptonica `src/pix1.c:1665`、`src/pix4.c:2942`、libxml2 `list.c:307`
  —— 它们在 R14 核实时读的是 HEAD，不是 pin；`verdict` 从 `false` 改成 `uncertain`。
- **新增 0 条**：本轮没有站点通过人工核实（igraph 0 站点）。
- 有效 **5 条**：libredwg ×4（真 1 / 存疑 1 / 假 2）、gpac ×1（真）。

### `HANDOFF.md` 改了哪些（完整 diff）

```diff
@@ -414,6 +414,57 @@
 
 ---
 
+## 限制 17 · `repo_local` **不是 pin**（R16 已修，但影响过 R14/R15 的核实）
+
+`fetch` 原来把 `ctx["repo_local"]` 设成**克隆的 HEAD**，而 CPG 是**按 pin 预建**的。
+实测 3/4 个项目的克隆不在 pin 上：
+
+| 项目 | pin | 克隆 HEAD | 一致？ |
+|---|---|---|:---:|
+| libredwg | `ff69eeda6658` | `ff69eeda6658` | ✅ |
+| leptonica | `90ec70fd4322` | `5914a4330da2` | ❌ |
+| libxml2 | `d4d1f3f33d6d` | `febeb5c91fff` | ❌ |
+| igraph | `c83b6ecdc3fe` | `22dd6a8ee4c2` | ❌ |
+
+**后果**：扫描器拿 HEAD 的源码去套 pin 的行号。实测同一行**完全不是同一段代码**：
+
+| 项目 | R14 读到的（HEAD） | pin 上同一行 |
+|---|---|---|
+| leptonica `src/pix1.c:1665` | `pixFreeData(pix); pix->data = data;` | `if (!valid) return ERROR_INT("colormap is not valid"…)` |
+| libxml2 `list.c:307` | `xmlListClear(l); xmlFree(l->sentinel);` | `lkNew = (xmlLinkPtr) xmlMalloc(sizeof(xmlLink))` |
+
+**所以 R14/R15 对 leptonica / libxml2 的"逐条读源码核实"是在错版本上做的**，
+台账里那 3 条已标 `invalid`。用 pin 源码重跑后，这两个项目 + igraph 的 **`原语` 都是 0** ——
+那些站点在 pin 上**根本不存在**。
+
+**修法**：`repo_local = ensure_src(repo, pin)`（按 commit 提取到独立目录），失败才退回克隆并**警告**。
+**libredwg 不受影响**（克隆正好在 pin，提取内容逐字相同），站点 / plan / verify / sha1 全不变。
+
+## 限制 18 · `extern "C"` 写在 `.c` 里会让 c2cpg **整个文件丢失**
+
+igraph 的 harness `fuzzing/read_gml_fuzzer.c` 第 27 行是 `extern "C"`。
+c2cpg 按 **C** 解析 `.c`，`extern "C"` 不是合法 C → 整个文件解析失败 → CPG 里只剩 `<global>`：
+
+```
+  igraph CPG dump 里，fuzzing/ 只有：
+    fuzzing/read_gml_fuzzer.c   <global>   L1
+  grep -c "LLVMFuzzerTestOneInput" cpg_dump.tsv → 0
+```
+
+**这就是 R13 记的"CPG 里没有 `LLVMFuzzerTestOneInput`（BFS 根缺失）"的真因**，
+不是"harness 不在仓库"。两个不同 pin 都缺，说明是**系统性解析失败**，不是图过期。
+
+**对照**：libredwg `extern int LLVMFuzzerTestOneInput(...)`（纯 C）✅；
+libxml2 裸 `int LLVMFuzzerTestOneInput(...)` ✅；leptonica `.cc`（走 C++ 前端）✅。
+
+**R16 实测：把这一处 `extern "C"` 换成注释后重建 CPG，igraph 的 `depth=2` 闭包从 0 → 40 个函数，
+`worklist` 自检通过**（`src/io/gml.c:462 ✅ 已被覆盖`），**不需要 `--fault-anchor`**。
+
+**但这不改变"没有第二个落地项目"的结论**：igraph 的 UAF 是**跨函数形态**，
+`features` 扫出 **`原语 0`**（见限制 7）。
+
+---
+
 # 二、当前状态（2026-11-04）
 
 ## 门禁
```

### 下一步建议

| 优先级 | 做什么 | 为什么 |
|---|---|---|
| **P0** | **重跑 R14/R15 的核实流程**（现在 `repo_local` 对了） | 那两轮的"leptonica/libxml2 假阳性"结论是在错版本上做的；虽然现在它们站点为 0，但**方法论**要重走一遍才可信 |
| **P0** | **同函数扫描器覆盖"跨函数形态"** —— 但 R12 已证明它需要别名分析 | igraph 是活证据：`worklist` 通、格式对、**原语 0**。这是唯一挡在"第二个项目"前面的东西 |
| **P0** | 建图前**统一剥掉 harness 里的 `extern "C"`**（或按 `.cpp` 处理） | 限制 18：至少 7 个项目（openh264 / espeak-ng / harfbuzz / open62541 / c-blosc2 / fluent-bit / opensc）可能同样被它挡着，从没验证过 |
| P1 | 给 `fetch` 加一个"CPG 的 commit 与 `repo_local` 的 commit 一致"的断言 | 限制 17 的根因就是没人检查这对一致性 |
| P1 | `docs/verified_sites.json` 每条加 `commit` 字段 | 台账现在只有 `osv_id`，项目换了 pin 就分不清 |

### 本轮刻意不做的

- 分支互斥控制流、修法 B、二进制构造推导、重跑 libredwg 的 generate、换崩溃类型
- **没有降低标准去凑第二个项目**：三条硬条件严格筛，结论是"没有"

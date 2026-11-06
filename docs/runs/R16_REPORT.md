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

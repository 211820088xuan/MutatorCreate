# R12 报告

日期：2026-11-05
本轮目标：让跨函数扫描器能看见 C 类（64/110）里的"经结构体字段"那部分。

> 本文是本轮全部产出。每完成一步追加一节，不覆盖前面内容。

---

## 步骤 1 · 64 条 C 类的子类分布

### 先报一个数据缺口：`facts` **不记录释放表达式**

这是本步最重要的发现，它决定了后面能做什么。

| 事实 | 数字 |
|---|---|
| 121 条 UAF 的 free 站点总数 | 125 |
| 其中 `code` 为 **null** 的 | **116** |
| 有 `code` 的 | **9** |

`facts` 里 free 站点的样子：

```json
{"kind": "free", "line": 1625, "fn": "xmlFreeAttribute", "code": null,
 "origin": "report:freed_by"}
```

**`origin: "report:freed_by"`** —— 它来自 ASan 报告的 "freed by" 栈帧，
只给出**函数名 + 行号**，没有表达式；有 `code` 的那 9 条是后来补的。

**后果**：**"释放的是 `obj->field` 还是 `free(ptr)`"这个问题，
对 116/125 的站点根本无法从 `facts` 判断。**

### 9 条有 `code` 的 free 站点——真实形态

| 样本 | 项目 | 释放表达式 | 形态 |
|---|---|---|---|
| `ARVO-42477951` | opensc | **`free(obj->data)`** | **字段** |
| `ARVO-42477951` | opensc | `free(obj)` | 变量 |
| `ARVO-42483440` | leptonica | **`LEPT_FREE(cmap->array)`** | **字段** |
| `ARVO-42483440` | leptonica | `LEPT_FREE(cmap)` | 变量 |
| `ARVO-42510333` | libxml2 | `xmlFree(cur)` | 变量 |
| `ARVO-42533886` | libredwg | `free (str)` | 变量 |
| `ARVO-42534222` | hdf5 | `H5MM_free(list)` | 变量 |
| `ARVO-42537493` | libxml2 | `xmlCharEncCloseFunc` → `xmlFree(handler)` | 变量 |
| `OSV-2021-371` | c-blosc2 | `free(csize_idx)` | 变量 |

**2/9 是字段释放**（22%）。但**这 2 条都不在 110 条候选里**（`free_cross_function=false`），
所以它们进不了 C 类，也就不能当步骤 2 的正例。

### 64 条的子类分布

按"free 表达式（有就优先）+ `ptr` 名字 + `use` 表达式形态"分类：

| 子类 | 条数 | 依据 |
|---|---:|---|
| **C5 判不出** | **49** | 释放表达式未知（`code: null`），且 `use` 表达式不足以区分 |
| **C1\* 候选（使用端是字段解引用，释放端未知）** | **11** | `use` 里有 `ptr->字段` |
| **C2 全局/常量** | **3** | `ptr` 是全大写（`LOW_COMPLEXITY` / `HB_AAT_LAYOUT_..._CASE` / `CURLOPT_FTP_SSL_CCC`） |
| **C5 假阳性（`ptr` 是类型名）** | **1** | `ptr=uint32_t` |
| **C1 结构体字段（确认）** | **0** | 释放表达式可确认是 `obj->field` 的，在 64 条里**一条都没有** |
| **C3 容器遍历** | 0 | 没有 `next/prev/head/tail` 形态的 |
| **C4 生命周期（不同实例）** | **判不出** | 见下 |

**所以"C 类里最大的一部分是经结构体字段"这个前提，在当前数据上不成立。**
真实情况是：**49/64 根本判不出释放的是什么**，另有 4 条是 `ptr` 提取错误的假阳性。

### C1 的样本清单（步骤 2 的正例池）

**11 条 C1\* 候选**（只有"使用端"是字段解引用，"释放端"未知）：

| osv_id | 项目 | 释放点 | 使用点 | ptr | 使用端字段 |
|---|---|---|---|---|---|
| `ARVO-372547409` | libxml2 | `xmlFreeAttribute:1625` | `xmlValidateOneElement:5992` | `cur` | `cur->prefix` |
| `ARVO-42474969` | open62541 | `deleteMembers_default:196` | `String_clear:136` | `s` | `s->data` |
| `ARVO-42481163` | open62541 | `Variant_decodeJsonUnwrap:2994` | `String_clear:140` | `s` | `s->data` |
| `ARVO-42484314` | ndpi | `LLVMFuzzerTestOneInput:84` | `ndpi_http_check_content:144` | `packet` | `packet->content_disposition_line` |
| `ARVO-42484479` | ndpi | 同上 | 同上 | `packet` | 同上 |
| `ARVO-42485194` | ndpi | `LLVMFuzzerTestOneInput:83` | `check_content_type_and_cha:342` | `flow` | `flow->protos` |
| `ARVO-42487785` | libxml2 | `xmlTextReaderFreeNode:481` | `xmlStaticCopyNode:4197` | `node` | `node->type` |
| `ARVO-42520826` | open62541 | `processDelayedCallback:180` | `UA_Session_detachFrom:87` | `session` | `session->header` |
| `ARVO-42530320` | libredwg | `dwg_add_object:4746` | `dxf_tables_read:11738` | `ctrl` | `ctrl->tio.object` |
| `ARVO-42530963` | opensc | `sc_file_free:643` | `authentic_emu_update:876` | `left` | `left->data` |
| `OSV-2021-765` | espeak-ng | `DeleteTranslator:218` | `LookupDict2:2622` | `tr` | `tr->transpose_min` |

**这 11 条里有 3 个项目我有源码**（libredwg / espeak-ng / leptonica 不含），
其中 **espeak-ng 这条我已经读过**：

```c
void DeleteTranslator(Translator *tr)   // src/libespeak-ng/translate.c:212
{
    if (!tr) return;
    if (tr->data_dictlist != NULL) free(tr->data_dictlist);
    free(tr);                            // ← 第 218 行，释放的是**变量**，不是字段
}
```

使用端在 `LookupDict2:2622` 读 `tr->transpose_min`。

→ **它是"释放局部/形参指针 → 另一个函数解引用它"，不是"释放字段"。**
`tr` 怎么到达 `LookupDict2` 的？需要读调用链——**这正是难点 1/2 要解决的问题**。

### C1 与 C4 的比例

按你要求的"把 C4 单列出来，看扩字段形态会带进多少假阳性"：

| | 条数 | 说明 |
|---|---:|---|
| **C1（确认的字段释放）** | **0** | 64 条里没有 |
| **C1\* （使用端是字段，释放端未知）** | 11 | 唯一的正例池，但**不保证是字段释放** |
| **C4（不同实例）** | **判不出** | R4 查证的那条反例（`dwg_free` vs `decode_R13_R2000` 的 `dwg->object`）**不在 110 条里**——110 里 libredwg 只有 5 条，全不是它 |
| C5 判不出 | 49 | 释放表达式未知 |
| 假阳性（ptr 提取错） | 4 | 3 全大写常量 + 1 类型名 |

**结论：C1 与 C4 的比例现在算不出来。** 不是数据少，是**判据缺字段**。

### 另一个发现：`freed_ptr` 提取有 4 条明显错误

| 样本 | `ptr` | 为什么错 |
|---|---|---|
| `ARVO-42479702` | `LOW_COMPLEXITY` | 全大写**枚举常量**，不是指针 |
| `ARVO-42502063` | `HB_AAT_LAYOUT_FEATURE_SELECTOR_DEFAULT_UPPER_CASE` | 同上（枚举值） |
| `ARVO-42508326` | `CURLOPT_FTP_SSL_CCC` | 同上（宏常量） |
| `ARVO-42473818` | `uint32_t` | **类型名** |

这 4 条进不了任何形态的扫描器，而且会让"110 条"这个数字偏大。

### 回答你隐含的那个问题：能不能直接按 64 条扩字段形态？

**不能。** 三个理由，都有数据：

1. **释放表达式未知（116/125）**——不知道释放的是 `obj->field` 还是 `free(ptr)`，
   扩出来的扫描器**没有东西可以验证**。
2. **确认的字段释放案例 0 条**（64 条里），而仅有的 2 条（opensc / leptonica）**不在候选里**。
3. **`freed_ptr` 有 4/64 是提取错误**——"110"这个分母本身掺了假阳性。

**所以本步的结论是：要先补 `facts` 的释放表达式，再扩字段形态。**

### 补 `facts` 的代价（供你判断）

`s2_2_facts.py` 已经有 free 站点的 `fn` + `line`，只需要**按行号把源码那一行读出来**填进 `code`。
它需要每个项目的源码——R11 只克隆了 3 个项目，110 条跨 34 个项目。
**按项目补一次即可，不需要重跑 stage2 的 Joern 部分**（那是分钟级/项目）。

**已经查清了（就在写本报告时顺手查的）**：

`s2_2_facts.py:861-862`：

```python
sites.append({"kind": "free", "line": rep.get("free_line"), "fn": rep.get("free_fn"),
              "code": None, "origin": "report:freed_by"})
```

**`code: None` 是硬编码的**——不是"源码取不到"，是**从来没取过**。
free 站点的信息只来自 ASan 报告的 "freed by" 栈（函数名 + 行号），
`s2_2_facts` 根本没去读那一行源码。

→ **所以补它是纯增量工作**：`free_fn` + `free_line` 都在，只要按行号读源码那一行。
不需要重跑 Joern，也不需要重跑整个 stage2；只要源码在本地。

---

### ⏸ 停止点：等用户确认（步骤 1 出口）

| 你要的 | 结果 |
|---|---|
| 64 条的子类分布表 | ✅ 已给（49 判不出 / 11 C1\* / 3 C2 / 1 假阳性 / 0 C1 确认） |
| C1 的样本清单 | ✅ 11 条 C1\*（osv / 项目 / 释放点 / 使用点 / 字段名） |
| C1 与 C4 的比例 | ❌ **判不出**，因为 `facts` 缺释放表达式；R4 那条反例不在候选里 |
| 提前告知 | **"C 类最大一部分是经结构体字段"这个前提在当前数据上不成立** |

**我的建议**：先花一步把 `facts` 的释放表达式补上（并按项目拉源码），
再回来扩字段形态。否则扩出来的东西无法验证正例、也无法确认那几个已知假阳性。

**请确认：是（A）先补 `facts` 的释放表达式，还是（B）就用这 11 条 C1\* 直接扩？**

---

## 步骤 1b · 补 `facts` 的释放表达式 + 重算分布（用户选 A）

### 做了什么

**① 新增 `tools/backfill_free_code.py`**

`s2_2_facts.py:861` 把 free 站点的 `code` 硬编码成 `None`，只留了 `fn` + `line`。
工具做的事：

1. 重新解析 `report.log` 的 "freed by" 段，拿到 `(fn, 绝对路径, 行号)`
   （`s2_2_facts` 当时拿过但没存）；
2. 按 `pin_commit` 用 **raw HTTP 拉那一个文件**（不克隆整仓）；
3. 读那一行，写进 `facts.sites[kind=free].code`，并补 `file`。

**过程中修的三处**（都是实测踩到的）：
- **路径归一化**：报告里有 `/work/build/../../src/perfetto/src/x.cc` 这种，要先解 `..`；
- **raw 协议不止一种**：GitHub（`raw.githubusercontent.com`）、GitLab
  （`/-/raw/<sha>/`）、`googlesource.com`（`+/<sha>/<path>?format=TEXT`，base64）；
- **帧选择**：`facts.free_fn` 常是**完整签名**（`WelsCommon::WelsFree(void*, char const*)`），
  而报告里是短名；很多释放包装被内联后栈上只剩调用者。改成：
  跳过 `compiler-rt` / `llvm-project` 的拦截器帧 → 按短名匹配 → 匹配不上回退到第一个非拦截器帧。

**结果**：

```
  UAF facts: 121
  ✅ 补上释放表达式: 100          （原来只有 9 条有）
  ✅ entity.name 判为常量/类型名（已清空）: 4
  ⚠️ 找不到 report.log: 2
  ⚠️ freed-by 段里没有对应帧: 3
  ⚠️ 拉不到源码: 11             （6 条 libvips 记录里没有 pin；3 条路径 404；2 条其他）
  已写回
```

**补全后：125 个 free 站点里 109 个有表达式**（原来 9 个）。

**② 修 `freed_ptr` 的 4 条假阳性**

`freed_ptr` = `facts.entity.name`。判据：全大写常量 / 类型名 → 不是指针。
清空并标 `entity._rejected_name`：

| 样本 | 被清空的值 |
|---|---|
| `ARVO-42479702` | `LOW_COMPLEXITY` |
| `ARVO-42508326` | `CURLOPT_FTP_SSL_CCC` |
| `ARVO-42473818` | `uint32_t` |
| `ARVO-42502063` | `HB_AAT_LAYOUT_FEATURE_SELECTOR_DEFAULT_UPPER_CASE` |

### 重算：110 条的"调用图方向 × 释放表达式形态"交叉表

| 方向 \ 形态 | **F1 结构体字段** | F3 容器元素 | **F4 裸指针（局部/形参）** | F5 未知 | **F6 包装调用** | 合计 |
|---|---:|---:|---:|---:|---:|---:|
| A 同函数释放 | 0 | 0 | 10 | 1 | 1 | 12 |
| B 方向反 | 0 | 0 | 3 | 0 | 2 | 5 |
| **C 互不可达** | **7** | **1** | **33** | **5** | **18** | **64** |
| D 无调用边 | 0 | 1 | 10 | 9 | 9 | 29 |
| **合计** | **7** | **2** | **56** | **15** | **30** | **110** |

形态说明：
- **F1 结构体字段**：释放提参里有 `->`（如 `PS_DEC_ALIGNED_FREE(ps_dec, ps_dec->pu1_pic_buf_base)`
  的第二个参数、`UA_free(dst->data)`、`DICT_FREE(cur->name)`）；
- **F4 裸指针**：`free(packet_checked)` / `xmlFree(attr)` / `pix_free(data)`；
- **F6 包装调用**：`freed by` 那一帧本身是**包装函数调用**（`DecreasePicBuff(...)` /
  `deleteMembersJumpTable[fi](...)`），真正的 `free` 在包装**里面**，所以不知道释放了什么；
- **F5 未知**：没能补上表达式（16 个站点）。

### **这推翻了"C 类主体是经结构体字段"这个前提**

| 你原来的假设 | 数据 |
|---|---|
| C 类 64 条里主体是"经结构体字段" | **F1 只有 7 条（11%）** |
| — | **F4 裸指针 33 条（52%）** |
| — | **F6 包装调用 18 条（28%）** |
| — | F5 未知 5 条、F3 容器 1 条 |

放到 110 条上看更清楚：**F1 = 7/110 = 6%**，而 **F4 + F6 = 86/110 = 78%**。

**而且这 7 条 F1 里 5 条是同一个项目同一个字段**（libavc 的
`ps_dec->pu1_pic_buf_base`，只出现在两个使用函数 `ih264_inter_pred_luma_*` 里）。
**去重后实际上只有 3 个不同的"字段形态"样本**（libavc / open62541 ×2 / libxml2）。

### 你预判对了

> 补上 code 之后 C 类 64 条会重新拆开，可能主体是别的形态
> （比如"释放局部指针后经调用链传递"，espeak-ng 那条就是）。

**数据正是这样**：F4 裸指针 33 条是 C 类的主体，而 espeak-ng 的
`DeleteTranslator` → `free(tr)` 就在这一类里。

### C1 的样本清单（如果仍要扩字段形态）

**7 条，去重后 3 个不同形态**：

| 样本 | 项目 | 释放表达式 | 使用点 |
|---|---|---|---|
| `ARVO-42479533` / `ARVO-42523611` / `OSV-2020-370` / `OSV-2023-342` | libavc | `PS_DEC_ALIGNED_FREE(ps_dec, ps_dec->pu1_pic_buf_base)` | `ih264_inter_pred_luma_horz/vert` |
| `ARVO-42481163` | open62541 | `UA_free(dst->data)` | `String_clear:140` |
| `ARVO-42486724` | open62541 | `config->nodestore.clear(config->nodestore.context)` | `UA_NodeMap_delete:447` |
| `ARVO-42484562` | libxml2 | `DICT_FREE(cur->name)` | `__xmlRaiseError:501` |

**只有 3–4 个正例可用**——比 R11 预计的"11 条"又少了一半。

### 失败与存疑

1. **21/121 仍没补上**：6 条 libvips 记录里**根本没有 pin**（无法按 commit 定位版本）；
   3 条路径 404（`pregenerated`/`build/` 目录里的生成文件）；2 条找不到 `report.log`；
   3 条 `freed by` 段里没有可用的项目帧。
2. **F6 的 30 条是"不知道释放了什么"**。要判它们的形态，得**再往里走一层**——
   在包装函数的函数体里找 `free(<包装形参>或它的字段)`。这是**另一个**待办，
   而且它比"扩字段"覆盖的面更大（30 vs 7）。
3. **`s2_2_facts.py:861` 本身还没改**——工具只补了历史产物。要让**今后**的 stage2
   产出带上表达式，得给它接一个源码根。**本轮没做**（它会牵动 stage2 的调用方式）。
4. **只有 7 条 F1、去重 3 个形态**——这不足以验证一个"字段形态扫描器"。
   扩出来的东西**大概率一条正例都过不了**，和 R11 的跨函数形态是同一个处境。

### ⏸ 停止点：等确认（形态选哪个）

按数据，扩哪个形态的价值排序是：

| 选项 | 覆盖 | 正例池 | 难点 |
|---|---:|---:|---|
| **(1) F6 包装调用** | **30/110（27%）** | 需要先"进包装内部找 free"，之后才知道形态 | 要解析包装函数体 |
| **(2) F4 裸指针 + 调用链传递** | **56/110（51%）** | espeak-ng 那条就是 | 要证明"同一实例 + 先后顺序"，就是 R12 难点 1/2 |
| **(3) F1 结构体字段**（原计划） | **7/110（6%）** | **去重后只有 3 个形态** | 同难点 1/2 |

**我的建议：先做 (1)。** 理由：
- 它**不是**扫新形态，而是**把已有信息补全**——F6 的 30 条里有 18 条在 C 类，
  补完之后**其中一部分会自动落进 F1/F4**，那时再扩形态才有足够正例；
- 它比 (3) 覆盖的面大 4 倍，且**不需要**"同一实例"证明（因为释放点就在包装里，
  实例就是包装的实参）。

**请选：(1) F6 包装 / (2) F4 裸指针+调用链 / (3) 仍按原计划扩 F1 字段。**

---

## 步骤 2 · 「包装调用」这个类别**不存在**——它拆成了 realloc / delete / 函数指针

### 按你的要求先看能不能复用 `wrapper_frees_param`

读了它（`s5_4_analyze.py`）：判据是"进被调函数体找 `free(<形参>)`"，
**但只用第一个形参，且返回 bool**，签名里的 `var` 参数其实**没被用到**。
要让 F6 用，需要"第几个形参被释放 + 那行表达式"。

**但在动手之前，我先把 24 条 F6 逐条看了**——结果发现**它们不是包装调用**。

### 24 条 F6 的真实成分

| 真实形态 | 条数 | 例子 |
|---|---:|---|
| **`realloc(...)`（第一实参就是被释放的旧块）** | 8 | `p = realloc(p, size ? size : 1)` / `dwg->object = realloc(...)` |
| **realloc 包装**（`spng__realloc` / `xmlRealloc`） | 5 | `newbuf = xmlRealloc(buf->content, size)` |
| **C++ `delete`** | 3 | `delete mXmlParser` / `delete deleteMe` / `delete afflst` |
| **间接 / 函数指针调用** | 7 | `dc->callback(server, dc->data)` / `deleteMembersJumpTable[fi](...)` / `(Curl_cfree)(mem)` / `igraph_i_finally_stack[p].func(...)` |
| 取错行 | 1 | `load_config(apath, key)`（那行不是 free） |

**没有一条是"进包装函数体找 free(<形参>)"那种包装。**
`wrapper_frees_param` 在这里**用不上**——它的前提是"被调函数是**有名字的**包装"，
而这 7 条间接调用**没有可解析的被调函数名**。

### 顺带修的一个解析 bug（影响很大）

`tools/backfill_free_code.py::parse_freed_by` 用 `(\S+)` 抓函数名，
而报告里的函数名是**完整签名、含空格**（`WelsDec::DecreasePicBuff(WelsDec::TagWelsDecoderContext*, ...)`），
于是 `#1` 帧被**整帧丢掉**，只剩 `#2`。

**后果**：把"包装内部释放"误判成"包装调用"——**这一步的 24 条 F6 里有相当一部分是它造成的**。

修法：`in\s+(.+?)\s+(/[^\s:]+):(\d+)`（非贪婪 + 路径必须是最后一个 `/…:行号`）。
修完后同一批样本的释放表达式变了，例如：

| 样本 | 修前（错） | 修后（对） |
|---|---|---|
| `ARVO-42473818` | `iErr = DecreasePicBuff (pCtx, …)` | `FreePicture (pPicOldBuf->ppPic[iPicIdx], pMa);` |
| `ARVO-42474468` | `…` | **`free (* (((void**) pPointer) - 1));`** |

### 最终分布（110 条）

| 形态 | 条数 | 占比 | 说明 |
|---|---:|---:|---|
| **F4 裸指针（局部/形参）** | **60** | **55%** | `free(packet_checked)` / `xmlFree(attr)` / `pix_free(data)` |
| F5 未知 | 15 | 14% | 补不上表达式 |
| **F7 realloc** | **12** | 11% | 裸指针 6 / 字段 6 |
| **F6 间接/函数指针调用** | **7** | **6%** | `dc->callback(...)` / `deleteMembersJumpTable[fi](...)` |
| **F1 结构体字段** | **6** | **5%** | 见下 |
| F9 判不出 | 4 | 4% | 那一行不是 free（行号错位） |
| F3 容器元素 | 3 | 3% | `free(x->arr[i])` |
| F8 C++ delete | 3 | 3% | — |

**C 类 64 条的分布**：F4 **41** / F1 6 / F6 6 / F5 5 / F7（裸 4 + 字段 2）/ F3 2 / F8 2 / F9 1。

### F1（结构体字段）：6 条，**去重后只有 4 个不同字段**

| 样本 | 项目 | 释放表达式 |
|---|---|---|
| `ARVO-42479533` / `OSV-2020-370` / `OSV-2023-342` | libavc | `PS_DEC_ALIGNED_FREE(ps_dec, ps_dec->pu1_pic_buf_base)` |
| `ARVO-42481163` | open62541 | `UA_free(dst->data)` |
| `ARVO-42484562` | libxml2 | `DICT_FREE(cur->name)` |
| `ARVO-42486724` | open62541 | `config->nodestore.clear(config->nodestore.context)` |

**去重后**：`config->nodestore.context` / `cur->name` / `dst->data` / `ps_dec->pu1_pic_buf_base`
→ **4 个**。你要求做的去重已做，**正例池不是"6 条"，是 4 个不同形态**。

### ⏸ 停止点：选 (1) 的前提被数据推翻了

| 你选的 | 数据 |
|---|---|
| **(1) 包装调用**（预期 30/110 = 27%） | **实际 7/110 = 6%**，而且**全是函数指针/间接调用**——`wrapper_frees_param` 要求被调函数**有名字**，这 7 条没有 |
| (2) F4 裸指针 + 调用链 | **60/110 = 55%**，是真正的主体 |
| (3) F1 结构体字段 | 6/110 = 5%，去重 **4 个** |

**所以 (1) 做不了**——不是难，是**没有可做的对象**：
`wrapper_frees_param` 复用的前提（有名字的包装）在这 7 条里不成立。

**建议改做 (2)**：F4 占 55%，而且 `facts` 现在**已经能告诉我们**释放的是哪个变量
（`free(packet_checked)` 里的 `packet_checked`），剩下的就是 R12 文档里那两个难点：
"同一实例" 和 "A 先于 B"。**正例池也最大**（C 类里 41 条）。

**请确认改做 (2)，还是仍要我在 7 条间接调用上做（那需要另加"函数指针表解析"，不在 `wrapper_frees_param` 的能力内）。**

---

## 步骤 2 前置 · F4 抽验（用户要求）

### 抽了 10 条，覆盖 10 个不同项目

| # | 样本 | 项目 | 我们提取的释放表达式 | 真的是 `free(局部/形参)`？ | 旧 `(\S+)` bug 影响过？ | `freed_ptr` 对不对？ |
|---|---|---|---|---|---|---|
| 1 | `ARVO-372547409` | libxml2 | `xmlFree(attr);` @ `valid.c:1625` | ✅ | ⚠️ 旧正则 11 帧 / 新 14 帧（丢 3） | ❌ `cur` ≠ `attr` |
| 2 | `ARVO-42473818` | openh264 | `FreePicture (pPicOldBuf->ppPic[iPicIdx], pMa);` @ `decoder.cpp:234` | ❌ **是包装调用** | ⚠️ 丢 5 帧 | —（已清空） |
| 3 | `ARVO-42484161` | leptonica | `pix_free(data);` @ `pix1.c:634` | ✅ | 无 | ❌ `val` ≠ `data` |
| 4 | `ARVO-42484314` | ndpi | `free(packet_checked);` @ `fuzz_ndpi_reader.c:84` | ✅ | ⚠️ 丢 3 帧 | ❌ `packet` ≠ `packet_checked` |
| 5 | `ARVO-42491876` | c-blosc2 | `free(ptr);` @ `zstd_common.c:81` | ✅ | ⚠️ 丢 3 帧 | ❌ `cMem` ≠ `ptr` |
| 6 | `ARVO-42494732` | libredwg | `free (pair);` @ `in_dxf.c:515` | ✅ | ⚠️ 丢 3 帧 | ✅ `pair` |
| 7 | `ARVO-42500437` | espeak-ng | `free(tr);` @ `translate.c:284` | ✅ | ⚠️ 丢 3 帧 | ❌ `n` ≠ `tr` |
| 8 | `ARVO-42502063` | harfbuzz | `return free (ptr);` @ `failing-alloc.c:56` | ✅ 语法对，**但那是 fuzzer 的 failing allocator**，不是项目 bug | ⚠️ 丢 6 帧 | ❌ |
| 9 | `ARVO-42511322` | mruby | `return realloc(p, size);` @ `state.c:69` | ❌ **是 realloc** | ⚠️ 丢 1 帧 | ❌ |
| 10 | `ARVO-42518828` | gpac | `FREE(ptr);` @ `utils/alloc.c:165` | ✅ 但那是 **`gf_free` 的包装体**，真正的调用点是 `gf_free(ar)` | 无 | —（已清空） |

### 三个结论

**① 释放表达式：8/10 正确 —— 过线。**

2 条不对，都是**分类噪声**不是数据错：
- `openh264` 的 `FreePicture(...)` 是**包装调用**（应归 F6/F1，我的分类把它算成了 F4）；
- `mruby` 的 `return realloc(...)` 是 **realloc**（应归 F7，同上）。

**② 旧 `(\S+)` bug 在 8/10 上都发生过 —— 确认它是普遍问题，不只是 F6 的幻觉。**

帧数差 1–6 帧。修完之后，同一批样本的表达式才变准（例如 `ARVO-42474468`
修前是 `…`，修后是 `free (* (((void**) pPointer) - 1));`）。
**所以 R11/R12 早期那批"F6 包装调用 30 条"确实主要是这个 bug 造成的。**

**③ `freed_ptr` 基本是错的 —— 12/79 = 15%。**

这是**新发现**，而且是**字段语义错误**，不是解析噪声：

```
  freed_ptr 等于释放实参里那个变量名的: 12 / 79 = 15%
```

| 样本 | 释放表达式 | 实参变量 | `freed_ptr` |
|---|---|---|---|
| `ARVO-42500437` | `free(tr);` | `tr` | `n` |
| `ARVO-42488143` | `free(ptr);` | `ptr` | `head` |
| `ARVO-42486565` | `xmlFree(cur);` | `cur` | `buf` |
| `ARVO-42491876` | `free(ptr);` | `ptr` | `cMem` |
| `ARVO-42530963` | `free(file);` | `file` | `left` |

**原因**：`freed_ptr` = `facts.entity.name`（`s2_3_interpretation.py:158,203`），
`entity` 是**崩溃点的对象**，不是**被释放的变量**。**名字与语义不符。**

**影响范围**：
- **不阻塞步骤 2**——跨函数扫描器是从源码扫的，不读 `freed_ptr`；
- 但**任何把 `freed_ptr` 当"被释放指针"用的分析都是错的**，包括
  `interpretation.key_facts` 和 agent prompt 里引用它的地方。

**这一条建议单独修**（把 `freed_ptr` 改名成 `crash_entity`，或按释放表达式重算），
它是**同 R12 补 `code` 一样的"字段从来没被正确填充"**问题。

### F4 的真实条数

60 条里抽验出 4 条不是 F4（2 条包装、1 条 realloc、1 条是 fuzzer 工具文件）：

| 类别 | 条数 |
|---|---:|
| F4 计数（分类器给的） | 60 |
| 抽验发现应剔除 | ~4 |
| **F4 实际约** | **~56（93%）** |

**没有缩水一半。** 抽验通过（按你给的"8/10 以上"标准）。

### ⏸ 停止点：等确认

两件事需要你定：

1. **`freed_ptr` 错了 85%**（12/79），要不要先修它？
   - 它**不阻塞**步骤 2（扫描器不读它）；
   - 但它是"字段名与语义不符"，会污染任何用它做输入的分析。
2. **F4 只有 56 条（55%→51%），且它们分布在 23 个项目、每个项目 1–11 条。**
   要跑扫描器，需要 **23 个项目的源码**（现在只有 3 个 + R11 克隆的 3 个）。
   **是逐项目拉源码（按 F4 条数降序），还是先只用已有源码的 6 个项目试？**

**请确认：(A) 先修 `freed_ptr` 再扩 F4；(B) `freed_ptr` 先记账、直接扩 F4。**

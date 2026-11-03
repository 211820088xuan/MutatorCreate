# R4 · PHASE B 报告 —— 第二个项目（B1/B2 筛选，出表即停）

日期：2026-11-03
状态：**按指令停在 B2 出口，未进入 B3（搭环境）/ B4（跑流程）/ B5（A/B）。**

---

## B0 介入记录

**本轮 Phase B 没有改动任何代码。** 详见仓库根 `INTERVENTIONS.md`。
B1/B2 全部是只读：读 `artifacts/reproduced_crashes.jsonl`、`outputs/stage3/uaf/final.json`、
`artifacts/facts/*/facts.json`、`reproduce_crash/artifacts/**/testcase`，加 2 次
`raw.githubusercontent.com` 取源码。

---

## B1 零成本预筛（35 个项目 × 5 个 pattern）

### 先说一个必须先讲清楚的结构性事实

`outputs/stage3/uaf/final.json` 里 5 个 pattern 的 `trigger_condition.where_free` / `where_use`
**不是"机制描述"，是各自样本集的散文摘要**——里面点名的是**构成该 pattern 的那批崩溃的函数**。

原文（节选）：

| pattern | support | `where_free` 原文（节选） |
|---|---:|---|
| 缓冲释放后旧指针 | 34 | `xrealloc、read_data、DecreasePicBuff/WelsFree、free_pool、ZSTD_free、yyrealloc、safe_realloc/json_fixed_string/xmlFuzzRealloc、ih264d_free_dynamic_bufs、blosc2_schunk_free/free 等` |
| 清理析构后悬垂访问 | 31 | `r_core_task_decref、sdb_free、deleteMembers_default、xmlTextReaderFreeProp/…、fpixDestroy/pixFree、DeleteTranslator、sc_file_free/…、finishFileMgr 等` |
| 容器节点销毁后遍历 | 26 | `xmlTextReaderFreeNode/FreeNodeList、igraph_i_gml_destroy_attrs/…、cil_destroy_*、_FreeModule/delete_filter、hb_free_impl、processDelayedCallbacks、mrb_default_allocf、xmlFreeID、xmlFreeNs、AK Vector clear/JS delete 等` |
| **同函数释放后访问** | **5** | `ResolveDescriptorTrack、pixcmapDestroy、flb_parser_decoder_list_destroy 内 flb_free、dxf_objects_read 内 dxf_free_pair、H5FL__blk_gc_list` |
| 跨函数陈旧对象访问 | 11 | `xmlFreeAttribute、LLVMFuzzerTestOneInput、xmlFreeNode/deleteMembers_noInit、sc_file_free/sc_file_clear_acl_entries` |

`同函数释放后访问` 最清楚：**support = 5，`where_free` 就是那 5 个样本的函数名**，
`where_use` 还带行号（`ResolveDescriptorTrack:485`、`dxf_objects_read:12267`、…）。

**推论（这是本轮最重要的发现）**：
Phase 2 加的"P3 预筛"（`where_free`/`where_use` 的标识符 ∩ 项目可达函数）在这个形态下
**不是"适用性判定"，而是"这个项目在不在该 pattern 的训练集里"的成员测试**。

验证：5 个 pattern 的样本集合起来覆盖 **33 / 35** 个 UAF 项目。

| 项目 | UAF | 在哪些 pattern 的样本集 | 项目 | UAF | 在哪些 pattern 的样本集 |
|---|---:|---|---|---:|---|
| libxml2 | 17 | P1,P2,P3,P5 | radare2 | 3 | P2,P5 |
| open62541 | 9 | P1,P2,P3,P5 | serenity | 3 | P3 |
| c-blosc2 | 7 | P1 | flac | 2 | P1 |
| libredwg | 6 | P1,P2,P4 | hdf5 | 2 | P4 |
| libvips | 6 | P1,P2 | lcms | 2 | P2 |
| openh264 | 5 | P1 | libarchive | 2 | P1,P3 |
| espeak-ng | 4 | P2 | openvswitch | 2 | P1 |
| harfbuzz | 4 | P3 | perfetto | 2 | P2,P4 |
| igraph | 4 | P1,P3 | selinux | 2 | P3 |
| leptonica | 4 | P2,P4 | wireshark | 2 | P1,P5 |
| libavc | 4 | P1 | **curl** | 1 | **—** |
| mruby | 4 | P1,P3 | **gpac** | 1 | **—** |
| assimp | 3 | P2 | kimageformats | 1 | P2 |
| fluent-bit | 3 | P2,P4 | libjxl | 1 | P3 |
| hunspell | 3 | P2 | mupdf | 1 | P2 |
| libspng | 3 | P1 | net-snmp | 1 | P5 |
| ndpi | 3 | P5 | wasm3 | 1 | P3 |
| opensc | 3 | P2,P5 | | | |

（P1 缓冲释放后旧指针 / P2 清理析构后悬垂访问 / P3 容器节点销毁后遍历 / P4 同函数释放后访问 / P5 跨函数陈旧对象访问）

**只有 `curl` 和 `gpac` 不在任何 pattern 的样本集里。** 也就是说：

- 对 33 个项目，预筛**一定会通过**——但这只证明"它曾经贡献过样本"，**不证明迁移**；
- 对 `curl` / `gpac`（唯一真正的 holdout），预筛**一定会判 not_applicable**，流程当场停住。

**→ 现阶段"原封不动跑第二个项目"要么是循环验证，要么被判无落点。**
把预筛放宽以让 holdout 通过，属于 B0 的**禁止类**（"改判据让特征落地"），所以本轮就地停止。

---

## B2 前置条件表

| 项目 | UAF | pattern | 有 CPG | 有 testcase | 输入格式（testcase 首 4KB 可打印率） | 目标 repo@pin | 谓词方向 |
|---|---:|---|---:|---:|---|---|---|
| libxml2 | 17 | P1,P2,P3,P5 | 17/17 | 17/17 | 二进制 61% | `gitlab.gnome.org/GNOME/libxml2@d4d1f3f3` | 需逐个 fetch |
| open62541 | 9 | P1,P2,P3,P5 | 9/9 | 9/9 | 二进制 25% | `open62541/open62541@4e38d391` | 需 fetch |
| c-blosc2 | 7 | P1 | 7/7 | 2/7 | 二进制 14% | `Blosc/c-blosc2@0739de6c` | 需 fetch |
| libredwg | 6 | P1,P2,P4 | 4/6 | 4/6 | 文本 89% | `LibreDWG/libredwg@ff69eeda` | **否定**（`!is_dwg_object(name)`，`in_dxf.c:12272`） |
| libvips | 6 | P1,P2 | **0/6** | 6/6 | 二进制 62% | `libvips/libvips@`（**pin 为空**） | 需 fetch |
| openh264 | 5 | P1 | 5/5 | 5/5 | 二进制 37% | `cisco/openh264@be82ccf4` | 需 fetch |
| espeak-ng | 4 | P2 | 4/4 | 1/4 | 二进制 30% | `espeak-ng/espeak-ng@0a713d52` | 需 fetch |
| harfbuzz | 4 | P3 | 4/4 | 4/4 | 二进制 7% | `harfbuzz/harfbuzz@2bd911b8` | 需 fetch |
| **igraph** | 4 | P1,P3 | 4/4 | 4/4 | **文本 99%** | `igraph/igraph@c83b6ecd` | 需 fetch |
| leptonica | 4 | P2,P4 | 4/4 | 4/4 | 二进制 54% | `DanBloomberg/leptonica@695ff35c` | 需 fetch |
| libavc | 4 | P1 | 2/4 | 2/4 | 二进制 31% | `android.googlesource.com/…/libavc@ea14d495` | 需 fetch |
| **mruby** | 4 | P1,P3 | 4/4 | 4/4 | **文本 100%** | `mruby/mruby@23ce122f` | 需 fetch |
| assimp | 3 | P2 | 3/3 | 3/3 | 文本 100% | `assimp/assimp@91cb2947` | 需 fetch |
| fluent-bit | 3 | P2,P4 | 3/3 | 3/3 | 文本 89% | `fluent/fluent-bit@1b262ceb` | 需 fetch |
| hunspell | 3 | P2 | 3/3 | **0/3** | 无 | `hunspell/hunspell@07564b7d` | 需 fetch |
| libspng | 3 | P1 | 3/3 | 3/3 | 文本 92% | `gitlab.com/randy408/libspng@9fcecef4` | 需 fetch |
| ndpi | 3 | P5 | 3/3 | 3/3 | 二进制 13% | `ntop/nDPI@b6eef17e` | 需 fetch |
| opensc | 3 | P2,P5 | 3/3 | 3/3 | 二进制 77% | `OpenSC/OpenSC@3b632e64` | 需 fetch |
| radare2 | 3 | P2,P5 | 3/3 | 3/3 | **空 testcase** | `radare/radare2@8f03b2a4` | 需 fetch |
| serenity | 3 | P3 | 3/3 | 3/3 | 文本 88% | `SerenityOS/serenity@81eab1a9` | 需 fetch |
| flac | 2 | P1 | 2/2 | 2/2 | 二进制 31% | `xiph/flac@383512d5` | 需 fetch |
| hdf5 | 2 | P4 | 1/2 | 1/2 | 二进制 9% | `HDFGroup/hdf5@966454aa` | 需 fetch |
| lcms | 2 | P2 | 2/2 | 2/2 | 文本 87% | `mm2/Little-CMS@a9796f61` | 需 fetch |
| libarchive | 2 | P1,P3 | 2/2 | 2/2 | 二进制 56% | `libarchive/libarchive@7ef089ec` | 需 fetch |
| openvswitch | 2 | P1 | 2/2 | 2/2 | 文本 91% | `openvswitch/ovs@bc9bbc4e` | 需 fetch |
| perfetto | 2 | P2,P4 | 2/2 | 2/2 | 二进制 14% | `android.googlesource.com/…/perfetto@8a1fbea3` | 需 fetch |
| selinux | 2 | P3 | 2/2 | 2/2 | 文本 97% | `SELinuxProject/selinux@0451adeb` | 需 fetch |
| wireshark | 2 | P1,P5 | 2/2 | 2/2 | 二进制 74% | `wireshark/wireshark@828ff6dd` | 需 fetch |
| **curl**（holdout） | 1 | — | 1/1 | 1/1 | 二进制 61% | `curl/curl@5c55fe6d` | **生命周期**（见下） |
| **gpac**（holdout） | 1 | — | 1/1 | 1/1 | 二进制 71% | `gpac/gpac@319d4479` | **否定**（`type ∉ 集合`，见下） |
| kimageformats | 1 | P2 | 1/1 | 1/1 | 文本 100% | `invent.kde.org/…/kimageformats@a30f043e` | 需 fetch |
| libjxl | 1 | P3 | 1/1 | 1/1 | 二进制 70% | `libjxl/libjxl@dbf8653b` | 需 fetch |
| mupdf | 1 | P2 | 1/1 | 1/1 | 文本 99% | `git.ghostscript.com/mupdf@80b59185` | 需 fetch |
| net-snmp | 1 | P5 | 1/1 | 1/1 | 二进制 67% | `net-snmp/net-snmp@f720ed11` | 需 fetch |
| wasm3 | 1 | P3 | 1/1 | 1/1 | 二进制 32% | `wasm3/wasm3@4f0b7696` | 需 fetch |

**harness 行数**列未填：`report_dir` 里只有 `testcase` / `report.log` / `INFO.txt` / `replay.sh`，
harness 源码要从项目仓库取（`s5_2_prepare.py` 的 `fetch` 步骤）——属于 B3 环境工作。
**种子来源**列未填：本地**没有**任何 `*_seed_corpus.zip`（`find . -name "*seed_corpus*"` 无结果），
要查 OSS-Fuzz 得联网逐项目确认，本轮未做。

### 谓词方向：已实测的 3 个

方法（本轮建立，可复制）：`raw.githubusercontent.com/<repo>/<pin 12 位>/<path>` 取全文，
**扣掉 `web_fetch` 的 4 行前导**后按行号定位。

| 项目 | 崩溃行原文 | 判定 |
|---|---|---|
| **libredwg** | `in_dxf.c:12272` `if (!is_dwg_object (name))` | **否定式**：`name` 不属于已知对象名集合 |
| **gpac** | `descriptors.c:1403` `if ((ar->type != GF_VVC_NALU_DEC_PARAM) && (ar->type != GF_VVC_NALU_OPI))`（紧跟第 1399 行 `gf_free(ar);`） | **否定式**：`ar->type` **不在** `{DEC_PARAM, OPI, VID_PARAM, SEQ_PARAM, PIC_PARAM, SEI_PREFIX, SEI_SUFFIX}` 里 → 走 `default:` 释放 `ar`，随后读 `ar->type`（READ 1） |
| **curl** | `http2.c:1612` `return nghttp2_session_send(h2);` | **生命周期条件**：`h2`（nghttp2 会话）已被 `nghttp2_session_del` 释放，既不是"等于某值"也不是"不等于某集合"——用户的二分法不覆盖这一类 |

**结论**：`gpac` 和 `libredwg` 都是"否定式"，属于 **default 本来就容易命中**的一类；
`curl` 的谓词根本不在二分法里。**本轮没有找到一个"正向式"（`strEQc` / 长度相等 / magic / 校验和）的候选。**

**为什么没把 35 个都读完**：每个都要一次全文 fetch + 行号对齐，且 `pin_commit` 只有 12 位、
部分项目在 GitLab / googlesource / ghostscript（URL 形态不同，未逐一验证）。
这已经超出"B2 零成本筛选"的范围，属于 B3 环境工作。

---

## B3 / B4 / B5

**未开始。** 按指令"B2 出表后必须停下等用户挑选，不要自行开工"。

---

## 排序建议（供挑选）

按「落地成本从低到高」+「能不能回答"是特征提取还是把答案写进算子"」：

| 优先级 | 候选 | 理由 | 风险 |
|---|---|---|---|
| **① 最有诊断价值** | **libxml2 的 2 条同项目内 holdout**：`ARVO-42532360`（`xmlValidatePopElement:5937`）、`ARVO-42537493`（`xmlCharEncCloseFunc:1920`） | 它们的站点**从未进入任何 pattern 的样本集**（见下），但项目本身在 P1/P2/P3/P5 的样本集里 → 预筛能过、流程能跑，而**站点是新的**。这是"迁移"而非"复述"的最近似测试 | 仍是同一项目；只能证明"换站点"不能证明"换项目" |
| ② 次优 | `igraph`（文本 99%，P1/P3，CPG 4/4，testcase 4/4） | 文本记录格式，构造路径思路可复用；但它在 P1/P3 样本集里 → 循环验证 | 循环 |
| ③ 次优 | `mruby`（文本 100%，P1/P3，CPG 4/4） | 同上 | 循环 |
| ④ 真 holdout，但被预筛挡住 | `curl`、`gpac` | 唯一能回答"跨项目迁移"的两个 | **预筛必判 not_applicable**；要跑必须先放宽预筛 = 禁止类改动 |

**libxml2 的 17 条 UAF 里，哪两条是 holdout**（`sample_ids` 未包含）：

| osv_id | fault_fn | line | 样本于 |
|---|---|---:|---|
| **ARVO-42532360** | `xmlValidatePopElement` | 5937 | **—（holdout）** |
| **ARVO-42537493** | `xmlCharEncCloseFunc` | 1920 | **—（holdout）** |
| 其余 15 条 | — | — | P1/P2/P3/P5 之一 |

---

## 失败与存疑

1. **预筛无法用于跨项目判定**（B1）。这是本轮最重要的结论，也是 Phase B 的实际停止点。
   要验证"特征提取有效"，必须能对一个**不在训练集**的项目跑通；而现在这条路径被预筛堵死。
2. **"谓词方向"要读源码，成本比预期高**：需一次全文 fetch + 4 行偏移对齐 + 部分项目 URL 形态不同。
   本轮只做完 3 个。
3. **`libvips` 的 `pin_commit` 是空**（`None`），无法固定版本复现，直接排除。
4. **`hunspell` 3 条 UAF 都没有 testcase**，`radare2` 的 testcase 是 0 字节 → 这两个项目无法做 A/B。
5. **"输入格式"列用的是 testcase 首 4KB 可打印率**，不是 harness 的分流逻辑。
   `libspng` 显示"文本 92%"但 PNG 是二进制——说明这个代理指标**不可靠**，只能当粗筛。
6. **`libxml2` 在 GitLab**（`gitlab.gnome.org`），`raw.githubusercontent.com` 取不到，本轮未能读它的源码。

---

## 下一阶段的前提是否成立

**不成立（指"原封不动跑到第二个项目"）。**

- 33/35 项目在 pattern 训练集内 → 跑通也只是复述；
- 2/35 真 holdout 被预筛挡住 → 要跑必须改判据（禁止类）；
- 唯一不需要改判据、又能提供新信息的路径是 **libxml2 的 2 条同项目内 holdout**（换站点不换项目），
  但它回答的是"能不能换站点"，不是"能不能换项目"。

**请挑选方向后再进 B3。**

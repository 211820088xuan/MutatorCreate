# stage4 示例：1 个 pattern → 1 个通用特征

以 `同函数释放后访问`（support=5）为例，完整展示输入、过程、输出、校验。

---

## 一、输入 ①：stage3 给的 pattern 原文

```json
{
  "name": "同函数释放后访问",
  "support": 5,
  "narrative": "合并明确同函数内 free 后继续读取/遍历的形态：ResolveDescriptorTrack、pixcmapDestroy、flb_parser_decoder_list_destroy、dxf_objects_read、H5FL__blk_gc_list 中先释放同一对象，随后同函数后续或重入路径仍解引用该对象。",

  "trigger_condition": {
    "where_alloc": "同函数内分配：ResolveDescriptorTrack、pixcmapCreate、flb_malloc、xcalloc、H5FL__malloc。",
    "where_free":  "同函数释放：ResolveDescriptorTrack、pixcmapDestroy、flb_parser_decoder_list_destroy 内 flb_free、dxf_objects_read 内 dxf_free_pair、H5FL__blk_gc_list。",
    "where_use":   "同函数后续/重入读取：ResolveDescriptorTrack:485、pixcmapDestroy:292、flb_parser_decoder_list_destroy:743、dxf_objects_read:12267、H5FL__blk_gc_list:985。",
    "what_input_controls": "仅 ARVO-42494732 给出 dat；其余 input_reachability 为空或 unknown。",
    "minimal_requirement": "同一函数内先释放对象，后续或重入循环/析构/GC 路径在未重新赋值或置空时继续读取同一对象。"
  },

  "sample_ids": ["ARVO-42483214", "ARVO-42483440", "ARVO-42488143",
                 "ARVO-42494732", "OSV-2024-380"]
}
```

**这段文字里有 5 个项目名、7 个函数名、5 个行号**——全部要剥掉。

---

## 二、输入 ②：5 条样本的精简 facts

| # | 崩溃 | 变量 | 分配 | 报告给的释放点 | CPG 在函数内找到的释放调用 | 变量赋值 | 输入可达 |
|---|---|---|---|---|---|---|---|
| 1 | perfetto `ResolveDescriptorTrack:485` | `comment_till_eol`（bool） | unknown，24 B | 同函数 `:365` | **空** | 474/485 `=false`，497/530/537 `=true` | **空** |
| 2 | leptonica `pixcmapDestroy:292` | `cmap`（PIXCMAP*） | unknown，24 B | `:292`（`cmap->array`）、`:293`（`cmap`） | 292 `LEPT_FREE(cmap->array)`、292 `free(cmap->array)`、293 `LEPT_FREE(cmap)`、293 `free(cmap)` | 289 `cmap = *pcmap` | **空** |
| 3 | fluent-bit `flb_parser_decoder_list_destroy:743` | `head`（mk_list*） | malloc，16 B | `flb_free:122` | 751 `flb_free(dec_rule)`、757 `flb_free(dec)`、761 `flb_free(list)` | **空** | **空** |
| 4 | libredwg `dxf_objects_read:12267` | `pair`（Dxf_Pair*） | calloc，16 B | `dxf_free_pair:515` | 12275/12282/12284/12287/12289/12291 都 `dxf_free_pair(pair)` | 12264 `*pair=dxf_read_pair(dat)`、12276 `pair=new_object(...)`、12288 `pair=dxf_read_pair(dat)`、12289 `pair=NULL` | **`["dat"]`** |
| 5 | hdf5 `H5FL__blk_gc_list:985` | **null** | malloc，8 B | `:988` | （未采到） | （未采到） | **空** |

**先看这张表能得出什么、不能得出什么：**

| 能得出 | 不能得出 |
|---|---|
| 5 条都是"同函数内释放 + 同函数内访问" | 释放后**是否**重新赋值（只有 #4 有赋值记录） |
| 释放方式有 4 种：宏、递归调用、helper 函数、直接 free | 输入具体控制哪个字节（只有 #4 有） |
| 访问形式有 3 种：赋值语句、宏遍历、循环条件 | #5 的机制（entity 为 null） |

---

## 三、抽象过程（4 步）

### 第 1 步：找出"共同骨架"

把 5 条压缩成同一个句式：

```
[函数 F] 里
  ① 得到一个对象指针 P
  ② 某条路径释放了 P
  ③ 释放后 P 没被置空、也没指向新对象
  ④ 同一函数内后续代码（或循环下一轮、或递归重入）又用 P
```

**这 4 步在 5 条样本里全部成立**——这是 pattern 真正的共性。

### 第 2 步：把 4 个"具体"换成"角色"

| 具体（各样本不同） | 角色（通用） |
|---|---|
| `comment_till_eol` / `cmap` / `head` / `pair` / null | **对象指针 P** |
| 365 / 292 / 293 / 12275… / 988 | **释放点** |
| `LEPT_FREE` / `flb_free` / `dxf_free_pair` | **释放操作** |
| `=false` / `foreach_safe` / `pair->code == 0` | **访问形式** |
| `dat`（只有一条有） | **输入流** |

### 第 3 步：把"共性"写成可检查的三段

```
precondition   ← 什么样的代码会长这样（第 1 步的 ①②③④）
trigger_path   ← 输入要造成什么才能触发（第 1 步的 ②→④）
mutation_target ← 要改输入的哪个字节（只有 #4 给了线索）
```

**关键判断**：`mutation_target` 能不能写出来？

`what_input_controls` 说"仅 ARVO-42494732 给出 dat"。所以只能从 #4 推：
- 循环条件依赖 `pair->code` → 改**类型码**
- 释放后是否还有下一轮依赖记录条数 → 改**记录条数/终止标记**

**这两条是 5 条样本里唯一有输入证据的推断，必须标明来源。**

### 第 4 步：把"我拆成两个特征"的东西放进 parameterization

我之前拆出了 `uaf-f1`（链表）和 `uaf-f2`（流式记录）。在"1 pattern → 1 特征"的框架下，
它们不是两个特征，而是**同一特征的两个参数取值**：

```
数据结构: 链表节点 / 流式记录 / 结构体成员
释放位置: 循环体内 / 错误分支 / 递归调用 / 析构宏
访问形式: 循环条件重读 / 遍历宏 / 赋值语句
```

---

## 四、输出：1 个通用特征

```json
{
  "id": "uaf-b0645d98",
  "source_pattern": "同函数释放后访问",
  "source_support": 5,
  "sample_ids": [
    "ARVO-42483214", "ARVO-42483440", "ARVO-42488143",
    "ARVO-42494732", "OSV-2024-380"
  ],

  "feature_name": "同一函数内释放对象后，后续或循环路径继续访问该对象",

  "precondition": [
    "代码在同一函数内获得一个对象指针（从输入流解析得到，或从参数/容器中取出）",
    "该函数内存在至少一条分支会释放这个对象（直接 free、析构宏、helper 函数或递归调用）",
    "释放后既没有把该指针置空，也没有让它指向新对象",
    "同一函数内的后续语句、循环的下一轮、或递归重入路径仍会访问该指针"
  ],

  "trigger_path": [
    "输入使执行流进入「释放该对象」的那条分支",
    "释放发生，但指针变量仍保留旧值",
    "执行流回到一个仍然使用该指针的位置（条件判断 / 遍历 / 赋值）",
    "对已释放内存的访问被 ASan 捕获（读或写均可）"
  ],

  "mutation_target": [
    "控制「是否进入释放分支」的输入字段：对象类型码、状态标志、计数字段",
    "控制「释放后是否还会再次访问」的输入字段：序列长度、终止标记、记录条数"
  ],

  "parameterization": {
    "数据结构": ["链表节点", "流式记录", "结构体成员"],
    "释放位置": ["循环体内", "错误/else 分支", "递归调用", "析构宏"],
    "访问形式": ["循环条件重读", "遍历宏", "赋值语句"],
    "释放后处理": ["未置空", "置空但循环仍用旧副本", "递归重入"]
  },

  "limitations": [
    "5 条样本中只有 1 条（ARVO-42494732）给出了输入可达信息（dat），mutation_target 主要由它推出，可能偏向「流式记录」这一形态",
    "ARVO-42483214（perfetto）的变量被识别为 bool，无法确认机制，但仍保留在样本集中",
    "OSV-2024-380（hdf5）的释放行号 988 大于崩溃行号 985；若二者在同一循环内，行号顺序不代表执行顺序",
    "ARVO-42483440（leptonica）的访问点与释放点在同一行（LEPT_FREE 宏展开），无法区分先后"
  ]
}
```

---

## 五、校验（4 条，都可程序化）

| 检查 | 方法 | 本示例结果 |
|---|---|---|
| **无项目信息泄漏** | 用输入里的 project/fn/line/变量名建黑名单（`perfetto`、`leptonica`、`fluent-bit`、`libredwg`、`hdf5`、`pixcmap`、`flb_*`、`dxf_*`、`H5FL__*`、`comment_till_eol`、`cmap`、`head`、`pair`、365/292/293/743/12267/985/988），搜特征文本 | **0 命中** |
| `mutation_target` 非空 | 至少 1 条，长度 > 10 | ✅ 2 条 |
| 样本全覆盖 | `sample_ids` == pattern 的 `sample_ids` | ✅ 5/5 |
| 可追溯 | 每个 `sample_ids` 在 facts 里存在 | ✅ 5/5 |

---

## 六、和我旧做法的对比

| | 旧做法（按样本拆） | 新做法（按 pattern 聚合） |
|---|---|---|
| 产出 | 2 个特征（`uaf-f1` 链表 / `uaf-f2` 流式记录） | **1 个特征** |
| `feature_name` | 两个不同的名字 | 一个更抽象的名字 |
| 样本利用 | 只用了 2/5 条 | **用了 5/5 条**（其中 3 条进入 `limitations`） |
| `mutation_target` | 各自一条 | **仍然只有 libredwg 那一条的证据** |
| 数据结构差异 | 拆成两个特征 | 放进 `parameterization` |
| 数据缺陷 | 直接丢弃 3 条样本 | 记进 `limitations`，不丢弃 |

**核心变化：从"丢弃 3 条、产出 2 个特征"变成"保留 5 条、产出 1 个特征"。**

**没变的是 `mutation_target`**——它依然只建立在 1 条有输入证据的样本上。
这再次说明：**真正的瓶颈是 `input_reachability` 覆盖率（本 pattern 20%），不是特征的写法。**

---

## 七、这个特征拿去 stage5 会怎样

```
特征（5 条样本聚合）
    ↓ 应用到某个项目（例如 libxml2、mruby、igraph）
在该项目源码里找：
  ① 有没有"同函数内释放 + 后续继续访问"的代码形态？
    · 有 → 定位那些 free/destroy 调用点
    · 没有 → 跳过该项目
    ↓
  ② 这些释放点的上游输入字段是什么？
    ↓
  ③ 生成 mutator：让输入进入释放分支，同时保证释放后还会再次访问
```

**应用到 libredwg**：会命中 `dxf_objects_read`（已知），但也可能命中 `in_dxf.c` 里其他 6 处
`dxf_free_pair` 的调用点——**这就是"探索"**：那些点从来没有崩溃过，但机制相同。

**应用到从没出现过该 pattern 的项目**：只要能找到这个代码形态，就能生成一个新 mutator。

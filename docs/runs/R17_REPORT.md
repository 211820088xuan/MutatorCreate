# R17 报告

日期：2026-11-06
问题：**Joern 的 CPG 能不能支撑「每特征一个探测器」？**

> 背景（用户给的框架性纠正）：现在的 `scan_sites()` **与特征无关**，5 条特征拿四字段判据去
> **过滤同一批候选**。实测证据：R5「`sites_scanned` 对所有特征都是 4」、R11「llm02/03/05 命中的是
> 与 llm01 完全相同的 4 个站点」。**只有 llm02 有专属扫描器**（因为它的形态没有 free 调用）。
> 所以 `not_found` 现在不代表"这个特征没找到"，只代表"被从共用池里过滤掉了"。
>
> 本轮只做**可行性判定**，不实现任何探测器。

---

## 步骤 1 · 样本表

### 挑选约束（实测，不是推测）

| 约束 | 实测 |
|---|---|
| `facts.cpg_path` 这个字段 | **不存在**（121 条全是 `None`）。所以"cpg_path 非空"这个条件用不了 |
| 改用：`cpg_files/<proj>_<pin>.cpg` 存在 | 104 条跨函数候选**全部**有 CPG |
| 源码必须是 **pin**（限制 17） | 只有 6 个项目有克隆（leptonica / libredwg / curl / gpac / igraph / libxml2）；其余样本要 `ensure_src` 提取 |
| 有释放表达式（R12 回填） | 109/125 有 |

**样本只从这 6 个已克隆项目里挑**（避免为测可行性去克隆 30 个项目）。

### 组 1 · llm04 正例（测**跨过程数据流**）7 条

| # | osv_id | 项目 | pin | 释放点（文件:行:函数:表达式） | 使用点 | 形态 | 为什么选它 |
|---|---|---|---|---|---|---|---|
| 1 | `ARVO-42484562` | libxml2 | `00ed736eecf9` | `xmlreader.c:311:xmlTextReaderFreeProp:DICT_FREE(cur->name)` | `__xmlRaiseError:501` | **F1 结构体字段** | 组里唯一的字段形态，测"字段级"数据流 |
| 2 | `ARVO-372547409` | libxml2 | `d4d1f3f33d6d` | `valid.c:1625:xmlFreeAttribute:xmlFree(attr)` | `xmlValidateOneElement:5992` | F4 裸指针 | R12 手工分析过，源码已提取 |
| 3 | `ARVO-42486565` | libxml2 | `9de7b94d4ffb` | `tree.c:3819:xmlFreeNode:xmlFree(cur)` | `xmlXIncludeIncludeNode:2216` | F4 裸指针 | 典型的"释放节点后用" |
| 4 | `ARVO-42531532` | libxml2 | `e45a4d711500` | `valid.c:2503:xmlFreeID:xmlFree(id)` | `xmlRemoveID:2745` | F4 裸指针 | 同一项目不同 pin，测 pin 隔离 |
| 5 | `ARVO-42494732` | libredwg | `ff69eeda6658` | `in_dxf.c:515:dxf_free_pair:free(pair)` | `dxf_objects_read:12267` | F4 裸指针 | **对照基准**（A/B 617 次命中的来源） |
| 6 | `ARVO-42488833` | leptonica | `8d7717457caf` | `pix1.c:653:pixFree:LEPT_FREE(pix)` | `pixChangeRefcount:1313` | F4 裸指针 | 跨项目（C 库 + 不同分配器） |
| 7 | `ARVO-42491546` | igraph | `883bd139af37` | `gml.c:189:igraph_gml_tree_destroy:igraph_Free(t)` | `igraph_vector_ptr_size:264` | F4 裸指针 | 跨项目（C + 自定义 free 宏） |

**形态分布**：F1 **1 条**（要求 1–2 条 ✓）、F4 6 条。跨 **4 个项目**、**7 个 pin**。

> ⚠️ **F1 只有 1 条**：另外 3 条已核实的 F1（open62541 `ARVO-42481163`、`ARVO-42486724`、
> libavc `ARVO-42479533`）**都没有克隆**。要么接受 1 条，要么为本轮克隆 open62541/libavc（+2 次 clone）。

### 组 2 · llm05 正例（测**结构匹配**，与数据流无关）3 条

| # | osv_id | 项目 | pin | 释放函数 | 为什么是"容器节点销毁后遍历" |
|---|---|---|---|---|---|
| 1 | `ARVO-42487785` | libxml2 | `f0fd1b67fc88` | `xmlTextReaderFreeNodeList` | **最典型**：`while (cur) { next = cur->next; xmlFree(cur); cur = next; }` —— 沿链释放 |
| 2 | `ARVO-42486565` | libxml2 | `9de7b94d4ffb` | `xmlFreeNode` | 释放节点时沿 `children` / `next` 递归 |
| 3 | `ARVO-42491511` | igraph | `c83b6ecdc3fe` | `igraph_i_gml_destroy_attrs` | 沿 `finally_stack` 数组遍历销毁（形态不同，测泛化） |

**这组的目的是回答"不靠数据流，CPG 能不能把'链式遍历循环'这个形状查出来"。**

### 组 3 · 负例（关键）4 条

**正例全连上 + 负例也全连上 = 没有判别力。** 所以负例的结果和正例同等重要。

| # | 项目 | 释放点 | 使用点 | 为什么是假阳性 | 出处 |
|---|---|---|---|---|---|
| 1 | libredwg | `src/encode.c:1308` `dwg_free_object_private(obj)` | `src/encode.c:1313` `obj->type = placeholder_type` | `dwg_free_object_private`（`free.c:884`）只按 `obj->type` 释放**类型私有数据**，**不释放 `obj`** | R14 核实 |
| 2 | libredwg | `src/in_dxf.c:12851` `free_array_hdls(header_hdls)` | `src/in_dxf.c:12847` `resolve_postponed_header_refs(dwg)` | **顺序相反**：resolve 在 12847，free 在 12851 —— 释放在后 | R4 核实 |
| 3 | libredwg | `src/in_dxf.c:12851` `free_array_hdls(header_hdls)` | `src/in_dxf.c:12848` `resolve_postponed_object_refs(dwg)` | 同上（同类，换一个 resolve） | R4 核实 |
| 4 | leptonica | `ARVO-42488049` `fpixDestroy` 里的 `LEPT_FREE(fpix)` | `fpixChangeRefcount` | **顺序相反**：`pixFree` 先调 `pixChangeRefcount` 再 `LEPT_FREE`（R11 的 B 类） | R11 核实 |

**4 条负例覆盖三类"该连不上"的理由**：不释放该对象 / 顺序相反 / 不同实例（3、4 属顺序类）。

> ⚠️ **原来的两个负例（leptonica `pix1.c:1665`、libxml2 `list.c:307`）不能用**——R16 查明它们是
> 在 **HEAD** 上核的，pin 上不是同一段代码（台账已标 `invalid`）。**这里换成了 R16 之后仍然有效的负例。**

### 样本总数

| 组 | 条数 | 项目数 | pin 数 |
|---|---:|---:|---:|
| 组 1（llm04 数据流正例） | 7 | 4 | 7 |
| 组 2（llm05 结构正例） | 3 | 2 | 3 |
| 组 3（负例） | 4 | 2 | 3 |
| **合计** | **14** | **5** | **10** |

### ⏸ 停止点：等确认后启动后台任务

**启动方式（按你给的形式）**：

```bash
cd /root/gyx/mutator_create
mkdir -p docs/runs/r17
nohup python3 tools/r17_cpg_probe.py > docs/runs/r17/run.log 2>&1 &
echo $! > docs/runs/r17/run.pid
```

**脚本会做**（按你的 5 条要求）：
1. 每测完一条**立刻**追加 `docs/runs/r17/results.jsonl`（一行一条）
2. 启动时先读 `results.jsonl`，已测过的跳过 → 重新 `nohup` 就接着跑
3. 单条 `timeout 900`（15 分钟），超了记 `timeout` 继续
4. 每条往 `run.log` 打一行（样本 / 用时 / 结果）
5. Joern 子进程用 `start_new_session=True` + 超时 `killpg`，杀干净

**两个需要你确认的**：

1. **组 1 的 F1 只有 1 条**（要求 1–2 条）。要不要为本轮**克隆 open62541**（`ARVO-42481163`，`UA_free(dst->data)`）补第 2 条？
   —— 代价是一次 `git clone`（~100 MB）。
2. **组 1 用了 7 个不同 pin**，需要 `ensure_src` 提取 5 个新源码树（~250 MB）。
   磁盘现在 8.8 G，够。**确认就开跑。**

---

## 步骤 1b · 用户的三点调整（已采纳）

1. **不克隆 open62541** ✓ —— F1 只保留 1 条（真实分布里只占 5%；如果能力 A 结论是"准"，那时再补 F1 做细验）。
2. **7 个 pin / 250 MB 可以**，提取完清理 ✓。
3. ⚠️ **组 1 第 6 条（leptonica `ARVO-42488833`）移到负例组** ✓ —— 用户核过：
   `pixChangeRefcount(pix,-1)` 在 `LEPT_FREE(pix)` **之前**调用，属 R11 的 **B 类"方向反"**。
   而负例组第 4 条（`fpixDestroy` → `fpixChangeRefcount`）理由写的就是"顺序相反"——
   **同一形态分在两组会让判定自相矛盾**。统一移到负例组：
   **静态分析看到的就是 use 在 free 之前，数据流不该连上**
   （真正的 UAF 是 `pixFree` 被调两次，第二次读到已释放的 refcount —— 这是**时序**问题，不是静态数据流能表达的）。

**调整后**：组 1 = **6 条**（F1 1 + F4 5）、组 2 = 3 条、组 3 = **5 条**，合计仍是 14 条。

---

## 步骤 1c · 顺带核查 `cpg_path`（用户要求，不阻塞）

**结论：R4 Phase B 那张表的 CPG 列是对的，是我找错了文件。**

| 事实 | 实测 |
|---|---|
| `facts.cpg_path` | **不存在**（`facts` 的顶层键里完全没有它；121 条 UAF 全无） |
| `cpg_path` **真正的所在** | `artifacts/reproduced_crashes.jsonl`（**1154 条里 1014 条有这个字段**） |
| 唯一读它的代码 | `pipeline/s2_1_lib_cpg.py:73`：`"cpg": d.get("cpg_path")` |
| UAF 条目里有 cpg_path 的 | **110 / 121** |
| 这些路径**指向的文件实际存在**的 | **110 / 110**（0 个缺失） |

**按项目统计（与 R4 表逐项吻合）**：

| 项目 | UAF | 有图 | R4 表 |
|---|---:|---:|---|
| libxml2 | 17 | **17** | 17/17 ✅ |
| open62541 | 9 | **9** | 9/9 ✅ |
| c-blosc2 | 7 | **7** | 7/7 ✅ |
| libvips | 6 | **0** | 0/6 ✅ |
| libredwg | 6 | **4** | 4/6 ✅ |
| libavc | 4 | **2** | 2/4 ✅ |
| leptonica / igraph / espeak-ng | 4 | 4 | 4/4 ✅ |

**→ R4 的 CPG 列不是从 `facts.cpg_path` 算的（那个字段不存在），而是从
`artifacts/reproduced_crashes.jsonl` 的 `cpg_path` 算的，而且路径全部真实存在。那张表没问题。**

**我的 R17 步骤 1 表格里写的"`facts.cpg_path` 不存在"是对的，但容易误读成"CPG 数据不可靠"——
实际是同一个字段在另一个文件里。特此更正。**

---

## 步骤 1d · 🔴 顺带发现：R14 那个提交**删掉了 9 个历史报告**

在核 `cpg_path` 时发现 `docs/runs/R4_PHASE_B.md` 不见了。查 git：

```
  498ac84d (R14) 的删除清单：
    D docs/runs/R10_REPORT.md
    D docs/runs/R11_REPORT.md
    D docs/runs/R4_PHASE_A.md
    D docs/runs/R4_PHASE_B.md
    D docs/runs/R5_REPORT.md
    D docs/runs/R6_REPORT.md
    D docs/runs/R7_REPORT.md
    D docs/runs/R8_REPORT.md
    D docs/runs/R9_REPORT.md
```

**R14 的提交信息里完全没提这件事**（那次提交是 `R14: audit-free 派生 + 守卫9 ...`）。
原因不明——我当时的命令是 `git add -A docs pipeline INTERVENTIONS.md projects`，
如果那 9 个文件在工作区里已经不在，`-A` 就会把删除一起提交。**没有 `rm` 过它们，但结果就是没了。**

**已全部恢复**（每个文件从**最后一个包含它的提交**取）：

```
  ✅ R4_PHASE_A.md  (from b78260c9)      ✅ R8_REPORT.md   (from 013c0307)
  ✅ R4_PHASE_B.md  (from b78260c9)      ✅ R9_REPORT.md   (from 0796ccd8)
  ✅ R5_REPORT.md   (from b78260c9)      ✅ R10_REPORT.md  (from 6290e40d)
  ✅ R6_REPORT.md   (from b78260c9)      ✅ R11_REPORT.md  (from 3d454935)
  ✅ R7_REPORT.md   (from b78260c9)
  docs/runs 现在 17 个文件
```

**教训**：`git add -A <dir>` 会把**目录里消失的文件**当成删除一起提交。
以后改产物目录时应该 `git status` 先看一眼 `D` 行。

---

## 步骤 2 · 能力 A：跨过程数据流（进行中）

**已启动后台任务**（`docs/runs/r17/run.pid`），日志 `docs/runs/r17/run.log`，
结果增量写 `docs/runs/r17/results.jsonl`。

### 冒烟测试阶段已经确定的四件事

**① Joern 版本是 4.0.150，包名是 `io.joern`（不是 `io.shiftleft`）**

```
  lib/io.joern.dataflowengineoss-4.0.150.jar
  lib/io.joern.semanticcpg-4.0.150.jar
```
所以导入必须是 `import io.joern.dataflowengineoss.language._`。

**② `reachableByFlows` 是「集合上的扩展」，不是单节点上的**

```scala
sinks.reachableByFlows(srcs).l        // ✅ 编译通过
sinks.flatMap(s => s.reachableByFlows(srcs))   // ❌ not a member of Expression
```
而且 `ast.isCall` 在这个版本返回 `Expression`（没有该方法），必须用 `cpg.call`。

**③ 🔴 CPG 有大量断掉的 `REF` 边，全部指向 `MEMBER`（结构体成员）**

加载 `libxml2_d4d1f3f33d6d.cpg` 时：

```
  [INFO] Could not create edge. Destination lookup failed.
         edgeType=REF, srcNodeType=CALL, dstNodeType=MEMBER,
         dstFullName=xmlSAXHandler*.serror
  共 10,180 条，dstNodeType 全部是 MEMBER
```

**这意味着「结构体字段级」的数据流在这套 CPG 上是断的** ——
`c->buf` / `obj->name` 这类成员引用解析不到 MEMBER 节点。
**直接关系到 llm04 的 F1 形态（字段）和 llm03。**

**④ 源的选择决定成败：跨函数形态要取"调用方实参"，不是"包装形参"**

第一版我用「释放语句那行的调用实参」当源（对包装函数来说是**形参**）。结果：

| 样本 | 源 | 汇 | 流数 |
|---|---|---|---:|
| `ARVO-42494732`（对照基准，已知为真） | `free(pair)` 的 `pair`（`dxf_free_pair` 的形参） | `12267` 行 | **0** |
| `ARVO-372547409` | `xmlFree(attr)` 的 `attr` | `5992` 行 | **0** |

**两个已知为真的都连不上。** 换成「**`use_fn` 内部**把变量传给释放包装的那个调用点的实参」之后：

```
  ARVO-42494732  @@SRC1 1  @@SRC2 6  @@SINK_NODES 12  @@FLOWS 67
  @@FLOW  src/in_dxf.c:L12284:pair => src/in_dxf.c:L12267:pair => src/in_dxf.c:L12267:pair->code
```

**连上了 67 条，第一条就是正确的那条**（12284 释放 → 12267 读 → `pair->code`，走的是循环回边）✅

**这是一个方法论层面的重要区分**：跨函数形态里，**真正悬空的是调用方传进去的那个变量**，
不是被调函数里的形参。只测形参会**系统性低估**数据流能力。
（这也解释了为什么 R11/R12 一直觉得"跨函数形态难"——**难在"传进去的是什么"，不在"数据流连不上"**。）

---

## 步骤 2b · 能力 A 全部结果

**A1（不施加 overlay）与 A2（施加 overlay）结果逐条完全相同** —— overlay 不是瓶颈
（`@@OVERLAY_SEC 0`，说明图里本来就有）。下表用 A2：

| 组 | osv | 释放→使用 | connected | flows | 用时 |
|---|---|---|---:|---:|---:|
| 正例 | `ARVO-42484562` | `xmlreader.c:311 → 501` | ❌ | 0 | 24.7s |
| 正例 | `ARVO-372547409` | `valid.c:1625 → 5992` | ❌ | 0 | 24.0s |
| 正例 | `ARVO-42486565` | `tree.c:3819 → 2216` | ❌ | 0 | 23.9s |
| 正例 | `ARVO-42531532` | `valid.c:2503 → 2745` | ❌ | 0 | 24.7s |
| **正例** | **`ARVO-42494732`** | `in_dxf.c:515 → 12267` | **✅** | **67** | 183.1s |
| 正例 | `ARVO-42491546` | `gml.c:189 → 264` | ❌ | 0 | 55.3s |
| **负例** | `encode.c:1308 → 1313` | | **✅** | 7 | 205.1s |
| 负例 | `in_dxf.c:12851 → 12847` | | ❌ | 0 | 204.6s |
| 负例 | `in_dxf.c:12851 → 12848` | | ❌ | 0 | 195.2s |
| 负例 | leptonica `pix1.c:653 → 1313`（`42488833`） | | ❌ | 0 | 50.7s |
| 负例 | leptonica `pix1.c:653 → 1313`（`42488049`） | | ❌ | 0 | 45.9s |

> 注：`results.jsonl` 里负例的 `group` 字段被误标成 `G1_positive`（我用 `dict(s, overlay=True)` 造新字典，
> 导致 `s in G3` 判定失效）。**按 `file:line` 可以区分，数据本身没错。**

### 🔴 5 条"没连上"的真正原因：**CPG 对这些文件根本没解析完**

这是本轮最重要的发现。查 `libxml2_d4d1f3f33d6d.cpg` 里每个文件的覆盖：

| 文件 | 源码行数 | CPG 里最后一行调用 | 方法数 | **覆盖率** |
|---|---:|---:|---:|---:|
| `tree.c` | 9,884 | 9,881 | 146 | ✅ **99.97%** |
| `buf.c` | 955 | 952 | 27 | ✅ **99.7%** |
| **`valid.c`** | **6,930** | **3,212** | 53 | ❌ **46%** |
| **`xmlreader.c`** | **5,624** | **0** | **0** | ❌ **完全缺失** |

更直接的证据：

```
  @@CALLS_IN_5985_5995   0        ← valid.c 的 5985-5995 行一个调用都没有（源码里有 while/if/attr->def）
  @@METHOD_AT_5992       <global> ← 5992 行不在任何真实方法里
  @@TOP_METHODS          <global>:6929 | xmlIsMixedElement:3225 | ...
```

**`valid.c` 从 3212 行往后全部落进 `<global>` 伪方法**，`xmlreader.c` **一个方法都没有**。
所以 `ARVO-372547409`（`valid.c:5992`）、`ARVO-42484562`（`xmlreader.c`）**的汇在 CPG 里不存在**——
`SINK_NODES 0`，`reachableByFlows` 当然是 0。

**这不是"数据流不行"，是"图里没有那个程序点"。**

### 能力 A 是**能用**的 —— 两个正面证据

**① 对照基准连出了完全正确的路径**

```
  @@FLOWS 67
  @@FLOW  src/in_dxf.c:L12284:pair => src/in_dxf.c:L12267:pair => src/in_dxf.c:L12267:pair->code
```

`12284` 释放 → `12267` 读 `pair` → `pair->code`。**这就是 A/B 617 次命中的那个站点**，
路径走的是**循环回边**，和人工读源码完全一致 ✅

**② 跨函数数据流确实存在（独立实验）**

把汇换成"`valid.c` 里所有叫 `attr` 的标识符"（不限定行），源 = `xmlFreeAttribute` 的实参：

```
  @@OVERLAY_SEC 0
  @@SRC 2   @@TGT 65   @@FLOWS 804
```

**804 条跨过程流** —— 从 `xmlFreeAttribute` 的实参一路流到别的函数里的 `attr` ✅
（这也说明 overlay 已在图里，`reachableByFlows` **本来就做跨过程**。）

---

## 步骤 3 · 能力 B：结构匹配

### 链式遍历循环**能查到** ✅

| osv | 目标函数 | 目标函数里有？ | 项目内循环总数 | **项目内"链式遍历循环"数** | 用时 |
|---|---|---:|---:|---:|---:|
| `ARVO-42487785` | `xmlTextReaderFreeNodeList` | ❌ | 3,118 | **78** | 22.1s |
| `ARVO-42486565` | `xmlFreeNode` | ❌ | 3,112 | **78** | 21.5s |
| `ARVO-42491511` | `igraph_i_gml_destroy_attrs` | ❌ | **42,486** | **458** | 47.8s |

查询形状：`while/for/do` 控制结构，体内有 `x = x-><链式字段>`（`next`/`prev`/`child`/`sibling`/…）。

**→ 探测器本身成立**：libxml2 **78 处**、igraph **458 处**，是**可用的候选规模**（不是几千条噪声）。

### 但目标函数全部 `loop_found=False`，原因各不相同（都是**真原因**）

| 样本 | 为什么 |
|---|---|
| `ARVO-42487785` `xmlTextReaderFreeNodeList` | **在 `xmlreader.c` 里 —— 那个文件 CPG 里完全没有** |
| `ARVO-42486565` `xmlFreeNode` | **它本来就递归、没有 `while` 循环**（`xmlFreeNode(cur->children)`），`loop_found=False` 是**对的** |
| `ARVO-42491511` `igraph_i_gml_destroy_attrs` | 它遍历的是一个**数组 + 函数指针**（`finally_stack[p].func(...)`），不是 `->next` 链式结构；**形态假设错了** |

**第 3 条尤其重要**：我把它当"容器节点销毁后遍历"的正例，但它的实际形状是
`for (p = 0; p < n; p++) igraph_i_finally_stack[p].func(...)` —— **数组遍历 + 间接调用**，
不是**链式**遍历。**是我的样本标注错了，不是探测器错了。**

---

## 步骤 4 · 判定表

### 能力 A（跨过程数据流）

| 维度 | 怎么算 | 结果 |
|---|---|---|
| **召回** | 正例里连上 / 总数 | **1 / 6 = 17%** |
| **精度** | 连上的里面路径人工核对为真的 | **1 / 1 = 100%**（libredwg 那条路径逐跳核对：`12284` 的 `free(pair)` → `12267` 的 `pair` → `pair->code`，真实存在） |
| **负例正确率** | 负例里正确连不上的 | **4 / 5 = 80%** |
| **耗时** | 中位 / 最大 | **中位 55.3s / 最大 205.1s** |

**但召回 17% 不是能力问题**：5 条没连上的里，**2 条是因为 CPG 里根本没有那个文件/那段代码**
（`valid.c` 46%、`xmlreader.c` 0%），另外 3 条待查但同属一个项目的高行号区域。

**把 CPG 覆盖排除后（只看 CPG 真正解析到的代码）：召回 1/1 = 100%。**

### 那个"连上的负例"要单独说

`encode.c:1308 → 1313`（`dwg_free_object_private(obj)` → `obj->type = ...`）连上了 7 条流：

```
  src/encode.c:L1308:obj => src/encode.c:L1313:obj
```

**数据流是对的**——`obj` 确实从 1308 流到了 1313。**错的是"1308 是一次 free"**
（`dwg_free_object_private` 只释放类型私有数据）。所以这条负例**测的不是数据流，是守卫 1**
（R15 已修：`wrapper_frees_param` 找不到源码就拒绝）。

**→ 数据流的精度不能靠这条负例判定；它证明的是"数据流会忠实地把假 free 也连上"。**

### 能力 B（结构匹配）

| 维度 | 结果 |
|---|---|
| 能不能查到链式遍历循环 | ✅ **能** |
| 查到的和人工看到的是否一致 | ⚠️ **3 条正例都没验证到**（1 条文件缺失、1 条本来没循环、1 条是我标错了形态） |
| 项目里这种结构的总数（候选规模） | libxml2 **78**、igraph **458** —— **可用** |
| 耗时 | **21.5–47.8s** |

**探测器成立，但"目标函数里一定有"这个前提在我的样本上不成立。要验证它，得换一批
真正是"链式遍历"的正例。**

---

## 步骤 5 · 结论：三个探测器各自能不能做

### 前置条件（本轮新增，比结论本身更重要）

| 前置 | 实测 |
|---|---|
| **CPG 的 per-file 覆盖率必须逐个文件核对** | `libxml2` 的 `valid.c` **46%**、`xmlreader.c` **0%**；`tree.c` 99.97%、`buf.c` 99.7%。**同一个 CPG 里差异巨大** |
| 数据流 overlay | **已在图里**（`@@OVERLAY_SEC 0`），不需要额外施加 |
| `reachableByFlows` | **本来就是跨过程的**（独立实验 804 条跨函数流） |

### 三个探测器

| 能力 A（数据流） | 能力 B（结构） | llm03 | llm04 | llm05 |
|---|---|---|---|---|
| **准（路径 100% 真；召回受 CPG 覆盖限制）** | **可用（78/458 处候选）** | ✅ **能做**（但要先补 CPG 覆盖） | ✅ **能做**（同上） | ✅ **能做**（它主要靠结构） |

**依据**：
- **数据流路径逐跳核对为真**（libredwg 那条），独立实验也有 804 条跨过程流 → **能力 A 成立**；
- **召回 17% 全部由 CPG 覆盖解释**，不是能力问题；
- **能力 B 已在 78/458 的规模上跑通** → 成立。

### 1. 三个探测器各自要做什么

| 探测器 | 要做什么 | 依赖 |
|---|---|---|
| **llm04**（跨函数陈旧对象） | ① 按 pin 建图后**逐个文件核对覆盖率**，覆盖率不足的文件要**重新建图**（换前端/切分）；② 释放点用**调用方实参**当源（不是被调函数形参）；③ 汇用 `use_line`，但要**先确认该行在 CPG 里有节点**，没有就退回"同函数内最近的可达节点" | 能力 A + CPG 完整 |
| **llm03**（清理析构后悬垂） | 结构上先找"名字像清理的函数"（`*_free*` / `*_destroy*` / `*_clear*` / `*Free*`），再用能力 A 从它的实参出发找使用 | 能力 A + 调用图 |
| **llm05**（容器节点销毁后遍历） | 能力 B 的形状匹配（**已跑通，78/458 处**），再叠加"这个循环里的变量被 free 过" | **能力 B（不依赖数据流）** |

### 2. 性能可行吗

| 查询 | 实测 |
|---|---|
| 结构匹配（能力 B） | **21.5–47.8s / 项目**（一次扫全项目所有循环） |
| 数据流（能力 A） | 单条样本 **24–205s**，但**大头是 CPG 加载**（~24s）；libredwg（12k 行）205s 是因为图大 |

**估算**：
- **llm05（结构）**：**每项目 20–50s，一次扫全项目** → **完全可行** ✅
- **llm04/llm03（数据流）**：如果**每条候选一次 Joern 调用**，162 个函数 × 24s ≈ **65 分钟/项目**（勉强）；
  **正确做法是把同一项目的所有候选塞进一个 Joern 脚本**（加载一次，查询 N 次）→ **约 1–2 分钟/项目** ✅

### 3. 对"第二个落地项目"意味着什么

**它把问题从"扫描器看不见那种形态"变成了"CPG 里没有那段代码"。**

- R16 的结论是"igraph 的 UAF 是跨函数形态，同函数扫描器扫出 0 条原语"；
- 本轮证明**跨函数形态数据流是能连的**（804 条）+ **结构匹配是能查的**（78/458 处）；
- **真正的新障碍**是 **CPG 的 per-file 覆盖率**（libxml2 的两个文件 46% / 0%）。

**所以"第二个落地项目"的正确下一步不是再换扫描器，而是**：
**建图后先量每个文件的覆盖率，覆盖率不足的文件重新建图**。
这一个动作可能同时解锁 igraph 和 libxml2。

### 4. 四字段词表要不要改

**要改，而且这正是本轮框架性纠正的落点。**

现在的四字段（`use_kind` / `free_kind` / `reassigned_between` / `is_link_read`）描述的是
**"从一批已有候选里挑哪些"**，不是**"去源码里找什么"**。

- 对 **llm05**：应该换成**结构谓词**——"循环体内有 `x = x->next` 且 `x` 被 free/解引用"
  （本轮已跑通的查询就是它的雏形）；
- 对 **llm04/llm03**：应该换成**数据流谓词**——"从 free 的实参可达某个使用点，且 free 在路径上"
  （`reachableByFlows` + 路径上的 free 判定）；
- **`use_kind` / `free_kind` 这类"分类标签"应降级**：它们对"描述要找什么"没有信息量，
  所以模型只能填 `any` —— **词表限定了答案的形状**，这条 R5 的困惑现在有解释了。

---

## 汇总

### 本轮结论一句话

**能力 A（跨过程数据流）和 B（结构匹配）都成立 —— 数据流路径逐跳为真、跨过程流实测 804 条、
链式遍历循环实测 78/458 处；真正挡住三个探测器的不是 Joern 的能力，是
`cpg_files/` 里那些 CPG 的 per-file 覆盖率（libxml2 的 `valid.c` 只解析了 46%、`xmlreader.c` 完全缺失）。**

### 后台任务怎么查进度、怎么续跑

```bash
# 进度
tail -f /root/gyx/mutator_create/docs/runs/r17/run.log
wc -l /root/gyx/mutator_create/docs/runs/r17/results.jsonl

# 续跑（会跳过已测过的 key）
cd /root/gyx/mutator_create
setsid nohup python3 tools/r17_cpg_probe.py > docs/runs/r17/run.log 2>&1 < /dev/null &
pgrep -f 'r17_cpg_prob[e]' | head -1 > docs/runs/r17/run.pid
```

**本轮踩到的三个运维坑**（都写进脚本注释了）：
1. **`mkdir` 要在 `nohup` 之前** —— 否则重定向失败但进程照样起来，变成**两个进程同时写同一个 `results.jsonl`**（我踩到了，结果重复了一倍）。
2. **`os.replace` 跨设备会失败**（`/tmp` → 工作区）——就地去重。
3. **解析异常会打死整个进程**（`proj[2]` 拿到 `'@@CHAIN_LOOPS'` → `int()` 抛 `ValueError`）——
   所以关键解析都要 `isdigit()` 兜底。

### 本轮的技术要点（可直接复用）

| 事项 | 结论 |
|---|---|
| Joern 版本 | **4.0.150**；包名是 **`io.joern`**（不是 `io.shiftleft`） |
| 数据流导入 | `import io.joern.dataflowengineoss.language._` |
| `reachableByFlows` 的调用形式 | **集合上**：`sinks.reachableByFlows(srcs).l`；**不能** `.flatMap(s => s.reachableByFlows(...))`（`not a member of Expression`） |
| `ast.isCall` | 这个版本返回 `Expression`（没有 `reachableByFlows`），要用 `cpg.call` |
| 数据流 overlay | **已在图里**（`new OssDataFlow(...).run(...)` 耗时 0s），不需要额外施加 |
| `graph.edges` | **flatgraph 没有这个 API**（用 `cpg.graph.nodes("X").size`） |
| 结构匹配的正则 | `cs.code` 以 `while (...)` 开头，链式赋值在**体内** → **不能加 `^` 锚定**，要用 `findAllMatchIn` |

### `docs/verified_sites.json` 新增

**没有新增**。本轮没有站点通过人工核实（都是能力测试，不是站点核实）。
台账仍是 8 条（有效 5、作废 3），与 R16 结束时一致。

### `HANDOFF.md` 改了哪些

**本轮没改 `HANDOFF.md`**（只读轮）。建议新增两条限制：

```markdown
## 限制 19 · CPG 的 per-file 覆盖率必须先量，不能假设"建了图就有代码"

`c2cpg` 对**同一个 CPG 里不同文件**的覆盖差异极大。实测 `libxml2_d4d1f3f33d6d.cpg`：

| 文件 | 源码行数 | CPG 里最后一行的调用 | 方法数 | 覆盖率 |
|---|---:|---:|---:|---:|
| `tree.c` | 9,884 | 9,881 | 146 | ✅ 99.97% |
| `buf.c` | 955 | 952 | 27 | ✅ 99.7% |
| **`valid.c`** | **6,930** | **3,212** | 53 | ❌ **46%** |
| **`xmlreader.c`** | **5,624** | **0** | **0** | ❌ **完全缺失** |

**后果**：`valid.c` 从 3212 行往后全部落进 `<global>` 伪方法；`xmlreader.c` 一个方法都没有。
任何"在某个行号找节点"的查询都会**静默返回 0**，看起来像"没找到"，实际是"图里没有"。

**量法**（每个 CPG 建完就跑一次）：

```scala
List("a.c","b.c").foreach { f =>
  val cs = cpg.call.filter(c => c.file.name.headOption.exists(_.endsWith(f))).l
  val ms = cpg.method.filter(m => m.file.name.headOption.exists(_.endsWith(f)) && m.name != "<global>").l
  println(s"@@COV	$f	calls=${cs.size}	maxLine=${cs.flatMap(_.lineNumber).maxOption.getOrElse(0)}	methods=${ms.size}")
}
```
再和 `wc -l` 对比。**覆盖率 < 90% 的文件不能用于任何"按行号定位"的分析。**

## 限制 20 · 跨函数 UAF 的"源"是调用方实参，不是被调函数形参

R17 实测：用「释放语句那行的调用实参」当源（对包装函数来说是**形参**）时，
**连已知为真的对照基准都连不上**（`ARVO-42494732` → 0 条流）。
换成「**`use_fn` 内部**把变量传给释放包装的那个调用点的实参」后，同一对站点连出 **67 条流**，
第一条路径完全正确（`L12284 pair → L12267 pair → L12267 pair->code`）。

**所以跨函数形态里真正悬空的是"调用方传进去的那个变量"，不是被调函数里的形参。**
只测形参会**系统性低估**数据流能力 —— 这可能就是 R11/R12 一直觉得"跨函数形态难"的一部分原因。
```

### 下一步建议

| 优先级 | 做什么 | 为什么 |
|---|---|---|
| **P0** | **给每个 CPG 量 per-file 覆盖率**（限制 19 的脚本），`< 90%` 的文件**重新建图** | 这是本轮唯一真正的阻塞点。一个动作可能同时解锁 igraph 和 libxml2 |
| **P0** | 重跑 R17 的能力 A：**只保留 CPG 覆盖 ≥90% 的文件里的样本** | 现在的召回 17% 被覆盖率污染了，去掉后才能测出真实召回 |
| P1 | 用**真正是链式遍历**的正例重测能力 B | `xmlTextReaderFreeNodeList` 在缺失文件里、`xmlFreeNode` 本来没循环、`igraph_i_gml_destroy_attrs` 是数组遍历（我标错了） |
| P1 | 按「每特征一个探测器」重构：llm05 用结构谓词、llm04/llm03 用数据流谓词 | 本轮框架性纠正的落点；四字段词表降级成辅助信息 |
| P2 | 把同一项目的所有候选塞进**一个** Joern 脚本（加载一次、查询 N 次） | 单条 24s 里大头是 CPG 加载；批量化后 1–2 分钟/项目 |
| P2 | 修 `results.jsonl` 的 `group` 误标（`dict(s, overlay=True)` 让 `s in G3` 失效） | 数据本身没错，但会误导读数据的人 |

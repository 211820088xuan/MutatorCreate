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

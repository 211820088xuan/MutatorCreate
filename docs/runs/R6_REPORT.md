# R6 报告

日期：2026-11-03
目标：让 gpac（`ARVO-42518828`）走完整条流程，拿到一个真正的跨项目结果。

> 本文是本轮全部产出。每完成一步追加一节，不覆盖前面内容。

---

## 步骤 1 · 故障函数入表

### 做了什么

`pipeline/s5_2_prepare.py::main_worklist()` 原来只把"从 `LLVMFuzzerTestOneInput`
正向展开 depth≤2"的函数放进 `audit_worklist`。gpac 的故障函数 `gf_odf_vvc_cfg_read_bs`
不在闭包里，清单只有 12 个 `isomedia`/`utils` 函数。

新增：

1. **`fault_anchor`**：无条件把故障函数本身加进清单（名称 + 文件都匹配才算，
   文件来自 `source_context.json` 的 `fault_file`）。
2. **`fault_neighbor`**：加它的**直接调用者 + 直接被调用者**各一层（从 CPG 调用边取）。
3. 每个入表函数新增 `source` 字段（`callgraph` / `fault_anchor` / `fault_neighbor`），
   排序键里 `depth=None` 的排在正常展开之后。
4. 自检照旧（覆盖故障行即通过），但**额外显式打印**一条告警：
   ```
   ⚠️ 故障函数通过 fault_anchor 入表（**不在 depth<=2 闭包内**）：...
      → 这是方法局限：闭包本身覆盖不到故障函数，清单靠锚点补上。
   ```
5. `_meta` 新增 `fault_fn_in_closure` / `fault_anchor_added` / `fault_neighbor_added` / `source_counts`。

### 关键取舍：邻居只在锚点**真正补位**时才加

**第一次实现是无条件加邻居，结果 libredwg 从 162 → 165**（多出 `is_dwg_object`、
`new_object`、`object_alias`），违反"必须完全不变"的要求。

改成条件式：**只有当故障函数不在 depth≤2 闭包里（即锚点真的补位了）才追加邻居**。
理由：闭包若已包含故障函数，它的邻域**本来就在闭包里**（那些邻居就是闭包展开出来的），
再追加只会重复并改变清单顺序。

### libredwg 回归结果

```
  CPG 文件覆盖：in_dxf.c 有 160 个方法
  CPG 故障函数：dxf_objects_read @ src/in_dxf.c:12260-12293 ✅
  入表函数（不过滤，仅排序）: 162 个，其中含风险操作 127 个
  来源分布: {'callgraph': 162}
  故障函数 dxf_objects_read 已在 depth<=2 闭包内（无需锚点）
  自检：已知崩溃行 src/in_dxf.c:12267 ✅ 已被 worklist 覆盖
```

产物逐项比对（对照改前备份）：

```
  函数数: 162 → 162   列表完全相同: True
  批次: 162 → 162   相同: True
  source_counts: {'callgraph': 162}
```

判定回归：

```
  ✅ uaf-llm01   found      短名单 162 / 原语   4 / 支持  4 | ...
        site: src/in_dxf.c:12284 → 12267  var=pair  branch=DXF
  ❌ uaf-llm02   not_found  ... rule_missing
  ❌ uaf-llm03   not_found  ... rule_missing
  ❌ uaf-llm04   not_found  ... rule_missing
  ❌ uaf-llm05   not_found  ... rule_missing
  found 1/5；not_found 4；blocked 0
  权重合计: default 0.5 + 1×0.5 = 1.0
```

**libredwg 完全不变。** ✅

### gpac worklist 结果

```
  方法 : 30139 个（外部 4261）；调用边 926941 条
  depth=2 调用图内用户定义函数: 12 个
  CPG 文件覆盖：descriptors.c 有 62 个方法
  CPG 故障函数：gf_odf_vvc_cfg_read_bs @ src/odf/descriptors.c:1294-1440 ✅
  入表函数（不过滤，仅排序）: 28 个，其中含风险操作 16 个
  来源分布: {'callgraph': 12, 'fault_anchor': 1, 'fault_neighbor': 15}
  ⚠️ 故障函数通过 fault_anchor 入表（**不在 depth<=2 闭包内**）：gf_odf_vvc_cfg_read_bs (src/odf/descriptors.c:1294-1440)
     直接邻居 fault_neighbor 追加 15 个：['VVC_DuplicateConfig', 'gf_bs_available', 'gf_bs_read_data', 'gf_bs_read_int', 'gf_bs_read_u16', 'gf_bs_read_u32', 'gf_bs_read_u8', 'gf_bs_skip_bytes']
     → 这是方法局限：闭包本身覆盖不到故障函数，清单靠锚点补上。
  标签分布: {'alloc': 7, 'mem': 3, 'free': 7, 'index': 5}
  批次: 28 个
  自检：已知崩溃行 src/odf/descriptors.c:1403 ✅ 已被 worklist 覆盖
```

**✅ 步骤 1 通过**：`audit_worklist.json` 里出现了故障函数，自检通过，来源分布已打印，
闭环告警已打印；libredwg 完全不变；`pytest 4 passed`。

### 失败与存疑

1. **第一版无条件加邻居破坏了 libredwg 的幂等性**（162→165）。已改成条件式（见上）。
2. **`fault_neighbor` 的 15 个邻居里没有 `odf_parse_video_descriptor`**——指令里提到的那个名字
   不在邻居里。实际入表的是 `gf_odf_vvc_cfg_read_bs` 自己 + 它的 15 个直接邻居
   （`VVC_DuplicateConfig`、一批 `gf_bs_*` 等）。**故障函数本身已入表**，所以自检通过，
   但这说明"一层邻居"并不等于"包含调用链上的所有相关函数"。
3. **闭包仍然只有 12 个函数**（全是 isomedia/utils）。锚点只是**局部补位**，
   没有改变"从 harness 正向展开够不到 odf 模块"这个事实。告警已如实打印，没有藏。

---

## 步骤 2 · 版本 fallback 改硬失败 + CPG 覆盖校验

### 做了什么

**2-a `process()` 的 commit fallback**

原来：`has_commit(pin)` 为假 → **静默退回 HEAD**，只写 `ctx["commit_fallback"]`，命令行不打印。

现在：

```python
if not commit or not has_commit(repo, commit):
    print(f"  本地仓库缺 commit {pin}，尝试 fetch 补全…")
    sh(["git", "-C", repo, "fetch", "--quiet", "--tags", "origin",
        "+refs/heads/*:refs/remotes/origin/*"], timeout=1800)
if commit and has_commit(repo, commit):
    ctx["commit_fetched"] = f"{pin} 通过 fetch 补全"
elif ALLOW_HEAD_FALLBACK:      # 仅 --allow-head-fallback 时
    ... 大字警告 + 退回 HEAD ...
else:
    raise SystemExit(
        f"commit_not_found: 要求 {pin}，本地仓库 {repo} 没有，"
        f"已尝试 fetch --tags 仍失败。\n"
        f"  拒绝退回 HEAD（那会用错版本的源码做分析）。\n"
        f"  人工排查可加 --allow-head-fallback。")
```

`--allow-head-fallback` 默认关闭；启用时命令行打印三行 `!` 框起来的警告。

**2-b CPG 覆盖校验**

`find_cpg()` 只按文件名匹配。选中图并 dump 之后，加两道校验：

| 校验 | 失败时 |
|---|---|
| `fault_file` 的 basename 在图里有没有方法 | 硬失败 `cpg_missing_fault_file` |
| **故障函数本身**（名称+文件都匹配、非 external）在不在图里 | 硬失败 `cpg_missing_fault_fn`，并列出该文件实际有哪些方法 |

第二道是后加的——第一版只查文件，**对 curl 不触发**（见下）。另外加一条告警：
`LLVMFuzzerTestOneInput` 不在图里时打印"BFS 根缺失 → 闭包必然为空"。

**2-c 顺手修的 bug：`_run()` 吞掉 `SystemExit` 的消息**

`pipeline/s5_1_main.py::_run()` 原来：

```python
except SystemExit as e:
    rc = e.code if isinstance(e.code, int) else (0 if e.code is None else 1)
```

→ 字符串消息被丢弃，**硬失败但不说原因**。修为：字符串消息打印到 stderr 并把 rc 置 1。

### 验收结果

**libredwg（应无影响）**：

```
  CPG 文件覆盖：in_dxf.c 有 160 个方法
  CPG 故障函数：dxf_objects_read @ src/in_dxf.c:12260-12293 ✅
  入表函数: 162 个
  自检：已知崩溃行 src/in_dxf.c:12267 ✅ 已被 worklist 覆盖
```

**curl（应报"CPG 不覆盖"这类明确原因）**：

```
  CPG 文件覆盖：http2.c 有 3 个方法
[stderr] [stage5] ✗ cpg_missing_fault_fn: curl_5c55fe6df605.cpg 的 http2.c 里没有 h2_session_send
          （该文件只有 3 个方法：['<global>', 'curl_pushheader_bynum', 'curl_pushheader_byname']）。
          常见原因：故障函数是 static、CPG 建图时没解析到它。
          没有它就无法 fault_anchor，站点扫描永远看不到该函数 → 需重建 CPG。
```

```
$ python3 -m pytest tests -q
4 passed in 0.29s
```

**✅ 步骤 2 通过**：curl 现在报的是明确原因（且是指令期望的类别——"该 CPG 不可用，需重建"）。

### 失败与存疑

1. **R5 的一个结论是本轮推翻的**（见下"更正"）——我 R5 写"CPG 不覆盖 `lib/http2.c`"，
   实际是**覆盖的**（3 个方法），只是**不含那个 static 故障函数**。
2. **第一版 CPG 校验对 curl 不触发**：因为 `lib/http2.c` 确实在 `@@M` 里
   （`<global>` + 两个非 static 函数）。所以"查文件"不够，必须"查函数"。
3. **`cpg_missing_fault_fn` 的修复方向是"重建 CPG"**，本轮没做（指令明确 curl 不管）。

### ⚠️ 更正 R5 的一个错误结论

R5 报告与 `HANDOFF.md` 的「限制 5」里写：

> 预建 CPG **不覆盖 `lib/http2.c`**（3625 个方法里一条都没有）

**这是错的。** 本轮实测：

```
  @@M 行数: 3625
  含 http2 的文件: ['docs/examples/http2-download.c', ..., 'lib/http2.c']  共 6
  endswith("http2.c") 的: ['lib/http2.c']
  lib/http2.c 的方法数: 3
  前 8 个方法名: ['<global>', 'curl_pushheader_bynum', 'curl_pushheader_byname']
  含 h2_session_send 的: []
  LLVMFuzzerTestOneInput 在 dump 里: 0 次
```

**错因**：R5 用的是 `grep "@@M" cpg_dump.tsv | grep "http2" | head -6`，
`docs/examples/http2-*.c` 排在前面把 6 行占满，`lib/http2.c` 被截断没看到。

**正确的表述**：curl 的 CPG **覆盖了 `lib/http2.c`，但只解析出 3 个方法**——
`h2_session_send` 是 `static`，没被建图；而且 `LLVMFuzzerTestOneInput` **完全不在图里**，
所以 BFS 连根都没有。**两道关卡都是"解析粒度"问题，不是"文件覆盖"问题。**

（这条更正已写入 `HANDOFF.md` 的限制 5。）

---

### ⏸ 停止点：等用户确认

按指令在步骤 2 结束处停止。

| 验收项 | 结果 |
|---|---|
| libredwg worklist 函数数/列表/批次完全不变 | ✅ 162 → 162，`列表完全相同: True`，`批次相同: True` |
| libredwg 判定与站点不变 | ✅ llm01 `found`，`src/in_dxf.c:12284 → 12267`，`var=pair`，`branch=DXF`；其余 4 个 `not_found`；权重 1.0 |
| gpac worklist 出现故障函数 | ✅ `fault_anchor: 1`，入表 28 个（12 callgraph + 1 anchor + 15 neighbor） |
| gpac 自检通过 | ✅ `covers_fault_line: True` |
| 来源分布已打印 | ✅ `{'callgraph': 12, 'fault_anchor': 1, 'fault_neighbor': 15}` |
| curl 报明确原因 | ✅ `cpg_missing_fault_fn`（不是泛化错误） |
| pytest | ✅ 4 passed |

**请确认后进步骤 3（gpac 跑完整条流程）。**

---

## 步骤 3 · gpac 全流程

### 逐环节结果（按指令那张表）

| 环节 | 结果 |
|---|---|
| **fetch** | ✅ `commit_used = 319d44795db1`（**不是 fallback**，`commit_fallback: None`）；故障函数抽出 **147 行**；`free 调用点 5 处`：`L32 gf_free(cfg)` / `L60 gf_free(cfg->general_constraint_info)` / `L61 gf_free(cfg)` / `L106 gf_free(ar)` / `L137 gf_free(sl)` |
| **worklist** | ✅ 函数总数 **28**（`callgraph 12` + `fault_anchor 1` + `fault_neighbor 15`）；自检 `covers_fault_line: True`（`src/odf/descriptors.c:1403` 被覆盖）；已打印"故障函数靠锚点入表、不在 depth≤2 闭包内" |
| **站点扫描** | ✅ 短名单 **28** 个函数，扫出 **1 处**「先释放后使用」：`gf_odf_vvc_cfg_read_bs`，`free_line 1400` → `use_line 1404`，`var=ar`，`use.kind=same_path`，`callee=gf_free`，`free_kind=direct_free` |
| **判据匹配** | ✅ **`uaf-llm01` 命中 1 个站点**（`sites_matched: 1`）。站点与 R4/R5 读源码确认的位置一致（`gf_free(ar)` → 读 `ar->type`）。`llm02–05` 全部 `not_found`（`rule_missing`，R5 已定的"表达不了"） |
| **证据链** | ✅ **六步全部 `complete`**：step1 `LLVMFuzzerTestOneInput` / step2 输入绑定 / step3 `gf_odf_vvc_cfg_read_bs:1294`+`gf_bs_read_*` / step4 `[1400, gf_free(ar);]` / step5 `[1400, gf_free(ar);]` / step6 `[1404, if (!valid \|\| ((ar->type != GF_VVC_NALU_DEC_PARAM) ...)]` |
| **plan** | ⛔ **未能运行**：`缺少 .../v2/candidate_findings.json`（`audit` 未跑，仓库里没有 `vuln_report.json`） |
| **生成 + 门禁** | ⛔ 未到 |

### 停在哪一步

两层，且**都不在判据层**：

**阻塞 1 · `input_branch()` 是写死的 libredwg 文件前缀表**

```python
def input_branch(rel, src_cache):
    if rel.startswith("src/in_dxf"):    return {"branch": "DXF", ...}
    if rel.startswith("src/in_json"):   return {"branch": "JSON", ...}
    if rel.startswith("src/decode") or rel.startswith("src/bits"): return {"branch": "DWG", ...}
    if rel.startswith("src/out_") or rel.startswith("src/encode"): return {"branch": "OUTPUT", ...}
    return {"branch": "UNKNOWN", "entry": None, "magic": None}
```

gpac 的站点在 `src/odf/descriptors.c` → 匹配不上任何分支 → `branch = UNKNOWN` →
`build_action()` 的 `ok = all(step.complete) and branch != "UNKNOWN"` 为假 →
`status = blocked`、`evidence_grade = blocked`、`blockers = ["输入分支未知"]`。

**这是 libredwg 专属的硬编码**，正是任务书 B0 里"把写死的项目常量泛化成通用规则"那一类。
但泛化要求"从 harness 的分流逻辑自动推导"，而——

**阻塞 2 · gpac 的 harness 是空的**

```
harness: {"dir": "harness", "marker": "LLVMFuzzerTestOneInput", "files": [], "definition_files": [], "fuzz_target_name": "fuzz_parse"}
validation.harness_present: false
$ ls projects/ARVO-42518828/harness/     → 空目录
```

`LLVMFuzzerTestOneInput` 不在 gpac 自己的仓库里（在 OSS-Fuzz 的 `projects/gpac/`），
所以 `fetch_harness` 拿不到，`input_format` 也退化成 `{"format": "raw_bytes", "evidence": "no seed"}`，
`target_surface.validation.field_mapping_complete = False`（`locator_present: False`）。

**→ 没有 harness 就没有"输入怎么分流"的依据，`input_branch` 无法泛化。**

### 途中修的一处**通用扫描器缺陷**（不是判据）

**现象**：第一版跑 gpac 时 `原语 0` —— 扫出 0 个「先释放后使用」，尽管
`L1400 gf_free(ar);` → `L1404 ar->type` 明明存在。

**根因**：`wrapper_frees_param()` 要判断"被调函数是不是真的释放了这个指针"，
它的正则是 `\bfree\s*\(...\)`（**小写、大小写敏感**）。而 gpac 的 `gf_free` 是：

```c
void gf_free(void *ptr)
{
	FREE(ptr);      /* ← 大写宏，正则匹配不到 */
}
```

→ 被误判成"只释放成员的包装函数" → `scan_sites` 里 `if not wrapper_frees_param(...): continue`
把**真站点丢掉**。

**修法**：正则加 `re.I`（大小写不敏感）。

**落盘前先做了对照测量**（在内存里打补丁，不改文件）：

| 项目 | 原样 | 大小写不敏感 |
|---|---|---|
| gpac | 站点 **0**，命中 llm01 **0** | 站点 **1**，命中 **1** = `gf_odf_vvc_cfg_read_bs 1400→1404 (same_path)` |
| libredwg | 站点 4，命中 4 | 站点 **4**，命中 **4**（不变） |

**判定这是通用缺陷修复而非"为 gpac 调参"的理由**：
1. 它不是判据（不在 `applicability_rules.json`、不在 `match_rule`/`classify`）；
2. 它不针对 gpac：任何用大写 `FREE()` / `Free()` 宏包装释放的项目都受益；
3. **libredwg 的 4 个站点与判定完全不变**（上面的测量）；
4. 它修的是"这个调用到底算不算释放"这个**正确性**问题，与"这个站点像不像 UAF"无关。

**如果你认为它越界，回滚命令**：
```bash
cp /tmp/r6_s5_4_analyze.BEFORE pipeline/s5_4_analyze.py
```
（回滚后 gpac 会退回 `原语 0 / not_found`。）

### 失败与存疑

1. **`--depth` 对 gpac 无效**：`--depth 3/4` 时打印仍是 `depth=2`、闭包仍是 12 个。Hmm，见 R5 已记录；本轮未深查。
2. **`fetch_harness` 对 gpac 完全失败**（`files: []`）。这直接影响 `input_format` 与
   `field_mapping_complete`，是"输入分支未知"的上游原因。
3. **`plan` 连运行都运行不了**（缺 `candidate_findings.json`）。而 `candidate_findings` 需要
   `audit` 或 `vuln_report.json`；gpac 没跑过 audit。**即使跑 plan，llm01 也是 `blocked`，
   所以 plan 必然是 `blocked`**（`main_plan` 只把 `status == "found"` 的算作有落点）。
4. **行号差 1**：扫描器报 `free_line 1400 / use_line 1404`，R4/R5 读源码时记的是 `1399 / 1403`。
   同一处语句，`git show` 与工作区文件的行号基准差 1。**不影响判定**，但引用时要注意。

### 这一步的真实价值

**跨项目验证的核心问题在这一步被回答了**：

> R5 改好的结构判据 `{use_kind:[loop_back, same_path], free_kind:direct_free, ...}`
> **在训练集之外的项目（gpac）上命中了真实站点**，而且命中的正是人工读源码确认的那一处
> （`gf_free(ar)` → `ar->type`）。**libredwg 的结果一字不变。**

剩下的阻塞（`input_branch` 硬编码 + 没有 harness）**都是 libredwg 专属的管道**，
不是特征层。所以可以说：

> **特征（判据）层已经能跨项目工作；卡住的是"把站点变成算子"的那一段管道，
> 它还是按 libredwg 的 DXF 文本记录写的。**

---

## 汇总

### 三步结论各一句话

| 步骤 | 结论 |
|---|---|
| **1 · 故障函数入表** | ✅ 成立。`fault_anchor` + `fault_neighbor`（**仅在锚点真正补位时**）让 gpac 的 worklist 从 12 → **28** 个函数且自检通过；**libredwg 162 → 162、列表与批次完全相同** |
| **2 · fallback 硬失败 + CPG 校验** | ✅ 成立。pin 缺失 → 先 fetch、仍缺则 `SystemExit`（不再静默退回 HEAD）；CPG 校验查**故障函数**而不是文件；curl 现在报 `cpg_missing_fault_fn` |
| **3 · gpac 全流程** | 🟡 **走到 `blocked`**。判据层跨项目成功（llm01 命中 `gf_odf_vvc_cfg_read_bs` `gf_free(ar)`@1400 → `ar->type`@1404，六步证据链全 complete），卡在 `input_branch()` 的 libredwg 硬编码 + gpac 没有 harness |

### gpac 这条路走到了哪一步，下一个阻塞是什么

**走到了**：`fetch → worklist → 站点扫描 → 判据匹配 → 证据链`，**六步证据链全部 `complete`**。

**卡在**：`build_action()` 的 `branch != "UNKNOWN"` 这一条。`input_branch()` 是写死的
libredwg 文件前缀表，gpac 的 `src/odf/descriptors.c` 匹配不上。

**下一个阻塞（按修复顺序）**：

| 顺序 | 阻塞 | 性质 | 能不能做 |
|---|---|---|---|
| ① | **gpac 的 `harness/` 是空的**（`LLVMFuzzerTestOneInput` 在 OSS-Fuzz 的 `projects/gpac/`，不在 gpac 仓库） | 环境工作 | ✅ 可以从 OSS-Fuzz 仓库取 `*_fuzzer.cc` 放进 `harness/`，但这属于"取外部源码"，要先确认允许 |
| ② | **`input_branch()` 是 libredwg 硬编码** | 有条件允许（B0：必须从 harness 分流逻辑自动推导） | ⚠️ 必须先有 ①，否则没有推导依据 |
| ③ | **`plan` 缺 `candidate_findings.json`**（没跑 audit） | 环境工作 | ⚠️ audit 要调 LLM（162 批），很贵；或用 `mech`（机械规则，0 LLM）先产出一版 |
| ④ | `validate()` 的 `field_mapping_complete = False`（`locator_present: False`） | 依赖 ① | ⚠️ 无 harness 时 `input_format` 只能是 `raw_bytes` |

**结论**：`fetch → worklist → 扫描 → 判据 → 证据链` 这五段已经**在第二个项目上跑通**；
剩下的是"站点 → 算子"那一段管道，它目前只会 DXF 文本记录。

### `HANDOFF.md` 改了哪几处（改动内容原文）

只改「限制 5」的后半段（原 `### 5.3` / `### 5.4` 两节 → 新的 `### 5.3`–`### 5.5` 三节）。
完整 diff：

```diff
@@ -85,32 +85,60 @@
 这不是模型偷懒——我在步骤 1 独立核对词表时就发现 `cross_function` **算不出来**。
 **所以"跨函数"是扫描器的能力边界，不是判据设计的选择。**
 
-### 5.3 真正的下一个瓶颈：`audit_worklist` 的闭包走不到故障函数
+### 5.3 gpac 已经走到 `blocked`：**判据层跨项目成功，卡在管道**
 
-R4 说的"第二个项目跑不了"这句话，本轮要**改成分层的**：
+R6 让 gpac（`ARVO-42518828`，pin `319d44795db1`）走到了站点扫描与判据匹配：
 
-| 层 | curl（`ARVO-42508326`） | gpac（`ARVO-42518828`） |
-|---|---|---|
-| fetch 源码 | ✅ 修了两个环境 bug 后成功（正确 pin） | ✅ 成功（正确 pin） |
-| 故障函数的 free 调用点 | **0 处**（生命周期 bug，`nghttp2_session_del` 在别处） | **5 处**（含 `gf_free(ar)`，同函数 `ar->type` UAF） |
-| 预建 CPG 覆盖故障文件 | ❌ **不覆盖 `lib/http2.c`**（3625 个方法里一条都没有） | ✅ 覆盖 `src/odf/descriptors.c`（30139 个方法，故障函数在 `@@M` 里） |
-| `audit_worklist` 闭包 | 0 个函数 → 自检"清单不可信" | **12 个函数，全是 `isomedia`/`utils`，不含故障函数** → 自检"清单不可信" |
-| 能否走到站点扫描 | ❌ | ❌ |
-
-**结论**：`fetch` 之后的两道关卡——**CPG 覆盖面**与 **worklist 闭包根**
-（从 `LLVMFuzzerTestOneInput` 展开 depth≤2）——在第二个项目上双双失效。
-gpac 的故障函数**在 CPG 里**、也**有同函数 free→use**，但闭包里没有它，所以站点扫描器永远看不到。
-
-### 5.4 对"跨项目验证"的准确表述
-
-**不能说"特征迁移不了"，也不能说"迁移成功了"。** 准确说法是：
-
-> 适用性判据的"名单化"问题已经修好（步骤 1–3 有 diff 与复现证据）；
-> 但跨项目验证在**更早的一层**就被挡住了——`audit_worklist` 的调用图闭包没能覆盖故障函数。
-> 所以在拿到 curl / gpac 的站点评分之前，**"特征能否迁移"这个问题还没有被真正问到**。
-
-这一步的修复属于环境/工程工作（重建 CPG、改闭包根或按故障函数反向取闭包），
-不是判据问题；但它是下一步的**前置条件**。
+| 环节 | 结果 |
+|---|---|
+| fetch | ✅ 正确 pin（`commit_fallback: None`），故障函数 147 行，5 个 free 调用点 |
+| worklist | ✅ 28 个函数（`callgraph 12` + `fault_anchor 1` + `fault_neighbor 15`），自检覆盖故障行 |
+| 站点扫描 | ✅ **1 处**：`gf_odf_vvc_cfg_read_bs`，`gf_free(ar)` @1400 → 读 `ar->type` @1404 |
+| **判据匹配** | ✅ **`uaf-llm01` 命中**（`sites_matched: 1`）—— 命中的正是人工读源码确认的那一处 |
+| 证据链 | ✅ **六步全部 `complete`** |
+| plan | ⛔ 缺 `candidate_findings.json`（没跑 audit）；且 llm01 是 `blocked`，plan 必然 `blocked` |
+
+**所以准确表述变成**：
+
+> **特征（判据）层已经能跨项目工作**——R5 改好的结构判据在训练集之外的项目上命中了真实站点，
+> 且 libredwg 的结果一字不变。**卡住的是"把站点变成算子"的那一段管道，
+> 它还是按 libredwg 的 DXF 文本记录写的。**
+
+两个阻塞点（**都不在判据层**）：
+
+1. **`input_branch()` 是写死的 libredwg 文件前缀表**
+   （`src/in_dxf` / `src/in_json` / `src/decode` / `src/bits` / `src/out_*` / `src/encode`）。
+   gpac 的 `src/odf/descriptors.c` 匹配不上 → `branch = UNKNOWN` →
+   `build_action()` 判 `blocked`（`blockers = ["输入分支未知"]`）。
+2. **gpac 的 `harness/` 是空的**（`files: []`，`harness_present: false`）——
+   `LLVMFuzzerTestOneInput` 在 OSS-Fuzz 的 `projects/gpac/` 而不是 gpac 仓库，
+   所以 `fetch_harness` 拿不到、`input_format` 退化成 `raw_bytes`、
+   `field_mapping_complete = False`（`locator_present: False`）。
+   **没有 harness 就没有"输入怎么分流"的依据，`input_branch` 也就无法按 B0 的要求泛化。**
+
+### 5.4 更正 R5 的一处错误结论：curl 的 CPG 是**覆盖**的
+
+R5 写过「预建 CPG **不覆盖 `lib/http2.c`**（3625 个方法里一条都没有）」。**这是错的。**
+
+实测：`lib/http2.c` **在** dump 里，有 **3 个方法**（`<global>`、`curl_pushheader_bynum`、
+`curl_pushheader_byname`）。**错因**：R5 用 `grep "@@M" ... | grep http2 | head -6`，
+`docs/examples/http2-*.c` 排在前面把 6 行占满，把它截断了。
+
+**正确原因**（两道关卡都是"解析粒度"，不是"文件覆盖"）：
+- `h2_session_send` 是 **`static`** → 没被建图；
+- **`LLVMFuzzerTestOneInput` 完全不在图里** → BFS 连根都没有。
+
+所以 curl 现在的报错是 `cpg_missing_fault_fn`（**故障函数**不在图里），不是"文件不覆盖"。
+这也是 `find_cpg()` 的覆盖校验必须查**函数**、不能只查文件的原因。
+
+### 5.5 R6 修的两处通用缺陷（都不是判据）
+
+1. **`wrapper_frees_param()` 大小写敏感**：gpac 的 `gf_free` 是
+   `void gf_free(void *ptr) { FREE(ptr); }` —— 大写宏 `FREE`，旧正则只认小写 `free`，
+   于是"真的释放了该指针"被误判成"只释放成员的包装"→ **真站点被丢弃**。
+   加 `re.I` 后 gpac 出 1 个站点、libredwg **仍是 4 个站点且判定不变**。
+   这不是判据、不针对 gpac、修的是"这个调用算不算释放"的正确性问题。
+2. **`_run()` 吞掉 `SystemExit` 的消息**：硬失败却不说原因。已改为打印到 stderr。
 
 ---
 
```

### 下一步建议

| 优先级 | 做什么 | 为什么 |
|---|---|---|
| **P0** | 把 gpac 的 fuzz harness 取进 `harness/`（OSS-Fuzz `projects/gpac/`） | 这是"输入分支"的唯一依据；没有它 `input_format` 只能 `raw_bytes`、`locator_present` 恒假 |
| **P0** | 有 harness 后，把 `input_branch()` 改成"从 harness 的分流逻辑自动推导"（B0 有条件允许） | 它是 gpac 从 `blocked` 变 `found` 的最后一道；**必须先有 P0-1** |
| P1 | 用 `mech`（0 LLM）先补一版 `candidate_findings.json`，让 `plan` 能跑 | 不用等 162 批 audit |
| P2 | 让 `scan_sites()` 支持跨函数站点 | 4 个特征仍判"表达不了"的根因 |
| P3 | 步骤 4（stage3 合并判据 + `reassigned_between` 接线） | 等 P2 |

### 本轮没有做的事（按指令）

- 没重跑路径 B 的 A/B（`reps_pathB_r3` 数据保留）
- 没动 R5 改好的判据（`applicability_rules.json` / `match_rule` / `classify` 零改动，已用 mtime 确认）
- 没重建 curl 的 CPG（curl 是真阴性）
- 没做覆盖率优化、DWG 策略、目录整理

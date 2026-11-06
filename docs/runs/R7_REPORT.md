# R7 报告

日期：2026-11-03
目标：让 gpac **自己**走到故障函数；把「判断输入格式」改通用；打通跨函数扫描。

> 本文是本轮全部产出。每完成一步追加一节，不覆盖前面内容。

---

## 步骤 1 · `--depth` 失效排查

### 做了什么

**根因（一处，两行代码）**：`pipeline/s5_1_main.py` 的直通分支

```python
args, extras = ap.parse_known_args()
...
if args.stage in PASSTHROUGH:
    argv = list(extras)          # ← 只有**未知**参数
```

`--depth` 是 `ap.add_argument("--depth", type=int, default=2)` 的**已知**参数，
被 argparse 吃进 `args.depth`，于是**不在 `extras` 里** → 直通时被丢弃。
下游 `main_worklist` 用自己的默认值 2，所以永远打印 `depth=2`。

**同一个 bug 还影响了 `--type` / `--feature` / `--default-weight`**（都是已知参数）。

**修法**：直通时转发**原始 argv**（去掉 stage token），并用 `strip_osv()` 摘掉
`--osv X` 后由调用方补回（避免重复）：

```python
argv = strip_osv([a for a in sys.argv[1:] if a != args.stage])
if args.stage == "fetch":
    argv = ([osv] if osv else []) + argv
elif osv:
    argv = ["--osv", osv] + argv
```

**验证 --depth 真的生效了**（gpac）：

```
  depth=2 → depth=2 调用图内用户定义函数: 12 个   来源分布 {'callgraph': 12, 'fault_anchor': 1, 'fault_neighbor': 15}
  depth=3 → depth=3 调用图内用户定义函数: 34 个   来源分布 {'callgraph': 34, 'fault_anchor': 1, 'fault_neighbor': 13}
  depth=4 → depth=4 调用图内用户定义函数: 98 个   来源分布 {'callgraph': 98, 'fault_anchor': 1, 'fault_neighbor': 11}
  depth=5 → depth=5 调用图内用户定义函数: 179 个  来源分布 {'callgraph': 179, 'fault_anchor': 1, 'fault_neighbor': 6}
```

### 各档 depth 数据表

**gpac（`ARVO-42518828`）**

| depth | 闭包函数数 | 入表函数数 | 含风险操作 | `fault_anchor` | 是否自然覆盖故障函数 |
|---:|---:|---:|---:|---:|:---:|
| 2 | 12 | 28 | 16 | 1 | ❌ |
| 3 | 34 | 48 | 23 | 1 | ❌ |
| 4 | 98 | 110 | 49 | 1 | ❌ |
| 5 | 179 | 186 | 91 | 1 | ❌ |

**`fault_anchor` 每一档都是 1 —— 加到 5 层仍然覆盖不到。**所以 depth 不是原因。

**libredwg（`ARVO-42494732`）**

| depth | 闭包函数数 | 入表函数数 | 含风险操作 | `fault_anchor` | 故障函数在闭包内 |
|---:|---:|---:|---:|---:|:---:|
| 2 | 162 | 162 | 127 | 0 | ✅（`dxf_objects_read`） |
| 3 | 333 | 333 | 249 | 0 | ✅ |
| 4 | 530 | 530 | 397 | 0 | ✅ |

### 最短调用链：**不存在**

在**完整**调用图（不限深度）上从 `LLVMFuzzerTestOneInput` 做 BFS：

```
  LLVMFuzzerTestOneInput 在图里: True   (fuzz_parse.c)
  从 harness 可达 984 个节点

  gf_odf_vvc_cfg_read_bs         可达=False   调用者=['VVC_DuplicateConfig', 'gf_odf_vvc_cfg_read', 'vvcc_box_read']
  vvcc_box_read                  可达=False   调用者=[]          ← 图里一个调用者都没有
  gf_odf_vvc_cfg_read            可达=False   调用者=['cenc_enc_configure', 'dasher_get_rfc_6381_codec_name', ...]  ← 全是流媒体/inspect，不是解析路径
  VVC_DuplicateConfig            可达=False   调用者=['gf_isom_vvc_config_get', 'gf_isom_vvc_config_new', ...]
  gf_isom_box_parse              可达=True
  gf_isom_box_parse_ex           可达=True

  ❌ 在完整调用图上从 LLVMFuzzerTestOneInput 也到不了 gf_odf_vvc_cfg_read_bs（可达节点 984 个）
```

**为什么**：`vvcc_box_read` 在 CPG 里**没有任何调用者** —— 它是通过 box 类型**注册表里的函数指针**
被调用的。源码证据：

```
src/isomedia/box_funcs.c:1893:    return a->registry->read_fn(a, bs);
```

**→ 故障函数经函数指针/分派表调用，静态调用图里根本没有这条边。
任何 depth 都到不了，不是深度问题。**

这是比"depth 不够"严重得多的结论：**ISOM/容器类格式（gpac、MP4 系）大量用
"box 类型 → read_fn 指针"的分派，Joern 的静态调用图建不出这条边。**
所以"从 fuzz target 调用的 API 出发自己找崩溃"这条路，对**分派表架构的解析器**
在**调用图这一层**就断了。

### libredwg 回归

```
  入表函数: 162 个    来源分布: {'callgraph': 162}
  故障函数 dxf_objects_read 已在 depth<=2 闭包内（无需锚点）
  自检：已知崩溃行 src/in_dxf.c:12267 ✅ 已被 worklist 覆盖
  ✅ uaf-llm01   found      短名单 162 / 原语 4 / 支持 4
  权重合计: default 0.5 + 1×0.5 = 1.0
```

**完全不变。** ✅

### 失败与存疑

1. **`--depth` 的 bug 是真的、已修，但它不是 gpac 需要锚点的原因。** 两件事必须分开说——
   R5/R6 把"depth 不生效"记成疑点是对的，但它和"gpac 够不到故障函数"是**两个独立问题**。
2. **`fault_neighbor` 的数量随 depth 递减**（15→13→11→6）：闭包越大，邻居越可能已经在闭包里。
   这是合理的，但也说明"邻居"这个补位策略和 depth 有耦合。
3. **cpag 的 `gf_odf_vvc_cfg_read` 调用者全是流媒体/inspect 路径**——说明即使有别的入口
   （非 fuzz 路径）能到故障函数，也不是 harness 走的那条。

---

## 步骤 2 · `fault_anchor` 降级为诊断开关

### 做了什么

1. `main_worklist()` 新增 `--fault-anchor`，**默认关闭**；锚点与邻居的追加整块受它控制。
2. 启用时打印大字警告：

   ```
   !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
   ⚠️  fault_anchor 已启用：故障函数是被直接塞进清单的，**不是流程自己找到的**。
       此次结果不能用于论证「能在新项目上自主发现站点」。
   !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
   ```

3. `audit_worklist.json` 的 `_meta` 记 `fault_anchor_enabled: true/false`；
   **下游继承**：`target_surface.json` 的 `validation` 与 `feature_pipeline.json` 顶层
   都写入 `fault_anchor_enabled` + `fault_fn_in_closure`。
4. **自检不覆盖故障行 → 硬停**（原来是打印一句"清单不可信"然后把不可信的清单写出去）：

   ```
   worklist_does_not_cover_fault: 清单没有覆盖已知崩溃行 src/odf/descriptors.c:1403。
     从 LLVMFuzzerTestOneInput 展开 depth<=2 得到 12 个函数，够不到故障函数。
     可能原因：
       ① 故障函数经函数指针/分派表调用（静态调用图没有这条边）——gpac 实测就是这种；
       ② depth 不够（--depth N 调深；v7 起该参数才真正生效）；
       ③ harness 入口不在 CPG 里。
     人工排查可加 --fault-anchor（会打印醒目警告，结果不能用于论证自主发现）。
   ```

5. 顺手修：`anchor_in_closure` 原来被算在开关块**里面**，默认关闭时是 `None`，
   导致 libredwg 打印出"既不在闭包里，也没能锚定"这种**错误**消息。改为**永远计算**
   （它是事实，与开关无关）。

### 默认关闭下 gpac 能否自己走到

**不能。**

```
  ⚠️ 故障函数 gf_odf_vvc_cfg_read_bs 不在 depth<=2 闭包里（未启用 --fault-anchor；
     这正是「流程没能自己走到它」的情况）
  入表函数（不过滤，仅排序）: 12 个，其中含风险操作 5 个
  自检：已知崩溃行 src/odf/descriptors.c:1403 ❌ 未被覆盖（清单不可信！）
  exit=1                      ← 硬停，不再写出清单
```

加上 `--fault-anchor` 才能跑（`来源分布 {'callgraph': 12, 'fault_anchor': 1, 'fault_neighbor': 15}`，
自检覆盖，`_meta.fault_anchor_enabled = True`）。

### 继承标记的验证

| 项目 | 锚点 | `target_surface.validation.fault_anchor_enabled` | `feature_pipeline.fault_anchor_enabled` | `fault_fn_in_closure` |
|---|:---:|---:|---:|:---:|
| libredwg | 关（默认） | **False** | **False** | True |
| gpac | 开（`--fault-anchor`） | **True** | **True** | False |

**这样任何引用 `feature_pipeline.json` 的人，一眼就能看到这份结果是不是"喂过答案的"。**

libredwg 判定在默认关闭下完全不变：`llm01 found`、4 站点、权重 1.0、`pytest 4 passed`。

### 失败与存疑

1. **硬停会让 gpac 无法进入后续步骤**——这是**正确**行为，但也意味着步骤 3/4 若要跑 gpac，
   必须显式加 `--fault-anchor`，并在报告里注明"喂过答案"。
2. **`_meta` 之外没有强制约束**：下游只是"继承标记"，没有在代码层面拒绝使用带标记的结果。
   本轮按指令只做继承，不做强制。
3. 主结论重新表述（供汇总引用）：
   **gpac 目前是"喂了答案的"**——`fault_fn_in_closure = False`，故障函数靠 `--fault-anchor` 入表。

---

### ⏸ 停止点：等用户确认（步骤 2 出口）

| 验收项 | 结果 |
|---|---|
| `--depth` 修好且生效 | ✅ 12 → 34 → 98 → 179 |
| gpac 某档 depth 能自然覆盖故障函数 | ❌ **不能，且原因不是深度**：`vvcc_box_read` 在图里零调用者（函数指针分派，`box_funcs.c:1893`） |
| 最短调用链 | ❌ **不存在**（完整图上 984 个可达节点里没有它） |
| libredwg depth 2 结果完全不变 | ✅ 162 个函数、llm01 found、4 站点、权重 1.0 |
| `fault_anchor` 默认关闭 | ✅ |
| 默认关闭下 gpac 停住 | ✅ 硬停 exit=1，报"清单不可信" |
| 标记下游继承 | ✅ `target_surface` / `feature_pipeline` 都有 |
| pytest | ✅ 4 passed |

**请确认后进步骤 3（harness + `input_branch` 泛化）。**

---

## 步骤 3 · harness + `input_branch` 泛化

### 做了什么

#### 3.1 取 harness —— 它不在 OSS-Fuzz，在 gpac 的 **submodule** 里

`fetch_harness` 用 `git grep LLVMFuzzerTestOneInput <commit>` 在项目仓库里找。gpac 返回空。

**逐层排查**：

| 检查 | 结果 |
|---|---|
| pin `319d44795db1` 里有 `fuzz` 路径吗 | **0 个**（`git ls-tree -r` 只 2003 个文件） |
| `origin/master` / master 呢 | 也是 0 |
| GitHub tree API（master, recursive） | 1453 个文件，**0 个含 fuzz** |
| OSS-Fuzz `projects/gpac/` | 只有 `Dockerfile` / `build.sh` / `project.yaml`，**无 fuzz target** |
| OSS-Fuzz `build.sh` 里 fuzz target 从哪来 | `find $SRC/gpac/testsuite/oss-fuzzers -name "fuzz_*.c"` |
| gpac 仓库的 `testsuite` | **是 submodule** → `https://github.com/gpac/testsuite.git` |

→ harness 在子模块里。`git grep` 不进入未初始化的 submodule，所以搜不到。

**取到**：`gpac/testsuite@master:oss-fuzzers/fuzz_parse.c`（1518 字节），放到
`projects/ARVO-42518828/harness/fuzz_parse.c`。**记入 `INTERVENTIONS.md` 的环境工作类。**

gpac 的 harness 长这样（关键部分）：

```c
int LLVMFuzzerTestOneInput(const uint8_t *data, size_t size) {
    if (size < 8 || size > 65536) return 0;
    ... 写 /tmp/libfuzzer.<pid> ...
    GF_ISOFile *movie = gf_isom_open_file(filename, GF_ISOM_OPEN_READ_DUMP, NULL);
    if (movie != NULL) { ... gf_isom_get_track_count / gf_isom_get_decoder_config ... }
    gf_isom_close(movie);
}
```

**它是单一入口、没有按输入内容分流**——正是指令里"只有一个入口、没有格式判别"的情况。

#### 3.2 `fetch_harness` 的两处修改

1. **预置 harness 优先**：如果 `harness/` 里已有含 `LLVMFuzzerTestOneInput` **定义**的文件，
   直接用（返回 `source: "preplaced"`）。否则像 gpac 这种"harness 在别的仓库"的情况，
   每次 `fetch` 都会把人工放好的文件当成不存在。
2. **搜不到就硬失败**：`SystemExit("harness_not_found: …")`，并读 `.gitmodules`
   把 submodule URL 列出来（"harness 可能在其中"）。原来静默留一个空目录，
   导致 `input_format` 悄悄退化成 `raw_bytes`。

#### 3.3 `input_branch()` 泛化

旧实现是写死的 libredwg 路径前缀表。新实现（`derive_format_dispatch` + `input_branch`）：

1. `_strip_if0()` 剥掉 `#if 0 … #endif`（支持嵌套）；
2. `_func_body()` 抽 `LLVMFuzzerTestOneInput` 的 `{ }` 体；**配平失败时回退到"下一个列 0 的 `}`"**
   （libredwg 的 harness 全文 `{` 20 个、`}` 19 个，配不平）；
3. 逐行找**对用户定义函数**的调用（只认 CPG 里存在的、名字含 `read/parse/decode/load/open/from/import`
   的），并**往回找最近的 `if` / `else if` / `else`** 作为守卫；
4. 从守卫条件里抽**字符字面量**拼成 magic（`chain[0]=='A' && chain[1]=='C'` → `"AC"`）；
5. **分支名从入口函数名推导**：去掉通用动词（`read/open/parse/file/data/…`）后取最后一个 token 大写。
   `dwg_read_dxf` → `DXF`；`dwg_read_json` → `JSON`；`dwg_decode` → `DWG`；`gf_isom_open_file` → `ISOM`；
6. 对每个入口在 CPG 上做 BFS，记下**每个可达函数的距离**；
7. `input_branch(rel, fn)`：先按**站点函数**在哪个入口的可达集合里、取**最短距离**；
   没有就退到"只有一条分支"；再退到"按文件归属"；都不行才 `UNKNOWN` 并写清原因。

**全程没有出现任何项目专属的路径或函数名。**

### 推导出的分支映射

**libredwg（`ARVO-42494732`）**

```
  输入分支推导：3 个
    DWG        entry=dwg_decode                       magic='AC'     可达文件 8 个
    JSON       entry=dwg_read_json                    magic='{'      可达文件 13 个
    DXF        entry=dwg_read_dxf                     magic=None     可达文件 13 个
```

**gpac（`ARVO-42518828`）**

```
  输入分支推导：2 个
    ISOM       entry=gf_isom_open_file                magic=None     可达文件 45 个
    CONFIG     entry=gf_isom_get_decoder_config       magic=None     可达文件 42 个
```

### libredwg 回归（唯一安全网）

| 项 | 改前（硬编码表） | 改后（harness 推导） | 一致 |
|---|---|---|---|
| `branch` | `DXF` | **`DXF`** | ✅ |
| `entry` | `dwg_read_dxf` | **`dwg_read_dxf`** | ✅ |
| `magic` | `非 'AC'、非 '{'` | `其余（非 'AC'、非 '{'）` | ✅ 等价 |
| site | `src/in_dxf.c:12284 → 12267`，`var=pair` | 同 | ✅ |
| `evidence_grade` | `proven` | `proven` | ✅ |
| 5 个特征状态 | `found, not_found×4` | 同 | ✅ |
| 权重 | `0.5 + 1×0.5 = 1.0` | 同 | ✅ |
| `fault_anchor_enabled` | — | `False`（libredwg 不依赖锚点） | ✅ |

新增的 `via` 字段还顺带解释了判定依据：
`"via": "function dxf_objects_read @ distance 1"`。

### gpac 结果

```
  ✅ uaf-llm01   found      短名单 28 / 原语 1 / 支持 1
        site: src/odf/descriptors.c:1400 → 1404  var=ar  branch=ISOM
  ❌ uaf-llm02/03/04/05   not_found（rule_missing）
  权重: default 0.5 + 1×0.5 = 1.0
```

**`build_action()` 的 `status` 从 `blocked` 变成 `found`**（`evidence_grade: proven`）。

但分支判定是**靠文件兜底**的，产物里已如实标注：

```json
{"branch": "ISOM", "entry": "gf_isom_open_file",
 "magic": "（无格式判别条件）", "via": "file", "ambiguous": ["ISOM", "CONFIG"]}
```

原因：`gf_odf_vvc_cfg_read_bs` 经**函数指针**被调用（步骤 1 已查明），
两个入口的**静态**可达集都到不了它（实测距离都是 `None`），所以只能按"文件归属"判；
而 `src/odf/descriptors.c` **同时**在 ISOM 与 CONFIG 两个分支的可达文件里 → 取**源码顺序最早**的那个（ISOM）。

### 失败与存疑

1. **分支推导会"过度切分"**：gpac 的 `gf_isom_get_decoder_config` 是**解析之后的处理**，
   不是输入格式分流，但因为它是入口函数、名字含 `get`… 不，含 `decoder`→`decode` 命中
   `ENTRY_VERBS` 的 `decode` → 被当成一个分支。**libredwg 没有这个问题**（三个分支都真带条件）。
   影响有限（按距离取最近的），但分支列表不纯。
2. **`ambiguous` 的消解靠"源码顺序最早"**，没有更强的依据。对 gpac 恰好正确
   （`gf_isom_open_file` 确实是主入口），但这是运气+合理性，不是证明。
3. **修 `_func_body` 时踩到的两个源文件问题**：
   - libredwg 的 `llvmfuzz.c` 全文 `{` 20 / `}` 19（`#if 0` / `#elif` / `#else` 段），配平必失败；
   - `strip_code()` 会把字符字面量 `'A'` 剥成 `''`，导致 magic 抽不出来。
     所以条件匹配必须用**原文**、不能用 `strip_code`。
4. **`fetch_harness` 的 `harness_not_found` 会打断 `fetch`**：这是设计（不要静默空目录），
   但意味着"harness 在 submodule"的项目必须先人工放文件。本轮已为 gpac 放好并记录来源。

---

### ⏸ 停止点：等用户确认（步骤 3 出口）

| 验收项 | 结果 |
|---|---|
| 从 OSS-Fuzz 取 harness | ❌ **它不在 OSS-Fuzz**；在 gpac 的 submodule `gpac/testsuite` 里，已取并落盘 |
| `fetch_harness` 改好（不静默空目录） | ✅ `harness_not_found` + submodule 提示 |
| `input_branch()` 从 harness 推导、无项目专属常量 | ✅ |
| libredwg 复现（branch/magic/site/权重） | ✅ 全项一致 |
| gpac 分支映射 + 站点落在哪 + status | ✅ 2 分支；站点落 `ISOM`（`via: file`，`ambiguous`）；`blocked → found` |
| pytest | ✅ 4 passed |

**请确认后进步骤 4（跨函数扫描，本轮最贵的一步）。**

---

## 步骤 4 · 跨函数站点扫描

### 做了什么

**1. 盘点已有能力（未重写）**：`pipeline/s5_3_audit.py` 里的 `Interproc` 类仍有
`callers()` / `callees()` / `field_uses()` 三个跨函数原语，`main_interproc` 也能按需 dump。
它们是**给 agent 用的工具**，不是批量扫描器，所以本轮没有复用它做批量枚举——
而是新增了一个**批量、可证明顺序**的形态（见下）。

**2. 新增 `scan_cross_function_sites()`**，实现的形态是：

> 函数 A 在 L 行释放了裸指针 V → **之后**（同一函数内，行号更大）调用 `G(V)` →
> G 的第一个形参 p 绑到 V → G 里读 `p->…` / `p.…` / `p[…]`。

**为什么这个形态能证明"释放先于使用"**：调用 `G(V)` 的**行号大于**释放行，所以释放先于调用，
调用先于 G 里的读。R4 记的"调用顺序相反"假阳性（`free_array_hdls` 在 `resolve_postponed_*` 之后才释放）
在行号顺序下直接过不了。
**为什么能证明"同一对象"**：实参就是被释放的那个变量，形参绑定它——不是"两个不同实例"。

站点产物新增 `use.kind = "cross_function"`，并记录
`use.in_function` / `use.via_param` / `use.call_line` / `use.call_code` 与三段 `path`
（free → call → use）。

**3. 六道守卫**（对着 R4 记的假阳性逐条设）：

| # | 守卫 | 对应 R4 的哪条假阳性 |
|---|---|---|
| 1 | `wrapper_frees_param()` 不通过就不算释放 | "只释放成员的包装"（`dwg_free_header_vars(dwg)`） |
| 2 | 释放后 `V = NULL/0` → break | 释放后立即置空（`bits.c:3032-3033`） |
| 3 | 释放后 `V = …` → break | 释放后立即重新赋值（`encode.c:1289-1290`） |
| 4 | 实参必须**整个**是 `V`（不能是 `V->field`） | 不同实例 / 字段误配 |
| 5 | 被调函数名含 `free/destroy/close/del/…` → 跳过 | 读发生在**释放助手内部**（`dxf_free_pair(pair)` 读 `pair->code`） |
| 6 | 被调函数体里直接 `free(p)` → 跳过 | 同上 |
| + | `#if 0 … #endif` 里的行一律跳过（`dead_lines()`） | `decode.c:3797-3808` 死代码 |

**4. 词表扩展**：`use_kind` 加 `cross_function`（`s4_abstract_features.py` 的 `RULE_VOCAB`
与 SYSTEM prompt 同步更新，并写明"目前只覆盖实参传递这一种跨函数形态"）。

### libredwg 回归 + 假阳性核对

**这一步的核对过程本身有两次"被数据打回来"**，都如实记录：

| 轮次 | 跨函数站点数 | 逐个核对结果 |
|---|---:|---|
| 第一版（只有守卫 1/2/3 + 死代码） | **15** | **全部假阳性**：14 个是"读发生在释放助手内部"（`dxf_free_pair(pair)` / `dwg_free_summaryinfo(dwg)` / `free_array_hdls(...)`）→ 加守卫 5/6 |
| 第二版（加守卫 5/6） | **6** | **仍全是假阳性**：`dwg_free_header_vars(dwg)` 被当成"释放了 dwg"——`wrapper_frees_param` 本来就是为排除它写的，但我的跨函数扫描**漏用了**（守卫 1 没加）→ 补上守卫 1 |
| 第三版（加守卫 1） | **0** | ✅ 与 R4 的独立结论一致（libredwg 的跨函数候选**全是假阳性**） |

**最终 libredwg 状态**：

```
  同函数站点（4 个，与改前完全一致）:
    dwg_read_dxf:12839→12842 (same_path)
    encode_unknown_as_dummy:1271→1272 (same_path)
    encode_unknown_as_dummy:1308→1313 (same_path)
    dxf_objects_read:12284→12267 (loop_back)   ← llm01 的站点，未变
  跨函数站点: 0
```

**gpac 同样归零**（第一版报了 3 个，逐个核对后全部是同一个正则 bug：`gf_list_add(cfg->param_array, ar)`
被当成"传了 `cfg`"。实参匹配 `&?VAR\b` 允许 `cfg` 后跟 `->`，改成必须跟 `,` 或 `)` 后 3 个全消失）。

### stage4 重跑结果（第二层验收）

`use_kind: cross_function` 可用之后重跑 `s4_abstract_features.py --all`：

**5 条判据全部产出，0 条 `rule_missing`**（R5/R6 时是 1 条可用 + 4 条 `rule_missing`）。

| feature | LLM 产出的规则 | 具体性 | libredwg 命中 | gpac 命中 |
|---|---|---|---:|---:|
| `uaf-llm01` | `use_kind:[loop_back,same_path], free_kind:direct_free` | 具体 | **4** | **1** |
| `uaf-llm02` | `use_kind:any, free_kind:any` | **恒真（空判据）** | 4 | 1 |
| `uaf-llm03` | `use_kind:[same_path,loop_back,cross_function,realloc_alias]`, `free_kind:[4 个值]` | **近乎恒真** | 4 | 1 |
| `uaf-llm04` | `use_kind:cross_function, free_kind:direct_free` | **具体、可 falsify** | **0** | **0** |
| `uaf-llm05` | `use_kind:[loop_back,same_path,cross_function], free_kind:direct_free` | 近乎恒真 | 4 | 1 |

**后果（必须记）**：libredwg 从 `found 1/5`（权重 `1×0.5`）变成
**`found 4/5`（权重 `4×0.125`）**，而**四个"命中"指向的是同一批 4 个站点**——
`llm02/03/05` 没有带来任何 llm01 看不到的东西，只是把 llm01 的权重从 50% 稀释到 12.5%。

### 失败与存疑

1. **`cross_function` 扫描器在 libredwg 与 gpac 上都是 0 命中**。所有候选都是假阳性，
   被守卫拒掉——这是**正确**的结果（R4 独立核过 libredwg 的跨函数候选全是假阳性），
   但也意味着**这个能力目前没有在一个真站点上兑现过**。
2. **LLM 的判据质量是这一轮最差的发现**：
   - `uaf-llm02` 直接给 `use_kind: any, free_kind: any` —— **恒真**，等价于"所有站点都算"；
   - `uaf-llm03` / `uaf-llm05` 把几乎整个词表都列进去 —— 近乎恒真；
   - 只有 `uaf-llm04` 给了具体、可证伪的判据（`use_kind: cross_function`），而它**两个项目都 0 命中**。
   
   **对比 R5 手工抽的那套**（`llm02: free_kind:[3 个 realloc 值]`、`llm03/04: name_regex`、
   `llm05: is_link_read:true`）——**手工版反而更具体**。
   所以"LLM 归纳比手写规则强"目前**没有正面证据**，反而有反例：
   **把词表放宽之后，模型倾向于选 `any` 来自保。**
3. **libredwg 的权重被稀释**（50% → 12.5%）。这不是 bug，是"4 个特征都判 found"的直接后果；
   但它让算子变差。**没有手工去改判据来阻止它**（那属于禁止类）。
4. **`uaf-llm05` 的判据触发了一次黑名单告警**：`项目信息泄漏: ['next']`
   （`next` 是样本里的标识符）。不致命，但说明 `applicability_rule.why` 里的自由文本
   仍可能带出标识符。
5. **守卫 4（实参必须整个是 V）是事后补的**：第一版用 `&?VAR\b`，把 `var->field` 当成传 `var`。
   这个 bug 让 gpac 产生 3 个假阳性、libredwg 也受影响。
6. **只支持"实参传递"一种跨函数形态**。结构体字段、全局变量、回调/函数指针这三种都没做。
   而 gpac 的故障函数恰恰是**经函数指针**被调用的——所以"跨函数"在 gpac 上从根上就看不见。

---

### ⏸ 步骤 4 出口

| 验收项 | 结果 |
|---|---|
| 第一层：libredwg 回归 | ✅ llm01 仍 `found`，站点 `src/in_dxf.c:12284 → 12267` |
| 第一层：新增跨函数站点逐个人工核对 | ✅ 15 → 6 → **0**，三轮全部核对为假阳性并补守卫 |
| 第二层：重跑 stage4，4 个特征能否产出判据 | ✅ **5/5 产出**（0 条 rule_missing） |
| 第二层：判据质量 | ❌ 2 条恒真/近乎恒真；只有 `llm04` 具体且可证伪，但两项目 0 命中 |
| pytest | ✅ 4 passed |

---

## 汇总

### 四步结论各一句话

| 步骤 | 结论 |
|---|---|
| **1 · `--depth` 排查** | ✅ **是一个真 bug**（`s5_1_main.py` 只转发 `extras`，`--depth`/`--type`/`--feature` 被入口吃掉），已修；但**它不是 gpac 需要锚点的原因**——故障函数经函数指针调用，静态调用图上不限深度也到不了 |
| **2 · 锚点降级** | ✅ `--fault-anchor` 默认关闭、启用时大字警告、`fault_anchor_enabled` 继承到 `target_surface` / `feature_pipeline`；默认关闭时 gpac 自检不过就**硬停**，不再写不可信清单 |
| **3 · harness + 分支泛化** | ✅ harness 在 gpac 的 **submodule** 里（不在 OSS-Fuzz），已取；`input_branch()` 改为**从 harness + 调用图推导**，libredwg 逐项复现（`DXF` + `其余（非 'AC'、非 '{'）'`），gpac `blocked → found` |
| **4 · 跨函数扫描** | 🟡 能力做出来了（可证明顺序的"实参传递"形态 + 6 道守卫），但**两个项目都 0 命中**；stage4 因此 5/5 都产出了判据，可 **2 条恒真、2 条近乎恒真**，只有 `llm04` 具体且可证伪——而它 0 命中 |

### gpac 现在走到哪一步：`found`，但**是喂了答案的**

```
uaf-llm01  found   site src/odf/descriptors.c:1400 → 1404  var=ar  branch=ISOM
权重 default 0.5 + 4×0.125 = 1.0
fault_anchor_enabled = True      ← 喂过答案
fault_fn_in_closure  = False     ← 不是流程自己走到的
```

**"自己走到的"和"喂了答案的"，界线很清楚**：
- 站点扫描、判据匹配、六步证据链、输入分支判定——**都是流程自己做的**；
- 但**"故障函数进入待扫描清单"这一步靠 `--fault-anchor`**。
  原因不是 depth 不够，而是 `vvcc_box_read` 在 CPG 里零调用者（box 注册表的函数指针）。

### 另外 4 个特征现在能不能表达，找到了什么 llm01 找不到的东西

**能表达**（5/5 产出判据，0 条 `rule_missing`），**但什么也没找到**：

| feature | 判据 | libredwg | gpac | 有没有找到 llm01 看不到的 |
|---|---|---:|---:|---|
| llm01 | 具体 | 4 | 1 | —（基准） |
| llm02 | `any/any`（恒真） | 4 | 1 | **没有**（同一批站点） |
| llm03 | 4×4 近乎恒真 | 4 | 1 | **没有** |
| llm04 | `cross_function`（具体） | **0** | **0** | **没有**（跨函数候选全是假阳性） |
| llm05 | 3×1 近乎恒真 | 4 | 1 | **没有** |

**所以答案是：放宽词表让模型"能表达"了，但表达出来的东西没有增量信息。**
而且是**负增量**——libredwg 的权重从 `1×0.5` 稀释到 `4×0.125`。

### `HANDOFF.md` 改了哪几处（改动内容原文）

改的是「限制 5」的 `### 5.3`–`### 5.5` 三节（旧的 5.3/5.4 被替换）。完整 diff：

```diff
@@ -85,60 +85,57 @@
 这不是模型偷懒——我在步骤 1 独立核对词表时就发现 `cross_function` **算不出来**。
 **所以"跨函数"是扫描器的能力边界，不是判据设计的选择。**
 
-### 5.3 gpac 已经走到 `blocked`：**判据层跨项目成功，卡在管道**
+### 5.3 gpac 已经走通到 `found`——但**是喂了答案的**
 
-R6 让 gpac（`ARVO-42518828`，pin `319d44795db1`）走到了站点扫描与判据匹配：
+R6 让 gpac 走到 `blocked`（`input_branch` = UNKNOWN）。R7 又往前推了三步：
 
 | 环节 | 结果 |
 |---|---|
-| fetch | ✅ 正确 pin（`commit_fallback: None`），故障函数 147 行，5 个 free 调用点 |
-| worklist | ✅ 28 个函数（`callgraph 12` + `fault_anchor 1` + `fault_neighbor 15`），自检覆盖故障行 |
-| 站点扫描 | ✅ **1 处**：`gf_odf_vvc_cfg_read_bs`，`gf_free(ar)` @1400 → 读 `ar->type` @1404 |
-| **判据匹配** | ✅ **`uaf-llm01` 命中**（`sites_matched: 1`）—— 命中的正是人工读源码确认的那一处 |
-| 证据链 | ✅ **六步全部 `complete`** |
-| plan | ⛔ 缺 `candidate_findings.json`（没跑 audit）；且 llm01 是 `blocked`，plan 必然 `blocked` |
-
-**所以准确表述变成**：
-
-> **特征（判据）层已经能跨项目工作**——R5 改好的结构判据在训练集之外的项目上命中了真实站点，
-> 且 libredwg 的结果一字不变。**卡住的是"把站点变成算子"的那一段管道，
-> 它还是按 libredwg 的 DXF 文本记录写的。**
-
-两个阻塞点（**都不在判据层**）：
-
-1. **`input_branch()` 是写死的 libredwg 文件前缀表**
-   （`src/in_dxf` / `src/in_json` / `src/decode` / `src/bits` / `src/out_*` / `src/encode`）。
-   gpac 的 `src/odf/descriptors.c` 匹配不上 → `branch = UNKNOWN` →
-   `build_action()` 判 `blocked`（`blockers = ["输入分支未知"]`）。
-2. **gpac 的 `harness/` 是空的**（`files: []`，`harness_present: false`）——
-   `LLVMFuzzerTestOneInput` 在 OSS-Fuzz 的 `projects/gpac/` 而不是 gpac 仓库，
-   所以 `fetch_harness` 拿不到、`input_format` 退化成 `raw_bytes`、
-   `field_mapping_complete = False`（`locator_present: False`）。
-   **没有 harness 就没有"输入怎么分流"的依据，`input_branch` 也就无法按 B0 的要求泛化。**
-
-### 5.4 更正 R5 的一处错误结论：curl 的 CPG 是**覆盖**的
-
-R5 写过「预建 CPG **不覆盖 `lib/http2.c`**（3625 个方法里一条都没有）」。**这是错的。**
-
-实测：`lib/http2.c` **在** dump 里，有 **3 个方法**（`<global>`、`curl_pushheader_bynum`、
-`curl_pushheader_byname`）。**错因**：R5 用 `grep "@@M" ... | grep http2 | head -6`，
-`docs/examples/http2-*.c` 排在前面把 6 行占满，把它截断了。
-
-**正确原因**（两道关卡都是"解析粒度"，不是"文件覆盖"）：
-- `h2_session_send` 是 **`static`** → 没被建图；
-- **`LLVMFuzzerTestOneInput` 完全不在图里** → BFS 连根都没有。
-
-所以 curl 现在的报错是 `cpg_missing_fault_fn`（**故障函数**不在图里），不是"文件不覆盖"。
-这也是 `find_cpg()` 的覆盖校验必须查**函数**、不能只查文件的原因。
-
-### 5.5 R6 修的两处通用缺陷（都不是判据）
-
-1. **`wrapper_frees_param()` 大小写敏感**：gpac 的 `gf_free` 是
-   `void gf_free(void *ptr) { FREE(ptr); }` —— 大写宏 `FREE`，旧正则只认小写 `free`，
-   于是"真的释放了该指针"被误判成"只释放成员的包装"→ **真站点被丢弃**。
-   加 `re.I` 后 gpac 出 1 个站点、libredwg **仍是 4 个站点且判定不变**。
-   这不是判据、不针对 gpac、修的是"这个调用算不算释放"的正确性问题。
-2. **`_run()` 吞掉 `SystemExit` 的消息**：硬失败却不说原因。已改为打印到 stderr。
+| `--depth` | **是个真 bug**：`s5_1_main.py` 只转发 `extras`，`--depth` 等已知参数被入口吃掉。修好后 gpac 闭包 12→34→98→179（depth 2/3/4/5） |
+| 但 depth **不是** gpac 需要锚点的原因 | `vvcc_box_read` 在 CPG 里**零调用者**——它经 box 注册表的**函数指针**被调用（`box_funcs.c:1893` `a->registry->read_fn(a, bs)`）。**静态调用图上从 `LLVMFuzzerTestOneInput` 出发（不限深度，984 个可达节点）根本到不了故障函数** |
+| `fault_anchor` | 已降级为 `--fault-anchor` 显式开关（默认关），启用时打大字警告；`fault_anchor_enabled` 继承到 `target_surface.json` / `feature_pipeline.json` |
+| harness | gpac 的 fuzz target **不在 OSS-Fuzz**，在 gpac 的 **submodule** `gpac/testsuite` 里（`oss-fuzzers/fuzz_parse.c`）。已取并落盘 |
+| `input_branch()` | 已从写死的 libredwg 路径前缀表 → **从 harness 源码 + CPG 调用图推导**。libredwg 推导出 `DWG/AC`、`JSON/{`、`DXF/默认`，站点判 `DXF`（**与硬编码版逐项一致**，含 magic 描述） |
+| gpac 的 status | `blocked` → **`found`**（`branch=ISOM`，`via: file`，`ambiguous: [ISOM, CONFIG]`） |
+
+**所以 gpac 现在是 `found`，但 `fault_anchor_enabled = True`、`fault_fn_in_closure = False`——
+故障函数是 `--fault-anchor` 塞进清单的，不是流程自己走到的。**
+
+### 5.4 R7 的核心结论：判据层放宽后，**LLM 反而更不具体**
+
+R7 给 `scan_sites()` 加了跨函数形态（`use_kind = cross_function`：
+A 里 `free(V)` → 之后调用 `G(V)` → G 里读形参，**行号顺序证明释放先于使用、实参证明同一对象**），
+并给 stage4 的词表加了 `cross_function`。
+
+结果：**5 条判据全部产出（0 条 `rule_missing`）**，但质量是：
+
+| feature | LLM 判据 | 具体性 |
+|---|---|---|
+| `uaf-llm01` | `use_kind:[loop_back,same_path], free_kind:direct_free` | 具体 ✅ |
+| `uaf-llm02` | `use_kind:any, free_kind:any` | **恒真（空判据）** ❌ |
+| `uaf-llm03` | 4 种 use_kind × 4 种 free_kind | 近乎恒真 ❌ |
+| `uaf-llm04` | `use_kind:cross_function, free_kind:direct_free` | **具体、可证伪** ✅ 但两项目 0 命中 |
+| `uaf-llm05` | 3 种 use_kind × direct_free | 近乎恒真 ❌ |
+
+**后果**：libredwg 从 `found 1/5`（`1×0.5`）变成 `found 4/5`（`4×0.125`），
+而四个"命中"指向**同一批 4 个站点**——llm02/03/05 没有找到任何 llm01 看不到的东西，
+只是把 llm01 的权重从 50% 稀释到 12.5%。
+
+**对比 R5 手工抽的那套**（`llm02: free_kind:[3 个 realloc 值]`、`llm05: is_link_read:true`…），
+**手工版反而更具体**。→ **"LLM 归纳比手写规则强"目前没有正面证据；
+把词表放宽之后，模型倾向于选 `any` 来自保。**
+
+### 5.5 跨函数扫描器目前 0 命中（这是正确的，但也是空的）
+
+libredwg 的跨函数候选：第一版 15 个、加守卫后 6 个、再补守卫后 **0 个**——
+三轮都逐个人工核对为假阳性（与 R4 的独立结论一致）。gpac 同样 0 个。
+
+6 道守卫（对着 R4 记的假阳性逐条设）：`wrapper_frees_param` 不算释放 / 释放后置空 /
+释放后重赋值 / 实参必须整个是 V / 被调函数是释放助手 / 被调函数体直接 free 了形参 /
+`#if 0` 死代码。
+
+**所以 `cross_function` 这个能力到今天为止，还没有在一个真站点上兑现过。**
+而且 gpac 的故障函数经**函数指针**被调用，本来就是"跨函数"从根上看不见的那种。
 
 ---
 
```

### 下一步建议

| 优先级 | 做什么 | 为什么 |
|---|---|---|
| **P0** | **让判据"可证伪"成为硬约束**：拒绝 `use_kind: any` + `free_kind: any` 这种恒真规则（至少要求规则能把一部分站点排除掉） | R7 实测：词表一放宽，模型就选 `any` 自保；现在是"5/5 都能表达"，但 3/5 是空话 |
| **P0** | 跨函数形态扩到**结构体字段 / 全局 / 回调**；尤其是**函数指针分派**（gpac 的 `registry->read_fn`） | 现在只支持实参传递，而真实项目里"跨函数"大量走字段和回调；gpac 的故障函数从根上就看不见 |
| P1 | 给 `scan_cross_function_sites()` 补上"被调函数是释放助手"之外的更多守卫，并用一个**已知真跨函数 UAF** 做正例回归 | 目前 0 命中，既可能是"确实没有"，也可能是"守卫过严"——这两种现在还分不开 |
| P2 | `uaf-llm05` 的 `why` 里带出了标识符 `next`（黑名单命中）；`why` 应该同样受黑名单约束 | 小的干净度问题 |
| P3 | 把 `fault_anchor` 的开关状态接进 `verification.json` / `mutator.json`，让"喂过答案"标记贯穿到最终产物 | 现在只到 `feature_pipeline` |

# 漏洞分析 · 总报告

---

## 0. 先回答：你的目的有没有被考虑进去

你的目的（原话拆解）：

> **G1** 用程序分析技术对**有漏洞的程序**做崩溃复现分析
> **G2** 观察**相同崩溃类型下**的不同程序，在分析过程中是否有某种**共性**
> **G3** 尽可能多地试**多种**程序分析方法
> **G4** 复现的程序也要**尽可能多**
> **G5** 以此提取共性
> **G6** 之后利用这个共性做一些处理（→ 结合 mutator 变异策略，让模型生成便于挖掘对应漏洞的 mutator）


---

## 1. 当前数据规模（全部实测）

```
已复现            166 条 / 11 个项目 / tier: strict 87 · medium 36 · loose 43
崩溃类型          heap-buffer-overflow 83 · unknown 23 · uninit-value 14 ·
                  global-buffer-overflow 12 · heap-UAF 9 · segv 5 · stack-overflow 5 ·
                  memcpy-param-overlap 3 · negative-size-param 3
项目分布          c-blosc2 61 · libavc 32 · hunspell 24 · unicorn 11 · pcre2 10 ·
                  libhevc 10 · libtsm 7 · espeak-ng 4 · md4c 3 · libwebp 3 · libspng 1

分析可用性        fixed_real（真修复 commit）  129/166 = 77.7%
                  故障点 file:line:col         159/166 = 95.8%
                  Shadow bytes 段              107/166 = 64.5%
                  M7 行内指令                   157/166 = 94.6%
                  M7 滤噪后真实内存操作          126/166 = 75.9%
                  S2 可分析（修复 diff）         119 条 / 7 项目（剔除 7 条无效 fixed_real）
```

⚠ **样本偏斜是全局性约束**：c-blosc2 占 **61/166 = 37%**。任何「共性」都必须排除它一个项目撑起来的可能（§3 就抓到一个这样的假共性）。

---

## 2. 试过的 17 种程序分析方法（G3）

### 2.1 静态分析（10 种）

| # | 方法 | 效果 | 实测依据 |
|---|---|---|---|
| 1 | **ELF/DWARF 普查**（pyelftools 数 DIE） | ✅ **性价比最高** | 103 CU / 82,329 DIE / 10,692 subprogram，但 **formal_parameter 0 · variable 0 · base_type 0 · structure_type 0** → 全部二进制是 `-gline-tables-only` → **一举否决整个变量级动态分析方向** |
| 2 | **Joern CPG**（`c2cpg` + 数据流查询） | ✅ **能区分漏洞版/修复版** | 见 §4.1。**但只在 1 个靶子上验证过** |
| 3 | **Semgrep 序列模式**（`pattern-not-inside`） | ✅ **能区分** | 漏洞版命中 1 / 修复版 0。⚠ 但硬编码了宏名 `NDLZ_UNEXPECT_CONDITIONAL`，跨项目需泛化 |
| 4 | **M7 故障指令提取**（llvm-objdump + DWARF 行号表） | ✅ **75.9% 有结果** | 一行 18 条指令 → 滤掉 ASAN shadow 检查 / SanitizerCoverage / cmplog 插桩 → 2 条真实内存操作 |
| 5 | 修复 diff **结构**归类（认形状+被比较量种类） | ✅ 119 条 / 7 项目 | 容量比较族 **59.7%**（§5.1） |
| 6 | 修复 diff **词法**归类（认变量名） | ⚠ **有项目偏见** | 在 3 个项目上给出 72.3%，但在 libavc 上 **0/27** —— 正则认死了 `destsize`/`frame->len`/`iend` |
| 7 | **Semgrep 污点模式** | ❌ **不能区分** | 两版**都**命中 1。原因查实：Semgrep 的 `pattern-sanitizers` 是**污点传播节点**语义，而修复是**控制流守卫**（`if (…) return`），不在污点路径上 → 结构上表达不了「缺少守卫」 |
| 8 | **cppcheck** | ❌ **沉默** | 靶子文件只输出 1 条 `toomanyconfigs` 提示 |
| 9 | **clang-tidy** | ❌ **沉默**（对靶子） | 报的是**另一个函数** `ndlz4_compress` 的内存泄漏 + `bugprone-easily-swappable-parameters`；11536 条 warning 里无一条指向故障点 |
| 10 | **Clang Static Analyzer**（clang 22，`--analyze`） | ❌ **沉默**（对靶子） | 同样只报内存泄漏 |

### 2.2 动态分析（7 种）

| # | 方法 | 效果 | 实测依据 |
|---|---|---|---|
| 11 | **Shadow bytes 段解析** | ✅ **64.5% 覆盖，新增一个可解释轴** | 故障地址落在哪种内存区：Heap left redzone 36 · Partially addressable 34 · Global redzone 7 · **Freed heap region 7** · Stack redzone 4。语义**从报告自带 legend 解析**（实测 107/107 都有，21 条映射），不硬编码 |
| 12 | **gdb 读相邻全局变量身份** | ⚠ **有存盘报告没有的新信息** | `48 bytes before global variable '.str.131' … is ascii string 'unhandled escape seq %u'`。未规模化 |
| 13 | **strace** | ⚠ 能跑、**无判别力** | 28 行轨迹（22 条 mmap/brk）。对内存越界不提供信息 |
| 14 | **gdb 断点读局部变量** | ❌ **不可能** | 断点精确命中（`__asan_report_load1` ← `vte_write_debug:514` ← `do_trans:1858`），寄存器可读，但 `info args` → **No symbol table info available**、`info locals` → **No locals**。4 条 × 4 项目全如此。根因见方法 1 |
| 15 | **BB 覆盖轨迹**（libFuzzer `-print_coverage=1`） | ❌ | 二进制**确有**插桩（`3103 inline 8-bit counters` + 3103 PC table），但 libFuzzer 在**进程退出时**才打印，崩溃输入让它提前终止 |
| 16 | **Valgrind** | ❌ **跑不起来** | `unhandled dwarf2 abbrev form code 0x25/0x1b/0x23` + `debuginfo reader: ensure_valid failed` → 退出码 1。**它的 DWARF 读取器不支持 DWARF5** |
| 17 | **ASAN_OPTIONS** 7 种组合（容器内实测） | ❌ **无新语义** | `malloc_context_size=30`（默认已是 30）、`detect_invalid_pointer_pairs=2`、`check_initialization_order=1:strict_init_order=1` → 输出**完全不变**（76 行 / 28 帧）；`print_stats=1` → 105 行（+Stats）；`symbolize=1:print_module_map=1` → 204 行（+模块映射）；`verbosity=1` → 314 行（更啰嗦，无新语义） |

### 2.3 三个「证明型」静态工具为什么集体沉默（结构性原因，不是工具缺陷）

靶子的漏洞是 `memset(op, 0, blockshape[0] * blockshape[1])`，而容量是**函数参数** `output_len`。
要证明越界，必须知道**调用方给 `output` 分配了多大** —— 这是**跨过程**信息。
cppcheck / clang-tidy / CSA 在单文件、库函数视角下**无法证明**，因此按设计沉默（它们只报能证明的）。

> **对本项目的直接含义**：找这类漏洞不能用「证明型」工具，要用「**模式 / 缺失检查型**」查询
> （Joern CPG 查询、Semgrep 序列模式、CodeQL 的 taint + missing-guard）。

---

## 3. 正面回答 G2：同一崩溃类型下、不同程序有共性吗？

用 **M7 的寻址方式**这一维做交叉（126 条有结果）。判据：某类型内**主导寻址方式**在多少个项目的分析结果里也占主导。

| 崩溃类型 | n | 项目数 | 主导寻址方式 | **与主导一致的项目** | 判定 |
|---|---|---|---|---|---|
| **use-of-uninitialized-value** | 13 | 4 | `(base)` 裸指针解引用 54% | **4/4** | ✅ **唯一全一致** |
| **heap-buffer-overflow** | 65 | **8** | `disp(base)` 62% | **5/8** | ⚠ 部分一致（c-blosc2 全 disp(base)、pcre2 主要 `(base)`、libwebp 是 base+idx） |
| unknown | 14 | 5 | `disp(base)` 64% | 2/5 | ❌ 不一致 |
| heap-use-after-free | 9 | 3 | `disp(base)` 78% | 1/3 | ❌ 不一致（且 5/9 是 c-blosc2） |
| **global-buffer-overflow** | 8 | 2 | `base+index` **88%** | 1/2 | ❌ **假共性**：**7/8 来自 libtsm** |
| stack-buffer-overflow | 4 | 2 | `(base)` 50% | 1/2 | ⓘ 样本太少 |

**结论**：在「寻址方式」这一维上，**共性只在 `use-of-uninitialized-value`（4/4）上成立**，
`heap-buffer-overflow` 部分成立（5/8），其余不成立。
`global-buffer-overflow` 的 88% 是**典型的项目假象** —— 这正是你一直担心的混淆，本轮又出现一次。

⚠ **这一维的效力限制**：M7 的「主导寻址方式」是对**同一源码行上多条真实内存指令**取众数
（平均 7.5 条/crash），本身有噪声；且 `func_range_unknown` 24 条（多为 C++ 项目，符号名匹配失败）。
→ **该结论是「未找到强共性」，不是「证明无共性」**。Joern 的结构特征维度还没做（§6）。

---

## 4. 唯一验证成功的两个方法，具体怎么工作的

### 4.1 Joern CPG（能区分漏洞版/修复版）

靶子 **OSV-2022-55**（c-blosc2，`plugins/codecs/ndlz/ndlz4x4.c:544`）。漏洞版与修复版只差 3 行：

```c
memcpy(&blockshape[0], ip, 4);        // ← blockshape 直接来自输入
memcpy(&blockshape[1], ip, 4);
eshape[0] = ((blockshape[0] + 3) / 4) * 4;
eshape[1] = ((blockshape[1] + 3) / 4) * 4;
+ if (NDLZ_UNEXPECT_CONDITIONAL(output_len < blockshape[0] * blockshape[1])) {   // ← 修复只加了这 3 行
+   return 0;
+ }
memset(op, 0, blockshape[0] * blockshape[1]);      // ← 故障点
```

同一组查询跑两版（CPG 由 `c2cpg` 建成：10/10 文件、7150 节点、148KB）：

| 查询 | 漏洞版 | 修复版 |
|---|---|---|
| 方法签名解析 | ✅ `int(uint8_t*,int32_t,uint8_t*,int32_t,uint8_t,blosc2_dparams*)` | ✅ |
| `output_len` 被引用次数 | 2 | **3** |
| **含 `output_len` 的比较数** | **0** | **1** |
| memset/memcpy sink | 16（含 `line=544 size=blockshape[0]*blockshape[1]`） | 16（同一 sink 移到 547） |
| **污点 `input` → memset 尺寸实参 可达** | **1** | 1 |
| **判决** | **HIT** | **MISS** ✅ |

**判别式**：`容量参数存在 ∧ 输入派生量到达写内存的尺寸实参 ∧ 该容量参数从未参与任何比较`。

⚠ 两个实测坑：① `reachableByFlows` 返回 **0 条路径**而 `reachableBy` 返回 **1** → 只用后者判决，
**不声称能给出完整污点路径**；② 对 **Traversal** 调 `.parameter`/`.call` 返回空，必须先 `.head` 取节点。

### 4.2 M7 故障指令提取（一行 18 条指令 → 2 条真实的）

`tsm-vte.c:514` 的完整反汇编（llvm-objdump，binutils 读不了 DWARF5）：

```
1f03e0: leaq   (%r14,%r13), %rdi          ← 地址计算（base+index）        ✅ 保留
1f03e4: movq   %rdi, %rax                 ← 无内存操作数                  滤除
1f03e7: shrq   $0x3, %rax                 ← ASAN shadow 偏移              滤除
1f03eb: movzbl 0x7fff8000(%rax), %eax     ← 读 shadow 字节                滤除
1f03f4: jne    0x1f04a1                   ← 分支（操作数是跳转目标非内存）  滤除
1f03fa: movzbl (%r14,%r13), %r12d         ← **真正的 1 字节载入**          ✅ 保留
1f0407: callq  __sanitizer_cov_trace_const_cmp1   ← cmplog 插桩           滤除
1f0411: incb   …<__sancov_cntrs+0x9e1>    ← 覆盖率计数器                  滤除
1f04ae: callq  __asan_report_load1        ← ASAN 报告调用                 滤除
```

留下的 `movzbl (%r14,%r13)` 与报告的 `READ of size 1` **吻合**，`__asan_report_load1` 变体也一致。

⚠ **一个反直觉的实测结论**：报告里的 `pc` **不是**出错访问，而是 `call __asan_report_*` 的
**返回地址**（实测定位到 `incb <__sancov_cntrs+0x9e4>`）。而且 **ASAN 在真正访问之前就拦截** →
「出错的那条指令」**根本没执行过**。这也是我放弃「pc 往前扫窗口」启发式的原因（两次都选错：
第一次选中覆盖率计数器，第二次选中栈重载 `movq -0x38(%rbp),%r15`，因为真地址计算在 0x1f03e0、
pc 在 0x1f04b3，中间隔着**向后跳转的循环**）。

---

## 5. 目前提取到的共性（G5）

### 5.1 唯一通过全部判据的共性 —— ⚠ 但来源偏离 G1

> **「一个从输入解析出的量（长度/尺寸、偏移、索引），在用于内存访问前，未与实际可用容量比较。」**

* 覆盖 **63→71/119 = 59.7%**（补样本后从 67.0% 降下来，说明原先有单项目成分）
* 出现在 **10 种崩溃类型**（3 种 ≥30%）、**7 个项目全部 33%–75%**
* 项目无关性：**H_rel = 1.302**（G.3 的「项目无关」基准区间内），q_proj = 0.018
* 逐项目：c-blosc2 75% · libavc 55% · unicorn 50% · hunspell 43% · pcre2 43% · libwebp 33% · libhevc 0%(n=2)

子族：**`size_vs_capacity` 60 条 / 5 项目**（最稳）· `index_vs_count` 20 条 / **5 项目** ·
`offset_vs_bound` 30 条但 **H_rel=2.05 判为项目特异**（hunspell 0/23、libwebp 0/3）

⚠ **这条共性是从「修复代码」提取的，不是从「漏洞程序」分析出来的** —— 即 G1 偏离的那条路。
它仍然有价值（修复 diff 是漏洞模式的直接证据），但**不满足你对 G1 的要求**。

### 5.2 漏洞程序本身的共性（符合 G1）—— 目前是**弱/负面**结果

* **寻址方式**：只有 `use-of-uninitialized-value` 做到 4/4 项目一致（§3）
* **访问宽度**：元素级（≤16B）占 **85.7%**（L1 全量 3,790 的 2,320 可测）、L2 独立测得 **72.9%**
  → 两层独立测量给出同一个 ~85:15 分裂（元素级 : 批量/变长），H_rel ≈ 1.0–1.3
* **调用深度**：harness→故障 ≥6 帧的占 **58.8%**（4 种类型 ≥30%，H_rel=1.01）
* **Shadow bytes 落区**：Heap left redzone 36 / Partially addressable 34 / Freed 7 / Global redzone 7

### 5.3 对 mutator 的可操作产出（G6 的输入，尚未落地）

现有 `mutator.c` 是 9 策略组合 + 手写常数（`WEIGHT={8,6,20,10,18,8,6,6,4}`、
`INTERESTING16` 15 个值、`pick16` 的 delta 族、`rnd()%3` 的自洽率）。按**跨项目证据强度**排序的缺口：

| 优先 | 缺什么 | 证据 |
|---|---|---|
| 1 | 让「声明长度/尺寸」超过实际数据或目标缓冲 | `size_vs_capacity` 60 条 / **5 项目** |
| 2 | 把计数/索引字段设到 ≥ 已知常量上界 | `index_vs_count` 20 条 / **5 项目** |
| 3 | **破坏 magic** | `magic_validate` 10 条 / 3 项目。现有 `M_HEADER` 只改 version/flags；且须在**序列化后**改字节（`parse()` 里 magic 不符会直接回退 `LLVMFuzzerMutate`） |
| 4 | 截到小于最小头长 | `min_input_len` 9 条（**仅 c-blosc2**）⚠ 单项目证据 |
| 5 | 偏移字段 + 截断容器 | `offset_vs_bound` 30 条但**项目特异**（H_rel=2.05）⚠ 曾被我错列为第 1 |
| 6 | 接近 INT32_MAX/INT64_MAX 的取值 | `overflow_guard` 2 条。但 `INTERESTING16` 上限 `0xFFFF` 且 `pick16` 会把 `v>0xFFFF` 钳回 → **结构上产生不了** |
| 新 | 让「已初始化」标志与真实状态脱钩 | `state_flag` 8 条 + libhevc 的 `init` 族；现有 9 策略**完全没有这一族** |

---

## 6. 三个结构性发现（决定后续该做什么）

**① 变量级动态分析对全部 166 个二进制不可能**
DWARF 只有行号表（0 参数 / 0 变量 / 0 类型）。要看变量值**必须用 `-g` 重编**。

**② `loc_offset`（越界距离）不能用来标定变异幅度**
批量级 17 条的 `loc_offset` **全是 0**，而实际访问宽度是 `201851904`、`3324313568` 量级 ——
因为 **ASAN 在第一个非法字节就报错**。它测的是「ASAN 首次检出位置」，不是「输入派生量错了多少」。
→ **要拿到那个量，只能重编**（`trace-cmp` 拿比较操作数 / MSAN origin tracking / 污点插桩）。

**③ 不变式在解析边界强制，不在访问点**
**22/65 = 33.8%** 的修复**没改故障点文件**：故障在 vendored `zstd_ddict.c:134`、修复在 `blosc2.c`/`frame.c`；
故障在 `blosc2.c`、修复在 `frame.c`。
→ Joern 查询**不能只在故障函数内找**，污点源在解析层、sink 在访问点，常跨文件甚至跨 vendored 库。

---

## 7. 尚未完成（按对你目标的重要性排序）

| 优先级 | 待做 | 属于 | 为什么重要 |
|---|---|---|---|
| **1** | **Joern 规模化**：对每条 crash 建 CPG、提结构特征（故障表达式是否源于参数 / 有无守卫 / 尺寸表达式形状），**再按崩溃类型分组看共性** | G1+G2+G5 | 这是唯一验证过「能区分漏洞版/修复版」的方法，但**只在 1 个靶子上试过**。不做完就无法回答 G2 |
| **2** | **继续扩复现**，且**按崩溃类型定向**（UAF 仅 9 条 / stack-overflow 仅 5 条，太少无法做同类型跨程序分析） | G4 | 现有 11 个项目里 4 个只有 1–3 条 |
| **3** | 补 `fixed_real` 剩余 37 条（21 条 not_located + 12 条真障碍 + 4 条其它）；并把已回填的 **64 条合并回复现记录表** | G5 | 目前回填结果只在 overlay 文件里，复现记录表未更新 |
| **4** | 重编类动态分析（`trace-cmp` / MSAN origin） | G1 | §6② 的盲区**只有这条路能填** |
| **5** | 用共性改 mutator + 跑 T5 那套 A/B 对照 | G6 | 最终目的，但要等 1–2 有结论 |

**待检验假设**（🅗，证据不足）：`use-of-uninitialized-value` 类崩溃的修复是「加初始化」而非「加边界检查」
→ **崩溃类型 ↔ 修复族可能存在映射**。若成立，mutator 可按崩溃类型选策略。
当前只有 libhevc 1 条有效样本（`WORD32 luma_nbr_flags_4x4[4] = { 0 };`），**远不足以成立**。
**证伪条件**：扩样本后若 uninit 类里「加边界检查」的比例 ≥「加初始化」，则该假设被推翻。

---

## 8. 复现命令与产物

```bash
cd /root/gyx/mutator_create/pattern_analysis

# 自测（4 套，全绿；已知答案 + 合成正负对照）
python3 s1_extract.py    --selftest    # 13 项：6 种 is located 措辞 + 16 种错误行 + shadow legend + 全量一致性
python3 s1_analyze.py    --selftest    # 11 项：7 合成正负对照（project ⊥ crash_type）+ 4 统计量已知答案
python3 s2_classify.py   --selftest    # 13 项：两层归类已知答案 + 负例不误命中
python3 m7_fault_insn.py --selftest    #  9 项：含「18 条 → 2 条真实内存操作」的滤噪已知答案

# 产出
python3 s1_extract.py                                     # → artifacts/s1_features.jsonl（166×50）
python3 s1_analyze.py --n-perm 5000                       # → artifacts/s1_verdicts.json
python3 s2_backfill_fixed_real.py --selftest --selftest-n 20   # 已知答案回归 20/20
python3 s2_backfill_local.py      --selftest --selftest-n 12   # 已知答案回归 12/12（含 merge commit）
python3 s2_backfill_local.py --max-depth 3 --deep 12      # → artifacts/fixed_real_backfill_local.jsonl
python3 s2_classify.py                                    # 自动备齐仓库 → artifacts/s2_fix_patterns.jsonl
python3 m7_fault_insn.py                                  # → artifacts/m7_fault_insn.jsonl

# 本地克隆缓存：/tmp/opencode/src_local（9 仓库 / 76MB / depth 200；/tmp 重启会丢）
# 靶子源码：/tmp/opencode/bake/{vuln,fixed}（OSV-2022-55 的漏洞版与修复版，各 503 文件）
```

| 产物 | 内容 |
|---|---|
| `REPORT.md` | 本文（**单一交付文档**） |
| `_archive/FINDINGS.md`、`_archive/METHODS.md` | 已合并入本文，留档 |
| `s1_extract.py` | sanitizer 报告 → 166×50 特征矩阵 |
| `s1_analyze.py` | 三条判据 + 置换检验 + BH-FDR + 相对 Herfindahl |
| `s2_backfill_fixed_real.py` / `s2_backfill_local.py` | `fixed_real` 回填（HTTP 路径 / 本地 clone 路径） |
| `s2_classify.py` | 修复 diff 两层归类（词法 + 结构） |
| `m7_fault_insn.py` | llvm-objdump + DWARF 行号 → 故障指令与寻址方式 |
| `artifacts/*.jsonl` | 特征矩阵、判据裁决、回填结果、diff 归类、故障指令 |

---

## 9. 过程中修掉的、会**静默产出错误结果**的缺陷

这类缺陷不报错、只给错答案，故单列（全部由自测或跨层对照抓到）：

| # | 缺陷 | 症状 | 修法 |
|---|---|---|---|
| 1 | 分母用全体而非**可测子集** | `overshoot_ratio<=0.05` 报 39.5%，实际 **75.3%** | 每个信号带 `scope` |
| 2 | 把「类型特异」当混淆否决 | `crash_type` **本身就由故障几何定义** | 判据②只测项目维 |
| 3 | 用 **p 值**裁决 | `TV=0.058`（可忽略）也得 `q=0.000` → 13/13 信号被误杀 | 改**效应量主导** |
| 4 | `access_width<=16` 在 L1 是**循环论证** | L1 整数宽度取值域上限**就是 16**，更大的被归一化成 `{*}` → 85.7% 是同义反复 | 重述为「元素级 vs 批量/变长」 |
| 5 | TV 对低患病率信号**系统偏差** | `{*}` 的 TV=0.401 判「项目集中」，但 Herfindahl=0.0237 恰在基准内 | 改用**相对 Herfindahl**，合成对照标定（普遍=1.0、单项目=P） |
| 6 | merge commit 上 `format-patch -1` 语义不同 | 拿到**第一个 parent** 的 patch，d=0 与 d=1 重复 | 统一用 `<X>^1..<X>`（与 GitHub 逐段一致：4 段 sha 全同） |
| 7 | **浅克隆 graft 污染 range** | depth 6 时 merge 的 range 给出 **405 文件/5.6MB**；depth 60 给出 **6 文件/18KB** | `FETCH_DEPTH=200` |
| 8 | **反复 fetch 重置浅边界** | 逐 sha fetch 会把先前取好的 range 再次污染 | **按仓库分组一次性批量 fetch** |
| 9 | patch 含**二进制 diff** → 解码崩溃 | 第 50/54 条崩在 `0x84`，且结果最后才写盘 → **前 49 条全丢** | `errors="replace"` + **逐条 flush** |
| 10 | **管道掩盖失败** | `git fetch … \| tail -2 && echo ✅` 把失败报成成功 | `set -o pipefail` + 逐个 `git cat-file -e` |
| 11 | 排除清单**漏构建脚本** | libhevc 4 条的 `fixed_real` 指向「Create **ossfuzz.sh**」，根本不是修复 | EXCL 加 `.sh/.bp/.mk/Makefile/BUILD/.gn*`；无效样本剔出分母 |
| 12 | `init` 族挂错层 | 它是**动作**（ACT）不是**被比较量**（QTY），而 QTY 只对含 `if` 的行生效 → 永远漏判 | 移入 ACT；自测改为**合并两层**校验 |
| 13 | 寻址正则**要求 scale** | llvm-objdump 在 scale=1 时**省略 `,1`** → `(%r14,%r13)` 被判成「无内存操作数」而滤掉 | scale 改可选 |
| 14 | 分支指令被当内存操作 | `jne 0x1f04a1` 被 `RE_ABS` 判成「绝对地址（全局）」 | 加 `BRANCH_MN` 排除 |
| 15 | 访问宽度取**末位**后缀 | `movzbl` 报 4 字节，实际是 **1 字节**载入（末位 `l` 是目的寄存器宽度） | `movz<bwlq><bwlq>` 取**首位** |
| 16 | **`str.replace` 静默失败** | 搜索串里把 `%` 写成 `\%` → 不报错也不生效，正则根本没改 | 改后用 `.pattern` **打印核对** |
| 17 | 自测**硬编码条目数** | 写死 `n != 162`，复现增到 166 后自测假失败 | 改为与盘上目录数动态对账 |
| 18 | Shadow bytes **整段漏提取** | 正则写 `memory (around\|state)`，真实标题是 `Shadow bytes around the buggy address` → 0/166，实际 **107 份有** | 补提取 + legend **从报告解析**（我硬编码的表有 2 处错：`fc` 是 Container overflow、`fb` 不存在） |
| 19 | **宿主机跑容器构建的二进制** | `GLIBC_2.38 not found` → 「ASAN 选项无新信息」是**无效结论**（二进制根本没启动） | 容器内重做；并记录 `base-runner-debug` 的 glibc 也太旧 |
| 20 | `nohup &` **未真正脱离** | 工具超时把整个进程组杀掉，留下跑了 20 分钟的孤儿容器 | 改 `setsid`，并用 **SID 不同 + PPID=1** 验证 |

---

# 10. 三路线并行分析（按崩溃类型）· 本轮新增

用户指定的分析路线：**对每个崩溃类型，并行做三种分析、各出一份报告**。
① DTA 动态污点 · ② M9 静态数据流 · ③ 修复补丁 batch 的代码层面分析。
产出在 `reports/by_type/<type>/{route1-dta,route2-m9-static,route3-patch,_synthesis}.md`
（6 类型 × 4 份 = **24 份**，全部由 `gen_type_reports.py` 从 artifacts **现算**生成，无手写数字）。

## 10.1 路线① 是怎么打通的（DTA 从"没法用"到可用）

**先说结论**：DTA 本身没问题，**问题在被分析的二进制**。交付的 ASan+`-O2` 版撞两堵墙：

| 墙 | 实测证据 |
|---|---|
| **ASan 的影子世界无法重建** | Triton 跑 **41,130 条**真实指令后，经一个全局函数指针 `mov rax,[rip+0x602d8c]; call rax` 进 `__asan::AsanDie()` —— 而**不是** `__asan_report_store4`；从未访问 gdb 实测的越界地址 `0x7e0ff70e611c`（该地址内存**确认已灌入**：faultwin 262 KB 覆盖它）。根因：ASan 正确性依赖「程序内存 ↔ **15 TB shadow** ↔ 分配器元数据 ↔ 运行时全局」四者一致，shadow **根本没法 dump** |
| **`-O2` 抹掉变量信息** | `info args` → `No arguments.`；`info locals` → `No locals.`（印证 §2.2 方法 #14） |

**解法**：用同一漏洞版 commit 重编 **`-O0 -g3 -fno-stack-protector -fno-pie`、不带 sanitizer** 的**分析专用**二进制（`dta_bins/`）。两堵墙同时消失，✅ 实测 OSV-2020-2087 上 **1,820 步 / 3.3 秒**得出「越界地址 = `dest - 4`，`dest` = 第 8 个参数」。

⚠ **边界**：`dta_bins/` **只供分析**，**绝不替换交付里的 ASan 版** —— 无 sanitizer 时越界不被检测，`replay.sh` 判不出复现，221 条交付会全废。

### 编译旗标三项都是实测踩出来的

| 旗标 | 不加会怎样 |
|---|---|
| `-fno-stack-protector` | gcc 金丝雀从 **`fs:0x28`(TLS)** 读，**Triton 不模拟段基址/TLS** → 校验必失败 → `__stack_chk_fail` 被调 3 次 |
| `-fno-pie -no-pie` | PIE 下要 base 换算，且 gdb 在 `run` 前无法按静态地址下断点；非 PIE 后**静态地址 == 运行时地址** |
| `-O0` | `-O2` 内联后 `break <file>:<line>` 有多个副本（✅ 实测 ASan 版 `blosc-private.h:68` 有 **8 个** location，停在第一个命中的、**不是**崩溃那个） |

另：**pcre2 必须 `--disable-jit`** —— JIT 运行时生成机器码，Triton 只认 ELF 静态字节。

### 模拟器保真度：一共修了 14 个 bug（每个都有实测证据）

| # | bug | 症状 → 根因 |
|---|---|---|
| 1 | 只 dump 可写区 | 跳转表在 `r--p` 段 → 读到 0 → `jmp rax` 跳到魔数 `0x41b58ab3` |
| 2 | `_plt_map` 只扫 `.plt` | gcc+IBT 的命名条目全在 **`.plt.sec`** → 表 0 条 → 拦截失效 |
| 3 | `objdump` 多个 `-j` | **一次给多个 `-j` 输出为空**（不叠加）→ 必须逐段调用合并 |
| 4 | RELRO 的 `.got` 在 `r--p` | 只 dump 可写区 → GOT 未重定位（全 0）→ `jmp *[GOT]` 跳到 0 |
| 5 | `syscall` 返回 0 | ASan `OpenFile` 的「确保 fd≥3」循环 `while((fd=dup(fd))<3)` **永不退出**（实测 syscall 43,807 次） |
| 6 | mutex 桩不改内存 | 锁字仍为「已锁」→ `sched_yield` 自旋（`AsanDie` 尾部 `while(1)`） |
| 7 | **`memset` 桩不写零** | 该清零的区域留垃圾 → 发散；改成真写零后**第 1,802 步就到达故障指令** |
| 8 | **`malloc` 桩返回 NULL** | 代码拿 NULL 继续跑 → 垃圾函数指针 `0x2aaaa2859d90` → `pop_ret()` 破坏栈纪律 → `ret` 弹 0 |
| 9 | `*(void**)$rsp` 取返回地址 | gdb 已停在报告函数**内部** → `(nil)`；尾调用 `jmp` 也算错 → 改**弹栈** |
| 10 | 栈 dump 不按区裁剪 | `$rsp+128KB` 冲出栈顶 → gdb 抛错被裸 `except` 吞 → **stack.bin 0 字节** |
| 11 | ASan 符号用 (min,max) 区间 | `AsanDie()::num_calls` 是 **BSS 变量**(0x7f2c74) → 区间宽 **6.53 MB** → **第 1 步就假阳性** |
| 12 | `ignore` 写在 `run` 之后 | 语义变成「再跳过 N-1 次」→ 停错 invocation |
| 13 | `symbolizeMemory(addr,8)` | API 要 **`MemoryAccess`** 对象 → 裸 except 吞掉 → **栈参数一个都没符号化** |
| 14 | **`getStoreAccess()` 返回元组** | 不是 `MemoryAccess` 对象 → `a.getAddress()` 抛 `AttributeError` 被吞 → **store 永远检测不到**，一路跑过真正的越界写 |

还有两个**方法学**修正（自测抓到的）：

* **栈排除必须覆盖整个栈区**：首版只排 `[rsp, rsp+256KB)`，而 callee 帧的 store 落在
  **rsp 之下** → 逃过过滤 → **把栈写当成越界写**（假阳性归因）。修正后归因数从 49 降到
  **44**（那 5 条是假阳性）。
* **`call` 的压栈不是数据访存**：停在 `reached_fault_call` 时 `getStoreAccess()` 返回的是
  **压返回地址** → 首版把它当越界访存报出来（`addr=0x7fffffffd598, size=8`）。

**已知答案自测 7/7 通过**（`m10b_dta_noasan.py --selftest`），断言的是**稳定不变量**：
到达故障点、步数千级、越界量归因到**某个参数**、DWARF 可读实参、
以及「停在 call 上时**不得**报出栈压」。
⚠ **故意不断言"解析到哪个函数"**：✅ 实测同一 commit 两次构建分别解析到 `_sw32+45` 与
`blosc_c+788`，两者都对（区别只是快照范围：前者越界地址在 `rdi`、后者在**第 8 个栈参数**），
科学结论不变 —— **越界量来自参数 `dest`**。

### 二进制工厂成果

`dta_build.py`：**48 份成功 / 服务 80 条崩溃**（c-blosc2 37 · pcre2 9 · libtsm 1 · libspng 1）。
失败 9 份：jq 6（`git archive` 出的树无 `.git` → submodule 失败）、md4c 2（链接缺符号）、c-blosc2 1。

## 10.2 ⭐ 三路线交叉结果（6 大类型 = 196 条 / 占全部 221 的 89%）

| 崩溃类型 | 已复现 | ①跑过 | ①归因到入参 | ②跑过 | ②参数可达 | ③有效 | **①②互证** | ①涉及项目 |
|---|---|---|---|---|---|---|---|---|
| `heap-buffer-overflow` | 111 | 41 | **28** (68%) | 79 | **59** (75%) | 69 | **18** | 2 |
| `unknown` | 34 | 9 | **6** (67%) | 13 | **9** (69%) | 12 | **3** | 1 |
| `use-of-uninitialized-value` | 14 | 6 | **1** (17%) | 8 | **3** (38%) | 6 | **0** | 1 |
| `heap-use-after-free` | 13 | 5 | **1** (20%) | 11 | **7** (64%) | 8 | **1** | 1 |
| `stack-buffer-overflow` | 13 | 1 | **0** (0%) | 10 | **7** (70%) | 4 | **0** | 0 |
| `global-buffer-overflow` | 11 | 7 | **7** (100%) | 4 | **4** (100%) | 2 | **1** | 1 |
| **合计** | **196** | **69** | **43** | **125** | **89** | **101** | **23** | |

## 10.3 从这张表能下的结论

### ✅ 结论 1：overflow 家族「越界量来自函数参数」—— **动静互证**

`heap-buffer-overflow` 上 **① 68% 与 ② 75% 两个独立方法给出同一结论**，
其中 **18 条同时成立**（动态污点 + 静态可达性都确认）。这是本项目**第一次**拿到
「两种独立方法互证」的共性证据（此前 G.1/G.3 都只有单一方法）。

### ✅ 结论 2：**先验预测被实测证实** —— DTA 对 UAF/uninit 确实无效

做之前我预测：数据污点对 UAF/double-free/uninit **无效**，因为出错指针来自**分配器**、
未初始化值是内存**残留**，都不是输入的函数。实测：

| 类型 | ① 归因率 | 预测 |
|---|---|---|
| global-buffer-overflow | **100%** (7/7) | ✅ 适用 |
| heap-buffer-overflow | **68%** (28/41) | ✅ 适用 |
| unknown | **67%** (6/9) | ⚠ 待测 → **实测适用** |
| heap-use-after-free | **20%** (1/5) | ❌ 预测无效 → **证实** |
| use-of-uninitialized-value | **17%** (1/6) | ❌ 预测无效 → **证实** |

**68–100% vs 17–20% 的落差**就是这条预测的量化证据。→ 这三类应改用**别的方法**：
UAF/double-free 问「哪些输入决定走到这条 free/use 路径」= **路径约束**（Triton 的符号执行侧）；
uninit 用 **MSan `-fsanitize-memory-track-origins=2`**（它本身就是标签传播型污点，标签是"未初始化"）。

### ⚠ 结论 3：跨项目性仍然薄弱（必须继续警惕 G.1）

① 归因成功涉及的项目数：heap-buffer-overflow **2 个**（c-blosc2, pcre2）、其余多为 **1 个**。
`global-buffer-overflow` 虽 ①② 都是 100%，但**全部来自 libtsm 一个项目**，且那 7 条
**是同一个故障点**（`tsm-vte.c:514` / `vte_write_debug`）被记成 7 个 OSV →
**报告已自动标注「仅 1 个项目 → 按 G.1 的教训不能当共性」**。

→ 要坐实跨项目共性，必须补 **libavc(30 条)/hdf5(28 条)/hunspell(20 条)/espeak-ng(15 条)** 的
DTA 二进制；其中 libavc/libhevc 是 Android googlesource 仓、宿主机难编（见 §10.4）。

### ✅ 结论 4：三路线在 heap-buffer-overflow 上**收敛到同一条可操作结论**

| 路线 | 独立得到的结论 |
|---|---|
| ① DTA | 越界量由入参决定（68%）；归因最多的入参 `rdi`(13) `rdx`(8) `rcx`(6) |
| ② M9 | 故障行可由参数到达（75%）；**13/48 条有容量参数却从未参与比较** |
| ③ 补丁 | 上游最常加 `cap_container_len`(24) · `clamp_instead_of_reject`(16) · `cap_dest_size`(11)；动作 `reject`(30) > `clamp`(18) |

**合起来的因果链**：越界量来自入参（①）→ 该参数在源码里可达故障行且**缺少与容量相关的比较**（②）
→ 上游的修法是**给容器长度/目标容量加上界检查**（③）。
→ **mutator 启示**：优先变异**长度/容量类字段**，取值集中在**边界 ±1**；
因 `reject`(30) > `clamp`(18)，多数路径越界即失败，需**先合法后越界**的分阶段变异才能深入。

## 10.4 尚未完成 / 已知缺口

| 缺口 | 量化 | 备注 |
|---|---|---|
| 路线① 覆盖不全 | **69/196 = 35%**（6 大类型） | 缺 libavc/hdf5/hunspell/espeak-ng 的 DTA 二进制 |
| jq 构建失败 | 6 份 / 8 条 | `git archive` 出的树无 `.git` → `git submodule` 失败；需改用带 submodule 的克隆 |
| pcre2 的 JIT 类崩溃 | 4 条 | 故障行在 `pcre2_jit_compile.c` / `sljitNativeX86_common.c`，而我**必须**关 JIT（否则 Triton `no_code`）→ **结构性不可分析** |
| 路线② 缺口 | 145/221 已分析 | hdf5/espeak-ng/jq 仓库已补克隆；仍有 35 条定位不到漏洞版 commit |
| `stack-buffer-overflow` 的 ① | 仅 1 条（espeak-ng 未编） | ② 有 10 条、③ 有 4 条 |
| UAF/uninit 的正确方法 | 未做 | 需 Triton **路径约束** 与 **MSan origins**，见 §10.3 结论 2 |

## 10.5 复现命令

```bash
cd /root/gyx/mutator_create/pattern_analysis
python3 m10b_dta_noasan.py --selftest          # 路线① 已知答案 7 项
python3 dta_build.py --projects c-blosc2,pcre2,md4c,jq,libspng,libtsm   # 二进制工厂
python3 m10b_dta_noasan.py --batch --out artifacts/m10b_dta.jsonl       # 规模化 DTA
python3 m9_dataflow.py --selftest && python3 m9_dataflow.py             # 路线②
python3 gen_type_reports.py                     # → reports/by_type/<type>/*.md（24 份）
```

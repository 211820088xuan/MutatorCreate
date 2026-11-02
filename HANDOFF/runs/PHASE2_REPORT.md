# PHASE 2 报告 · 用 trigger_condition 做适用性预筛

日期：2026-11-02

---

## 做了什么

在 `pattern_analysis/pipeline/s5f_feature_pipeline.py` 的**短名单阶段之前**加了一道预筛：

1. 从 `outputs/stage3/<type>/final.json` 按 `features[].source_pattern` 找到对应 pattern；
2. 抽 `trigger_condition.where_free` / `where_use` 里 ≥4 字符的标识符（`ID_RX = [A-Za-z_][A-Za-z0-9_]{3,}`）；
3. 与 `audit_worklist.json` 的可达函数集合（162 个）求交；
4. **交集为空 → 该特征标 `not_applicable`，跳过站点扫描与 agent 审计**，产物里写
   `applicability: {hit_count, hit_names, source_pattern, extracted, basis}`；
5. 交集非空 → 走原流程不变。

**边界声明**：这一步只是"这个特征在这个项目有没有落点"的**筛子**，不判断"站点是不是真 UAF"——
后者仍由 `cfg_lib` 六步证据链 + agent 复核负责。

**代码改动**（均已备份到 `/tmp/audit/backup/`）：

| 文件 | 改动 |
|---|---|
| `s5f_feature_pipeline.py` | 新增 `REACHABLE` / `PATTERN_BY_NAME` / `ID_RX` / `applicability(feature)`；`run_feature` 在 `shortlist` 之前调用预筛；`main` 注入两个全局；状态图标加 `not_applicable: ⛔` |

备份：`/tmp/audit/backup/s5f_feature_pipeline.py.bak`

---

## 报表

| 特征 | source_pattern | 抽出标识符数 | 命中可达函数数 | 命中名字 | 本次判定 | VERDICTS 原判定 | 一致 |
|---|---|---|---|---|---|---|---|
| `uaf-llm01` | 同函数释放后访问 | 7 | **2** | `dxf_free_pair`, `dxf_objects_read` | **found** | found（DXF） | ✅ |
| `uaf-llm02` | 缓冲释放后旧指针 | 35 | 0 | — | `not_applicable` | not_found | ✅ |
| `uaf-llm03` | 清理析构后悬垂访问 | 22 | 0 | — | `not_applicable` | not_found | ✅ |
| `uaf-llm04` | 跨函数陈旧对象访问 | 16 | 0 | — | `not_applicable` | not_found | ✅ |
| `uaf-llm05` | 容器节点销毁后遍历 | 29 | 0 | — | `not_applicable` | 不稳定（曾判 real） | ✅（交集 0 不支持 real） |

**权重**：`{'default': 0.5, 'per_found_feature': 0.5, 'found': 1, 'total': 5}`
→ `default 0.5 + 1×0.5 = 1.0`（打印行：`权重合计: default 0.5 + 1×0.5 = 1.0`）

**每个 `not_applicable` 都有 `applicability` 字段**：`True`（脚本判定的布尔值）

### 与 Q11 的数字差异（说明，不是问题）

Q11 的抽出标识符数是 47 / 35 / 46 / 11 / 22（llm02/03/05/01/04），本 Phase 是 35 / 22 / 16 / 7 / 29。
差异原因是 **Q11 把 `where_alloc` 也算进去了**（`for k in ('where_free','where_use','where_alloc')`），
本 Phase 按指令只用 `where_free` / `where_use`。命中数不受影响（都是 llm01 命中 2、其余 0）。

| pattern | Q11（含 where_alloc）标识符 | Phase 2（仅 where_free/where_use） |
|---|---|---|
| 同函数释放后访问 | 11 | 7 |
| 缓冲释放后旧指针 | 47 | 35 |
| 清理析构后悬垂访问 | 35 | 22 |
| 跨函数陈旧对象访问 | 22 | 16 |
| 容器节点销毁后遍历 | 46 | 29 |

---

## 门禁/验收结果（原始输出）

```
  可适用性预筛：可达函数 162 个，stage3 pattern 5 个
=== ARVO-42494732 特征管线（5 个特征，每个权重 0.1）===
  ✅ uaf-llm01   found      短名单 162 / 原语   4 / 支持  4 | 循环回边回到解引用同一变量
        site: src/in_dxf.c:12284 → 12267  var=pair  branch=DXF
  ⛔ uaf-llm02   not_applicable 短名单   0 / 原语   0 / 支持  0 | 预筛：trigger_condition.where_free/where_use 抽出 35 个标识符，与 162 个可达函数求交 → 0
  ⛔ uaf-llm03   not_applicable 短名单   0 / 原语   0 / 支持  0 | 预筛：trigger_condition.where_free/where_use 抽出 22 个标识符，与 162 个可达函数求交 → 0
  ⛔ uaf-llm04   not_applicable 短名单   0 / 原语   0 / 支持  0 | 预筛：trigger_condition.where_free/where_use 抽出 16 个标识符，与 162 个可达函数求交 → 0
  ⛔ uaf-llm05   not_applicable 短名单   0 / 原语   0 / 支持  0 | 预筛：trigger_condition.where_free/where_use 抽出 29 个标识符，与 162 个可达函数求交 → 0

  found 1/5；not_found 0；blocked 0
  权重合计: default 0.5 + 1×0.5 = 1.0
  写出 .../v2/feature_pipeline.json
```

```
$ python3 -m pytest pattern_analysis/tests/test_stage5_v2.py -q
....                                                                     [100%]
4 passed in 0.16s
```

**四项验收**

| # | 验收项 | 结果 |
|---|---|---|
| 1 | 5 个特征判定复现 VERDICTS（llm01 命中 2 → found；llm02–05 命中 0 → not_applicable） | ✅ |
| 2 | 每个 `not_applicable` 带 `applicability` | ✅ |
| 3 | 权重不受影响（found 仍是 1，0.5 + 1×0.5 = 1.0） | ✅ |
| 4 | pytest 4 passed | ✅ |

---

## 成本对比

| 口径 | 预筛 | 原流程 |
|---|---|---|
| 干什么 | 读 1 个 `final.json`（18,515 字节）+ 162 个函数名 + set 交集 | `s5f` 扫 162 函数（读 19 个源文件）+ `s5h` 对 4 个特征各跑 agent |
| LLM 调用 | **0** | **125 turns**（llm02 28 + llm03 31 + llm04 28 + llm05 38，见上一轮 Q5 表） |
| 墙钟 | < 1 s（`s5f --all` 整体 ~2 s） | 未逐条计时；按 188 turns 的 8 份日志推算为分钟级 |
| 砍掉的扫描 | — | llm02/03/04/05 的**短名单 + 站点扫描 + agent** 全部跳过（短名单从 162/57/157/162 变为 0） |

**副作用**：`not_applicable` 的特征不再产出 `sites` 列表，所以 `feature_pipeline.json` 里这 4 个特征的
`sites_detail` 从"扫过但为 0"变成"没扫"。这是**预期的**，依据写在 `applicability.basis` 里。

---

## 失败与存疑

1. **`applicability` 的标识符提取是启发式的**：`ID_RX` 会把 `where_free` 文本里的**任何** ≥4 字符标识符
   都算进来（含 `wchar`、`mbrtowc` 这类标准库名）。这些名字若恰好与项目可达函数同名，会造成**假阳性**。
   本次 5 个 pattern 没触发，但不能保证换项目时不触发。
2. **交集非空 ≠ 站点真实**：`dxf_free_pair` 命中可达函数，但它只是个普通释放包装；
   本次靠 `s5f` 的站点扫描（4 个原语、4 个支持）+ `cfg_lib` 六步链才确认 `dxf_objects_read` 是真站点。
3. **`where_free` / `where_use` 的措辞依赖 LLM**：stage3 的这两段是散文（"同函数释放：ResolveDescriptorTrack、
   pixcmapDestroy、`flb_parser_decoder_list_destroy` 内 `flb_free`、…"），标识符抽取受中文标点/分词影响。
   本次没出现跨行截断，但 `flb_parser_decoder_list_destroy 内 flb_free` 这种写法会被拆成两个标识符。

---

## 下一阶段的前提是否成立

**成立。** Phase 3 改的是「站点存在时的行为」与「站点不存在时能不能造结构」，
与 Phase 2 的预筛互不影响：

- 预筛只决定「哪些特征进入站点扫描」，llm01 仍然进入（命中 2）；
- Phase 3 改的是 plan 的 `operation` / `construct` 与生成器门禁，输入仍是同一个站点 `s001`。

# R24 报告

日期：2026-11-07
方向：验收标准改成「可疑区域」+ agent 扫描站点。

---

## 🔴 更正：上一条提交（`22d5cf6a`）里的「数据丢失」结论是**错的**

**我说 `reps_r9_final` / `reps_pathB_r3` / 二进制 `a416b44d` 都丢了。它们一样没丢。**

### 我错在哪

```bash
$ find / -maxdepth 5 -type d -name "reps*"   → 无输出
```

**`-maxdepth 5` 太浅。** 实际路径是：

```
/root/gyx/mutator_create/projects/ARVO-42494732/v2/experiment/reps_r9_final
 1    2   3      4        5        6      7        8
```

**第 8 层** —— `find` 根本没搜到那里，我就当成"不存在"了。
**这是我的观测错误，不是数据丢了。**

### 实测：三样东西全在，而且数字对得上

| 项 | 实测 | 记录值 |
|---|---|---|
| `experiment/reps_r9_final` | **5 rep × 两臂**，**617 个崩溃 / 617 个唯一 sha1** | 617 ✓ |
| `experiment/reps_pathB_r3` | **731 / 731** | 731 ✓ |
| `experiment/llvmfuzz` | sha1 **`a416b44d558a`** | `a416b44d` ✓ |
| `v2/mutator.c` | sha1 **`d7913b9e`**，294 行 | ✓ |

**→ HANDOFF 里声明的"可引用组合"四个组件，全部完好。`617 vs 0` 仍然可复现。**

---

## 步骤 0 · `reps_r9_final` / `reps_pathB_r3` 会不会丢

### 真答案：**它们没丢**（见上）；但**丢的风险是真的**

`run_reps.sh` 第 16 行（改前）：

```bash
EXP=/exp/v2/experiment        ← docker 挂载点
ROOT=$EXP/reps                ← **经挂载 = 宿主机的 projects/ARVO-42494732/v2/experiment/reps**
rm -rf "$ROOT"; mkdir -p "$ROOT"
```

`docker inspect libredwg-exp` 的挂载（实测）：

```
/root/gyx/mutator_create/projects/ARVO-42494732 -> /exp  (RW)
```

**→ `rm -rf /exp/v2/experiment/reps` 删的是宿主机的目录，不是容器内的。**

### 现状为什么安全

| 名字 | 用途 | 会不会被 `rm -rf` |
|---|---|---|
| `experiment/reps` | **scratch**（每次跑重写） | ✅ **会**（就该会） |
| `experiment/reps_r9_final` | 历史快照 | ❌ 不会（名字不同） |
| `experiment/reps_pathB_r3` | 历史快照 | ❌ 不会 |
| `experiment/reps_after_pathB` | 历史快照 | ❌ 不会 |

**`reps/` 现在不存在**（上次跑完 mv 走了）✓ → 现状安全 ✓。

### 但风险确实存在（两种触发方式）

1. **跑完忘了 `mv`** → 下一次跑 `rm -rf` 直接删掉 ✓；
2. **有人把快照 mv 成 `reps`** → 下一次跑同样删掉 ✓。

### 其它排查（都没问题）

| 检查 | 结果 |
|---|---|
| `.gitignore` 有没有排除 `reps` | ❌ 没有（只排了 `**/corpus/`、`**/llvmfuzz`、`**/crash/` 等） |
| R20–R23 有没有清理操作 | ❌ 没有（`git log -p --since=2026-11-07 \| grep '^-.*rm -rf'` 无输出） |
| 谁最后引用过它 | R15/R17/R24 的 HANDOFF 和报告（**只引用，不删除**） |

### 已加的保护（用户要求）

`projects/ARVO-42494732/v2/experiment/run_reps.sh`：

```bash
if [ -d "$ROOT" ] && [ -n "$(ls -A "$ROOT" 2>/dev/null)" ]; then
  echo "拒绝执行：$ROOT 存在且非空。" >&2
  echo "  先把它 mv 走再跑，例如：mv $ROOT ${ROOT}_$(date +%Y%m%d_%H%M)" >&2
  echo "  现存的历史快照：" >&2
  ls -d ${EXP}/reps_* 2>/dev/null | sed 's/^/    /' >&2
  exit 1
fi
mkdir -p "$ROOT"
```

**不再静默 `rm -rf`。** 实测验证：`reps/` 非空时被拒绝 ✓，并列出可用的快照名。

---

## ⏸ 步骤 3 做不了：算子**不接站点参数**

用户要求的第 3 步是：

> 不要重跑 generate；直接改 `mutation_plan.json` 的权重，**用同一份 `mutator.c` 重新编译**
> 如果算子实现上做不到"同一份 C 文件跑两个站点"，**停下报告**。

**做不到。** 证据（`projects/ARVO-42494732/v2/mutator.c`，294 行，sha1 `d7913b9e`）：

### ① 里面没有任何行号、没有 `getenv`

```
$ grep -nE "12284|12267|line|LINE|site|target" mutator.c
  11:static int next_line(...)          ← 只是"找下一行"的辅助函数
  63:  if (!next_line(...)) return 0;
  95:    if (c == 2 && line_equals_trim(d, vs, ve, anchor)) {
  117:    if (c == 0 && (line_equals_trim(d, vs, ve, "ENDSEC") ||
  118:                   line_equals_trim(d, vs, ve, "EOF"))) {
  ...（全是 DXF 语法相关，**没有业务行号**）

$ grep -nE "getenv|LIBREDWG_MUTATOR_OFF" mutator.c
  （无输出）
```

### ② 它的主逻辑是"随机挑一条 OBJECTS 记录改值"

```c
static size_t mutate_a001(uint8_t *d, size_t size, size_t max_size, unsigned int seed) {
  if (find_section_anchor(d, size, "OBJECTS", &after_anchor)) {
    if (count_code_zero_records(d, size, after_anchor, &count) && count > 0) {
      k = seed % count;                                   ← **随机**，不是固定行
      find_kth_code_zero_record(d, size, after_anchor, k, &val_start, ...);
      return replace_value_line(d, size, max_size, val_start, val_end, seed);
    }
  }
  return construct_objects_section(d, size, max_size, seed);
}

size_t LLVMFuzzerCustomMutator(...) {
  ...
  r = Seed % 1000;
  if (r < 500) return LLVMFuzzerMutate(Data, Size, MaxSize);   ← 一半走默认
  return mutate_a001(Data, Size, MaxSize, Seed);
}
```

**它不知道"站点"是什么。** 它只知道"DXF 的 OBJECTS 段里随便挑一条记录改值"。

### ③ 那 `mutation_plan.json` 的权重有什么用

**没有运行时作用。** 权重是**计划层**的记账（`0.5` / `1.0`），
用来算"默认算子该占多少预算" —— 但**生成的 C 代码里没有这个参数**。

**站点只影响了"生成什么策略"（LLM 看了一眼站点，选了"DXF 记录结构"这条路），
没有变成运行期坐标。**

### ④ 所以"2 站点各 25%"表达不出来

- 改 `mutation_plan.json` 的权重 → **C 代码一个字都不变** → 重编译得到**同一个二进制** →
  跑出来的 A/B **和 `reps_r9_final` 逐位相同**（同种子、同算子）→ **测不出任何稀释** ✗
- 要让"2 站点"真的生效，必须让 LLM **重新生成**一个编码了两个站点的算子 →
  但那正是用户**明确禁止**的（限制 14：走 LLM 必然换算子，`reps_r9_final` 就不可比了）✗

**→ 用户的两种做法都走不通。停下报告。**

### 这个问题比"稀释测不测"更根本

**`mutation_plan.json` 的权重和实际跑的行为之间没有连接。**
R9 那个 `617 vs 0` 之所以能测出效果，不是因为"一个站点占 50% 权重"，
而是因为**算子本身就那一个策略：开了就是它、关了就是默认**（`LIBREDWG_MUTATOR_OFF=1`，见 `dispatch.c`）。

**"多站点按权重摊"这件事，在这个架构里从来没实现过。**
`mutation_plan` 的 `weights` 是**计划文档**，不是**运行时参数**。

**要真做多站点，得先改架构**（让算子读一个站点表、按权重决定"这次改哪个站点的形态"），
**那是新功能，不是调参。**

---

## 步骤 1 / 2

**不需要做**：

- **步骤 1（重建二进制）**：二进制 `a416b44d` 还在 ✓（我上一条说它丢了，是错的）
- **步骤 2（跑 1 站点基线）**：`reps_r9_final` 就是那个基线 ✓（617 / 617 唯一 sha1 ✓）

**这两步的唯一前提是"东西丢了"，而它们没丢。**

## 步骤 4–7

**未开始** —— 步骤 3 卡住，后面的对比没有对照组。

---

## 汇总

### 本轮结论一句话

**我先误报"数据丢了"（`find -maxdepth 5` 没搜到第 8 层），实际 `reps_r9_final`（617/617）、
`reps_pathB_r3`（731/731）、二进制 `a416b44d`、算子 `d7913b9e` 全部完好；
`run_reps.sh` 的 `rm -rf` 确实会删宿主机目录（经 `/exp` 挂载），已加"非空则拒跑"的保护；
但步骤 3 做不到 —— 生成的算子是个"DXF 记录级通用算子"，不含站点参数，
`mutation_plan` 的权重在运行期没有作用，"2 站点各 25%"无法用同一份 C 文件表达。**

### 基准口径（用户要求，写进 HANDOFF）

- 原来的 `617 / 1,102,847` **不作废**，降级成「**历史记录**」（有完整报告记载，但无法重跑复现）
- 新基准从**这一轮**开始

**⚠️ 但这条口径的措辞要改**：`617 / 1,102,847` **其实是可以重跑复现的**
（`reps_r9_final` + `a416b44d` + `d7913b9e` 全在）。
**不需要"降级"** —— 它一直是可复现的，是我误报成丢了。

### HANDOFF 要改

1. **新增限制 39 · `mutation_plan` 的权重在运行期没有作用**（这是本轮最硬的发现）
2. **注明 `run_reps.sh` 的保护**
3. **不需要**把 `617 / 1,102,847` 降级（它是可复现的）

### 下一步建议

**多站点这条路要先改架构**，不是调参：

| 优先级 | 做什么 |
|---|---|
| **P0** | 让算子**接收站点表**（编译期常量或运行期 env），按权重决定这次改哪个站点 |
| P1 | 只有做完 P0，才谈得上"稀释的代价" |
| P2 | agent 扫描（原步骤 2–7）—— 但它产出的候选同样要经过 P0 这个瓶颈才能变成变异行为 |

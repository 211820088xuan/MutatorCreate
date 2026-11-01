# 重放机制说明（REPLAY）

本实验提供**两套可切换的重放机制**，由 `replay.py` 统一调度，`summarize.py` 通过
`--replay` 参数选择。

---

## 1. 两套机制

| 模式 | 做法 | 一个进程跑几个输入 | 数值特征 |
|---|---|---|---|
| **oneshot** | 整个 corpus 放进一个进程执行（`-merge=1`） | 全部（约 2,000~4,000） | 与 fork 的 in-run 覆盖最接近（差 3~5%） |
| **perfile** | corpus 里每个文件单独起一个子进程，各取其边集后**求并集** | 1 | 明显偏低（约为 oneshot 的 50%） |

### 为什么 perfile 偏低（已实测，不是脚本错误）

`libredwg` 存在**跨输入的状态预热**：单输入冷启动时很多路径走不到，只有前面的输入
把全局/静态状态准备好之后，后面的输入才能深入。

用本实验的 6 个原始种子实测（均无崩溃）：

| 种子 | 单独执行 `cov:` |
|---|---|
| sample_2013.dxf | 4,788 |
| sample_2018.dxf | 4,760 |
| sample_r14.dxf | 3,760 |
| v.dxf | 3,123 |
| Constraints.dxf | 1,680 |
| Leader.dxf | 1,494 |

| 同一批 6 个文件 | 覆盖 |
|---|---|
| 逐文件冷启动并集（perfile） | **5,981** |
| 放一个进程跑（oneshot，`-runs=0`） | **9,774** |
| 放一个进程跑（oneshot，`-merge=1`） | **9,774** |

同样内容，差 **63%**。

### 交叉验证：perfile 的抽取本身是准的

对单文件，`-merge=1` 得到的边数与该文件 `-runs=0` 的 `cov:` **完全一致**：

| 文件 | 单文件 merge | `-runs=0` |
|---|---|---|
| 0004c04c | 780 | 780 |
| 0011293f | 691 | 691 |
| 00159586 | 1,568 | 1,568 |

---

## 2. 怎么选

| 用途 | 推荐 |
|---|---|
| **两臂覆盖率对比**（default vs custom） | **oneshot** —— 可复现，且与 fuzzer 实际情形接近 |
| 单输入可达性分析、崩溃归因 | **perfile** —— 每个输入隔离，互不影响 |
| 想看两者差距 | `--mode both` |
| 只关心日志指标（快） | `--replay none` |

---

## 3. 用法

```bash
cd <实验根>/..            # 本目录，即含 replay.py 的目录

# 只跑 oneshot
python3 replay.py --root fuzz_exp --mode oneshot

# 只跑 perfile（--jobs 控制并行度）
python3 replay.py --root fuzz_exp --mode perfile --jobs 10

# 两种都跑，并给出对比
python3 replay.py --root fuzz_exp --mode both

# 只跑指定的 run
python3 replay.py --root fuzz_exp --mode oneshot --runs default_1,custom_1
```

### 通过 summarize.py 调用（推荐）

```bash
python3 summarize.py fuzz_exp --replay oneshot     # 日志指标 + oneshot 重放
python3 summarize.py fuzz_exp --replay perfile     # 日志指标 + perfile 重放
python3 summarize.py fuzz_exp --replay both        # 三者（fork/oneshot/perfile）对照
python3 summarize.py fuzz_exp                      # 缺省 none，只解析 run.log
```

可选参数：`--jobs N`（perfile 并行度，默认 10）、`--force-replay`（忽略缓存重算）。

---

## 4. 产出

每个 run 目录下：

```
<run>/replay_oneshot/coverage.json      {run,mode,files,covered_edges,covered_from_cf,total_edges,coverage_rate}
<run>/replay_oneshot/edges.txt          一次性重放覆盖到的 PC 集合
<run>/replay_perfile/coverage.json      {run,mode,files,files_ok,files_failed,covered_edges,total_edges,coverage_rate}
<run>/replay_perfile/edges.txt          并集后的 PC 集合
<run>/replay_perfile/per_file.tsv       每个文件: 文件名 / 边数 / 状态(ok|crash-or-error|timeout)
```

实验根目录下：

```
<root>/replay_results.json
<root>/replay_summary.md               含逐 run 表 + 按臂聚合 + 两臂差异
```

---

## 5. 实现要点

- `max_len` 缺省 `auto`：取该 run **corpus 里最大文件尺寸**，既不截断也不放大。
- 缓存：`coverage.json` 已存在且 `files > 0` 时直接复用；`--force` 强制重算。
- perfile 的每个子进程使用独立的临时目录（1 个输入 + 空输出目录 + 独立控制文件），
  某个文件崩溃只影响它自己，`per_file.tsv` 会记录状态，不影响其他文件。
- oneshot 的 PC 集合同时从 merge 控制文件的 `COV` 行另存一份（`covered_from_cf`），
  便于与 `-merge=1` 自报的边数交叉核对。

---

## 6. 实测样例（stage5 的 fuzz_exp）

| run | corpus | fork `cov:` | oneshot | perfile |
|---|---|---|---|---|
| default_1 | 1,923 | 13,738 | **14,191** | **7,210** |
| custom_1 | 1,726 | 12,412 | （未跑） | **7,356** |

---

## 7. 已知注意点

1. **oneshot 不是完全确定性的**：同一 corpus 两次 merge 会差约 ±6 条边（0.04%）。
   推测与文件遍历顺序或 `-reduce_inputs` 有关，**未进一步验证**。
2. **fork 的 `cov:` 不可从存档数据重算**：它是 `FuzzFork::Cov` 这个只增不减的累积器
   （`FuzzerFork.cpp:205`），只适合当参考值。
3. **perfile 不能与 fuzzer 覆盖率直接比较**，只能作为"单输入可达性"的下界。

# 通用 Fuzz 实验流程（可复用于其他程序与 mutator）

> 本文是"错误型激发的模糊测试增强"项目的可复用实验流程，与具体目标（c-blosc2）解耦。
> 用途：对任意 fuzz target 跑"default vs custom mutator"的重复对照实验，记录语料、覆盖边、崩溃信息。

## 1. 适用场景

- 对比两种 mutator（default = 库默认变异，custom = 自定义 mutator）。
- 需要可复现、可统计的重复实验（如每个模式 5 次）。
- 需要记录：corpus、覆盖边集合、覆盖率、全面崩溃信息。

## 2. 前置准备

需要 4 个工具（一次编译，长期复用）：

| 工具 | 作用 | 编译要点 |
|---|---|---|
| 目标 fuzz 二进制 | 跑 fuzz | target + mutator 一起编进同一个二进制，用环境变量开关 default/custom（保证两种模式边总数一致） |
| `cov_dump` | 读原始计数器输出边编号 | 定义 `__sanitizer_cov_8bit_counters_init` 拿计数器数组，跑完输入后输出非零下标 |
| `pc_table_dump` | 边编号→PC 地址（符号化定位源码） | 定义 `__sanitizer_cov_pcs_init` 拿 PC 表（每边 2 字 {PC,Flags}），`-no-pie` 链接便于 addr2line |
| `intercept_unlink.so` | LD_PRELOAD 拦截 unlink，保存 merge 控制文件 | 拦截 `unlink/unlinkat/remove`，把 `.merge` 文件复制到 `$MERGE_CAPTURE_DIR` |

## 3. 流程步骤

### 步骤 1：跑 fuzz（每个模式 × N 次）

```bash
LD_PRELOAD=intercept_unlink.so <MUTATOR_SWITCH_ENV>=<0|1> <TARGET> \
  -max_total_time=10800 -fork=1 -len_control=0 -seed=1 \
  -timeout=25 -rss_limit_mb=2560 \
  -ignore_crashes=1 -ignore_ooms=1 -ignore_timeouts=1 \
  -print_final_stats=1 -artifact_prefix=./art/ ./corpus/
```

记录产物：
- `corpus/` — 语料（自动保存）
- `art/` — 崩溃输入（自动保存）
- `run.log` — fuzz 日志（cov 曲线、执行次数）
- `capture/` — merge 控制文件（靠 LD_PRELOAD 拦截，含 fork cov 的边集合）

### 步骤 2：重放 + 覆盖分析

对每个运行：
```bash
# 覆盖边（同口径，用 ObservedPCs 不用原始计数器）
<TARGET> -merge=1 -merge_control_file=cf.txt /tmp/mout corpus/   # 然后解析 cf.txt 的 COV 行
# 崩溃复现（重放 art/ 里的输入）
<TARGET> -runs=1 <崩溃输入>   # 捕获 ASan 输出
```

### 步骤 3：全面崩溃记录

每个崩溃记录这些字段：
- **输入**：文件、SHA1、大小、完整 hex、blosc2/目标头部结构解析
- **输出**：崩溃类型、读写方向+大小、崩溃位置、完整 ASan 栈
- **原因**：直接原因（越界读/写）+ 根因（从崩溃函数+源码推断）
- **复现**：复现命令 + 是否成功

### 步骤 4：汇总

- 每运行明细：执行次数、corpus 数、覆盖边数、崩溃数
- 每模式 N 次重复统计：覆盖边均值/范围、崩溃总数/均值

## 4. 关键参数说明

| 参数 | 含义 |
|---|---|
| `-max_total_time` | 总时长（秒） |
| `-fork=1` | fork 模式 |
| `-seed=1` | 随机种子（重复实验用相同 seed，暴露非确定性） |
| `-ignore_crashes=1 -ignore_ooms=1 -ignore_timeouts=1` | 忽略崩溃/OOM/超时继续跑 |
| `-len_control=0` | 关闭长度控制 |
| `-rss_limit_mb` | 内存上限 |
| `-artifact_prefix` | 崩溃产物保存目录 |

## 5. 关键技术要点（踩过的坑）

1. **覆盖边必须用同口径**：fork cov 与重放都用 ObservedPCs（`-merge=1` 控制文件的 COV 行）。**不要用 `cov_dump` 读原始 8-bit 计数器做对比**——计数器每 256 次回绕归 0，会漏掉高频边。
2. **重复实验必要**：即使相同 seed，fork 模式的 RNG 也不完全受 `-seed` 控制（有 worker 调度/PID 等随机源），覆盖边和崩溃数波动大，单次结果不可靠。
3. **custom mutator 的盲点要查回退路径**：自定义 mutator 常有"解析失败/随机概率回退到默认变异"的路径，这些回退会改到 custom 本不碰的字段（如 codec 字节），不能简单说"custom 永远到不了某路径"。
4. **等进程结束别用 `pgrep -x`**：进程名被截断到 15 字符会匹配失败；用 `pgrep -f "<唯一参数子串>"`，且保证脚本自身命令行不含该子串（避免自匹配）。
5. **长任务防被杀**：会话空闲会杀掉 nohup 后台任务；用持久目标（goal）维持会话活跃，结束后再手动/自动跑分析。

## 6. 目录结构约定

```
fuzz_exp/
├── {mode}_{i}/            # mode×重复次数 个运行
│   ├── corpus/  art/  capture/  run.log
├── replay/{mode}_{i}/
│   ├── edges.txt         # 覆盖边编号（一行一边）
│   ├── coverage.txt      # 覆盖率
│   ├── crash_report.txt  # 崩溃摘要
│   ├── crash_report_full.md  # 全面崩溃报告
│   └── crash/*.log       # 完整 ASan 输出
└── summary.md            # 汇总
```

## 7. 可复用脚本清单

| 脚本 | 作用 |
|---|---|
| `run_one.sh <mode> <suffix>` | 启动单次 fuzz |
| `analyze_run.py <mode> <suffix>` | 重放 + 覆盖边 + 覆盖率 + 崩溃摘要 |
| `crash_analyze_full.py <mode> <suffix>` | 全面崩溃报告 |
| `summarize.py` | 汇总 |
| `wait_and_analyze.sh` | 等 fuzz 结束自动跑分析 |

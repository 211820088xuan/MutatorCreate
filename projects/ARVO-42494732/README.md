# stage5/ARVO-42494732 —— 目录地图

本目录是「把这个崩溃的通用特征落成变异算子，再跑 A/B 实验」的完整工作区。
**这个目录整体被挂载到容器的 `/exp`**（`docker run -v <此目录>:/exp`）。

---

## 1. 顶层一览

| 路径 | 是什么 | 谁产出 |
|---|---|---|
| `design/` | **设计文档**（3 份）。见 §2 | 生成阶段 |
| `source/` | **崩溃版本的源码**：`in_dxf.c`（12,885 行，commit `ff69eeda`） | `s5_fetch_source.py` |
| `harness/` | **fuzz target 的源码**：`llvmfuzz.c`（277 行，`LLVMFuzzerTestOneInput` 的定义）+ `dwgfuzz.c`（同目录的另一个 harness，未参与本次编译） | `s5_fetch_source.py` |
| `source_context.json` | 从源码抽出的语义上下文（故障函数 33 行、4 处 free 调用点、`DXF_RETURN_ENDSEC` 宏、`is_dwg_object` 定义） | 同上 |
| `features.json` | 输入：stage4 产出的 **5 个通用特征** | stage4 |
| `mutator.c` | **产物：5 策略变异算子**（1,126 行，权重 default 60% + 各 8%） | 生成 agent |
| `seeds/` | **种子语料**。6 个真实 DXF + 60 个无扩展名的 DXF（后者是另一个会话加的，`run_one.sh` 只复制 `*.dxf`，**当前未被使用**） | 6 个来自 fuzz_exp3 corpus；60 个来源不明 |
| `fuzz_exp/` | **实验结果**。见 §3 | 实验 |
| `build_fuzzer.sh` | 容器内构建带算子的 `llvmfuzz` | — |
| `run_one.sh` | 单次 fuzz（`default` 或 `custom`） | — |
| `run_all.sh` | 6 实例全并行编排（3 轮 × 2 模式） | — |
| `stage5_verify.py` | **四级门禁**：V1 语法 / V2 结构 / V3 自举 / V4 权重 | — |
| `dedup_crashes.py` | 按 ASan 崩溃点去重（`crash-<sha1>` 是按输入命名的，不去重会虚高） | — |
| `summarize.py` | 汇总表 | — |
| `inspect_insert.py` | 检查每个策略把字节插到了哪里 | — |
| `measure_strategy_cov.py` | 逐策略独立覆盖率（强制单个策略跑 N 秒） | — |
| `drv.c` | 单独调用 `LLVMFuzzerCustomMutator` 的驱动（配合上面两个检查脚本） | — |
| `mutator_verify.py` | 你早期的三级门禁（已被 `stage5_verify.py` 取代，留作参考） | 你自己的尝试 |
| `replay.py` / `replay_perfile.py` / `compare_cov.py` / `REPLAY.md` | **另一个会话**做的覆盖率口径研究（fork / oneshot / perfile 三种重放） | 另一个会话 |

---

## 2. `design/` 里的三份文档

| 文件 | 作用 |
|---|---|
| `MUTATOR_CONTRACT.md` | **接口契约**：文件形态（只依赖 libc）、5 个策略函数签名、权重（60% / 8%×5）、4 个环境变量（`MUTATOR_OFF` / `CUSTOM_PCT` / `FORCE_STRATEGY` / `TRACE_FILE`）、随机数、边界、不变量（不删字节、单次插入 ≤256 B）、DXF 格式 |
| `landing_plan.json` | **落地设计**：5 个特征各自在 `in_dxf.c` 里对应的代码位置（带行号）、插入什么字节、插在哪、期望走哪条路径到 UAF、置信度、`honest_note`（如实标注哪几条没有已知崩溃证据） |
| `review.json` | **独立审查结论**：`PASS_WITH_FIXES` + 14 条 `must_fix`（按 P1/P2/P3 排序）。它抓出了落地设计里 3 处事实错误 |

---

## 3. `fuzz_exp/` 的结构

**统一约定：每次运行一个目录，内部固定四件**

```
fuzz_exp/
├── llvmfuzz                    74 MB，**6 次运行共用这一个二进制**
├── RESULT.md                   实验结论（含去重后的唯一崩溃点）
├── summary.json                汇总（执行次数 / 覆盖 / 崩溃数 / 重放口径）
├── crash_dedup.json            去重明细（每个崩溃文件 → 崩溃点）
├── replay_results.json         重放结果
├── replay_summary.md           重放说明
├── strategy_cov.json           逐策略独立覆盖率
├── run_all.log / nohup.log     编排日志
├── _stray_artifacts/           早期落在根目录的 8 个 crash- + 2 个 oom-
├── default_1/                  ← 每次运行一个目录
│   ├── corpus/                 本次语料（种子 + 演化出的输入）
│   ├── crash/                  ★ libFuzzer 产物：crash-* / timeout-* / oom-*
│   ├── replay/                 重放与覆盖
│   │   ├── oneshot/            coverage.json + edges.txt（整包一个进程，主指标）
│   │   ├── perfile/            coverage.json + edges.txt + per_file.tsv（逐文件下界）
│   │   └── crash/              每个崩溃的重放日志（旧版 analyze_run 产出）
│   ├── run.log                 libFuzzer 输出（含 cov/ft/exec/s 进度行）
│   └── run_one.out             本次运行的 stdout
├── default_2/  default_3/
└── custom_1/   custom_2/   custom_3/
```

### 崩溃文件在哪

**在每次运行的 `crash/` 下**：

```
fuzz_exp/custom_1/crash/crash-<sha1>
fuzz_exp/default_1/crash/crash-<sha1>
```

数量：default_1/2/3 = 88/19/24，custom_1/2/3 = 96/160/139（合计 **526**）。

`crash/` 里除了 `crash-*` 还会有 `timeout-*` / `oom-*`——它们同属 libFuzzer 的
`-artifact_prefix` 产物，放在一起才不会把 run 目录搞乱。

⚠️ **`crash-<sha1>` 的 sha1 是「输入内容」的哈希，不是崩溃点的哈希**。
同一个 bug 可能产生上百个不同输入——所以必须用 `dedup_crashes.py` 按
`SUMMARY: AddressSanitizer: <type> <file>:<line>` 归并。实测：
default_1 的 88 个文件其实只是 **2 个** bug。

### 两种模式的切换

同一个二进制，只靠环境变量：

```bash
LIBREDWG_MUTATOR_OFF=1   → 100% default
LIBREDWG_MUTATOR_OFF=0   → 60% default + 5×8% 自定义
```

### 读取 crash 的脚本都做了兼容

`summarize.py` 与 `dedup_crashes.py` 里都有：

```python
def crash_dir(d):
    """crash 文件可能在 run 根目录（旧），也可能在 crash/ 子目录（新）"""
    c = os.path.join(d, "crash")
    return c if os.path.isdir(c) else d
```

---

## 4. 一次完整跑法

```bash
# 构建（容器内）
docker exec libredwg-exp bash /exp/build_fuzzer.sh

# 门禁（必须 PASS 才允许跑实验）
docker exec libredwg-exp python3 /exp/stage5_verify.py \
    --mutator /exp/mutator.c --seed /exp/seeds/sample_r14.dxf \
    --binary /exp/fuzz_exp/llvmfuzz \
    --expect-file in_dxf.c --expect-line 12267 --require-hit 0

# 实验（6 实例并行，30 分钟）
docker exec libredwg-exp bash /exp/run_all.sh 1800 3

# 汇总 + 去重
python3 summarize.py "$PWD/fuzz_exp"
docker exec libredwg-exp python3 /exp/dedup_crashes.py /exp/fuzz_exp
```

---

## 5. 两个会话在同一目录里写过（解释结构为什么乱）

| 时间 | 谁 | 产出 |
|---|---|---|
| 10-27 15:50–16:17 | 你（手动探索） | `drv.c`、`insert.py`、`mutator.c` 早期版、`mutator_verify.py` |
| 10-28 15:26–16:45 | 我 | `design/`、`source/`、`mutator.c`（5 策略版）、门禁、6 实例实验 |
| 10-28 17:10–17:44 | **另一个会话** | `replay_perfile.py`、`compare_cov.py`、`replay.py`、`REPLAY.md`、`oom-*` |

`compare_cov.py:30` 写的是 `RUNS = [default_1..5] + [custom_1..5]`，
即它按 **5 次重复**设计，而现有实验只跑了 3 次——所以它后续可能还会生成 `default_4/5`。

**因此本目录暂不做深度重排**（会把另一个会话的脚本路径打断）。
若要重排，建议先确认那个会话结束。

# mutator_create 项目交接（入口）

> ⚠️ **2026-11-02 状态说明**：原计划放在 `HANDOFF/00–05 + PROMPT.md` 的 6 册详细文档**已丢失**
> （`HANDOFF/` 目录只剩 `runs/`；已尝试全盘查找、无备份、无回收站）。
> 本文件已按 `HANDOFF/runs/PHASE4_DOC_CORRECTIONS.md` 的 C1–C10 修正**重写**，
> 是当前唯一幸存的总结文档。

---

## 怎么读

| 你的目的 | 读 |
|---|---|
| **项目全貌 + 目标 + 数据字典 + 各阶段细节** | [`docs/REPORT.md`](docs/REPORT.md)（711 行，Q1–Q12 完整调查，含逐字段说明） |
| 本轮的四个阶段报告 | [`HANDOFF/runs/PHASE1_REPORT.md`](HANDOFF/runs/PHASE1_REPORT.md)（重跑 n=5 + DXF-only）<br>[`HANDOFF/runs/PHASE2_REPORT.md`](HANDOFF/runs/PHASE2_REPORT.md)（trigger_condition 预筛）<br>[`HANDOFF/runs/PHASE3_REPORT.md`](HANDOFF/runs/PHASE3_REPORT.md)（**路径 B：构造型算子**）<br>[`HANDOFF/runs/PHASE4_DOC_CORRECTIONS.md`](HANDOFF/runs/PHASE4_DOC_CORRECTIONS.md)（10 条文档修正） |
| 原始流水线文档 | `PIPELINE.md`（1,018 行，§0–§6；§7/§8/§9 是用户自己删的，别恢复） |
| 单次 / n=5 实验旧结论 | `v2/experiment/README.md`、`v2/experiment/REPS.md` |

---

## 三句话版本

1. **在做什么**：从 1,154 条已复现崩溃归纳通用特征，落到具体项目生成 custom mutator，目标是比 libFuzzer 自带变异更容易触发目标崩溃。
2. **验收标准只有一条**：**custom vs default 的 A/B 对照**里 custom 更好。不是"找到新 bug"，不是"覆盖率涨了"。
3. **当前状态（2026-11-02 更新）**：管道闭环、门禁全绿（V1–V4 `pass`、pytest 4 passed）。
   在**剥段种子**（无 `OBJECTS` 段）上，改造后的构造型算子把目标从"够不着"变成"稳定命中"：
   **default 3 / 1,018,452 execs vs custom 675 / 609,670 execs，RR = 375.9，CI [120.9, 1168.3]**。

---

## 关键数字（2026-11-02 实测）

### 路径 B：构造型算子（**本轮唯一验收口径**）

| 口径 | 剥段种子 A/B（300 s × 5 rep） | 现种子回归（150 s × 5 rep） |
|---|---|---|
| default 命中 / execs | **3 / 1,018,452**（0.29/100k） | 36 / 45,136（79.76/100k） |
| custom 命中 / execs | **675 / 609,670**（110.72/100k） | 27 / 33,477（80.65/100k） |
| RR（95% CI） | **375.86 [120.92, 1168.34]** | 1.011 [0.61, 1.67] |
| 覆盖率比（中位） | **0.820** | 1.023 |
| 唯一点数 | default [0,0,0,1,1] / custom [1,1,1,1,1] | default [2,2,2,1,1] / custom [1,2,1,1,2] |

**结论**：构造型在**结构不存在**的场景把目标从"几乎够不着"变成"稳定命中"；
在**结构存在**的原场景**没有变差**（RR 1.011，CI 含 1）。

### 算子的能力边界

| 输入 | 改前（替换型） | 改后（构造型） |
|---|---|---|
| 含 `OBJECTS` 的 DXF | CHANGED 500/1000，DISTINCT 500 | CHANGED 500，DISTINCT 500 |
| **剥掉 `OBJECTS` 的 DXF** | **CHANGED 0** | **CHANGED 500，DISTINCT 500** |
| DWG | CHANGED 0（路由到 default） | CHANGED 0（路由到 default） |

### 1A / 1B（路径 C 被否）

| 组 | default 率/100k | custom 率/100k | RR（95% CI） | 配对胜出 |
|---|---|---|---|---|
| 1A 复跑（现种子，150 s×5） | 95.54 | 108.09 | **1.131 [0.72, 1.78]** | 2/5 |
| 1A 旧值（2026-11-01） | 96.21 | 91.77 | 0.954 [0.61, 1.48] | 2/5 |
| **1B DXF-only（去掉 DWG 种子）** | 26.52 | 11.70 | **0.441 [0.28, 0.69]** | **0/5** |

- **1B 的 default 在 DXF-only 上反而更快**（426k vs 196k execs），custom 显著更差 → **路径 C（去掉 DWG 种子）作为"放大效应量"的手段失败**。
- DWG 没有从 DXF 变异长回来（`rep01/default` 语料 741 个里 DWG 只 0.1%，且已查明是 DXF 变异后首两字节变成 `AC` 的副产物，非种子泄漏）。
- 1A 与旧值**符号相反**（0.954 → 1.131），两次 CI 都含 1 → 该配置下效应量在噪声以下。

---

## 7 条必须知道的（2026-11-02 修正后）

1. **a001 改前是 default 的真子集**：只在 `OBJECTS` 段存在时起作用（`v2/mutator.c:129`、`:131` 直接 `return Size`），最多增长 63 字节（`:150`）；default 的崩溃输入有插入（164,002 > 127,870）和拼接（`POLYLINXRECORD`）。→ 这是必须改构造型的理由。
2. **构造路径只在 DXF 上生效**：`is_dxf_format()` 把 DWG/JSON 全路由到 default。DWG 那 49% 语料仍然只有 default。
3. **构造型的代价是覆盖率**：剥段种子上覆盖率比 0.820（每 2 次迭代塞一个段，语料被结构主导）。
4. **`dimensions` 在 stage5 里零消费**：7 个维度名在整个 stage5 没有真读取。改键名只需管 stage3 合并轮与 stage4 prompt。
5. **`reassigned_between` 不是"数据没有"**：`interpretation` 里 121 条 UAF 有 **41 条确定值**（`True` 25 / `False` 16）。stage3 的 `unknown` 是 LLM 自己写的；`跨函数陈旧对象访问` 的多数是 `True`，却被写成 `unknown`。
6. **三配置横向对比（0.60× / 1.33×）不可用**：配置 A/B 的日志已被 `rm -rf` 删除；同一 default 配置的密度波动是 **5.6 倍**。
7. **`run_reps.sh` 会覆盖 `reps/`**：跑前必须 `ps` 查残留进程，跑完必须立刻 `cp -a reps reps_<tag>`。旧 n=5 的 `rep05` 就是这么被覆盖的（`summary.json` 记 1,391，现存 `run.log` 12,178）。

---

## 五条硬约束（用户原话）

1. 不要机械化——候选发现的主力是 **agent + 控制流工具**。（`trigger_condition` 预筛只是"有没有落点"的筛子，不判断"是不是真 UAF"。）
2. 自己实现 agent，**不要 shell 出去调 `claude` 之类的 CLI**（调项目自己的 DeepSeek 管线是允许的）。
3. `PIPELINE.md` 的 §7/§8/§9 是用户自己删的，**不要恢复**。
4. 不得覆盖 V1 基线：顶层 `mutator.c`、`fuzz_exp/`、`fuzz_exp2/`。
5. 报表给表、少写散文（"数字差额不用解释，给出一些数据就行了"）。

---

## 下一步（优先级）

| 优先级 | 内容 | 依据 |
|---|---|---|
| **P1** | **降构造频率**（段不存在时只以 1/4 概率构造），把覆盖率比从 0.820 拉回 ≥0.95 且不损失命中率 | 第 3 条 |
| P2 | 权重按输入格式分配（DWG 仍无策略，49% 语料只有 default） | 第 2 条 |
| P3 | 补算 `cross_frame_count`；把 `reassigned_between` 从 `interpretation` 传进 stage3 | 第 5 条 |
| P4 | stage4 加 `differentiator`（必填，取自 stage3 维度）+ "维度向量相同就合并" 硬校验 | `docs/REPORT.md` §Q10 |

---

## 关键产物位置

```
mutator_custom/stage5/ARVO-42494732/
├── mutator.c                    # V1 基线（1126 行，5 策略，60/40）— 别删
├── fuzz_exp/ fuzz_exp2/         # V1 实验 — 别删
├── source_context.json          # 已加 testcase_path（V4 闭环）
├── seeds/                       # 6 DXF + 2 DWG + _fuzzer_corpus/(379 个旧污染)
└── v2/
    ├── mutator.c                # ★ 构造型算子（294 行 / 9,717 字节）
    ├── mutation_plan.json       # v5：operation=ensure_record_structure + construct
    ├── target_surface.json      # 六步证据链（6/6 complete）
    ├── feature_pipeline.json    # 5 特征 × 6 阶段（4 个 not_applicable）
    ├── features/VERDICTS.json   # 5 个特征的判定记录
    ├── verification.json        # V1–V4 全 pass
    └── experiment/
        ├── gate_seeds/          # 4 个剥段种子（门禁固件，勿放进 seeds/）
        ├── strip.py             # 剥段脚本
        ├── reps_n5_r1/          # 旧 n=5（2026-11-01）
        ├── reps_n5_r2/          # 1A 复跑
        ├── reps_n5_dxfonly/     # 1B DXF-only
        ├── reps_pathB/          # ★ 路径 B 的剥段种子 A/B
        └── reps_after_pathB/    # 路径 B 的现种子回归
```

---

## 工作纪律

- 改完代码必须跑：`cd /root/gyx/mutator_create && python3 -m pytest pattern_analysis/tests/test_stage5_v2.py -q`（应 **4 passed**）
- 容器 heredoc 不会被转发：脚本写到挂载目录，再 `docker exec … python3 /exp/xxx.py`
- 实验二进制在**主机**也能直接跑（ELF x86-64，实测可打印 libFuzzer banner）
- 磁盘紧张（95%）：每组 reps 只保留一份快照，别叠副本

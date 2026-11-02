# 重复对照实验（n=5，全并行）

10 个 run（5 rep × 2 臂）**同时启动**，16 核各占一核，150 s/run，总耗时 3 分钟。
种子：6 DXF + 2 DWG。两臂共享同一时间窗，时间漂移影响一致。

## 每次 rep

| rep | default 率/100k | custom 率/100k | 比值 |
|---|---|---|---|
| rep01 | 63.71 | 72.72 | 1.14× |
| rep02 | 125.04 | 195.50 | 1.56× |
| rep03 | 103.47 | 73.63 | 0.71× |
| rep04 | 71.87 | 64.64 | 0.90× |
| rep05 | 359.45 | 71.26 | **0.20×** |

## 合并

| | default | custom |
|---|---|---|
| 目标崩溃 | 50 | 33 |
| execs | 51,967 | 35,960 |
| 率 | 96.21 / 100k | 91.77 / 100k |

**RR = 0.954，95% CI = [0.61, 1.48] → CI 含 1，没有证据表明 custom 增强了。**
配对胜出 **2/5**，中位比值 **0.90×**。

## 对异常值敏感

rep05 的 default 只跑了 **1,391 execs**（exec/s 塌到 9），却有 5 次目标崩溃 → 359/100k，
是明显的离群点。去掉它之后：

**RR = 1.102，95% CI = [0.68, 1.78] → 仍然不显著。**

所以结论不是"变差"，而是"**看不出来**"。

## 覆盖率没有损失

custom/default 的覆盖率比：中位 **0.971**，范围 [0.911, 1.078]。
（50% default 的混合策略确实把之前"覆盖率掉到 85%"的问题解决了。）

## 但广度变窄

| 臂 | 每次 rep 的唯一崩溃点数 |
|---|---|
| default | 2, 3, 2, 1, 2 |
| custom | **1, 1, 1, 1, 1** |

custom **每次都只命中同一个目标 UAF**；default 还多找到 `SEGV @ in_dxf.c:971`（一个真实的 NULL 解引用：
`dxf_read_CMC` 只检查了 `color` 没检查 `pair`）。

## 结论：这个 bug 对 default 来说太容易了

default 自己就有 **96 / 100k** 的命中率（约每 1,000 次执行命中一次）。
**前提不成立**——"需要特殊变异才够得着"对这个目标不成立，所以没有提升空间。

要证明增强，需要选一个 **default 很难碰到的目标**，例如：
- 去掉含 OBJECTS 段的种子（让 default 很难构造出合法段）
- 或者换一个前置条件更深的 UAF（需要连续两次结构正确的变异）

## 复现

```bash
docker exec libredwg-exp bash /exp/v2/experiment/run_reps.sh 150 5
docker exec libredwg-exp python3 /exp/v2/experiment/analyze_reps.py \
    /exp/v2/experiment/reps --binary /exp/v2/experiment/llvmfuzz \
    --json-out /exp/v2/experiment/reps/summary.json
```

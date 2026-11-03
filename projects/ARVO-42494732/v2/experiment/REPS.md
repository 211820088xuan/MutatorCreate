# 重复对照实验（n=5，全并行）

> ## ⚠️ 2026-11-02 状态修正：本文数字已全部过期
>
> 1. **rep05 已无法复核**：`rep05/default/run.log` 现存 12,178 execs，本文记的是 1,391
>    （那次运行的 `exec/s` 塌到 9，是损坏运行）。
> 2. **`-seed=1` 缺陷**：`run_reps.sh` 原本对所有 run 硬编码 `-seed=1`，5 个 rep 不是独立样本。
>    实测本文这组的 38 个崩溃文件只有 **13 个唯一 sha1**（跨 rep 重复 25 个）。
>    → **96.21 vs 91.77 与 `RR = 0.954` 的 CI 偏窄，不能当 5 次独立重复。**
> 3. 已改为逐 rep 变 seed（`-seed=$((SEED_BASE + r))`）。目前只有 `reps_pathB_r2`
>    是真正独立的（646 个崩溃文件 646 个唯一 sha1）。
> 4. 下表作为**历史记录**保留。当前有效口径见 `docs/ARCHITECTURE.md` §8。

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

要证明增强，需要选一个 **default 很难碰到的目标**。

**2026-11-02 更新**：

- ~~去掉含 OBJECTS 段的种子~~ **已实测作废**：剥段后目标对两臂都不可达——
  default 在 300 s × 5 rep 里只命中 3 次 / 1,018,452 execs，而当时那版算子
  在剥段种子上 `CHANGED = 0/1000`（完全空转）。
- **已实施的是路径 B**：把算子从"替换型"改成"构造型"——段不存在时按
  `construct.sequence` 插入 `0/SECTION + 2/OBJECTS + 0/<随机名> + 0/ENDSEC`。
  改造后在剥段种子上 `CHANGED` 从 **0 → 500**（DISTINCT 500）。
  这条路径是否真的赢过 default，需要独立的 n=5 重测（见下）。

## 复现

```bash
docker exec libredwg-exp bash /exp/v2/experiment/run_reps.sh 150 5
docker exec libredwg-exp python3 /exp/v2/experiment/analyze_reps.py \
    /exp/v2/experiment/reps --binary /exp/v2/experiment/llvmfuzz \
    --json-out /exp/v2/experiment/reps/summary.json
```

# V2 对照实验

同一二进制，`LIBREDWG_MUTATOR_OFF` 切换：`=1` → 100% default；`=0` → V2 算子（50% default + 50% 特征）。
180 s × 2 臂。种子：6 个 DXF + 2 个 DWG。

## 权重（实测）

```
CHANGED 10000 / 20000 = 50.0%
```

算子的分发器（`mutator.c`）：

```c
if (Size >= 2 && Data[0] == 'A' && Data[1] == 'C')   return LLVMFuzzerMutate(...);  /* 二进制 DWG */
if (Size >= 1 && Data[0] == '{')                     return LLVMFuzzerMutate(...);  /* JSON */
unsigned r = Seed % 1000;
if (r < 500)                                         return LLVMFuzzerMutate(...);  /* default 50% */
return mutate_a001(Data, Size, MaxSize, Seed);                                      /* 特征 50% */
```

非 DXF 输入直接回退 default——因为唯一的 found 特征（`uaf-llm01`）只对 DXF 记录有意义。

## 结果（2026-11-02，生成器重试通过后的 mutator）

| 口径 | default | custom | 比值 |
|---|---|---|---|
| execs | 7,875 | 9,730 | 1.24× |
| exec/s | 54 | 71 | 1.31× |
| cov | 26,755 | 24,676 | 92.2% |
| ft | 47,411 | 40,990 | 86.5% |
| corpus | 469 | 500 | 1.07× |
| 崩溃文件 | 2 | 3 | — |
| 唯一崩溃点 | 1 | 1（同一处） | — |
| **目标触发密度** | 25.40 / 100k | **30.83 / 100k** | **1.21×** |

**RR = 1.21，95% CI ≈ [0.20, 7.3]；事件数只有 2 vs 3。**

## 这个结果不能当结论

1. **事件数太少**：2 vs 3 个崩溃。任何比值都落在极宽的置信区间里。
2. **单次运行**：同一配置在不同次运行间的基线波动本身就可达 2–3 倍。
3. **两臂命中的是同一个唯一崩溃点**（`in_dxf.c:12267`）——没有发现新的漏洞。

历史参考（不同 mutator / 不同种子集，**不可与前表直接比较**）：

| 期 | default | custom | 目标密度比 | 说明 |
|---|---|---|---|---|
| 早期 | 129,348 | 3,555 | — | 100% 单策略，无 default：exec/s 塌到 18 |
| 中期 | 13,049 | 6,533 | 1.33×（137.94 vs 183.68） | 50% + 5×10%，但 4 个 generic 策略是哑弹 |
| 本期 | 7,875 | 9,730 | **1.21×**（25.40 vs 30.83） | 只留 1 个 found 特征，50/50 |

## 要证明"增强了"，还缺什么

| 缺口 | 做法 |
|---|---|
| 统计功效 | **≥5 次重复 × 2 臂**，配对检验，报中位数与置信区间 |
| 新漏洞 | 扩到其他项目（ARVO 里还有 5,223 条未尝试的崩溃） |
| 算子开销 | 当前 **0.28 ms/次调用**（440 行、要扫输入定位记录），是 default 单次执行（约 1.3 ms）的 21%；p95 需要关注 |

## 复现

```bash
# 容器（已构建好 libredwg 的镜像 + 单项目工作区挂到 /exp）
docker run -d --name libredwg-exp -w /src \
  -v /root/gyx/mutator_create/projects/ARVO-42494732:/exp \
  libredwg-exp:with-libredwg-20261102 sleep infinity

docker exec libredwg-exp bash /exp/v2/experiment/build.sh
docker exec libredwg-exp bash /exp/v2/experiment/run_matrix.sh 180
docker exec libredwg-exp python3 /exp/v2/experiment/summarize.py \
    /exp/v2/experiment --binary /exp/v2/experiment/llvmfuzz
```

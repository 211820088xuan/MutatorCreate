# R28 报告

日期：2026-11-08
目标：候选 → 策略 → A/B（libredwg + libxml2）。

## 先纠正一个判定错误（用户指出）

R26b/R27 把「人工核实为假」当成了失败信号。**这偏离了口径**：

> 「如果源码中没有错误，我们只是找到了可能会发生错误的地方，那这样其实就可以了，
> 未必是设计问题，可能是源码中本就没有错误。」

**站点不要求是真崩溃点。唯一的验证器是 A/B。** 本轮就是去跑它。

**配置用 R26b 那版**（标尺 high、候选 42/77），**R27 的 `code`/`expr`/`access` 退回**
（它让标尺丢了、候选塌了 7–11 倍）。

---

## 步骤 0 · libxml2 可行性

### ① agent 的候选命中几条已知崩溃

libxml2 的 `facts`：**34 条**（12 个文件、**31 个行号**）。

R26b 的 **44 条**候选里，**命中已知崩溃行号的只有 1 条**：

```
  tree.c:3698→3704  (medium)
```

**→ "复现已知崩溃"这个信号在 libxml2 上非常弱。**

### ② harness

`projects/ARVO-42533950/harness/` **有现成的** ✓：

| 文件 | 行数 |
|---|---:|
| `api.c` | 3,497 |
| `html.c` | 123 |
| `regexp.c` | 53 |
| `schema.c` | 52 |
| `uri.c` | 105 |
| `valid.c` | 137 |
| `xinclude.c` | 114 |
| `xml.c` | 153 |
| `xpath.c` | 76 |

`fuzz_target.marker` = `LLVMFuzzerTestOneInput` ✓，入口在 `api.c`。

### ③ fuzz 环境

| 项 | 状态 |
|---|---|
| OSS-Fuzz 基础设施 | ✅ `/root/gyx/oss-fuzz` 在（`build/`、`infra/` 都有） |
| **libxml2 的 docker 镜像** | ❌ **没有**（只有 `n132/arvo:42494732-vul`=libredwg、`42475028-vul`=pcre2） |
| 宿主机 `/src` `/out` | ❌ 空（那是 libredwg 容器里的） |

**→ 要从零搭**：`infra/helper.py build_image libxml2` + `build_fuzzers`。
**镜像约 4.5 G**（参照 libredwg 的 `libredwg-exp:with-libredwg-20261102` = 4.48 GB）。

### ④ 种子

**没有**。需要 OSS-Fuzz 的 `libxml2/seed_corpus.zip`（要下载），或自己造。

### ⑤ 预估搭环境要多久 —— **和磁盘**

| 项 | 估计 |
|---|---|
| 拉 base 镜像 + `build_image libxml2` | **40–60 分钟** |
| `build_fuzzers`（带 ASan） | **20–30 分钟** |
| 种子下载 + 验证 | 10 分钟 |
| **合计** | **约 1.5 小时** |

**但真正的阻塞是磁盘**：

```
  /dev/vda2   100G   94G   6.1G  (94% 已用)
  新的 libxml2 镜像 ≈ 4.5 G   →   装完只剩 ~1.6 G
  A/B 两个臂 2 小时 × 2 的 corpus/crash 还要几个 G
```

**→ 磁盘不够。**

### 判定：**libxml2 本轮不跑 A/B**

三个理由（按重要性）：

1. **磁盘**：6.1 G 装不下 4.5 G 的镜像 + 2 小时的 A/B 产物（铁律要求"不够就先清 `workspace/`"，
   但 workspace 只有 1.5 G，清了也只到 7.6 G）；
2. **环境**：要从零搭 1.5 小时，且没有任何 libxml2 的 fuzz 产物可复用；
3. **目标信号太弱**：44 条候选里**只有 1 条**命中已知崩溃行号 —— 就算跑起来，"复现"那一栏也只能数这 1 条。

**→ 按用户给的 fallback：libredwg 跑完整流程（步骤 1–4）；libxml2 只做到步骤 3（生成算子），A/B 留到下一轮。**

### 顺带：libredwg 那边的可行性（确认过）

| 项 | 状态 |
|---|---|
| 容器 `libredwg-exp` | ✅ Up 5 days |
| 二进制 `a416b44d` | ✅ 在（`experiment/llvmfuzz`） |
| `run_reps.sh` | ✅ 在，**已加"reps 非空则拒跑"的保护** |
| 剥段种子 | ✅ `projects/ARVO-42494732/seeds/*.dxf` **6 个** |
| `reps_r9_final` 基线 | ✅ 617/617 唯一 sha1 |
| 候选 | ✅ R26b 的 42 条（`docs/runs/r26b/post2/paired.json`） |
| 已知崩溃命中 | ✅ 标尺 `12284→12267` **在候选里**（high） |

**libredwg 完全可行，2 小时 A/B 没问题。**

### ⏸ 停止点：等确认

确认后进步骤 1：两个项目各排一次序、选前 5。
（libxml2 也排序 —— 虽然不跑 A/B，但那 1 条命中已知崩溃的会排第一，可以验证排序逻辑。）

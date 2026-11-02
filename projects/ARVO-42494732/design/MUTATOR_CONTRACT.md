# custom_mutator.c 接口契约（v1）

生成 agent 必须严格遵守。验证脚本 `stage5_verify.py` 依赖以下约定。

---

## 1. 文件形态

- 单文件 C11，**只依赖 libc**：`<stdint.h> <stddef.h> <string.h> <stdlib.h> <stdio.h>`
- **不得** include libredwg 的头文件，**不得**调用 libredwg 内部函数
- 只导出 `LLVMFuzzerCustomMutator`；`LLVMFuzzerMutate` 用 extern 声明

```c
extern size_t LLVMFuzzerMutate(uint8_t *Data, size_t Size, size_t MaxSize);
size_t LLVMFuzzerCustomMutator(uint8_t *Data, size_t Size, size_t MaxSize, unsigned int Seed);
```

---

## 2. 策略函数

5 个特征各对应一个策略函数：

```c
static size_t strat_0(uint8_t *D, size_t n, size_t max, uint32_t *rng);
static size_t strat_1(uint8_t *D, size_t n, size_t max, uint32_t *rng);
static size_t strat_2(uint8_t *D, size_t n, size_t max, uint32_t *rng);
static size_t strat_3(uint8_t *D, size_t n, size_t max, uint32_t *rng);
static size_t strat_4(uint8_t *D, size_t n, size_t max, uint32_t *rng);
```

- 返回新的长度，**必须 `<= max`**
- 若该策略在当前输入上不适用，**返回 0**（表示"放弃"，由上层回退到 default）
- 不得写越界，不得返回大于 `max` 的值

---

## 3. 权重（硬性要求）

| 来源 | 权重 |
|---|---|
| `LLVMFuzzerMutate`（default） | **60%** |
| 每个策略 | **40% / 5 = 8%** |

实现（整数运算，避免浮点）：

```c
unsigned r = rng_next(&s) % 100u;
if (r < 60u) return LLVMFuzzerMutate(Data, Size, MaxSize);
unsigned k = (r - 60u) * 5u / 40u;   /* 0..4，均匀 */
```

**注意**：`(r-60)*5/40` 对 r=60..99 映射到 k=0..4，每个 k 恰好 8 个取值 → 精确 8%。

---

## 4. 环境变量（测试钩子，必须实现）

| 变量 | 作用 |
|---|---|
| `LIBREDWG_MUTATOR_OFF=1` | **100% 走 default**（A/B 对照用） |
| `LIBREDWG_CUSTOM_PCT=<0..100>` | 覆盖自定义比例；默认 40（即 default 占 60%） |
| `LIBREDWG_FORCE_STRATEGY=<0..4>` | 强制某个策略，**忽略权重与 PCT** |
| `LIBREDWG_TRACE_FILE=<path>` | 每次调用追加一行：`D` / `S<k>` / `F<k>` |

**trace 语义**（验证脚本据此统计权重）：

| 标记 | 含义 |
|---|---|
| `D` | 按权重选了 default |
| `S<k>` | 按权重选中策略 k，且成功产出 |
| `F<k>` | 按权重选中策略 k，但策略返回 0，回退到 default |

**为什么要区分 S 和 F**：策略在不适用的输入上会返回 0（回退）。若不区分，回退会被误算成 default，导致权重统计失真。

**强制模式的语义（重要）**：设置 `LIBREDWG_FORCE_STRATEGY=k` 时，**只调用策略 k，不回退 default**。
若策略 k 返回 0，则**直接返回原长度**（输入不变）。
这样验证脚本能区分两件事：
- 输出 == 输入 → 该策略在当前种子上**不适用**
- 输出 != 输入 → 该策略**生效**了

---

## 5. 随机数

- 用 `Seed` 派生的**本地** xorshift32
- **禁止** `rand()` / `srand()` / `random()`：会与 libFuzzer 抢全局状态，破坏可复现性

```c
static uint32_t rng_next(uint32_t *s) {
  uint32_t x = *s ? *s : 0x9e3779b9u;
  x ^= x << 13; x ^= x >> 17; x ^= x << 5;
  *s = x; return x;
}
```

---

## 6. 边界条件

- 任何写操作前检查 `Size + ins <= MaxSize`
- `Size < 8` 时直接走 default
- **不得**假定输入以 `'\0'` 结尾（DXF 是二进制读的）
- **不得**假定 DXF 结构完整：所有 `find` 类操作都要处理"找不到"

---

## 7. 不变量

- **不得删除已有字节**（只插入，或做等长原位替换）→ 保证 `ENDSEC` 数量不变（V2 会检查）
- 单次变异插入量 **<= 256 字节**（v2 修订，原为 64）
- 返回值 `> 0`；若所有路径都不可行，返回 `LLVMFuzzerMutate(Data, Size, MaxSize)`

> **v2 修订说明（为什么从 64 放宽到 256）**
>
> 用对齐 pair 解析实测 8 个真实种子：OBJECTS 段内**最小的完整对象块是 83 字节**
> （分布 83 / 105 / 115 / … ）。64 字节的上限导致 `strat_3`（"整块复制一个对象"）
> 在所有真实种子上**100% 不适用**，策略永远返回 0 → 8% 的变异预算被浪费在 no-op 上。
>
> 放宽到 256 后：83–115 字节的完整对象块可以整块复制；相对 12–38 KB 的输入仍 < 2%，
> 依然满足"变异是局部的"这一初衷。上限是**硬约束**，超过必须放弃该次变异。

---

## 8. DXF 输入格式（供策略参考）

```
0            ← group code（整数，单独一行）
SECTION      ← value（下一行）
2
HEADER
...
0
ENDSEC
```

- 一个 "pair" = `group code` 行 + `value` 行
- 崩溃相关的段是 `OBJECTS`，以 `0 / OBJECTS` 开始，以 `0 / ENDSEC` 结束
- `dxf_read_pair` 按行读取，返回 `Dxf_Pair { code, value.s }`
- 若某行不是合法整数，group code 解析会失败 → 该 pair 为 `NULL` 或提前结束

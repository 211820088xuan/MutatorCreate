# 四类崩溃的"必要条件"枚举 + Mutator 设计

---

# 阶段划分

| 阶段 | 名称 | 内容 | 状态 |
|---|---|---|---|
| **0** | **数据补充阶段** | P0 深度查询 → 合并进 facts → 重跑 interpretation → P1 源码切片 | 🔄 **进行中**（P0 165/476） |
| **1** | **阶段 3：LLM 提取共性** | 批量调用脚本 + 跨批汇总 prompt + 跑四类全量 | ⏸️ 待开始 |
| **2** | **阶段 4：抽象通用特征** | 把形态抽象成不含项目信息的特征 | ⏸️ 未开始 |
| **3** | **阶段 5：生成 mutator** | 特征落到具体项目，生成 mutator | ⏸️ 未开始 |

**数据补充阶段完成后立即进入阶段 3。**

---

# 零、字段完整度现状与补充计划

## 0.1 当前字段覆盖率（实测）

| 字段 | 现在 | 说明 |
|---|---|---|
| `entity.decl`（变量声明） | 45-56% | 只对有 entity 名的样本跑 |
| `entity.name`（变量名） | 58-72% | 依赖 dataflow 的 ids |
| `crash.line_code`（故障行代码） | 60-77% | 依赖 dataflow 的 call_codes |
| `alloc.size_expr`（分配大小表达式） | **0%** | 从未提取 |
| `sites` 含 malloc | 2-8% | 漏掉包装函数（如 `xmlFuzzMalloc`） |
| `free_related` | 1-2% | 只在 ≥2 次 free 时计算，UAF 通常只有 1 次 free |
| `alloc.size_bytes`（HBO 缓冲区大小） | **0%** | 报告里没有 region 大小 |
| `guards`（边界检查） | 22-40% | 只查了故障行 |
| `reachability` | 43-60% | 只到参数级 |

**这些低覆盖大部分是实现太浅，不是数据没有。**

## 0.2 补充计划

### P0：一次 CPG 查询（不需要源码）

| 补充字段 | 现在 → 之后 |
|---|---|
| `crash.line_code` / `line_ids` / `line_calls` | 60-77% → ~95% |
| `entity.name` / `decl` / `assignments` | 58-72% / 45-56% / 无 → ~90% / ~80% / ~80% |
| `sites`（含包装函数）+ `alloc.size_expr` | 2-8% / 0% → ~90% / ~85% |
| `guards`（函数内所有比较） | 32% → ~60% |
| `func.params` | 无 → 100% |

### P1：源码切片（需要重新拉取 40 个仓库）

| 补充字段 | 现在 → 之后 |
|---|---|
| `func.snippet`（故障行 ±20 行原文，`>>>` 标注故障行） | 无 → ~90% |

**为什么要拉仓库**：CPG 里 `method.code` 只保留前 1000 字符（签名 + 开头几行），故障行常在中间看不到；建 CPG 时的源码副本已被删除。ARVO 数据库记录了全部 6138 条的 `repo_addr`，用 `git fetch --depth 1` 浅拉取单个 commit 即可（约 4-8 GB）。

### 补充后对必要条件的影响

| 必要条件 | 现在 | P0+P1 后 |
|---|---|---|
| UAF N4/N5（中间无重赋值/重分配） | 2% | ~80% |
| UAF N6/N9（free 实参、是否置空） | 部分 | ~90% / ~80% |
| HBO N3（缓冲区大小） | 0% | ~85% |
| HBO N5/N6/N7（基址/下标/元素类型） | 部分 | ~85% |
| stack N1/N2/N4（声明/维度/VLA） | 部分 | ~80% |

---

# 一、方法：必要条件枚举

一次崩溃要能被判定为某类，必须**同时**满足 N1 ∧ N2 ∧ ... ∧ Nk。

对每条必要条件问三个问题：

| 问题 | 含义 |
|---|---|
| 这条能从哪里取到？ | 报告 / CPG / 两者 |
| 现在能判吗？ | ✅能 / ⚠️部分 / ❌不能 |
| 判不了怎么办？ | 标"不可判"，不假装 |

---

> **状态含义**：✅ 能判（覆盖率 ≥90%）｜⚠️ 只能判一部分（30-90%）｜❌ 判不了（需额外分析，或原理上不可得）

# 二、heap-use-after-free（121 条）

| # | 必要条件 | 数据来源 | 现能判吗 |
|---|---|---|---|
| # | 必要条件 | 状态 | 依据 / 缺什么 |
|---|---|---|---|
| N1 | 对象是堆分配 | ✅ 能判 | `alloc` 有值 100% |
| N2 | 存在 `free(p)` 调用 | ✅ 能判 | `sites` 里有 free 的 100% |
| N3 | free 在执行上早于解引用 | ⚠️ 只能近似 | 行号比较覆盖 68%；配合 `in_loop`(66%) 可区分"循环迭代"这种行号反序的情况 |
| N4 | 中间无指针重赋值 | ❌ 判不了 | `free_related` 只覆盖 **2%**（仅在 ≥2 次 free 时计算，UAF 通常只有 1 次 free） |
| N5 | 中间无重新 malloc | ❌ 判不了 | 同上 |
| N6 | free 实参是 `p` 本身 | ⚠️ 只能判一部分 | 需要逐个检查 free 调用实参，当前未提取 |
| N7 | 解引用与 free 是同一对象（别名） | ❌ 判不了 | 需要指针分析（CPG 只有语法关系） |
| N8 | 两者在同一可达路径 | ❌ 判不了 | 需要 CFG 可达性分析 |
| N9 | 解引用时未置空 | ⚠️ 只能判一部分 | 需要赋值链分析，当前未提取 |
| N10 | 解引用不在 free 的同一语句内 | ⚠️ 只能判一部分 | 需要语句级顺序，当前只有行号 |

---

# 三、heap-buffer-overflow（526 条）

| # | 必要条件 | 数据来源 | 现能判吗 |
|---|---|---|---|
| # | 必要条件 | 状态 | 依据 / 缺什么 |
|---|---|---|---|
| N1 | 访问对象是堆分配 | ✅ 能判 | `alloc` 有值 95% |
| N2 | 一次访问的字节宽度 | ✅ 能判 | `access.width` 100%，中位 4 字节 |
| N3 | 缓冲区大小 S | ❌ 判不了 | `alloc.size_bytes` 覆盖 **0%**——报告里通常没有 region 大小 |
| N4 | 是否存在边界检查 | ⚠️ 只能判一部分 | `guards` 非空只有 32%（其余是"确实没有检查"或"没提取到"） |
| N5 | 访问基址是 `B` 还是 `B+off` | ⚠️ 只能判一部分 | semantic 的 `idx_base`（正在补） |
| N6 | 下标表达式及其来源 | ⚠️ 只能判一部分 | semantic 的 `idx_expr`（正在补） |
| N7 | 元素类型 | ⚠️ 只能判一部分 | semantic 的 `decl_type`，当前 decl 覆盖 51% |
| N8 | 下标运算是否整数溢出 | ❌ 判不了 | 需要位宽 + 值域分析 |
| N9 | 下标有无符号 | ⚠️ 只能判一部分 | 需要类型符号信息 |
| N10 | 分配大小是否输入控制 | ✅ 能判 | `reachability` 60% |
| N11 | 循环内多次访问累积越界 | ⚠️ 只能判一部分 | `in_loop` 76%，但没有循环上界 |

---

# 四、stack-buffer-overflow（97 条）

| # | 必要条件 | 数据来源 | 现能判吗 |
|---|---|---|---|
| # | 必要条件 | 状态 | 依据 / 缺什么 |
|---|---|---|---|
| N1 | 对象是函数内栈数组 | ⚠️ 只能判一部分 | `entity.decl` 覆盖 56% |
| N2 | 数组声明维度 | ⚠️ 只能判一部分 | semantic 的 `decl_dim`（正在补） |
| N3 | 访问宽度 | ✅ 能判 | `access.width` 100%，中位 4 字节 |
| N4 | 是否 VLA（`char buf[n]`） | ⚠️ 只能判一部分 | semantic 的 `decl_is_vla`（正在补） |
| N5 | 数组所在栈帧 | ⚠️ 只能判一部分 | 需要方法归属信息 |
| N6 | 写入形式（memcpy / 逐字节循环） | ⚠️ 只能判一部分 | 用 `crash.code` 启发式判断 |
| N7 | 栈增长方向 + 覆盖对象 | ❌ 判不了 | 静态分析原理上不可得（依赖 ABI 与运行时布局） |
| N8 | 是否经由 `alloca` | ⚠️ 只能判一部分 | 需要查调用点 |

---

# 五、global-buffer-overflow（61 条）

| # | 必要条件 | 数据来源 | 现能判吗 |
|---|---|---|---|
| # | 必要条件 | 状态 | 依据 / 缺什么 |
|---|---|---|---|
| N1 | 访问对象是全局数组/表 | ⚠️ 只能判一部分 | `entity.decl` 覆盖 53% |
| N2 | 访问宽度 | ✅ 能判 | `access.width` 100%，**中位 1 字节** |
| N3 | 下标表达式及其来源 | ⚠️ 只能判一部分 | semantic 的 `idx_expr`（正在补） |
| N4 | 常量表 vs 可变全局缓冲区 | ⚠️ 只能判一部分 | 需要查声明是否 const |
| N5 | 下标是单字节还是多字节 | ⚠️ 只能判一部分 | 需要类型信息 |
| N6 | 表长是否是 2 的幂 | ⚠️ 只能判一部分 | semantic 的 `decl_dim`（正在补） |
| N7 | 同一输入索引访问多个表 | ❌ 判不了 | 需要跨表的数据流分析 |

**关键实测**：宽度中位 **1 字节**，与 heap/stack 的 4 字节明显不同，说明多为**单字节查表**（`table[c]`）。

---

# 六、Mutator 设计（每类一条，关键代码）

> 原则：mutator 不是"随机变异"，而是**把必要条件变成可操作的变异动作**。
> 每个 mutator 只需要实现"让某条必要条件成立/被破坏"的那一步。

## 6.1 UAF（以"循环内 free 后复用"为例）

```c
/* 让触发 free 的条目多来一次，进入第二次循环迭代 */
size_t LLVMFuzzerCustomMutator(uint8_t *data, size_t size,
                               size_t max_size, unsigned int seed) {
    size_t off, end;
    if (!find_entry_list(data, size, &off, &end)) return size;
    size_t es, ee;
    if (!last_tlv(data, off, end, &es, &ee)) return size;
    size_t elen = ee - es;
    if (size + elen > max_size) return size;
    memmove(data + ee + elen, data + ee, size - ee);
    memcpy(data + ee, data + es, elen);
    size += elen;
    patch_outer_length(data, size, elen);
    return size;
}
```

## 6.2 heap-buffer-overflow（以"下标/长度字段"为例）

```c
/* 放大控制下标的长度字段，越过堆缓冲区 */
size_t LLVMFuzzerCustomMutator(uint8_t *data, size_t size,
                               size_t max_size, unsigned int seed) {
    FieldVec fv;
    if (!find_len_fields(data, size, &fv) || fv.n == 0) return size;
    Field *f = &fv.f[seed % fv.n];
    uint64_t v = read_field(data, f);
    v *= (2 + seed % 3);                 /* 放大 2-4 倍 */
    if (v > f->max) v = f->max;
    write_field(data, f, v);
    return size;
}
```

## 6.3 stack-buffer-overflow（以"定长栈数组 + 循环写"为例）

```c
/* 把循环上界推到常见栈数组尺寸之上 */
size_t LLVMFuzzerCustomMutator(uint8_t *data, size_t size,
                               size_t max_size, unsigned int seed) {
    FieldVec fv;
    if (!find_count_fields(data, size, &fv) || fv.n == 0) return size;
    Field *f = &fv.f[seed % fv.n];
    static const uint64_t kB[] = {16, 32, 64, 128, 256, 512, 1024};
    write_field(data, f, kB[seed % 7] + seed % 4);
    return size;
}
```

## 6.4 global-buffer-overflow（以"单字节查表"为例）

```c
/* 把被当作全局表下标的那一字节改成越界值 */
size_t LLVMFuzzerCustomMutator(uint8_t *data, size_t size,
                               size_t max_size, unsigned int seed) {
    if (size == 0) return size;
    size_t pos = pick_index_candidate(data, size, seed);
    static const uint8_t kV[] = {0xFF, 0x80, 0x7F, 0x40, 0x20, 0x10};
    data[pos] = kV[seed % 6];
    return size;
}
```

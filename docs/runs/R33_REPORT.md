# R33 报告

日期：2026-11-08
目标：验证「执行门禁」可不可行（只做这一步，不改 pipeline）。

---

## 步骤 1 · 工具支不支持 —— ❌ **不支持，而且给出的报告不可靠**

### 实测三轮

| 查什么 | 结果 |
|---|---|
| `-print_coverage=1` | **能跑**，但只打印 `UNCOVERED_FUNC` 清单（4966 个函数） |
| `-print_pcs=1` | **输出 0 个 PC**（没有 `trace-pc-guard` 插桩） |
| `__sanitizer_cov_*` 符号 | 有 22 个（只有 `inline-8bit-counters` 一类） |

### 决定性证据：报告**在说谎**

拿一个**确定会到达** `dxf_objects_read` 的输入（`testcase_uaf_12267.bin`）：

```
回放确认它确实到达：
  SUMMARY: AddressSanitizer: heap-use-after-free
           /src/libredwg/src/in_dxf.c:12267:36 in dxf_objects_read   ← 就在这个函数里

同一份输入跑 -print_coverage=1：
  UNCOVERED_FUNC 总数: 4966
  UNCOVERED_FUNC: hits: 0 edges: 0/32 dxf_objects_read /src/libredwg/src/in_dxf.c:12262
                                       ↑ 把**正在执行的函数**报成 "未覆盖"
```

**→ `a416b44d` 的 `-print_coverage` 不可用。**
这也解释了为什么我先测的 20+20 个产物两臂**到达率都是 0** —— 不是真的没到达，是报告不可信。

### 6 个原始种子也全是 `reach=NO`

同一份不可信报告的结果（每个种子都在 `UNCOVERED_FUNC` 里）—— **同样不能用。**

### 判定：走第三档

| 情况 | 结论 |
|---|---|
| 支持行级 | ❌ |
| 只支持函数级 | ❌（函数级也是坏的） |
| **完全不支持** | ✅ **就是这个** |

**→ 按你给的规则：另编一个带覆盖率的二进制专供门禁用。**
`a416b44d` 和 `reps_r9_final` 不动，新二进制同 pin（`ff69eeda6658`）另起文件名。

---

## 步骤 2 / 3 / 4

**未做** —— 前置条件（能测到执行有没有到达）**不成立**。

用现有二进制测出来的任何到达率都是错的（见上面的决定性证据）。

---

## 汇总

### 本轮结论一句话

**执行门禁这个设计方向本身没问题，但当前二进制 `a416b44d` 测不到「执行有没有到达站点」——
它的 `-print_coverage` 把正在执行的函数报成"未覆盖"，`-print_pcs` 输出 0 个 PC。**

### 下一步（按你给的规则）

**另编一个带 `-fsanitize-coverage=trace-pc-guard` 的二进制**：

- 源码同 pin（`ff69eeda6658`，容器里现成）
- 另起文件名（`llvmfuzz_cov`），**不碰 `a416b44d` / `reps_r9_final`**
- 编完先用 `testcase_uaf_12267.bin` 验：**`dxf_objects_read` 必须显示为已覆盖**，否则新二进制同样不可信
- 然后才谈步骤 2/3/4

**成本估计**：容器里 `libredwg` 已 configure 过，只需重编 fuzzer 那一层 + 加插桩，约 20–30 分钟；
磁盘 16 G 够。

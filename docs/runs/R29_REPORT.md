# R29 报告

日期：2026-11-08
目标：把站点数从 4 降到 2，看能不能过门禁；过了就跑 A/B。

---

## 步骤 0 · 清磁盘

| 清了什么 | 大小 |
|---|---:|
| `docker rm` 三个停着的容器（`libredwg-exp-old`、`libredwg-exp-old-mount`、`modest_mccarthy`） | ~2.0 G |
| `docker rmi libredwg-built:latest`（只被上面那两个 exited 容器用着） | 4.36 G |
| `docker rmi n132/arvo:42475028-vul`（pcre2，本项目不用） | 1.43 G |

**删之前逐个确认过**：
- 三个容器都是 `exited` / `created`（不是 `running`）；
- `libredwg-exp` 用的是 `libredwg-exp:with-libredwg-20261102`，**和 `libredwg-built` 无关**；
- 二进制 `a416b44d` 在**宿主机** `projects/ARVO-42494732/v2/experiment/llvmfuzz`，**不在镜像里**；
- 删完 `docker exec libredwg-exp echo "容器 OK"` ✅。

```
  清理前: 6.1 G 可用（94% 已用）
  清理后: 16 G 可用（85% 已用）   ← 目标 10 G，已超
```

`workspace/`（1.5 G）、`cpg_files/`（9.2 G）、`/tmp/opencode`（1.3 G）**都没动** —— 16 G 够用，不需要冒险。

---

## 步骤 1 · 2 个站点生成

### plan

| # | 站点 | var | 权重 |
|---|---|---|---:|
| a001 | `src/in_dxf.c:12284→12267` | `pair` | 0.25 |
| a002 | `src/encode.c:1391→1393` | `_obj->texts[i]` | 0.25 |

`default 0.5 + 2×0.25 = 1.0`，两个策略平等。

### 结果：**没有报错**（4 站点两次都报错，2 站点一次就过）

```
  [stage5.v2] plan_status=READY  plan=.../mutation_plan.json
    prompt 字符数: 11508（只含 plan + 6 行证据）
    写出 .../mutator.json 和 mutator.c（8679 字节）
    implements: ['a001', 'a002']
```

`mutator.c` **278 行，sha1 `de5eb910`**。

### 分流逻辑（`mutator.c:272-278`）

```c
size_t LLVMFuzzerCustomMutator(uint8_t *Data, size_t Size, size_t MaxSize, unsigned Seed) {
  if (!is_dxf_input(Data, Size)) return LLVMFuzzerMutate(Data, Size, MaxSize);   ← 入口做了格式检查 ✓
  unsigned r = Seed % 1000u;
  if (r < 500u) return LLVMFuzzerMutate(Data, Size, MaxSize);   ← 50% default ✓
  if (r < 750u) return mutate_a001(Data, Size, MaxSize, Seed);  ← 25% a001 ✓
  return mutate_a002(Data, Size, MaxSize, Seed);                ← 25% a002 ✓
}
```

**格式检查在入口** ✓ —— 4 站点那次门禁报的"格式没分流"这次**没有** ✓。

### 🔴 但两个"策略"是**同一个算法**

```c
262: static size_t mutate_a001(...) {
264:   return ensure_record_structure_value_line(Data, Size, MaxSize, Seed, 0x10001u);
265: }
267: static size_t mutate_a002(...) {
269:   return ensure_record_structure_value_line(Data, Size, MaxSize, Seed, 0x20002u);
270: }
```

**a001 和 a002 调用的是同一个函数，只有最后一个 `salt` 参数不同。**

而 `salt` 在 `ensure_record_structure_value_line` 里只影响两处：
```c
  uint32_t rs = (uint32_t)Seed ^ salt ^ 0x9e3779b9u;    ← RNG 种子
  make_random_name(Seed, salt, orig, orig_len, name, &name_len);   ← 生成的名称
```

**→ 两个"策略"是同一策略的两种随机扰动，不是两种形态。**

### 更关键：**a002 的证据链一行都没进代码**

```
  grep -ciE "dictionary|handle|nod|texts|0xC|ACAD_" mutator.c  →  0
```

**a002 的证据链是**：「DICTIONARY 对象、`handle.value == 0xC`、版本 ≥ R2007、条目名 `ACAD_<unstable type>`」——
**生成的代码里没有任何 `handle` / `DICTIONARY` / `NOD` / `texts` 的逻辑。**

**→ 它把 a002 当成了"再来一份同样的 DXF 记录变异"，只是换了个 salt。**

### 5 道门禁：**只跑了 1 道**

```json
  "generation_gate": {"plan_status": "ready", "evidence_check": "pass",
                      "compile_check": "pending", "replay_check": "pending"}
```

**`compile_check` 和 `replay_check` 都是 `pending`（没跑）。**
所以"没报错"只说明 `evidence_check` 过了 —— **不等于 5 道都过**。

### 判定：落在**第三档**（"2 个也过不了，但错的是别的门禁"→ 其实是"没报错但策略是假的"）

| 你的判据 | 结果 |
|---|---|
| 2 个站点过了门禁 → 进 A/B | ⚠️ **没报错，但只验证了 1/5 道** |
| 2 个也过不了，错的还是那两个门禁 | ✗（这次没报错） |
| 2 个也过不了，错的是别的门禁 | ✗ |
| **（新增）generate 产出的还是单策略 → 停下报告** | ✅ **就是这个** |

---

## 🔴 结论：**停下报告**

**站点数确实是因素之一**（4 站点两次都被门禁拒；2 站点没报错），**但更根本的问题是**：

**多站点时，LLM 只把第一个站点的证据链实现出来，其余站点变成"同一算法的不同 salt"。**

**证据**：
1. `mutate_a001` 和 `mutate_a002` 调用**同一个**函数，只差 `salt`；
2. `salt` 只影响 RNG 种子和生成的名称；
3. a002 的证据链关键词（`DICTIONARY` / `handle` / `NOD` / `texts` / `ACAD_`）在代码里**一个都没有**。

**→ 拿这个算子跑 A/B，测的是"同一策略跑两次 vs 默认"，不是"多策略"。**

### 已恢复的东西（铁律）

```
  mutator.c sha1: d7913b9eaa3b     ← 已从备份恢复
  新算子另存为: mutator_multi2_de5eb910.c（sha1 de5eb910）
  mutation_plan.json: 1 mutation   ← 已恢复
  reps_r9_final / reps_pathB_r3 / 二进制 a416b44d  ← 没碰
```

### 三个方向（都没做，等你说）

| 方向 | 内容 |
|---|---|
| **(a) 接受"单形态 + 多 salt"，跑 A/B** | 测的其实是"同一策略重复调用是否提高触发率"；能出数，但不是你要的"多策略" |
| **(b) 换第 2 个站点**：挑一个**形态和 a001 明显不同**的（比如 `free.c:859→862` 走"对象类型"路），看它会不会被真正实现 | 最便宜；能验证"是不是 a002 的证据链太难实现" |
| **(c) 分两次 generate**：先只生成 a001，再单独生成 a002，**手工合并**两个 `mutate_a00X` | 绕开"一次生成多个"的退化；但要改流程 |

**我倾向 (b)** —— 它直接回答"是站点数的问题，还是第 2 个站点的证据链太难实现"。

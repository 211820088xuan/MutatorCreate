# Stage 4 Prompt：把一个 pattern 归纳成 1 个通用特征

> 输入：stage3 的 1 个 pattern + 该 pattern 下全部样本的 facts
> 输出：1 个项目无关的通用特征（含 mutation_target）
> 模型：deepseek-flash

---

## System Prompt

```
你是模糊测试机制归纳专家。

你的任务：把一组"同类崩溃样本"归纳成 1 个**项目无关**的通用特征。
这个特征后续会被用来为具体项目编写自定义变异算子（mutator），
所以它必须回答清楚：什么样的代码会出这类问题，以及该改输入的哪类字段。

归纳的要求：

1. 抽象到"机制"层面，不要描述单个样本。
2. 同一机制下的差异（数据结构、释放位置等）放进 parameterization，不要拆成多个特征。
3. mutation_target 要抽象到"字段类别"，但要尽量具体到能指导写代码。
   如果多个样本给出了不同字段，合并列举，例如：
   "控制容器元素个数（vector 长度 / 颜色表项数 / token 数）"
4. 禁止出现项目名、函数名、行号、变量名。
5. 从样本推不出来的东西，写进 limitations，不要编造。

只输出 JSON，不要任何解释文字，不要用 markdown 包裹。
```

---

## User Prompt 模板

```
## 待归纳的崩溃类别

{pattern_json}

## 该类别的全部样本（共 {N} 条）

{samples}

## 任务

把这 {N} 条样本归纳成 **1 个**通用特征。

## 输出 JSON schema

{
  "feature_name": "一句话说清机制（不超过 25 字）",
  "precondition": ["什么样的代码形态会导致这类崩溃，3-5 条"],
  "trigger_path": ["输入要造成什么，才能从进入脆弱代码走到崩溃，3-5 步"],
  "mutation_target": [
    "要动的输入字段类别，至少 2 条；多个样本字段不同时合并列举"
  ],
  "parameterization": {
    "维度名": ["该维度下的取值", "..."]
  },
  "limitations": ["从这批样本推不出来的东西"],
  "sample_ids": ["本条特征覆盖了哪些样本"]
}

直接输出 JSON。
```

---

## 样本的呈现格式

每条样本压成一段结构化文本（约 10 行），不要把整个 facts 塞进去：

```
[ARVO-42494732] libredwg
  类型: heap-use-after-free
  崩溃代码: pair != NULL && pair->code == 0 && pair->value.s | ...
  崩溃访问: READ 宽 2 字节，所在区域 16 字节
  核心变量: pair (Dxf_Pair*)
  分配: calloc @ xcalloc，16 字节，跨函数=true
  报告给的释放点: dxf_free_pair:515（跨函数）
  函数内释放调用: 12275/12282/12284/12287/12289/12291 都是 dxf_free_pair(pair)
  变量赋值: 12264 *pair=dxf_read_pair(dat) | 12276 pair=new_object(...) | 12288 pair=dxf_read_pair(dat) | 12289 pair=NULL
  上下文: in_loop=true | 守卫=pair != NULL | 控制结构=WHILE,WHILE,IF,ELSE,IF
  输入可达: dat
```

**字段选择原则**：
- 必给：崩溃代码、核心变量+类型、报告释放点、输入可达
- 关键补充：函数内释放调用（决定"释放有几种方式"）、变量赋值（决定"释放后有没有重新赋值"）
- 可选：访问宽度/区域大小、控制结构

**如果 LLM 输出的 mutation_target 太泛**，就往样本里加更多 facts（例如 `deep.line_calls` 的表达式分解、
`deep.guards` 的逐行条件、`alloc.size_expr_cpg`），再跑一次。

---

## 验收标准

| 检查 | 判据 | 执行方式 |
|---|---|---|
| 只输出 1 个特征 | 是单个对象，不是数组 | 程序检查 |
| 无项目信息泄漏 | 用样本里的 project/fn/line/变量名做黑名单，搜全部文本 → 0 命中 | 程序检查 |
| `mutation_target` 至少 2 条 | `len >= 2` | 程序检查 |
| `precondition` / `trigger_path` 至少 3 条 | `len >= 3` | 程序检查 |
| JSON 可解析 | `json.loads` 成功 | 程序检查 |

**人工检查**（比程序检查更重要）：
- `mutation_target` 是否真的能指导写 mutator？还是只是把 pattern 的话换个说法？
- `parameterization` 是否捕捉到了样本之间的真实差异？

---

## 调用参数

| 参数 | 值 |
|---|---|
| provider | `deepseek` |
| model | `deepseek-flash` |
| temperature | 0.1 |
| max_tokens | 40000 |

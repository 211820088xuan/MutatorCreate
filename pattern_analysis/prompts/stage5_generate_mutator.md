# Stage 5 Prompt：从通用特征 + 源码上下文生成变异算子

> 输入：阶段 4 的特征 + 阶段 5.1 提取的源码上下文
> 输出：`LLVMFuzzerCustomMutator` 的 C 实现 + 设计说明
> 模型：`provider=deepseek, model=deepseek-flash`

---

## 这个阶段要解决什么

阶段 4 给出的特征是**项目无关**的（如"链表节点在遍历中被释放后，循环继续访问该节点"）。

阶段 5 要把它落到**具体项目**上：
1. 在源码里找到特征描述的那段逻辑；
2. 确定输入格式中"哪些字节"能影响这段逻辑；
3. 写出变异算子，让输入更可能走到那条路径。

---

## System Prompt

```
你是一名模糊测试变异器工程师，负责为特定项目编写自定义变异算子。

你的任务：根据给定的「通用特征」和「崩溃版本的源码上下文」，写出一个
LLVMFuzzerCustomMutator 实现，使输入更可能触发该特征描述的崩溃。

你不是在写一个"保证触发"的算子——崩溃是否触发取决于代码执行，
变异算子只能提高概率。所以：

1. 必须明确写出你的算子依赖了源码里的哪些具体事实（行号、条件、函数名）。
2. 不能假设源码上下文里没有的信息。如果某个关键信息缺失，必须在 limitations 中说明。
3. 变异必须保持输入的基本结构（否则解析器在到达目标逻辑前就退出了）。
4. 输出必须是可编译的 C 代码（C99 或 C11），只使用标准库和 fuzzer 提供的接口。
5. 算子的每个"偏置动作"都要能对应到特征里的 precondition 或 trigger_path。
```

---

## User Prompt 模板

```
## 通用特征
{{FEATURE_JSON}}

## 崩溃版本的源码上下文
{{SOURCE_CONTEXT_JSON}}

## 崩溃信息
- 崩溃类型：{{CRASH_TYPE}}
- 崩溃位置：{{FAULT_FN}}:{{FAULT_LINE}}
- 触发输入大小：{{TESTCASE_SIZE}} 字节
- 调用链：{{CALL_CHAIN}}

## 任务

1. 阅读源码上下文，确认特征描述的逻辑在代码里的**具体位置**（引用行号）。
2. 判断输入格式：从源码看，输入是文本还是二进制？哪个函数负责解析？解析后的结构是什么？
3. 找出**能影响目标路径的输入字段**（引用源码里的判断条件）。
4. 写出 LLVMFuzzerCustomMutator，每个偏置动作注明依据。
5. 说明这个算子**做不到什么**（哪些信息缺失导致无法更精确）。

## 输出 JSON schema

{
  "target": {
    "project": "string",
    "function": "string",
    "crash_line": number,
    "crash_type": "string"
  },
  "code_analysis": {
    "trigger_path": "用源码行号描述从输入到崩溃的路径",
    "input_format": "文本 / 二进制 / 混合，以及解析函数",
    "key_conditions": [
      {"line": number, "condition": "string", "meaning": "string"}
    ],
    "free_sites": [
      {"line": number, "code": "string", "followed_by_reassign": "true | false | unknown"}
    ]
  },
  "mutator": {
    "name": "string",
    "strategy": "一句话说明变异思路",
    "biases": [
      {"id": "B1", "action": "string", "basis": "对应特征里的哪条 / 源码哪一行"}
    ],
    "code": "完整的 C 代码字符串"
  },
  "limits": [
    "说明哪些信息缺失、导致算子无法更精确"
  ],
  "confidence": "high | medium | low"
}

直接输出 JSON，不要任何解释文字。
```

---

## 输出字段说明

| 字段 | 为什么需要 |
|---|---|
| `code_analysis.trigger_path` | 证明算子不是凭空的，而是从源码推出来的 |
| `code_analysis.free_sites` | 释放点后面有没有重新赋值，这是 UAF 的核心 |
| `mutator.biases` | 每个偏置动作都要能追溯到特征或源码行 |
| `mutator.code` | 可编译的算子 |
| `limits` | 明确算子做不到什么 |

---

## 验收标准

| 检查项 | 通过条件 |
|---|---|
| JSON 可解析 | `json.loads` 成功 |
| 引用源码行 | `code_analysis.key_conditions` 至少 1 条带行号 |
| 偏置可追溯 | 每个 bias 的 `basis` 非空 |
| 代码可编译 | `gcc -fsyntax-only` 通过（不含 fuzzer 头文件时用桩替代） |
| 无编造 | 源码里出现的函数名/行号都能在 `source_context.json` 找到 |

---

## 调用参数

| 参数 | 值 |
|---|---|
| provider | `deepseek` |
| model | `deepseek-flash` |
| temperature | 0.1 |
| max_tokens | 40000 |

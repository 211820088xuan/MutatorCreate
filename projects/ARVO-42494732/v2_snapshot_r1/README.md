# Mutator Generation V2 —— 单项目闭环工作区

本目录是 V2 的**唯一**输出位置。**旧实验（`../mutator.c`、`../fuzz_exp/`、`../RESULT.md`）是基线，绝不覆盖。**

## 与 V1 的差别

| | V1（旧） | V2（本目录） |
|---|---|---|
| 生成器输入 | `features.json` + `source_context.json` | 必须先有 `mutation_plan.json` 且 `status=ready` |
| 特征绑定 | 5 个 UAF 特征一次全用 | **只绑一个主特征** |
| 输入字段 | 靠 LLM 自己从源码猜 | 必须是 `input_contract` 里的显式 locator |
| 无依据时 | 照样生成 mutator | **`blocked`，不生成 C** |
| 归因 | 无法归因 | 每层 JSON 独立、带证据引用 |

## 产物顺序（缺一层就停）

```
target_surface.json → candidate_findings.json → feature_bindings.json
→ mutation_plan.json → mutator.json + mutator.c → verification.json
```

## 状态字段的语义

| 状态 | 含义 |
|---|---|
| `ready` | 所有硬门禁通过，可以生成代码 |
| `blocked` | 缺证据，**流程必须停**，并写明缺什么（这是合法交付） |
| `rejected` | 明确不成立（例如证据行与源码不符） |

## 已冻结的输入

见 `manifest.json`。任何输入文件哈希变化都意味着基线变了，必须重跑。

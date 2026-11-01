#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""s5_generate_mutator.py —— 阶段 5：用「特征 + 源码上下文」生成变异算子。

输入：
  outputs/stage4/<type>/features.json       阶段 3 的特征
  mutator_custom/stage5/<OSV>/source_context.json  阶段 4.1 的源码上下文

输出：
  mutator_custom/stage5/<OSV>/mutator.json         完整输出（含代码分析、偏置说明、limits）
  mutator_custom/stage5/<OSV>/mutator.c            抽出的 C 代码（可直接编译）

用法：
  python3 s5_generate_mutator.py --feature uaf-llm01 --osv ARVO-42494732 --type uaf
"""
from __future__ import annotations
import argparse, json, os, subprocess, sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)   # pattern_analysis/
TOP = os.path.dirname(ROOT)    # mutator_create/
sys.path.insert(0, HERE)
from s3_extract_patterns import call_llm, parse_json

OUT = os.path.join(TOP, "mutator_custom", "stage5")
STAGE4 = os.path.join(ROOT, "outputs", "stage4")

SYSTEM = """你是一名模糊测试变异器工程师，负责为特定项目编写自定义变异算子。

你的任务：根据给定的「通用特征」和「崩溃版本的源码上下文」，写出一个
LLVMFuzzerCustomMutator 实现，使输入更可能触发该特征描述的崩溃。

你不是在写一个"保证触发"的算子——崩溃是否触发取决于代码执行，
变异算子只能提高概率。所以：

1. 必须明确写出你的算子依赖了源码里的哪些具体事实（行号、条件、函数名）。
2. 不能假设源码上下文里没有的信息。如果某个关键信息缺失，必须在 limits 中说明。
3. 变异必须保持输入的基本结构（否则解析器在到达目标逻辑前就退出了）。
4. 输出必须是可编译的 C 代码（C99 或 C11），只使用标准库和 fuzzer 提供的接口。
5. 算子的每个"偏置动作"都要能对应到特征里的 precondition 或 trigger_path。
6. 只输出 JSON，不要任何解释文字，不要用 markdown 包裹。"""

USER = """## 通用特征

```json
{feature_json}
```

## 崩溃版本的源码上下文

```json
{source_json}
```

## 崩溃信息

- 崩溃类型：{crash_type}
- 崩溃位置：{fault_fn}:{fault_line}
- 触发输入大小：{testcase_size} 字节
- 调用链：{call_chain}

## 任务

1. 阅读源码上下文，确认特征描述的逻辑在代码里的**具体位置**（引用行号）。
2. 判断输入格式：从源码看，输入是文本还是二进制？哪个函数负责解析？解析后的结构是什么？
3. 找出**能影响目标路径的输入字段**（引用源码里的判断条件）。
4. 写出 LLVMFuzzerCustomMutator，每个偏置动作注明依据。
5. 说明这个算子**做不到什么**（哪些信息缺失导致无法更精确）。

## 输出 JSON schema

{{
  "target": {{
    "project": "string",
    "function": "string",
    "crash_line": number,
    "crash_type": "string"
  }},
  "code_analysis": {{
    "trigger_path": "用源码行号描述从输入到崩溃的路径",
    "input_format": "文本 / 二进制 / 混合，以及解析函数",
    "key_conditions": [
      {{"line": number, "condition": "string", "meaning": "string"}}
    ],
    "free_sites": [
      {{"line": number, "code": "string", "followed_by_reassign": "true | false | unknown"}}
    ]
  }},
  "mutator": {{
    "name": "string",
    "strategy": "一句话说明变异思路",
    "biases": [
      {{"id": "B1", "action": "string", "basis": "对应特征里的哪条 / 源码哪一行"}}
    ],
    "code": "完整的 C 代码字符串"
  }},
  "limits": [
    "说明哪些信息缺失、导致算子无法更精确"
  ],
  "confidence": "high | medium | low"
}}

直接输出 JSON。"""


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--feature", required=True, help="特征 ID，如 uaf-f2")
    ap.add_argument("--osv", required=True, help="崩溃 ID，如 ARVO-42494732")
    ap.add_argument("--type", default="uaf", help="类型目录名，如 uaf")
    ap.add_argument("--force", action="store_true", help="已有输出时也重跑")
    ap.add_argument("--verify-cmd", default=None,
                    help="验证命令模板（{cfile} 会替换成生成的 mutator.c 路径）；"
                         "退出码非 0 视为不通过")
    ap.add_argument("--allow-unverified", action="store_true",
                    help="显式跳过验证门禁（不推荐）")
    a = ap.parse_args()

    fp_feat = os.path.join(STAGE4, a.type, "features.json")
    fp_ctx = os.path.join(OUT, a.osv, "source_context.json")
    fp_out = os.path.join(OUT, a.osv, "mutator.json")
    fp_c = os.path.join(OUT, a.osv, "mutator.c")

    if os.path.isfile(fp_out) and not a.force:
        print(f"已存在 {fp_out}，加 --force 重跑")
        return 0
    for p in (fp_feat, fp_ctx):
        if not os.path.isfile(p):
            print(f"缺少输入: {p}")
            return 1

    feats = json.load(open(fp_feat, encoding="utf-8"))
    feat = next((f for f in feats.get("features") or [] if f.get("id") == a.feature), None)
    if not feat:
        print(f"找不到特征 {a.feature}")
        return 1
    ctx = json.load(open(fp_ctx, encoding="utf-8"))

    # 调用链（从 reproduced_crashes 里取不到，用 source_context 的）
    call_chain = ctx.get("call_chain") or []

    prompt = SYSTEM + "\n\n" + USER.format(
        feature_json=json.dumps(feat, ensure_ascii=False, indent=1),
        source_json=json.dumps(ctx, ensure_ascii=False, indent=1),
        crash_type=ctx.get("crash_type"),
        fault_fn=ctx.get("fault_fn"),
        fault_line=ctx.get("fault_line"),
        testcase_size=ctx.get("testcase_size"),
        call_chain=json.dumps(call_chain, ensure_ascii=False),
    )
    print(f"prompt 字符数: {len(prompt)}，调用模型…", flush=True)

    last = None
    for i in range(3):
        try:
            txt = call_llm(prompt, max_tokens=40000)
            d = parse_json(txt)
            break
        except Exception as e:
            last = str(e)[:200]
            print(f"  重试 {i+1}: {last}", flush=True)
    else:
        print(f"失败: {last}")
        return 2

    json.dump(d, open(fp_out, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    code = (d.get("mutator") or {}).get("code") or ""
    if code:
        with open(fp_c, "w", encoding="utf-8") as fh:
            fh.write(code)

    print(f"\n已写出: {fp_out}")
    print(f"目标: {d.get('target')}")
    print(f"策略: {(d.get('mutator') or {}).get('strategy')}")
    print(f"偏置数: {len((d.get('mutator') or {}).get('biases') or [])}")
    print(f"代码行数: {len(code.splitlines())}")
    print(f"置信度: {d.get('confidence')}")
    print(f"\n关键条件:")
    for c in (d.get("code_analysis") or {}).get("key_conditions") or []:
        print(f"  L{c.get('line')}: {str(c.get('condition'))[:80]}")
    print(f"\nlimits:")
    for l in d.get("limits") or []:
        print(f"  - {l}")

    # ---------- 验证门禁 ----------
    # 历史教训：v1 的代码有 3 个实现 bug，因为没人验证，白跑了两轮实验。
    # 规则：没通过验证的算子不得进入 fuzz 实验。
    print()
    if a.verify_cmd:
        cmd = a.verify_cmd.replace("{cfile}", fp_c)
        print("=== 执行验证门禁 ===")
        print("  " + cmd[:240])
        r = subprocess.run(cmd, shell=True)
        if r.returncode != 0:
            print(f"\n[门禁] 不通过（退出码 {r.returncode}）：该算子不得进入 fuzz 实验")
            return 3
        print("\n[门禁] 通过，可以进入 fuzz 实验")
    elif not a.allow_unverified:
        print("[门禁] 未提供 --verify-cmd，按规则不得进入 fuzz 实验。")
        print("       验证脚本: mutator_verify.py（V1 语法 / V2 结构 / V3 自举重放）")
        print("       如确需跳过，加 --allow-unverified")
        return 3
    else:
        print("[门禁] 已显式跳过验证（--allow-unverified）")
    return 0


if __name__ == "__main__":
    sys.exit(main())

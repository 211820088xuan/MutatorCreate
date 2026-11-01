#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""s5_generate_mutator_v2.py —— 阶段5.5：只从 ready plan 生成 mutator

设计约束（与 V1 的关键差别）
  · **只接受 `mutation_plan.json` 且 `status=ready`**。blocked / 缺失 → 非零退出，不产出 C。
  · prompt 只包含 plan、被选特征的摘要和少量证据行，**不塞 12,000 行源码**。
    模型不再自己决定"改哪个字段"，只负责把已冻结的计划翻译成 C。
  · 生成后做机械校验：接口签名、是否引用了计划里的 locator、有没有长度边界。
    任一不过 → 不写 mutator.c，非零退出。

用法
  python3 s5_generate_mutator_v2.py --plan <mutation_plan.json> --out <dir>
  python3 s5_generate_mutator_v2.py --osv ARVO-42494732        # 缺省用 v2/ 下的 plan
"""
from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
TOP = os.path.dirname(ROOT)
OUT = os.path.join(TOP, "mutator_custom", "stage5")
sys.path.insert(0, HERE)

SYSTEM = """你是一名 C 语言 fuzzer 变异器工程师。

你会收到一份**已经冻结**的 mutation plan，里面有 N 个特征策略和一个 default 权重。
你的任务：为每个策略写一个独立 C 函数，再写一个**按权重**分发的
`LLVMFuzzerCustomMutator`，其中 default 部分直接调用 `LLVMFuzzerMutate`。
你不负责、也不允许改变下列任何决定：
  · 改哪个字段（`mutations[].field_id`）
  · 用什么操作（`mutations[].operation`）
  · 边界是多少（`mutations[].bounds`）
  · 必须保持哪些不变量（`mutations[].preserve`）
如果 plan 里有你没把握的地方，在 `limits` 里写清楚，**不要自己补一个新策略**。

硬性要求：
1. **plan 里有几个 mutation action，就要实现几个独立的策略函数**，一个不能少。
2. **必须同时保留 libFuzzer 的 default 变异**：分发器按 `weighting` 的比例决定走哪条路。
   例如 default=0.5、5 个特征各 0.1 时：
     ```
     unsigned r = Seed % 1000;
     if (r < 500) return LLVMFuzzerMutate(Data, Size, MaxSize);   /* default 50% */
     switch ((r - 500) / 100) { case 0: ... case 4: ... }        /* 特征 50%，各 10% */
     ```
   **不允许把 default 去掉**——去掉探索就停了，覆盖率会崩。
3. **`mutations[].target_part` 决定改哪一部分，必须严格遵守：**
     · `value_line`  → 改组码**后面那一行**（记录的值）。**组码数字本身必须保持不变。**
     · `numeric_field` → 改数值类组码的值。
     · `section_or_key` → 改段名/键名/别名表项。
     · `handle_ref` → 改对象引用类句柄。
     · `object_handle` → 复制/篡改对象句柄。
   改错部位是最严重的错误：它会让输入变成另一种合法记录，从而绕开目标缺陷。
2. 必须保持 plan 的 `preserve` 里列出的格式不变量；做不到就把这条写进 limits。
3. 输出长度必须 ≤ MaxSize；任何情况下都要返回合法值（失败时返回原输入副本）。
4. 只使用标准库和 libFuzzer 提供的接口。
6. 每个策略函数都要自己做边界检查（`MaxSize`、行长、`memmove` 范围），失败时原样返回。
7. **行切分必须同时兼容 `\n`、`\r\n`、`\r`。** 计划里的 `input_contract.line_endings`
   和 `sample_hex` 是真实字节，照着它写；遇到 CRLF 只认 `\n` 会一行都解析不出来。
8. 必须真的能改动输入：`sample_hex` 里给出了段名后面的第一条记录，策略要能定位并改它。
7. 只输出 JSON，不要解释文字，不要 markdown 包裹。"""

USER = """# Mutation Plan（已冻结，status={status}）

```json
{plan}
```

# 被绑定的特征（只作解释参考）

- id: {feature_id}
- 名称: {feature_name}
- mutation_target:
{mutation_target}

# 证据行（源码原文，供你写注释用）

{evidence}

# 任务

把 plan 实现成 `LLVMFuzzerCustomMutator`。输出 JSON：

{{
  "mutator": {{
    "name": "string",
    "strategy": "一句话",
    "implements_action_ids": ["a001", "a002", "..."],
    "dispatch": {{"default": 0.5, "features": {{"a001": 0.1, "a002": 0.1}}}},
    "biases": [{{"action_id": "a001", "code_hint": "string", "basis": "plan 里哪条"}}],
    "code": "完整的 C 代码字符串"
  }},
  "limits": ["说明哪些地方没把握"],
  "confidence": "high | medium | low"
}}
"""

SIG = "LLVMFuzzerCustomMutator"


def die(msg: str, code: int = 2):
    print(f"[stage5.v2] plan_status=BLOCKED  {msg}", file=sys.stderr)
    sys.exit(code)



DRIVER = r"""
#include <stddef.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
size_t LLVMFuzzerMutate(uint8_t *D, size_t S, size_t M) { (void)D; return S; }
#define LLVMFuzzerCustomMutator PLAN_MUT
#include "gen.c"
static void dump_rec(const uint8_t *d, size_t n) {
  size_t i = 0; int found = 0;
  for (i = 0; i + 7 <= n; i++) if (memcmp(d + i, "OBJECTS", 7) == 0) { found = 1; break; }
  if (!found) { fprintf(stderr, "REC ?\n"); return; }
  fprintf(stderr, "REC ");
  size_t j = i + 7;
  for (size_t k = 0; k < 140 && j + k < n; k++) {
    unsigned char c = d[j + k];
    fputc((c == '\n' || c == '\r') ? '|' : ((c >= 32 && c < 127) ? (int)c : '?'), stderr);
  }
  fputc('\n', stderr);
}

int main(int argc, char **argv) {
  if (argc < 2) return 2;
  FILE *f = fopen(argv[1], "rb");
  if (!f) return 3;
  static uint8_t a[8 << 20], b[8 << 20];
  size_t n = fread(a, 1, sizeof a, f);
  fclose(f);
  int total = (argc > 2) ? atoi(argv[2]) : 1000;
  int unchanged = 0, changed = 0;
  unsigned long sig = 1469598103u;
  for (int s = 0; s < total; s++) {
    memcpy(b, a, n);
    size_t m = PLAN_MUT(b, n, sizeof b, (unsigned)s);
    if (m == n && memcmp(b, a, n) == 0) { unchanged++; continue; }
    changed++;
    if (changed <= 60) dump_rec(b, m);
    for (size_t i = 0; i < m; i++) sig = (sig ^ b[i]) * 16777619u;   /* 输出指纹 */
    sig = (sig ^ (unsigned long)m) * 16777619u;
  }
  fprintf(stderr, "UNCHANGED %d CHANGED %d SIG %lu\n", unchanged, changed, sig);
  printf("%d %d %lu\n", unchanged, changed, sig);
  return 0;
}
"""


def _record_after(blob: bytes, anchor: bytes = b"OBJECTS"):
    """取 anchor 之后第一条 "码行 / 值行"，返回 (码, 值)。"""
    i = blob.find(anchor)
    if i < 0:
        return None, None
    lines = blob[i + len(anchor):].replace(b"\r\n", b"\n").split(b"\n")
    lines = [x for x in lines[:6]]
    for k in range(len(lines) - 1):
        code = lines[k].strip()
        if re.fullmatch(rb"\d{1,3}", code):
            return code, lines[k + 1]
    return None, None


def check_behavior(code: str, plan: dict, seed_path: str, workdir: str) -> list[str]:
    """实际跑算子：① 实测 default 权重 ② 检查"改值行"类策略真的改了值行。"""
    if not seed_path or not os.path.isfile(seed_path):
        return [f"行为校验跳过：找不到种子 {seed_path}"]
    if not shutil.which("clang"):
        return ["行为校验跳过：没有 clang"]
    d = tempfile.mkdtemp(prefix="behav_", dir=workdir)
    open(os.path.join(d, "gen.c"), "w", encoding="utf-8").write(code)
    open(os.path.join(d, "drv.c"), "w", encoding="utf-8").write(DRIVER)
    exe = os.path.join(d, "drv")
    r = subprocess.run(["clang", "-O0", "-std=c11", "-w", os.path.join(d, "drv.c"),
                        "-o", exe], capture_output=True, text=True)
    if r.returncode != 0:
        return ["行为校验失败：编译不过 " + (r.stderr or "")[:400].replace("\n", " | ")]
    r = subprocess.run([exe, seed_path, "1000"], capture_output=True, timeout=300,
                       text=True, errors="replace")
    if r.returncode != 0:
        return [f"行为校验失败：驱动返回 {r.returncode}"]

    bad = []
    m = re.search(r"UNCHANGED (\d+) CHANGED (\d+)", r.stderr or "")
    if not m:
        return ["行为校验失败：驱动没有输出统计"]
    un, ch = int(m.group(1)), int(m.group(2))
    total = un + ch
    want = float((plan.get("weighting") or {}).get("default") or 0.5)
    frac = un / total if total else 0.0
    if not (want - 0.2 <= frac <= want + 0.2):
        bad.append(f"default 权重不对：计划 {want:.2f}，实测未变化比例 {frac:.2f}"
                   f"（{un}/{total}）；upper bound 口径，偏低说明算子没生效，偏高说明 default 拿多了")

    src = open(seed_path, "rb").read()
    oc, ov = _record_after(src)
    recs = re.findall(r"^REC (.*)$", r.stderr or "", re.M)
    same_code_changed_value = 0
    for rec in recs:
        lines = [x for x in rec.split("|") if x.strip()]
        for k in range(len(lines) - 1):
            if re.fullmatch(r"\d{1,3}", lines[k].strip()):
                if lines[k].strip() == (oc or b"").decode(errors="ignore") and \
                   lines[k + 1].strip() != (ov or b"").strip().decode(errors="ignore"):
                    same_code_changed_value += 1
                break
    needs_value = any(a.get("target_part") == "value_line"
                      for a in plan.get("mutations") or [])
    if needs_value and ch and same_code_changed_value == 0:
        bad.append("没有观察到『组码不变、值行改变』的产物——value_line 类策略没生效"
                   f"（已检查 {len(recs)} 个变化输出）")
    return bad


def check_code(code: str, plan: dict) -> list[str]:
    """生成后的机械校验。返回问题列表（空 = 通过）。"""
    bad = []
    if SIG not in code:
        bad.append(f"缺少 {SIG} 接口")
    if "MaxSize" not in code:
        bad.append("没有使用 MaxSize 做长度边界")
    anchors = {a.get("locator", {}).get("section_anchor") for a in plan.get("mutations") or []}
    anchors = {x for x in anchors if x}
    if anchors and not any(a in code for a in anchors):
        bad.append(f"没有引用 plan 的段锚点 {sorted(anchors)}")
    codes = {a.get("locator", {}).get("anchor") for a in plan.get("mutations") or []}
    codes = {x for x in codes if x}
    if codes and not any(str(c) in code for c in codes):
        bad.append(f"没有引用 plan 的字段锚点 {sorted(codes)}")
    if not re.search(r"memcpy|memmove", code):
        bad.append("没有把原输入拷出来（失败时无法返回原输入）")
    if "LLVMFuzzerMutate" not in code:
        bad.append("没有保留 default 变异（未调用 LLVMFuzzerMutate）→ 探索会停")
    for a in plan.get("mutations") or []:
        aid = a.get("action_id")
        if aid and aid.replace("a", "") and str(aid)[1:] not in code and aid not in code:
            bad.append(f"代码里没有对应 action {aid} 的策略函数（建议在注释里标注 action id）")
    return bad


def main():
    ap = argparse.ArgumentParser(description="阶段5.5：从 ready plan 生成 mutator")
    ap.add_argument("--plan", default=None)
    ap.add_argument("--out", default=None)
    ap.add_argument("--osv", default=None)
    ap.add_argument("--model", default=os.environ.get("GEN_MODEL", "deepseek-chat"))
    ap.add_argument("--seed", default=None, help="行为校验用的种子（默认 seeds/ 第一个）")
    ap.add_argument("--dry-run", action="store_true", help="只打印 prompt 长度，不调用模型")
    args = ap.parse_args()

    if args.plan:
        pp = args.plan
        outdir = args.out or os.path.dirname(os.path.abspath(pp))
    elif args.osv:
        outdir = os.path.join(OUT, args.osv, "v2")
        pp = os.path.join(outdir, "mutation_plan.json")
    else:
        die("必须给 --plan 或 --osv")

    if not os.path.exists(pp):
        print(f"[stage5.v2] plan 不存在 not found: {pp}", file=sys.stderr)
        sys.exit(2)

    plan = json.load(open(pp, encoding="utf-8"))
    status = plan.get("status")
    if status != "ready":
        die(f"plan status={status}，blockers={plan.get('blockers')}；拒绝生成 mutator.c")
    if not (plan.get("mutations") or []):
        die("plan 里没有 mutations")

    # 特征摘要（可选）
    aids = [a.get("feature_id") for a in (plan.get("mutations") or [])]
    feature = {"id": (aids[0] if aids else None)}
    if args.osv:
        fp = os.path.join(ROOT, "outputs", "stage4", "uaf", "features.json")
        if os.path.exists(fp):
            for f in json.load(open(fp, encoding="utf-8")).get("features") or []:
                if f.get("id") == feature["id"]:
                    feature = f
                    break

    # 证据行（少量，不塞全量源码）
    ev = []
    cf = os.path.join(outdir, "candidate_findings.json")
    if os.path.exists(cf):
        d = json.load(open(cf, encoding="utf-8"))
        for x in (d.get("findings") or []):
            if x.get("function") == (plan.get("targets") or [{}])[0].get("function"):
                ev = [[e[0], e[1]] for e in (x.get("evidence_lines") or [])][:6]
                break

    mt = feature.get("mutation_target") or []
    prompt = SYSTEM + "\n\n" + USER.format(
        status=status, plan=json.dumps(plan, ensure_ascii=False, indent=1),
        feature_id=feature.get("id"), feature_name=feature.get("feature_name"),
        mutation_target="\n".join(f"  - {x}" for x in mt) or "  - （无）",
        evidence="\n".join(f"  L{e[0]}: {e[1]}" for e in ev) or "  （无）")

    print(f"[stage5.v2] plan_status=READY  plan={pp}")
    print(f"  prompt 字符数: {len(prompt)}（只含 plan + {len(ev)} 行证据）")
    if args.dry_run:
        return

    from s3_extract_patterns import call_llm
    txt = call_llm(prompt, max_tokens=30000)
    m = re.search(r"\{.*\}", txt, re.S)
    if not m:
        print("[stage5.v2] 模型没有返回 JSON", file=sys.stderr); sys.exit(3)
    obj = json.loads(m.group(0))
    mut = obj.get("mutator") or {}
    code = mut.get("code") or ""
    if not code.strip():
        print("[stage5.v2] mutator.code 为空", file=sys.stderr); sys.exit(3)

    bad = check_code(code, plan)
    sd = os.path.join(OUT, args.osv, "seeds") if args.osv else None
    want = (plan.get("input_contract") or {}).get("seed_file")
    seedp = args.seed or (os.path.join(sd, want) if (sd and want and
                          os.path.isfile(os.path.join(sd, want))) else None)
    if not seedp and sd and os.path.isdir(sd):
        seedp = next((os.path.join(sd, f) for f in sorted(os.listdir(sd))
                      if f.endswith(".dxf")), None)
    bad += check_behavior(code, plan, seedp, os.path.dirname(os.path.abspath(__file__)))
    if bad:
        print("[stage5.v2] 生成后校验失败：", file=sys.stderr)
        for b in bad:
            print(f"  ✗ {b}", file=sys.stderr)
        # 保留被拒的代码，便于复查（不写 mutator.c）
        rej = os.path.join(outdir, "mutator_rejected.c")
        open(rej, "w", encoding="utf-8").write(code)
        json.dump({"problems": bad, "mutator": mut, "limits": obj.get("limits")},
                  open(os.path.join(outdir, "mutator_rejected.json"), "w", encoding="utf-8"),
                  ensure_ascii=False, indent=1)
        print(f"  被拒代码已保存到 {rej}", file=sys.stderr)
        sys.exit(4)

    os.makedirs(outdir, exist_ok=True)
    rec = {
        "schema_version": "stage5.mutator.v2",
        "target": plan.get("target"),
        "provenance": {"plan_file": os.path.relpath(pp, outdir),
                       "binding_file": "feature_bindings.json",
                       "finding_file": "candidate_findings.json",
                       "source_commit": (plan.get("target") or {}).get("commit")},
        "generation_gate": {"plan_status": status, "evidence_check": "pass",
                            "compile_check": "pending", "replay_check": "pending"},
        "mutator": mut,
        "limits": obj.get("limits") or [],
        "confidence": obj.get("confidence"),
    }
    json.dump(rec, open(os.path.join(outdir, "mutator.json"), "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)
    open(os.path.join(outdir, "mutator.c"), "w", encoding="utf-8").write(code)
    print(f"  写出 {outdir}/mutator.json 和 mutator.c（{len(code)} 字节）")
    print(f"  implements: {mut.get('implements_action_ids')}")


if __name__ == "__main__":
    main()

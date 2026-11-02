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
OUT = os.path.join(ROOT, "projects")
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
9. **禁止用固定候选值列表。** `new_value_policy.kind = random_unrecognized_name` 的意思是：
   值必须**由 Seed 推导生成**（长度在 `length` 区间内、字符取自 `alphabet`），
   不能写成 `{"FUZZ_OBJECT","AAAAAAAA","\x7f"}` 这种 2~3 个固定常量——
   那样 1000 个 Seed 只会产出个位数不同结果，等于半个预算在造重复。
8. **`locator.pick = random_k`**：段内通常有多条同组码记录，必须按 Seed 随机选第 k 条，
   不能永远改第一条。
11. **格式分流**：`input_contract.format_scope` 之外的输入，必须**调用 `LLVMFuzzerMutate`**，
    **不能返回原输入**——返回原输入等于这次迭代什么也没做，白白浪费一半预算。
    llvmfuzz 的分流规则：前两字节 `AC` → DWG；首字节 `{` → JSON；其余 → DXF。
13. **`operation = ensure_record_structure` 时，策略函数必须有两条路径**：
    · **段存在**（能在输入里找到 `locator.section_anchor` 那一行）→ 现行为：
      按 `locator.pick=random_k` 选段内第 k 条 code-0 记录，替换它的**值行**；
    · **段不存在** → 按 `construct.sequence` 在 `construct.insert_position` 处
      插入完整结构（`0/SECTION` + `2/<anchor>` + `0/<随机非已知名>` + `0/ENDSEC`）。
    两条路径都必须做 `MaxSize` 边界检查、兼容 `\n`/`\r\n`/`\r`、失败返回原输入。
    **段不存在时不能返回原输入**（那是空转）。
14. 只输出 JSON，不要解释文字，不要 markdown 包裹。"""

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
static long g_default_calls = 0;
size_t LLVMFuzzerMutate(uint8_t *D, size_t S, size_t M) {
  (void)D; (void)M;
  g_default_calls++;         /* 只计数、不改数据：这样 CHANGED/DISTINCT/DIFF 只反映特征路径 */
  return S;
}
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
  const char *dump_path = (argc > 3) ? argv[3] : NULL;
  int dumped = 0;
  int unchanged = 0, changed = 0, ndump = 0;
  static unsigned long seen[4096]; int nseen = 0;
  unsigned long sig = 1469598103u;
  for (int s = 0; s < total; s++) {
    memcpy(b, a, n);
    size_t m = PLAN_MUT(b, n, sizeof b, (unsigned)s);
    if (m == n && memcmp(b, a, n) == 0) { unchanged++; continue; }
    changed++;
    if (dump_path && !dumped) {
      FILE *o = fopen(dump_path, "wb");
      if (o) { fwrite(b, 1, m, o); fclose(o); dumped = 1; }
    }
    {
      unsigned long h = 1469598103ul;
      for (size_t i = 0; i < m; i++) h = (h ^ b[i]) * 16777619ul;
      h ^= (unsigned long)m;
      int dup = 0;
      for (int i = 0; i < nseen; i++) if (seen[i] == h) { dup = 1; break; }
      if (!dup && nseen < 4096) seen[nseen++] = h;
    }
    if (s % 10 == 0 && ndump < 60) {
      size_t lim = (m < n) ? m : n, k = 0;
      while (k < lim && b[k] == a[k]) k++;
      fprintf(stderr, "DIFF %zu\n", k);
      ndump++;
    }
    for (size_t i = 0; i < m; i++) sig = (sig ^ b[i]) * 16777619u;   /* 输出指纹 */
    sig = (sig ^ (unsigned long)m) * 16777619u;
  }
  fprintf(stderr, "UNCHANGED %d CHANGED %d DISTINCT %d DEFAULT %ld SIG %lu\n",
          unchanged, changed, nseen, g_default_calls, sig);
  printf("%d %d %d %ld %lu\n", unchanged, changed, nseen, g_default_calls, sig);
  return 0;
}
"""



def _lines_of(b):
    out = []; i = 0; n = len(b)
    while i < n:
        j = i
        while j < n and b[j] not in (10, 13):
            j += 1
        out.append(b[i:j])
        i = (j + 2) if (j < n and b[j] == 13 and j + 1 < n and b[j + 1] == 10) else (
            j + 1 if j < n else j)
    return out


def _has_structure(blob, anchor: bytes = b"OBJECTS"):
    """校验构造路径产出：存在 0/SECTION、2/OBJECTS、>=1 条 code-0 记录。"""
    L = _lines_of(blob)
    oi = None
    for k in range(len(L) - 1):
        if L[k].strip() == b"2" and L[k + 1].strip() == anchor:
            oi = k
            break
    if oi is None:
        return False, False, 0
    has_sec = any(L[k].strip() == b"0" and L[k + 1].strip() == b"SECTION"
                  for k in range(max(0, oi - 2), oi))
    n0 = 0
    k = oi + 1
    while k < len(L) - 1:
        if L[k].strip() == b"0":
            if L[k + 1].strip() == b"ENDSEC":
                break
            n0 += 1
        k += 1
    return has_sec, True, n0

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


def check_behavior(code: str, plan: dict, seed_path: str, workdir: str,
                   other_seed: str | None = None,
                   gate_seed: str | None = None) -> list[str]:
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
    m = re.search(r"UNCHANGED (\d+) CHANGED (\d+) DISTINCT (\d+) DEFAULT (\d+)",
                  r.stderr or "")
    if not m:
        return ["行为校验失败：驱动没有输出统计"]
    un, ch, distinct, ndefault = (int(m.group(i)) for i in (1, 2, 3, 4))
    total = un + ch
    want = float((plan.get("weighting") or {}).get("default") or 0.5)
    frac = ndefault / total if total else 0.0   # 精确：default 被调用了几次
    if not (want - 0.15 <= frac <= want + 0.15):
        bad.append(f"default 权重不对：计划 {want:.2f}，实测 {frac:.2f}"
                   f"（default 被调用 {ndefault}/{total}）")

    need_dist = int((plan.get("mutation_space") or {}).get("min_distinct_outputs") or 0)
    if need_dist and distinct < need_dist:
        bad.append(f"有效变异空间太小：1000 个 Seed 只产出 {distinct} 个互不相同的输出，"
                   f"要求 ≥ {need_dist}（固定候选列表或没有随机化都会这样）")

    # 门禁 5：构造路径有效性（在**剥掉 OBJECTS 段**的种子上跑）
    constructing = any(op == "ensure_record_structure"
                       for op in ([a.get("operation") for a in plan.get("mutations") or []]
                                  + [x for a in plan.get("mutations") or []
                                     for x in (a.get("operation_paths") or [])]))
    if gate_seed and os.path.isfile(gate_seed):
        dpath = os.path.join(d, "mutant.bin")
        r3 = subprocess.run([exe, gate_seed, "1000", dpath], capture_output=True,
                            timeout=600, text=True, errors="replace")
        m3 = re.search(r"UNCHANGED (\d+) CHANGED (\d+) DISTINCT (\d+) DEFAULT (\d+)",
                       r3.stderr or "")
        if not m3:
            bad.append("构造路径门禁：驱动在剥段种子上没有输出统计")
        else:
            ch3 = int(m3.group(2))
            if ch3 < 400:
                bad.append(f"构造路径无效：剥掉 OBJECTS 的种子上 1000 Seed 只改动 {ch3} 次"
                           f"（要求 ≥ 400；当前算子应为 0）")
            elif os.path.isfile(dpath):
                blob = open(dpath, "rb").read()
                hs, ho, n0 = _has_structure(blob)
                if not (hs and ho and n0 >= 1):
                    bad.append(f"构造路径产出的不是合法结构：0/SECTION={hs} "
                               f"2/OBJECTS={ho} 段内 code-0 记录数={n0}")

    # 格式分流：format_scope 之外的输入必须全部走 default（否则那部分预算空转）
    if other_seed and os.path.isfile(other_seed):
        r2 = subprocess.run([exe, other_seed, "1000"], capture_output=True, timeout=300,
                            text=True, errors="replace")
        m2 = re.search(r"UNCHANGED (\d+) CHANGED (\d+) DISTINCT (\d+) DEFAULT (\d+)",
                       r2.stderr or "")
        if m2:
            un2, ch2, _d2, def2 = (int(m2.group(i)) for i in (1, 2, 3, 4))
            tot2 = un2 + ch2
            frac2 = def2 / tot2 if tot2 else 0.0
            if frac2 < 0.95:
                bad.append(f"格式没分流：在非目标格式的输入上只有 {frac2:.0%} 走 default；"
                           f"format_scope 之外的输入必须全部交给 LLVMFuzzerMutate")

    src = open(seed_path, "rb").read()
    need_value = any(a.get("target_part") == "value_line"
                     for a in plan.get("mutations") or [])
    if need_value and ch and src.find(b"OBJECTS") >= 0:
        objs = src.find(b"OBJECTS")
        offs = [int(x) for x in re.findall(r"^DIFF (\d+)$", r.stderr or "", re.M)]
        inside_code_line = 0
        before_section = 0
        checked = 0
        for off in offs:
            if off >= len(src):
                continue
            ls = src.rfind(b"\n", 0, off) + 1
            le = src.find(b"\n", off)
            le = len(src) if le < 0 else le
            line = src[ls:le].strip()
            checked += 1
            if re.fullmatch(rb"\d{1,3}", line):
                inside_code_line += 1      # 改到了组码行 → 违反 preserve
            if objs >= 0 and off <= objs and not constructing:
                before_section += 1        # 改到段名之前 → 不在目标区域
                                           # （构造路径下段本来就不存在，不适用）
        if checked == 0:
            bad.append("没有观察到任何差异采样，无法确认 value_line 策略生效")
        elif inside_code_line:
            bad.append(f"{inside_code_line}/{checked} 个采样改到了组码行，违反 "
                       f"preserve=group_code_digits（应只改值行）")
        elif before_section:
            bad.append(f"{before_section}/{checked} 个采样改在 OBJECTS 段之前")
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
    ap.add_argument("--retries", type=int, default=3,
                    help="LLM 生成的重试次数（默认 3；0 等价于 1）")
    ap.add_argument("--max-tokens", type=int, default=48000,
                    help="单次生成的 token 上限（默认 48000，给 reasoning 留余量）")
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
    # 生成步是 LLM 调用，**天然不稳定**：模型 reasoning 偶尔吃掉整个 max_tokens
    # （finish_reason=length），或者产出的代码过不了行为门禁。两者重试都可能解决，
    # 所以这里做有限重试；重试用尽才失败。--retries 0 表示只跑一次。
    tries = max(1, args.retries)
    obj, code = None, None
    for attempt in range(1, tries + 1):
        if attempt > 1:
            print(f"  [retry {attempt}/{tries}] 上一次失败，重新生成…", file=sys.stderr)
        try:
            txt = call_llm(prompt, max_tokens=args.max_tokens)
        except RuntimeError as e:
            print(f"  ✗ [retry {attempt}/{tries}] {e}", file=sys.stderr)
            continue
        m = re.search(r"\{.*\}", txt, re.S)
        if not m:
            print(f"  ✗ [retry {attempt}/{tries}] 模型没有返回 JSON", file=sys.stderr)
            continue
        obj = json.loads(m.group(0))
        mut = obj.get("mutator") or {}
        code = mut.get("code") or ""
        if not code.strip():
            print(f"  ✗ [retry {attempt}/{tries}] mutator.code 为空", file=sys.stderr)
            continue
        break
    if not code or not code.strip():
        print(f"[stage5.v2] 连续 {tries} 次都没拿到可用代码", file=sys.stderr)
        sys.exit(3)

    bad = check_code(code, plan)
    sd = os.path.join(OUT, args.osv, "seeds") if args.osv else None
    want = (plan.get("input_contract") or {}).get("seed_file")
    seedp = args.seed or (os.path.join(sd, want) if (sd and want and
                          os.path.isfile(os.path.join(sd, want))) else None)
    if not seedp and sd and os.path.isdir(sd):
        seedp = next((os.path.join(sd, f) for f in sorted(os.listdir(sd))
                      if f.endswith(".dxf")), None)
    otherp = None
    if sd and os.path.isdir(sd):
        otherp = next((os.path.join(sd, f) for f in sorted(os.listdir(sd))
                       if f.endswith(".dwg")), None)
    gatep = None
    gd = os.path.join(OUT, args.osv, "v2", "experiment", "gate_seeds")
    if os.path.isdir(gd):
        gatep = next((os.path.join(gd, f) for f in sorted(os.listdir(gd))
                      if f.endswith(".dxf")), None)
    bad += check_behavior(code, plan, seedp, os.path.dirname(os.path.abspath(__file__)),
                          other_seed=otherp, gate_seed=gatep)
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

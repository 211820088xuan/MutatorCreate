"""R37 Part 1：组装器 assemble_multi() —— 纯程序，不调 LLM。

## 模式 B：并列拼接

每个单策略算子**各自保留完整函数体**，只在入口分流，符号加前缀防冲突。

不选模式 A（参数化合并：提公共骨架、差异提成参数）的理由：
  A 需要理解算子内部逻辑；B 不需要 —— 符号重命名是纯机械操作，可以 100% 准确。
  之前手工做的 mutator_multi_OBJ_ENT.c 走的是 A，那是因为两个算子都从同一份
  `4864893e` 派生、只差一个字符串常量；LLM 为结构不同的站点生成的算子不保证有这个性质。

## 符号重命名：用 nm，不用正则

C 声明形态太多，正则必错。编译成 .o 让链接器告诉我们哪些是 local 符号：
  `nm x.o | awk '$2 ~ /^[tdbrs]$/ {print $3}'`
小写 t/d/b/r/s = local，要加前缀；大写 T/D/B 和 U（标准库引用）一个都不许改。

改名只在标识符边界上做（`\bfoo\b`），**且不动字符串字面量内部**。
"""
from __future__ import annotations

import os
import re
import subprocess
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

HEADER = """/* R37 多策略算子（由 tools/r37_assemble.py 机械生成，不要手改）
 *
 * 模式 B：并列拼接。每个策略保留完整函数体，符号加了 sNNN_ 前缀。
 * 分流只用 Seed，不读 Data —— 否则等价性验证做不了。
 *
 * 策略清单：
__MANIFEST__
 */
#include <stddef.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

size_t LLVMFuzzerMutate(uint8_t *Data, size_t Size, size_t MaxSize);

"""

ENTRY = """
size_t LLVMFuzzerCustomMutator(uint8_t *Data, size_t Size, size_t MaxSize,
                               unsigned int Seed)
{
  unsigned int r = Seed % 1000u;
__SPLIT__
}
"""

DEFAULT_STUB = """/* 编译期桩：只为让 nm 跑起来取 local 符号；不会进产物 */
size_t LLVMFuzzerMutate(uint8_t *Data, size_t Size, size_t MaxSize)
{ (void)Data; (void)MaxSize; return Size; }
"""


def _run(cmd, timeout=300):
    return subprocess.run(cmd, shell=isinstance(cmd, str), capture_output=True,
                          text=True, timeout=timeout)


def local_symbols(src_path: str) -> list[str]:
    """编译成 .o，返回 local 符号名（小写 t/d/b/r/s）。"""
    with tempfile.TemporaryDirectory() as d:
        probe = os.path.join(d, "probe.c")
        obj = os.path.join(d, "probe.o")
        text = open(src_path, encoding="utf-8", errors="replace").read()
        # 补一个桩，避免 LLVMFuzzerMutate 未定义导致编不过
        if "LLVMFuzzerMutate" not in text:
            text = DEFAULT_STUB + "\n" + text
        open(probe, "w", encoding="utf-8").write(text)
        r = _run(["gcc", "-c", "-O0", "-w", "-std=c11", probe, "-o", obj])
        if r.returncode != 0:
            raise RuntimeError(f"nm 探针编译失败：{r.stderr[:400]}")
        n = _run(["nm", obj])
        out = []
        for ln in n.stdout.splitlines():
            parts = ln.split()
            if len(parts) >= 3 and re.fullmatch(r"[tdbrs]", parts[1]):
                out.append(parts[2])
        return out


def _split_literals(text: str):
    """把字符串/字符字面量挖出来换成占位符，避免改名改到字面量内部。"""
    lits, out, i, n = [], [], 0, len(text)
    while i < n:
        c = text[i]
        if c in "\"'":
            q, j = c, i + 1
            while j < n:
                if text[j] == "\\":
                    j += 2
                    continue
                if text[j] == q:
                    j += 1
                    break
                j += 1
            lits.append(text[i:j])
            out.append(f"\x00L{len(lits)-1}\x00")
            i = j
        else:
            out.append(c)
            i += 1
    return "".join(out), lits


def _restore_literals(text: str, lits) -> str:
    for k, v in enumerate(lits):
        text = text.replace(f"\x00L{k}\x00", v)
    return text


def rename_locals(text: str, syms, prefix: str) -> str:
    """给 local 符号加前缀（标识符边界、不动字面量）。"""
    body, lits = _split_literals(text)
    for s in sorted(set(syms), key=len, reverse=True):
        if not s or s.startswith("LLVMFuzzerMutate"):
            continue
        body = re.sub(rf"\b{re.escape(s)}\b", f"{prefix}{s}", body)
    return _restore_literals(body, lits)


def strip_common(text: str) -> str:
    """去掉重复的 #include 和 LLVMFuzzerMutate 声明（头部统一给一次）。"""
    keep = []
    for ln in text.split("\n"):
        st = ln.strip()
        if st.startswith("#include"):
            continue
        if re.match(r"^size_t\s+LLVMFuzzerMutate\s*\(", st):
            continue
        keep.append(ln)
    # 去掉连续空行
    out, blank = [], 0
    for ln in keep:
        if not ln.strip():
            blank += 1
            if blank > 2:
                continue
        else:
            blank = 0
        out.append(ln)
    return "\n".join(out).strip("\n")


def assemble_multi(inputs, out_path, default_weight=0.5):
    """inputs: [(path, label)] → 写多策略算子。

    权重：default 固定 0.50，剩下 0.50 在 N 个策略间均分。
    """
    n = len(inputs)
    if n < 2:
        raise ValueError("至少两个策略才有意义")
    per = round((1.0 - default_weight) / n, 4)
    chunks, manifest = [], []
    for i, (p, label) in enumerate(inputs, 1):
        prefix = f"s{i:03d}_"
        text = open(p, encoding="utf-8", errors="replace").read()
        syms = local_symbols(p)
        renamed = rename_locals(text, syms, prefix)
        # 入口函数改名
        renamed = re.sub(r"\bLLVMFuzzerCustomMutator\b", f"{prefix}entry", renamed)
        renamed = strip_common(renamed)
        chunks.append(f"/* ───── 策略 {i}: {label} (原文件 {os.path.basename(p)}) ───── */\n{renamed}\n")
        manifest.append((i, label, os.path.basename(p), len(syms), prefix))

    # 入口分流
    lines = []
    cut = int(round(default_weight * 1000))
    lines.append(f"  if (r < {cut}u) return LLVMFuzzerMutate(Data, Size, MaxSize);"
                 f"   /* default {default_weight:.2f} */")
    acc = cut
    for i in range(1, n + 1):
        if i < n:
            acc_i = int(round((default_weight + per * i) * 1000))
            lines.append(f"  if (r < {acc_i}u) return s{i:03d}_entry(Data, Size, MaxSize, Seed);"
                         f"   /* {per:.2f} */")
        else:
            lines.append(f"  return s{i:03d}_entry(Data, Size, MaxSize, Seed);"
                         f"                   /* {per:.2f} */")
    mtext = "\n".join(f" *   {i:03d}. {lb}  ({fn}, {ns} 个 local 符号, 前缀 {pf})"
                      for i, lb, fn, ns, pf in manifest)
    body = (HEADER.replace("__MANIFEST__", mtext) + "\n".join(chunks) + "\n"
            + ENTRY.replace("__SPLIT__", "\n".join(lines)))
    open(out_path, "w", encoding="utf-8").write(body)
    return dict(out=out_path, n=n, per=per, default=default_weight,
                manifest=manifest, bytes=len(body))


if __name__ == "__main__":
    V2 = os.path.join(ROOT, "projects", "ARVO-42494732", "v2")
    ins = [(os.path.join(V2, "mutator_single_OBJECTS.c"), "OBJECTS 段"),
           (os.path.join(V2, "mutator_single_ENTITIES_r36_63b23547.c"), "ENTITIES 段")]
    out = os.path.join(V2, "mutator_multi_r37.c")
    info = assemble_multi(ins, out)
    print(f"  写出 {info['out']}（{info['bytes']} 字节）")
    for i, lb, fn, ns, pf in info['manifest']:
        print(f"    {i}: {lb}  {fn}  {ns} 个 local 符号  前缀 {pf}")
    print(f"  权重: default {info['default']:.2f} + {info['n']} × {info['per']:.2f}")

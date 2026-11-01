#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""W5：⑥ walk-back **停止判据**的自测（N12 的 🅗 改进：`frac≥0.6` 即停）。

⚠ **[W5 更新] 默认值已翻转**：预注册判据「distinct-crash n≥10 且 tier 损失 0」**已满足**
（实测 n=11、触发 22、省 32 次构建、损失 0）→ `--stop-frac` 默认由 0 改 **0.6**。
但那 11 条**全是 c-blosc2**（单项目 100%）→ 跨项目泛化未证；判据当初没写多样性要求，
故**照预注册翻**（事后加条件＝移动球门），另以「多项目轮次显式传 `--stop-frac 0` 作对照」
继续攒跨项目 shadow。详见 DELIVERY §4.36/§4.43。

判据抽成纯函数 `run_repro.stop_decision()`，不依赖 docker / 数据，可单测。

**默认 OFF**（`--stop-frac 0`）—— 离线回放（`w5_phase1_replay_stopfrac.py`）显示：
现有 24 条 crash / 43 格里，阈值 0.6 会触发 5 次、省 7 次构建、tier 损失 0，
但那 5 次只是 **3 条不同 crash**（同一条在 depth1/depth2 各触发一次，嵌套重复计数），
且 2/3 是 c-blosc2 → n 太小。更要紧的是：**默认 ON 会摧毁测量通道**（一停就再也
观察不到更深格），W5 便永远无法给 N12 定论。故本轮只记 shadow 字段攒数据。
**预注册翻转判据**：distinct-crash n≥10 且 tier 损失 0 → 默认改 0.6。

复算：python3 preflight/w5_selftest_stopfrac.py
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, ROOT)
import run_repro as RR               # noqa: E402

FAILS = []


def ck(cond, msg):
    print(("  ✅ " if cond else "  ❌ ") + msg)
    if not cond:
        FAILS.append(msg)


def d(tier, frac, rep, stop_frac, shadow=0.6):
    return RR.stop_decision(tier, frac, rep, stop_frac, shadow_frac=shadow)


def main():
    print("═" * 72)
    print("W5 ⑥ 自测：walk-back 停止判据（tier 停 + frac 停 + shadow）")
    print("═" * 72)

    print("\n[A] tier 停（W3 已有判据，不得被 frac 规则破坏）")
    r = d("strict", 0.0, True, 0.6)
    ck(r["stop"] and r["reason"] == "tier", f"strict → 停，reason=tier（{r}）")
    r = d("medium", 0.3333, True, 0.6)
    ck(r["stop"] and r["reason"] == "tier", "medium → 停，reason=tier（即使 frac 低）")
    ck(d("strict", 1.0, True, 0.6)["would_fire"] is False,
       "已达 medium+ 时 shadow 不再计（frac 规则此时无意义）")

    print("\n[B] frac 停（新判据，开启时）")
    r = d("loose", 1.0, True, 0.6)
    ck(r["stop"] and r["reason"] == "frac", f"loose + frac=1.0 → 停，reason=frac（{r}）")
    ck(r["would_fire"] is True, "同时 shadow=True")
    ck(d("loose", 0.6667, True, 0.6)["stop"] is True, "loose + frac=0.6667 ≥0.6 → 停")
    ck(d("loose", 0.6, True, 0.6)["stop"] is True, "边界：frac == 阈值 → 停（用 ≥ 不用 >）")
    ck(d("loose", 0.3333, True, 0.6)["stop"] is False, "loose + frac=0.3333 <0.6 → **不停**，继续下探")

    print("\n[C] 守卫：不该停的情况一个都不能停")
    ck(d("none", 0.0, False, 0.6)["stop"] is False, "none（没崩）→ 不停")
    ck(d("loose", 1.0, False, 0.6)["stop"] is False,
       "frac 高但 reproduced=False → 不停（守卫有效；实测未复现格 frac 恒为 0.0）")
    ck(d("loose", None, True, 0.6)["stop"] is False, "frac=None → 不停（None 安全，不抛异常）")
    ck(d("loose", 1.0, True, 0.0)["stop"] is False, "`--stop-frac 0`（关）→ 不停")

    print("\n[D] shadow 常开：默认 OFF 时也要记下「本来会停」")
    r = d("loose", 1.0, True, 0.0)
    ck(r["would_fire"] is True and r["stop"] is False,
       f"关闭状态下 shadow 仍为 True（{r}）→ W5 每轮自动攒 A/B 数据")
    ck(d("loose", 0.3333, True, 0.0)["would_fire"] is False, "frac 低于 shadow 阈值 → shadow=False")
    ck(d("loose", 1.0, True, 0.0, shadow=0.0)["would_fire"] is False,
       "shadow 阈值设 0 → 完全禁用（不留痕）")

    print("\n[E] 与 ⑥ 的接线：CLI 默认值（W5 已按预注册判据翻转为 0.6）")
    ap = RR.build_argparser() if hasattr(RR, "build_argparser") else None
    if ap is None:
        ck(False, "run_repro 需暴露 build_argparser() 以便无 docker 检查默认值")
    else:
        a = ap.parse_args([])                    # ⑥ 无必填项 → 空参即得默认值
        # [W5 翻转] 预注册判据「distinct-crash n≥10 且 tier 损失 0」**已满足**
        # （✅ 实测 n=11、触发 22 次、省 32 次构建、tier 损失 **0**）→ 默认由 0 改 0.6。
        # ⚠ 但这 11 条**全是 c-blosc2**（单项目 100%）→ 跨项目泛化未证；故多项目轮次
        #   仍以 `--stop-frac 0` 作**显式对照**继续攒 shadow（见 §4.43）。
        ck(a.stop_frac == 0.6, f"`--stop-frac` 默认 = {a.stop_frac}（预注册判据已满足 → 翻转 ON）")
        a2 = ap.parse_args(["--stop-frac", "0"])
        ck(a2.stop_frac == 0.0, "可显式关掉（对照实验用，多项目轮次就这么跑）")
        ck(ap.parse_args(["--stop-project-after", "2"]).stop_project_after == 2,
           "抽取 build_argparser() 未破坏既有选项（W4 的早停阈值仍在）")

    print("\n" + ("❌ %d 项未通过：%s" % (len(FAILS), FAILS) if FAILS else "✅ 全部通过"))
    return 1 if FAILS else 0


if __name__ == "__main__":
    sys.exit(main())

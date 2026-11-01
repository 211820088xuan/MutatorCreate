#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""W5：⑤ `annotate_dataset.merge()` 的字段透传自测。

起因（✅ W5 实测抓到的接线缺陷）：⑥ 已把 `walkback_stop_reason` 写进 observation
（`--stop-frac 0.6` 那轮 trace 里 `stop_reason='frac'`），但 **dataset 行里是 None**
→ ⑤ 的 `walkback_*` 白名单（annotate_dataset.py:165）没带上新字段。
后果不是「少个字段」这么轻：**dataset 是交付物，trace 是中间产物**；
若只有 trace 记了提前停，交付出去的复现记录表就无法回答「哪些行是 frac 停的、
它们的结论是否因此偏保守」——正是 N12 翻转默认值时要审计的东西。

复算：python3 preflight/w5_selftest_annotate.py
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, ROOT)
import annotate_dataset as A         # noqa: E402

FAILS = []
MAN = {"osv_id": "OSV-2020-2184", "project": "c-blosc2", "crash_type": "Heap-buffer-overflow"}


def ck(cond, msg):
    print(("  ✅ " if cond else "  ❌ ") + msg)
    if not cond:
        FAILS.append(msg)


def obs(**kw):
    base = {"osv_id": "OSV-2020-2184", "reproduced_any": True, "observed_crash_type": "SEGV",
            "walkback_depth_actual": 1, "walkback_best_depth": 1, "walkback_best_tier": "loose",
            "walkback_depths_tried": 1, "walkback_n_build_fail": 0}
    base.update(kw)
    return base


def main():
    print("═" * 72)
    print("W5 ⑤ 自测：walkback_stop_reason 必须透传进 dataset 行")
    print("═" * 72)

    print("\n[A] 新字段")
    r = A.merge(MAN, obs(walkback_stop_reason="frac"), {}, None, "w5-t", 1)
    ck(r.get("walkback_stop_reason") == "frac",
       f"obs 带 stop_reason='frac' → dataset 行 = {r.get('walkback_stop_reason')!r}（期望 'frac'）")
    r2 = A.merge(MAN, obs(walkback_stop_reason="tier"), {}, None, "w5-t", 1)
    ck(r2.get("walkback_stop_reason") == "tier", "stop_reason='tier' 同样透传")
    r3 = A.merge(MAN, obs(), {}, None, "w5-t", 1)
    ck(r3.get("walkback_stop_reason") is None,
       f"obs 没有该字段 → 行为不变（{r3.get('walkback_stop_reason')!r}，不报错）")
    ck("walkback_stop_reason" not in (r.get("_obs_extra") or {}),
       "不该被 `_obs_extra` 吞掉（它是正式字段，不是附加信息）")

    print("\n[B] 既有 walkback_* 字段不得被打破（回归）")
    for k in ("walkback_best_depth", "walkback_best_tier", "walkback_depths_tried",
              "walkback_n_build_fail", "walkback_depth_actual"):
        ck(r.get(k) == obs().get(k), f"{k} = {r.get(k)!r}")
    ck(A.merge(MAN, obs(walkback_exhausted=True, walkback_best_depth=None), {}, None,
               "w5-t", 1).get("walkback_exhausted") is True, "walkback_exhausted 仍透传")

    print("\n[D] binary_dir 已不存在 → ⑤ 必须**自己**标注（不留无声悬空指针）")
    # ✅ W5 实测：60 条历史行的 binary_dir 指向已被裁掉的目录却毫无标记。
    # ⑥ 只在「本轮逐条回收」时标 binary_pruned；**轮末裁剪**（W3 机制）删掉的从不标
    # → 消费者读 binary_dir 会扑空且无从判断。故 ⑤ 在 merge 时按**目录是否存在**兜底。
    gone = A.merge(MAN, obs(), {}, {"build_status": "ok", "path": "pinned",
                                    "binary_dir": "/definitely/not/here/xyz",
                                    "binary_sha256": "ef" * 32}, "w5-t", 1)
    ck(gone.get("binary_pruned") is True,
       f"目录不存在 → binary_pruned={gone.get('binary_pruned')!r}（期望 True）")
    ck(gone.get("binary_sha256") == "ef" * 32, "sha256 仍留住（指纹不随目录消失）")
    here = os.path.dirname(os.path.abspath(__file__))
    live = A.merge(MAN, obs(), {}, {"build_status": "ok", "path": "pinned",
                                    "binary_dir": here, "binary_sha256": "12" * 32}, "w5-t", 1)
    ck(live.get("binary_pruned") is None,
       f"目录存在 → 不标（{live.get('binary_pruned')!r}），避免把活证据说成已删")
    kept = A.merge(MAN, obs(binary_pruned=True), {}, {"build_status": "ok", "path": "pinned",
                                                      "binary_dir": here}, "w5-t", 1)
    ck(kept.get("binary_pruned") is True, "⑥ 已显式标注的不被覆盖")

    print("\n[C] 负对照：证明 [A] 不是空过")
    r4 = A.merge(MAN, obs(walkback_stop_reason="frac"), {}, None, "w5-t", 1)
    ck(r4.get("walkback_best_tier") != "frac",
       "断言确实读的是新字段、不是碰巧从别的字段取到同值")
    ck(r4.get("walkback_stop_reason") != r4.get("walkback_best_tier"),
       f"stop_reason({r4.get('walkback_stop_reason')!r}) 与 best_tier"
       f"({r4.get('walkback_best_tier')!r}) 是两个独立字段")

    print("\n" + (f"❌ {len(FAILS)} 项未通过：{FAILS}" if FAILS else "✅ 全部通过"))
    return 1 if FAILS else 0


if __name__ == "__main__":
    sys.exit(main())

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""⑥ `run_repro.py` — 顶层编排（DELIVERY §1.3⑥ / §1.6 增量循环）。

单轮流程（**HEAD-first**，§1.2）：
```
① manifest_builder  → run 目录 manifest.jsonl + build_groups.json（本轮范围）
② build_orchestrator --stage 1   → HEAD 构建（(project,sanitizer) 共享，一次服务同组全部 crash）
③ repro_runner                   → 用归档位二进制跑 testcase
[若非 --stage1-only]
② build_orchestrator --stage auto --observations <③ 的输出>  → 只给**未复现者**钉版
③ repro_runner                   → 再跑一遍（钉版二进制）
④ verify_tiered                  → Tiered 分级（三 score 全记）
⑤ annotate_dataset               → append 进 repro_dataset.jsonl（带 run_id/run_ts）
```

**为何 `--stage auto` 放在 ⑥ 而不是 ②**：auto 需要 ③ 的复现结果才知道谁没复现；② 只负责构建，
不该知道复现语义。② 单独跑 `--stage auto` 而没给 `--observations` 时会退化成只做 Stage1
（不擅自把全部 crash 钉一遍——钉版 per-commit 独占，单位成本约 8×）。

**幂等/可续跑**：`artifacts/state.json` 记每 `(project,sanitizer,commit)` 的 build_status +
`binary_dir`（归档位）+ era commit 缓存 + HEAD SHA 缓存；重跑跳过已完成。`--force` = 忽略构建缓存
重建，但 dataset 仍**追加**新 run_id（不删旧；下游按 osv_id 取 run_ts 最新）。

**限界**：`--limit` 界 crash 数、`--max-builds` 界**单轮构建数**（HEAD+钉版合计，跨两个 stage
共享同一预算，Stage1 用掉的部分会从 Stage2 预算里扣）。
"""
from __future__ import annotations

import argparse
import collections
import datetime
import json
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import repro_common as rc  # noqa: E402
import verify_tiered as VT  # noqa: E402  [W3 N12] 复用 ④ 的**同一份**分级逻辑（不另写判据）
import build_orchestrator as BO  # noqa: E402  [W5] 复用 ② 的 purge_archives（逐条回收归档）

RUNS = os.path.join(rc.ARTIFACTS, "runs")
DATASET = os.path.join(rc.REPRO_DIR, "repro_dataset.jsonl")
BUILD_RECORDS = os.path.join(rc.ARTIFACTS, "build_records.jsonl")
STATE = os.path.join(rc.ARTIFACTS, "state.json")


def log(*a):
    print(*a, file=sys.stderr, flush=True)


# [W4 Phase3b] **版本确定性**失败类：由「上游 commit × 当前 build.sh/工具链」决定，
# 同项目同 era 必然同样失败 → 可据此早停。瞬态类（`network_fetch`）不在此列（② 会自动重试）。
# [W5 **N43** 修正] 原先 `commit_not_found` 也在里面 —— 但它的成立条件是**「哪一个 commit」**，
# 不是「上游 commit × 当前 build.sh/工具链」这种**项目级**确定性：同一项目里有的 commit 在、
# 有的不在（✅ libavc 实测：43 条里 29 条走 github、14 条走 android.googlesource，
# 两种源都出过复现，个别 commit 报 `does not exist in current branch`）。
# 把「逐 commit 才成立」的失败当成「项目级必然失败」→ 连续 2 次就封整个项目，
# **实测误伤 33 条**（而当轮已试 10 条里 7 条成功）。故移出，与 `network_fetch` 同等对待。
DETERMINISTIC_FAIL = ("buildscript_mismatch", "toolchain_drift", "compile_error",
                      "dockerfile_drift",
                      # [W5 **N58**] 镜像里烘死的依赖与 era 不匹配：镜像是**固定的**，
                      # 所以每个 commit 都会同样失败 → 属项目级确定性，计入早停。
                      "era_dep_drift")

# tier 序（模块级：W5 起 `stop_decision()` 也要用，不再在循环里重复定义）
TIER_RANK = {"strict": 3, "medium": 2, "loose": 1, "none": 0, None: -1}


def mid_round_clean(a, why, t_start):
    """**[N62] 轮中即时回收**（复用 `disk_policy.py` 的全套安全检查，不在此另写删除逻辑）。

    为什么需要：`--post-clean` 只在**轮末**触发，而单归档很大的项目会在**轮中**就把盘写满 ——
    ✅ 实测 unicorn：单个 `fuzz_emu_*` 二进制就 **108MB**（内嵌 QEMU），一次构建产出**全部**变体
    → 3 条探针产生 **3.8GB**；定向批 6 条期间可用空间一度掉到 **2.6GB**。
    整池 30 条按 ~2.3 构建/条 × ~540MB/构建估算要 **~37GB**，轮末才清根本来不及。

    ⚠ **已知代价**（不是缺陷，是取舍）：轮中瘦身时，本轮**后面**那些 crash 还没成为 verified 行，
    故 `disk_policy` 的 `needed_map` 不知道它们；若后面某条钉到**同一 commit 却要另一个 target**，
    ② 会重建它（多一次构建的成本）。`reuse` 保护规则（服务 >1 条的归档不瘦身）能挡掉大部分。
    """
    if not a.post_clean:
        return
    log(f"  [N62] 磁盘水位 {free_gb(rc.ARTIFACTS):.1f} GB < {a.mid_clean_free_gb} GB（{why}）"
        f" → 轮中即时回收 …")
    # **[N63] 必须传 `--protect-since t_start`**：否则本轮**在飞**（已构建、还没落账）的归档
    # 会被当成「无 verified 行引用的孤儿目录」整目录删掉。✅ 实测事故：unicorn 批
    # `w5-unicorn-b2` 轮中触发 3 次清理，删掉 **4 条刚复现的 crash** 的归档
    # （OSV-2020-1409/-1945/-2180/-231）→ ⑤ 只能标 binary_pruned、审计 3 条红线。
    subprocess.run([sys.executable, os.path.join(HERE, "disk_policy.py"),
                    "--clean-build", "--prune-images",
                    "--prune-orphans", "--prune-siblings",
                    "--min-free-gb", str(a.mid_clean_free_gb),
                    "--protect-since", str(t_start), "--force", "--apply"],
                   check=False)
    # **[N64] 硬底线安全阀**：清完仍不够 → **优雅停轮**，不能继续构建到把盘写满。
    # ✅ 实测事故（w5-fix-n63）：水位线确实触发了 2 次、N63 也确实保护住了在飞归档
    # （`保护 6 个 / 7.29 GB`），但**保护本身就把盘占住了** —— 可用空间一路掉到
    # **68 KB（100% 满）**，进程僵死、连 shell 输出都写不出来。
    # 「保护在飞归档」与「继续构建」在 unicorn 这种单归档 100MB+ 的项目上是**冲突**的，
    # 光靠水位线不够，必须有个「清完仍低于底线就停」的闸门。
    left = free_gb(rc.ARTIFACTS)
    if left < a.disk_hard_floor_gb:
        raise RuntimeError(
            f"[N64] 磁盘硬底线：轮中回收后仍只剩 {left:.1f} GB < --disk-hard-floor-gb "
            f"{a.disk_hard_floor_gb} GB。\n"
            f"  原因通常是「本轮在飞归档受 N63 保护」与「继续构建」互相挤占"
            f"（unicorn 单个 fuzz_emu_* 就 108MB、一次构建产出全部变体）。\n"
            f"  → 本轮在此**优雅停止**（已完成的记录已落盘）。续跑请**减小 --limit**"
            f"（分批），或调低 --mid-clean-free-gb / 调高 --disk-hard-floor-gb。")


def stop_decision(tier, frac, reproduced, stop_frac, shadow_frac=0.6):
    """[W5 N12] walk-back 某一格「要不要停」的**纯函数**判据（可单测，不依赖 docker）。

    → `{"stop": bool, "reason": "tier"|"frac"|None, "would_fire": bool}`

    * `reason="tier"`：**W3 已有判据** —— `strict`/`medium` 即停。
    * `reason="frac"`：**W5 新增（默认关）** —— 未达 medium 但 `score_subseq_frac ≥ stop_frac`
      且确已崩 → 视为「同一 bug 的不同表现」（N15 形态：帧全对齐、只是 crash_type 从 HBO 变 SEGV）
      而停，省掉无收益下探。✅ 离线回放：阈值 0.6 触发 5 次 / 省 7 次构建 / **tier 损失 0**，
      但只有 **3 条不同 crash**（同一条在 depth1、depth2 各触发一次 = 嵌套重复计数）、2/3 是
      c-blosc2 → 仍是 🅗。**默认 OFF 的真正理由**：一旦开启就再也观察不到更深格 →
      **测量通道被摧毁**，W5 扩样本便无法给 N12 定论。省构建 vs 永久失去定论能力 → 选后者。
    * `would_fire`：**shadow，常开**（与 `stop_frac` 无关，用 `shadow_frac`）→ 每轮自动攒 A/B 数据。
      **预注册翻转判据**：distinct-crash n≥10 且 tier 损失 0 → `--stop-frac` 默认改 0.6。
      ✅ **W5 已按该判据翻转默认**（实测 n=11、触发 22、省 32 次构建、损失 0）。
      ⚠ 但那 11 条**全是 c-blosc2**（单项目 100%）→ **跨项目泛化未证**；判据当初只写了
      n 与损失、没写项目多样性，故按预注册**照翻不误**（事后加条件＝移动球门），
      同时把「多项目轮次显式传 `--stop-frac 0` 作对照」定为后续动作（DELIVERY §4.43）。
    守卫：`frac` 为 None 或 `reproduced` 为假 → 一律不停（实测未复现格 frac 恒为 0.0，双保险）。
    """
    if TIER_RANK.get(tier, -1) >= 2:
        return {"stop": True, "reason": "tier", "would_fire": False}
    hi = (frac is not None and bool(reproduced))
    return {"stop": bool(hi and stop_frac > 0 and frac >= stop_frac),
            "reason": ("frac" if (hi and stop_frac > 0 and frac >= stop_frac) else None),
            "would_fire": bool(hi and shadow_frac > 0 and frac >= shadow_frac)}


def free_gb(path="/"):
    """[W3 Phase2] 磁盘余量（GB）。

    **[N62] 加容错**：取不到 → 返回一个大数（**宁可不清也不误清**）。
    ⚠ 本函数在文件里**只应有一份定义** —— 我加 N62 时曾在模块顶部另写一份，被这里的
    后定义**静默覆盖**（Python 后定义者胜），导致 `except OSError` 那版根本没生效。
    ✅ 由 `free_gb('/nonexistent')` 抛 FileNotFoundError 当场抓到。
    """
    try:
        st = os.statvfs(path)
        return st.f_bavail * st.f_frsize / (1 << 30)
    except OSError:
        return 1e9


def step(name, cmd, dry=False):
    log(f"\n{'═'*76}\n▶ {name}\n  $ {' '.join(str(c) for c in cmd)}\n{'═'*76}")
    if dry:
        return 0
    p = subprocess.run([str(c) for c in cmd], cwd=HERE)
    if p.returncode != 0:
        log(f"  ❌ {name} 退出码 {p.returncode}")
    return p.returncode


def count_builds(path, since_ts=0):
    """build_records.jsonl 里 ts > since_ts 的**实际构建**条数（不含缓存命中）。"""
    if not os.path.exists(path):
        return 0
    n = 0
    for line in open(path, encoding="utf-8"):
        try:
            d = json.loads(line)
        except json.JSONDecodeError:
            continue
        if (d.get("ts") or 0) > since_ts and not d.get("cache_hit") \
                and d.get("build_status") not in (None, "skipped"):
            n += 1
    return n


def _latest(path, key="osv_id"):
    """jsonl → {key: 最后一条}（文件顺序 = 时间顺序）。"""
    out = {}
    if not path or not os.path.exists(path):
        return out
    for line in open(path, encoding="utf-8"):
        line = line.strip()
        if not line:
            continue
        try:
            d = json.loads(line)
        except json.JSONDecodeError:
            continue
        if d.get(key):
            out[d[key]] = d
    return out


def _append(path, rec):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "a", encoding="utf-8") as f:
        f.write(json.dumps(rec, ensure_ascii=False) + "\n")


def _latest_build_for(oid, path):
    """build_records.jsonl 里该 osv_id 的**最后一条**（= 刚建的那格）。"""
    last = None
    if not os.path.exists(path):
        return None
    for line in open(path, encoding="utf-8"):
        try:
            d = json.loads(line)
        except json.JSONDecodeError:
            continue
        if d.get("osv_id") == oid:
            last = d
    return last


plan_meta = {}


def get_plan(oid, man, a, py):
    """调 ② --print-plan 拿该 crash 的钉版计划 → [(depth, commit, note)]。"""
    cmd = [py, "build_orchestrator.py", "--manifest", man, "--stage", "2", "--print-plan",
           "--only-osv", oid, "--max-depth", str(a.max_depth)]
    p = subprocess.run(cmd, cwd=HERE, capture_output=True, text=True)
    if p.returncode != 0:
        # [实现 W3 修] **② 非 0 退出不得静默当成「无钉版计划」**。
        # ✅ W3 实测：② 因 gate 条件② 判脏而 ABORT（rc=2），⑥ 却把 5 条 crash 记成
        # 「无计划 → repro_version=none」继续跑 —— 等于**在 worktree 已被污染的情况下继续构建**，
        # 正是 gate 要防的事。rc=2 专指 gate ABORT → 抛出，让整轮停下。
        tail = (p.stderr or "").strip().splitlines()[-3:]
        if p.returncode == 2:
            raise RuntimeError("② gate ABORT（rc=2，worktree/镜像不安全）→ 整轮停止。"
                               f"末尾日志: {tail}")
        log(f"    ⚠ --print-plan 失败 rc={p.returncode}: {tail}")
        return []
    try:
        plans = json.loads(p.stdout.strip().splitlines()[-1])
    except (json.JSONDecodeError, IndexError):
        log("    ⚠ --print-plan 输出不可解析")
        return []
    e = plans.get(oid) or {}
    plan_meta[oid] = e
    if e.get("no_plan_why"):
        log(f"    ⓘ 无计划：{e['no_plan_why']}")
    return [(d, c, n) for d, c, n in (e.get("plan") or [])]


def summarize(obs_path, ver_path):
    o = [json.loads(l) for l in open(obs_path, encoding="utf-8")] if os.path.exists(obs_path) else []
    v = [json.loads(l) for l in open(ver_path, encoding="utf-8")] if os.path.exists(ver_path) else []
    lat_o, lat_v = {}, {}
    for x in o:
        lat_o[x["osv_id"]] = x
    for x in v:
        lat_v[x["osv_id"]] = x
    tiers = collections.Counter(x.get("verification_tier") for x in lat_v.values())
    repro = sum(1 for x in lat_o.values() if x.get("reproduced_any"))
    skip = collections.Counter(x.get("skip_reason") for x in lat_o.values() if x.get("skip_reason"))
    return dict(n_obs=len(lat_o), n_ver=len(lat_v), reproduced=repro,
                tiers=dict(tiers), skipped=dict(skip))


def build_argparser():
    """⑥ 的 CLI。抽成函数 → 自测可在**不跑 docker** 的前提下检查默认值（W5）。"""
    ap = argparse.ArgumentParser(description="⑥ 顶层编排：一轮增量复现（①→⑤）")
    ap.add_argument("--projects", default=None, help="逗号分隔项目名")
    ap.add_argument("--limit", type=int, default=0, help="界 crash 数")
    ap.add_argument("--crash-types", default=None, help="归一化 crash_type，逗号分隔")
    ap.add_argument("--sanitizers", default=None, help="address,memory,undefined")
    ap.add_argument("--languages", default="c,c++", help="默认 C/C++ 主线（R5 exact-match）")
    ap.add_argument("--sort", default="fixed_first",
                    help="**[W5 根因修正]** 默认由 no_fixed_first 改为 fixed_first："
                         "W3 把路由翻成 has_fixed→钉版（复现率 **45.7%% vs HEAD 6.7%%**）后排序键没跟着改"
                         " → 收益最高的一批被排到队尾（✅ 实测 92 条积压位于默认序第 196–2996 位，"
                         "历轮 --limit ≤30 → 三轮都没碰到）")
    ap.add_argument("--purge-on-verify", action=argparse.BooleanOptionalAction, default=False,
                    help="[W5 → **W5 第十一轮反转默认为关**] 每条 crash 的证据落盘后立即删其钉版归档。"
                         "**默认关**，理由：① **重放必须有二进制** —— 删了就把「现场」换成「要重搭一次现场」，"
                         "下游若要反复重放（变异算子归纳正是这种用法）这个代价是持续性的；"
                         "② ✅ 实测重建全部 60 个归档只要 **1.6h / ≈2.8GB**，而磁盘有 11G 可用 → "
                         "**留着是付得起的**，当初「非删不可」的前提（3,093 条 × 48MB ≈ 145GB > 100G 磁盘）"
                         "只在**跑满整个队列**时才成立，而实测新项目 6 试 0 中、根本跑不满；"
                         "③ 这条路径已出过 **N30**（绕过保护集删掉已交付 strict 证据）与 "
                         "**N41**（保护集字符串比对、路径一有别名就静默失配 → 会删光 verified 归档）"
                         "两次事故 —— **默认关掉最危险的那条路径**本身就是护栏。"
                         "跑满大队列且磁盘吃紧时再显式加 `--purge-on-verify`。"
                         "HEAD/_shared 归档永不删（共享 + 负对照要用）")
    ap.add_argument("--max-builds", type=int, default=0, help="单轮构建上限（HEAD+钉版合计）")
    ap.add_argument("--stage1-only", action="store_true", help="本轮只跑 HEAD")
    ap.add_argument("--force-stage1", action="store_true",
                    help="[W3 Phase1] **退回 W2 旧路由**：全部 crash 都先跑 HEAD（仅供对照实验，"
                         "默认关——has_fixed 组 HEAD 复现率 0.8%%，低于 break-even 6.2%%）")
    ap.add_argument("--min-free-gb", type=float, default=0.0,
                    help="[W3 Phase2] 磁盘余量护栏：低于此值停止本轮（0=不检查）")
    ap.add_argument("--match-job-arch", action=argparse.BooleanOptionalAction, default=True,
                    help="[W4 Phase4(d)] 钉版构建按 crash 自己的 `job_arch` 走（默认开）。"
                         "✅ 实测 i386 上报的 crash 用 i386 构建可使 tier 从 medium 升 **strict**"
                         "（帧不被内联掉）；是**替换**不是新增构建。--no-match-job-arch 全走 x86_64")
    ap.add_argument("--stop-project-after", type=int, default=2,
                    help="[W4 Phase3b] 同项目连续 N 次**同类版本确定性失败** → 跳过该项目本轮"
                         "剩余队列（默认 2，理由见 walk-back 循环处注释；network_fetch 不计入）")
    ap.add_argument("--stop-frac", type=float, default=0.6,
                    help="[W5 N12] walk-back 追加停止判据：某格 `score_subseq_frac ≥ 此值`（且确已崩）"
                         "即视为「同一 bug 的不同表现」而停，不再下探。"
                         "**默认 0.6 = 开（W5 按预注册判据翻转）**：判据「distinct-crash n≥10 且"
                         " tier 损失 0」**已满足** —— ✅ 离线回放实测 n=**11**、触发 22 次、"
                         "省 **32** 次构建、tier 损失 **0**（复算 preflight/w5_phase1_replay_stopfrac.py）。"
                         "⚠ **但这 11 条全是 c-blosc2**（单项目 100%%）→ **跨项目泛化未证**；"
                         "故多项目轮次应显式传 `--stop-frac 0` 作对照，继续攒 shadow 数据。"
                         "无论开关，每格都记 shadow 字段 `frac_stop_would_fire`")
    ap.add_argument("--force", action="store_true", help="忽略构建缓存重建（dataset 仍追加）")
    ap.add_argument("--only-osv", default=None)
    ap.add_argument("--run-id", default=None)
    ap.add_argument("--static-check", action="store_true",
                    help="① 跑复合证据分静态 check（需网络；给 pin_commit/walkback_depth）")
    ap.add_argument("--static-check-limit", type=int, default=50)
    ap.add_argument("--degenerate-only", action=argparse.BooleanOptionalAction, default=True,
                    help="静态 check 只跑 N6 退化复核（默认开，省 3,000+ 次请求）。"
                         "**--no-degenerate-only** = 对范围内记录跑完整静态 check "
                         "（给 pin_commit/`located`·`not_located`，Phase 5 的 not_located 桶需要它）")
    ap.add_argument("--max-depth", type=int, default=3)
    ap.add_argument("--build-timeout", type=int, default=3600)
    # **[N61] 轮末自动回收磁盘**（默认开；用户批准的「自动回收 + 分级保留」策略）
    ap.add_argument("--post-clean", action=argparse.BooleanOptionalAction, default=True,
                    help="轮末调 disk_policy.py：无条件清 build/ 中间产物 + 悬空镜像；"
                         "归档瘦身只在低于 --post-clean-free-gb 时才动（默认开）")
    ap.add_argument("--post-clean-free-gb", type=float, default=6.0,
                    help="可用空间低于此值才做**归档瘦身**（默认 6.0 GB；纯废物清理不受此门控）")
    ap.add_argument("--disk-hard-floor-gb", type=float, default=2.5,
                    help="**[N64] 磁盘硬底线**：轮中回收后仍低于此值就**优雅停轮**（默认 2.5 GB）。"
                         "✅ 实测缺这道阀时可用空间掉到 68 KB（100%% 满）、进程僵死")
    ap.add_argument("--mid-clean-free-gb", type=float, default=5.0,
                    help="**[N62] 轮中水位线**：每处理一条 crash 前查一次，可用低于此值就即时回收"
                         "（默认 5.0 GB）。大归档项目必需 —— ✅ 实测 unicorn 单归档 104~124MB、"
                         "整池估算 ~37GB，只在轮末清会写满")
    ap.add_argument("--stop-after-failures", type=int, default=5)
    ap.add_argument("--no-era-precheckout", action="store_true")
    ap.add_argument("--t-strict", type=float, default=1.0)
    ap.add_argument("--no-prune", action="store_true",
                    help="[W3 Phase2] 关闭轮末归档裁剪（默认开：裁掉未被 verified 记录引用的归档）")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--skip-manifest", action="store_true",
                    help="复用已有 run manifest（调试用）")
    return ap


def main():
    a = build_argparser().parse_args()

    rc.install_recovered(rc.load_recovered())   # [W3] VT.verify_one → normalize_frames 的闭包依赖
    run_id = a.run_id or f"w3-{datetime.datetime.now().strftime('%Y%m%d-%H%M%S')}"
    rd = os.path.join(RUNS, run_id)
    os.makedirs(rd, exist_ok=True)
    man = os.path.join(rd, "manifest.jsonl")
    bg = os.path.join(rd, "build_groups.json")
    obs = os.path.join(rd, "observations.jsonl")
    obs2 = os.path.join(rd, "observations_stage2.jsonl")
    ver = os.path.join(rd, "verifications.jsonl")
    t_start = datetime.datetime.now().timestamp()

    log(f"{'#'*76}\n# ⑥ run_repro  run_id={run_id}\n"
        f"# 范围: projects={a.projects or '(全部)'} limit={a.limit or '(无)'} "
        f"sanitizers={a.sanitizers or '(全部)'} crash_types={a.crash_types or '(全部)'}\n"
        f"# stage1_only={a.stage1_only} max_builds={a.max_builds or '(无)'} force={a.force}\n"
        f"# run 目录: {rd}\n{'#'*76}")

    py = sys.executable

    # ---------- ① manifest ----------
    if a.skip_manifest and os.path.exists(man):
        log(f"\n▶ ① 跳过（--skip-manifest，复用 {man}）")
    else:
        cmd = [py, "manifest_builder.py", "--out", man, "--build-groups", bg,
               "--languages", a.languages, "--sort", a.sort, "--no-regression"]
        if a.projects:
            cmd += ["--projects", a.projects]
        if a.limit:
            cmd += ["--limit", str(a.limit)]
        if a.crash_types:
            cmd += ["--crash-types", a.crash_types]
        if a.sanitizers:
            cmd += ["--sanitizers", a.sanitizers]
        if a.only_osv:
            cmd += ["--only-osv", a.only_osv]
        if a.static_check:
            cmd += ["--static-check", "--static-check-limit", str(a.static_check_limit),
                    "--max-depth", str(a.max_depth)]
            if a.degenerate_only:
                cmd += ["--degenerate-only"]
        if step("① manifest_builder", cmd, a.dry_run) != 0:
            return 1

    n_man = sum(1 for _ in open(man, encoding="utf-8")) if os.path.exists(man) and not a.dry_run else 0
    log(f"  ① 本轮 manifest: {n_man} 条")

    # ========== [W3 Phase1] 路由：has_fixed 跳过 Stage1 ==========
    # 依据（✅ W3 用 W2 真实数据复算，非推测）：
    #   * has_fixed（`commit_source ∈ {fixed_parent, fixed_ancestor, introducing}`）在 HEAD 的
    #     复现率 = **1/119 = 0.8%**（Wilson 95% 上界 **4.6%**）；那 1 条是 libtsm OSV-2021-1373，
    #     而 libtsm 上游 HEAD 冻结在 **2014-04-24**、比报告年 2021 早 7 年 → HEAD 就是漏洞版，
    #     **不构成 has_fixed 组 HEAD 有用的证据**。排除它则 **0/118**、上界 **3.2%**。
    #   * break-even：一组 k 条 crash 加 HEAD 层花 `T_head + k·t_run`、省 `h·T_pin`
    #     → 划算 ⟺ yield > `(T_head/k + t_run)/T_pin`。实测 T_head 中位 **72s**、T_pin **79s**
    #     （同项目比值中位 **0.87**，n=4）、t_run≈1.5s：
    #       k=20.8（W2 样本，偏向大项目）→ **6.2%**；k=7.76（总体 3,136/404 head_groups）→ **13.5%**。
    #   * 4.6% < 6.2% ≤ 13.5% → **三种 k 口径下都不划算**。R16 当年「HEAD 共享、成本差 8×」是
    #     **纯推测**（8× 从未测过；实测 T_head/T_pin ≈ 0.87，共享只摊薄 T_head 那一项）。
    prior, man_rec = {}, {}
    if os.path.exists(man):        # [W3] dry-run 也要能读（配合 --skip-manifest 验证路由）
        for line in open(man, encoding="utf-8"):
            d = json.loads(line)
            prior[d["osv_id"]] = d.get("commit_source")
            man_rec[d["osv_id"]] = d
    scope_ids = list(prior)
    # [实现 W3] --only-osv 也要约束 ⑥ 自己的 scope（原来只透传给 ①③；配 --skip-manifest
    # 复用已有 manifest 时，⑥ 会把 manifest 里**全部**记录当作本轮范围 → 白跑一堆）。
    # **必须在 stage1_ids 计算之前**过滤 prior/man_rec（首次插入时放错位置 → UnboundLocalError，
    # 而且那次「修好」的补丁因为 `pkill -f run_repro.py` 把执行补丁的 shell 自己杀了而从未落盘
    # —— 教训：pkill/pgrep 的 -f 模式会匹配到自己的命令行）。
    if a.only_osv:
        want = set(x.strip() for x in a.only_osv.split(",") if x.strip())
        scope_ids = [o for o in scope_ids if o in want]
        prior = {k: v for k, v in prior.items() if k in want}
        man_rec = {k: v for k, v in man_rec.items() if k in want}
        log(f"[范围] --only-osv 限定 → {len(scope_ids)} 条")
    if a.force_stage1:
        stage1_ids = scope_ids
        log(f"\n[路由] --force-stage1 → 全部 {len(scope_ids)} 条走 Stage1（W2 旧行为，仅供对照）")
    else:
        stage1_ids = [o for o in scope_ids if prior.get(o) == "head"]
        log(f"\n[路由 W3] Stage1(HEAD) 只给 `commit_source=head` 的 **{len(stage1_ids)}/{len(scope_ids)}** 条；"
            f"其余 {len(scope_ids)-len(stage1_ids)} 条 has_fixed **直接进钉版队列**")
    if a.min_free_gb:
        log(f"[护栏] --min-free-gb {a.min_free_gb}：每次构建前检查磁盘余量")

    # ---------- ② Stage1 ----------
    def bcmd(stage, extra=(), max_builds=None):
        c = [py, "build_orchestrator.py", "--manifest", man, "--out", BUILD_RECORDS,
             "--state", STATE, "--stage", stage, "--build-timeout", str(a.build_timeout),
             "--stop-after-failures", str(a.stop_after_failures)]
        mb = a.max_builds if max_builds is None else max_builds
        if mb:
            c += ["--max-builds", str(mb)]
        if a.force:
            c += ["--force"]
        if a.no_era_precheckout:
            c += ["--no-era-precheckout"]
        if a.min_free_gb:
            c += ["--min-free-gb", str(a.min_free_gb)]
        c += list(extra)
        return c

    if not stage1_ids:
        log("\n▶ Stage1 **整段跳过**（本轮范围内没有 `commit_source=head` 的 crash）")
    else:
        if step(f"② build_orchestrator --stage 1（HEAD 构建，{len(stage1_ids)} 条）",
                bcmd("1", ["--only-osv", ",".join(stage1_ids)]), a.dry_run) not in (0,):
            log("  ⚠ Stage1 非 0 退出（可能 gate ABORT 或急停）→ 仍继续跑 ③ 看已有产物")
        cmd3 = [py, "repro_runner.py", "--manifest", man, "--build-records", BUILD_RECORDS,
                "--state", STATE, "--out", obs, "--only-osv", ",".join(stage1_ids)]
        if step("③ repro_runner（HEAD 二进制）", cmd3, a.dry_run) != 0:
            return 1

    # ---------- Stage2：walk-back（② 与 ③ **逐格交错** + [W3 N12] tier 感知停止）----------
    # [实现 W2 架构修] walk-back 循环必须在 ⑥：「何时停」需要**复现+分级**结果，② 只懂构建。
    # [实现 W3 N12] 停止判据从「首个 reproduced_any」改为「首个 **tier ∈ {strict, medium}**」：
    #   W2 实测 OSV-2020-2251 在 depth1 撞上一个**无关** bug（use-after-free，帧全不同）就停了，
    #   而静态 check 说真修复在 depth2 → 该条被记成 loose。现在只拿到 loose 会继续往下试，
    #   各格结果全记进 `walkback_trace.jsonl`，最后取**最佳 tier** 那格作为该 crash 的结论。
    # [实现 W3 N17] 任何一格**构建失败**都继续下一格（含 ① `located` 的主格，其回退格由
    #   `plan_pinned` 给出）→ 不再因一次构建失败丢掉整条 crash。
    if not a.stage1_only:
        lat1 = _latest(obs)
        repro_head = {o for o, d in lat1.items() if d.get("reproduced_any")}
        todo = [o for o in scope_ids
                if o not in repro_head and not (man_rec.get(o) or {}).get("skip_reason")]
        log(f"\n{'═'*76}\n▶ Stage2 walk-back：{len(todo)} 条待钉版"
            f"（范围内 {len(scope_ids)} − HEAD 已复现 {len(repro_head & set(scope_ids))}"
            f" − manifest 终止性 skip {len(scope_ids)-len(todo)-len(repro_head & set(scope_ids))}）"
            f"\n{'═'*76}")
        aborted_gate = None        # TIER_RANK 已提到模块级（W5：`stop_decision()` 也要用）
        # ---- [W4 Phase3b] 同项目连续同类失败 → 早停。N 默认 **2**，理由：----
        # ① 只数**版本确定性**失败类（DETERMINISTIC_FAIL：由「上游 commit × 当前 build.sh/
        #    工具链」决定，同项目同 era 必然同样失败）；瞬态的 `network_fetch` **不计入**
        #    （且 ② 已按 N16 自动重试 1 次）。
        # ② 实测支持：harfbuzz **6/6** 同类失败、flatbuffers **4/4** 同类失败（W2+W3），
        #    未出现过「前 2 次同类失败、第 3 次成功」的实例。
        # ③ 代价有界：早停只影响**本轮**该项目剩余队列（不写进 state，下轮可重试）。
        #    取 3 → 多白跑一次（harfbuzz 单次 90–320s）；取 1 → 一次偶发失败就封项目，太激进。
        fail_streak = collections.defaultdict(collections.Counter)
        blocked_proj = set()
        n_precheck = n_skip_blocked = 0

        def proj_of(osv):
            return (man_rec.get(osv) or {}).get("project")

        def bump_fail(proj, cls):
            """记一次确定性失败 → 返回该项目该类的连续次数（瞬态类返回 0、不计数）。"""
            if cls not in DETERMINISTIC_FAIL:
                return 0
            fail_streak[proj][cls] += 1
            return fail_streak[proj][cls]
        trace_path = os.path.join(rd, "walkback_trace.jsonl")
        n_stop_early = n_loose_cont = n_buildfail_cont = 0
        n_stop_frac = n_shadow_fire = 0     # [W5 N12] frac 停次数 / shadow「本来会停」次数
        n_purged = purge_freed = 0          # [W5] 逐条回收计数
        for oid in todo:
            stop_reason = None              # 本条是 tier 停还是 frac 停（None = 走完/失败）
            cell_recs = []                  # [W5] 本条用过的构建记录 → 证据落盘后据此回收归档
            if a.max_builds and count_builds(BUILD_RECORDS, t_start) >= a.max_builds:
                log(f"  ⛔ --max-builds {a.max_builds} 用尽 → 停止 walk-back")
                break
            if a.min_free_gb and free_gb() < a.min_free_gb:
                log(f"  ⛔ 磁盘余量 {free_gb():.1f}G < --min-free-gb {a.min_free_gb} → 停止本轮")
                break
            if proj_of(oid) in blocked_proj:
                n_skip_blocked += 1
                continue                       # [W4 Phase3b] 该项目已被早停
            try:
                plan = get_plan(oid, man, a, py)
            except RuntimeError as e:
                log(f"  ⛔ {e}")
                log("  → 本轮在此停止（已完成的记录已落盘；修好 gate 条件后重跑即可续）")
                aborted_gate = str(e)
                break
            if not plan:
                log(f"  {oid}: 无钉版计划（见 --print-plan 的 no_plan_why）→ repro_version=none")
                continue
            # **[N62] 每条 crash 开跑前查一次磁盘水位**（低于阈值就即时回收，见 mid_round_clean）
            # **[N64]** 回收后仍低于硬底线 → mid_round_clean 抛 RuntimeError，在此**优雅停轮**
            #   （与上面 gate 中止同一处置：已完成的记录已落盘，续跑减小 --limit 即可）
            if free_gb(rc.ARTIFACTS) < a.mid_clean_free_gb:
                try:
                    mid_round_clean(a, f"即将处理 {oid}", t_start)
                except RuntimeError as e:
                    log(f"  ⛔ {e}")
                    log("  → 本轮在此停止（已完成的记录已落盘）")
                    aborted_gate = str(e)
                    break
            log(f"  ── {oid}: 计划 {len(plan)} 格 {[(d, (c or '?')[:10]) for d, c, _ in plan]}")
            results, best = [], None
            for depth, commit, note in plan:
                if not commit:
                    log(f"     depth={depth} 无法解析 → 中止 walk-back")
                    results.append(dict(depth=depth, commit=None, note=note, build="unresolved"))
                    break
                if a.max_builds and count_builds(BUILD_RECORDS, t_start) >= a.max_builds:
                    log("     ⛔ --max-builds 用尽（walk-back 中）")
                    break
                if a.min_free_gb and free_gb() < a.min_free_gb:
                    log(f"     ⛔ 磁盘余量 {free_gb():.1f}G < {a.min_free_gb} → 中止本条")
                    break
                ov = f"{oid}={commit}" + (f":{depth}" if depth is not None else "")
                # [实现 W4 Phase4(d)] **按 crash 自己的 `job_arch` 构建**（默认开）。
                # ✅ W4 配对实测（c-blosc2 同 commit 同 testcase，n=2）：ground truth 来自 i386 job，
                # x86_64 构建把 `ndlz_decompress` **内联掉**了 → observed 少一帧 →
                # `pos 0.3333 / subseq 0.0 / frac 0.6667` = **medium**；
                # i386 构建该帧在 → `1.0/1.0/1.0/1.0` = **strict**。**tier 直接升一档。**
                # 注意这是**替换**而非新增：i386 上报的 crash 本来也要建一次，只是换成对的架构
                # → 常规情况**不多花构建**（仅当同项目同 commit 同时有 x86_64 与 i386 crash 时才多一次）。
                arch = ((man_rec.get(oid) or {}).get("job_arch") or "x86_64") \
                    if a.match_job_arch else "x86_64"
                if arch != "x86_64":
                    log(f"     [arch] {oid} 的 job_arch={arch} → 按该架构构建（Phase4(d)）")
                if step(f"② 建第 {depth} 格 {commit[:12]}",
                        bcmd("2", ["--only-osv", oid, "--commit-override", ov,
                                   "--architecture", arch]), a.dry_run) != 0:
                    log("     ⚠ ② 非 0 退出 → 试下一格")
                brec = _latest_build_for(oid, BUILD_RECORDS)
                if a.dry_run:
                    continue
                if not brec or brec.get("build_status") != "ok" or not brec.get("binary_dir"):
                    cls = (brec or {}).get("build_error_class")
                    # [W4 Phase3a] 预检拦截 → **放弃整条**：更深的格是更老的 commit，
                    # build.sh 要的 target 只会更不可能存在（✅ W3：harfbuzz 三格全同一错误）
                    if cls == "buildscript_mismatch":
                        left = len(plan) - len(results) - 1
                        log(f"     第 {depth} 格被**构建前预检**拦下（{cls}）→ 放弃整条"
                            f"（更深的格只会更老、同样缺；省 {max(left,0)} 次构建）")
                        results.append(dict(depth=depth, commit=commit, note=note,
                                            build="precheck_blocked", build_error_class=cls))
                        n_precheck += 1
                        bump_fail(proj_of(oid), cls)
                        break
                    log(f"     第 {depth} 格**构建失败**（{cls}）→ [N17] 继续下一格")
                    if bump_fail(proj_of(oid), cls) >= a.stop_project_after:
                        blocked_proj.add(proj_of(oid))
                        log(f"  ⛔ [早停] {proj_of(oid)} 已连续 {a.stop_project_after} 次 `{cls}`"
                            f" → 跳过该项目本轮剩余队列（W3 harfbuzz 白跑 19.5min 的教训）")
                    results.append(dict(depth=depth, commit=commit, note=note, build="fail",
                                        build_error_class=cls,
                                        build_seconds=(brec or {}).get("build_seconds")))
                    n_buildfail_cont += 1
                    continue
                cell_recs.append(brec)     # [W5] 只有构建成功的格才有归档可回收
                c3 = [py, "repro_runner.py", "--manifest", man, "--build-records", BUILD_RECORDS,
                      "--state", STATE, "--out", obs2, "--only-osv", oid, "--prefer", "pinned",
                      "--binary-override", f"{oid}={brec['binary_dir']}"]
                if step(f"③ 跑第 {depth} 格", c3, a.dry_run) != 0:
                    log("     ⚠ ③ 非 0 退出 → 试下一格")
                    continue
                o = _latest(obs2).get(oid)
                if not o:
                    continue
                v = VT.verify_one(o, a.t_strict, 3)          # 复用 ④ 的**同一份**分级逻辑
                tier = v["verification_tier"]
                # [W5 N12] 停止判据 = 纯函数（自测 preflight/w5_selftest_stopfrac.py 19 项）。
                # `--stop-frac` 默认 0（关）→ 行为与 W4 完全一致；shadow 字段则**常开**。
                dec = stop_decision(tier, v["score_subseq_frac"],
                                    bool(o.get("reproduced_any")), a.stop_frac)
                results.append(dict(depth=depth, commit=commit, note=note, build="ok",
                                    tier=tier, reproduced=bool(o.get("reproduced_any")),
                                    score_pos=v["score_pos"], score_subseq=v["score_subseq"],
                                    score_subseq_frac=v["score_subseq_frac"],
                                    crash_type_match=v["crash_type_match"],
                                    observed_crash_type=o.get("observed_crash_type"),
                                    build_seconds=brec.get("build_seconds"),
                                    era_cache_hit=brec.get("era_cache_hit"),
                                    # shadow：默认 OFF 也记下「本来会停」→ 每轮自动攒 A/B 数据，
                                    # 攒够 distinct-crash n≥10 且 0 tier 损失即可翻转默认（预注册）
                                    frac_stop_would_fire=dec["would_fire"]))
                if dec["would_fire"]:
                    n_shadow_fire += 1
                if dec["stop"]:
                    best = (depth, o, v)
                    stop_reason = dec["reason"]
                    if dec["reason"] == "tier":
                        n_stop_early += 1
                        log(f"     ✅ 第 {depth} 格 **{tier}** → 停（walkback_best_depth={depth}）")
                    else:
                        n_stop_frac += 1
                        log(f"     ✅ 第 {depth} 格 **{tier}** 但 frac="
                            f"{v['score_subseq_frac']:.3f} ≥ --stop-frac {a.stop_frac}"
                            f" → [N12] 停（帧已对齐 = 同一 bug 的不同表现，下探无收益）")
                    break
                if best is None or TIER_RANK[tier] > TIER_RANK[best[2]["verification_tier"]]:
                    best = (depth, o, v)
                log(f"     第 {depth} 格 = **{tier}**（未达 medium）→ [N12] 继续往下试"
                    + ("；shadow：frac≥0.6 本会停" if dec["would_fire"] else ""))
                n_loose_cont += 1
            if a.dry_run:
                continue
            # 逐格轨迹落盘（Phase 5(a) 与 B/C 重算的原始依据）
            _append(trace_path, {"osv_id": oid, "project": (man_rec.get(oid) or {}).get("project"),
                                 "prior_commit_source": prior.get(oid),
                                 "static_check_verdict": (man_rec.get(oid) or {}).get("static_check_verdict"),
                                 "plan": [[d, c, n2] for d, c, n2 in plan],
                                 "results": results,
                                 "best_depth": (best[0] if best else None),
                                 "best_tier": (best[2]["verification_tier"] if best else None),
                                 "stop_reason": stop_reason,          # [W5] tier / frac / None
                                 "stop_frac_arg": a.stop_frac})       # 本轮阈值（0=关）→ 可复算
            # [W5] 顺序要紧：**先标 binary_pruned → 再写证据 → 最后删二进制**。
            # 反了就会留下一行指向已删目录、却没有任何标记的记录（无声悬空指针，N25/N26 同族）。
            purge_dirs = BO.select_purge_dirs(cell_recs) if a.purge_on_verify else []
            pruned_flag = True if purge_dirs else None
            if best:
                depth, o, v = best
                chosen = dict(o)
                chosen.update({"walkback_depth_actual": depth, "walkback_best_depth": depth,
                               "walkback_best_tier": v["verification_tier"],
                               "walkback_depths_tried": len(results),
                               "walkback_n_build_fail": sum(1 for x in results
                                                            if x.get("build") == "fail"),
                               "walkback_stop_reason": stop_reason,   # [W5 N12]
                               "binary_pruned": pruned_flag,          # [W5] 归档已回收
                               "skip_reason": None, "prefer": "pinned"})
                _append(obs2, chosen)          # 最后写入 = ④/⑤ 的「最新」→ dataset 取最佳 tier
            else:
                last = _latest(obs2).get(oid) or _latest(obs).get(oid) or {}
                merged = dict(last)
                merged.update({"osv_id": oid,
                               "project": last.get("project")
                               or plan_meta.get(oid, {}).get("project"),
                               "reproduced_any": False, "walkback_exhausted": True,
                               "walkback_depth_actual": None, "walkback_best_depth": None,
                               "walkback_depths_tried": len(results),
                                "walkback_n_build_fail": sum(1 for x in results
                                                             if x.get("build") == "fail"),
                                "walkback_stop_reason": stop_reason,   # [W5] 此路必为 None
                                "binary_pruned": pruned_flag,          # [W5] 三格全空也照样回收
                                "notes": ((last.get("notes") or "") +
                                          " walkback_exhausted").strip(),
                               "skip_reason": None, "prefer": "pinned",
                               "binary_source": last.get("binary_source")
                               or "walkback_exhausted"})
                _append(obs2, merged)
            if purge_dirs:                   # [W5] 逐条回收：证据已落盘，现在才删二进制
                pr = BO.purge_archives(purge_dirs, dataset_path=DATASET,   # [W5] 必传：共享归档保护
                                       why=f"purge_on_verify:{oid}")
                n_purged += pr["n_deleted"]
                purge_freed += pr["freed_bytes"]
        log(f"\n  [walk-back 统计] 达 medium+ 即停 {n_stop_early} 次；只拿到 loose/none 而继续下探 "
            f"{n_loose_cont} 次；构建失败后继续下一格 {n_buildfail_cont} 次；"
            f"**构建前预检拦截 {n_precheck} 次**；早停跳过 {n_skip_blocked} 条"
            f"（被封项目 {sorted(blocked_proj) or '无'}）")
        # [W5 N12] frac 停 + shadow 计数。shadow 是**翻转默认值的唯一依据**，必须每轮都报：
        # 预注册判据 = distinct-crash n≥10 且 tier 损失 0 → `--stop-frac` 默认改 0.6。
        if a.purge_on_verify:
            log(f"  [W5 逐条回收] 删除 {n_purged} 个钉版归档、释放 {purge_freed/1e6:.0f} MB"
                f"（HEAD/_shared 保留；行标 binary_pruned=true，sha256+配方仍在 → 可 bit 级重建）")
        log(f"  [N12 frac 停] --stop-frac={a.stop_frac}（0=关）→ 实际 frac 停 {n_stop_frac} 次；"
            f"**shadow「本来会停」{n_shadow_fire} 格**（重算："
            f"python3 preflight/w5_phase1_replay_stopfrac.py）")

    # ---------- ④ 分级 ----------
    # 两遍 observation 合成一个输入（④ --latest-only 会按文件顺序取最新 = Stage2 覆盖 Stage1）
    obs_all = os.path.join(rd, "observations_all.jsonl")
    if not a.dry_run:
        with open(obs_all, "w", encoding="utf-8") as fo:
            for pth in (obs, obs2):
                if os.path.exists(pth):
                    fo.write(open(pth, encoding="utf-8").read())
    cmd4 = [py, "verify_tiered.py", "--observations", obs_all, "--out", ver,
            "--t-strict", str(a.t_strict)]
    if step("④ verify_tiered", cmd4, a.dry_run) != 0:
        return 1

    # ---------- ⑤ 落数据集 ----------
    cmd5 = [py, "annotate_dataset.py", "--manifest", man, "--build-records", BUILD_RECORDS,
            "--observations", obs_all, "--verifications", ver, "--out", DATASET,
            "--run-id", run_id, "--only-observed"]      # [W3 修] 不得用未跑记录覆盖上轮真实结果
    if step("⑤ annotate_dataset（append-only）", cmd5, a.dry_run) != 0:
        return 1

    # ---------- [W3 Phase2] 归档裁剪（默认开）----------
    if not a.no_prune and not a.dry_run:
        step("② --prune-archive --prune-apply（裁掉未被 verified 记录引用的归档）",
             [py, "build_orchestrator.py", "--prune-archive", "--prune-apply", "--state", STATE,
              "--dataset", DATASET, "--manifest", man])
    elif a.no_prune:
        log("\n▶ 归档裁剪：--no-prune 关闭")

    # ---------- 汇总 ----------
    if not a.dry_run:
        s = summarize(obs_all, ver)
        el = datetime.datetime.now().timestamp() - t_start
        nb = count_builds(BUILD_RECORDS, t_start)
        log(f"\n{'#'*76}\n# 本轮汇总 run_id={run_id}")
        log(f"#   manifest {n_man} 条 → observation {s['n_obs']} 条 → 复现 {s['reproduced']} 条")
        log(f"#   tier 分布: {s['tiers']}")
        if s["skipped"]:
            log(f"#   跳过原因: {s['skipped']}")
        log(f"#   实际构建 {nb} 次" + (f"（上限 {a.max_builds}）" if a.max_builds else "")
            + f"；墙钟 {el/60:.1f}min")
        log(f"#   dataset: {DATASET}（append-only）\n{'#'*76}")
        # 写一份 run 元数据，便于跨轮对账
        json.dump(dict(run_id=run_id, n_manifest=n_man, n_obs=s["n_obs"],
                       reproduced=s["reproduced"], tiers=s["tiers"], skipped=s["skipped"],
                       n_builds=nb, wall_seconds=round(el, 1), stage1_only=a.stage1_only,
                       max_builds=a.max_builds, force=a.force, projects=a.projects,
                       limit=a.limit, sanitizers=a.sanitizers, crash_types=a.crash_types,
                       t_strict=a.t_strict),
                   open(os.path.join(rd, "run_meta.json"), "w"), ensure_ascii=False, indent=1)
        # **[N61] 轮末自动回收磁盘**（用户批准的「自动回收 + 分级保留」策略）。
        # ✅ 实测本轮之前：归档涨到 8.5 GB、可用只剩 4.1 GB，unicorn 探针期间一度掉到 **2.7 GB**
        #   （era 机制为每个 era commit 建 ~2.4 GB 镜像、旧 tag 变悬空）。
        # 语义见 disk_policy.py：`--clean-build`/`--prune-images` 是**纯废物 → 无条件清**；
        # 归档瘦身（orphans/siblings）只在低于 `--min-free-gb` 时才动，且**只删未被交付引用的文件**
        # （交付视图硬链接进归档，交付必需的那份永远不动），事后强制跑交付自校验 + 审计。
        if a.post_clean:
            log("# [N61] 轮末自动回收磁盘 …")
            subprocess.run([sys.executable, os.path.join(HERE, "disk_policy.py"),
                            "--clean-build", "--prune-images",
                            "--prune-orphans", "--prune-siblings",
                            "--min-free-gb", str(a.post_clean_free_gb), "--apply"],
                           check=False)
    return 0


if __name__ == "__main__":
    sys.exit(main())

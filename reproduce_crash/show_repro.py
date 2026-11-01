#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""看一条 crash 的复现：把复现记录表行 + 三件套 + ④ 的判分依据一次摊开。

用法：
    python3 show_repro.py OSV-2020-2087          # 看一条
    python3 show_repro.py --tier strict          # 列某一档全部
    python3 show_repro.py --list                 # 列全部（按 tier/项目）
    python3 show_repro.py --project hunspell     # 列某项目
    python3 show_repro.py OSV-2022-1004 --cmd    # 额外打印可直接复制的重跑命令

设计原则（与本仓库一致）：**只读复现记录表与磁盘，不重算、不改写**。
`--check` 会额外做三件只读核对：报告文件在不在、输入在不在、二进制在不在（或已标回收）。
"""
import argparse
import json
import collections
import glob
import os
import re
import shutil
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
DATASET = os.path.join(HERE, "repro_dataset.jsonl")
TIERS = ("strict", "medium", "loose", "none")


def load():
    """append-only 复现记录表 → 每个 osv_id 取**最新**一行。"""
    lat = {}
    with open(DATASET, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                r = json.loads(line)
                lat[r["osv_id"]] = r
    return lat


def _sig_strip(f):
    """只留函数名，剥掉 C++ 参数签名。

    为什么要它：**R**（`crash_state_recovered.jsonl`）存的是符号化后的**裸函数名**，
    而 **O**（ASAN/MSAN stderr）带完整 demangle 签名（`AffixMgr::cpdcase_check(char const*, int)`）。
    两侧形态天生不同 → 现行 `normalize_one_frame` 不剥签名，C++ 项目**每帧都对不上**（N39）。
    """
    return re.sub(r"\(.*$", "", str(f))


def _mark(ok, yes="在盘", no="**不在**"):
    return yes if ok else no


def show(r, want_cmd=False, check=False):
    oid = r["osv_id"]
    tier = str(r.get("verification_tier"))
    ve = r.get("_ver_extra") or {}
    oe = r.get("_obs_extra") or {}
    bd = r.get("binary_dir")
    on_disk = bool(bd) and os.path.isdir(bd)
    pruned = bool(r.get("binary_pruned"))
    tc = r.get("testcase_path") or ""
    lg = r.get("raw_log_path") or ""

    print("=" * 84)
    print(f"{oid}    {r.get('project')} / {r.get('sanitizer')} / {r.get('fuzz_target')}"
          f"    →  tier = {tier.upper()}")
    print("=" * 84)

    print("【1】钉在哪个版本")
    print(f"  pinned_commit   {r.get('pinned_commit')}")
    print(f"  fixed_commit    {r.get('fixed_commit')}   （pinned = fixed~{r.get('walkback_depth_actual')}）")
    print(f"  commit_source   {r.get('commit_source')}      repo_url {r.get('repo_url')}")
    if r.get("repo_url_build") and r["repo_url_build"] != r.get("repo_url"):
        print(f"  实际拉取源      {r['repo_url_build']}   （N37 镜像，SHA 不变）")

    print("\n【2】期望 vs 实测")
    print(f"  期望崩溃类型    {r.get('crash_type_full_expected')}")
    print(f"  实测崩溃类型    {r.get('observed_crash_type')}")
    print(f"  类型一致        {r.get('crash_type_match')}"
          f"      dedup_token {oe.get('dedup_token')}"
          f"      scariness {oe.get('scariness')} ({oe.get('scariness_label')})")
    print(f"  退出码/信号     {r.get('exit_code')} / {r.get('signal')}"
          f"      重试 {r.get('retry_count')} 次      用时 {oe.get('run_seconds')}s")

    print("\n【3】④ 的判分依据")
    print("  算法：`score_subseq` = R 是否为 O 的**有序子序列**（只要求先后顺序，**不要求位置相同**）")
    R = r.get("recovered_frames") or []
    O = r.get("observed_frames") or []
    if not R:
        print("  ⚠ R 为空 → 三个帧分数不可用，tier 只能靠 crash_type 判（见 DELIVERY §2.2）")
    else:
        print(f"  R（原始恢复帧，共 {len(R)}）逐帧在 O 里按序找：")
        cursor = 0
        exact = nameonly = 0
        for i, rr in enumerate(R):
            at = None
            kind = None
            for j in range(cursor, len(O)):
                if O[j] == rr:
                    at, kind, cursor = j, "exact", j + 1
                    break
                if _sig_strip(O[j]) == _sig_strip(rr):
                    at, kind, cursor = j, "name", j + 1
                    break
            if at is None:
                print(f"    [{i}] {str(rr)[:52]:<54} → ❌ O 里没有")
            elif kind == "exact":
                exact += 1
                print(f"    [{i}] {str(rr)[:52]:<54} → ✅ O[{at}] 完全相同")
            else:
                nameonly += 1
                print(f"    [{i}] {str(rr)[:52]:<54} → ⚠ O[{at}] 仅函数名同（差 C++ 签名）")
        print(f"  → 完全相同且按序命中 **{exact}/{len(R)}**；另有 {nameonly} 帧「只差签名」")
        print("    （`score_subseq` 只认**完全相同**，所以「只差签名」的帧**不计分** → 见 N39）")
        if exact < len(R) and nameonly:
            print("    ⚠ 这条就是被签名差异降档的典型：函数名与顺序其实全对得上")
    print(f"  O（本次实测帧，前 8）: {', '.join(str(x)[:40] for x in O[:8])}"
          + (" …" if len(O) > 8 else ""))
    print(f"  → tier_why: {ve.get('tier_why')}")

    print("\n【4】三件套在哪")
    print(f"  崩溃报告  {lg or '（无）'}")
    print(f"            {_mark(os.path.exists(lg)) if lg else '—'}")
    print(f"  输入      {tc}  ({r.get('testcase_size')} 字节, sha256 {str(r.get('testcase_sha256'))[:16]}…)")
    print(f"            {_mark(os.path.exists(tc)) if tc else '—'}")
    print(f"  二进制    {bd or '（无）'}")
    if on_disk:
        try:
            names = sorted(os.listdir(bd))
            print(f"            在盘，{len(names)} 个文件: {' '.join(names[:5])}"
                  + (" …" if len(names) > 5 else ""))
        except OSError:
            print("            在盘（列目录失败）")
    elif pruned:
        print("            **已回收**（binary_pruned=true）→ sha256 与构建配方仍在复现记录表，可 bit 级重建")
    else:
        print("            **缺失且未标回收** ← 这是红线，审计报告里必须为 0")

    if check:
        bad = []
        if lg and not os.path.exists(lg):
            bad.append("崩溃报告缺失")
        if tc and not os.path.exists(tc):
            bad.append("输入缺失")
        if bd and not on_disk and not pruned:
            bad.append("二进制缺失且未标回收")
        if tier in ("strict", "medium", "loose") and not r.get("reproduced_any"):
            bad.append("tier≠none 但 reproduced_any 为假")
        print("\n【5】只读核对：" + ("✅ 无异常" if not bad else "❌ " + "；".join(bad)))

    if want_cmd:
        print("\n【6】重跑命令（复制即用）")
        if not on_disk:
            print("  ⚠ 二进制已回收，需先重建：见 DELIVERY §6 的重建流程")
        else:
            tgt = r.get("fuzz_target") or ""
            print(f"  cd {HERE}")
            print(f"  docker run --rm -i \\")
            print(f"    -v {bd}:/out -v {tc}:/testcase \\")
            print(f"    -e FUZZING_ENGINE=libfuzzer -e SANITIZER={r.get('sanitizer')} \\")
            print(f"    -e RUN_FUZZER_MODE=interactive \\")
            print(f"    gcr.io/oss-fuzz-base/base-runner:ubuntu-24-04 \\")
            print(f"    bash -c 'cd /out; ./{tgt} -- /testcase < /dev/null'")
    print()


def lst(lat, tier=None, project=None):
    rows = [r for r in lat.values()
            if (not tier or r.get("verification_tier") == tier)
            and (not project or r.get("project") == project)]
    order = {t: i for i, t in enumerate(TIERS)}
    rows.sort(key=lambda r: (order.get(str(r.get("verification_tier")), 9),
                             str(r.get("project")), r["osv_id"]))
    print(f"{'OSV':<18}{'项目':<14}{'san':<9}{'tier':<8}{'实测崩溃类型':<34}报告 输入 二进制")
    for r in rows:
        lg = r.get("raw_log_path") or ""
        tc = r.get("testcase_path") or ""
        bd = r.get("binary_dir")
        b = "在盘" if (bd and os.path.isdir(bd)) else ("回收" if r.get("binary_pruned") else "缺")
        print(f"{r['osv_id']:<18}{str(r.get('project')):<14}{str(r.get('sanitizer')):<9}"
              f"{str(r.get('verification_tier')):<8}"
              f"{str(r.get('observed_crash_type') or r.get('crash_type_full_expected'))[:32]:<34}"
              f"{'✅' if os.path.exists(lg) else '❌':<5}"
              f"{'✅' if os.path.exists(tc) else '❌':<5}{b}")
    print(f"\n共 {len(rows)} 条")


INDEX_DIR = os.path.join(HERE, "artifacts", "by_crash_type")
REPRO_LOGS = os.path.join(HERE, "artifacts", "logs", "reproduce")


def _replay_bundle(bd, target):
    """**精确**最小重放包 → (文件名列表, 是否含脚本包装器)。

    规则：`target` 本身 + **若它不是 ELF 而是脚本包装器**则解析它引用的兄弟文件 +
    同名 `.dict`/`.options`。

    ✅ 实测 151 条：每包**恰好 1 个 ELF**；文件数 1 → 128 条、2 → 19 条、3 → 4 条；
       合计 1555 MB（用硬链接则**额外 0 字节**）。
    ⚠ **不能用「同前缀」规则**：`pcre2_fuzzer_1` 会误匹配 `pcre2_fuzzer_16`
       → 实测会多出 1 条 21 文件的包、3 条含 2 个 ELF 的包。
    ⚠ libwebp 的 target 形如 `advanced_api_fuzzer@AdvancedApi.AdvancedApiTest`，
       那是 **shell 包装脚本**（`$this_dir/advanced_api_fuzzer --fuzz=… -- $@`），
       真 ELF 是 `advanced_api_fuzzer` → 两个都得带上，否则
       `./advanced_api_fuzzer: not found`。
       （顺带解释 N47：脚本最后一行是 `chmod -x`，**退出码取的是 chmod 的**，
        所以子进程 ASan 崩了而 `exit_code=0`。）
    """
    files, wrapped = [target], False
    p = os.path.join(bd, target)
    if os.path.isfile(p):
        try:
            is_elf = open(p, "rb").read(4) == b"\x7fELF"
        except OSError:
            is_elf = True
        if not is_elf:                                   # 脚本包装器 → 解析它引用的兄弟文件
            wrapped = True
            try:
                txt = open(p, encoding="utf-8", errors="replace").read()
            except OSError:
                txt = ""
            for m in re.findall(r"this_dir/([A-Za-z0-9_.@+%-]+)", txt):
                if m != target and os.path.isfile(os.path.join(bd, m)):
                    files.append(m)
    for suf in (".dict", ".options"):                    # 运行期数据文件（不是二进制）
        if os.path.isfile(os.path.join(bd, target + suf)):
            files.append(target + suf)
    return sorted(set(files)), wrapped


def _select_report(r):
    """挑**与复现记录表 `binary_dir` 一致且 `exit==1`** 的那一份 report（含 N40 轮转副本）。

    为什么不能直接用 `raw_log_path`：那是 `logs/reproduce/<OSV>.log` **单一可变路径**，
    后一次重放会覆盖它；而 walk-back 对 loose 档「继续下探」→ 留在盘上的最新一份
    往往是**更深、没崩的那一格**。✅ 实测 3 条会出现「tier 说崩了、report 显示没崩」的观感矛盾。
    → 交付视图里存**冻结副本**，从轮转副本中选出对得上的那一份。
    """
    oid = r["osv_id"]
    want = os.path.basename((r.get("binary_dir") or "").rstrip("/"))
    cands = sorted(glob.glob(os.path.join(REPRO_LOGS, oid + "*")))
    fallback = r.get("raw_log_path")
    for p in cands:                                      # 先找「同 binary_dir 且 exit==1」
        try:
            head = open(p, encoding="utf-8", errors="replace").read(4000)
        except OSError:
            continue
        m = re.search(r"^# binary_dir: (\S+)", head, re.M)
        e = re.search(r"^# exit: (\S+)", head, re.M)
        if m and e and e.group(1) == "1" and os.path.basename(m.group(1).rstrip("/")) == want:
            return p, None
    if fallback and os.path.isfile(fallback):
        return fallback, ("⚠ 找不到「binary_dir 与复现记录表一致且 exit==1」的 report，"
                          "退回 raw_log_path；这一份可能来自 walk-back 的**另一格**")
    return (cands[0] if cands else None), "⚠ 盘上没有该 OSV 的任何 report"


def build_index(lat, verbose=True):
    """建「按 crash 类型浏览」的**自包含交付视图**（幂等可重建；二进制走硬链接 → 0 额外空间）。

    层级：

        by_crash_type/<crash_type>/<project>/<sanitizer>/<commit>[@arch]/<OSV-ID>/
            ├── <fuzz_target>        ← **唯一的 ELF 可执行文件**（这条 crash 的 driver）
            ├── <fuzz_target>.dict   ← 仅 23 条有：运行期数据文件（**不是**二进制）
            ├── <包装脚本>            ← 仅 libwebp 3 条：入口脚本，它调上面那个 ELF
            ├── testcase             ← 输入文件（副本）
            ├── report.log           ← 崩溃报告（**冻结副本**，选与复现记录表一致的那一份）
            ├── replay.sh            ← 一条命令重放（无需拼 docker 参数）
            └── INFO.txt             ← tier / 期望vs实测 / commit / 判分依据

    **[W5 第十五轮改 · N50]** 用户第二次指出「一个 OSV 文件夹里为什么有多个二进制」——
    N49 把 `binary` 收窄成单文件、却仍保留 `out/` 指向整棵构建树，于是文件夹里**照样有
    2～17 个可执行文件**（那是同一次构建产出的**兄弟 fuzz target**，与这条 crash 无关）。
    本轮改为**只放最小重放包**：实测 151 条**每条恰好 1 个 ELF**，128 条整个文件夹只有
    1 个二进制 + testcase + report + INFO。

    为什么之前要留整棵树、现在可以不留：**实测**（14 个项目×sanitizer 组合逐条真跑）
    「只放 driver（+自身 .dict）」即可重放成功 —— ASan/MSan 运行时是**静态链进 driver** 的
    （`ldd` 无 `libclang_rt.*.so`），符号化也不依赖归档里的 `llvm-symbolizer`。
    原先「只给 driver 会重放失败」的说法**被实验推翻**（那是 W2 flatbuffers 缺 `.bfbs`
    的个案，已泛化过度）。

    为什么归档层仍保留整棵树：缓存键是 `(project, san, commit)`，**同一 commit 的另一条
    crash 可能要另一个 target**（W2 教训：只存请求的那个 → pcre2 8 条 `target_not_in_archive`）。
    → 归档层存全、**交付层收窄**，两层各司其职。

    为什么 commit 层单独存在：一份归档服务多条 crash（✅ 实测 122 个归档服务 151 条）。
    为什么不物理搬动归档：复现记录表 `binary_dir` 是 append-only 的历史绝对路径（N20/N30 同型事故）。
    """
    if os.path.isdir(INDEX_DIR):
        shutil.rmtree(INDEX_DIR)
    # **[N52] 把「全量重放验收」的实测结果写回每个条目**：flaky 不是猜测，是量出来的。
    # 来源 `artifacts/replay_verification.json`（151 条逐条跑 replay.sh、失败者重试）。
    _rv = {}
    _rvp = os.path.join(HERE, "artifacts", "replay_verification.json")
    if os.path.isfile(_rvp):
        try:
            _j = json.load(open(_rvp, encoding="utf-8"))
            for _o, _n in (_j.get("needed_retry") or {}).items():
                _rv[_o] = f"⚠ **flaky**：全量重放验收时**第 {_n} 次**才崩（首轮未崩）→ 请多跑几次"
            for _o, _e in (_j.get("heavily_flaky") or {}).items():
                _rv[_o] = (f"⚠ **重度 flaky**：加测到**第 {_e.get('crashed_on')} 次**才崩"
                           f"（崩溃率 {_e.get('crash_rate')}）；崩时实测 "
                           f"`{_e.get('observed_on_success')}`")
        except (OSError, ValueError):
            pass
    n_ok = n_pruned = n_nodrv = n_wrapped = n_rep_fb = n_with_dir = 0
    per_type = collections.Counter()
    for r in sorted(lat.values(), key=lambda x: x["osv_id"]):
        if r.get("verification_tier") not in ("strict", "medium", "loose"):
            continue                                     # 没复现的没有二进制可交
        bd, oid, tgt = r.get("binary_dir"), r["osv_id"], r.get("fuzz_target")
        if not bd:
            continue
        ct = str(r.get("crash_type_norm") or "unknown")
        base = os.path.basename(bd.rstrip("/"))            # <commit> 或 <commit>__i386
        d = os.path.join(INDEX_DIR, ct, str(r.get("project")), str(r.get("sanitizer")),
                         base, oid)
        os.makedirs(d, exist_ok=True)
        per_type[ct] += 1

        if not os.path.isdir(bd):
            n_pruned += 1
            with open(os.path.join(d, "PRUNED.txt"), "w", encoding="utf-8") as f:
                f.write(f"归档已被回收：{bd}\nsha256 与配方仍在 repro_dataset.jsonl → 可 bit 级重建：\n"
                        f"  python3 rebuild_archives.py --project {r.get('project')}\n")
            # **[N60] 不能在写 INFO.txt 之前 `continue`。** 审计 [4c] 是靠**找 INFO.txt** 来枚举
            # 交付条目的 → 原先已回收条目对审计**完全不可见**：✅ 实测 `OSV-2023-1322` 的归档被回收、
            # 交付里只剩一个 PRUNED.txt，而审计仍报「0 条红线违反」。
            # 「verified 但拿不出二进制」正是最该报红的情形，却被自己的目录结构藏了起来。
            with open(os.path.join(d, "INFO.txt"), "w", encoding="utf-8") as f:
                f.write(f"{oid}   {r.get('project')} / {r.get('sanitizer')}\n")
                f.write(f"⚠ **本条不可重放**：归档已被回收（binary_pruned={r.get('binary_pruned')}）\n")
                f.write(f"tier            = {r.get('verification_tier')}（历史判定，report.log 是当时的证据）\n")
                f.write(f"原 binary_dir   = {bd}\n")
                f.write(f"重建            = python3 rebuild_archives.py --project {r.get('project')}\n")
            continue
        bundle, wrapped = _replay_bundle(bd, tgt)
        elf = [f for f in bundle if os.path.isfile(os.path.join(bd, f))
               and open(os.path.join(bd, f), "rb").read(4) == b"\x7fELF"]
        if not elf or (tgt not in bundle):
            n_nodrv += 1
            with open(os.path.join(d, "DRIVER_MISSING.txt"), "w", encoding="utf-8") as f:
                f.write(f"⚠ `{tgt}` 不在它自己的归档里 → 无法重放（N45）。\n"
                        f"归档: {bd}\n实际有: {sorted(os.listdir(bd))}\n")
            continue
        # ---- 二进制：硬链接（0 额外空间）。**有包装脚本时改用副本**：脚本会 `chmod +x/-x`
        #      它引用的 ELF，硬链接会把 mode 改动传导回归档、破坏 ⑥ 后续直接挂载归档重放。
        for f in bundle:
            src, dst = os.path.join(bd, f), os.path.join(d, f)
            if not os.path.isfile(src):
                continue
            try:
                if wrapped:
                    shutil.copy2(src, dst)
                else:
                    os.link(src, dst)
            except OSError:
                shutil.copy2(src, dst)
            # ⚠ **包装脚本本身也必须可执行**（replay.sh 是 `./<target>` 起手的）。
            #   ✅ 实测抓到：原先「非 ELF 一律 0o644」→ libwebp 3 条 `exit=126`（不可执行）。
            #   规则：ELF、或入口 target、或源文件本来就可执行 → 755；其余（.dict/.options）644。
            os.chmod(dst, 0o755 if (f in elf or f == tgt or os.access(src, os.X_OK)) else 0o644)
        n_ok += 1
        n_wrapped += 1 if wrapped else 0
        # **[W7 修 N69] 归档里的子目录也必须进交付包**（运行期数据文件）。
        # ✅ 实测 espeak-ng：`projects/espeak-ng/build.sh:25` 是 `cp -r espeak-ng-data/ $OUT/`，
        #   N66 修好归档后归档里有 `espeak-ng-data/`（474–487 文件 / 1.4MB），但本函数原先
        #   只按 `bundle` 逐个 `os.path.isfile` 拷 → **交付副本缺整个数据目录** →
        #   `replay.sh` 报 `Error processing file '/out/phontab': No such file or directory`
        #   → exit 77 `fuzz target exited` → **tier=strict 的行实际重放不出来**
        #   （✅ 实测受害者 OSV-2021-1631）。
        #   用硬链接 → 额外磁盘 0 字节（与二进制同策略）。
        n_dir_files = 0
        for _root, _ds, _fs in os.walk(bd):
            if os.path.abspath(_root) == os.path.abspath(bd):
                continue                                  # 顶层文件已由 bundle 处理
            for _fn in _fs:
                _src = os.path.join(_root, _fn)
                _rel = os.path.relpath(_src, bd)
                _dst = os.path.join(d, _rel)
                if os.path.exists(_dst):
                    continue
                os.makedirs(os.path.dirname(_dst), exist_ok=True)
                try:
                    os.link(_src, _dst)
                except OSError:
                    shutil.copy2(_src, _dst)
                n_dir_files += 1
        if n_dir_files:
            n_with_dir += 1
        # ---- testcase / report：副本（小文件 → 文件夹自包含，可整体 tar 交付）
        tc = r.get("testcase_path")
        if tc and os.path.isfile(tc):
            shutil.copy2(tc, os.path.join(d, "testcase"))
        rep, rep_note = _select_report(r)
        if rep:
            shutil.copy2(rep, os.path.join(d, "report.log"))
            n_rep_fb += 1 if rep_note else 0
        # ---- replay.sh：一条命令重放，并**自己给判决**
        # ⚠ 判决必须按**报告内容**而非退出码（与 ⑥ 同一原则，N47）：libwebp 那类 target 的入口是
        #   shell 包装脚本，脚本最后一行是 `chmod -x`，**退出码取的是 chmod 的** → 子进程 ASan
        #   崩了而 `$?`=0。✅ 实测 3 条 libwebp 全是 `exit=0` 却有完整 ASan 报告。
        # ⚠ **[N51] 必须照抄 ⑥ 当时的 `runtime_limits`**：首版 replay.sh 没带
        #   `-rss_limit_mb=2560 -timeout=25`，libFuzzer 就用默认的 2048MB 上限 →
        #   ✅ 实测 2 条 c-blosc2（`OSV-2021-464`/`OSV-2021-366`，复现记录表 **tier=strict**、
        #   验证时 `score_subseq=1.0` 且 crash_type 完全对得上）在交付文件夹里重放变成
        #   `SUMMARY: libFuzzer: out-of-memory`、容器 exit=71 —— **交付的重放命令与产出
        #   report 的那次不是同一个实验**，这比不放命令更糟。
        entry = tgt
        _rl = str(r.get("runtime_limits") or "")
        _kv = dict(x.split("=", 1) for x in _rl.split(":") if "=" in x)
        _fargs = []
        if _kv.get("rss_limit_mb"):
            _fargs.append(f"-rss_limit_mb={_kv['rss_limit_mb']}")
        if _kv.get("timeout"):
            _fargs.append(f"-timeout={_kv['timeout']}")
        _fargs = " ".join(_fargs)
        _dict = f" -dict={tgt}.dict" if os.path.isfile(os.path.join(bd, tgt + ".dict")) else ""
        with open(os.path.join(d, "replay.sh"), "w", encoding="utf-8") as f:
            f.write("#!/bin/sh\n"
                    f"# 重放 {oid}（{r.get('project')}/{r.get('sanitizer')}，"
                    f"tier={r.get('verification_tier')}）\n"
                    "# 用法： bash replay.sh\n"
                    "# 退出码： 1 = **复现成功**（检测到 sanitizer 崩溃报告）；0 = 未复现\n"
                    "#   ⚠ 判决按**报告内容**而非容器退出码 —— 若入口是 shell 包装脚本"
                    "（libwebp 那类），\n"
                    "#     脚本最后一行 `chmod -x` 会把子进程的崩溃退出码吃掉（N47）。\n"
                    f"#   运行参数照抄复现记录表 runtime_limits（N51）：{_rl or '(空)'}\n"
                    "#   ⚠ 本条 crash 若属 flaky（尤其 MSAN / abort 类），单次不崩不代表没复现；"
                    "复现记录表 retry_count>0 的行就是靠重试救回的。\n"
                    'HERE=$(cd "$(dirname "$0")" && pwd)\n'
                    'OUT=$(docker run --rm -v "$HERE":/out -v "$HERE/testcase":/testcase \\\n'
                    f'  -e FUZZING_ENGINE=libfuzzer -e SANITIZER={r.get("sanitizer")} \\\n'
                    '  -e RUN_FUZZER_MODE=interactive \\\n'
                    '  gcr.io/oss-fuzz-base/base-runner:ubuntu-24-04 \\\n'
                    f"  bash -c 'cd /out; ./{entry} -- {_fargs} /testcase{_dict} < /dev/null' 2>&1)\n"
                    'RC=$?\n'
                    'printf "%s\\n" "$OUT"\n'
                    'HIT=$(printf "%s" "$OUT" | grep -m1 -E '
                    '"ERROR: (Address|Memory|Thread)Sanitizer|WARNING: MemorySanitizer|'
                    'SUMMARY: UndefinedBehaviorSanitizer|runtime error:|'
                    # **[N74] 补 `deadly signal`**：`repro_common.py:74-76` 明确规定
                    #   「`deadly signal`（如裸 SEGV）**不排除**——那是真崩溃，只是没有
                    #   sanitizer 报告」，④ verify_tiered 就是按这条判的 tier。
                    # ✅ 实证 OSV-2024-1044（hdf5/**undefined** 构建，无 ASan）：输出
                    #   `SUMMARY: libFuzzer: deadly signal`、`exit_code=77` 与复现记录表**完全一致**，
                    #   但旧正则不认 → replay.sh 报「❌ 未复现」，与复现记录表 tier=loose **自相矛盾**。
                    'ERROR: libFuzzer: deadly signal|SUMMARY: libFuzzer: deadly signal")\n'
                    'if [ -n "$HIT" ]; then\n'
                    '  echo "[verdict] ✅ 复现成功（容器退出码 $RC）：$HIT"\n'
                    '  exit 1\n'
                    'fi\n'
                    'echo "[verdict] ❌ 未复现：无 sanitizer 报告（容器退出码 $RC）"\n'
                    'exit 0\n')
        os.chmod(os.path.join(d, "replay.sh"), 0o755)
        # ---- INFO.txt
        with open(os.path.join(d, "INFO.txt"), "w", encoding="utf-8") as f:
            f.write(f"{oid}   {r.get('project')} / {r.get('sanitizer')}\n")
            f.write(f"唯一可执行文件  = {elf[0]}"
                    f"{'（ELF；入口是包装脚本 ' + entry + '，它调这个 ELF）' if wrapped else ''}\n")
            f.write(f"重放入口        = ./{entry}\n")
            f.write(f"一条命令重放    = bash replay.sh   → 末行打 [verdict]；退出码 1=复现成功\n")
            if oid in _rv:
                f.write(f"重放实测        = {_rv[oid]}\n")
            _extra = [x for x in bundle if x not in elf]
            f.write(f"本目录其它文件  = {_extra or '（无）'} ← 运行期数据/包装脚本，**不是**多个复现结果\n")
            f.write(f"tier            = {r.get('verification_tier')}\n")
            f.write(f"crash_type 期望 = {r.get('crash_type_full_expected')}\n")
            f.write(f"crash_type 实测 = {r.get('observed_crash_type')}\n")
            _d = r.get("walkback_depth_actual")
            f.write(f"pinned_commit   = {r.get('pinned_commit')}  "
                    f"{'(= fixed~%s)' % _d if _d else '(commit_source=%s)' % r.get('commit_source')}\n")
            f.write(f"fixed_commit    = {r.get('fixed_commit')}\n")
            f.write(f"run_id          = {r.get('run_id')}\n")
            f.write(f"源归档          = {bd}\n")
            if rep_note:
                f.write(f"report 说明     = {rep_note}\n")
            f.write("\n判分依据（④）:\n")
            f.write(f"  R (原始恢复帧) = {r.get('recovered_frames')}\n")
            f.write(f"  O (实测帧前6)  = {[str(x)[:60] for x in (r.get('observed_frames') or [])[:6]]}\n")
            f.write(f"  score_subseq   = {r.get('score_subseq')}   crash_type_match = {r.get('crash_type_match')}\n")
            f.write(f"  tier_why       = {(r.get('_ver_extra') or {}).get('tier_why')}\n")
            if r.get("_n46_correction"):
                f.write(f"  N46 更正       = {r['_n46_correction']}\n")
    if verbose:
        print(f"已建索引 {INDEX_DIR}")
        print(f"  crash 条目 {sum(per_type.values())} 个 → **自包含可重放 {n_ok}** / "
              f"⚠ driver 缺失 {n_nodrv} / 归档已回收 {n_pruned}")
        print(f"  每条 = **1 个 ELF** + testcase + report.log(冻结副本) + replay.sh + INFO.txt")
        print(f"  其中 libwebp 式包装脚本 {n_wrapped} 条（入口是脚本、真 ELF 是同目录那个）")
        print(f"  其中含**运行期数据子目录** {n_with_dir} 条（N69：如 espeak-ng 的 espeak-ng-data/）")
        print(f"  report 用了退回副本的 {n_rep_fb} 条（INFO.txt 里已标注）")
        print(f"  层级：<crash_type>/<project>/<sanitizer>/<commit>[@arch]/<OSV-ID>/")
        print(f"  crash 类型 {len(per_type)} 种：")
        for k, v in per_type.most_common():
            print(f"    {k:<30}{v:>4} 条")
    return n_ok, n_pruned, n_nodrv


def tree(limit_per_type=None, depth=99):
    """打印索引树（只读）。"""
    if not os.path.isdir(INDEX_DIR):
        print("（尚未建索引：python3 show_repro.py --build-index）")
        return
    for ct in sorted(os.listdir(INDEX_DIR)):
        cd = os.path.join(INDEX_DIR, ct)
        if not os.path.isdir(cd):
            continue
        n = 0
        for proj in os.listdir(cd):
            for san in os.listdir(os.path.join(cd, proj)):
                for com in os.listdir(os.path.join(cd, proj, san)):
                    n += len(os.listdir(os.path.join(cd, proj, san, com)))
        print(f"{ct}/  ({n} 条)")
        if depth < 2:
            continue
        for proj in sorted(os.listdir(cd)):
            pd = os.path.join(cd, proj)
            if not os.path.isdir(pd):
                continue
            for san in sorted(os.listdir(pd)):
                sd = os.path.join(pd, san)
                if not os.path.isdir(sd):
                    continue
                coms = sorted(os.listdir(sd))
                print(f"  {proj}/{san}/  ({len(coms)} 个 commit)")
                if depth < 3:
                    continue
                show = coms if not limit_per_type else coms[:limit_per_type]
                for com in show:
                    osvs = sorted(os.listdir(os.path.join(sd, com)))
                    print(f"    {com}/")
                    for o in osvs:
                        _od = os.path.join(sd, com, o)
                        extra = ("" if os.path.islink(os.path.join(_od, "binary")) else
                                 ("  ⚠driver缺失" if os.path.exists(os.path.join(_od, "DRIVER_MISSING.txt"))
                                  else "  (已回收)"))
                        print(f"      {o}{extra}")
                if limit_per_type and len(coms) > limit_per_type:
                    print(f"    … 另 {len(coms) - limit_per_type} 个 commit")


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("osv", nargs="*", help="OSV id（可多个）")
    ap.add_argument("--tier", choices=TIERS)
    ap.add_argument("--project")
    ap.add_argument("--list", action="store_true", help="列表模式（不展开详情）")
    ap.add_argument("--cmd", action="store_true", help="额外打印重跑命令")
    ap.add_argument("--check", action="store_true", help="额外做只读核对")
    ap.add_argument("--build-index", action="store_true",
                    help="重建 artifacts/by_crash_type/ **自包含交付视图**（按 crash 类型→项目→"
                         "sanitizer→commit→OSV；每条 = 1 个 ELF + testcase + report.log 冻结副本 "
                         "+ replay.sh + INFO.txt。二进制走硬链接 → 0 额外空间；N50）")
    ap.add_argument("--tree", action="store_true", help="打印 by_crash_type 索引树")
    ap.add_argument("--limit", type=int, default=None, help="--tree 时每个 sanitizer 下最多列几个 commit")
    ap.add_argument("--depth", type=int, default=99, help="--tree 展开到第几层（2=只到类型，3=到项目/sanitizer）")
    a = ap.parse_args()
    lat = load()
    if a.build_index:
        build_index(lat)
        return 0
    if a.tree:
        tree(a.limit, a.depth)
        return 0
    if a.list or a.tier or a.project:
        if a.osv:
            print("⚠ --list/--tier/--project 与位置参数同时给出时，走列表模式")
        lst(lat, a.tier, a.project)
        return 0
    if not a.osv:
        ap.print_help()
        return 2
    miss = [o for o in a.osv if o not in lat]
    if miss:
        print(f"❌ 复现记录表里没有: {miss}")
        print(f"   （复现记录表共 {len(lat)} 条唯一 crash；用 --list 浏览）")
        return 1
    for o in a.osv:
        show(lat[o], want_cmd=a.cmd, check=a.check)
    return 0


if __name__ == "__main__":
    sys.exit(main())

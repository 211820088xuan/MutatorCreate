#!/usr/bin/env bash
# ─────────────────────────────────────────────────────────────────────────────
# 后台复现驱动：优先攻「从未进过流水线」的新程序，以广度换程序多样性
#
# 依据（docs/specs/2026-09-30-...-design.md §6 Phase 0）：
#   * 源数据集 3,790 条 / 334 个程序，已复现仅覆盖 14 个 = 4.2%
#   * 主组 67 条崩溃有 51 个独立簇 / 58 个不同出错点（独立率 76–87%）
#     → 瓶颈不是样本量、不是独立性，而是**程序种类只有 6–7 个**
#   * 补已有程序的崩溃不改善这一点，只有新程序能
#
# 为什么一组只放一个项目（而不是两三个）：
#   run_repro 的 --stop-project-after 只管**构建失败**跳过，
#   没有「每项目成功 N 条就换下一个」的开关。若一组塞多个项目，
#   --sort fixed_first + --limit 会把预算**全给组内产出潜力最高的那个**
#   （✅ W6 实测：matio+lcms 同组 --limit 6 时 6 条全落在一个项目上），
#   → 广度目标落空。故一组一项目、每组小 limit，确保 24 个新程序都被触及。
#
# 为什么显式 --sort fixed_first：
#   N75（DELIVERY.md §4.66）修复前该默认值**语义反转**，实际把无修复提交的排前面，
#   配 --limit 时预期产出 0.4 条 vs 修复后 2.7 条（≈7×）。此处显式写出并加注释，
#   防止将来又被静默改回；行为由 preflight/selftest/w6_selftest_sort_direction.py 锁住。
#
# 为什么显式 --stop-frac 0：
#   run_repro.py:308-315 自身注明该判据的 11 条验证样本**全是 c-blosc2**、
#   跨项目泛化未证，「多项目轮次应显式传 --stop-frac 0 作对照」。
#
# 为什么这些水位线：
#   启动时磁盘可用 12G；最大单项目归档实测 unicorn 4.6G；
#   N64 已实测缺硬底线时可用水掉到 68KB（100% 满）导致进程僵死。
# ─────────────────────────────────────────────────────────────────────────────
set -uo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$HERE" || exit 1

RUN_TAG="${RUN_TAG:-newproj-$(date +%Y%m%d-%H%M)}"
LOG_DIR="$HERE/artifacts/runs/_bg_$RUN_TAG"
mkdir -p "$LOG_DIR"
MAIN_LOG="$LOG_DIR/MAIN.log"

# 排除项及理由（均为实测，非猜测）：
#   ghostscript  200 条，但 unshallow 速率实测仅 29 KB/s → 拉代码就要数天
#   checkstyle / apache-poi  project.yaml language=jvm → 主线只收 c,c++
#   unrar        不在 oss-fuzz/projects/ 树内 → language_of 返回 name-miss
#   matio / net-snmp / cryptofuzz  ← ✅ W6 逐个实测 `resolve_commit_meta(fixed~1)`：
#       matio、net-snmp 的 repo_url 是 `git.code.sf.net`（SourceForge）→ 返回 None；
#       cryptofuzz 虽是 github.com 但该 commit 返回 **http404**。
#       `build_orchestrator.py:303` [N35] 注明解析器只认 github/gitlab（`.patch` 端点）
#       + `REPO_MIRRORS` 显式映射（当前只有 mupdf 一条）+ googlesource（[N42] Gitiles）。
#       → 这 3 个项目共 93 条有修复提交的崩溃**当前无法钉版**，故移出列表。
#
# ⚠ **不要按主机名猜可解析性**：✅ W6 实测 `gitlab.gnome.org`(libxml2)、
#   `gitlab.freedesktop.org`(poppler)、`gitlab.com`(wireshark) **全部可解析**，
#   而我按"只认 gitlab.com"的猜测本会错杀这 3 个（合计 114 条崩溃）。
#   实测结果：24 个候选中 **21 个可解析、覆盖 957 条**有修复提交的崩溃。
#   复算方式见本文件末尾注释。
#
# 排序依据（✅ W6 实测每项目「有 fixed_commit 条数」× 45.7% + 无 × 6.7% 的预期产出，
# 再叠加构建体量：小而快的 C 库放前面尽早拿到多样性收益，巨型构建放最后）：
#   项目        总数  有修复  预期产出
#   lcms         27     27    12.3      yara     24  24  11.0
#   file         32     31    14.2      curl     27  27  12.3
#   grok         26     14     7.2      matio    60  52  24.3
#   libredwg     80     68    31.9      ndpi    142 142  64.9
#   net-snmp     24     22    10.2      cryptofuzz 21 19   8.8
#   open62541    39     39    17.8      libxml2  55  53  24.4
#   poppler      25     24    11.0      libvips  32  32  14.6
#   libjxl       27     25    11.6      openexr  44  44  20.1
#   fluent-bit   77     75    34.4      openthread 53 53 24.2
#   mruby        76     73    33.6      arrow    59  59  27.0
#   serenity     42     39    18.0      systemd  23  22  10.1
#   wireshark    37     36    16.5      php      51  50  22.9
PROJ_LIST=(
  lcms yara file curl grok libredwg ndpi open62541 libxml2 poppler libvips
  libjxl openexr fluent-bit openthread mruby arrow serenity systemd wireshark php
)

# 每组（=每项目）尝试的崩溃数。
#
# ⚠ **为什么是 12 而不是 4**（W6 实测的选样偏差，第二个坑，与 N75 不同）：
#   `--sort fixed_first` 的次级键是 osv_id 升序 → **最老的崩溃排最前**，
#   而老崩溃恰恰最常缺 fuzz_target 元数据。实测这 24 个项目：
#     全量 1,103 条中无 fuzz_target 者 120 条 = 11%
#     但按 fixed_first 取**前 96 条**（=24 组 × limit 4）中无 target 者 **53 条 = 55%**
#   → limit=4 时过半预算花在 `unreproducible_no_target` 上（lcms 首轮 4 条里 1 条即如此）。
#   无 target 的记录**不触发构建**、成本近零，故放大 limit 是零风险解法；
#   limit=12 → 约 6.6 条可跑 × (钉版构建成功率 76.2% × 复现率 45.7% ≈ 35%) ≈ **2.3 条/项目**，
#   24 个项目 → 预期 **≈55 条新复现**、程序种类 14 → 最多 38。
#   （改 sort_key 让「可跑」优先是更彻底的解法，但 skip_reason 在 build_record 阶段才算出、
#     sort 时尚不可得，改动面大且影响所有调用方的 --limit 语义 → 本轮不做，仅记录。）
LIMIT_PER_GROUP="${LIMIT_PER_GROUP:-12}"

log() { printf '[%s] %s\n' "$(date '+%F %T')" "$*" | tee -a "$MAIN_LOG"; }

# ── [N77] worktree 自愈 ──────────────────────────────────────────────────────
# 根因（✅ W6 实测，代价是整整一轮 24 组全空转、0 复现）：
#   `build_orchestrator.py:763-766` 的 era 预 checkout
#       git -C $WT checkout <era_commit> -- projects/<project>
#   会**同时改工作区与索引**；流水线在钉版结束后调 `restore_projects()`
#   （`build_orchestrator.py:678`，用 `git restore --source=HEAD --staged --worktree`
#     + `clean -fdq` + projects/ 全域兜底）还原。
#   但**进程在 precheckout 与 restore 之间被中断**（kill / OOM / 超时 / docker rm -f）
#   → 还原不执行 → worktree 脏 → §1.7 H gate 的「②无未提交改动」判负
#   → **此后每一组都 ABORT、0 次构建**，而 run_repro 仍以 rc=0 正常结束、
#     每组只花 4–90 秒，看上去像"跑完了"。
#   SIGKILL 无法用 try/finally 防住，故在驱动层每组开始前自愈。
# ⚠ 只还原 `projects/`：era checkout 的作用域就是它（见 678-702 行的兜底扫描），
#   不动其它路径，避免掩盖真正需要人工看的改动。
WT="${WT:-/root/gyx/oss-fuzz-repro}"
WT_HEAD="${WT_HEAD:-07522dc0e}"

heal_worktree() {
  local dirty
  dirty=$(git -C "$WT" status --porcelain -- projects 2>/dev/null | wc -l)
  if [ "$dirty" -gt 0 ]; then
    log "  ⚠ [N77] worktree 脏（projects/ 下 $dirty 项，era precheckout 未还原）→ 自愈"
    git -C "$WT" status --porcelain -- projects 2>/dev/null | head -4 | while read -r l; do
      log "      $l"
    done
    git -C "$WT" restore --source=HEAD --staged --worktree -- projects >/dev/null 2>&1
    git -C "$WT" clean -fdq -- projects >/dev/null 2>&1
    dirty=$(git -C "$WT" status --porcelain -- projects 2>/dev/null | wc -l)
    if [ "$dirty" -eq 0 ]; then
      log "      ✅ 已还原（projects/ 干净）"
    else
      log "      ❌ 还原后仍有 $dirty 项 → **停止整轮**（gate 会持续拦截，继续跑只是空转）"
      return 1
    fi
  fi
  # HEAD / 分支漂移检查：不是自愈能解决的，必须停
  local head
  head=$(git -C "$WT" rev-parse --short HEAD 2>/dev/null)
  if [ "$head" != "$WT_HEAD" ]; then
    log "  ❌ worktree HEAD=$head ≠ 约定基线 $WT_HEAD → 停止整轮（不擅自 reset）"
    return 1
  fi
  return 0
}

log "════════════════════════════════════════════════════════════"
log "后台复现启动  run_tag=$RUN_TAG"
log "  组数=${#PROJ_LIST[@]}  每组 limit=$LIMIT_PER_GROUP"
log "  日志目录=$LOG_DIR"
log "  磁盘可用=$(df -h / | awk 'NR==2{print $4}')  水位线: post=10 mid=8 floor=5 min=4"
log "════════════════════════════════════════════════════════════"

i=0
empty_streak=0          # [N77] 连续「0 次构建」的组数，达 4 组即判定系统性问题并停轮
for g in "${PROJ_LIST[@]}"; do
  i=$((i+1))
  free_gb=$(df --output=avail -BG / | tail -1 | tr -dc '0-9')
  log ""
  log "▶ 组 $i/${#PROJ_LIST[@]}: $g   （磁盘可用 ${free_gb}G）"

  if [ "$free_gb" -lt 5 ]; then
    log "  ⚠ 磁盘可用 ${free_gb}G < 5G，跳过本组（避免触发 N64 硬底线僵死）"
    continue
  fi

  # [N77] 每组开始前自愈 worktree；治不好就停整轮（继续跑必然全被 gate 拦）
  if ! heal_worktree; then
    log "  ■ 整轮提前终止于第 $i 组（worktree 无法自愈）"
    break
  fi

  rid="${RUN_TAG}-g$(printf '%02d' "$i")"
  start=$(date +%s)

  timeout 21600 python3 run_repro.py \
      --projects "$g" \
      --limit "$LIMIT_PER_GROUP" \
      --sort fixed_first \
      --stop-frac 0 \
      --post-clean \
      --post-clean-free-gb 10 \
      --mid-clean-free-gb 8 \
      --disk-hard-floor-gb 5 \
      --min-free-gb 4 \
      --run-id "$rid" \
      >"$LOG_DIR/g$(printf '%02d' "$i")_${g//,/+}.log" 2>&1
  rc=$?

  el=$(( $(date +%s) - start ))
  log "  ← 组 $i 结束 rc=$rc 耗时 $((el/60))分$((el%60))秒"

  # ── [N77] 空转探测 ────────────────────────────────────────────────────────
  # 为什么必须有：✅ W6 实测第一轮 24 组**全部**被 gate 拦截、0 次构建、0 复现，
  # 但 run_repro 每组都 rc=0 正常退出、整轮 16 分钟"跑完"，MAIN.log 里只有
  # 「本轮记录 12 条 → 复现 0 条」这种看起来像"项目不行"的行 ——
  # 只有人工翻组内日志才发现是 `❌ gate 未通过 → ABORT`。
  # 系统性阻塞必须**立刻停并喊出来**，不能连跑 24 组。
  glog="$LOG_DIR/g$(printf '%02d' "$i")_${g//,/+}.log"
  n_gate=$(grep -c "gate 未通过" "$glog" 2>/dev/null || echo 0)
  n_build=$(grep -cE "^▶ ② 建第" "$glog" 2>/dev/null || echo 0)
  if [ "${n_gate:-0}" -gt 0 ]; then
    log "  ❌ [N77] 本组 gate 拦截 ${n_gate} 次（尝试建格 ${n_build} 次）→ **系统性阻塞**"
    log "     常见根因：worktree 脏（era precheckout 未还原）、镜像 dc-injected 残留、"
    log "     HEAD 漂移。已写 BLOCKED.md；下一组开头会尝试自愈，但本轮先停以免空转。"
    grep -m3 -E "\[❌\]|→ 已写|BLOCKED" "$glog" 2>/dev/null | cut -c1-120 | while read -r l; do
      log "       $l"
    done
    log "  ■ 整轮提前终止于第 $i/${#PROJ_LIST[@]} 组（gate 系统性拦截）"
    break
  fi
  if [ "${n_build:-0}" -eq 0 ]; then
    empty_streak=$((empty_streak + 1))
    log "  ⚠ 本组 0 次构建尝试（连续 ${empty_streak} 组）—— 选样可能全被 skip 或计划为空"
    if [ "$empty_streak" -ge 4 ]; then
      log "  ❌ 连续 ${empty_streak} 组 0 构建 → 判定系统性问题，停整轮（不做无意义空转）"
      log "  ■ 整轮提前终止于第 $i/${#PROJ_LIST[@]} 组"
      break
    fi
  else
    empty_streak=0
  fi

  # 本轮战果：从账本取该 run_id 的最新记录
  python3 - "$rid" "$g" <<'PY' 2>>"$MAIN_LOG" | tee -a "$MAIN_LOG"
import json, sys, collections
rid, grp = sys.argv[1], sys.argv[2]
latest = {}
try:
    for l in open('repro_dataset.jsonl', encoding='utf-8'):
        try: r = json.loads(l)
        except Exception: continue
        if r.get('run_id') == rid and r.get('osv_id'):
            latest[r['osv_id']] = r
except FileNotFoundError:
    print('  (账本不存在)'); sys.exit()
if not latest:
    print(f'  本轮无记录落盘（run_id={rid}）'); sys.exit()
rep = sum(1 for r in latest.values() if r.get('reproduced_any'))
tiers = collections.Counter(r.get('verification_tier') for r in latest.values() if r.get('reproduced_any'))
bs = collections.Counter(r.get('build_status') for r in latest.values())
pj = collections.Counter(r['project'] for r in latest.values() if r.get('reproduced_any'))
print(f'  本轮记录 {len(latest)} 条 → 复现 {rep} 条  tier={dict(tiers)}')
print(f'  build_status={dict(bs)}')
if pj: print(f'  ✅ 新复现项目: {dict(pj)}')
PY
done

log ""
log "════════════════════════════════════════════════════════════"
log "全部 ${#PROJ_LIST[@]} 组跑完  磁盘可用=$(df -h / | awk 'NR==2{print $4}')"
python3 - <<'PY' 2>&1 | tee -a "$MAIN_LOG"
import json, collections
latest = {}
for l in open('repro_dataset.jsonl', encoding='utf-8'):
    try: r = json.loads(l)
    except Exception: continue
    if r.get('osv_id'): latest[r['osv_id']] = r
V = {o for o, r in latest.items() if r.get('reproduced_any')}
pj = collections.Counter(latest[o]['project'] for o in V)
print(f'  累计: 复现 {len(V)} 条 / {len(pj)} 个项目')
print(f'  项目明细: {dict(pj.most_common())}')
PY
log "════════════════════════════════════════════════════════════"

# ─────────────────────────────────────────────────────────────────────────────
# 附：repo_url 可解析性的复算方法（✅ W6 实测用此法，勿凭主机名推断）
#
#   cd reproduce_crash && python3 - <<'PY'
#   import json, sys; sys.path.insert(0,'.')
#   import build_orchestrator as B
#   rows=[json.loads(l) for l in open('/tmp/opencode/mb_all2.jsonl')]   # manifest_builder 全量产出
#   seen={}
#   for r in rows:
#       p=r['project']
#       if p not in seen and r.get('fixed_commit') and r.get('repo_url'): seen[p]=r
#   for p,r in sorted(seen.items()):
#       m=B.resolve_commit_meta(r['repo_url'], f"{r['fixed_commit']}~1") or {}
#       print(f"{p:<14} {r['repo_url'][:44]:<46} {m.get('sha') or m.get('error')}")
#   PY
#
# 先决条件：/tmp/opencode/mb_all2.jsonl 由
#   python3 manifest_builder.py --projects <24个> --languages c,c++ --sort fixed_first \
#       --no-regression --out /tmp/opencode/mb_all2.jsonl --build-groups /tmp/opencode/mb_all2.json
# 生成。
# ─────────────────────────────────────────────────────────────────────────────

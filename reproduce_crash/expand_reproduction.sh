#!/usr/bin/env bash
# ─────────────────────────────────────────────────────────────────────────────
# 复现扩面驱动：**深度优先**（把已验证可构建的项目榨干），目标 234 → ~350 条
#
# 为什么是深度优先而不是继续攻新项目（✅ W6 实测）：
#   已复现的 16 个项目在源数据集里共 464 条，其中 **320 条已进账本、234 条复现**，
#   → **还有 144 条从未尝试**。按各项目**已实现的复现率**折算，预期可再拿 **≈107 条**，
#   几乎覆盖 +116 的目标；而这些项目的构建配置**已经验证可行**，
#   比攻新项目便宜得多（上一轮 21 个新项目 × 12 条 = 252 次尝试只出 13 条，产出率 5%）。
#
#   余量分布（源数据 − 已进账本）：
#     libredwg 68（复现率 75%）  assimp 32（50%，但 n=2 样本极小）
#     yara     20（100%，n=4）    unicorn 19（83%，⚠ 单归档 4.6G）
#     libtsm 3 / c-blosc2 1 / jq 1 / 其余 0
#
# 两个放大器：
#   ① **N77 修复**（可跑者优先排序）：上一轮 yara 是 4 条尝试→4 条复现，
#      但那时 `--limit 12` 里只有 4 条可跑；修复后同样 limit 能拿到 12 条可跑。
#   ② **N75 修复**（`--sort fixed_first` 语义反转）：预期产出 0.4→2.7 条/6 条（≈7×）。
#
# 沿用 add_new_projects.sh 的两道护栏（都是踩过坑才加的）：
#   [N77] 每组开始前自愈 worktree —— era precheckout 被中断会留下脏索引，
#         导致此后每组都被 §1.7 H gate 拦下、0 次构建，而 run_repro 仍 rc=0"正常结束"
#   [N77] 空转探测 —— gate 拦截 / 连续 0 构建 → 立刻停轮喊出来，不连跑几十组
# ─────────────────────────────────────────────────────────────────────────────
set -uo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$HERE" || exit 1

RUN_TAG="${RUN_TAG:-expand-$(date +%Y%m%d-%H%M)}"
LOG_DIR="$HERE/artifacts/runs/_bg_$RUN_TAG"
mkdir -p "$LOG_DIR"
MAIN_LOG="$LOG_DIR/MAIN.log"
WT="${WT:-/root/gyx/oss-fuzz-repro}"
WT_HEAD="${WT_HEAD:-07522dc0e}"

# 项目:limit 对。limit 取「余量 + 少量冗余」，让 N77 修复后的可跑者优先排序
# 有足够名额把该项目的可跑崩溃都排进来。
# ⚠ unicorn 放最后：单归档实测 4.6G，最易击穿磁盘硬底线（N64 实测缺阀时
#   可用空间会掉到 68KB / 100% 满、进程僵死）。
TARGETS=(
  "libredwg:70"
  "yara:24"
  "assimp:34"
  "libtsm:6"
  "c-blosc2:6"
  "jq:6"
  "unicorn:20"
)

log() { printf '[%s] %s\n' "$(date '+%F %T')" "$*" | tee -a "$MAIN_LOG"; }

heal_worktree() {
  local dirty
  dirty=$(git -C "$WT" status --porcelain -- projects 2>/dev/null | wc -l)
  dirty=${dirty:-0}
  if [ "$dirty" -gt 0 ]; then
    log "  ⚠ [N77] worktree 脏（projects/ 下 $dirty 项，era precheckout 未还原）→ 自愈"
    git -C "$WT" status --porcelain -- projects 2>/dev/null | head -4 | while read -r l; do
      log "      $l"
    done
    git -C "$WT" restore --source=HEAD --staged --worktree -- projects >/dev/null 2>&1
    git -C "$WT" clean -fdq -- projects >/dev/null 2>&1
    dirty=$(git -C "$WT" status --porcelain -- projects 2>/dev/null | wc -l)
    dirty=${dirty:-0}
    if [ "$dirty" -eq 0 ]; then
      log "      ✅ 已还原（projects/ 干净）"
    else
      log "      ❌ 还原后仍有 $dirty 项 → 停止整轮"
      return 1
    fi
  fi
  local head
  head=$(git -C "$WT" rev-parse --short HEAD 2>/dev/null)
  if [ "$head" != "$WT_HEAD" ]; then
    log "  ❌ worktree HEAD=$head ≠ 基线 $WT_HEAD → 停止整轮（不擅自 reset）"
    return 1
  fi
  return 0
}

# 账本快照（用于计算本轮净增）
snapshot() {
  python3 - <<'PY'
import json
lat = {}
for l in open('repro_dataset.jsonl', encoding='utf-8'):
    try: r = json.loads(l)
    except Exception: continue
    if r.get('osv_id'): lat[r['osv_id']] = r
print(sum(1 for r in lat.values() if r.get('reproduced_any')))
PY
}

N0=$(snapshot)
log "════════════════════════════════════════════════════════════"
log "复现扩面（深度优先）启动  run_tag=$RUN_TAG"
log "  起点：已复现 $N0 条   目标：~350 条（需 +$((350 - N0))）"
log "  目标项目 ${#TARGETS[@]} 个：${TARGETS[*]}"
log "  日志目录=$LOG_DIR"
log "  磁盘可用=$(df -h / | awk 'NR==2{print $4}')  水位线: post=10 mid=8 floor=6 min=5"
log "════════════════════════════════════════════════════════════"

i=0
empty_streak=0
for t in "${TARGETS[@]}"; do
  i=$((i+1))
  g="${t%%:*}"
  lim="${t##*:}"

  cur=$(snapshot)
  if [ "$cur" -ge 350 ]; then
    log ""
    log "■ 已达目标 $cur ≥ 350 → 提前收工（第 $i 组 $g 不再跑）"
    break
  fi

  free_gb=$(df --output=avail -BG / | tail -1 | tr -dc '0-9')
  free_gb=${free_gb:-0}
  log ""
  log "▶ 组 $i/${#TARGETS[@]}: $g  limit=$lim   （磁盘 ${free_gb}G，累计已复现 $cur）"

  if [ "$free_gb" -lt 6 ]; then
    log "  ⚠ 磁盘 ${free_gb}G < 6G，跳过本组（unicorn 单归档 4.6G，硬底线必须留足）"
    continue
  fi
  if ! heal_worktree; then
    log "  ■ 整轮终止于第 $i 组（worktree 无法自愈）"
    break
  fi

  rid="${RUN_TAG}-g$(printf '%02d' "$i")-$g"
  start=$(date +%s)
  glog="$LOG_DIR/g$(printf '%02d' "$i")_${g}.log"

  timeout 43200 python3 run_repro.py \
      --projects "$g" \
      --limit "$lim" \
      --sort fixed_first \
      --stop-frac 0 \
      --post-clean \
      --post-clean-free-gb 10 \
      --mid-clean-free-gb 8 \
      --disk-hard-floor-gb 6 \
      --min-free-gb 5 \
      --run-id "$rid" \
      >"$glog" 2>&1
  rc=$?
  el=$(( $(date +%s) - start ))
  after=$(snapshot)
  log "  ← 组 $i 结束 rc=$rc 耗时 $((el/60))分$((el%60))秒  复现 $cur → $after（净增 $((after - cur))）"

  # ── 空转探测（✅ 上一轮 9 组全被 gate 拦、每组仍 rc=0，只有翻组内日志才发现）──
  # ⚠ `grep -c` 无匹配时**退出码非 0 但仍会打印 0**，故不能用 `|| echo 0`
  #   （那会得到两行 "0"，令 `[ ... -gt 0 ]` 报 integer expression expected 而静默失效）。
  n_gate=$(grep -c "gate 未通过" "$glog" 2>/dev/null); n_gate=${n_gate:-0}
  n_build=$(grep -cE "^▶ ② 建第" "$glog" 2>/dev/null); n_build=${n_build:-0}
  n_floor=$(grep -c "磁盘硬底线" "$glog" 2>/dev/null); n_floor=${n_floor:-0}
  if [ "$n_gate" -gt 0 ]; then
    log "  ❌ [N77] gate 拦截 ${n_gate} 次（尝试建格 ${n_build} 次）→ 系统性阻塞，停整轮"
    grep -m3 -E "\[❌\]|→ 已写|BLOCKED" "$glog" 2>/dev/null | cut -c1-120 | while read -r l; do
      log "       $l"
    done
    break
  fi
  if [ "$n_floor" -gt 0 ]; then
    log "  ⚠ 触发磁盘硬底线 ${n_floor} 次 → 后续组大概率同样受限"
  fi
  if [ "$n_build" -eq 0 ]; then
    empty_streak=$((empty_streak + 1))
    log "  ⚠ 本组 0 次构建尝试（连续 ${empty_streak} 组）"
    if [ "$empty_streak" -ge 3 ]; then
      log "  ❌ 连续 ${empty_streak} 组 0 构建 → 判定系统性问题，停整轮"
      break
    fi
  else
    empty_streak=0
  fi
done

log ""
log "════════════════════════════════════════════════════════════"
N1=$(snapshot)
log "扩面结束：$N0 → $N1 条（净增 $((N1 - N0))，距 350 还差 $((350 - N1))）"
log "磁盘可用=$(df -h / | awk 'NR==2{print $4}')"
python3 - <<'PY' 2>&1 | tee -a "$MAIN_LOG"
import json, collections
lat = {}
for l in open('repro_dataset.jsonl', encoding='utf-8'):
    try: r = json.loads(l)
    except Exception: continue
    if r.get('osv_id'): lat[r['osv_id']] = r
V = {o for o, r in lat.items() if r.get('reproduced_any')}
pj = collections.Counter(lat[o]['project'] for o in V)
ti = collections.Counter(lat[o].get('verification_tier') for o in V)
ct = collections.Counter(lat[o].get('crash_type_norm') for o in V)
print(f'  复现 {len(V)} 条 / {len(pj)} 个项目')
print(f'  tier 分布: {dict(ti.most_common())}')
print(f'  项目明细: {dict(pj.most_common())}')
print(f'  崩溃类型前 8: {dict(ct.most_common(8))}')
PY
log "════════════════════════════════════════════════════════════"

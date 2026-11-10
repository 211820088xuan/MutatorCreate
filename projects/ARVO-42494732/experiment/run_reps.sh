#!/bin/bash
# 重复对照：**所有 run 同时启动**（16 核 / 10 个 run，各占一个核）。
# 这样两臂共享同一时间窗，时间漂移对它们影响一致；配对比较更干净。
#
# 2026-11-02 修正：原来是 -seed=1 硬编码，导致 5 个 rep 是**同一个确定性 run 的 5 次重放**
# （实测 reps_pathB 的 675 个崩溃文件只有 136 个唯一 sha1，134 个出现在全部 5 个 rep）。
# 现改为逐 rep 变 seed：-seed=$((SEED_BASE + r))，同 rep 的两臂共用同一 seed（保持配对）。
set -u
DUR="${1:-150}"
REPS="${2:-5}"
SEED_BASE="${SEED_BASE:-0}"
# RSS_MB：1.5h 那轮 6 并行下 -rss_limit_mb=1200 导致 3/6 run 大量 OOM
# （88/219/70 次），污染对比。24h 10 并行改为默认 2000（10×2G=20G < 24G）。
RSS_MB="${RSS_MB:-2000}"
EXP=/exp/experiment
BIN=$EXP/llvmfuzz
SEEDS=/exp/seeds
ROOT=$EXP/reps
# 2026-11-07（R24）：**不要静默 rm -rf**。
# `$EXP` 是宿主机 `projects/ARVO-42494732` 的挂载点（docker inspect 可证），
# 所以 `$ROOT` = 宿主机的 `v2/experiment/reps` —— 上一次跑完忘了 `mv` 走，
# 这一次就会把它**无声地删掉**。
# 历史快照放在 `experiment/reps_*`（名字带下划线），和这里的 scratch 名 `reps` 不同。
# 但如果有人把快照 mv 成 `reps`，或者忘了 mv，就会永久丢数据。
if [ -d "$ROOT" ] && [ -n "$(ls -A "$ROOT" 2>/dev/null)" ]; then
  echo "拒绝执行：$ROOT 存在且非空。" >&2
  echo "  先把它 mv 走再跑，例如：mv $ROOT ${ROOT}_$(date +%Y%m%d_%H%M)" >&2
  echo "  现存的历史快照：" >&2
  ls -d ${EXP}/reps_* 2>/dev/null | sed 's/^/    /' >&2
  exit 1
fi
mkdir -p "$ROOT"

pids=()
for r in $(seq 1 "$REPS"); do
  for arm in default custom; do
    OUT=$ROOT/rep$(printf %02d "$r")/$arm
    mkdir -p "$OUT/corpus" "$OUT/crash"
    cp "$SEEDS"/*.dxf "$OUT/corpus"/ 2>/dev/null || true
    cp "$SEEDS"/*.dwg "$OUT/corpus"/ 2>/dev/null || true
    [ "$arm" = default ] && MO=1 || MO=0
    (
      LIBREDWG_MUTATOR_OFF="$MO" ASAN_OPTIONS=detect_leaks=0 LSAN_OPTIONS=detect_leaks=0 \
        "$BIN" -max_total_time="$DUR" -fork=1 -detect_leaks=0 -seed=$((SEED_BASE + r)) \
          -timeout=25 -rss_limit_mb=${RSS_MB} \
          -ignore_crashes=1 -ignore_ooms=1 -ignore_timeouts=1 \
          -print_final_stats=1 -artifact_prefix="$OUT/crash/" \
          "$OUT/corpus/" > "$OUT/run.log" 2>&1
    ) &
    pids+=($!)
  done
done
echo "[$(date '+%T')] 已启动 ${#pids[@]} 个 run，每个 ${DUR}s"

# 磁盘看门狗：低于 MIN_FREE_GB 时停掉全部 run，避免 24h 跑到中途写满磁盘
(
  while :; do
    alive=0
    for p in "${pids[@]}"; do kill -0 "$p" 2>/dev/null && alive=1; done
    [ "$alive" -eq 0 ] && break
    free=$(df -BG --output=avail / | tail -1 | tr -dc '0-9')
    if [ "${free:-0}" -lt "${MIN_FREE_GB:-3}" ]; then
      echo "[watchdog $(date '+%T')] 磁盘仅剩 ${free}G，停止全部 run"
      touch "$EXP/.disk_low"
      for p in "${pids[@]}"; do kill -TERM "$p" 2>/dev/null; done
      break
    fi
    sleep 120
  done
) &
WD=$!
wait
kill "$WD" 2>/dev/null
echo "[$(date '+%T')] 全部完成"

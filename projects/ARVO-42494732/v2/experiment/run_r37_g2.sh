#!/bin/bash
# R37 组 2 · 真实性组：**整个 seeds/ 文件夹**，3 reps，固定 -runs（两臂 exec 数相同）
set -u
RUNS="${1:-120000}"; REPS="${2:-3}"; SEED_BASE="${SEED_BASE:-100}"
EXP=/exp/v2/experiment; ROOT=$EXP/reps_r37_g2
A=$EXP/llvmfuzz; B=$EXP/llvmfuzz_multi_r37
if [ -d "$ROOT" ] && [ -n "$(ls -A "$ROOT" 2>/dev/null)" ]; then echo "拒绝：$ROOT 非空" >&2; exit 1; fi
mkdir -p "$ROOT"
pids=()
for r in $(seq 1 "$REPS"); do
  for arm in A B; do
    OUT=$ROOT/rep$(printf %02d "$r")/$arm
    mkdir -p "$OUT/corpus" "$OUT/crash"
    # corpus 隔离：每个 rep 从干净副本开始
    cp /exp/seeds/* "$OUT/corpus/"
    if [ "$arm" = "A" ]; then BIN=$A; MO=1; else BIN=$B; MO=0; fi
    (
      LIBREDWG_MUTATOR_OFF="$MO" ASAN_OPTIONS=detect_leaks=0 LSAN_OPTIONS=detect_leaks=0 \
        "$BIN" -runs="$RUNS" -fork=1 -detect_leaks=0 -seed=$((SEED_BASE + r)) \
          -timeout=25 -rss_limit_mb=1200 -ignore_crashes=1 -ignore_ooms=1 -ignore_timeouts=1 \
          -print_final_stats=1 -artifact_prefix="$OUT/crash/" "$OUT/corpus/" > "$OUT/run.log" 2>&1
    ) &
    pids+=($!)
  done
done
echo "[$(date '+%T')] 已启动 ${#pids[@]} 个 run，每个 ${RUNS} runs"
wait
echo "[$(date '+%T')] 全部完成"

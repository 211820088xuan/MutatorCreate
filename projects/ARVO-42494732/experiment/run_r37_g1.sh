#!/bin/bash
# R37 组 1 · 可比性组：**单个 Constraints.dxf**，5 reps × 300s，对齐 reps_r9_final
set -u
DUR="${1:-300}"; REPS="${2:-5}"; SEED_BASE="${SEED_BASE:-0}"
EXP=/exp/v2/experiment; ROOT=$EXP/reps_r37_g1
A=$EXP/llvmfuzz              # A 臂：默认变异器（LIBREDWG_MUTATOR_OFF=1）
B=$EXP/llvmfuzz_multi_r37    # B 臂：多策略算子
if [ -d "$ROOT" ] && [ -n "$(ls -A "$ROOT" 2>/dev/null)" ]; then echo "拒绝：$ROOT 非空" >&2; exit 1; fi
mkdir -p "$ROOT"
pids=()
for r in $(seq 1 "$REPS"); do
  for arm in A B; do
    OUT=$ROOT/rep$(printf %02d "$r")/$arm
    mkdir -p "$OUT/corpus" "$OUT/crash"
    cp /exp/seeds/Constraints.dxf "$OUT/corpus/only.dxf"
    if [ "$arm" = "A" ]; then BIN=$A; MO=1; else BIN=$B; MO=0; fi
    (
      LIBREDWG_MUTATOR_OFF="$MO" ASAN_OPTIONS=detect_leaks=0 LSAN_OPTIONS=detect_leaks=0 \
        "$BIN" -max_total_time="$DUR" -fork=1 -detect_leaks=0 -seed=$((SEED_BASE + r)) \
          -timeout=25 -rss_limit_mb=1200 -ignore_crashes=1 -ignore_ooms=1 -ignore_timeouts=1 \
          -print_final_stats=1 -artifact_prefix="$OUT/crash/" "$OUT/corpus/" > "$OUT/run.log" 2>&1
    ) &
    pids+=($!)
  done
done
echo "[$(date '+%T')] 已启动 ${#pids[@]} 个 run，每个 ${DUR}s"
wait
echo "[$(date '+%T')] 全部完成"

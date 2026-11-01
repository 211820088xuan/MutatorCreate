#!/bin/bash
# sweep.sh —— 自定义占比扫描（剂量-反应实验）
# usage: sweep.sh "0,20,40,60,80,100" [reps] [duration_seconds]
#   p0   = 纯默认变异（基线）
#   p20  = 20% 自定义 + 80% 默认
#   p100 = 纯自定义
set -u
PCTS="${1:-20}"
REPS="${2:-2}"
DUR="${3:-900}"

BASE=/exp/fuzz_exp
BIN=/exp/fuzz_exp/llvmfuzz
SEED=/exp/seeds
PIPE=/exp/fuzz_exp/pipeline

echo "=== 配置 ==="
echo "  占比: $PCTS  reps=$REPS  duration=${DUR}s"
echo -n "  二进制 sancov: "; nm "$BIN" | grep -c sancov
echo -n "  种子数: "; ls "$SEED"/*.dxf 2>/dev/null | wc -l

for pct in ${PCTS//,/ }; do
  for i in $(seq 1 "$REPS"); do
    d="$BASE/p${pct}_${i}"
    rm -rf "$d"; mkdir -p "$d/corpus" "$d/crash"
    cp "$SEED"/*.dxf "$d/corpus/" 2>/dev/null
    echo "[$(date '+%T')] 启动 p${pct}_${i}"
    (
      ASAN_OPTIONS=detect_leaks=0 LSAN_OPTIONS=detect_leaks=0 \
      LIBREDWG_CUSTOM_PCT="$pct" "$BIN" \
        -max_total_time="$DUR" -fork=1 -detect_leaks=0 -seed=1 \
        -timeout=25 -rss_limit_mb=2560 \
        -ignore_crashes=1 -ignore_ooms=1 -ignore_timeouts=1 \
        -print_final_stats=1 -artifact_prefix="$d/crash/" \
        "$d/corpus/" > "$d/run.log" 2>&1
    ) &
  done
done
wait
echo "[$(date '+%T')] 全部 fuzz 结束"

echo "=== 重放分析 ==="
for pct in ${PCTS//,/ }; do
  for i in $(seq 1 "$REPS"); do
    python3 "$PIPE/analyze_run.py" "p${pct}" "$i"
  done
done

echo "=== 汇总 ==="
python3 "$PIPE/sweep_summary.py" "$PCTS" "$REPS"

#!/bin/bash
# run_all.sh —— 全流程：N 次重复 × 2 模式并行 fuzz → 重放分析 → 汇总
# usage: run_all.sh [reps] [duration_seconds]
#   reps     默认 5（default_1..5 / custom_1..5）
#   duration 默认 1200 秒（20 分钟）
set -u
REPS="${1:-5}"
DUR="${2:-1200}"

BASE=/exp/fuzz_exp
PIPE=/exp/fuzz_exp/pipeline

rm -rf "$BASE"/default_* "$BASE"/custom_* "$BASE"/replay "$BASE"/summary.md 2>/dev/null
mkdir -p "$BASE"

echo "=== 检查二进制 ==="
[ -x /exp/fuzz_exp/llvmfuzz ] || { echo "缺少 /exp/fuzz_exp/llvmfuzz"; exit 1; }
echo -n "  sancov 符号: "; nm /exp/fuzz_exp/llvmfuzz | grep -c sancov
echo -n "  corpus_min:  "; ls /exp/corpus_min/*.dxf 2>/dev/null | wc -l
echo "  reps=$REPS  duration=${DUR}s"

echo ""
echo "=== 启动 $((REPS*2)) 个 fuzz（并行）==="
for mode in default custom; do
  for i in $(seq 1 "$REPS"); do
    bash "$PIPE/run_one.sh" "$mode" "$i" "$DUR" &
  done
done
wait
echo "=== 全部 fuzz 结束 ==="

echo ""
echo "=== 重放分析 ==="
for mode in default custom; do
  for i in $(seq 1 "$REPS"); do
    python3 "$PIPE/analyze_run.py" "$mode" "$i"
  done
done

echo ""
echo "=== 汇总 ==="
python3 "$PIPE/summarize.py" "$REPS"

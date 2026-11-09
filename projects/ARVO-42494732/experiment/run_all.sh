#!/bin/bash
# 对比实验编排（全并行版）：3 轮 × 2 模式 = 6 个实例**同时**启动、同时结束
#
# 为什么全并行：
#   1) 6 组在同一时刻、同一台机器上跑，资源条件完全一致 → 最公平
#   2) 总耗时 = 1 轮时长（30 分钟），而不是 6 × 30 分钟
#
# 资源核算（实测）：16 核 / 31 GB 内存；每个 -fork=1 实例约占 1 核、400 MB
#   → 6 实例 ≈ 6 核 / 2.4 GB，余量充足
#
# 用法（容器内）: bash /exp/run_all.sh [每组秒数] [重复轮数]
set -u
SECS=${1:-1800}
REPS=${2:-3}
EXP=/exp
LOG=$EXP/fuzz_exp/run_all.log
mkdir -p "$EXP/fuzz_exp"

: > "$LOG"
{
  echo "=== 开始 $(date -Iseconds)   每组 ${SECS}s × ${REPS} 轮 × 2 模式（6 实例全并行）==="
  echo "=== 二进制: $(ls -l "$EXP/fuzz_exp/llvmfuzz" | awk '{print $5" B"}')"
  echo "=== 可用 CPU: $(nproc)   内存: $(free -g | awk '/^Mem:/{print $2" GB"}')"
} | tee -a "$LOG"

PIDS=()
NAMES=()
for rep in $(seq 1 "$REPS"); do
  for mode in default custom; do
    mkdir -p "$EXP/fuzz_exp/${mode}_${rep}"
    bash "$EXP/run_one.sh" "$mode" "$rep" "$SECS" \
        > "$EXP/fuzz_exp/${mode}_${rep}/run_one.out" 2>&1 &
    PIDS+=($!)
    NAMES+=("${mode}_${rep}")
    echo "  启动 ${mode}_${rep}  pid=$!" | tee -a "$LOG"
  done
done

echo "" | tee -a "$LOG"
echo "=== 全部启动完成，等待 $((${#PIDS[@]})) 个实例 $(date -Iseconds) ===" | tee -a "$LOG"

fail=0
for i in "${!PIDS[@]}"; do
  wait "${PIDS[$i]}" || { rc=$?; echo "  ${NAMES[$i]} 结束 rc=$rc" | tee -a "$LOG"; fail=$((fail+1)); }
done

echo "" | tee -a "$LOG"
echo "=== 全部完成 $(date -Iseconds)   异常 ${fail} 个 ===" | tee -a "$LOG"

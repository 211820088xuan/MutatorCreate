#!/bin/bash
# 24h × 5 rep × 2 臂实验的收尾：快照 → pipeline 分析
set -u
EXP=/exp/experiment
ROOT=$EXP/reps
SNAP=$EXP/reps_24h_5rep

echo "[$(date '+%T')] 等待 llvmfuzz 全部退出..."
while pgrep -x llvmfuzz >/dev/null 2>&1; do sleep 120; done
sleep 20

if [ -d "$ROOT" ]; then
  if [ -d "$SNAP" ]; then
    SNAP="${SNAP}_$(date +%Y%m%d_%H%M)"
  fi
  mv "$ROOT" "$SNAP"
  echo "[$(date '+%T')] 快照: $SNAP"
else
  echo "[$(date '+%T')] 没有找到 $ROOT"
  exit 1
fi

echo "[$(date '+%T')] 开始分析..."
python3 "$EXP/analyze_reps.py" "$SNAP" --binary "$EXP/llvmfuzz" > "$SNAP/ANALYSIS.md" 2>&1
rc=$?
echo "[$(date '+%T')] 分析退出码 $rc"
[ $rc -eq 0 ] && touch "$SNAP/.analysis_done"
echo "[$(date '+%T')] 完成"

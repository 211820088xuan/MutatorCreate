#!/bin/bash
# 等 run_reps.sh 的 6 个 run 结束后：快照 → 用 pipeline 的 analyze_reps.py 分析
#
# 为什么需要它：run_reps.sh 只做 wait，不会自动 mv 快照；
# 而 HANDOFF 纪律 1 要求"跑完立刻 mv reps reps_<tag>"（否则下次 rm -rf）。
set -u
EXP=/exp/experiment
ROOT=$EXP/reps
SNAP=$EXP/reps_attached_1p5h

echo "[$(date '+%T')] 等待 llvmfuzz 全部退出..."
while pgrep -x llvmfuzz >/dev/null 2>&1; do sleep 60; done
sleep 15

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

echo "[$(date '+%T')] 开始分析（逐 rep + 率比 + CI + 崩溃点去重）..."
python3 "$EXP/analyze_reps.py" "$SNAP" --binary "$EXP/llvmfuzz" > "$SNAP/ANALYSIS.md" 2>&1
rc=$?
echo "[$(date '+%T')] 分析退出码 $rc"
[ $rc -eq 0 ] && touch "$SNAP/.analysis_done"
echo "[$(date '+%T')] 完成"

#!/bin/bash
# s1_reproduce.sh —— 阶段1（漏洞复现）入口
#
# 为什么是一层包装而不是把脚本搬进来：
#   reproduce_crash/ 是一个自成一体的子项目——14 个脚本互相 import、
#   自带 state.json / artifacts/ / binaries/ 目录树，且路径全部基于
#   __file__。把它们搬进 pipeline/ 会让所有路径与 import 同时失效。
#   所以这里只做“切目录 + 转发”，实现保持原样。
#
# 用法：
#   bash s1_reproduce.sh --projects libredwg --limit 5 --stage1-only
#   bash s1_reproduce.sh --help                     # 透传 run_repro.py 的帮助
set -u
PIPE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TOP="$(dirname "$(dirname "$PIPE")")"
RC="$TOP/reproduce_crash"

if [ ! -f "$RC/run_repro.py" ]; then
  echo "找不到 $RC/run_repro.py"
  exit 1
fi

cd "$RC" || exit 1
echo "=== 阶段1 入口: $RC/run_repro.py"
exec python3 run_repro.py "$@"

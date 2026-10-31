#!/bin/bash
set -euo pipefail
source "$(dirname "$0")/../scripts/env.sh"
trap 'echo "流程已结束；按回车关闭窗口。"; read -r' EXIT
"$CONTROLLER_ROOT/scripts/setup_bridge.sh"
echo '请先在旧 Bridge 终端按 Control+C。此入口会继续你选择的原 Codex 会话。'
echo '原会话若仍由桌面 App 加载，需用 Command+Q 退出桌面 App 后运行此入口。'
"$CONTROLLER_ROOT/private/bridge-venv/bin/python" "$CONTROLLER_ROOT/scripts/run_native_cli.py" "$@"

#!/bin/bash
set -euo pipefail
source "$(dirname "$0")/../scripts/env.sh"
trap 'echo "按回车关闭"; read -r' EXIT
CONTROLLER_PROJECT="$(cd "$CONTROLLER_ROOT/../.." && pwd)"
python "$CONTROLLER_ROOT/scripts/install_hooks.py" --user --remove-project-copy "$CONTROLLER_PROJECT"
echo '请在 Codex 审阅并信任 Passport Hook，然后用 Command+Q 完全退出桌面应用并重新打开原聊天。'
echo '仅切换聊天不保证重载旧会话。保持 Bridge 运行，再发起新请求；无需刷机或重配 Wi-Fi。'

#!/bin/bash
set -euo pipefail
CONTROLLER_SCRIPT_ROOT="$(cd "$(dirname "$0")" && pwd)"
echo '先停止旧 Bridge；请用可传数据的 USB 线连接 AI Passport。'
echo '备份并更新声音固件后，选择原会话进入 CLI 实体审批模式。'
echo '需要用 Command+Q 完全退出桌面 App，释放原会话；无需重新配 Wi-Fi。'
exec "$CONTROLLER_SCRIPT_ROOT/更新固件保留配网.command" --native "$@"

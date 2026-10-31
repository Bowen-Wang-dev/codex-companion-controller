#!/bin/bash
set -euo pipefail
source "$(dirname "$0")/../scripts/env.sh"
trap 'echo "流程已结束；按回车关闭窗口。"; read -r' EXIT
python "$CONTROLLER_ROOT/scripts/preflight.py"
"$CONTROLLER_ROOT/scripts/setup_bridge.sh"
shopt -s nullglob
CONTROLLER_PORTS=(/dev/cu.usbmodem*)
if [[ ${#CONTROLLER_PORTS[@]} != 1 ]]; then echo '请用 USB 连接一台 AI Passport。'; exit 1; fi
python "$CONTROLLER_ROOT/bridge/account.py"
echo '备份需读取两次 8 MB：此设备之前每轮约 3 分钟。以下显示进度。'
python "$CONTROLLER_ROOT/scripts/flash.py" flash --port "${CONTROLLER_PORTS[0]}" --execute
sleep 2
python "$CONTROLLER_ROOT/scripts/pair_wifi.py"
"$CONTROLLER_ROOT/private/bridge-venv/bin/python" "$CONTROLLER_ROOT/bridge/service.py"

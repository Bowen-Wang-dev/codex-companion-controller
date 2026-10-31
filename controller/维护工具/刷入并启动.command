#!/bin/bash
set -euo pipefail
CONTROLLER_SCRIPT_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
source "$CONTROLLER_SCRIPT_ROOT/scripts/env.sh"
trap 'echo; echo "脚本已停止；可查看上方结果。按回车关闭。"; read -r' EXIT
python "$CONTROLLER_ROOT/scripts/preflight.py"
shopt -s nullglob
CONTROLLER_PORTS=(/dev/cu.usbmodem*)
if [[ ${#CONTROLLER_PORTS[@]} != 1 ]]; then
  echo '需要且只能连接一台 USB AI Passport。'; exit 1
fi
CONTROLLER_PORT="${CONTROLLER_PORTS[0]}"
echo '校验 Mac 上的 ChatGPT 账户（只读，不消费额度）…'
python "$CONTROLLER_ROOT/bridge/account.py"
echo '将双读验证 8 MB 备份，然后只更新 factory 应用；不擦除整片 Flash。'
python "$CONTROLLER_ROOT/scripts/flash.py" flash --port "$CONTROLLER_PORT" --execute
sleep 2
"$CONTROLLER_ROOT/scripts/setup_bridge.sh"
"$CONTROLLER_ROOT/private/bridge-venv/bin/python" "$CONTROLLER_ROOT/bridge/service.py" --port "$CONTROLLER_PORT"

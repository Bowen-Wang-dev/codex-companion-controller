#!/bin/bash
set -euo pipefail
source "$(dirname "$0")/../scripts/env.sh"
trap 'echo "流程已结束；按回车关闭窗口。"; read -r' EXIT
python "$CONTROLLER_ROOT/scripts/preflight.py"
shopt -s nullglob
CONTROLLER_PORTS=(/dev/cu.usbmodem*)
if [[ ${#CONTROLLER_PORTS[@]} != 1 ]]; then echo '请用数据线连接一台 AI Passport。'; exit 1; fi
if [[ "${1:-}" == "--native" ]]; then
 "$CONTROLLER_ROOT/scripts/setup_bridge.sh"
 echo '先检查真实官方 CLI 接口，尚未写入 Flash…'
 "$CONTROLLER_ROOT/private/bridge-venv/bin/python" "$CONTROLLER_ROOT/scripts/run_native_cli.py" --check
fi
echo '更新 V0.2.4：备份后只写应用，保留现有 Wi-Fi 配对、NVS、分区表和 bootloader。'
python "$CONTROLLER_ROOT/scripts/flash.py" flash --port "${CONTROLLER_PORTS[0]}" --execute
if [[ "${1:-}" == "--native" ]]; then
 shift
 "$CONTROLLER_ROOT/scripts/setup_bridge.sh"
 "$CONTROLLER_ROOT/private/bridge-venv/bin/python" "$CONTROLLER_ROOT/scripts/run_native_cli.py" "$@"
else
 "$CONTROLLER_ROOT/scripts/run_bridge.sh"
fi

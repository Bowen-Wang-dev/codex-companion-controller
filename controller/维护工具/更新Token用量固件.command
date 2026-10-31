#!/bin/bash
set -euo pipefail
source "$(dirname "$0")/../scripts/env.sh"
trap 'echo "流程已结束；按回车关闭窗口。"; read -r' EXIT
python "$CONTROLLER_ROOT/scripts/preflight.py"
shopt -s nullglob
CONTROLLER_PORTS=(/dev/cu.usbmodem*)
if [[ ${#CONTROLLER_PORTS[@]} != 1 ]]; then
 echo '请用数据线连接一台 AI Passport。当前步骤不会修改设备。'
 exit 1
fi
echo '更新固件 0.2.7：修复模型状态闪断，并支持 K/M/G/T/P Token 缩写。'
echo '先双读 8 MB Flash 备份，只更新 factory 应用；保留配网、NVS、分区表和 bootloader。'
echo '先停止本项目所有 Bridge，释放 USB 串口；不会影响其他项目。'
"$CONTROLLER_ROOT/private/bridge-venv/bin/python" "$CONTROLLER_ROOT/scripts/stop_all_bridges.py" || true
read -r -p '按回车开始备份和更新；按 Control-C 取消：'
python "$CONTROLLER_ROOT/scripts/flash.py" flash --port "${CONTROLLER_PORTS[0]}" --execute
echo
echo '固件已更新并校验。请在独立 Bridge 终端按 Control+C，再双击「仅启动桌面App桥接.command」。'

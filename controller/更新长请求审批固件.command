#!/bin/bash
set -euo pipefail
source "$(dirname "$0")/scripts/env.sh"
trap 'echo "流程已结束；按回车关闭窗口。"; read -r' EXIT
"$CONTROLLER_ROOT/scripts/setup_bridge.sh"
"$CONTROLLER_ROOT/private/bridge-venv/bin/python" - "$CONTROLLER_ROOT" <<'PY'
import os,sys
sys.path.insert(0,os.path.join(sys.argv[1],'bridge'))
from ipc_path import acquire_endpoint
try:
 lease=acquire_endpoint();lease.close()
except (OSError,RuntimeError) as error:
 sys.exit('旧 Bridge 仍在运行。请只在旧启动终端按 Control+C，然后重试。不要退出桌面 App。\n'+str(error))
PY
shopt -s nullglob
CONTROLLER_PORTS=(/dev/cu.usbmodem*)
if [[ ${#CONTROLLER_PORTS[@]} != 1 ]]; then echo '请用可传数据的 USB 线连接一台 AI Passport。'; exit 1; fi
python "$CONTROLLER_ROOT/scripts/preflight.py"
echo '更新 V0.2.4：长请求逐页查看，最后一页实体审批；常用中文显示。'
echo '先双读备份，只更新应用；保留 Wi-Fi 配对、NVS、分区表和 bootloader。'
echo '保持当前桌面 App 打开；本入口不退出 App，也不切换聊天。'
python "$CONTROLLER_ROOT/scripts/flash.py" flash --port "${CONTROLLER_PORTS[0]}" --execute
echo '固件更新完成。正在重新连接现有 App 的实体审批通道…'
"$CONTROLLER_ROOT/private/bridge-venv/bin/python" "$CONTROLLER_ROOT/bridge/service.py" --desktop

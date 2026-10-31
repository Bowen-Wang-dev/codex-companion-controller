#!/bin/bash
set -euo pipefail
source "$(dirname "$0")/../scripts/env.sh"
trap 'echo "流程已结束；按回车关闭窗口。"; read -r' EXIT
"$CONTROLLER_ROOT/scripts/setup_bridge.sh"
python "$CONTROLLER_ROOT/scripts/preflight.py"
"$CONTROLLER_ROOT/private/bridge-venv/bin/python" - "$CONTROLLER_ROOT" <<'PY'
import sys
from pathlib import Path
sys.path.insert(0,str(Path(sys.argv[1])/'scripts'))
from launch_desktop import verify_build
verify_build()
PY
shopt -s nullglob
CONTROLLER_PORTS=(/dev/cu.usbmodem*)
if [[ ${#CONTROLLER_PORTS[@]} != 1 ]]; then
 echo '请用可传数据的 USB 线连接一台 AI Passport，再重新打开本更新入口。'
 exit 1
fi
echo '更新 V0.2.5：长按方向键跳到首/末页，确认页可以返回，长按确认转到 Mac。'
echo '先双读完整备份，只更新应用；保留 Wi-Fi 配对、NVS、bootloader 和分区表。'
echo '刷机期间可保持当前 App 打开。此脚本不自动退出 App，不发任务，不批准权限。'
python "$CONTROLLER_ROOT/scripts/flash.py" flash --port "${CONTROLLER_PORTS[0]}" --execute
echo
echo '固件已更新并校验。新版审批回执还需要重新加载 App 接入层。'
echo '请记下当前聊天名称，使用 Command+Q 完全退出 Codex/ChatGPT App。'
echo '退出后回到本终端，按回车重新打开 App 与 Bridge，然后从侧栏打开原来的聊天。'
echo '这不会清除聊天，也不需要重新配 Wi-Fi。'
read -r
"$CONTROLLER_ROOT/private/bridge-venv/bin/python" "$CONTROLLER_ROOT/scripts/launch_desktop.py"

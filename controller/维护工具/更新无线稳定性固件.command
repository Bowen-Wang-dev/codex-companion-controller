#!/bin/bash
set -euo pipefail
source "$(dirname "$0")/../scripts/env.sh"
trap 'echo "流程已结束；按回车关闭窗口。"; read -r' EXIT
python "$CONTROLLER_ROOT/scripts/preflight.py"
"$CONTROLLER_ROOT/scripts/setup_bridge.sh"
echo '更新 0.2.8：修复无线重连阻塞、有限重试与中文快照编码，新增断线诊断。'
echo '请保持 App 和当前聊天打开，仅在旧 Bridge 终端按 Control+C。无需重配 Wi-Fi。'
echo '先运行完整主机测试；测试失败会停止，不写 Flash。'
"$CONTROLLER_ROOT/private/bridge-venv/bin/python" -m unittest discover -s "$CONTROLLER_ROOT/tests" -v
shopt -s nullglob
CONTROLLER_PORTS=(/dev/cu.usbmodem*)
if [[ ${#CONTROLLER_PORTS[@]} != 1 ]]; then
 echo '请通过 USB 数据线连接一台 AI Passport，再重新运行。'
 exit 1
fi
echo '随后双读 8 MB 备份并校验，仅写 factory 应用并回读验证，保留配网和 NVS。'
read -r -p '确认旧 Bridge 已停止后按回车开始更新；Control+C 取消：'
python "$CONTROLLER_ROOT/scripts/flash.py" flash --port "${CONTROLLER_PORTS[0]}" --execute
echo '更新完成。正在重新连接当前 App 与已配对的 Wi-Fi；保持本窗口运行。'
exec "$CONTROLLER_ROOT/private/bridge-venv/bin/python" "$CONTROLLER_ROOT/bridge/service.py" --desktop

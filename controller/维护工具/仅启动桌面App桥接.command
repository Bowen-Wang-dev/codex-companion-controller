#!/bin/bash
set -euo pipefail
source "$(dirname "$0")/../scripts/env.sh"
trap 'echo "流程已结束；按回车关闭窗口。"; read -r' EXIT
python "$CONTROLLER_ROOT/scripts/preflight.py"
"$CONTROLLER_ROOT/scripts/setup_bridge.sh"
echo '正在连接已打开的桌面 App；不刷固件、不退出 App、不切换聊天。'
echo '请保持从「启动桌面App实体审批.command」打开的 App 继续运行。'
echo '本版审批详情使用中文说明，完整保留实际路径、命令与权限范围。'
"$CONTROLLER_ROOT/private/bridge-venv/bin/python" "$CONTROLLER_ROOT/bridge/service.py" --desktop

#!/bin/bash
set -euo pipefail
source "$(dirname "$0")/../scripts/env.sh"
trap 'echo "流程结束；按回车关闭窗口。"; read -r' EXIT
"$CONTROLLER_ROOT/scripts/setup_bridge.sh"
"$CONTROLLER_BRIDGE_PYTHON" "$CONTROLLER_ROOT/scripts/recover_bridge.py"

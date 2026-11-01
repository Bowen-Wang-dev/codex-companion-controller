#!/bin/bash
set -euo pipefail
source "$(dirname "$0")/../scripts/env.sh"
trap 'echo "按回车关闭窗口。"; read -r' EXIT
"$CONTROLLER_ROOT/scripts/setup_bridge.sh"
"$CONTROLLER_BRIDGE_PYTHON" "$CONTROLLER_ROOT/scripts/metering.py" --reset

#!/bin/bash
set -euo pipefail
source "$(dirname "$0")/scripts/env.sh"
trap 'echo "核对结束；按回车关闭窗口。"; read -r' EXIT
"$CONTROLLER_ROOT/scripts/setup_bridge.sh"
"$CONTROLLER_ROOT/private/bridge-venv/bin/python" "$CONTROLLER_ROOT/scripts/audit_usage.py" "$@"

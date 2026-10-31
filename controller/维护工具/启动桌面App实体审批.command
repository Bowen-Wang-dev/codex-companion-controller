#!/bin/bash
set -euo pipefail
CONTROLLER_SCRIPT_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
source "$CONTROLLER_SCRIPT_ROOT/scripts/env.sh"
"$CONTROLLER_SCRIPT_ROOT/scripts/setup_bridge.sh"
set +e
"$CONTROLLER_SCRIPT_ROOT/private/bridge-venv/bin/python" "$CONTROLLER_SCRIPT_ROOT/scripts/launch_desktop.py"
CONTROLLER_RESULT=$?
echo '流程结束；按回车关闭。'
read -r
exit "$CONTROLLER_RESULT"

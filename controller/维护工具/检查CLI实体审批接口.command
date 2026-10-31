#!/bin/bash
set -euo pipefail
source "$(dirname "$0")/../scripts/env.sh"
trap 'echo "检查已结束；按回车关闭。"; read -r' EXIT
"$CONTROLLER_ROOT/scripts/setup_bridge.sh"
"$CONTROLLER_ROOT/private/bridge-venv/bin/python" "$CONTROLLER_ROOT/scripts/run_native_cli.py" --check

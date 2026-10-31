#!/bin/bash
set -euo pipefail
source "$(dirname "$0")/../scripts/env.sh"
trap 'echo "按回车关闭"; read -r' EXIT
python "$CONTROLLER_ROOT/scripts/preflight.py"
python "$CONTROLLER_ROOT/scripts/pair_wifi.py"
"$CONTROLLER_ROOT/scripts/run_bridge.sh"

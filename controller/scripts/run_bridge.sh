#!/bin/bash
set -euo pipefail
source "$(dirname "$0")/env.sh"
if [[ $# -gt 0 ]]; then CONTROLLER_PORT="$1"; else
  shopt -s nullglob
  CONTROLLER_PORTS=(/dev/cu.usbmodem*)
  if [[ -f "$CONTROLLER_ROOT/private/wireless.json" ]]; then CONTROLLER_PORT="";
  elif [[ ${#CONTROLLER_PORTS[@]} == 1 ]]; then CONTROLLER_PORT="${CONTROLLER_PORTS[0]}"; else CONTROLLER_PORT=""; fi
fi
"$CONTROLLER_ROOT/scripts/setup_bridge.sh"
exec "$CONTROLLER_ROOT/private/bridge-venv/bin/python" "$CONTROLLER_ROOT/bridge/service.py" --port "$CONTROLLER_PORT"

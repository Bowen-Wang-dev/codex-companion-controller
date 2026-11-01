#!/bin/bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
source "$ROOT/scripts/env.sh"
"$ROOT/scripts/setup_bridge.sh"
exec "$CONTROLLER_BRIDGE_PYTHON" "$ROOT/bridge/token_rates_gui.py"

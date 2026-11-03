#!/bin/bash
set -euo pipefail
export COMPANION_LANGUAGE=en
ROOT="$(cd "$(dirname "$0")" && pwd)"
source "$ROOT/scripts/env.sh"
"$ROOT/scripts/setup_bridge.sh"
exec "$CONTROLLER_BRIDGE_PYTHON" "$ROOT/scripts/controller_console.py" "$@"

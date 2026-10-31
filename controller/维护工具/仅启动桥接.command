#!/bin/bash
set -euo pipefail
CONTROLLER_SCRIPT_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
exec "$CONTROLLER_SCRIPT_ROOT/scripts/run_bridge.sh" "$@"

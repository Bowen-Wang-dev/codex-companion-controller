#!/bin/bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")" && pwd)"
source "$ROOT/scripts/env.sh"
"$ROOT/scripts/setup_bridge.sh"
exec "$ROOT/private/bridge-venv/bin/python" "$ROOT/scripts/controller_console.py"

#!/bin/bash
set -euo pipefail
CONTROLLER_SCRIPT_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
source "$CONTROLLER_SCRIPT_ROOT/scripts/env.sh"
CONTROLLER_REAL_CODEX="${PASSPORT_REAL_CODEX:-/Applications/ChatGPT.app/Contents/Resources/codex-cli/CodexCLI.app/Contents/MacOS/codex}"
exec "$CONTROLLER_BRIDGE_PYTHON" "$CONTROLLER_SCRIPT_ROOT/bridge/stdio_relay.py" --real "$CONTROLLER_REAL_CODEX" -- "$@"

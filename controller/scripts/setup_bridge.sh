#!/bin/bash
set -euo pipefail
source "$(dirname "$0")/env.sh"
CONTROLLER_MODERN_PYTHON="${CONTROLLER_MODERN_PYTHON:-$(command -v python3 || true)}"
if [[ ! -x "$CONTROLLER_MODERN_PYTHON" ]]; then echo '需要 Python 3.11+ / OpenSSL 3。请设置 CONTROLLER_MODERN_PYTHON。'; exit 1; fi
"$CONTROLLER_MODERN_PYTHON" -c 'import sys,ssl;assert sys.version_info >= (3,11), "Python 3.11+ required";assert ssl.OPENSSL_VERSION.startswith("OpenSSL 3."), "OpenSSL 3 required"'
if [[ ! -x "$CONTROLLER_ROOT/private/bridge-venv/bin/python" ]]; then
 "$CONTROLLER_MODERN_PYTHON" -m venv "$CONTROLLER_ROOT/private/bridge-venv"
fi
if ! "$CONTROLLER_ROOT/private/bridge-venv/bin/python" -c 'import serial;assert serial.VERSION=="3.5"' 2>/dev/null; then
 "$CONTROLLER_ROOT/private/bridge-venv/bin/python" -m pip install -r "$CONTROLLER_ROOT/requirements-bridge.txt"
fi
"$CONTROLLER_ROOT/private/bridge-venv/bin/python" "$CONTROLLER_ROOT/scripts/setup_bridge_deps.py"
"$CONTROLLER_ROOT/private/bridge-venv/bin/python" -c 'import ssl,serial;print("Bridge runtime:",ssl.OPENSSL_VERSION)'

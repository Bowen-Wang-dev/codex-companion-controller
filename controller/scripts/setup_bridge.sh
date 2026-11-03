#!/bin/bash
set -euo pipefail
source "$(dirname "$0")/env.sh"
CONTROLLER_MODERN_PYTHON="${CONTROLLER_MODERN_PYTHON:-$(command -v python3 || true)}"
if [[ ! -x "$CONTROLLER_MODERN_PYTHON" ]]; then
 companion_message '需要 Python 3.11+ / OpenSSL 3。请设置 CONTROLLER_MODERN_PYTHON。' 'Python 3.11+ / OpenSSL 3 required. Set CONTROLLER_MODERN_PYTHON.'
 exit 1
fi
"$CONTROLLER_MODERN_PYTHON" -c 'import sys,ssl;assert sys.version_info >= (3,11), "Python 3.11+ required";assert ssl.OPENSSL_VERSION.startswith("OpenSSL 3."), "OpenSSL 3 required"'
if [[ ! -x "$CONTROLLER_BRIDGE_PYTHON" ]]; then
 "$CONTROLLER_MODERN_PYTHON" -m venv "$(dirname "$(dirname "$CONTROLLER_BRIDGE_PYTHON")")"
fi
"$CONTROLLER_BRIDGE_PYTHON" "$CONTROLLER_ROOT/scripts/setup_bridge_deps.py"
"$CONTROLLER_BRIDGE_PYTHON" -c 'import ssl,serial,websockets;assert serial.VERSION=="3.5";assert websockets.__version__=="17.3";print("Bridge runtime:",ssl.OPENSSL_VERSION)'

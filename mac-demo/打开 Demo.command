#!/bin/zsh
set -euo pipefail
DEMO_ROOT="${0:A:h}"
if [[ ! -x "$DEMO_ROOT/Codex Companion.app/Contents/MacOS/CompanionDemo" ]]; then
  "$DEMO_ROOT/build.sh"
fi
open -n "$DEMO_ROOT/Codex Companion.app"

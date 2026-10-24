#!/bin/bash
set -euo pipefail
source "$(dirname "$0")/env.sh"
cd "$CONTROLLER_ROOT/firmware"
if [[ -n "${PASSPORT_DEPS:-}" ]]; then export IDF_COMPONENT_MANAGER=0; fi
python "$IDF_PATH/tools/idf.py" -B "$CONTROLLER_ROOT/private/build" build
mkdir -p "$CONTROLLER_ROOT/dist"
cp "$CONTROLLER_ROOT/private/build/PassportController.bin" "$CONTROLLER_ROOT/dist/PassportController.bin.tmp"
mv "$CONTROLLER_ROOT/dist/PassportController.bin.tmp" "$CONTROLLER_ROOT/dist/PassportController.bin"
cp "$CONTROLLER_ROOT/firmware/sdkconfig" "$CONTROLLER_ROOT/dist/sdkconfig.built"
python "$CONTROLLER_ROOT/scripts/manifest.py"

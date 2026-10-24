#!/bin/bash
set -euo pipefail
source "$(dirname "$0")/env.sh"
: "${IDF_PATH:?Install ESP-IDF 5.5.3 and source its export.sh before building.}"
cd "$CONTROLLER_ROOT/firmware"
if [[ -n "${PASSPORT_DEPS:-}" ]]; then export IDF_COMPONENT_MANAGER=0; fi
python "$IDF_PATH/tools/idf.py" -B "$CONTROLLER_ROOT/private/build" build
mkdir -p "$CONTROLLER_ROOT/dist"
cp "$CONTROLLER_ROOT/private/build/PassportController.bin" "$CONTROLLER_ROOT/dist/"
cp "$CONTROLLER_ROOT/firmware/sdkconfig" "$CONTROLLER_ROOT/dist/sdkconfig.built"
python "$CONTROLLER_ROOT/scripts/manifest.py"

#!/bin/bash
set -euo pipefail
source "$(dirname "$0")/env.sh"
cd "$CONTROLLER_ROOT/firmware"
CONTROLLER_BUILD_LANGUAGE=zh-CN
if [[ "${COMPANION_LANGUAGE:-}" == en ]]; then CONTROLLER_BUILD_LANGUAGE=en; fi
if [[ -n "${PASSPORT_DEPS:-}" ]]; then export IDF_COMPONENT_MANAGER=0; fi
python "$IDF_PATH/tools/idf.py" "-DCOMPANION_FIRMWARE_LANGUAGE=$CONTROLLER_BUILD_LANGUAGE" -B "$CONTROLLER_ROOT/private/build" build
mkdir -p "$CONTROLLER_ROOT/dist"
cp "$CONTROLLER_ROOT/private/build/PassportController.bin" "$CONTROLLER_ROOT/dist/PassportController.bin.tmp"
mv "$CONTROLLER_ROOT/dist/PassportController.bin.tmp" "$CONTROLLER_ROOT/dist/PassportController.bin"
cp "$CONTROLLER_ROOT/firmware/sdkconfig" "$CONTROLLER_ROOT/dist/sdkconfig.built"
python "$CONTROLLER_ROOT/scripts/manifest.py"
mkdir -p "$CONTROLLER_ROOT/dist/$CONTROLLER_BUILD_LANGUAGE"
cp "$CONTROLLER_ROOT/dist/PassportController.bin" "$CONTROLLER_ROOT/dist/$CONTROLLER_BUILD_LANGUAGE/PassportController.bin"
cp "$CONTROLLER_ROOT/dist/manifest.json" "$CONTROLLER_ROOT/dist/$CONTROLLER_BUILD_LANGUAGE/manifest.json"

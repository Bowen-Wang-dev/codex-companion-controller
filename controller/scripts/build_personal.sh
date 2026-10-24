#!/bin/bash
set -euo pipefail
source "$(dirname "$0")/env.sh"
CONTROLLER_IMAGE_PYTHON="${CONTROLLER_IMAGE_PYTHON:-${CONTROLLER_MODERN_PYTHON:-$(command -v python3)}}"
mkdir -p "$CONTROLLER_ROOT/private/apple-originals" "$CONTROLLER_ROOT/private/swift-cache"
swiftc -module-cache-path "$CONTROLLER_ROOT/private/swift-cache" "$CONTROLLER_ROOT/tools/RenderAppleEmoji.swift" -o "$CONTROLLER_ROOT/private/RenderAppleEmoji" -framework AppKit
"$CONTROLLER_ROOT/private/RenderAppleEmoji" "$CONTROLLER_ROOT/private/apple-originals"
"$CONTROLLER_IMAGE_PYTHON" "$CONTROLLER_ROOT/scripts/import_assets.py" --source "$CONTROLLER_ROOT/private/apple-originals" --local-system-render
"$CONTROLLER_ROOT/scripts/build.sh"

#!/bin/zsh
set -euo pipefail
DEMO_ROOT="${0:A:h}"
DEMO_CACHE="${COMPANION_BUILD_CACHE:-${TMPDIR:-/tmp}/codex-companion-build-${UID}}"
mkdir -p "$DEMO_CACHE/swift-module-cache" "$DEMO_CACHE/swift-cache"
export CLANG_MODULE_CACHE_PATH="$DEMO_CACHE/swift-module-cache"
export SWIFTPM_MODULECACHE_OVERRIDE="$DEMO_CACHE/swift-module-cache"
swift run --package-path "$DEMO_ROOT" --scratch-path "$DEMO_CACHE/demo-build" --cache-path "$DEMO_CACHE/swift-cache" --disable-sandbox -Xswiftc -module-cache-path -Xswiftc "$DEMO_CACHE/swift-module-cache" CompanionCoreChecks

#!/bin/zsh
set -euo pipefail
DEMO_ROOT="${0:A:h}"
DEMO_CACHE="${COMPANION_BUILD_CACHE:-${TMPDIR:-/tmp}/codex-companion-build-${UID}}"
mkdir -p "$DEMO_CACHE/swift-module-cache" "$DEMO_CACHE/swift-cache"
export CLANG_MODULE_CACHE_PATH="$DEMO_CACHE/swift-module-cache"
export SWIFTPM_MODULECACHE_OVERRIDE="$DEMO_CACHE/swift-module-cache"
swift build --package-path "$DEMO_ROOT" --scratch-path "$DEMO_CACHE/demo-build" --cache-path "$DEMO_CACHE/swift-cache" --disable-sandbox -c release -Xswiftc -module-cache-path -Xswiftc "$DEMO_CACHE/swift-module-cache"
DEMO_APP="$DEMO_ROOT/Codex Companion.app"
mkdir -p "$DEMO_APP/Contents/MacOS" "$DEMO_APP/Contents/Resources"
cp "$DEMO_CACHE/demo-build/release/CompanionDemo" "$DEMO_APP/Contents/MacOS/CompanionDemo"
cat > "$DEMO_APP/Contents/Info.plist" <<'PLIST'
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0"><dict>
<key>CFBundleExecutable</key><string>CompanionDemo</string>
<key>CFBundleIdentifier</key><string>local.codexcompanion.macdemo</string>
<key>CFBundleName</key><string>Codex Companion</string>
<key>CFBundleDisplayName</key><string>Codex Companion</string>
<key>CFBundleVersion</key><string>4</string>
<key>CFBundleShortVersionString</key><string>0.4.0</string>
<key>CFBundlePackageType</key><string>APPL</string>
<key>LSMinimumSystemVersion</key><string>14.0</string>
<key>NSHighResolutionCapable</key><true/>
</dict></plist>
PLIST
codesign --force --deep --sign - "$DEMO_APP"
echo "Built: $DEMO_APP"

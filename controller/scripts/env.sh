#!/bin/bash
# Source from the project; toolchain remains read-only, all build/cache output is local.
if [ -n "${BASH_VERSION:-}" ]; then
  CONTROLLER_ENV_PATH="${BASH_SOURCE[0]}"
elif [ -n "${ZSH_VERSION:-}" ]; then
  CONTROLLER_ENV_PATH="${(%):-%x}"
else
  echo 'Source env.sh from bash or zsh.' >&2
  return 1
fi
CONTROLLER_ROOT="$(cd "$(dirname "$CONTROLLER_ENV_PATH")/.." && pwd)"
CONTROLLER_UI_LANGUAGE="${COMPANION_LANGUAGE:-zh-CN}"
if [[ -f "$CONTROLLER_ROOT/private/local-env.sh" ]]; then
  source "$CONTROLLER_ROOT/private/local-env.sh"
fi
export COMPANION_LANGUAGE="$CONTROLLER_UI_LANGUAGE"
source "$CONTROLLER_ROOT/scripts/console_i18n.sh"
export CONTROLLER_BRIDGE_PYTHON="${CONTROLLER_BRIDGE_PYTHON:-$CONTROLLER_ROOT/private/bridge-venv/bin/python}"
# Prefer the environment produced by ESP-IDF's export.sh. The optional bundled
# tool root keeps the original offline-layout workflow available without a
# developer-specific absolute path in the source release.
if [[ -n "${PASSPORT_TOOL_ROOT:-}" ]]; then
  export IDF_PATH="${IDF_PATH:-$PASSPORT_TOOL_ROOT/esp-idf-v5.5.3}"
  export IDF_TOOLS_PATH="${IDF_TOOLS_PATH:-$PASSPORT_TOOL_ROOT/espressif-tools}"
  export PATH="$PASSPORT_TOOL_ROOT/host-tools/bin:$IDF_TOOLS_PATH/tools/riscv32-esp-elf/esp-14.2.0_20251107/riscv32-esp-elf/bin:$PATH"
fi
if [[ -n "${IDF_PYTHON_ENV_PATH:-}" ]]; then
  export PATH="$IDF_PYTHON_ENV_PATH/bin:$PATH"
  export CONTROLLER_FLASH_PYTHON="${CONTROLLER_FLASH_PYTHON:-$IDF_PYTHON_ENV_PATH/bin/python}"
fi
export IDF_COMPONENT_CACHE_PATH="$CONTROLLER_ROOT/private/component-cache"
export PYTHONPYCACHEPREFIX="$CONTROLLER_ROOT/private/pycache"
export IDF_CCACHE_ENABLE=0
export CCACHE_DISABLE=1
mkdir -p "$CONTROLLER_ROOT/private"
chmod 700 "$CONTROLLER_ROOT/private"
export ESP_IDF_VERSION=5.5.3
if [[ -n "${IDF_TOOLS_PATH:-}" ]]; then
  export ESP_ROM_ELF_DIR="${ESP_ROM_ELF_DIR:-$IDF_TOOLS_PATH/tools/esp-rom-elfs/20241011}"
fi
if [[ -z "${COMPANION_CODEX:-}" ]] && [[ -x '/Applications/ChatGPT.app/Contents/Resources/codex-cli/CodexCLI.app/Contents/MacOS/codex' ]]; then
  export COMPANION_CODEX='/Applications/ChatGPT.app/Contents/Resources/codex-cli/CodexCLI.app/Contents/MacOS/codex'
fi

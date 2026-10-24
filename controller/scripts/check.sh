#!/bin/bash
set -euo pipefail
source "$(dirname "$0")/env.sh"
mkdir -p "$CONTROLLER_ROOT/private/checks"
cc -std=c11 -Wall -Wextra -Werror "$CONTROLLER_ROOT/firmware/main/controller.c" "$CONTROLLER_ROOT/firmware/main/sound_model.c" "$CONTROLLER_ROOT/tests/controller_test.c" -o "$CONTROLLER_ROOT/private/checks/controller"
"$CONTROLLER_ROOT/private/checks/controller"
cc -std=c11 -Wall -Wextra -Werror "$CONTROLLER_ROOT/firmware/main/sound_model.c" "$CONTROLLER_ROOT/tests/sound_test.c" -o "$CONTROLLER_ROOT/private/checks/sound"
"$CONTROLLER_ROOT/private/checks/sound"
cc -std=c11 -Wall -Wextra -Werror -I"$CONTROLLER_ROOT/tests/audio_stubs" "$CONTROLLER_ROOT/firmware/main/sound.c" "$CONTROLLER_ROOT/firmware/main/sound_model.c" "$CONTROLLER_ROOT/tests/audio_runtime_test.c" -o "$CONTROLLER_ROOT/private/checks/audio-runtime"
for CONTROLLER_AUDIO_CASE in pager priority mute request_mute pending_mute zero init_error write_error; do
 "$CONTROLLER_ROOT/private/checks/audio-runtime" "$CONTROLLER_AUDIO_CASE"
done
"$CONTROLLER_ROOT/scripts/setup_bridge.sh"
"$CONTROLLER_ROOT/private/bridge-venv/bin/python" -m unittest discover -s "$CONTROLLER_ROOT/tests" -v
python -m esptool --chip esp32c3 image_info "$CONTROLLER_ROOT/dist/PassportController.bin"

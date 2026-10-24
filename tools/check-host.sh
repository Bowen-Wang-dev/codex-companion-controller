#!/bin/bash
set -euo pipefail
SOURCE_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
CHECK_ROOT="$SOURCE_ROOT/controller/private/checks"
mkdir -p "$CHECK_ROOT"
cc -std=c11 -Wall -Wextra -Werror "$SOURCE_ROOT/controller/firmware/main/controller.c" "$SOURCE_ROOT/controller/firmware/main/sound_model.c" "$SOURCE_ROOT/controller/tests/controller_test.c" -o "$CHECK_ROOT/controller"
"$CHECK_ROOT/controller"
cc -std=c11 -Wall -Wextra -Werror "$SOURCE_ROOT/controller/firmware/main/sound_model.c" "$SOURCE_ROOT/controller/tests/sound_test.c" -o "$CHECK_ROOT/sound"
"$CHECK_ROOT/sound"
cc -std=c11 -Wall -Wextra -Werror -I"$SOURCE_ROOT/controller/tests/audio_stubs" "$SOURCE_ROOT/controller/firmware/main/sound.c" "$SOURCE_ROOT/controller/firmware/main/sound_model.c" "$SOURCE_ROOT/controller/tests/audio_runtime_test.c" -o "$CHECK_ROOT/audio-runtime"
for AUDIO_CASE in pager priority mute request_mute pending_mute zero init_error write_error; do
  "$CHECK_ROOT/audio-runtime" "$AUDIO_CASE"
done

#pragma once
#include <stdbool.h>
#include <stdint.h>
#include "sound_model.h"
typedef enum { SOUND_STARTING, SOUND_READY, SOUND_ERROR } sound_state_t;
typedef struct { sound_state_t state; int error; uint32_t samples, played, start_delay_ms, max_feed_gap_ms; } sound_health_t;
void sound_start(void);
void sound_play(sound_kind_t kind);
void sound_mute(bool mute);
void sound_cancel_permission(void);

void sound_volume(int volume);
sound_health_t sound_health(void);

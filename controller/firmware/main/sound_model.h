#pragma once
#include <stddef.h>
#include <stdint.h>
typedef enum {
 SOUND_PERMISSION, SOUND_COMPLETED, SOUND_FAILED, SOUND_DISCONNECTED,
 SOUND_EXHAUSTED, SOUND_ALLOWED, SOUND_DENIED, SOUND_TOUCH, SOUND_PREVIEW,
 SOUND_COUNT
} sound_kind_t;
typedef struct { int hz, ms; } sound_note_t;
typedef struct { uint32_t phase; } sound_pcm_t;
size_t sound_notes(sound_kind_t kind, const sound_note_t **notes);
int sound_priority(sound_kind_t kind);
int sound_volume_step(int value, int direction);
void sound_pcm(sound_pcm_t *state, int hz, int note_samples, int offset,
               int16_t *pcm, int count, int volume);

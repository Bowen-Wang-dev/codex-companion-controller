#pragma once
#include <stdbool.h>
#include <stdint.h>
typedef struct {
 int page, option, selected, stage, key;
 int64_t pressed_at, last_rx, expires, delight_until;
 bool consumed, online, request, request_visible, can_allow, can_deny, muted, sound, volume_edit, mac_confirm, user_input;
 char id[40], epoch[40], digest[65], state[20], command[192], project[96];
 char scope[128], receipt[96];
 int review_protocol, review_page, review_total, review_loaded;
 char review_text[512];
 uint32_t sequence;
 int primary, secondary, resets, minutes[2];
 int64_t resets_at[2], utc, clock_at;
 int utc_offset;
 int reset_stage, volume, interval;
 char reset_id[40], reset_status[96], usage_status[96], transport[8], history[8][96];
 int history_count;
 char face[20];
 char hook_status[128];
} controller_t;
typedef enum { ACTION_NONE, ACTION_DENY, ACTION_ALLOW, ACTION_MUTE, ACTION_RESET, ACTION_PAIR,
 ACTION_TEST_AUDIO, ACTION_PREVIEW_AUDIO, ACTION_TOUCH, ACTION_DISMISS, ACTION_REVIEW } action_t;
void controller_init(controller_t *s);
void controller_press(controller_t *s, int key, int64_t now);
action_t controller_tick(controller_t *s, int64_t now);
action_t controller_release(controller_t *s, int key, int64_t now);
void controller_cancel_input(controller_t *s);
void controller_request(controller_t *s, const char *id);
bool controller_review_final(const controller_t *s);
void controller_review_snapshot(controller_t *s,int page,int total,const char *text);
uint32_t controller_view_hash(const controller_t *s);

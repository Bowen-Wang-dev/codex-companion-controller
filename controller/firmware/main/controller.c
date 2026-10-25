#include "controller.h"
#include "sound_model.h"
#include <string.h>
#include <stdio.h>

uint32_t controller_view_hash(const controller_t *s) {
 uint32_t h=2166136261u;
 const char *strings[]={s->id,s->state,s->command,s->project,s->scope,s->receipt,s->face,
  s->reset_id,s->reset_status,s->usage_status,s->hook_status,s->transport,s->review_text,
  s->billing,s->token_model,s->model_source,s->meter_id,s->token_cost_currency,s->token_cost_status,s->token_total_status};
 for(unsigned i=0;i<sizeof(strings)/sizeof(strings[0]);i++) {
  for(const unsigned char *p=(const unsigned char *)strings[i];*p;p++)h=(h^*p)*16777619u;
  h=(h^0xffu)*16777619u;
 }
 for(int i=0;i<s->history_count && i<8;i++)
  for(const unsigned char *p=(const unsigned char *)s->history[i];*p;p++)h=(h^*p)*16777619u;
 const int values[]={s->page,s->option,s->stage,s->selected,s->online,s->request_visible,
  s->can_allow,s->can_deny,s->mac_confirm,s->user_input,s->handling_on_mac,s->sound,s->muted,s->volume,s->volume_edit,
  s->interval,s->reset_stage,s->primary,s->secondary,s->resets,s->history_count,
  s->review_protocol,s->review_page,s->review_loaded,s->review_total,s->meter_stage,s->token_updated,s->token_total_updated,s->token_priced};
 for(unsigned i=0;i<sizeof(values)/sizeof(values[0]);i++)h=(h^(uint32_t)values[i])*16777619u;
 for(int k=0;k<6;k++) {
  h=(h^(uint32_t)s->token_last[k])*16777619u;
  h=(h^(uint32_t)(s->token_last[k]>>32))*16777619u;
  h=(h^(uint32_t)s->token_total[k])*16777619u;
  h=(h^(uint32_t)(s->token_total[k]>>32))*16777619u;
 }
 const unsigned char *cost=(const unsigned char *)&s->token_cost_last;
 for(unsigned k=0;k<sizeof(s->token_cost_last);k++)h=(h^cost[k])*16777619u;
 cost=(const unsigned char *)&s->token_cost_total;
 for(unsigned k=0;k<sizeof(s->token_cost_total);k++)h=(h^cost[k])*16777619u;
 return h;
}

void controller_init(controller_t *s) {
 memset(s, 0, sizeof(*s)); s->key=-1; s->selected=-1;
 s->primary=s->secondary=s->resets=-1; s->sound=true; s->volume=20; s->interval=30; s->can_deny=true;
 strcpy(s->state,"idle");
}
void controller_cancel_input(controller_t *s) { s->consumed=true; s->stage=0; s->selected=-1; s->reset_stage=0; s->meter_stage=0; s->volume_edit=false; }
void controller_request(controller_t *s, const char *id) {
 if(strcmp(s->id,id)) {
  controller_cancel_input(s); snprintf(s->id,sizeof(s->id),"%s",id);
  s->request=*id!=0; s->request_visible=s->request; s->muted=false;
  s->handling_on_mac=false;
  s->review_protocol=0; s->review_page=0; s->review_loaded=-1; s->review_total=0; s->review_text[0]=0;
 }
}
bool controller_review_final(const controller_t *s) {
 return s->review_protocol!=1 || (s->review_total>0 && s->review_page==s->review_total && s->review_loaded==s->review_page);
}
void controller_review_snapshot(controller_t *s,int page,int total,const char *text) {
 if(total<1 || total>4096 || page<0 || page>total || strlen(text)>=sizeof(s->review_text))return;
 if(s->review_protocol!=1) { controller_cancel_input(s);s->review_page=0;s->review_loaded=-1; }
 s->review_protocol=1; s->review_total=total;
 if(page==s->review_page) { s->review_loaded=page;snprintf(s->review_text,sizeof(s->review_text),"%s",text); }
 else {
  // A delayed queued page command can move the Bridge back. Re-request the
  // desired page instead of getting stuck with stale final-screen flags.
  s->review_loaded=-1;
  if(s->stage==1)controller_cancel_input(s);
 }
}
static action_t review_move(controller_t *s,int key,bool held) {
 if(s->stage==2)return ACTION_NONE;
 int next=s->review_page;
 if(held) {
  next=key==0?0:s->review_total;
  // Even if already on the final page, a held direction exits the second
  // confirmation and clears its choice. Releasing it must never select again.
  s->selected=-1;s->stage=0;s->handling_on_mac=false;
 }
 else if(s->review_loaded==s->review_page && s->review_page<s->review_total)
  next+=key==0?-1:1;
 if(next<0)next=0;
 if(next==s->review_page)return ACTION_NONE;
 s->review_page=next; s->selected=-1; s->stage=0;
 return ACTION_REVIEW;
}
void controller_press(controller_t *s,int key,int64_t now) {
 if(s->key>=0) return;
 s->key=key; s->pressed_at=now; s->consumed=false;
}
static void turn(controller_t *s,int direction) {
 if(s->page==0 && strcmp(s->billing,"token") && (s->primary==0 || s->secondary==0 || !strcmp(s->state,"exhausted")) && direction<0) s->page=2;
 else s->page=(s->page+direction+6)%6;
 s->option=0; s->selected=-1; s->stage=0; s->reset_stage=0; s->meter_stage=0; s->request_visible=false; s->volume_edit=false;
}
action_t controller_tick(controller_t *s,int64_t now) {
 if(s->online && now-s->last_rx>5000) { s->online=false; controller_cancel_input(s); }
 if(s->request && now>=s->expires) { controller_request(s,""); }
 if(s->meter_stage==2 && now-s->meter_sent_at>10000) {
  s->meter_stage=0;snprintf(s->receipt,sizeof(s->receipt),"计数回执未确认");
 }
 if(s->key<0 || s->consumed) return ACTION_NONE;
 int threshold=(s->key==2 && (s->stage==1 || s->reset_stage==2 || s->meter_stage==1))?1000:650;
 if(now-s->pressed_at<threshold) return ACTION_NONE;
 s->consumed=true;
 if(s->key!=2) {
  if(s->request_visible && s->review_protocol==1)return review_move(s,s->key,true);
  turn(s,s->key==0?-1:1); return ACTION_NONE;
 }
 if(s->request_visible && !s->user_input && controller_review_final(s) && s->stage==1 && s->online && s->request && now<s->expires) {
  if((s->selected==1 && s->can_deny) || (s->selected==0 && s->can_allow)) {
   s->stage=2; return s->selected==0?ACTION_ALLOW:ACTION_DENY;
  }
 }
 if(s->key==2 && s->page==2 && strcmp(s->billing,"token") && s->reset_stage==2 && s->online && s->resets>0 && *s->reset_id) {
  s->reset_stage=3; return ACTION_RESET;
 }
 if(!s->request_visible && !s->request && s->page==1 && !strcmp(s->billing,"token") && s->meter_stage==1 && s->online && *s->meter_id) {
  s->meter_stage=2;s->meter_sent_at=now;return ACTION_METER_RESET;
 }
 if(s->meter_stage==2)return ACTION_NONE;
 // Long OK on a browsing page returns to the pending request, or home.
 if(!s->request_visible) { s->page=0; s->request_visible=s->request; s->volume_edit=false; }
 else if(s->stage==0) { s->selected=-1;s->handling_on_mac=true;s->muted=true;return ACTION_MAC; }
 return ACTION_NONE;
}
action_t controller_release(controller_t *s,int key,int64_t now) {
 if(s->key!=key) return ACTION_NONE;
 action_t a=controller_tick(s,now);
 bool short_press=!s->consumed; s->key=-1;
 if(!short_press) return a;
 if(s->request_visible && (!s->online || now>=s->expires))return ACTION_NONE;
 if(s->request_visible && s->handling_on_mac) {
  if(key==2)s->handling_on_mac=false;
  return ACTION_NONE;
 }
 if(key!=2) {
  if(s->request_visible) {
   if(s->review_protocol==1 && !controller_review_final(s))return review_move(s,key,false);
   if(s->stage==0 && ((key==0 && s->can_allow) || (key==1 && s->can_deny))) s->selected=key;
   else if(s->stage==1) {
    if(key==0) { s->stage=0; s->selected=-1; }
    else { s->muted=true; return ACTION_MUTE; }
   }
  } else if(s->meter_stage) { s->meter_stage=0;
  } else if(s->reset_stage) { s->reset_stage=0;
  } else if(s->page==3 && s->volume_edit) {
   int previous=s->volume; s->volume=sound_volume_step(s->volume,key==0?1:-1);
   if(s->volume!=previous)return ACTION_PREVIEW_AUDIO;
 } else if(s->page==3 || s->page==4) {
   int count=s->page==3?6:(s->history_count?s->history_count:1);
   s->option=(s->option+(key==0?-1:1)+count)%count;
  } else turn(s,key==0?-1:1);
 } else if(s->request_visible && s->stage==0) {
  if(!controller_review_final(s)) { s->muted=true; return ACTION_MUTE; }
  if(s->user_input) { s->request_visible=false; s->page=0; return ACTION_DISMISS; }
  if((s->selected==1 && s->can_deny) || (s->selected==0 && s->can_allow)) s->stage=1;
  else if(!s->can_allow && !s->can_deny) { s->muted=true; return ACTION_MUTE; }
 } else if(!s->request_visible && !s->request && s->page==1 && !strcmp(s->billing,"token")) {
  if(s->online && *s->meter_id && s->meter_stage==0)s->meter_stage=1;
 } else if(!s->request_visible && s->page==3) {
  if(s->option==0) { s->sound=!s->sound; if(s->sound)return ACTION_PREVIEW_AUDIO; }
  else if(s->option==1)return ACTION_TEST_AUDIO;
  else if(s->option==2) { s->muted=true; return ACTION_MUTE; }
  else if(s->option==3) s->volume_edit=!s->volume_edit;
  else if(s->option==4) s->interval=s->interval==30?60:s->interval==60?120:30;
  else s->page=0;
 } else if(!s->request_visible && s->page==2 && strcmp(s->billing,"token")) {
  if(s->online && s->resets>0 && *s->reset_id && s->reset_stage<2)s->reset_stage++;
 } else if(!s->request_visible && s->page==5) { return ACTION_PAIR;
 } else if(!s->request_visible && s->page==0) { s->delight_until=now+1200; return ACTION_TOUCH; }
 return ACTION_NONE;
}

#include "controller.h"
#include "sound_model.h"
#include <string.h>
#include <stdio.h>

uint32_t controller_view_hash(const controller_t *s) {
 uint32_t h=2166136261u;
 const char *strings[]={s->id,s->state,s->command,s->project,s->scope,s->receipt,s->face,
  s->reset_id,s->reset_status,s->usage_status,s->hook_status,s->transport};
 for(unsigned i=0;i<sizeof(strings)/sizeof(strings[0]);i++) {
  for(const unsigned char *p=(const unsigned char *)strings[i];*p;p++)h=(h^*p)*16777619u;
  h=(h^0xffu)*16777619u;
 }
 for(int i=0;i<s->history_count && i<8;i++)
  for(const unsigned char *p=(const unsigned char *)s->history[i];*p;p++)h=(h^*p)*16777619u;
 const int values[]={s->page,s->option,s->stage,s->selected,s->online,s->request_visible,
  s->can_allow,s->can_deny,s->mac_confirm,s->sound,s->muted,s->volume,s->volume_edit,
  s->interval,s->reset_stage,s->primary,s->secondary,s->resets,s->history_count};
 for(unsigned i=0;i<sizeof(values)/sizeof(values[0]);i++)h=(h^(uint32_t)values[i])*16777619u;
 return h;
}

void controller_init(controller_t *s) {
 memset(s, 0, sizeof(*s)); s->key=-1; s->selected=-1;
 s->primary=s->secondary=s->resets=-1; s->sound=true; s->volume=20; s->interval=30; s->can_deny=true;
 strcpy(s->state,"idle");
}
void controller_cancel_input(controller_t *s) { s->consumed=true; s->stage=0; s->selected=-1; s->reset_stage=0; s->volume_edit=false; }
void controller_request(controller_t *s, const char *id) {
 if(strcmp(s->id,id)) {
  controller_cancel_input(s); snprintf(s->id,sizeof(s->id),"%s",id);
  s->request=*id!=0; s->request_visible=s->request; s->muted=false;
 }
}
void controller_press(controller_t *s,int key,int64_t now) {
 if(s->key>=0) return;
 s->key=key; s->pressed_at=now; s->consumed=false;
}
static void turn(controller_t *s,int direction) {
 if(s->page==0 && (s->primary==0 || s->secondary==0 || !strcmp(s->state,"exhausted")) && direction<0) s->page=2;
 else s->page=(s->page+direction+6)%6;
 s->option=0; s->selected=-1; s->stage=0; s->reset_stage=0; s->request_visible=false; s->volume_edit=false;
}
action_t controller_tick(controller_t *s,int64_t now) {
 if(s->online && now-s->last_rx>5000) { s->online=false; controller_cancel_input(s); }
 if(s->request && now>=s->expires) { controller_request(s,""); }
 if(s->key<0 || s->consumed) return ACTION_NONE;
 int threshold=(s->key==2 && (s->stage==1 || s->reset_stage==2))?1000:650;
 if(now-s->pressed_at<threshold) return ACTION_NONE;
 s->consumed=true;
 if(s->key!=2) { turn(s,s->key==0?-1:1); return ACTION_NONE; }
 if(s->request_visible && s->stage==1 && s->online && s->request && now<s->expires) {
  if((s->selected==1 && s->can_deny) || (s->selected==0 && s->can_allow)) {
   s->stage=2; return s->selected==0?ACTION_ALLOW:ACTION_DENY;
  }
 }
 if(s->key==2 && s->page==2 && s->reset_stage==2 && s->online && s->resets>0 && *s->reset_id) {
  s->reset_stage=3; return ACTION_RESET;
 }
 // Long OK on a browsing page returns to the pending request, or home.
 if(!s->request_visible) { s->page=0; s->request_visible=s->request; s->volume_edit=false; }
 else if(s->stage==0) { s->muted=true; return ACTION_MUTE; }
 return ACTION_NONE;
}
action_t controller_release(controller_t *s,int key,int64_t now) {
 if(s->key!=key) return ACTION_NONE;
 action_t a=controller_tick(s,now);
 bool short_press=!s->consumed; s->key=-1;
 if(!short_press) return a;
 if(s->request_visible && (!s->online || now>=s->expires))return ACTION_NONE;
 if(key!=2) {
  if(s->request_visible) {
   if(s->stage==0 && ((key==0 && s->can_allow) || (key==1 && s->can_deny))) s->selected=key;
   else if(s->stage==1) {
    if(key==0) { s->stage=0; s->selected=-1; }
    else { s->muted=true; return ACTION_MUTE; }
   }
  } else if(s->reset_stage) { s->reset_stage=0;
  } else if(s->page==3 && s->volume_edit) {
   int previous=s->volume; s->volume=sound_volume_step(s->volume,key==0?1:-1);
   if(s->volume!=previous)return ACTION_PREVIEW_AUDIO;
  } else if(s->page==3 || s->page==4) {
   int count=s->page==3?6:(s->history_count?s->history_count:1);
   s->option=(s->option+(key==0?-1:1)+count)%count;
  } else turn(s,key==0?-1:1);
 } else if(s->request_visible && s->stage==0) {
  if((s->selected==1 && s->can_deny) || (s->selected==0 && s->can_allow)) s->stage=1;
  else if(!s->can_allow && !s->can_deny) { s->muted=true; return ACTION_MUTE; }
 } else if(!s->request_visible && s->page==3) {
  if(s->option==0) { s->sound=!s->sound; if(s->sound)return ACTION_PREVIEW_AUDIO; }
  else if(s->option==1)return ACTION_TEST_AUDIO;
  else if(s->option==2) { s->muted=true; return ACTION_MUTE; }
  else if(s->option==3) s->volume_edit=!s->volume_edit;
  else if(s->option==4) s->interval=s->interval==30?60:s->interval==60?120:30;
  else s->page=0;
 } else if(!s->request_visible && s->page==2) {
  if(s->online && s->resets>0 && *s->reset_id && s->reset_stage<2)s->reset_stage++;
 } else if(!s->request_visible && s->page==5) { return ACTION_PAIR;
 } else if(!s->request_visible && s->page==0) { s->delight_until=now+1200; return ACTION_TOUCH; }
 return ACTION_NONE;
}

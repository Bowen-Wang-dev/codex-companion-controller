#include "controller.h"
#include "sound.h"
#include "network.h"
#include "battery.h"
#include "bsp_i2c.h"
#include "esp_system.h"
#include "bsp_button.h"
#include "bsp_display.h"
#include "driver/usb_serial_jtag.h"
#include "esp_timer.h"
#include "esp_random.h"
#include "esp_log.h"
#include "esp_heap_caps.h"
#include "freertos/FreeRTOS.h"
#include "freertos/queue.h"
#include "freertos/task.h"
#include "cJSON.h"
#include "lvgl.h"
#include <stdio.h>
#include <inttypes.h>
#include <string.h>
#include <time.h>
#include <sys/time.h>
LV_FONT_DECLARE(ui_font)
#include <stdatomic.h>

#if __has_include("pet_assets.h")
#include "pet_assets.h"
#define HAVE_PETS 1
#else
#define HAVE_PETS 0
#endif

static controller_t s;
typedef struct { int key; bool down; int64_t at; } key_event_t;
static QueueHandle_t keys;
static atomic_bool queue_lost;
static char boot[17], rx[4096];
static size_t rx_len;
static bool rx_overflow;
static int reminders;
static int64_t next_reminder, last_render, last_hello;
static int64_t now_ms(void) { return esp_timer_get_time()/1000; }
static void button(bsp_btn_t btn,bsp_btn_ev_t event,void *arg) {
 if(event!=BSP_BTN_PRESS && event!=BSP_BTN_RELEASE) return;
 key_event_t e={btn,event==BSP_BTN_PRESS,now_ms()};
 if(xQueueSend(keys,&e,0)!=pdTRUE) atomic_store(&queue_lost,true);
}
static const char *text(cJSON *o,const char *key) {
 cJSON *x=cJSON_GetObjectItemCaseSensitive(o,key); return cJSON_IsString(x)?x->valuestring:"";
}
static int number(cJSON *o,const char *key,int fallback) {
 cJSON *x=cJSON_GetObjectItemCaseSensitive(o,key); return cJSON_IsNumber(x)?x->valueint:fallback;
}
static void send_json(cJSON *o) {
 cJSON_AddStringToObject(o,"boot",boot);
 char *line=cJSON_PrintUnformatted(o);
 if(line) {
  // Single main task owns TX; bounded writes never block button/audio tasks indefinitely.
  const char *kind=text(o,"type");
  network_send(line,!strcmp(kind,"decision") || !strcmp(kind,"reset") || !strcmp(kind,"meter_reset") || !strcmp(kind,"review_page"));
  char frame[512]; int len=snprintf(frame,sizeof(frame),"PC1 %s\n",line);
  if(len>0 && len<sizeof(frame)) usb_serial_jtag_write_bytes(frame,len,pdMS_TO_TICKS(10));
  cJSON_free(line);
 }
 cJSON_Delete(o);
}
static void hello(void) {
 cJSON *o=cJSON_CreateObject(); cJSON_AddStringToObject(o,"type","hello");
 cJSON_AddStringToObject(o,"firmware","0.2.10"); cJSON_AddBoolToObject(o,"assets",HAVE_PETS);
 cJSON_AddBoolToObject(o,"readonly_notices",true);
 cJSON_AddBoolToObject(o,"prehook_review",true);
 cJSON_AddBoolToObject(o,"user_input_notices",true);
 cJSON_AddNumberToObject(o,"review_protocol",1);
 cJSON_AddBoolToObject(o,"review_jumps",true);
 cJSON_AddNumberToObject(o,"battery",battery_percent());
 sound_health_t audio=sound_health();
 cJSON_AddStringToObject(o,"audio_state",audio.state==SOUND_READY?"ready":audio.state==SOUND_ERROR?"error":"starting");
 cJSON_AddNumberToObject(o,"audio_error",audio.error);
 cJSON_AddNumberToObject(o,"audio_samples",audio.samples);
 cJSON_AddNumberToObject(o,"audio_played",audio.played);
 cJSON_AddNumberToObject(o,"audio_start_delay_ms",audio.start_delay_ms);
 cJSON_AddNumberToObject(o,"audio_max_feed_gap_ms",audio.max_feed_gap_ms);
 cJSON_AddBoolToObject(o,"sound_enabled",s.sound);
 cJSON_AddNumberToObject(o,"sound_volume",s.volume);
 unsigned drops, failures; int reason, phase;
 network_diagnostics(&drops,&reason,&failures,&phase);
 int diagnostics[]={(int)drops,reason,(int)failures,phase};
 cJSON_AddItemToObject(o,"net",cJSON_CreateIntArray(diagnostics,4));
 int error,code,duration;network_http_diagnostics(&error,&code,&duration);
 int http_diagnostics[]={error,code,duration};
 cJSON_AddItemToObject(o,"net_io",cJSON_CreateIntArray(http_diagnostics,3));
 cJSON_AddNumberToObject(o,"free_heap",esp_get_free_heap_size());
 cJSON_AddNumberToObject(o,"largest_heap",heap_caps_get_largest_free_block(MALLOC_CAP_8BIT)); send_json(o);
}
static void action(action_t a) {
 if(a==ACTION_TEST_AUDIO || a==ACTION_PREVIEW_AUDIO || a==ACTION_TOUCH) {
  sound_volume(s.volume); sound_mute(!s.sound);
  sound_play(a==ACTION_TEST_AUDIO?SOUND_PERMISSION:a==ACTION_TOUCH?SOUND_TOUCH:SOUND_PREVIEW); return;
 }
 if(a==ACTION_PAIR) { network_arm(); return; }
 if(a==ACTION_RESET) {
  cJSON *o=cJSON_CreateObject(); cJSON_AddStringToObject(o,"type","reset");
  cJSON_AddStringToObject(o,"epoch",s.epoch); cJSON_AddStringToObject(o,"id",s.reset_id); send_json(o); return;
 }
 if(a==ACTION_METER_RESET) {
  cJSON *o=cJSON_CreateObject(); cJSON_AddStringToObject(o,"type","meter_reset");
  cJSON_AddStringToObject(o,"epoch",s.epoch); cJSON_AddStringToObject(o,"meter_id",s.meter_id);
  send_json(o);return;
 }
 if(a==ACTION_MUTE || a==ACTION_MAC) { sound_cancel_permission(); return; }
 if(a==ACTION_REVIEW) {
  cJSON *o=cJSON_CreateObject(); cJSON_AddStringToObject(o,"type","review_page");
  cJSON_AddStringToObject(o,"epoch",s.epoch); cJSON_AddStringToObject(o,"id",s.id);
  cJSON_AddStringToObject(o,"digest",s.digest); cJSON_AddNumberToObject(o,"review_page",s.review_page);
  send_json(o); return;
 }
 if(a==ACTION_DISMISS) {
  sound_cancel_permission();
  cJSON *o=cJSON_CreateObject(); cJSON_AddStringToObject(o,"type","dismiss");
  cJSON_AddStringToObject(o,"epoch",s.epoch); cJSON_AddStringToObject(o,"id",s.id);
  cJSON_AddStringToObject(o,"digest",s.digest); send_json(o); return;
 }
 if(a!=ACTION_ALLOW && a!=ACTION_DENY) return;
 cJSON *o=cJSON_CreateObject(); cJSON_AddStringToObject(o,"type","decision");
 cJSON_AddStringToObject(o,"epoch",s.epoch); cJSON_AddStringToObject(o,"id",s.id);
 cJSON_AddStringToObject(o,"digest",s.digest);
 cJSON_AddStringToObject(o,"choice",a==ACTION_ALLOW?"allow":"deny");
 if(s.review_protocol==1)cJSON_AddNumberToObject(o,"review_page",s.review_page);
 send_json(o);
 snprintf(s.receipt,sizeof(s.receipt),"Sent; waiting for Mac");
}
static void snapshot(cJSON *o) {
 if(strcmp(text(o,"type"),"snapshot") || strcmp(text(o,"boot"),boot)) return;
 const char *epoch=text(o,"epoch");
 if(!*epoch || strlen(epoch)>=sizeof(s.epoch)) return;
 double seq=0; cJSON *v=cJSON_GetObjectItemCaseSensitive(o,"seq");
 if(!cJSON_IsNumber(v) || (seq=v->valuedouble)<1 || seq>UINT32_MAX) return;
 if(strcmp(s.epoch,epoch)) {
  controller_cancel_input(&s); controller_request(&s,""); s.sequence=0;
  snprintf(s.epoch,sizeof(s.epoch),"%s",epoch);
 }
 if(seq<=s.sequence) return;
 s.sequence=(uint32_t)seq; s.last_rx=now_ms(); s.online=true;
 const char *state=text(o,"state");
 if(strcmp(state,s.state)) {
  if(!strcmp(state,"completed"))sound_play(SOUND_COMPLETED);
  else if(!strcmp(state,"failed"))sound_play(SOUND_FAILED);
  else if(!strcmp(state,"denied"))sound_play(SOUND_DENIED);
  else if(!strcmp(state,"exhausted"))sound_play(SOUND_EXHAUSTED);
 }
 snprintf(s.state,sizeof(s.state),"%s",state);
 s.primary=number(o,"primary",-1); s.secondary=number(o,"secondary",-1);
 s.resets=number(o,"resets",-1);
 snprintf(s.billing,sizeof(s.billing),"%s",text(cJSON_GetObjectItem(o,"provider"),"billing"));
 snprintf(s.token_model,sizeof(s.token_model),"%.63s",text(cJSON_GetObjectItem(o,"provider"),"active_model"));
 snprintf(s.model_source,sizeof(s.model_source),"%.15s",text(cJSON_GetObjectItem(o,"provider"),"model_source"));
 cJSON *tu=cJSON_GetObjectItem(o,"token_usage"),*tc=cJSON_GetObjectItem(o,"token_cost");
 if(!*s.token_model)snprintf(s.token_model,sizeof(s.token_model),"%.63s",text(tu,"model"));
 s.token_updated=cJSON_IsTrue(cJSON_GetObjectItem(tu,"updated"));
 s.token_total_updated=cJSON_IsTrue(cJSON_GetObjectItem(tu,"total_updated"));
 s.token_priced=cJSON_IsTrue(cJSON_GetObjectItem(tc,"priced"));
 const char *meter=text(tu,"meter_id");
 if(strcmp(meter,s.meter_id))s.meter_stage=0;
 snprintf(s.meter_id,sizeof(s.meter_id),"%s",meter);
 snprintf(s.token_cost_status,sizeof(s.token_cost_status),"%s",text(tc,"last_status"));
 snprintf(s.token_total_status,sizeof(s.token_total_status),"%s",text(tc,"total_status"));
 snprintf(s.token_cost_currency,sizeof(s.token_cost_currency),"%.7s",text(tc,"currency"));
 s.token_cost_last=cJSON_IsNumber(cJSON_GetObjectItem(tc,"last"))?cJSON_GetObjectItem(tc,"last")->valuedouble:-1;
 s.token_cost_total=cJSON_IsNumber(cJSON_GetObjectItem(tc,"total"))?cJSON_GetObjectItem(tc,"total")->valuedouble:-1;
 const char *token_fields[]={"inputTokens","cachedInputTokens","cacheWriteInputTokens","outputTokens","reasoningOutputTokens","totalTokens"};
 for(int k=0;k<6;k++) {
  cJSON *last=cJSON_GetObjectItem(tu,"last"),*total=cJSON_GetObjectItem(tu,"total");
  cJSON *a=cJSON_GetObjectItem(last,token_fields[k]),*z=cJSON_GetObjectItem(total,token_fields[k]);
  s.token_last[k]=cJSON_IsNumber(a)&&a->valuedouble>=0&&a->valuedouble<=1.0e12?(uint64_t)a->valuedouble:0;
  s.token_total[k]=cJSON_IsNumber(z)&&z->valuedouble>=0&&z->valuedouble<=1.0e12?(uint64_t)z->valuedouble:0;
 }
 s.minutes[0]=number(o,"primary_mins",0); s.minutes[1]=number(o,"secondary_mins",0);
 cJSON *utc=cJSON_GetObjectItemCaseSensitive(o,"utc");
 if(cJSON_IsNumber(utc) && utc->valuedouble>1700000000) { s.utc=(int64_t)utc->valuedouble; s.clock_at=now_ms(); struct timeval wall={.tv_sec=s.utc}; settimeofday(&wall,NULL); }
 int offset=number(o,"utc_offset",0); if(offset>=-50400 && offset<=50400)s.utc_offset=offset;
 s.resets_at[0]=(int64_t)number(o,"primary_reset",0); s.resets_at[1]=(int64_t)number(o,"secondary_reset",0);
 const char *id=text(o,"req_id"); int ttl=number(o,"ttl",0);
 if(strlen(id)>=sizeof(s.id) || ttl<=0 || ttl>120) id="";
 bool changed=strcmp(s.id,id)!=0;
 if(!changed && *id && strcmp(s.digest,text(o,"digest")))controller_cancel_input(&s);
 controller_request(&s,id);
 if(s.request) {
  s.expires=now_ms()+ttl*1000;
  snprintf(s.digest,sizeof(s.digest),"%s",text(o,"digest"));
  snprintf(s.command,sizeof(s.command),"%s",text(o,"command"));
  snprintf(s.project,sizeof(s.project),"%s",text(o,"project"));
  snprintf(s.scope,sizeof(s.scope),"%s",text(o,"scope"));
  s.can_allow=cJSON_IsTrue(cJSON_GetObjectItem(o,"can_allow"));
  s.can_deny=!cJSON_IsFalse(cJSON_GetObjectItem(o,"can_deny"));
  if(number(o,"review_protocol",0)==1) {
   // Malformed, clipped, or stale pages must never unlock a decision.
   if(s.review_protocol!=1) { controller_cancel_input(&s);s.review_protocol=1;s.review_loaded=-1; }
   cJSON *page=cJSON_GetObjectItem(o,"review_page"),*total=cJSON_GetObjectItem(o,"review_total");
   if(cJSON_IsNumber(page) && cJSON_IsNumber(total) && page->valuedouble==page->valueint && total->valuedouble==total->valueint)
    controller_review_snapshot(&s,page->valueint,total->valueint,text(o,"review_text"));
   if(!controller_review_final(&s)) { s.can_allow=false;s.can_deny=false; }
  } else if(s.review_protocol==1) { s.can_allow=false;s.can_deny=false;controller_cancel_input(&s); }
  bool user_input=!strcmp(text(o,"request_kind"),"user_input");
  if(s.user_input!=user_input)controller_cancel_input(&s);
  s.user_input=user_input;
  if(s.user_input) { s.can_allow=false; s.can_deny=false; }
  bool mac_confirm=!strcmp(text(o,"action_mode"),"mac_confirm");
  if(s.mac_confirm!=mac_confirm) { controller_cancel_input(&s);s.mac_confirm=mac_confirm; }
  if(changed) { reminders=0; next_reminder=now_ms()+s.interval*1000; sound_volume(s.volume); sound_mute(!s.sound); sound_play(SOUND_PERMISSION); }
 }
 snprintf(s.receipt,sizeof(s.receipt),"%s",text(o,"receipt"));
 snprintf(s.reset_status,sizeof(s.reset_status),"%s",text(o,"reset_status"));
 if(strcmp(s.reset_id,text(o,"reset_id")))s.reset_stage=0;
 snprintf(s.reset_id,sizeof(s.reset_id),"%s",text(o,"reset_id"));
 snprintf(s.usage_status,sizeof(s.usage_status),"%s",text(o,"usage_status"));
 if(strcmp(s.face,text(o,"face")) && !strcmp(text(o,"face"),"delight"))sound_play(SOUND_ALLOWED);
 snprintf(s.face,sizeof(s.face),"%s",text(o,"face"));
 snprintf(s.transport,sizeof(s.transport),"%s",text(o,"transport"));
 snprintf(s.hook_status,sizeof(s.hook_status),"%s",text(o,"hook_status"));
 cJSON *history=cJSON_GetObjectItem(o,"history"); s.history_count=0;
 if(cJSON_IsArray(history))for(int i=0;i<cJSON_GetArraySize(history)&&i<8;i++) {
  cJSON *item=cJSON_GetArrayItem(history,i); if(cJSON_IsString(item))snprintf(s.history[s.history_count++],96,"%s",item->valuestring);
 }
 if(s.option>=s.history_count && s.page==4)s.option=0;
}
static void receive(void) {
 char chunk[128]; int n=usb_serial_jtag_read_bytes(chunk,sizeof(chunk),0);
 for(int i=0;i<n;i++) {
  char c=chunk[i];
  if(c=='\n') {
   if(!rx_overflow && rx_len>4 && !memcmp(rx,"PC1 ",4)) {
    rx[rx_len]=0; cJSON *o=cJSON_Parse(rx+4); if(o) {
     if(!strcmp(text(o,"type"),"provision")) {
      bool ok=network_provision(o); cJSON *reply=cJSON_CreateObject(); cJSON_AddStringToObject(reply,"type","provisioned"); cJSON_AddBoolToObject(reply,"ok",ok); send_json(reply);
      if(ok) { usb_serial_jtag_wait_tx_done(pdMS_TO_TICKS(500)); esp_restart(); }
     } else snapshot(o); cJSON_Delete(o);
    }
   }
   rx_len=0; rx_overflow=false;
  } else if(!rx_overflow) {
   if(rx_len<sizeof(rx)-1)rx[rx_len++]=c; else { rx_overflow=true; rx_len=0; }
  }
 }
}
static lv_obj_t *label(lv_obj_t *root,int x,int y,int w,const char *str,int color,int size) {
 lv_obj_t *l=lv_label_create(root); lv_obj_set_pos(l,x,y); lv_obj_set_width(l,w);
 lv_label_set_text(l,str); lv_obj_set_style_text_color(l,lv_color_hex(color),0);
 lv_obj_set_style_text_font(l,&ui_font,0);
 return l;
}
static void battery_indicator(lv_obj_t *root) {
 int value=battery_percent();
 int color=value<0?0x92a6b9:value<=10?0xff6969:value<=20?0xffbf5c:0x8bf0cd;
 char percent[16]; if(value<0)snprintf(percent,sizeof(percent),"—"); else snprintf(percent,sizeof(percent),"%d%%",value);
 lv_obj_t *number=label(root,147,12,49,percent,color,12);
 lv_obj_set_style_text_align(number,LV_TEXT_ALIGN_RIGHT,0);
 lv_obj_t *body=lv_obj_create(root); lv_obj_remove_style_all(body);
 lv_obj_set_pos(body,202,14); lv_obj_set_size(body,24,13);
 lv_obj_set_style_border_width(body,1,0); lv_obj_set_style_border_color(body,lv_color_hex(color),0); lv_obj_set_style_radius(body,2,0);
 lv_obj_remove_flag(body,LV_OBJ_FLAG_SCROLLABLE);
 lv_obj_t *cap=lv_obj_create(root); lv_obj_remove_style_all(cap);
 lv_obj_set_pos(cap,227,18); lv_obj_set_size(cap,2,5);
 lv_obj_set_style_bg_color(cap,lv_color_hex(color),0); lv_obj_set_style_bg_opa(cap,255,0);
 if(value>0) {
  int width=(18*value+99)/100;
  lv_obj_t *fill=lv_obj_create(body); lv_obj_remove_style_all(fill);
  lv_obj_set_pos(fill,2,2); lv_obj_set_size(fill,width,7);
  lv_obj_set_style_bg_color(fill,lv_color_hex(color),0); lv_obj_set_style_bg_opa(fill,255,0);
 }
}
static void bar(lv_obj_t *r,int y,int remaining) {
 for(int i=0;i<10;i++) {
  lv_obj_t *v=lv_obj_create(r); lv_obj_remove_style_all(v); lv_obj_set_pos(v,16+i*21,y);
  lv_obj_set_size(v,18,6); lv_obj_set_style_bg_color(v,lv_color_hex(0x263039),0); lv_obj_set_style_bg_opa(v,255,0);
  if(remaining>i*10) {
   int w=(remaining-i*10)>=10?18:(remaining-i*10)*18/10;
   lv_obj_t *fill=lv_obj_create(v); lv_obj_remove_style_all(fill); lv_obj_set_size(fill,w,6);
   lv_obj_set_style_bg_color(fill,lv_color_hex(remaining<=20?0xffbf5c:0x8bf0cd),0); lv_obj_set_style_bg_opa(fill,255,0);
  }
 }
}
static void quota(lv_obj_t *r,int index,int y) {
 char b[64]; int value=index?s.secondary:s.primary;
 const char *window=s.minutes[index]==300?"5 小时":s.minutes[index]==10080?"7 天":"额度窗口";
 if(value<0)snprintf(b,sizeof(b),"%s：等待同步",window);
 else snprintf(b,sizeof(b),"%s  剩余 %d%%",window,value);
 label(r,16,y,210,b,0xc7d7e5,12); bar(r,y+20,value);
}
static void token_count(char *out,size_t size,uint64_t value) {
 static const char suffixes[]=" KMGTP";
 double scaled=(double)value;
 unsigned tier=0;
 while(scaled>=1000.0 && tier<5){scaled/=1000.0;tier++;}
 if(tier)snprintf(out,size,"%.2f%c",scaled,suffixes[tier]);
 else snprintf(out,size,"%" PRIu64,value);
}
static const char *token_cost_hint(bool total) {
 const char *status=total?s.token_total_status:s.token_cost_status;
 if(!strcmp(status,"waiting_usage"))return "费率已配置 · 等待用量";
 if(!strcmp(status,"model_unknown"))return "模型未识别 · 费用待确认";
 if(!strcmp(status,"cache_write_rate_missing"))return "缓存写入费率未配置";
 if(!strcmp(status,"model_rate_missing"))return "此模型费率未配置";
 return s.token_priced?"费率已配置 · 等待用量":"请在 Mac 检查费率";
}
static void token_cost_text(char *out,size_t size,const char *prefix,double value) {
 if(!strcmp(s.token_cost_currency,"USD"))snprintf(out,size,"%s$%.4f",prefix,value);
 else snprintf(out,size,"%s%s %.4f",prefix,s.token_cost_currency,value);
}
#if HAVE_PETS
static const char *pet_state(void) {
 if(s.request_visible)return "permission";
 if(!strcmp(s.state,"failed") || !strcmp(s.state,"denied"))return "crying";
 if(!strcmp(s.state,"exhausted"))return "exhausted";
 if(!strcmp(s.face,"crying"))return "crying";
 if(!strcmp(s.face,"delight"))return "delight";
 if(s.delight_until>now_ms())return "delight";
 if(!strcmp(s.state,"working") || !strcmp(s.state,"approval_sent"))return "working";
 if(!strcmp(s.state,"completed"))return "completed";
 return "idle";
}
#endif
static void reset_countdown(char *out,size_t size,int index) {
 if(!s.utc || !s.resets_at[index]) { snprintf(out,size,"等待同步"); return; }
 int64_t left=s.resets_at[index]-s.utc-(now_ms()-s.clock_at)/1000;
 if(left<=0) { snprintf(out,size,"等待额度更新"); return; }
 if(left>=86400)snprintf(out,size,"%lld天 %02lld:%02lld",(long long)(left/86400),(long long)(left%86400/3600),(long long)(left%3600/60));
 else snprintf(out,size,"%02lld:%02lld:%02lld",(long long)(left/3600),(long long)(left%3600/60),(long long)(left%60));
}
static void render(void) {
 if(!bsp_lvgl_lock(30))return;
 lv_obj_t *r=lv_screen_active(); lv_obj_clean(r);
 lv_obj_set_style_bg_color(r,lv_color_hex(0x000000),0); lv_obj_remove_flag(r,LV_OBJ_FLAG_SCROLLABLE);
 char b[256];
 if(s.utc) {
  time_t t=s.utc+(now_ms()-s.clock_at)/1000+s.utc_offset; struct tm local;
  // Mac sends its current UTC offset each snapshot, including DST changes.
  gmtime_r(&t,&local); strftime(b,sizeof(b),"%H:%M",&local);
 } else snprintf(b,sizeof(b),"--:--");
 label(r,16,12,72,b,0xffffff,14);
 label(r,96,12,48,s.online?(!strcmp(s.transport,"wifi")?"Wi-Fi":"USB"):"离线",s.online?0x8bf0cd:0xffbf5c,12);
 battery_indicator(r);
 if(s.request_visible) {
  label(r,16,42,144,s.user_input?"等待你回复":s.review_protocol==1?s.command:"权限请求",0xffbf5c,14);
#if HAVE_PETS
  lv_obj_t *face=lv_image_create(r); lv_image_set_src(face,pet_asset("permission"));
  lv_image_set_scale(face,128); lv_obj_set_pos(face,144,20);
#endif
  if(s.handling_on_mac) {
   label(r,16,106,210,"请在 Mac 处理此请求",0xffffff,16);
   label(r,16,150,210,"在 App 的审批窗口\n查看详情并允许或拒绝。\n设备提醒已静音。",0x92a6b9,14);
   label(r,16,226,210,"尚未提交允许或拒绝",0xffbf5c,14);
   label(r,16,277,210,"短按确认：返回设备审阅\n长按上/下：详情首/末页",0x92a6b9,12);
  } else if(s.stage==1) {
   label(r,16,106,210,s.selected==0?(s.mac_confirm?"在 Mac 确认本次权限？":"确认批准本次请求？"):"确认拒绝本次请求？",0xffffff,14);
   label(r,16,150,210,"释放按键后，\n长按确认 1 秒提交。",0xffbf5c,14);
   label(r,16,212,210,s.command,0xffffff,12);
   label(r,16,277,210,s.review_protocol==1?"长按上/下：取消并回首/末页\n长按确认：提交当前选择":"上键取消 · 下键静音\n长按方向键离开",0x92a6b9,12);
  } else if(s.review_protocol==1) {
   bool ready=s.review_loaded==s.review_page;
   if(!controller_review_final(&s)) {
    if(s.review_page==s.review_total)snprintf(b,sizeof(b),"正在读取确认页");
    else snprintf(b,sizeof(b),"请求详情 %d / %d",s.review_page+1,s.review_total);
    label(r,16,94,210,b,0x8bf0cd,14);
    lv_obj_t *body=label(r,16,120,210,ready?s.review_text:"正在读取本页…",0xffffff,16);
    lv_obj_set_style_text_line_space(body,2,0);lv_obj_set_height(body,160);
    label(r,16,277,210,"长按上/下：首/末页\n长按确认：转到 Mac 处理",0x92a6b9,12);
   } else {
    label(r,16,94,210,s.user_input?"请在 Mac 回复此问题":"请选择本次操作",0x8bf0cd,16);
    label(r,16,131,210,s.scope,0x92a6b9,14);
    label(r,16,190,210,"建议先在 Mac 查看\n长按确认：转到 Mac 处理",0xffbf5c,14);
    label(r,16,247,210,s.stage==2?"已发送，等待回执":s.user_input?"按确认：标记已读":s.selected==0?"> 允许 · 按确认继续":s.selected==1?"> 拒绝 · 按确认继续":s.can_allow?"上键允许 · 下键拒绝":"请在 Mac 审阅 · 下键拒绝",0xffffff,14);
    label(r,16,291,210,s.user_input?"已读不会代替你的回复":"长按上键：返回详情开头",0x92a6b9,12);
   }
  } else {
   lv_obj_t *command=label(r,16,94,210,s.command,0xffffff,12); lv_obj_set_height(command,36);
   lv_obj_t *project=label(r,16,130,210,s.project,0x92a6b9,12); lv_obj_set_height(project,120);
   lv_obj_t *scope=label(r,16,254,210,s.scope,0x92a6b9,12); lv_obj_set_height(scope,36);
   if(s.stage==2) label(r,16,294,210,"已发送，等待处理",0xffbf5c,12);
   else label(r,16,294,210,s.user_input?"在 Mac 回复 · 确认已读":!s.can_deny?"在 Mac 确认 · 按确认静音":s.selected==1?"> 拒绝 · 确认继续":s.selected==0?(s.mac_confirm?"> 在 Mac 确认":"> 批准 · 确认继续"):s.mac_confirm?"上到 Mac · 下拒绝":s.can_allow?"上批准 · 下拒绝":"需 Mac 审阅 · 下键拒绝",0xffffff,14);
  }

 } else if(s.page==0) {
#if HAVE_PETS
  const lv_image_dsc_t *pet=pet_asset(pet_state());
  if(pet) { lv_obj_t *im=lv_image_create(r); lv_image_set_src(im,pet); lv_obj_set_pos(im,72,44); }
#else
  label(r,34,60,180,"宠物图片未导入",0x92a6b9,20);
#endif
  const char *state=!s.online?"连接已断开":!strcmp(s.state,"working")?"正在思考 / 工作":!strcmp(s.state,"approval_sent")?"批准待回执":!strcmp(s.state,"denied")?"权限已拒绝":!strcmp(s.state,"failed")?"任务失败":!strcmp(s.state,"completed")?"本轮已结束":!strcmp(s.state,"exhausted")?"额度已耗尽":"待机 · 等待事件";
  label(r,16,148,210,!strcmp(s.face,"delight")?s.receipt:state,0xffffff,18);
  if(!strcmp(s.billing,"token")) {
   if(s.token_updated) {
    char count[32];token_count(count,sizeof(count),s.token_last[5]);snprintf(b,sizeof(b),"本轮  %s",count);label(r,16,181,210,b,0x8bf0cd,13);
    token_count(count,sizeof(count),s.token_total[5]);snprintf(b,sizeof(b),"累计  %s",count);label(r,16,203,210,b,0xffffff,13);
   } else label(r,16,181,210,"等待 Token 用量",0x92a6b9,13);
   snprintf(b,sizeof(b),"模型 · %.35s%s",*s.token_model?s.token_model:"等待同步",!strcmp(s.model_source,"manual")?" · 手动":"");
   label(r,16,225,210,b,0x92a6b9,10);
   if(s.token_cost_last>=0)token_cost_text(b,sizeof(b),"约 ",s.token_cost_last);
   else snprintf(b,sizeof(b),"%s",token_cost_hint(false));
   label(r,16,245,210,b,0x92a6b9,12);
  } else {
   quota(r,0,183); quota(r,1,221);
   char countdown[64]; reset_countdown(countdown,sizeof(countdown),0);
   label(r,16,253,140,countdown,0x92a6b9,12);
   if(s.resets>=0)snprintf(b,sizeof(b),"额外%d次",s.resets); else snprintf(b,sizeof(b),"额外—");
   label(r,164,253,62,b,0x8bf0cd,12);
  }
  if(strcmp(s.billing,"token") && (s.primary==0 || s.secondary==0 || !strcmp(s.state,"exhausted"))) label(r,16,277,210,"上键：前往重置 · 或等待",0xffbf5c,12);
  else label(r,16,277,210,s.request?"长按确认：返回权限请求":"确认：摸摸宠物",0x92a6b9,12);
 } else if(s.page==1 && !strcmp(s.billing,"token")) {
  label(r,16,42,210,"累计 Token · 自清零",0xffffff,18);
  if(s.meter_stage) {
   label(r,16,84,210,s.meter_stage==2?"已发送 · 等待回执":"确认清零 Token？",0xffbf5c,16);
   label(r,16,126,210,"仅清除控制器计数与估价\n保留 Codex 聊天和账单",0xffffff,13);
   label(r,16,212,210,s.meter_stage==2?"请等待 Bridge 确认":"松开后长按确认 1 秒\n方向键取消",0x92a6b9,13);
  } else {
  if(!s.token_total_updated) label(r,16,78,210,"等待 Codex 用量事件",0xffbf5c,13);
  else {
   const char *names[]={"输入含缓存","缓存读取","缓存写入","输出含推理","其中推理","总计"};
   for(int k=0;k<6;k++) { char count[32];token_count(count,sizeof(count),s.token_total[k]);snprintf(b,sizeof(b),"%s   %s",names[k],count); label(r,16,77+k*27,210,b,0xffffff,13); }
  }
  if(s.token_cost_total>=0) { token_cost_text(b,sizeof(b),"累计估价  ",s.token_cost_total);label(r,16,250,210,b,0x8bf0cd,12); }
  else label(r,16,250,210,token_cost_hint(true),0x92a6b9,11);
  label(r,16,277,210,s.request?"请先处理权限请求":"确认：打开清零确认",0x92a6b9,12);
  }
 } else if(s.page==1) {
  label(r,16,45,210,"额度窗口",0xffffff,20); quota(r,0,90); quota(r,1,180);
  reset_countdown(b,sizeof(b),0); label(r,16,128,210,b,0x92a6b9,12);
  reset_countdown(b,sizeof(b),1); label(r,16,218,210,b,0x92a6b9,12);
  label(r,16,260,210,s.usage_status,0x92a6b9,12);

 } else if(s.page==2 && !strcmp(s.billing,"token")) {
  label(r,16,42,210,"最近一轮 Token",0xffffff,18);
  if(!s.token_updated) label(r,16,78,210,"等待 Codex 用量事件",0xffbf5c,13);
  else {
   const char *names[]={"输入含缓存","缓存读取","缓存写入","输出含推理","其中推理","总计"};
   for(int k=0;k<6;k++) { char count[32];token_count(count,sizeof(count),s.token_last[k]);snprintf(b,sizeof(b),"%s   %s",names[k],count); label(r,16,77+k*27,210,b,0xffffff,13); }
  }
  if(s.token_cost_last>=0) { token_cost_text(b,sizeof(b),"本轮估价  ",s.token_cost_last);label(r,16,250,210,b,0x8bf0cd,12); }
  else label(r,16,250,210,token_cost_hint(false),0x92a6b9,11);
  label(r,16,277,210,"本机请求估价 · 非后台账单",0x92a6b9,12);
 } else if(s.page==2) {
  label(r,16,45,210,"额外额度重置",0xffffff,20);
  if(s.resets>=0)snprintf(b,sizeof(b),"%d 次可用",s.resets); else snprintf(b,sizeof(b),"等待账户同步");
  label(r,16,90,210,b,0x8bf0cd,20);
  const char *hint=s.reset_stage==1?"将消耗 1 次额外重置。\n短按确认继续。\n方向键取消。":s.reset_stage==2?"最终确认：消耗 1 次\n释放按键后，\n长按确认 1 秒提交。":s.reset_stage==3?"已提交，等待官方结果":s.resets==0?"没有额外次数，\n可等待额度自动重置。":!s.online?"连接 Bridge 后操作":!*s.reset_id?"正在校验账户和次数":"确认：打开重置确认页\n也可以等待自然重置。";
  label(r,16,140,210,hint,0xffffff,14);
  label(r,16,243,210,s.reset_status,0xffbf5c,12);
 } else if(s.page==3) {
  label(r,16,42,210,"声音设置",0xffffff,20);
  snprintf(b,sizeof(b),"%c 提示音：%s\n%c 试听提示音\n%c 静音当前请求\n%c 音量：%d%%%s\n%c 提醒间隔：%d秒\n%c 返回主页",s.option==0?'>':' ',s.sound?"开":"关",s.option==1?'>':' ',s.option==2?'>':' ',s.option==3?'>':' ',s.volume,s.volume_edit?" · 调节中":"",s.option==4?'>':' ',s.interval,s.option==5?'>':' ');
  label(r,16,72,210,b,0xffffff,14);
  sound_health_t audio=sound_health();
  if(audio.state==SOUND_ERROR)snprintf(b,sizeof(b),"音频故障 0x%x",audio.error);
  else snprintf(b,sizeof(b),"%s",audio.state==SOUND_READY?"音频就绪":"音频初始化中");
  label(r,16,217,210,b,audio.state==SOUND_ERROR?0xffbf5c:0x92a6b9,12);
  label(r,16,253,210,s.volume_edit?"上加下减 10% · 确认退出\n范围 0%—100% · 长按换页":"短按方向键选择 · 确认修改\n长按方向键切换页面",0x92a6b9,12);
 } else if(s.page==4) {
  label(r,16,42,210,"事件记录",0xffffff,20);
  snprintf(b,sizeof(b),"%d / %d",s.history_count?s.option+1:0,s.history_count); label(r,16,76,210,b,0x8bf0cd,12);
  label(r,16,104,210,s.history_count?s.history[s.option]:"等待会话事件\n请在 Codex 信任项目 Hooks",0xffffff,14);
  label(r,16,253,210,"短按方向键浏览事件\n长按方向键切换页面",0x92a6b9,12);
 } else {
  label(r,16,42,210,"连接与配网",0xffffff,20);
  // Validated snapshots (matching boot/epoch/sequence) are the evidence that
  // Bridge is connected; the HTTP worker's transient phase is not UI status.
  label(r,16,78,210,s.online&&!network_pairing_armed()?(!strcmp(s.transport,"wifi")?"无线同步正常":"USB 同步正常"):network_status(),0x8bf0cd,14);
  if(s.online) {
   if(!strcmp(s.billing,"token")) {
    label(r,16,112,210,"第三方 API · Token 计费",0x92a6b9,12);
    snprintf(b,sizeof(b),"模型：%.28s",*s.token_model?s.token_model:"等待同步");
    label(r,16,141,210,b,0x92a6b9,11);
   } else label(r,16,112,210,s.usage_status,0x92a6b9,12);
   label(r,16,174,210,*s.hook_status?s.hook_status:"等待 Bridge 更新事件状态",0xffbf5c,12);
   label(r,16,224,210,"短按确认：允许 USB 重配\n配对窗口有效期为 60 秒",0x92a6b9,12);
  } else {
   label(r,16,136,210,"首次用 USB 安全配对。\n在 Mac 运行无线配置，\n随后即可拔掉数据线。\n\n短按确认：允许配对 60 秒",0x92a6b9,14);
   label(r,16,254,210,s.usage_status,0x92a6b9,12);
  }
 }

 snprintf(b,sizeof(b),"%c %c %c %c %c %c",s.page==0?'o':'.',s.page==1?'o':'.',s.page==2?'o':'.',s.page==3?'o':'.',s.page==4?'o':'.',s.page==5?'o':'.');
 label(r,84,300,100,s.request_visible?"":b,0x8bf0cd,12);
 bsp_lvgl_unlock();
}
void app_main(void) {
 vTaskPrioritySet(NULL,5);
 esp_log_level_set("*",ESP_LOG_NONE);
 controller_init(&s); snprintf(boot,sizeof(boot),"%08lx%08lx",(unsigned long)esp_random(),(unsigned long)esp_random());
 usb_serial_jtag_driver_config_t usb={.tx_buffer_size=1024,.rx_buffer_size=4096};
 ESP_ERROR_CHECK(usb_serial_jtag_driver_install(&usb));
 ESP_ERROR_CHECK(bsp_display_init()); if(!bsp_lvgl_init())abort();
 // BSP intentionally initializes PWM at 0%; the application must enable it.
 bsp_display_backlight(80);
 keys=xQueueCreate(12,sizeof(key_event_t)); if(!keys)abort();
 ESP_ERROR_CHECK(bsp_button_init(button,NULL));
 // Create the shared I2C bus once before starting audio/battery workers, so
 // concurrent initialization cannot create two owners of the same peripheral.
 if(bsp_i2c_init()==ESP_OK)battery_start();
 sound_start(); // Report initialization failures instead of a permanent silent UI.
 network_start();
 for(;;) {
  receive(); static char wireless[4096];
  if(network_receive(wireless,sizeof(wireless))) { cJSON *packet=cJSON_Parse(wireless); if(packet) { snapshot(packet); cJSON_Delete(packet); } }
  int64_t now=now_ms();
  if(atomic_exchange(&queue_lost,false)) { controller_cancel_input(&s); s.key=-1; }
  key_event_t e;
  while(xQueueReceive(keys,&e,0)==pdTRUE) {
   if(e.down)controller_press(&s,e.key,e.at); else action(controller_release(&s,e.key,e.at));
  }
  bool was_online=s.online; action(controller_tick(&s,now));
  static int64_t last_review_retry;
  if(s.request_visible && s.online && s.review_protocol==1 && s.review_loaded!=s.review_page && now-last_review_retry>=500) {
   action(ACTION_REVIEW);last_review_retry=now;
  }
  if(was_online && !s.online) { sound_mute(!s.sound); sound_play(SOUND_DISCONNECTED); }
  if(s.request && s.online && !s.muted && s.sound && reminders<3 && now>=next_reminder) {
   sound_play(SOUND_PERMISSION); reminders++; next_reminder=now+s.interval*1000;
  }
  sound_volume(s.volume);
  sound_mute(!s.sound);
  if(now-last_hello>=500) { hello(); last_hello=now; }
  static uint32_t rendered;static bool touched;
  uint32_t view=controller_view_hash(&s);bool touch=now<s.delight_until;
  if(now-last_render>=50 && (view!=rendered || touch!=touched || now-last_render>=1000)) {
   render();last_render=now;rendered=view;touched=touch;
  }
  vTaskDelay(pdMS_TO_TICKS(10));
 }
}

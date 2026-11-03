#include "../firmware/main/controller.h"
#include "../firmware/main/ui_language.h"
#include <assert.h>
#include <stdio.h>
#include <string.h>

int main(void) {
 controller_t state;controller_init(&state);
 assert(state.english==COMPANION_DEFAULT_ENGLISH);
 assert(!strcmp(device_language(),state.english?"en":"zh-CN"));
 assert(!strcmp(device_text(true,"确认批准本次请求？"),"Allow this request?"));
 assert(!strcmp(device_text(false,"确认批准本次请求？"),"确认批准本次请求？"));
 const char *path="/权限请求/用户原文";
 assert(device_text(true,path)==path);
 char line[64];snprintf(line,sizeof(line),device_text(true,"请求详情 %d / %d"),3,7);
 assert(!strcmp(line,"Request details 3 / 7"));
 snprintf(line,sizeof(line),device_text(true,"%s  剩余 %d%%"),device_text(true,"5 小时"),42);
 assert(!strcmp(line,"5 hours  42% left"));
 uint32_t before=controller_view_hash(&state);state.english=!state.english;
 assert(controller_view_hash(&state)!=before);
 puts("ui language: installed default, fallback, user data, formatting and redraw passed");
 return 0;
}

#include "../firmware/main/sound.h"
#include "audio_stubs/bsp_audio.h"
#include "audio_stubs/freertos/FreeRTOS.h"
#include "audio_stubs/freertos/queue.h"
#include <assert.h>
#include <setjmp.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
static sound_kind_t queued;
static int occupied,hardware_volume,init_calls,write_calls,init_fail,write_fail;
static int injected;
static const char *mode;
static void (*worker_entry)(void *);
static jmp_buf idle;
static int16_t captured[20000];
static size_t captured_count;
static int64_t clock_us;
int64_t esp_timer_get_time(void) { return clock_us; }
QueueHandle_t xQueueCreate(unsigned count,size_t size) { assert(count==1 && size==sizeof(queued));return &queued; }
int xQueuePeek(QueueHandle_t queue,void *item,uint32_t wait) {
 (void)queue;
 if(!occupied && wait==portMAX_DELAY)longjmp(idle,1);
 if(occupied)memcpy(item,&queued,sizeof(queued));return occupied;
}
int xQueueReceive(QueueHandle_t queue,void *item,uint32_t wait) {
 int result=xQueuePeek(queue,item,wait);occupied=0;return result;
}
int xQueueOverwrite(QueueHandle_t queue,const void *item) { (void)queue;memcpy(&queued,item,sizeof(queued));occupied=1;return pdTRUE; }
int xQueueReset(QueueHandle_t queue) { (void)queue;occupied=0;return pdTRUE; }
int xTaskCreate(void (*entry)(void *),const char *name,unsigned stack,void *arg,unsigned priority,void *handle) {
 (void)name;(void)stack;(void)arg;(void)handle;assert(priority>5);worker_entry=entry;return pdPASS;
}
esp_err_t bsp_audio_init(void) { init_calls++;return init_fail?ESP_FAIL:ESP_OK; }
esp_err_t bsp_audio_set_format(uint32_t hz,uint8_t bits,uint8_t channels) { assert(hz==16000 && bits==16 && channels==1 && hardware_volume==100);return ESP_OK; }
void bsp_audio_set_volume(uint8_t volume) { hardware_volume=volume; }
esp_err_t bsp_audio_write(const void *pcm,size_t bytes) {
 write_calls++;
 clock_us+=10000;
 if(write_fail)return ESP_FAIL;
 assert(captured_count+bytes/2<sizeof(captured)/sizeof(captured[0]));
 memcpy(captured+captured_count,pcm,bytes);captured_count+=bytes/2;
 if(!strcmp(mode,"priority")) {
  if(injected==0) { injected=1;sound_play(SOUND_PERMISSION); }
  else sound_play(SOUND_FAILED); // Lower-priority events must not replace pager.
 } else if(!strcmp(mode,"mute") && !injected) { injected=1;sound_mute(true); }
 else if(!strcmp(mode,"request_mute") && !injected) { injected=1;sound_cancel_permission(); }
 return ESP_OK;
}
static void run(void) { if(setjmp(idle)==0)worker_entry(NULL); }
int main(int argc,char **argv) {
 assert(argc==2);mode=argv[1];sound_start();sound_volume(20);
 if(!strcmp(mode,"init_error"))init_fail=1;
 if(!strcmp(mode,"write_error"))write_fail=1;
 if(!strcmp(mode,"zero"))sound_volume(0);
 sound_play(!strcmp(mode,"priority")?SOUND_COMPLETED:SOUND_PERMISSION);
 clock_us+=5000;
 if(!strcmp(mode,"pending_mute")) { sound_cancel_permission();sound_play(SOUND_PREVIEW); }
 if(!strcmp(mode,"pager"))sound_play(SOUND_COMPLETED); // Queued pager survives.
 run();sound_health_t health=sound_health();
 assert(health.start_delay_ms<=5 && health.max_feed_gap_ms==0);
 if(!strcmp(mode,"init_error") || !strcmp(mode,"write_error")) {
  assert(health.state==SOUND_ERROR && health.error==ESP_FAIL && health.samples==0);
  init_fail=write_fail=0;sound_play(SOUND_PERMISSION);run();health=sound_health();
  assert(init_calls>=2 && health.state==SOUND_READY && health.samples==12480 && health.played==1);
 } else if(!strcmp(mode,"priority"))assert(health.samples==12640 && health.played==1);
 else if(!strcmp(mode,"mute") || !strcmp(mode,"request_mute")) {
  assert(health.samples==160 && health.played==0);
  if(!strcmp(mode,"mute"))sound_mute(false);
  sound_play(SOUND_PREVIEW);run();health=sound_health();
  assert(health.samples==3040 && health.played==1);
 } else if(!strcmp(mode,"pending_mute"))assert(health.samples==2880 && health.played==1);
 else if(!strcmp(mode,"zero"))assert(health.samples==0 && health.played==0);
 else {
  assert(health.samples==12480 && health.played==1);
  for(int i=2880;i<4800;i++)assert(captured[i]==0);
  int peak=0;for(size_t i=0;i<captured_count;i++)if(abs(captured[i])>peak)peak=abs(captured[i]);
  assert(peak>3800);
 }
 assert(hardware_volume==100);
 printf("audio runtime: %s passed (actual worker with mocked BSP / RTOS)\n",mode);
}

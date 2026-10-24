#include "sound.h"
#include "bsp_audio.h"
#include "freertos/FreeRTOS.h"
#include "freertos/task.h"
#include "freertos/queue.h"
#include "esp_timer.h"
#include <stdatomic.h>
static QueueHandle_t queue;
static portMUX_TYPE queue_lock=portMUX_INITIALIZER_UNLOCKED;
static atomic_bool muted;
static atomic_int volume=20, active_priority, audio_state=SOUND_STARTING, audio_error;
static atomic_uint generation, written_samples, played;
static atomic_uint start_delay_ms, max_feed_gap_ms;
static int64_t queued_at;
static void maximum(atomic_uint *value,unsigned sample) {
 unsigned old=atomic_load(value);
 while(sample>old && !atomic_compare_exchange_weak(value,&old,sample)) {}
}
static bool ready(void) {
 if(atomic_load(&audio_state)==SOUND_READY)return true;
 esp_err_t error=bsp_audio_init();
 if(error==ESP_OK) {
  // Set the stored gain before open: BSP's checked set_format path then
  // verifies the codec-volume write instead of relying on a void setter.
  bsp_audio_set_volume(100); error=bsp_audio_set_format(16000,16,1);
 }
 if(error!=ESP_OK) {
  atomic_store(&audio_error,error); atomic_store(&audio_state,SOUND_ERROR); return false;
 }
 // Codec percent is a dB curve, not linear gain. Apply user volume once in PCM.
 atomic_store(&audio_error,ESP_OK); atomic_store(&audio_state,SOUND_READY); return true;
}
static bool tone(sound_note_t note,unsigned ticket,int64_t *last_write) {
 int16_t pcm[160]; int total=note.ms*16; sound_pcm_t synth={0};
 for(int pos=0;pos<total;pos+=160) {
  if(atomic_load(&muted) || ticket!=atomic_load(&generation))return false;
  int64_t started=esp_timer_get_time();
  if(*last_write)maximum(&max_feed_gap_ms,(unsigned)((started-*last_write)/1000));
  int count=total-pos<160?total-pos:160;
  sound_pcm(&synth,note.hz,total,pos,pcm,count,atomic_load(&volume));
  esp_err_t error=bsp_audio_write(pcm,count*sizeof(int16_t));
  *last_write=esp_timer_get_time();
  if(error!=ESP_OK) {
   atomic_store(&audio_error,error); atomic_store(&audio_state,SOUND_ERROR); return false;
  }
  atomic_fetch_add(&written_samples,(unsigned)count);
 }
 return true;
}
static void worker(void *arg) {
 (void)arg; (void)ready();
 for(;;) {
  sound_kind_t kind;
  if(xQueuePeek(queue,&kind,portMAX_DELAY)!=pdTRUE)continue;
  portENTER_CRITICAL(&queue_lock);
  if(xQueueReceive(queue,&kind,0)!=pdTRUE) { portEXIT_CRITICAL(&queue_lock); continue; }
  atomic_store(&active_priority,sound_priority(kind));
  unsigned ticket=atomic_load(&generation);
  atomic_store(&start_delay_ms,(unsigned)((esp_timer_get_time()-queued_at)/1000));
  portEXIT_CRITICAL(&queue_lock);
  if(!atomic_load(&muted) && atomic_load(&volume)>0 && ready()) {
   const sound_note_t *notes; size_t count=sound_notes(kind,&notes); bool complete=true;
   int64_t last_write=0;
   for(size_t i=0;i<count && complete;i++)complete=tone(notes[i],ticket,&last_write);
   if(complete)atomic_fetch_add(&played,1);
  }
  atomic_store(&active_priority,0);
 }
}
void sound_start(void) {
 queue=xQueueCreate(1,sizeof(sound_kind_t));
 // Refill DMA ahead of the app (5) and LVGL (4); I2S writes block/yield.
 // Wi-Fi's system task still has higher priority on the single-core C3.
 if(!queue || xTaskCreate(worker,"sound",4096,NULL,7,NULL)!=pdPASS) {
  atomic_store(&audio_error,ESP_ERR_NO_MEM); atomic_store(&audio_state,SOUND_ERROR);
 }
}
void sound_play(sound_kind_t kind) {
 if(!queue || kind<0 || kind>=SOUND_COUNT || atomic_load(&muted))return;
 portENTER_CRITICAL(&queue_lock);
 sound_kind_t pending; int priority=sound_priority(kind);
 bool occupied=xQueuePeek(queue,&pending,0)==pdTRUE;
 if(priority>=atomic_load(&active_priority) && (!occupied || priority>=sound_priority(pending))) {
  if(kind==SOUND_PERMISSION)atomic_fetch_add(&generation,1);
  queued_at=esp_timer_get_time();
  xQueueOverwrite(queue,&kind);
 }
 portEXIT_CRITICAL(&queue_lock);
}
void sound_mute(bool mute) {
 portENTER_CRITICAL(&queue_lock);
 if(mute && !atomic_exchange(&muted,true)) {
  atomic_fetch_add(&generation,1);
  if(queue)xQueueReset(queue);
 } else if(!mute)atomic_store(&muted,false);
 portEXIT_CRITICAL(&queue_lock);
}
void sound_cancel_permission(void) {
 if(!queue)return;
 portENTER_CRITICAL(&queue_lock);
 if(atomic_load(&active_priority)==sound_priority(SOUND_PERMISSION))atomic_fetch_add(&generation,1);
 sound_kind_t pending;
 if(xQueuePeek(queue,&pending,0)==pdTRUE && pending==SOUND_PERMISSION)xQueueReset(queue);
 portEXIT_CRITICAL(&queue_lock);
}
void sound_volume(int value) { atomic_store(&volume,value<0?0:value>100?100:value); }
sound_health_t sound_health(void) {
 return (sound_health_t){atomic_load(&audio_state),atomic_load(&audio_error),
                         atomic_load(&written_samples),atomic_load(&played),
                         atomic_load(&start_delay_ms),atomic_load(&max_feed_gap_ms)};
}

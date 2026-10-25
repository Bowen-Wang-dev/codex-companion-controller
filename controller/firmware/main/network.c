#include "network.h"
#include "esp_wifi.h"
#include "esp_event.h"
#include "esp_netif.h"
#include "esp_http_client.h"
#include "esp_timer.h"
#include "esp_system.h"
#include "nvs_flash.h"
#include "nvs.h"
#include "freertos/FreeRTOS.h"
#include "freertos/task.h"
#include "freertos/queue.h"
#include <string.h>
#include <stdio.h>
#include <stdlib.h>
#include <stdatomic.h>
#include <sys/time.h>
typedef struct { char ssid[33], password[65], url[160], token[65], cert[2048]; int64_t utc; } config_t;
static config_t config;
static QueueHandle_t incoming, outgoing;
static atomic_int status;
static atomic_bool wifi_ready;
static atomic_uint wifi_generation, wifi_disconnects, http_failures;
static atomic_int wifi_reason, http_phase;
static atomic_int http_error, http_code, http_duration_ms;
void network_http_diagnostics(int *error,int *code,int *duration_ms) {
 *error=atomic_load(&http_error);*code=atomic_load(&http_code);*duration_ms=atomic_load(&http_duration_ms);
}
void network_diagnostics(unsigned *disconnects,int *reason,unsigned *failures,int *phase) {
 *disconnects=atomic_load(&wifi_disconnects); *reason=atomic_load(&wifi_reason);
 *failures=atomic_load(&http_failures); *phase=atomic_load(&http_phase);
}
static int64_t armed_until;
typedef struct { char *data; int length; bool overflow, finished; } response_t;
static esp_err_t http_event(esp_http_client_event_t *event) {
 response_t *response=event->user_data;
 if(event->event_id==HTTP_EVENT_ON_DATA) {
  if(event->data_len<0 || response->length+event->data_len>=4096) {
   response->overflow=true;return ESP_FAIL;
  }
  memcpy(response->data+response->length,event->data,event->data_len);
  response->length+=event->data_len;
 } else if(event->event_id==HTTP_EVENT_ON_FINISH)response->finished=true;
 return ESP_OK;
}
bool network_pairing_armed(void) { return armed_until && esp_timer_get_time()<armed_until; }
static const char *value(cJSON *o,const char *key) { cJSON *v=cJSON_GetObjectItem(o,key); return cJSON_IsString(v)?v->valuestring:""; }
const char *network_status(void) {
 static const char *states[]={"未配置：按确认配对","正在连接 Wi-Fi","Wi-Fi 已连接","正在验证 Bridge","无线同步正常","连接失败：检查网络","证书或 Bridge 连接失败","配置存储不可用","请在 Mac 运行无线配对"};
 if(network_pairing_armed())return states[8];
 int current=atomic_load(&status); return states[current==8?0:current];
}
void network_arm(void) { armed_until=esp_timer_get_time()+60000000; atomic_store(&status,8); }
bool network_provision(cJSON *o) {
 if(esp_timer_get_time()>armed_until || !armed_until)return false;
 const char *ssid=value(o,"ssid"), *pass=value(o,"password"), *url=value(o,"url"), *token=value(o,"token"), *cert=value(o,"cert");
 if(!*ssid || strlen(ssid)>32 || strlen(pass)>64 || strncmp(url,"https://",8) || strlen(url)>=sizeof(config.url) || strlen(token)!=64 || !strstr(cert,"-----BEGIN CERTIFICATE-----") || strlen(cert)>=sizeof(config.cert))return false;
 config_t proposed={0};
 snprintf(proposed.ssid,sizeof(proposed.ssid),"%s",ssid); snprintf(proposed.password,sizeof(proposed.password),"%s",pass);
 snprintf(proposed.url,sizeof(proposed.url),"%s",url); snprintf(proposed.token,sizeof(proposed.token),"%s",token); snprintf(proposed.cert,sizeof(proposed.cert),"%s",cert);
 cJSON *utc=cJSON_GetObjectItem(o,"utc"); if(!cJSON_IsNumber(utc)||utc->valuedouble<1700000000)return false;
 proposed.utc=(int64_t)utc->valuedouble;
 nvs_handle_t nvs; if(nvs_open("pcc_wifi",NVS_READWRITE,&nvs)!=ESP_OK)return false;
 esp_err_t result=nvs_set_blob(nvs,"config",&proposed,sizeof(proposed));
 if(result==ESP_OK)result=nvs_commit(nvs);
 nvs_close(nvs); return result==ESP_OK;
}
static void event(void *a,esp_event_base_t base,int32_t id,void *data) {
 if(base==WIFI_EVENT && id==WIFI_EVENT_STA_START)esp_wifi_connect();
 if(base==WIFI_EVENT && id==WIFI_EVENT_STA_DISCONNECTED) {
  atomic_store(&wifi_ready,false); atomic_fetch_add(&wifi_generation,1);
  atomic_fetch_add(&wifi_disconnects,1);
  wifi_event_sta_disconnected_t *disconnected=data;
  atomic_store(&wifi_reason,disconnected?disconnected->reason:0);
  atomic_store(&status,5); esp_wifi_connect();
 }
 if(base==IP_EVENT && id==IP_EVENT_STA_GOT_IP) {
  atomic_fetch_add(&wifi_generation,1); atomic_store(&wifi_ready,true);
  atomic_store(&status,2);
 }
}
static void worker(void *arg) {
 struct timeval clock={.tv_sec=config.utc}; settimeofday(&clock,NULL);
 if(esp_netif_init()!=ESP_OK)goto failed;
 if(esp_event_loop_create_default()!=ESP_OK)goto failed;
 esp_netif_create_default_wifi_sta(); wifi_init_config_t init=WIFI_INIT_CONFIG_DEFAULT();
 if(esp_wifi_init(&init)!=ESP_OK)goto failed;
 esp_event_handler_register(WIFI_EVENT,ESP_EVENT_ANY_ID,event,NULL); esp_event_handler_register(IP_EVENT,IP_EVENT_STA_GOT_IP,event,NULL);
 wifi_config_t wifi={0}; memcpy(wifi.sta.ssid,config.ssid,strlen(config.ssid)); memcpy(wifi.sta.password,config.password,strlen(config.password));
 wifi.sta.pmf_cfg.capable=true;
 esp_wifi_set_storage(WIFI_STORAGE_RAM); esp_wifi_set_mode(WIFI_MODE_STA); esp_wifi_set_config(WIFI_IF_STA,&wifi);
 atomic_store(&status,1); if(esp_wifi_start()!=ESP_OK)goto failed;
 // This is a latency-sensitive controller. Modem sleep adds burst latency to
 // small LAN requests; battery optimization can be a separate explicit mode.
 esp_wifi_set_ps(WIFI_PS_NONE);
 char *tx=malloc(512), *rx=malloc(4096); if(!tx || !rx)goto failed;
 response_t response={.data=rx};
 esp_http_client_config_t http={.url=config.url,.cert_pem=config.cert,.timeout_ms=2000,.keep_alive_enable=true,
  .buffer_size=1024,.buffer_size_tx=1024,.event_handler=http_event,.user_data=&response,
  .disable_auto_redirect=true};
 esp_http_client_handle_t client=esp_http_client_init(&http); if(!client)goto failed;
 char auth[80]; snprintf(auth,sizeof(auth),"Bearer %s",config.token);
 esp_http_client_set_header(client,"Authorization",auth); esp_http_client_set_header(client,"Content-Type","application/json");
 unsigned client_generation=0;
 for(;;) {
  if(xQueueReceive(outgoing,tx,pdMS_TO_TICKS(500))!=pdTRUE)continue;
  if(!atomic_load(&wifi_ready)) { esp_http_client_close(client);continue; }
  // One immediate retry only; fresh heartbeats and urgent decisions must run.
  for(int attempt=0;attempt<2;attempt++) {
  if(!atomic_load(&wifi_ready))break;
  unsigned generation=atomic_load(&wifi_generation);
  if(client_generation!=generation) {
   esp_http_client_close(client); client_generation=generation;
  }
  int phase=1;
  if(atomic_load(&status)!=4)atomic_store(&status,3);
  esp_http_client_set_method(client,HTTP_METHOD_POST);
  response.length=0;response.overflow=false;response.finished=false;
  esp_http_client_set_post_field(client,tx,strlen(tx));
  // Let IDF own the complete HTTP lifecycle, including persistent connection
  // cleanup and error transitions. Collect the body in a bounded callback.
  int64_t started=esp_timer_get_time();
  esp_err_t error=esp_http_client_perform(client);
  phase=response.length?4:3;
  atomic_store(&http_duration_ms,(int)((esp_timer_get_time()-started)/1000));
  if(error!=ESP_OK || esp_http_client_get_status_code(client)!=200) {
   atomic_store(&http_error,error);atomic_store(&http_code,esp_http_client_get_status_code(client));
  }
  if(error!=ESP_OK || esp_http_client_get_status_code(client)!=200 ||
     response.overflow || !response.finished || response.length<=0 ||
     !esp_http_client_is_complete_data_received(client))goto retry;
  rx[response.length]=0;
  if(!atomic_load(&wifi_ready) || generation!=atomic_load(&wifi_generation))goto retry;
  xQueueOverwrite(incoming,rx); atomic_store(&status,4);
  // Reuse authenticated TLS instead of handshaking again on every poll.
  break;
 retry:
  atomic_fetch_add(&http_failures,1); atomic_store(&http_phase,phase);
  esp_http_client_close(client);
  atomic_store(&status,atomic_load(&wifi_ready)?6:5);
  if(attempt==0)vTaskDelay(pdMS_TO_TICKS(100));
  }
 }
 failed:
 atomic_store(&status,5); vTaskDelete(NULL);
}
void network_start(void) {
 if(nvs_flash_init()!=ESP_OK) { atomic_store(&status,7); return; } // Never erase existing NVS.
 nvs_handle_t nvs; if(nvs_open("pcc_wifi",NVS_READONLY,&nvs)!=ESP_OK)return;
 size_t size=sizeof(config); esp_err_t e=nvs_get_blob(nvs,"config",&config,&size); nvs_close(nvs);
 if(e!=ESP_OK || size!=sizeof(config))return;
 incoming=xQueueCreate(1,4096); outgoing=xQueueCreate(4,512);
 if(!incoming||!outgoing) { atomic_store(&status,5); return; }
 xTaskCreate(worker,"wifi",7168,NULL,4,NULL);
}
bool network_receive(char *out,unsigned size) { return size>=4096 && incoming && xQueueReceive(incoming,out,0)==pdTRUE; }
bool network_send(const char *frame,bool urgent) {
 if(!outgoing || strlen(frame)>=512)return false;
 char packet[512]={0}; strcpy(packet,frame);
 if(!urgent && uxQueueMessagesWaiting(outgoing)>0)return false;
 return (urgent?xQueueSendToFront(outgoing,packet,0):xQueueSend(outgoing,packet,0))==pdTRUE;
}

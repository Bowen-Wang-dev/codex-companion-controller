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
static int64_t armed_until;
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
 if(base==WIFI_EVENT && id==WIFI_EVENT_STA_DISCONNECTED) { atomic_store(&status,5); esp_wifi_connect(); }
 if(base==IP_EVENT && id==IP_EVENT_STA_GOT_IP)atomic_store(&status,2);
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
 char *tx=malloc(512), *rx=malloc(4096); if(!tx || !rx)goto failed;
 esp_http_client_config_t http={.url=config.url,.cert_pem=config.cert,.timeout_ms=3000,.keep_alive_enable=true,.buffer_size=1024,.buffer_size_tx=1024};
 esp_http_client_handle_t client=esp_http_client_init(&http); if(!client)goto failed;
 char auth[80]; snprintf(auth,sizeof(auth),"Bearer %s",config.token);
 esp_http_client_set_header(client,"Authorization",auth); esp_http_client_set_header(client,"Content-Type","application/json");
 for(;;) {
  if(xQueueReceive(outgoing,tx,pdMS_TO_TICKS(500))!=pdTRUE)continue;
  int previous=atomic_load(&status); if(previous==1||previous==5)continue;
 request:
  if(atomic_load(&status)!=4)atomic_store(&status,3);
  esp_http_client_set_method(client,HTTP_METHOD_POST);
  if(esp_http_client_open(client,strlen(tx))!=ESP_OK)goto retry;
  if(esp_http_client_write(client,tx,strlen(tx))!=strlen(tx))goto retry;
  int64_t expected=esp_http_client_fetch_headers(client);
  if(expected<=0 || expected>=4096 || esp_http_client_get_status_code(client)!=200)goto retry;
  int total=0, count;
  while(total<expected && (count=esp_http_client_read(client,rx+total,(int)expected-total))>0)total+=count;
  rx[total]=0;
  if(total!=expected || !esp_http_client_is_complete_data_received(client))goto retry;
  xQueueOverwrite(incoming,rx); atomic_store(&status,4);
  // Reuse authenticated TLS instead of handshaking again on every poll.
  continue;
 retry:
  esp_http_client_close(client); atomic_store(&status,6); vTaskDelay(pdMS_TO_TICKS(1000)); goto request;
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

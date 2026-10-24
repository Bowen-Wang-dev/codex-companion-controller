#pragma once
#include <stddef.h>
#include <stdint.h>
typedef int esp_err_t;
#define ESP_OK 0
#define ESP_FAIL -1
#define ESP_ERR_NO_MEM 0x101
esp_err_t bsp_audio_init(void);
esp_err_t bsp_audio_set_format(uint32_t hz,uint8_t bits,uint8_t channels);
void bsp_audio_set_volume(uint8_t volume);
esp_err_t bsp_audio_write(const void *pcm,size_t bytes);

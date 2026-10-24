#pragma once
#include <stddef.h>
#include <stdint.h>
typedef void *QueueHandle_t;
QueueHandle_t xQueueCreate(unsigned count,size_t size);
int xQueuePeek(QueueHandle_t queue,void *item,uint32_t wait);
int xQueueReceive(QueueHandle_t queue,void *item,uint32_t wait);
int xQueueOverwrite(QueueHandle_t queue,const void *item);
int xQueueReset(QueueHandle_t queue);

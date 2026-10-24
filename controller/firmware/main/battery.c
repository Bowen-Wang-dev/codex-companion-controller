#include "battery.h"
#include "bsp_battery.h"
#include "freertos/FreeRTOS.h"
#include "freertos/task.h"
#include <stdatomic.h>
#include <stdbool.h>

static atomic_int percentage = -1;

static void worker(void *arg) {
    bool ready = false;
    for (;;) {
        // Official BSP checks CW2017 at I2C 0x63 and uses the stock 500 mAh
        // cell's profile. Its initial SOC calculation can take up to 5 seconds;
        // run it away from the UI/network/button task.
        if (!ready) ready = bsp_battery_init() == ESP_OK;
        int value = ready ? bsp_battery_soc() : -1;
        atomic_store(&percentage, value >= 0 && value <= 100 ? value : -1);
        vTaskDelay(pdMS_TO_TICKS(10000));
    }
}

void battery_start(void) { xTaskCreate(worker, "battery", 3072, NULL, 2, NULL); }
int battery_percent(void) { return atomic_load(&percentage); }

idf_component_register(SRCS "main.c" "controller.c" "sound.c" "sound_model.c" "network.c" "battery.c" "ui_font.c"
 INCLUDE_DIRS "." REQUIRES bsp json esp_timer esp_driver_usb_serial_jtag esp_wifi esp_netif esp_event esp_http_client nvs_flash)

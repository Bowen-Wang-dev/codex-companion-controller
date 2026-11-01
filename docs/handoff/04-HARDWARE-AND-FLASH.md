# 硬件与刷写边界

目标为 FoloToy AI Passport，ESP32-C3、8MB Flash、约 400KB 片上 SRAM、无 PSRAM，240×320 ST7789 屏、2.4GHz Wi-Fi/BLE。实际板卡以 BSP 与设备探测为准。没有 SIM/蜂窝；被动 NTAG213 不当作 MCU 外设。

引脚唯一事实源：`controller/firmware/components/bsp/include/bsp_pins.h`。本文记录当前代码值，换板必须重新验证：
- 屏：SPI2，MOSI9、SCLK8、CS1、DC20、BL21，RST=-1（无 MCU 复位脚）。
- 三键：GPIO0/ADC1_CH0 电阻梯，当前 mV 窗口为半开区间 `[0,150)`、`[150,447)`、`[447,1900)`。
- I2C：SDA10、SCL7；ES8311 地址 0x18，CW2017 电量计 0x63。
- 音频：ES8311/I2S，MCLK6、BCLK5、WS3、DOUT2、DIN4；PA_CTRL=-1。
- 使用 codec/I2S，不假设 ESP32-C3 有内置 DAC。音频和 USB 驱动已有特定初始化/恢复逻辑，不随意替换。

## 只刷应用
1. USB 数据线连接唯一目标，先查芯片/Flash/boot 安全状态。
2. 双读完整 8MB，并校验一致；保留本机私有备份。
3. 读取实际分区表，仅支持被脚本验证的布局；镜像大小、芯片和边界必须合适。
4. 只写 factory 应用，常见偏移 0x10000；回读 digest 验证。
5. 不覆盖 NVS、身份、配对、分区表、bootloader，不整片 erase。

仓库 `controller/firmware/partitions.csv` 是构建期容量上限，不是设备现场布局；不能直接据它刷分区表。不要执行 `idf.py flash` 或构建输出的通用多地址 write_flash 指令。

此前 Hello World 只有单 factory，用户允许替换测试应用，但不等于允许永久删除原始备份/整片清零。

## 工具限制
沙箱曾在授予串口路径访问后仍拒绝 termios 配置。发生这种情况，记录具体错误，通过唯一控制台在普通 Terminal 执行获准操作；不绕过沙箱，也不将未执行的刷写记录为成功。备份读取可能数分钟，须显示进度，不把“Reading flash twice”误判为已经开始写 Flash。

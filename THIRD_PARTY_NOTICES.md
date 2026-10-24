# Third-party notices / 第三方许可

Original project code has not been assigned an open-source license. No broader license is implied by uploading this repository. Third-party code and generated font data retain their original terms.

本项目原始代码尚未指定开源许可证，上传仓库不自动授予更广泛许可。第三方组件与生成字体保留各自权利和许可。

| Component / 组件 | Location / 位置 | Terms / 许可 |
|---|---|---|
| FoloToy AI Passport BSP | `controller/firmware/components/bsp/` | Included `LICENSE`; see upstream [ai-passport](https://github.com/FoloToy/ai-passport) |
| ESP-IDF and ESP components | Retrieved by ESP-IDF; versions locked | Notices in `controller/licenses/` and upstream distributions |
| LVGL and associated font assets | `controller/firmware/main/ui_font.c` and managed dependency | LVGL, Montserrat, FontAwesome notices in `controller/licenses/` |
| Source Han Sans subset | `controller/firmware/main/ui_font.c` | SIL Open Font License; `controller/licenses/SourceHanSansSC.txt`, provenance in `controller/docs/ui-font.json` |
| websockets 17.3 | Unmodified wheel in `controller/vendor/` | BSD-3-Clause license inside wheel; digest documented in vendor README |
| pySerial | Installed during Bridge setup | BSD; distributed through its upstream package |

Apple Emoji artwork and Apple Color Emoji font files are **not distributed**. The Mac demo uses the OS-provided font. The optional renderer and importer do not grant image redistribution rights. No firmware binaries are included in this source repository.

本仓库**不分发** Apple Emoji 图像或字体文件。Mac Demo 使用系统字体。可选渲染及导入工具不授予素材分发权。本源码仓库不包含固件二进制。

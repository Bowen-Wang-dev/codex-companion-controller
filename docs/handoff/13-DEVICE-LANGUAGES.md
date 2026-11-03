# 设备语言：由安装入口决定

简体中文（默认） · [English](13-DEVICE-LANGUAGES.en.md)

适用源码：固件 `0.2.14`、Bridge `0.2.14-native-app`。维护日期：2026-11-03（Australia/Sydney）。这是第三阶段设备固件及配套工作；源码、构建、安装和实机验收分别记录。

## 安装后的语言

| 安装入口 | 构建/安装的设备语言 |
|---|---|
| `Codex Companion 控制台.command` / `Codex Companion 控制台.cmd` | 中文，默认 |
| `Codex Companion Console.command` / `Codex Companion Console.cmd` | English |

语言编入固件。英文入口安装的设备从开机起就是英文，离线、配对前及重启后也保持英文；中文入口安装则为中文。之后运行另一种语言的 PC 控制台，不会改变已经安装的设备语言。要更换设备语言，需从对应入口重新构建，并经过相同安全升级流程安装；没有运行时自动切换或额外按键组合。

构建参数为 `-DCOMPANION_FIRMWARE_LANGUAGE=en` 或 `-DCOMPANION_FIRMWARE_LANGUAGE=zh-CN`；全新直接构建未指定时默认中文；复用 CMake 缓存时应显式传入语言，正式入口始终显式传入。两套固件均保留原版 Apple 素材及既有三键交互，不生成或替换表情。

## 从所需语言入口更新

先保存工作，连接唯一目标的 USB 数据线，再打开所需语言的入口。Windows 和 macOS 均使用菜单 7 的同一套子菜单：

1. 7→1 构建该入口语言的固件，使用现有 ESP-IDF 5.5.3（Windows 可复用 WSL）及私有原版素材。
2. 7→2 检查版本、芯片、大小、SHA-256、当前源码指纹、私有素材标记及设备语言。
3. 需要时 7→4 准备 Windows esptool 4.8.1；macOS 此项说明 `CONTROLLER_FLASH_PYTHON` 配置要求。
4. 7→3 进入安全升级。Windows 仍须输入 `FLASH`，macOS 保留既有人工确认。确认前不停止 Bridge；存在待审批时不得升级。
5. 依照提示恢复 Bridge 并在原 App 原聊天验证设备。镜像校验和主机预览不代表实机功能通过。

升级仍是双读完整 8 MB 备份、身份/live 分区核验、仅 factory 应用写入及回读验证。不写 bootloader、分区表或已有 NVS，不整片擦除，不自动重试写入，不重配网、不清零账本、不改变账户。macOS 继续调用既有安全维护脚本，不改成 Windows COM 流程。

## 防止语言刷错

镜像内包含唯一 `COMPANION_UI_LANGUAGE=en` 或 `COMPANION_UI_LANGUAGE=zh-CN` 标记；manifest 的 `ui_language` 从镜像本身读取，不只相信 PC 环境变量。语言标记缺失/不唯一、manifest 与镜像不一致，或镜像语言与当前入口不一致时，安装提前拒绝，要求从正确入口重新构建。

本机保留 `controller/dist/en/` 与 `controller/dist/zh-CN/` 两套镜像/manifest；历史 `controller/dist/PassportController.bin` 仍是当前待更新镜像。如果最后构建的是另一语言，先从目标入口重新构建；不会默默刷入另一语言或下载 GitHub 镜像。旧 `0.2.13` 镜像不满足新源码/语言绑定要求。

含图镜像、素材、Flash 备份和预览截图只保留本机，不能提交或公开分发。

## Bridge 与审批内容

新固件 hello 声明 `ui_language_protocol=1` 和 `ui_language`。Bridge 依据设备安装语言生成菜单配套状态、审批标题/范围/分页、问题提醒、历史事件、计量/账户状态及真实提交回执；不依据当前 PC 界面语言改写设备。旧固件或无有效语言能力声明时继续使用中文。同一 boot 的语言声明变化被忽略，避免已浏览的审批页在处理中换语言；设备重启仍按原 boot/epoch 规则结束旧请求。

为容纳语言声明和较大的诊断计数，USB/网络上行缓冲统一为有界 768 字节，并校验最大 hello 帧；审批详情接收仍为 4096 字节。

仅显式标记的系统文案翻译。用户问题、理由、命令、路径、自定义模型名及未知字段值保持原文；不调用模型翻译或摘要。原始请求摘要、授权结果、逐页送达、二次确认、松开后长按提交、双端首答及 submitted 回执规则不变。未知语义、缺失 diff 或附加授权仍不允许设备批准。

240×320 布局中，英文系统标签使用现有 Montserrat 字体；含中文的用户内容继续用现有思源黑体子集。仍按保守的 13 字符×7 行完整分页，不丢失内容。动态信息较长时会按现有页面范围显示，不把“工具返回”冒充任务成功，也不把“标记已读”当作回复。

## 验证与未覆盖范围

配套回归检查入口语言与镜像标记、旧固件兼容、设备语言独立于 PC、同 boot 语言稳定、原始数据完整、英文审批页加载及提交保护。C 主机检查覆盖两种编译默认值和同一三键审批流程，音频仍使用 mocked BSP/RTOS。

`controller/tools/preview_firmware.py` 使用实际 `render()`、锁定 LVGL 和真实字库离线渲染界面，硬件由桩代替；`--private-artwork` 只读取本机原素材。预览写入 ignored `controller/private/ui-preview/`，不访问设备或网络。本轮共渲染中英文 40 屏，标签越界/重叠检查为 0。这不是 ESP32 真屏、扬声器或长期稳定性验收。

本阶段不代用户刷机、启动/重启真实 App/Bridge、配网、清零或修改账户。新版中英文真屏、完整双端 Allow/Deny、重启/离线语言、配对提示、所有权限类型及长稳仍待安装后实测；macOS 本机执行也须单独记录。

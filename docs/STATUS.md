# Validation status / 验证状态

2026-10-24 · Australia/Sydney

## 中文

- 固件 0.2.4；Bridge `0.2.4-app-relay-preview-human1`；Mac Demo 0.4.0。
- 实际设备已双读备份、仅刷应用并回读校验，保留 Wi-Fi 配对并重新联网，声明 `review_protocol=1`。原厂标识、NVS、bootloader 和分区表未覆盖。
- 桌面 App 26.1016.62342 的原聊天中，真实目录写权限请求已分别通过设备允许和拒绝。匹配硬件选择后，官方工具分别返回授予唯一申请路径／未授予文件权限。没有写测试文件、没有消费额外重置次数；早先在 Mac 点击允许不计入硬件批准。
- 用户已验证详情翻阅、末页选择和新中文字库。中文说明保留实际路径、原因、命令、权限及有效期，不调用模型摘要；路由 ID 和内部时间戳不占页面。确认已读不代替回答或授权。
- 开发树通过 129 项 Python 检查、控制器／音序及八组音频线程检查。实际字库 LVGL 预览检查详情页与末页布局。Mac Demo 基线为 30 项状态机／导航检查。
- App 适配使用已核对版本中的内部开关，非稳定公开设置。先核验版本与入口摘要，App 升级后拒绝套用旧适配。原生审批使用官方 App Server 协议；没有修改 App 安装包、自动点击 GUI 或更改全局账户／提供商配置。
- 目录验收不自动验证网络、命令、缺失 diff 的文件修改、其他客户端或未来版本。网络／命令已有协议实现和主机测试；没有完整修改内容或未支持的附加授权语义仍需 Mac 审阅。第三方 OpenAI/GPT/Codex 中转 API 仍为后续计划。
- 音频线程报告 ready、无错误；已观察到播放计数及 0 ms 启动／供数间隔诊断，不能代替听感验收。声音设置目前重启恢复默认。
- Apple 原图、图像头文件、含图固件、账户、配网密钥及设备备份均未上传。新构建须自行提供适用素材权限。

本次可分享快照另行通过 129 项 Python 检查、控制器／音序及八组音频检查，并使用 ESP-IDF 5.5.3 和已有离线组件成功构建。无 Apple 图片的应用为 2,224,656 字节；没有刷写设备。143 个纳入 Git 的文件经过发布路径、凭据模式及个人路径检查。该扫描是启发式检查，不保证识别所有可能的敏感值。

详细记录：[App 实机验收](../controller/docs/桌面App实体审批验收.md)、[长请求操作](../controller/docs/长请求实体审批.md)。已有离线环境的成功构建不等于任意干净环境已经复现。

## English

- Firmware 0.2.4; Bridge `0.2.4-app-relay-preview-human1`; Mac demo 0.4.0.
- The physical device was backed up twice, application-only updated and read-back verified. Wi-Fi pairing survived and it reconnected with `review_protocol=1`. Identity data, NVS, bootloader and partition table were retained.
- Real directory write requests in the original chat of App 26.1016.62342 passed physical Allow and Deny. Matched hardware choices corresponded to official tool results: the requested path was granted, or filesystem permission remained ungranted. No test files were written or reset credits consumed. Earlier Mac-click approvals were excluded.
- The user verified paged review, final-page selection and corrected Chinese glyphs. Chinese descriptions retain actual paths, reasons, commands, scope and validity without model summarization. Routing IDs/internal timestamps remain in backend checks. Read acknowledgement neither answers a question nor grants access.
- The development tree passed 129 Python tests, controller/tone checks and eight audio-worker cases. Actual-font LVGL previews checked detail/final layouts. The Mac demo baseline has 30 state/navigation checks.
- The App adapter uses internal switches present in the verified build, not stable public settings. Version/entry-script checks reject unverified App upgrades. Native approvals use the official App Server protocol; no App patches, automated GUI clicks or global provider/account changes are used.
- Directory acceptance does not establish network, command, missing-diff file-change, other-client or future-build coverage. Network/command implementations have host tests. Missing change details or unsupported extra-grant semantics still need Mac review. Third-party OpenAI/GPT/Codex gateways remain planned.
- Audio reports ready/no errors with observed play counts and zero-ms scheduling diagnostics; these do not replace listening tests. Audio settings currently reset on reboot.
- Apple artwork, generated image headers, artwork-containing firmware, account files, pairing secrets and device backups are excluded. Supply authorized artwork for new builds.

This shareable snapshot separately passed 129 Python tests, controller/tone checks and eight audio cases, and built successfully with ESP-IDF 5.5.3 and the existing offline dependencies. The artwork-free application is 2,224,656 bytes; no device was flashed. All 143 indexed files were checked for publication paths, credential patterns and personal paths. These are heuristic checks, not proof that every possible sensitive value is absent.

See [hardware acceptance](../controller/docs/桌面App实体审批验收.md) and [paged approvals](../controller/docs/长请求实体审批.md). Success in the available offline environment does not establish arbitrary clean-machine reproducibility.

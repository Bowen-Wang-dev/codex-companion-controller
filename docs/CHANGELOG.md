# Changes / 更新记录

## 0.2.5 · 2026-10-25

### 中文

- 长请求详情支持长按上／下直接跳到首／末页；二次确认可长按方向键返回详情；长按确认提交只作用于二次确认页。
- 真实 App 网络权限已通过设备允许实测；设备选择与 relay 回执匹配，官方工具确认本轮授权；设备 😆 回执经用户确认显示正常。
- 新增交互／回执固件更新入口，保留 Wi-Fi 配对；App relay 更新后需按脚本重新启动 App 并打开原聊天。
- 主机回归检查增至 135 项 Python 测试，并通过固件构建与实际字库预览。

### English

- Hold Up/Down to jump to the first/final page of a long request. Direction holds return from second confirmation; a Confirm hold submits only on that page.
- A real App network permission was allowed on-device; the device choice matched the relay receipt and the official tool confirmed the turn-scoped grant. The user confirmed the 😆 receipt displayed correctly.
- Added an interaction/receipt firmware updater that preserves Wi-Fi pairing. Relaunch the App and reopen the original chat after the relay update.
- Host regression coverage increased to 135 Python tests; firmware build and actual-font previews passed.

## 0.2.4 · 2026-10-24

### 中文

- 版本限定的桌面 App stdio relay 保留原聊天；真实目录申请的设备允许／拒绝双向实测通过。
- 长请求分页，末页无默认选项；短按确认后重新长按提交，长按上键回首屏并取消选择。
- 中文模板替代 JSON 源码，完整保留实际操作信息，不调用模型；常用中文与未知字形可见转义。
- 等待回复／操作的提醒与确认已读独立于权限决定。
- 新增保持 App 打开的 Bridge-only 入口和保留配网的分页固件更新入口。
- 原始请求 ID／摘要、boot／epoch、期限、页状态及竞争处理均参与校验，记录真实设备选择以核对结果。
- stdio／Unix IPC、分页、中文说明和用户提醒等主机检查增至 129 项。

### English

- Version-bound desktop App stdio relay preserves the original chat; real directory requests pass physical Allow/Deny acceptance.
- Complete paged review, no default choice, short confirmation then a fresh hold to submit; holding Up rereads from the beginning and clears selection.
- Chinese descriptions replace JSON dumps without model summarization or omitted operation details; common Chinese glyphs and visible unsupported-character escapes.
- User-action/reply notices and read acknowledgements remain separate from permission decisions.
- Bridge-only reconnection keeping the App open; application-only firmware update retaining Wi-Fi pairing.
- Request/boot/epoch/digest/expiry/page validation and response-race handling; bound device choices recorded for result verification.
- Host coverage, including stdio/Unix IPC, pagination, readable details and notifications, reaches 129 Python checks.

## 0.2.3

Initial source: ESP-IDF firmware, Wi-Fi Bridge, SwiftUI demo, Hooks, audio/state fixes, bilingual documentation and compatible-API roadmap. Direct desktop App grants were not connected in that baseline.

首次源码：ESP-IDF 固件、Wi-Fi Bridge、SwiftUI Demo、Hook、音频／状态修复、中英双语文档和兼容 API 路线图。当时未接通 App 原生权限的设备直接批准。

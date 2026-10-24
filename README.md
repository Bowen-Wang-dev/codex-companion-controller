# Codex Companion Controller

**AI Passport · ESP32-C3 · Mac Bridge · SwiftUI Demo**

[简体中文](#简体中文) · [English](#english)

> Firmware **0.2.5** · Bridge **0.2.5-review-jumps-receipts** · Mac demo **0.4.0**
>
> Experimental personal hardware project. Not an official OpenAI, Apple, or FoloToy product.

## 简体中文

把 FoloToy AI Passport 变成 Codex 的实体状态显示器、三键控制器和 Emoji 电子宠物。Mac Bridge 负责账户、会话和审批，ESP32-C3 负责显示、按键、Wi-Fi 与提示音。

```text
Codex desktop App → version-checked stdio relay → Mac Bridge → HTTPS / Wi-Fi → AI Passport
Codex Hooks → Mac Bridge (task state and user-action notifications)
Codex CLI → shared App Server → Mac Bridge (optional)
```

### 当前功能与真实边界

| 功能 | 当前状态 |
|---|---|
| Wi-Fi 同步、USB 首次配对、时间与电量 | 已实现；设备已通过无线同步联调。时间来自 Mac，精度依赖 Mac 校时 |
| ChatGPT 额度窗口、倒计时与额外重置次数 | 已接入官方账户接口；未知数据不冒充 0 |
| 额外额度重置 | 已实现二次确认和幂等提交；测试没有消耗真实重置次数 |
| 任务状态、事件记录与三秒回待机 | 已实现；Hook 的 Stop 表示本轮结束，不保证整个项目成功 |
| BB 机提醒、音量 0–100%、10% 步进 | 已实现；三声约 1200 Hz，每声 180 ms，间隔 120 ms |
| App 内置目录权限申请 | **已实机验证设备直接批准与拒绝**，保留 App 界面和原聊天 |
| App 网络权限与命令审批 | 已实现原生协议及主机测试；这些类型未因目录测试而自动视为实机验收 |
| 长请求与中文说明 | 完整分页显示实际路径、原因、工作目录、权限和有效期；无需模型精简 |
| 普通 PermissionRequest Hook 审批 | 新固件支持完整输入分页；只处理实际收到的官方 Hook |
| 等待用户操作／回复 | 设备提醒、翻阅、确认已读；已读不代替 Mac 上的回答 |
| CLI 共享 App Server 审批 | 已实现官方协议接入及主机测试；完整实机链路仍需单独验收 |
| 第三方 OpenAI／GPT／Codex 兼容 API | **后续计划，当前 Bridge 未实现提供商适配，也未验证具体服务商** |

实机组合为 App **26.1016.62342**、固件 0.2.5 和加密 Wi-Fi Bridge。目录权限已通过设备允许／拒绝实测；网络权限也已在原 App 聊天中由设备批准，硬件选择与 Bridge 提交回执匹配，官方工具确认本轮网络权限授予。用户确认批准后显示 😆 正常。测试未写测试文件、未消费额外重置次数。见[实机验收记录](controller/docs/桌面App实体审批验收.md)。

App 启动适配使用已核对版本的内部开关，并非稳定公开 API；App 升级后会拒绝套用旧适配。原生审批走官方 App Server 协议，账户和原聊天继续留在 App。缺少文件修改 diff 或尚未支持的额外授权语义，仍需在 Mac 审阅。不能把这次目录测试扩展为所有客户端和所有权限类型均已完成。

### 表情与三键

| 状态 | 表情 |
|---|---|
| 待机 | 😋 |
| 思考／工作 | 🤔 |
| 等待审批 | 🥺 |
| 互动／确认批准后的短暂反馈 | 😆 |
| 额度耗尽 | 😐🤲 |
| 拒绝／失败 | 😭 |
| 本轮完成 | 🥳 |

拒绝直接显示 😭，没有中间表情。普通浏览页短按、长按方向键都换页；设置和事件页短按选择、长按换页。长请求详情页短按上下翻页，长按上键跳到首页、长按下键跳到末页；只有末页的短按上下键才选择允许／拒绝。短按确认进入二次确认，长按上下可返回首／末页；审批不预选，长按确认约 1 秒提交。电源键不作为第四个应用键；固件不依赖同时按上下键静音。

### 项目结构

```text
controller/       ESP-IDF 固件、Mac Bridge、安全刷写及配网脚本、测试
mac-demo/         SwiftUI / AppKit 交互 Demo，键盘 ↑ ↓ Return 模拟三键
docs/            架构、验证状态、OpenAI 兼容 API 路线图
tools/           可独立运行的源码检查
```

### 先体验 Mac Demo

需要 macOS 14+、Swift 6 和 Xcode Command Line Tools。Demo 的任务、额度与审批是模拟数据；应用时钟会发起 HTTPS 校时请求，不修改系统时间。

```sh
cd mac-demo
./test.sh
./build.sh
open "Codex Companion.app"
```

### 配置 Bridge 与构建固件

需要 ESP-IDF **5.5.3**、ESP32-C3 工具链，以及 Python **3.11+ / OpenSSL 3**。先按 ESP-IDF 官方步骤安装并载入 `export.sh`；BSP 在仓库内，组件版本记录在 `controller/firmware/dependencies.lock`。

```sh
# 仅执行本机状态机与 Bridge 测试，不刷写、不登录、不消费额度
python3 -m venv controller/private/bridge-venv
controller/private/bridge-venv/bin/python -m pip install -r controller/requirements-bridge.txt
controller/private/bridge-venv/bin/python controller/scripts/setup_bridge_deps.py
controller/private/bridge-venv/bin/python -m unittest discover -s controller/tests -v
bash tools/check-host.sh

# 已安装并激活 ESP-IDF 5.5.3 后构建
bash controller/scripts/build.sh
```

这个源码仓库不包含 Apple 图像。未导入资源时固件显示素材缺失提示；这不是完整视觉体验的成品镜像。导入有权使用的 Apple 原图见 [controller/README.md](controller/README.md)。

首次使用：在 Mac 登录官方 Codex，构建固件并通过备份及应用区刷写流程更新设备。运行 `配置无线连接.command`，用 USB 和设备确认完成配对。通过 `安装通知接入.command` 注册并审阅 Hooks。

桌面 App 实体审批：先停止旧 Bridge 并退出 App，再运行 `controller/启动桌面App实体审批.command`，打开原聊天。之后若仅更新 Bridge，只在 Bridge 终端 Control+C，再运行 `controller/仅启动桌面App桥接.command`；保持 App 打开，无需刷机。普通 `仅启动桥接.command` 是通知／同步模式，不等于 App 实体审批入口。具体版本限制与入口见 [controller/README.md](controller/README.md)。

### 数据、素材与后续 API 兼容

- 账户凭据只留在 Mac；设备只有 Wi-Fi 配置、Bridge 配对密钥和证书。请求绑定 ID、摘要、启动标识和有效期。
- 刷写要求双读校验完整 8 MB 备份，检查实际设备及分区，只更新受支持的 factory 应用；不执行整片擦除，不覆盖 bootloader、分区表或已有 NVS。
- `private/`、设备备份、账户文件、Wi-Fi 密码、配对证书、Apple 图像和含图像固件均不纳入 Git。
- Apple Emoji 设计属于相应权利人。项目未取得将其随固件公开分发的许可；在线图片、裁剪及本机渲染都不自动产生分发权。Mac Demo 使用系统 Emoji，不附带 Apple 字体或图像。
- 后续兼容目标是第三方提供的 OpenAI／GPT／Codex API：验证 Responses、流式事件、工具调用及多轮继续；将提供商余额与 ChatGPT 的额度／重置分开。换 API 不会自动解决 App 审批通道问题。见 [兼容路线图](docs/API_COMPATIBILITY.md)。

项目原始代码尚未指定开源许可证；第三方组件保留各自许可，见 [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md)。当前验证状态见 [docs/STATUS.md](docs/STATUS.md)。

## English

A physical Codex status display, three-button controller, and emoji companion for the FoloToy AI Passport. The Mac Bridge owns account access, sessions, and approval routing; the ESP32-C3 owns the screen, buttons, Wi-Fi, and audio.

```text
Codex desktop App → version-checked stdio relay → Mac Bridge → HTTPS / Wi-Fi → AI Passport
Codex Hooks → Mac Bridge (task state and user-action notifications)
Codex CLI → shared App Server → Mac Bridge (optional)
```

### Current capabilities and limits

| Feature | Status |
|---|---|
| Wi-Fi sync, initial USB pairing, clock, battery | Implemented; wireless sync tested on the device. Clock accuracy depends on the Mac |
| ChatGPT usage windows, countdowns, reset-credit count | Official account integration implemented; missing values are not shown as zero |
| Extra rate-limit reset | Confirmation and idempotent submission implemented; tests did not spend real credits |
| Task state, history, return to idle after three seconds | Implemented; a Hook Stop means the turn ended, not that the whole project passed |
| Pager alerts and 0–100% volume in 10% steps | Implemented; three tones around 1200 Hz, 180 ms each with 120 ms gaps |
| Built-in App directory permission requests | **Physical Allow and Deny verified in the real App**, retaining its UI and original chat |
| App network and command approvals | Native protocol implementation and host tests; directory tests do not validate every approval type |
| Long requests and readable Chinese details | Complete paged paths, reason, working directory, permissions and validity; no model summarization |
| Ordinary PermissionRequest Hook approvals | Complete input pagination on new firmware, for Hooks actually received |
| User-action / reply requests | Device notification, reading and acknowledgement; acknowledgement does not answer the Mac question |
| CLI sharing an App Server with the Bridge | Protocol integration and host tests implemented; full hardware acceptance remains separate |
| Third-party OpenAI/GPT/Codex-compatible APIs | **Planned. No provider adapter or specific third-party service has been validated** |

The verified combination is App **26.1016.62342**, firmware 0.2.5 and the encrypted Wi-Fi Bridge. Real directory requests passed physical Allow/Deny. A network permission request in the original App chat was also allowed on-device; the physical choice matched the Bridge delivery receipt and the official tool confirmed the turn-scoped grant. The user confirmed the 😆 feedback displayed correctly. No test files were written and no extra reset credits were spent. See the [hardware acceptance record](controller/docs/桌面App实体审批验收.md).

The App launch adapter uses internal switches present in the checked build, not stable public settings. Version changes reject the old adapter. Native approvals use the official App Server protocol while preserving the App's account and original chat. Missing file diffs and unsupported extra-grant semantics still require Mac review. These directory tests do not establish every client or permission type.

### Expressions and controls

| State | Emoji |
|---|---|
| Idle | 😋 |
| Thinking / working | 🤔 |
| Waiting for approval | 🥺 |
| Interaction / brief confirmed-approval feedback | 😆 |
| Usage exhausted | 😐🤲 |
| Denied / failed | 😭 |
| Turn completed | 🥳 |

Denial shows 😭 immediately without an intermediate face. On browsing pages, short and long direction presses change pages. On settings/history pages, short presses select content and long presses change pages. During request review, short Up/Down browse details; hold Up/Down to jump to the first/final page. Only the final page uses short Up/Down to choose Allow/Deny. Short Confirm opens a second confirmation; hold Up/Down there to return to the first/final page. No option is preselected; a fresh one-second Confirm hold submits. The power button is not a fourth application key; firmware does not depend on an Up+Down mute chord.

### Repository layout

```text
controller/       ESP-IDF firmware, Mac Bridge, pairing/flashing scripts and tests
mac-demo/         SwiftUI/AppKit demo; ↑ ↓ Return emulate the physical controls
docs/             Architecture, validation status and compatible-API roadmap
tools/            Standalone source checks
```

### Try the Mac demo

Requires macOS 14+, Swift 6, and Xcode Command Line Tools. Tasks, usage, and approvals are simulated. The demo makes HTTPS clock-calibration requests without changing system time.

```sh
cd mac-demo
./test.sh
./build.sh
open "Codex Companion.app"
```

### Set up the Bridge and build firmware

Use ESP-IDF **5.5.3**, the ESP32-C3 toolchain, and Python **3.11+ / OpenSSL 3**. Install ESP-IDF and source its `export.sh` first. The BSP is included; component versions are recorded in `controller/firmware/dependencies.lock`.

```sh
# Host tests only: no flashing, account login, model tasks or credit redemption
python3 -m venv controller/private/bridge-venv
controller/private/bridge-venv/bin/python -m pip install -r controller/requirements-bridge.txt
controller/private/bridge-venv/bin/python controller/scripts/setup_bridge_deps.py
controller/private/bridge-venv/bin/python -m unittest discover -s controller/tests -v
bash tools/check-host.sh

# After installing and activating ESP-IDF 5.5.3
bash controller/scripts/build.sh
```

Apple artwork is excluded. Firmware built without imported assets displays a missing-artwork message; this source checkout is not a ready-to-flash image with the complete visuals. See [controller/README.md](controller/README.md) for importing authorized Apple originals.

For first setup, sign into official Codex, build firmware and use the backup/application-only flash workflow. Run `配置无线连接.command` for USB pairing with physical confirmation. Register and review Hooks with `安装通知接入.command`.

For desktop App physical approvals, stop the old Bridge and quit the App, then run `controller/启动桌面App实体审批.command` and reopen the original chat. For Bridge-only updates, stop just the Bridge with Control+C and run `controller/仅启动桌面App桥接.command`, keeping the App open; no flashing is needed. The ordinary `仅启动桥接.command` starts notification/sync mode, not the desktop approval adapter. See [controller/README.md](controller/README.md) for translated launchers and version limits.

### Data, artwork and API compatibility

- Codex credentials stay on the Mac. The device stores Wi-Fi configuration, a Bridge pairing key, and certificate. Requests bind their ID, digest, boot identity, and expiry.
- Flashing requires two matching full 8 MB reads, live device/partition checks, and a supported factory application layout. The updater does not erase the entire flash or overwrite the bootloader, partition table, or existing NVS.
- Runtime state, flash backups, account files, Wi-Fi passwords, pairing certificates, Apple artwork, and firmware containing artwork are excluded from Git.
- Apple Emoji designs belong to their rights holders. No public firmware redistribution license has been established. Downloading, cropping, or locally rendering an image does not grant distribution rights. The Mac demo uses the system emoji font without bundling it.
- Future compatibility targets third-party OpenAI/GPT/Codex APIs. Validate Responses streaming, tools, and conversation continuation, and keep provider balances separate from ChatGPT limits/reset credits. Changing inference providers does not automatically expose desktop App approvals. See [API compatibility roadmap](docs/API_COMPATIBILITY.md).

No open-source license has been selected for original project code. Third-party components retain their own terms; see [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md). See [docs/STATUS.md](docs/STATUS.md) for validation evidence and remaining work.

## References / 参考

- [FoloToy AI Passport](https://github.com/FoloToy/ai-passport)
- [Codex Hooks](https://learn.chatgpt.com/docs/hooks)
- [Codex App Server](https://learn.chatgpt.com/docs/app-server)
- [Codex provider/gateway configuration](https://learn.chatgpt.com/docs/enterprise/connect-to-a-gateway)
- [Gateway compatibility](https://learn.chatgpt.com/docs/enterprise/gateway-compatibility)

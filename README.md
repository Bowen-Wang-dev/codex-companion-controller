# Codex Companion Controller

**AI Passport · ESP32-C3 · Mac Bridge · SwiftUI Demo**

[简体中文](#简体中文) · [English](#english)

> Firmware **0.2.3** · Bridge **0.2.3-hookfix1** · Mac demo **0.4.0**
>
> Experimental personal hardware project. Not an official OpenAI, Apple, or FoloToy product.

## 简体中文

把 FoloToy AI Passport 变成 Codex 的实体状态显示器、三键控制器和 Emoji 电子宠物。Mac Bridge 负责账户、会话和审批，ESP32-C3 负责显示、按键、Wi-Fi 与提示音。

```text
Codex App / CLI → Hooks 或共享 App Server → Mac Bridge → HTTPS / Wi-Fi → AI Passport
```

### 当前功能与真实边界

| 功能 | 当前状态 |
|---|---|
| Wi-Fi 同步、USB 首次配对、时间与电量 | 已实现；设备已通过无线同步联调。时间来自 Mac，精度依赖 Mac 校时 |
| ChatGPT 额度窗口、倒计时与额外重置次数 | 已接入官方账户接口；未知数据不冒充 0 |
| 额外额度重置 | 已实现二次确认和幂等提交；测试没有消耗真实重置次数 |
| 任务状态、事件记录与三秒回待机 | 已实现；Hook 的 Stop 表示本轮结束，不保证整个项目成功 |
| BB 机提醒、音量 0–100%、10% 步进 | 已实现；三声约 1200 Hz，每声 180 ms，间隔 120 ms |
| 普通 PermissionRequest Hook 审批 | 支持完整可显示且已识别的操作；复杂或过长内容在 Mac 审阅 |
| App 内置目录／网络权限申请 | 设备可拒绝或转到 Mac；**直接授予仍未接通** |
| CLI 共享 App Server 审批 | 已实现官方协议接入及主机测试；完整实机链路仍需单独验收 |
| 第三方 OpenAI／GPT／Codex 兼容 API | **后续计划，当前 Bridge 未实现提供商适配，也未验证具体服务商** |

用户已在实机验证 App 原生权限申请的设备提醒、设备拒绝和继续到 Mac。设备“允许后转到 Mac”不等于设备已授予目录权限。不能把主机测试通过写成所有 App 审批均已完成。

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

拒绝直接显示 😭，没有中间表情。普通浏览页短按、长按方向键都换页；设置和事件页短按选择、长按换页。审批不预选：上／下选择，短按确认，松开后再次长按约 1 秒提交。电源键不作为第四个应用键；固件不依赖同时按上下键静音。

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

首次使用：在 Mac 登录官方 Codex；构建自己的固件，使用 `刷入并启动.command` 的备份及应用区刷写流程；运行 `配置无线连接.command`，用 USB 和设备确认完成配对。之后运行 `安装通知接入.command`，由用户审阅并信任 Hooks，再完整重开 App。日常运行 `仅启动桥接.command`，保持 Mac 和设备处于可互访的网络。具体入口与限制见 [controller/README.md](controller/README.md)。

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
Codex App / CLI → Hooks or shared App Server → Mac Bridge → HTTPS / Wi-Fi → AI Passport
```

### Current capabilities and limits

| Feature | Status |
|---|---|
| Wi-Fi sync, initial USB pairing, clock, battery | Implemented; wireless sync tested on the device. Clock accuracy depends on the Mac |
| ChatGPT usage windows, countdowns, reset-credit count | Official account integration implemented; missing values are not shown as zero |
| Extra rate-limit reset | Confirmation and idempotent submission implemented; tests did not spend real credits |
| Task state, history, return to idle after three seconds | Implemented; a Hook Stop means the turn ended, not that the whole project passed |
| Pager alerts and 0–100% volume in 10% steps | Implemented; three tones around 1200 Hz, 180 ms each with 120 ms gaps |
| Ordinary PermissionRequest Hook approvals | Supported for recognized operations whose required details fit the display |
| Built-in App directory/network permission grants | Device denial or handoff to Mac; **direct grants are not connected yet** |
| CLI sharing an App Server with the Bridge | Protocol integration and host tests implemented; full hardware acceptance remains separate |
| Third-party OpenAI/GPT/Codex-compatible APIs | **Planned. No provider adapter or specific third-party service has been validated** |

The user has verified real App permission notifications, hardware denial, and continuation to the Mac. Continuing to the Mac does not grant filesystem access. Host tests do not prove complete desktop App approval coverage.

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

Denial shows 😭 immediately without an intermediate face. On browsing pages, short and long direction presses change pages. On settings/history pages, short presses select content and long presses change pages. Approvals have no default selection: select with Up/Down, press Confirm, release it, then hold Confirm again for about one second. The power button is not a fourth application key; firmware does not depend on an Up+Down mute chord.

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

For first setup, sign into official Codex on the Mac, build your firmware, and use `刷入并启动.command` to back up and update the application partition. Run `配置无线连接.command` for USB pairing with physical confirmation. Run `安装通知接入.command`, review and trust the Hooks yourself, then fully restart the App. For daily use run `仅启动桥接.command` and keep the Mac and device on reachable networks. See [controller/README.md](controller/README.md) for launcher translations and limitations.

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

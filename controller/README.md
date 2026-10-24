# Controller setup / 控制器配置

See the [bilingual project README](../README.md) for current capability limits. Firmware 0.2.4, Bridge 0.2.4-app-relay-preview-human1. This directory contains source, not a prebuilt firmware release.

当前功能边界见[中英双语主页](../README.md)。这里是源码，不含可直接刷入的完整视觉固件。

## Prerequisites / 环境

- ESP-IDF 5.5.3 installed with the ESP32-C3 tools; source its `export.sh` before building/flashing.
- Python 3.11+ built with OpenSSL 3 for the Bridge. Set `CONTROLLER_MODERN_PYTHON` to its absolute executable path if `python3` is older.
- Optional `PASSPORT_DEPS` points to an offline ESP component directory; otherwise IDF Component Manager downloads the pinned dependencies.
- `COMPANION_CODEX` can select the official Codex executable; the installed macOS App bundle is detected when available.

需要 ESP-IDF 5.5.3、ESP32-C3 工具链及 Python 3.11+ / OpenSSL 3。先载入 IDF 的 `export.sh`；可用 `CONTROLLER_MODERN_PYTHON` 指定现代 Python，`COMPANION_CODEX` 指定官方 CLI。`PASSPORT_DEPS` 仅用于已有离线组件缓存。

```sh
bash scripts/setup_bridge.sh
bash scripts/build.sh
```

Without artwork, the firmware displays a missing-assets message. To import authorized Apple originals, provide `idle.png`, `working.png`, `permission.png`, `delight.png`, `crying.png`, `completed.png`, `neutral.png`, and `palms.png`. Use a local rights JSON containing `apple_original: true` and a nonempty `rights_basis`, then run:

未导入图片时固件显示素材缺失提示。自行提供有权使用的上述八个 Apple 原图，权利记录 JSON 包含 `apple_original: true` 与非空 `rights_basis`：

```sh
private/bridge-venv/bin/python -m pip install Pillow
private/bridge-venv/bin/python scripts/import_assets.py \
  --source /absolute/path/to/authorized-images \
  --rights-file /absolute/path/to/rights.json
bash scripts/build.sh
```

The optional `build_personal.sh` renders the local macOS system emoji. It makes no claim that extraction, embedding or redistribution is licensed; check applicable rights before using it. Generated images, `pet_assets.h`, and firmware stay outside Git.

`build_personal.sh` 是可选的本机系统 Emoji 渲染入口，不承诺提取、嵌入或分发许可；使用前自行确认适用权利。所有输出都应留在 Git 外。

## Launchers / 启动入口

Run scripts from a normal macOS Terminal. Source releases omit firmware binaries, so build locally before any launcher that flashes. Keep the Bridge running for device synchronization.

在正常 macOS Terminal 运行；刷写入口必须先有本机构建镜像。日常同步需要 Bridge 保持运行。

| Launcher | Purpose |
|---|---|
| `启动桌面App实体审批.command` | Launch the checked App build with native approval relay / 启动版本限定 App 实体审批 |
| `仅启动桌面App桥接.command` | Reconnect Bridge to the already-open adapted App; no flash / 保持 App 打开，仅重启审批 Bridge |
| `更新长请求审批固件.command` | Back up, update 0.2.4, retain pairing, reconnect existing App / 更新分页固件并接回现有 App |
| `检查桌面审批接口.command` | Read-only public control-socket probe; empty loaded-thread list is not App attachment / 只读接口检查 |
| `刷入并启动.command` | Back up, validate, update the factory app, start Bridge / 备份、校验、刷应用并启动 |
| `更新固件保留配网.command` | Update firmware and preserve Wi-Fi pairing / 更新固件、保留配网 |
| `配置无线连接.command` | USB pairing with physical confirmation / USB 安全配网 |
| `仅启动桥接.command` | Start Bridge without flashing / 不刷固件，仅启动 Bridge |
| `安装通知接入.command` | Register Hooks; does not grant trust / 注册 Hook，不代替用户信任 |
| `审阅通知Hook.command` | Open official CLI to inspect `/hooks` / 审阅 Hook |
| `检查通知接入.command` | Read-only integration diagnostics / 只读诊断 |
| `用CLI继续原会话并启用设备审批.command` | Resume an existing chat through shared App Server / CLI 原会话审批模式 |

## Desktop App approvals / 桌面 App 实体审批

The adapter verifies App version **26.1016.62342** and the installed entry-script hash before using its internal local-executor switches. It does not patch the App bundle or change global account/provider settings. Future App versions require a fresh compatibility check. Start from `启动桌面App实体审批.command`, then open the original chat. If updating only the Bridge, stop just the old Bridge and run `仅启动桌面App桥接.command`; do not quit the App or reflash.

适配先核验 App 26.1016.62342 及入口摘要，再使用该版本的内部启动开关。不开 CLI 操作界面，不修改 App 安装包或全局账户／提供商配置。App 升级后必须重新核查。首次使用实体审批入口后打开原聊天；仅更新 Bridge 时保持 App 打开，用「仅启动桌面App桥接」重新连接，无需刷机。

Physical Allow/Deny for real directory requests is verified. Long details use Chinese templates with full paths/commands/reasons and no model calls. Up/Down browse details; the final decision page has no default. Select Up=Allow or Down=Deny, short Confirm, release, then hold Confirm for one second. Hold Up to reread from the start. A user-reply notice instead ends in an acknowledgement; it never answers the question or grants access.

真实目录请求的设备允许／拒绝已验收。长详情采用中文模板，完整保留路径、命令、原因，不调用模型。详情页上下翻阅；末页无默认选择，上允许／下拒绝，短按确认，松开后长按 1 秒提交。长按上键回首屏。等待回复的提醒只能确认已读，不能代替回答或授权。

Missing file-change diffs and unsupported additional-grant semantics still need Mac review. See [hardware acceptance](docs/桌面App实体审批验收.md) and [paged approval details](docs/长请求实体审批.md).

缺失文件修改明细或未支持的附加授权语义仍需在 Mac 审阅。详见上述实机验收及分页说明。

Do not erase the whole flash. The updater requires two matching full-flash reads and a compatible single-factory partition layout. Keep private backups locally. Unsupported layouts and encrypted/secure-boot devices are refused.

禁止整片擦除。刷写脚本要求双读匹配备份及兼容的单 factory 布局；备份自行妥善保存。不支持的布局、加密或 Secure Boot 设备会被拒绝。

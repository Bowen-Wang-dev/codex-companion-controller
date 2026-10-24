# Controller setup / 控制器配置

See the [bilingual project README](../README.md) for current capability limits. Firmware 0.2.3, Bridge 0.2.3-hookfix1. This directory contains source, not a prebuilt firmware release.

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
| `刷入并启动.command` | Back up, validate, update the factory app, start Bridge / 备份、校验、刷应用并启动 |
| `更新固件保留配网.command` | Update firmware and preserve Wi-Fi pairing / 更新固件、保留配网 |
| `配置无线连接.command` | USB pairing with physical confirmation / USB 安全配网 |
| `仅启动桥接.command` | Start Bridge without flashing / 不刷固件，仅启动 Bridge |
| `安装通知接入.command` | Register Hooks; does not grant trust / 注册 Hook，不代替用户信任 |
| `审阅通知Hook.command` | Open official CLI to inspect `/hooks` / 审阅 Hook |
| `检查通知接入.command` | Read-only integration diagnostics / 只读诊断 |
| `用CLI继续原会话并启用设备审批.command` | Resume an existing chat through shared App Server / CLI 原会话审批模式 |

Do not erase the whole flash. The updater requires two matching full-flash reads and a compatible single-factory partition layout. Keep private backups locally. Unsupported layouts and encrypted/secure-boot devices are refused.

禁止整片擦除。刷写脚本要求双读匹配备份及兼容的单 factory 布局；备份自行妥善保存。不支持的布局、加密或 Secure Boot 设备会被拒绝。

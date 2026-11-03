# Codex Companion Controller

简体中文（默认） · [English](README.en.md)

FoloToy AI Passport 的 Codex 实体控制器、状态显示器与 Emoji 交互原型。PC 端 Bridge 负责会话、审批和本地计量，ESP32-C3 负责显示、三键输入、无线连接与提示音。支持 macOS，并新增 Windows 10/11 主机适配；本轮验证环境为 Windows 11 Pro，完整平台/实机边界见[双平台说明](docs/handoff/11-HOST-PLATFORMS.md)。本项目不是 OpenAI、Apple 或 FoloToy 的官方产品。

## 版本与验证状态

截至 2026-11-03（Australia/Sydney）：

| 项目 | 状态 |
|---|---|
| 源码 | 固件 `0.2.13`；Bridge `0.2.13-native-app`；PC 端 Demo `0.4.0` |
| 已有发布基线 | Git 标签 `v0.2.12`；五项原生双端实机验收见[发布记录](docs/releases/v0.2.12.md) |
| 设备最近记录 | 后续运行日志已报告固件 `0.2.13`；用户随后确认完成 Windows 升级及基本目视检查，新版完整验收仍未完成 |
| 本次维护 | 本阶段只整理 Markdown；控制台入口与固件语言分别在后续阶段提交 |
| 后续工作 | Windows 10、macOS 本轮执行及 Windows 原 App/设备实机矩阵待验证；见[项目状态](docs/handoff/01-PROJECT-STATE.md) |

固件版本、Bridge 源码修订号、当前进程已加载的代码与实机验收是不同状态。最近一次日志或单次操作反馈不能替代完整验收。

## 功能与边界

- 同一审批经 relay 同时交给原 PC 端 App 原聊天和设备，首个有效答复生效。设备端保留完整分页、无默认选择、二次确认及长按提交。
- v0.2.13 移除详情页长按“转到 PC 端”；PC 端可直接查看和处理请求。缺少文件修改明细或尚未支持的授权语义时，设备不能批准。
- Hooks 提供任务状态及用户操作提醒。确认已读不代替回复；工具返回、审批提交和任务成功分别表示不同事件。
- 支持 USB 物理确认配对与 HTTPS 同步。设备在线只说明设备与 Bridge 连通；桌面审批还需 relay 和原会话接入。
- ChatGPT 账户窗口与第三方 Token 计量分别处理。估价使用本机配置，按逐请求边界判定费率；不是账户总账或实时官方价格服务。
- PC 端 Demo 的任务、审批、额度和重置均为模拟数据；HTTPS 校时是真实网络请求，不修改系统时间。

PC 端 App 适配仅支持源码登记的精确版本和文件摘要，当前登记 `26.1016.62342`、`26.1027.30824`。内部启动开关不是稳定公开设置；未知版本必须重新核查。

## 日常入口

macOS 使用 `controller/Codex Companion 控制台.command`；Windows 使用同名 `.cmd`。两者调用同一控制台；Windows 首次运行会准备独立 Python 环境。检查和环境要求见[双平台说明](docs/handoff/11-HOST-PLATFORMS.md)。现有入口仍为中文；独立英文入口属于第二阶段，不在本文档提交中交付。

| 菜单 | 用途 |
|---|---|
| 1 | 通过已核对入口启动 App、relay 与 Bridge |
| 2 | 诊断和恢复设备 / Bridge；子菜单 2 根据 App 状态选择启动链 |
| 3 | 首次配对或更新 Wi-Fi |
| 4 | 编辑本地模型费率、价格来源、长上下文档位与倍率 |
| 5 | 查看计数、只读核对最近一小时、确认后清零本机计数 |
| 6 | 安装或修复 Hooks；信任仍需人工审阅 |
| 7 | 双平台 USB 固件备份与应用更新；Windows 提供构建、校验、安全升级及刷写环境准备 |

App 已运行时，仅重启 Bridge 不能为普通启动的 App 补上 relay。应保留工作，手动退出 App，再由控制台启动。设备显示“App 实体审批已接入”是连接条件，仍需真实请求验证。完整步骤见[运行手册](docs/handoff/06-RUNBOOK.md)。历史 `.command` 入口保留在 `controller/维护工具/`，不作为日常入口。

## 开发与检查

Bridge 需要 Python 3.11+、OpenSSL 3；本机已记录独立 Python 3.12 环境。先配置 `CONTROLLER_MODERN_PYTHON`，已有环境可配置 `CONTROLLER_BRIDGE_PYTHON`。macOS 的 `scripts/env.sh` 读取本机私有配置；固定摘要的依赖 wheel 随源码提供。

macOS 检查，从仓库根目录执行：

```sh
bash controller/scripts/setup_bridge.sh
source controller/scripts/env.sh
"$CONTROLLER_BRIDGE_PYTHON" -m unittest discover -s controller/tests -v
python3 -m unittest discover -s tools -p 'test_*.py'
bash tools/check-host.sh
zsh mac-demo/test.sh
```

Windows 环境准备及检查，从仓库根目录执行：

```powershell
$env:PYTHONUTF8 = '1'
python controller/scripts/setup_windows.py --setup-only
python controller/scripts/setup_windows.py --check-only
& './controller/private/bridge-venv-windows/Scripts/python.exe' -m unittest discover -s controller/tests -v
& './controller/private/bridge-venv-windows/Scripts/python.exe' -m unittest discover -s tools -p 'test_*.py' -v
```

socket 回归需要本机 TCP/Unix 权限。主机测试不调用模型、不消费额外重置次数，也不构成设备功能验收。

固件构建需要 ESP-IDF 5.5.3 和 ESP32-C3 工具链；先载入该工具链的 `export.sh`，macOS 再执行 `bash controller/scripts/build.sh`；Windows 菜单 7 复用现有 ESP-IDF 或 WSL。组件版本见 `controller/firmware/dependencies.lock`。构建不会刷写，源码也不包含 Apple 图像。素材导入、镜像检查和恢复说明见[Controller 使用说明](controller/README.md)。

## 安全与数据

Codex 登录凭据留在原主机，不拷入设备；迁移不将原 Mac 凭据复制到 Windows。`controller/private/`、配对密钥、账本、Flash 备份、Apple 原图和含图固件均不得上传。设备更新必须经过双读完整备份、现场分区校验及仅应用更新，不整片擦除。

Apple 图像不随源码分发；下载、裁剪或本机渲染不代表已取得固件分发许可。原始项目代码尚未指定开源许可证，第三方条款见 [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md)。

## 文档导航

- [文档总索引及语言规则](docs/README.md)
- [Agent 工作边界](AGENTS.md)与[交接入口](docs/handoff/00-START-HERE.md)
- [架构](docs/handoff/02-ARCHITECTURE.md)、[交互规范](docs/handoff/03-UX-CONTRACT.md)、[硬件与刷写](docs/handoff/04-HARDWARE-AND-FLASH.md)
- [计量模型](docs/handoff/05-TOKEN-AND-PRICING.md)、[迁移与私有数据](docs/handoff/07-MIGRATION-AND-PRIVACY.md)
- [变更记录](docs/handoff/08-CHANGE-AND-DECISIONS.md)、[待办](docs/handoff/09-BACKLOG.md)、[本次审查报告](docs/reviews/2026-11-02-code-and-docs.md)

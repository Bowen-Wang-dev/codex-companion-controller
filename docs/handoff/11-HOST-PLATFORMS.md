# macOS / Windows 主机适配

简体中文（默认） · [English](11-HOST-PLATFORMS.en.md)

维护日期：2026-11-03（Australia/Sydney）。用户授权 Windows 10/11 主机适配，同时保留 macOS；不迁移或替换 Mac 产品，不删除原入口、固件和 Swift Demo。

## 当前 Windows 固件维护

菜单 7 调用 `scripts/firmware_update.py`：1 构建，2 校验镜像，3 USB 安全升级，4 准备独立 esptool 4.8.1。复用现有 ESP-IDF 或 WSL ESP-IDF 5.5.3，USB 始终由 Windows 访问；没有新增顶层启动器。升级校验本机构建与当前源码一致，不从 GitHub 下载“最新固件”。

原先缺少私有 `controller/firmware/main/pet_assets.h` 的阻塞已解除：已从 Mac 私有包恢复原版素材、构建绑定当前源码的 0.2.13，并在分块读取修复后由用户确认 Windows 升级及基本目视检查完成。不要要求重复刷机；完整审批矩阵、Windows 10 和长期稳定性仍须单独验收。

未来获得明确授权后更新：7→1 构建、7→2 校验、需要时 7→4 准备环境、7→3 输入 `FLASH`。缺素材或镜像过期在停 Bridge 前拒绝。升级双读完整备份并核对摘要，检查身份/live 分区，仅写应用并验证；菜单 2 恢复 Bridge。需要数据线及唯一目标。Windows 使用 256 KiB 块、有限只读重试和末次 ROM 回退；写入不自动重试。

## 平台与验证范围

| 能力 | macOS | Windows 10/11 |
|---|---|---|
| 日常入口 | 保留 `controller/Codex Companion 控制台.command` | 同名 `.cmd`，双击运行 |
| Python | 原有独立环境与 `env.sh` | Python 3.11+ / OpenSSL 3；独立 `private/bridge-venv-windows` |
| 主机私有通信 | Unix socket、0700/0600、flock | 仅 127.0.0.1 随机端口、每次启动随机鉴权、当前用户 DACL、Windows 文件锁 |
| 桌面接入 | 保留版本与摘要登记 | 单独登记 App 26.1027.30824（MSIX 26.1027.3384.0）四个启动文件摘要 |
| relay | 原 `.command` | 私有生成原生 `.exe`，共用 stdio relay 和 Broker |
| USB 候选 | 保留 `/dev/cu.usbmodem*` | ESP32-C3 VID/PID 303A:1001；拒绝随意选择 COM |
| Wi-Fi 配对、计量、费率、Hooks | 共用实现 | 共用实现，补 Windows IP/OpenSSL 发现、Hook 命令及文件权限 |
| 归档 / 本地迁移 | 原功能保留 | 补 DACL 与 Windows 环境准备；排除 Windows venv、机器专属 relay；不复制 auth.json |
| 固件菜单 / ESP-IDF 构建 | 保留安全流程 | 已接 ESP-IDF/WSL 及 Windows COM 安全更新器；用户确认升级/基本目视检查，完整验收待补 |
| Swift Demo | 原 macOS Demo 保留 | 无 Windows Demo，不计入硬件 Bridge 支持 |

开发环境为 Windows 11 Pro / Python 3.12.10。Windows 10 为实现目标，尚无运行证据；Windows CI 不替代 Windows 10/11 实机验收。macOS 本轮无法实跑，旧证据保留；新增双平台 CI 尚无成功运行记录。

## Windows 使用

安装含 pip、venv、Tcl/Tk 的 Python 3.11+，双击 `.cmd`。准备只创建本机 venv、核对仓库固定 SHA-256 wheel、生成 relay；不下载替代固件、不启动 App、不执行设备维护。菜单 1 显式启动 App/Bridge。

从仓库根目录仅准备或检查：

```powershell
$env:PYTHONUTF8 = '1'
python controller/scripts/setup_windows.py --setup-only
python controller/scripts/setup_windows.py --check-only
& './controller/private/bridge-venv-windows/Scripts/python.exe' -m unittest discover -s controller/tests -v
& './controller/private/bridge-venv-windows/Scripts/python.exe' -m unittest discover -s tools -p 'test_*.py' -v
```

`.cmd` 默认调用 `python`；多 Python 可设 `CONTROLLER_MODERN_PYTHON` 为完整解释器路径。`CONTROLLER_OPENSSL` 可指定可执行文件，否则从 PATH 或 Git for Windows 查找。Python TLS 库与配对用 OpenSSL 命令行工具是两个依赖。

App 默认从当前用户 OpenAI.Codex MSIX 包发现。`COMPANION_DESKTOP_APP` 可指定含 `ChatGPT.exe`、`resources` 的 `app` 目录，覆盖仍须精确版本/摘要校验。未知版本/文件变更拒绝旧适配，不修改安装包。不自动关闭正在工作的 App；保存、手动完全退出，再由控制台启动并打开原聊天。

Windows Hooks 通过编码 PowerShell 调用当前独立解释器，保留路径中文、空格、引号。安装及信任仍须菜单确认；初次主机适配未注册真实 Hooks。Windows 不运行旧 Mac 激活流程；配对 IP、证书、防火墙可达性须针对实际主机检查，复制配对不证明新电脑能连接。

## 证据与下一步

- 初次主机检查通过 App 版本及四项文件摘要，只读枚举 COM4；当时未开串口或读取设备固件。后续升级为独立证据。
- 初次 Controller 265 项：249 通过、16 平台/权限跳过；工具 19 项：15 通过、4 符号链接跳过。真实本机传输用例覆盖首答、分页 Allow/Deny、取消及 submitted，但后端/设备为合成对象，不是原 App/设备验收。
- 初次完整日志留在 ignored `controller/private/windows-host-tests-20261103.log`、`windows-tools-tests-20261103.log`，不发布。
- Git Bash 下 35 个 macOS shell 入口语法检查通过，不等于 macOS 运行或 C/Swift 编译验收；Windows `.cmd --check-only` 实际通过。
- 新用例覆盖 Windows 鉴权、DACL 拒绝、单实例、COM 过滤、Hook stdin/中文引号路径、原生 relay 参数/退出码，包括中文、空格、引号、尾反斜杠和 shell 元字符。
- 后续安全维护修复实际运行 274 项 Controller（16 skipped）；分块读取修复 280 项（16 skipped），补块间 `no_reset` 断言后 6 项局部复测通过。这些是既有结果，本次 Markdown 阶段不重新宣称运行。
- 初次适配不重启 App、不启真实 Bridge、不刷机、配网、清零、改账户、注册 Hooks；后续用户确认 Windows 升级另记。本阶段只改 Markdown，已获 commit/push 授权，控制台及固件语言分别后续处理。
- 下一步保存工作后从 `.cmd` 菜单 1 启动，确认“App 实体审批已接入”，在原聊天实测设备/电脑 Allow/Deny；再补 Windows 10、本轮 macOS 和休眠重连证据。

[官方 App Server 参考](https://learn.chatgpt.com/docs/app-server)说明 stdio JSONL/审批；[Windows App 参考](https://learn.chatgpt.com/docs/windows/windows-app)说明产品环境。内部开关及本机摘要来自安装文件核查；协议存在不证明原 App 接入已实机通过。本阶段未重新核对这些外部参考。

# macOS / Windows 主机适配

维护日期：2026-11-03（Australia/Sydney）。本次授权新增 Windows 10/11 主机适配，同时保留 macOS；不迁移或替换 Mac 产品，也不删除原入口、固件和 Swift Demo。

## 后续更新：Windows 固件菜单已接入（尚未实机刷写）

以下表格及证据章节保留初次适配阶段的记录。后续修复已将菜单 7 接到 `scripts/firmware_update.py`：1 构建，2 检查镜像，3 USB 安全升级，4 准备独立 esptool 4.8.1。使用已有 ESP-IDF 环境或 WSL 中的 ESP-IDF 5.5.3，USB 始终由 Windows 访问；没有另加顶层启动脚本。升级不是下载 GitHub 最新固件，而是校验本机构建镜像与当前源码一致。

当前 Windows 缺少私有 `controller/firmware/main/pet_assets.h`。先从原 Mac 私有备份恢复这个文件，保留 Apple 原版表情；不上传。再从菜单 7→1 构建、7→2 校验、7→4 准备刷写环境、7→3 输入 FLASH。缺素材或镜像过期时提前拒绝，不停止 Bridge。实际升级双读完整备份、核对设备/live 分区，仅写应用并验证；完成后菜单 2 恢复 Bridge。需要 USB 数据线及唯一目标设备。未实机验证这套 Windows 升级流程。

## 平台与验证范围

| 能力 | macOS | Windows 10/11 |
|---|---|---|
| 日常入口 | `controller/Codex Companion 控制台.command`，保留 | 新增同名 `.cmd`，双击运行 |
| Python | 原有独立环境与 `env.sh` | Python 3.11+ / OpenSSL 3；独立 `private/bridge-venv-windows` |
| 主机私有通信 | 原有 Unix socket、0700/0600、flock | 仅 127.0.0.1 随机端口、每次启动随机鉴权、当前用户 DACL、Windows 文件锁 |
| 桌面接入 | 原有版本及摘要登记保留 | 单独登记 Windows App 26.1027.30824（MSIX 26.1027.3384.0）的四个启动文件摘要 |
| relay | 原 `.command` | 私有环境生成原生 `.exe`，共用 stdio relay 和 Broker |
| USB 候选 | 保留 `/dev/cu.usbmodem*` | 按 VID/PID 303A:1001 枚举 ESP32-C3，拒绝随意选择 COM 设备 |
| Wi-Fi 配对、计量、费率、Hooks | 共用实现 | 共用实现，补 Windows IP 查询、OpenSSL 发现、Hook 命令与文件权限 |
| 归档 / 本地迁移 | 保留原功能 | 补 DACL、Windows 环境准备；排除 Windows venv、机器专属 relay；不复制 auth.json |
| 固件菜单更新、ESP-IDF 构建 | 原安全流程保留 | 尚未移植并验收整套流程；菜单 7 提示限制，不调用 macOS 脚本 |
| Swift Demo | 原 macOS Demo 保留 | 无 Windows 版，不计入硬件 Bridge 支持 |

本轮真实开发环境是 Windows 11 Pro / Python 3.12.10。Windows 10 是实现目标，尚无 Windows 10 主机运行证据；Windows CI runner 也不能替代 Windows 10/11 实机验收。macOS 本轮无法实跑，旧验收证据保留，新增双平台 CI 配置尚未提交、上传或运行。

## Windows 使用

安装含 pip、venv、Tcl/Tk 的 Python 3.11+，再双击 `.cmd`。环境准备只在本机创建 venv、校验仓库内固定 SHA-256 wheel 并生成 relay，不下载替代固件，不启动 App 或设备维护。控制台仍通过菜单 1 显式启动 App/Bridge。

从项目根目录只准备或检查：

```powershell
$env:PYTHONUTF8 = '1'
python controller/scripts/setup_windows.py --setup-only
python controller/scripts/setup_windows.py --check-only
& './controller/private/bridge-venv-windows/Scripts/python.exe' -m unittest discover -s controller/tests -v
& './controller/private/bridge-venv-windows/Scripts/python.exe' -m unittest discover -s tools -p 'test_*.py' -v
```

`.cmd` 默认调用 `python`；多 Python 环境可设置 `CONTROLLER_MODERN_PYTHON` 为完整解释器路径。`CONTROLLER_OPENSSL` 可指定 OpenSSL 可执行文件；默认从 PATH 或 Git for Windows 安装目录发现。Python 自带 TLS 库与配对时的 OpenSSL 命令行工具是两个依赖。

默认从当前用户的 OpenAI.Codex MSIX 包发现 App，`COMPANION_DESKTOP_APP` 可显式指定包含 `ChatGPT.exe` 和 `resources` 的 `app` 目录；覆盖路径仍要通过精确版本/摘要校验。未知版本或文件变化拒绝启用旧适配，不修改安装包。当前 App 正在工作时，程序拒绝自动关闭；保存工作并手动完全退出后，再从控制台启动并打开原聊天。

Windows Hook 命令通过编码后的 PowerShell 命令调用当前独立解释器，避免路径中的中文、空格与引号丢失。安装及信任仍通过现有菜单确认，本轮未注册真实 Hooks。Windows 不执行旧 Mac 运行目录激活程序；配对 IP、证书与防火墙可达性必须针对实际主机检查，复制旧配对不代表新电脑可连接设备。

## 当前证据与下一步

- 本机 App 版本和四项启动文件摘要校验通过；只读 USB 枚举发现 COM4。未打开该串口，没有从设备读取固件版本。
- Controller 265 项中 249 项通过、16 项按平台/权限跳过；工具 19 项中 15 项通过、4 项符号链接测试跳过。通过真实本机传输的用例包含双端首答生效、分页 Allow/Deny、取消及 submitted 回执；后端与设备均为合成对象，不能记为原 App/设备实机验收。
- 本机完整测试日志保存在 ignored 的 `controller/private/windows-host-tests-20261103.log` 与 `windows-tools-tests-20261103.log`；不随源码发布。
- 35 个 macOS shell 入口在 Git Bash 下语法检查通过；这是语法检查，不是 macOS 运行或 C/Swift 编译验收。Windows `.cmd --check-only` 实际通过。
- 新增 Windows 鉴权、DACL 拒绝、单实例锁、COM 过滤、Hook stdin/中文引号路径和原生 relay 参数/退出码用例；专门覆盖中文、空格、引号、尾反斜杠及 shell 元字符。
- 本轮不重启现有 App，不启动真实 Bridge，不刷机、配网、清零、改账户、注册 Hooks、提交或推送。当前设备仍保留原固件。
- 下一步需保存当前工作、从 `.cmd` 菜单 1 启动，确认“App 实体审批已接入”，在原聊天实际验证设备/电脑 Allow 和 Deny。再分别补 Windows 10、macOS 本轮回归与休眠重连证据。

官方 [App Server 文档](https://learn.chatgpt.com/docs/app-server)说明 stdio JSONL 与审批协议；[Windows App 文档](https://learn.chatgpt.com/docs/windows/windows-app)提供 Windows 产品环境说明。内部启动开关与本机摘要来自安装文件核查；官方协议存在不代表这套原 App 接入已完成实机验收。

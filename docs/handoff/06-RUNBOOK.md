# 运行、诊断与测试手册

简体中文（默认） · [English](06-RUNBOOK.en.md)

适用源码：固件 `0.2.13`、Bridge `0.2.13-native-app`。当前部署与验收记录见[项目状态](01-PROJECT-STATE.md)，历史测试次数不作为本次运行结果。

## 日常启动

每平台每种语言一个入口：macOS 为 `controller/Codex Companion 控制台.command`，Windows 为同名 `.cmd`。Windows 环境准备、只读检查及测试命令见 [双平台说明](11-HOST-PLATFORMS.md)；菜单 7 现已支持双平台安全固件维护。第二阶段已新增独立英文 `Codex Companion Console.command` / `Codex Companion Console.cmd`，覆盖菜单、子工具、费率窗口及 PC 日志；中文入口保留并固定中文。运行方式及验证边界见[PC 端语言说明](12-HOST-LANGUAGES.md)。设备语言留到第三阶段。

| 菜单 | 操作 |
|---|---|
| 1 | 启动经过精确版本与摘要校验的 App、relay 和 Bridge |
| 2 → 1 | 只读诊断设备与 App 连接 |
| 2 → 2 | 安全重启 Bridge；App 未运行时使用完整启动链 |
| 2 → 3 | USB 恢复或重新配置 Wi-Fi |
| 3 | 首次配对或更新 Wi-Fi |
| 4 | 本机模型费率、来源、长上下文和倍率 |
| 5 | 计数、最近一小时只读核对、确认后清零本机计数 |
| 6 | 注册或修复 Hooks，随后人工审阅信任 |
| 7 | USB 固件备份与应用更新 |

App 已运行时，2 → 2 只重启 Bridge，不能把普通启动的 App 自动接入 relay。若 App 未经适配入口启动，应保存工作并macOS 手动 Command+Q、Windows 使用 App 退出操作完全退出，再用菜单 1 启动并打开原聊天。程序不自动关闭用户工作。

有待处理审批时不得重启或配网。App 进程探测失败时停止操作，不将“无法探测”当作“App 已退出”。

## 连接状态

- “无线同步正常”：设备与 Bridge 已同步。
- “App 已连接 · 等待会话”：relay 存在，尚未确认原聊天接入。
- “App 实体审批已接入”：relay 和会话已连接；仍需实际请求验证审批功能。
- “App 审批尚未连接”或启动日志“等待启动适配接入实际 App 会话”：审批链路尚未建立。
- “在 PC 端确认”（历史提示为“在 Mac 确认”）：需要电脑端处理，不是设备批准成功。

设备在线、单条 `UserPromptSubmit`、模型同步或 Token 同步均不能单独证明真实 Allow/Deny 验收完成。审批提交、工具返回和任务成功须分别判断。英文文档解释现有设备提示的含义；本阶段不修改固件文字。

## 断线与改网

1. 先检查 Bridge、relay、设备状态和 PC 端当前局域网 IPv4。
2. 地址不再匹配配对 URL 时，重启不能修正证书与设备配置；需 USB 配对流程。
3. 配对脚本先打开 USB 并等待稳定 hello，再由设备连接页短按确认开放 60 秒窗口。
4. 收到保存回执并确认 Wi-Fi 同步后再拔 USB。可配置路由器 DHCP 地址预留。
5. USB termios 或网络沙箱受限时，保留具体错误，由获准环境运行；不得关闭 TLS 校验或无限延长离线阈值。

macOS 迁移标记 `controller/private/runtime-migration.json` 存在时，菜单 1 进入受保护切换流程。先手动退出 App，备份并精确替换旧 Hook 路径，停止旧服务后同步最新账本。新路径仍需人工审阅信任。不得同时运行新旧 Bridge。Windows 不激活旧 Mac 账户或配对。

## 主机测试

以下命令从仓库根目录执行，使用 `env.sh` 选定的 Bridge Python：

```sh
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

TCP/Unix socket 测试需要本机权限；沙箱拒绝不是业务断言失败，应在获准环境重跑并保留两次结果。Swift 缓存可通过 `COMPANION_BUILD_CACHE` 指定。C 音频检查使用 mocked BSP/RTOS，不能称为扬声器实机验收。

## 构建与设备维护

固件需要 ESP-IDF 5.5.3；macOS 先载入其 `export.sh`。有已锁定离线组件时可配置 `PASSPORT_DEPS`，然后执行：

```sh
bash controller/scripts/build.sh
```

构建不刷机。macOS 镜像综合检查 `controller/scripts/check.sh` 额外需要 `CONTROLLER_FLASH_PYTHON`（esptool 4.x）。Bridge 与刷写解释器分别选择，维护入口在停服务前检查依赖。

Windows 菜单 7→1 使用现有 ESP-IDF / WSL 构建，7→2 校验镜像与当前源码，7→4 准备独立 esptool 4.8.1，7→3 输入 `FLASH` 才开始安全 USB 更新。要求原版私有表情及匹配源码指纹，USB 始终由 Windows 访问。

设备更新通过菜单 7 及各平台原有受保护流程：测试与 manifest 校验、人工确认、停止 Bridge、双读完整备份、现场分区校验、仅应用更新及回读验证，再连接原 App。设备已报告目标版本时，不能为加载纯 Bridge 修复重复刷机。Windows 使用 256 KiB 读取块与有上限的只读重试；备份失败不进入写入。用户已确认修复后的 Windows 升级及基本目视检查，无需重复刷写。具体安全要求见[硬件与刷写](04-HARDWARE-AND-FLASH.md)。

## 指定区间的只读对账

控制台默认核对最近一小时。导出文件路径及时间区间需显式传参：

```sh
source controller/scripts/env.sh
"$CONTROLLER_BRIDGE_PYTHON" controller/scripts/audit_usage.py \
  --provider-log /absolute/path/to/export.csv \
  --since '2026-11-01T00:00:00+11:00' \
  --until '2026-11-02T00:00:00+11:00'
```

Windows 用 `controller/private/bridge-venv-windows/Scripts/python.exe` 执行同一脚本与参数，导出路径使用本机绝对路径。示例日期仅演示带时区参数，不代表实际账期。对账不修改账单；缺失、未读完、截断或已轮换的本机记录必须报告扫描未完成。

## 环境与运行证据

macOS 已记录独立 Homebrew Python 3.12 环境，Windows 使用本机独立私有 Python 环境。所有 shell 入口通过 `CONTROLLER_BRIDGE_PYTHON` 选择 Bridge Python；不得用 prepared 回执代替实际激活记录。

`--restart-app` 需要用户自行保存工作并退出 App；启动后 `private/active-python.json` 记录所选解释器。该回执不证明后续每个补丁已加载，也不证明实机验收。Tcl/Tk 导入检查不覆盖价格编辑器的人工交互全流程。

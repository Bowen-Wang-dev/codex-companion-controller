# PC 端语言与独立入口

简体中文（默认） · [English](12-HOST-LANGUAGES.en.md)

维护日期：2026-11-03（Australia/Sydney）。这是双语工作的第二阶段：PC 端用户交互。第一阶段文档提交为 `48603c8`；第三阶段现已补上 0.2.14 设备安装语言及配套保护，见 [设备语言](13-DEVICE-LANGUAGES.md)；下述未改固件的描述保留第二阶段边界。

## 选择入口

| 平台 | 中文（默认） | English |
|---|---|---|
| Windows | `controller/Codex Companion 控制台.cmd` | `controller/Codex Companion Console.cmd` |
| macOS | `controller/Codex Companion 控制台.command` | `controller/Codex Companion Console.command` |

双击所需语言入口即可。两个语言版本分别运行，共用同一套配对、费率、账本、依赖及安全检查；切换入口语言不复制配置、不建立第二份服务，也不改变账户。存在运行中的 Bridge 时仍使用原有单实例保护，不能并行启动两种语言的 Bridge。已有进程不会因文件更新自动切换语言；下次通过所选入口启动或安全重启时生效。

Windows 批处理使用 UTF-8 代码页及 CRLF；`.command` / `.sh` 使用 LF，仓库 `.gitattributes` 固定换行。入口固定 `COMPANION_LANGUAGE=zh-CN` 或 `en`，传给环境准备、子菜单、App 启动链和 Bridge。macOS 私有环境配置不会覆盖入口选定语言。未设置或不识别语言值时使用中文。

## 英文覆盖范围

- 主菜单、设备/Bridge 诊断、连接恢复、启动/重启提示及取消/错误回执。
- USB 配对引导、网络输入提示及校验错误；Wi-Fi 密码仍隐藏输入。
- Token 统计、只读对账、清零提示，以及模型费率窗口的标题、字段、帮助、保存和输入校验。
- Hooks 注册/信任提示、Windows 固件维护菜单、镜像校验/备份进度，以及 macOS 菜单 7 的维护引导。
- PC 端 Bridge 的连接、握手、无线诊断及事件日志。费率窗口支持纵向滚动，并按屏幕高度限制初始窗口，便于阅读较长英文。

`YES`、`RESET`、`FLASH`、菜单编号、参数、协议字段和文件路径保持不变，不翻译成其他确认词。设备审批、原 App 原聊天、精确版本/摘要保护、双备份/live 分区安全更新及首答生效规则继续沿用。设备屏幕、设备下发请求/回执和第三方程序的原始输出不做 PC 界面替换；用户自定义模型名、命令、路径及其他数据按原样展示。系统或第三方错误可能仍使用其自身语言。

## 单独运行与检查

从仓库根目录做 Windows 只读检查：

```powershell
& './controller/Codex Companion Console.cmd' --check-only
```

直接运行 Python 工具时，可自行选择语言；未设置默认中文：

```powershell
$env:COMPANION_LANGUAGE = 'en'
& './controller/private/bridge-venv-windows/Scripts/python.exe' controller/scripts/controller_console.py
```

macOS 日常使用英文入口；直接运行工具时：

```sh
export COMPANION_LANGUAGE=en
source controller/scripts/env.sh
"$CONTROLLER_BRIDGE_PYTHON" controller/scripts/controller_console.py
```

选择任一正式语言入口会以该入口的固定语言覆盖继承的语言设置。只读检查不打开串口，不启动或关闭 App/Bridge；环境准备会核验并启用现有离线依赖。

## 实际验证与边界

新增回归覆盖两种语言的真实控制台进程、真实 Windows CMD 参数/退出码、子菜单取消、`RESET`/`FLASH` 精确确认保护、语言传递、翻译字典完整性、错误与用户数据隔离、隐藏 Tk 窗口英文控件/宽度、临时费率保存/校验及 UTF-8 模型名读取。合成 Broker 用例确认英文 PC 日志不会改变中文设备请求或批准能力。

Windows 英文 CMD 的真实 `--check-only` 通过，输出没有中文界面文本。WSL 下五项隔离 shell 回归通过，覆盖 macOS 两语言入口、私有配置不覆盖语言、维护流程与失败前置保护；假解释器不操作设备，这不是 macOS 实机验收。Python 3.11 语法兼容检查通过。

本阶段最终 Windows Controller 回归：295 项，OK（18 skipped）；其中 13 项 PC 语言回归通过，包含真实 CMD/隐藏 Tk 临时配置检查。WSL 五项隔离 shell 回归通过；英文 CMD 真实 `--check-only`、48 个 Python 文件的 3.11 语法兼容、全部 shell/command 语法及 60 个 Markdown 本地链接检查通过。macOS 本机运行、真实 App/设备全流程及人工 GUI 验收仍未覆盖。

本阶段未启动真实 App/Bridge、未刷写、配网、清零、注册 Hooks 或改账户。完整 Windows/macOS GUI 人工流程、真 App/设备双端矩阵及第三阶段固件英文仍须分别验证。测试仅使用临时配置及合成请求，原始日志保存在 ignored `controller/private/stage2-*.log`。

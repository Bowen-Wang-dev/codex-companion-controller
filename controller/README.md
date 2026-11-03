# Controller 使用说明

简体中文（默认） · [English](README.en.md)

适用源码：固件 `0.2.13`、Bridge `0.2.13-native-app`。文档维护日期：2026-11-03（Australia/Sydney）。部署与实机验收以[项目状态](../docs/handoff/01-PROJECT-STATE.md)为准，不能仅凭源码版本判断运行状态。

## 日常操作

macOS 双击 `Codex Companion 控制台.command`；Windows 双击同名 `.cmd`，每平台每种语言一个日常入口。共用控制台与审批逻辑，Mac 原实现保留。具体菜单及接入条件见[运行手册](../docs/handoff/06-RUNBOOK.md)，Windows 安装、当前测试与限制见[双平台说明](../docs/handoff/11-HOST-PLATFORMS.md)。历史 macOS 脚本集中在 `维护工具/`。第二阶段已新增独立英文 `Codex Companion Console.command` / `Codex Companion Console.cmd`，覆盖菜单、子工具、费率窗口及 PC 日志；中文入口保留并固定中文。运行方式及验证边界见[PC 端语言说明](../docs/handoff/12-HOST-LANGUAGES.md)。设备语言留到第三阶段。

审批可在设备或原 App 原生卡片操作，首个有效答复生效。详情页长按交接已在 v0.2.13 移除；二次确认页的长按提交保留。设备拒绝或失败直接显示 😭，批准反馈必须对应实际提交回执。表情、三键及分页规范见[交互契约](../docs/handoff/03-UX-CONTRACT.md)。

若设备在线但显示“App 审批尚未连接”，先检查 App 是否通过已核对入口启动并打开原聊天。不得通过反复刷机、延长离线窗口或取消版本检查处理该问题。

## Bridge 环境

- Python 3.11+、OpenSSL 3；本机已记录独立 Python 3.12 venv。
- macOS 的 `scripts/env.sh` 统一选择 `CONTROLLER_BRIDGE_PYTHON`，本机路径保存在 ignored 的 `private/local-env.sh`。
- macOS 首次准备需显式配置可用的 `CONTROLLER_MODERN_PYTHON`；`bash controller/scripts/setup_bridge.sh` 校验并启用 vendor 中固定摘要的 pySerial / websockets wheel。
- Windows `.cmd` 调用 `scripts/setup_windows.py`，创建 `private/bridge-venv-windows` 并生成私有原生 relay；`CONTROLLER_MODERN_PYTHON` 可选择启动解释器。
- macOS Hook 客户端使用系统 Python，Windows Hooks 使用选定的独立解释器；Bridge 的 TLS 与依赖运行环境独立于 ESP-IDF Python。

macOS 主机检查从仓库根目录执行：

```sh
source controller/scripts/env.sh
"$CONTROLLER_BRIDGE_PYTHON" -m unittest discover -s controller/tests -v
python3 -m unittest discover -s tools -p 'test_*.py'
bash tools/check-host.sh
zsh mac-demo/test.sh
```

Windows 环境准备及检查：

```powershell
$env:PYTHONUTF8 = '1'
python controller/scripts/setup_windows.py --setup-only
python controller/scripts/setup_windows.py --check-only
& './controller/private/bridge-venv-windows/Scripts/python.exe' -m unittest discover -s controller/tests -v
& './controller/private/bridge-venv-windows/Scripts/python.exe' -m unittest discover -s tools -p 'test_*.py' -v
```

测试中的 TCP/Unix socket、合成账单及 mocked BSP/RTOS 不代表实机、服务商或 GUI 全流程验收。

## 固件构建与镜像检查

固件需要 ESP-IDF 5.5.3、ESP32-C3 工具链及锁定组件。macOS 先载入 ESP-IDF 的 `export.sh`，再从仓库根目录执行：

```sh
bash controller/scripts/build.sh
```

Windows 菜单 7→1 复用现有 ESP-IDF 或 WSL ESP-IDF 5.5.3，USB 由 Windows 访问。构建输出位于本机 `controller/private/build/`（或 `private/build-windows/`）与 `controller/dist/`。构建不更新设备。现场分区事实由安全更新脚本读取，不能用仓库构建分区表替代。

macOS 的 `scripts/check.sh` 额外检查本地镜像，需要配置 `CONTROLLER_FLASH_PYTHON`（esptool 4.x）；与 Bridge Python 分开选择，不依赖 Terminal 存在裸 `python` 命令。Windows 菜单 7→2 检查镜像版本、芯片、大小、摘要、当前源码绑定及原版素材；7→4 准备独立 esptool 4.8.1。镜像检查不打开串口。

## Apple 图像与字体

公开源码不含 Apple 原图、生成图片头或含图固件。无素材构建会显示素材缺失提示，安全更新入口拒绝使用这种镜像。

已取得适用素材权利时，可从仓库根目录导入原图；此步骤需要所选 Python 环境安装 Pillow：

```sh
/path/to/image-python controller/scripts/import_assets.py \
  --source /absolute/path/to/authorized-originals \
  --rights-file /absolute/path/to/rights.json
```

素材名为 `idle`、`working`、`permission`、`delight`、`crying`、`completed`、`neutral`、`palms`，扩展名均为 `.png`。rights 文件需包含 `apple_original: true` 和非空 `rights_basis`。脚本只进行缩放与 RGB565 转换，不下载、重绘或替换表情风格。

`scripts/build_personal.sh` 使用本机系统渲染路径；该能力不代表已取得公开分发许可。生成内容只保留本机。中文字体清单见 `docs/ui-font.json`，第三方许可见 `licenses/`。

## 设备更新与恢复

设备维护通过控制台菜单 7，要求唯一 USB 目标、可用工具链、镜像摘要与版本一致、无待处理审批。执行双读完整 8 MB 备份、现场分区及安全状态校验后，只更新受支持的 factory 应用并回读验证；不写 bootloader、分区表或已有 NVS，不整片擦除。

Windows 以 115200、256 KiB 分块读取，关闭块内刷屏进度；只读最多三次尝试，末次 ROM 回退。失败块丢弃，块间保持应用停止；写入不自动重试。用户已确认 Windows 升级及基本目视检查完成，不扩展为全部审批或长期稳定性验收。

恢复必须匹配备份目录的 `last-write.json` 和当次原始镜像，限定在已记录应用区间；不得根据通用 IDF 输出直接刷写。完整边界见[硬件与刷写](../docs/handoff/04-HARDWARE-AND-FLASH.md)。本次文档阶段不执行更新或恢复。

## 计量与私有数据

费率按精确模型 ID 匹配。内置价格是快照，不自动更新；自定义费率和倍率以本机配置为准。输入包含缓存，输出包含推理；五类互斥分项只累计一次。长上下文按逐请求输入判档，不能按整轮总数推断。

控制台菜单 5 提供最近一小时只读核对；指定 CSV/TSV 路径及时间区间需使用 `scripts/audit_usage.py --provider-log`。对账是本地核对，不是服务商总账 API。清零仅影响本机计数及估价，需要单独确认。

`private/` 含配对、证书、账本和恢复备份，应保持私密。迁移不复制 Codex `auth.json`；归档将源码与私有恢复包分开。具体规则见[迁移与隐私](../docs/handoff/07-MIGRATION-AND-PRIVACY.md)。

## 历史记录

审查前的阶段性说明保存在[Controller README 历史快照](../docs/history/controller-readme-before-2026-11-02-review.md)，其中旧路径、旧版本限制和当时未验收结论不覆盖当前规范。历次真实验收及功能沿革继续保留在发布说明和交接记录中。

现行译本及历史原始证据的区别见[文档索引](../docs/README.md)。

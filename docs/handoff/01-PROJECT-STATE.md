# 项目现状与验收边界

日期：2026-11-02（悉尼）；基于归档时的本地文件。

## 2026-11-02 新目录 Bridge 已激活
- 用户已完成手动退出 App 和 Terminal 确认。私有 `runtime-activation.json` 记录 2026-11-02 01:07:29 +1100 激活：最新账本已同步，Hooks 已迁移；待迁移标记已移除。
- 本次只读进程与 IPC 核验：Bridge、stdio relay、launch_desktop 均运行在 `/Users/bowen/Developer/codex-companion-controller/controller`；旧 outputs 工程 Bridge 不再运行。
- 新 Bridge 实测设备 Wi-Fi online=true、固件 0.2.11，desktop.connected=true、approval_receipts=true、session_count=2。七类用户级 Passport Hooks 全部指向新工程，未见旧路径命令；配对 IP 仍匹配当前 Mac。此为瞬时状态，不代表长期稳定性。
- 安装 App 26.1027.30824 的登记摘要再次核验通过。私有配对、证书、费率保持原值，旧工程保留；切换前账本及 Hooks 备份在 private/activation-backup-*。
- 新增 6 项 synthetic/mock 切换回归、既有连接恢复 8 项、通知/Hooks 14 项通过（共 28 项，上一轮实际运行）；本轮为只读核验与文档更新，未重复跑代码测试。
- **本次真实设备验收通过**：迁移后原 App 聊天经 PermissionRequest Hook，设备 Allow 后独立验收文件实际写入，设备 Deny 后工具返回 `PermissionRequest hook denied approval` 且目标文件不存在。用户确认两次均仅实体按键，批准 😆、拒绝直接 😭（无 😶）；验收文件已清理，证据在 private/hardware-acceptance-20261102-*.json。这是真实设备测试，非 mock。
- **仍待验收**：native stdio relay 独立 `approval/submitted` 提交回执（本次 Allow 的 last_device_decision.source=hook，last_device_delivery=null，不能据此宣称 native relay 全链路通过）、重启/休眠后重连、所有权限类型和长期稳定性。Hook 路径信任已至少对本次 PermissionRequest 生效，不扩展声称所有 Hook 均已验收。
- Python/依赖收尾：已安装 Homebrew Python 3.12.15、OpenSSL 3.5.9、Tk/Tcl 9.1，独立环境为 private/bridge-venv-homebrew；pySerial 3.5 与 websockets 17.3 均从本工程 vendor 的 SHA-256 校验 wheel 离线加载，pip check 通过。local-env.sh 与所有 shell 入口统一选择 CONTROLLER_BRIDGE_PYTHON，不再为未来启动依赖 Codex cache。
- **激活边界**：本轮不自动关闭当前 App；已运行的旧 Python 进程须在用户手动退出并由新入口重开后才换用新环境。private/python-runtime-prepared.json 是准备证据，private/active-python.json 在实际新启动后生成；未看到后者及新进程前不可声称运行中进程已切换。旧 venv 保留回退，Hook 命令文件未改。
- 日常仍仅使用 `controller/Codex Companion 控制台.command`。项目保持暂停，不因迁移成功自动开始功能开发或刷机。

## 版本与证据
| 项 | 状态/证据 |
|---|---|
| GitHub 基线 | `00b61330f1b415b555d8acde8ddd4a6d055c48d0`，main；包含统一控制台和 Token 分项 |
| 固件 | 0.2.11；本地含图镜像 2,360,240 字节；SHA-256 `5a9d882e2245b60e3e234d090714c550feb9b075c3a54458a3ee15db83885473` |
| 实际刷写 | 旧运行目录 private/backups 下 2026-11-01 记录：`last-result.json` 的 verified=true，last-write 的镜像摘要吻合；仅 factory、未写分区表/bootloader、未整片擦除 |
| Bridge | 源码为本项目 Python Bridge；部分启动/诊断仍显示 0.2.10 标签，不可单看这个标签判断功能 |
| Mac Demo | SwiftUI/AppKit 0.4.0；模拟任务/额度，不能作为真实 App 审批验收 |
| 桌面 App 适配 | 明确登记 26.1016.62342、26.1027.30824，校验入口/分块摘要；未知升级拒绝套用 |
| 既有主机结果 | 上一轮本机/可分享树各 217 Python 检查通过，控制器/音序/8 组音频检查通过，ESP-IDF 5.5.3 构建成功；这不是本次重新运行结果 |
| 归档/迁移 | Developer 文件迁移及新运行目录激活均已核验；340 文件复制校验记录见根下 LOCAL-MIGRATION-RECEIPT.json，运行切换记录见 controller/private/runtime-activation.json |

## 已有真实设备验收
- 旧已核对 App 原聊天的目录写权限：设备 Allow/Deny 双向通过；网络权限：设备 Allow 通过，回执与真实工具授权对应。
- 用户确认过长请求浏览到末页再选择、中文无方框、批准后 😆。
- 2026-10-31 更换网络后，通过 USB 重新配对，拔 USB 后 Wi-Fi 在线；短时采样无掉线/HTTP 错误。
- 0.2.11 已有写入/回读校验记录；这只证明镜像写入完整，不证明每个新页面已经用户验收。

## 仍不可声称完成
- 新 App 26.1027.30824 的全链路设备审批，所有权限类型、所有项目和长时间运行，不因旧版本测试而自动验收。
- 0.2.11 分项数字/金额在真屏的排版、精度、未知值和中文字体完整性。
- 新控制台各菜单的真实 GUI 全流程；单元测试不覆盖所有组合。
- 服务商账户总账实时读取。现有本地估价+可选 CSV/TSV 对账不是总账 API。
- Apple 原图或含图固件的公开分发许可。
- App/Bridge 关闭重开及休眠生命周期、native relay 独立提交回执和所有权限类型的全流程验收；新路径 PermissionRequest Hook 设备 Allow/Deny 与表情已真实验证。

## 已知需复核的实现边界
- OpenAI 预设目前仅内置明确核对的 gpt-6.1-sol；模型/价格会变化，未来调整需查当时官方文档。自定义价格优先尊重用户。
- 某些旧私有账单没有 reasoning 细分，导入适配以 0 表示该字段；因此“可见输出/推理”分项可能不完整，不能把它当真实无推理的保证。
- 缓存写入实现只有一条费率；官方可能按不同 TTL 收费，需未来扩展真实明细，不可伪造。
- 控制台菜单曾声称“账单导入”，实际菜单目前只提供默认最近一小时审计；带 CSV/TSV 路径需调用 audit_usage.py --provider-log。

## 2026-11-02 本地归档与依赖收尾
- 用户确认 Hooks 已确认，并授权本地归档及 Python/依赖整理。没有推送或上传授权，源码仅本地 commit。
- 新 Python：完整 controller Python 回归 227 项通过（socket 用例在获准本机网络权限后跑）；迁移/归档工具 10 项通过；C 控制器、音序及 8 组 mocked BSP/RTOS 音频运行检查通过。Tk/Tcl 导入与 Tcl 解释器初始化、pip check 通过；未据此声称 GUI 全流程或新 Python 下实机授权已验收。
- 修复迁移器 destination.absolute 与 source.resolve 混用导致的 macOS /var→/private/var 路径别名子目录检测漏洞；原有“目标不能位于源内”回归现已通过。
- 归档目标为 `/Users/bowen/Developer/codex-companion-archives/2026-11-02-python-handoff`：源码 tar.gz、Git 历史 bundle、独立 PRIVATE-RECOVERY.tar.gz、恢复说明、摘要回执。以目标 ARCHIVE-RECEIPT.json 存在且摘要可复核为成功依据；私有包回读校验每个成员，不含 Codex auth.json、venv、缓存或运行日志。
- 私有归档为服务运行期间逐文件快照，JSON 完整解析校验，不是全局停机事务快照；同盘独立目录不是异地备份。保持本机私密，不公开私有素材/含图固件或密钥。

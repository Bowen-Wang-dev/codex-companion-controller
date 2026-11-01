# 项目现状与验收边界

日期：2026-11-02（悉尼）；基于归档时的本地文件。

## 2026-11-02 Bridge 工具返回回执中文修复（源码完成，待加载）
- 更新后的只读审批测试实际打印 `COMPANION_V0213_APPROVAL_TEST`，人工反馈操作正常，随后报告设备批准后出现英文工具回执。未独立读取本次部署版本或采集双端完整验收矩阵，不把单次允许扩展为全部新版实机验收。
- 定位 `service.py` 的普通 `PostToolUse` 分支：它将回执写成 `Tool returned on Mac`；Git 历史显示该字面量于 2026-10-25 的 `efb760c` 引入，v0.2.12 已存在，并非 v0.2.13 移除交接时新增。工具返回发生在批准提交回执之后，可能在原 3 秒反馈期间覆盖中文文字；现有记录不能确定此前为何没有注意到该提示。
- 将此回执改为“工具已返回”，不改变事件顺序、表情持续时间或成功/失败判定。普通工具返回不表示授权成功，也不表示任务成功；既有特殊权限结果及匹配命令执行返回分支保持原语义。
- 实际运行 DesktopBrokerTests **11 项通过**，包括新增普通工具返回不伪造授权成功、真实提交反馈期间回执中文且不延长反馈的两项回归。本次未重跑完整回归或重建固件，历史完整 237 项结果属于上一阶段。
- 本次仅修改 Bridge 文案及测试，不改固件，不刷机、不重启当前 Bridge。通过唯一控制台主菜单 2 → 子菜单 2 安全重启 Bridge 后加载修复；保留原 App、聊天和配对，随后实机确认此条回执中文。

## 2026-11-02 桌面 App 接入修复：菜单 2→2 补齐启动链
- 运行日志确认设备已连接并报告固件 0.2.13，但 Bridge 状态为“等待启动适配接入实际 App 会话”，随后仅收到 `UserPromptSubmit`/`SessionEnd`，没有稳定的 desktop relay 心跳、模型事件或 Token 用量事件。设备“无线同步正常”只代表 HTTPS 链路，不能代表原 App 审批已接入。
- 根因是统一控制台的设备/Bridge 菜单 **2→2** 直接执行 `bridge/service.py --desktop`，只启动 Bridge，不启动经过版本/文件摘要校验的桌面 App 和 relay。App 未运行时会形成设备在线、Bridge 在线、App 审批尚未连接的假可用状态；因此测试命令不会显示在设备上，用量和模型也不会同步。
- 修复：菜单 2→2 现在先检查桌面 App。App 未运行时，安全停止旧 Bridge（若存在）并调用完整 `launch_desktop.py` 启动链；App 已运行时，保留仅重启 Bridge 的行为。启动链仍拒绝未知 App 版本/摘要，不自动关闭用户工作。
- 新增控制台生命周期回归：运行/未运行/探测失败三种状态共 3 项；连接恢复和运行时激活回归共 16 项通过；DesktopBrokerTests 11 项通过。尚未在用户当前 Mac 会话中重新启动 App 或执行新版真实审批，当前日志只证明设备连接，不证明 relay 已接入。
- 文档与入口说明已改为“App 实体审批已接入”才算成功；下一次启动后应先确认该状态，再验证模型、Token 与设备 Allow/Deny。无需重新刷机；该问题属于桌面 App/relay 生命周期。

## 历史阶段：2026-11-02 v0.2.13 源码与构建完成，部署前记录
- 版本规划已在文档提交 `9545223` 留档，现已完成对应代码实现；变更范围仅限 v0.2.13，其余 backlog 暂停。
- 固件删除 `ACTION_MAC`、交接状态、`mac_handoff` 发送、`mac_ready` 解析和交接页面；详情改为“可在电脑查看详情”。详情长按确认及松手无操作，二次确认长按提交 Allow/Deny 保留；普通页面长按确认返回待处理请求的行为保留。
- Bridge 删除交接处理、Hook 交接释放分支、焦点注入、`native_app_ui.py` 及显示回执字段；旧设备发送交接消息按未知消息忽略，不提交审批、不取消请求、不启动 App。原 App 双端直接审批、版本/摘要保护和真实提交回执路径保持。
- 源码版本为固件 **0.2.13**、Bridge **0.2.13-native-app**；启动说明、维护入口和 manifest 校验同步。当前运行环境仍沿用此前已验收的 0.2.12，本轮没有重启 App/Bridge 或刷机，不能声称新行为已实机生效。
- 实际验证：完整 controller Python **237 项通过**（240 项基线上移除已抛弃唤回模块的 3 项测试，原交接测试改为旧消息无副作用测试）；既有 stdio/Unix IPC 集成覆盖设备及原 App Allow/Deny、对端取消与提交回执。C 导航/确认和音序、8 组 mocked BSP/RTOS 音频检查通过；新增 15 组请求形态/选择组合验证长按和松手无误操作。新提示全部字形已存在，shell 语法、版本/manifest/摘要和旧代码 Git 留存核验通过。
- 首次完整回归 18 项因本机 TCP/Unix socket 沙箱权限失败，获准后完整重跑通过；构建提示无法访问组件 registry，沿用现有锁定组件完成 ESP-IDF 5.5.3 构建，没有升级依赖。
- 本机含图镜像 `controller/dist/PassportController.bin` 为 **2,359,568 字节**，SHA-256 `94b52c72ff45a984eccb86aab92b516b47dbf3aa02e0267aabc556e01d5c0e21`。仅本机留存，不上传 Apple 素材或含图镜像；构建不等于刷写或设备功能验收。
- 版本复核：入口与发布文档使用版本规划、功能状态和变更记录表述；历史段落明确标注当时状态，避免“本回合仅文档”等旧表述被误读为当前进度。源码/构建版本与镜像摘要一致，历史 v0.2.12 实现和第 5 项验收仍保留。
- 下一步：通过唯一控制台菜单 7 的现有双备份/live 分区校验与仅应用更新流程部署，再在原聊天实测双端允许/拒绝、详情提示及长按无交接；设备二次确认长按提交仍需真实验证。部署前保持旧运行环境，不清零、重配网或换账户。详见 [v0.2.13](../releases/v0.2.13.md)。

## 历史阶段：2026-11-02 抛弃长按交接，仅提交文档
- 用户反馈更新后设备与原 App 原生审批同时提示、任一端均可操作，实际使用方便，确认采用“听到设备提示音后，按设备或直接用鼠标点电脑”的日常流程，无需转交。
- 详情长按确认“转到 Mac”标注为**已抛弃的历史功能**。功能沿革、历史文档及实机验收不能删除；旧代码由 Git 的 `v0.2.12` 标签（提交 `fb02632`）保留。最新版不再部署或调用这套功能，下一步从固件与 Bridge 中移除交接动作、唤回与显示回执代码，减少无用实现；资源收益未经测量，不宣称具体性能提升。
- 该阶段仅整理版本规划、UX 契约及入口文档；源码、当前运行的 Bridge 和设备固件保持 0.2.12 原状。旧长按动作、`mac_handoff` 协议与激活原 App 的兼容代码尚在，不声称已删除或已部署新提示。没有构建、刷机、重启、配网、清零或发布新版本。
- 现有五项实机证据保留，第 5 项仅说明当时交接功能通过，不再代表现行需求。设备后续仅提示“可在电脑查看详情”，无需转交；双端直接审批、设备分页/二次确认/提交回执继续有效。
- 该规划阶段先完成 Markdown 留档与 commit，再进行固件、Bridge 及相关程序的实现；当时未改代码、构建、刷机、重启或创建版本标签。规划与后续结果见 [v0.2.13](../releases/v0.2.13.md)，其他 backlog 继续暂停。

## 2026-11-02 v0.2.12 五项原生双端实机验收完成，授权发布
- 用户已完成 Bridge 切换；本聊天实际 IPC 确认设备 0.2.12 在线、approval_ui=native_app、desktop.connected=true。不是仅有源码/编译结果。
- 用户逐项操作并确认五项 passed：设备允许、设备拒绝、Mac 原生卡片允许、Mac 原生卡片拒绝、设备详情长按交接唤回原 App 后在 Mac 允许。设备与 Mac 端互相结束审批，交接不自动批准；设备表情由用户确认。
- 第 1 项真实命令成功，source=desktop、choice=allow，与独立 delivery stage=submitted 匹配，补齐此前 native relay 独立提交回执未验收项。第 2/4 项工具返回 rejected by user 且命令未执行；第 3/5 项分别有成功打印标记。仅第 1 项捕获独立回执，不扩展为五项均采集。
- 私有证据为 controller/private/hardware-acceptance-native-20261102.json（0600），源自当前真实工具输出和用户逐项确认；对外发布去身份化的验收矩阵 docs/releases/v0.2.12.md。
- 用户明确要求先更新 Markdown 再发布：源码发布标识 **v0.2.12**，Bridge 修订号 **0.2.12-native-app**，设备固件仍 **0.2.12**。仅发布审计源码/文档，不上传私有数据、Apple 素材或含图固件。发布完成以 origin/main 和远端标签核对结果为准。
- README、controller README、发布说明、运行手册和交接文档已更新；此前“待切换/待验收”和独立窗口段落均属历史阶段，下文历史证据不等同当前状态。
- 其余权限类型、所有项目、文件 diff/附加授权语义、休眠唤醒和长期稳定性仍未覆盖。0.2.12 的交接页可能保守显示等待窗口回执；native 转发不等于界面绘制回执，本次由用户目视确认唤回原 App。

## 历史阶段：2026-11-02 改用原 App 原生审批（当时尚待切换）
- **用户明确不接受单独 Tk/Companion 审批窗口，要求审批显示在当前 ChatGPT/Codex App 原聊天内。** 此版本方案替代下文独立窗口方案；不再增加独立审批界面，不换 CLI/新聊天，不修改 App 安装包。
- 用户已自行更新后，本聊天只读 IPC 实测设备 firmware=0.2.12、online=true、App desktop.connected=true、approval_receipts=true；一次只读查询由旧独立窗口 Hook allow 执行，**这不是原生双端验收**。随后的拒绝验收被用户中止，独立测试文件不存在，不能记录 Deny 通过。
- 已将 `mac_approval_gui.py` 改为不创建任何窗口的兼容空入口（旧运行 Broker 仍可能调用此文件，因此暂留）；新 service 不再导入或启动它，移除 mac_review/mac_decision 私有审批接口和独立窗口页状态。
- 新 Bridge desktop 模式的 PermissionRequest/权限 PreToolUse 不再等待硬件：返回空 Hook 结果，既不批准也不拒绝，让原 App 创建原生审批；随后由现有 stdio relay 原样转发 native request，同时交给设备，同一请求先答者生效。旧 Hook 结果缓存也不能抢先返回 allow。
- mac_handoff 改为仅激活已运行、精确版本/摘要验证通过的原 App；不自动点按钮、不另起聊天。旧非桌面阻塞 Hook 的交接只释放等待以允许原生界面出现。保留 0.2.12 固件兼容，无需本轮重刷；其原有“正在请求 Mac 显示/尚未收到显示回执”提示仍保守保留，不伪造原生界面已绘制回执。
- 核对安装版本 26.1027.30824 的登记摘要通过；从本机官方二进制仅生成 JSON schema，保留该版本 startedAtMs 等校验。查阅官方 App Server 审批/解决事件文档，不将协议支持等同于本机 App 实机成功。
- **本轮完整 controller Python 240 项通过**：移除独立 UI 的 13 项测试，新增 8 项 native routing/缓存/交接/版本检查/空入口用例；既有 2 项“Mac”集成改为原 App 真实协议响应的 Allow/Deny（包括页未读完时 App 答复取消设备）。再补强激活超时处理后相关 8 项通过。数字下降来自移除被用户否定的功能用例，不是删失败用例。
- **待切换/验收**：新 Bridge 源码尚未重启载入；未再触发实机授权测试。用户可用唯一控制台主菜单 2 → 子菜单 2“安全重启 Bridge”，保留当前 App、聊天、现有配对及 0.2.12 固件。此操作需无待审批，现有入口会检查。随后仅验收原 App 审批卡片与设备双端 Allow/Deny；未出现真实 native 回调则继续排查，不退回独立弹窗或声称完成。

## 历史阶段：2026-11-02 独立窗口方案准备与首次更新失败（已被替代）
- **用户首次自行更新在刷写前退出，入口已修复待重试**：用户提供 01:49–01:50 终端日志，完整 242 测试通过后，菜单 7 在第 20 行串口发现阶段报 `python: command not found`。此时尚未停止 Bridge、读取备份或写入设备，不能记为已更新 0.2.12。
- 根因：日常 Terminal 未提供裸 `python` 命令，原维护脚本仍依赖 IDF 环境的隐式 PATH。已将串口发现及 preflight 显式绑定 `CONTROLLER_BRIDGE_PYTHON`；刷写独立使用 `CONTROLLER_FLASH_PYTHON`，在停 Bridge 前验证可执行及 esptool 4.x。env.sh 支持已配置 IDF 环境的显式 fallback，本机 ignored private/local-env.sh 已指向现有 IDF 刷写解释器（Python 3.9.6 / esptool 4.12.0），不安装依赖、不更换 Bridge Python。
- 本轮验证：3 项隔离 shell 回归通过（无裸 python 的 PATH 下正确调度；缺刷写解释器或缺 esptool 时不停止 Bridge/不写入），4 项既有依赖/入口测试通过；最小 Terminal PATH 下真实 esptool import 和 USB 候选发现通过（仅枚举，未开串口）。没有重新跑完整 242 项；没有执行刷写。请用户保持 USB，用同一控制台菜单 7 重试，更新仍未实机验收。
- 用户随后要求自行更新固件并索取命令；核对发现控制台菜单 7 的历史维护脚本仍限定 0.2.11，已更新其说明及 manifest 校验为 0.2.12，shell 语法和本机产物/入口版本一致性核验通过。用户可保持现有 App 打开，经唯一控制台菜单 7 停 Bridge→双备份/live 校验→仅更新应用→启动新 Bridge 接回原聊天；本次 relay 未改，无需为这条路径额外退出 App。下文“退出 App 后重启”是另一种切换路径，不是菜单 7 的前置要求。本轮没有执行更新或连接设备。
- 用户明确提出两项新任务：修复设备“转到 Mac”但 Mac 无界面；同一审批同时显示在电脑和设备，并可从任一端操作。本次授权恢复范围仅限这两项，不自动恢复其余 backlog。
- 根因核对：0.2.11 的 ACTION_MAC 在 main.c 只取消提示音，未发送交接消息；PermissionRequest Hook 在返回前阻塞原 App 审批，所以不能假设原 App 已经显示审批框。
- 新增 `bridge/mac_approval_gui.py`：Bridge 有待审批时自动启动独立 Mac Companion 审批窗口（不是模拟 Demo，也不是修改原 App UI）。通过原私有 Unix IPC 分块读取完整请求，确认后操作同一 pending；共用锁只接受首个审批结果，Mac 阅读不跳过设备本身分页约束。原 App native 审批仍通过原 relay 竞争，未知/缺少 diff 的批准继续留在原 App。
- 固件源码 0.2.12：长按确认发送绑定 boot/epoch/id/digest 的 mac_handoff；等待真实窗口心跳，完整内容显示且窗口可见后才显示“Mac 审批窗口已显示”。收起窗口、重新交接或心跳超时清除已显示状态；普通问题通知仍在原 App 回复，不冒充设备回答。
- 本轮验证：完整 controller Python 242 项通过（包含新增 13 项 Mac 审阅/交接/竞争用例与 2 项 Mac→relay stdio 集成用例）；随后补强显示回执清除和完整内容约束，相关 13 项重跑通过。C 三键导航、音序、8 组 mocked BSP/RTOS 音频检查通过。合成 Tk 窗口完整详情/按钮、收起/唤回、二次确认/提交检查通过；C UA 截图读取超时，未声称截图目视 QA 或实机验收。
- ESP-IDF 5.5.3 构建成功；本机含图 0.2.12 镜像 2,360,544 字节，SHA-256 `dae8c7c2dacea383f0c3deb3cbc9ac3a0d78faa653151faf2b73e1338053de04`。新增固件文案字形覆盖检查通过。含图产物仅保留本机，不公开。
- 首次完整测试 16 项因 socket sandbox 拒绝；获准本机网络后完整回归通过。首次构建无法访问 Espressif registry；获准后按锁定版本构建成功，没有升级依赖。
- **尚未生效/验收**：没有停止或重启当前 App/Bridge，没有刷机、重新配网、清零、变更账户或上传。运行环境仍沿用下文已激活版本，不能因源码与构建完成声称设备已更新。
- 下一步：用户保存工作并手动完全退出 App后，通过唯一控制台入口重启接入；USB 可用时仅走现有双备份/live 分区应用更新脚本更新 0.2.12，绝不执行 IDF 输出通用 flash。再在原 App 聊天验收双端同时显示、Mac Allow/Deny、设备 Allow/Deny 清除对端、长按唤回窗口及显示回执；保留原来的 native 独立回执与长稳未验收边界。

## 2026-11-02 新目录 Bridge 已激活
- 用户已完成手动退出 App 和 Terminal 确认。私有 `runtime-activation.json` 记录 2026-11-02 01:07:29 +1100 激活：最新账本已同步，Hooks 已迁移；待迁移标记已移除。
- 本次只读进程与 IPC 核验：Bridge、stdio relay、launch_desktop 均运行在 `/Users/bowen/Developer/codex-companion-controller/controller`；旧 outputs 工程 Bridge 不再运行。
- 新 Bridge 实测设备 Wi-Fi online=true、固件 0.2.11，desktop.connected=true、approval_receipts=true、session_count=2。七类用户级 Passport Hooks 全部指向新工程，未见旧路径命令；配对 IP 仍匹配当前 Mac。此为瞬时状态，不代表长期稳定性。
- 安装 App 26.1027.30824 的登记摘要再次核验通过。私有配对、证书、费率保持原值，旧工程保留；切换前账本及 Hooks 备份在 private/activation-backup-*。
- 新增 6 项 synthetic/mock 切换回归、既有连接恢复 8 项、通知/Hooks 14 项通过（共 28 项，上一轮实际运行）；本轮为只读核验与文档更新，未重复跑代码测试。
- **本次真实设备验收通过**：迁移后原 App 聊天经 PermissionRequest Hook，设备 Allow 后独立验收文件实际写入，设备 Deny 后工具返回 `PermissionRequest hook denied approval` 且目标文件不存在。用户确认两次均仅实体按键，批准 😆、拒绝直接 😭（无 😶）；验收文件已清理，证据在 private/hardware-acceptance-20261102-*.json。这是真实设备测试，非 mock。
- **仍待验收**：native stdio relay 独立 `approval/submitted` 提交回执（本次 Allow 的 last_device_decision.source=hook，last_device_delivery=null，不能据此宣称 native relay 全链路通过）、休眠唤醒后重连、所有权限类型和长期稳定性。Hook 路径信任已至少对本次 PermissionRequest 生效，不扩展声称所有 Hook 均已验收。
- Python/依赖收尾：已安装 Homebrew Python 3.12.15、OpenSSL 3.5.9、Tk/Tcl 9.1，独立环境为 private/bridge-venv-homebrew；pySerial 3.5 与 websockets 17.3 均从本工程 vendor 的 SHA-256 校验 wheel 离线加载，pip check 通过。local-env.sh 与所有 shell 入口统一选择 CONTROLLER_BRIDGE_PYTHON，不再为未来启动依赖 Codex cache。
- **独立 Python 已激活**：用户已手动退出并重开原 App，确认设备重新连接。private/active-python.json 记录 2026-11-02T01:27:58+11:00 启动，实际选择 private/bridge-venv-homebrew/bin/python，base_prefix 在 /opt/homebrew，Python 3.12.15 / OpenSSL 3.5.9 / pySerial 3.5 / websockets 17.3。原 prepared 回执保留作历史准备证据，不能覆盖此较新的激活记录；旧 venv 仍保留回退。
- 日常仍仅使用 `controller/Codex Companion 控制台.command`。项目保持暂停，不因迁移成功自动开始功能开发或刷机。

## 版本与证据
| 项 | 状态/证据 |
|---|---|
| 历史 GitHub 基线 | `00b61330f1b415b555d8acde8ddd4a6d055c48d0`，main；包含统一控制台和 Token 分项 |
| 当前固件 | 0.2.12；本机含图镜像 2,360,544 字节；SHA-256 `dae8c7c2dacea383f0c3deb3cbc9ac3a0d78faa653151faf2b73e1338053de04`；实际 hello 已确认 |
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
- 休眠唤醒生命周期、native relay 独立提交回执和所有权限类型的全流程验收；独立 Python 下 App 关闭重开与设备重连已有用户确认及启动回执，先前新路径 PermissionRequest Hook Allow/Deny 不自动扩展成新环境所有权限复测。

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

## 2026-11-02 最终激活与归档补记
- 用户提供完整 --restart-app 日志，确认已重开并重新连接；独立 Python 的启动回执已核对。日志中“Bridge 未运行 / FileNotFoundError”发生在停止旧 Bridge 与启动新 Bridge 之间，是本次正常切换的中间状态。
- 首份归档已实际生成：`2026-11-02-python-handoff` 对应 e4fb7c5，149 个私有成员回读校验通过；外层 SHA-256 已再次核对。
- 最终补记归档目录：`/Users/bowen/Developer/codex-companion-archives/2026-11-02-final`，包含本次激活回执和更新后的源码/交接。以该目录 ARCHIVE-RECEIPT.json 的提交号与摘要作为最终对应版本；保留首份归档不覆盖。
- 本轮仅核验、记录与本地归档，不重复运行前一轮已通过的 227+10 项代码回归，不自动扩大硬件验收范围。

## 2026-11-02 GitHub 同步授权
- 用户在归档完成后明确要求将更新上传 GitHub，覆盖此前“仅本地、未授权 push”的历史边界。允许推送已审计源码及交接文档；私有归档、private/、配对密钥、Apple 素材和含图固件仍不上传。
- 同步前 fetch 成功，origin/main 为本地祖先，本地含两项已验证更新提交；源码索引 207 文件敏感路径/凭据模式审计通过，工作区干净。使用普通 fast-forward push，不 force；实际结果以远端 main 与 HEAD 一致为准。

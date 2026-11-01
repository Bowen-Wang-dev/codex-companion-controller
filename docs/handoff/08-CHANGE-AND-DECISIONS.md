# 决策与演进记录

以下为从长会话提炼的决定；不抄录原聊天，也不包含秘密。

- 初始目标：Codex 独立实体控制器+状态/额度显示+Apple Emoji 宠物；第一阶段不做庞大 Pocket OS。
- 用户没有完整旧宠物代码可提供，明确同意按其 Emoji 映射重做。不能声称复用了不存在的旧代码。
- 先做 Mac Demo，用方向键/Return 模拟三键。Demo 模拟数据必须标注，不能混成实际账户/审批。
- 交互从“上下键切页/选项冲突”改为短按选项、长按主页面；长请求再加入首/末页跳转、末页选择和二次确认返回。
- 用户非常重视桌面 App 的原聊天硬件 Approve/Deny，曾接受 CLI 备选，但随后再次明确桌面 App 是主交付。只能通知/Mac允许不是满足需求。
- 桌面 App 采用已核对版本内部启动开关+透明 stdio relay；不改 App 包，不用 GUI 自动点允许。不同版本必须重新核查。
- 早期 USB-only/Unknown/无素材提示不符合目标，后来加入加密 Wi-Fi、USB物理配对、真实用量、Apple 私有图、中文分页、电量和音频。
- 音量固定 0–100%、10% 步进；音频调度不得阻塞网络。完成约3秒回待机。
- 第三方服务商也是 OpenAI/Codex/GPT 兼容网关，但不把网关余额混成 ChatGPT 额度或额外重置次数。
- Token 计量先修复恢复聊天模型、累计去重、整轮统计；再补 compaction 和后台有账但本机缺完成记录的对账边界。
- 金额用 `$`，不要又改成占空间的 USD 标签。清零必须二次确认/长按。
- 网络问题曾有 HTTP 头失败；保持证书验证、有限重试、代际检查、固定离线安全窗口。另一次真实断线是 Mac换网段+旧配对IP+Bridge不运行+App升级。
- 长上下文不是总价简单翻倍；Sol 单笔>272K 输入/缓存2倍、输出1.5倍，逐笔累计。加入自定义/OpenAI价格来源和默认1倍率，不能重复折扣。
- 顶层27个command太乱，收敛为一个控制台，旧入口保留在维护工具；新 Agent 不要再次拆散日常入口。
- 2026-11-02：用户决定项目先暂停，整理到 Developer 并补全面 Markdown，供新会话阅读。

后续变更请追加日期、用户意图、实现证据、验收情况，不将未验收内容写成完成。

## 2026-11-02：新工作目录接入 Bridge
- 用户要求从旧 Codex outputs 工程迁移到 Developer 后接上新 Bridge。实际检查发现旧 App、Bridge 和 relay 仍运行；用户级七类 Passport Hooks 仍引用旧绝对路径。
- 增加 `controller/scripts/activate_migrated_runtime.py`，由唯一日常控制台入口调度，未增加顶层 command。用户退出 App 后才允许停止旧服务；保留旧工程、配对和费率；切换前备份目标账本与原 Hooks，只替换精确匹配的旧 Passport 命令，不授予 Hook 信任。
- 新目录配对/证书/费率字节一致，新旧账本不同，因此不直接用迁移时账本启动，停旧服务后再同步最新数据。
- 本次验证：新切换回归 6 项通过；连接恢复回归 8 项通过；通知/Hooks 回归 14 项通过（合计 28 项）；控制台 shell 语法检查通过；新 Python 的 pySerial 3.5 / OpenSSL 3 / websockets 导入通过。真实服务切换及设备 Allow/Deny 尚待用户退出 App 后验收。
- 首次 sandbox 进程读取被拒，按审批后读取成功；未刷机、重配网、清零或改账户。

- 切换前只读 IPC 实测：旧 Bridge desktop.connected=true、无待审批，但设备 online=false；新目录 Bridge 未运行。不能将准备入口完成说成无线或实体审批已恢复。

## 2026-11-02：迁移后运行核验
- 用户表示已完成切换；核对私有激活回执（01:07:29 +1100）、新目录进程及新旧 IPC：新 Bridge/relay/App 启动器已在 Developer 工程运行，旧 Bridge 未运行。
- 新服务 Wi-Fi 设备在线、固件 0.2.11、desktop.connected 与 approval_receipts 为 true；七类 Passport Hook 均为新路径。配对地址检查无变化，App 26.1027.30824 登记摘要校验通过。
- 采样存在待审批（permission_pending=true、hook_pending=1），未触发停止、重启或自动批准。新路径真实 Allow/Deny、Hook 信任、重启/休眠稳定性仍未验收。
- 本轮仅只读运行核验与文档更新，无刷机/配网/清零/账户变更；首次本机 IPC 因 sandbox PermissionError 受限，审批后读取成功。不以主机回归替代实机验收。

- 额外依赖检查：serial 位于新 venv、websockets wheel/pth 位于新工程；Python base 仍依赖 Codex runtime cache。已将稳定解释器、源码提交、私有独立备份列入归档收尾，未擅自安装、提交、上传或删除旧目录。

## 2026-11-02：迁移后实体按键验收
- 用户明确要求实机验收。在原 App 聊天触发真实目录写权限请求，独立文件位于 Developer 下，未刷机、重配网、清零或更改账户。
- Allow：实体按键允许后命令执行，文件实际生成；即时 Bridge 记录 source=hook、choice=allow、review_page=15，设备 Wi-Fi 在线、App relay 已连接。
- Deny：实体按键拒绝后工具返回 `Rejected("PermissionRequest hook denied approval")`，命令未执行，deny 文件不存在。这是预期测试结果，不是自动审批审查拒绝。
- 用户明确反馈“两次均为实体按键，表情符合”：批准 😆，拒绝直接 😭，无 😶。额外实体 Allow 完成清理，精确内容校验后删除本次 allow 文件；deny 文件仍不存在。
- 证据保存于 ignored private/hardware-acceptance-20261102-allow.json 与 -result.json。结果覆盖真实 PermissionRequest Hook Allow/Deny、执行效果、用户目视表情；不是 mock，也不等于所有权限和长稳验收。
- 本次 last_device_delivery=null，未获得 native relay 独立 approval/submitted 回执，明确留作未验收。未执行 App 重启、系统休眠唤醒测试；项目保持暂停。

## 2026-11-02：授权归档、独立 Python 与离线依赖
- 用户明确确认 Hooks，并要求归档保存、Python 和依赖收尾。保持暂停开发，不刷机、清零或变更账户；仅本地 Git 保存，不推送。
- 使用 Homebrew python@3.12（3.12.15）、python-tk@3.12（Tcl/Tk 9.1）及 OpenSSL 3.5.9；新 private/bridge-venv-homebrew 与旧运行环境并存。local-env.sh 指向稳定 Homebrew 路径，所有 shell 入口改从统一 CONTROLLER_BRIDGE_PYTHON 取解释器。App relay 启动脚本也读取同一 env；不改 Hook 源码或信任命令。
- 补入 PyPI 原始 pySerial 3.5 wheel、上游 v3.5 BSD 许可及固定 SHA-256；与既有 websockets wheel 一并先校验再配置 .pth，离线恢复不依赖 pip/网络。源码审计仅额外放行这一枚固定摘要 wheel。
- 本次实际验证：controller Python 227 项通过，tools 10 项通过，C 导航/音序与 8 组 mock 音频通过，Tk/Tcl 导入和 Tcl 初始化、pip check 通过。首次完整回归 16 个 socket 用例受 sandbox 拒绝，获准后重跑通过；pySerial 下载首次 sandbox DNS 失败，获准后从 PyPI 下载成功。
- 工具回归发现 macOS /var 路径别名使迁移子目录判断失效，已统一 destination.resolve 并通过原回归。归档工具新增排除凭据/venv/日志/符号链接、私有成员哈希回读、坏 JSON 拒绝测试。
- 本地归档使用独立同盘 sibling 目录；源码快照与 Git bundle 分开保存，私有恢复包包含配对/账本/Flash 备份/私有素材与 Hooks 配置，0600/0700 权限，排除 Codex 登录凭据；逐文件在线快照不冒充全局事务或异地备份。
- 运行中的 Python 不热替换，也不自动关闭用户 App。需手动退出后通过同一控制台 --restart-app 重启；实际启动时记录 private/active-python.json。旧 venv、旧 outputs 和 IDF 工具链保留。

## 2026-11-02：独立 Python 重启完成
- 用户已按 --restart-app 提示手动退出 App 并由同一控制台重开，提供完整 Terminal 日志并确认重新连上。
- 核对 active-python.json：2026-11-02T01:27:58+11:00，解释器为新工程 bridge-venv-homebrew，base_prefix 指向 Homebrew，Python 3.12.15 / OpenSSL 3.5.9 / pySerial 3.5 / websockets 17.3。旧 prepared 回执的 false 是切换前历史，不是当前状态。
- 切换时“Bridge 未运行 / FileNotFoundError”位于旧服务关闭与新服务启动之间，不作为持续连接故障。保留旧 venv 与首份已校验归档（e4fb7c5、149 私有文件）。
- 最终激活文档和私有回执补充保存于 sibling 目录 2026-11-02-final；实际成功依据为其 ARCHIVE-RECEIPT.json。没有推送、刷机、重配网或清零。
- 仍保留休眠唤醒、native relay 独立提交回执、全部权限类型及长稳测试边界，不将基础依赖检查或重新连上扩展成这些验收已通过。

## 2026-11-02：用户授权同步 GitHub
- 用户明确要求“如果有什么更新就上传到 GitHub”。已 fetch 核对远端，没有需要合并的上游新提交，本地领先两项归档/独立 Python 更新。
- 207 个索引文件通过敏感路径和凭据模式审计，既有测试结果沿用对应提交记录，本轮不重复宣称新测试；仅推送源码、依赖 wheel/许可证与交接文档。
- 私有恢复归档、账本、配对身份、登录凭据、Apple 图片及含图固件不入库、不上传；保留本地归档快照，不因公开同步删除。普通推送后核对远端 main 提交号。

## 2026-11-02：按用户新任务准备双端审批与 Mac 交接修复
- 用户反馈设备显示转到 Mac，电脑却没有审批界面，并要求任一端均可处理。核对发现 ACTION_MAC 仅本地静音，且阻塞 PermissionRequest Hook 时原 App 尚未弹出 native 审批；旧“在 App 审批窗口处理”提示不可靠。
- 使用现有 Broker 请求和私有 Unix IPC 增加真实 Companion Tk 审批窗口；启动只传请求 ID，请求详情不写文件、不进进程参数、不发送模型。完整详情分块读取，二次确认后提交同一个请求；Mac/设备/原 App relay 保持首个决定生效、另一端撤销，保留原聊天和 App 版本/摘要校验。
- 0.2.12 固件发送真实 mac_handoff，Bridge 唤回或重开窗口；仅收到完整且可见窗口的短期心跳才显示已显示，收起/新交接即撤回回执。没有把窗口显示、已提交或已读冒充实际批准/执行成功。Mac 审阅不改变设备分页，未知 native 批准语义仍需原 App。
- 实际验证：controller 完整 242 Python 测试通过；显示回执补强后相关 13 测试通过；C 导航/音序和 8 组 mock 音频通过；合成 Tk 窗口完整内容、按钮、收起/唤回、二次确认/提交通过。截图工具超时，未完成截图目视验收。首次 socket sandbox / registry 网络阻断均获准后重试成功。
- ESP-IDF 5.5.3 仅构建通过，0.2.12 含图镜像为 2,360,544 字节，SHA-256 `dae8c7c2dacea383f0c3deb3cbc9ac3a0d78faa653151faf2b73e1338053de04`；新文案现有中文字形覆盖通过。未刷机、未重启当前 App/Bridge，未改配对/账户/账本，也未提交或推送。
- 待用户保存并手动退出 App 后经唯一控制台切换，设备经既有双备份与 live 分区校验流程更新，再做原聊天真实双端操作验收；不得把上述 synthetic/mock/构建称为实机功能通过。

## 2026-11-02：用户自行更新 0.2.12 的入口收尾
- 用户询问是否已刷机并要求自行执行命令。明确：0.2.12 已构建，未刷入；本轮未执行设备更新。
- 检查发现唯一控制台菜单 7 调用的历史维护脚本仍断言 manifest=0.2.11；已将版本校验与提示更新到 0.2.12，保留 App 精确版本校验、全回归、停 Bridge、双读备份/live 分区校验、应用写入/回读验证和接回原聊天流程。
- shell 语法与入口/manifest/镜像版本、大小、SHA-256 一致性核验通过；未重复宣称完整 242 项或实机刷写通过。该入口会重启 Bridge，而本轮 relay 未变，因此可保持原 App 打开，无需额外退出 App；这补充修正上一条的一般重启步骤。

## 2026-11-02：修复普通 Terminal 更新入口缺少 python
- 用户贴回完整日志：242 回归通过后在串口发现处 `python: command not found`，没有进入停止 Bridge/备份/刷写阶段，设备版本不能认定已更新。
- 维护入口不再调用裸 python：Bridge 解释器负责串口枚举和 IPC preflight；独立 CONTROLLER_FLASH_PYTHON 执行 esptool 4.x。停 Bridge 前先验证刷写解释器与依赖，配置缺失立即退出。env.sh 在 IDF_PYTHON_ENV_PATH 明确配置时提供 fallback；本机 ignored local-env.sh 指向已有 IDF Python/esptool，不新增安装、不改现代 Bridge 解释器。
- 3 项真实 shell/隔离假解释器回归覆盖最小 PATH 成功调度和两种依赖缺失的提前退出，另 4 项依赖/入口检查通过。真实最小 PATH 依赖导入及 USB 候选枚举通过；没有打开 USB 串口、停止 Bridge 或执行更新，不把隔离测试称为刷写验收。
- 用户仍通过唯一控制台菜单 7 自行重试，无需新 command、重配网或清零；待实际双备份、写入/校验及 0.2.12 hello 后再记录部署。

## 2026-11-02：用户否定独立窗口，审批回归原 App
- 用户自行更新后，只读 IPC 核对 0.2.12 在线、App relay 已连接；曾通过独立 Tk 窗口允许一次只读检查。第二条拒绝测试由用户中止、测试文件未创建。用户明确表示不喜欢独立窗口，要求原 ChatGPT/Codex App 原生显示；此决定覆盖之前独立 UI 方案。
- 停止实机测试；Tk 窗口入口改为无操作兼容文件，新 Broker 删除所有独立窗口接口和自动启动代码。保留文件仅防止旧运行 Broker 再启动弹窗，不是新增应用。
- 桌面模式不再通过阻塞 PermissionRequest/权限 PreToolUse 抢先决定；返回空 Hook 结果交原 App 原生审批，relay 同时镜像真实 native 请求到设备。命中旧缓存也不能绕过原生审批。设备长按仅激活已经运行且版本/摘要验证通过的原 App，无自动点击或安装包修改。
- 仅生成本机官方 JSON schema 核对字段，并核验 26.1027.30824 登记摘要；保留 startedAtMs、scope 和 request binding 等校验。官方审批文档仅支持设计依据，不当作实机证据。
- 完整 controller Python 240 项通过（删除被否定 UI 的 13 项，新增 8 项原生 routing/focus/缓存/兼容用例；2 项原 Mac 私有接口集成改为原 App Allow/Deny 协议响应撤销设备）。随后焦点激活的超时处理补强，相关 8 项通过。
- 本轮不重刷固件，不自动停止 App 或 Bridge；新源码待用户用控制台 2→2 安全重启 Bridge 后生效，保留当前 App 原聊天。0.2.12 屏幕仍显示保守的“请求 Mac 显示/未收到回执”，不能伪造原生卡片已绘制。原生双端实机通过前保持未验收，绝不回退到独立弹窗替代。

## 2026-11-02：五项原生双端实机通过，授权发布 v0.2.12
- 用户已切换 Bridge 并逐项操作：设备 Allow、设备 Deny、设备不操作的原 App Allow、设备不操作的原 App Deny、设备详情长按转到原 App 后 Allow；五项均由用户确认 passed。
- 设备 Allow 的真实只读命令执行成功，Broker 记录 source=desktop、choice=allow，匹配独立 submitted 回执，补齐旧 native relay 回执未验收项。两项拒绝返回 rejected by user、命令未执行；两项 Mac Allow 均输出成功标记。用户确认对端待审批页面结束；第 5 项确认原 App 唤回且交接未自动批准。未把拒绝结果当异常，也未给全部五项虚构回执。
- 本机证据保存为 ignored private/hardware-acceptance-native-20261102.json（0600）。公开发布说明仅含去身份化矩阵，不公开会话/设备身份或私有日志。此前中止的独立窗口测试不算新原生方案验收。
- 用户明确要求先补 Markdown 再发布。更新根 README、controller README、交接入口/状态/架构/UX/运行手册/待办以及 docs/releases/v0.2.12.md；历史准备、失败和被否定方案保留为历史，不冒充当前状态。
- 发布前本轮完整 controller Python **240 项通过**，C 导航/音序和 8 组 mocked BSP/RTOS 音频检查通过；桥接诊断版本统一为 0.2.12-native-app。没有再次刷机或改变配对/账户/账本。
- 以 v0.2.12 标记源码发布，提交/推送前审计索引，GitHub 仅包含源码、文档及既有固定校验依赖；私有数据、Apple 原图和含图固件不随版本发布。远端 main/标签最终核对才算发布完成。其余 backlog、所有权限类型和长稳不因本次五项测试获得自动实施或验收结论。

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

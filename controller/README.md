# Codex Companion Controller · 0.2.11

2026-10-26：补计上下文压缩响应，加入后台导出对账，修复无线 HTTP 生命周期；保留 $ 显示、二次确认后长按清零和原聊天实体审批。详细核对与限制见 [0.2.10 修复记录](docs/Token与无线修复0.2.10.md)。新固件已构建，实机更新与稳定性验收以该记录为准。

日常统一入口为「Codex Companion 控制台.command」。菜单包含桌面 App 实体按键审批、Bridge／USB／Wi-Fi 恢复、配网、Token 费率与倍率、长上下文费率、用量核对、本机清零、Hook 管理和固件备份更新。历史启动器已收进「维护工具」文件夹；日常不必逐个找 command。

Compaction-response accounting, optional private provider-export reconciliation and HTTP transport fixes. Dollar display and explicitly confirmed resets are retained. See the bilingual repair record for validation status and billing limitations.

## Previous development notes / 历史开发记录

0.2.8 已构建，尚未刷机。保持 App 打开，停止旧 Bridge，运行「更新无线稳定性固件.command」。脚本先在普通 Terminal 运行完整测试，通过后备份、仅更新应用并保留配网，再启动 Bridge。记录见 [无线稳定性修复](docs/无线稳定性修复.md)。

V0.2.8 is built locally; device update and real TLS endurance verification are pending. See the bilingual repair record.

V0.2.6 已在本机完成固件构建，尚未刷入设备或做实机验收。设备连接 USB 后，运行「更新Token用量固件.command」会双读备份完整 8 MB Flash，并只更新 factory 应用，保留无线配网与其他分区。刷入后需重启 Bridge；自定义 API 实际会话是否持续提供 Token 统计仍需实机确认。

0.2.5 增加详情首/末页快捷跳转、二次确认返回、长按确认转到 Mac 处理，以及 App 接入层实际提交审批后的 3 秒 😆 回执。新固件已刷入并通过 Wi-Fi 握手，原 App 的网络权限申请已由设备批准并收到提交回执；用户已确认设备正确显示 😆。更新入口为 `更新交互与回执固件.command`；保留 Wi-Fi 配对。此次同时更新 App relay，脚本在刷机后提示手动退出 App，再重新启动原 App 和 Bridge；随后从侧栏打开原聊天。按键表和回执含义见 `docs/交互与回执更新.md`。

V0.2.5 adds first/last-page jumps, a return path from confirmation, hold-OK handoff to Mac, and a three-second 😆 after the relay actually submits the hardware approval. Host checks/build pass. Flashing, Wi-Fi handshake, and a real desktop App network grant with a matching physical decision/delivery receipt are confirmed; the user confirmed the 😆 feedback displayed correctly. Run `更新交互与回执固件.command`; pairing is retained. The script asks you to quit and relaunch the App after flashing so its relay reloads, then reopen the original chat from the sidebar. See `docs/交互与回执更新.md`.

## 第三方 API 模式（Bridge 0.2.6 基础适配）

Bridge 已读取 Mac 当前 `~/.codex/config.toml` 中的 `model_provider`、provider 名称、模型和 wire API。当前配置被本机只读识别为自定义 provider「灵算」、模型 `gpt-5.6-sol`、Responses；API bearer token 和自定义 header 不会发到 Passport 或写入设备状态。

自定义 provider 不再调用 ChatGPT 专用账户额度／重置接口。桌面 App Server 的 `thread/tokenUsage/updated` 通知可提供本轮和会话累计的输入、缓存输入、缓存写入、输出、推理输出及总 Token 数；Bridge 只读取用量数字和实际模型 ID，不读取聊天正文或凭据。设备的原“额度窗口”和“额外额度重置”页在自定义 provider 模式下显示会话累计与本轮 Token。用量仅对当前活跃会话显示；没有收到官方用量通知时显示等待状态，不用任务时长推算。

Token 页面将未缓存输入、缓存读取、缓存写入、可见输出、推理分别显示数量与估价，再显示总计。推理 Token 属于输出 Token 子集，使用同一输出费率但拆行展示，合计只加一次。费率编辑器提供「自定义价格 × 倍率」和「OpenAI 官方基准价 × 倍率」，倍率默认为 1；长上下文逐请求按输入（含缓存）>272,000 分档，不能按整轮总量判档。旧数据没有请求边界时，长档估价明确显示未知，不猜测。

本次连接修复只需要重启 Mac Bridge，不用 USB 或刷固件。保持桌面 App 打开，在旧 Bridge 终端按 Control+C，再运行「仅启动桌面App桥接.command」。设备显示「无线同步正常」只证明设备连上 Bridge；「App 已连接 · 等待会话」表示 relay 在但还没见到原聊天会话；「App 实体审批已接入」才表示 App 会话已通过 relay 握手。若新 Bridge 启动后仍无 App relay，保留 App 打开并查看 Bridge 终端提示，先不要刷机或重新配网。


桌面 App 原生实体审批的版本限定转发入口已通过真实 App 目录权限批准／拒绝验收，**其他审批类型仍按各自支持范围处理，不能称为所有功能完整版已交付**。入口为「启动桌面App实体审批.command」；首次先停止旧 Bridge，并用 Command+Q 退出 App，再运行此入口。无需切到 CLI 操作界面，无需重新配网。兼容已核对的 App 26.1016.62342；内部启动开关不是稳定公开 API，版本变化会拒绝旧适配。详细证据、限制与恢复方式见 `docs/桌面App实体审批验收.md`。

0.2.4 另补上「等待你回复」提醒与确认已读；这个已读操作不代替回答或权限批准。长请求支持逐页完整查看，在末尾选择允许／拒绝，再进行二次确认；详情页的上下键只翻阅，长按上键从头查看。无需调用模型精简。细节与验收见 `docs/长请求实体审批.md`。

0.2.4 已刷入并回读校验，设备在线并声明分页协议。用户已确认可以翻到末页选择，中文不再显示方框。`human1` 更新进一步将 JSON 改成中文说明，完整显示具体权限、路径、原因、工作目录和有效期。只在旧 Bridge 终端 Control+C，保持 App 打开，再运行「仅启动桌面App桥接.command」即可加载；无需为这个显示修复再次刷机。真实设备允许／拒绝回传的验收结果以 `docs/桌面App实体审批验收.md` 为准。

以下为 0.2.3 及更早版本的历史记录。

2026-10-24 · AI Passport / ESP32-C3 / ESP-IDF 5.5.3。

**0.2.3 提示出现几秒就消失：** 已发现本项目 `.codex/hooks.json` 仍有 1 秒超时的旧副本，与用户级 115 秒配置同时加载。已备份并清理项目旧副本，同时修复共享等待逻辑：一个重复 Hook 退出，不会再清掉另一个仍在线的等待者。安装器以后默认清理本项目旧副本，保留其他 Hook。重启 Bridge（旧终端 Control+C，再运行「仅启动桥接.command」）并用 Command+Q 重开 App 以加载修复；无需刷固件或重新配网。诊断修订号为 `0.2.3-hookfix1`。

**V0.2.3 / 继续使用 App：** 修复本轮结束 3 秒后恢复 😋；扩大普通 Hook 的设备审批，原生网络 / 目录申请新增「到 Mac 继续 / 在设备拒绝」；提高音频供数优先级，减少无变化重绘，并复用 HTTPS 连接。App 原生权限的批准仍在 Mac，未把它描述为已实现。

更新时停止旧 Bridge、接 USB，运行「更新固件保留配网.command」（不带 --native）。不需要改用 CLI，也不重配 Wi-Fi。全局 PreToolUse 的等待上限已更新；请在 App 审阅变更的 Hook，再用 Command+Q 重开 App 以加载它。构建、主机测试及实机边界见 `docs/V0.2.3验收.md`。设备刷入和音频实际听感以实机记录为准。

以下保留 V0.2.2 及此前的历史说明。


**升级脚本停在「操作超时」：** 已修正 Mac 端的传输错误。旧代码误把 `app-server proxy` 当成 JSONL / WebSocket 转换器；它实际只转发原始字节，而 Unix listener 要求 WebSocket 握手。现在用随项目提供、固定版本并校验摘要的 WebSocket 客户端直接连接，不需要联网安装依赖。再次运行「升级并启用实体审批.command」即可；检查阶段会分四步显示进度，超时会指明具体接口。上次在检查阶段停止，没有写入固件；不必重新配网或再次信任 Hooks。

固件和 Mac Bridge 已更新到 V0.2.2，包含声音 / 音量修复，以及用户选择的 **CLI 原会话实体审批模式**。上次确认的实机版本为 V0.2.1；尚未收到 V0.2.2 成功刷入记录，实机声光与 CLI 审批仍待验收。本次传输修复仅修改 Mac 代码，没有刷写设备。构建和主机验证见 `docs/V0.2.2验收.md`。

## V0.2.2：声音、音量和 CLI 实体审批

- 音量默认 20%，范围 0%–100%，每档 10%。声音设置中选中「音量」后短按确认进入编辑，上键增加、下键减少；到边界停止，再确认退出。长按方向键仍换页。新增「试听提示音」、驱动状态和错误码。声音开关 / 音量 / 间隔目前重启恢复默认。
- 修正 Codec 分贝曲线与小振幅叠加造成的极低输出；用户音量只在线性 PCM 中计算一次。复用 demo 的软电子波形和完整事件音序。BB 三声 1200 Hz / 180 ms / 120 ms，总计 780 ms，保留最高优先级、有限重复和静音。初始化失败不再静默删除工作线程。
- CLI 模式使用独立私有 Unix App Server，官方 CLI 与 Bridge 订阅同一原会话。只调用 `thread/resume`，不创建新会话或 fork，不自动发送模型任务。原会话仍由桌面 App 持有时拒绝接管，不复制历史冒充接入。
- `request_permissions` 原生网络权限和可完整展示的单一路径目录权限支持设备批准 / 拒绝。返回官方 `permissions` 的授予子集，固定 `scope=turn`；拒绝返回空权限集。普通白名单命令支持当前命令的 accept / decline。过长、多路径、特殊路径、高风险或不支持的范围必须在 CLI 审阅，设备可以拒绝。
- 按键仍为：上批准、下拒绝，短按确认进入二次确认，释放后重新长按确认 1 秒提交。无预选。请求 ID、摘要、启动标识、期限、重复回调和 CLI 处理回执均参与检查。收到匹配的实际授予结果后才显示 😆；拒绝直接 😭。CLI 模式用真实 `turn/completed` 区分失败，避免把 Stop 当作成功。

**升级并进入 CLI 模式：**

1. 在旧 Bridge 终端 Control+C，连接设备 USB 数据线。用 Command+Q 完全退出桌面 App，释放要继续的原会话。
2. 双击「升级并启用实体审批.command」。先执行不发模型任务的真实官方接口检查；通过后双读备份并只刷应用，保留 Wi-Fi / NVS / bootloader / 分区表。备份可能约 6 分钟，等待进度，不要重复启动。
3. 在列表中选择原会话，进入官方 CLI。设备连接页应显示「CLI 审批已接入」。日后直接运行「用CLI继续原会话并启用设备审批.command」，不用重新刷写或配网。
4. 在设备声音设置选「试听提示音」，再在 CLI 发起一次实际网络权限请求，验证声音、上下选择、两步确认和官方返回结果。仍需这个实机验收，主机模拟通过不代表已在你的扬声器上发声。

「仅启动桥接.command」继续用于桌面 App 的 Hook 模式；桌面原生 `request_permissions` 在该模式仍是只读提醒。需要实体授予网络 / 目录权限时使用上述 CLI 入口。官方 App Server 协议处于实验阶段；本机依据已安装 0.163.0-alpha.11.2 的生成类型、官方文档及源码核对，未通过私有桌面 IPC 或自动点击代替授权。

以下 V0.2 / V0.2.1 内容保留为此前配网和通知排查记录。

## 已有思考 / 本轮结束状态，但网络权限没有提醒

2026-10-24，重启桌面应用后实际收到 Hook，Bridge 只读检查计数为 24。新建的「发起审批测试请求」申请的是 `permissions.network.enabled=true`；旧通知代码只提取文件系统路径，没有路径就直接忽略，因此网络权限没有弹窗。这是 Bridge 代码遗漏。

已补上网络及网络 / 目录混合权限的只读提醒，保留同一请求 ID、110 秒有效期、完成 / 中断 / 重启清理和重复请求去重。仍通过现有固件的弹窗与 BB 提醒路径展示，原生权限在 Mac 授予，不会伪装为硬件批准成功。诊断增加事件 / 工具计数及通知处理版本，不记录参数、提示词或令牌。

**只需在旧 Bridge 终端按 Control+C，再运行「仅启动桥接.command」**。启动日志应出现「权限提醒处理 v2」，然后在原聊天发起一次新请求。无需刷固件、重新配网、再次信任或重启桌面应用。旧的已结束请求不会补发。

## V0.2.1：已联网，但连接页验证中 / 其他聊天无通知

用户已确认真实额度正确。新版在所有页面最右上角加入设备电池图标和百分比（CW2017 实际 SOC，低电量变色，读取失败显示「—」），并修正连接页状态：收到有效快照后显示「无线同步正常」，并增加实际 Hook 接入状态。账户已连接不代表当前聊天已加载 Hook。

本机用户级 Hook 已注册；运行「审阅通知Hook.command」，输入 `/hooks`，审阅并信任 ~/.codex/hooks.json 的 Passport 条目。随后退出 CLI，用 **Command+Q 完全退出 Codex / ChatGPT 桌面应用，再重新打开原聊天并发起新请求**。保持 Bridge 终端运行；仅切换聊天不保证卸载仍在运行的旧会话，检查脚本读取的磁盘信任状态也不等于旧会话已经加载。已完成信任无需再次 Trust All，旧请求不会补发。其他电脑先运行「安装通知接入.command」。助手若已完成用户级注册则不必重复安装。

固件更新：保持 USB，先在旧 Bridge 终端 Control+C，再运行「更新固件保留配网.command」。它保留 Wi-Fi 配对和 NVS，不需要重新配网；成功后自动启动新版 Bridge。固件必须更新，单独重启 Bridge 不会改变设备界面。

此次目录写权限测试使用 `request_permissions`。新版通过它的 PreToolUse 事件做设备弹窗与 BB 提醒，**实际目录授权仍在 Mac 原生页面完成**；设备不会伪装批准 / 拒绝成功。普通 Bash 命令审批继续支持设备选择。需要信任后的真实聊天联调，不能把主机测试称为设备已收到通知。详见 `docs/V0.2.1验收.md`。

## 已保存配对，但显示「证书或 Bridge 连接失败」

2026-10-24 已修复 Mac 配对脚本的证书生成：macOS 当前 LibreSSL 生成了显式曲线参数，而固件同版本 Mbed TLS 3.6.5 的主机复现无法解析该证书，返回 `-0x3D00`。现在显式要求命名曲线 P-256，并检查生成证书的实际公钥编码；旧证书不会因 IP 相同而继续复用。新证书通过相同库的解析、IP 匹配、自签信任验证和 TLS 1.2 握手，仍保留证书校验和配对密钥认证。

**不需要重新刷固件。** 在旧 Bridge 终端按 Control+C，保持 USB 连接，重新运行「配置无线连接.command」。输入 / 确认网络信息后，脚本会显示「检测到旧证书编码不兼容」；随后等待 USB 握手，在设备第六页短按并松开确认，再在终端回车。成功后自动启动新的 Bridge；等设备 Wi-Fi 握手和时间额度同步后再拔 USB。

之所以要再配对一次，是因为设备 NVS 中也保存了旧证书，单独重启 Mac Bridge 不能更新它。修复只更新本机脚本及 USB 写入的配网数据，不更新应用固件，不消费额度。

验证记录见 `docs/V0.2验收.md`。曲线编码参数依据：[OpenSSL 官方说明](https://docs.openssl.org/3.0/man1/openssl-genpkey/#ec-key-generation-options)。实际兼容性由本机测试确认，尚未把主机测试称为设备已连通。

## 已刷 V0.2，但配对失败时

不用重新刷固件。保持 USB 数据线连接，在旧 Bridge 终端按 Control+C 停止，运行 **「配置无线连接.command」**。

1. 输入 2.4 GHz Wi-Fi 名称、隐藏密码和 Mac 局域网 IPv4 地址。设备此时显示「离线 / 未配置」正常。
2. 等终端显示「USB 已连接，固件 0.2.0」，再用设备方向键找到第六页「连接与配网」。
3. **短按并松开确认键，不是电源键，也不要长按。** 屏幕应变成「请在 Mac 运行无线配对」。
4. 在这次许可的 60 秒内，回到终端按回车。只有收到设备保存成功回执，才会启用本机无线配置；拒绝时可在同一串口中重新短按确认重试，无需重输密码。
5. 成功后该命令自动启动 Bridge。等终端显示「设备已握手：Wi-Fi 加密连接；固件 0.2.0」，设备顶部显示 Wi-Fi、时间与额度已同步，再拔 USB。Bridge 终端需要保持运行。

旧脚本先提示设备授权、后打开串口，存在开串口时改变 DTR/RTS 导致授权失效的风险；[pySerial 官方文档](https://pyserial.readthedocs.io/en/latest/pyserial_api.html#serial.Serial.open)说明了打开串口时的控制线变化。新版先打开 USB、收到稳定 hello，再提示物理授权；用 boot 标识检测其间重启。**这是代码中已发现的时序问题，本次用户拒绝回执的具体原因尚未从实机确认。** V0.2.0 只有布尔失败回执，不能区分未授权、过期和 NVS 存储失败；脚本不会把它称为密码错误。

Wi-Fi 密码只经 USB 发送到设备，不写入 Mac 配对文件。`private/wireless-pending.json` 只保留 IP 与随机配对密钥，用于回执丢失后的重试；收到成功回执才提升为 `wireless.json`。

## 本次升级

1. 在所有正在运行 Bridge 的终端按 Control+C 停止它。保持 USB 数据线连接。
2. 双击 **「升级并配置无线.command」**。脚本先检查旧 Bridge 是否占用，再验证账户、双读备份和更新应用。此设备两次读取完整 Flash 合计约 6 分钟，进度会显示；不要重复启动。
3. 刷入后，脚本询问 2.4 GHz Wi-Fi 名称、隐藏输入的密码、Mac 局域网 IP。默认 IP 来自 en0，可修改为实际地址。
4. 等终端显示 USB 已连接后，在设备第六页「连接与配网」短按并松开确认，看到「请在 Mac 运行无线配对」后，在 60 秒内回到终端按回车发送配置。收到设备成功回执才完成配对。
5. 脚本自动启动无线 Bridge。设备应显示 Wi-Fi、当前时间、真实窗口和次数，终端应显示「设备已握手：Wi-Fi 加密连接；固件 0.2.0」。此时可以拔掉 USB 数据线。
6. 日后运行 **「仅启动桥接.command」**。已配对时默认无线；Mac 需要开机、Bridge 运行，并与设备处于可互访的局域网。若 macOS 防火墙询问 Python 入站连接，需要允许这个 Bridge。

仅重新配网：先关闭 Bridge，连接 USB，运行「配置无线连接.command」，等 USB 握手后在设备允许配对，再发送；成功后自动启动无线 Bridge。若 Mac 的 DHCP 地址变了，也用这个流程更新地址和证书。建议为 Mac 设路由器 DHCP 地址保留。

继续用 USB 也可以：未配置无线时「仅启动桥接」自动选择唯一的 USB 设备；已配对后若需要 USB，可在终端执行 `scripts/run_bridge.sh /dev/cu.usbmodem1101`。不需要再刷写。

## 界面与三个按键

- 普通页面：短按 / 长按上、下都换页；设置与事件页：短按选择内容，长按换页。长按阈值 650 ms，每次只换一页，释放不补短按。
- 主页：Apple 原版宠物、状态、5 小时 / 7 天额度；确认互动。失败和拒绝使用 😭，没有 😶 过渡；额度耗尽使用分别处理后并排的 😐🤲。
- 额度页：显示真实窗口和下一次重置倒计时。数据不存在时说明等待同步，不能把未知当 0。窗口由官方实际分钟数决定。
- 重置页：显示真实可用次数，确认进入提示，再确认进入最终步骤，释放后重新长按 1 秒提交。明确消耗 1 次。方向键取消或长按离页；零次数 / 离线 / 身份未校验时不能提交。也可以一直等待自然重置。
- 权限页：自动弹出，默认无选择。上键批准、下键拒绝，短按确认，再释放后重新长按 1 秒提交；确认页上键取消、下键静音。长按方向键离开会取消选择，请求仍保留；在普通页面长按确认可返回待处理请求。
- 声音页：提示音开关、当前请求静音、音量、重复间隔（30/60/120 秒）、返回主页。
- 事件页：最近事件，短按方向键浏览。初始明确提示等待会话事件，不以 `unknown` 冒充任务状态。
- 连接页：真实无线状态、失败原因、账户同步状态、允许 USB 配对入口。设备没有 SIM，无需蜂窝网络。

权限提醒仍为 1200 Hz 三声、180 ms 发声、120 ms 间隔；立即一轮，之后按间隔最多再三轮。独立音频任务，队列有界。设置未持久化，重启恢复默认；Wi-Fi 配对会保留。

## 批准与重置的真实边界

设备批准已启用，不再一律拒绝所有批准。当前仅开放能够完整显示、字段范围明确的普通 Bash 请求：`pwd`、`/bin/pwd`、`ls`、`ls -la`、`git status`、`git status --short`、`git diff --stat`；工作目录或完整项目名称必须可在设备显示。长路径以完整的项目名称和上级文件夹标识，并绑定原始路径摘要。复杂脚本、项目名称仍过长、非 ASCII 目录、额外未知权限字段、持久权限前缀和其他工具仍要求 Mac 审阅。它不是对命令零风险的保证，也不会改写命令或申请扩大范围。

批准通过官方 PermissionRequest Hook 的 allow 输出返回原客户端；拒绝用 deny。界面先显示「批准待回执」，只有观察到相同会话、工具和输入的 PostToolUse，才短暂显示 😆。其他 Hooks 仍可能否决；向 Hook 提交不等于最终执行成功。

额外重置使用官方 `account/rateLimitResetCredit/consume`。Bridge 在提交前重新读取并核对账户身份；同一次操作的 UUID 写入私有日志后才调用接口，断线重试复用原 UUID。结果为 reset / alreadyRedeemed / nothingToReset / noCredit，随后重新读取窗口和次数。没有根据响应自行把额度填成 100%。开发测试只使用模拟 consumer，**没有消费真实次数**。

本机已注册用户级 Hooks，覆盖其他本地 Codex 项目；首次审阅并信任后，完整退出桌面应用再重新打开原聊天，避免继续使用安装前的旧会话。不用重复注册项目副本。Bridge 不启动无关模型任务来冒充接入。Stop 表示本轮响应结束，显示庆祝；不等于整个项目验收成功。官方 Hook 暂不提供可靠的整轮失败事件，本版不会把普通工具非零退出误判为整项任务失败；失败表情已实现，但真实失败事件仍需后续宿主联调。

## Apple 图像与字体

本机通过 AppKit 和系统 Apple Color Emoji 输出透明 PNG，只缩放和转换 RGB565，黑色背景直接融合；没有 AI 绘制、网页截图背景、其他平台 Emoji 或嵌入字体文件。生成资源已编入本机待刷镜像，设备不运行时下载图片。

Apple 设计仍归权利人所有。本次没有查到覆盖 ESP32 固件公开分发的许可；从网站裁剪不能消除版权。本机生成用于当前私人原型，**这不是对该用途合法性的保证，也不是获得公开分发许可**。PNG、生成的图片头和含图像二进制不放入源码分享包。公开分发前应取得适用权利，或导入有权使用的 Apple 原图。来源记录在 `assets/generated/rights.json`。

界面中文使用 Adobe 思源黑体的专用子集，许可证在 `licenses/SourceHanSansSC.txt`；它仅用于文字，不替代 Apple Emoji。字库清单与来源哈希在 `docs/ui-font.json`。

## 通信和账户

- Mac 保管官方 Codex 登录，设备只有 Wi-Fi 凭据、Bridge 配对密钥和服务器证书，不保存 Codex token / API Key。
- 初次通过物理 USB 和设备确认，配置 2.4 GHz Wi-Fi。随后通过 HTTPS、私有 CA / 主机地址校验和随机配对密钥通信；未关闭证书校验。
- LAN 服务默认 8765，仅响应有正确密钥的设备请求。配对证书与密钥、幂等日志和备份位于权限 0700 的 `private/`，不要上传。
- 设备每秒交换快照，包含 boot / epoch / 序号 / 请求 ID / 内容摘要 / TTL。过期、重复、旧启动会话的决策被拒绝。
- 时间从 Mac 的 UTC 和本地偏移同步，使用单调时钟计算长按、过期与提醒。联网精度依赖 Mac 系统校时；不是设备独立 SNTP。
- V0.2 Bridge 使用私有 Python 3.12 / OpenSSL 3 环境。旧 SDK Python 的 TLS 不兼容问题已在本机复现，因此不再用于无线服务；Hook 本身仍可用系统 Python。

## 备份、构建和恢复

刷写只写经过核对的 factory 应用，保留 bootloader / 分区表 / NVS，不执行整片擦除。要求实际 8 MB C3、未启用 Secure Boot / Flash Encryption、有效分区 MD5、单 factory 布局、匹配的设备身份，写入的完整擦除扇区不能越过分区或 0x300000。配对阶段会在 NVS 的本项目命名空间 `pcc_wifi` 保存配置，不擦除原有其他数据。

恢复此次改动区间：

```sh
source scripts/env.sh
python scripts/flash.py restore --backup private/backups/对应目录 --image dist/此次写入的原版本.bin --execute
```

需要匹配备份旁的 last-write.json。之前的 V0.1.0 / V0.1.1 应用已保存在 dist 中；新备份生成后，应保留本版镜像，便于回退。

本机重建：

```sh
# 从当前聊天工作目录执行，复用已经验证过的离线组件缓存：
PASSPORT_DEPS="$PWD/work/firmware-deps" outputs/PassportController/scripts/build_personal.sh
outputs/PassportController/scripts/check.sh
```

`build_personal.sh` 在本机生成 Apple 图片并构建；含图像文件应保留在私人使用范围，先确认适用权利。换电脑需设置 `PASSPORT_TOOL_ROOT`、现代 Python 和 Pillow 路径，不能假设本机缓存可用。SDK 组件版本锁定见 firmware/dependencies.lock。

本次验证：`docs/V0.2验收.md`。早期文档描述当时的限制，不能覆盖本版说明。

官方依据：[Codex Hooks](https://learn.chatgpt.com/docs/hooks)、[App Server 账户与重置](https://learn.chatgpt.com/docs/app-server)、[Apple macOS 许可](https://www.apple.com/legal/sla/docs/macOSSequoia.pdf)、[Emojipedia 的厂商图像授权说明](https://prod-v2.emojipedia.org/licensing)、[Adobe 思源黑体](https://github.com/adobe-fonts/source-han-sans)、[LVGL 字体转换器](https://github.com/lvgl/lv_font_conv)。这些资料不构成 Apple 向本项目授予固件图像分发许可。

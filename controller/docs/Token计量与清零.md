# 0.2.9 Token 计量与清零 / Token accounting and reset

> 历史版本记录 / Historical version record. 当前候选版见 [0.2.10](Token与无线修复0.2.10.md)。

2026-10-25 · Firmware 0.2.9 · Bridge 0.2.9-token-ledger

## 中文

「启动桌面App实体审批.command」是正确的日常入口。它使用同目录的 Bridge、relay 和 private 配置。费率编辑器与 Bridge 共用 private/token_rates.json；新启动提示显示程序目录和已配置的模型 ID。「检查Token计量.command」只读显示实际运行版本、模型、费率命中、用量、费用状态和程序路径。

### 修复的问题

- 官方线程启动／恢复结果的 model 位于 result.model。旧 relay 漏读它，可能导致当前模型未知，无法匹配已经保存的价格。
- 官方 thread/tokenUsage/updated 的 last 是最后一次模型响应的用量，不是整轮对话。新计量器对同轮累计差值求和，重复事件不重复增加。
- 旧版将整段历史累计套用当前模型的费率。新版按观测到的模型分组，分别计算费用；模型切换不把历史用量重新算成新模型价格。无法确定模型的部分不伪造费用。
- Bridge 重启后，relay 会重放模型和数值摘要。首次恢复的历史快照只建立基线；已有基线上的新增差值可以补计，重复或较旧的摘要不重复计数。
- 缓存输入、缓存写入已属于输入分类；费用计算分别按对应费率计一次。推理 Token 已包含在输出中，不重复收费。
- 费用提示区分等待用量、模型未知、此模型费率缺失和缓存写入费率缺失，不再一律显示“费用关闭”。价格保存后热加载，无需为费率编辑重启 Bridge。
- Token、费用、模型和费率状态参与设备刷新判断，避免显示更新延迟。

### 统计范围

首页和“最近一轮”显示当前活跃聊天的一轮中已观测到的用量；一轮可以包含多次模型调用。累计页显示本项目 Bridge 接入的聊天自开始记录／上次清零后的总计，不是服务商账户总账，也不是上下文占用率。首次接入前的旧历史不回溯估价；切入正在运行的轮次时可能只覆盖后半段。输入每次包含服务端计入的上下文，因此累计输入可以远高于可见聊天文字数量。

计数、原始累计基线、轮次和模型分组保存在本机 private/token-ledger.json（0600）。Bridge 重启保留计数。缓存/推理细目不能再与输入/输出重复相加。费用是按当前本地费率重算的估计值；修改费率会重算已观测用量的估价，不是服务商发票。未取得上游用量、计数回退或存储失败时，通过检查入口查看原因，不用文本长度或时间估算 Token。

### 清零

设备：在“累计 Token · 自清零”页第一次短按确认只打开二次确认页，不会清零；必须松开，再长按确认一秒才提交。连续短按不会清零；方向键取消。必须有有效 Bridge 连接和计数版本。收到新版本回执才结束等待；超时不冒充成功。

Mac：运行「清零Token计数.command」，查看状态后输入 RESET；费率窗口也有“清零控制器计数”。清零保存到本机，保留原始累计基线来拒绝重复旧数据。它不修改 Codex 聊天、服务商用量、账单、订阅额度或额外重置次数。

### 更新与验证

运行「更新Token计量与清零固件.command」。脚本核对镜像和 App 版本，运行完整主机测试，提示停止旧 Bridge，双读 8 MB 备份，只更新 factory 应用并回读校验，保留 Wi-Fi 和费率。随后按提示 Command+Q 退出 App，再回终端按回车，由脚本重新打开 App 和 Bridge；从侧栏打开原聊天。重新打开 App 是为了加载新的 relay，单独重启 Bridge 无法改变已运行的旧 relay 代码。

验证：178 项 Python 测试，控制器／音序及八组音频检查通过；固件 2,357,504 字节，ESP-IDF 5.5.3 构建及 esptool 校验通过。五种实际字库 LVGL 预览已检查。93 个本机真实数值事件的离线回放与累计差值一致，重复回放和重载未重复计数，配置的模型费率命中。当前在线设备/Bridge 在开发检查时仍为 0.2.8；0.2.9 尚未刷入或完成实体清零验收。不更改用户已保存的费率，不在本次修复中自动清零实际计数。

## English

The existing desktop approval launcher is the correct entry point. Bridge, relay and rate editor share its project-local private directory. The new diagnostic launcher reports the running version, selected model, configured price cards, usage, pricing reason and project path.

The relay now reads result.model from official thread start/resume responses. Accounting uses cumulative deltas, groups observed usage by model, sums multiple model responses within one user turn, and deduplicates replays. Initial restored snapshots establish a baseline instead of charging old history again. Existing baselines recover missed final deltas. Cached input/write categories and reasoning output are not billed twice.

The current-turn display covers observed responses in the active chat; the resettable total covers chats observed by this project's Bridge since recording began or the last local reset. It is not account-wide billing or context occupancy. Missing earlier history is not reconstructed or priced. Estimates use the currently configured local rates, so editing rates reprices observed model groups; they are not provider invoices.

Numeric baselines, counters, turn IDs and model groups persist privately in token-ledger.json. Reset preserves the cumulative replay baselines but clears the local displayed counters/estimates. On-device reset opens a separate confirmation screen on a short press. Only a fresh one-second hold there submits it; repeated short presses never reset counters. Direction keys cancel. A matching live meter version is required. A Mac launcher and the rate editor also provide explicitly confirmed reset. None of these actions modifies chats, upstream billing, subscription limits or reset credits.

Run 更新Token计量与清零固件.command to validate/build-check, back up and application-only update while retaining pairing and rates, then follow its App relaunch instructions to load the new relay. Do not simply restart the old Bridge and expect already-running relay code to change.

Validation: 178 Python tests, controller/tone and eight audio-worker checks, ESP-IDF build and esptool image verification, five actual-font LVGL previews, and offline replay of 93 real numeric usage events. Duplicate replay/reload produced no double counting and the configured model rate matched. Firmware 0.2.9 is built locally (2,357,504 bytes); physical update/reset acceptance is still pending. No actual counter reset or device flash was performed by this repair session.

## Sources / 依据

- Official App Server notifications: https://developers.openai.com/codex/app-server
- Installed CLI-generated v2 ThreadStartResponse, ThreadResumeResponse, ThreadTokenUsage and TokenUsageBreakdown definitions.
- Official protocol/core usage semantics: https://github.com/openai/codex/blob/main/codex-rs/protocol/src/protocol.rs
- Official Responses usage mapping: https://github.com/openai/codex/blob/main/codex-rs/codex-api/src/sse/responses.rs
- Official restored-usage replay: https://github.com/openai/codex/blob/main/codex-rs/app-server/src/request_processors/token_usage_replay.rs

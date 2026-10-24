# OpenAI / GPT / Codex API compatibility · API 兼容路线图

## 中文

用户要求兼容第三方提供的 Codex／OpenAI／GPT API。本计划指兼容这些模型与协议的服务商或网关，当前不扩展为通用多平台模型框架。

**状态：自定义 provider 的会话 Token 计数与本地估价已实现；服务商覆盖仍需逐一实测。** Bridge 读取当前 Codex App Server 的 `thread/tokenUsage/updated` 通知，并显示实际线程报告的本轮与会话累计 Token 分项；没有通知时不估算。它不会调用 ChatGPT 专用账户／重置 RPC，也不会把第三方余额伪装成订阅额度。可在 Mac 用 `配置Token费率.command` 按模型 ID 设置每百万 Token 价格；不预设 GPT-6 Astra 价格，费率文件留在私有本机目录。

分三层实现，保留现有固件协议：

1. **推理提供商**：优先使用 Codex 官方用户级 `model_provider` / `model_providers` 配置，核对 Responses、SSE 完成事件、工具调用 ID、工具结果、多轮输入和实际模型目录。只有 Chat Completions 兼容不能视为可用。
2. **会话与审批**：继续在 Mac 通过受支持的 Hooks 或与界面共享的 App Server 处理。当前 ChatGPT 模式、已核对 App 版本的原聊天已通过真实目录申请的设备允许／拒绝；每个第三方配置仍须重新验证。模型 API 不负责 Mac 文件系统授权，禁止将模型生成的“允许”当成人的按键批准。
3. **用量提供商**：将 ChatGPT 订阅窗口／重置次数与第三方 token 用量／预算／余额独立表示。没有服务商官方余额接口时显示“不支持查询”，不推算剩余额度或使用假重置时间。

后续验收清单：

- [x] 从 Codex 本地配置识别当前 provider/model；令牌和自定义 header 不转发到设备。
- [ ] 验证服务商、实际模型 ID、文档和认证方式；密钥只保存在 Mac。
- [ ] 使用隔离配置验证 CLI，再验证桌面 App；保留原有 ChatGPT 配置。
- [ ] 验证流式完成、工具往返、多轮继续、失败、断线与限额错误。
- [ ] 验证真实硬件允许／拒绝、过期、重复请求、Mac 同时处理和撤销。
- [x] 读取 App Server 当前线程 tokenUsage 通知；费用默认隐藏，只有按模型配置本地费率后估算；缓存写入缺少费率时不显示总估价。
- [ ] 在用户当前使用的实际第三方模型／网关上，确认 App Server 会持续报告真实 Token 用量并与服务商账单核对。
- [ ] 验证现有 Emoji、提醒、三键、时间和电量不受切换影响。

## English

The compatibility target is third-party services or gateways exposing Codex/OpenAI/GPT models and protocols. A general-purpose multi-provider model framework is outside this phase.

**Status: session token metering and local estimates for custom providers are implemented; each model/gateway still needs real-world verification.** The Bridge reads the active Codex App Server `thread/tokenUsage/updated` notification and reports per-turn and session totals for the active thread. Missing notifications stay unavailable. The Bridge does not call ChatGPT-only account/reset RPCs or present third-party balances as subscription limits. A local Mac editor configures per-million-token prices by model ID; GPT-6 Astra pricing is not hard-coded and the rate file stays private.

Keep the firmware protocol and separate three responsibilities:

1. **Inference provider:** use official user-level `model_provider` / `model_providers` configuration where possible. Validate Responses, SSE completion events, tool call IDs/results, replayed conversation input and model catalogs. Chat Completions support alone is insufficient.
2. **Sessions and approvals:** keep supported Hooks or a shared App Server on the Mac. The current ChatGPT configuration and checked App build passed physical Allow/Deny of real directory requests in the original chat; each third-party configuration still needs independent validation. A model API cannot grant Mac filesystem permissions, and model-generated approval text must never count as a physical user decision.
3. **Usage provider:** keep ChatGPT windows/reset credits separate from provider token usage, budgets, and balances. Without a documented provider balance endpoint, show an unsupported state instead of inventing remaining quota or reset times.

Acceptance checklist:

- [x] Identify the configured provider/model and keep keys on the Mac; never expose bearer headers to the device.
- [ ] Verify the provider model catalog and authentication behavior against its own documentation.
- [ ] Validate CLI in an isolated configuration, then the desktop App; preserve existing ChatGPT configuration.
- [ ] Test streaming completion, tool round trips, follow-ups, failures, disconnects and limit errors.
- [ ] Test real hardware allow/deny, expiry, duplicates, Mac-side resolution and cancellation.
- [x] Read App Server token-usage notifications; estimates are disabled until local per-model rates are configured, and remain unavailable when a reported token class has no rate.
- [ ] Validate that each model/gateway the user uses reports token usage consistently and reconcile counts against its billing records.
- [ ] Preserve emoji, sound, button, clock and battery behavior across provider changes.

## Official references / 官方依据

- [Provider configuration](https://learn.chatgpt.com/docs/enterprise/connect-to-a-gateway)
- [Responses and tool compatibility requirements](https://learn.chatgpt.com/docs/enterprise/gateway-compatibility)
- [Hooks](https://learn.chatgpt.com/docs/hooks)
- [App Server approvals and account interfaces](https://learn.chatgpt.com/docs/app-server)

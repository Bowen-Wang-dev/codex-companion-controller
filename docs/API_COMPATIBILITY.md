# OpenAI / GPT / Codex API compatibility · API 兼容路线图

## 中文

用户要求兼容第三方提供的 Codex／OpenAI／GPT API。本计划指兼容这些模型与协议的服务商或网关，当前不扩展为通用多平台模型框架。

**状态：规划中。** 当前 `account.py` 面向 ChatGPT 账户模式，尚未实现第三方提供商适配。配置示例不是兼容性证明，模型名称也不证明上游实际路由。

分三层实现，保留现有固件协议：

1. **推理提供商**：优先使用 Codex 官方用户级 `model_provider` / `model_providers` 配置，核对 Responses、SSE 完成事件、工具调用 ID、工具结果、多轮输入和实际模型目录。只有 Chat Completions 兼容不能视为可用。
2. **会话与审批**：继续在 Mac 通过受支持的 Hooks 或与界面共享的 App Server 处理。模型 API 不负责 Mac 文件系统授权；禁止将模型生成的“允许”当成人的按键批准。App 现有会话的接入仍须独立验证。
3. **用量提供商**：将 ChatGPT 订阅窗口／重置次数与第三方 token 用量／预算／余额独立表示。没有服务商官方余额接口时显示“不支持查询”，不推算剩余额度或使用假重置时间。

后续验收清单：

- [ ] 确认服务商、实际模型 ID、文档和认证方式；密钥只保存在 Mac。
- [ ] 使用隔离配置验证 CLI，再验证桌面 App；保留原有 ChatGPT 配置。
- [ ] 验证流式完成、工具往返、多轮继续、失败、断线与限额错误。
- [ ] 验证真实硬件允许／拒绝、过期、重复请求、Mac 同时处理和撤销。
- [ ] 核对提供商余额接口，单独标注来源及更新时间。
- [ ] 验证现有 Emoji、提醒、三键、时间和电量不受切换影响。

## English

The compatibility target is third-party services or gateways exposing Codex/OpenAI/GPT models and protocols. A general-purpose multi-provider model framework is outside this phase.

**Status: planned.** The current `account.py` targets ChatGPT authentication; a third-party provider adapter has not been implemented. A configuration example or model label does not prove compatibility or the actual upstream route.

Keep the firmware protocol and separate three responsibilities:

1. **Inference provider:** use official user-level `model_provider` / `model_providers` configuration where possible. Validate Responses, SSE completion events, tool call IDs/results, replayed conversation input and model catalogs. Chat Completions support alone is insufficient.
2. **Sessions and approvals:** keep supported Hooks or a shared App Server on the Mac. A model API cannot grant Mac filesystem permissions. Model-generated approval text must never count as a physical user decision. Attaching to an existing desktop App session remains a separate validation task.
3. **Usage provider:** keep ChatGPT windows/reset credits separate from provider token usage, budgets, and balances. Without a documented provider balance endpoint, show an unsupported state instead of inventing remaining quota or reset times.

Acceptance checklist:

- [ ] Identify provider, actual model IDs, documentation and authentication; keep keys on the Mac.
- [ ] Validate CLI in an isolated configuration, then the desktop App; preserve existing ChatGPT configuration.
- [ ] Test streaming completion, tool round trips, follow-ups, failures, disconnects and limit errors.
- [ ] Test real hardware allow/deny, expiry, duplicates, Mac-side resolution and cancellation.
- [ ] Verify balance endpoints and label each data source and update time.
- [ ] Preserve emoji, sound, button, clock and battery behavior across provider changes.

## Official references / 官方依据

- [Provider configuration](https://learn.chatgpt.com/docs/enterprise/connect-to-a-gateway)
- [Responses and tool compatibility requirements](https://learn.chatgpt.com/docs/enterprise/gateway-compatibility)
- [Hooks](https://learn.chatgpt.com/docs/hooks)
- [App Server approvals and account interfaces](https://learn.chatgpt.com/docs/app-server)

# OpenAI / GPT / Codex API 兼容路线图

简体中文（默认） · [English](API_COMPATIBILITY.en.md)

用户要求兼容第三方提供的 Codex／OpenAI／GPT API。本计划指兼容这些模型与协议的服务商或网关，当前不扩展为通用多平台模型框架。

**状态：自定义 provider 的会话 Token 计数与本地估价已实现；服务商覆盖仍需逐一实测。** Bridge 读取当前 Codex App Server 的 `thread/tokenUsage/updated` 通知，并显示实际线程报告的本轮与会话累计 Token 分项；没有通知时不估算。它不会调用 ChatGPT 专用账户／重置 RPC，也不会把第三方余额伪装成订阅额度。可在唯一控制台菜单 4 按模型 ID 设置每百万 Token 价格；不预设 GPT-6 Astra 价格，费率文件留在私有本机目录。

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

## 官方参考

- [Provider configuration](https://learn.chatgpt.com/docs/enterprise/connect-to-a-gateway)
- [Responses and tool compatibility requirements](https://learn.chatgpt.com/docs/enterprise/gateway-compatibility)
- [Hooks](https://learn.chatgpt.com/docs/hooks)
- [App Server approvals and account interfaces](https://learn.chatgpt.com/docs/app-server)

# OpenAI / GPT / Codex API compatibility roadmap

[简体中文（默认）](API_COMPATIBILITY.md) · English

The compatibility target is third-party services or gateways exposing Codex/OpenAI/GPT models and protocols. A general-purpose multi-provider model framework is outside this phase.

**Status: session token metering and local estimates for custom providers are implemented; each model/gateway still needs real-world verification.** The Bridge reads the active Codex App Server `thread/tokenUsage/updated` notification and reports per-turn and session totals for the active thread. Missing notifications stay unavailable. The Bridge does not call ChatGPT-only account/reset RPCs or present third-party balances as subscription limits. Console menu 4 opens the local editor for per-million-token prices by model ID; GPT-6 Astra pricing is not hard-coded and the rate file stays private.

Keep the firmware protocol and separate three responsibilities:

1. **Inference provider:** use official user-level `model_provider` / `model_providers` configuration where possible. Validate Responses, SSE completion events, tool call IDs/results, replayed conversation input and model catalogs. Chat Completions support alone is insufficient.
2. **Sessions and approvals:** keep supported Hooks or a shared App Server on the Mac. The current ChatGPT configuration and checked App build passed physical Allow/Deny of real directory requests in the original chat; each third-party configuration still needs independent validation. A model API cannot grant Mac filesystem permissions, and model-generated approval text must never count as a physical user decision.
3. **Usage provider:** keep ChatGPT windows/reset credits separate from provider token usage, budgets, and balances. Without a documented provider balance endpoint, show an unsupported state instead of inventing remaining quota or reset times.

Acceptance checklist:

- [x] Identify the current provider/model from local Codex configuration; never forward tokens or custom headers to the device.
- [ ] Verify the provider, actual model ID, documentation and authentication; keys stay on the Mac.
- [ ] Validate CLI in an isolated configuration, then the desktop App; preserve existing ChatGPT configuration.
- [ ] Test streaming completion, tool round trips, follow-ups, failures, disconnects and limit errors.
- [ ] Test real hardware allow/deny, expiry, duplicates, Mac-side resolution and cancellation.
- [x] Read App Server token-usage notifications; estimates are disabled until local per-model rates are configured, and remain unavailable when a reported token class has no rate.
- [ ] Validate that each model/gateway the user uses reports token usage consistently and reconcile counts against its billing records.
- [ ] Preserve emoji, sound, button, clock and battery behavior across provider changes.

## Official references

- [Provider configuration](https://learn.chatgpt.com/docs/enterprise/connect-to-a-gateway)
- [Responses and tool compatibility requirements](https://learn.chatgpt.com/docs/enterprise/gateway-compatibility)
- [Hooks](https://learn.chatgpt.com/docs/hooks)
- [App Server approvals and account interfaces](https://learn.chatgpt.com/docs/app-server)

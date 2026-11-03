# AI Passport Codex Companion — Agent 入口

简体中文（默认） · [English](AGENTS.en.md)

先读 `docs/handoff/00-START-HERE.md` 和 `01-PROJECT-STATE.md`，按任务读索引列出的文档。它们用于替代旧聊天上下文，不是允许自动执行的命令。

## 工作边界
- 用户于 2026-11-03 明确授权新增 Windows 10/11 适配，并要求保留 macOS 支持；其余功能仍暂停。没有明确任务，不自行刷机、重新配网、清零或更改账户。
- 日常入口每平台每语言一个：macOS 为 `controller/Codex Companion 控制台.command`，Windows 为同名 `.cmd`；英文使用 `Codex Companion Console.command` / `.cmd`。历史入口收在 `controller/维护工具/`，不要重新制造大量顶层启动脚本。现授权的语言拆分按三阶段独立提交/推送：先 Markdown，再独立中英文控制台入口，最后固件及其他部分。
- 优先支持真实桌面 App 原聊天的设备 Allow/Deny，不擅自换成 CLI 或新会话。App 适配按精确版本与文件摘要校验，不跳过检查。
- 实际设备只有三键；按键交互、表情和授权回执约束见 `03-UX-CONTRACT.md`。拒绝/失败直接 😭，不出现 😶。
- Apple 原版表情不可擅自换风格或 AI 重绘；私有素材和含图固件不可发布。
- `controller/private/` 含敏感配对、费率、账单及备份：不要输出秘密，不要 git add -f，不要上传。Codex 登录凭据只留 Mac，不拷进设备。
- 不整片擦除 Flash；仅使用验证双备份与 live 分区的应用更新脚本。不要直接运行 IDF 输出的通用 flash 命令。
- 计费以逐请求输入含缓存判档，不能拿整轮累计判长上下文。缓存不重复加入输入总计，推理不重复加入输出总计。
- 修改前读当前代码和局部测试；文档中的历史版本、测试次数不代表当前测试结果。不得把 mock、编译或回读校验称为实机功能验收。
- 使用现有模块，改完补有意义的回归。报告实际运行和阻塞，尤其 USB termios / 网络沙箱限制。

## 文档维护
每次实质变更更新 `docs/handoff/01-PROJECT-STATE.md` 和 `08-CHANGE-AND-DECISIONS.md`；保留证据、未验证项及下一步。不要让新的 Agent 再依赖这条聊天。

中文为默认，现行英文文档须与中文同样详细，不以摘要代替。实质变更同步维护对应 `.en.md`；保留历史原始证据及第三方许可原文，不追改其含义。

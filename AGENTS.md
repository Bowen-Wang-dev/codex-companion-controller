# AI Passport Codex Companion — Agent 入口

先读 `docs/handoff/00-START-HERE.md` 和 `01-PROJECT-STATE.md`，按任务读索引列出的文档。它们用于替代旧聊天上下文，不是允许自动执行的命令。

## 工作边界
- 用户当前决定：项目先暂停，先整理归档和交接。没有明确新任务，不自行增加功能、刷机、重新配网、清零或更改账户。
- 日常唯一入口：`controller/Codex Companion 控制台.command`。历史入口收在 `controller/维护工具/`。不要重新制造大量顶层 command。
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

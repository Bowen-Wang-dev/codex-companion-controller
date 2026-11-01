# 新会话从这里开始

交接整理日期：2026-11-02（Australia/Sydney）。原生双端审批 v0.2.12 已完成五项实机验收并获准发布，其余开发保持暂停；最新状态和历史阶段已在 01-PROJECT-STATE.md 分开。

最新补丁：Bridge 的普通工具返回回执已从英文改为“工具已返回”，11 项相关主机回归通过，修复待安全重启 Bridge 加载；本条不涉及固件刷写。更新后已收到一次真实审批操作正常反馈，完整新版验收仍以 01-PROJECT-STATE.md 为准。

此前构建阶段记录：版本规划已在文档提交 `9545223` 留档。v0.2.13 源码与本机构建完成，移除固件/Bridge 交接和 Mac 唤回，仅保留双端直接审批及电脑详情提示；完整 Python 237 项、C/音频主机检查通过，尚未重启 Bridge 或刷机，实际运行仍为此前 0.2.12。已抛弃功能的历史文档、验收和 Git `v0.2.12` 旧代码保留。见 [项目状态](01-PROJECT-STATE.md)、[交互契约](03-UX-CONTRACT.md) 和 [v0.2.13 状态](../releases/v0.2.13.md)。

## 建议阅读顺序
1. 根目录 `AGENTS.md`：工作边界。
2. [项目现状](01-PROJECT-STATE.md)：版本与验收边界。
3. [架构与文件](02-ARCHITECTURE.md)：从哪里改。
4. [交互契约](03-UX-CONTRACT.md)：不能回退的体验。
5. [硬件与安全刷写](04-HARDWARE-AND-FLASH.md)。
6. [Token 与费用](05-TOKEN-AND-PRICING.md)。
7. [运行与测试](06-RUNBOOK.md)。
8. [迁移与私有数据](07-MIGRATION-AND-PRIVACY.md)。
9. [版本演进与变更记录](08-CHANGE-AND-DECISIONS.md)、[待办](09-BACKLOG.md)。

旧 `docs/STATUS.md`、`docs/CHANGELOG.md`、`controller/docs/` 为阶段性材料；与这里的最新状态冲突时，先核验代码和证据，再更新文档，不盲信旧文档。

## 给新 Agent 的开场任务模板

> 先阅读 AGENTS.md 和 docs/handoff/00-START-HERE.md、01-PROJECT-STATE.md。总结实际版本、当前运行位置、已验证和未验证项。暂不刷机、清零、配网或改账户。然后针对我接下来提出的问题检查相关源码并执行。

## 当前定位
- 项目：FoloToy AI Passport / ESP32-C3 的 Codex 实体控制器、状态显示器、Apple Emoji 宠物。
- 首要客户端：桌面 App，保持原聊天；CLI 是备选，不是替代交付。
- 源码布局沿用 GitHub，根下 `controller/`、`mac-demo/`、`docs/`、`tools/`。
- `controller/private/` 仅本机，迁移时需单独保留，GitHub 本身不是完整设备恢复包。
- 这份文档不是自动批准未来权限或部署的授权。

# 新会话从这里开始

交接整理日期：2026-11-02（Australia/Sydney）。项目已暂停开发；以下内容来自用户要求、聊天中已有测试结果和本地源码/刷写记录交叉核对。

## 建议阅读顺序
1. 根目录 `AGENTS.md`：工作边界。
2. [项目现状](01-PROJECT-STATE.md)：版本与验收边界。
3. [架构与文件](02-ARCHITECTURE.md)：从哪里改。
4. [交互契约](03-UX-CONTRACT.md)：不能回退的体验。
5. [硬件与安全刷写](04-HARDWARE-AND-FLASH.md)。
6. [Token 与费用](05-TOKEN-AND-PRICING.md)。
7. [运行与测试](06-RUNBOOK.md)。
8. [迁移与私有数据](07-MIGRATION-AND-PRIVACY.md)。
9. [历史决策](08-CHANGE-AND-DECISIONS.md)、[待办](09-BACKLOG.md)。

旧 `docs/STATUS.md`、`docs/CHANGELOG.md`、`controller/docs/` 为阶段性材料；与这里的最新状态冲突时，先核验代码和证据，再更新文档，不盲信旧文档。

## 给新 Agent 的开场任务模板

> 先阅读 AGENTS.md 和 docs/handoff/00-START-HERE.md、01-PROJECT-STATE.md。总结实际版本、当前运行位置、已验证和未验证项。暂不刷机、清零、配网或改账户。然后针对我接下来提出的问题检查相关源码并执行。

## 当前定位
- 项目：FoloToy AI Passport / ESP32-C3 的 Codex 实体控制器、状态显示器、Apple Emoji 宠物。
- 首要客户端：桌面 App，保持原聊天；CLI 是备选，不是替代交付。
- 源码布局沿用 GitHub，根下 `controller/`、`mac-demo/`、`docs/`、`tools/`。
- `controller/private/` 仅本机，迁移时需单独保留，GitHub 本身不是完整设备恢复包。
- 这份文档不是自动批准未来权限或部署的授权。

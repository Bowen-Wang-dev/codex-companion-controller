# 项目交接入口

维护日期：2026-11-02（Australia/Sydney）。本次授权范围为代码审查、必要修复及文档整理；新功能、部署、刷机、配网、清零和账户调整不在本次范围内。

## 当前摘要

- 源码：固件 `0.2.13`，Bridge `0.2.13-native-app`；已移除详情页长按交接，保留双端直接审批。
- 已有发布基线：`v0.2.12`，五项原生双端实机验收记录完整保留。
- 最近运行记录：后续日志已报告设备固件 `0.2.13`，且有一次真实审批操作正常的反馈；新版完整验收矩阵及各补丁是否已加载仍需分别确认。
- 本次审查不采集新的运行版本快照，不重启服务，不刷写设备。当前状态、历史阶段和验证边界见 [01-PROJECT-STATE.md](01-PROJECT-STATE.md)。
- 普通工具返回中文回执及控制台启动链修复已有源码与回归证据；是否在运行进程中生效，不能从源码版本推定。

## 阅读顺序

1. 根目录 [AGENTS.md](../../AGENTS.md)：工作边界。
2. [项目状态](01-PROJECT-STATE.md)：当前证据及历史阶段。
3. [架构与文件](02-ARCHITECTURE.md)、[交互契约](03-UX-CONTRACT.md)。
4. 按任务阅读 [硬件与刷写](04-HARDWARE-AND-FLASH.md)、[计量](05-TOKEN-AND-PRICING.md)、[运行手册](06-RUNBOOK.md)、[迁移与隐私](07-MIGRATION-AND-PRIVACY.md)。
5. [变更记录](08-CHANGE-AND-DECISIONS.md)、[待办](09-BACKLOG.md)、[常见问题](10-QUICK-FAQ.md)。
6. 本次维护的范围、发现、修复和验证见[审查报告](../reviews/2026-11-02-code-and-docs.md)。

## 操作入口与资料优先级

日常唯一入口为 `controller/Codex Companion 控制台.command`；历史入口在 `controller/维护工具/`。桌面 App 原聊天是主要交付对象，CLI 为备选。

`docs/STATUS.md`、`docs/CHANGELOG.md`、`controller/docs/` 和 [Controller README 历史快照](../history/controller-readme-before-2026-11-02-review.md)属于历史资料。文中的“当前”“本次”均指各自记录阶段。冲突时核对源码和证据，更新现行摘要，不删除历史验收或将其扩展到新版本。

`controller/private/` 仅本机保存，Git 仓库不是完整设备恢复包。文档中的操作步骤只说明流程，不构成未来部署或权限操作的自动授权。

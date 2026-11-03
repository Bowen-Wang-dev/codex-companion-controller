# 文档总索引

简体中文（默认） · [English](README.en.md)

维护日期：2026-11-03（Australia/Sydney）。项目默认使用中文；下表的英文文档是完整对应说明，覆盖相同功能、步骤、技术值、历史阶段及验证边界，不是摘要。两种语言分文件，通过页首链接切换。

## 现行文档

| 内容 | 中文（默认） | English |
|---|---|---|
| 项目介绍与快速入口 | [README](../README.md) | [README](../README.en.md) |
| Controller 使用说明 | [使用说明](../controller/README.md) | [Controller guide](../controller/README.en.md) |
| Agent 工作边界 | [AGENTS](../AGENTS.md) | [AGENTS](../AGENTS.en.md) |
| 交接入口 | [00](handoff/00-START-HERE.md) | [00](handoff/00-START-HERE.en.md) |
| 项目状态与验收边界 | [01](handoff/01-PROJECT-STATE.md) | [01](handoff/01-PROJECT-STATE.en.md) |
| 架构与源码导航 | [02](handoff/02-ARCHITECTURE.md) | [02](handoff/02-ARCHITECTURE.en.md) |
| 交互规范 | [03](handoff/03-UX-CONTRACT.md) | [03](handoff/03-UX-CONTRACT.en.md) |
| 硬件与安全升级 | [04](handoff/04-HARDWARE-AND-FLASH.md) | [04](handoff/04-HARDWARE-AND-FLASH.en.md) |
| Token 与计费模型 | [05](handoff/05-TOKEN-AND-PRICING.md) | [05](handoff/05-TOKEN-AND-PRICING.en.md) |
| 运行与诊断 | [06](handoff/06-RUNBOOK.md) | [06](handoff/06-RUNBOOK.en.md) |
| 迁移、归档与隐私 | [07](handoff/07-MIGRATION-AND-PRIVACY.md) | [07](handoff/07-MIGRATION-AND-PRIVACY.en.md) |
| 版本演进与决策 | [08](handoff/08-CHANGE-AND-DECISIONS.md) | [08](handoff/08-CHANGE-AND-DECISIONS.en.md) |
| 待办与未验收项 | [09](handoff/09-BACKLOG.md) | [09](handoff/09-BACKLOG.en.md) |
| 常见问题 | [10](handoff/10-QUICK-FAQ.md) | [10](handoff/10-QUICK-FAQ.en.md) |
| 设备安装语言 | [13](handoff/13-DEVICE-LANGUAGES.md) | [13](handoff/13-DEVICE-LANGUAGES.en.md) |
| v0.2.14 设备中英文版本 | [版本记录](releases/v0.2.14.md) | [Version record](releases/v0.2.14.en.md) |
| PC 端语言与独立入口 | [12](handoff/12-HOST-LANGUAGES.md) | [12](handoff/12-HOST-LANGUAGES.en.md) |
| macOS / Windows | [11](handoff/11-HOST-PLATFORMS.md) | [11](handoff/11-HOST-PLATFORMS.en.md) |
| 第三方 API 兼容 | [路线图](API_COMPATIBILITY.md) | [Compatibility](API_COMPATIBILITY.en.md) |
| v0.2.12 发布及五项验收 | [发布记录](releases/v0.2.12.md) | [Release record](releases/v0.2.12.en.md) |
| v0.2.13 实现与部署边界 | [版本记录](releases/v0.2.13.md) | [Version record](releases/v0.2.13.en.md) |
| 2026-11-02 代码与文档审查 | [审查报告](reviews/2026-11-02-code-and-docs.md) | [Review report](reviews/2026-11-02-code-and-docs.en.md) |
| Mac Demo | [中文](../mac-demo/README.md) | [English](../mac-demo/README.en.md) |
| 离线依赖与摘要 | [中文](../controller/vendor/README.md) | [English](../controller/vendor/README.en.md) |

第三方许可见[许可说明](../THIRD_PARTY_NOTICES.md)，同页提供完整中文与英文；上游许可原文按原样保留，不以译文替换法律文本。

## 历史资料

[旧 STATUS](STATUS.md)、[旧 CHANGELOG](CHANGELOG.md)、`controller/docs/` 的阶段报告与 [Controller README 原始快照](history/controller-readme-before-2026-11-02-review.md)保留当时原文及已有双语内容，供追溯证据。它们不是现行操作手册，不能把旧文中的“当前”“待更新”当成今日结论；现行完整中英文状态与变更沿革见 01、08 及版本记录。原始快照和第三方许可不为语言整理而追改。

## 维护规则与阶段

- 更新现行中文时，同步更新对应英文，保留同等细节；命令、路径、版本、金额、阈值、摘要、测试数字及已验收/待验收结论必须一致。界面原文可作为识别设备提示的引用保留；不擅自翻译文件名或命令。
- 第一阶段 Markdown 已单独 commit/push；第二阶段现实现独立中文/英文 `.command` / `.cmd` 控制台及 PC 子工具，单独提交/推送；第三阶段现提供由安装入口决定语言的 0.2.14 设备固件及配套保护，另行提交/推送，未代用户刷写。文档描述后续计划不等于相关功能已经交付。
- 源码、镜像、运行加载和实机验收分开记录。本文档阶段不重新运行服务、不触及设备，不把以前测试称为本次新执行。
- 私有配置、账单、配对、备份、Apple 素材及含图固件不进入公开文档或 Git。

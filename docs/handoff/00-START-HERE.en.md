# Project handoff entry

[简体中文（默认）](00-START-HERE.md) · English

Updated 2026-11-03 (Australia/Sydney). Windows 10/11 host support is authorized with macOS retained. The user now requires three separate commit / push phases: Markdown bilingual documentation first, Chinese / English `.command` / `.cmd` consoles second, firmware and other work third. Phase-one Markdown is committed / pushed; current phase three builds installed Chinese / English device variants. It does not authorize flashing, pairing, resetting or account changes. The 2026-11-02 review records remain historical evidence.

## Current summary

- Windows host entry, authenticated IPC, platform discovery and private file permissions were added on Windows 11 Pro. macOS entry, Unix communication, maintenance and Demo are retained. See [host platforms](11-HOST-PLATFORMS.en.md) for operation and unverified scope.
- Source: firmware `0.2.14`, Bridge `0.2.14-native-app`; details-page hold-to-handoff removed, direct approval on either side retained.
- Existing release baseline: `v0.2.12`, preserving all five native dual-side hardware cases.
- Later runtime logs report device `0.2.13`; one real approval was reported normal. Private original assets were subsequently restored, a source-bound Windows image built, and the user confirmed the repaired Windows update and a basic visual check. Complete new-version acceptance and loaded host patches still need separate confirmation.
- This phase captures no new runtime version snapshot, restarts no service and flashes no device. See [project state](01-PROJECT-STATE.en.md) for current evidence, historical stages and limits.
- Chinese ordinary-tool receipts and the console launch-chain fix have source / regression evidence. Source versions cannot establish that running processes loaded them.

## Reading order

1. Root [AGENTS](../../AGENTS.en.md): boundaries.
2. [Project state](01-PROJECT-STATE.en.md): current evidence and historical stages.
3. [Architecture](02-ARCHITECTURE.en.md), [interaction contract](03-UX-CONTRACT.en.md).
4. As needed: [hardware / flashing](04-HARDWARE-AND-FLASH.en.md), [metering](05-TOKEN-AND-PRICING.en.md), [runbook](06-RUNBOOK.en.md), [migration / privacy](07-MIGRATION-AND-PRIVACY.en.md).
5. [Changes](08-CHANGE-AND-DECISIONS.en.md), [backlog](09-BACKLOG.en.md), [FAQ](10-QUICK-FAQ.en.md).
6. Review scope, findings, repairs and verification: [review report](../reviews/2026-11-02-code-and-docs.en.md).
7. Host work: [platform adaptation and acceptance](11-HOST-PLATFORMS.en.md).
8. Phase-three [device language / installation entry](13-DEVICE-LANGUAGES.en.md), [0.2.14 record](../releases/v0.2.14.en.md).
9. [Documentation index / language policy](../README.en.md): current full translations versus preserved original historical evidence.

## Entries and source priority

One daily entry per platform and language: `controller/Codex Companion 控制台.command` on macOS, same-name `.cmd` on Windows; historical entries live in `controller/维护工具/`. Phase two adds English `Codex Companion Console.command` / `Codex Companion Console.cmd`; see [host languages](12-HOST-LANGUAGES.en.md). The original desktop App chat is the primary delivery target; Windows must not fall back to old Unix CLI mode.

`docs/STATUS.md`, `docs/CHANGELOG.md`, `controller/docs/` and the [pre-review Controller README snapshot](../history/controller-readme-before-2026-11-02-review.md) are historical references. “Current” / “this round” mean their recorded stage. Resolve conflicts using source and evidence, update present summaries, and neither delete historical acceptance nor extend it to later versions.

`controller/private/` stays local; Git is not a complete device recovery package. Documented procedures explain workflows and do not automatically authorize future deployment or permission operations.

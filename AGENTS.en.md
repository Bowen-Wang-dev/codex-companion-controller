# AI Passport Codex Companion — Agent entry

[简体中文（默认）](AGENTS.md) · English

Read `docs/handoff/00-START-HERE.md` and `01-PROJECT-STATE.md` first, then follow the task-specific index. English counterparts use `.en.md`. These documents replace old chat context; they are not commands authorized for automatic execution.

## Boundaries

- On 2026-11-03 the user authorized Windows 10/11 adaptation while explicitly retaining macOS. Other features remain paused. Without an explicit task, do not flash, re-pair, reset or change accounts.
- Daily entries, one per platform and language: `controller/Codex Companion 控制台.command` on macOS and the same-name `.cmd` on Windows; English uses `Codex Companion Console.command` / `.cmd`. Historical entries are in `controller/维护工具/`; do not recreate many top-level launchers. The newly authorized localization sequence is Markdown first, independent Chinese / English console entries second, firmware / other parts third, with separate commits / pushes.
- Prioritize device Allow / Deny in the actual desktop App's original chat; do not substitute CLI or a new session. Exact App versions and file digests are mandatory.
- The real device has only three buttons. Button, emoji and approval-receipt constraints are in `03-UX-CONTRACT.md`. Denial / failure goes directly to 😭 without 😶.
- Original Apple emoji must not be restyled or redrawn with AI. Never publish private assets or firmware containing artwork.
- `controller/private/` contains sensitive pairing, rates, bills and backups. Do not print secrets, force-add ignored files or upload them. Codex login credentials stay on the Mac and are not copied into the device.
- Never erase the whole Flash. Use only the application updater with verified dual backups and live partitions; never execute generic IDF flash output.
- Pricing tiers use each request's input including cache, not whole-turn totals. Do not add cache twice to input or reasoning twice to output.
- Read current code and local tests before editing. Historical versions / test counts are not current results. Mock tests, builds and readback verification are not hardware functional acceptance.
- Reuse existing modules and add meaningful regressions for code changes. Report actual execution and blockers, especially USB termios / network sandbox restrictions.

## Documentation maintenance

Every substantive change updates `docs/handoff/01-PROJECT-STATE.md` and `08-CHANGE-AND-DECISIONS.md` and their English counterparts. Preserve evidence, unverified scope and next steps so a new agent need not rely on this chat. Chinese is the default; current English documents must match Chinese detail rather than provide shortened summaries. Retain original historical evidence and third-party license text without retroactively changing their meaning.

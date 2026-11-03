# Documentation index

[简体中文（默认）](README.md) · English

Updated 2026-11-03 (Australia/Sydney). Chinese is the default. English documents below provide full corresponding explanations of the same features, procedures, technical values, historical stages and acceptance boundaries, rather than shortened summaries. Languages use separate files, with switches at the top.

## Current documentation

| Content | Chinese (default) | English |
|---|---|---|
| Project overview / quick entry | [README](../README.md) | [README](../README.en.md) |
| Controller guide | [Guide](../controller/README.md) | [Controller guide](../controller/README.en.md) |
| Agent boundaries | [AGENTS](../AGENTS.md) | [AGENTS](../AGENTS.en.md) |
| Handoff entry | [00](handoff/00-START-HERE.md) | [00](handoff/00-START-HERE.en.md) |
| State / acceptance boundaries | [01](handoff/01-PROJECT-STATE.md) | [01](handoff/01-PROJECT-STATE.en.md) |
| Architecture / source navigation | [02](handoff/02-ARCHITECTURE.md) | [02](handoff/02-ARCHITECTURE.en.md) |
| Interaction contract | [03](handoff/03-UX-CONTRACT.md) | [03](handoff/03-UX-CONTRACT.en.md) |
| Hardware / safe update | [04](handoff/04-HARDWARE-AND-FLASH.md) | [04](handoff/04-HARDWARE-AND-FLASH.en.md) |
| Token / pricing model | [05](handoff/05-TOKEN-AND-PRICING.md) | [05](handoff/05-TOKEN-AND-PRICING.en.md) |
| Operation / diagnosis | [06](handoff/06-RUNBOOK.md) | [06](handoff/06-RUNBOOK.en.md) |
| Migration / archives / privacy | [07](handoff/07-MIGRATION-AND-PRIVACY.md) | [07](handoff/07-MIGRATION-AND-PRIVACY.en.md) |
| Version evolution / decisions | [08](handoff/08-CHANGE-AND-DECISIONS.md) | [08](handoff/08-CHANGE-AND-DECISIONS.en.md) |
| Backlog / unaccepted scope | [09](handoff/09-BACKLOG.md) | [09](handoff/09-BACKLOG.en.md) |
| FAQ | [10](handoff/10-QUICK-FAQ.md) | [10](handoff/10-QUICK-FAQ.en.md) |
| Installed device language | [13](handoff/13-DEVICE-LANGUAGES.md) | [13](handoff/13-DEVICE-LANGUAGES.en.md) |
| v0.2.14 Chinese / English device variants | [Version record](releases/v0.2.14.md) | [Version record](releases/v0.2.14.en.md) |
| Host languages / separate entries | [12](handoff/12-HOST-LANGUAGES.md) | [12](handoff/12-HOST-LANGUAGES.en.md) |
| macOS / Windows | [11](handoff/11-HOST-PLATFORMS.md) | [11](handoff/11-HOST-PLATFORMS.en.md) |
| Third-party API compatibility | [Roadmap](API_COMPATIBILITY.md) | [Compatibility](API_COMPATIBILITY.en.md) |
| v0.2.12 release / five hardware cases | [Release](releases/v0.2.12.md) | [Release record](releases/v0.2.12.en.md) |
| v0.2.13 implementation / deployment boundaries | [Version](releases/v0.2.13.md) | [Version record](releases/v0.2.13.en.md) |
| 2026-11-02 code / documentation review | [Report](reviews/2026-11-02-code-and-docs.md) | [Review report](reviews/2026-11-02-code-and-docs.en.md) |
| Mac Demo | [Chinese](../mac-demo/README.md) | [English](../mac-demo/README.en.md) |
| Offline dependencies / digests | [Chinese](../controller/vendor/README.md) | [English](../controller/vendor/README.en.md) |

See [third-party notices](../THIRD_PARTY_NOTICES.md) for full Chinese / English notices on one page. Upstream license originals remain unchanged; translations do not replace legal text.

## Historical material

[Old STATUS](STATUS.md), [old CHANGELOG](CHANGELOG.md), stage reports in `controller/docs/` and the [original Controller README snapshot](history/controller-readme-before-2026-11-02-review.md) retain their original wording and existing bilingual content for evidence. They are not current operating manuals; their “current” / “awaiting update” states do not describe today. Full current Chinese / English state and evolution are in 01, 08 and version records. Original snapshots / third-party licenses are not retroactively rewritten for language organization.

## Maintenance and phases

- Update current English with Chinese, preserving equal detail. Commands, paths, versions, money, thresholds, digests, test counts and accepted / pending conclusions must agree. Existing interface wording may remain quoted to identify real device prompts; never translate filenames or commands speculatively.
- Phase-one Markdown is separately committed / pushed. Phase two now implements separate Chinese / English `.command` / `.cmd` consoles and host subtools, with its own commit / push. Phase three now adds installation-selected 0.2.14 device languages and guards in a separate commit / push, without flashing for the user. Describing future plans does not mean those features are delivered.
- Record source, image, loaded runtime and hardware acceptance separately. This documentation phase does not rerun services or touch devices and does not claim old tests as fresh execution.
- Never put private configuration, bills, pairing, backups, Apple artwork or artwork-containing firmware in public docs / Git.

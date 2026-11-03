# Backlog and unverified items

[简体中文（默认）](09-BACKLOG.md) · English

Updated 2026-11-03 (Australia/Sydney). Windows 10/11 adaptation is authorized with macOS retained. The user has now split bilingual work into three separately committed / pushed phases: Markdown first; `.command` / `.cmd` and console second; firmware / other parts third. This phase changes only Markdown. Other features and device operations still require an explicit task.

## Platform follow-up

- Windows 11 has a host layer, isolated environment, version / digest protection and synthetic transport regressions. Verify original-App / device Allow / Deny, GUI, sleep reconnect and firewall reachability next.
- Execute on Windows 10 and repeat this round on macOS. Added cross-platform CI has no recorded successful run and cannot replace target-host acceptance.
- Windows ESP-IDF / WSL build and safe backup / live-partition / application update are implemented; private assets were restored and the user confirmed the update and a basic visual check. Complete upgrade fault coverage, Windows 10 and long-term stability remain unverified. Preserve the macOS safe path; Windows does not invoke Mac update scripts.

## Confirmed and repaired

- Preserve v0.2.12's five hardware cases: device Allow / Deny, original-App Allow / Deny and historical handoff then Allow. The separate device-Allow submitted receipt was captured and is no longer missing.
- v0.2.13 source removes handoff; later logs report that device version. Track complete acceptance and loaded host patches separately; neither “never deployed” nor “fully accepted” is an accurate blanket statement.
- Repairs / regressions cover mixed-tier / multiplier aggregation, non-object ledgers, usage deletion / truncation / rotation, failed App probes, Hook project paths / failures, long-tier rereading and price-source switching state.
- Migration excludes login credentials. Private archives restrict permissions before writing and reject existing files / symlink roots. Publication audit inspects actual Git index contents. See the [review report](../reviews/2026-11-02-code-and-docs.en.md).

## Hardware and runtime verification

- Complete v0.2.13 device / original-App Allow / Deny, opposite-side clearing, details hold / release without handoff, and second-confirmation hold-to-submit in the original chat.
- Confirm Chinese tool receipts and launch-chain patches in actual running processes; do not reflash for Bridge-only fixes.
- Cover additional permission types, file diffs, extra authorization semantics, all relevant Hooks, user-reply notices, sleep / wake and long-term stability.
- Check real-screen numeric / monetary categories, Chinese glyphs, column widths, large values and unknown states; measure audio, battery and power. Host checks cannot replace this evidence.
- Manually accept GUI price-source switching, existing `custom_prices` editing, long-tier and multiplier persistence end to end. Headless regression covers the confirmed state bugs, not complete manual interaction.

## Data and engineering

- Provider CSV adapters currently fill absent reasoning with 0. Add source-completeness metadata so this is not mistaken for actual absence of reasoning.
- Cache-write TTL and tier detail coverage remain limited; built-in prices are snapshots. Verify sources / rate agreements before updating, without overwriting custom prices.
- The 4096-byte snapshot limit may constrain large metering details. Preserve authorization content and evaluate a compact paginated protocol later.
- Measure ledger size, per-request estimation scan costs, relay session-set growth and background file lifecycle before choosing caches / module separation.
- Firmware network initialization cleanup and task-creation failure paths need SDK builds and fault injection. The review did not change drivers for speculative optimization.
- `service.py` combines state, approvals, metering and lifecycle. Split gradually under behavioral tests if needed; the review only extracted shared App probing / usage-integrity checks rather than rewriting it.

## Archives and publication

- Same-disk file-by-file snapshots are not off-site or stopped transactional backups. Recheck recovery before cleaning old outputs, venvs, IDF or caches.
- After review the user explicitly authorized commit / GitHub synchronization; see state / change records. Historical release records do not authorize future automatic deployment or publication.
- Keep private data, credentials, Apple images and firmware containing artwork out of the public repository.

## Outside current scope

New Pocket OS, active NFC, SIM / cellular, automatic approval, unconfirmed consumption of resets, old-backup deletion, bypassing unknown App version protection and cloud storage of Codex credentials.

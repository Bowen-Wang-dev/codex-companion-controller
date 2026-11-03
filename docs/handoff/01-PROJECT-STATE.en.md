# Project state and acceptance boundaries

[简体中文（默认）](01-PROJECT-STATE.md) · English

Updated 2026-11-03 (Australia/Sydney). Source, recent runtime evidence and hardware acceptance are separate. Later sections preserve facts from their respective stages.

## Current work: phase-two English host interaction

- Phase-one Markdown was independently committed / pushed as `48603c8`. The user now authorizes English host interaction: add `Codex Companion Console.command` / `Codex Companion Console.cmd`, retain Chinese entries, one entry per platform and language without other top-level launchers.
- Shared `COMPANION_LANGUAGE` and 341 English messages cover console, diagnosis / recovery, pairing, metering / rate editor, Hooks, maintenance and host Bridge logs. Chinese is default; entries pin language and pass it to children. Windows CMD uses CRLF / UTF-8, shell uses LF; macOS private configuration cannot override entry language.
- The English rate editor gains vertical scrolling and screen-height adaptation; rate / model override and audit CSV reads specify UTF-8. Model names, paths, protocol IDs, `YES` / `RESET` / `FLASH` and user data are not translated. Device snapshots / requests / receipts remain Chinese, without firmware or original-App package changes.
- Final Windows Controller regression: 295 tests, OK (18 skipped), including 13 host-language cases with real CMD / hidden Tk and temporary settings. Five isolated WSL shell cases passed, along with actual English CMD `--check-only`, Python 3.11 syntax for 48 files, all shell / command syntax and local links across 60 Markdown files. Native macOS execution, real App / device workflows and complete manual GUI acceptance remain uncovered.
- See [host languages](12-HOST-LANGUAGES.en.md) for checks and unverified scope. No real App / Bridge launch, flash, pairing, reset, Hook registration or account change; existing App digest, single-instance, dual-backup and live-partition protections remain. This adds no real App / device functional acceptance; phase-three firmware English is not implemented.

## Completed phase one: staged bilingual documentation

- The user requires three separate commit / push phases: Markdown bilingual documentation; Chinese / English `.command` / `.cmd` console entries; firmware and other parts. This phase changes only Markdown, with Chinese default and full-detail English counterparts. It does not deploy code, change console language or flash firmware.
- Console localization started before this clarification was saved locally in ignored `controller/private/stage2-console.patch` and companion files, then removed from the worktree. It is not part of the documentation index / commit and is not validated as phase-two completion.
- Current operational guides correct outdated “Windows firmware maintenance unavailable” and “assets missing” claims. Historical stage evidence remains scoped to its own date. Local links, paired-document structure, technical literals and the staged file list are checked before commit; no historical software tests are claimed as rerun here. Final documentation checks covered 22 full Chinese / English pairs and local links across 58 Markdown files, with no broken links. Matching image digests, executable code blocks and section structure passed (architecture / directory comments are translated); `git diff --check` passed.

## Current work: 2026-11-03 Windows added, macOS retained

- Latest user hardware feedback: Windows flashing completed and a basic visual check found no obvious problems. The repaired block-backup update was actually completed by the user; do not request another flash. This does not establish complete permission-matrix, long-term stability or Windows 10 acceptance. “Retry pending / not flashed” below are earlier-stage records.
- First Windows safe update: user logs show a short esptool `Corrupt data` frame at 36% of the first read-only 8 MB backup, before backup 2, application write or readback. It was not successful updating. Windows reads were changed to 256 KiB blocks at 115200 with per-frame progress disabled, at most three read-only attempts and final ROM fallback. Between blocks the application is not started, avoiding NVS changes. Failed blocks are not concatenated; two complete matching backup digests remain mandatory. Writes are not automatically retried; failed backup directories remain.
- That repair ran 280 Controller tests, OK (16 skipped), adding six read-recovery cases. After adding inter-block `no_reset` assertions, the six local cases passed again. At that stage the repaired real-device dual-backup / flash path had not yet been accepted and the user could retry menu 7 → 3 without rebuilding. The later user confirmation above supersedes that pending retry.
- Subsequent asset note: a private package from Mac was received. Package SHA-256 `22e383c9a3efa2087d5558f7b939f81fb5d27a41b60d64d656f604370f76781d` and paths / sizes / digests of 27 members were verified. `pet_assets.h`, eight PNGs and `rights.json` were restored. Original package / reference settings stay ignored in `controller/private/imports/2026-11-03-windows-private-assets/`; Windows settings were not overwritten. Earlier missing-assets statements were resolved.
- The same Windows console build function used existing WSL ESP-IDF 5.5.3 to generate artwork-containing 0.2.13: 2,363,280 bytes, SHA-256 `faa362cd75794d48bd9d8d71a224c9c9e6c6c2c8760304c772a4af724ef1b19a`. Source binding passed; seven original RGB565 arrays were present, new host reply / details / pairing prompts existed and their old counterparts were absent. Windows esptool 4.8.1 checksum and Validation Hash passed.
- Nine firmware-maintenance regressions passed after restoration. That build / inspection did not open serial, stop Bridge or write the device. At that stage real-screen layout, Windows dual backup / write / readback and functionality remained unverified. Existing CMD menu 7 → 3 required one USB target and `FLASH`; 7 → 2 validated first. Assets / artwork-containing firmware stay local. The later user-confirmed update is separate evidence.
- Earlier repair connected Windows menu 7 to `firmware_update.py` with build, image validation, safe USB upgrade and isolated esptool 4.8.1 setup. It no longer only reports unavailable. Images must match current source digest, version, chip and file digest and contain original private emoji; old images are rejected. The macOS manifest generator also records source digest.
- Blocker at that earlier point: missing `firmware/main/pet_assets.h`; existing dist was an old image without emoji or source binding. Restore from the original Mac private backup, build 7 → 1, validate 7 → 2, then 7 → 3 and `FLASH`. No new image or write was performed in that repair; it was not hardware flash acceptance. Existing Ubuntu 22.04 / ESP-IDF 5.5.3 was found; Windows handles COM, WSL only builds. Subsequent restoration resolved the blocker.
- Maintenance repair: 274 Controller tests, OK (16 skipped). Coverage includes damaged images, source / configuration / asset changes, old manifests, missing assets, cancellation and lock release after flash exceptions; partition / backup tests remain. Backup folders gained Windows private ACLs; isolated flash environment is excluded from archives.
- Isolated Windows esptool 4.8.1 was prepared; existing-image `image_info` checksum / Validation Hash parsed successfully. Tools: 19 tests OK (4 skipped). This did not open serial or verify a real write.
- On 2026-11-03 the user reported notifications basically usable and requested platform-neutral wording. Firmware, Bridge, console and maintenance prompts adopted “host / desktop App” while preserving platform paths, MAC-address fields and historical acceptance. At that point source had not been built / flashed and Bridge was not restarted. Regression exposed Windows default-encoding failure in approval-glyph reading; explicit UTF-8 fixed it.
- That wording round ran 265 Controller tests, OK (16 skipped); the glyph list included the required character. New real-screen layout was not verified in that round.
- Windows 10/11 adaptation was explicitly authorized alongside macOS on Windows 11 Pro. Other backlog was not resumed and that initial host work did not change firmware / device.
- One daily entry per platform was retained: original macOS `.command`, new same-name Windows `.cmd`. Console, approvals / receipts and metering are shared; host_platform, IPC and permission modules isolate platform differences. Independent language entries are newly authorized phase two.
- Windows adds isolated venv, digest-checked offline dependencies, native relay.exe, authenticated random loopback endpoint, current-user DACL, single-instance lock, COM / IPv4 discovery, OpenSSL lookup, Hook commands and archive / migration permissions. macOS Unix sockets / locks, registered App digests, firmware maintenance and Swift Demo remain.
- Installed MSIX `26.1027.3384.0`, App `26.1027.30824`: four launch-file digests passed. COM4 was only enumerated read-only; initial host work did not open serial or read device version.
- See [platform evidence](11-HOST-PLATFORMS.en.md). Windows 10, current-round macOS execution, real Windows App / device matrix, GUI and sleep reconnect remain unverified. Added CI was not run and is not successful evidence.
- Initial host work did not close / restart App, start real Bridge, flash, pair, reset, change accounts, register real Hooks, commit or push. At that initial stage complete Windows firmware maintenance was unavailable; later maintenance and user-confirmed updating above supersede that limitation.

The next summary and sections belong to the retained 2026-11-02 stages. Their authorization and counts do not cover later Windows work.

## Summary after code and documentation review

| Item | Confirmed scope |
|---|---|
| Work | Comprehensive review, necessary refactoring / bug fixes authorized; no unrelated development / deployment |
| Source | Firmware `0.2.13`, Bridge `0.2.13-native-app`; details handoff removed, direct dual-side approvals retained |
| Release baseline | Local Git `v0.2.12`; five hardware cases and separate submitted receipt preserved |
| Later device evidence | Runtime logs report `0.2.13`; early not-deployed claims apply only to their stage; no fresh device / process query during review |
| New-version coverage | One normal approval does not establish complete matrix, permission types or stability |
| Patches awaiting verification | Chinese receipts, launcher and host patches cannot be assumed loaded from source revisions |
| Changes | Credential exclusions, archive / index audit, cost metadata, ledger / usage lifecycle, launcher, Hook paths and maintenance checks |
| Actual validation | Controller Python 256, tools 19, Swift core 30, C navigation / tones and 8 mock audio groups; complete Swift Demo build; [review report](../reviews/2026-11-02-code-and-docs.en.md) |

Review did not restart App / Bridge, flash, pair, reset, change accounts, read / print login credentials, commit, push or tag. Subsequent source synchronization was separately authorized below.

## 2026-11-02 review commit and GitHub synchronization

- The user explicitly authorized GitHub submission of repaired code, tests, documentation and report, excluding private logs, credentials, bills, Apple assets and artwork-containing firmware.
- Reused actual 256 Controller / 19 tools / 30 Swift / C / audio / full Demo results. Synchronization reviewed diffs, remote relationship and final Git index rather than claiming fresh test execution.
- Ordinary commit / fast-forward push, no forced push or new release tag. Source synchronization does not prove running Bridge patches or deployed firmware; retain hardware boundaries.
- Completion requires remote GitHub `main` equal to local `HEAD`; a local commit is not upload evidence.

## Historical stage records

Each section records implementation / runtime / acceptance at that stage. Early “still 0.2.12”, “awaiting deployment” and “receipt unaccepted” statements were later partly superseded and cannot be read as unqualified present facts.

## 2026-11-02 ordinary Bridge tool receipts in Chinese (source complete, awaiting load)

- A real read-only approval test printed `COMPANION_V0213_APPROVAL_TEST` and interaction was reported normal; the device then displayed an English tool receipt. No independent new version snapshot / full matrix was collected, so one Allow is not complete new-version acceptance.
- `service.py` ordinary `PostToolUse` wrote `Tool returned on Mac`. Git history traces it to `efb760c` on 2026-10-25; it existed in v0.2.12 and was not introduced by v0.2.13 handoff removal. Tool return follows submitted approval and may overwrite Chinese during its three-second feedback. Existing evidence does not establish why it had not previously been noticed.
- Changed only the receipt to Chinese “tool returned”, preserving order, emoji duration and success / failure interpretation. Ordinary tool return means neither permission success nor task success. Existing special-permission results / matching-command branches remain unchanged.
- DesktopBrokerTests: 11 passed, including two new cases for ordinary returns not fabricating approval and Chinese receipts during real submission feedback without extending its duration. No full-suite rerun or firmware rebuild; the earlier 237 count belongs to the prior stage.
- Bridge text / tests only; no firmware change, flash or restart. Load through existing console 2 → 2 safe Bridge restart, retain App / chat / pairing, then visually verify the receipt.

## 2026-11-02 desktop integration fix: complete launch chain in 2 → 2

- Logs showed device firmware 0.2.13 and HTTPS but Bridge waiting for actual App-session integration, followed only by `UserPromptSubmit` / `SessionEnd`, without stable desktop relay heartbeat, model events or usage events. Wireless sync proves HTTPS, not original-App approval integration.
- Root cause: 2 → 2 ran `bridge/service.py --desktop` alone rather than the verified `launch_desktop.py` App / relay / Bridge chain. With the App closed this looked device-online / Bridge-online while approvals, tokens and model stayed disconnected.
- Fix: probe App first. If closed, safely stop old Bridge if present and call the full launcher; if already running, retain Bridge-only restart. Unknown versions / digests remain rejected and active work is not closed.
- Three new lifecycle cases cover running / closed / probe failure; 16 connection-recovery / activation cases and 11 DesktopBrokerTests passed. The current Mac App session was not restarted and no new real approval was executed; device logs alone do not prove relay integration.
- Require App physical approvals connected before validating model, tokens and Allow / Deny. No repeat flash; this is a host / relay lifecycle issue.

## Historical 2026-11-02 v0.2.13 source / build, before deployment

- Version plan was saved in `9545223` before implementation. Scope was only v0.2.13; other backlog remained paused.
- Firmware removed `ACTION_MAC`, handoff state / page, `mac_handoff` send and `mac_ready` parsing. Details stated that information can be viewed on the computer. Details hold-confirm does nothing and release does not become a short press. Second-confirmation hold-to-submit and ordinary-page hold-confirm return to pending requests remain.
- Bridge removed handoff handling, Hook handoff release, focus injection, `native_app_ui.py` and display-receipt fields. Old-device handoff messages are unknown / ignored: no submission, cancellation or App launch. Original-App approvals, version / digest protection and genuine submission receipts remain.
- Firmware source `0.2.13`, Bridge `0.2.13-native-app`; launcher, maintenance and manifest checks aligned. Runtime was then the accepted 0.2.12, without App / Bridge restart or flash; source / build completion was not live functionality.
- Full Controller Python: 237 passed. Three retired recall tests were removed from the 240 baseline; former handoff cases became old-message-no-side-effect tests. Existing stdio / Unix integration covered device / App Allow / Deny, cancellation and submitted receipts. C navigation / confirmation / tones and 8 mocked BSP / RTOS audio groups passed; 15 request / choice combinations checked harmless hold / release. Glyphs already covered new text; shell, versions, manifests, digests and old Git code checks passed.
- First full regression had 18 socket-sandbox errors; authorized rerun passed. Registry access warning during build was handled with existing locked components under ESP-IDF 5.5.3, without dependency upgrades.
- Local artwork image `controller/dist/PassportController.bin`: 2,359,568 bytes, SHA-256 `94b52c72ff45a984eccb86aab92b516b47dbf3aa02e0267aabc556e01d5c0e21`. Kept local; build is neither flash nor hardware functionality acceptance.
- Version wording was checked for historical scope rather than chat narration. Source / build / image digests matched; historical v0.2.12 implementation and case 5 stayed preserved.
- Next at that stage: existing menu 7 dual backups / live partitions / application-only update, then real original-chat dual Allow / Deny and details hold behavior, including second-confirmation hold-submit. No reset / pairing / account changes. See [v0.2.13](../releases/v0.2.13.en.md).

## Historical 2026-11-02 handoff retirement, documentation only

- The user found simultaneous device / original-App approvals convenient and adopted either device buttons or desktop mouse after the alert, without transfer.
- Details hold-confirm “to Mac” became a retired historical feature. Preserve its existence / acceptance, with old source at Git `v0.2.12` (`fb02632`); remove executable handoff / recall / display receipts from the next version. Resource benefits were not measured and no performance claim was made.
- At that planning stage only version plan, UX and entry docs changed. Source, Bridge and device were still 0.2.12, with old protocol / activation code present. No build, flash, restart, pairing, reset or release.
- Five hardware cases remained history; case 5 was no longer a current requirement. The later device would only state that details are available on the computer, while pagination / confirmation / submission receipts remained.
- Markdown was committed before implementation. No code / deployment / tags in that planning phase; see [v0.2.13](../releases/v0.2.13.en.md). Other backlog stayed paused.

## 2026-11-02 v0.2.12: five native dual-side cases passed, release authorized

- After the user's Bridge switch, real IPC confirmed device 0.2.12 online, `approval_ui=native_app`, `desktop.connected=true`; this was not only source / build evidence.
- User individually confirmed device Allow, device Deny, original Mac native-card Allow, original Mac native-card Deny and details handoff recalling original App then Mac Allow. Either side cleared the other; handoff did not auto-approve; user confirmed emoji.
- Device Allow executed a real command, `source=desktop`, `choice=allow`, with a separate matching submitted-stage delivery receipt. Both denials returned rejected by user without executing. Both Mac allows printed success markers. Do not fabricate separate receipts for all five.
- Evidence remains ignored in `private/hardware-acceptance-native-20261102.json` with 0600 permissions; public docs contain only a de-identified matrix, no device / session identities.
- The user authorized Markdown first, then v0.2.12 source publication, excluding private data, Apple assets and artwork firmware. Release completion depends on remote `origin/main` and tag verification.
- README, Controller README, release / runbook / handoff were updated. Earlier pending / standalone-window sections remain historical.
- Other permission types, all projects, file diffs / extra scope, sleep and stability were not covered. 0.2.12 conservatively waited for a window receipt; native forwarding is not proof of drawing, although the user visually confirmed recall.

## Historical 2026-11-02 native App routing, then awaiting switch

- The user explicitly rejected a separate Tk / Companion approval window and required the existing original ChatGPT / Codex App chat. Native routing replaced the standalone design without CLI / new chat or package modification.
- After the user's update, read-only IPC showed firmware 0.2.12 online, desktop connected and approval receipts supported. One read-only query used the old standalone Hook Allow; this was not native dual-side acceptance. The following Deny test was aborted and its file absent, so Deny did not pass then.
- `bridge/mac_approval_gui.py` became a no-window compatibility no-op because an old running Broker might still call it. New service neither imports nor starts it; private mac_review / mac_decision interfaces and standalone UI state were removed.
- Desktop-mode `PermissionRequest` / permission `PreToolUse` returns empty Hook results rather than blocking or approving / denying, letting the original App show native approval. Stdio relay mirrors the real request to the device; first response wins. Old Hook caches must not bypass this.
- `mac_handoff` only activated an already running exact-version / digest-verified App; no clicks / new chats. Old non-desktop blocking Hooks released waiting to permit native UI. Firmware 0.2.12 stayed compatible without reflash, with conservative request / waiting-for-display prompts rather than invented render receipts.
- Installed 26.1027.30824 digests passed; only JSON schema was generated from the official local binary, retaining `startedAtMs` and related validation. Official protocol documents supported design, not hardware success.
- Full Controller: 240 passed, removing 13 rejected-UI cases and adding eight native routing / cache / activation / no-op cases. Two former Mac-private-interface integrations became original-App protocol Allow / Deny, clearing device state even before final-page review. After activation timeout hardening, eight related cases passed again.
- New Bridge source was not loaded / retested on hardware then. User could choose 2 → 2 only with no pending approvals, preserving App / chat / pairing / 0.2.12. Native cases remained pending; never substitute standalone popups for missing callbacks.

## Historical 2026-11-02 standalone design and first update failure (superseded)

- User's 01:49–01:50 log passed 242 tests, then menu 7 failed during serial discovery with `python: command not found`. Bridge stop, backup and writing had not occurred, so 0.2.12 deployment was unconfirmed.
- Maintenance used implicit IDF bare Python. Serial discovery / preflight moved to `CONTROLLER_BRIDGE_PYTHON`, flashing to `CONTROLLER_FLASH_PYTHON` with executable / esptool 4.x checked before stopping Bridge. `env.sh` gained an explicitly configured IDF fallback. Ignored local-env selected existing IDF Python 3.9.6 / esptool 4.12.0, without installation or replacing Bridge Python.
- Three isolated shell cases covered minimal PATH dispatch and early exit for missing interpreter / esptool; four dependency / launcher cases passed. Actual minimal-PATH esptool import and USB enumeration passed without opening serial. No full 242 rerun or flash; user could retry existing menu 7 with USB.
- Before that, menu 7's old 0.2.11 assertion was updated to 0.2.12 after the user requested an update command. Shell / image / manifest / size / digest consistency passed. The chain stops Bridge, makes dual backups, checks live partitions, writes only the App and restores Bridge to the original chat. Relay did not change, so keeping the App open was valid; earlier manual-quit steps described another path. No device operation in that launcher edit.
- Original user task: device offered “to Mac” without desktop UI, and approvals should work on either side. Root cause: firmware `ACTION_MAC` only muted sound and sent no handoff, while blocking PermissionRequest prevented original native approval from appearing.
- A real Companion Tk approval window was added using existing Broker / private Unix IPC, automatically appearing for pending approvals. Only request ID was passed on launch; complete request details were chunk-read, not written to files / argv / models. Second confirmation submitted the same pending request; first answer won across Mac / device / native relay. Mac review did not bypass device pagination; unsupported native approval semantics stayed with original App.
- Firmware 0.2.12 added bound boot / epoch / ID / digest handoff and real window recall. Only complete visible-window short-lived heartbeats produced displayed receipts; hiding / new handoff / expiry revoked them. No visibility / read / submission state pretended execution success.
- Full Controller 242, then 13 related receipt-hardening cases passed. C navigation / tones and 8 mock audio groups passed. Synthetic Tk content, buttons, hide / recall and confirmation / submit checks passed. Screenshot tool timed out, so no screenshot visual QA / hardware acceptance was claimed. Socket / registry failures were retried after approval.
- ESP-IDF 5.5.3 build only: artwork 0.2.12, 2,360,544 bytes, SHA-256 `dae8c7c2dacea383f0c3deb3cbc9ac3a0d78faa653151faf2b73e1338053de04`. Glyph coverage passed. No flash, restart, pairing / account / ledger changes, commit or push in that design stage.
- At that stage the next step was manual save / quit / console activation, protected update and real original-chat dual-side cases. These synthetic / build results never established hardware success; later rejection of the standalone design superseded it.

## 2026-11-02 new-directory Bridge activated

- The user completed manual App exit / Terminal confirmation. `private/runtime-activation.json` records activation at 01:07:29 +1100: latest ledger synced, Hooks migrated and pending marker removed.
- Read-only process / IPC checks found Bridge, stdio relay and `launch_desktop` at `/Users/bowen/Developer/codex-companion-controller/controller`; old outputs Bridge was not running.
- New Bridge: Wi-Fi online, firmware 0.2.11, desktop connected, approval receipts supported, session_count=2. Seven user Passport Hook types pointed at the new project; pairing IP still matched. This was a snapshot, not stability proof.
- Installed App 26.1027.30824 digests passed again. Pairing / certificate / rates retained; old project preserved. Ledger / Hook backups stay in `private/activation-backup-*`.
- Earlier execution passed six synthetic activation, eight recovery and fourteen notification / Hook cases (28 total). This read-only verification did not repeat them.
- Real hardware acceptance: original-chat PermissionRequest created an independent file after physical Allow; physical Deny returned `PermissionRequest hook denied approval` and did not create its target. User confirmed both were button actions, Allow 😆 and Deny directly 😭 without 😶. Files were cleaned; private acceptance JSON retains evidence. This was real, not mock.
- Pending then: native relay independent `approval/submitted` receipt because `source=hook` and `last_device_delivery=null`; sleep / wake, all permissions and stability. Hook path trust was demonstrated for that PermissionRequest, not all Hooks.
- Independent Homebrew Python 3.12.15, OpenSSL 3.5.9 and Tcl / Tk 9.1 were prepared at `private/bridge-venv-homebrew`. pySerial 3.5 / websockets 17.3 came from digest-checked vendor wheels; pip check passed. Shell entries / local-env selected `CONTROLLER_BRIDGE_PYTHON`, removing future dependence on Codex cache.
- The independent Python was later activated after user quit / reopened App and confirmed device reconnect. `active-python.json` at `2026-11-02T01:27:58+11:00` records Homebrew base / interpreter and the versions above. Earlier prepared records are historical, not current activation. Old venv remains for rollback.
- Daily entry remained the original `.command`. Migration did not resume paused features or authorize flashing.

## Historical archive-stage versions and evidence

| Item | Stage-specific evidence |
|---|---|
| GitHub baseline | `00b61330f1b415b555d8acde8ddd4a6d055c48d0`, main; shared console and token categories |
| Firmware at that stage | 0.2.12, real hello; artwork image 2,360,544 bytes, SHA-256 `dae8c7c2dacea383f0c3deb3cbc9ac3a0d78faa653151faf2b73e1338053de04` |
| Actual flashing | Old runtime `private/backups` 2026-11-01 `last-result.json` verified=true; last-write digest matched; factory only, no partition table / bootloader / whole erase |
| Bridge | This project's Python source; some diagnostics still displayed 0.2.10, insufficient alone to identify behavior |
| Mac Demo | SwiftUI / AppKit 0.4.0; simulated tasks / quota, not real approvals |
| Desktop integration | Registered 26.1016.62342 / 26.1027.30824 and launch-chunk digests; unknown upgrades rejected |
| Earlier host results | 217 Python checks in local / shareable trees, C controller / tones / 8 audio groups and ESP-IDF 5.5.3 build; not rerun in this stage |
| Migration | Developer copy / activation verified; 340-file root local migration receipt and private runtime activation receipt |

## Historical real-device acceptance

- Original App directory-write Allow / Deny passed on the previously verified build; native network Allow passed with a matching real authorization receipt.
- User confirmed last-page review before choice, Chinese glyphs without boxes and 😆 after approval.
- On 2026-10-31, USB pairing after a network change restored Wi-Fi after unplugging; short samples had no disconnect / HTTP error.
- 0.2.11 write / readback evidence proves image integrity, not acceptance of every new page.

## Acceptance still not covered

- Complete v0.2.13 dual-side / no-details-handoff matrix, every permission / project and long runs; do not inherit v0.2.12's five cases automatically.
- Real-screen 0.2.11 category numbers / money, precision, unknown states and Chinese coverage.
- Complete real console GUI menu combinations; unit tests do not cover them all.
- Live provider account ledger; local estimates plus optional CSV / TSV audit are not that API.
- Public distribution rights for Apple images / artwork firmware.
- Sleep / wake lifecycle and all permission workflows. The v0.2.12 native submitted receipt and independent-Python App / device reconnect are recorded, but do not accept every later case.

## Implementation limits requiring review

- Only explicitly checked `gpt-6.1-sol` is built into the OpenAI preset. Future model / price changes require fresh sources; respect custom prices.
- Older private billing lacks reasoning breakdown; adapter 0 means an incomplete category, not proof of no reasoning.
- Only one cache-write rate exists; TTL-dependent billing needs future real detail, not invented values.
- The console previously claimed bill import while menu currently offers only last-hour auditing; CSV / TSV paths require `audit_usage.py --provider-log`.

## 2026-11-02 local archives and dependencies

- User confirmed Hooks and authorized local archival / Python cleanup, not push at that stage; source was committed locally.
- New Python: 227 Controller, 10 migration / archive tools, C controller / tones and 8 mocked audio groups passed; local socket permissions needed approval. Tk / Tcl import / initialization and pip check passed without GUI / hardware acceptance.
- Fixed `destination.absolute` versus `source.resolve` mismatch allowing macOS `/var` → `/private/var` aliases to bypass child-directory checks. Existing regression passed after consistent resolution.
- Archive target `/Users/bowen/Developer/codex-companion-archives/2026-11-02-python-handoff`: source tar.gz, Git bundle, separate `PRIVATE-RECOVERY.tar.gz`, recovery instructions and digest receipts. Success requires `ARCHIVE-RECEIPT.json` and verifiable hashes; private members were read back, excluding auth.json, venvs, caches and logs.
- The private archive is a live per-file snapshot with parsed JSON, not a global stopped transaction. Same-disk copies are not off-site backups. Never publish private assets, artwork firmware or keys.

## 2026-11-02 final activation / archive addendum

- Full user `--restart-app` log and reconnection confirmed the independent-Python activation receipt. Intermediate “Bridge not running / FileNotFoundError” occurred between old shutdown and new startup, not a persistent outage.
- First archive actually exists for `e4fb7c5`, with 149 private members readback-verified and outer SHA-256 checked again.
- Final sibling `/Users/bowen/Developer/codex-companion-archives/2026-11-02-final` includes activation receipts and updated source / handoff; its archive receipt identifies commit / digests. Preserve the first archive.
- Only verification / recording / archival, not a rerun of 227 + 10 tests or expanded hardware acceptance.

## 2026-11-02 GitHub authorization

- After archival the user authorized uploading updates to GitHub, superseding the earlier local-only boundary for audited source / handoff. Private archives, pairing, credentials, Apple artwork and artwork firmware remain excluded.
- Fetch succeeded; origin/main was a local ancestor with two verified local updates ahead. Audit of 207 indexed files for sensitive paths / credential patterns passed, worktree clean. Ordinary fast-forward push, no force; success requires remote main equal to HEAD.

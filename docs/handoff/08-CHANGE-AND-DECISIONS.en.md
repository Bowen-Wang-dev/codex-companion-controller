# Version evolution and change records

[简体中文（默认）](08-CHANGE-AND-DECISIONS.md) · English

Developer-maintained version plans, implementation changes, verification evidence and history, without chat transcripts or secrets.

## 2026-11-03: phase-two English host interaction

- Phase-one Markdown was independently committed / pushed as `48603c8`. The user now authorizes English host interaction: add `Codex Companion Console.command` / `Codex Companion Console.cmd`, retain Chinese entries, one entry per platform and language without other top-level launchers.
- Shared `COMPANION_LANGUAGE` and 341 English messages cover console, diagnosis / recovery, pairing, metering / rate editor, Hooks, maintenance and host Bridge logs. Chinese is default; entries pin language and pass it to children. Windows CMD uses CRLF / UTF-8, shell uses LF; macOS private configuration cannot override entry language.
- The English rate editor gains vertical scrolling and screen-height adaptation; rate / model override and audit CSV reads specify UTF-8. Model names, paths, protocol IDs, `YES` / `RESET` / `FLASH` and user data are not translated. Device snapshots / requests / receipts remain Chinese, without firmware or original-App package changes.
- Final Windows Controller regression: 295 tests, OK (18 skipped), including 13 host-language cases with real CMD / hidden Tk and temporary settings. Five isolated WSL shell cases passed, along with actual English CMD `--check-only`, Python 3.11 syntax for 48 files, all shell / command syntax and local links across 60 Markdown files. Native macOS execution, real App / device workflows and complete manual GUI acceptance remain uncovered.
- See [host languages](12-HOST-LANGUAGES.en.md) for checks and unverified scope. No real App / Bridge launch, flash, pairing, reset, Hook registration or account change; existing App digest, single-instance, dual-backup and live-partition protections remain. This adds no real App / device functional acceptance; phase-three firmware English is not implemented.

## 2026-11-03: three separately committed bilingual phases

- User clarified order: Markdown bilingual documentation first; `.command` / `.cmd` and independent Chinese / English consoles second; firmware and other work third. Each phase is committed / pushed separately.
- This phase changes only Markdown. Chinese remains default and English has matching detail in separate linked files. Existing console code / entries and device firmware remain unchanged. Initial console edits were saved under ignored private paths for phase two, then removed from the worktree.
- Current documentation corrects outdated Windows maintenance / missing-assets claims without rewriting historical evidence. Validation covers relative links, bilingual structure, technical values and Markdown-only staged content; earlier software / hardware tests are not represented as new execution. Final documentation checks covered 22 full Chinese / English pairs and local links across 58 Markdown files, with no broken links. Matching image digests, executable code blocks and section structure passed (architecture / directory comments are translated); `git diff --check` passed.

## 2026-11-03: user confirmed Windows flashing and authorized synchronization

- User explicitly confirmed flashing finished and the device looked basically fine. Record actual Windows update / basic visual feedback, not complete functionality / stability; do not request another flash.
- User authorized commit / push of block-backup repair, regressions, asset-restoration and artwork-build records. Reuse actual 280 tests (16 skipped) and six final local read tests; do not submit assets, package, private backups or artwork firmware.

## 2026-11-03: Windows full-backup short-frame recovery

- First update log: backup 1 at 36%, `expected 0x1000 ... received 0xf6d`; no write yet. Do not call it firmware corruption or successful update. Windows USB / terminal streaming is implicated, but cable / driver cause is not independently established.
- Based on local esptool 4.8.1, Windows full reads use 256 KiB blocks with per-frame terminal progress disabled and inter-block `no_reset` keeping the application stopped. Only reads retry, at most three times, final attempt in ROM mode. Failed block output is discarded, length checked before joining. Two matching full digests remain mandatory; failure generates no completed manifest and triggers no write. macOS keeps single-read behavior; writes have no automatic retry.
- 280 Controller tests OK (16 skipped), including six new synthetic cases for short frames, discarded fragments, ROM fallback / retry cap, existing backup preservation, failed backup without manifest and macOS behavior. `read_flash --help` confirmed `--no-progress`. No new serial access / flash by the agent; real stability awaited user retry at that stage.

## 2026-11-03: Mac private assets restored and Windows artwork build

- User supplied local private asset package, SHA-256 `22e383c9a3efa2087d5558f7b939f81fb5d27a41b60d64d656f604370f76781d`; 27 ordinary members checked by path, size and SHA-256. Restored only `pet_assets.h`, eight original PNGs and `rights.json`, without executing packaged scripts or replacing reference configuration. Original / references moved into ignored private imports to avoid accidental staging.
- Existing Windows build function used WSL ESP-IDF 5.5.3: artwork 0.2.13, 2,363,280 bytes, SHA-256 `faa362cd75794d48bd9d8d71a224c9c9e6c6c2c8760304c772a4af724ef1b19a`. Source fingerprint, seven original pixel arrays, new host prompts / old counterparts removed checked. esptool 4.8.1 checksum / Validation Hash and nine maintenance regressions passed.
- Restoration, build and read-only inspection only: no serial open, Bridge stop, flash or hardware acceptance, and no Apple asset / image upload. Historical uncertain Mac build provenance remains uncertain; the new build has its own digest.

## 2026-11-03: Windows safe firmware maintenance connected

- User requested fixing Windows console firmware maintenance with its own commit / push; bilingual docs / English console were postponed then.
- Menu 7 invokes Python maintenance, reusing installed ESP-IDF / WSL and native Windows COM with esptool 4.8.1; never generic IDF flash. Only after `FLASH` does it stop this project's idle Bridge, acquire an exclusive IPC lease, perform existing dual 8 MB reads, identity / live partition checks, factory-only write and `verify_flash`. Failure is not success and writes do not automatically retry.
- Image records source fingerprint and checks version, chip, size, SHA-256, artwork flag and application bounds. Missing assets / stale manifest reject before Bridge stop. Backup folders receive private Windows ACLs; flash environment / images remain unpublished.
- At that point `pet_assets.h` was missing and existing image lacked original artwork; never replace device emoji with artwork-free firmware. Original Mac restoration was required before build / real update / layout acceptance. No flashing occurred in that repair stage.
- Controller 274 OK (16 skipped), tools 19 OK (4 skipped), nine new maintenance cases. Isolated Windows esptool 4.8.1 installed and read-only existing-image checksum / Validation Hash passed. No serial open, so not flash acceptance.

## 2026-11-03: platform-neutral host wording

- Notifications were reported basically usable. User requested host wording instead of generic Mac references. Firmware, Bridge, console and maintenance prompts were unified, including permission / reply / pairing / rates / failure / receipts, retaining platform paths, MAC-address fields, mac-demo and historical evidence.
- Approval glyph list now reads explicitly as UTF-8 on Windows. Source change is not runtime activation; that stage did not restart Bridge, build or flash, and added no hardware conclusion.
- 265 Controller tests OK (16 skipped); required glyph present. Real-screen layout awaited later build / deployment.

## 2026-11-03: Windows hosts added, macOS retained

- Windows 10/11 host adaptation authorized, explicitly alongside macOS. Original Mac entries, firmware maintenance and Swift Demo retained; other backlog not resumed.
- Added `.cmd`, Windows isolated setup and native relay.exe. Shared original-chat first-response approvals, submitted receipts, usage and pricing. Windows App version / four digests registered separately rather than reusing Mac hashes; installed App unmodified.
- Windows: loopback-only random port / random authentication, current-user DACL and file locks. macOS: Unix sockets / 0700 / 0600 / flock. Added COM VID/PID filtering, IP / OpenSSL lookup, Hook commands, process probes and argument / exit forwarding; fixed Windows `execv` losing spaced arguments / exit status.
- Archive / migration uses platform permissions and excludes Windows venv / machine relay / auth.json. Transport tests use isolated real platform IPC; macOS-only tests stay and skip by platform. Cross-platform CI added.
- [Platform guide](11-HOST-PLATFORMS.en.md) records actual tests / boundaries. Initial work did not restart App / real Bridge, flash, pair, reset, change accounts, register real Hooks, commit or push. Windows 10, current macOS and real App / device matrix remained pending. Windows firmware maintenance was not yet ported at that initial stage; later sections supersede that limit.

## 2026-11-02: review commit and GitHub synchronization authorized

- User explicitly authorized GitHub submission of review repairs, tests, documentation and report; private data / logs, Apple images and artwork firmware excluded.
- Fetch remote, inspect ancestry / diffs / final index, reuse already executed full regressions and builds. Ordinary commit / fast-forward push, no force or release tag.
- Source sync is distinct from deployment: no App / Bridge restart, flash, pairing, reset or account changes. Completion requires remote main equal to HEAD.

## 2026-11-02: repository review and documentation normalization

- User authorized code review, necessary repairs / refactoring and formal accurate docs, without unrelated feature development / deployment.
- Fixed migration credential copying, archive overwrite / permissions, index audit bytes, cost metadata, ledger shape / usage-file lifecycle, failed App probes, Hook paths / failures, tier rereading, source switching, relay transparent forwarding / validation, interpreter choice and asset parent creation.
- Shared App probing / usage completeness checks extracted; unused imports removed. No wholesale approval / billing / hardware-state rewrite, price-card amount changes or unmeasured performance claims.
- Rewrote active README / runbook / backlog / FAQ; old Controller README archived and stages labeled. Separated build, later device 0.2.13 evidence, unverified loaded patches and complete hardware acceptance. Preserved all five v0.2.12 cases and actual submitted receipt.
- Actual results: Controller 256, tools 19, Swift core 30, C navigation / tones / eight mocked audio groups, full Demo build. Initial socket / Swift cache restrictions passed after authorization. Old Hook fixtures retained / extended before full rerun. See [review report](../reviews/2026-11-02-code-and-docs.en.md). No real service restart, flash, pairing, reset, account change, commit, push or tag during review.

Subsequent historical records apply only to their respective stages, including wording such as current / this round / awaiting deployment.

## 2026-11-02: menu 2 → 2 desktop launch fix

- Device / HTTPS logs existed but App session integration waited; only `UserPromptSubmit` / `SessionEnd`, no relay heartbeat, model or usage events. Root cause: Bridge-only `--desktop` launch rather than `launch_desktop.py` version checks / App / relay chain.
- 2 → 2 probes App: closed → stop idle Bridge and full verified launch; running → Bridge-only restart. Unknown versions / digests still reject; active App not auto-closed.
- 16 recovery / activation, three new console lifecycle and 11 DesktopBroker cases passed. Actual new App integration / device approvals awaited App physical approvals connected and real requests. No reflash; host lifecycle only.

## 2026-11-02: ordinary English tool receipt fixed

- Ordinary `PostToolUse` overwrote Chinese feedback with `Tool returned on Mac`, introduced by `efb760c` on 2026-10-25 and present before v0.2.13. Changed only that receipt to Chinese; no redefinition of approval / execution success or duration.
- 11 DesktopBroker tests passed, including two new cases. No full 237 rerun or rebuild / flash / Bridge restart. Load via 2 → 2 and visually inspect; no firmware update needed.
- Earlier real read-only command printed successfully and user reported interaction normal, without a fresh version / complete dual matrix. Retain that scope.

## 2026-11-02: v0.2.13 implementation after committed plan, then undeployed

- Plan `9545223` preceded code. Scope only removed retired handoff.
- Firmware handoff action / state / message / page removed; computer-details prompt only. Bridge handoff / recall module / calls / display receipts removed; old messages harmless. Second-confirmation hold-submit, first response wins and genuine submitted receipts retained. Launcher / maintenance / manifest firmware `0.2.13`, Bridge `0.2.13-native-app`.
- Full Python 237; three retired recall cases removed, old handoff cases now verify no recall / submit / cancel. C navigation / confirmation / tones and eight mock audio groups passed; 15 request / choice combinations checked harmless hold / release. Font / shell / version / manifest checks passed.
- First run: 18 sandbox socket errors; authorized rerun passed. ESP-IDF 5.5.3 reused locked components despite registry warning, without upgrading. Local-only artwork image 2,359,568 bytes, SHA-256 `94b52c72ff45a984eccb86aab92b516b47dbf3aa02e0267aabc556e01d5c0e21`; logs ignored in `private/regression-0.2.13.log` and `private/build-0.2.13.log`.
- No restart / flash / pairing / reset / account change / release; runtime was still 0.2.12 then. Hardware awaited deployment. Historical case 5 / docs and Git v0.2.12 remained; mock / build was not hardware success.
- Version review removed chat narration, labeled planning as then / that stage, updated link descriptions to current implementation / deployment state, and rechecked retirement boundaries / preserved approvals / old evidence.

## Historical plan 2026-11-02: direct operation on both sides, retire hold-handoff

- User liked simultaneous native App / device prompts, using device or mouse after sound. Adopted direct dual Allow / Deny; first answer clears the other without preliminary transfer.
- Details hold-confirm to Mac became retired history, preserved with notes / strikeout and Git v0.2.12 (`fb02632`). Next version removes executable handoff / recall / display receipts, leaving a desktop-details prompt. Distinguish retained second-confirmation hold-submit.
- Markdown / commit first, then bounded firmware / Bridge implementation, not a wholesale rewrite. At planning, source / runtime remained 0.2.12; no build / deployment and other backlog paused. See [v0.2.13](../releases/v0.2.13.en.md).
- Preserve five hardware cases as history; case 5 no longer a current requirement. Only doc diff / links / consistency were checked then, without re-claiming tests or new hardware success.

## Documentation wording

Record version-specific feature state, change scope, verification and deployment using engineering descriptions such as planned / implemented / retired / awaiting deployment. Preserve historical features / evidence and maintain developer records rather than retell chats.

## Historical evolution

- Initial goal: standalone Codex physical controller, state / quota display and Apple emoji pet; no large Pocket OS in phase one.
- User had no complete old pet code and explicitly accepted recreation from the emoji mapping. Do not claim reuse of nonexistent code.
- Mac Demo came first with direction / Return simulating three buttons; mark all simulated account / approval data.
- Direction interactions evolved from page / selection conflicts into short-select / long-main-page navigation; long requests gained first / last jumps, final-page selection and return from confirmation.
- Original desktop-App hardware Approve / Deny is primary. CLI was temporarily accepted as a fallback, then desktop priority reaffirmed. Notifications / Mac-only approval do not satisfy the requirement.
- Inspected internal launch switches and transparent stdio relay preserve the App package and avoid GUI auto-approval; new versions require inspection.
- Early USB-only / Unknown / missing-art prompts did not meet the goal. Later came encrypted Wi-Fi, physical USB pairing, real usage, private Apple images, Chinese pagination, battery and audio.
- Volume 0–100%, 10% steps; audio cannot block networking. Completion returns to idle after roughly three seconds.
- Third-party OpenAI / Codex / GPT gateways must not have balances presented as ChatGPT quota / resets.
- Token repairs progressed through restored-chat models, cumulative deduplication and turn totals, then compaction / billed-but-local-missing reconciliation.
- Show money with `$`, not space-consuming USD labels. Reset needs second confirmation / hold.
- HTTP header failures motivated verified certificates, bounded retry, generations and fixed offline safety windows. Another actual outage involved changed Mac subnet, old paired IP, stopped Bridge and App upgrade.
- Long context is not a simple doubling of total cost: recorded Sol requests above 272K input have doubled input / cache and 1.5× output, per request. Custom / OpenAI source and default multiplier 1 prevent duplicate discounts.
- Twenty-seven top-level command entries were consolidated into one console, with old entries under maintenance tools; do not scatter daily launchers again. The newly authorized independent language entries are a deliberate later-phase exception.
- On 2026-11-02 development paused for Developer-directory organization and comprehensive Markdown handoff.

Append dated intent, implementation evidence and acceptance for later work; never mark unaccepted work complete.

## 2026-11-02: new working directory Bridge integration

- User requested activation after moving from old Codex outputs to Developer. Inspection found old App / Bridge / relay and seven old absolute Passport Hook paths still live.
- Added `controller/scripts/activate_migrated_runtime.py` through the existing console, without top-level command. Only after manual App exit may it stop old service. Preserve old project / pairing / rates; back up target ledger and Hooks, replace exact old Passport commands only, never grant trust.
- Pairing / certificates / rates matched bytewise; ledgers differed. Sync latest ledger only after old shutdown rather than launch the migration-time copy.
- Six new switch, eight recovery and fourteen notification / Hook tests passed (28); console shell syntax and new Python serial 3.5 / OpenSSL 3 / websockets imports passed. Real switch / Allow / Deny awaited manual exit.
- Process inspection first hit sandbox denial and succeeded after approval. No flash / pairing / reset / account changes.
- Pre-switch read-only IPC: old desktop connected, no pending approvals, device offline; new Bridge not running. Prepared entry did not establish recovered wireless / physical approval.

## 2026-11-02: post-migration runtime verification

- User reported switching. Receipt at 01:07:29 +1100, new-directory processes and old / new IPC confirmed Developer Bridge / relay / launcher running and old Bridge stopped.
- Wi-Fi device online, firmware 0.2.11, desktop / approval_receipts true; seven Hooks at new paths. Pairing address unchanged; App 26.1027.30824 digests passed.
- Snapshot had `permission_pending=true`, `hook_pending=1`; no stop, restart or auto-approval. New-path Allow / Deny, Hook trust, restart / sleep stability were not yet accepted.
- Read-only verification / docs only. Initial local IPC PermissionError passed after approval; host tests were not hardware evidence.
- Dependencies came from the new venv / wheel / .pth, but base Python still used Codex runtime cache. Stable Python, source commit and independent private backup were listed for authorized archival; no unrequested install / commit / upload / old-directory deletion.

## 2026-11-02: physical-button acceptance after migration

- User requested real hardware acceptance. Original-chat directory-write requests used independent Developer files; no flash / pairing / reset / account change.
- Physical Allow executed and created its file. Broker: `source=hook`, `choice=allow`, `review_page=15`, Wi-Fi online and relay connected.
- Physical Deny returned `Rejected("PermissionRequest hook denied approval")`, command not executed, deny file absent. Expected test denial, not automatic approval-review rejection.
- User confirmed physical buttons and emoji: Allow 😆, Deny immediately 😭, no 😶. Extra physical Allow cleaned the exact verified allow file; deny file stayed absent.
- Ignored `private/hardware-acceptance-20261102-allow.json` / `-result.json` retain evidence. Scope: real PermissionRequest Allow / Deny, execution effects and visually confirmed emoji, not all permissions / stability.
- `last_device_delivery=null`; native independent submitted receipt remained unaccepted then. No App restart or system sleep test; project stayed paused.

## 2026-11-02: authorized archives, independent Python and offline dependencies

- User confirmed Hooks and authorized archival / Python cleanup. Development stayed paused; no flash / reset / account change; local commit only, no push then.
- Homebrew Python 3.12.15, Tcl / Tk 9.1 and OpenSSL 3.5.9; new `private/bridge-venv-homebrew` alongside the old runtime. `local-env.sh` points at stable Homebrew and all shell / relay entries use shared `CONTROLLER_BRIDGE_PYTHON`; Hook source / trust commands unchanged.
- Added original PyPI pySerial 3.5 wheel, upstream v3.5 BSD license and fixed SHA-256. Both serial / websockets wheels are verified before .pth writes, enabling offline restore without pip / network. Publication audit permits only that pinned wheel.
- Actual results: Controller 227, tools 10, C navigation / tones and eight mock audio groups, Tk / Tcl import / initialization and pip check passed. First full run had 16 sandbox socket errors; authorized rerun passed. PySerial download first had sandbox DNS failure and succeeded from PyPI after approval.
- Tool regression exposed macOS `/var` alias bypass; consistent `destination.resolve` fixed it and existing test passed. Archive cases cover credentials / venv / logs / symlink exclusion, member hash readback and malformed JSON rejection.
- Independent same-disk sibling archive separates source / Git bundle and private recovery material with pairing / ledger / Flash / assets / Hooks, modes 0600 / 0700, no Codex credentials. Live per-file snapshot is neither global transaction nor off-site backup.
- Running Python was not hot-swapped or App auto-closed. Manual quit / same console `--restart-app` writes actual `private/active-python.json`. Old venv / outputs / IDF retained.

## 2026-11-02: independent Python restart completed

- User followed `--restart-app`, quit manually, reopened through console and confirmed reconnect with a full Terminal log.
- Receipt `2026-11-02T01:27:58+11:00`: new bridge-venv-homebrew, Homebrew base, Python 3.12.15 / OpenSSL 3.5.9 / pySerial 3.5 / websockets 17.3. Old prepared false was pre-switch history.
- Intermediate no-Bridge / FileNotFoundError was between old stop / new start, not persistent failure. Old venv and verified first archive (`e4fb7c5`, 149 private members) retained.
- Final activation docs / private receipts saved in sibling `2026-11-02-final`; success by `ARCHIVE-RECEIPT.json`. No push, flash, pairing or reset then.
- Sleep / native submitted receipts / all permissions / stability stayed separately unverified; import checks / reconnect did not accept them.

## 2026-11-02: GitHub synchronization authorized

- User explicitly requested updates uploaded. Fetch showed no new upstream work to merge, with two local archive / Python updates ahead.
- 207 indexed files passed sensitive-path / credential-pattern audit; prior test evidence remained attached to its commits, not rerun. Push only source, pinned wheels / licenses and handoff.
- Never upload recovery archives, ledger, pairing identities, login credentials, Apple images or artwork firmware. Preserve local archives; verify remote main after ordinary push.

## 2026-11-02: dual-side approval and Mac handoff design (later superseded)

- User saw device handoff without desktop UI and wanted either side usable. `ACTION_MAC` only muted locally and blocking PermissionRequest hid native App approval, so the old App-window prompt was unreliable.
- Added real Companion Tk UI through existing Broker / private Unix IPC. Launch argv had request ID only; full details were chunk-read without file / argv / model disclosure. Second confirmation submits the same request; first answer clears other device / Mac / relay views, retaining chat / version-digest protections.
- 0.2.12 sent real `mac_handoff`; Bridge recalled / reopened the window. Only complete visible-window short-lived heartbeat yielded displayed status, revoked on hide / new handoff. Display / submitted / read state did not pretend actual authorization or execution. Mac review did not change device page review; unknown native Allow semantics stayed with original App.
- Full Python 242 and thirteen receipt-hardening cases, C navigation / tones and eight mocked audio groups passed; synthetic Tk content / buttons / hide-recall / second-confirm-submit passed. Screenshot timeout prevented visual QA. Authorized retries overcame socket / registry blocks.
- ESP-IDF 5.5.3 build only: artwork 0.2.12, 2,360,544 bytes, SHA-256 `dae8c7c2dacea383f0c3deb3cbc9ac3a0d78faa653151faf2b73e1338053de04`. New glyphs covered. No flash / runtime restart / pairing / account / ledger / commit / push.
- Next then: save / manual quit / console switch, protected dual-backup / live-partition update and original-chat hardware acceptance. Synthetic / mock / build checks are not real-device success.

## 2026-11-02: user update launcher finalized

- User asked if firmware was flashed and requested a self-run command. 0.2.12 was built but not flashed; no device update in this step.
- Existing menu 7 maintenance still asserted 0.2.11; changed to 0.2.12 while preserving exact App checks, full tests, Bridge stop, dual backups / live partitions, factory write / readback and original-chat reconnect.
- Shell / launcher / manifest / image version, size and SHA-256 consistency passed; no new claim of full 242 or real flash. Relay unchanged, so App could stay open; this corrected the earlier generic quit step.

## 2026-11-02: ordinary Terminal missing Python fixed

- User log: 242 tests passed then `python: command not found` during USB discovery. No Bridge stop / backup / flash; deployment unconfirmed.
- Bridge interpreter now performs discovery / IPC preflight; separate `CONTROLLER_FLASH_PYTHON` runs esptool 4.x. Check before stopping Bridge. `env.sh` fallback only with explicit `IDF_PYTHON_ENV_PATH`; ignored local-env selected existing IDF Python / esptool without installing or replacing modern Bridge Python.
- Three isolated shell / fake-interpreter cases and four dependency / launcher checks passed. Actual minimal-PATH import / USB enumeration passed, without opening USB, stopping Bridge or updating. Isolated tests are not flash acceptance.
- Retry through the same menu 7, no new command / pairing / reset. Record deployment only after actual matching backups, write / verification and 0.2.12 hello.

## 2026-11-02: standalone UI rejected; approvals return to original App

- After user update, read-only IPC showed 0.2.12 online and relay connected; one read-only query allowed through Tk. Deny was aborted with no test file. User explicitly rejected standalone UI and required original native cards.
- Hardware testing stopped; Tk entry became a no-op compatibility file for old running Brokers. New Broker removed all UI APIs / auto-launch, not a new app.
- Desktop Hooks no longer block / pre-answer PermissionRequest / permission PreToolUse; empty Hook results leave native approval to App, relay mirrors real requests to device. Cached results cannot bypass native. Device hold only activates an already running verified App, with no automatic clicks / package modification.
- Only local official JSON schema was generated and 26.1027.30824 digests checked, retaining `startedAtMs`, scope / request binding. Protocol docs are design references, not hardware evidence.
- Full Controller 240: removed thirteen rejected UI cases, added eight routing / activation / cache / compatibility cases, converted two private-Mac integrations into real App-protocol Allow / Deny clearing device state. Eight related cases passed after activation-timeout hardening.
- No firmware reflash or automatic App / Bridge stop. New source awaited user 2 → 2 safe restart, preserving chat. Device 0.2.12 retained conservative window requests / no receipt; no invented card-render proof. Native dual hardware remained pending then, without fallback to standalone UI.

## 2026-11-02: five native dual-side hardware cases passed, v0.2.12 release authorized

- User switched Bridge and individually confirmed device Allow / Deny, original-App Allow / Deny with device untouched, and details handoff recalling App then Allow.
- Device Allow executed a real read-only command, `source=desktop`, `choice=allow`, with separate matching submitted receipt. Both denials returned rejected by user without execution. Both Mac allows printed success markers. User confirmed opposite-side clearing and no auto-approval during handoff. Do not treat denials as errors or invent five receipts.
- Ignored 0600 `private/hardware-acceptance-native-20261102.json` stores evidence; publication has only de-identified matrix. Earlier aborted standalone test is not native acceptance.
- User requested Markdown first, then publication. Updated root / controller README, handoff entry / state / architecture / UX / runbook / backlog and release notes, preserving failed / rejected stages as history.
- Pre-release full Controller 240, C navigation / tones and eight mocked audio groups passed; diagnostic revision aligned to `0.2.12-native-app`. No repeated flash or pairing / account / ledger changes.
- Source release tagged v0.2.12 after index audit, with only source / docs / pinned dependencies, never private data / Apple assets / artwork firmware. Completion requires remote main / tag verification. No automatic expansion of backlog, permission coverage or stability conclusions.

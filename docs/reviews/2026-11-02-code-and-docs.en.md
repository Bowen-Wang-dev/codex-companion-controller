# Code and documentation review report

[简体中文（默认）](2026-11-02-code-and-docs.md) · English

Date: 2026-11-02 (Australia/Sydney). Baseline: local `b0165da` and worktree, within the user's code review, necessary refactoring and documentation-normalization task. Changes initially stayed in the worktree; subsequent commit / GitHub synchronization was separately authorized, as recorded in [project state](../handoff/01-PROJECT-STATE.en.md). Source synchronization is neither device deployment nor a new release tag.

## Scope and method

Git-tracked and new maintenance files covered Bridge, relay, approvals / metering, pairing / update scripts, migration / archive tools, firmware application, BSP, Swift Demo, tests and public documentation. Private credentials, bills and device backups were not traversed; historical counts did not substitute for actual execution.

Inventory: 217 public source / documentation files: 70 Python, 37 C/H, 13 Swift, 39 shell / command, 34 Markdown; remaining files were configuration, pinned dependencies and licenses.

Checks included full inventory, all Python AST parsing, all shell / command syntax, manual critical-state / data-path review, existing / new regressions, C host checks, Swift core and full Demo build, actual Git index / worktree publication audit and relative Markdown links.

Manual focus: authorization, races / receipts, disconnects / file lifecycle, cost categories, launchers, private data and migration paths. Generated `ui_font.c` was not manually rewritten line by line; BSP and licenses retained provenance. Repository-wide review is not a formal proof of correctness or complete hardware-driver fault injection.

## Fixed issues

| ID | Problem / effect | Repair and regression |
|---|---|---|
| R01 | Migration copied auth.json from runtime / backup trees, violating credential isolation | Excluded in both paths; synthetic tests retain pairing / device backups |
| R02 | Archive permissions tightened only at end, existing outputs overwritten, symlink roots bypassed child checks | Mode 0600 before private writes, exclusive creation, reject private / dist symlink roots; failure files stay private |
| R03 | Publication audit listed index paths but read worktree bytes, allowing clean unstaged edits to hide staged sensitive content | Inspect actual Git stage / mode / blobs; retain pinned-wheel digest checks and errors without content disclosure |
| R04 | Mixed-tier / multiplier metadata could revert to a single value after a third component, depending on order | Aggregate using sets; six permutations verify identical flags / amounts |
| R05 | Valid JSON ledgers with array / null / scalar roots caused uncaught exceptions | Require an object, retain original file and block counting; no automatic reset / overwrite |
| R06 | Usage-file deletion could crash completeness checks; truncation / rotation could appear complete | Shared caught_up() verifies inode, size and read offset; delete / restore / partial append / truncate / replacement regressions |
| R07 | Launcher did not distinguish App exit from failed process probing | Shared probe stops launch / restart on failure; regression confirms no Bridge process creation |
| R08 | Hook installation / diagnosis assumed old directory geometry and could report success after subprocess failure | Default current repository; explicit old-directory override; check result, preserve unrelated Hooks / backups |
| R09 | Long-context config rereading compared normalized cards to raw cards and falsely failed on added metadata | Compare normalized expected values; temporary config verifies success before simulated restart |
| R10 | Price-source switching re-enabled disabled custom long tiers, parsed unused invalid thresholds, mishandled non-object rate files | Back up only enabled tiers, retain unused text without early conversion, defend shapes; headless roundtrip tests |
| R11 | Relay assumed JSON metadata objects; unknown shapes interrupted forwarding; missing --listen value indexed past argv | Parse supported objects only, forward other original lines byte-for-byte; official program handles non-stdio / incomplete listen arguments |
| R12 | Non-object device / IPC JSON and bad timestamps reached unguarded code | Reject shapes, boolean / nonfinite timestamps and invalid relay IDs; preserve connections / pending requests |
| R13 | Image check used bare python; asset import on clean tree lacked parent directories | Separate CONTROLLER_FLASH_PYTHON with clear missing-tool exit; create asset parent; no device write |

Unused imports removed and shared checks reused. No price-card amount, tier-selection, approval-choice, firmware emoji or Flash-range changes. No unmeasured performance / power claims.

## Documentation organization

- Rewrote root / Controller README, aligning Chinese / English version state, daily console, environment prerequisites and executable paths.
- Separated source, build, later runtime evidence, patch loading and hardware acceptance. Early never-deployed 0.2.13 claims conflicted with later logs; labeled phases / evidence without fresh device queries or inference.
- Preserved five v0.2.12 hardware cases and separate submitted receipt, no longer missing; did not extend acceptance to later versions / all permissions.
- Rewrote runbook, backlog and FAQ; prices consistently described as snapshots rather than live official prices.
- Preserved original Controller README as a scoped historical snapshot; labeled STATUS, CHANGELOG and stage docs historical without deleting evidence / evolution.

## Actual verification

| Check | Actual result in that review |
|---|---|
| Controller baseline | 241 passed; first restricted run had 18 TCP / Unix permission errors, authorized full rerun passed |
| Controller after fixes | 256 passed; 15 new test methods; old Hook cleanup case extended for current default / explicit legacy directory |
| Migration / archive / publication tools | 19 passed, nine new versus baseline; temporary directories / synthetic data |
| C host | Navigation, holds, approvals, expiry, disconnection, pagination / reset assertions; tones and eight mocked BSP / RTOS audio groups passed |
| Swift core | 30 state / navigation checks passed |
| Swift Demo | Full CompanionDemo build passed; GUI not launched |
| Syntax / docs | AST for 70 Python, syntax for 39 shell / command, local links in 34 Markdown and git diff --check passed |
| Publication contents | 213 existing indexed blobs audited; separately 217 worktree / new paths, credential patterns and two vendor-wheel digests passed; not staged into the real index |

The final full run first exposed an old Hook fixture assuming `outputs/PassportController` as default. The case was retained / extended for current default cleanup and explicit legacy-path cleanup, preserving unrelated Hooks / backups. The subsequent full 256 passed; no failed case was deleted.

The first additional Swift build failed on sandbox compiler-cache denial and derived SDK errors. After authorization, the same toolchain compiled fully with a temporary cache. No SDK upgrade / dependency installation.

Baseline, sandbox failures, final Python and Swift logs remain ignored under `controller/private/checks/code-doc-review-20261102/`, mode 0600. Results do not include hardware acceptance.

## Not performed and remaining scope

The review did not restart real App / Bridge, open device serial, flash, pair, reset, change accounts, read login credentials, create tags or push. Later GitHub synchronization used separate authorization without changing device boundaries. No firmware rebuild or real Apple asset import; C audio uses mocks and Swift compilation is not manual GUI acceptance.

Remaining: new-version hardware matrix, sleep / wake / long runs, real-screen layout, GUI end-to-end, provider export completeness and cache TTL breakdown. `service.py` separation, ledger / estimation scan costs, relay session growth and firmware initialization cleanup are in the [backlog](../handoff/09-BACKLOG.en.md), driven by measurements / fault injection rather than speculative rewrites.

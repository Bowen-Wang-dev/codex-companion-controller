# Organization, migration and private data

[简体中文（默认）](07-MIGRATION-AND-PRIVACY.md) · English

The target layout follows GitHub:

```text
codex-companion-controller/
  AGENTS.md
  README.md
  controller/         # firmware, host Bridge, main console
    private/          # local-only pairing/certificates/rates/ledger/backups
  mac-demo/           # independent simulated Demo
  docs/handoff/       # agent handoff
  tools/              # checks and one-off migration utilities
```

## Organization principles

Copy and organize without deleting the old directory. Preserve Git history, remotes and uncommitted handoff documents. The migration source baseline came from the organized local GitHubSource (`00b6133`); old outputs / work build caches and compressed archives do not join the source tree.

Migration copies key local files only into ignored paths: pairing settings / certificates, rates / model override, ledger, private audits, Flash backups, Apple assets and personal firmware images. Do not copy `~/.codex/auth.json`; same-name login credential files are explicitly excluded at the runtime root and inside private backup trees. Old compiler / Swift / component caches, large logs and temporary test directories stay at their old locations.

Recreate virtual environments at the final destination; old shebangs and wheel `.pth` paths cannot simply be moved. Component caches and IDF tools are outside the old project; retain that toolchain for now. The migrator records machine Python in ignored `controller/private/local-env.sh`; use `PASSPORT_TOOL_ROOT` to identify old external IDF paths manually if needed. Reconfigure ESP-IDF before building. Windows has a separate venv / native relay and current-user DACL; these machine-specific generated files are excluded from source archives.

## Activating the new directory is separate

1. Copying files alone does not change the running App / Bridge or flash firmware.
2. A new root changes the private IPC hash. Do not run old and new Bridges together; both use device service port 8765.
3. Keep the current chat and finish work first. Stop old Bridge, have the user quit the App manually, then launch the console from the new directory.
4. User Hooks contain absolute old `bridge/hook.py` paths. Do not append duplicate commands with the ordinary installer. Back up `~/.codex/hooks.json`, remove only exact old Passport handlers, then register the new path while preserving unrelated plugins / Hooks.
5. Removing / replacing Hooks can require trust again. Never choose Trust All for the user. Verify events and physical approvals at the new path.

Windows setup does not copy an old Mac account or activate Mac pairing. Device host IP, certificate and firewall reachability must be checked for the actual host.

## Privacy and copyright

Keep `private/`, authentication files, tokens / passwords / private keys, device identifiers, real CSV exports, original Apple images and firmware containing them out of Git. Preserve the old project for rollback; GitHub source is not a reason to delete NVS backups or images. Before activation verify ignore rules, key file hashes, venv dependencies and source tests.

## Migration status (updated 2026-11-02)

The Developer destination was copied and activated. Ignored root `LOCAL-MIGRATION-RECEIPT.json` records 340 verified files; `controller/private/runtime-activation.json` records the latest ledger sync and Hook path switch. The new-directory Bridge / relay and device Wi-Fi were actually online; the old service was not running. Hardware approval acceptance boundaries are in [project state](01-PROJECT-STATE.en.md).

Retain the old project, old toolchain and pairing / backups / private assets in the new directory. Migration completion does not authorize deletion. Git is not a private recovery package: later archives must separately back up private data without uploading secrets, original Apple artwork or firmware containing it.

## Local archive and recovery

`tools/archive_local.py --destination <new-directory> --include-hooks` requires a clean source worktree. It generates `source.tar.gz`, `source-history.bundle`, `PRIVATE-RECOVERY.tar.gz`, `RESTORE.txt` and digest receipts. Never upload the private package. Included `host-config/hooks.json` is reference material, not permission to overwrite unrelated plugin settings; `~/.codex/auth.json` is excluded.

Recorded local destination: `/Users/bowen/Developer/codex-companion-archives/2026-11-02-python-handoff`. This is a same-disk copy; off-site / offline encrypted backup has not been performed. `ARCHIVE-RECEIPT.json` and internal `PRIVATE-MANIFEST.json` establish successful verification, with every member read back and compared by SHA-256. Ledgers were read file by file while running; this is not a stopped transactional snapshot.

Python recovery: install independent Python 3.11+ / OpenSSL 3 first. Recorded macOS choices are Homebrew `python@3.12` and `python-tk@3.12`. Rebuild the private venv at the new path, update `CONTROLLER_MODERN_PYTHON` and `CONTROLLER_BRIDGE_PYTHON` in `private/local-env.sh`, then run `scripts/setup_bridge.sh`. Both wheels are in vendor and can be checked / enabled offline. On Windows use `scripts/setup_windows.py`. Retain old local environments until the new process is verified.

The final activation addendum archive is the sibling `2026-11-02-final`, including the actual Homebrew Python launch receipt and updated handoff. Do not overwrite `2026-11-02-python-handoff`; each `ARCHIVE-RECEIPT.json` identifies its source commit.

2026-11-02 review addition: private archives receive mode 0600 before content is written; existing archives and symlink roots are rejected. Partial failure output is not a successful archive. Migration / archive regressions use synthetic material. The review did not repeat a real private migration / archive; this documentation phase does neither.

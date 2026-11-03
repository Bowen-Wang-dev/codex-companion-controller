# Host languages and separate entries

[简体中文（默认）](12-HOST-LANGUAGES.md) · English

Updated 2026-11-03 (Australia/Sydney). This is bilingual phase two: host user interaction. Phase-one documentation commit is `48603c8`; phase three now adds 0.2.14 installed device languages and guards; see [device languages](13-DEVICE-LANGUAGES.en.md). Statements below about unchanged firmware retain the phase-two boundary.

## Choose an entry

| Platform | Chinese (default) | English |
|---|---|---|
| Windows | `controller/Codex Companion 控制台.cmd` | `controller/Codex Companion Console.cmd` |
| macOS | `controller/Codex Companion 控制台.command` | `controller/Codex Companion Console.command` |

Double-click the desired language entry. The two language versions run separately, sharing pairing, rates, ledger, dependencies and safety checks. Choosing a language neither copies configuration, creates a second service nor changes accounts. Existing Bridge instances retain single-instance protection; do not run Chinese and English Bridges together. Updating files does not change a running process's language; the next launch or safe restart through the selected entry loads it.

Windows batch files use the UTF-8 code page and CRLF; `.command` / `.sh` use LF, enforced by `.gitattributes`. Entries pin `COMPANION_LANGUAGE=zh-CN` or `en`, inherited by setup, submenus, the App launch chain and Bridge. macOS private configuration cannot override the entry's selection. Missing / unknown language values default to Chinese.

## English coverage

- Main menu, device / Bridge diagnosis, connection recovery, launch / restart instructions and cancellation / error receipts.
- USB pairing instructions, network input prompts and validation errors; Wi-Fi password entry remains hidden.
- Token totals, read-only audit, reset prompts, and rate-editor titles, fields, help, saving and validation.
- Hook registration / trust prompts, Windows firmware maintenance, image validation / backup progress, and macOS menu 7 maintenance instructions.
- Host Bridge connection, handshake, wireless diagnostics and event logs. The rate editor scrolls vertically and limits initial height to the screen, accommodating longer English text.

`YES`, `RESET`, `FLASH`, menu numbers, arguments, protocol fields and paths remain unchanged; confirmation words are not translated. Device decisions, the original App chat, exact version / digest protection, dual-backup / live-partition safe updating and first-response semantics remain. Device screens, device-bound requests / receipts and third-party program output are not replaced by host UI localization. Custom model names, commands, paths and other user data are displayed unchanged. System / third-party errors may retain their own language.

## Direct use and checks

Windows read-only check from repository root:

```powershell
& './controller/Codex Companion Console.cmd' --check-only
```

Choose a language explicitly when invoking Python tools directly; without a setting the default is Chinese:

```powershell
$env:COMPANION_LANGUAGE = 'en'
& './controller/private/bridge-venv-windows/Scripts/python.exe' controller/scripts/controller_console.py
```

On macOS use the English entry daily. For direct tool invocation:

```sh
export COMPANION_LANGUAGE=en
source controller/scripts/env.sh
"$CONTROLLER_BRIDGE_PYTHON" controller/scripts/controller_console.py
```

Either official language entry overrides inherited language with its fixed selection. Read-only checks do not open serial or start / close App / Bridge; environment preparation verifies and enables existing offline dependencies.

## Actual verification and boundaries

New regressions cover real console processes in both languages, real Windows CMD argument / exit forwarding, submenu cancellation, exact `RESET` / `FLASH` protection, language inheritance, catalog completeness, errors versus user data, English controls / width in a hidden Tk window, temporary rate persistence / validation and UTF-8 model names. A synthetic Broker case verifies English host logs leave Chinese device requests and approval capability unchanged.

The actual English Windows CMD `--check-only` passed without Chinese interface text in its output. Five isolated shell regressions passed under WSL, covering both macOS language entries, private configuration not overriding language, maintenance and early failure protection. Fake interpreters do not operate devices; this is not macOS hardware acceptance. Python 3.11 syntax compatibility passed.

Final Windows Controller regression: 295 tests, OK (18 skipped), including 13 host-language cases with real CMD / hidden Tk and temporary settings. Five isolated WSL shell cases passed, along with actual English CMD `--check-only`, Python 3.11 syntax for 48 files, all shell / command syntax and local links across 60 Markdown files. Native macOS execution, real App / device workflows and complete manual GUI acceptance remain uncovered.

This phase did not launch real App / Bridge, flash, pair, reset, register Hooks or change accounts. Complete manual Windows / macOS GUI flows, real App / device dual-side cases and phase-three firmware English need separate verification. Tests use temporary settings / synthetic requests; original logs remain ignored in `controller/private/stage2-*.log`.

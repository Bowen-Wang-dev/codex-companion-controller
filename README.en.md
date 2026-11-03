# Codex Companion Controller

[简体中文（默认）](README.md) · English

A physical Codex controller, status display and emoji interaction prototype for the FoloToy AI Passport. The host Bridge handles sessions, approvals and local metering; the ESP32-C3 handles the display, three buttons, wireless connectivity and alerts. macOS is supported alongside the Windows 10/11 host implementation. Development evidence comes from Windows 11 Pro; see the [platform and hardware acceptance boundaries](docs/handoff/11-HOST-PLATFORMS.en.md). This is not an official OpenAI, Apple or FoloToy product.

## Versions and verification status

As of 2026-11-03 (Australia/Sydney):

| Item | Status |
|---|---|
| Source | Firmware `0.2.13`; Bridge `0.2.13-native-app`; host Demo `0.4.0` |
| Existing release baseline | Git tag `v0.2.12`; five native dual-side hardware acceptance cases in the [release notes](docs/releases/v0.2.12.en.md) |
| Latest device evidence | Later logs report firmware `0.2.13`; the user subsequently confirmed completing the Windows update and a basic visual check. Complete acceptance of the new version remains pending |
| This phase | Markdown documentation only; console launchers and firmware localization belong to separate later commits |
| Follow-up | Windows 10, this round's macOS execution and the Windows original-App/device approval matrix remain unverified; see [project state](docs/handoff/01-PROJECT-STATE.en.md) |

Firmware versions, Bridge source revisions, code loaded by running processes and hardware acceptance are distinct states. One log or one successful operation does not replace complete acceptance.

## Features and boundaries

- The relay delivers the same approval to the original desktop App chat and the device; the first valid response wins. Device review retains complete pagination, no default selection, a second confirmation and hold-to-submit.
- v0.2.13 removes hold-to-handoff from the details page. Requests can be viewed and handled directly in the desktop App. Missing file modification details or unsupported permission semantics cannot be approved on the device.
- Hooks provide task state and user-action reminders. Marking a notice read does not answer it; tool return, approval submission and task success are separate events.
- USB physical-consent pairing and HTTPS synchronization are supported. Device online status proves only the device-to-Bridge link; desktop approvals also need the relay and original session.
- ChatGPT account windows and third-party token metering are separate. Estimates use local configuration and per-request tier boundaries; this is neither an account-wide billing ledger nor a live official price service.
- Demo tasks, approvals, quotas and resets are simulated. HTTPS clock calibration is a real network request and does not change system time.

Desktop App integration accepts only exact versions and file digests registered in source: `26.1016.62342` and `26.1027.30824`. Internal launch switches are not stable public settings; unknown versions require a fresh inspection.

## Daily entry

On macOS use `controller/Codex Companion 控制台.command`; on Windows use the same-name `.cmd`. Both invoke the shared console; the first Windows run prepares an isolated Python environment. Requirements and checks are in the [platform guide](docs/handoff/11-HOST-PLATFORMS.en.md). These existing entries are Chinese; separate English entries are planned for phase two and are not delivered by this documentation commit.

| Menu | Purpose |
|---|---|
| 1 | Start the App, relay and Bridge through the verified launcher |
| 2 | Diagnose and recover device / Bridge; submenu 2 selects the launch path according to App state |
| 3 | First-time pairing or Wi-Fi update |
| 4 | Edit local model rates, price source, long-context tier and multiplier |
| 5 | View counters, audit the last hour read-only, reset local counters after confirmation |
| 6 | Install or repair Hooks; trust still requires manual review |
| 7 | USB firmware backup and application update on both platforms; Windows includes build, validation, safe update and flash-environment preparation |

When the App is running, restarting Bridge cannot add a relay to an App launched normally. Save your work, quit the App manually, then start through the console. The device status “App physical approvals connected” is a connection prerequisite; a real request must still verify behavior. See the [runbook](docs/handoff/06-RUNBOOK.en.md). Historical `.command` entries remain in `controller/维护工具/` and are not daily launchers.

## Development and checks

Bridge requires Python 3.11+ and OpenSSL 3; local independent Python 3.12 environments have been recorded. Set `CONTROLLER_MODERN_PYTHON` for setup, or `CONTROLLER_BRIDGE_PYTHON` for an existing environment. On macOS, `scripts/env.sh` reads local private settings. Dependency wheels with pinned digests ship with source.

macOS checks, from the repository root:

```sh
bash controller/scripts/setup_bridge.sh
source controller/scripts/env.sh
"$CONTROLLER_BRIDGE_PYTHON" -m unittest discover -s controller/tests -v
python3 -m unittest discover -s tools -p 'test_*.py'
bash tools/check-host.sh
zsh mac-demo/test.sh
```

Windows setup and checks, from the repository root:

```powershell
$env:PYTHONUTF8 = '1'
python controller/scripts/setup_windows.py --setup-only
python controller/scripts/setup_windows.py --check-only
& './controller/private/bridge-venv-windows/Scripts/python.exe' -m unittest discover -s controller/tests -v
& './controller/private/bridge-venv-windows/Scripts/python.exe' -m unittest discover -s tools -p 'test_*.py' -v
```

Socket regression tests require local TCP / Unix permissions. Host tests do not call models, spend extra reset credits or constitute hardware acceptance.

Firmware builds require ESP-IDF 5.5.3 and the ESP32-C3 toolchain. Load its `export.sh` before running `bash controller/scripts/build.sh` on macOS; Windows menu 7 reuses an installed ESP-IDF environment or WSL. Component versions are locked in `controller/firmware/dependencies.lock`. Building does not flash the device, and source does not include Apple artwork. See the [controller guide](controller/README.en.md) for asset import, image checks and recovery.

## Safety and data

Codex login credentials stay on their original host and are never copied into the device; migration does not copy the original Mac's credentials to Windows. Never upload `controller/private/`, pairing keys, ledgers, Flash backups, original Apple artwork or firmware containing artwork. Device updates require two matching full reads, live partition checks and an application-only write; never erase the whole chip.

Apple artwork is not distributed with source. Downloading, cropping or local rendering does not establish firmware redistribution rights. Original project code has no assigned open-source license; see [third-party notices](THIRD_PARTY_NOTICES.md).

## Documentation

- [Documentation index and language policy](docs/README.en.md)
- [Agent boundaries](AGENTS.en.md) and [handoff entry](docs/handoff/00-START-HERE.en.md)
- [Architecture](docs/handoff/02-ARCHITECTURE.en.md), [interaction contract](docs/handoff/03-UX-CONTRACT.en.md), [hardware and flashing](docs/handoff/04-HARDWARE-AND-FLASH.en.md)
- [Metering model](docs/handoff/05-TOKEN-AND-PRICING.en.md), [migration and private data](docs/handoff/07-MIGRATION-AND-PRIVACY.en.md)
- [Change log](docs/handoff/08-CHANGE-AND-DECISIONS.en.md), [backlog](docs/handoff/09-BACKLOG.en.md), [review report](docs/reviews/2026-11-02-code-and-docs.en.md)

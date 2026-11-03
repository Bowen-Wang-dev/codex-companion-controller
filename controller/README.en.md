# Controller guide

[简体中文（默认）](README.md) · English

Source: firmware `0.2.13`, Bridge `0.2.13-native-app`. Updated 2026-11-03 (Australia/Sydney). Deployment and hardware acceptance follow [project state](../docs/handoff/01-PROJECT-STATE.en.md); source versions alone do not identify running code.

## Daily operation

On macOS double-click `Codex Companion 控制台.command`; on Windows double-click the same-name `.cmd`. There is one daily entry per platform and language, sharing console and approval logic while preserving the Mac implementation. See the [runbook](../docs/handoff/06-RUNBOOK.en.md) for menus and integration prerequisites, and the [platform guide](../docs/handoff/11-HOST-PLATFORMS.en.md) for Windows setup, tests and limits. Historical macOS scripts are in `维护工具/`. Phase two adds separate English `Codex Companion Console.command` / `Codex Companion Console.cmd` entries covering menus, subtools, rate editor and host logs. Existing Chinese entries remain and pin Chinese. See [host languages](../docs/handoff/12-HOST-LANGUAGES.en.md) for usage and verification boundaries. Device language remains phase three.

Approvals can be handled on the device or original App native card; the first valid response wins. v0.2.13 removes details-page hold-to-handoff while retaining hold-to-submit on the second confirmation page. Device denial or failure shows 😭 immediately. Approval feedback requires a real submission receipt. See the [interaction contract](../docs/handoff/03-UX-CONTRACT.en.md) for emoji, buttons and pagination.

If the device is online but App approvals are disconnected, check that the App was started through the verified launcher and the original chat is open. Repeated flashing, extending offline limits or removing version checks are not remedies.

## Bridge environment

- Python 3.11+, OpenSSL 3; independent Python 3.12 virtual environments have been recorded locally.
- On macOS `scripts/env.sh` selects `CONTROLLER_BRIDGE_PYTHON`; machine paths live in ignored `private/local-env.sh`.
- Initial macOS setup requires a usable `CONTROLLER_MODERN_PYTHON`; `bash controller/scripts/setup_bridge.sh` verifies and enables pinned pySerial / websockets wheels from vendor.
- Windows `.cmd` invokes `scripts/setup_windows.py`, creates `private/bridge-venv-windows` and generates the private native relay. Set `CONTROLLER_MODERN_PYTHON` to select the bootstrap interpreter.
- The macOS Hook client uses system Python; Windows Hooks use the selected isolated interpreter. Bridge TLS and dependencies remain separate from ESP-IDF's Python.

macOS host checks, from repository root:

```sh
source controller/scripts/env.sh
"$CONTROLLER_BRIDGE_PYTHON" -m unittest discover -s controller/tests -v
python3 -m unittest discover -s tools -p 'test_*.py'
bash tools/check-host.sh
zsh mac-demo/test.sh
```

Windows setup / checks:

```powershell
$env:PYTHONUTF8 = '1'
python controller/scripts/setup_windows.py --setup-only
python controller/scripts/setup_windows.py --check-only
& './controller/private/bridge-venv-windows/Scripts/python.exe' -m unittest discover -s controller/tests -v
& './controller/private/bridge-venv-windows/Scripts/python.exe' -m unittest discover -s tools -p 'test_*.py' -v
```

TCP / Unix sockets, synthetic billing and mocked BSP / RTOS tests do not establish hardware, provider or complete GUI acceptance.

## Firmware build and image checks

Firmware requires ESP-IDF 5.5.3, the ESP32-C3 toolchain and locked components. On macOS load ESP-IDF's `export.sh`, then from repository root:

```sh
bash controller/scripts/build.sh
```

Windows menu 7 → 1 reuses an installed ESP-IDF environment or WSL ESP-IDF 5.5.3; Windows handles USB. Local outputs are in `controller/private/build/` (or `private/build-windows/`) and `controller/dist/`. Building does not update the device. The safe updater reads actual partitions; the repository build partition table cannot replace that evidence.

On macOS `scripts/check.sh` additionally checks the local image and requires `CONTROLLER_FLASH_PYTHON` with esptool 4.x, selected separately from Bridge Python without relying on a bare `python` in Terminal. Windows menu 7 → 2 checks image version, chip, size, digest, current-source binding and original artwork. Menu 7 → 4 prepares isolated esptool 4.8.1. Image checks do not open serial ports.

## Apple artwork and fonts

Public source excludes original Apple images, generated image headers and firmware containing artwork. Builds without assets show a missing-assets message; the safe update path rejects such an image.

With applicable artwork rights, import originals from repository root using a Python environment with Pillow:

```sh
/path/to/image-python controller/scripts/import_assets.py \
  --source /absolute/path/to/authorized-originals \
  --rights-file /absolute/path/to/rights.json
```

Asset names are `idle`, `working`, `permission`, `delight`, `crying`, `completed`, `neutral` and `palms`, all `.png`. The rights file must include `apple_original: true` and a nonempty `rights_basis`. The importer only scales and converts RGB565; it does not download, redraw or replace the emoji style.

`scripts/build_personal.sh` uses local system rendering; this does not grant public redistribution rights. Generated output stays local. Chinese glyph provenance is in `docs/ui-font.json`; third-party licenses are in `licenses/`.

## Device update and recovery

Use console menu 7. Requirements include one USB target, available tools, matching image version / digest and no pending approvals. After two full matching 8 MB backups, live partition and security-state checks, only the supported factory application is updated and verified by readback. Bootloader, partition table and existing NVS are not written; no whole-chip erase.

Windows reads in 256 KiB blocks at 115200 baud, disables per-frame progress and retries only reads, at most three times with a final ROM fallback. Failed blocks are discarded; the application stays stopped between blocks. Writes are not automatically retried. The user confirmed completing the Windows update and a basic visual check; this does not establish complete approval or long-term stability acceptance.

Recovery must match the backup directory's `last-write.json` and the original image from that update, within the recorded application range. Never flash generic IDF output directly. See [hardware and flashing](../docs/handoff/04-HARDWARE-AND-FLASH.en.md). This documentation phase performs no update or recovery.

## Metering and private data

Rates match exact model IDs. Built-in prices are snapshots without automatic updates; custom prices and multipliers follow local configuration. Input includes cache and output includes reasoning; five disjoint displayed categories are counted once. Long-context tiers use each request's input, not a whole turn's total.

Menu 5 audits the last hour read-only; specify CSV / TSV paths and time ranges through `scripts/audit_usage.py --provider-log`. Reconciliation is local and is not a provider account-ledger API. Reset affects only local counters and estimates and needs separate confirmation.

`private/` contains pairing, certificates, ledgers and recovery backups and must remain private. Migration excludes Codex `auth.json`; archives separate source from private recovery material. See [migration and privacy](../docs/handoff/07-MIGRATION-AND-PRIVACY.en.md).

## Historical records

The [pre-review Controller README snapshot](../docs/history/controller-readme-before-2026-11-02-review.md) preserves earlier descriptions; its old paths, versions and then-pending acceptance statements do not override current requirements. Release notes and handoff records retain actual acceptance and feature history. See the [documentation index](../docs/README.en.md) for the distinction between current translations and original historical evidence.

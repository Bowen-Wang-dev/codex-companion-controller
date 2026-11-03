# Operation, diagnosis and test runbook

[简体中文（默认）](06-RUNBOOK.md) · English

Source: firmware `0.2.13`, Bridge `0.2.13-native-app`. Current deployment and acceptance are in [project state](01-PROJECT-STATE.en.md); historical test counts are not results from this phase.

## Daily startup

Currently one entry per platform: `controller/Codex Companion 控制台.command` on macOS and the same-name `.cmd` on Windows. See the [platform guide](11-HOST-PLATFORMS.en.md) for Windows preparation, read-only checks and test commands. Menu 7 now supports safe firmware maintenance on both platforms. Separate English entries are phase two; the documentation commit does not create them.

| Menu | Operation |
|---|---|
| 1 | Launch the App, relay and Bridge after exact version / digest checks |
| 2 → 1 | Read-only device and App connection diagnosis |
| 2 → 2 | Safely restart Bridge; use the full launch chain when the App is closed |
| 2 → 3 | USB recovery or Wi-Fi reconfiguration |
| 3 | First-time pairing or Wi-Fi update |
| 4 | Local model rates, source, long-context tier and multiplier |
| 5 | Counters, last-hour read-only audit and separately confirmed local reset |
| 6 | Register / repair Hooks, then review and trust manually |
| 7 | USB firmware backup and application update |

When the App is running, 2 → 2 restarts only Bridge and cannot add a relay to an ordinary App launch. Save work and quit completely by Command+Q on macOS or the App's quit operation on Windows, then choose menu 1 and open the original chat. The program does not close active work automatically.

Do not restart or pair while approval is pending. A failed App process probe stops the operation; unknown is never treated as exited.

## Connection states

- Wireless synchronization normal: the device and Bridge synchronized.
- App connected, waiting for session: relay exists, but original-chat integration is not confirmed.
- App physical approvals connected: relay and session are connected; real requests still need to verify approval behavior.
- App approvals disconnected, or startup log waiting for the actual App session through the adapter: the approval chain is not established.
- Confirm on host (historically “Confirm on Mac”): desktop handling is needed; this is not successful device approval.

Device online status, one `UserPromptSubmit`, model synchronization or token synchronization alone cannot establish real Allow / Deny acceptance. Approval submission, tool return and task success must be assessed separately. English documentation describes the meaning of existing device prompts; firmware wording is unchanged in this phase.

## Disconnection and network changes

1. Check Bridge, relay, device status and current host LAN IPv4 first.
2. If the address no longer matches the paired URL, restarting cannot fix certificates / device configuration; use USB pairing.
3. The pairing script opens USB and waits for stable hello before a brief confirm press on the device connection page opens the 60-second window.
4. Unplug USB only after a save receipt and confirmed Wi-Fi sync. A router DHCP reservation can help keep the address stable.
5. If USB termios or network sandbox permissions fail, retain the exact error and run in an authorized environment. Do not disable TLS checks or extend offline thresholds indefinitely.

On macOS, if `controller/private/runtime-migration.json` exists, menu 1 enters protected activation: quit the App manually, back up and precisely replace old Hook paths, stop the old service, then synchronize the latest ledger. The new path still requires manual review / trust. Do not run old and new Bridges together. Windows does not activate the old Mac account or pairing.

## Host tests

From repository root on macOS, using Bridge Python selected by `env.sh`:

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

TCP / Unix tests need local permissions. Sandbox rejection is not a business assertion failure; rerun in an authorized environment and preserve both outcomes. Set `COMPANION_BUILD_CACHE` for Swift caches if needed. C audio tests mock BSP / RTOS and do not establish physical speaker acceptance.

## Build and device maintenance

Firmware requires ESP-IDF 5.5.3. On macOS load its `export.sh`; `PASSPORT_DEPS` may identify existing locked offline components:

```sh
bash controller/scripts/build.sh
```

Building does not flash. macOS comprehensive image check `controller/scripts/check.sh` additionally needs `CONTROLLER_FLASH_PYTHON` with esptool 4.x. Bridge and flash interpreters are separate; dependencies are checked before stopping service.

On Windows, menu 7 → 1 builds using existing ESP-IDF / WSL; 7 → 2 validates the image against current source; 7 → 4 prepares isolated esptool 4.8.1; 7 → 3 requires typing `FLASH` before safe USB update. Original private emoji assets and a matching source fingerprint are mandatory. USB access remains on Windows.

Updates use menu 7 and the platform's existing protected path: tests / manifest checks, manual confirmation, Bridge stop, two complete matching backups, live partition checks, application-only write and readback verification, then reconnect the original App. Windows uses 256 KiB read blocks and bounded read-only retries; failed backups never trigger a write. If the device already reports the target version, do not reflash just to load a Bridge-only patch. The user confirmed the repaired Windows update and a basic visual check; no repeat flash is required. See [hardware and flashing](04-HARDWARE-AND-FLASH.en.md).

## Read-only reconciliation for a specific interval

The console defaults to the last hour. Explicitly pass the export path and time range:

```sh
source controller/scripts/env.sh
"$CONTROLLER_BRIDGE_PYTHON" controller/scripts/audit_usage.py \
  --provider-log /absolute/path/to/export.csv \
  --since '2026-11-01T00:00:00+11:00' \
  --until '2026-11-02T00:00:00+11:00'
```

On Windows use the same Python script / arguments with `controller/private/bridge-venv-windows/Scripts/python.exe` and a local absolute export path. Example dates illustrate timezone-bearing parameters, not a real billing period. Reconciliation does not change bills. Missing, incompletely read, truncated or rotated local records must report an incomplete scan.

## Environment and runtime evidence

An independent Homebrew Python 3.12 environment was recorded on macOS; Windows has its own private Python environment. Shell entries select Bridge Python through `CONTROLLER_BRIDGE_PYTHON`. A prepared receipt cannot replace an activation record.

`--restart-app` requires saving work and manually quitting the App. After launch, `private/active-python.json` records the selected interpreter. This receipt proves neither that every later patch loaded nor hardware acceptance. Tcl / Tk import checks do not cover all manual interactions in the rate editor.

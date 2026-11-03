# macOS / Windows host adaptation

[简体中文（默认）](11-HOST-PLATFORMS.md) · English

Updated 2026-11-03 (Australia/Sydney). Windows 10/11 host adaptation is authorized alongside retained macOS support. This neither migrates / replaces the Mac product nor deletes its entry, firmware or Swift Demo.

## Current Windows firmware maintenance

Menu 7 calls `scripts/firmware_update.py`: 1 build, 2 validate image, 3 safe USB update, 4 prepare isolated esptool 4.8.1. It reuses installed ESP-IDF or WSL ESP-IDF 5.5.3, while Windows always handles USB. There is no extra top-level launcher. Updates validate a locally built image against current source; they do not download a “latest firmware” from GitHub.

The original missing private `controller/firmware/main/pet_assets.h` blocker has been resolved: original assets were restored from the Mac private package, a source-bound 0.2.13 image was built, and after the block-read repair the user confirmed completing the Windows update and a basic visual check. Do not ask for repeat flashing. This is not full approval-matrix, Windows 10 or long-term stability acceptance.

For a future authorized update: 7 → 1 build, 7 → 2 validate, 7 → 4 prepare the flash environment if needed, 7 → 3 type `FLASH`. Missing assets / stale images are rejected before Bridge stops. The update reads two full matching backups, checks identity / live partitions, writes only the application and verifies it. Restore Bridge through menu 2. A data cable and exactly one target are required. Windows uses 256 KiB read blocks with bounded read-only retries and final ROM fallback; writes are not retried automatically.

## Platforms and acceptance boundaries

| Capability | macOS | Windows 10/11 |
|---|---|---|
| Daily entry | Retained `controller/Codex Companion 控制台.command` | Same-name `.cmd`, double-click |
| Python | Existing isolated environment and `env.sh` | Python 3.11+ / OpenSSL 3; isolated `private/bridge-venv-windows` |
| Private host communication | Unix socket, 0700 / 0600, flock | Random port on 127.0.0.1 only, per-launch random authentication, current-user DACL, Windows file lock |
| Desktop integration | Existing version / digest records retained | Separate registration of four launch-file digests for App 26.1027.30824 (MSIX 26.1027.3384.0) |
| Relay | Existing `.command` | Private generated native `.exe`, shared stdio relay and Broker |
| USB candidates | `/dev/cu.usbmodem*` retained | ESP32-C3 VID/PID 303A:1001; arbitrary COM selection rejected |
| Wi-Fi pairing, metering, rates, Hooks | Shared implementation | Shared, with Windows IP / OpenSSL discovery, Hook commands and file permissions |
| Archive / local migration | Existing functions retained | DACL and Windows preparation added; exclude Windows venv / machine relay; never copy auth.json |
| Firmware menu / ESP-IDF build | Existing safe path retained | Implemented with ESP-IDF / WSL and Windows COM safe updater; user-confirmed update / basic visual check, broader acceptance pending |
| Swift Demo | Existing macOS Demo retained | No Windows Demo; not part of hardware Bridge support |

Development environment: Windows 11 Pro / Python 3.12.10. Windows 10 is a target without recorded host execution. Windows CI does not replace Windows 10/11 hardware acceptance. macOS was not runnable in this round; old evidence is retained. Added cross-platform CI has no recorded successful run.

## Windows usage

Install Python 3.11+ including pip, venv and Tcl / Tk, then double-click `.cmd`. Preparation creates the local venv, checks fixed SHA-256 wheels from the repository and generates the relay. It does not download alternative firmware, start the App or perform device maintenance. Choose menu 1 explicitly to start App / Bridge.

Prepare or check only, from repository root:

```powershell
$env:PYTHONUTF8 = '1'
python controller/scripts/setup_windows.py --setup-only
python controller/scripts/setup_windows.py --check-only
& './controller/private/bridge-venv-windows/Scripts/python.exe' -m unittest discover -s controller/tests -v
& './controller/private/bridge-venv-windows/Scripts/python.exe' -m unittest discover -s tools -p 'test_*.py' -v
```

`.cmd` uses `python` by default; set `CONTROLLER_MODERN_PYTHON` to a full interpreter path for multiple installations. `CONTROLLER_OPENSSL` may point to an OpenSSL executable, otherwise discovered from PATH or Git for Windows. Python's TLS library and the OpenSSL command-line tool used by pairing are separate dependencies.

App discovery defaults to the current user's OpenAI.Codex MSIX package. `COMPANION_DESKTOP_APP` can specify the `app` directory containing `ChatGPT.exe` and `resources`; overridden paths still require exact version / digest checks. Unknown versions / changed files reject old adapters without modifying the package. Active App work is never closed automatically. Save work, quit completely, then launch from the console and open the original chat.

Windows Hooks invoke the current isolated interpreter through encoded PowerShell commands, preserving Chinese characters, spaces and quotes in paths. Installation / trust retain menu confirmation. No real Hooks were registered during the initial host adaptation. Windows does not run old Mac runtime activation; pairing IP, certificates and firewall reachability require checks for the actual host. Copied pairing does not prove this host can connect.

## Evidence and next steps

- Initial host inspection verified the App version and four launch-file digests and enumerated COM4 read-only. That inspection did not open serial or read device firmware. Later update evidence above is separate.
- Initial Controller tests: 265 run, 249 passed and 16 platform / permission skips. Tools: 19 run, 15 passed and 4 symlink skips. Real local transport tests cover first response wins, paginated Allow / Deny, cancellation and submitted receipts, using synthetic backend / device objects. They are not original-App / device acceptance.
- Initial full logs stay ignored in `controller/private/windows-host-tests-20261103.log` and `windows-tools-tests-20261103.log`; they are not published with source.
- Git Bash syntax checks passed for 35 macOS shell entries; this is neither macOS execution nor C / Swift build acceptance. Windows `.cmd --check-only` actually passed.
- Added cases cover Windows authentication, DACL rejection, single-instance locking, COM filtering, Hook stdin / quoted Chinese paths and native relay arguments / exit codes, including Chinese characters, spaces, quotes, trailing backslashes and shell metacharacters.
- The later safe-maintenance repair ran 274 Controller tests (16 skipped); the block-read repair ran 280 (16 skipped), followed by six local read regressions after adding inter-block `no_reset` assertions. These are prior results, not rerun by this Markdown phase.
- Initial host work did not restart App, start a real Bridge, flash, pair, reset counters, change accounts or register Hooks. Later user-confirmed Windows updating is recorded separately. Phase-one Markdown was subsequently committed / pushed. Phase-two host English was committed / pushed as `cc1bbfd`. Current phase-three 0.2.14 builds Chinese / English device variants by installation entry; see [device languages](13-DEVICE-LANGUAGES.en.md). See [host languages](12-HOST-LANGUAGES.en.md).
- Next, save work and use `.cmd` menu 1, confirm App physical approvals connected, then verify device / desktop Allow and Deny in the original chat. Separately add Windows 10, current macOS and sleep-reconnect evidence.

The [official App Server reference](https://learn.chatgpt.com/docs/app-server) describes stdio JSONL / approvals; the [Windows App reference](https://learn.chatgpt.com/docs/windows/windows-app) provides product environment information. Internal switches / local digests came from installed-file inspection. An official protocol's existence does not prove this original-App integration passed hardware acceptance. This phase does not revalidate those external references.

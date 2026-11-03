# Architecture and source navigation

[简体中文（默认）](02-ARCHITECTURE.md) · English

```text
Codex desktop App ↔ stdio relay ↔ official Codex App Server
                         ↕ private host IPC
                  macOS / Windows Bridge
                         ↕ HTTPS / Wi-Fi (or PC1 JSONL USB)
                  AI Passport ESP32-C3
```

App integration uses internal launch switches from the installed version, not stable public settings. The protocol layer uses official App Server requests / notifications. Modifying the installed App, automatically clicking its GUI or disabling version checks cannot establish support.

## Host source

The Python modules below are shared by macOS and Windows. Platform differences are concentrated in `bridge/host_platform.py`, `bridge/ipc_path.py`, `bridge/windows_security.py` and `bridge/private_permissions.py`. Windows follows `.cmd` → `scripts/setup_windows.py` → shared `controller_console.py`; the App follows private generated `app-relay.exe` → `scripts/app_relay.py` → shared `stdio_relay.py`. macOS retains `.command` and Unix IPC. See [platform details and pending acceptance](11-HOST-PLATFORMS.en.md).

- `controller/scripts/controller_console.py`: shared menu; `Codex Companion 控制台.command` and same-name `.cmd` are the current daily entries. Separate English `Codex Companion Console.command` / `Codex Companion Console.cmd` entries now pass `COMPANION_LANGUAGE`. Host translation uses `bridge/console_i18n.py` and `locale_en.json` without generically translating device payloads. Phase three uses `bridge/device_i18n.py` to mark / render system text in the installed language declared by firmware hello, preserving user content; see [device languages](13-DEVICE-LANGUAGES.en.md).
- `scripts/launch_desktop.py`: exact App version / digest checks, environment and relay launch, Bridge lifecycle.
- `scripts/app_relay.command` + `bridge/stdio_relay.py`: transparent JSONL forwarding, device / original-App approval race and a single submission receipt.
- `bridge/service.py`: Broker state, request / event management, device snapshots, account / numeric updates and private IPC.
- Retired historical module: `bridge/native_app_ui.py` activated the original App via `mac_handoff`. v0.2.13 deletes it, service loading / calls, Hook handoff release and `mac_ready` fields. Old messages have no effect; historical code is in Git `v0.2.12`. Dual-side approvals use native cards and stdio relay directly, without device handoff. `mac_approval_gui.py` is a retired no-op compatibility entry, not loaded by current service; the independently displayed popup was explicitly rejected and must not be restored.
- `bridge/ipc_path.py`: root-dependent short Unix sockets / locks on macOS and authenticated loopback endpoints / locks on Windows. Migration changes the endpoint.
- `bridge/wireless.py`: paired HTTPS, certificate verification and fixed device receive limits.
- `bridge/usb_transport.py`: sets DTR / RTS before serial open and normalizes macOS termios errors.
- `scripts/pair_wifi.py`: opens USB, waits for stable hello, then requires physical permission for a 60-second pairing window.
- `bridge/approval_review.py`, `hook_policy.py`: readable details / pagination and permission-scope assessment.
- `bridge/usage_meter.py`: numeric validation, ledger, deduplication, per-request dual tiers, category estimates and rates.
- `bridge/response_usage.py`: incremental reads of completed local records, including compaction; supplemental local format, not a stable billing API.
- `bridge/provider_billing.py`: private CSV / TSV reconciliation and missing-request supplements only when uniquely attributable.
- `bridge/token_rates_gui.py`: local GUI rate settings; `scripts/audit_usage.py` provides read-only auditing.
- `scripts/flash.py`: backups, live partition checks, factory write and readback verification. `scripts/firmware_update.py` connects the Windows menu to build, image validation and safe update.

## Firmware and Demo

- `controller/firmware/main/controller.c/.h`: three-button state machine and request / confirmation flow.
- `ui_language.c/.h`: installed default and 126 static messages, compiled from the selected entry rather than switching with PC language at runtime.
- `main.c`: display, snapshot decoding and prompts; `network.c`: Wi-Fi / HTTPS / pairing.
- `sound.c`, `sound_model.c`: nonblocking audio scheduling; `battery.c`: battery state.
- `firmware/components/bsp/`: display, ADC buttons, audio, I2C and battery drivers.
- `mac-demo/`: independent SwiftUI / AppKit interaction simulation, distinct from real-device functionality.

## Connection and security model

Requests bind a unique ID, digest, epoch / boot, expiry and page state. Offline, cancelled, expired, superseded or unacknowledged submissions cannot display granted permission. Marking a notice read is neither answering nor authorizing it. HTTPS certificates / device pairing tokens are unrelated to Codex login; the device never stores Codex credentials.

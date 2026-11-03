# Device language follows the installation entry

[简体中文（默认）](13-DEVICE-LANGUAGES.md) · English

Source: firmware `0.2.14`, Bridge `0.2.14-native-app`. Updated 2026-11-03 (Australia/Sydney). This is phase-three firmware and accompanying work; source, build, installation and hardware acceptance are recorded separately.

## Language after installation

| Installation entry | Built / installed device language |
|---|---|
| `Codex Companion 控制台.command` / `Codex Companion 控制台.cmd` | Chinese, default |
| `Codex Companion Console.command` / `Codex Companion Console.cmd` | English |

Language is compiled into firmware. A device installed through the English entry is English from startup, while offline, before pairing and after reboot. A Chinese-entry installation is Chinese. Later running a different-language PC console does not change the installed device language. Changing device language requires rebuilding through the corresponding entry and installing with the same safe updater; there is no automatic runtime switch or extra button combination.

Build selection is `-DCOMPANION_FIRMWARE_LANGUAGE=en` or `-DCOMPANION_FIRMWARE_LANGUAGE=zh-CN`; fresh direct builds default to Chinese if unspecified; pass language explicitly when reusing a CMake cache. Official entries always do so. Both variants retain original Apple assets and existing three-button interaction, without generating / replacing emoji.

## Update through the desired language entry

Save work, connect exactly one USB target, then open the desired language entry. Windows and macOS share menu 7 submenus:

1. 7 → 1 builds firmware in that entry's language using existing ESP-IDF 5.5.3 (WSL may be reused on Windows) and private original assets.
2. 7 → 2 checks version, chip, size, SHA-256, current-source fingerprint, artwork flag and device language.
3. If needed, 7 → 4 prepares Windows esptool 4.8.1; on macOS it explains `CONTROLLER_FLASH_PYTHON` requirements.
4. 7 → 3 starts safe updating. Windows still requires `FLASH`; macOS retains existing manual confirmation. Bridge is not stopped before confirmation; never upgrade with approvals pending.
5. Follow prompts to restore Bridge and verify the device in the original App chat. Image checks / host previews do not establish hardware functionality.

Updating retains two full 8 MB reads, identity / live-partition checks, factory-application-only writing and readback verification. No bootloader, partition-table or existing NVS write, whole-chip erase, automatic write retry, re-pairing, ledger reset or account change. macOS continues calling its existing safe maintenance script rather than switching to Windows COM behavior.

## Prevent installing the wrong language

An image contains exactly one `COMPANION_UI_LANGUAGE=en` or `COMPANION_UI_LANGUAGE=zh-CN` marker. Manifest `ui_language` comes from the image, not just the PC environment. Missing / ambiguous markers, image / manifest disagreement or a language different from the selected entry reject installation early and require rebuilding from the correct entry.

Local `controller/dist/en/` and `controller/dist/zh-CN/` retain both image / manifest variants; historical `controller/dist/PassportController.bin` remains the active update image. If the last build was the other language, rebuild through the desired entry first. The updater neither silently flashes the other language nor downloads a GitHub image. Old `0.2.13` images lack the new source / language binding.

Artwork-containing images, assets, Flash backups and preview screenshots stay local and cannot be committed / publicly distributed.

## Bridge and approval content

New firmware hello declares `ui_language_protocol=1` and `ui_language`. Bridge uses the installed language for device state, approval titles / scopes / pages, question notices, history, metering / account status and genuine submission receipts; the PC interface language does not override it. Old firmware / invalid capabilities remain Chinese. Changed language declarations within the same boot are ignored so an active review cannot change language halfway through. Reboots still end old requests under existing boot / epoch rules.

USB / network transmit buffers are bounded at 768 bytes to fit language declarations and large diagnostic counters; the maximum hello frame is checked. Approval-detail receive capacity remains 4096 bytes.

Only explicitly marked system text is translated. User questions, reasons, commands, paths, custom model names and unknown field values remain original; no model translation / summarization. Original digests, permission results, delivered-page checks, second confirmation, release-then-hold submission, first response wins and submitted receipts remain unchanged. Unknown semantics, missing diffs or additional grants still cannot be approved on the device.

On the 240×320 layout, English system labels use existing Montserrat fonts; Chinese user content retains the existing Source Han Sans subset. Conservative 13-character × 7-line pagination preserves every character. Longer dynamic information uses existing page bounds. Tool return does not become task success, and marking a notice read does not answer it.

## Verification and uncovered scope

Regressions check entry language / image markers, legacy compatibility, device language independent of PC, same-boot stability, original-data preservation and delivered English-page submission guards. C host checks cover both compiled defaults and the same three-button approval flow. Audio still uses mocked BSP / RTOS.

`controller/tools/preview_firmware.py` renders the actual `render()`, locked LVGL and real fonts offline with mocked hardware. `--private-artwork` reads only local original assets. Previews stay ignored in `controller/private/ui-preview/`, without device / network access. This run rendered 40 Chinese / English screens with zero label overlap / out-of-bounds findings. This is not real ESP32 display, speaker or endurance acceptance.

This phase does not flash for the user, start / restart real App / Bridge, pair, reset or change accounts. Real Chinese / English screens, complete dual-side Allow / Deny, reboot / offline language, pairing prompts, all permissions and long-term stability await installed-device testing; native macOS execution also needs its own record.

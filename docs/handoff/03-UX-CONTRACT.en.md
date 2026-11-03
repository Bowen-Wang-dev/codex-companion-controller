# Interaction contract

[简体中文（默认）](03-UX-CONTRACT.md) · English

## Fixed emoji

| State | Original Apple emoji |
|---|---|
| Idle | 😋 |
| Thinking / working | 🤔 |
| Approval requested | 🥺 |
| Interaction / brief feedback after confirmed approval | 😆 |
| Quota exhausted | 😐🤲 |
| Permission denied / task failed | 😭 |
| Turn completed | 🥳 |

Denial goes directly to 😭, never 😶 or 😶→😭. Approval feedback waits for a real relay submission receipt; pressing a button alone cannot show success. Completion feedback lasts roughly three seconds before returning to idle, rather than indefinitely showing a completed turn. After feedback, restore 🤔 if the original App is working, otherwise 😋.

## Three buttons

- Browsing pages without selection: short or long direction presses change pages.
- Settings / event pages with selection: short presses move selection; long presses move to the previous / next main page.
- Long-request details: short up / down changes detail pages; long up jumps to the first page and long down to the last.
- Only the final page allows short up / down to choose allow / deny, with no default. Short confirm opens the second confirmation.
- Second confirmation: release first, then hold confirm again for about one second to submit. Long up / down returns to first / last details and cancels the confirmation choice.
- v0.2.13 contract: display and operation on both sides. The same request appears on the device and the native approval card in the original ChatGPT / Codex App chat. After the device alert, use either the device buttons or desktop allow / deny directly. No preliminary handoff. The first response wins and clears the other side. Final-page selection, second confirmation and real submission receipts remain mandatory on the device.
- Retired, preserved as history: holding confirm in details handed the request to Mac and activated the original App. It existed in 0.2.12 and passed hardware case 5. Preserve history and evidence; do not deploy it as a current feature.
- v0.2.13 source removes firmware / Bridge handoff, recall and window-display receipts. The device only states that details can be viewed on the host: direct desktop review / action, no handoff command, hold requirement or extra confirmation. Holding confirm on the second confirmation page remains exclusively for submitting the device decision and must not be deleted with handoff.
- In v0.2.13, holding confirm in details does nothing; release does not become a short press. Hold-to-submit on second confirmation and long-confirm return to pending approvals from ordinary pages remain. Later logs report firmware 0.2.13, but complete interaction acceptance needs its own record. The review did not flash or restart Bridge and added no hardware conclusion. Old code remains at Git `v0.2.12` (`fb02632`).
- On 2026-11-02 the user explicitly rejected a separate Tk / Companion approval window. Native mode was switched and five real dual-side cases individually confirmed. Case 5 remains historical handoff evidence, not a current requirement. Firmware 0.2.12 remains usable.
- Reset: a short press only opens a separate confirmation; release, then hold again. A single touch must not reset counters.
- The three buttons share an ADC resistor ladder; simultaneous up + down must not be required. Power is not a fourth application button.

## Long requests and reminders

Preserve actual paths, commands, reasons, directories, scopes and necessary permission information. Do not send only JSON, one screen of punctuation, or shorten away authorization scope to save pages. No model call is needed to summarize. Insufficient information / unsupported semantics must explicitly require desktop review rather than pretend hardware support.

Permissions take priority and open automatically. Pager-style alert: three roughly 1200 Hz tones, 180 ms each, 120 ms gaps; one immediate sequence, repeat after 30 seconds by default, at most three extra sequences, with mute available. Audio must not block networking / buttons or accumulate without limit. Volume: 0–100%, in 10% steps.

## Screen and appearance

240×320, no touch; host-synchronized time and battery at top right. No SIM / cellular; remove misleading SIM wording. Main-page dots share a common vertical position.

Original Apple images must not be AI-generated, redrawn or replaced with Noto / Twemoji / other platform artwork. Compose 😐 and 🤲 from their separate originals. Public source excludes Apple assets and firmware containing them. Phase-three 0.2.14 compiles device language from its installation entry: English installs English startup / offline text; Chinese installs Chinese. Later PC console language does not change the device. Buttons, emoji, full content and real submitted receipts remain; see [device languages](13-DEVICE-LANGUAGES.en.md). This round did not flash or add hardware acceptance.

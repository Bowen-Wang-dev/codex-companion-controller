# Frequently asked questions

[简体中文（默认）](10-QUICK-FAQ.md) · English

**The device is online; why are approvals missing?** Device sync, Hooks and App relay are different links. Check the verified App launcher, original-chat integration and whether the request type is supported.

**Can restarting Bridge recover an already running App?** Only if that App was launched through the relay. For an ordinary App launch, save work, quit manually, then use the existing console.

**Can we use a fourth application button or up / down combinations?** Interaction relies on three buttons. Direction buttons share an ADC ladder; combinations must not be necessary.

**What if model, rate or request boundaries are missing?** Report unknown / pending explicitly. Do not guess models, infer individual request prices from accumulated usage or replace missing data with 0. Existing CSV reasoning zeros are a documented adapter limitation.

**How do input, cache, output and reasoning add up?** API input includes cache; output includes reasoning. Display five disjoint categories: uncached input, cache read, cache write, visible output and reasoning, counted once each.

**Does exceeding the total-token threshold trigger the long tier?** No. Use the price card's per-request input threshold, including cache, then aggregate requests. Built-in thresholds / prices are snapshots.

**Does Git contain complete recovery material?** No. Pairing, private keys, ledgers, Apple images, firmware containing artwork and device backups stay local; toolchains require separate setup.

**Can old caches be reused directly after migration?** Do not copy old venvs, absolute-path `.pth` files or CMake caches directly. Hook paths and IPC endpoints change with project paths; follow migration checks and retain rollback material.

**Does marking a reminder read mean allowing or replying?** No. Reading a notice, answering, submitting authorization and tool execution are distinct events.

**Does a source version prove the device updated or a patch loaded?** No. Record source, image, later runtime logs, loaded code and hardware acceptance separately.

**Is Windows firmware maintenance still unavailable?** It is now implemented. Menu 7 provides build / image validation / safe USB update / isolated flash setup. Private assets were restored and the user confirmed completing the repaired update and a basic visual check. Complete functionality, Windows 10 and long-term stability still need separate evidence.

**Does English Markdown mean the console and device are English?** No. Phase one is documentation only. Separate Chinese / English `.command` / `.cmd` consoles are phase two; firmware and other localization are phase three. Current entries remain Chinese until their own implementation and checks are committed.

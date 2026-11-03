# Mac Demo

[简体中文（默认）](README.md) · English

SwiftUI / AppKit Demo `0.4.0`, macOS 14+, Swift 6. See the [project README](../README.en.md).

From `mac-demo/`:

```sh
./test.sh
./build.sh
open "Codex Companion.app"
```

Use ↑ / ↓ / Return as the device's three buttons. Short direction presses select items on selection pages; long presses change pages. Approval requires selection, short confirm, release, then a new one-second hold. The side panel injects local simulated events.

Tasks, permissions, usage and resets are simulated; the Demo does not control a real Codex session. HTTPS clock calibration is a real request but never changes system time. Emoji use the system Apple font; no Apple images or font files are included. Historical Demo sound defaults may differ from later device firmware.

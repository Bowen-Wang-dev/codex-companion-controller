# Mac demo / Mac 演示

SwiftUI / AppKit demo 0.4.0, macOS 14+, Swift 6. See the [bilingual project README](../README.md).

```sh
./test.sh
./build.sh
open "Codex Companion.app"
```

Use ↑ / ↓ / Return as the device's three keys. Short direction presses select items on selection pages; long presses change pages. Approval requires selection, a short confirmation, release, and a new one-second hold. The side panel injects local simulated events.

使用 ↑／↓／Return 模拟三键。选择页面短按方向键选择、长按换页；审批需要选择、短按确认、松开、重新长按一秒。侧栏用于注入本地模拟事件。

Tasks, permissions, usage and resets are simulated; the demo does not control a real Codex session. HTTPS clock calibration is real but never changes system time. Emoji are rendered by the system Apple font; no Apple images or font files are included. The demo's historical sound defaults may differ from the later device firmware.

任务、权限、额度与重置都是模拟数据，不控制真实 Codex。HTTPS 校时真实发起，不修改系统时间。Emoji 使用系统 Apple 字体，不打包 Apple 图像或字体。Demo 的早期音量默认值与后来的设备固件可能不同。

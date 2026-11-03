# Mac 演示

简体中文（默认） · [English](README.en.md)

SwiftUI / AppKit Demo `0.4.0`，macOS 14+，Swift 6。见[项目 README](../README.md)。

在 `mac-demo/` 内执行：

```sh
./test.sh
./build.sh
open "Codex Companion.app"
```

用 ↑／↓／Return 模拟设备三键。选择页面短按方向键选择、长按换页；审批需要选择、短按确认、松开、重新长按一秒。侧栏注入本地模拟事件。

任务、权限、额度与重置都是模拟数据，不控制真实 Codex 会话。HTTPS 校时真实发起请求，但不修改系统时间。Emoji 使用系统 Apple 字体，不打包 Apple 图像或字体。Demo 历史声音默认值可能与后来的设备固件不同。

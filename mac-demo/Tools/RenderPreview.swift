import AppKit
import SwiftUI
import CompanionCore

// Renders this project's view hierarchy in a hidden window. No screen capture,
// accessibility permissions, global keyboard hooks, or other applications.
@main struct RenderPreview {
    @MainActor static func main() throws {
        _ = NSApplication.shared
        NSApp.setActivationPolicy(.prohibited)
        let arguments = CommandLine.arguments
        guard arguments.count >= 3 else { print("RenderPreview <mode> <output.png>"); return }
        let store = DemoStore()
        let now = store.timestamp
        store.clockAnchor = ClockAnchor(utc: Date(), uptime: now, source: "离屏预览", uncertainty: 1)
        store.clockMessage = "校时状态预览（示例）"
        switch arguments[1] {
        case "approval": _ = store.state.receive(Approval(deadline: now + 120), now: now)
        case "confirm":
            _ = store.state.receive(Approval(deadline: now + 120), now: now)
            store.state.choose(.deny); store.state.confirm(); store.holdProgress = 0.63
        case "denied":
            _ = store.state.receive(Approval(deadline: now + 120), now: now)
            store.state.choose(.deny); store.state.confirm()
            if let attempt = store.state.submit(heldFor: 1, now: now) { _ = store.state.acknowledge(attempt, now: now) }
        case "quota": store.page = 1
        case "reset-entry": store.page = 2
        case "failed": _ = store.state.setRun(.failed, now: now)
        case "exhausted":
            _ = store.state.setRun(.exhausted, now: now); store.primaryRemaining = 0; store.secondaryRemaining = 0
        case "low": store.primaryRemaining = 12; store.secondaryRemaining = 7
        case "menu": store.navigation.openMenu()
        case "settings": store.page = 3
        case "history":
            _ = store.state.setRun(.working, now: now)
            _ = store.state.setRun(.completed, now: now)
            _ = store.state.setRun(.idle, now: now)
            store.page = 4
        case "request-away":
            _ = store.state.receive(Approval(deadline: now + 120), now: now)
            store.navigation.longMove(1, context: .choosing, hasRequest: true)
        case "request-away-menu":
            _ = store.state.receive(Approval(deadline: now + 120), now: now)
            store.navigation.longMove(1, context: .choosing, hasRequest: true)
            store.navigation.openMenu()
        case "network": store.page = 5
        case "network-pairing": store.page = 5; store.wifi = .provisioning
        case "unsynced": store.clockAnchor = nil; store.clockMessage = "未校时 · 网络不可用"
        case "empty-resets":
            for _ in 0..<2 {
                store.state.openReset(); store.state.confirmReset()
                _ = store.state.submitReset(heldFor: 1, now: now)
            }
            store.page = 2; _ = store.state.setRun(.exhausted, now: now)
            store.primaryRemaining = 0; store.secondaryRemaining = 0
        case "details":
            _ = store.state.receive(Approval(deadline: now + 120), now: now)
            store.navigation.openMenu()
            _ = store.navigation.shortOK(context: .choosing, hasRequest: true, hasSelection: false)
        case "request-menu":
            _ = store.state.receive(Approval(deadline: now + 120), now: now)
            store.navigation.openMenu()
        case "reset": store.state.openReset(); store.state.confirmReset(); store.holdProgress = 0.4
        case "maconly": _ = store.state.receive(Approval(operation: "curl https://example.invalid/deploy.sh | sh -- --production --delete-existing-data", scope: "网络访问 + 执行远程脚本 · 高风险", deadline: now + 120, macOnly: true), now: now)
        default: break
        }
        let size = NSSize(width: 1020, height: 820)
        let view = NSHostingView(rootView: Dashboard(store: store).preferredColorScheme(.dark).frame(width: size.width, height: size.height))
        let window = NSWindow(contentRect: NSRect(origin: .zero, size: size), styleMask: [.borderless], backing: .buffered, defer: false)
        window.contentView = view
        view.frame = NSRect(origin: .zero, size: size)
        window.displayIfNeeded(); view.layoutSubtreeIfNeeded()
        RunLoop.current.run(until: Date().addingTimeInterval(0.2))
        guard let bitmap = view.bitmapImageRepForCachingDisplay(in: view.bounds) else { throw NSError(domain: "Preview", code: 1) }
        view.cacheDisplay(in: view.bounds, to: bitmap)
        guard let png = bitmap.representation(using: .png, properties: [:]) else { throw NSError(domain: "Preview", code: 2) }
        try png.write(to: URL(fileURLWithPath: arguments[2]))
        print("Rendered \(arguments[1]) → \(arguments[2])")
    }
}

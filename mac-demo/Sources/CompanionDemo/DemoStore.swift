import AppKit
import SwiftUI
import CompanionCore

enum WiFiDemoState { case unconfigured, provisioning, joining, connected }

@MainActor final class DemoStore: ObservableObject {
    @Published var state = ControllerState()
    @Published var now = Date()
    @Published var clockAnchor: ClockAnchor?
    @Published var clockSyncing = false
    @Published var clockMessage = "未校时"
    @Published var wifi: WiFiDemoState = .unconfigured
    @Published var navigation = DeviceNavigation()
    var page: Int {
        get { navigation.page.rawValue }
        set { navigation.page = DevicePage(rawValue: newValue) ?? .home }
    }
    @Published var holdProgress: Double = 0
    @Published var volume: Double = 18 { didSet { audio.volume = Float(volume / 100) } }
    @Published var soundEnabled = true { didSet { state.soundEnabled = soundEnabled; audio.enabled = soundEnabled; if !soundEnabled { audio.stop() } } }
    @Published var interval: Double = 30 { didSet { state.setReminderInterval(interval, now: timestamp) } }
    @Published var touchSound = false
    @Published var simulateLostReceipt = false
    @Published var primaryRemaining = 64
    @Published var secondaryRemaining = 38
    private var primaryResetDue = ProcessInfo.processInfo.systemUptime + 2 * 3600 + 14 * 60
    private var secondaryResetDue = ProcessInfo.processInfo.systemUptime + 4 * 86400 + 3 * 3600
    var primaryReset: Date { now.addingTimeInterval(primaryResetDue - timestamp) }
    var secondaryReset: Date { now.addingTimeInterval(secondaryResetDue - timestamp) }
    var quotaDepleted: Bool { primaryRemaining == 0 || secondaryRemaining == 0 }
    var relevantReset: Date {
        var depleted: [TimeInterval] = []
        if primaryRemaining == 0 { depleted.append(primaryResetDue) }
        if secondaryRemaining == 0 { depleted.append(secondaryResetDue) }
        let due = depleted.max() ?? min(primaryResetDue, secondaryResetDue)
        return now.addingTimeInterval(due - timestamp)
    }
    let audio = AudioEngine()
    private var timer: Timer?
    private var downMonitor: Any?
    private var upMonitor: Any?
    private var observer: NSObjectProtocol?
    private var returnDown = false
    private var heldFrom: TimeInterval?
    private var heldRequest: UUID?
    private var heldChoice: Choice?
    private var holdingReset = false
    private var holdingMenu = false
    private var submittedThisPress = false
    private var previousHover: TimeInterval = 0
    private var lastClockAttempt = -Double.infinity
    private var wifiAttempt = UUID()
    private var directionPress = DirectionalPress()
    private var directionRoute = ""
    // Expiry, reminders and holds use monotonic time, independent of calibration.
    var timestamp: TimeInterval { ProcessInfo.processInfo.systemUptime }
    var requestVisible: Bool { state.pending != nil && navigation.requestVisible }
    var inputContext: InputContext {
        if requestVisible {
            switch state.stage {
            case .choosing: return .choosing
            case .confirming: return .confirming
            case .sending, .uncertain: return .waiting
            }
        }
        if state.resetPage { return .resetConfirmation }
        return navigation.page == .home && quotaDepleted ? .exhausted : .normal
    }
    private var inputRoute: String {
        "\(page)|\(navigation.panel)|\(navigation.requestVisible)|\(state.pending?.id.uuidString ?? "")|\(state.stage)|\(state.selected?.rawValue ?? "")|\(state.resetPage)|\(state.resetConfirmed)|\(state.connected)"
    }
    var detailPages: [(String, String)] {
        guard let request = state.pending else { return [] }
        let characters = Array(request.operation)
        var pages: [(String, String)] = []
        for start in stride(from: 0, to: characters.count, by: 120) {
            pages.append(("命令 · \(pages.count + 1)", String(characters[start..<min(start + 120, characters.count)])))
        }
        pages.append(("工作目录", request.project))
        pages.append(("权限范围", request.scope))
        pages.append(("请求身份", "类型：命令执行\n\n\(request.id.uuidString)"))
        return pages
    }

    func start() {
        guard timer == nil else { return }
        downMonitor = NSEvent.addLocalMonitorForEvents(matching: .keyDown) { [weak self] event in
            guard let self, NSApp.keyWindow != nil, !event.modifierFlags.contains(.command) else { return event }
            return self.keyDown(event) ? nil : event
        }
        upMonitor = NSEvent.addLocalMonitorForEvents(matching: .keyUp) { [weak self] event in
            guard let self else { return event }
            switch event.keyCode {
            case 126: self.releaseDirection(-1); return nil
            case 125: self.releaseDirection(1); return nil
            case 36, 76: self.releaseReturn(); return nil
            default: return event
            }
        }
        observer = NotificationCenter.default.addObserver(forName: NSApplication.didResignActiveNotification, object: nil, queue: .main) { [weak self] _ in
            MainActor.assumeIsolated {
                self?.releaseReturn(cancel: true)
                self?.directionPress.reset()
            }
        }
        timer = Timer.scheduledTimer(withTimeInterval: 0.025, repeats: true) { [weak self] _ in
            MainActor.assumeIsolated { self?.tick() }
        }
        if let timer { RunLoop.main.add(timer, forMode: .common) }
        synchronizeClock()
    }

    func synchronizeClock() {
        guard !clockSyncing else { return }
        clockSyncing = true; clockMessage = "联网校时中"; lastClockAttempt = timestamp
        Task {
            do {
                let sample = try await NetworkTimeClient.read()
                clockAnchor = sample; now = sample.date(at: timestamp)
                clockMessage = "已联网校时"
            } catch {
                clockMessage = clockAnchor == nil ? "未校时 · 网络不可用" : "离线 · 保持计时"
            }
            clockSyncing = false
        }
    }

    private func tick() {
        now = clockAnchor?.date(at: timestamp) ?? Date()
        if timestamp - lastClockAttempt > (clockAnchor == nil ? 60 : 600) { synchronizeClock() }
        if timestamp >= primaryResetDue { primaryRemaining = 100; primaryResetDue = timestamp + 5 * 3600 }
        if timestamp >= secondaryResetDue { secondaryRemaining = 100; secondaryResetDue = timestamp + 7 * 86400 }
        if state.run == .exhausted && !quotaDepleted { _ = state.setRun(.idle, now: timestamp) }
        let oldID = state.pending?.id
        play(state.tick(now: timestamp))
        if state.pending?.id != oldID {
            releaseReturn(cancel: true); directionPress.cancelUntilRelease()
            if state.pending != nil { navigation.presentRequest() } else { navigation.dismiss() }
        }
        if directionRoute != inputRoute || !NSApp.isActive { directionPress.cancelUntilRelease() }
        if let gesture = directionPress.tick(at: timestamp) { handleDirection(gesture) }
        if let start = heldFrom {
            let valid = holdingMenu ? state.pending?.id == heldRequest : holdingReset ? state.resetPage && state.resetConfirmed && state.pending == nil : state.pending?.id == heldRequest && state.selected == heldChoice && state.stage == .confirming
            guard valid, holdingMenu || state.connected, NSApp.isActive else { releaseReturn(cancel: true); return }
            let threshold = holdingMenu ? 0.65 : 1.0
            holdProgress = min(1, (ProcessInfo.processInfo.systemUptime - start) / threshold)
            if holdProgress >= 1 && !submittedThisPress {
                submittedThisPress = true
                if holdingMenu {
                    if state.resetPage { state.back() }
                    navigation.openMenu(); state.clearSelection()
                } else if holdingReset {
                    if state.submitReset(heldFor: 1, now: timestamp) {
                        primaryRemaining = 100; secondaryRemaining = 100
                        primaryResetDue = timestamp + 5 * 3600; secondaryResetDue = timestamp + 7 * 86400
                        play(.allowed)
                    }
                } else if let attempt = state.submit(heldFor: 1, now: timestamp) {
                    if !simulateLostReceipt {
                        DispatchQueue.main.asyncAfter(deadline: .now() + 0.65) { [weak self] in
                            guard let self else { return }
                            let sound = self.state.acknowledge(attempt, now: self.timestamp)
                            if sound != nil { self.navigation.dismiss() }
                            self.play(sound)
                        }
                    }
                }
                heldFrom = nil; holdProgress = 0
            }
        }
    }

    private func keyDown(_ event: NSEvent) -> Bool {
        switch event.keyCode {
        case 126: if !event.isARepeat { pressDirection(-1) }; return true
        case 125: if !event.isARepeat { pressDirection(1) }; return true
        case 36, 76:
            if !event.isARepeat { pressReturn() }; return true
        default: break
        }
        return false
    }

    func pressReturn() {
        guard !returnDown else { return }
        directionPress.cancelUntilRelease()
        returnDown = true; submittedThisPress = false
        if navigation.panel == .none && state.stage == .confirming && requestVisible {
            heldFrom = ProcessInfo.processInfo.systemUptime; heldRequest = state.pending?.id
            heldChoice = state.selected; holdingReset = false
        } else if navigation.panel == .none && state.resetPage && state.resetConfirmed {
            heldFrom = ProcessInfo.processInfo.systemUptime; holdingReset = true
        } else {
            heldFrom = ProcessInfo.processInfo.systemUptime; holdingMenu = true
            heldRequest = state.pending?.id
        }
    }

    func releaseReturn(cancel: Bool = false) {
        guard returnDown else { resetHold(); return }
        let wasHolding = heldFrom != nil
        let shortPressCanAct = holdingMenu
        let wasSubmitted = submittedThisPress
        returnDown = false; resetHold()
        guard !cancel, !wasSubmitted, !wasHolding || shortPressCanAct else { return }
        perform(navigation.shortOK(context: inputContext, hasRequest: state.pending != nil, hasSelection: state.selected != nil))
    }

    func resetHold() { heldFrom = nil; heldRequest = nil; heldChoice = nil; holdingReset = false; holdingMenu = false; holdProgress = 0 }
    func move(_ direction: Int) {
        releaseReturn(cancel: true)
        perform(navigation.move(direction, context: inputContext, hasRequest: state.pending != nil, detailCount: detailPages.count, historyCount: state.log.count))
    }
    func up() { move(-1) }
    func down() { move(1) }

    func pressDirection(_ direction: Int) {
        guard NSApp.isActive else { return }
        guard directionPress.press(direction, at: timestamp) else { return }
        releaseReturn(cancel: true)
        directionRoute = inputRoute
    }

    func releaseDirection(_ direction: Int) {
        if directionRoute != inputRoute || !NSApp.isActive { directionPress.cancelUntilRelease() }
        if let gesture = directionPress.release(direction, at: timestamp) { handleDirection(gesture) }
    }

    private func handleDirection(_ gesture: DirectionGesture) {
        switch gesture {
        case .short(let direction): move(direction)
        case .long(let direction):
            releaseReturn(cancel: true)
            let context = inputContext
            state.back(); state.clearSelection()
            navigation.longMove(direction, context: context, hasRequest: state.pending != nil)
        }
    }

    func returnToRequest() {
        releaseReturn(cancel: true); directionPress.cancelUntilRelease()
        state.back(); state.clearSelection(); navigation.presentRequest()
    }
    private func perform(_ action: DeviceAction) {
        switch action {
        case .none: break
        case .allow: state.choose(.allow)
        case .deny: state.choose(.deny)
        case .confirmApproval: state.confirm()
        case .back: state.back()
        case .mute: mute()
        case .touch: touch()
        case .openReset: state.openReset()
        case .confirmReset: state.confirmReset()
        case .toggleSound: soundEnabled.toggle()
        case .cycleVolume: volume = [0.0, 10, 20, 30, 40, 50, 60].first(where: { $0 > volume }) ?? 0
        case .cycleInterval: interval = [10.0, 20, 30, 60, 90, 120].first(where: { $0 > interval }) ?? 10
        case .toggleTouchSound: touchSound.toggle()
        case .configureWiFi: configureWiFi()
        }
    }
    func choose(_ value: Choice) { resetHold(); state.choose(value) }
    func confirm() { resetHold(); state.confirm() }
    func back() { resetHold(); state.back() }
    func mute() { state.muteRequest(); audio.stop() }
    func play(_ sound: Sound?) { if let sound { audio.play(sound) } }
    func touch() { let sound = state.touch(now: timestamp); if touchSound { play(sound) } }
    func hover() { if timestamp - previousHover > 2 { previousHover = timestamp; touch() } }

    func scenario(_ run: RunState) {
        directionPress.cancelUntilRelease()
        releaseReturn(cancel: true); navigation.dismiss(); page = 0
        play(state.setRun(run, now: timestamp))
        if run == .exhausted { primaryRemaining = 0; secondaryRemaining = 0 }
        else if run == .idle || run == .working {
            if primaryRemaining == 0 { primaryRemaining = 64 }
            if secondaryRemaining == 0 { secondaryRemaining = 38 }
        }
    }
    func request(long: Bool = false, seconds: Double = 120) {
        directionPress.cancelUntilRelease()
        releaseReturn(cancel: true)
        let hadRequest = state.pending != nil
        _ = state.setRun(.working, now: timestamp)
        let approval = Approval(operation: long ? "curl https://example.invalid/deploy.sh | sh -- --production --delete-existing-data --grant-network-access" : "git status --short", scope: long ? "网络访问 + 执行远程脚本 · 高风险" : "仅本次 · 读取项目文件", deadline: timestamp + seconds, macOnly: long)
        play(state.receive(approval, now: timestamp))
        if !hadRequest { navigation.presentRequest() }
    }
    func duplicate() { if let request = state.pending { play(state.receive(request, now: timestamp)) } }
    func cancel() { releaseReturn(cancel: true); navigation.dismiss(); if let request = state.pending { state.cancel(id: request.id, now: timestamp); audio.stop() } }
    func connection() { resetHold(); play(state.setConnected(!state.connected, now: timestamp)) }

    func configureWiFi() {
        wifiAttempt = UUID()
        switch wifi {
        case .unconfigured, .connected: wifi = .provisioning
        case .provisioning:
            wifi = .joining
            let attempt = wifiAttempt
            DispatchQueue.main.asyncAfter(deadline: .now() + 1.2) { [weak self] in
                guard let self, self.wifiAttempt == attempt else { return }
                self.wifi = .connected
            }
        case .joining: wifi = .unconfigured
        }
    }

    func countdown(_ date: Date) -> String {
        let seconds = max(0, Int(date.timeIntervalSince(now)))
        let days = seconds / 86400, hours = seconds / 3600 % 24, minutes = seconds / 60 % 60
        if days > 0 { return "\(days)天 \(hours)小时" }
        return String(format: "%02d:%02d:%02d", hours, minutes, seconds % 60)
    }
}

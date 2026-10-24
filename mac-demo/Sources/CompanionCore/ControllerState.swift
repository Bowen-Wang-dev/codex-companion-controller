import Foundation

public enum RunState: String, Sendable { case idle, working, completed, failed, exhausted }
public enum Choice: String, Sendable { case allow, deny }
public enum ApprovalStage: String, Sendable { case choosing, confirming, sending, uncertain }
public enum Sound: Sendable { case permission, allowed, denied, completed, failed, exhausted, disconnected, touch }

public struct Approval: Equatable, Sendable {
    public let id: UUID
    public let operation: String
    public let project: String
    public let scope: String
    public let deadline: TimeInterval
    public let macOnly: Bool
    public init(id: UUID = UUID(), operation: String = "git status --short", project: String = "~/Projects/companion-demo", scope: String = "仅本次 · 读取项目文件", deadline: TimeInterval, macOnly: Bool = false) {
        self.id = id; self.operation = operation; self.project = project
        self.scope = scope; self.deadline = deadline; self.macOnly = macOnly
    }
}

public struct Submission: Equatable, Sendable {
    public let requestID: UUID
    public let attemptID: UUID
    public let choice: Choice
}

public struct ControllerState: Sendable {
    public private(set) var run: RunState = .idle
    public private(set) var connected = true
    public private(set) var pending: Approval?
    public private(set) var queue: [Approval] = []
    public private(set) var selected: Choice?
    public private(set) var stage: ApprovalStage = .choosing
    public private(set) var submission: Submission?
    public private(set) var log: [String] = []
    public private(set) var mutedRequest: UUID?
    public private(set) var reminderCount = 0
    public private(set) var nextReminder: TimeInterval?
    public private(set) var flash: String?
    public private(set) var flashUntil: TimeInterval = 0
    public private(set) var resetCredits = 2
    public private(set) var resetPage = false
    public private(set) var resetConfirmed = false
    public var reminderInterval: TimeInterval = 30
    public var soundEnabled = true
    private var seen: Set<UUID> = []

    public init() {}

    public var emoji: String {
        if pending != nil { return "🥺" }
        if let flash { return flash }
        switch run {
        case .idle: return "😋"
        case .failed: return "😭"
        case .working: return "🤔"
        case .completed: return "🥳"
        case .exhausted: return "😐🤲"
        }
    }

    public var status: String {
        if !connected { return "连接断开 · 状态待同步" }
        if pending != nil {
            switch stage {
            case .choosing: return "正在等你批准"
            case .confirming: return "请长按确认"
            case .sending: return "已发送 · 等待回执"
            case .uncertain: return "结果未知 · 等待同步"
            }
        }
        if flash == "😭" { return "权限已拒绝" }
        if flash == "😆" { return "开心一下！" }
        switch run {
        case .idle: return "待机 · 随时准备好"
        case .working: return "正在思考 / 工作"
        case .completed: return "任务完成！"
        case .failed: return "任务失败 · 请在 Mac 查看"
        case .exhausted: return "额度耗尽 · 等待重置"
        }
    }

    private mutating func record(_ message: String) {
        log.insert(message, at: 0)
        if log.count > 40 { log.removeLast(log.count - 40) }
    }

    public mutating func setRun(_ value: RunState, now: TimeInterval) -> Sound? {
        run = value; flash = nil
        record("模拟任务：\(value.rawValue)")
        switch value {
        case .completed: return .completed
        case .failed: return .failed
        case .exhausted: return .exhausted
        default: return nil
        }
    }

    @discardableResult public mutating func receive(_ request: Approval, now: TimeInterval) -> Sound? {
        guard request.deadline > now, !seen.contains(request.id), queue.count < 8 else { return nil }
        seen.insert(request.id)
        // The demo retains at most 512 deduplication IDs; production persists outstanding IDs.
        if seen.count > 512 { seen = Set(([pending?.id].compactMap { $0 }) + queue.map(\.id) + [request.id]) }
        if pending != nil { queue.append(request); record("请求排队（\(queue.count)）"); return nil }
        activate(request, now: now)
        return connected && soundEnabled ? .permission : nil
    }

    private mutating func activate(_ request: Approval, now: TimeInterval) {
        pending = request; selected = nil; stage = .choosing; submission = nil
        reminderCount = 0; nextReminder = now + reminderInterval
        mutedRequest = nil; flash = nil; resetPage = false; resetConfirmed = false
        record("收到模拟权限请求 \(request.id.uuidString.prefix(8))")
    }

    public mutating func choose(_ value: Choice) {
        guard connected, let pending, stage == .choosing else { return }
        guard value == .deny || !pending.macOnly else { return }
        selected = value
    }

    public mutating func confirm() {
        guard connected, pending != nil, selected != nil, stage == .choosing else { return }
        stage = .confirming
    }

    public mutating func clearSelection() {
        if stage == .choosing { selected = nil }
    }

    public mutating func back() {
        if stage == .confirming { stage = .choosing; selected = nil }
        resetPage = false; resetConfirmed = false
    }

    public mutating func submit(heldFor: TimeInterval, now: TimeInterval) -> Submission? {
        guard heldFor >= 1, connected, let request = pending, request.deadline > now,
              stage == .confirming, let choice = selected,
              choice == .deny || !request.macOnly else { return nil }
        let attempt = Submission(requestID: request.id, attemptID: UUID(), choice: choice)
        submission = attempt; stage = .sending; nextReminder = nil
        record("模拟决策已发送，等待回执")
        return attempt
    }

    public mutating func acknowledge(_ attempt: Submission, now: TimeInterval) -> Sound? {
        guard connected, stage == .sending, submission == attempt,
              let request = pending, request.id == attempt.requestID, request.deadline > now else { return nil }
        pending = nil; selected = nil; submission = nil; stage = .choosing; nextReminder = nil
        flash = attempt.choice == .allow ? "😆" : "😭"
        flashUntil = now + (attempt.choice == .allow ? 1.2 : 2.5)
        record(attempt.choice == .allow ? "模拟回执：批准成功（未执行命令）" : "模拟回执：已拒绝")
        return attempt.choice == .allow ? .allowed : .denied
    }

    public mutating func cancel(id: UUID, now: TimeInterval) {
        queue.removeAll { $0.id == id }
        guard pending?.id == id else { return }
        pending = nil; selected = nil; submission = nil; nextReminder = nil; stage = .choosing
        record("请求已撤销 · 禁止提交")
    }

    public mutating func muteRequest() {
        guard let pending else { return }
        mutedRequest = pending.id; nextReminder = nil; record("已静音当前请求")
    }

    public mutating func setReminderInterval(_ interval: TimeInterval, now: TimeInterval) {
        reminderInterval = min(120, max(10, interval))
        if let request = pending, mutedRequest != request.id, reminderCount < 3,
           stage == .choosing || stage == .confirming {
            nextReminder = now + reminderInterval
        }
    }

    public mutating func setConnected(_ value: Bool, now: TimeInterval) -> Sound? {
        guard connected != value else { return nil }
        connected = value; selected = nil; submission = nil
        stage = value ? .choosing : .uncertain
        if value { nextReminder = now + reminderInterval }
        record(value ? "模拟连接恢复 · 已同步，需重新确认" : "模拟断线 · 所有提交已禁用")
        return value ? nil : .disconnected
    }

    public mutating func touch(now: TimeInterval) -> Sound? {
        guard pending == nil, !resetPage, run != .failed, run != .exhausted else { return nil }
        flash = "😆"; flashUntil = now + 1.2
        return .touch
    }

    public mutating func tick(now: TimeInterval) -> Sound? {
        if let request = pending, request.deadline <= now {
            cancel(id: request.id, now: now); record("请求已过期 · 请在 Mac 重新发起")
        }
        queue.removeAll { $0.deadline <= now }
        if flash != nil && now >= flashUntil { flash = nil }
        if pending == nil, flash == nil, !queue.isEmpty {
            activate(queue.removeFirst(), now: now)
            return connected && soundEnabled ? .permission : nil
        }
        if let request = pending, connected, soundEnabled, mutedRequest != request.id,
           stage == .choosing || stage == .confirming,
           reminderCount < 3, let due = nextReminder, now >= due {
            reminderCount += 1; nextReminder = now + reminderInterval
            return .permission
        }
        return nil
    }

    public mutating func openReset() {
        guard pending == nil, connected, resetCredits > 0 else { return }
        resetPage = true; resetConfirmed = false
    }

    public mutating func confirmReset() {
        guard resetPage, resetCredits > 0, connected, pending == nil else { return }
        resetConfirmed = true
    }

    public mutating func submitReset(heldFor: TimeInterval, now: TimeInterval) -> Bool {
        guard heldFor >= 1, resetPage, resetConfirmed, resetCredits > 0, connected, pending == nil else { return false }
        resetCredits -= 1; resetPage = false; resetConfirmed = false
        run = .idle; record("模拟额度重置：减 1 次（未调用账户接口）")
        return true
    }
}

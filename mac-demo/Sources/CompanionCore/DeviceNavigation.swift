import Foundation

public enum DevicePage: Int, CaseIterable, Sendable {
    case home, quota, reset, settings, history, network
    public var title: String {
        switch self {
        case .home: return "宠物主页"
        case .quota: return "额度窗口"
        case .reset: return "额外重置"
        case .settings: return "声音设置"
        case .history: return "事件记录"
        case .network: return "Wi-Fi 与校时"
        }
    }
}

public enum DevicePanel: Equatable, Sendable { case none, menu, details }
public enum InputContext: Sendable { case normal, exhausted, choosing, confirming, waiting, resetConfirmation }
public enum DeviceAction: Equatable, Sendable {
    case none, allow, deny, confirmApproval, back, mute, touch, openReset, confirmReset
    case toggleSound, cycleVolume, cycleInterval, toggleTouchSound
    case configureWiFi
}

// This navigation model consumes only UP, DOWN and OK. Test/debug event injection
// belongs to the Mac console, never to additional device buttons.
public struct DeviceNavigation: Sendable {
    public var page: DevicePage = .home
    public private(set) var panel: DevicePanel = .none
    public private(set) var menuIndex = 0
    public private(set) var detailIndex = 0
    public private(set) var settingIndex = 0
    public private(set) var historyIndex = 0
    public private(set) var requestVisible = true
    public init() {}

    public func menuItems(hasRequest: Bool) -> [String] {
        if hasRequest && requestVisible { return ["查看请求详情", "静音当前请求", "返回权限页面"] }
        return (hasRequest ? ["返回权限请求"] : []) + DevicePage.allCases.map(\.title) + ["关闭菜单"]
    }

    public mutating func openMenu() { panel = .menu; menuIndex = 0 }
    public mutating func dismiss() { panel = .none; detailIndex = 0 }
    public mutating func presentRequest() { requestVisible = true; dismiss() }

    public mutating func longMove(_ direction: Int, context: InputContext, hasRequest: Bool) {
        dismiss()
        if context == .exhausted { page = direction < 0 ? .reset : .quota }
        else { turnPage(direction) }
        if hasRequest { requestVisible = false }
    }

    private mutating func turnPage(_ direction: Int) {
        page = DevicePage(rawValue: (page.rawValue + direction + DevicePage.allCases.count) % DevicePage.allCases.count)!
        settingIndex = 0; historyIndex = 0
    }

    public mutating func move(_ direction: Int, context: InputContext, hasRequest: Bool, detailCount: Int, historyCount: Int) -> DeviceAction {
        if panel == .menu {
            menuIndex = max(0, min(menuItems(hasRequest: hasRequest).count - 1, menuIndex + direction)); return .none
        }
        if panel == .details {
            detailIndex = max(0, min(max(0, detailCount - 1), detailIndex + direction)); return .none
        }
        switch context {
        case .exhausted:
            page = direction < 0 ? .reset : .quota; return .none
        case .choosing: return direction < 0 ? .allow : .deny
        case .confirming: return direction < 0 ? .back : .mute
        case .resetConfirmation: return .back
        case .waiting: return .none
        case .normal:
            if page == .settings { settingIndex = max(0, min(4, settingIndex + direction)) }
            else if page == .history { historyIndex = max(0, min(max(0, historyCount - 1), historyIndex + direction)) }
            else { turnPage(direction) }
            return .none
        }
    }

    public mutating func shortOK(context: InputContext, hasRequest: Bool, hasSelection: Bool) -> DeviceAction {
        if panel == .menu {
            if hasRequest && requestVisible {
                switch menuIndex {
                case 0: panel = .details; detailIndex = 0; return .none
                case 1: panel = .none; return .mute
                default: panel = .none; return .none
                }
            }
            if hasRequest && menuIndex == 0 { presentRequest(); return .none }
            let pageIndex = menuIndex - (hasRequest ? 1 : 0)
            if let target = DevicePage(rawValue: pageIndex) { page = target; settingIndex = 0; historyIndex = 0 }
            panel = .none; return .none
        }
        if panel == .details { panel = .none; return .none }
        switch context {
        case .exhausted: return .none // waiting is the default; UP is only navigation
        case .choosing:
            if hasSelection { return .confirmApproval }
            openMenu(); return .none
        case .confirming: return .none // only a fresh one-second hold can submit
        case .waiting: openMenu(); return .none
        case .resetConfirmation: return .confirmReset
        case .normal:
            switch page {
            case .home: return .touch
            case .quota: return .none
            case .reset: return .openReset
            case .history: page = .home; return .none
            case .network: return .configureWiFi
            case .settings:
                switch settingIndex {
                case 0: return .toggleSound
                case 1: return .cycleVolume
                case 2: return .cycleInterval
                case 3: return .toggleTouchSound
                default: page = .home; return .none
                }
            }
        }
    }
}

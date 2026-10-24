import Foundation
import CompanionCore

func exactExpressionMapping() {
    var state = ControllerState()
    expect(state.emoji == "😋")
    _ = state.setRun(.working, now: 0); expect(state.emoji == "🤔")
    _ = state.setRun(.completed, now: 0); expect(state.emoji == "🥳")
    _ = state.setRun(.exhausted, now: 0); expect(state.emoji == "😐🤲")
    _ = state.setRun(.failed, now: 0); expect(state.emoji == "😭")
    _ = state.tick(now: 60); expect(state.emoji == "😭")
    expect(state.status == "任务失败 · 请在 Mac 查看")
    _ = state.receive(Approval(deadline: 120), now: 0); expect(state.emoji == "🥺")
}

func noDefaultChoiceAndTwoStepHold() {
    var state = ControllerState()
    _ = state.receive(Approval(deadline: 120), now: 0)
    expect(state.selected == nil)
    state.confirm(); expect(state.stage == .choosing)
    expect(state.submit(heldFor: 4, now: 1) == nil)
    state.choose(.allow)
    expect(state.submit(heldFor: 4, now: 1) == nil)
    state.confirm()
    expect(state.submit(heldFor: 0.999, now: 1) == nil)
    expect(state.submit(heldFor: 1, now: 1) != nil)
    expect(state.submit(heldFor: 2, now: 2) == nil)
    expect(state.emoji == "🥺")
}

func denialGoesDirectlyToCrying() throws {
    var state = ControllerState()
    _ = state.setRun(.working, now: 0)
    _ = state.receive(Approval(deadline: 120), now: 0)
    state.choose(.deny); state.confirm()
    let submission = try require(state.submit(heldFor: 1, now: 1))
    expect(state.emoji == "🥺")
    expect(state.acknowledge(submission, now: 2) == .denied)
    expect(state.emoji == "😭")
    _ = state.tick(now: 4); expect(state.emoji == "😭")
    _ = state.tick(now: 5); expect(state.emoji == "🤔")
}

func allowedReceiptThenRestoreActualRunState() throws {
    var state = ControllerState()
    _ = state.setRun(.working, now: 0)
    _ = state.receive(Approval(deadline: 120), now: 0)
    state.choose(.allow); state.confirm()
    let submission = try require(state.submit(heldFor: 1, now: 1))
    expect(state.acknowledge(submission, now: 2) == .allowed)
    expect(state.emoji == "😆")
    _ = state.tick(now: 4); expect(state.emoji == "🤔")
    expect(state.acknowledge(submission, now: 5) == nil)
}

func expiredOrCancelledRequestRejectsLateReceipt() throws {
    for cancel in [true, false] {
        var state = ControllerState()
        let request = Approval(deadline: 10)
        _ = state.receive(request, now: 0); state.choose(.allow); state.confirm()
        let submission = try require(state.submit(heldFor: 1, now: 1))
        if cancel { state.cancel(id: request.id, now: 2) } else { _ = state.tick(now: 10) }
        expect(state.acknowledge(submission, now: 11) == nil)
        expect(state.pending == nil)
        expect(state.emoji != "😆")
    }
}

func disconnectInvalidatesAttemptAndRequiresFreshChoice() throws {
    var state = ControllerState()
    _ = state.receive(Approval(deadline: 120), now: 0); state.choose(.allow); state.confirm()
    let old = try require(state.submit(heldFor: 1, now: 1))
    _ = state.setConnected(false, now: 2)
    expect(state.stage == .uncertain)
    expect(state.acknowledge(old, now: 3) == nil)
    expect(state.submit(heldFor: 2, now: 3) == nil)
    _ = state.setConnected(true, now: 4)
    expect(state.selected == nil)
    expect(state.stage == .choosing)
    expect(state.acknowledge(old, now: 5) == nil)
}

func highRiskApprovalIsUnavailableButDenialWorks() {
    var state = ControllerState()
    _ = state.receive(Approval(deadline: 120, macOnly: true), now: 0)
    state.choose(.allow); expect(state.selected == nil)
    state.confirm(); expect(state.submit(heldFor: 2, now: 1) == nil)
    state.choose(.deny); state.confirm()
    expect(state.submit(heldFor: 1, now: 1)?.choice == .deny)
}

func duplicateAndQueuedRequestsDoNotStealSelection() {
    var state = ControllerState()
    let first = Approval(deadline: 120), next = Approval(deadline: 120)
    _ = state.receive(first, now: 0); state.choose(.deny)
    expect(state.receive(first, now: 1) == nil)
    expect(state.receive(next, now: 1) == nil)
    expect(state.selected == .deny)
    expect(state.queue.count == 1)
    state.cancel(id: first.id, now: 2); _ = state.tick(now: 3)
    expect(state.pending?.id == next.id)
    expect(state.selected == nil)
}

func reminderIsImmediateThenThreeRepeatsOnly() {
    var state = ControllerState()
    expect(state.receive(Approval(deadline: 300), now: 0) == .permission)
    expect(state.tick(now: 29) == nil)
    for time in [30.0, 60, 90] { expect(state.tick(now: time) == .permission) }
    expect(state.reminderCount == 3)
    expect(state.tick(now: 120) == nil)
    expect(state.tick(now: 150) == nil)
}

func muteAndSendingStopRepeatedAlerts() throws {
    var state = ControllerState()
    _ = state.receive(Approval(deadline: 300), now: 0)
    state.muteRequest(); expect(state.tick(now: 30) == nil)
    var other = ControllerState()
    _ = other.receive(Approval(deadline: 300), now: 0)
    other.choose(.allow); other.confirm()
    _ = try require(other.submit(heldFor: 1, now: 1))
    expect(other.tick(now: 30) == nil)
}

func resetRequiresSeparateConfirmationAndNeverGoesNegative() {
    var state = ControllerState()
    expect(!state.submitReset(heldFor: 2, now: 0))
    state.openReset(); expect(!state.submitReset(heldFor: 2, now: 0))
    state.confirmReset(); expect(!state.submitReset(heldFor: 0.9, now: 0))
    expect(state.submitReset(heldFor: 1, now: 1)); expect(state.resetCredits == 1)
    expect(!state.submitReset(heldFor: 2, now: 1)); expect(state.resetCredits == 1)
    state.openReset(); state.confirmReset()
    _ = state.receive(Approval(deadline: 120), now: 2)
    expect(!state.submitReset(heldFor: 2, now: 3))
}

func touchNeverMasksAnApproval() {
    var state = ControllerState()
    expect(state.touch(now: 0) == .touch); expect(state.emoji == "😆")
    _ = state.receive(Approval(deadline: 120), now: 1)
    expect(state.touch(now: 2) == nil); expect(state.emoji == "🥺")
}

func reminderSettingReschedulesCurrentRequest() {
    var state = ControllerState()
    _ = state.receive(Approval(deadline: 300), now: 0)
    state.setReminderInterval(10, now: 5)
    expect(state.tick(now: 14) == nil)
    expect(state.tick(now: 15) == .permission)
    state.muteRequest(); state.setReminderInterval(30, now: 16)
    expect(state.tick(now: 46) == nil)
}

func threeKeysReachEveryDevicePage() {
    for page in DevicePage.allCases {
        var nav = DeviceNavigation()
        nav.openMenu()
        for _ in 0..<page.rawValue {
            _ = nav.move(1, context: .normal, hasRequest: false, detailCount: 0, historyCount: 0)
        }
        expect(nav.shortOK(context: .normal, hasRequest: false, hasSelection: false) == .none)
        expect(nav.page == page); expect(nav.panel == .none)
    }
}

func threeKeysHandleApprovalAndBackWithoutExtraKeys() {
    var nav = DeviceNavigation()
    expect(nav.move(-1, context: .choosing, hasRequest: true, detailCount: 4, historyCount: 0) == .allow)
    expect(nav.move(1, context: .choosing, hasRequest: true, detailCount: 4, historyCount: 0) == .deny)
    expect(nav.shortOK(context: .choosing, hasRequest: true, hasSelection: true) == .confirmApproval)
    expect(nav.shortOK(context: .confirming, hasRequest: true, hasSelection: true) == .none)
    expect(nav.move(-1, context: .confirming, hasRequest: true, detailCount: 4, historyCount: 0) == .back)
    expect(nav.move(1, context: .confirming, hasRequest: true, detailCount: 4, historyCount: 0) == .mute)
}

func threeKeysReachDetailsAndMuteWithoutApproving() {
    var nav = DeviceNavigation()
    // A short OK without a choice opens a menu; it cannot approve.
    expect(nav.shortOK(context: .choosing, hasRequest: true, hasSelection: false) == .none)
    expect(nav.panel == .menu)
    expect(nav.shortOK(context: .choosing, hasRequest: true, hasSelection: false) == .none)
    expect(nav.panel == .details)
    for _ in 0..<10 { _ = nav.move(1, context: .choosing, hasRequest: true, detailCount: 4, historyCount: 0) }
    expect(nav.detailIndex == 3)
    _ = nav.shortOK(context: .choosing, hasRequest: true, hasSelection: false)
    expect(nav.panel == .none)
    nav.openMenu()
    _ = nav.move(1, context: .waiting, hasRequest: true, detailCount: 4, historyCount: 0)
    expect(nav.shortOK(context: .waiting, hasRequest: true, hasSelection: false) == .mute)
    expect(nav.panel == .none)
}

func threeKeysReachEverySettingAndReturnHome() {
    var nav = DeviceNavigation(); nav.page = .settings
    let actions: [DeviceAction] = [.toggleSound, .cycleVolume, .cycleInterval, .toggleTouchSound]
    for action in actions {
        expect(nav.shortOK(context: .normal, hasRequest: false, hasSelection: false) == action)
        _ = nav.move(1, context: .normal, hasRequest: false, detailCount: 0, historyCount: 0)
    }
    _ = nav.shortOK(context: .normal, hasRequest: false, hasSelection: false)
    expect(nav.page == .home)
    expect(nav.shortOK(context: .normal, hasRequest: false, hasSelection: false) == .touch)
}

func openingApprovalMenuClearsPreviousChoice() {
    var state = ControllerState()
    _ = state.receive(Approval(deadline: 120), now: 0)
    state.choose(.allow); state.clearSelection(); state.confirm()
    expect(state.selected == nil); expect(state.stage == .choosing)
    expect(state.submit(heldFor: 1, now: 1) == nil)
}

func exhaustedUpNavigatesWithoutSpending() {
    var nav = DeviceNavigation()
    var state = ControllerState()
    _ = state.setRun(.exhausted, now: 0)
    let originalCredits = state.resetCredits
    expect(nav.move(-1, context: .exhausted, hasRequest: false, detailCount: 0, historyCount: 0) == .none)
    expect(nav.page == .reset)
    expect(state.resetCredits == originalCredits)
    expect(!state.resetPage)
    nav.page = .home
    expect(nav.shortOK(context: .exhausted, hasRequest: false, hasSelection: false) == .none)
    expect(nav.page == .home) // default is to wait; no forced redemption
}

func failedAndExhaustedNeverBecomeHappyFromHover() {
    for run in [RunState.failed, .exhausted] {
        var state = ControllerState()
        _ = state.setRun(run, now: 0)
        expect(state.touch(now: 1) == nil)
        expect(state.emoji == (run == .failed ? "😭" : "😐🤲"))
    }
}

func zeroCreditsDoNotOfferConfirmation() {
    var state = ControllerState()
    for time in [0.0, 1] {
        state.openReset(); state.confirmReset()
        expect(state.submitReset(heldFor: 1, now: time))
    }
    expect(state.resetCredits == 0)
    state.openReset(); expect(!state.resetPage)
    expect(!state.submitReset(heldFor: 1, now: 3))
}

func networkClockUsesMonotonicAnchor() throws {
    let sample = try NetworkClock.parse(status: 204, date: "Fri, 23 Oct 2026 12:08:05 GMT", age: nil, roundTrip: 0.2, receivedUptime: 100, source: "test")
    expect(abs(sample.date(at: 110).timeIntervalSince(sample.utc) - 10) < 0.0001)
    expect(sample.date(at: 90) == sample.utc)
    var state = ControllerState()
    _ = state.receive(Approval(deadline: 120), now: 100)
    // Changing the wall-clock anchor cannot expire a request; protocol TTL stays in uptime.
    _ = ClockAnchor(utc: Date(timeIntervalSince1970: 0), uptime: 100, source: "test", uncertainty: 1)
    _ = state.tick(now: 110); expect(state.pending != nil)
    _ = state.tick(now: 120); expect(state.pending == nil)
}

func invalidOrStaleNetworkTimeIsRejected() {
    for (status, date, age, rtt) in [(404, "Fri, 23 Oct 2026 12:08:05 GMT", "0", 0.2), (204, "garbage", "0", 0.2), (204, "Fri, 23 Oct 2026 12:08:05 GMT", "30", 0.2), (204, "Fri, 23 Oct 2026 12:08:05 GMT", "0", 5.0)] {
        do {
            _ = try NetworkClock.parse(status: status, date: date, age: age, roundTrip: rtt, receivedUptime: 100, source: "test")
            expect(false)
        } catch { /* expected */ }
    }
}

func shortDirectionsWaitForReleaseAndNeverMoveOptionsEarly() {
    var key = DirectionalPress()
    var nav = DeviceNavigation(); nav.page = .settings
    expect(key.press(1, at: 0))
    expect(key.tick(at: 0.3) == nil)
    expect(nav.settingIndex == 0)
    expect(key.release(1, at: 0.4) == .short(1))
    _ = nav.move(1, context: .normal, hasRequest: false, detailCount: 0, historyCount: 0)
    expect(nav.settingIndex == 1); expect(nav.page == .settings)
}

func heldDirectionProducesOnePageAndNoReleaseClick() {
    for direction in [-1, 1] {
        var key = DirectionalPress()
        var nav = DeviceNavigation(); nav.page = .settings
        expect(key.press(direction, at: 0))
        expect(!key.press(direction, at: 0.2)) // repeated keyDown is ignored
        expect(key.tick(at: 0.649) == nil)
        expect(key.tick(at: 0.65) == .long(direction))
        nav.longMove(direction, context: .normal, hasRequest: false)
        expect(nav.page == (direction < 0 ? .reset : .history))
        expect(nav.settingIndex == 0); expect(nav.historyIndex == 0)
        expect(key.tick(at: 1.3) == nil)
        expect(key.tick(at: 10) == nil)
        expect(key.release(direction, at: 10) == nil)
        expect(key.press(direction, at: 11)) // must release before the next page
    }
}

func releaseThresholdWorksWithoutTimerAndCancellationDoesNotClick() {
    var key = DirectionalPress()
    expect(key.press(-1, at: 0))
    expect(key.release(-1, at: 0.65) == .long(-1))
    expect(key.press(1, at: 1))
    key.cancelUntilRelease()
    expect(key.tick(at: 2) == nil)
    expect(key.release(1, at: 2) == nil)
    expect(key.press(1, at: 3))
    key.reset() // focus loss abandons the key
    expect(key.release(1, at: 3.1) == nil)
}

func everyPageCanBeTraversedWithLongDirections() {
    var nav = DeviceNavigation()
    for page in [DevicePage.quota, .reset, .settings, .history, .network, .home] {
        nav.longMove(1, context: .normal, hasRequest: false)
        expect(nav.page == page)
    }
    nav.longMove(-1, context: .normal, hasRequest: false); expect(nav.page == .network)
    nav.longMove(-1, context: .normal, hasRequest: false); expect(nav.page == .history)
    let page = nav.page
    _ = nav.move(1, context: .normal, hasRequest: false, detailCount: 0, historyCount: 5)
    expect(nav.page == page); expect(nav.historyIndex == 1)
    nav.longMove(-1, context: .normal, hasRequest: false); expect(nav.page == .settings)
}

func ordinaryShortAndLongDirectionsHaveTheSameDestination() {
    for page in [DevicePage.home, .quota, .reset, .network] {
        for direction in [-1, 1] {
            var shortNav = DeviceNavigation(); shortNav.page = page
            var longNav = shortNav
            _ = shortNav.move(direction, context: .normal, hasRequest: false, detailCount: 0, historyCount: 0)
            longNav.longMove(direction, context: .normal, hasRequest: false)
            expect(shortNav.page == longNav.page)
        }
    }
}

func leavingConfirmationCancelsChoiceButKeepsRequestPending() {
    var state = ControllerState(); var nav = DeviceNavigation()
    let request = Approval(deadline: 120)
    _ = state.receive(request, now: 0); state.choose(.allow); state.confirm()
    state.back(); state.clearSelection()
    nav.longMove(1, context: .confirming, hasRequest: true)
    expect(state.selected == nil); expect(state.stage == .choosing)
    expect(state.pending?.id == request.id); expect(state.submission == nil)
    expect(state.submit(heldFor: 2, now: 2) == nil)
    expect(!nav.requestVisible)
    nav.openMenu(); expect(nav.menuItems(hasRequest: true).first == "返回权限请求")
    _ = nav.shortOK(context: .normal, hasRequest: true, hasSelection: false)
    expect(nav.requestVisible); expect(nav.panel == .none)
    expect(state.selected == nil)
}

func directionPageTurnNeverSpendsAResetOrResolvesARequest() {
    var state = ControllerState(); var nav = DeviceNavigation(); nav.page = .reset
    state.openReset(); state.confirmReset()
    state.back(); nav.longMove(1, context: .resetConfirmation, hasRequest: false)
    expect(!state.resetPage); expect(!state.resetConfirmed); expect(state.resetCredits == 2)
    expect(!state.submitReset(heldFor: 1, now: 1)); expect(nav.page == .settings)
    _ = state.receive(Approval(deadline: 120), now: 0)
    nav.presentRequest(); nav.openMenu()
    nav.longMove(1, context: .choosing, hasRequest: true)
    expect(nav.panel == .none); expect(!nav.requestVisible)
    expect(state.pending != nil)
}

func expect(_ condition: @autoclosure () -> Bool, file: String = #filePath, line: Int = #line) {
    if !condition() { print("FAIL \(file):\(line)"); exit(1) }
}
enum CheckError: Error { case missingValue }
func require<T>(_ value: T?) throws -> T { guard let value else { throw CheckError.missingValue }; return value }

let checks: [(String, () throws -> Void)] = [
    ("exactExpressionMapping", exactExpressionMapping),
    ("noDefaultChoiceAndTwoStepHold", noDefaultChoiceAndTwoStepHold),
    ("denialGoesDirectlyToCrying", denialGoesDirectlyToCrying),
    ("allowedReceiptThenRestoreActualRunState", allowedReceiptThenRestoreActualRunState),
    ("expiredOrCancelledRequestRejectsLateReceipt", expiredOrCancelledRequestRejectsLateReceipt),
    ("disconnectInvalidatesAttemptAndRequiresFreshChoice", disconnectInvalidatesAttemptAndRequiresFreshChoice),
    ("highRiskApprovalIsUnavailableButDenialWorks", highRiskApprovalIsUnavailableButDenialWorks),
    ("duplicateAndQueuedRequestsDoNotStealSelection", duplicateAndQueuedRequestsDoNotStealSelection),
    ("reminderIsImmediateThenThreeRepeatsOnly", reminderIsImmediateThenThreeRepeatsOnly),
    ("muteAndSendingStopRepeatedAlerts", muteAndSendingStopRepeatedAlerts),
    ("resetRequiresSeparateConfirmationAndNeverGoesNegative", resetRequiresSeparateConfirmationAndNeverGoesNegative),
    ("touchNeverMasksAnApproval", touchNeverMasksAnApproval),
    ("reminderSettingReschedulesCurrentRequest", reminderSettingReschedulesCurrentRequest),
    ("threeKeysReachEveryDevicePage", threeKeysReachEveryDevicePage),
    ("threeKeysHandleApprovalAndBackWithoutExtraKeys", threeKeysHandleApprovalAndBackWithoutExtraKeys),
    ("threeKeysReachDetailsAndMuteWithoutApproving", threeKeysReachDetailsAndMuteWithoutApproving),
    ("threeKeysReachEverySettingAndReturnHome", threeKeysReachEverySettingAndReturnHome),
    ("openingApprovalMenuClearsPreviousChoice", openingApprovalMenuClearsPreviousChoice),
    ("exhaustedUpNavigatesWithoutSpending", exhaustedUpNavigatesWithoutSpending),
    ("failedAndExhaustedNeverBecomeHappyFromHover", failedAndExhaustedNeverBecomeHappyFromHover),
    ("zeroCreditsDoNotOfferConfirmation", zeroCreditsDoNotOfferConfirmation),
    ("networkClockUsesMonotonicAnchor", networkClockUsesMonotonicAnchor),
    ("invalidOrStaleNetworkTimeIsRejected", invalidOrStaleNetworkTimeIsRejected),
    ("shortDirectionsWaitForReleaseAndNeverMoveOptionsEarly", shortDirectionsWaitForReleaseAndNeverMoveOptionsEarly),
    ("heldDirectionProducesOnePageAndNoReleaseClick", heldDirectionProducesOnePageAndNoReleaseClick),
    ("releaseThresholdWorksWithoutTimerAndCancellationDoesNotClick", releaseThresholdWorksWithoutTimerAndCancellationDoesNotClick),
    ("everyPageCanBeTraversedWithLongDirections", everyPageCanBeTraversedWithLongDirections),
    ("ordinaryShortAndLongDirectionsHaveTheSameDestination", ordinaryShortAndLongDirectionsHaveTheSameDestination),
    ("leavingConfirmationCancelsChoiceButKeepsRequestPending", leavingConfirmationCancelsChoiceButKeepsRequestPending),
    ("directionPageTurnNeverSpendsAResetOrResolvesARequest", directionPageTurnNeverSpendsAResetOrResolvesARequest),
]
do {
    for (name, check) in checks { try check(); print("PASS \(name)") }
    print("All \(checks.count) state-machine checks passed.")
} catch { print("FAIL: \(error)"); exit(1) }

import AppKit
import SwiftUI
import CompanionCore

private let ink = Color(red: 0.055, green: 0.075, blue: 0.105)
private let panel = Color(red: 0.085, green: 0.108, blue: 0.145)
private let muted = Color(red: 0.55, green: 0.61, blue: 0.7)
private let mint = Color(red: 0.53, green: 0.94, blue: 0.76)
private let amber = Color(red: 1, green: 0.76, blue: 0.36)

#if !PREVIEW
@main struct CompanionDemoApp: App {
    @StateObject private var store = DemoStore()
    init() {
        // The launcher uses open -n so a rebuilt binary really starts. Retire
        // previous demo instances instead of leaving the user on old code.
        let ownPID = ProcessInfo.processInfo.processIdentifier
        for application in NSRunningApplication.runningApplications(withBundleIdentifier: "local.codexcompanion.macdemo") where application.processIdentifier != ownPID {
            application.terminate()
        }
    }
    var body: some Scene {
        WindowGroup("Codex Companion · v0.4.0") {
            Dashboard(store: store)
                .preferredColorScheme(.dark)
                .onAppear { store.start(); NSApp.activate(ignoringOtherApps: true) }
        }
        .defaultSize(width: 1020, height: 820)
        .windowResizability(.contentMinSize)
        .commands {
            CommandGroup(replacing: .newItem) {}
        }
    }
}
#endif

struct Dashboard: View {
    @ObservedObject var store: DemoStore
    var body: some View {
        VStack(alignment: .leading, spacing: 22) {
            HStack(spacing: 13) {
                Image(systemName: "command.square.fill").font(.system(size: 34)).foregroundStyle(mint)
                VStack(alignment: .leading, spacing: 3) {
                    HStack(alignment: .firstTextBaseline, spacing: 9) {
                        Text("Codex Companion").font(.system(size: 25, weight: .semibold, design: .rounded))
                        Text("v0.4.0").font(.system(size: 10, weight: .medium, design: .monospaced)).foregroundStyle(mint)
                    }
                    Text("你的桌面搭子，也是一台未来的实体控制器。")
                        .font(.system(size: 12)).foregroundStyle(muted)
                }
                Spacer()
                Label("本地模拟", systemImage: "circle.fill").font(.system(size: 11, weight: .medium))
                    .foregroundStyle(amber).padding(.horizontal, 13).padding(.vertical, 8)
                    .background(amber.opacity(0.1), in: Capsule())
            }
            HStack(alignment: .top, spacing: 26) {
                VStack(spacing: 17) {
                    HStack {
                        Text("AI PASSPORT").font(.system(size: 10, weight: .bold, design: .monospaced)).tracking(2)
                        Spacer()
                        Text("240 × 320").font(.system(size: 10, design: .monospaced)).foregroundStyle(muted)
                    }
                    DeviceScreen(store: store)
                        .frame(width: 240, height: 320)
                        .scaleEffect(1.5)
                        .frame(width: 360, height: 480)
                        .background(.black, in: RoundedRectangle(cornerRadius: 30))
                        .overlay(RoundedRectangle(cornerRadius: 30).stroke(.white.opacity(0.12)))
                        .shadow(color: .black.opacity(0.28), radius: 24, y: 12)
                    HStack(spacing: 15) {
                        directionButton("↑", direction: -1)
                        directionButton("↓", direction: 1)
                        Text("↵").font(.system(size: 19, weight: .medium))
                            .frame(width: 80, height: 36)
                            .background(.white.opacity(0.08), in: RoundedRectangle(cornerRadius: 9))
                            .overlay(RoundedRectangle(cornerRadius: 9).stroke(.white.opacity(0.1)))
                            .contentShape(Rectangle())
                            .gesture(DragGesture(minimumDistance: 0).onChanged { _ in store.pressReturn() }.onEnded { _ in store.releaseReturn() })
                            .help("短按确认；长按 0.65 秒打开菜单；危险操作确认页长按 1 秒提交")
                    }
                    Text("短按 ↑↓ 选择 / 翻页 · 长按 ↑↓ 换页")
                        .font(.system(size: 11, design: .monospaced)).foregroundStyle(muted)
                }
                .padding(22).frame(width: 406)
                .background(panel, in: RoundedRectangle(cornerRadius: 24))

                ScrollView {
                    VStack(alignment: .leading, spacing: 17) {
                        scenarios
                        keyboard
                        audioSettings
                        networkStatus
                        diagnostics
                        history
                    }.padding(.trailing, 4)
                }.scrollIndicators(.hidden)
            }
            HStack {
                Text("Apple 系统 Emoji · 原生渲染").foregroundStyle(muted)
                Spacer()
                Text("Codex / 配网为模拟 · 时钟联网校准 · 不消耗真实重置次数").foregroundStyle(muted)
            }.font(.system(size: 10))
        }
        .padding(28).background(ink).frame(minWidth: 960, minHeight: 800)
    }

    private func directionButton(_ title: String, direction: Int) -> some View {
        Text(title).font(.system(size: 19, weight: .medium)).frame(width: 80, height: 36)
            .background(.white.opacity(0.08), in: RoundedRectangle(cornerRadius: 9))
            .overlay(RoundedRectangle(cornerRadius: 9).stroke(.white.opacity(0.1)))
            .contentShape(Rectangle())
            .gesture(DragGesture(minimumDistance: 0).onChanged { _ in store.pressDirection(direction) }.onEnded { _ in store.releaseDirection(direction) })
            .accessibilityLabel(direction < 0 ? "上键：短按选择或翻页，长按上一页" : "下键：短按选择或翻页，长按下一页")
    }

    private var scenarios: some View {
        VStack(alignment: .leading, spacing: 12) {
            sectionHeading("模拟事件 · 仅 Mac 测试面板", caption: "鼠标触发")
            LazyVGrid(columns: [GridItem(.flexible()), GridItem(.flexible())], spacing: 9) {
                scenario("😋", "待机", "") { store.scenario(.idle) }
                scenario("🤔", "工作中", "") { store.scenario(.working) }
                scenario("🥺", "权限请求", "") { store.request() }
                scenario("🥳", "任务完成", "") { store.scenario(.completed) }
                scenario("😐🤲", "额度耗尽", "") { store.scenario(.exhausted) }
                scenario("😭", "任务失败", "") { store.scenario(.failed) }
            }
        }
    }

    private func scenario(_ emoji: String, _ title: String, _ key: String, symbol: Bool = false, action: @escaping () -> Void) -> some View {
        Button(action: action) {
            HStack(spacing: 9) {
                if symbol { Image(systemName: emoji).font(.system(size: 20)).foregroundStyle(amber).frame(width: 35) }
                else { Text(emoji).font(.custom("Apple Color Emoji", size: emoji.count > 1 ? 19 : 27)).fixedSize().frame(width: 40) }
                Text(title).font(.system(size: 12, weight: .medium))
                Spacer(minLength: 0)
                Text(key).font(.system(size: 10, design: .monospaced)).foregroundStyle(muted)
            }.padding(.horizontal, 11).frame(height: 51).background(panel, in: RoundedRectangle(cornerRadius: 12))
        }.buttonStyle(.plain)
    }

    private var keyboard: some View {
        VStack(alignment: .leading, spacing: 10) {
            sectionHeading("日常操作只需三个键", caption: "设备映射")
            HStack(spacing: 9) { keycap("短按 ↑↓"); Text("普通页翻页；设置 / 事件页选择内容") }
            HStack(spacing: 9) { keycap("长按 ↑↓"); Text("上一页 / 下一页 · 一次按住只翻一页") }
            HStack(spacing: 9) { keycap("↵"); Text("进入确认，再松开并长按 1 秒提交") }
            HStack(spacing: 9) { keycap("长按 ↵"); Text("打开菜单：详情、静音、设置和页面") }
            Text("确认页：短按 ↑ 返回、↓ 静音；长按方向键离开并取消确认。")
        }.font(.system(size: 11)).foregroundStyle(muted)
    }

    private func keycap(_ value: String) -> some View {
        Text(value).font(.system(size: 10, weight: .medium, design: .monospaced)).foregroundStyle(.white.opacity(0.9))
            .padding(.horizontal, 7).padding(.vertical, 4).background(.white.opacity(0.07), in: RoundedRectangle(cornerRadius: 5))
    }

    private var audioSettings: some View {
        VStack(alignment: .leading, spacing: 11) {
            HStack { Text("复古 BB 机").font(.system(size: 13, weight: .semibold)); Spacer(); Toggle("声音", isOn: $store.soundEnabled).toggleStyle(.switch).controlSize(.mini) }
            Text("1200 Hz · 哔哔哔 · 780 ms").font(.system(size: 11, design: .monospaced)).foregroundStyle(muted)
            HStack { Text("音量").font(.system(size: 11)); Slider(value: $store.volume, in: 0...60); Text("\(Int(store.volume))%").monospacedDigit().font(.system(size: 11)).frame(width: 30) }
            HStack { Text("每 \(Int(store.interval)) 秒提醒，最多追加 3 轮").font(.system(size: 11)); Spacer(); Stepper("", value: $store.interval, in: 10...120, step: 10).labelsHidden() }
            Toggle("摸宠物时也播放声音", isOn: $store.touchSound).toggleStyle(.checkbox).font(.system(size: 11))
        }.padding(15).background(panel, in: RoundedRectangle(cornerRadius: 14))
    }

    private var diagnostics: some View {
        DisclosureGroup {
            VStack(alignment: .leading, spacing: 8) {
                HStack {
                    Button("高风险 / 长命令") { store.request(long: true) }
                    Button("10 秒过期") { store.request(seconds: 10) }
                }
                HStack {
                    Button("重复同一请求") { store.duplicate() }.disabled(store.state.pending == nil)
                    Button("撤销请求") { store.cancel() }.disabled(store.state.pending == nil)
                    Button(store.state.connected ? "断线" : "重连") { store.connection() }
                }
                Toggle("丢失下一个模拟回执", isOn: $store.simulateLostReceipt).toggleStyle(.checkbox)
                Text("高风险批准被禁用；断线不判定成功；回执到达前保持“等待回执”。")
                    .foregroundStyle(muted).fixedSize(horizontal: false, vertical: true)
            }.font(.system(size: 11)).padding(.top, 10)
        } label: { Text("异常场景测试").font(.system(size: 12, weight: .medium)) }
        .tint(muted)
    }

    private var networkStatus: some View {
        VStack(alignment: .leading, spacing: 7) {
            HStack {
                Label(store.clockMessage, systemImage: store.clockAnchor == nil ? "clock.badge.exclamationmark" : "checkmark.circle")
                    .font(.system(size: 11)).foregroundStyle(store.clockAnchor == nil ? amber : mint)
                Spacer()
                Button("重新校时") { store.synchronizeClock() }.disabled(store.clockSyncing).font(.system(size: 10))
            }
            Text(store.clockAnchor.map { "HTTPS · \($0.source) · 约 ±\(Int(ceil($0.uncertainty))) 秒" } ?? "启动时联网；未成功时明确标记未校时")
                .font(.system(size: 9, design: .monospaced)).foregroundStyle(muted)
            Button("查看设备 Wi-Fi 配网流程（演示）") { store.navigation.dismiss(); store.page = 5 }
                .font(.system(size: 10)).buttonStyle(.plain).foregroundStyle(mint)
        }.padding(12).background(panel, in: RoundedRectangle(cornerRadius: 12))
    }

    private var history: some View {
        VStack(alignment: .leading, spacing: 7) {
            HStack { Text("事件记录").font(.system(size: 11, weight: .medium)); Spacer(); Text("LOCAL ONLY").font(.system(size: 9, design: .monospaced)).foregroundStyle(muted) }
            if store.state.log.isEmpty { Text("点击“权限请求”注入模拟事件；用左侧三个键处理。") .font(.system(size: 11)).foregroundStyle(muted) }
            ForEach(Array(store.state.log.prefix(4).enumerated()), id: \.offset) { index, line in
                HStack(alignment: .top, spacing: 7) {
                    Circle().fill(index == 0 ? mint : muted.opacity(0.4)).frame(width: 4, height: 4).padding(.top, 5)
                    Text(line).font(.system(size: 10)).foregroundStyle(index == 0 ? .white.opacity(0.8) : muted)
                }
            }
        }
    }

    private func sectionHeading(_ title: String, caption: String) -> some View {
        HStack { Text(title).font(.system(size: 13, weight: .semibold)); Spacer(); Text(caption).font(.system(size: 10)).foregroundStyle(muted) }
    }


}

private struct DeviceScreen: View {
    @ObservedObject var store: DemoStore
    private var state: ControllerState { store.state }
    var body: some View {
        VStack(spacing: 0) {
            HStack {
                Text(timeText)
                    .font(.system(size: 12, weight: .semibold, design: .monospaced)).monospacedDigit()
                Image(systemName: store.clockAnchor == nil ? "clock.badge.exclamationmark" : "checkmark.circle.fill")
                    .font(.system(size: 8)).foregroundStyle(store.clockAnchor == nil ? amber : mint)
                Spacer()
                if state.pending != nil && !store.requestVisible {
                    Button("待批准") { store.returnToRequest() }.buttonStyle(.plain)
                        .font(.system(size: 8, weight: .semibold)).foregroundStyle(amber)
                        .help("仍有请求等待处理；长按确认键也可从菜单返回")
                }
                Image(systemName: store.wifi == .connected ? "wifi" : "wifi.slash").font(.system(size: 10)).foregroundStyle(store.wifi == .connected ? mint : amber)
            }.padding(.horizontal, 20).frame(height: 34)
            Rectangle().fill(.white.opacity(0.08)).frame(height: 1)
            Group {
                if store.navigation.panel == .menu { deviceMenu }
                else if store.navigation.panel == .details { requestDetails }
                else if store.requestVisible { permission }
                else if state.resetPage { resetConfirmation }
                else if store.page == 1 { quotaPage }
                else if store.page == 2 { resetPage }
                else if store.page == 3 { settingsPage }
                else if store.page == 4 { historyPage }
                else if store.page == 5 { wifiPage }
                else { home }
            }.frame(width: 240, height: 265).clipped()
            // A single reserved footer gives every page the same dot baseline.
            dots.frame(height: 12).padding(.bottom, 8)
                .opacity(!store.requestVisible && !state.resetPage && store.navigation.panel == .none ? 1 : 0)
        }
        .background(Color(red: 0.035, green: 0.05, blue: 0.07))
        .clipShape(RoundedRectangle(cornerRadius: 20))
    }

    private var timeText: String {
        guard store.clockAnchor != nil else { return "--:--" }
        let formatter = DateFormatter()
        formatter.locale = Locale(identifier: "en_US_POSIX")
        formatter.timeZone = TimeZone(identifier: "Australia/Sydney")
        formatter.dateFormat = "HH:mm"
        return formatter.string(from: store.now)
    }

    private var home: some View {
        VStack(spacing: 5) {
            Spacer(minLength: 0)
            Text(state.emoji).font(.custom("Apple Color Emoji", size: state.run == .exhausted ? 51 : 75))
                .frame(height: 83).onHover { if $0 { store.hover() } }.onTapGesture { store.touch() }
            Text(state.status).font(.system(size: 12, weight: .semibold)).foregroundStyle(state.connected ? .white : amber)
            Spacer(minLength: 0)
            VStack(spacing: 9) {
                meter("5 小时", value: store.primaryRemaining)
                meter("7 天", value: store.secondaryRemaining)
                HStack { Text(store.quotaDepleted ? "等待重置" : "下次重置"); Spacer(); Text(store.countdown(store.relevantReset)).monospacedDigit().foregroundStyle(.white) }.font(.system(size: 9)).foregroundStyle(muted)
            }
            HStack { Text("额外重置 \(state.resetCredits) 次"); Spacer(); Text("模拟数据") }.font(.system(size: 8)).foregroundStyle(muted)
            if store.quotaDepleted {
                Text("↑ 前往重置 · 或等待自动重置").font(.system(size: 9, weight: .semibold)).foregroundStyle(amber)
            }
        }.padding(.horizontal, 18).padding(.bottom, 3)
    }

    private func meter(_ name: String, value: Int) -> some View {
        let remaining = min(100, max(0, value))
        let color = remaining == 0 ? Color(red: 1, green: 0.43, blue: 0.43) : remaining <= 20 ? amber : mint
        return VStack(spacing: 5) {
            HStack(alignment: .firstTextBaseline, spacing: 4) {
                Text(name).font(.system(size: 10, weight: .medium)).foregroundStyle(.white.opacity(0.8))
                Spacer()
                Text(remaining == 0 ? "已耗尽" : "剩余").font(.system(size: 8)).foregroundStyle(muted)
                Text("\(remaining)").font(.system(size: 14, weight: .semibold, design: .rounded)).monospacedDigit().foregroundStyle(color)
                Text("%").font(.system(size: 9, weight: .medium)).foregroundStyle(color)
            }
            HStack(spacing: 2) {
                ForEach(0..<10) { index in
                    GeometryReader { proxy in
                        RoundedRectangle(cornerRadius: 1.5).fill(.white.opacity(0.1))
                            .overlay(alignment: .leading) {
                                Rectangle().fill(color).frame(width: proxy.size.width * min(1, max(0, Double(remaining) / 10 - Double(index))))
                            }.clipShape(RoundedRectangle(cornerRadius: 1.5))
                    }
                }
            }.frame(height: 7)
                .accessibilityElement(children: .ignore).accessibilityLabel("\(name)剩余\(remaining)百分比")
                .animation(.easeOut(duration: 0.25), value: remaining)
        }
    }

    private var quotaPage: some View {
        VStack(alignment: .leading, spacing: 10) {
            Text("额度窗口").font(.system(size: 18, weight: .semibold))
            meter("5 小时窗口", value: store.primaryRemaining)
            Text("重置倒计时  \(store.countdown(store.primaryReset))").font(.system(size: 9, design: .monospaced)).foregroundStyle(muted)
            Divider()
            meter("7 天窗口", value: store.secondaryRemaining)
            Text("重置倒计时  \(store.countdown(store.secondaryReset))").font(.system(size: 9, design: .monospaced)).foregroundStyle(muted)
            Text("示例额度，未读取真实账户。\n窗口由实际接口数据决定。").font(.system(size: 9)).foregroundStyle(muted).lineSpacing(3)
            Spacer(minLength: 0)
        }.padding(18)
    }

    private var resetPage: some View {
        VStack(spacing: 12) {
            Text("arrow.counterclockwise.circle").hidden().frame(height: 0)
            Image(systemName: "arrow.counterclockwise.circle").font(.system(size: 40, weight: .light)).foregroundStyle(mint)
            Text("额外额度重置").font(.system(size: 17, weight: .semibold))
            Text("\(state.resetCredits) 次可用").font(.system(size: 25, weight: .medium, design: .rounded))
            Text("本地模拟 · 不消耗真实次数").font(.system(size: 9)).foregroundStyle(amber)
            Text(state.pending != nil ? "请先处理待批准请求" : state.resetCredits > 0 ? "↵ 打开确认 · 不会立即重置" : "暂无额外次数，请等待自动重置").font(.system(size: 9)).foregroundStyle(muted)
            if store.quotaDepleted { Text("等待 \(store.countdown(store.relevantReset))").font(.system(size: 9, design: .monospaced)).foregroundStyle(amber) }
            Spacer(minLength: 0)
        }.padding(20)
    }

    private var resetConfirmation: some View {
        VStack(spacing: 14) {
            Image(systemName: "arrow.counterclockwise").font(.system(size: 30)).foregroundStyle(amber)
            Text("确认模拟重置？").font(.system(size: 17, weight: .semibold))
            Text("将消耗 1 次模拟重置\n当前剩余 \(state.resetCredits) 次").font(.system(size: 12)).multilineTextAlignment(.center).lineSpacing(5)
            Text(state.resetCredits == 0 ? "没有可用的模拟重置次数" : state.resetConfirmed ? "松开后，长按 Return 1 秒" : "按 Return 进入二次确认").font(.system(size: 10)).foregroundStyle(muted)
            if state.resetConfirmed { holdMeter }
            Text("↑ 或 ↓ 返回 · 模拟操作").font(.system(size: 9)).foregroundStyle(amber)
        }.padding(18)
    }

    private var permission: some View {
        VStack(spacing: 7) {
            if let request = state.pending {
                if state.stage == .confirming {
                    Text("🥺").font(.custom("Apple Color Emoji", size: 57))
                    Text(state.selected == .allow ? "批准这个请求？" : "拒绝这个请求？").font(.system(size: 16, weight: .semibold))
                    Text(request.operation).font(.system(size: 10, design: .monospaced)).lineLimit(2).multilineTextAlignment(.center)
                    Text("请先松开 Return\n再按住 1 秒提交").font(.system(size: 10)).foregroundStyle(muted).multilineTextAlignment(.center).lineSpacing(3)
                    holdMeter
                    Text("短按 ↑ 返回 · ↓ 静音\n长按 ↑↓ 取消确认并换页").font(.system(size: 8)).foregroundStyle(muted)
                } else {
                    HStack(spacing: 8) {
                        Text("🥺").font(.custom("Apple Color Emoji", size: 35))
                        VStack(alignment: .leading, spacing: 3) {
                            Text("权限请求").font(.system(size: 14, weight: .semibold))
                            Text("命令执行 · \(request.id.uuidString.prefix(6))").font(.system(size: 8, design: .monospaced)).foregroundStyle(muted)
                        }
                        Spacer(minLength: 0)
                    }
                    Text(request.operation).font(.system(size: 11, weight: .medium, design: .monospaced))
                        .frame(maxWidth: .infinity, alignment: .leading).lineLimit(2)
                        .padding(8).background(.white.opacity(0.055), in: RoundedRectangle(cornerRadius: 7))
                    VStack(alignment: .leading, spacing: 4) {
                        Text("项目  companion-demo").lineLimit(1)
                        Text("范围  \(request.scope)").lineLimit(2)
                        Text("状态  \(state.status)").foregroundStyle(amber)
                    }.font(.system(size: 9)).frame(maxWidth: .infinity, alignment: .leading).foregroundStyle(muted)
                    if request.macOnly {
                        Text("请在 Mac 查看完整详情").font(.system(size: 10, weight: .semibold)).foregroundStyle(amber)
                        Text("长按 ↵ → 查看详情").font(.system(size: 9)).foregroundStyle(mint)
                    }
                    if state.stage == .sending || state.stage == .uncertain {
                        ProgressView().controlSize(.small).padding(3)
                        Text("收到回执前不会显示成功").font(.system(size: 9)).foregroundStyle(muted)
                    } else {
                        HStack(spacing: 7) {
                            choice("↑ 批准", .allow, disabled: request.macOnly)
                            choice("↓ 拒绝", .deny, disabled: false)
                        }
                        Text(state.selected == nil ? "未选择 · 长按 ↵ 详情 / 静音" : "短按 ↵ 确认 · 长按 ↵ 菜单").font(.system(size: 9)).foregroundStyle(muted)
                    }
                    HStack {
                        Text("\(max(0, Int(request.deadline - store.timestamp))) 秒有效").monospacedDigit()
                        Spacer()
                        Text(state.mutedRequest == request.id ? "已静音" : "提醒 \(state.reminderCount)/3")
                        if !state.queue.isEmpty { Text("排队 \(state.queue.count)") }
                    }.font(.system(size: 8)).foregroundStyle(muted)
                }
            }
        }.padding(.horizontal, 16).padding(.vertical, 9)
    }

    private var deviceMenu: some View {
        VStack(alignment: .leading, spacing: 3) {
            Text(store.requestVisible ? "请求菜单" : "快捷菜单").font(.system(size: 17, weight: .semibold)).padding(.bottom, 3)
            let items = store.navigation.menuItems(hasRequest: state.pending != nil)
            ForEach(Array(items.enumerated()), id: \.offset) { index, title in
                menuRow(title, value: "", selected: store.navigation.menuIndex == index, height: 20)
            }
            Spacer(minLength: 3)
            Text("↑↓ 选择 · ↵ 打开 · 长按 ↑↓ 换页").font(.system(size: 8)).foregroundStyle(muted)
        }.padding(15)
    }

    private var requestDetails: some View {
        VStack(alignment: .leading, spacing: 13) {
            let pages = store.detailPages
            let index = min(store.navigation.detailIndex, max(0, pages.count - 1))
            HStack {
                Text("请求详情").font(.system(size: 17, weight: .semibold))
                Spacer()
                Text("\(index + 1)/\(max(1, pages.count))").font(.system(size: 9, design: .monospaced)).foregroundStyle(muted)
            }
            if !pages.isEmpty {
                Text(pages[index].0).font(.system(size: 10, weight: .medium)).foregroundStyle(mint)
                Text(pages[index].1).font(.system(size: 10, design: .monospaced)).foregroundStyle(.white.opacity(0.9))
                    .fixedSize(horizontal: false, vertical: true).lineSpacing(4)
            }
            Spacer(minLength: 2)
            if state.pending?.macOnly == true { Text("高风险：仍需在真实 Codex 审批").font(.system(size: 9)).foregroundStyle(amber) }
            Text("短按 ↑↓ 看详情 · 长按 ↑↓ 换页\n↵ 返回权限页").font(.system(size: 8)).foregroundStyle(muted)
        }.padding(18)
    }

    private var settingsPage: some View {
        VStack(alignment: .leading, spacing: 6) {
            Text("声音设置").font(.system(size: 17, weight: .semibold)).padding(.bottom, 3)
            menuRow("提示音", value: store.soundEnabled ? "开启" : "关闭", selected: store.navigation.settingIndex == 0)
            menuRow("音量", value: "\(Int(store.volume))%", selected: store.navigation.settingIndex == 1)
            menuRow("提醒间隔", value: "\(Int(store.interval)) 秒", selected: store.navigation.settingIndex == 2)
            menuRow("互动音效", value: store.touchSound ? "开启" : "关闭", selected: store.navigation.settingIndex == 3)
            menuRow("返回主页", value: "↵", selected: store.navigation.settingIndex == 4)
            Spacer(minLength: 2)
            Text("短按 ↑↓ 选项 · ↵ 修改\n长按 ↑ 上一页 · 长按 ↓ 下一页")
                .font(.system(size: 9)).foregroundStyle(muted).lineSpacing(3)
                .fixedSize(horizontal: false, vertical: true)
        }.padding(17)
    }

    private var historyPage: some View {
        VStack(alignment: .leading, spacing: 12) {
            Text("事件记录").font(.system(size: 17, weight: .semibold))
            if state.log.isEmpty {
                Text("还没有事件").font(.system(size: 12)).foregroundStyle(muted)
            } else {
                let index = min(store.navigation.historyIndex, state.log.count - 1)
                Text("\(index + 1) / \(state.log.count)").font(.system(size: 10, design: .monospaced)).foregroundStyle(mint)
                Text(state.log[index]).font(.system(size: 12)).lineSpacing(5)
            }
            Spacer()
            Text("短按 ↑↓ 事件 · ↵ 返回主页\n长按 ↑ 上一页 · 长按 ↓ 下一页").font(.system(size: 9)).foregroundStyle(muted).lineSpacing(3)
        }.padding(18)
    }

    private var wifiPage: some View {
        VStack(alignment: .leading, spacing: 6) {
            Text("Wi-Fi 与校时").font(.system(size: 16, weight: .semibold))
            Text("设备配网流程演示").font(.system(size: 9)).foregroundStyle(amber)
            switch store.wifi {
            case .unconfigured:
                Text("Wi-Fi 未配置").font(.system(size: 13, weight: .medium))
                Text("↵ 开始蓝牙配网\n手机发送 2.4 GHz Wi-Fi\n名称与密码，无需逐字按键输入。")
                    .font(.system(size: 10)).foregroundStyle(muted).lineSpacing(3).fixedSize(horizontal: false, vertical: true)
            case .provisioning:
                Text("等待手机发送网络").font(.system(size: 12, weight: .medium)).foregroundStyle(mint)
                Text("真机方案：BLUFI 配网\n选择设备 → 输入 Wi-Fi\n拿到 IP 后退出蓝牙配网。")
                    .font(.system(size: 10)).foregroundStyle(muted).lineSpacing(3).fixedSize(horizontal: false, vertical: true)
                Text("↵ 模拟提交并连接").font(.system(size: 10, weight: .semibold))
            case .joining:
                Text("正在模拟连接…").font(.system(size: 12)).foregroundStyle(mint)
                Text("↵ 取消").font(.system(size: 10)).foregroundStyle(muted)
            case .connected:
                Text("示例网络已连接").font(.system(size: 12, weight: .medium)).foregroundStyle(mint)
                Text("SSID：Demo-WiFi（模拟）\n↵ 重新配网")
                    .font(.system(size: 10)).foregroundStyle(muted).lineSpacing(4)
            }
            Divider()
            Text(store.clockMessage).font(.system(size: 10)).foregroundStyle(store.clockAnchor == nil ? amber : mint)
            Text("校时使用 Mac 真实网络；\n本页不创建真实蓝牙连接。")
                .font(.system(size: 9)).foregroundStyle(muted).lineSpacing(3)
            Spacer(minLength: 0)
            Text("↑↓ 换页 · 长按 ↵ 菜单").font(.system(size: 9)).foregroundStyle(muted)
        }.padding(17)
    }

    private func menuRow(_ title: String, value: String, selected: Bool, height: CGFloat = 27) -> some View {
        HStack(spacing: 5) {
            Text(selected ? "›" : " ").foregroundStyle(mint).frame(width: 7)
            Text(title).font(.system(size: 11, weight: selected ? .semibold : .regular))
            Spacer(minLength: 0)
            Text(value).font(.system(size: 10, weight: .medium)).foregroundStyle(selected ? mint : muted)
        }.padding(.horizontal, 7).frame(height: height)
            .background(selected ? mint.opacity(0.1) : .clear, in: RoundedRectangle(cornerRadius: 6))
            .foregroundStyle(selected ? .white : muted)
    }

    private var holdMeter: some View {
        VStack(spacing: 6) {
            GeometryReader { proxy in
                Capsule().fill(.white.opacity(0.12))
                    .overlay(alignment: .leading) { Capsule().fill(mint).frame(width: proxy.size.width * min(1, max(0, store.holdProgress))) }
            }.frame(height: 8)
            Text(store.holdProgress > 0 ? "保持按住… \(Int(store.holdProgress * 100))%" : "等待长按确认")
                .font(.system(size: 9, design: .monospaced)).foregroundStyle(mint)
        }.padding(.vertical, 8)
    }

    private func choice(_ title: String, _ value: Choice, disabled: Bool) -> some View {
        Button { store.choose(value) } label: {
            Text(title).font(.system(size: 11, weight: .semibold)).frame(maxWidth: .infinity).padding(.vertical, 8)
                .foregroundStyle(disabled ? muted.opacity(0.5) : state.selected == value ? ink : .white)
                .background(state.selected == value ? (value == .allow ? mint : amber) : .white.opacity(0.06), in: RoundedRectangle(cornerRadius: 7))
        }.buttonStyle(.plain).disabled(disabled || !state.connected)
    }

    private var dots: some View {
        HStack(spacing: 5) { ForEach(0..<DevicePage.allCases.count, id: \.self) { index in Circle().fill(store.page == index ? mint : muted.opacity(0.3)).frame(width: 4, height: 4) } }
            .frame(maxWidth: .infinity)
    }
}

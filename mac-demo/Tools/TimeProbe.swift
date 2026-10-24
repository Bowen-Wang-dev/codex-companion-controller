import Foundation
import CompanionCore

@main struct TimeProbe {
    static func main() async {
        do {
            let anchor = try await NetworkTimeClient.read()
            print("PASS HTTPS time calibration")
            print("source: \(anchor.source)")
            print("UTC: \(anchor.date(at: ProcessInfo.processInfo.systemUptime).ISO8601Format())")
            print("estimated uncertainty: ±\(anchor.uncertainty) s")
        } catch { print("FAIL HTTPS time calibration: \(error)"); exit(1) }
    }
}

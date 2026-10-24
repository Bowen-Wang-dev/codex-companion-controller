import Foundation

public struct ClockAnchor: Sendable {
    public let utc: Date
    public let uptime: TimeInterval
    public let source: String
    public let uncertainty: TimeInterval
    public init(utc: Date, uptime: TimeInterval, source: String, uncertainty: TimeInterval) {
        self.utc = utc; self.uptime = uptime; self.source = source; self.uncertainty = uncertainty
    }
    public func date(at currentUptime: TimeInterval) -> Date {
        utc.addingTimeInterval(max(0, currentUptime - uptime))
    }
}

public enum ClockError: Error { case invalidResponse, staleResponse, slowResponse }

public enum NetworkClock {
    // HTTPS Date has one-second granularity. This is display-clock calibration,
    // not NTP precision, and must never control approval expiry or key holds.
    public static func parse(status: Int, date: String?, age: String?, roundTrip: TimeInterval, receivedUptime: TimeInterval, source: String) throws -> ClockAnchor {
        guard (200..<300).contains(status), let date else { throw ClockError.invalidResponse }
        guard roundTrip >= 0, roundTrip <= 4 else { throw ClockError.slowResponse }
        if let age, Double(age) == nil || Double(age)! > 3 { throw ClockError.staleResponse }
        let formatter = DateFormatter()
        formatter.locale = Locale(identifier: "en_US_POSIX")
        formatter.timeZone = TimeZone(secondsFromGMT: 0)
        formatter.dateFormat = "EEE, dd MMM yyyy HH:mm:ss zzz"
        guard let serverDate = formatter.date(from: date), serverDate.timeIntervalSince1970 > 1577836800 else { throw ClockError.invalidResponse }
        return ClockAnchor(utc: serverDate.addingTimeInterval(roundTrip / 2), uptime: receivedUptime, source: source, uncertainty: 1 + roundTrip / 2)
    }
}

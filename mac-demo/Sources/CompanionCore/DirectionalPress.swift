import Foundation

public enum DirectionGesture: Equatable, Sendable {
    case short(Int), long(Int)
}

// A press has exactly one result: short on release, or long at the threshold.
// Keep a consumed press until release so key repeats cannot turn another page.
public struct DirectionalPress: Sendable {
    public static let longThreshold: TimeInterval = 0.65
    private var direction: Int?
    private var began: TimeInterval = 0
    private var consumed = false
    public init() {}

    @discardableResult public mutating func press(_ value: Int, at now: TimeInterval) -> Bool {
        guard direction == nil, value == -1 || value == 1 else { return false }
        direction = value; began = now; consumed = false
        return true
    }

    public mutating func tick(at now: TimeInterval) -> DirectionGesture? {
        guard let direction, !consumed, now - began >= Self.longThreshold else { return nil }
        consumed = true
        return .long(direction)
    }

    public mutating func release(_ value: Int, at now: TimeInterval) -> DirectionGesture? {
        guard direction == value else { return nil }
        defer { reset() }
        guard !consumed else { return nil }
        return now - began >= Self.longThreshold ? .long(value) : .short(value)
    }

    public mutating func cancelUntilRelease() { consumed = true }
    public mutating func reset() { direction = nil; consumed = false }
}

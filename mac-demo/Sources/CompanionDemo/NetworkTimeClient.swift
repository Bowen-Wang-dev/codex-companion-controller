import Foundation
import CompanionCore

struct NetworkTimeClient {
    static func read() async throws -> ClockAnchor {
        let configuration = URLSessionConfiguration.ephemeral
        configuration.urlCache = nil
        configuration.httpCookieStorage = nil
        configuration.httpShouldSetCookies = false
        configuration.requestCachePolicy = .reloadIgnoringLocalAndRemoteCacheData
        configuration.timeoutIntervalForRequest = 5
        configuration.timeoutIntervalForResource = 6
        let session = URLSession(configuration: configuration)
        defer { session.invalidateAndCancel() }
        let sources = ["https://www.google.com/generate_204", "https://www.apple.com/"]
        var lastError: any Error = ClockError.invalidResponse
        for source in sources {
            do {
                let url = URL(string: source + "?companion_time=" + UUID().uuidString)!
                var request = URLRequest(url: url)
                request.httpMethod = "HEAD"
                request.setValue("no-cache, no-store", forHTTPHeaderField: "Cache-Control")
                let started = ProcessInfo.processInfo.systemUptime
                let (_, response) = try await session.data(for: request)
                let received = ProcessInfo.processInfo.systemUptime
                guard let http = response as? HTTPURLResponse, http.url?.scheme == "https", http.url?.host == url.host else { throw ClockError.invalidResponse }
                return try NetworkClock.parse(status: http.statusCode, date: http.value(forHTTPHeaderField: "Date"), age: http.value(forHTTPHeaderField: "Age"), roundTrip: received - started, receivedUptime: received, source: url.host!)
            } catch { lastError = error }
        }
        throw lastError
    }
}

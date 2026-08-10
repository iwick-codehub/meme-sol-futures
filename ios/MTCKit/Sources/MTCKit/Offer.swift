import Foundation

/// An MTC is a signed offer record, not a coin. It is a QR payload that a
/// reader validates offline; nothing about it touches a chain, and it carries
/// no transferable value. Keeping that true is what keeps the app out of
/// App Review's cryptocurrency rules entirely.
public struct Offer: Codable, Equatable, Sendable, Identifiable {
    public enum State: String, Codable, Sendable { case issued, redeemed, expired }

    public let id: String
    public let brand: String
    public let item: String
    public let valueCents: Int
    public let fiscalYear: Int
    public let startWeek: Int
    public let durationWeeks: Int
    public var state: State

    public init(id: String, brand: String, item: String, valueCents: Int,
                fiscalYear: Int, startWeek: Int, durationWeeks: Int,
                state: State = .issued) {
        self.id = id; self.brand = brand; self.item = item
        self.valueCents = valueCents; self.fiscalYear = fiscalYear
        self.startWeek = startWeek; self.durationWeeks = durationWeeks
        self.state = state
    }

    public var close: (fiscalYear: Int, week: Int) {
        WalmartCalendar.closeWeek(fiscalYear: fiscalYear,
                                  startWeek: startWeek, duration: durationWeeks)
    }

    public var opensAt: Date {
        WalmartCalendar.weekStart(fiscalYear: fiscalYear, week: startWeek)
    }

    /// Friday 23:59:59 Eastern of the closing week.
    public var expiresAt: Date {
        let c = close
        return WalmartCalendar.weekEnd(fiscalYear: c.fiscalYear, week: c.week)
    }

    public func isRedeemable(at now: Date = Date()) -> Bool {
        state == .issued && now >= opensAt && now <= expiresAt
    }

    /// The string that gets signed and encoded into the QR. Compact because a
    /// QR that needs a high version scans badly on a scuffed phone screen.
    public func payload(wallet: String) -> String {
        "MTC1|\(id)|\(wallet)|\(valueCents)|\(fiscalYear)|\(close.week)"
    }
}

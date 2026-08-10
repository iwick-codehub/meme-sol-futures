import Foundation

/// The Walmart retail calendar, which is the clock every MTC offer runs on.
///
/// A fiscal year opens on the Saturday on or before 1 February of the prior
/// calendar year, and weeks run Saturday 00:00:00 through Friday 23:59:59.
/// Week COUNT is derived from the gap between two anchors and never tabled —
/// that is what makes a 53-week year fall out on its own instead of needing a
/// special case that someone forgets to update.
///
/// Everything is Eastern time. HCP runs on Eastern, and a promo that expires
/// "Friday at midnight" has to mean the same instant for every reader.
public enum WalmartCalendar {

    public static let timeZone = TimeZone(identifier: "America/New_York")!

    public static var calendar: Calendar {
        var c = Calendar(identifier: .gregorian)
        c.timeZone = timeZone
        return c
    }

    /// First day of a fiscal year: the Saturday on or before 1 Feb of `fy - 1`.
    public static func yearStart(_ fiscalYear: Int) -> Date {
        let cal = calendar
        let anchor = cal.date(from: DateComponents(year: fiscalYear - 1, month: 2, day: 1))!
        // Foundation weekday: 1 = Sunday … 7 = Saturday. Saturday needs no roll,
        // Sunday rolls back one, Monday two, and so on.
        let back = cal.component(.weekday, from: anchor) % 7
        return cal.date(byAdding: .day, value: -back, to: anchor)!
    }

    /// 52 or 53, derived — never looked up.
    public static func weeks(in fiscalYear: Int) -> Int {
        let days = calendar.dateComponents(
            [.day], from: yearStart(fiscalYear), to: yearStart(fiscalYear + 1)).day!
        return days / 7
    }

    public static func weekStart(fiscalYear: Int, week: Int) -> Date {
        calendar.date(byAdding: .day, value: (week - 1) * 7, to: yearStart(fiscalYear))!
    }

    /// Friday 23:59:59 — the instant an offer in this week stops being redeemable.
    public static func weekEnd(fiscalYear: Int, week: Int) -> Date {
        let start = weekStart(fiscalYear: fiscalYear, week: week)
        let nextWeek = calendar.date(byAdding: .day, value: 7, to: start)!
        return calendar.date(byAdding: .second, value: -1, to: nextWeek)!
    }

    /// The fiscal year and week containing `date`.
    public static func period(for date: Date = Date()) -> (fiscalYear: Int, week: Int) {
        let cal = calendar
        // Start from the calendar-year guess and correct, because a January date
        // usually belongs to the fiscal year that opened the previous February.
        var fy = cal.component(.year, from: date) + 1
        while date < yearStart(fy) { fy -= 1 }
        while date >= yearStart(fy + 1) { fy += 1 }
        let days = cal.dateComponents([.day], from: yearStart(fy), to: date).day!
        return (fy, days / 7 + 1)
    }

    /// Where an offer opening at `week` for `duration` weeks closes. Rolls into
    /// the next fiscal year rather than clamping — a 26-week promo booked in
    /// week 40 is legitimate and must not be silently truncated at year end.
    public static func closeWeek(fiscalYear: Int, startWeek: Int, duration: Int)
        -> (fiscalYear: Int, week: Int) {
        precondition(duration >= 1, "an offer runs for at least one week")
        var fy = fiscalYear, w = startWeek + duration - 1
        while w > weeks(in: fy) { w -= weeks(in: fy); fy += 1 }
        return (fy, w)
    }

    public static func label(fiscalYear: Int, week: Int) -> String {
        "FY\(fiscalYear) WK\(week)"
    }
}

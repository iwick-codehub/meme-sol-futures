#!/usr/bin/env python3
"""Walmart fiscal calendar — the spine of the whole system.

Every offer window, every expiry and every ledger period in this system is
denominated in Walmart weeks. That is not cosmetic. Walmart's trade team plans,
funds and reports promotional dollars in these weeks, so a redemption ledger
kept in the same weeks reconciles to a brand's own trade report with no
translation step: no partial weeks, no allocation assumptions, no argument about
which week a Tuesday redemption belongs to.

THE RULES (verified against Walmart supplier documentation, Aug 2026):
  * A Walmart week runs SATURDAY 00:00:00 through FRIDAY 23:59:59.
  * The fiscal year runs Feb 1 - Jan 31 and BEGINS on the Saturday of the week
    containing Feb 1. FY2027 therefore begins Sat 31 Jan 2026.
  * Structure is 4-5-4: 13 weeks a quarter, 52 weeks, 364 days.
  * 364 < 365, so the calendar drifts a day a year and roughly every 5-6 years
    Walmart runs a 53-WEEK year. We MIRROR Walmart rather than computing our
    own length: the fiscal year ends the day before the next one begins, and
    whatever number of weeks that produces is the truth. (Todd's rule: "match
    walmart cal actions always".)

TIMEZONE: America/New_York, not a fixed EST offset. HCP is Eastern, and strict
EST is UTC-5 year round -- from March to November an offer set to expire
"Friday midnight" would actually die at 1:00am local, an hour the customer
believes they still have. America/New_York observes the DST shift so Friday
midnight is midnight on the wall clock every week of the year.
"""
from __future__ import annotations

from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo

TZ = ZoneInfo("America/New_York")
SATURDAY = 5          # date.weekday(): Mon=0 ... Sat=5, Sun=6


def fy_start(fiscal_year: int) -> date:
    """First day (a Saturday) of the given Walmart fiscal year.

    Walmart names a fiscal year for the calendar year it ENDS in: FY2027 runs
    Feb 2026 -> Jan 2027. So the anchor is Feb 1 of the PRIOR calendar year.
    """
    anchor = date(fiscal_year - 1, 2, 1)
    # step back to the Saturday that opens the week containing Feb 1
    return anchor - timedelta(days=(anchor.weekday() - SATURDAY) % 7)


def fy_weeks(fiscal_year: int) -> int:
    """Weeks in a fiscal year -- 52 normally, 53 when the drift catches up.

    Derived, never assumed: the year runs until the next one starts, so the
    week count falls out of the two anchors. This is how a 53-week year gets
    handled without a special case anywhere else in the system.
    """
    return (fy_start(fiscal_year + 1) - fy_start(fiscal_year)).days // 7


def week_start(fiscal_year: int, week: int) -> datetime:
    """Saturday 00:00:00 Eastern that opens Walmart week `week`."""
    if not 1 <= week <= fy_weeks(fiscal_year):
        raise ValueError(f"FY{fiscal_year} has {fy_weeks(fiscal_year)} weeks; "
                         f"week {week} does not exist")
    d = fy_start(fiscal_year) + timedelta(weeks=week - 1)
    return datetime(d.year, d.month, d.day, 0, 0, 0, tzinfo=TZ)


def week_end(fiscal_year: int, week: int) -> datetime:
    """Friday 23:59:59 Eastern that closes the week. Every expiry lands here."""
    return week_start(fiscal_year, week) + timedelta(days=7) - timedelta(seconds=1)


def current(when: datetime | None = None) -> tuple[int, int]:
    """(fiscal_year, week) containing `when`. Defaults to now, Eastern."""
    when = (when or datetime.now(TZ)).astimezone(TZ)
    d = when.date()
    # try the fiscal year this date most likely belongs to, then its neighbour
    for fy in (d.year + 1, d.year):
        s = fy_start(fy)
        if s <= d < fy_start(fy + 1):
            return fy, (d - s).days // 7 + 1
    raise ValueError(f"no fiscal year contains {d}")


def window(fiscal_year: int, start_week: int, weeks: int) -> tuple[datetime, datetime]:
    """Offer window: opens Saturday of start_week, closes Friday of the last week.

    `weeks` is 1-52 by policy -- one week minimum so no offer is shorter than a
    single planning period, and 52 maximum so no offer outlives the fiscal plan
    that funded it. In a 53-week year the DURATION cap stays 52; the calendar
    has 53 weeks but an offer still cannot span more than a year of them.
    """
    if not 1 <= weeks <= 52:
        raise ValueError("offer duration must be 1-52 Walmart weeks")
    last = start_week + weeks - 1
    total = fy_weeks(fiscal_year)
    # ROLL OVER rather than refuse. An earlier draft rejected any offer running
    # past fiscal year end, which quietly made a 52-week offer impossible unless
    # it began in week 1 -- the sim caught it on the first run. The rule Todd
    # set is duration: 1 to 52 weeks, from wherever it starts. A year-long offer
    # funded in week 27 simply lands in the next fiscal year, and the closing
    # week is reported in the fiscal year it actually falls in so it still
    # reconciles to the right trade plan.
    fy_close = fiscal_year
    while last > total:
        last -= total
        fy_close += 1
        total = fy_weeks(fy_close)
    return week_start(fiscal_year, start_week), week_end(fy_close, last)


def close_week(fiscal_year: int, start_week: int, weeks: int):
    """Which (fy, week) an offer actually closes in, after any rollover."""
    last = start_week + weeks - 1
    fy_close, total = fiscal_year, fy_weeks(fiscal_year)
    while last > total:
        last -= total
        fy_close += 1
        total = fy_weeks(fy_close)
    return fy_close, last


def label(fiscal_year: int, week: int) -> str:
    s, e = week_start(fiscal_year, week), week_end(fiscal_year, week)
    return (f"FY{fiscal_year} WK{week:02d}  "
            f"{s.strftime('%a %d %b')} - {e.strftime('%a %d %b %Y')}")


if __name__ == "__main__":
    fy, wk = current()
    print(f"NOW: {label(fy, wk)}   ({datetime.now(TZ):%Y-%m-%d %H:%M %Z})\n")
    for y in (2026, 2027, 2028, 2029, 2030, 2031, 2032):
        n = fy_weeks(y)
        print(f"  FY{y}: starts {fy_start(y)} ({fy_start(y).strftime('%a')}), "
              f"{n} weeks{'   <- 53-WEEK YEAR' if n == 53 else ''}")

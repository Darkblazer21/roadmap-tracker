"""Week clock: compute the current roadmap week from the start_date anchor.

``current_week_number(start_date, today)`` returns ceil((today - start_date)/7)
so day 0-6 = week 1, day 7-13 = week 2, etc. ``week_window(n)`` returns the
7-day datetime span that week n occupies, used later by the GitHub sync
verdict (did you commit inside the window?).
"""

from __future__ import annotations

import math
from datetime import date, datetime, timedelta


def current_week_number(start_date: date, today: date | None = None) -> int | None:
    """Return the 1-indexed current week, or None if start_date is in the future."""
    if start_date is None:
        return None
    today = today or date.today()
    if today < start_date:
        return None
    delta_days = (today - start_date).days
    return math.floor(delta_days / 7) + 1


def total_planned_weeks(start_date: date, roadmap_weeks: int = 56) -> int:
    """How many weeks have elapsed since start_date, capped at the plan length."""
    today = date.today()
    if today < start_date:
        return 0
    elapsed = math.floor((today - start_date).days / 7) + 1
    return min(elapsed, roadmap_weeks)


def week_window(
    week_number: int,
    start_date: date,
) -> tuple[datetime, datetime]:
    """Return the (start, end) datetimes spanning week ``week_number``.

    Week n starts at start_date + (n-1)*7 days, at 00:00 local.
    Week n ends at start_date + n*7 days, at 00:00 (exclusive).
    """
    if start_date is None:
        raise ValueError("start_date is required to compute a week window")
    start = datetime.combine(start_date + timedelta(days=(week_number - 1) * 7), datetime.min.time())
    end = datetime.combine(start_date + timedelta(days=week_number * 7), datetime.min.time())
    return start, end


def is_on_track(
    start_date: date,
    first_incomplete_week: int,
    today: date | None = None,
    tolerance: int = 2,
) -> tuple[bool, int]:
    """Compare the calendar week to the first incomplete plan week.

    Returns (on_track, gap). gap is the number of weeks the user is ahead
    (positive) or behind (negative) the plan. Within ``tolerance`` weeks is
    considered on_track to avoid noise from buffer periods.
    """
    if start_date is None:
        return True, 0
    today = today or date.today()
    calendar_week = current_week_number(start_date, today)
    if calendar_week is None:
        return True, 0  # plan hasn't started yet
    gap = calendar_week - first_incomplete_week
    return abs(gap) <= tolerance, gap
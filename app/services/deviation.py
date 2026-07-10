"""Deviation service: compare where you *are* (first incomplete week) to where
you *should be* (calendar week from start_date) and flag weeks-behind.

Respects ``buffer`` weeks (19-22, 33-34) so the dashboard doesn't alarm during
known dense phases. Returns a payload the frontend renders as a colored banner.
"""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.settings import AppSettings
from app.models.week import Week, WeekStatus
from app.services.week_clock import current_week_number

# Weeks of slack before the deviation banner appears.
DEFAULT_TOLERANCE = 2


async def compute_deviation(db: AsyncSession) -> dict:
    """Return a deviation banner payload, or an all-clear payload."""
    settings = (
        await db.execute(select(AppSettings).where(AppSettings.id == 1))
    ).scalar_one_or_none()
    if settings is None or settings.start_date is None:
        return {
            "status": "unknown",
            "message": "Set your start_date in Settings to enable deviation tracking.",
            "calendar_week": None,
            "first_incomplete_week": None,
            "gap": 0,
            "tolerance": DEFAULT_TOLERANCE,
        }

    cal_week = current_week_number(settings.start_date)
    if cal_week is None:
        return {
            "status": "not_started",
            "message": "Your roadmap hasn't started yet.",
            "calendar_week": None,
            "first_incomplete_week": None,
            "gap": 0,
            "tolerance": DEFAULT_TOLERANCE,
        }

    # Find the first week whose status is not 'done' or 'skipped'.
    weeks = (
        await db.execute(select(Week).order_by(Week.number))
    ).scalars().all()

    first_incomplete: int | None = None
    for w in weeks:
        if w.status not in (WeekStatus.done, WeekStatus.skipped):
            first_incomplete = w.number
            break

    if first_incomplete is None:
        return {
            "status": "complete",
            "message": "All weeks are done — congratulations!",
            "calendar_week": cal_week,
            "first_incomplete_week": None,
            "gap": 0,
            "tolerance": DEFAULT_TOLERANCE,
        }

    gap = cal_week - first_incomplete

    # Check if the user is inside a buffer zone (weeks 19-22 or 33-34).
    in_buffer = any(
        w.number == first_incomplete and w.buffer for w in weeks
        if first_incomplete - 2 <= w.number <= first_incomplete + 2
    )

    if gap <= 0:
        status = "on_track"
        message = f"You're on track — calendar week {cal_week}, working on week {first_incomplete}."
    elif gap <= DEFAULT_TOLERANCE and in_buffer:
        status = "buffer"
        message = f"{gap} week(s) behind, but you're in a known buffer zone — keep going."
    elif gap <= DEFAULT_TOLERANCE:
        status = "slight_delay"
        message = f"Slight delay — {gap} week(s) behind the calendar (week {first_incomplete} vs cal {cal_week})."
    else:
        status = "behind"
        message = f"⚠ {gap} week(s) behind plan (week {first_incomplete} vs calendar week {cal_week}). Consider using a buffer week or adjusting pace."

    return {
        "status": status,
        "message": message,
        "calendar_week": cal_week,
        "first_incomplete_week": first_incomplete,
        "gap": gap,
        "tolerance": DEFAULT_TOLERANCE,
        "in_buffer": in_buffer,
    }
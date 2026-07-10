"""Hours aggregator: roll session seconds into day/week/phase totals.

Pure DB-query helpers reused by the sessions router, the pomodoro engine
(M4, when completing a pomo bumps the week's actual_hours) and the Sunday
recap generator (M5).
"""

from __future__ import annotations

from collections import defaultdict
from datetime import datetime

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.session import Session
from app.models.week import Week
from app.schemas import WeekAggregate


async def aggregate_for_week(db: AsyncSession, week_id: int) -> WeekAggregate:
    """Compute total/breakdown for a single roadmap week."""
    result = await db.execute(
        select(Session).where(Session.week_id == week_id)
    )
    sessions = list(result.scalars().all())

    total_sec = 0.0
    by_type: dict[str, float] = defaultdict(float)
    by_day: dict[str, float] = defaultdict(float)

    for s in sessions:
        total_sec += s.duration_sec
        by_type[s.type.value] += s.duration_sec
        day_key = s.started_at.strftime("%Y-%m-%d")
        by_day[day_key] += s.duration_sec

    total_hours = total_sec / 3600.0

    # Fetch the week plan range + current actual_hours to compute flags.
    w = await db.get(Week, week_id)
    hours_min = float(w.hours_min) if w else 0.0
    hours_max = float(w.hours_max) if w else 0.0

    return WeekAggregate(
        week_id=week_id,
        total_sec=total_sec,
        total_hours=round(total_hours, 2),
        by_type=dict(by_type),
        by_day=dict(by_day),
        session_count=len(sessions),
        hours_min=hours_min,
        hours_max=hours_max,
        actual_hours=round(total_hours, 2),
        over_cap=total_hours > hours_max if hours_max > 0 else False,
        under_min=total_hours < hours_min if hours_min > 0 else False,
        in_range=(hours_min <= total_hours <= hours_max) if (hours_min > 0 or hours_max > 0) else True,
    )


async def bump_week_actual_hours(db: AsyncSession, week_id: int) -> Week:
    """Recompute and persist ``Week.actual_hours`` from all sessions.

    Called after every session insert/delete so the weeks list and the cap
    alert stay in sync with reality.
    """
    result = await db.execute(
        select(func.coalesce(func.sum(Session.duration_sec), 0.0)).where(
            Session.week_id == week_id
        )
    )
    total_sec = float(result.scalar_one())
    week = await db.get(Week, week_id)
    if week is not None:
        week.actual_hours = round(total_sec / 3600.0, 2)
        await db.flush()
    return week  # type: ignore[return-value]
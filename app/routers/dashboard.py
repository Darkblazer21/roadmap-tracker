"""Dashboard router: today's summary in one call.

Aggregates the current calendar week, this week's hours vs. target, last
7-day activity, pomodoro state (idle), deviation banner, and latest GitHub
verdict — so the dashboard page makes a single fetch to render everything.
"""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_db
from app.models.session import Session
from app.models.settings import AppSettings
from app.models.user import User
from app.models.week import Week, WeekStatus
from app.services.deviation import compute_deviation
from app.services.hours_aggregator import aggregate_for_week
from app.services.security import get_current_user
from app.services.week_clock import current_week_number

router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])


@router.get("")
async def get_dashboard(
    db: Annotated[AsyncSession, Depends(get_db)],
    _user: Annotated[User, Depends(get_current_user)],
) -> dict:
    """One-stop summary for the dashboard page."""
    settings = (
        await db.execute(select(AppSettings).where(AppSettings.id == 1))
    ).scalar_one_or_none()

    start_date = settings.start_date if settings else None
    cal_week = (
        current_week_number(start_date, tz=settings.timezone)
        if start_date and settings is not None
        else None
    )

    # Current week's aggregate.
    week = None
    week_agg = None
    if cal_week and cal_week > 0:
        week = await db.get(Week, cal_week)
        if week:
            week_agg = await aggregate_for_week(db, cal_week)

    # Last 7 days total hours.
    from datetime import datetime, timedelta, timezone

    cutoff = datetime.now(timezone.utc) - timedelta(days=7)
    result = await db.execute(
        select(func.coalesce(func.sum(Session.duration_sec), 0.0)).where(
            Session.started_at >= cutoff
        )
    )
    last_7d_sec = float(result.scalar_one())
    last_7d_hours = round(last_7d_sec / 3600.0, 2)

    # Active day count in the last 7 days.
    days_result = await db.execute(
        select(func.count(func.distinct(func.date_trunc("day", Session.started_at)))).where(
            Session.started_at >= cutoff
        )
    )
    active_days = int(days_result.scalar_one())

    # Deviation banner.
    deviation = await compute_deviation(db)

    # Done/in-progress/remaining week counts.
    weeks = (
        await db.execute(select(Week).order_by(Week.number))
    ).scalars().all()
    done = sum(1 for w in weeks if w.status == WeekStatus.done)
    in_progress = sum(1 for w in weeks if w.status == WeekStatus.in_progress)
    total = len(weeks)

    return {
        "calendar_week": cal_week,
        "current_week_theme": week.theme if week else None,
        "this_week": {
            "total_hours": week_agg.total_hours if week_agg else 0.0,
            "hours_min": week_agg.hours_min if week_agg else 0.0,
            "hours_max": week_agg.hours_max if week_agg else 0.0,
            "over_cap": week_agg.over_cap if week_agg else False,
            "under_min": week_agg.under_min if week_agg else False,
            "in_range": week_agg.in_range if week_agg else True,
        } if week_agg else None,
        "last_7_days": {
            "total_hours": last_7d_hours,
            "active_days": active_days,
        },
        "deviation": deviation,
        "week_counts": {
            "done": done,
            "in_progress": in_progress,
            "remaining": total - done - in_progress,
            "total": total,
        },
    }
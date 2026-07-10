"""Settings router: read, update, and reset the single-row AppSettings.

All routes are auth-protected. ``GET`` also returns the computed
``current_week`` so the frontend dashboard can highlight where the user is
in the plan without a separate call. ``POST /reset`` clears all user data
(sessions, daily logs, recaps, week statuses) so the user can start fresh.
"""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import delete, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_db
from app.models.daily_log import DailyLog
from app.models.recap import Recap
from app.models.session import Session
from app.models.settings import AppSettings
from app.models.user import User
from app.models.week import Week, WeekStatus
from app.schemas import SettingsOut, SettingsPatch
from app.services.security import get_current_user
from app.services.week_clock import current_week_number

router = APIRouter(prefix="/api/settings", tags=["settings"])


async def _get_singleton(db: AsyncSession) -> AppSettings:
    """Fetch the single settings row, creating it if it doesn't exist yet."""
    result = await db.execute(select(AppSettings).where(AppSettings.id == 1))
    settings = result.scalar_one_or_none()
    if settings is None:
        settings = AppSettings(id=1)
        db.add(settings)
        await db.flush()
    return settings


@router.get("", response_model=SettingsOut)
async def get_settings(
    db: Annotated[AsyncSession, Depends(get_db)],
    _user: Annotated[User, Depends(get_current_user)],
) -> AppSettings:
    return await _get_singleton(db)


@router.patch("", response_model=SettingsOut)
async def patch_settings(
    payload: SettingsPatch,
    db: Annotated[AsyncSession, Depends(get_db)],
    _user: Annotated[User, Depends(get_current_user)],
) -> AppSettings:
    settings = await _get_singleton(db)
    updates = payload.model_dump(exclude_unset=True)
    for field, value in updates.items():
        setattr(settings, field, value)
    await db.commit()
    await db.refresh(settings)
    return settings


@router.post("/reset")
async def reset_progress(
    db: Annotated[AsyncSession, Depends(get_db)],
    _user: Annotated[User, Depends(get_current_user)],
) -> dict:
    """Delete all sessions, daily logs, recaps, and reset every week to
    ``not_started`` with ``actual_hours = 0``. Also clears the pomodoro
    timer from Redis. The settings row (start_date, pomo config, repos) is
    preserved — only user *progress* is wiped.
    """
    # Clear user data tables.
    await db.execute(delete(Session))
    await db.execute(delete(DailyLog))
    await db.execute(delete(Recap))

    # Reset all weeks to not_started.
    await db.execute(
        update(Week).values(
            status=WeekStatus.not_started,
            actual_hours=0.0,
            recap_sunday=None,
            reviewed_at=None,
        )
    )

    # Clear pomodoro state from Redis.
    from app.services.redis_client import get_redis

    r = get_redis()
    await r.delete("pomo:state")

    await db.commit()

    return {"status": "reset", "cleared": {"sessions": True, "daily_logs": True, "recaps": True, "weeks": True}}


@router.get("/current-week")
async def get_current_week(
    db: Annotated[AsyncSession, Depends(get_db)],
    _user: Annotated[User, Depends(get_current_user)],
) -> dict[str, int | None]:
    """Return the week number the calendar says we're in right now."""
    settings = await _get_singleton(db)
    week = current_week_number(settings.start_date) if settings.start_date else None
    return {"current_week": week}
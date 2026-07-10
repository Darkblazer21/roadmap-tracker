"""Settings router: read and update the single-row AppSettings.

All routes are auth-protected. ``GET`` also returns the computed
``current_week`` so the frontend dashboard can highlight where the user is
in the plan without a separate call.
"""

from __future__ import annotations

from datetime import date
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_db
from app.models.settings import AppSettings
from app.models.user import User
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


@router.get("/current-week")
async def get_current_week(
    db: Annotated[AsyncSession, Depends(get_db)],
    _user: Annotated[User, Depends(get_current_user)],
) -> dict[str, int | None]:
    """Return the week number the calendar says we're in right now."""
    settings = await _get_singleton(db)
    week = current_week_number(settings.start_date) if settings.start_date else None
    return {"current_week": week}
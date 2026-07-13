"""Pomodoro router: start / pause / resume / stop / state.

All routes require JWT. The state is hosted in Redis (so a browser refresh
can't lose a running timer); on each poll ``sync_state`` advances transitions
and persists newly completed pomodoro sessions to the DB.
"""

from __future__ import annotations

from typing import Annotated

import redis.asyncio as redis
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_db
from app.models.settings import AppSettings
from app.models.user import User
from app.models.week import Week
from app.schemas import PomoStart, PomoStateView
from app.services.pomodoro_machine import (
    PomoConfig,
    pause_timer,
    resume_timer,
    start_timer,
    stop_timer,
    sync_state,
)
from app.services.redis_client import get_redis
from app.services.security import get_current_user
from app.services.week_clock import current_week_number

router = APIRouter(prefix="/api/pomo", tags=["pomodoro"])


async def _load_config(db: AsyncSession) -> PomoConfig:
    """Pull the pomodoro config from the single-row settings table."""
    settings = (
        await db.execute(select(AppSettings).where(AppSettings.id == 1))
    ).scalar_one_or_none()
    if settings is None:
        from app.config import settings as cfg

        return PomoConfig.from_minutes(
            cfg.pomo_work_min,
            cfg.pomo_short_break_min,
            cfg.pomo_long_break_min,
            cfg.pomo_marathon_break_min,
            cfg.pomo_cycles_per_set,
            cfg.pomo_cycles_per_marathon,
        )
    return PomoConfig.from_minutes(
        settings.pomo_work_min,
        settings.pomo_short_break_min,
        settings.pomo_long_break_min,
        settings.pomo_marathon_break_min,
        settings.pomo_cycles_per_set,
        settings.pomo_cycles_per_marathon,
    )


async def _resolve_week_id(
    db: AsyncSession,
    explicit: int | None,
) -> int:
    """Defaults to the current calendar week derived from start_date."""
    if explicit is not None:
        week = await db.get(Week, explicit)
        if week is None:
            raise HTTPException(status_code=404, detail=f"Week {explicit} not found")
        return explicit
    # Fall back to settings.start_date.
    settings = (
        await db.execute(select(AppSettings).where(AppSettings.id == 1))
    ).scalar_one_or_none()
    if settings is None or settings.start_date is None:
        raise HTTPException(
            status_code=400,
            detail="No week_id given and settings.start_date is not set yet",
        )
    week = current_week_number(settings.start_date, tz=settings.timezone)
    if week is None:
        raise HTTPException(
            status_code=400,
            detail="The roadmap hasn't started yet (start_date is in the future)",
        )
    return week


@router.get("/state", response_model=PomoStateView)
async def get_state(
    db: Annotated[AsyncSession, Depends(get_db)],
    _user: Annotated[User, Depends(get_current_user)],
    r: Annotated[redis.Redis, Depends(get_redis)],
) -> PomoStateView:
    cfg = await _load_config(db)
    view = await sync_state(r, db, cfg)
    return PomoStateView(**view.to_dict())


@router.post("/start", response_model=PomoStateView)
async def start(
    payload: PomoStart,
    db: Annotated[AsyncSession, Depends(get_db)],
    _user: Annotated[User, Depends(get_current_user)],
    r: Annotated[redis.Redis, Depends(get_redis)],
) -> PomoStateView:
    cfg = await _load_config(db)
    week_id = await _resolve_week_id(db, payload.week_id)
    await start_timer(r, week_id, cfg)
    view = await sync_state(r, db, cfg)
    return PomoStateView(**view.to_dict())


@router.post("/pause", response_model=PomoStateView)
async def pause(
    db: Annotated[AsyncSession, Depends(get_db)],
    _user: Annotated[User, Depends(get_current_user)],
    r: Annotated[redis.Redis, Depends(get_redis)],
) -> PomoStateView:
    cfg = await _load_config(db)
    await pause_timer(r)
    view = await sync_state(r, db, cfg)
    return PomoStateView(**view.to_dict())


@router.post("/resume", response_model=PomoStateView)
async def resume(
    db: Annotated[AsyncSession, Depends(get_db)],
    _user: Annotated[User, Depends(get_current_user)],
    r: Annotated[redis.Redis, Depends(get_redis)],
) -> PomoStateView:
    cfg = await _load_config(db)
    await resume_timer(r)
    view = await sync_state(r, db, cfg)
    return PomoStateView(**view.to_dict())


@router.post("/stop", response_model=PomoStateView)
async def stop(
    db: Annotated[AsyncSession, Depends(get_db)],
    _user: Annotated[User, Depends(get_current_user)],
    r: Annotated[redis.Redis, Depends(get_redis)],
) -> PomoStateView:
    cfg = await _load_config(db)
    await stop_timer(r)
    view = await sync_state(r, db, cfg)
    return PomoStateView(**view.to_dict())
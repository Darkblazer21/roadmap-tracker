"""Daily log router: CRUD + scoped list.

A (week_id, log_date) pair is unique; upserting by that pair keeps the user
from having to remember the row id when they re-submit today's log.
"""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_db
from app.models.daily_log import DailyLog
from app.models.user import User
from app.models.week import Week
from app.schemas import DailyLogOut, DailyLogPatch
from app.schemas.daily_log import DailyLogBase
from app.services.security import get_current_user

router = APIRouter(prefix="/api/daily-logs", tags=["daily-logs"])


@router.get("", response_model=list[DailyLogOut])
async def list_daily_logs(
    db: Annotated[AsyncSession, Depends(get_db)],
    _user: Annotated[User, Depends(get_current_user)],
    week_id: Annotated[int | None, Query()] = None,
) -> list[DailyLog]:
    stmt = select(DailyLog).order_by(DailyLog.log_date.desc())
    if week_id is not None:
        stmt = stmt.where(DailyLog.week_id == week_id)
    result = await db.execute(stmt)
    return list(result.scalars().all())


@router.post("", response_model=DailyLogOut, status_code=201)
async def upsert_daily_log(
    payload: DailyLogBase,
    db: Annotated[AsyncSession, Depends(get_db)],
    _user: Annotated[User, Depends(get_current_user)],
) -> DailyLog:
    """Create or replace the log for a given (week_id, log_date)."""
    week = await db.get(Week, payload.week_id)
    if week is None:
        raise HTTPException(status_code=404, detail=f"Week {payload.week_id} not found")

    result = await db.execute(
        select(DailyLog).where(
            DailyLog.week_id == payload.week_id,
            DailyLog.log_date == payload.log_date,
        )
    )
    log = result.scalar_one_or_none()
    if log is None:
        log = DailyLog(**payload.model_dump())
        db.add(log)
    else:
        for field, value in payload.model_dump().items():
            setattr(log, field, value)
    await db.commit()
    await db.refresh(log)
    return log


@router.patch("/{log_id}", response_model=DailyLogOut)
async def patch_daily_log(
    log_id: int,
    payload: DailyLogPatch,
    db: Annotated[AsyncSession, Depends(get_db)],
    _user: Annotated[User, Depends(get_current_user)],
) -> DailyLog:
    log = await db.get(DailyLog, log_id)
    if log is None:
        raise HTTPException(status_code=404, detail=f"Daily log {log_id} not found")
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(log, field, value)
    await db.commit()
    await db.refresh(log)
    return log


@router.delete("/{log_id}", status_code=204)
async def delete_daily_log(
    log_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    _user: Annotated[User, Depends(get_current_user)],
) -> None:
    log = await db.get(DailyLog, log_id)
    if log is None:
        raise HTTPException(status_code=404, detail=f"Daily log {log_id} not found")
    await db.delete(log)
    await db.commit()
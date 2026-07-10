"""Weeks and phases read API.

Endpoints:
    GET  /api/weeks          - all phases with their weeks (phase accordion)
    GET  /api/weeks/{number} - a single week by plan number
    PATCH /api/weeks/{number} - update user state (auth-protected from M2)
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.db import get_db
from app.models.phase import Phase
from app.models.week import Week
from app.schemas import PhaseWithWeeks, WeekOut, WeekPatch

router = APIRouter(prefix="/api", tags=["weeks"])


@router.get("/weeks", response_model=list[PhaseWithWeeks])
async def list_weeks(db: AsyncSession = Depends(get_db)) -> list[Phase]:
    """Return all phases with their ordered weeks for the sidebar."""
    result = await db.execute(
        select(Phase)
        .options(selectinload(Phase.weeks))
        .order_by(Phase.position)
    )
    return list(result.scalars().unique())


@router.get("/weeks/{number}", response_model=WeekOut)
async def get_week(number: int, db: AsyncSession = Depends(get_db)) -> Week:
    result = await db.execute(select(Week).where(Week.number == number))
    week = result.scalar_one_or_none()
    if week is None:
        raise HTTPException(status_code=404, detail=f"Week {number} not found")
    return week


@router.patch("/weeks/{number}", response_model=WeekOut)
async def patch_week(
    number: int,
    payload: WeekPatch,
    db: AsyncSession = Depends(get_db),
) -> Week:
    """Update a week's user state (actual_hours, recap, status, reviewed_at).

    In M1 this is unprotected. M2 wraps it with JWT auth via Depends(get_current_user).
    """
    result = await db.execute(select(Week).where(Week.number == number))
    week = result.scalar_one_or_none()
    if week is None:
        raise HTTPException(status_code=404, detail=f"Week {number} not found")

    updates = payload.model_dump(exclude_unset=True)
    for field, value in updates.items():
        setattr(week, field, value)

    await db.commit()
    await db.refresh(week)
    return week
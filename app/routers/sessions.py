"""Sessions router: create / list / aggregate / delete.

All routes require JWT auth - logging focus hours is a user action.
Creating a ``pomodoro`` session also triggers ``actual_hours`` recompute
and the ``hours_max`` cap alert ( decisión M5 ).
"""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_db
from app.models.session import Session
from app.models.user import User
from app.models.week import Week
from app.schemas import SessionCreate, SessionOut, WeekAggregate
from app.services.hours_aggregator import aggregate_for_week, bump_week_actual_hours
from app.services.security import get_current_user

router = APIRouter(prefix="/api/sessions", tags=["sessions"])


@router.post("", response_model=SessionOut, status_code=201)
async def create_session(
    payload: SessionCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    _user: Annotated[User, Depends(get_current_user)],
) -> Session:
    """Log a focus/pomodoro session against a roadmap week.

    Recomputes the week's ``actual_hours`` afterwards so the cap alert fires
    immediately (decision: completed pomodoros count toward ``hours_max``).
    """
    week = await db.get(Week, payload.week_id)
    if week is None:
        raise HTTPException(status_code=404, detail=f"Week {payload.week_id} not found")

    session = Session(
        week_id=payload.week_id,
        type=payload.type,
        duration_sec=payload.duration_sec,
        started_at=payload.started_at,  # None → server_default now()
        ended_at=payload.ended_at,
        notes=payload.notes,
    )
    db.add(session)
    await db.flush()  # get the id + server-default started_at

    await bump_week_actual_hours(db, payload.week_id)
    await db.commit()
    await db.refresh(session)
    return session


@router.get("", response_model=list[SessionOut])
async def list_sessions(
    db: Annotated[AsyncSession, Depends(get_db)],
    _user: Annotated[User, Depends(get_current_user)],
    week_id: Annotated[int | None, Query()] = None,
) -> list[Session]:
    """List sessions, optionally filtered by week."""
    stmt = select(Session).order_by(Session.started_at.desc())
    if week_id is not None:
        stmt = stmt.where(Session.week_id == week_id)
    result = await db.execute(stmt)
    return list(result.scalars().all())


@router.get("/aggregate", response_model=WeekAggregate)
async def get_aggregate(
    week_id: Annotated[int, Query()],
    db: Annotated[AsyncSession, Depends(get_db)],
    _user: Annotated[User, Depends(get_current_user)],
) -> WeekAggregate:
    """Return total hours + day/type breakdown + cap flags for a week."""
    week = await db.get(Week, week_id)
    if week is None:
        raise HTTPException(status_code=404, detail=f"Week {week_id} not found")
    return await aggregate_for_week(db, week_id)


@router.delete("/{session_id}", status_code=204)
async def delete_session(
    session_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    _user: Annotated[User, Depends(get_current_user)],
) -> None:
    result = await db.execute(select(Session).where(Session.id == session_id))
    session = result.scalar_one_or_none()
    if session is None:
        raise HTTPException(status_code=404, detail=f"Session {session_id} not found")
    week_id = session.week_id
    await db.delete(session)
    await bump_week_actual_hours(db, week_id)
    await db.commit()
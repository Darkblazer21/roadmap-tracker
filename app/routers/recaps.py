"""Recaps router: generate a draft (ephemeral) + save/list the edited version.

The "Generate" action does not persist anything; it returns a draft the user
can edit. Saving upserts a single ``Recap`` row per week (idempotent).
"""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_db
from app.models.recap import Recap
from app.models.user import User
from app.schemas.recap import RecapDraft, RecapOut, RecapSave
from app.services.recap_generator import WeekNotFoundError, generate_draft
from app.services.security import get_current_user

router = APIRouter(prefix="/api/recaps", tags=["recaps"])


@router.get("", response_model=list[RecapOut])
async def list_recaps(
    db: Annotated[AsyncSession, Depends(get_db)],
    _user: Annotated[User, Depends(get_current_user)],
    from_week: Annotated[int | None, Query(alias="from")] = None,
    to_week: Annotated[int | None, Query(alias="to")] = None,
) -> list[Recap]:
    stmt = select(Recap).order_by(Recap.week_id)
    if from_week is not None:
        stmt = stmt.where(Recap.week_id >= from_week)
    if to_week is not None:
        stmt = stmt.where(Recap.week_id <= to_week)
    result = await db.execute(stmt)
    return list(result.scalars().all())


@router.get("/{week_id}", response_model=RecapOut)
async def get_recap(
    week_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    _user: Annotated[User, Depends(get_current_user)],
) -> Recap:
    recap = await db.get(Recap, week_id)
    if recap is None:
        raise HTTPException(status_code=404, detail=f"No recap saved for week {week_id}")
    return recap


@router.post("/{week_id}/generate", response_model=RecapDraft)
async def generate(
    week_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    _user: Annotated[User, Depends(get_current_user)],
) -> RecapDraft:
    """Return a draft 3-line recap; does NOT persist (user edits then saves)."""
    try:
        return await generate_draft(db, week_id)
    except WeekNotFoundError:
        raise HTTPException(status_code=404, detail=f"Week {week_id} not found")


@router.put("/{week_id}", response_model=RecapOut)
async def save(
    week_id: int,
    payload: RecapSave,
    db: Annotated[AsyncSession, Depends(get_db)],
    _user: Annotated[User, Depends(get_current_user)],
) -> Recap:
    """Upsert the user-edited recap for week ``week_id``."""
    recap = await db.get(Recap, week_id)
    if recap is None:
        recap = Recap(week_id=week_id, **payload.model_dump(exclude={"week_id"}))
        db.add(recap)
    else:
        for field in ("successes", "blockers", "next_step"):
            value = getattr(payload, field)
            if value is not None:
                setattr(recap, field, value)
    await db.commit()
    await db.refresh(recap)
    return recap
"""Export router: download session + daily log + recap history as JSON or CSV."""

from __future__ import annotations

import csv
import io
from typing import Annotated

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_db
from app.models.daily_log import DailyLog
from app.models.recap import Recap
from app.models.session import Session
from app.models.user import User
from app.services.security import get_current_user

router = APIRouter(prefix="/api/export", tags=["export"])


@router.get("/sessions.json")
async def export_sessions_json(
    db: Annotated[AsyncSession, Depends(get_db)],
    _user: Annotated[User, Depends(get_current_user)],
) -> dict:
    result = await db.execute(select(Session).order_by(Session.started_at))
    sessions = result.scalars().all()
    return {
        "sessions": [
            {
                "id": s.id,
                "week_id": s.week_id,
                "type": s.type.value,
                "started_at": s.started_at.isoformat() if s.started_at else None,
                "duration_sec": s.duration_sec,
                "duration_hours": round(s.duration_sec / 3600.0, 2),
                "notes": s.notes,
            }
            for s in sessions
        ]
    }


@router.get("/sessions.csv")
async def export_sessions_csv(
    db: Annotated[AsyncSession, Depends(get_db)],
    _user: Annotated[User, Depends(get_current_user)],
) -> StreamingResponse:
    result = await db.execute(select(Session).order_by(Session.started_at))
    sessions = result.scalars().all()

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["id", "week_id", "type", "started_at", "duration_sec", "duration_hours", "notes"])
    for s in sessions:
        writer.writerow([
            s.id, s.week_id, s.type.value,
            s.started_at.isoformat() if s.started_at else "",
            s.duration_sec, round(s.duration_sec / 3600.0, 2),
            s.notes or "",
        ])
    output.seek(0)
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=sessions.csv"},
    )


@router.get("/all.json")
async def export_all_json(
    db: Annotated[AsyncSession, Depends(get_db)],
    _user: Annotated[User, Depends(get_current_user)],
) -> dict:
    """Full export: sessions + daily logs + recaps as a single JSON bundle."""
    sessions = (await db.execute(select(Session).order_by(Session.started_at))).scalars().all()
    logs = (await db.execute(select(DailyLog).order_by(DailyLog.log_date))).scalars().all()
    recaps = (await db.execute(select(Recap).order_by(Recap.week_id))).scalars().all()

    return {
        "sessions": [
            {
                "week_id": s.week_id, "type": s.type.value,
                "started_at": s.started_at.isoformat() if s.started_at else None,
                "duration_hours": round(s.duration_sec / 3600.0, 2),
                "notes": s.notes,
            }
            for s in sessions
        ],
        "daily_logs": [
            {
                "week_id": log.week_id, "log_date": str(log.log_date),
                "topic": log.topic, "learned": log.learned,
                "blockers": log.blockers,
            }
            for log in logs
        ],
        "recaps": [
            {
                "week_id": r.week_id, "successes": r.successes,
                "blockers": r.blockers, "next_step": r.next_step,
            }
            for r in recaps
        ],
    }
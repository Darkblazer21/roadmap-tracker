"""GitHub router: manual sync trigger + verdict matrix + raw events list."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_db
from app.models.github_event import GithubEvent
from app.models.user import User
from app.services.security import get_current_user
from app.services.week_verdict import compute_verdicts
from app.services.scheduler import run_sync_now

router = APIRouter(prefix="/api/github", tags=["github"])


@router.post("/sync", status_code=202)
async def sync(
    background_tasks: BackgroundTasks,
    _user: Annotated[User, Depends(get_current_user)],
) -> dict[str, str]:
    """Trigger a GitHub sync in the background and return immediately.

    The sync walks each tracked repo's recent history (network I/O) and can
    take a while, so it runs as a background task instead of blocking the
    request. Poll GET /verdicts to see the refreshed results.
    """
    background_tasks.add_task(run_sync_now)
    return {"status": "sync_started"}


@router.get("/verdicts")
async def get_verdicts(
    db: Annotated[AsyncSession, Depends(get_db)],
    _user: Annotated[User, Depends(get_current_user)],
) -> dict[str, dict[int, dict[str, object]]]:
    """Return the per-week verdict matrix: {repo: {week_number: {verdict, count, latest_at}}}."""
    return await compute_verdicts(db)


@router.get("/events")
async def list_events(
    db: Annotated[AsyncSession, Depends(get_db)],
    _user: Annotated[User, Depends(get_current_user)],
    week_id: Annotated[int | None, Query()] = None,
    repo: Annotated[str | None, Query()] = None,
    limit: Annotated[int, Query(ge=1, le=500)] = 50,
) -> list[dict[str, object]]:
    """List cached GitHub events, optionally filtered by week or repo."""
    from datetime import datetime, timezone
    from app.models.settings import AppSettings
    from app.services.week_clock import week_window

    settings = (
        await db.execute(select(AppSettings).where(AppSettings.id == 1))
    ).scalar_one_or_none()
    start = settings.start_date if settings else None

    stmt = select(GithubEvent).order_by(GithubEvent.authored_at.desc()).limit(limit)
    if repo:
        stmt = stmt.where(GithubEvent.repo == repo)
    if week_id is not None:
        if start is None:
            raise HTTPException(
                status_code=400,
                detail="Cannot filter by week without a configured start_date",
            )
        window_start, window_end = week_window(week_id, start, settings.timezone)
        # Compare as absolute instants: tz-aware windows compare directly;
        # only force UTC when the window is naive (no configured timezone).
        ws = window_start if window_start.tzinfo is not None else window_start.replace(tzinfo=timezone.utc)
        we = window_end if window_end.tzinfo is not None else window_end.replace(tzinfo=timezone.utc)
        stmt = stmt.where(
            GithubEvent.authored_at >= ws,
            GithubEvent.authored_at < we,
        )

    rows = (await db.execute(stmt)).scalars().all()
    return [
        {
            "repo": r.repo,
            "sha": r.sha,
            "message": r.message,
            "author": r.author,
            "authored_at": r.authored_at.isoformat() if r.authored_at else None,
            "kind": r.kind.value,
        }
        for r in rows
    ]
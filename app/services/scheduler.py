"""APScheduler: nightly GitHub sync job (03:00 local) + manual trigger entrypoint."""

from __future__ import annotations

import logging

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from sqlalchemy import select

from app.db import async_session_factory
from app.models.settings import AppSettings
from app.services.github_sync import sync_all

logger = logging.getLogger(__name__)

_scheduler: AsyncIOScheduler | None = None


def start_scheduler() -> AsyncIOScheduler:
    global _scheduler
    if _scheduler is not None:
        return _scheduler
    _scheduler = AsyncIOScheduler()
    _scheduler.add_job(
        _nightly_sync,
        CronTrigger(hour=3, minute=0),
        id="github_nightly_sync",
        replace_existing=True,
    )
    _scheduler.start()
    logger.info("APScheduler started: nightly GitHub sync at 03:00")
    return _scheduler


async def stop_scheduler() -> None:
    global _scheduler
    if _scheduler is not None:
        _scheduler.shutdown(wait=False)
        _scheduler = None


async def _nightly_sync() -> None:
    logger.info("Nightly GitHub sync starting")
    async with async_session_factory() as db:
        settings = (
            await db.execute(select(AppSettings).where(AppSettings.id == 1))
        ).scalar_one_or_none()
        repos = settings.tracked_repos if settings else []
        if not repos:
            logger.info("No tracked repos - skipping sync")
            return
        await sync_all(db, repos)
    logger.info("Nightly GitHub sync complete")


async def run_sync_now() -> dict[str, int]:
    """Manual trigger - also called by the POST /api/github/sync endpoint."""
    async with async_session_factory() as db:
        settings = (
            await db.execute(select(AppSettings).where(AppSettings.id == 1))
        ).scalar_one_or_none()
        repos = settings.tracked_repos if settings else []
        if not repos:
            return {}
        return await sync_all(db, repos)
"""FastAPI application entrypoint.

M1 scope: health check + CORS + lifespan that seeds the database from
``roadmap.md`` on first boot, plus the weeks router for reading/updating.
"""

import logging
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import select

from app.config import settings
from app.db import async_session_factory, engine
from app.models.user import User
from app.models.week import Week
from app.routers import auth as auth_router
from app.routers import daily_logs as daily_logs_router
from app.routers import github as github_router
from app.routers import pomodoro as pomodoro_router
from app.routers import recaps as recaps_router
from app.routers import sessions as sessions_router
from app.routers import settings as settings_router
from app.routers import weeks as weeks_router

logger = logging.getLogger(__name__)


async def _seed_user(session) -> None:
    """Create the seed user from env vars if none exists yet."""
    result = await session.execute(select(User).limit(1))
    if result.scalar_one_or_none() is not None:
        return
    from app.services.security import hash_password

    user = User(
        username=settings.seed_username,
        password_hash=hash_password(settings.seed_password),
    )
    session.add(user)
    await session.commit()
    logger.info("Seeded user %r", settings.seed_username)


async def _seed_settings(session) -> None:
    """Ensure the singleton settings row exists (id=1)."""
    from app.models.settings import AppSettings

    result = await session.execute(select(AppSettings).where(AppSettings.id == 1))
    if result.scalar_one_or_none() is None:
        session.add(AppSettings(id=1))
        await session.commit()


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    # Seed the database from roadmap.md if it's empty.
    async with async_session_factory() as session:
        result = await session.execute(select(Week).limit(1))
        if result.scalar_one_or_none() is None:
            markdown = settings.roadmap_path.read_text(encoding="utf-8")
            from app.services.importer import sync_database

            phases_n, weeks_n = await sync_database(session, markdown)
            logger.info("Seeded roadmap: %d phases, %d weeks", phases_n, weeks_n)
        else:
            logger.info("Roadmap already seeded - skipping import")

        await _seed_user(session)
        await _seed_settings(session)

    # Start the nightly GitHub sync scheduler (M6).
    from app.services.scheduler import start_scheduler

    start_scheduler()

    yield
    # Shutdown hook: stop scheduler, close Redis, close engine.
    from app.services.scheduler import stop_scheduler
    from app.services.redis_client import close_redis

    await stop_scheduler()
    await close_redis()
    await engine.dispose()


app = FastAPI(
    title="Roadmap Tracker",
    description=(
        "Local standalone tracker for a 52-56 week backend/cloud roadmap: "
        "pomodoro, hours, day-to-day logging, Sunday recaps and on-time "
        "GitHub commit verification."
    ),
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(weeks_router.router)
app.include_router(auth_router.router)
app.include_router(settings_router.router)
app.include_router(sessions_router.router)
app.include_router(pomodoro_router.router)
app.include_router(daily_logs_router.router)
app.include_router(recaps_router.router)
app.include_router(github_router.router)


@app.get("/health")
async def health() -> dict[str, str]:
    """Liveness probe - no DB hit, returns ok as soon as uvicorn is up."""
    return {"status": "ok"}


@app.get("/")
async def root() -> dict[str, str]:
    return {
        "name": "Roadmap Tracker",
        "version": "0.1.0",
        "docs": "/docs",
    }
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
from app.models.week import Week
from app.routers import weeks as weeks_router

logger = logging.getLogger(__name__)


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

    yield
    # Shutdown hook: close the async engine cleanly.
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
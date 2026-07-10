"""FastAPI application entrypoint.

M0 scope: health check + CORS + lifespan placeholder for the scheduler that
will be added in M6. Routers are mounted incrementally from M1 onward.
"""

from contextlib import asynccontextmanager
from collections.abc import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings


@asynccontextmanager
def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    # M6 will start the APScheduler here (nightly GitHub sync).
    # M1 will run the roadmap importer to seed the database on first boot.
    yield
    # Shutdown hook: close the async engine + scheduler cleanly.
    from app.db import engine
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
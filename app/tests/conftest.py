"""Pytest configuration and shared fixtures."""

import os

# Configure the test environment BEFORE importing the app so the settings
# singleton binds to the test config (not the real .env). setdefault keeps
# any values provided by the CI environment.
os.environ.setdefault("JWT_SECRET", "test-secret")
os.environ.setdefault("SEED_USERNAME", "testuser")
os.environ.setdefault("SEED_PASSWORD", "testpass")
os.environ.setdefault("GITHUB_TOKEN", "")
os.environ.setdefault("REDIS_URL", "redis://localhost:6379/1")

import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

# Import all models so they register on Base.metadata.
from app.models import (  # noqa: F401
    AppSettings,
    DailyLog,
    GithubEvent,
    GithubSyncState,
    Phase,
    Recap,
    Session,
    User,
    Week,
    WeekStatus,
)

# Default to a local Postgres/Redis so tests run without Docker; CI overrides
# TEST_DATABASE_URL (and REDIS_URL) to reach the service containers.
TEST_DB_URL = os.environ.get(
    "TEST_DATABASE_URL",
    "postgresql+asyncpg://roadmap:roadmap@localhost:5432/roadmap_tracker_test",
)
os.environ["JWT_SECRET"] = "test-secret"
os.environ["SEED_USERNAME"] = "testuser"
os.environ["SEED_PASSWORD"] = "testpass"
os.environ["GITHUB_TOKEN"] = ""
os.environ["REDIS_URL"] = "redis://redis:6379/1"


@pytest_asyncio.fixture
async def db_session():
    """Per-test async session, tables created fresh each time."""
    from app.db import Base

    engine = create_async_engine(TEST_DB_URL, echo=False, pool_pre_ping=True)

    # Drop and create in separate transactions to ensure DDL is committed
    # before the seeding session opens its own connection.
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # Seed the minimal data needed for API tests.
    from app.services.security import hash_password

    session_factory = async_sessionmaker(bind=engine, expire_on_commit=False)
    async with session_factory() as session:
        session.add(User(username="testuser", password_hash=hash_password("testpass")))
        session.add(AppSettings(id=1))
        phase = Phase(key="test-phase", title="Test Phase", position=1)
        session.add(phase)
        await session.flush()
        for n in range(1, 6):
            session.add(Week(
                number=n, phase_id=phase.id, theme=f"Theme {n}",
                resources="res", deliverable="deliverable",
                hours_min=float(n * 10), hours_max=float(n * 10 + 5),
                buffer=False, status=WeekStatus.not_started,
            ))
        await session.commit()

    yield engine, session_factory

    # Teardown
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


@pytest_asyncio.fixture
async def client(db_session):
    """Async HTTP client with the DB dependency overridden to use the test DB."""
    engine, session_factory = db_session
    from app.db import get_db
    from app.main import app

    async def _override_get_db():
        async with session_factory() as s:
            yield s

    app.dependency_overrides[get_db] = _override_get_db

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac

    app.dependency_overrides.clear()
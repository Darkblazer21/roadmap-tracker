"""Shared async Redis client.

Initialised lazily on first use and closed in the FastAPI lifespan shutdown
hook. A module-level singleton keeps the connection pool shared across
requests (single-user local app: one connection is plenty).
"""

from __future__ import annotations

import redis.asyncio as redis

from app.config import settings

_client: redis.Redis | None = None


def get_redis() -> redis.Redis:
    """Return the shared async Redis client, creating it on first call."""
    global _client
    if _client is None:
        _client = redis.Redis.from_url(
            settings.redis_url,
            decode_responses=True,
            health_check_interval=30,
        )
    return _client


async def close_redis() -> None:
    """Shut down the pool - called from the lifespan shutdown hook."""
    global _client
    if _client is not None:
        await _client.aclose()
        _client = None
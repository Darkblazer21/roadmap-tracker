"""Tests for the API: auth, weeks, sessions, JWT protection (require test DB)."""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_health(client: AsyncClient):
    res = await client.get("/health")
    assert res.status_code == 200
    assert res.json()["status"] == "ok"


@pytest.mark.asyncio
async def test_login_success(client: AsyncClient):
    res = await client.post("/api/auth/login", json={"username": "testuser", "password": "testpass"})
    assert res.status_code == 200
    assert "access_token" in res.json()
    assert res.json()["token_type"] == "bearer"


@pytest.mark.asyncio
async def test_login_wrong_password(client: AsyncClient):
    res = await client.post("/api/auth/login", json={"username": "testuser", "password": "WRONG"})
    assert res.status_code == 401


@pytest.mark.asyncio
async def test_protected_route_requires_token(client: AsyncClient):
    res = await client.get("/api/auth/me")
    assert res.status_code == 401


@pytest.mark.asyncio
async def test_protected_route_with_token(client: AsyncClient):
    login_res = await client.post("/api/auth/login", json={"username": "testuser", "password": "testpass"})
    token = login_res.json()["access_token"]
    res = await client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 200
    assert res.json()["username"] == "testuser"


@pytest.mark.asyncio
async def test_patch_week_requires_auth(client: AsyncClient):
    res = await client.patch("/api/weeks/1", json={"actual_hours": 5.0})
    assert res.status_code == 401


@pytest.mark.asyncio
async def test_patch_week_with_auth(client: AsyncClient):
    login_res = await client.post("/api/auth/login", json={"username": "testuser", "password": "testpass"})
    token = login_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    res = await client.patch("/api/weeks/1", json={"actual_hours": 5.0, "status": "in_progress"}, headers=headers)
    assert res.status_code == 200
    assert res.json()["actual_hours"] == 5.0
    assert res.json()["status"] == "in_progress"


@pytest.mark.asyncio
async def test_create_session_omitting_started_at_uses_server_default(client: AsyncClient):
    """Regression for H2: omitting started_at must NOT store NULL.

    Passing started_at=None explicitly used to override the column's
    server_default=func.now(), persisting NULL and 500-ing on read.
    """
    login_res = await client.post("/api/auth/login", json={"username": "testuser", "password": "testpass"})
    token = login_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    res = await client.post(
        "/api/sessions",
        json={"week_id": 1, "type": "focus", "duration_sec": 1500},
        headers=headers,
    )
    assert res.status_code == 201, res.text
    body = res.json()
    assert body["started_at"] is not None
    # Must be a parseable ISO datetime (proves it came from server_default).
    from datetime import datetime

    datetime.fromisoformat(body["started_at"].replace("Z", "+00:00"))


@pytest.mark.asyncio
async def test_weeks_read_endpoints_require_auth(client: AsyncClient):
    """Regression for H1: GET /api/weeks and /api/weeks/{n} must be protected."""
    assert (await client.get("/api/weeks")).status_code == 401
    assert (await client.get("/api/weeks/1")).status_code == 401
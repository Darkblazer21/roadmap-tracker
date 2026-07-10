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
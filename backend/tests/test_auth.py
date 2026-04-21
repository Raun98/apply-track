"""
Integration tests for the auth API (/register, /login, /refresh, /me).
"""
import pytest


async def test_register_creates_user(client):
    resp = await client.post(
        "/api/v1/auth/register",
        json={"email": "new@test.com", "password": "Password1"},
    )
    assert resp.status_code == 201
    data = resp.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["user"]["email"] == "new@test.com"


async def test_register_duplicate_email_rejected(client):
    payload = {"email": "dup@test.com", "password": "Password1"}
    await client.post("/api/v1/auth/register", json=payload)
    resp = await client.post("/api/v1/auth/register", json=payload)
    assert resp.status_code == 400
    assert "already registered" in resp.json()["detail"].lower()


async def test_register_weak_password_rejected(client):
    resp = await client.post(
        "/api/v1/auth/register",
        json={"email": "weak@test.com", "password": "short"},
    )
    assert resp.status_code == 422  # pydantic validation


async def test_login_success(client):
    await client.post(
        "/api/v1/auth/register",
        json={"email": "login@test.com", "password": "Password1"},
    )
    resp = await client.post(
        "/api/v1/auth/login",
        json={"email": "login@test.com", "password": "Password1"},
    )
    assert resp.status_code == 200
    assert "access_token" in resp.json()


async def test_login_wrong_password(client):
    await client.post(
        "/api/v1/auth/register",
        json={"email": "wrong@test.com", "password": "Password1"},
    )
    resp = await client.post(
        "/api/v1/auth/login",
        json={"email": "wrong@test.com", "password": "BadPassword1"},
    )
    assert resp.status_code == 401


async def test_login_unknown_email(client):
    resp = await client.post(
        "/api/v1/auth/login",
        json={"email": "nobody@test.com", "password": "Password1"},
    )
    assert resp.status_code == 401


async def test_get_me_requires_auth(client):
    resp = await client.get("/api/v1/auth/me")
    assert resp.status_code in (401, 403)


async def test_get_me_returns_user(client):
    reg = await client.post(
        "/api/v1/auth/register",
        json={"email": "me@test.com", "password": "Password1"},
    )
    token = reg.json()["access_token"]
    resp = await client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200
    assert resp.json()["email"] == "me@test.com"


async def test_refresh_token(client):
    reg = await client.post(
        "/api/v1/auth/register",
        json={"email": "refresh@test.com", "password": "Password1"},
    )
    refresh_token = reg.json()["refresh_token"]
    resp = await client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": refresh_token},
    )
    assert resp.status_code == 200
    assert "access_token" in resp.json()


async def test_refresh_with_invalid_token(client):
    resp = await client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": "not-a-real-token"},
    )
    assert resp.status_code == 401


async def test_inbox_address_returned_on_register(client):
    resp = await client.post(
        "/api/v1/auth/register",
        json={"email": "inbox@test.com", "password": "Password1"},
    )
    assert resp.status_code == 201
    user = resp.json()["user"]
    assert user.get("inbox_address") is not None
    assert "@" in user["inbox_address"]

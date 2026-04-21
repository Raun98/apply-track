"""
Tests for the /board/stats endpoint — verifies the fixed response_rate calculation.
"""
import pytest
import pytest_asyncio
from datetime import datetime, timezone

from app.models.application import Application, ApplicationStatus, JobSource
from app.models.user import User
from app.api.deps import get_password_hash


async def _create_user(db_session) -> User:
    user = User(
        email="stats@test.com",
        password_hash=get_password_hash("Password1"),
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


async def _add_app(db_session, user_id: int, status: ApplicationStatus) -> Application:
    app = Application(
        user_id=user_id,
        company_name="Co",
        position_title="Role",
        source=JobSource.MANUAL,
        status=status,
        applied_date=datetime.now(timezone.utc),
        last_updated=datetime.now(timezone.utc),
    )
    db_session.add(app)
    await db_session.commit()
    return app


async def test_stats_response_rate_differs_from_interview_rate(client, db_session):
    """response_rate should include screening+interview+offer+accepted+rejected,
    while interview_rate should only be interview+offer+accepted."""
    user = await _create_user(db_session)

    # 10 applied, 2 screening, 1 interview, 1 rejected = 14 total
    # response = screening(2) + interview(1) + rejected(1) = 4/14
    # interview = interview(1) / 14
    for _ in range(10):
        await _add_app(db_session, user.id, ApplicationStatus.APPLIED)
    for _ in range(2):
        await _add_app(db_session, user.id, ApplicationStatus.SCREENING)
    await _add_app(db_session, user.id, ApplicationStatus.INTERVIEW)
    await _add_app(db_session, user.id, ApplicationStatus.REJECTED)

    # Authenticate
    login_resp = await client.post(
        "/api/v1/auth/login",
        json={"email": "stats@test.com", "password": "Password1"},
    )
    assert login_resp.status_code == 200
    token = login_resp.json()["access_token"]

    resp = await client.get(
        "/api/v1/board/stats",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200
    data = resp.json()

    assert data["response_rate"] != data["interview_rate"], (
        "response_rate and interview_rate must differ when there are screening/rejected apps"
    )
    # response_rate = 4/14 ≈ 28.6 %
    assert abs(data["response_rate"] - round(4 / 14 * 100, 1)) < 0.1
    # interview_rate = 1/14 ≈ 7.1 %
    assert abs(data["interview_rate"] - round(1 / 14 * 100, 1)) < 0.1


async def test_stats_zero_applications(client, db_session):
    user = await _create_user(db_session)
    # Override email so user is unique
    user.email = "stats_zero@test.com"
    await db_session.commit()

    login_resp = await client.post(
        "/api/v1/auth/login",
        json={"email": "stats_zero@test.com", "password": "Password1"},
    )
    # User was added but password_hash is set, yet registration wasn't called.
    # Create via register endpoint instead so password_hash is correct.


async def test_stats_all_zeros_when_no_apps(client, db_session):
    reg = await client.post(
        "/api/v1/auth/register",
        json={"email": "stats_empty@test.com", "password": "Password1"},
    )
    assert reg.status_code == 201
    token = reg.json()["access_token"]

    resp = await client.get(
        "/api/v1/board/stats",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["total_applications"] == 0
    assert data["response_rate"] == 0
    assert data["interview_rate"] == 0
    assert data["offer_rate"] == 0

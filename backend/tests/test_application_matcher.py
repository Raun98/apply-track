"""
Unit tests for ApplicationMatcherService — match, create, and status-update logic.
"""
import pytest
import pytest_asyncio
from datetime import datetime, timezone

from app.services.application_matcher import ApplicationMatcherService, _resolve_status
from app.models.application import Application, ApplicationStatus, JobSource


# ── _resolve_status ───────────────────────────────────────────────────────────

def test_resolve_status_forward_progress():
    result = _resolve_status("interview", ApplicationStatus.APPLIED)
    assert result == ApplicationStatus.INTERVIEW


def test_resolve_status_no_regression():
    """An email saying 'applied' shouldn't move a card already at 'interview' backwards."""
    result = _resolve_status("applied", ApplicationStatus.INTERVIEW)
    assert result is None


def test_resolve_status_update_returns_none():
    """The generic 'update' status should never change the current status."""
    result = _resolve_status("update", ApplicationStatus.SCREENING)
    assert result is None


def test_resolve_status_rejected_always_accepted():
    """Rejected can move from any forward status."""
    result = _resolve_status("rejected", ApplicationStatus.OFFER)
    assert result == ApplicationStatus.REJECTED


def test_resolve_status_unknown_string():
    result = _resolve_status("gibberish", ApplicationStatus.APPLIED)
    assert result is None


def test_resolve_status_empty_string():
    result = _resolve_status("", ApplicationStatus.APPLIED)
    assert result is None


# ── Matcher integration (requires DB session) ─────────────────────────────────

@pytest_asyncio.fixture
async def matcher(db_session):
    return ApplicationMatcherService(db_session)


@pytest_asyncio.fixture
async def sample_application(db_session):
    app = Application(
        user_id=1,
        company_name="Acme Corp",
        position_title="Software Engineer",
        source=JobSource.LINKEDIN,
        status=ApplicationStatus.APPLIED,
        applied_date=datetime.now(timezone.utc),
        last_updated=datetime.now(timezone.utc),
    )
    db_session.add(app)
    await db_session.commit()
    await db_session.refresh(app)
    return app


async def test_find_matching_application_by_company_and_position(matcher, sample_application):
    result = await matcher.find_matching_application(
        user_id=1,
        company_name="Acme Corp",
        position_title="Software Engineer",
        from_address="hr@acme.com",
    )
    assert result is not None
    assert result.id == sample_application.id


async def test_find_matching_application_partial_company(matcher, sample_application):
    result = await matcher.find_matching_application(
        user_id=1,
        company_name="Acme",
        position_title=None,
        from_address="hr@acme.com",
    )
    assert result is not None


async def test_find_matching_application_no_match(matcher, sample_application):
    result = await matcher.find_matching_application(
        user_id=1,
        company_name="Totally Different Company",
        position_title="Totally Different Role",
        from_address="hr@other.com",
    )
    assert result is None


async def test_find_matching_application_wrong_user(matcher, sample_application):
    result = await matcher.find_matching_application(
        user_id=99,  # different user
        company_name="Acme Corp",
        position_title="Software Engineer",
        from_address="hr@acme.com",
    )
    assert result is None


async def test_find_matching_application_both_none(matcher, sample_application):
    result = await matcher.find_matching_application(
        user_id=1,
        company_name=None,
        position_title=None,
        from_address="hr@acme.com",
    )
    assert result is None


async def test_create_application_from_email(matcher, db_session):
    app = await matcher.create_application_from_email(
        user_id=1,
        company_name="NewCo",
        position_title="Designer",
        source="linkedin",
        status="applied",
    )
    assert app.id is not None
    assert app.company_name == "NewCo"
    assert app.status == ApplicationStatus.APPLIED
    assert app.source == JobSource.LINKEDIN


async def test_create_application_ignores_update_status(matcher, db_session):
    """'update' as initial status should fall back to 'applied'."""
    app = await matcher.create_application_from_email(
        user_id=1,
        company_name="SomeCo",
        position_title="Dev",
        source="unknown",
        status="update",
    )
    assert app.status == ApplicationStatus.APPLIED


async def test_update_application_status_advances(matcher, sample_application):
    changed = await matcher.update_application_status(
        application=sample_application,
        new_status="interview",
        reason="Interview scheduled",
    )
    assert changed is True
    assert sample_application.status == ApplicationStatus.INTERVIEW


async def test_update_application_status_no_regression(matcher, sample_application):
    """Trying to move back to 'applied' from 'applied' should be a no-op."""
    changed = await matcher.update_application_status(
        application=sample_application,
        new_status="applied",
        reason="Accidental re-send",
    )
    assert changed is False
    assert sample_application.status == ApplicationStatus.APPLIED

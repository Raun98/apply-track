"""
Integration tests for webhook endpoints.
Covers: user validation, dedup, and basic happy-path email ingestion.
"""
import pytest
from unittest.mock import patch

from app.config import get_settings

WEBHOOK_SECRET = get_settings().WEBHOOK_SECRET
HEADERS = {"X-Webhook-Secret": WEBHOOK_SECRET}


# ── /webhooks/email ───────────────────────────────────────────────────────────

async def test_webhook_rejects_wrong_secret(client):
    resp = await client.post(
        "/api/v1/webhooks/email",
        json={"to": "user1@inbox.applytrack.app", "from": "hr@acme.com", "subject": "Hi"},
        headers={"X-Webhook-Secret": "WRONG"},
    )
    assert resp.status_code == 401


async def test_webhook_rejects_unknown_user(client):
    """Sending to user99999 which doesn't exist must return 400."""
    with patch("app.tasks.email_processor.process_email.delay"):
        resp = await client.post(
            "/api/v1/webhooks/email",
            json={
                "to": "user99999@inbox.applytrack.app",
                "from": "hr@acme.com",
                "subject": "Test",
                "text": "body",
            },
            headers=HEADERS,
        )
    assert resp.status_code == 400
    assert "not found" in resp.json()["detail"].lower()


async def _register_user(client, email="wh@test.com"):
    reg = await client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": "Password1"},
    )
    return reg.json()["user"]["id"]


async def test_webhook_creates_email_for_valid_user(client):
    user_id = await _register_user(client, "valid@test.com")
    with patch("app.tasks.email_processor.process_email.delay") as mock_delay:
        resp = await client.post(
            "/api/v1/webhooks/email",
            json={
                "to": f"user{user_id}@inbox.applytrack.app",
                "from": "hr@acme.com",
                "subject": "Interview Invite",
                "text": "We'd like to schedule an interview.",
                "message_id": "unique-msg-id-001",
            },
            headers=HEADERS,
        )
    assert resp.status_code == 200
    assert "email_id" in resp.json()
    mock_delay.assert_called_once()


async def test_webhook_dedup_same_message_id(client):
    user_id = await _register_user(client, "dedup@test.com")
    payload = {
        "to": f"user{user_id}@inbox.applytrack.app",
        "from": "hr@acme.com",
        "subject": "Same Email",
        "text": "body",
        "message_id": "deduplicate-me-123",
    }
    with patch("app.tasks.email_processor.process_email.delay"):
        resp1 = await client.post("/api/v1/webhooks/email", json=payload, headers=HEADERS)
        resp2 = await client.post("/api/v1/webhooks/email", json=payload, headers=HEADERS)

    assert resp1.status_code == 200
    assert resp2.json().get("duplicate") is True


async def test_webhook_bad_recipient_format(client):
    resp = await client.post(
        "/api/v1/webhooks/email",
        json={
            "to": "notauseraddress@inbox.applytrack.app",
            "from": "hr@acme.com",
            "subject": "Test",
        },
        headers=HEADERS,
    )
    assert resp.status_code == 400


# ── /webhooks/mailgun-inbound ─────────────────────────────────────────────────

async def test_mailgun_inbound_ignores_bad_recipient_format(client):
    resp = await client.post(
        "/api/v1/webhooks/mailgun-inbound",
        data={
            "recipient": "badformat@inbox.applytrack.app",
            "sender": "hr@acme.com",
            "subject": "Hi",
            "body-plain": "test",
            "timestamp": "0",
            "token": "x",
            "signature": "x",
        },
    )
    assert resp.status_code == 200
    assert resp.json()["status"] == "ignored"


async def test_mailgun_inbound_rejects_unknown_user(client):
    with patch("app.tasks.email_processor.process_email.delay"):
        resp = await client.post(
            "/api/v1/webhooks/mailgun-inbound",
            data={
                "recipient": "user99999@inbox.applytrack.app",
                "sender": "hr@acme.com",
                "subject": "Hi",
                "body-plain": "test",
                "Message-Id": "mailgun-test-001",
                "timestamp": "0",
                "token": "x",
                "signature": "x",
            },
        )
    assert resp.status_code == 400


async def test_mailgun_inbound_happy_path(client):
    user_id = await _register_user(client, "mg@test.com")
    with patch("app.tasks.email_processor.process_email.delay") as mock_delay:
        resp = await client.post(
            "/api/v1/webhooks/mailgun-inbound",
            data={
                "recipient": f"user{user_id}@inbox.applytrack.app",
                "sender": "hr@acme.com",
                "subject": "Offer Letter",
                "body-plain": "Congratulations!",
                "Message-Id": "mg-unique-001",
                "timestamp": "0",
                "token": "x",
                "signature": "x",
            },
        )
    assert resp.status_code == 200
    assert resp.json()["status"] == "queued"
    mock_delay.assert_called_once()

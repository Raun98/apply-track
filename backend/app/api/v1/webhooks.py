import hashlib
import hmac
import re
from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Header, Request, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.api.deps import get_db
from app.config import get_settings
from app.models.email import Email, ProcessedStatus
from app.models.user import User
from app.tasks.email_processor import process_email

router = APIRouter()
settings = get_settings()


async def _require_user(user_id: int, db: AsyncSession) -> None:
    """Raise 400 if the user_id doesn't exist in the database."""
    result = await db.execute(select(User).where(User.id == user_id))
    if result.scalar_one_or_none() is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Recipient user not found",
        )


@router.post("/email")
async def receive_email_webhook(
    request: Request,
    x_webhook_secret: str = Header(None, alias="X-Webhook-Secret"),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """Receive emails from temporary mailbox forwarding."""
    # Verify webhook secret
    if x_webhook_secret != settings.WEBHOOK_SECRET:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid webhook secret",
        )

    # Parse email data
    try:
        data = await request.json()
    except Exception:
        # Try parsing as form data
        form_data = await request.form()
        data = dict(form_data)

    if not data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No email data provided",
        )

    # Extract email fields
    to_address = data.get("to") or data.get("recipient") or ""
    from_address = data.get("from") or data.get("sender") or ""
    subject = data.get("subject") or ""
    body_text = data.get("text") or data.get("body") or ""
    body_html = data.get("html") or ""
    message_id = data.get("message_id") or data.get("Message-ID") or f"webhook-{datetime.now(timezone.utc).timestamp()}"

    # Dedup: skip if this message_id already exists
    existing = await db.execute(
        select(Email).where(Email.message_id == message_id)
    )
    if existing.scalar_one_or_none():
        return {"message": "Duplicate email — skipped", "duplicate": True}

    # Extract user_id from to_address (e.g., user123@tracker.app)
    user_id = None
    if "@" in to_address:
        local_part = to_address.split("@")[0]
        if local_part.startswith("user"):
            try:
                user_id = int(local_part[4:])
            except ValueError:
                pass
        else:
            try:
                user_id = int(local_part)
            except ValueError:
                pass

    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Could not determine user from recipient address",
        )

    await _require_user(user_id, db)

    # Create email record
    email = Email(
        user_id=user_id,
        message_id=message_id,
        from_address=from_address,
        to_address=to_address,
        subject=subject,
        body_text=body_text,
        body_html=body_html,
        received_at=datetime.now(timezone.utc),
        processed_status=ProcessedStatus.PENDING,
    )

    db.add(email)
    await db.commit()
    await db.refresh(email)

    # Queue for processing
    process_email.delay(email.id)

    return {
        "message": "Email received and queued for processing",
        "email_id": email.id,
    }


@router.post("/email/raw")
async def receive_raw_email(
    request: Request,
    x_webhook_secret: str = Header(None, alias="X-Webhook-Secret"),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """Receive raw email content (RFC 2822 format)."""
    import email
    from email import policy
    from email.parser import BytesParser

    # Verify webhook secret
    if x_webhook_secret != settings.WEBHOOK_SECRET:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid webhook secret",
        )

    # Read raw email
    raw_content = await request.body()

    try:
        # Parse email
        msg = BytesParser(policy=policy.default).parsebytes(raw_content)

        # Extract fields
        from_address = msg["From"] or ""
        to_address = msg["To"] or ""
        subject = msg["Subject"] or ""
        message_id = msg["Message-ID"] or f"raw-{datetime.now(timezone.utc).timestamp()}"

        # Dedup: skip if this message_id already exists
        existing = await db.execute(
            select(Email).where(Email.message_id == message_id)
        )
        if existing.scalar_one_or_none():
            return {"message": "Duplicate email — skipped", "duplicate": True}

        # Extract body
        body_text = ""
        body_html = ""

        if msg.is_multipart():
            for part in msg.walk():
                content_type = part.get_content_type()
                if content_type == "text/plain":
                    body_text = part.get_content()
                elif content_type == "text/html":
                    body_html = part.get_content()
        else:
            body_text = msg.get_content()

        # Extract user_id from to_address
        user_id = None
        if "@" in to_address:
            local_part = to_address.split("@")[0]
            if local_part.startswith("user"):
                try:
                    user_id = int(local_part[4:])
                except ValueError:
                    pass
            else:
                try:
                    user_id = int(local_part)
                except ValueError:
                    pass

        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Could not determine user from recipient address",
            )

        await _require_user(user_id, db)

        # Create email record
        email_record = Email(
            user_id=user_id,
            message_id=message_id,
            from_address=from_address,
            to_address=to_address,
            subject=subject,
            body_text=body_text[:10000],
            body_html=body_html[:10000] if body_html else None,
            received_at=datetime.now(timezone.utc),
            processed_status=ProcessedStatus.PENDING,
        )

        db.add(email_record)
        await db.commit()
        await db.refresh(email_record)

        # Queue for processing
        process_email.delay(email_record.id)

        return {
            "message": "Email received and queued for processing",
            "email_id": email_record.id,
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to parse email: {str(e)}",
        )


@router.post("/mailgun-inbound")
async def mailgun_inbound(
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Handles Mailgun inbound email routing.
    Mailgun POSTs multipart/form-data with fields:
      recipient, sender, subject, body-plain, body-html, Message-Id, timestamp, token, signature

    Route all mail to user{id}@INBOX_DOMAIN here.
    """
    form = await request.form()

    # Verify Mailgun signature
    timestamp = form.get("timestamp", "")
    mg_token = form.get("token", "")
    signature = form.get("signature", "")

    # Use the dedicated webhook signing key (Mailgun dashboard → Webhooks).
    # Fall back to the API key only if the signing key is not configured yet.
    signing_key = settings.MAILGUN_WEBHOOK_SIGNING_KEY or settings.MAILGUN_API_KEY
    if signing_key:
        expected = hmac.new(
            signing_key.encode(),
            f"{timestamp}{mg_token}".encode(),
            hashlib.sha256,
        ).hexdigest()
        if not hmac.compare_digest(expected, signature):
            raise HTTPException(status_code=403, detail="Invalid Mailgun signature")

    recipient = form.get("recipient", "")
    sender = form.get("sender", "")
    subject = form.get("subject", "")
    body_plain = form.get("body-plain", "")
    body_html = form.get("body-html", "")
    message_id = form.get("Message-Id", "") or f"mailgun-{datetime.now(timezone.utc).timestamp()}"

    # Extract user ID from recipient: user{id}@inbox.applytrack.app
    match = re.match(r"user(\d+)@", recipient)
    if not match:
        return {"status": "ignored", "reason": "recipient format not recognized"}

    user_id = int(match.group(1))
    await _require_user(user_id, db)

    # Check message_id dedup
    if message_id:
        existing = await db.execute(
            select(Email).where(Email.message_id == message_id)
        )
        if existing.scalar_one_or_none():
            return {"status": "duplicate", "message_id": message_id}

    # Create email record and queue for processing (same flow as other webhooks)
    email_record = Email(
        user_id=user_id,
        message_id=message_id,
        from_address=sender,
        to_address=recipient,
        subject=subject,
        body_text=body_plain[:10000] if body_plain else "",
        body_html=body_html[:10000] if body_html else None,
        received_at=datetime.now(timezone.utc),
        processed_status=ProcessedStatus.PENDING,
    )

    db.add(email_record)
    await db.commit()
    await db.refresh(email_record)

    # Queue for processing via the same Celery task
    process_email.delay(email_record.id)

    return {"status": "queued", "email_id": email_record.id}

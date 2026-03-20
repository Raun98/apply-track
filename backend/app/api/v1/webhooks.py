from datetime import datetime
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Header, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db
from app.config import get_settings
from app.models.email import Email, ProcessedStatus
from app.tasks.email_processor import process_email

router = APIRouter()
settings = get_settings()


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
    message_id = data.get("message_id") or data.get("Message-ID") or f"webhook-{datetime.utcnow().timestamp()}"

    # Extract user_id from to_address (e.g., user123@tracker.app)
    user_id = None
    if "@" in to_address:
        local_part = to_address.split("@")[0]
        # Try to extract numeric user ID
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

    # Create email record
    email = Email(
        user_id=user_id,
        message_id=message_id,
        from_address=from_address,
        to_address=to_address,
        subject=subject,
        body_text=body_text,
        body_html=body_html,
        received_at=datetime.utcnow(),
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
        message_id = msg["Message-ID"] or f"raw-{datetime.utcnow().timestamp()}"

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

        # Create email record
        email_record = Email(
            user_id=user_id,
            message_id=message_id,
            from_address=from_address,
            to_address=to_address,
            subject=subject,
            body_text=body_text[:10000],  # Limit size
            body_html=body_html[:10000] if body_html else None,
            received_at=datetime.utcnow(),
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

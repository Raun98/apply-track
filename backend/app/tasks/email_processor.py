import asyncio
import logging
from datetime import datetime, timezone
from typing import Optional

from celery import shared_task
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import AsyncSessionLocal
from app.models.email import Email, ProcessedStatus
from app.models.application import Application, Activity
from app.services.email_parser import email_parser, ParsedEmailResult
from app.services.application_matcher import ApplicationMatcherService
from app.services.websocket_manager import WebSocketManager

logger = logging.getLogger(__name__)


async def process_email_async(email_id: int) -> bool:
    """Process a single email asynchronously."""
    async with AsyncSessionLocal() as db:
        try:
            from sqlalchemy import select

            result = await db.execute(
                select(Email).where(Email.id == email_id)
            )
            email = result.scalar_one_or_none()

            if not email:
                return False

            # Update status to processing
            email.processed_status = ProcessedStatus.PROCESSING
            await db.commit()

            # Parse with Claude, Ollama fallback, or heuristics
            parsed = await email_parser.parse_email(
                subject=email.subject,
                from_address=email.from_address,
                body=email.body_text or "",
                date=email.received_at.isoformat(),
                body_html=email.body_html or "",
            )

            if not parsed or not parsed.is_job_email:
                email.processed_status = ProcessedStatus.IGNORED
                email.parsed_data = {"ignored_reason": "Not a job-related email"}
                await db.commit()
                return True

            # Store parsed data
            email.parsed_data = {
                "source_platform": parsed.source_platform,
                "company_name": parsed.company_name,
                "position_title": parsed.position_title,
                "application_status": parsed.application_status,
                "interview_details": parsed.interview_details,
                "key_info_summary": parsed.key_info_summary,
                "confidence_score": parsed.confidence_score,
            }

            # Match or create application
            matcher = ApplicationMatcherService(db)

            application = await matcher.find_matching_application(
                user_id=email.user_id,
                company_name=parsed.company_name,
                position_title=parsed.position_title,
                from_address=email.from_address,
            )

            if application:
                # Update existing application
                if parsed.application_status:
                    old_status = application.status.value if hasattr(application.status, "value") else str(application.status)
                    status_changed = await matcher.update_application_status(
                        application=application,
                        new_status=parsed.application_status,
                        reason=parsed.key_info_summary,
                        email_id=email.id,
                    )

                    if status_changed:
                        # Create Activity record for status change
                        activity = Activity(
                            user_id=email.user_id,
                            application_id=application.id,
                            type="status_change",
                            description=f"Status changed from {old_status} to {parsed.application_status}: {parsed.key_info_summary or ''}".strip(),
                            extra_data={
                                "from_status": old_status,
                                "to_status": parsed.application_status,
                                "email_id": email.id,
                            },
                        )
                        db.add(activity)

                        # Notify via WebSocket (sync — from Celery worker)
                        WebSocketManager.publish_sync(
                            user_id=email.user_id,
                            event="status_change",
                            data={
                                "application_id": application.id,
                                "new_status": parsed.application_status,
                                "reason": parsed.key_info_summary,
                            },
                        )

                # Record interview details if present
                if parsed.interview_details:
                    interview_activity = Activity(
                        user_id=email.user_id,
                        application_id=application.id,
                        type="interview",
                        description=f"Interview details received: {parsed.interview_details}",
                        extra_data={"interview_details": parsed.interview_details, "email_id": email.id},
                    )
                    db.add(interview_activity)

                email.application_id = application.id
            else:
                # Create new application if we have enough info
                if parsed.company_name and parsed.position_title:
                    application = await matcher.create_application_from_email(
                        user_id=email.user_id,
                        company_name=parsed.company_name,
                        position_title=parsed.position_title,
                        source=parsed.source_platform,
                        status=parsed.application_status or "applied",
                        email_id=email.id,
                    )
                    email.application_id = application.id

                    # Activity for new application
                    activity = Activity(
                        user_id=email.user_id,
                        application_id=application.id,
                        type="new_application",
                        description=f"Application auto-created from email: {parsed.company_name} — {parsed.position_title}",
                        extra_data={"source": parsed.source_platform, "email_id": email.id},
                    )
                    db.add(activity)

                    # Notify about new application (sync)
                    WebSocketManager.publish_sync(
                        user_id=email.user_id,
                        event="new_application",
                        data={
                            "application_id": application.id,
                            "company": parsed.company_name,
                            "position": parsed.position_title,
                            "status": parsed.application_status or "applied",
                        },
                    )

            email.processed_status = ProcessedStatus.PROCESSED
            await db.commit()

            # Notify about processed email (sync)
            WebSocketManager.publish_sync(
                user_id=email.user_id,
                event="new_email",
                data={
                    "email_id": email.id,
                    "application_id": email.application_id,
                },
            )

            return True

        except Exception as e:
            await db.rollback()

            result = await db.execute(
                select(Email).where(Email.id == email_id)
            )
            email = result.scalar_one_or_none()
            if email:
                email.processed_status = ProcessedStatus.FAILED
                email.processing_error = str(e)[:500]
                await db.commit()

            raise


@shared_task(bind=True, max_retries=3)
def process_email(self, email_id: int) -> bool:
    """Celery task to process an email."""
    try:
        return asyncio.run(process_email_async(email_id))
    except Exception as exc:
        raise self.retry(exc=exc, countdown=60)


async def poll_imap_account_async(account_id: int) -> int:
    """Poll an IMAP account for new emails."""
    from app.services.imap_service import IMAPService
    from app.models.email_account import EmailAccount
    from sqlalchemy import select

    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(EmailAccount).where(EmailAccount.id == account_id)
        )
        account = result.scalar_one_or_none()

        if not account or not account.is_active:
            return 0

        imap_service = IMAPService()
        new_emails = await imap_service.fetch_new_emails(account, db)

        for email in new_emails:
            process_email.delay(email.id)

        account.last_sync_at = datetime.now(timezone.utc)
        await db.commit()

        return len(new_emails)


@shared_task
def poll_imap_account(account_id: int) -> int:
    """Celery task to poll an IMAP account."""
    return asyncio.run(poll_imap_account_async(account_id))


@shared_task
def poll_all_imap_accounts() -> dict:
    """Poll all active IMAP accounts."""
    from app.models.email_account import EmailAccount
    from sqlalchemy import select

    async def do_poll():
        async with AsyncSessionLocal() as db:
            result = await db.execute(
                select(EmailAccount).where(EmailAccount.is_active == True)
            )
            accounts = result.scalars().all()

            results = {}
            for account in accounts:
                try:
                    count = await poll_imap_account_async(account.id)
                    results[account.id] = {"status": "success", "new_emails": count}
                except Exception as e:
                    results[account.id] = {"status": "error", "error": str(e)}

            return results

    return asyncio.run(do_poll())

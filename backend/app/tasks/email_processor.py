import asyncio
from datetime import datetime
from typing import Optional

from celery import shared_task
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import AsyncSessionLocal
from app.models.email import Email, ProcessedStatus
from app.models.application import Application
from app.services.email_parser import email_parser, ParsedEmailResult
from app.services.application_matcher import ApplicationMatcherService
from app.services.websocket_manager import websocket_manager


async def process_email_async(email_id: int) -> bool:
    """Process a single email asynchronously."""
    async with AsyncSessionLocal() as db:
        try:
            # Get email
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

            # Parse with Claude API
            parsed = await email_parser.parse_email(
                subject=email.subject,
                from_address=email.from_address,
                body=email.body_text or "",
                date=email.received_at.isoformat(),
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
                    status_changed = await matcher.update_application_status(
                        application=application,
                        new_status=parsed.application_status,
                        reason=parsed.key_info_summary,
                        email_id=email.id,
                    )

                    if status_changed:
                        # Notify via WebSocket
                        await websocket_manager.notify_application_update(
                            user_id=email.user_id,
                            application_id=application.id,
                            update_type="status_change",
                            data={
                                "new_status": parsed.application_status,
                                "reason": parsed.key_info_summary,
                            },
                        )

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

                    # Notify about new application
                    await websocket_manager.notify_application_update(
                        user_id=email.user_id,
                        application_id=application.id,
                        update_type="new_application",
                        data={
                            "company": parsed.company_name,
                            "position": parsed.position_title,
                            "status": parsed.application_status or "applied",
                        },
                    )

            email.processed_status = ProcessedStatus.PROCESSED
            await db.commit()

            # Notify about processed email
            await websocket_manager.notify_new_email(
                user_id=email.user_id,
                email_id=email.id,
                application_id=email.application_id,
            )

            return True

        except Exception as e:
            await db.rollback()

            # Update email status to failed
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
        # Retry on failure
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

        # Queue each new email for processing
        for email in new_emails:
            process_email.delay(email.id)

        # Update last sync time
        account.last_sync_at = datetime.utcnow()
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

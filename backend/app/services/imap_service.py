from datetime import datetime
from typing import List, Optional

from imap_tools import MailBox, AND
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.email import Email, ProcessedStatus
from app.models.email_account import EmailAccount
from app.services.encryption import decrypt_password


class IMAPService:
    """Service for IMAP email fetching."""

    PROVIDER_SETTINGS = {
        "gmail": {"host": "imap.gmail.com", "port": 993},
        "outlook": {"host": "outlook.office365.com", "port": 993},
        "yahoo": {"host": "imap.mail.yahoo.com", "port": 993},
    }

    def get_imap_settings(self, account: EmailAccount) -> dict:
        """Get IMAP settings for an account."""
        if account.imap_host and account.imap_port:
            return {
                "host": account.imap_host,
                "port": account.imap_port,
            }

        # Use provider defaults
        provider = account.provider.value if hasattr(account.provider, 'value') else account.provider
        if provider in self.PROVIDER_SETTINGS:
            return self.PROVIDER_SETTINGS[provider]

        # Default to Gmail
        return self.PROVIDER_SETTINGS["gmail"]

    async def fetch_new_emails(
        self,
        account: EmailAccount,
        db: AsyncSession,
    ) -> List[Email]:
        """Fetch new emails from IMAP account."""
        settings = self.get_imap_settings(account)
        new_emails = []

        try:
            with MailBox(settings["host"]).login(
                account.imap_username or account.email,
                decrypt_password(account.imap_password) if account.imap_password else "",
            ) as mailbox:
                # Search criteria - emails since last sync or last 7 days
                since_date = account.last_sync_at or datetime.utcnow() - __import__('datetime').timedelta(days=7)

                # Fetch emails
                for msg in mailbox.fetch(AND(date__gt=since_date.date())):
                    # Check if email already exists
                    from sqlalchemy import select
                    result = await db.execute(
                        select(Email).where(Email.message_id == msg.uid)
                    )
                    existing = result.scalar_one_or_none()

                    if existing:
                        continue

                    # Create new email record
                    email = Email(
                        user_id=account.user_id,
                        account_id=account.id,
                        message_id=msg.uid,
                        from_address=msg.from_,
                        from_name=msg.from_values.full if msg.from_values else None,
                        to_address=msg.to[0] if msg.to else account.email,
                        subject=msg.subject,
                        body_text=msg.text,
                        body_html=msg.html,
                        received_at=msg.date or datetime.utcnow(),
                        processed_status=ProcessedStatus.PENDING,
                    )

                    db.add(email)
                    await db.flush()  # Get the ID
                    new_emails.append(email)

                await db.commit()

        except Exception as e:
            await db.rollback()
            account.last_error = str(e)[:500]
            await db.commit()
            raise

        return new_emails

    async def test_connection(self, account: EmailAccount) -> bool:
        """Test IMAP connection."""
        settings = self.get_imap_settings(account)

        try:
            with MailBox(settings["host"]).login(
                account.imap_username or account.email,
                decrypt_password(account.imap_password) if account.imap_password else "",
            ) as mailbox:
                return mailbox.folder.exists("INBOX")
        except Exception:
            return False

import asyncio
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import List, Optional

from imap_tools import MailBox, AND
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.email import Email, ProcessedStatus
from app.models.email_account import EmailAccount, EmailProvider
from app.services.encryption import decrypt_password, encrypt_password


@dataclass
class _RawMessage:
    """Plain-data snapshot of an IMAP message, safe to pass across thread boundaries."""
    message_id: str
    from_address: str
    from_name: Optional[str]
    to_address: str
    subject: str
    body_text: str
    body_html: Optional[str]
    received_at: datetime


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
            return {"host": account.imap_host, "port": account.imap_port}

        provider = account.provider.value if hasattr(account.provider, "value") else account.provider
        return self.PROVIDER_SETTINGS.get(provider, self.PROVIDER_SETTINGS["gmail"])

    async def ensure_token_fresh(self, account: EmailAccount, db: AsyncSession) -> str:
        """Return a valid access token, refreshing it if it expires within 5 minutes."""
        from app.services.oauth_service import refresh_google_token, refresh_microsoft_token

        access_token = decrypt_password(account.access_token) if account.access_token else ""

        if account.token_expires_at:
            expiry = account.token_expires_at
            if expiry.tzinfo is None:
                expiry = expiry.replace(tzinfo=timezone.utc)
            needs_refresh = expiry <= datetime.now(timezone.utc) + timedelta(minutes=5)
        else:
            needs_refresh = False

        if needs_refresh and account.refresh_token:
            refresh_tok = decrypt_password(account.refresh_token)
            provider = account.provider.value if hasattr(account.provider, "value") else account.provider
            if provider == EmailProvider.GMAIL.value:
                result = await refresh_google_token(refresh_tok)
            else:
                result = await refresh_microsoft_token(refresh_tok)

            account.access_token = encrypt_password(result["access_token"])
            account.token_expires_at = result["expires_at"]
            await db.commit()
            access_token = result["access_token"]

        return access_token

    def _fetch_messages_sync_oauth(
        self,
        host: str,
        username: str,
        access_token: str,
        since_date: datetime,
        fallback_email: str,
    ) -> List[_RawMessage]:
        """Blocking IMAP fetch using XOAUTH2 — runs in a thread pool."""
        messages: List[_RawMessage] = []
        with MailBox(host).xoauth2(username, access_token) as mailbox:
            for msg in mailbox.fetch(AND(date__gt=since_date.date())):
                rfc_message_id = (msg.headers.get("message-id") or "").strip() or str(msg.uid)
                messages.append(
                    _RawMessage(
                        message_id=rfc_message_id,
                        from_address=msg.from_ or "",
                        from_name=msg.from_values.full if msg.from_values else None,
                        to_address=(msg.to[0] if msg.to else fallback_email),
                        subject=msg.subject or "",
                        body_text=msg.text or "",
                        body_html=msg.html or None,
                        received_at=msg.date or datetime.now(timezone.utc),
                    )
                )
        return messages

    def _fetch_messages_sync(
        self,
        host: str,
        username: str,
        password: str,
        since_date: datetime,
        fallback_email: str,
    ) -> List[_RawMessage]:
        """Blocking IMAP fetch — runs in a thread pool via asyncio.to_thread."""
        messages: List[_RawMessage] = []
        with MailBox(host).login(username, password) as mailbox:
            for msg in mailbox.fetch(AND(date__gt=since_date.date())):
                rfc_message_id = (msg.headers.get("message-id") or "").strip() or str(msg.uid)
                messages.append(
                    _RawMessage(
                        message_id=rfc_message_id,
                        from_address=msg.from_ or "",
                        from_name=msg.from_values.full if msg.from_values else None,
                        to_address=(msg.to[0] if msg.to else fallback_email),
                        subject=msg.subject or "",
                        body_text=msg.text or "",
                        body_html=msg.html or None,
                        received_at=msg.date or datetime.now(timezone.utc),
                    )
                )
        return messages

    def _test_connection_sync_oauth(self, host: str, username: str, access_token: str) -> bool:
        """Blocking XOAUTH2 IMAP connection test — runs in a thread pool."""
        try:
            with MailBox(host).xoauth2(username, access_token) as mailbox:
                return mailbox.folder.exists("INBOX")
        except Exception:
            return False

    def _test_connection_sync(self, host: str, username: str, password: str) -> bool:
        """Blocking IMAP connection test — runs in a thread pool."""
        try:
            with MailBox(host).login(username, password) as mailbox:
                return mailbox.folder.exists("INBOX")
        except Exception:
            return False

    async def fetch_new_emails(
        self,
        account: EmailAccount,
        db: AsyncSession,
    ) -> List[Email]:
        """Fetch new emails from an IMAP account without blocking the event loop.

        The blocking IMAP I/O runs in a thread pool; the subsequent DB writes
        are fully async.
        """
        imap_cfg = self.get_imap_settings(account)
        username = account.imap_username or account.email
        since_date = account.last_sync_at or datetime.now(timezone.utc) - timedelta(days=7)

        try:
            if account.access_token:
                access_token = await self.ensure_token_fresh(account, db)
                raw_messages: List[_RawMessage] = await asyncio.to_thread(
                    self._fetch_messages_sync_oauth,
                    imap_cfg["host"],
                    username,
                    access_token,
                    since_date,
                    account.email,
                )
            else:
                password = decrypt_password(account.imap_password) if account.imap_password else ""
                raw_messages = await asyncio.to_thread(
                    self._fetch_messages_sync,
                    imap_cfg["host"],
                    username,
                    password,
                    since_date,
                    account.email,
                )
        except Exception as e:
            account.last_error = str(e)[:500]
            await db.commit()
            raise

        new_emails: List[Email] = []

        for raw in raw_messages:
            result = await db.execute(
                select(Email).where(Email.message_id == raw.message_id)
            )
            if result.scalar_one_or_none():
                continue

            email = Email(
                user_id=account.user_id,
                account_id=account.id,
                message_id=raw.message_id,
                from_address=raw.from_address,
                from_name=raw.from_name,
                to_address=raw.to_address,
                subject=raw.subject,
                body_text=raw.body_text,
                body_html=raw.body_html,
                received_at=raw.received_at,
                processed_status=ProcessedStatus.PENDING,
            )
            db.add(email)
            await db.flush()
            new_emails.append(email)

        await db.commit()
        return new_emails

    async def test_connection(self, account: EmailAccount, db: Optional[AsyncSession] = None) -> bool:
        """Test IMAP connection without blocking the event loop."""
        imap_cfg = self.get_imap_settings(account)
        username = account.imap_username or account.email

        if account.access_token:
            if db is None:
                access_token = decrypt_password(account.access_token)
            else:
                access_token = await self.ensure_token_fresh(account, db)
            return await asyncio.to_thread(
                self._test_connection_sync_oauth,
                imap_cfg["host"],
                username,
                access_token,
            )

        password = decrypt_password(account.imap_password) if account.imap_password else ""
        return await asyncio.to_thread(
            self._test_connection_sync,
            imap_cfg["host"],
            username,
            password,
        )

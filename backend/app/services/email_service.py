import httpx
import logging
from ..config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


async def send_email(to: str, subject: str, html_body: str) -> bool:
    """Send email via Mailgun. Returns True on success."""
    if not settings.MAILGUN_API_KEY or not settings.MAILGUN_DOMAIN:
        logger.warning(f"Email not sent (Mailgun not configured): {subject} → {to}")
        return False
    async with httpx.AsyncClient() as client:
        try:
            resp = await client.post(
                f"https://api.mailgun.net/v3/{settings.MAILGUN_DOMAIN}/messages",
                auth=("api", settings.MAILGUN_API_KEY),
                data={
                    "from": settings.EMAIL_FROM,
                    "to": to,
                    "subject": subject,
                    "html": html_body,
                },
                timeout=10,
            )
            resp.raise_for_status()
            return True
        except Exception as e:
            logger.error(f"Mailgun error: {e}")
            return False

import enum
from datetime import datetime
from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import (
    JSON,
    Boolean,
    Column,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

if TYPE_CHECKING:
    from app.models.user import User
    from app.models.application import Application


class EmailProvider(str, enum.Enum):
    GMAIL = "gmail"
    OUTLOOK = "outlook"
    YAHOO = "yahoo"
    OTHER = "other"


class EmailAccount(Base):
    __tablename__ = "email_accounts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )

    # Provider info
    provider: Mapped[EmailProvider] = mapped_column(Enum(EmailProvider), nullable=False)
    email: Mapped[str] = mapped_column(String(255), nullable=False)

    # IMAP settings
    imap_host: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    imap_port: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    imap_username: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    imap_password: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    # OAuth tokens (for Gmail/Outlook)
    access_token: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    refresh_token: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    token_expires_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    # Sync status
    last_sync_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    last_error: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="email_accounts")
    emails: Mapped[List["Email"]] = relationship(
        "Email", back_populates="account", cascade="all, delete-orphan"
    )

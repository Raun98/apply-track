import enum
from datetime import datetime, timezone
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
    from app.models.email_account import EmailAccount


class ProcessedStatus(str, enum.Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    PROCESSED = "processed"
    FAILED = "failed"
    IGNORED = "ignored"


class Email(Base):
    __tablename__ = "emails"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    account_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("email_accounts.id", ondelete="SET NULL"), nullable=True
    )

    # Email metadata
    message_id: Mapped[str] = mapped_column(String(500), unique=True, index=True)
    from_address: Mapped[str] = mapped_column(String(255), nullable=False)
    from_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    to_address: Mapped[str] = mapped_column(String(255), nullable=False)
    subject: Mapped[str] = mapped_column(String(500), nullable=False)

    # Content
    body_text: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    body_html: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Timestamps
    received_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    # Processing
    parsed_data: Mapped[Optional[dict]] = mapped_column(JSON, default=dict)
    processed_status: Mapped[ProcessedStatus] = mapped_column(
        Enum(ProcessedStatus), default=ProcessedStatus.PENDING
    )
    processing_error: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Link to application
    application_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("applications.id", ondelete="SET NULL"), nullable=True
    )

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="emails")
    account: Mapped[Optional["EmailAccount"]] = relationship(
        "EmailAccount", back_populates="emails"
    )
    application: Mapped[Optional["Application"]] = relationship(
        "Application", back_populates="emails"
    )

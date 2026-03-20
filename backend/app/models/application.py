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
    from app.models.email import Email


class ApplicationStatus(str, enum.Enum):
    APPLIED = "applied"
    SCREENING = "screening"
    INTERVIEW = "interview"
    OFFER = "offer"
    REJECTED = "rejected"
    ACCEPTED = "accepted"


class JobSource(str, enum.Enum):
    LINKEDIN = "linkedin"
    NAUKRI = "naukri"
    INDEED = "indeed"
    MANUAL = "manual"
    UNKNOWN = "unknown"


class Application(Base):
    __tablename__ = "applications"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )

    # Job details
    company_name: Mapped[str] = mapped_column(String(255), nullable=False)
    position_title: Mapped[str] = mapped_column(String(255), nullable=False)
    location: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    salary_range: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)

    # Source and status
    source: Mapped[JobSource] = mapped_column(
        Enum(JobSource), default=JobSource.UNKNOWN
    )
    status: Mapped[ApplicationStatus] = mapped_column(
        Enum(ApplicationStatus), default=ApplicationStatus.APPLIED
    )

    # Timeline
    applied_date: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    last_updated: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    # Additional info
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    email_thread_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    extra_data: Mapped[Optional[dict]] = mapped_column(JSON, default=dict)

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="applications")
    emails: Mapped[List["Email"]] = relationship(
        "Email", back_populates="application"
    )
    status_history: Mapped[List["StatusHistory"]] = relationship(
        "StatusHistory", back_populates="application", cascade="all, delete-orphan"
    )
    activities: Mapped[List["Activity"]] = relationship(
        "Activity", back_populates="application", cascade="all, delete-orphan"
    )


class StatusHistory(Base):
    __tablename__ = "status_history"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    application_id: Mapped[int] = mapped_column(
        ForeignKey("applications.id", ondelete="CASCADE"), nullable=False
    )
    from_status: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    to_status: Mapped[str] = mapped_column(String(50), nullable=False)
    changed_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    email_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("emails.id", ondelete="SET NULL"), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # Relationships
    application: Mapped["Application"] = relationship(
        "Application", back_populates="status_history"
    )


class Activity(Base):
    __tablename__ = "activities"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    application_id: Mapped[int] = mapped_column(
        ForeignKey("applications.id", ondelete="CASCADE"), nullable=False
    )
    type: Mapped[str] = mapped_column(String(50), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    extra_data: Mapped[Optional[dict]] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # Relationships
    user: Mapped["User"] = relationship("User")
    application: Mapped["Application"] = relationship(
        "Application", back_populates="activities"
    )

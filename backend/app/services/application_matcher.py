from datetime import datetime, timedelta
from typing import List, Optional

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_

from app.models.application import Application, ApplicationStatus, JobSource
from app.models.email import Email


class ApplicationMatcherService:
    """Service to match incoming emails to existing applications."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def find_matching_application(
        self,
        user_id: int,
        company_name: Optional[str],
        position_title: Optional[str],
        from_address: str,
    ) -> Optional[Application]:
        """Find an existing application that matches the email."""
        if not company_name and not position_title:
            return None

        query = select(Application).where(
            Application.user_id == user_id
        )

        # Build matching conditions
        conditions = []

        if company_name:
            # Fuzzy match on company name
            conditions.append(
                Application.company_name.ilike(f"%{company_name}%")
            )

        if position_title:
            # Fuzzy match on position
            conditions.append(
                Application.position_title.ilike(f"%{position_title}%")
            )

        if conditions:
            query = query.where(or_(*conditions))

        # Order by most recent
        query = query.order_by(Application.applied_date.desc()).limit(1)

        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def create_application_from_email(
        self,
        user_id: int,
        company_name: str,
        position_title: str,
        source: str,
        status: str,
        location: Optional[str] = None,
        email_id: Optional[int] = None,
    ) -> Application:
        """Create a new application from parsed email data."""
        # Map source string to enum
        source_enum = JobSource.UNKNOWN
        if source:
            source_lower = source.lower()
            if source_lower in ["linkedin", "naukri", "indeed", "manual"]:
                source_enum = JobSource(source_lower)

        # Map status string to enum
        status_enum = ApplicationStatus.APPLIED
        if status:
            status_lower = status.lower()
            if status_lower in ["applied", "screening", "interview", "offer", "rejected", "accepted"]:
                status_enum = ApplicationStatus(status_lower)

        application = Application(
            user_id=user_id,
            company_name=company_name or "Unknown Company",
            position_title=position_title or "Unknown Position",
            location=location,
            source=source_enum,
            status=status_enum,
            email_thread_id=str(email_id) if email_id else None,
            metadata={"created_from_email": True},
        )

        self.db.add(application)
        await self.db.commit()
        await self.db.refresh(application)

        return application

    async def update_application_status(
        self,
        application: Application,
        new_status: str,
        reason: Optional[str] = None,
        email_id: Optional[int] = None,
    ) -> bool:
        """Update application status and create history entry."""
        from app.models.application import StatusHistory

        old_status = application.status.value

        if new_status.lower() == old_status:
            return False

        # Map new status
        status_enum = ApplicationStatus.APPLIED
        if new_status.lower() in ["applied", "screening", "interview", "offer", "rejected", "accepted"]:
            status_enum = ApplicationStatus(new_status.lower())

        # Update application
        application.status = status_enum
        application.last_updated = datetime.utcnow()

        # Create status history
        history = StatusHistory(
            application_id=application.id,
            from_status=old_status,
            to_status=status_enum.value,
            reason=reason,
            email_id=email_id,
        )
        self.db.add(history)

        await self.db.commit()
        return True

    async def get_recent_applications(
        self,
        user_id: int,
        days: int = 30,
    ) -> List[Application]:
        """Get applications from the last N days."""
        cutoff_date = datetime.utcnow() - timedelta(days=days)

        query = select(Application).where(
            and_(
                Application.user_id == user_id,
                Application.applied_date >= cutoff_date,
            )
        ).order_by(Application.applied_date.desc())

        result = await self.db.execute(query)
        return result.scalars().all()

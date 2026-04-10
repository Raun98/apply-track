from datetime import datetime, timedelta
from typing import List, Optional

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_

from app.models.application import Application, ApplicationStatus, JobSource
from app.models.email import Email


# Statuses that represent genuine forward progress — used when the LLM
# returns the generic "update" status (meaning "something changed" but not
# specifying what).  We keep the current status in that case.
_PROGRESS_STATUSES = {
    ApplicationStatus.SCREENING,
    ApplicationStatus.INTERVIEW,
    ApplicationStatus.OFFER,
    ApplicationStatus.ACCEPTED,
    ApplicationStatus.REJECTED,
}

# Status ordering — higher number = further along the funnel.
# We never move a card backwards automatically.
_STATUS_ORDER = {
    ApplicationStatus.APPLIED: 0,
    ApplicationStatus.SCREENING: 1,
    ApplicationStatus.INTERVIEW: 2,
    ApplicationStatus.OFFER: 3,
    ApplicationStatus.ACCEPTED: 4,
    ApplicationStatus.REJECTED: 5,
    ApplicationStatus.UPDATE: -1,   # special — see _resolve_status
}


def _resolve_status(
    new_status_str: str,
    current_status: ApplicationStatus,
) -> Optional[ApplicationStatus]:
    """
    Map an LLM-returned status string to a concrete ApplicationStatus.

    Rules:
    - "update" → keep current status (it's a generic progress signal)
    - Any other valid status → only accept if it moves the card *forward*
      in the funnel (prevent auto-regression, e.g. interview → applied)
    - Unknown strings → None (no change)
    """
    if not new_status_str:
        return None

    try:
        new_enum = ApplicationStatus(new_status_str.lower())
    except ValueError:
        return None

    if new_enum == ApplicationStatus.UPDATE:
        # Generic "update" — don't change status
        return None

    # Never auto-move backwards (regression protection)
    new_order = _STATUS_ORDER.get(new_enum, -1)
    cur_order = _STATUS_ORDER.get(current_status, -1)
    if new_order <= cur_order and new_enum != ApplicationStatus.REJECTED:
        return None

    return new_enum


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
        """
        Find an existing application that matches the email.

        Matching strategy (strictest → most lenient):
        1. company AND position both match  (AND — highest confidence)
        2. company match only (if position is missing from parsed data)
        3. position match only (if company is missing from parsed data)

        This prevents the previous bug where a single OR condition could
        match unrelated applications sharing only a common word.
        """
        if not company_name and not position_title:
            return None

        base_query = (
            select(Application)
            .where(Application.user_id == user_id)
            .order_by(Application.applied_date.desc())
        )

        # Strategy 1: AND match (company + position)
        if company_name and position_title:
            result = await self.db.execute(
                base_query.where(
                    and_(
                        Application.company_name.ilike(f"%{company_name}%"),
                        Application.position_title.ilike(f"%{position_title}%"),
                    )
                ).limit(1)
            )
            match = result.scalar_one_or_none()
            if match:
                return match

        # Strategy 2: company-only match (when position not extracted)
        if company_name:
            result = await self.db.execute(
                base_query.where(
                    Application.company_name.ilike(f"%{company_name}%")
                ).limit(1)
            )
            match = result.scalar_one_or_none()
            if match:
                return match

        # Strategy 3: position-only match (when company not extracted)
        if position_title:
            result = await self.db.execute(
                base_query.where(
                    Application.position_title.ilike(f"%{position_title}%")
                ).limit(1)
            )
            return result.scalar_one_or_none()

        return None

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
        source_enum = JobSource.UNKNOWN
        if source:
            source_lower = source.lower()
            if source_lower in [e.value for e in JobSource]:
                source_enum = JobSource(source_lower)

        # Resolve status — default to APPLIED for new records
        status_enum = ApplicationStatus.APPLIED
        if status and status.lower() not in ("update", ""):
            try:
                candidate = ApplicationStatus(status.lower())
                if candidate != ApplicationStatus.UPDATE:
                    status_enum = candidate
            except ValueError:
                pass

        application = Application(
            user_id=user_id,
            company_name=company_name or "Unknown Company",
            position_title=position_title or "Unknown Position",
            location=location,
            source=source_enum,
            status=status_enum,
            email_thread_id=str(email_id) if email_id else None,
            extra_data={"created_from_email": True},
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
        """
        Update application status and create history entry.
        Returns True if the status actually changed.
        """
        from app.models.application import StatusHistory

        resolved = _resolve_status(new_status, application.status)
        if resolved is None:
            return False

        old_status = application.status

        application.status = resolved
        application.last_updated = datetime.utcnow()

        history = StatusHistory(
            application_id=application.id,
            from_status=old_status.value,
            to_status=resolved.value,
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

        query = (
            select(Application)
            .where(
                and_(
                    Application.user_id == user_id,
                    Application.applied_date >= cutoff_date,
                )
            )
            .order_by(Application.applied_date.desc())
        )

        result = await self.db.execute(query)
        return result.scalars().all()

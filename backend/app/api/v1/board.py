from typing import Any, List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc

from app.api.deps import get_db, get_current_active_user
from app.models.user import User
from app.models.application import Application, ApplicationStatus
from app.schemas import BoardColumn, MoveCardRequest, ApplicationResponse

router = APIRouter()


# Default board columns
DEFAULT_COLUMNS = [
    {"id": "applied", "title": "Applied", "order": 0},
    {"id": "screening", "title": "Screening", "order": 1},
    {"id": "interview", "title": "Interview", "order": 2},
    {"id": "offer", "title": "Offer", "order": 3},
    {"id": "rejected", "title": "Rejected", "order": 4},
    {"id": "accepted", "title": "Accepted", "order": 5},
]


@router.get("/columns")
async def get_board_columns(
    current_user: User = Depends(get_current_active_user),
) -> Any:
    """Get board column configuration."""
    # For now, return default columns
    # In the future, this could be user-configurable
    return DEFAULT_COLUMNS


@router.get("/applications")
async def get_board_applications(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """Get all applications organized by board columns."""
    result = await db.execute(
        select(Application)
        .where(Application.user_id == current_user.id)
        .order_by(desc(Application.last_updated))
    )
    applications = result.scalars().all()

    # Organize by status
    columns = {col["id"]: [] for col in DEFAULT_COLUMNS}

    for app in applications:
        status_key = app.status.value
        if status_key in columns:
            columns[status_key].append(ApplicationResponse.model_validate(app))

    return {
        "columns": DEFAULT_COLUMNS,
        "data": columns,
    }


@router.post("/cards/{application_id}/move")
async def move_card(
    application_id: int,
    data: MoveCardRequest,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """Move an application card to a different column."""
    from app.models.application import StatusHistory

    # Validate target column
    valid_columns = [col["id"] for col in DEFAULT_COLUMNS]
    if data.to_column not in valid_columns:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid column. Must be one of: {', '.join(valid_columns)}",
        )

    # Get application
    result = await db.execute(
        select(Application).where(
            (Application.id == application_id) &
            (Application.user_id == current_user.id)
        )
    )
    application = result.scalar_one_or_none()

    if not application:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Application not found",
        )

    # Update status
    old_status = application.status
    new_status = ApplicationStatus(data.to_column)

    if old_status != new_status:
        application.status = new_status

        # Create status history
        history = StatusHistory(
            application_id=application.id,
            from_status=old_status.value,
            to_status=new_status.value,
            reason="Moved via board",
        )
        db.add(history)

        await db.commit()

    return ApplicationResponse.model_validate(application)


@router.get("/stats")
async def get_board_stats(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """Get statistics for the board."""
    from sqlalchemy import func

    # Count by status
    result = await db.execute(
        select(Application.status, func.count(Application.id))
        .where(Application.user_id == current_user.id)
        .group_by(Application.status)
    )
    status_counts = {status.value: count for status, count in result.all()}

    # Total applications
    total = sum(status_counts.values())

    # Calculate rates
    interview_count = status_counts.get("interview", 0) + status_counts.get("offer", 0) + status_counts.get("accepted", 0)
    offer_count = status_counts.get("offer", 0) + status_counts.get("accepted", 0)
    accepted_count = status_counts.get("accepted", 0)

    response_rate = (interview_count / total * 100) if total > 0 else 0
    interview_rate = (interview_count / total * 100) if total > 0 else 0
    offer_rate = (offer_count / total * 100) if total > 0 else 0

    return {
        "total_applications": total,
        "by_status": status_counts,
        "response_rate": round(response_rate, 1),
        "interview_rate": round(interview_rate, 1),
        "offer_rate": round(offer_rate, 1),
    }

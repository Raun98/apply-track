from typing import Any, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc, func

from app.api.deps import get_db, get_current_active_user
from app.models.user import User
from app.models.application import Application, ApplicationStatus, JobSource, StatusHistory
from app.schemas import (
    ApplicationCreate,
    ApplicationUpdate,
    ApplicationResponse,
    ApplicationListResponse,
    StatusHistoryResponse,
)

router = APIRouter()


@router.get("", response_model=ApplicationListResponse)
async def list_applications(
    status: Optional[str] = Query(None, description="Filter by status"),
    source: Optional[str] = Query(None, description="Filter by source"),
    search: Optional[str] = Query(None, description="Search in company/position"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """List user's job applications with filters."""
    query = select(Application).where(Application.user_id == current_user.id)

    # Apply filters
    if status:
        try:
            status_enum = ApplicationStatus(status.lower())
            query = query.where(Application.status == status_enum)
        except ValueError:
            pass

    if source:
        try:
            source_enum = JobSource(source.lower())
            query = query.where(Application.source == source_enum)
        except ValueError:
            pass

    if search:
        search_filter = f"%{search}%"
        query = query.where(
            (Application.company_name.ilike(search_filter)) |
            (Application.position_title.ilike(search_filter))
        )

    # Get total count
    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar()

    # Apply pagination
    query = query.order_by(desc(Application.last_updated))
    query = query.offset((page - 1) * page_size).limit(page_size)

    result = await db.execute(query)
    items = result.scalars().all()

    return {
        "items": items,
        "total": total,
        "page": page,
        "page_size": page_size,
    }


@router.post("", response_model=ApplicationResponse, status_code=status.HTTP_201_CREATED)
async def create_application(
    data: ApplicationCreate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """Create a new job application manually."""
    # Map source
    source_enum = JobSource.MANUAL
    if data.source:
        try:
            source_enum = JobSource(data.source.lower())
        except ValueError:
            pass

    # Map status
    status_enum = ApplicationStatus.APPLIED
    if data.status:
        try:
            status_enum = ApplicationStatus(data.status.lower())
        except ValueError:
            pass

    application = Application(
        user_id=current_user.id,
        company_name=data.company_name,
        position_title=data.position_title,
        location=data.location,
        salary_range=data.salary_range,
        source=source_enum,
        status=status_enum,
        notes=data.notes,
    )

    db.add(application)
    await db.commit()
    await db.refresh(application)

    return application


@router.get("/{application_id}", response_model=ApplicationResponse)
async def get_application(
    application_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """Get a specific application."""
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

    return application


@router.patch("/{application_id}", response_model=ApplicationResponse)
async def update_application(
    application_id: int,
    data: ApplicationUpdate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """Update an application."""
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

    # Track status change
    old_status = application.status

    # Update fields
    if data.company_name is not None:
        application.company_name = data.company_name
    if data.position_title is not None:
        application.position_title = data.position_title
    if data.location is not None:
        application.location = data.location
    if data.salary_range is not None:
        application.salary_range = data.salary_range
    if data.notes is not None:
        application.notes = data.notes

    if data.status is not None:
        try:
            new_status = ApplicationStatus(data.status.lower())
            if new_status != old_status:
                application.status = new_status

                # Create status history
                history = StatusHistory(
                    application_id=application.id,
                    from_status=old_status.value,
                    to_status=new_status.value,
                    reason="Manual update via API",
                )
                db.add(history)
        except ValueError:
            pass

    await db.commit()
    await db.refresh(application)

    return application


@router.delete("/{application_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_application(
    application_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> None:
    """Delete an application."""
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

    await db.delete(application)
    await db.commit()


@router.get("/{application_id}/history", response_model=List[StatusHistoryResponse])
async def get_application_history(
    application_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """Get status history for an application."""
    # Verify application belongs to user
    result = await db.execute(
        select(Application).where(
            (Application.id == application_id) &
            (Application.user_id == current_user.id)
        )
    )
    if not result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Application not found",
        )

    result = await db.execute(
        select(StatusHistory)
        .where(StatusHistory.application_id == application_id)
        .order_by(desc(StatusHistory.changed_at))
    )

    return result.scalars().all()

from typing import Any, List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc, func

from app.api.deps import get_db, get_current_active_user
from app.models.user import User
from app.models.email_account import EmailAccount, EmailProvider
from app.models.subscription import Subscription, SubscriptionPlan, SubscriptionStatus
from app.schemas import EmailAccountCreate, EmailAccountResponse
from app.services.imap_service import IMAPService
from app.services.encryption import encrypt_password

router = APIRouter()


@router.get("", response_model=List[EmailAccountResponse])
async def list_email_accounts(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """List user's connected email accounts."""
    result = await db.execute(
        select(EmailAccount)
        .where(EmailAccount.user_id == current_user.id)
        .order_by(desc(EmailAccount.created_at))
    )
    return result.scalars().all()


@router.post("", response_model=EmailAccountResponse, status_code=status.HTTP_201_CREATED)
async def create_email_account(
    data: EmailAccountCreate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """Connect a new email account."""
    sub_result = await db.execute(
        select(Subscription)
        .where(Subscription.user_id == current_user.id)
        .where(Subscription.status == SubscriptionStatus.ACTIVE)
    )
    active_sub = sub_result.scalar_one_or_none()
    if active_sub:
        plan_result = await db.execute(
            select(SubscriptionPlan).where(SubscriptionPlan.id == active_sub.plan_id)
        )
        plan = plan_result.scalar_one_or_none()
        if plan and plan.features:
            max_accounts = plan.features.get("email_accounts")
            if max_accounts is not None and max_accounts != -1:
                count_result = await db.execute(
                    select(func.count()).select_from(EmailAccount).where(EmailAccount.user_id == current_user.id)
                )
                current_count = count_result.scalar_one()
                if current_count >= max_accounts:
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail="Email account limit reached for your plan. Please upgrade.",
                    )

    # Map provider
    provider_enum = EmailProvider.OTHER
    try:
        provider_enum = EmailProvider(data.provider.lower())
    except ValueError:
        pass

    # Set default IMAP settings based on provider
    imap_host = data.imap_host
    imap_port = data.imap_port

    if not imap_host:
        provider_defaults = {
            "gmail": ("imap.gmail.com", 993),
            "outlook": ("outlook.office365.com", 993),
            "yahoo": ("imap.mail.yahoo.com", 993),
        }
        if provider_enum.value in provider_defaults:
            imap_host, imap_port = provider_defaults[provider_enum.value]

    account = EmailAccount(
        user_id=current_user.id,
        provider=provider_enum,
        email=data.email,
        imap_host=imap_host,
        imap_port=imap_port,
        imap_username=data.imap_username or data.email,
        imap_password=encrypt_password(data.imap_password) if data.imap_password else None,
    )

    # Test connection
    if data.imap_password:
        imap_service = IMAPService()
        try:
            is_valid = await imap_service.test_connection(account)
            if not is_valid:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Could not connect to email server. Please check your credentials.",
                )
        except Exception:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Could not connect to email server. Please check your credentials and IMAP settings.",
            )

    db.add(account)
    await db.commit()
    await db.refresh(account)

    return account


@router.delete("/{account_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_email_account(
    account_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> None:
    """Delete an email account."""
    result = await db.execute(
        select(EmailAccount).where(
            (EmailAccount.id == account_id) &
            (EmailAccount.user_id == current_user.id)
        )
    )
    account = result.scalar_one_or_none()

    if not account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Email account not found",
        )

    await db.delete(account)
    await db.commit()


@router.post("/{account_id}/sync")
async def sync_email_account(
    account_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """Trigger manual sync for an email account."""
    from app.tasks.email_processor import poll_imap_account

    result = await db.execute(
        select(EmailAccount).where(
            (EmailAccount.id == account_id) &
            (EmailAccount.user_id == current_user.id)
        )
    )
    account = result.scalar_one_or_none()

    if not account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Email account not found",
        )

    # Queue sync task
    task = poll_imap_account.delay(account_id)

    return {
        "message": "Sync queued",
        "task_id": task.id,
    }

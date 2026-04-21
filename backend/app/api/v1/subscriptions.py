import hmac
import hashlib
import json
import logging
from typing import Any, List, Optional
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.api.deps import get_db, get_current_user
from app.models.user import User
from app.models.subscription import Subscription, SubscriptionPlan, SubscriptionStatus, PlanType
from app.schemas import SubscriptionResponse, SubscriptionCreate, SubscriptionUpdate, SubscriptionPlanResponse
from app.services.razorpay_service import get_razorpay_service
from app.config import get_settings

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/plans", response_model=List[SubscriptionPlanResponse])
async def get_subscription_plans(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get all active subscription plans"""
    result = await db.execute(
        select(SubscriptionPlan).where(SubscriptionPlan.is_active == True)
    )
    plans = result.scalars().all()
    return plans


@router.get("/current", response_model=Optional[SubscriptionResponse])
async def get_current_subscription(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get current user's active subscription"""
    result = await db.execute(
        select(Subscription)
        .where(Subscription.user_id == current_user.id)
        .where(Subscription.status == SubscriptionStatus.ACTIVE)
    )
    subscription = result.scalar_one_or_none()
    return subscription


@router.post("/activate-free", response_model=dict)
async def activate_free_plan(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Activate the free plan for the current user (no Razorpay needed)."""
    # Check if user already has an active subscription
    result = await db.execute(
        select(Subscription)
        .where(Subscription.user_id == current_user.id)
        .where(Subscription.status == SubscriptionStatus.ACTIVE)
    )
    if result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User already has an active subscription",
        )

    # Find the free plan
    result = await db.execute(
        select(SubscriptionPlan).where(SubscriptionPlan.plan_type == PlanType.FREE)
    )
    free_plan = result.scalar_one_or_none()
    if not free_plan:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Free plan not found",
        )

    subscription = Subscription(
        user_id=current_user.id,
        plan_id=free_plan.id,
        status=SubscriptionStatus.ACTIVE,
        current_period_start=datetime.now(timezone.utc),
    )
    db.add(subscription)
    await db.commit()
    await db.refresh(subscription)

    return {
        "subscription_id": subscription.id,
        "status": subscription.status.value,
        "plan": free_plan.name,
    }


@router.post("/create", response_model=dict)
async def create_subscription(
    subscription_data: SubscriptionCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Create a new subscription"""
    # Check if user already has an active subscription
    result = await db.execute(
        select(Subscription)
        .where(Subscription.user_id == current_user.id)
        .where(Subscription.status == SubscriptionStatus.ACTIVE)
    )
    if result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User already has an active subscription",
        )

    # Get plan details
    result = await db.execute(
        select(SubscriptionPlan).where(SubscriptionPlan.id == subscription_data.plan_id)
    )
    plan = result.scalar_one_or_none()

    if not plan:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Subscription plan not found",
        )

    if not plan.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Subscription plan is not active",
        )

    # Free plan — bypass Razorpay
    if plan.plan_type == PlanType.FREE:
        subscription = Subscription(
            user_id=current_user.id,
            plan_id=plan.id,
            status=SubscriptionStatus.ACTIVE,
            current_period_start=datetime.now(timezone.utc),
        )
        db.add(subscription)
        await db.commit()
        await db.refresh(subscription)
        return {
            "subscription_id": subscription.id,
            "status": subscription.status.value,
            "plan": plan.name,
        }

    # Paid plan — require razorpay_plan_id
    if not plan.razorpay_plan_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Razorpay plan ID not configured for this plan",
        )

    razorpay_svc = get_razorpay_service()
    if not razorpay_svc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Payment service unavailable",
        )

    # Create Razorpay customer
    customer_data = razorpay_svc.create_customer(
        email=current_user.email,
        name=current_user.name or current_user.email.split("@")[0],
    )
    customer_id = customer_data["id"]

    # Create Razorpay subscription
    razorpay_subscription = razorpay_svc.create_subscription(
        plan_id=plan.razorpay_plan_id,
        customer_id=customer_id,
        notes={
            "user_id": current_user.id,
            "plan_id": plan.id,
            "email": current_user.email,
        },
    )

    subscription = Subscription(
        user_id=current_user.id,
        plan_id=plan.id,
        razorpay_customer_id=customer_id,
        razorpay_subscription_id=razorpay_subscription["id"],
        status=SubscriptionStatus.INACTIVE,  # activated via webhook
        current_period_start=datetime.fromtimestamp(razorpay_subscription["current_start"]),
        current_period_end=datetime.fromtimestamp(razorpay_subscription["current_end"]),
    )

    db.add(subscription)
    await db.commit()
    await db.refresh(subscription)

    return {
        "subscription_id": subscription.id,
        "razorpay_subscription_id": subscription.razorpay_subscription_id,
        "razorpay_payment_link": razorpay_subscription.get("short_url"),
        "status": subscription.status.value,
    }


@router.post("/cancel/{subscription_id}")
async def cancel_subscription(
    subscription_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Cancel a subscription"""
    result = await db.execute(
        select(Subscription)
        .where(Subscription.id == subscription_id)
        .where(Subscription.user_id == current_user.id)
    )
    subscription = result.scalar_one_or_none()

    if not subscription:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Subscription not found",
        )

    if subscription.status != SubscriptionStatus.ACTIVE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Subscription is not active",
        )

    # Cancel in Razorpay if applicable
    if subscription.razorpay_subscription_id:
        razorpay_svc = get_razorpay_service()
        if razorpay_svc:
            razorpay_svc.cancel_subscription(subscription.razorpay_subscription_id)

    subscription.status = SubscriptionStatus.CANCELLED
    subscription.cancelled_at = datetime.now(timezone.utc)
    await db.commit()

    return {"message": "Subscription cancelled successfully"}


async def verify_razorpay_webhook_signature(body: bytes, signature: str, webhook_secret: str) -> bool:
    expected = hmac.new(
        webhook_secret.encode("utf-8"),
        body,
        hashlib.sha256,
    ).hexdigest()
    return hmac.compare_digest(expected, signature)


@router.post("/webhook")
async def razorpay_webhook(
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """Handle Razorpay webhook events"""
    body = await request.body()
    signature = request.headers.get("X-Razorpay-Signature", "")
    webhook_secret = get_settings().RAZORPAY_WEBHOOK_SECRET

    is_valid = await verify_razorpay_webhook_signature(body, signature, webhook_secret)
    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid webhook signature",
        )

    webhook_data = json.loads(body.decode("utf-8"))
    event = webhook_data.get("event")
    payload = webhook_data.get("payload", {})

    if event in ("subscription.completed", "subscription.activated"):
        subscription_entity = payload.get("subscription", {}).get("entity", {})
        subscription_id = subscription_entity.get("id")

        result = await db.execute(
            select(Subscription).where(
                Subscription.razorpay_subscription_id == subscription_id
            )
        )
        subscription = result.scalar_one_or_none()

        if subscription:
            subscription.status = SubscriptionStatus.ACTIVE
            await db.commit()

    elif event == "subscription.cancelled":
        subscription_entity = payload.get("subscription", {}).get("entity", {})
        subscription_id = subscription_entity.get("id")

        result = await db.execute(
            select(Subscription).where(
                Subscription.razorpay_subscription_id == subscription_id
            )
        )
        subscription = result.scalar_one_or_none()

        if subscription:
            subscription.status = SubscriptionStatus.CANCELLED
            subscription.cancelled_at = datetime.now(timezone.utc)
            await db.commit()

    elif event == "payment.failed":
        subscription_entity = payload.get("subscription", {}).get("entity", {})
        subscription_id = subscription_entity.get("id")

        result = await db.execute(
            select(Subscription).where(
                Subscription.razorpay_subscription_id == subscription_id
            )
        )
        subscription = result.scalar_one_or_none()

        if subscription:
            subscription.status = SubscriptionStatus.INACTIVE
            await db.commit()

    return {"status": "ok"}

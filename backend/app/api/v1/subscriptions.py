import hmac
import hashlib
import json
from typing import Any, List, Optional
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.api.deps import get_db, get_current_user
from app.models.user import User
from app.models.subscription import Subscription, SubscriptionPlan, SubscriptionStatus, PlanType
from app.schemas import SubscriptionResponse, SubscriptionCreate, SubscriptionUpdate, SubscriptionPlanResponse
from app.services.razorpay_service import razorpay_service
from app.config import get_settings

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
    existing_subscription = result.scalar_one_or_none()

    if existing_subscription:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User already has an active subscription"
        )

    # Get plan details
    result = await db.execute(
        select(SubscriptionPlan).where(SubscriptionPlan.id == subscription_data.plan_id)
    )
    plan = result.scalar_one_or_none()

    if not plan:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Subscription plan not found"
        )

    if not plan.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Subscription plan is not active"
        )

    # Create Razorpay customer
    customer_data = razorpay_service.create_customer(
        email=current_user.email,
        name=current_user.email.split('@')[0],  # Use email prefix as name
    )
    customer_id = customer_data["id"]

    # Create Razorpay subscription
    razorpay_subscription = razorpay_service.create_subscription(
        plan_id=plan.razorpay_plan_id,  # We'll need to add this field
        customer_id=customer_id,
        notes={
            "user_id": current_user.id,
            "plan_id": plan.id,
            "email": current_user.email
        }
    )

    # Create subscription record in database
    subscription = Subscription(
        user_id=current_user.id,
        plan_id=plan.id,
        razorpay_customer_id=customer_id,
        razorpay_subscription_id=razorpay_subscription["id"],
        status=SubscriptionStatus.ACTIVE,
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
        "status": subscription.status.value
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
            detail="Subscription not found"
        )

    if subscription.status != SubscriptionStatus.ACTIVE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Subscription is not active"
        )

    # Cancel in Razorpay
    if subscription.razorpay_subscription_id:
        razorpay_service.cancel_subscription(subscription.razorpay_subscription_id)

    # Update subscription status
    subscription.status = SubscriptionStatus.CANCELLED
    subscription.cancelled_at = datetime.utcnow()

    await db.commit()

    return {"message": "Subscription cancelled successfully"}


async def verify_razorpay_webhook_signature(body: bytes, signature: str, webhook_secret: str) -> bool:
    expected = hmac.new(
        webhook_secret.encode('utf-8'),
        body,
        hashlib.sha256
    ).hexdigest()
    return hmac.compare_digest(expected, signature)


@router.post("/webhook")
async def razorpay_webhook(
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """Handle Razorpay webhook events"""
    body = await request.body()
    raw_body = body.decode('utf-8')
    signature = request.headers.get('X-Razorpay-Signature', '')
    webhook_secret = get_settings().RAZORPAY_WEBHOOK_SECRET

    is_valid = await verify_razorpay_webhook_signature(raw_body, signature, webhook_secret)
    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid webhook signature"
        )

    webhook_data = json.loads(raw_body)

    event = webhook_data.get("event")
    payload = webhook_data.get("payload", {})

    if event == "subscription.completed":
        # Subscription payment successful
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
            # Update period details if needed
            await db.commit()

    elif event == "subscription.cancelled":
        # Subscription cancelled
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
            subscription.cancelled_at = datetime.utcnow()
            await db.commit()

    elif event == "payment.failed":
        # Payment failed
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
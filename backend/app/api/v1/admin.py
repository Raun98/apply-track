from datetime import datetime, timezone
from typing import Any, Dict, List, Literal, Optional

from fastapi import APIRouter, Depends, Header, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db, get_current_user
from app.models.user import User
from app.models.subscription import Subscription, SubscriptionPlan, SubscriptionStatus, PlanType
from app.models.coupon import Coupon
from app.services.razorpay_service import get_razorpay_service
from app.config import get_settings

router = APIRouter()


async def require_admin(
    x_admin_secret: str = Header(..., alias="X-Admin-Secret"),
    current_user: User = Depends(get_current_user),
) -> User:
    admin_secret = get_settings().ADMIN_SECRET
    if not admin_secret:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Admin mode not configured",
        )
    if x_admin_secret != admin_secret:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid admin secret",
        )
    return current_user


# ============= SCHEMAS =============

class PlanCreate(BaseModel):
    name: str
    plan_type: str
    price_monthly: int
    price_yearly: Optional[int] = None
    razorpay_plan_id: Optional[str] = None
    razorpay_plan_id_yearly: Optional[str] = None
    features: Dict[str, Any] = {}
    description: Optional[str] = None
    is_active: bool = True


class PlanUpdate(BaseModel):
    name: Optional[str] = None
    price_monthly: Optional[int] = None
    price_yearly: Optional[int] = None
    razorpay_plan_id: Optional[str] = None
    razorpay_plan_id_yearly: Optional[str] = None
    features: Optional[Dict[str, Any]] = None
    description: Optional[str] = None
    is_active: Optional[bool] = None


class CouponCreate(BaseModel):
    code: str
    discount_type: Literal["percentage", "fixed"]
    discount_value: int
    min_order_amount: Optional[int] = None
    max_uses: Optional[int] = None
    expires_at: Optional[datetime] = None
    is_active: bool = True


class CouponUpdate(BaseModel):
    code: Optional[str] = None
    discount_type: Optional[str] = None
    discount_value: Optional[int] = None
    min_order_amount: Optional[int] = None
    max_uses: Optional[int] = None
    current_uses: Optional[int] = None
    expires_at: Optional[datetime] = None
    is_active: Optional[bool] = None


# ============= PLANS =============

@router.get("/plans")
async def list_plans(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    """List all subscription plans."""
    result = await db.execute(select(SubscriptionPlan).order_by(SubscriptionPlan.price_monthly))
    plans = result.scalars().all()
    return plans


@router.get("/plans/{plan_id}")
async def get_plan(
    plan_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    """Get a specific plan."""
    result = await db.execute(select(SubscriptionPlan).where(SubscriptionPlan.id == plan_id))
    plan = result.scalar_one_or_none()
    if not plan:
        raise HTTPException(status_code=404, detail="Plan not found")
    return plan


@router.post("/plans")
async def create_plan(
    plan_data: PlanCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    """Create a new subscription plan."""
    plan = SubscriptionPlan(
        name=plan_data.name,
        plan_type=PlanType(plan_data.plan_type),
        price_monthly=plan_data.price_monthly,
        price_yearly=plan_data.price_yearly,
        razorpay_plan_id=plan_data.razorpay_plan_id,
        razorpay_plan_id_yearly=plan_data.razorpay_plan_id_yearly,
        features=plan_data.features,
        description=plan_data.description,
        is_active=plan_data.is_active,
    )
    db.add(plan)
    await db.commit()
    await db.refresh(plan)
    return plan


@router.patch("/plans/{plan_id}")
async def update_plan(
    plan_id: int,
    plan_data: PlanUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    """Update a subscription plan."""
    result = await db.execute(select(SubscriptionPlan).where(SubscriptionPlan.id == plan_id))
    plan = result.scalar_one_or_none()
    if not plan:
        raise HTTPException(status_code=404, detail="Plan not found")

    for field, value in plan_data.model_dump(exclude_unset=True).items():
        setattr(plan, field, value)

    await db.commit()
    await db.refresh(plan)
    return plan


@router.delete("/plans/{plan_id}")
async def delete_plan(
    plan_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    """Delete a subscription plan (soft delete by deactivating)."""
    result = await db.execute(select(SubscriptionPlan).where(SubscriptionPlan.id == plan_id))
    plan = result.scalar_one_or_none()
    if not plan:
        raise HTTPException(status_code=404, detail="Plan not found")

    plan.is_active = False
    await db.commit()
    return {"message": "Plan deactivated"}


# ============= SUBSCRIPTIONS =============

@router.get("/subscriptions")
async def list_subscriptions(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin),
    status_filter: Optional[str] = None,
    skip: int = 0,
    limit: int = 50,
):
    """List all subscriptions with optional status filter."""
    query = select(Subscription).order_by(Subscription.created_at.desc())
    
    if status_filter:
        query = query.where(Subscription.status == SubscriptionStatus(status_filter))
    
    query = query.offset(skip).limit(limit)
    result = await db.execute(query)
    subscriptions = result.scalars().all()
    
    # Get total count
    count_query = select(func.count(Subscription.id))
    if status_filter:
        count_query = count_query.where(Subscription.status == SubscriptionStatus(status_filter))
    total_result = await db.execute(count_query)
    total = total_result.scalar()
    
    return {"subscriptions": subscriptions, "total": total}


@router.get("/subscriptions/stats")
async def get_subscription_stats(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    """Get subscription statistics."""
    stats = {}
    for status_val in SubscriptionStatus:
        count_query = select(func.count(Subscription.id)).where(Subscription.status == status_val)
        result = await db.execute(count_query)
        stats[status_val.value] = result.scalar()
    
    # Get plan breakdown
    plan_query = select(
        SubscriptionPlan.name,
        func.count(Subscription.id).label('count')
    ).join(Subscription).group_by(SubscriptionPlan.name)
    plan_result = await db.execute(plan_query)
    plan_stats = [{"plan": row[0], "count": row[1]} for row in plan_result.fetchall()]
    
    total_users_result = await db.execute(select(func.count(User.id)))
    total_users = total_users_result.scalar()

    return {
        "by_status": stats,
        "by_plan": plan_stats,
        "total_users": total_users,
    }


@router.post("/subscriptions/{subscription_id}/cancel")
async def admin_cancel_subscription(
    subscription_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    """Admin cancel a subscription."""
    result = await db.execute(select(Subscription).where(Subscription.id == subscription_id))
    subscription = result.scalar_one_or_none()
    if not subscription:
        raise HTTPException(status_code=404, detail="Subscription not found")

    if subscription.razorpay_subscription_id:
        razorpay_svc = get_razorpay_service()
        if razorpay_svc:
            razorpay_svc.cancel_subscription(subscription.razorpay_subscription_id)

    subscription.status = SubscriptionStatus.CANCELLED
    subscription.cancelled_at = datetime.now(timezone.utc)
    await db.commit()
    
    return {"message": "Subscription cancelled"}


# ============= COUPONS =============

@router.get("/coupons")
async def list_coupons(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    """List all coupons."""
    result = await db.execute(select(Coupon).order_by(Coupon.created_at.desc()))
    coupons = result.scalars().all()
    return coupons


@router.get("/coupons/{coupon_id}")
async def get_coupon(
    coupon_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    """Get a specific coupon."""
    result = await db.execute(select(Coupon).where(Coupon.id == coupon_id))
    coupon = result.scalar_one_or_none()
    if not coupon:
        raise HTTPException(status_code=404, detail="Coupon not found")
    return coupon


@router.post("/coupons")
async def create_coupon(
    coupon_data: CouponCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    """Create a new coupon."""
    # Check if code already exists
    existing = await db.execute(select(Coupon).where(Coupon.code == coupon_data.code.upper()))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Coupon code already exists")

    coupon = Coupon(
        code=coupon_data.code.upper(),
        discount_type=coupon_data.discount_type,
        discount_value=coupon_data.discount_value,
        min_order_amount=coupon_data.min_order_amount,
        max_uses=coupon_data.max_uses,
        expires_at=coupon_data.expires_at,
        is_active=coupon_data.is_active,
    )
    db.add(coupon)
    await db.commit()
    await db.refresh(coupon)
    return coupon


@router.patch("/coupons/{coupon_id}")
async def update_coupon(
    coupon_id: int,
    coupon_data: CouponUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    """Update a coupon."""
    result = await db.execute(select(Coupon).where(Coupon.id == coupon_id))
    coupon = result.scalar_one_or_none()
    if not coupon:
        raise HTTPException(status_code=404, detail="Coupon not found")

    for field, value in coupon_data.model_dump(exclude_unset=True).items():
        setattr(coupon, field, value)

    await db.commit()
    await db.refresh(coupon)
    return coupon


@router.delete("/coupons/{coupon_id}")
async def delete_coupon(
    coupon_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    """Delete a coupon."""
    result = await db.execute(select(Coupon).where(Coupon.id == coupon_id))
    coupon = result.scalar_one_or_none()
    if not coupon:
        raise HTTPException(status_code=404, detail="Coupon not found")

    coupon.is_active = False
    await db.commit()
    return {"message": "Coupon deactivated"}


# ============= RAZORPAY HELPERS =============

@router.get("/razorpay/plans")
async def list_razorpay_plans(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    """Fetch plans from Razorpay (if configured)."""
    razorpay_svc = get_razorpay_service()
    if not razorpay_svc:
        raise HTTPException(
            status_code=503,
            detail="Razorpay not configured. Set RAZORPAY_KEY_ID and RAZORPAY_KEY_SECRET",
        )
    
    try:
        plans = razorpay_svc.list_plans()
        return plans
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/razorpay/sync-plans")
async def sync_plans_from_razorpay(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    """Sync plans from Razorpay to local database."""
    razorpay_svc = get_razorpay_service()
    if not razorpay_svc:
        raise HTTPException(status_code=503, detail="Razorpay not configured")
    
    try:
        razorpay_plans = razorpay_svc.list_plans()
        synced = []
        
        for rp_plan in razorpay_plans:
            # Check if plan exists by razorpay_plan_id
            result = await db.execute(
                select(SubscriptionPlan).where(
                    SubscriptionPlan.razorpay_plan_id == rp_plan["id"]
                )
            )
            existing = result.scalar_one_or_none()
            
            if existing:
                # Update existing
                existing.price_monthly = int(rp_plan["item"]["amount"])
                existing.name = rp_plan["item"]["name"]
                await db.commit()
                synced.append(f"Updated: {existing.name}")
            else:
                # Create new
                new_plan = SubscriptionPlan(
                    name=rp_plan["item"]["name"],
                    plan_type=PlanType.PRO,  # Default to PRO
                    price_monthly=int(rp_plan["item"]["amount"]),
                    razorpay_plan_id=rp_plan["id"],
                    features={},
                    is_active=True,
                )
                db.add(new_plan)
                await db.commit()
                synced.append(f"Created: {new_plan.name}")
        
        return {"synced": synced}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# ============= USER MANAGEMENT =============

@router.get("/users")
async def list_users(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin),
    skip: int = 0,
    limit: int = 50,
):
    """List all users with subscription info."""
    query = select(User).order_by(User.created_at.desc()).offset(skip).limit(limit)
    result = await db.execute(query)
    users = result.scalars().all()
    
    # Get subscription for each user
    user_data = []
    for user in users:
        sub_result = await db.execute(
            select(Subscription)
            .where(Subscription.user_id == user.id)
            .where(Subscription.status == SubscriptionStatus.ACTIVE)
        )
        subscription = sub_result.scalar_one_or_none()
        
        plan_name = None
        if subscription:
            plan_result = await db.execute(
                select(SubscriptionPlan).where(SubscriptionPlan.id == subscription.plan_id)
            )
            plan = plan_result.scalar_one_or_none()
            plan_name = plan.name if plan else None
        
        user_data.append({
            "id": user.id,
            "email": user.email,
            "name": user.name,
            "is_active": user.is_active,
            "created_at": user.created_at,
            "subscription": plan_name,
        })
    
    return user_data


@router.get("/users/stats")
async def get_user_stats(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    """Get user statistics."""
    total_query = select(func.count(User.id))
    total_result = await db.execute(total_query)
    total_users = total_result.scalar()
    
    active_query = select(func.count(User.id)).where(User.is_active == True)
    active_result = await db.execute(active_query)
    active_users = active_result.scalar()
    
    return {
        "total_users": total_users,
        "active_users": active_users,
    }

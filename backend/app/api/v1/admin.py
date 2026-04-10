"""Admin endpoints — protected by ADMIN_SECRET header."""
import os
from fastapi import APIRouter, Depends, HTTPException, Header
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from app.api.deps import get_db
from app.models.subscription import SubscriptionPlan
from app.services.razorpay_service import get_razorpay_service

router = APIRouter()

ADMIN_SECRET = os.environ.get("ADMIN_SECRET", "")


def require_admin(x_admin_secret: str = Header(...)):
    if not ADMIN_SECRET or x_admin_secret != ADMIN_SECRET:
        raise HTTPException(status_code=403, detail="Forbidden")


@router.post("/seed-razorpay-plans")
async def seed_razorpay_plans(
    db: AsyncSession = Depends(get_db),
    _: None = Depends(require_admin),
):
    """
    Creates Razorpay plans for Pro and Premium tiers and saves the plan IDs to the DB.
    Safe to call multiple times — skips plans that already have a razorpay_plan_id.
    Requires X-Admin-Secret header.
    """
    rz = get_razorpay_service()
    if rz is None:
        raise HTTPException(status_code=500, detail="Razorpay not configured")

    result = await db.execute(select(SubscriptionPlan))
    plans = result.scalars().all()

    seeded = []
    skipped = []

    for plan in plans:
        if plan.price_monthly == 0:
            skipped.append({"name": plan.name, "reason": "free plan — no Razorpay plan needed"})
            continue
        if plan.razorpay_plan_id:
            skipped.append({"name": plan.name, "reason": f"already seeded: {plan.razorpay_plan_id}"})
            continue

        # Create plan in Razorpay
        rz_plan = rz.client.plan.create({
            "period": "monthly",
            "interval": 1,
            "item": {
                "name": f"ApplyTrack {plan.name}",
                "amount": plan.price_monthly,
                "currency": "INR",
                "description": f"ApplyTrack {plan.name} monthly subscription",
            },
            "notes": {"plan_db_id": str(plan.id)},
        })

        await db.execute(
            update(SubscriptionPlan)
            .where(SubscriptionPlan.id == plan.id)
            .values(razorpay_plan_id=rz_plan["id"])
        )
        seeded.append({"name": plan.name, "razorpay_plan_id": rz_plan["id"]})

    await db.commit()
    return {"seeded": seeded, "skipped": skipped}

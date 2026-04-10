import logging
from typing import Dict, Any, Optional
from datetime import datetime, timedelta

from app.models.subscription import SubscriptionPlan, Subscription, SubscriptionStatus, PlanType

logger = logging.getLogger(__name__)

_razorpay_service = None


def get_razorpay_service():
    """Lazy singleton — only initializes when actually called."""
    global _razorpay_service
    if _razorpay_service is None:
        import razorpay
        from app.config import get_settings
        settings = get_settings()
        if not settings.RAZORPAY_KEY_ID or not settings.RAZORPAY_KEY_SECRET:
            logger.warning("Razorpay keys not configured — service will be unavailable")
            return None
        _razorpay_service = RazorpayService(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET)
    return _razorpay_service


class RazorpayService:
    def __init__(self, key_id: str, key_secret: str):
        import razorpay
        self.client = razorpay.Client(auth=(key_id, key_secret))

    def create_customer(self, email: str, name: str, contact: Optional[str] = None) -> Dict[str, Any]:
        data = {"email": email, "name": name}
        if contact:
            data["contact"] = contact
        return self.client.customer.create(data)

    def create_subscription(
        self,
        plan_id: str,
        customer_id: str,
        total_count: Optional[int] = None,
        notes: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        data = {
            "plan_id": plan_id,
            "customer_id": customer_id,
            "total_count": total_count,
            "notes": notes or {},
        }
        data = {k: v for k, v in data.items() if v is not None}
        return self.client.subscription.create(data)

    def fetch_subscription(self, subscription_id: str) -> Dict[str, Any]:
        return self.client.subscription.fetch(subscription_id)

    def cancel_subscription(self, subscription_id: str) -> Dict[str, Any]:
        return self.client.subscription.cancel(subscription_id)

    def fetch_plan(self, plan_id: str) -> Dict[str, Any]:
        return self.client.plan.fetch(plan_id)

    def create_plan(
        self,
        name: str,
        amount: int,
        currency: str = "INR",
        interval: str = "monthly",
        interval_count: int = 1,
        notes: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        data = {
            "period": interval,
            "interval": interval_count,
            "item": {"name": name, "amount": amount, "currency": currency},
            "notes": notes or {},
        }
        return self.client.plan.create(data)


async def initialize_subscription_plans():
    """Seed subscription plans if they don't already exist"""
    from app.database import AsyncSessionLocal
    from sqlalchemy import select

    default_plans = [
        {
            "name": "Free",
            "plan_type": PlanType.FREE,
            "price_monthly": 0,
            "price_yearly": None,
            "description": "Basic free tier",
            "features": {
                "max_applications": 10,
                "email_accounts": 1,
                "ai_matching": False,
            },
        },
        {
            "name": "Pro",
            "plan_type": PlanType.PRO,
            "price_monthly": 49900,
            "price_yearly": 499900,
            "description": "For serious job seekers",
            "features": {
                "max_applications": None,
                "email_accounts": 3,
                "ai_matching": True,
            },
        },
        {
            "name": "Premium",
            "plan_type": PlanType.PREMIUM,
            "price_monthly": 99900,
            "price_yearly": 999900,
            "description": "Full feature access",
            "features": {
                "max_applications": None,
                "email_accounts": 10,
                "ai_matching": True,
                "priority_support": True,
            },
        },
    ]

    async with AsyncSessionLocal() as session:
        for plan_data in default_plans:
            result = await session.execute(
                select(SubscriptionPlan).where(SubscriptionPlan.name == plan_data["name"])
            )
            existing = result.scalar_one_or_none()
            if existing:
                existing.price_monthly = plan_data["price_monthly"]
                existing.price_yearly = plan_data["price_yearly"]
                existing.description = plan_data["description"]
                existing.features = plan_data["features"]
            else:
                plan = SubscriptionPlan(**plan_data)
                session.add(plan)
        await session.commit()

import razorpay
from typing import Dict, Any, Optional
from datetime import datetime, timedelta

from app.config import get_settings
from app.models.subscription import SubscriptionPlan, Subscription, SubscriptionStatus, PlanType

settings = get_settings()


class RazorpayService:
    def __init__(self):
        self.client = razorpay.Client(
            auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET)
        )

    def create_customer(self, email: str, name: str, contact: Optional[str] = None) -> Dict[str, Any]:
        """Create a Razorpay customer"""
        data = {
            "email": email,
            "name": name,
        }
        if contact:
            data["contact"] = contact

        return self.client.customer.create(data)

    def create_subscription(
        self,
        plan_id: str,
        customer_id: str,
        total_count: Optional[int] = None,
        notes: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Create a Razorpay subscription"""
        data = {
            "plan_id": plan_id,
            "customer_id": customer_id,
            "total_count": total_count,
            "notes": notes or {}
        }
        # Remove None values
        data = {k: v for k, v in data.items() if v is not None}

        return self.client.subscription.create(data)

    def fetch_subscription(self, subscription_id: str) -> Dict[str, Any]:
        """Fetch subscription details from Razorpay"""
        return self.client.subscription.fetch(subscription_id)

    def cancel_subscription(self, subscription_id: str) -> Dict[str, Any]:
        """Cancel a Razorpay subscription"""
        return self.client.subscription.cancel(subscription_id)

    def fetch_plan(self, plan_id: str) -> Dict[str, Any]:
        """Fetch plan details from Razorpay"""
        return self.client.plan.fetch(plan_id)

    def create_plan(
        self,
        name: str,
        amount: int,  # amount in paise
        currency: str = "INR",
        interval: str = "monthly",
        interval_count: int = 1,
        notes: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Create a Razorpay plan"""
        data = {
            "period": interval,
            "interval": interval_count,
            "item": {
                "name": name,
                "amount": amount,
                "currency": currency
            },
            "notes": notes or {}
        }
        return self.client.plan.create(data)


# Initialize Razorpay service
razorpay_service = RazorpayService()


async def initialize_subscription_plans():
    """Seed subscription plans if they don't already exist"""
    from app.database import AsyncSessionLocal
    from sqlalchemy import select, text

    default_plans = [
        {
            "name": "Free",
            "plan_type": PlanType.FREE,
            "price_monthly": 0,
            "price_yearly": None,
            "description": "Basic free tier",
            "features": {
                "max_applications": 50,
                "email_accounts": 1,
                "ai_matching": False,
            },
        },
        {
            "name": "Pro",
            "plan_type": PlanType.PRO,
            "price_monthly": 49900,  # ₹499 in paise
            "price_yearly": 499900,  # ₹4999 in paise
            "description": "For serious job seekers",
            "features": {
                "max_applications": None,  # unlimited
                "email_accounts": 3,
                "ai_matching": True,
            },
        },
        {
            "name": "Premium",
            "plan_type": PlanType.PREMIUM,
            "price_monthly": 99900,  # ₹999 in paise
            "price_yearly": 999900,  # ₹9999 in paise
            "description": "Full feature access",
            "features": {
                "max_applications": None,  # unlimited
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
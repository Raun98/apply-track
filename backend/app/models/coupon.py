from datetime import datetime
from typing import Optional

from sqlalchemy import Boolean, DateTime, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class Coupon(Base):
    __tablename__ = "coupons"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    code: Mapped[str] = mapped_column(String(50), unique=True, index=True, nullable=False)
    discount_type: Mapped[str] = mapped_column(String(20), nullable=False)  # "percentage" or "fixed"
    discount_value: Mapped[int] = mapped_column(Integer, nullable=False)  # in paise or percentage
    min_order_amount: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    max_uses: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    current_uses: Mapped[int] = mapped_column(Integer, default=0)
    expires_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

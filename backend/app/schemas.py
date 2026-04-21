from datetime import datetime
from typing import List, Literal, Optional

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator


def _validate_password_strength(value: str) -> str:
    """Require ≥ 8 chars, at least one uppercase letter, and at least one digit.

    The pydantic `pattern` field with lookaheads is not supported by Pydantic's
    Rust regex backend (Python 3.13+), so we validate in Python instead.
    """
    if len(value) < 8:
        raise ValueError("Password must be at least 8 characters")
    if not any(c.isupper() for c in value):
        raise ValueError("Password must contain at least one uppercase letter")
    if not any(c.isdigit() for c in value):
        raise ValueError("Password must contain at least one digit")
    return value


class UserBase(BaseModel):
    email: EmailStr


class UserCreate(UserBase):
    password: str = Field(min_length=8)

    @field_validator("password")
    @classmethod
    def password_strength(cls, v: str) -> str:
        return _validate_password_strength(v)


class UserResponse(UserBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: Optional[str] = None
    is_active: bool
    created_at: datetime
    inbox_address: Optional[str] = None

    @classmethod
    def model_validate(cls, obj, *args, **kwargs):
        instance = super().model_validate(obj, *args, **kwargs)
        if instance.inbox_address is None and hasattr(obj, "id"):
            from app.config import get_settings
            settings = get_settings()
            instance.inbox_address = f"user{obj.id}@{settings.INBOX_DOMAIN}"
        return instance


class UserUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[EmailStr] = None


class ForgotPasswordRequest(BaseModel):
    email: EmailStr


class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str = Field(min_length=8)

    @field_validator("new_password")
    @classmethod
    def password_strength(cls, v: str) -> str:
        return _validate_password_strength(v)


class ApplicationBase(BaseModel):
    company_name: str = Field(max_length=255)
    position_title: str = Field(max_length=255)
    location: Optional[str] = Field(default=None, max_length=255)
    salary_range: Optional[str] = Field(default=None, max_length=100)
    source: str = "manual"
    status: str = "applied"
    notes: Optional[str] = None


class ApplicationCreate(ApplicationBase):
    pass


class ApplicationUpdate(BaseModel):
    company_name: Optional[str] = Field(default=None, max_length=255)
    position_title: Optional[str] = Field(default=None, max_length=255)
    location: Optional[str] = Field(default=None, max_length=255)
    salary_range: Optional[str] = Field(default=None, max_length=100)
    status: Optional[str] = None
    notes: Optional[str] = None


class ApplicationResponse(ApplicationBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    applied_date: datetime
    last_updated: datetime
    email_thread_id: Optional[str] = None
    extra_data: Optional[dict] = None


class ApplicationListResponse(BaseModel):
    items: List[ApplicationResponse]
    total: int
    page: int
    page_size: int


class StatusHistoryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    from_status: Optional[str]
    to_status: str
    changed_at: datetime
    reason: Optional[str]


class ActivityCreate(BaseModel):
    type: Literal["note", "call", "email", "interview", "status_change"] = "note"
    description: str
    extra_data: Optional[dict] = None


class ActivityResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    type: str
    description: str
    extra_data: Optional[dict]
    created_at: datetime


class EmailBase(BaseModel):
    from_address: str
    subject: str
    body_text: Optional[str] = None


class EmailCreate(EmailBase):
    message_id: str
    to_address: str
    received_at: datetime
    body_html: Optional[str] = None
    from_name: Optional[str] = None


class EmailResponse(EmailBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    message_id: str
    received_at: datetime
    processed_status: str
    parsed_data: Optional[dict]
    application_id: Optional[int]


class EmailAccountBase(BaseModel):
    provider: str
    email: EmailStr


class EmailAccountCreate(EmailAccountBase):
    imap_host: Optional[str] = None
    imap_port: Optional[int] = None
    imap_username: Optional[str] = None
    imap_password: Optional[str] = Field(default=None, exclude=True, repr=False)


class EmailAccountResponse(EmailAccountBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    last_sync_at: Optional[datetime]
    is_active: bool
    created_at: datetime


class BoardColumn(BaseModel):
    id: str
    title: str
    order: int


class MoveCardRequest(BaseModel):
    to_column: str
    order: int = 0


class StatusCount(BaseModel):
    status: str
    count: int


class StatsOverview(BaseModel):
    total_applications: int
    by_status: List[StatusCount]
    response_rate: float
    interview_rate: float
    offer_rate: float


class TimelineData(BaseModel):
    date: str
    applied: int
    responses: int
    interviews: int


class SubscriptionPlanResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    plan_type: str
    price_monthly: int
    price_yearly: Optional[int] = None
    razorpay_plan_id: Optional[str] = None
    description: Optional[str] = None
    features: Optional[dict] = None
    is_active: bool


class SubscriptionCreate(BaseModel):
    plan_id: int


class SubscriptionUpdate(BaseModel):
    status: Optional[str] = None


class SubscriptionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    plan_id: int
    razorpay_subscription_id: Optional[str] = None
    razorpay_customer_id: Optional[str] = None
    status: str
    current_period_start: Optional[datetime] = None
    current_period_end: Optional[datetime] = None
    trial_start: Optional[datetime] = None
    trial_end: Optional[datetime] = None
    cancelled_at: Optional[datetime] = None
    created_at: datetime

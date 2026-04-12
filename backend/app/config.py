from functools import lru_cache
from typing import List, Optional

from pydantic import field_validator, model_validator
from pydantic_settings import BaseSettings

_DEFAULT_SECRETS = {
    "SECRET_KEY": "your-secret-key-change-in-production",
    "WEBHOOK_SECRET": "webhook-secret-change-in-production",
}


class Settings(BaseSettings):
    APP_NAME: str = "ApplyTrack"
    DEBUG: bool = False
    API_V1_PREFIX: str = "/api/v1"
    ENVIRONMENT: str = "development"

    DATABASE_URL: str = "postgresql://user:password@localhost:5432/jobtracker"

    REDIS_URL: str = "redis://localhost:6379/0"

    SECRET_KEY: str = "your-secret-key-change-in-production"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    ALGORITHM: str = "HS256"

    ANTHROPIC_API_KEY: str = ""

    OLLAMA_BASE_URL: str = ""
    OLLAMA_MODEL: str = "llama3.2"

    RAZORPAY_KEY_ID: str = ""
    RAZORPAY_KEY_SECRET: str = ""
    RAZORPAY_WEBHOOK_SECRET: str = ""

    IMAP_POLL_INTERVAL_MINUTES: int = 5
    WEBHOOK_SECRET: str = "webhook-secret-change-in-production"
    INBOX_DOMAIN: str = "inbox.applytrack.app"

    ENCRYPTION_KEY: str = ""

    MAILGUN_API_KEY: str = ""
    MAILGUN_DOMAIN: str = ""
    EMAIL_FROM: str = "noreply@applytrack.app"

    ADMIN_SECRET: str = ""

    CORS_ORIGINS: List[str] = ["http://localhost:3000", "http://localhost:5173"]

    FRONTEND_URL: str = "http://localhost:3000"

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def parse_cors_origins(cls, v):
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",") if origin.strip()]
        return v

    @model_validator(mode="after")
    def validate_production_secrets(self) -> "Settings":
        if self.ENVIRONMENT != "development":
            for field, default in _DEFAULT_SECRETS.items():
                value = getattr(self, field)
                if value == default:
                    raise ValueError(
                        f"{field} must be changed from default in production. "
                        f"Generate a secure value and set it via environment variable."
                    )
            if not self.ENCRYPTION_KEY:
                raise ValueError(
                    "ENCRYPTION_KEY is required in production. "
                    "Generate one with: python -c \"from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())\""
                )
        return self

    class Config:
        env_file = ".env"
        case_sensitive = True


@lru_cache()
def get_settings() -> Settings:
    return Settings()

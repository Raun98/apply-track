"""
Shared pytest fixtures.

Database: SQLite (aiosqlite) in-memory — avoids requiring a live Postgres/Redis in CI.
Redis:    fakeredis — stubs the Redis client used by WebSocketManager.publish_sync.
"""
import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession

from app.database import Base, get_db
from app.main import app
from app.config import get_settings

# Disable rate limiting for all tests so the in-memory limiter doesn't
# accumulate hits across test functions and cause spurious 429 responses.
from app.api.v1.auth import limiter as _auth_limiter
_auth_limiter.enabled = False

# ── In-memory SQLite ──────────────────────────────────────────────────────────

TEST_DB_URL = "sqlite+aiosqlite:///:memory:"


@pytest_asyncio.fixture(scope="function")
async def db_engine():
    engine = create_async_engine(TEST_DB_URL, future=True)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


@pytest_asyncio.fixture(scope="function")
async def db_session(db_engine):
    session_factory = async_sessionmaker(db_engine, class_=AsyncSession, expire_on_commit=False)
    async with session_factory() as session:
        yield session


@pytest_asyncio.fixture(scope="function")
async def client(db_session):
    """HTTP test client with the in-memory DB injected."""

    async def _override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = _override_get_db
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac
    app.dependency_overrides.clear()


# ── Seed helpers ──────────────────────────────────────────────────────────────

from app.models.subscription import SubscriptionPlan, PlanType


async def create_free_plan(db: AsyncSession) -> SubscriptionPlan:
    plan = SubscriptionPlan(
        name="Free",
        plan_type=PlanType.FREE,
        price_monthly=0,
        features={"max_applications": 10, "email_accounts": 1},
        is_active=True,
    )
    db.add(plan)
    await db.commit()
    await db.refresh(plan)
    return plan

"""Add subscription_plans, subscriptions tables; extend applicationstatus enum

Revision ID: 002
Revises: 001
Create Date: 2026-04-10 00:00:00.000000
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = '002'
down_revision = '001'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ----------------------------------------------------------------
    # ALTER TYPE ADD VALUE must run outside any transaction block.
    # Create a separate raw connection with AUTOCOMMIT isolation.
    # ----------------------------------------------------------------
    from sqlalchemy import create_engine
    from app.config import get_settings
    settings = get_settings()
    engine = create_engine(settings.DATABASE_URL)
    with engine.connect().execution_options(isolation_level="AUTOCOMMIT") as conn:
        conn.execute(sa.text("ALTER TYPE applicationstatus ADD VALUE IF NOT EXISTS 'UPDATE'"))
    engine.dispose()

    # ----------------------------------------------------------------
    # subscription_plans
    # ----------------------------------------------------------------
    op.create_table(
        'subscription_plans',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=50), nullable=False),
        sa.Column(
            'plan_type',
            sa.Enum('FREE', 'PRO', 'PREMIUM', name='plantype'),
            nullable=False,
        ),
        sa.Column('price_monthly', sa.Integer(), nullable=False),
        sa.Column('price_yearly', sa.Integer(), nullable=True),
        sa.Column('razorpay_plan_id', sa.String(length=100), nullable=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('features', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name'),
        sa.UniqueConstraint('plan_type'),
        sa.UniqueConstraint('razorpay_plan_id'),
    )
    op.create_index(op.f('ix_subscription_plans_id'), 'subscription_plans', ['id'], unique=False)

    # ----------------------------------------------------------------
    # Seed the three default plans
    # ----------------------------------------------------------------
    op.execute(sa.text("""
        INSERT INTO subscription_plans
            (name, plan_type, price_monthly, price_yearly, description, features, is_active, created_at, updated_at)
        VALUES
        (
            'Free',
            'FREE',
            0,
            0,
            'Get started tracking your job applications for free.',
            '{"max_applications": 25, "email_accounts": 1, "ai_parsing": false}'::jsonb,
            true,
            NOW(),
            NOW()
        ),
        (
            'Pro',
            'PRO',
            49900,
            499000,
            'Everything you need for an active job search.',
            '{"max_applications": 500, "email_accounts": 3, "ai_parsing": true, "analytics": true}'::jsonb,
            true,
            NOW(),
            NOW()
        ),
        (
            'Premium',
            'PREMIUM',
            99900,
            999000,
            'Unlimited tracking with advanced AI and analytics.',
            '{"max_applications": -1, "email_accounts": -1, "ai_parsing": true, "analytics": true, "priority_support": true}'::jsonb,
            true,
            NOW(),
            NOW()
        )
    """))

    # ----------------------------------------------------------------
    # subscriptions
    # ----------------------------------------------------------------
    op.create_table(
        'subscriptions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('plan_id', sa.Integer(), nullable=False),
        sa.Column('razorpay_subscription_id', sa.String(length=100), nullable=True),
        sa.Column('razorpay_customer_id', sa.String(length=100), nullable=True),
        sa.Column(
            'status',
            sa.Enum('ACTIVE', 'INACTIVE', 'CANCELLED', 'EXPIRED', 'TRIAL', name='subscriptionstatus'),
            nullable=False,
        ),
        sa.Column('current_period_start', sa.DateTime(), nullable=True),
        sa.Column('current_period_end', sa.DateTime(), nullable=True),
        sa.Column('trial_start', sa.DateTime(), nullable=True),
        sa.Column('trial_end', sa.DateTime(), nullable=True),
        sa.Column('cancelled_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['plan_id'], ['subscription_plans.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('razorpay_subscription_id'),
    )
    op.create_index(op.f('ix_subscriptions_id'), 'subscriptions', ['id'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_subscriptions_id'), table_name='subscriptions')
    op.drop_table('subscriptions')
    op.drop_index(op.f('ix_subscription_plans_id'), table_name='subscription_plans')
    op.drop_table('subscription_plans')
    op.execute(sa.text("DROP TYPE IF EXISTS subscriptionstatus"))
    op.execute(sa.text("DROP TYPE IF EXISTS plantype"))
    # Note: removing an enum value from PostgreSQL requires recreating the type.
    # Downgrade intentionally leaves 'UPDATE' in applicationstatus.

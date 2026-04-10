"""add password reset and email verification columns

Revision ID: 004
Revises: 003
Create Date: 2026-04-10
"""
from alembic import op
import sqlalchemy as sa

revision = '004'
down_revision = '003'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('users', sa.Column('password_reset_token', sa.String(255), nullable=True))
    op.add_column('users', sa.Column('password_reset_expires', sa.DateTime(timezone=True), nullable=True))
    op.add_column('users', sa.Column('email_verified', sa.Boolean(), nullable=False, server_default='false'))
    op.add_column('users', sa.Column('email_verify_token', sa.String(255), nullable=True))


def downgrade():
    op.drop_column('users', 'email_verify_token')
    op.drop_column('users', 'email_verified')
    op.drop_column('users', 'password_reset_expires')
    op.drop_column('users', 'password_reset_token')

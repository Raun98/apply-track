"""add user name column

Revision ID: 003
Revises: 002
Create Date: 2026-04-10

"""
from alembic import op
import sqlalchemy as sa

revision = '003'
down_revision = '002'
branch_labels = None
depends_on = None

def upgrade():
    op.add_column('users', sa.Column('name', sa.String(255), nullable=True))

def downgrade():
    op.drop_column('users', 'name')

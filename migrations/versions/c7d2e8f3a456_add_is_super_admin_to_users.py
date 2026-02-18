"""add_is_super_admin_to_users

Revision ID: c7d2e8f3a456
Revises: 4fd8387cf361
Create Date: 2025-11-03 13:20:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'c7d2e8f3a456'
down_revision = '4fd8387cf361'
branch_labels = None
depends_on = None


def upgrade():
    # Add is_super_admin column to users table
    op.add_column('users', sa.Column('is_super_admin', sa.Boolean(), nullable=True, server_default='false'))


def downgrade():
    # Remove is_super_admin column from users table
    op.drop_column('users', 'is_super_admin')

"""drop person auth fields

Revision ID: q6r7s8t9u012
Revises: p5q6r7s8t901
Create Date: 2025-01-24 00:00:00.000000

Description:
    Remove app_user_id and password_hash columns from persons table.
    These fields are now handled exclusively by the mobile_users table
    for cleaner separation of identity (Person) vs authentication (MobileUser).

IMPORTANT: This migration removes authentication data from persons table.
Ensure all mobile authentication is migrated to mobile_users table before running.

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'q6r7s8t9u012'
down_revision = 'p5q6r7s8t901'
branch_labels = None
depends_on = None


def upgrade():
    """
    Drop redundant authentication fields from persons table.
    MobileUser table now handles all mobile authentication.
    """
    # Drop indexes first
    op.drop_index('ix_persons_app_user_id', table_name='persons')

    # Drop columns
    op.drop_column('persons', 'password_hash')
    op.drop_column('persons', 'app_user_id')


def downgrade():
    """
    Restore authentication fields to persons table.
    WARNING: Data will be lost - these fields will be NULL after downgrade.
    """
    # Add columns back
    op.add_column('persons', sa.Column('app_user_id', sa.String(36), nullable=True))
    op.add_column('persons', sa.Column('password_hash', sa.String(255), nullable=True))

    # Recreate indexes
    op.create_index('ix_persons_app_user_id', 'persons', ['app_user_id'], unique=True)

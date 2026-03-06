"""add billing_enabled to estates and units tables

Revision ID: c7d8e9f0g123
Revises: a6b7c8d9e012
Create Date: 2026-03-06 12:00:00.000000

Adds billing_enabled boolean column to estates and units tables.
Defaults to True so existing data retains current billing behavior.
Estates can toggle billing on/off, cascading to all units.
Units can override independently.
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'c7d8e9f0g123'
down_revision = 'a6b7c8d9e012'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        'estates',
        sa.Column('billing_enabled', sa.Boolean(), nullable=False, server_default=sa.text('true'))
    )
    op.add_column(
        'units',
        sa.Column('billing_enabled', sa.Boolean(), nullable=False, server_default=sa.text('true'))
    )


def downgrade():
    op.drop_column('units', 'billing_enabled')
    op.drop_column('estates', 'billing_enabled')

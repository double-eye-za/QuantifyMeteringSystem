"""add credit_limit to wallets table

Revision ID: x3y4z5a6b789
Revises: w2x3y4z5a678
Create Date: 2026-02-18 12:00:00.000000

Adds nullable credit_limit column to wallets for future arrears management.
No impact on existing data (nullable, no default).
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'x3y4z5a6b789'
down_revision = 'w2x3y4z5a678'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        'wallets',
        sa.Column('credit_limit', sa.Numeric(10, 2), nullable=True)
    )


def downgrade():
    op.drop_column('wallets', 'credit_limit')

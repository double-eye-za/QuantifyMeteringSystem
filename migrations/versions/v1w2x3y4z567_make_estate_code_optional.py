"""make estate code optional

Revision ID: v1w2x3y4z567
Revises: u0v1w2x3y456
Create Date: 2025-12-10 10:45:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'v1w2x3y4z567'
down_revision = 'u0v1w2x3y456'
branch_labels = None
depends_on = None


def upgrade():
    # Drop the unique constraint on code column
    op.drop_constraint('estates_code_key', 'estates', type_='unique')

    # Make code column nullable
    op.alter_column('estates', 'code',
                    existing_type=sa.String(20),
                    nullable=True)

    # Convert existing empty strings to NULL
    op.execute("UPDATE estates SET code = NULL WHERE code = ''")


def downgrade():
    # Convert NULLs back to empty string first (to avoid constraint violation)
    op.execute("UPDATE estates SET code = '' WHERE code IS NULL")

    # Make code column non-nullable again
    op.alter_column('estates', 'code',
                    existing_type=sa.String(20),
                    nullable=False)

    # Re-add unique constraint
    op.create_unique_constraint('estates_code_key', 'estates', ['code'])

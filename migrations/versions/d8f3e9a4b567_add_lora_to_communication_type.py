"""Add lora to communication_type constraint

Revision ID: d8f3e9a4b567
Revises: c7d2e8f3a456
Create Date: 2025-11-06 14:30:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'd8f3e9a4b567'
down_revision = 'c7d2e8f3a456'
branch_labels = None
depends_on = None


def upgrade():
    """
    Add 'lora' to the communication_type CHECK constraint.
    This allows LoRaWAN meters to be registered with communication_type='lora'.
    """
    # Drop the old constraint
    op.drop_constraint('ck_meters_comm_type', 'meters', type_='check')

    # Create new constraint with 'lora' included
    op.create_check_constraint(
        'ck_meters_comm_type',
        'meters',
        "communication_type IN ('plc','cellular','wifi','manual','lora')"
    )


def downgrade():
    """
    Remove 'lora' from communication_type constraint.
    WARNING: This will fail if any meters exist with communication_type='lora'.
    """
    # Drop the new constraint
    op.drop_constraint('ck_meters_comm_type', 'meters', type_='check')

    # Recreate old constraint without 'lora'
    op.create_check_constraint(
        'ck_meters_comm_type',
        'meters',
        "communication_type IN ('plc','cellular','wifi','manual')"
    )

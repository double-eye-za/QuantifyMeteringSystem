"""Add expected_posting_interval to meters table

Revision ID: a6b7c8d9e012
Revises: b2c3d4e5f678
Create Date: 2026-03-05 10:00:00.000000
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'a6b7c8d9e012'
down_revision = 'b2c3d4e5f678'
branch_labels = None
depends_on = None


def upgrade():
    # Add the column
    op.add_column('meters', sa.Column('expected_posting_interval', sa.Integer(), nullable=True))

    # Backfill sensible defaults by device type
    # KPM31: posts every ~30s, 5 min (300s) = ~10 missed posts before alert
    op.execute("UPDATE meters SET expected_posting_interval = 300 WHERE lorawan_device_type = 'kpm31'")

    # Qalcosonic W1: posts every ~1h, 24h (86400s) = generous buffer
    op.execute("UPDATE meters SET expected_posting_interval = 86400 WHERE lorawan_device_type = 'qalcosonic_w1'")

    # Milesight EM300, Eastron SDM, IVY EM114: posts every ~15 min, 2h (7200s)
    op.execute(
        "UPDATE meters SET expected_posting_interval = 7200 "
        "WHERE lorawan_device_type IN ('milesight_em300', 'eastron_sdm', 'ivy_em114')"
    )


def downgrade():
    op.drop_column('meters', 'expected_posting_interval')

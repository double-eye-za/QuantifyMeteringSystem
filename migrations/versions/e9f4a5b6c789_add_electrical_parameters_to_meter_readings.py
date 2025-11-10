"""add_electrical_parameters_to_meter_readings

Revision ID: e9f4a5b6c789
Revises: d0d0934bbfb7
Create Date: 2025-11-10 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'e9f4a5b6c789'
down_revision = 'd0d0934bbfb7'
branch_labels = None
depends_on = None


def upgrade():
    # Add electrical parameters to meter_readings table
    op.add_column('meter_readings', sa.Column('voltage', sa.Numeric(precision=6, scale=2), nullable=True))
    op.add_column('meter_readings', sa.Column('current', sa.Numeric(precision=8, scale=3), nullable=True))
    op.add_column('meter_readings', sa.Column('power', sa.Numeric(precision=10, scale=3), nullable=True))
    op.add_column('meter_readings', sa.Column('power_factor', sa.Numeric(precision=4, scale=3), nullable=True))
    op.add_column('meter_readings', sa.Column('frequency', sa.Numeric(precision=5, scale=2), nullable=True))

    # Add water meter parameters to meter_readings table
    op.add_column('meter_readings', sa.Column('flow_rate', sa.Numeric(precision=10, scale=3), nullable=True))
    op.add_column('meter_readings', sa.Column('pressure', sa.Numeric(precision=6, scale=2), nullable=True))

    # Add status field
    op.add_column('meter_readings', sa.Column('status', sa.String(length=50), nullable=True))


def downgrade():
    # Remove all new fields from meter_readings
    op.drop_column('meter_readings', 'status')
    op.drop_column('meter_readings', 'pressure')
    op.drop_column('meter_readings', 'flow_rate')
    op.drop_column('meter_readings', 'frequency')
    op.drop_column('meter_readings', 'power_factor')
    op.drop_column('meter_readings', 'power')
    op.drop_column('meter_readings', 'current')
    op.drop_column('meter_readings', 'voltage')

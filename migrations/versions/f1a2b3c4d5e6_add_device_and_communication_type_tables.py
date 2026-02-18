"""add device and communication type tables

Revision ID: f1a2b3c4d5e6
Revises: e9f4a5b6c789
Create Date: 2025-11-11 09:31:43.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'f1a2b3c4d5e6'
down_revision = 'e9f4a5b6c789'
branch_labels = None
depends_on = None


def upgrade():
    # Create device_types table
    op.create_table('device_types',
    sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('code', sa.String(length=50), nullable=False),
    sa.Column('name', sa.String(length=100), nullable=False),
    sa.Column('description', sa.Text(), nullable=True),
    sa.Column('manufacturer', sa.String(length=100), nullable=True),
    sa.Column('default_model', sa.String(length=100), nullable=True),
    sa.Column('supports_temperature', sa.Boolean(), nullable=True),
    sa.Column('supports_pulse', sa.Boolean(), nullable=True),
    sa.Column('supports_modbus', sa.Boolean(), nullable=True),
    sa.Column('is_active', sa.Boolean(), nullable=True),
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.Column('updated_at', sa.DateTime(), nullable=False),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('code')
    )
    op.create_index(op.f('ix_device_types_code'), 'device_types', ['code'], unique=False)

    # Create communication_types table
    op.create_table('communication_types',
    sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('code', sa.String(length=20), nullable=False),
    sa.Column('name', sa.String(length=100), nullable=False),
    sa.Column('description', sa.Text(), nullable=True),
    sa.Column('requires_device_eui', sa.Boolean(), nullable=True),
    sa.Column('requires_gateway', sa.Boolean(), nullable=True),
    sa.Column('supports_remote_control', sa.Boolean(), nullable=True),
    sa.Column('is_active', sa.Boolean(), nullable=True),
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.Column('updated_at', sa.DateTime(), nullable=False),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('code')
    )
    op.create_index(op.f('ix_communication_types_code'), 'communication_types', ['code'], unique=False)


def downgrade():
    op.drop_index(op.f('ix_communication_types_code'), table_name='communication_types')
    op.drop_table('communication_types')
    op.drop_index(op.f('ix_device_types_code'), table_name='device_types')
    op.drop_table('device_types')

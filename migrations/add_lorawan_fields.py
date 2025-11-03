"""
Database Migration: Add LoRaWAN Integration Fields
Add fields to meters and meter_readings tables
Create device_commands table for command queue
"""

from alembic import op
import sqlalchemy as sa

# Revision identifiers
revision = 'add_lorawan_fields'
down_revision = None  # Update this to your last migration revision
branch_labels = None
depends_on = None


def upgrade():
    """Add LoRaWAN integration fields"""

    # Add fields to meters table
    op.add_column('meters', sa.Column('device_eui', sa.String(length=16), nullable=True))
    op.add_column('meters', sa.Column('lorawan_device_type', sa.String(length=50), nullable=True))

    # Create indexes on meters table
    op.create_index(op.f('ix_meters_device_eui'), 'meters', ['device_eui'], unique=True)

    # Add fields to meter_readings table
    op.add_column('meter_readings', sa.Column('pulse_count', sa.Integer(), nullable=True))
    op.add_column('meter_readings', sa.Column('temperature', sa.Numeric(precision=5, scale=2), nullable=True))
    op.add_column('meter_readings', sa.Column('humidity', sa.Numeric(precision=5, scale=2), nullable=True))
    op.add_column('meter_readings', sa.Column('rssi', sa.Integer(), nullable=True))
    op.add_column('meter_readings', sa.Column('snr', sa.Numeric(precision=5, scale=2), nullable=True))
    op.add_column('meter_readings', sa.Column('battery_level', sa.Integer(), nullable=True))
    op.add_column('meter_readings', sa.Column('raw_payload', sa.Text(), nullable=True))

    # Create device_commands table
    op.create_table('device_commands',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('meter_id', sa.Integer(), nullable=False),
        sa.Column('device_eui', sa.String(length=16), nullable=False),
        sa.Column('command_type', sa.String(length=50), nullable=False),
        sa.Column('command_data', sa.Text(), nullable=True),
        sa.Column('status', sa.String(length=20), nullable=False),
        sa.Column('priority', sa.Integer(), nullable=False),
        sa.Column('scheduled_at', sa.DateTime(), nullable=True),
        sa.Column('sent_at', sa.DateTime(), nullable=True),
        sa.Column('completed_at', sa.DateTime(), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('retry_count', sa.Integer(), nullable=False),
        sa.Column('max_retries', sa.Integer(), nullable=False),
        sa.Column('created_by', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.CheckConstraint(
            "command_type IN ('switch_on','switch_off','update_credit','read_meter','reset_meter','update_config')",
            name='ck_device_commands_type'
        ),
        sa.CheckConstraint(
            "status IN ('pending','queued','sent','completed','failed','cancelled')",
            name='ck_device_commands_status'
        ),
        sa.CheckConstraint(
            'priority >= 1 AND priority <= 10',
            name='ck_device_commands_priority'
        ),
        sa.ForeignKeyConstraint(['meter_id'], ['meters.id'], ),
        sa.ForeignKeyConstraint(['created_by'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )

    # Create indexes on device_commands table
    op.create_index(op.f('ix_device_commands_meter_id'), 'device_commands', ['meter_id'], unique=False)
    op.create_index(op.f('ix_device_commands_device_eui'), 'device_commands', ['device_eui'], unique=False)
    op.create_index(op.f('ix_device_commands_status'), 'device_commands', ['status'], unique=False)

    print("✅ Migration complete: LoRaWAN integration fields added")


def downgrade():
    """Remove LoRaWAN integration fields"""

    # Drop device_commands table
    op.drop_index(op.f('ix_device_commands_status'), table_name='device_commands')
    op.drop_index(op.f('ix_device_commands_device_eui'), table_name='device_commands')
    op.drop_index(op.f('ix_device_commands_meter_id'), table_name='device_commands')
    op.drop_table('device_commands')

    # Remove fields from meter_readings
    op.drop_column('meter_readings', 'raw_payload')
    op.drop_column('meter_readings', 'battery_level')
    op.drop_column('meter_readings', 'snr')
    op.drop_column('meter_readings', 'rssi')
    op.drop_column('meter_readings', 'humidity')
    op.drop_column('meter_readings', 'temperature')
    op.drop_column('meter_readings', 'pulse_count')

    # Remove fields from meters
    op.drop_index(op.f('ix_meters_device_eui'), table_name='meters')
    op.drop_column('meters', 'lorawan_device_type')
    op.drop_column('meters', 'device_eui')

    print("✅ Migration rolled back: LoRaWAN fields removed")

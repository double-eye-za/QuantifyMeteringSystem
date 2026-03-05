"""create kpm31_telemetry table

Revision ID: b2c3d4e5f678
Revises: z5a6b7c8d901
Create Date: 2026-03-05 12:00:00.000000

Creates the kpm31_telemetry table for storing full raw data from Compere KPM31
4G electricity meters. Supports both single-phase and three-phase variants with
~50 columns covering per-phase voltages, currents, power, sequence components,
demand values, and unbalance rates. Links to meters and meter_readings tables.
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'b2c3d4e5f678'
down_revision = 'z5a6b7c8d901'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'kpm31_telemetry',

        # Primary key and relationships
        sa.Column('id', sa.Integer, primary_key=True, autoincrement=True, nullable=False),
        sa.Column('meter_id', sa.Integer, sa.ForeignKey('meters.id'), nullable=False),
        sa.Column('reading_id', sa.Integer, sa.ForeignKey('meter_readings.id'), nullable=True),

        # Timestamps
        sa.Column('recorded_at', sa.DateTime, nullable=False, server_default=sa.func.now()),
        sa.Column('device_timestamp', sa.String(14), nullable=True),

        # Phase type discriminator
        sa.Column('phase_type', sa.String(10), nullable=False),

        # ─── Single-phase only fields ───
        sa.Column('voltage', sa.Numeric(6, 2), nullable=True),              # u
        sa.Column('current', sa.Numeric(8, 3), nullable=True),              # i
        sa.Column('prepaid_balance_kwh', sa.Numeric(12, 3), nullable=True), # sydn
        sa.Column('current_demand', sa.Numeric(8, 3), nullable=True),       # idm

        # ─── Three-phase per-phase voltages ───
        sa.Column('voltage_a', sa.Numeric(6, 2), nullable=True),    # ua
        sa.Column('voltage_b', sa.Numeric(6, 2), nullable=True),    # ub
        sa.Column('voltage_c', sa.Numeric(6, 2), nullable=True),    # uc
        sa.Column('voltage_ab', sa.Numeric(6, 2), nullable=True),   # uab
        sa.Column('voltage_bc', sa.Numeric(6, 2), nullable=True),   # ubc
        sa.Column('voltage_ca', sa.Numeric(6, 2), nullable=True),   # uca

        # ─── Three-phase per-phase currents ───
        sa.Column('current_a', sa.Numeric(8, 3), nullable=True),    # ia
        sa.Column('current_b', sa.Numeric(8, 3), nullable=True),    # ib
        sa.Column('current_c', sa.Numeric(8, 3), nullable=True),    # ic

        # ─── Three-phase per-phase power ───
        sa.Column('active_power_a', sa.Numeric(10, 3), nullable=True),   # pa (kW)
        sa.Column('active_power_b', sa.Numeric(10, 3), nullable=True),   # pb
        sa.Column('active_power_c', sa.Numeric(10, 3), nullable=True),   # pc
        sa.Column('apparent_power_a', sa.Numeric(10, 3), nullable=True), # sa (kVA)
        sa.Column('apparent_power_b', sa.Numeric(10, 3), nullable=True), # sb
        sa.Column('apparent_power_c', sa.Numeric(10, 3), nullable=True), # sc
        sa.Column('power_factor_a', sa.Numeric(4, 3), nullable=True),    # pfa
        sa.Column('power_factor_b', sa.Numeric(4, 3), nullable=True),    # pfb
        sa.Column('power_factor_c', sa.Numeric(4, 3), nullable=True),    # pfc

        # ─── System totals (both variants) ───
        sa.Column('total_active_power', sa.Numeric(10, 3), nullable=True),    # zyggl (kW)
        sa.Column('total_reactive_power', sa.Numeric(10, 3), nullable=True),  # zwggl (kvar)
        sa.Column('total_apparent_power', sa.Numeric(10, 3), nullable=True),  # zszgl (kVA)
        sa.Column('total_power_factor', sa.Numeric(4, 3), nullable=True),     # zglys
        sa.Column('frequency', sa.Numeric(5, 2), nullable=True),              # f (Hz)

        # ─── Demand values (both variants) ───
        sa.Column('active_demand', sa.Numeric(10, 3), nullable=True),    # pdm (kW)
        sa.Column('reactive_demand', sa.Numeric(10, 3), nullable=True),  # qdm (kvar)
        sa.Column('apparent_demand', sa.Numeric(10, 3), nullable=True),  # sdm (kVA)

        # ─── Sequence components (three-phase only) ───
        sa.Column('voltage_zero_seq', sa.Numeric(6, 2), nullable=True),  # u0
        sa.Column('voltage_pos_seq', sa.Numeric(6, 2), nullable=True),   # u+
        sa.Column('voltage_neg_seq', sa.Numeric(6, 2), nullable=True),   # u-
        sa.Column('current_zero_seq', sa.Numeric(8, 3), nullable=True),  # i0
        sa.Column('current_pos_seq', sa.Numeric(8, 3), nullable=True),   # i+
        sa.Column('current_neg_seq', sa.Numeric(8, 3), nullable=True),   # i-

        # ─── Fundamental/measured values (three-phase only) ───
        sa.Column('voltage_fund_a', sa.Numeric(6, 2), nullable=True),  # uxja
        sa.Column('voltage_fund_b', sa.Numeric(6, 2), nullable=True),  # uxjb
        sa.Column('voltage_fund_c', sa.Numeric(6, 2), nullable=True),  # uxjc
        sa.Column('current_fund_a', sa.Numeric(8, 3), nullable=True),  # ixja
        sa.Column('current_fund_b', sa.Numeric(8, 3), nullable=True),  # ixjb
        sa.Column('current_fund_c', sa.Numeric(8, 3), nullable=True),  # ixjc

        # ─── Unbalance rates (three-phase only) ───
        sa.Column('voltage_unbalance', sa.Numeric(5, 2), nullable=True),  # unb (%)
        sa.Column('current_unbalance', sa.Numeric(5, 2), nullable=True),  # inb (%)

        # ─── Raw payload & metadata ───
        sa.Column('raw_payload', sa.Text, nullable=True),
        sa.Column('isend', sa.String(5), nullable=True),

        # Constraints
        sa.CheckConstraint(
            "phase_type IN ('single','three')",
            name='ck_kpm31_telemetry_phase_type'
        ),
    )

    # Indexes
    op.create_index('ix_kpm31_telemetry_meter_id', 'kpm31_telemetry', ['meter_id'])
    op.create_index('ix_kpm31_telemetry_recorded_at', 'kpm31_telemetry', ['recorded_at'])
    op.create_index(
        'ix_kpm31_telemetry_meter_recorded',
        'kpm31_telemetry',
        ['meter_id', sa.text('recorded_at DESC')]
    )


def downgrade():
    op.drop_index('ix_kpm31_telemetry_meter_recorded', 'kpm31_telemetry')
    op.drop_index('ix_kpm31_telemetry_recorded_at', 'kpm31_telemetry')
    op.drop_index('ix_kpm31_telemetry_meter_id', 'kpm31_telemetry')
    op.drop_table('kpm31_telemetry')

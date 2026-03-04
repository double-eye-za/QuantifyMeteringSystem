"""add hot water rate table support

Revision ID: z5a6b7c8d901
Revises: y4z5a6b7c890
Create Date: 2026-03-02 18:00:00.000000

Adds hot_water as a valid utility_type for rate_tables, and adds
hot_water_rate_table_id + hot_water_markup_percentage columns to
estates and units for dedicated hot water rate assignment.

All new columns are NULLABLE — existing rows are unaffected.
Hot water meters without a dedicated rate table continue using
water_rate_table_id (unchanged behaviour).
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'z5a6b7c8d901'
down_revision = 'y4z5a6b7c890'
branch_labels = None
depends_on = None


def upgrade():
    conn = op.get_bind()
    inspector = sa.inspect(conn)

    # 1a. Update rate_tables utility_type CHECK constraint to include 'hot_water'
    op.drop_constraint('ck_rate_tables_utility_type', 'rate_tables', type_='check')
    op.create_check_constraint(
        'ck_rate_tables_utility_type',
        'rate_tables',
        "utility_type IN ('electricity','water','solar','hot_water')",
    )

    # 1b. Add hot_water_rate_table_id and hot_water_markup_percentage to estates
    estate_columns = [col['name'] for col in inspector.get_columns('estates')]

    if 'hot_water_rate_table_id' not in estate_columns:
        op.add_column('estates', sa.Column('hot_water_rate_table_id', sa.Integer(), nullable=True))
        op.create_foreign_key(
            'fk_estates_hot_water_rate_table', 'estates', 'rate_tables',
            ['hot_water_rate_table_id'], ['id'], ondelete='SET NULL',
        )

    if 'hot_water_markup_percentage' not in estate_columns:
        op.add_column('estates', sa.Column(
            'hot_water_markup_percentage', sa.Numeric(5, 2),
            nullable=True, server_default='0.00',
        ))

    # 1c. Add hot_water_rate_table_id to units
    unit_columns = [col['name'] for col in inspector.get_columns('units')]

    if 'hot_water_rate_table_id' not in unit_columns:
        op.add_column('units', sa.Column('hot_water_rate_table_id', sa.Integer(), nullable=True))
        op.create_foreign_key(
            'fk_units_hot_water_rate_table', 'units', 'rate_tables',
            ['hot_water_rate_table_id'], ['id'], ondelete='SET NULL',
        )


def downgrade():
    # Remove unit column
    op.drop_constraint('fk_units_hot_water_rate_table', 'units', type_='foreignkey')
    op.drop_column('units', 'hot_water_rate_table_id')

    # Remove estate columns
    op.drop_column('estates', 'hot_water_markup_percentage')
    op.drop_constraint('fk_estates_hot_water_rate_table', 'estates', type_='foreignkey')
    op.drop_column('estates', 'hot_water_rate_table_id')

    # Revert CHECK constraint
    op.drop_constraint('ck_rate_tables_utility_type', 'rate_tables', type_='check')
    op.create_check_constraint(
        'ck_rate_tables_utility_type',
        'rate_tables',
        "utility_type IN ('electricity','water','solar')",
    )

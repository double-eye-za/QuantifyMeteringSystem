"""add rate table ids to units

Revision ID: i4j5k6l7m890
Revises: h3i4j5k6l789
Create Date: 2025-11-18 10:05:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'i4j5k6l7m890'
down_revision = 'h3i4j5k6l789'
branch_labels = None
depends_on = None


def upgrade():
    # Check if columns already exist
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    columns = [col['name'] for col in inspector.get_columns('units')]

    if 'electricity_rate_table_id' not in columns:
        op.add_column('units', sa.Column('electricity_rate_table_id', sa.Integer(), nullable=True))
        op.create_foreign_key('fk_units_electricity_rate_table', 'units', 'rate_tables',
                             ['electricity_rate_table_id'], ['id'], ondelete='SET NULL')

    if 'water_rate_table_id' not in columns:
        op.add_column('units', sa.Column('water_rate_table_id', sa.Integer(), nullable=True))
        op.create_foreign_key('fk_units_water_rate_table', 'units', 'rate_tables',
                             ['water_rate_table_id'], ['id'], ondelete='SET NULL')


def downgrade():
    op.drop_constraint('fk_units_water_rate_table', 'units', type_='foreignkey')
    op.drop_column('units', 'water_rate_table_id')
    op.drop_constraint('fk_units_electricity_rate_table', 'units', type_='foreignkey')
    op.drop_column('units', 'electricity_rate_table_id')

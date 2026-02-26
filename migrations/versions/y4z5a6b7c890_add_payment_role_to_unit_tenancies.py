"""add payment_role and delegated_payer_id to unit_tenancies

Revision ID: y4z5a6b7c890
Revises: x3y4z5a6b789
Create Date: 2026-02-24 14:00:00.000000

Adds payment_role ('delegated_payer' or 'sponsored') and delegated_payer_id
FK to unit_tenancies for wallet top-up permission control.

Existing rows get NULL payment_role which is treated as 'delegated_payer'
in application code — zero impact on existing tenants.
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'y4z5a6b7c890'
down_revision = 'x3y4z5a6b789'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        'unit_tenancies',
        sa.Column('payment_role', sa.String(20), nullable=True,
                  server_default='delegated_payer')
    )
    op.add_column(
        'unit_tenancies',
        sa.Column('delegated_payer_id', sa.Integer(),
                  sa.ForeignKey('persons.id', ondelete='SET NULL'),
                  nullable=True)
    )
    op.create_index(
        'ix_unit_tenancies_delegated_payer_id',
        'unit_tenancies',
        ['delegated_payer_id']
    )
    op.create_check_constraint(
        'ck_tenancy_payment_role',
        'unit_tenancies',
        "payment_role IN ('delegated_payer', 'sponsored')"
    )


def downgrade():
    op.drop_constraint('ck_tenancy_payment_role', 'unit_tenancies', type_='check')
    op.drop_index('ix_unit_tenancies_delegated_payer_id', table_name='unit_tenancies')
    op.drop_column('unit_tenancies', 'delegated_payer_id')
    op.drop_column('unit_tenancies', 'payment_role')

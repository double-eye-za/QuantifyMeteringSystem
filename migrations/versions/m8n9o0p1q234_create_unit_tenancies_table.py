"""create unit tenancies table

Revision ID: m8n9o0p1q234
Revises: l7m8n9o0p123
Create Date: 2025-11-19 10:10:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'm8n9o0p1q234'
down_revision = 'l7m8n9o0p123'
branch_labels = None
depends_on = None


def upgrade():
    """
    Create the unit_tenancies table - tracks rental/tenancy relationships between persons and units.
    Includes lease information and billing responsibility.
    """
    op.create_table(
        'unit_tenancies',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('unit_id', sa.Integer(), nullable=False),
        sa.Column('person_id', sa.Integer(), nullable=False),
        sa.Column('lease_start_date', sa.Date(), nullable=True),
        sa.Column('lease_end_date', sa.Date(), nullable=True),
        sa.Column('monthly_rent', sa.Numeric(precision=10, scale=2), nullable=True),
        sa.Column('deposit_amount', sa.Numeric(precision=10, scale=2), nullable=True),
        sa.Column('is_primary_tenant', sa.Boolean(), nullable=True, server_default='false'),
        sa.Column('status', sa.String(length=20), nullable=True, server_default='active'),
        sa.Column('move_in_date', sa.Date(), nullable=True),
        sa.Column('move_out_date', sa.Date(), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=True, onupdate=sa.func.now()),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('unit_id', 'person_id', name='uq_unit_tenancy'),
        sa.ForeignKeyConstraint(['unit_id'], ['units.id'], name='fk_unit_tenancy_unit', ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['person_id'], ['persons.id'], name='fk_unit_tenancy_person', ondelete='CASCADE'),
        sa.CheckConstraint(
            "status IN ('active','expired','terminated')",
            name='ck_tenancy_status'
        ),
    )

    # Create indexes for performance
    op.create_index('ix_unit_tenancies_unit_id', 'unit_tenancies', ['unit_id'])
    op.create_index('ix_unit_tenancies_person_id', 'unit_tenancies', ['person_id'])
    op.create_index('ix_unit_tenancies_status', 'unit_tenancies', ['status'])
    op.create_index('ix_unit_tenancies_is_primary', 'unit_tenancies', ['is_primary_tenant'])
    op.create_index('ix_unit_tenancies_move_out_date', 'unit_tenancies', ['move_out_date'])


def downgrade():
    """Remove unit_tenancies table and indexes"""
    op.drop_index('ix_unit_tenancies_move_out_date', 'unit_tenancies')
    op.drop_index('ix_unit_tenancies_is_primary', 'unit_tenancies')
    op.drop_index('ix_unit_tenancies_status', 'unit_tenancies')
    op.drop_index('ix_unit_tenancies_person_id', 'unit_tenancies')
    op.drop_index('ix_unit_tenancies_unit_id', 'unit_tenancies')
    op.drop_table('unit_tenancies')

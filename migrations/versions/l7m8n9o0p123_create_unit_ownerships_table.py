"""create unit ownerships table

Revision ID: l7m8n9o0p123
Revises: k6l7m8n9o012
Create Date: 2025-11-19 10:05:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'l7m8n9o0p123'
down_revision = 'k6l7m8n9o012'
branch_labels = None
depends_on = None


def upgrade():
    """
    Create the unit_ownerships table - tracks ownership relationships between persons and units.
    Supports joint ownership with ownership percentages.
    """
    op.create_table(
        'unit_ownerships',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('unit_id', sa.Integer(), nullable=False),
        sa.Column('person_id', sa.Integer(), nullable=False),
        sa.Column('ownership_percentage', sa.Numeric(precision=5, scale=2), nullable=False, server_default='100.00'),
        sa.Column('purchase_date', sa.Date(), nullable=True),
        sa.Column('purchase_price', sa.Numeric(precision=15, scale=2), nullable=True),
        sa.Column('is_primary_owner', sa.Boolean(), nullable=True, server_default='false'),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=True, onupdate=sa.func.now()),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('unit_id', 'person_id', name='uq_unit_ownership'),
        sa.ForeignKeyConstraint(['unit_id'], ['units.id'], name='fk_unit_ownership_unit', ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['person_id'], ['persons.id'], name='fk_unit_ownership_person', ondelete='CASCADE'),
        sa.CheckConstraint(
            'ownership_percentage >= 0 AND ownership_percentage <= 100',
            name='ck_ownership_percentage'
        ),
    )

    # Create indexes for performance
    op.create_index('ix_unit_ownerships_unit_id', 'unit_ownerships', ['unit_id'])
    op.create_index('ix_unit_ownerships_person_id', 'unit_ownerships', ['person_id'])
    op.create_index('ix_unit_ownerships_is_primary', 'unit_ownerships', ['is_primary_owner'])


def downgrade():
    """Remove unit_ownerships table and indexes"""
    op.drop_index('ix_unit_ownerships_is_primary', 'unit_ownerships')
    op.drop_index('ix_unit_ownerships_person_id', 'unit_ownerships')
    op.drop_index('ix_unit_ownerships_unit_id', 'unit_ownerships')
    op.drop_table('unit_ownerships')

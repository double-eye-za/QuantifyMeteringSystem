"""drop residents table

Revision ID: r7s8t9u0v123
Revises: q6r7s8t9u012
Create Date: 2025-01-24 00:00:01.000000

Description:
    Drop the residents table as it has been fully replaced by the Person model
    combined with UnitOwnership and UnitTenancy relationship tables.

    The Resident model was deprecated in favor of:
    - Person: Core identity for owners and tenants
    - UnitOwnership: Tracks ownership relationships (with percentages)
    - UnitTenancy: Tracks rental/lease relationships (with lease dates)

IMPORTANT: This migration is irreversible in practice. While a downgrade path
is provided, it will recreate an empty residents table. All resident data should
already have been migrated to the persons table via previous migrations.

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'r7s8t9u0v123'
down_revision = 'q6r7s8t9u012'
branch_labels = None
depends_on = None


def upgrade():
    """
    Drop the residents table completely.
    All data should have been migrated to persons, unit_ownerships, and unit_tenancies.
    """
    # Drop the residents table
    op.drop_table('residents')


def downgrade():
    """
    Recreate the residents table structure (for rollback).
    WARNING: This will create an EMPTY table - all data will be lost.
    """
    op.create_table(
        'residents',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('id_number', sa.String(20), nullable=True),
        sa.Column('first_name', sa.String(100), nullable=False),
        sa.Column('last_name', sa.String(100), nullable=False),
        sa.Column('email', sa.String(255), nullable=False),
        sa.Column('phone', sa.String(20), nullable=False),
        sa.Column('alternate_phone', sa.String(20), nullable=True),
        sa.Column('emergency_contact_name', sa.String(200), nullable=True),
        sa.Column('emergency_contact_phone', sa.String(20), nullable=True),
        sa.Column('lease_start_date', sa.Date(), nullable=True),
        sa.Column('lease_end_date', sa.Date(), nullable=True),
        sa.Column('status', sa.String(20), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=True),
        sa.Column('app_user_id', sa.String(36), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.Column('created_by', sa.Integer(), nullable=True),
        sa.Column('updated_by', sa.Integer(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['created_by'], ['users.id']),
        sa.ForeignKeyConstraint(['updated_by'], ['users.id']),
    )

    # Recreate indexes
    op.create_index('ix_residents_email', 'residents', ['email'], unique=True)
    op.create_index('ix_residents_id_number', 'residents', ['id_number'], unique=True)
    op.create_index('ix_residents_is_active', 'residents', ['is_active'], unique=False)

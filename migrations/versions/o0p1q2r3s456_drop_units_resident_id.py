"""drop units resident_id

Revision ID: o0p1q2r3s456
Revises: n9o0p1q2r345
Create Date: 2025-11-19 10:20:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'o0p1q2r3s456'
down_revision = 'n9o0p1q2r345'
branch_labels = None
depends_on = None


def upgrade():
    """
    Remove the old resident_id column from units table.

    This migration:
    1. Drops the foreign key constraint units_resident_id_fkey
    2. Drops the resident_id column from units table

    Prerequisites: Migration 4 must have already copied all resident data to persons
    and created corresponding unit_tenancies records.
    """

    # Drop the foreign key constraint first
    op.drop_constraint('units_resident_id_fkey', 'units', type_='foreignkey')

    # Drop the resident_id column
    op.drop_column('units', 'resident_id')

    print("Successfully removed units.resident_id column and constraint")


def downgrade():
    """
    Restore the units.resident_id column and foreign key constraint.

    WARNING: This will restore the column but it will be empty!
    Data recovery requires manual SQL to copy primary tenant from unit_tenancies
    back to units.resident_id
    """

    # Re-add the resident_id column
    op.add_column('units', sa.Column('resident_id', sa.Integer(), nullable=True))

    # Re-create the foreign key constraint
    op.create_foreign_key(
        'units_resident_id_fkey',
        'units',
        'residents',
        ['resident_id'],
        ['id'],
        ondelete='SET NULL'
    )

    print("Restored units.resident_id column (data is empty - requires manual recovery)")

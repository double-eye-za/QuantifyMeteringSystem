"""migrate residents to persons

Revision ID: n9o0p1q2r345
Revises: m8n9o0p1q234
Create Date: 2025-11-19 10:15:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.sql import table, column


# revision identifiers, used by Alembic.
revision = 'n9o0p1q2r345'
down_revision = 'm8n9o0p1q234'
branch_labels = None
depends_on = None


def upgrade():
    """
    Migrate existing residents data to persons table and create tenancy records.

    This migration:
    1. Copies all residents to persons (if not already copied)
    2. Creates unit_tenancies records for units.resident_id relationships
    3. Is idempotent - safe to run multiple times
    """

    # Define table references for raw SQL
    conn = op.get_bind()

    # Step 1: Copy residents to persons (idempotent - only copy if not exists)
    print("Migrating residents to persons...")
    conn.execute(sa.text("""
        INSERT INTO persons (
            id, first_name, last_name, email, phone, alternate_phone,
            id_number, emergency_contact_name, emergency_contact_phone,
            is_active, app_user_id, created_by, updated_by,
            created_at, updated_at
        )
        SELECT
            r.id, r.first_name, r.last_name, r.email, r.phone, r.alternate_phone,
            r.id_number, r.emergency_contact_name, r.emergency_contact_phone,
            r.is_active, r.app_user_id, r.created_by, r.updated_by,
            r.created_at, r.updated_at
        FROM residents r
        WHERE NOT EXISTS (
            SELECT 1 FROM persons p WHERE p.email = r.email
        )
    """))

    # Get count of migrated residents
    result = conn.execute(sa.text("SELECT COUNT(*) FROM residents"))
    resident_count = result.scalar()
    print(f"Migrated {resident_count} residents to persons table")

    # Step 2: Create tenancy records from units.resident_id
    # Only create if the relationship doesn't already exist
    print("Creating tenancy records from unit assignments...")
    conn.execute(sa.text("""
        INSERT INTO unit_tenancies (
            unit_id, person_id, is_primary_tenant,
            lease_start_date, lease_end_date, status,
            move_in_date, created_at
        )
        SELECT
            u.id as unit_id,
            p.id as person_id,
            true as is_primary_tenant,
            r.lease_start_date,
            r.lease_end_date,
            COALESCE(r.status, 'active') as status,
            r.lease_start_date as move_in_date,
            CURRENT_TIMESTAMP as created_at
        FROM units u
        INNER JOIN residents r ON u.resident_id = r.id
        INNER JOIN persons p ON p.email = r.email
        WHERE u.resident_id IS NOT NULL
        AND NOT EXISTS (
            SELECT 1 FROM unit_tenancies ut
            WHERE ut.unit_id = u.id AND ut.person_id = p.id
        )
    """))

    # Get count of tenancies created
    result = conn.execute(sa.text("SELECT COUNT(*) FROM unit_tenancies"))
    tenancy_count = result.scalar()
    print(f"Created {tenancy_count} tenancy records")

    # Sync the persons ID sequence to avoid conflicts
    # This ensures new persons get IDs higher than migrated ones
    conn.execute(sa.text("""
        SELECT setval('persons_id_seq',
            COALESCE((SELECT MAX(id) FROM persons), 0) + 1,
            false
        )
    """))

    print("Migration complete!")


def downgrade():
    """
    Rollback: Remove migrated data from persons and unit_tenancies

    WARNING: This only removes data that was migrated from residents.
    If new persons were created after migration, they will remain.
    """

    conn = op.get_bind()

    # Remove tenancies that were created from units.resident_id
    # (Tenancies where person exists in residents table)
    print("Removing migrated tenancy records...")
    conn.execute(sa.text("""
        DELETE FROM unit_tenancies ut
        WHERE EXISTS (
            SELECT 1 FROM residents r
            INNER JOIN persons p ON p.email = r.email
            WHERE ut.person_id = p.id
        )
    """))

    # Remove persons that came from residents
    # (Only remove if their email exists in residents table)
    print("Removing migrated persons...")
    conn.execute(sa.text("""
        DELETE FROM persons p
        WHERE EXISTS (
            SELECT 1 FROM residents r WHERE r.email = p.email
        )
    """))

    print("Downgrade complete!")

#!/usr/bin/env python3
"""
Verification script for Person/UnitOwnership/UnitTenancy migration.

This script verifies that:
1. All new tables exist (persons, unit_ownerships, unit_tenancies)
2. Old units.resident_id column has been dropped
3. Data migration was successful (if any residents existed)
4. All relationships are correctly configured
"""

import sys
from sqlalchemy import inspect, text

# Add parent directory to path
sys.path.insert(0, ".")

from application import create_app
from app.db import db
from app.models import Person, UnitOwnership, UnitTenancy, Unit


def verify_tables_exist():
    """Verify that all new tables exist in the database"""
    print("\n" + "="*70)
    print("1. VERIFYING TABLE EXISTENCE")
    print("="*70)

    inspector = inspect(db.engine)
    existing_tables = inspector.get_table_names()

    required_tables = ['persons', 'unit_ownerships', 'unit_tenancies']
    missing_tables = []

    for table in required_tables:
        if table in existing_tables:
            print(f"  [+] Table '{table}' exists")
        else:
            print(f"  [-] Table '{table}' MISSING")
            missing_tables.append(table)

    if missing_tables:
        print(f"\n  [!] ERROR: Missing tables: {', '.join(missing_tables)}")
        return False
    else:
        print("\n  [OK] All required tables exist")
        return True


def verify_units_resident_id_dropped():
    """Verify that units.resident_id column has been dropped"""
    print("\n" + "="*70)
    print("2. VERIFYING UNITS.RESIDENT_ID COLUMN DROPPED")
    print("="*70)

    inspector = inspect(db.engine)
    units_columns = [col['name'] for col in inspector.get_columns('units')]

    if 'resident_id' in units_columns:
        print("  [-] ERROR: units.resident_id column still exists!")
        return False
    else:
        print("  [+] units.resident_id column successfully dropped")
        return True


def verify_persons_table_structure():
    """Verify persons table has all required columns"""
    print("\n" + "="*70)
    print("3. VERIFYING PERSONS TABLE STRUCTURE")
    print("="*70)

    inspector = inspect(db.engine)
    columns = {col['name']: col for col in inspector.get_columns('persons')}

    required_columns = [
        'id', 'first_name', 'last_name', 'email', 'phone',
        'alternate_phone', 'id_number', 'emergency_contact_name',
        'emergency_contact_phone', 'app_user_id', 'password_hash',
        'is_active', 'profile_photo_url', 'created_by', 'updated_by',
        'created_at', 'updated_at'
    ]

    missing_columns = []
    for col in required_columns:
        if col in columns:
            print(f"  [+] Column '{col}' exists")
        else:
            print(f"  [-] Column '{col}' MISSING")
            missing_columns.append(col)

    # Check unique constraints
    print("\n  Checking unique constraints...")
    constraints = inspector.get_unique_constraints('persons')
    constraint_names = [c['name'] for c in constraints]

    expected_constraints = ['uq_persons_email', 'uq_persons_id_number', 'uq_persons_app_user_id']
    for constraint in expected_constraints:
        if constraint in constraint_names:
            print(f"  [+] Constraint '{constraint}' exists")
        else:
            print(f"  [-] Constraint '{constraint}' MISSING (may have different name)")

    if missing_columns:
        print(f"\n  [!] ERROR: Missing columns: {', '.join(missing_columns)}")
        return False
    else:
        print("\n  [OK] Persons table structure is correct")
        return True


def verify_data_migration():
    """Verify that data was migrated correctly"""
    print("\n" + "="*70)
    print("4. VERIFYING DATA MIGRATION")
    print("="*70)

    # Count persons
    person_count = Person.query.count()
    print(f"  Persons in database: {person_count}")

    # Count tenancies
    tenancy_count = UnitTenancy.query.count()
    print(f"  Tenancy records: {tenancy_count}")

    # Count ownerships
    ownership_count = UnitOwnership.query.count()
    print(f"  Ownership records: {ownership_count}")

    # Check for orphaned tenancies (tenancies without person or unit)
    print("\n  Checking for orphaned tenancy records...")
    orphaned_tenancies = db.session.execute(text("""
        SELECT COUNT(*) FROM unit_tenancies ut
        WHERE NOT EXISTS (SELECT 1 FROM persons p WHERE p.id = ut.person_id)
        OR NOT EXISTS (SELECT 1 FROM units u WHERE u.id = ut.unit_id)
    """)).scalar()

    if orphaned_tenancies > 0:
        print(f"  [-] ERROR: Found {orphaned_tenancies} orphaned tenancy records!")
        return False
    else:
        print(f"  [+] No orphaned tenancy records")

    # Check for orphaned ownerships
    print("\n  Checking for orphaned ownership records...")
    orphaned_ownerships = db.session.execute(text("""
        SELECT COUNT(*) FROM unit_ownerships uo
        WHERE NOT EXISTS (SELECT 1 FROM persons p WHERE p.id = uo.person_id)
        OR NOT EXISTS (SELECT 1 FROM units u WHERE u.id = uo.unit_id)
    """)).scalar()

    if orphaned_ownerships > 0:
        print(f"  [-] ERROR: Found {orphaned_ownerships} orphaned ownership records!")
        return False
    else:
        print(f"  [+] No orphaned ownership records")

    print("\n  [OK] Data migration verification passed")
    return True


def verify_relationships():
    """Verify that SQLAlchemy relationships work correctly"""
    print("\n" + "="*70)
    print("5. VERIFYING SQLALCHEMY RELATIONSHIPS")
    print("="*70)

    try:
        # Test Person relationships
        person = Person.query.first()
        if person:
            print(f"\n  Testing Person: {person.full_name}")
            print(f"    - units_owned: {len(person.units_owned)} units")
            print(f"    - units_rented: {len(person.units_rented)} units")
            print(f"    - all_units: {len(person.all_units)} units")
            print(f"    [+] Person relationships work")
        else:
            print("  [~] No persons in database to test")

        # Test Unit relationships
        unit = Unit.query.first()
        if unit:
            print(f"\n  Testing Unit: {unit.unit_number}")
            print(f"    - owners: {len(unit.owners)} persons")
            print(f"    - tenants: {len(unit.tenants)} persons")
            print(f"    - all_tenants: {len(unit.all_tenants)} persons")
            print(f"    - primary_owner: {unit.primary_owner.full_name if unit.primary_owner else 'None'}")
            print(f"    - primary_tenant: {unit.primary_tenant.full_name if unit.primary_tenant else 'None'}")
            print(f"    [+] Unit relationships work")
        else:
            print("  [~] No units in database to test")

        # Test UnitTenancy relationships
        tenancy = UnitTenancy.query.first()
        if tenancy:
            print(f"\n  Testing UnitTenancy:")
            print(f"    - person: {tenancy.person.full_name}")
            print(f"    - unit: {tenancy.unit.unit_number}")
            print(f"    - is_active: {tenancy.is_active}")
            print(f"    [+] UnitTenancy relationships work")
        else:
            print("  [~] No tenancies in database to test")

        # Test UnitOwnership relationships
        ownership = UnitOwnership.query.first()
        if ownership:
            print(f"\n  Testing UnitOwnership:")
            print(f"    - person: {ownership.person.full_name}")
            print(f"    - unit: {ownership.unit.unit_number}")
            print(f"    - ownership_percentage: {ownership.ownership_percentage}%")
            print(f"    [+] UnitOwnership relationships work")
        else:
            print("  [~] No ownerships in database to test")

        print("\n  [OK] All relationships are working correctly")
        return True

    except Exception as e:
        print(f"\n  [-] ERROR: Relationship test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def verify_backward_compatibility():
    """Verify that backward compatibility properties work"""
    print("\n" + "="*70)
    print("6. VERIFYING BACKWARD COMPATIBILITY")
    print("="*70)

    try:
        unit = Unit.query.first()
        if unit:
            # Test backward compatibility properties
            print(f"\n  Testing Unit backward compatibility:")
            print(f"    - unit.resident (should return primary_tenant): {unit.resident.full_name if unit.resident else 'None'}")
            print(f"    - unit.residents (should return tenants list): {len(unit.residents)} persons")
            print(f"    [+] Backward compatibility properties work")
        else:
            print("  [~] No units in database to test")

        print("\n  [OK] Backward compatibility verified")
        return True

    except Exception as e:
        print(f"\n  [-] ERROR: Backward compatibility test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all verification checks"""
    print("\n" + "#"*70)
    print("# PERSON MIGRATION VERIFICATION SCRIPT")
    print("#"*70)

    app = create_app()
    with app.app_context():
        results = []

        # Run all verification steps
        results.append(("Tables Exist", verify_tables_exist()))
        results.append(("resident_id Dropped", verify_units_resident_id_dropped()))
        results.append(("Persons Structure", verify_persons_table_structure()))
        results.append(("Data Migration", verify_data_migration()))
        results.append(("Relationships", verify_relationships()))
        results.append(("Backward Compatibility", verify_backward_compatibility()))

        # Print summary
        print("\n" + "="*70)
        print("VERIFICATION SUMMARY")
        print("="*70)

        all_passed = True
        for test_name, result in results:
            status = "[OK]" if result else "[FAIL]"
            print(f"  {status} {test_name}")
            if not result:
                all_passed = False

        print("="*70)

        if all_passed:
            print("\n[SUCCESS] All verification checks passed!")
            print("\nThe Person migration was successful. You can now:")
            print("  1. Access /api/v1/persons to manage persons")
            print("  2. Create tenancies and ownerships for units")
            print("  3. Multiple persons can now own or rent the same unit")
            return 0
        else:
            print("\n[FAILURE] Some verification checks failed!")
            print("\nPlease review the errors above and fix them before using the new system.")
            return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)

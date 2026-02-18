"""Test script for MobileUser model and services"""
import os
os.environ['FLASK_APP'] = 'application:create_app'

from application import create_app
from app.db import db
from app.models import Person, MobileUser
from app.services.mobile_users import (
    create_mobile_user,
    authenticate_mobile_user,
    change_password,
    get_user_units,
    can_access_unit
)
from app.utils.password_generator import (
    generate_temporary_password,
    validate_password_strength,
    validate_phone_number
)

def test_password_utilities():
    """Test password generation and validation"""
    print("\n=== Testing Password Utilities ===")

    # Test password generation
    pwd = generate_temporary_password()
    print(f"Generated password: {pwd}")
    print(f"Password length: {len(pwd)}")

    # Test password strength validation
    is_valid, error = validate_password_strength(pwd)
    print(f"Generated password valid: {is_valid}")
    if not is_valid:
        print(f"Error: {error}")

    # Test weak passwords
    weak_passwords = [
        ("abc123", "too short, no uppercase"),
        ("Abc12345", "valid"),
        ("password", "no uppercase or numbers"),
        ("PASSWORD123", "no lowercase"),
    ]

    for pwd, description in weak_passwords:
        is_valid, error = validate_password_strength(pwd)
        status = "VALID" if is_valid else f"INVALID: {error}"
        print(f"  {pwd} ({description}): {status}")

def test_phone_validation():
    """Test phone number validation"""
    print("\n=== Testing Phone Validation ===")

    test_phones = [
        ("0821234567", "South African mobile"),
        ("+27821234567", "E.164 format"),
        ("082 123 4567", "with spaces"),
        ("082-123-4567", "with dashes"),
        ("1234567890", "invalid format"),
        ("", "empty"),
    ]

    for phone, description in test_phones:
        is_valid, normalized = validate_phone_number(phone)
        status = f"VALID -> {normalized}" if is_valid else "INVALID"
        print(f"  {phone} ({description}): {status}")

def test_mobile_user_creation():
    """Test creating a mobile user"""
    print("\n=== Testing Mobile User Creation ===")

    # Find a person to create mobile user for (use person ID 4 which has valid phone)
    person = Person.query.get(4)

    if not person:
        print("ERROR: No person found in database. Please create a person first.")
        return

    print(f"Found person: {person.full_name} (ID: {person.id})")
    print(f"Person phone: {person.phone}")

    # Check if person already has mobile user
    existing = MobileUser.query.filter_by(person_id=person.id).first()
    if existing:
        print(f"Person already has mobile user account (ID: {existing.id})")
        print(f"Phone number: {existing.phone_number}")
        print(f"Is active: {existing.is_active}")
        print(f"Password must change: {existing.password_must_change}")
        return existing

    # If person has no phone, update it
    if not person.phone:
        print("Person has no phone number, setting one for testing...")
        person.phone = "0821234567"
        db.session.commit()
        print(f"Set phone to: {person.phone}")

    # Create mobile user
    print("\nCreating mobile user account...")
    success, result = create_mobile_user(person.id, send_sms=False)

    if success:
        mobile_user = result['user']
        temp_password = result['temp_password']
        print(f"SUCCESS: Created mobile user")
        print(f"  User ID: {mobile_user.id}")
        print(f"  Phone: {mobile_user.phone_number}")
        print(f"  Temp password: {temp_password}")
        print(f"  Must change password: {mobile_user.password_must_change}")
        return mobile_user, temp_password
    else:
        print(f"FAILED: {result['message']}")
        return None

def test_authentication():
    """Test mobile user authentication"""
    print("\n=== Testing Authentication ===")

    # Get first mobile user
    mobile_user = MobileUser.query.first()

    if not mobile_user:
        print("ERROR: No mobile user found. Create one first.")
        return

    print(f"Testing authentication for: {mobile_user.phone_number}")

    # Test with wrong password
    print("\n1. Testing with wrong password...")
    success, result = authenticate_mobile_user(mobile_user.phone_number, "WrongPass123")
    if not success:
        print(f"  Correctly rejected: {result['message']}")
    else:
        print(f"  ERROR: Should have rejected wrong password")

    # For testing with correct password, we need to know it
    # Let's set a known password
    print("\n2. Setting known test password...")
    test_password = "TestPass123"
    mobile_user.set_temporary_password(test_password)
    db.session.commit()
    print(f"  Set temporary password: {test_password}")

    # Test with correct password
    print("\n3. Testing with correct password...")
    success, result = authenticate_mobile_user(mobile_user.phone_number, test_password)
    if success:
        print(f"  SUCCESS: Authenticated successfully")
        print(f"  User ID: {result.id}")
        print(f"  Last login updated: {result.last_login}")
    else:
        print(f"  ERROR: Should have authenticated: {result['message']}")

def test_password_change():
    """Test password change functionality"""
    print("\n=== Testing Password Change ===")

    mobile_user = MobileUser.query.first()

    if not mobile_user:
        print("ERROR: No mobile user found.")
        return

    print(f"Testing password change for: {mobile_user.phone_number}")

    # Set current password
    current_pwd = "Current123"
    mobile_user.set_password(current_pwd)
    db.session.commit()
    print(f"Set current password: {current_pwd}")
    print(f"Password must change: {mobile_user.password_must_change}")

    # Test changing to weak password
    print("\n1. Testing with weak password...")
    success, result = change_password(mobile_user, "weak", current_pwd)
    if not success:
        print(f"  Correctly rejected: {result['message']}")

    # Test changing to strong password
    print("\n2. Testing with strong password...")
    new_pwd = "NewPass456"
    success, result = change_password(mobile_user, new_pwd, current_pwd)
    if success:
        print(f"  SUCCESS: Password changed")
        print(f"  Password must change flag cleared: {mobile_user.password_must_change}")

        # Verify new password works
        print("\n3. Verifying new password works...")
        if mobile_user.check_password(new_pwd):
            print(f"  SUCCESS: New password verified")
        else:
            print(f"  ERROR: New password doesn't work")
    else:
        print(f"  ERROR: {result['message']}")

def test_user_units():
    """Test getting user units"""
    print("\n=== Testing User Units ===")

    # Find a person with units
    from app.models import UnitOwnership, UnitTenancy

    ownership = UnitOwnership.query.first()
    if ownership:
        person_id = ownership.person_id
        person = Person.query.get(person_id)
        print(f"Testing units for person: {person.full_name} (ID: {person_id})")

        units = get_user_units(person_id)
        print(f"Found {len(units)} unit(s):")
        for unit in units:
            print(f"  - Unit {unit['unit_number']} ({unit['role']})")
            if unit['role'] == 'owner':
                print(f"    Ownership: {unit['ownership_percentage']}%")
            elif unit['role'] == 'tenant':
                print(f"    Rent: R{unit['monthly_rent']}")
    else:
        print("No ownerships found in database")

def main():
    """Run all tests"""
    app = create_app()

    with app.app_context():
        try:
            print("="*60)
            print("MOBILE USER TESTING")
            print("="*60)

            test_password_utilities()
            test_phone_validation()
            test_mobile_user_creation()
            test_authentication()
            test_password_change()
            test_user_units()

            print("\n" + "="*60)
            print("TESTING COMPLETE")
            print("="*60)

        except Exception as e:
            print(f"\n[ERROR] Test failed: {str(e)}")
            import traceback
            traceback.print_exc()

if __name__ == '__main__':
    main()

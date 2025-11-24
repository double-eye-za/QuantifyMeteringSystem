"""Reset a mobile user's password for testing"""
import os
import sys
os.environ['FLASK_APP'] = 'application:create_app'

from application import create_app
from app.db import db
from app.models import MobileUser, Person
from app.utils.password_generator import generate_temporary_password

def reset_password(phone_number: str):
    """Reset password for a mobile user by phone number"""
    app = create_app()

    with app.app_context():
        # Find mobile user by phone
        mobile_user = MobileUser.query.filter_by(phone_number=phone_number).first()

        if not mobile_user:
            print(f"[ERROR] No mobile user found with phone number: {phone_number}")
            print("\nAvailable mobile users:")
            all_users = MobileUser.query.all()
            for user in all_users:
                person = Person.query.get(user.person_id)
                print(f"  - {user.phone_number} ({person.full_name if person else 'Unknown'})")
            return

        # Get person info
        person = Person.query.get(mobile_user.person_id)

        print(f"\nFound mobile user:")
        print(f"  Person: {person.full_name if person else 'Unknown'}")
        print(f"  Phone: {mobile_user.phone_number}")
        print(f"  Current status: {'Active' if mobile_user.is_active else 'Inactive'}")

        # Generate new temporary password
        temp_password = generate_temporary_password()

        # Set temporary password
        mobile_user.set_temporary_password(temp_password)
        db.session.commit()

        print(f"\n[SUCCESS] Password reset successfully!")
        print(f"\n" + "="*60)
        print(f"LOGIN CREDENTIALS FOR MOBILE APP:")
        print(f"="*60)
        print(f"Phone Number: {mobile_user.phone_number}")
        print(f"Password: {temp_password}")
        print(f"="*60)
        print(f"\nUse these credentials to login via the mobile app.")
        print(f"You will be prompted to change the password on first login.")

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: python reset_mobile_password.py <phone_number>")
        print("\nExamples:")
        print("  python reset_mobile_password.py +27821234567")
        print("  python reset_mobile_password.py 0821234567")
        print("\nTo see all mobile users, run:")
        print("  python reset_mobile_password.py list")
        sys.exit(1)

    phone = sys.argv[1]

    if phone == 'list':
        app = create_app()
        with app.app_context():
            print("\nAll mobile users:")
            print("="*60)
            all_users = MobileUser.query.all()
            if not all_users:
                print("  No mobile users found.")
            for user in all_users:
                person = Person.query.get(user.person_id)
                status = "Active" if user.is_active else "Inactive"
                print(f"  {user.phone_number:20} | {person.full_name if person else 'Unknown':30} | {status}")
            print("="*60)
    else:
        # Normalize phone if needed
        if phone.startswith('0') and len(phone) == 10:
            phone = f"+27{phone[1:]}"

        reset_password(phone)

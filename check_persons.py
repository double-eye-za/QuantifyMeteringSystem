"""Check persons in database"""
import os
os.environ['FLASK_APP'] = 'application:create_app'

from application import create_app
from app.models import Person
from app.utils.password_generator import validate_phone_number

def main():
    app = create_app()

    with app.app_context():
        print("Persons in database:")
        print("="*70)

        persons = Person.query.all()

        for person in persons:
            is_valid, normalized = validate_phone_number(person.phone) if person.phone else (False, "")
            status = f"[OK] Valid: {normalized}" if is_valid else "[X] Invalid" if person.phone else "[X] No phone"
            print(f"ID {person.id}: {person.full_name:30} | {person.phone or 'N/A':15} | {status}")

if __name__ == '__main__':
    main()

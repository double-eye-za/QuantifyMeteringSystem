"""Update a person with a valid phone number for testing"""
import os
os.environ['FLASK_APP'] = 'application:create_app'

from application import create_app
from app.db import db
from app.models import Person

def main():
    app = create_app()

    with app.app_context():
        # Update person ID 4 (Luke Bob) with a valid phone
        person = Person.query.get(4)

        if person:
            print(f"Updating person: {person.full_name} (ID: {person.id})")
            print(f"Old phone: {person.phone}")

            # Set valid South African phone number
            person.phone = "0821234567"
            db.session.commit()

            print(f"New phone: {person.phone}")
            print("[OK] Phone number updated successfully")
        else:
            print("Person ID 4 not found")

if __name__ == '__main__':
    main()

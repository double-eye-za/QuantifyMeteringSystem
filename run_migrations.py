"""Simple script to run database migrations"""
import os
import sys

# Set the Flask app
os.environ['FLASK_APP'] = 'application:create_app'

# Import after setting env var
from application import create_app
from flask_migrate import upgrade
from app.db import db

if __name__ == '__main__':
    app = create_app()
    with app.app_context():
        print("Running database migrations...")
        try:
            upgrade()
            print("\n[OK] Migrations completed successfully!")
        except Exception as e:
            print(f"\n[ERROR] Migration failed: {str(e)}")
            import traceback
            traceback.print_exc()
            sys.exit(1)

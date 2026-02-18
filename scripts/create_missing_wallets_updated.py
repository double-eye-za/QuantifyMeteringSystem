"""Create wallets for units that don't have one"""
import os
import sys

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

os.environ['FLASK_APP'] = 'application:create_app'

from application import create_app
from app.db import db
from app.models import Unit, Wallet

def create_missing_wallets():
    """Create wallets for all units that don't have one"""
    app = create_app()

    with app.app_context():
        print("\n" + "="*60)
        print("CREATING MISSING WALLETS FOR UNITS")
        print("="*60 + "\n")

        # Get all units
        all_units = Unit.query.all()
        print(f"Found {len(all_units)} total units")

        # Track statistics
        created_count = 0
        existing_count = 0

        for unit in all_units:
            # Check if unit already has a wallet
            existing_wallet = Wallet.query.filter_by(unit_id=unit.id).first()

            if existing_wallet:
                existing_count += 1
                print(f"  Unit {unit.unit_number} (ID: {unit.id}): Already has wallet (Balance: R{existing_wallet.balance})")
            else:
                # Create wallet for this unit
                wallet = Wallet(
                    unit_id=unit.id,
                    balance=0.0,
                    electricity_balance=0.0,
                    water_balance=0.0,
                    solar_balance=0.0,
                    hot_water_balance=0.0
                )
                db.session.add(wallet)
                created_count += 1
                print(f"  Unit {unit.unit_number} (ID: {unit.id}): Created new wallet")

        # Commit all changes
        if created_count > 0:
            db.session.commit()
            print(f"\n[SUCCESS] Created {created_count} new wallet(s)")

        print(f"\nSummary:")
        print(f"  - Units with existing wallets: {existing_count}")
        print(f"  - New wallets created: {created_count}")
        print(f"  - Total units: {len(all_units)}")
        print("\n" + "="*60)

if __name__ == '__main__':
    create_missing_wallets()

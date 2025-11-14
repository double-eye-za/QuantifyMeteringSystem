#!/usr/bin/env python3
"""
Create wallets for all units that don't have one
"""
import sys
import os

# Add parent directory to path so we can import app
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app
from app.db import db
from app.models import Unit, Wallet

def create_missing_wallets():
    """Create wallets for all units that don't have one."""
    app = create_app()

    with app.app_context():
        # Find all units
        all_units = Unit.query.all()
        print(f"Found {len(all_units)} total units")

        created_count = 0
        already_have_wallet = 0

        for unit in all_units:
            # Check if wallet already exists
            existing_wallet = Wallet.query.filter_by(unit_id=unit.id).first()

            if existing_wallet:
                already_have_wallet += 1
                print(f"  ✓ Unit {unit.unit_number} (ID: {unit.id}) already has wallet (ID: {existing_wallet.id})")
            else:
                # Create new wallet
                wallet = Wallet(
                    unit_id=unit.id,
                    balance=0.00,
                    electricity_balance=0.00,
                    water_balance=0.00,
                    solar_balance=0.00,
                    hot_water_balance=0.00,
                    low_balance_threshold=50.00,
                    is_active=True
                )
                db.session.add(wallet)
                created_count += 1
                print(f"  + Created wallet for Unit {unit.unit_number} (ID: {unit.id})")

        # Commit all new wallets
        if created_count > 0:
            db.session.commit()
            print(f"\n✓ Successfully created {created_count} new wallets")
        else:
            print(f"\n✓ No new wallets needed - all units already have wallets")

        print(f"  Total units: {len(all_units)}")
        print(f"  Already had wallets: {already_have_wallet}")
        print(f"  Newly created: {created_count}")

if __name__ == "__main__":
    create_missing_wallets()

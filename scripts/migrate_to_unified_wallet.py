#!/usr/bin/env python3
"""
Migrate wallets from utility-siloed balances to unified wallet model.

WHAT THIS DOES:
- Recalculates wallet.balance as the true remaining funds from transaction history
  (total topups - total consumption)
- Populates utility columns (electricity_balance, water_balance, etc.) with
  cumulative spend (negative numbers representing how much each utility has consumed)

BEFORE RUNNING:
1. Backup the database!
2. Review the --dry-run output first

USAGE:
    python scripts/migrate_to_unified_wallet.py --dry-run   # Preview changes
    python scripts/migrate_to_unified_wallet.py --apply      # Apply changes
"""
import sys
import os
import argparse

# Add parent directory to path so we can import app
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from application import create_app
from app.db import db
from sqlalchemy import text


def migrate_to_unified_wallet(dry_run=True):
    """Migrate all wallets to unified model using transaction history."""
    app = create_app()

    with app.app_context():
        print("=" * 70)
        print("UNIFIED WALLET MIGRATION")
        print(f"Mode: {'DRY RUN (no changes)' if dry_run else 'APPLY (will modify data)'}")
        print("=" * 70)

        # Step 1: Get all wallets with their current state
        wallets = db.session.execute(text("""
            SELECT id, unit_id, balance,
                   electricity_balance, water_balance,
                   solar_balance, hot_water_balance
            FROM wallets
            ORDER BY id
        """)).fetchall()

        print(f"\nFound {len(wallets)} wallets to process\n")

        # Step 2: Calculate correct balance and spend per wallet from transactions
        txn_summary = db.session.execute(text("""
            SELECT
                wallet_id,
                COALESCE(SUM(CASE
                    WHEN transaction_type LIKE 'topup%%' AND status = 'completed'
                    THEN amount ELSE 0 END), 0) AS total_topups,
                COALESCE(SUM(CASE
                    WHEN transaction_type = 'consumption_electricity' AND status = 'completed'
                    THEN amount ELSE 0 END), 0) AS elec_consumed,
                COALESCE(SUM(CASE
                    WHEN transaction_type = 'consumption_water' AND status = 'completed'
                    THEN amount ELSE 0 END), 0) AS water_consumed,
                COALESCE(SUM(CASE
                    WHEN transaction_type = 'consumption_solar' AND status = 'completed'
                    THEN amount ELSE 0 END), 0) AS solar_consumed,
                COALESCE(SUM(CASE
                    WHEN transaction_type = 'consumption_hot_water' AND status = 'completed'
                    THEN amount ELSE 0 END), 0) AS hotw_consumed,
                COALESCE(SUM(CASE
                    WHEN transaction_type LIKE 'consumption_%%' AND status = 'completed'
                    THEN amount ELSE 0 END), 0) AS total_consumed,
                COALESCE(SUM(CASE
                    WHEN transaction_type IN ('refund', 'adjustment') AND status = 'completed'
                    THEN amount ELSE 0 END), 0) AS adjustments
            FROM transactions
            GROUP BY wallet_id
        """)).fetchall()

        # Build lookup: wallet_id -> transaction summary
        txn_map = {}
        for row in txn_summary:
            txn_map[row[0]] = {
                'total_topups': float(row[1]),
                'elec_consumed': float(row[2]),
                'water_consumed': float(row[3]),
                'solar_consumed': float(row[4]),
                'hotw_consumed': float(row[5]),
                'total_consumed': float(row[6]),
                'adjustments': float(row[7]),
            }

        # Step 3: Process each wallet
        updated = 0
        skipped = 0
        errors = 0

        for w in wallets:
            wallet_id = w[0]
            unit_id = w[1]
            old_balance = float(w[2] or 0)
            old_elec = float(w[3] or 0)
            old_water = float(w[4] or 0)
            old_solar = float(w[5] or 0)
            old_hotw = float(w[6] or 0)

            # Get transaction history for this wallet
            txn = txn_map.get(wallet_id, {
                'total_topups': 0, 'elec_consumed': 0, 'water_consumed': 0,
                'solar_consumed': 0, 'hotw_consumed': 0, 'total_consumed': 0,
                'adjustments': 0,
            })

            # Calculate new values
            # balance = total topups - total consumption + adjustments
            new_balance = txn['total_topups'] - txn['total_consumed'] + txn['adjustments']

            # Utility columns = negative cumulative spend
            new_elec = -txn['elec_consumed']
            new_water = -txn['water_consumed']
            new_solar = -txn['solar_consumed']
            new_hotw = -txn['hotw_consumed']

            print(f"Wallet #{wallet_id} (Unit {unit_id}):")
            print(f"  Transaction history:")
            print(f"    Total top-ups:    R{txn['total_topups']:>10.2f}")
            print(f"    Total consumed:   R{txn['total_consumed']:>10.2f}")
            print(f"    Adjustments:      R{txn['adjustments']:>10.2f}")
            print(f"  BEFORE (siloed):")
            print(f"    balance:            R{old_balance:>10.2f}")
            print(f"    electricity_balance: R{old_elec:>10.2f}")
            print(f"    water_balance:       R{old_water:>10.2f}")
            print(f"    solar_balance:       R{old_solar:>10.2f}")
            print(f"    hot_water_balance:   R{old_hotw:>10.2f}")
            print(f"  AFTER (unified):")
            print(f"    balance:            R{new_balance:>10.2f}  (available funds)")
            print(f"    electricity_balance: R{new_elec:>10.2f}  (cumulative spend)")
            print(f"    water_balance:       R{new_water:>10.2f}  (cumulative spend)")
            print(f"    solar_balance:       R{new_solar:>10.2f}  (cumulative spend)")
            print(f"    hot_water_balance:   R{new_hotw:>10.2f}  (cumulative spend)")

            # Sanity check: warn if calculated balance differs significantly from current
            diff = abs(new_balance - old_balance)
            if diff > 1.0:
                print(f"  ⚠️  Balance difference: R{diff:.2f} (old: R{old_balance:.2f}, calculated: R{new_balance:.2f})")
            print()

            if not dry_run:
                try:
                    db.session.execute(text("""
                        UPDATE wallets SET
                            balance = :balance,
                            electricity_balance = :elec,
                            water_balance = :water,
                            solar_balance = :solar,
                            hot_water_balance = :hotw,
                            updated_at = NOW()
                        WHERE id = :wallet_id
                    """), {
                        'balance': new_balance,
                        'elec': new_elec,
                        'water': new_water,
                        'solar': new_solar,
                        'hotw': new_hotw,
                        'wallet_id': wallet_id,
                    })
                    updated += 1
                except Exception as e:
                    errors += 1
                    print(f"  ❌ ERROR updating wallet #{wallet_id}: {e}")
            else:
                updated += 1

        # Step 4: Commit or report
        if not dry_run:
            db.session.commit()
            print("=" * 70)
            print(f"MIGRATION COMPLETE: {updated} wallets updated, {errors} errors")
            print("=" * 70)
        else:
            print("=" * 70)
            print(f"DRY RUN COMPLETE: {updated} wallets would be updated")
            print("Re-run with --apply to apply changes")
            print("=" * 70)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Migrate wallets to unified model')
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--dry-run', action='store_true', help='Preview changes without modifying data')
    group.add_argument('--apply', action='store_true', help='Apply the migration')
    args = parser.parse_args()

    migrate_to_unified_wallet(dry_run=args.dry_run)

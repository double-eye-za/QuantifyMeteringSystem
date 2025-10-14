from __future__ import annotations

import os
import sys
from datetime import date
import json
import logging

# Ensure project root is on sys.path when running this script directly
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(CURRENT_DIR)
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from application import create_app
from app.db import db
from app.models import (
    User,
    Role,
    Estate,
    Unit,
    Meter,
    Wallet,
    RateTable,
)
from sqlalchemy import text


def ensure_admin_user() -> User:
    user = User.query.filter_by(username="admin").first()
    if user:
        return user
    user = User(
        username="admin",
        email="admin@example.com",
        first_name="Admin",
        last_name="User",
        is_active=True,
    )
    user.set_password("password")
    db.session.add(user)
    db.session.commit()
    return user


def create_rate_tables(admin_user: User) -> dict[str, RateTable]:
    existing = {rt.name: rt for rt in RateTable.query.all()}
    tables: dict[str, RateTable] = {}
    created_count = 0

    # Standard Residential
    if "Standard Residential" not in existing:
        rt = RateTable(
            name="Standard Residential",
            utility_type="electricity",
            rate_structure=json.dumps(
                {
                    "electricity": [
                        {"up_to": 150, "rate": 1.15},
                        {"up_to": 350, "rate": 1.60},
                        {"up_to": 600, "rate": 2.10},
                        {"up_to": None, "rate": 2.40},
                    ],
                    "water": [
                        {"up_to": 6, "rate": 10.00},
                        {"up_to": 15, "rate": 15.00},
                        {"up_to": 30, "rate": 20.00},
                        {"up_to": None, "rate": 25.00},
                    ],
                }
            ),
            is_default=True,
            effective_from=date.today(),
            is_active=True,
            created_by=admin_user.id,
        )
        db.session.add(rt)
        tables[rt.name] = rt
        created_count += 1
    else:
        tables["Standard Residential"] = existing["Standard Residential"]

    # Pensioner Subsidized
    if "Pensioner Subsidized" not in existing:
        rt = RateTable(
            name="Pensioner Subsidized",
            utility_type="electricity",
            rate_structure=json.dumps(
                {
                    "electricity": [
                        {"up_to": 100, "rate": 0.70},
                        {"up_to": None, "rate": 1.00},
                    ],
                    "water": [
                        {"up_to": 10, "rate": 7.00},
                        {"up_to": None, "rate": 12.00},
                    ],
                }
            ),
            is_default=False,
            effective_from=date.today(),
            is_active=True,
            created_by=admin_user.id,
        )
        db.session.add(rt)
        tables[rt.name] = rt
        created_count += 1
    else:
        tables["Pensioner Subsidized"] = existing["Pensioner Subsidized"]

    # Commercial Standard
    if "Commercial Standard" not in existing:
        rt = RateTable(
            name="Commercial Standard",
            utility_type="electricity",
            rate_structure=json.dumps(
                {
                    "electricity": [
                        {"up_to": 200, "rate": 2.00},
                        {"up_to": 1000, "rate": 2.60},
                        {"up_to": None, "rate": 3.20},
                    ],
                    "water": [
                        {"up_to": 30, "rate": 18.00},
                        {"up_to": 100, "rate": 22.00},
                        {"up_to": None, "rate": 28.00},
                    ],
                }
            ),
            is_default=False,
            effective_from=date.today(),
            is_active=True,
            created_by=admin_user.id,
        )
        db.session.add(rt)
        tables[rt.name] = rt
        created_count += 1
    else:
        tables["Commercial Standard"] = existing["Commercial Standard"]

    db.session.commit()
    logging.info(
        "Seeding rate tables done (created=%d, total=%d)",
        created_count,
        RateTable.query.count(),
    )
    return tables


def create_estates_and_units(
    admin_user: User, rate_tables: dict[str, RateTable]
) -> dict[str, int]:
    # Estates inspired by prototype
    estates_data = [
        {
            "code": "WCRK",
            "name": "Willow Creek",
            "city": "Johannesburg",
            "total_units": 50,
            "electricity_markup_percentage": 20.0,
            "water_markup_percentage": 15.0,
            "solar_free_allocation_kwh": 50.0,
            "electricity_rate_table_id": rate_tables["Standard Residential"].id,
            "water_rate_table_id": rate_tables["Standard Residential"].id,
        },
        {
            "code": "PKVG",
            "name": "Parkview Gardens",
            "city": "Johannesburg",
            "total_units": 50,
            "electricity_markup_percentage": 20.0,
            "water_markup_percentage": 15.0,
            "solar_free_allocation_kwh": 50.0,
            "electricity_rate_table_id": rate_tables["Standard Residential"].id,
            "water_rate_table_id": rate_tables["Standard Residential"].id,
        },
        {
            "code": "SNSR",
            "name": "Sunset Ridge",
            "city": "Johannesburg",
            "total_units": 75,
            "electricity_markup_percentage": 20.0,
            "water_markup_percentage": 15.0,
            "solar_free_allocation_kwh": 50.0,
            "electricity_rate_table_id": rate_tables["Standard Residential"].id,
            "water_rate_table_id": rate_tables["Standard Residential"].id,
        },
        {
            "code": "RVMD",
            "name": "Riverside Meadows",
            "city": "Johannesburg",
            "total_units": 20,
            "electricity_markup_percentage": 15.0,
            "water_markup_percentage": 10.0,
            "solar_free_allocation_kwh": 50.0,
            "electricity_rate_table_id": rate_tables["Standard Residential"].id,
            "water_rate_table_id": rate_tables["Standard Residential"].id,
        },
    ]

    estates: dict[str, Estate] = {}
    estates_created = 0
    for ed in estates_data:
        estate = Estate.query.filter_by(code=ed["code"]).first()
        if not estate:
            estate = Estate.create_from_payload(ed)
            estates_created += 1
        estates[ed["code"]] = estate

    # Create sample meters and units matching prototype examples
    meters_created = 0
    units_created = 0

    def ensure_meter(serial: str, mtype: str) -> Meter:
        m = Meter.query.filter_by(serial_number=serial).first()
        if m:
            return m
        m = Meter(serial_number=serial, meter_type=mtype)
        db.session.add(m)
        db.session.commit()
        nonlocal meters_created
        meters_created += 1
        return m

    # Willow Creek examples
    e_e460_001 = ensure_meter("E460-001", "electricity")
    e_wtr_001 = ensure_meter("WTR-001", "water")
    e_sol_001 = ensure_meter("SOL-001", "solar")

    unit_a101 = Unit.query.filter_by(
        estate_id=estates["WCRK"].id, unit_number="A-101"
    ).first()
    if not unit_a101:
        unit_a101 = Unit.create_from_payload(
            {
                "estate_id": estates["WCRK"].id,
                "unit_number": "A-101",
                "floor": "Ground Floor",
                "occupancy_status": "occupied",
                "electricity_meter_id": e_e460_001.id,
                "water_meter_id": e_wtr_001.id,
                "solar_meter_id": e_sol_001.id,
            }
        )
        units_created += 1

    # Another unit
    e_e460_002 = ensure_meter("E460-002", "electricity")
    e_wtr_002 = ensure_meter("WTR-002", "water")
    e_sol_002 = ensure_meter("SOL-002", "solar")
    if not Unit.query.filter_by(
        estate_id=estates["WCRK"].id, unit_number="A-102"
    ).first():
        Unit.create_from_payload(
            {
                "estate_id": estates["WCRK"].id,
                "unit_number": "A-102",
                "floor": "Ground Floor",
                "occupancy_status": "occupied",
                "electricity_meter_id": e_e460_002.id,
                "water_meter_id": e_wtr_002.id,
                "solar_meter_id": e_sol_002.id,
            }
        )
        units_created += 1

    # Vacant example in Parkview
    pk_e460_051 = ensure_meter("E460-051", "electricity")
    pk_wtr_051 = ensure_meter("WTR-051", "water")
    pk_sol_051 = ensure_meter("SOL-051", "solar")
    if not Unit.query.filter_by(
        estate_id=estates["PKVG"].id, unit_number="B-201"
    ).first():
        Unit.create_from_payload(
            {
                "estate_id": estates["PKVG"].id,
                "unit_number": "B-201",
                "floor": "Second Floor",
                "occupancy_status": "vacant",
                "electricity_meter_id": pk_e460_051.id,
                "water_meter_id": pk_wtr_051.id,
                "solar_meter_id": pk_sol_051.id,
            }
        )
        units_created += 1

    # Another Parkview occupied unit
    pk_e460_052 = ensure_meter("E460-052", "electricity")
    pk_wtr_052 = ensure_meter("WTR-052", "water")
    pk_sol_052 = ensure_meter("SOL-052", "solar")
    if not Unit.query.filter_by(
        estate_id=estates["PKVG"].id, unit_number="B-202"
    ).first():
        Unit.create_from_payload(
            {
                "estate_id": estates["PKVG"].id,
                "unit_number": "B-202",
                "floor": "Second Floor",
                "occupancy_status": "occupied",
                "electricity_meter_id": pk_e460_052.id,
                "water_meter_id": pk_wtr_052.id,
                "solar_meter_id": pk_sol_052.id,
            }
        )
        units_created += 1

    # Bulk meters
    ensure_meter("BULK-E-001", "bulk_electricity")
    ensure_meter("WAT-025", "water")

    # Sunset Ridge two units
    sn_e460_050 = ensure_meter("E460-050", "electricity")
    sn_wtr_050 = ensure_meter("WTR-050", "water")
    sn_sol_050 = ensure_meter("SOL-050", "solar")
    if not Unit.query.filter_by(
        estate_id=estates["SNSR"].id, unit_number="C-301"
    ).first():
        Unit.create_from_payload(
            {
                "estate_id": estates["SNSR"].id,
                "unit_number": "C-301",
                "floor": "Third Floor",
                "occupancy_status": "occupied",
                "electricity_meter_id": sn_e460_050.id,
                "water_meter_id": sn_wtr_050.id,
                "solar_meter_id": sn_sol_050.id,
            }
        )
        units_created += 1

    sn_e460_075 = ensure_meter("E460-075", "electricity")
    sn_wtr_075 = ensure_meter("WTR-075", "water")
    sn_sol_075 = ensure_meter("SOL-075", "solar")
    if not Unit.query.filter_by(
        estate_id=estates["SNSR"].id, unit_number="C-302"
    ).first():
        Unit.create_from_payload(
            {
                "estate_id": estates["SNSR"].id,
                "unit_number": "C-302",
                "floor": "Third Floor",
                "occupancy_status": "occupied",
                "electricity_meter_id": sn_e460_075.id,
                "water_meter_id": sn_wtr_075.id,
                "solar_meter_id": sn_sol_075.id,
            }
        )
        units_created += 1

    # New estate Riverside Meadows with two units
    rv_e460_001 = ensure_meter("E460-RV-001", "electricity")
    rv_wtr_001 = ensure_meter("WTR-RV-001", "water")
    rv_sol_001 = ensure_meter("SOL-RV-001", "solar")
    if not Unit.query.filter_by(
        estate_id=estates["RVMD"].id, unit_number="D-101"
    ).first():
        Unit.create_from_payload(
            {
                "estate_id": estates["RVMD"].id,
                "unit_number": "D-101",
                "floor": "Ground Floor",
                "occupancy_status": "occupied",
                "electricity_meter_id": rv_e460_001.id,
                "water_meter_id": rv_wtr_001.id,
                "solar_meter_id": rv_sol_001.id,
            }
        )
        units_created += 1

    rv_e460_002 = ensure_meter("E460-RV-002", "electricity")
    rv_wtr_002 = ensure_meter("WTR-RV-002", "water")
    rv_sol_002 = ensure_meter("SOL-RV-002", "solar")
    if not Unit.query.filter_by(
        estate_id=estates["RVMD"].id, unit_number="D-102"
    ).first():
        Unit.create_from_payload(
            {
                "estate_id": estates["RVMD"].id,
                "unit_number": "D-102",
                "floor": "Ground Floor",
                "occupancy_status": "vacant",
                "electricity_meter_id": rv_e460_002.id,
                "water_meter_id": rv_wtr_002.id,
                "solar_meter_id": rv_sol_002.id,
            }
        )
        units_created += 1

    # Create one wallet per unit if missing (1:1 via wallets.unit_id)
    wallets_created = 0
    for unit in Unit.query.all():
        existing = Wallet.query.filter_by(unit_id=unit.id).first()
        if not existing:
            wallet = Wallet(unit_id=unit.id)
            db.session.add(wallet)
            db.session.commit()
            wallets_created += 1

    logging.info(
        "Seeding estates and units done (estates_created=%d, units_created=%d, meters_created=%d, wallets_created=%d)",
        estates_created,
        units_created,
        meters_created,
        wallets_created,
    )

    return {
        "estates_created": estates_created,
        "units_created": units_created,
        "meters_created": meters_created,
        "wallets_created": wallets_created,
    }


def reset_database_data() -> None:
    engine_name = db.engine.name
    logging.info("Resetting database data using engine='%s'", engine_name)
    if engine_name == "postgresql":
        # Use TRUNCATE ... CASCADE to clear all data and reset identities
        db.session.execute(
            text("""
            DO $$ DECLARE
                r RECORD;
            BEGIN
                FOR r IN (
                    SELECT tablename FROM pg_tables WHERE schemaname = 'public'
                ) LOOP
                    EXECUTE 'TRUNCATE TABLE ' || quote_ident(r.tablename) || ' RESTART IDENTITY CASCADE';
                END LOOP;
            END $$;
        """)
        )
        db.session.commit()
    else:
        # Generic fallback: delete from all tables in reverse dependency order
        meta = db.metadata
        meta.reflect(bind=db.engine)
        for table in reversed(meta.sorted_tables):
            db.session.execute(table.delete())
        db.session.commit()
        if engine_name == "sqlite":
            # Reset autoincrement in SQLite
            try:
                db.session.execute(text("DELETE FROM sqlite_sequence"))
                db.session.commit()
            except Exception:
                db.session.rollback()


def main():
    # Allow overriding the DB URL via env for local runs
    logging.basicConfig(level=logging.INFO, format="[%(levelname)s] %(message)s")
    app = create_app()
    with app.app_context():
        logging.info("Starting seed...")
        reset_database_data()
        admin_user = ensure_admin_user()
        logging.info("Admin user ensured: id=%s", admin_user.id)
        rate_tables = create_rate_tables(admin_user)
        counts = create_estates_and_units(admin_user, rate_tables)
        summary = {
            "users_total": User.query.count(),
            "estates_total": Estate.query.count(),
            "units_total": Unit.query.count(),
            "meters_total": Meter.query.count(),
            "wallets_total": Wallet.query.count(),
            "rate_tables_total": RateTable.query.count(),
        }
        logging.info(
            "Seeding completed. Created: estates=%d, units=%d, meters=%d, wallets=%d. Totals: users=%d, estates=%d, units=%d, meters=%d, wallets=%d, rate_tables=%d",
            counts["estates_created"],
            counts["units_created"],
            counts["meters_created"],
            counts["wallets_created"],
            summary["users_total"],
            summary["estates_total"],
            summary["units_total"],
            summary["meters_total"],
            summary["wallets_total"],
            summary["rate_tables_total"],
        )
        print(
            "Seed complete: "
            + f"created(estates={counts['estates_created']}, units={counts['units_created']}, meters={counts['meters_created']}, wallets={counts['wallets_created']}) | "
            f"totals(users={summary['users_total']}, estates={summary['estates_total']}, units={summary['units_total']}, meters={summary['meters_total']}, wallets={summary['wallets_total']}, rate_tables={summary['rate_tables_total']})"
        )


if __name__ == "__main__":
    main()

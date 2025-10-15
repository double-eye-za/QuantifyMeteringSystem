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
    MeterReading,
    MeterAlert,
    Resident,
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

    # Electricity: Standard Residential
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

    # Electricity: Pensioner Subsidized
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

    # Electricity: Commercial Standard
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

    # WATER rate tables (separate utility_type='water')
    if "Standard Residential Water" not in existing:
        rt = RateTable(
            name="Standard Residential Water",
            utility_type="water",
            rate_structure=json.dumps(
                {
                    "water": [
                        {"up_to": 6, "rate": 10.00},
                        {"up_to": 15, "rate": 15.00},
                        {"up_to": 30, "rate": 20.00},
                        {"up_to": None, "rate": 25.00},
                    ]
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
        tables["Standard Residential Water"] = existing["Standard Residential Water"]

    if "Pensioner Subsidized Water" not in existing:
        rt = RateTable(
            name="Pensioner Subsidized Water",
            utility_type="water",
            rate_structure=json.dumps(
                {
                    "water": [
                        {"up_to": 10, "rate": 7.00},
                        {"up_to": None, "rate": 12.00},
                    ]
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
        tables["Pensioner Subsidized Water"] = existing["Pensioner Subsidized Water"]

    if "Commercial Standard Water" not in existing:
        rt = RateTable(
            name="Commercial Standard Water",
            utility_type="water",
            rate_structure=json.dumps(
                {
                    "water": [
                        {"up_to": 30, "rate": 18.00},
                        {"up_to": 100, "rate": 22.00},
                        {"up_to": None, "rate": 28.00},
                    ]
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
        tables["Commercial Standard Water"] = existing["Commercial Standard Water"]

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
            "name": "Willow Creek Estate",
            "address": "123 Main Road",
            "city": "Johannesburg",
            "postal_code": "2000",
            "contact_name": "John Smith",
            "contact_phone": "+27 11 123 4567",
            "contact_email": "manager.willow@example.com",
            "total_units": 50,
            "electricity_markup_percentage": 20.0,
            "water_markup_percentage": 15.0,
            "solar_free_allocation_kwh": 50.0,
            "electricity_rate_table_id": rate_tables["Standard Residential"].id,
            "water_rate_table_id": rate_tables["Standard Residential Water"].id,
        },
        {
            "code": "PKVG",
            "name": "Parkview Gardens",
            "address": "456 Park Avenue",
            "city": "Pretoria",
            "postal_code": "0083",
            "contact_name": "Jane Doe",
            "contact_phone": "+27 12 345 6789",
            "contact_email": "manager.parkview@example.com",
            "total_units": 50,
            "electricity_markup_percentage": 20.0,
            "water_markup_percentage": 15.0,
            "solar_free_allocation_kwh": 50.0,
            "electricity_rate_table_id": rate_tables["Standard Residential"].id,
            "water_rate_table_id": rate_tables["Standard Residential Water"].id,
        },
        {
            "code": "SNSR",
            "name": "Sunset Ridge Estate",
            "address": "789 Ridge Road",
            "city": "Cape Town",
            "postal_code": "7441",
            "contact_name": "Peter Brown",
            "contact_phone": "+27 21 555 0101",
            "contact_email": "manager.sunset@example.com",
            "total_units": 75,
            "electricity_markup_percentage": 20.0,
            "water_markup_percentage": 15.0,
            "solar_free_allocation_kwh": 50.0,
            "electricity_rate_table_id": rate_tables["Standard Residential"].id,
            "water_rate_table_id": rate_tables["Standard Residential Water"].id,
        },
        {
            "code": "RVMD",
            "name": "Riverside Meadows",
            "address": "12 River Close",
            "city": "Johannesburg",
            "postal_code": "2191",
            "contact_name": "Sarah Johnson",
            "contact_phone": "+27 10 555 0000",
            "contact_email": "manager.riverside@example.com",
            "total_units": 20,
            "electricity_markup_percentage": 15.0,
            "water_markup_percentage": 10.0,
            "solar_free_allocation_kwh": 50.0,
            "electricity_rate_table_id": rate_tables["Standard Residential"].id,
            "water_rate_table_id": rate_tables["Standard Residential Water"].id,
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

    # Willow Creek examples + bulk meters
    blk_e_wcrk = ensure_meter("BULK-E-WCRK", "bulk_electricity")
    blk_w_wcrk = ensure_meter("BULK-W-WCRK", "bulk_water")
    wcrk = estates["WCRK"]
    if not wcrk.bulk_electricity_meter_id:
        wcrk.bulk_electricity_meter_id = blk_e_wcrk.id
    if not wcrk.bulk_water_meter_id:
        wcrk.bulk_water_meter_id = blk_w_wcrk.id
    db.session.commit()

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

    # Parkview + bulk
    blk_e_pkvg = ensure_meter("BULK-E-PKVG", "bulk_electricity")
    blk_w_pkvg = ensure_meter("BULK-W-PKVG", "bulk_water")
    pkvg = estates["PKVG"]
    if not pkvg.bulk_electricity_meter_id:
        pkvg.bulk_electricity_meter_id = blk_e_pkvg.id
    if not pkvg.bulk_water_meter_id:
        pkvg.bulk_water_meter_id = blk_w_pkvg.id
    db.session.commit()

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

    # Additional meters
    ensure_meter("WAT-025", "water")

    # Sunset Ridge + bulk
    blk_e_snsr = ensure_meter("BULK-E-SNSR", "bulk_electricity")
    blk_w_snsr = ensure_meter("BULK-W-SNSR", "bulk_water")
    snsr = estates["SNSR"]
    if not snsr.bulk_electricity_meter_id:
        snsr.bulk_electricity_meter_id = blk_e_snsr.id
    if not snsr.bulk_water_meter_id:
        snsr.bulk_water_meter_id = blk_w_snsr.id
    db.session.commit()

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

    # Riverside Meadows + bulk
    blk_e_rvmd = ensure_meter("BULK-E-RVMD", "bulk_electricity")
    blk_w_rvmd = ensure_meter("BULK-W-RVMD", "bulk_water")
    rvmd = estates["RVMD"]
    if not rvmd.bulk_electricity_meter_id:
        rvmd.bulk_electricity_meter_id = blk_e_rvmd.id
    if not rvmd.bulk_water_meter_id:
        rvmd.bulk_water_meter_id = blk_w_rvmd.id
    db.session.commit()

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


def create_readings_and_alerts() -> dict[str, int]:
    from datetime import datetime, timedelta

    readings_created = 0
    alerts_created = 0

    # Create last 7 days readings per meter
    for meter in Meter.query.all():
        base = 1000.0
        for i in range(7, 0, -1):
            ts = datetime.utcnow() - timedelta(days=i)
            value = base + (7 - i) * 50 + (meter.id % 5) * 10
            if not MeterReading.query.filter_by(
                meter_id=meter.id, reading_date=ts
            ).first():
                mr = MeterReading(
                    meter_id=meter.id,
                    reading_value=value,
                    reading_date=ts,
                    reading_type="automatic",
                    is_validated=True,
                    validation_date=ts,
                )
                db.session.add(mr)
                readings_created += 1
        db.session.commit()

    # Create a few alerts
    some_meter = Meter.query.first()
    if some_meter and not MeterAlert.query.first():
        alert = MeterAlert(
            meter_id=some_meter.id,
            alert_type="communication_loss",
            severity="warning",
            message="Intermittent communication detected",
            is_resolved=False,
        )
        db.session.add(alert)
        alerts_created += 1
        db.session.commit()

    logging.info(
        "Seeding readings and alerts done (readings=%d, alerts=%d)",
        readings_created,
        alerts_created,
    )
    return {"readings_created": readings_created, "alerts_created": alerts_created}


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
        ra_counts = create_readings_and_alerts()
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
            + f"created(estates={counts['estates_created']}, units={counts['units_created']}, meters={counts['meters_created']}, wallets={counts['wallets_created']}, readings={ra_counts['readings_created']}, alerts={ra_counts['alerts_created']}) | "
            f"totals(users={summary['users_total']}, estates={summary['estates_total']}, units={summary['units_total']}, meters={summary['meters_total']}, wallets={summary['wallets_total']}, rate_tables={summary['rate_tables_total']})"
        )


if __name__ == "__main__":
    main()

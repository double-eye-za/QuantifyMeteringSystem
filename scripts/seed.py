from __future__ import annotations

import os
import sys
from datetime import date, time
from typing import Optional
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
    RateTableTier,
    TimeOfUseRate,
    MeterReading,
    MeterAlert,
    Resident,
    Transaction,
)
from sqlalchemy import text

import random
from datetime import datetime, timedelta
from decimal import Decimal


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


def create_tiers_and_time_of_use(rate_tables: dict[str, RateTable]) -> None:
    """Create example tiers and TOU periods aligned with the screenshot for demo purposes."""

    # Helper to ensure tier
    def add_tier(
        rt: RateTable,
        tier_number: int,
        from_kwh: float,
        to_kwh,
        rate: float,
        desc: Optional[str] = None,
    ):
        existing = RateTableTier.query.filter_by(
            rate_table_id=rt.id, tier_number=tier_number
        ).first()
        if existing:
            return
        if rt.id is None:
            return
        t = RateTableTier(
            rate_table_id=rt.id,
            tier_number=tier_number,
            from_kwh=from_kwh,
            to_kwh=to_kwh,
            rate_per_kwh=rate,
            description=desc,
        )
        db.session.add(t)

    # Helper to ensure TOU
    def add_tou(
        rt: RateTable,
        name: str,
        start: time,
        end: time,
        weekdays: bool,
        weekends: bool,
        rate: float,
    ):
        existing = TimeOfUseRate.query.filter_by(
            rate_table_id=rt.id,
            period_name=name,
            start_time=start,
            end_time=end,
        ).first()
        if existing:
            return
        if rt.id is None:
            return
        p = TimeOfUseRate(
            rate_table_id=rt.id,
            period_name=name,
            start_time=start,
            end_time=end,
            weekdays=weekdays,
            weekends=weekends,
            rate_per_kwh=rate,
        )
        db.session.add(p)

    # Seed tiers/TOU for every rate table created above
    # Use reasonable demo defaults by utility; numbers are illustrative
    for rt in rate_tables.values():
        if rt.utility_type == "electricity":
            add_tier(rt, 1, 0, 600, 3.2926, "0–600 kWh")
            add_tier(rt, 2, 600, None, 4.1332, ">600 kWh")
            add_tier(rt, 3, 0, None, 3.7650, "Prepaid single rate")

            add_tou(rt, "Off-peak", time(22, 0), time(6, 0), True, True, 2.432)
            add_tou(rt, "Standard", time(6, 0), time(17, 0), True, False, 3.096)
            add_tou(rt, "Peak", time(17, 0), time(22, 0), True, False, 4.996)
        elif rt.utility_type == "water":
            add_tier(rt, 1, 0, 6, 21.15, "0–6 kL")
            add_tier(rt, 2, 6, 10.5, 29.06, ">6–10.5 kL")
            add_tier(rt, 3, 10.5, 35, 43.44, ">10.5–35 kL")
            add_tier(rt, 4, 35, None, 83.80, ">35 kL")

    db.session.commit()


def ensure_roles_and_super_admin() -> None:
    """Create Super Administrator, Administrator, Standard User roles with appropriate permissions and a super admin user."""
    from app.models.permissions import Permission

    # Define permissions for each module
    full_crud = {"view": True, "create": True, "edit": True, "delete": True}
    view_only = {"view": True}

    # Super Admin gets all permissions
    super_admin_permissions = {
        "estates": full_crud,
        "units": full_crud,
        "meters": full_crud,
        "residents": full_crud,
        "rate_tables": full_crud,
        "settings": {"view": True, "edit": True},
        "audit_logs": view_only,
        "wallets": view_only,
        "transactions": view_only,
        "notifications": view_only,
        "reports": view_only,
        "users": {
            "view": True,
            "create": True,
            "edit": True,
            "delete": True,
            "enable": True,
            "disable": True,
        },
        "roles": full_crud,
    }

    admin_permissions = {
        "estates": full_crud,
        "units": full_crud,
        "meters": full_crud,
        "residents": full_crud,
        "rate_tables": full_crud,
        "settings": {
            "view": False,
            "edit": False,
        },
        "audit_logs": {
            "view": False,
        },
        "wallets": {"view": False},
        "transactions": {"view": False},
        "notifications": view_only,
        "reports": {"view": False},
        "users": {
            "view": True,
            "create": True,
            "edit": True,
            "delete": True,
            "enable": True,
            "disable": True,
        },
        "roles": full_crud,
    }

    standard_permissions = {
        "estates": {"view": True, "create": False, "edit": False, "delete": False},
        "units": {"view": True, "create": False, "edit": False, "delete": False},
        "meters": {"view": True, "create": False, "edit": False, "delete": False},
        "residents": {"view": False, "create": False, "edit": False, "delete": False},
        "rate_tables": {"view": True, "create": False, "edit": False, "delete": False},
        "settings": {
            "view": False,
            "edit": False,
        },
        "audit_logs": {
            "view": False,
        },
        "wallets": {"view": True},
        "transactions": {"view": True},
        "notifications": {
            "view": True,
        },
        "reports": {
            "view": False,
        },
        "users": {
            "view": False,
            "create": False,
            "edit": False,
            "delete": False,
        },
        "roles": {
            "view": False,
            "create": False,
            "edit": False,
            "delete": False,
        },
    }

    def get_or_create_role(name: str, description: str, permissions_data: dict):
        role = Role.query.filter_by(name=name).first()
        if role and role.permission_id:
            return role.id
        perm = Permission.query.filter_by(name=f"{name} Permissions").first()
        if not perm:
            perm = Permission.create_permission(
                name=f"{name} Permissions",
                description=f"Permissions for {name}",
                permissions_data=permissions_data,
            )
            db.session.flush()
        if not role:
            role = Role(
                name=name,
                description=description,
                permission_id=perm.id,
                is_system_role=(name.lower().startswith("super")),
            )
            db.session.add(role)
        else:
            role.permission_id = perm.id
        db.session.commit()
        return role.id

    super_admin_role_id = get_or_create_role(
        "Super Administrator", "Full system access", super_admin_permissions
    )
    admin_role_id = get_or_create_role(
        "Administrator", "Administrative access", admin_permissions
    )
    standard_role_id = get_or_create_role(
        "Standard User", "Standard user access", standard_permissions
    )

    # Ensure the requested super admin user
    user = User.query.filter_by(email="takudzwa@metalogix.solutions").first()
    if not user:
        user = User.create_user(
            username="takudzwa",
            email="takudzwa@metalogix.solutions",
            first_name="Takudzwa",
            last_name="Maseva",
            password="takudzwa",
            role_id=super_admin_role_id,
            is_active=True,
        )
        user.is_super_admin = True
        db.session.commit()
    else:
        user.role_id = super_admin_role_id
        user.is_super_admin = True
        db.session.commit()


def create_estates_and_units(
    admin_user: User, rate_tables: dict[str, RateTable]
) -> dict[str, int]:
    # Estates inspired by prototype
    estates_data = [
        {
            "code": "OAKR",
            "name": "Oak Ridge Estate",
            "address": "123 Main Road",
            "city": "Johannesburg",
            "postal_code": "2000",
            "contact_name": "John Smith",
            "contact_phone": "+27 11 123 4567",
            "contact_email": "manager.oakridge@example.com",
            "total_units": 50,
            "electricity_markup_percentage": 20.0,
            "water_markup_percentage": 15.0,
            "solar_free_allocation_kwh": 50.0,
            "electricity_rate_table_id": rate_tables["Standard Residential"].id,
            "water_rate_table_id": rate_tables["Standard Residential Water"].id,
        },
        {
            "code": "GRNV",
            "name": "Green Valley Gardens",
            "address": "456 Park Avenue",
            "city": "Pretoria",
            "postal_code": "0083",
            "contact_name": "Jane Doe",
            "contact_phone": "+27 12 345 6789",
            "contact_email": "manager.greenvalley@example.com",
            "total_units": 50,
            "electricity_markup_percentage": 20.0,
            "water_markup_percentage": 15.0,
            "solar_free_allocation_kwh": 50.0,
            "electricity_rate_table_id": rate_tables["Standard Residential"].id,
            "water_rate_table_id": rate_tables["Standard Residential Water"].id,
        },
        {
            "code": "DRBN",
            "name": "Durban Heights Estate",
            "address": "789 Beach Road",
            "city": "Durban",
            "postal_code": "4001",
            "contact_name": "Peter Brown",
            "contact_phone": "+27 31 555 0101",
            "contact_email": "manager.durban@example.com",
            "total_units": 75,
            "electricity_markup_percentage": 20.0,
            "water_markup_percentage": 15.0,
            "solar_free_allocation_kwh": 50.0,
            "electricity_rate_table_id": rate_tables["Standard Residential"].id,
            "water_rate_table_id": rate_tables["Standard Residential Water"].id,
        },
        {
            "code": "PEBA",
            "name": "Port Elizabeth Bayview",
            "address": "12 Bay Close",
            "city": "Port Elizabeth",
            "postal_code": "6001",
            "contact_name": "Sarah Johnson",
            "contact_phone": "+27 41 555 0000",
            "contact_email": "manager.pebayview@example.com",
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
        estate_code: str = ed["code"]
        estate = Estate.query.filter_by(code=estate_code).first()
        if not estate:
            estate = Estate.create_from_payload(ed)
            estates_created += 1
        estates[estate_code] = estate

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

    # Oak Ridge examples + bulk meters
    blk_e_oakr = ensure_meter("BULK-E-OAKR", "bulk_electricity")
    blk_w_oakr = ensure_meter("BULK-W-OAKR", "bulk_water")
    oakr = estates["OAKR"]
    if not oakr.bulk_electricity_meter_id:
        oakr.bulk_electricity_meter_id = blk_e_oakr.id
    if not oakr.bulk_water_meter_id:
        oakr.bulk_water_meter_id = blk_w_oakr.id
    db.session.commit()

    e_e460_001 = ensure_meter("E460-001", "electricity")
    e_wtr_001 = ensure_meter("WTR-001", "water")
    e_sol_001 = ensure_meter("SOL-001", "solar")

    unit_a101 = Unit.query.filter_by(
        estate_id=estates["OAKR"].id, unit_number="A-101"
    ).first()
    if not unit_a101:
        unit_a101 = Unit.create_from_payload(
            {
                "estate_id": estates["OAKR"].id,
                "unit_number": "A-101",
                "floor": "Ground Floor",
                "occupancy_status": "occupied",
                "electricity_meter_id": e_e460_001.id,
                "water_meter_id": e_wtr_001.id,
                "solar_meter_id": e_sol_001.id,
                "electricity_rate_table_id": rate_tables["Standard Residential"].id,
                "water_rate_table_id": rate_tables["Standard Residential Water"].id,
            }
        )
        units_created += 1

    # Another unit
    e_e460_002 = ensure_meter("E460-002", "electricity")
    e_wtr_002 = ensure_meter("WTR-002", "water")
    e_sol_002 = ensure_meter("SOL-002", "solar")
    if not Unit.query.filter_by(
        estate_id=estates["OAKR"].id, unit_number="A-102"
    ).first():
        Unit.create_from_payload(
            {
                "estate_id": estates["OAKR"].id,
                "unit_number": "A-102",
                "floor": "Ground Floor",
                "occupancy_status": "occupied",
                "electricity_meter_id": e_e460_002.id,
                "water_meter_id": e_wtr_002.id,
                "solar_meter_id": e_sol_002.id,
                "electricity_rate_table_id": rate_tables["Standard Residential"].id,
                "water_rate_table_id": rate_tables["Standard Residential Water"].id,
            }
        )
        units_created += 1

    # Green Valley Gardens + bulk
    blk_e_grnv = ensure_meter("BULK-E-GRNV", "bulk_electricity")
    blk_w_grnv = ensure_meter("BULK-W-GRNV", "bulk_water")
    grnv = estates["GRNV"]
    if not grnv.bulk_electricity_meter_id:
        grnv.bulk_electricity_meter_id = blk_e_grnv.id
    if not grnv.bulk_water_meter_id:
        grnv.bulk_water_meter_id = blk_w_grnv.id
    db.session.commit()

    # Vacant example in Green Valley Gardens
    gv_e460_051 = ensure_meter("E460-051", "electricity")
    gv_wtr_051 = ensure_meter("WTR-051", "water")
    gv_sol_051 = ensure_meter("SOL-051", "solar")
    if not Unit.query.filter_by(
        estate_id=estates["GRNV"].id, unit_number="B-201"
    ).first():
        Unit.create_from_payload(
            {
                "estate_id": estates["GRNV"].id,
                "unit_number": "B-201",
                "floor": "Second Floor",
                "occupancy_status": "vacant",
                "electricity_meter_id": gv_e460_051.id,
                "water_meter_id": gv_wtr_051.id,
                "solar_meter_id": gv_sol_051.id,
                "electricity_rate_table_id": rate_tables["Standard Residential"].id,
                "water_rate_table_id": rate_tables["Standard Residential Water"].id,
            }
        )
        units_created += 1

    # Another Green Valley Gardens occupied unit
    gv_e460_052 = ensure_meter("E460-052", "electricity")
    gv_wtr_052 = ensure_meter("WTR-052", "water")
    gv_sol_052 = ensure_meter("SOL-052", "solar")
    if not Unit.query.filter_by(
        estate_id=estates["GRNV"].id, unit_number="B-202"
    ).first():
        Unit.create_from_payload(
            {
                "estate_id": estates["GRNV"].id,
                "unit_number": "B-202",
                "floor": "Second Floor",
                "occupancy_status": "occupied",
                "electricity_meter_id": gv_e460_052.id,
                "water_meter_id": gv_wtr_052.id,
                "solar_meter_id": gv_sol_052.id,
                "electricity_rate_table_id": rate_tables["Standard Residential"].id,
                "water_rate_table_id": rate_tables["Standard Residential Water"].id,
            }
        )
        units_created += 1

    # Additional meters
    ensure_meter("WAT-025", "water")

    # Durban Heights + bulk
    blk_e_drbn = ensure_meter("BULK-E-DRBN", "bulk_electricity")
    blk_w_drbn = ensure_meter("BULK-W-DRBN", "bulk_water")
    drbn = estates["DRBN"]
    if not drbn.bulk_electricity_meter_id:
        drbn.bulk_electricity_meter_id = blk_e_drbn.id
    if not drbn.bulk_water_meter_id:
        drbn.bulk_water_meter_id = blk_w_drbn.id
    db.session.commit()

    # Durban Heights two units
    dh_e460_050 = ensure_meter("E460-050", "electricity")
    dh_wtr_050 = ensure_meter("WTR-050", "water")
    dh_sol_050 = ensure_meter("SOL-050", "solar")
    if not Unit.query.filter_by(
        estate_id=estates["DRBN"].id, unit_number="C-301"
    ).first():
        Unit.create_from_payload(
            {
                "estate_id": estates["DRBN"].id,
                "unit_number": "C-301",
                "floor": "Third Floor",
                "occupancy_status": "occupied",
                "electricity_meter_id": dh_e460_050.id,
                "water_meter_id": dh_wtr_050.id,
                "solar_meter_id": dh_sol_050.id,
                "electricity_rate_table_id": rate_tables["Standard Residential"].id,
                "water_rate_table_id": rate_tables["Standard Residential Water"].id,
            }
        )
        units_created += 1

    dh_e460_075 = ensure_meter("E460-075", "electricity")
    dh_wtr_075 = ensure_meter("WTR-075", "water")
    dh_sol_075 = ensure_meter("SOL-075", "solar")
    if not Unit.query.filter_by(
        estate_id=estates["DRBN"].id, unit_number="C-302"
    ).first():
        Unit.create_from_payload(
            {
                "estate_id": estates["DRBN"].id,
                "unit_number": "C-302",
                "floor": "Third Floor",
                "occupancy_status": "occupied",
                "electricity_meter_id": dh_e460_075.id,
                "water_meter_id": dh_wtr_075.id,
                "solar_meter_id": dh_sol_075.id,
                "electricity_rate_table_id": rate_tables["Standard Residential"].id,
                "water_rate_table_id": rate_tables["Standard Residential Water"].id,
            }
        )
        units_created += 1

    # Port Elizabeth Bayview + bulk
    blk_e_peba = ensure_meter("BULK-E-PEBA", "bulk_electricity")
    blk_w_peba = ensure_meter("BULK-W-PEBA", "bulk_water")
    peba = estates["PEBA"]
    if not peba.bulk_electricity_meter_id:
        peba.bulk_electricity_meter_id = blk_e_peba.id
    if not peba.bulk_water_meter_id:
        peba.bulk_water_meter_id = blk_w_peba.id
    db.session.commit()

    # Port Elizabeth Bayview with two units
    pe_e460_001 = ensure_meter("E460-PE-001", "electricity")
    pe_wtr_001 = ensure_meter("WTR-PE-001", "water")
    pe_sol_001 = ensure_meter("SOL-PE-001", "solar")
    if not Unit.query.filter_by(
        estate_id=estates["PEBA"].id, unit_number="D-101"
    ).first():
        Unit.create_from_payload(
            {
                "estate_id": estates["PEBA"].id,
                "unit_number": "D-101",
                "floor": "Ground Floor",
                "occupancy_status": "occupied",
                "electricity_meter_id": pe_e460_001.id,
                "water_meter_id": pe_wtr_001.id,
                "solar_meter_id": pe_sol_001.id,
                "electricity_rate_table_id": rate_tables["Standard Residential"].id,
                "water_rate_table_id": rate_tables["Standard Residential Water"].id,
            }
        )
        units_created += 1

    pe_e460_002 = ensure_meter("E460-PE-002", "electricity")
    pe_wtr_002 = ensure_meter("WTR-PE-002", "water")
    pe_sol_002 = ensure_meter("SOL-PE-002", "solar")
    if not Unit.query.filter_by(
        estate_id=estates["PEBA"].id, unit_number="D-102"
    ).first():
        Unit.create_from_payload(
            {
                "estate_id": estates["PEBA"].id,
                "unit_number": "D-102",
                "floor": "Ground Floor",
                "occupancy_status": "vacant",
                "electricity_meter_id": pe_e460_002.id,
                "water_meter_id": pe_wtr_002.id,
                "solar_meter_id": pe_sol_002.id,
                "electricity_rate_table_id": rate_tables["Standard Residential"].id,
                "water_rate_table_id": rate_tables["Standard Residential Water"].id,
            }
        )
        units_created += 1

    # Create/ensure one wallet per unit and seed varied balances
    from random import randint, choice

    wallets_created = 0
    for unit in Unit.query.all():
        # Ensure vacant units do not have wallets
        if unit.occupancy_status == "vacant":
            existing = Wallet.query.filter_by(unit_id=unit.id).first()
            if existing:
                db.session.delete(existing)
                db.session.commit()
            continue
        wallet = Wallet.query.filter_by(unit_id=unit.id).first()
        if not wallet:
            wallet = Wallet(unit_id=unit.id)
            db.session.add(wallet)
            wallets_created += 1

        # Assign a balance profile: empty, low, or healthy
        profile = unit.id % 3  # deterministic variety across units
        if profile == 0:
            elec, water, solar = 0.00, 0.00, 0.00
        elif profile == 1:
            elec = round(choice([10.0, 25.0, 35.0, 49.0]), 2)
            water = round(choice([5.0, 12.5, 20.0, 30.0]), 2)
            solar = round(choice([2.0, 8.5, 15.0, 22.0]), 2)
        else:
            elec = round(choice([100.0, 150.0, 200.0, 350.0]), 2)
            water = round(choice([80.0, 120.0, 160.0, 220.0]), 2)
            solar = round(choice([60.0, 110.0, 140.0, 180.0]), 2)

        wallet.electricity_balance = elec
        wallet.water_balance = water
        wallet.solar_balance = solar
        # Also set aggregate balance as sum
        wallet.balance = (elec or 0) + (water or 0) + (solar or 0)

        # Persist
        db.session.commit()

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


def create_monthly_readings_and_transactions():
    readings = 0
    transactions = 0
    today = datetime.now()
    for unit in Unit.query.all():
        if unit.occupancy_status != "occupied":
            continue
        base_values = {"electricity": 0, "water": 0, "solar": 0}
        for day in range(1, today.day + 1):
            ts = today.replace(day=day, hour=0, minute=0, second=0, microsecond=0)
            for meter_id, mtype in [
                (unit.electricity_meter_id, "electricity"),
                (unit.water_meter_id, "water"),
                (unit.solar_meter_id, "solar"),
            ]:
                if not meter_id:
                    continue
                prev_reading = (
                    MeterReading.query.filter_by(meter_id=meter_id)
                    .order_by(MeterReading.reading_date.desc())
                    .first()
                )
                delta_min, delta_max = (
                    (20, 100)
                    if mtype == "electricity"
                    else (10, 50)
                    if mtype == "water"
                    else (5, 30)
                )
                delta = Decimal(str(random.uniform(delta_min, delta_max))).quantize(
                    Decimal("0.01")
                )
                value = (prev_reading.reading_value + delta) if prev_reading else delta
                if not MeterReading.query.filter_by(
                    meter_id=meter_id, reading_date=ts
                ).first():
                    mr = MeterReading(
                        meter_id=meter_id,
                        reading_value=value,
                        consumption_since_last=delta,
                        reading_date=ts,
                        reading_type="automatic",
                        is_validated=True,
                        validation_date=ts,
                    )
                    db.session.add(mr)
                    readings += 1

            # Create utility-specific topup transactions every 3 days
            if unit.wallet and day % 3 == 0:
                # Create separate topup transactions for each utility type
                utilities = ["electricity", "water", "solar"]
                for utility in utilities:
                    amount = Decimal(random.uniform(100, 500)).quantize(Decimal("0.01"))
                    balance_before = unit.wallet.balance or 0
                    balance_after = balance_before + amount

                    # Create utility-specific descriptions for proper categorization
                    descriptions = {
                        "electricity": f"Electricity credit purchase for Unit {unit.unit_number}",
                        "water": f"Water credit purchase for Unit {unit.unit_number}",
                        "solar": f"Solar credit purchase for Unit {unit.unit_number}",
                    }

                    trans = Transaction(
                        transaction_number=f"TXN-{ts.strftime('%Y%m%d')}-{random.randint(1000, 9999)}",
                        wallet_id=unit.wallet.id,
                        transaction_type="topup",
                        amount=amount,
                        balance_before=balance_before,
                        balance_after=balance_after,
                        status="completed",
                        initiated_at=ts,
                        completed_at=ts,
                        reference=f"TOPUP-{unit.id}-{utility}-{day}",
                        description=descriptions[utility],
                        payment_method="eft"
                        if random.choice([True, False])
                        else "card",
                    )
                    db.session.add(trans)
                    unit.wallet.balance = balance_after
                    transactions += 1

    for estate in Estate.query.all():
        base_values = {"bulk_electricity": 0, "bulk_water": 0}
        for day in range(1, today.day + 1):
            ts = today.replace(day=day, hour=0, minute=0, second=0, microsecond=0)
            for meter_id, mtype in [
                (estate.bulk_electricity_meter_id, "bulk_electricity"),
                (estate.bulk_water_meter_id, "bulk_water"),
            ]:
                if not meter_id:
                    continue
                prev_reading = (
                    MeterReading.query.filter_by(meter_id=meter_id)
                    .order_by(MeterReading.reading_date.desc())
                    .first()
                )
                delta_min, delta_max = (
                    (500, 2000) if mtype == "bulk_electricity" else (200, 1000)
                )
                delta = Decimal(str(random.uniform(delta_min, delta_max))).quantize(
                    Decimal("0.01")
                )
                value = (prev_reading.reading_value + delta) if prev_reading else delta
                if not MeterReading.query.filter_by(
                    meter_id=meter_id, reading_date=ts
                ).first():
                    mr = MeterReading(
                        meter_id=meter_id,
                        reading_value=value,
                        consumption_since_last=delta,
                        reading_date=ts,
                        reading_type="automatic",
                        is_validated=True,
                        validation_date=ts,
                    )
                    db.session.add(mr)
                    readings += 1
    db.session.commit()

    logging.info("Created %d readings and %d transactions", readings, transactions)
    return {"readings": readings, "transactions": transactions}


def create_notifications():
    """Create sample notifications according to functional specification."""
    from app.models import Notification

    notifications_created = 0

    # Sample notifications based on functional spec
    sample_notifications = [
        {
            "subject": "Low Balance Alert",
            "message": "Unit A-101 has a low balance of R45.50. Estimated 2 days remaining.",
            "notification_type": "low_balance",
            "priority": "high",
            "status": "sent",
            "channel": "in_app",
        },
        {
            "subject": "Meter Offline",
            "message": "Electricity meter E460-112 in Willow Estate has been offline for 2 hours.",
            "notification_type": "meter_offline",
            "priority": "high",
            "status": "sent",
            "channel": "in_app",
        },
        {
            "subject": "Failed Top-up",
            "message": "Top-up transaction TXN-20241215-1234 failed for Unit B-205. Amount: R300.00",
            "notification_type": "payment_failed",
            "priority": "high",
            "status": "sent",
            "channel": "in_app",
        },
        {
            "subject": "Tamper Detection",
            "message": "Water meter W789-456 in Parkview Estate detected tampering attempt.",
            "notification_type": "tamper",
            "priority": "critical",
            "status": "sent",
            "channel": "in_app",
        },
        {
            "subject": "System Maintenance",
            "message": "Scheduled maintenance window: Dec 20, 2024 02:00-04:00 AM",
            "notification_type": "maintenance",
            "priority": "normal",
            "status": "read",
            "channel": "in_app",
        },
        {
            "subject": "New Unit Registered",
            "message": "Unit C-301 has been registered in Sunset Ridge Estate.",
            "notification_type": "unit_registered",
            "priority": "normal",
            "status": "read",
            "channel": "in_app",
        },
        {
            "subject": "High Consumption Alert",
            "message": "Unit A-203 has consumed 150% above average daily usage.",
            "notification_type": "high_consumption",
            "priority": "high",
            "status": "sent",
            "channel": "in_app",
        },
        {
            "subject": "Solar Allocation Used",
            "message": "Unit B-107 has used 45/50 kWh of free solar allocation this month.",
            "notification_type": "solar_allocation",
            "priority": "normal",
            "status": "read",
            "channel": "in_app",
        },
    ]

    for notif_data in sample_notifications:
        # Check if notification already exists
        existing = Notification.query.filter_by(
            subject=notif_data["subject"], message=notif_data["message"]
        ).first()

        if not existing:
            notification = Notification(
                recipient_type="system",
                recipient_id=None,
                subject=notif_data["subject"],
                message=notif_data["message"],
                notification_type=notif_data["notification_type"],
                priority=notif_data["priority"],
                channel=notif_data["channel"],
                status=notif_data["status"],
                created_at=datetime.now() - timedelta(hours=random.randint(1, 72)),
                sent_at=datetime.now() - timedelta(hours=random.randint(1, 72))
                if notif_data["status"] in ["sent", "read"]
                else None,
                read_at=datetime.now() - timedelta(hours=random.randint(1, 24))
                if notif_data["status"] == "read"
                else None,
            )
            db.session.add(notification)
            notifications_created += 1

    db.session.commit()
    logging.info("Created %d notifications", notifications_created)
    return {"notifications_created": notifications_created}


def create_residents_and_assign(admin_user: User) -> dict[str, int]:
    from random import randint
    from datetime import date, timedelta

    created = 0
    assigned = 0

    first_names = [
        "John",
        "Sarah",
        "Mike",
        "Jane",
        "Peter",
        "Anna",
        "Takudzwa",
        "Emily",
        "Tom",
        "Grace",
    ]
    last_names = [
        "Smith",
        "Johnson",
        "Chen",
        "Doe",
        "Brown",
        "Williams",
        "Maseva",
        "Khan",
        "Naidoo",
        "Botha",
    ]

    def ensure_resident(email: str, data: dict) -> Resident:
        r = Resident.query.filter_by(email=email).first()
        if r:
            return r
        r = Resident(
            id_number=data.get("id_number"),
            first_name=data["first_name"],
            last_name=data["last_name"],
            email=email,
            phone=data["phone"],
            lease_start_date=data.get("lease_start_date"),
            lease_end_date=data.get("lease_end_date"),
            is_active=True,
            created_by=admin_user.id,
        )
        db.session.add(r)
        db.session.commit()
        nonlocal created
        created += 1
        return r

    for unit in Unit.query.all():
        if unit.occupancy_status == "occupied" and not unit.resident_id:
            fn = first_names[unit.id % len(first_names)]
            ln = last_names[unit.id % len(last_names)]
            email = f"{fn.lower()}.{ln.lower()}{unit.id}@example.com"
            phone = f"+27 10 {randint(100, 999)} {randint(1000, 9999)}"
            res = ensure_resident(
                email,
                {
                    "id_number": f"800101{unit.id:04d}0080",
                    "first_name": fn,
                    "last_name": ln,
                    "phone": phone,
                    "lease_start_date": date.today() - timedelta(days=randint(30, 365)),
                    "lease_end_date": None,
                },
            )
            unit.resident_id = res.id
            db.session.commit()
            assigned += 1

    logging.info(
        "Seeding residents done (created=%d, assigned_to_units=%d)", created, assigned
    )
    return {"residents_created": created, "assigned": assigned}


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
        create_tiers_and_time_of_use(rate_tables)
        ensure_roles_and_super_admin()
        counts = create_estates_and_units(admin_user, rate_tables)
        res_counts = create_residents_and_assign(admin_user)
        ra_counts = create_readings_and_alerts()
        monthly_counts = create_monthly_readings_and_transactions()
        notif_counts = create_notifications()
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
            + f"created(estates={counts['estates_created']}, units={counts['units_created']}, meters={counts['meters_created']}, wallets={counts['wallets_created']}, readings={ra_counts['readings_created']}, alerts={ra_counts['alerts_created']}, notifications={notif_counts['notifications_created']}) | "
            f"totals(users={summary['users_total']}, estates={summary['estates_total']}, units={summary['units_total']}, meters={summary['meters_total']}, wallets={summary['wallets_total']}, rate_tables={summary['rate_tables_total']}) | "
            f"residents(created={res_counts['residents_created']}, assigned={res_counts['assigned']})"
        )


if __name__ == "__main__":
    main()

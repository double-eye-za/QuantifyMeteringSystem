from __future__ import annotations

from typing import Optional

from sqlalchemy import or_, func

from app.db import db
from app.models import Estate, Unit, Wallet, Meter, RateTable


def list_estates(search: Optional[str] = None, is_active: Optional[bool] = None):
    query = Estate.query
    if search:
        like = f"%{search}%"
        query = query.filter(or_(Estate.name.ilike(like), Estate.code.ilike(like)))
    if is_active is not None:
        query = query.filter(Estate.is_active == is_active)
    return query


def get_estate_by_id(estate_id: int) -> Optional[Estate]:
    return Estate.query.get(estate_id)


def create_estate(payload: dict, user_id: Optional[int] = None) -> Estate:
    estate = Estate(
        code=payload.get("code"),
        name=payload.get("name"),
        address=payload.get("address"),
        city=payload.get("city"),
        postal_code=payload.get("postal_code"),
        contact_name=payload.get("contact_name"),
        contact_phone=payload.get("contact_phone"),
        contact_email=payload.get("contact_email"),
        total_units=payload.get("total_units", 0),
        electricity_rate_table_id=payload.get("electricity_rate_table_id"),
        water_rate_table_id=payload.get("water_rate_table_id"),
        bulk_electricity_meter_id=payload.get("bulk_electricity_meter_id"),
        bulk_water_meter_id=payload.get("bulk_water_meter_id"),
        electricity_markup_percentage=payload.get(
            "electricity_markup_percentage", 0.00
        ),
        water_markup_percentage=payload.get("water_markup_percentage", 0.00),
        solar_free_allocation_kwh=payload.get("solar_free_allocation_kwh", 50.00),
        is_active=payload.get("is_active", True),
        created_by=user_id,
    )
    db.session.add(estate)
    db.session.commit()
    return estate


def update_estate(
    estate: Estate, payload: dict, user_id: Optional[int] = None
) -> Estate:
    old_elec = estate.electricity_rate_table_id
    old_water = estate.water_rate_table_id

    for field in (
        "code",
        "name",
        "address",
        "city",
        "postal_code",
        "contact_name",
        "contact_phone",
        "contact_email",
        "total_units",
        "electricity_rate_table_id",
        "water_rate_table_id",
        "bulk_electricity_meter_id",
        "bulk_water_meter_id",
        "electricity_markup_percentage",
        "water_markup_percentage",
        "solar_free_allocation_kwh",
        "is_active",
    ):
        if field in payload:
            setattr(estate, field, payload[field])
    if user_id is not None:
        estate.updated_by = user_id
    db.session.commit()

    if (
        old_elec != estate.electricity_rate_table_id
        or old_water != estate.water_rate_table_id
    ):
        units = Unit.query.filter_by(estate_id=estate.id).all()
        for unit in units:
            if (
                unit.electricity_rate_table_id is None
                and estate.electricity_rate_table_id is not None
            ):
                unit.electricity_rate_table_id = estate.electricity_rate_table_id
            if (
                unit.water_rate_table_id is None
                and estate.water_rate_table_id is not None
            ):
                unit.water_rate_table_id = estate.water_rate_table_id
        db.session.commit()
    return estate


def delete_estate(estate: Estate) -> None:
    # Delete related units and their wallets, then the estate
    units = Unit.query.filter_by(estate_id=estate.id).all()
    for unit in units:
        wallet = Wallet.query.filter_by(unit_id=unit.id).first()
        if wallet:
            db.session.delete(wallet)
        db.session.delete(unit)
    db.session.delete(estate)
    db.session.commit()


def count_estates() -> int:
    return Estate.query.count()


def list_rate_tables_for_dropdown(utility_type: str):
    return RateTable.query.filter(RateTable.utility_type == utility_type).all()


def get_meter_by_id(meter_id: int):
    return Meter.query.get(meter_id)

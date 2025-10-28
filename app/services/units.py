from __future__ import annotations

from typing import Optional

from sqlalchemy import or_

from app.db import db
from app.models import Unit, Estate


def list_units(
    estate_id: Optional[int] = None,
    occupancy_status: Optional[str] = None,
    search: Optional[str] = None,
):
    query = Unit.query
    if estate_id is not None:
        query = query.filter(Unit.estate_id == estate_id)
    if occupancy_status is not None:
        query = query.filter(Unit.occupancy_status == occupancy_status)
    if search:
        like = f"%{search}%"
        query = query.filter(
            or_(Unit.unit_number.ilike(like), Unit.building.ilike(like))
        )
    return query


def get_unit_by_id(unit_id: int) -> Optional[Unit]:
    return Unit.query.get(unit_id)


def create_unit(payload: dict, user_id: Optional[int] = None) -> Unit:
    estate = (
        Estate.query.get(payload["estate_id"]) if payload.get("estate_id") else None
    )
    occupancy = payload.get("occupancy_status")
    if occupancy is None and payload.get("resident_id"):
        occupancy = "occupied"
    unit = Unit(
        estate_id=payload["estate_id"],
        unit_number=payload["unit_number"],
        floor=payload.get("floor"),
        building=payload.get("building"),
        bedrooms=payload.get("bedrooms"),
        bathrooms=payload.get("bathrooms"),
        size_sqm=payload.get("size_sqm"),
        occupancy_status=occupancy or "vacant",
        resident_id=payload.get("resident_id"),
        electricity_meter_id=payload.get("electricity_meter_id"),
        water_meter_id=payload.get("water_meter_id"),
        solar_meter_id=payload.get("solar_meter_id"),
        hot_water_meter_id=payload.get("hot_water_meter_id"),
        electricity_rate_table_id=payload.get("electricity_rate_table_id")
        or (estate.electricity_rate_table_id if estate else None),
        water_rate_table_id=payload.get("water_rate_table_id")
        or (estate.water_rate_table_id if estate else None),
        is_active=payload.get("is_active", True),
        created_by=user_id,
    )
    db.session.add(unit)
    db.session.commit()
    return unit


def update_unit(unit: Unit, payload: dict, user_id: Optional[int] = None) -> Unit:
    for field in (
        "estate_id",
        "unit_number",
        "floor",
        "building",
        "bedrooms",
        "bathrooms",
        "size_sqm",
        "occupancy_status",
        "resident_id",
        "electricity_meter_id",
        "water_meter_id",
        "solar_meter_id",
        "hot_water_meter_id",
        "electricity_rate_table_id",
        "water_rate_table_id",
        "is_active",
    ):
        if field in payload:
            setattr(unit, field, payload[field])
    if user_id is not None:
        unit.updated_by = user_id
    db.session.commit()
    return unit


def delete_unit(unit: Unit) -> None:
    db.session.delete(unit)
    db.session.commit()


def count_units() -> int:
    return Unit.query.count()


def find_unit_by_meter_id(meter_id: int) -> Optional[Unit]:
    if not meter_id:
        return None
    return Unit.query.filter(
        or_(
            Unit.electricity_meter_id == meter_id,
            Unit.water_meter_id == meter_id,
            Unit.solar_meter_id == meter_id,
            Unit.hot_water_meter_id == meter_id,
        )
    ).first()

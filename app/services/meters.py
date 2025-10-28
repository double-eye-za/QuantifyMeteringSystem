from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy import or_

from app.db import db
from app.models import Meter, Unit, Wallet, MeterReading


def list_meters(
    meter_type: Optional[str] = None, communication_status: Optional[str] = None
):
    query = Meter.query
    if meter_type:
        query = query.filter(Meter.meter_type == meter_type)
    if communication_status:
        query = query.filter(Meter.communication_status == communication_status)
    return query


def get_meter_by_id(meter_id: int) -> Optional[Meter]:
    return Meter.query.get(meter_id)


def create_meter(payload: dict) -> Meter:
    meter = Meter(
        serial_number=payload["serial_number"],
        meter_type=payload["meter_type"],
        installation_date=payload.get("installation_date"),
        is_active=payload.get("is_active", True),
    )
    db.session.add(meter)
    db.session.commit()
    return meter


def list_available_by_type(meter_type: str):
    return (
        Meter.query.filter(Meter.meter_type == meter_type, Meter.is_active == True)
        .outerjoin(
            Unit,
            or_(
                Unit.electricity_meter_id == Meter.id,
                Unit.water_meter_id == Meter.id,
                Unit.solar_meter_id == Meter.id,
                Unit.hot_water_meter_id == Meter.id,
            ),
        )
        .filter(Unit.id.is_(None))
        .all()
    )


def list_for_meter_readings(
    meter_id: int, start: Optional[datetime] = None, end: Optional[datetime] = None
):
    q = MeterReading.query.filter_by(meter_id=meter_id)
    if start:
        q = q.filter(MeterReading.reading_date >= start)
    if end:
        q = q.filter(MeterReading.reading_date <= end)
    return q.order_by(MeterReading.reading_date.desc())

from __future__ import annotations

from datetime import datetime
from typing import Optional, Tuple, List, Dict, Any

from sqlalchemy import or_, case, and_, literal, func
from sqlalchemy.orm import aliased

from app.db import db
from app.models import Meter, Unit, Wallet, MeterReading, Estate


def list_meters(
    meter_type: Optional[str] = None, communication_status: Optional[str] = None
):
    query = Meter.query
    if meter_type:
        query = query.filter(Meter.meter_type == meter_type)
    if communication_status:
        query = query.filter(Meter.communication_status == communication_status)
    return query


def list_meters_paginated(
    search: Optional[str] = None,
    meter_type: Optional[str] = None,
    communication_status: Optional[str] = None,
    estate_id: Optional[int] = None,
    credit_status: Optional[str] = None,
    page: int = 1,
    per_page: int = 20,
) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    """
    List meters with efficient server-side pagination using SQL joins.

    Returns:
        Tuple of (list of meter dicts with related data, pagination metadata)
    """
    # Alias for bulk meter estate assignments
    BulkElecEstate = aliased(Estate)
    BulkWaterEstate = aliased(Estate)

    # Build base query with all necessary joins
    # Join meters to units (a meter can be assigned via any of the 4 meter_id columns)
    # Also join to estates for bulk meters
    query = (
        db.session.query(Meter, Unit, Wallet, Estate, BulkElecEstate, BulkWaterEstate)
        .outerjoin(
            Unit,
            or_(
                Unit.electricity_meter_id == Meter.id,
                Unit.water_meter_id == Meter.id,
                Unit.solar_meter_id == Meter.id,
                Unit.hot_water_meter_id == Meter.id,
            ),
        )
        .outerjoin(Wallet, Wallet.unit_id == Unit.id)
        .outerjoin(Estate, Estate.id == Unit.estate_id)
        # Join for bulk electricity meters
        .outerjoin(
            BulkElecEstate,
            BulkElecEstate.bulk_electricity_meter_id == Meter.id,
        )
        # Join for bulk water meters
        .outerjoin(
            BulkWaterEstate,
            BulkWaterEstate.bulk_water_meter_id == Meter.id,
        )
    )

    # Apply meter_type filter
    if meter_type:
        query = query.filter(Meter.meter_type == meter_type)

    # Apply communication_status filter
    if communication_status:
        query = query.filter(Meter.communication_status == communication_status)

    # Apply estate filter (for unit-assigned meters and bulk meters)
    if estate_id:
        # Filter by estate (either through unit or bulk meter assignment)
        query = query.filter(
            or_(
                Estate.id == estate_id,
                BulkElecEstate.id == estate_id,
                BulkWaterEstate.id == estate_id,
            )
        )

    # Apply search filter
    if search:
        like = f"%{search}%"
        query = query.filter(
            or_(
                Meter.device_eui.ilike(like),
                Meter.serial_number.ilike(like),
                Unit.unit_number.ilike(like),
                Estate.name.ilike(like),
                BulkElecEstate.name.ilike(like),
                BulkWaterEstate.name.ilike(like),
            )
        )

    # For credit_status filter, we need to compute the balance and compare
    # This is done using SQL CASE expression
    if credit_status:
        # Balance expression based on meter type
        balance_expr = case(
            (Meter.meter_type == "electricity", Wallet.electricity_balance),
            (Meter.meter_type == "water", Wallet.water_balance),
            (Meter.meter_type == "solar", Wallet.solar_balance),
            (Meter.meter_type == "hot_water", Wallet.hot_water_balance),
            else_=Wallet.balance,
        )

        # Threshold - use wallet's threshold or default to 50
        threshold_expr = case(
            (Wallet.low_balance_threshold.isnot(None), Wallet.low_balance_threshold),
            else_=literal(50.0),
        )

        if credit_status == "disconnected":
            query = query.filter(
                or_(
                    balance_expr <= 0,
                    and_(Wallet.id.is_(None), Unit.id.isnot(None)),  # No wallet = disconnected
                )
            )
        elif credit_status == "low":
            query = query.filter(
                and_(
                    balance_expr > 0,
                    balance_expr < threshold_expr,
                )
            )
        elif credit_status == "ok":
            query = query.filter(balance_expr >= threshold_expr)

    # Get total count before pagination (using a subquery for efficiency)
    total = query.count()

    # Create a coalesced estate name expression that considers:
    # 1. Estate from unit assignment
    # 2. Estate from bulk electricity meter assignment
    # 3. Estate from bulk water meter assignment
    # 4. NULL for truly unassigned meters
    effective_estate_name = func.coalesce(
        Estate.name,
        BulkElecEstate.name,
        BulkWaterEstate.name
    )

    # Apply pagination with sorting by estate name (nulls/unassigned last), then unit number, then meter serial
    items = (
        query.order_by(
            # Unassigned meters (no estate from any source) should appear last
            case((effective_estate_name.is_(None), 1), else_=0),
            effective_estate_name.asc(),
            Unit.unit_number.asc(),
            Meter.serial_number.asc()
        )
        .offset((page - 1) * per_page)
        .limit(per_page)
        .all()
    )

    # Build result list with computed fields
    meters_data = []
    for meter, unit, wallet, estate, bulk_elec_estate, bulk_water_estate in items:
        # Compute credit status
        if wallet:
            if meter.meter_type == "electricity":
                bal = float(wallet.electricity_balance or 0)
            elif meter.meter_type == "water":
                bal = float(wallet.water_balance or 0)
            elif meter.meter_type == "solar":
                bal = float(wallet.solar_balance or 0)
            elif meter.meter_type == "hot_water":
                bal = float(wallet.hot_water_balance or 0)
            else:
                bal = float(wallet.balance or 0)

            threshold = float(wallet.low_balance_threshold or 50.0)
            if bal <= 0:
                derived_credit = "disconnected"
            elif bal < threshold:
                derived_credit = "low"
            else:
                derived_credit = "ok"
        else:
            bal = 0.0
            derived_credit = "disconnected" if unit else None

        # Check for bulk meter estate assignment (use joined data, no extra queries)
        assigned_estate = bulk_elec_estate or bulk_water_estate

        meters_data.append({
            **meter.to_dict(),
            "unit": {
                "id": unit.id,
                "estate_id": unit.estate_id,
                "estate_name": estate.name if estate else None,
                "unit_number": unit.unit_number,
                "occupancy_status": unit.occupancy_status,
            } if unit else None,
            "assigned_estate": {
                "id": assigned_estate.id,
                "name": assigned_estate.name,
            } if assigned_estate else None,
            "wallet": wallet.to_dict() if wallet else None,
            "credit_status": derived_credit,
            "balance": bal,
        })

    # Pagination metadata
    pages = (total + per_page - 1) // per_page if per_page else 1
    meta = {
        "page": page,
        "per_page": per_page,
        "total": total,
        "pages": pages,
        "next_page": page + 1 if page < pages else None,
        "prev_page": page - 1 if page > 1 else None,
    }

    return meters_data, meta


def get_meter_by_id(meter_id: int):
    return Meter.query.get(meter_id)


def create_meter(payload: dict):
    # Convert string booleans to actual booleans
    def to_bool(value, default=True):
        if isinstance(value, bool):
            return value
        if isinstance(value, str):
            return value.lower() in ('true', '1', 'yes')
        return default

    meter = Meter(
        serial_number=payload["serial_number"],
        meter_type=payload["meter_type"],
        manufacturer=payload.get("manufacturer"),
        model=payload.get("model"),
        installation_date=payload.get("installation_date"),
        communication_type=payload.get("communication_type", "cellular"),
        is_prepaid=to_bool(payload.get("is_prepaid"), True),
        is_active=to_bool(payload.get("is_active"), True),
        # LoRaWAN device fields
        device_eui=payload.get("device_eui"),
        lorawan_device_type=payload.get("lorawan_device_type"),
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

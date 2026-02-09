from __future__ import annotations

from typing import Optional

from sqlalchemy import or_

from app.db import db
from app.models import Unit, Estate, Person, UnitTenancy


def list_units(
    estate_id: Optional[int] = None,
    occupancy_status: Optional[str] = None,
    search: Optional[str] = None,
):
    # Always join to Estate for sorting by estate name
    query = Unit.query.outerjoin(Estate, Unit.estate_id == Estate.id)

    if estate_id is not None:
        query = query.filter(Unit.estate_id == estate_id)
    if occupancy_status is not None:
        query = query.filter(Unit.occupancy_status == occupancy_status)
    if search:
        like = f"%{search}%"
        # Search across unit_number, building, estate name, and tenant name
        # Use outerjoin to include units without tenants
        query = (
            query.outerjoin(UnitTenancy, Unit.id == UnitTenancy.unit_id)
            .outerjoin(Person, UnitTenancy.person_id == Person.id)
            .filter(
                or_(
                    Unit.unit_number.ilike(like),
                    Unit.building.ilike(like),
                    Estate.name.ilike(like),
                    Person.first_name.ilike(like),
                    Person.last_name.ilike(like),
                )
            )
            .distinct()
        )

    # Sort by Estate name, then by Unit number
    query = query.order_by(Estate.name.asc(), Unit.unit_number.asc())

    return query


def get_unit_by_id(unit_id: int):
    return Unit.query.get(unit_id)


def create_unit(payload: dict, user_id: Optional[int] = None):
    from ..models import Wallet

    estate = (
        Estate.query.get(payload["estate_id"]) if payload.get("estate_id") else None
    )
    occupancy = payload.get("occupancy_status") or "vacant"
    unit = Unit(
        estate_id=payload["estate_id"],
        unit_number=payload["unit_number"],
        floor=payload.get("floor"),
        building=payload.get("building"),
        bedrooms=payload.get("bedrooms"),
        bathrooms=payload.get("bathrooms"),
        size_sqm=payload.get("size_sqm"),
        occupancy_status=occupancy,
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

    # Auto-create wallet for this unit
    existing_wallet = Wallet.query.filter_by(unit_id=unit.id).first()
    if not existing_wallet:
        wallet = Wallet(
            unit_id=unit.id,
            balance=0.0,
            electricity_balance=0.0,
            water_balance=0.0,
            solar_balance=0.0,
            hot_water_balance=0.0
        )
        db.session.add(wallet)
        db.session.commit()

    return unit


def update_unit(unit: Unit, payload: dict, user_id: Optional[int] = None):
    for field in (
        "estate_id",
        "unit_number",
        "floor",
        "building",
        "bedrooms",
        "bathrooms",
        "size_sqm",
        "occupancy_status",
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


class UnitDeleteError(Exception):
    """Raised when a unit cannot be deleted due to dependencies."""
    pass


def delete_unit(unit: Unit):
    """
    Delete a unit safely.

    Rules:
    - If wallet has transactions, raise error (can't delete financial history)
    - If wallet exists but no transactions, delete wallet first
    - Unlink meters (don't delete them, they can be repurposed)
    - Delete unit
    """
    from ..models import Wallet, Transaction

    # Check if unit has a wallet
    wallet = Wallet.query.filter_by(unit_id=unit.id).first()

    if wallet:
        # Check if wallet has any transactions (financial history)
        transaction_count = Transaction.query.filter_by(wallet_id=wallet.id).count()

        if transaction_count > 0:
            raise UnitDeleteError(
                f"Cannot delete unit '{unit.unit_number}': wallet has {transaction_count} transaction(s). "
                f"Consider decommissioning the unit instead to preserve financial history."
            )

        # No transactions - safe to delete wallet
        db.session.delete(wallet)

    # Unlink meters (don't delete them - they can be repurposed)
    unit.electricity_meter_id = None
    unit.water_meter_id = None
    unit.solar_meter_id = None
    unit.hot_water_meter_id = None

    # Now delete the unit
    db.session.delete(unit)
    db.session.commit()


def decommission_unit(unit: Unit):
    """
    Decommission a unit (soft delete).

    This preserves financial history while removing the unit from active use.
    - Sets is_active = False
    - Unlinks all meters (they can be repurposed)
    - Keeps wallet and transactions for audit trail
    """
    # Unlink meters (don't delete them - they can be repurposed)
    unit.electricity_meter_id = None
    unit.water_meter_id = None
    unit.solar_meter_id = None
    unit.hot_water_meter_id = None

    # Mark as inactive
    unit.is_active = False

    db.session.commit()
    return unit


def recommission_unit(unit: Unit):
    """
    Recommission a previously decommissioned unit.

    This brings the unit back to active status.
    - Sets is_active = True
    - Sets occupancy_status to 'vacant' (meters need to be reassigned)
    - Meters must be reassigned manually after recommissioning
    """
    unit.is_active = True
    unit.occupancy_status = "vacant"

    db.session.commit()
    return unit


def count_units():
    return Unit.query.count()


def find_unit_by_meter_id(meter_id: int):
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

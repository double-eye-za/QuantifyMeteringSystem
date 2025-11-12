from __future__ import annotations

from typing import Dict, Any, Optional, List, Tuple


def _compute_tiered_amount(
    quantity: float,
    tiers: List[Dict[str, Any]],
    from_key: str = "from",
    to_key: str = "to",
    rate_key: str = "rate",
) -> float:
    """Compute amount given a tier list. Each tier is a dict with from, optional to, and rate.
    Quantity and rates are treated as floats.
    """
    if not tiers or quantity <= 0:
        return 0.0
    remaining = float(quantity)
    total = 0.0
    for tier in sorted(tiers, key=lambda t: float(t.get(from_key, 0))):
        start = float(tier.get(from_key, 0))
        end = tier.get(to_key)
        rate = float(tier.get(rate_key, 0))
        if remaining <= 0:
            break
        # Determine applicable span for this tier
        if end is None:
            span = max(0.0, remaining)
        else:
            span_limit = max(0.0, float(end) - float(start) + 1e-9)
            span = min(remaining, span_limit)
        if span > 0 and remaining > 0:
            total += span * rate
            remaining -= span
    return round(total, 2)


def compute_from_structure(quantity: float, structure: Dict[str, Any]) -> float:
    """Compute amount from a flexible structure.
    Supports either flat: {"flat_rate": <number>} or tiers: {"tiers": [{from,to,rate}]}.
    """
    if not structure or quantity <= 0:
        return 0.0
    if isinstance(structure, dict):
        if "flat_rate" in structure:
            return round(float(structure.get("flat_rate", 0.0)) * float(quantity), 2)
        if "tiers" in structure and isinstance(structure["tiers"], list):
            return _compute_tiered_amount(float(quantity), structure["tiers"])
    # Unknown structure
    return 0.0


def apply_markup(amount: float, markup_percent: Optional[float]) -> float:
    if not amount:
        return 0.0
    m = float(markup_percent or 0.0)
    return round(float(amount) * (1.0 + m / 100.0), 2)


def calculate_estate_bill(
    *,
    electricity_kwh: float,
    water_kl: float,
    electricity_structure: Optional[Dict[str, Any]] = None,
    water_structure: Optional[Dict[str, Any]] = None,
    electricity_markup_percent: Optional[float] = None,
    water_markup_percent: Optional[float] = None,
    service_fee: Optional[float] = None,
) -> Dict[str, Any]:
    """Return a simple bill breakdown using provided structures and markups."""
    elec_base = compute_from_structure(
        float(electricity_kwh or 0.0), electricity_structure or {}
    )
    water_base = compute_from_structure(float(water_kl or 0.0), water_structure or {})
    elec_total = apply_markup(elec_base, electricity_markup_percent)
    water_total = apply_markup(water_base, water_markup_percent)
    fee = float(service_fee or 0.0)
    total = round(elec_total + water_total + fee, 2)
    return {
        "electricity_base": elec_base,
        "electricity_total": elec_total,
        "water_base": water_base,
        "water_total": water_total,
        "service_fee": fee,
        "total": total,
    }


def calculate_unit_bill(
    *,
    unit_id: int,
    electricity_kwh: float,
    water_kl: float,
    electricity_structure: Optional[Dict[str, Any]] = None,
    water_structure: Optional[Dict[str, Any]] = None,
    electricity_markup_percent: Optional[float] = None,
    water_markup_percent: Optional[float] = None,
    service_fee: Optional[float] = None,
) -> Dict[str, Any]:
    """Calculate bill for a specific unit using its rate table assignments."""
    from ..models import Unit, Estate, RateTable

    unit = Unit.get_by_id(unit_id)
    if not unit:
        raise ValueError(f"Unit {unit_id} not found")

    estate = Estate.get_by_id(unit.estate_id)
    if not estate:
        raise ValueError(f"Estate {unit.estate_id} not found")

    # Use unit's rate table assignments, fall back to estate if unit has None
    electricity_rate_table_id = (
        unit.electricity_rate_table_id or estate.electricity_rate_table_id
    )
    water_rate_table_id = unit.water_rate_table_id or estate.water_rate_table_id

    # Get rate structures from rate tables
    electricity_structure = electricity_structure or {}
    water_structure = water_structure or {}

    if electricity_rate_table_id:
        electricity_rate_table = RateTable.get_by_id(electricity_rate_table_id)
        if electricity_rate_table and electricity_rate_table.rate_structure:
            electricity_structure = electricity_rate_table.rate_structure

    if water_rate_table_id:
        water_rate_table = RateTable.get_by_id(water_rate_table_id)
        if water_rate_table and water_rate_table.rate_structure:
            water_structure = water_rate_table.rate_structure

    # Use estate markups if not provided
    electricity_markup_percent = (
        electricity_markup_percent or estate.electricity_markup_percentage
    )
    water_markup_percent = water_markup_percent or estate.water_markup_percentage

    return calculate_estate_bill(
        electricity_kwh=electricity_kwh,
        water_kl=water_kl,
        electricity_structure=electricity_structure,
        water_structure=water_structure,
        electricity_markup_percent=electricity_markup_percent,
        water_markup_percent=water_markup_percent,
        service_fee=service_fee,
    )


def calculate_bill_breakdown(
    *,
    consumption: float,
    rate_structure: Dict[str, Any],
    markup_percent: Optional[float] = None,
    service_fee: Optional[float] = None,
) -> Dict[str, Any]:
    """Calculate detailed bill breakdown for a single utility type."""
    base_amount = compute_from_structure(consumption, rate_structure)
    total_amount = apply_markup(base_amount, markup_percent)
    fee = float(service_fee or 0.0)
    final_total = round(total_amount + fee, 2)

    return {
        "consumption": consumption,
        "base_amount": base_amount,
        "markup_percent": markup_percent or 0.0,
        "markup_amount": round(total_amount - base_amount, 2),
        "total_amount": total_amount,
        "service_fee": fee,
        "final_total": final_total,
    }


def get_default_rate_structure(utility_type: str) -> Dict[str, Any]:
    """Get default rate structure from system settings or first active rate table.
    Falls back to hardcoded values if no rate tables exist.

    Args:
        utility_type: 'electricity' or 'water'

    Returns:
        Rate structure dict with 'flat_rate' or 'tiers'
    """
    from ..models import RateTable

    # Try to get a default rate table for this utility type
    rate_table = RateTable.query.filter_by(
        utility_type=utility_type,
        is_active=True
    ).first()

    if rate_table and rate_table.rate_structure:
        return rate_table.rate_structure

    # Fallback to simple flat rates if no rate tables exist
    if utility_type == "electricity":
        return {"flat_rate": 2.50}  # R2.50/kWh
    elif utility_type == "water":
        return {"flat_rate": 15.00}  # R15.00/kL
    else:
        return {"flat_rate": 0.00}


def calculate_consumption_charge(
    consumption: float,
    utility_type: str,
    rate_structure: Optional[Dict[str, Any]] = None,
    markup_percent: Optional[float] = None
) -> float:
    """Calculate charge for consumption, using rate structure or default rates.

    Args:
        consumption: Amount consumed (kWh or kL)
        utility_type: 'electricity' or 'water'
        rate_structure: Optional rate structure dict
        markup_percent: Optional markup percentage

    Returns:
        Total charge amount
    """
    if not rate_structure:
        rate_structure = get_default_rate_structure(utility_type)

    base_amount = compute_from_structure(consumption, rate_structure)
    total_amount = apply_markup(base_amount, markup_percent)

    return total_amount

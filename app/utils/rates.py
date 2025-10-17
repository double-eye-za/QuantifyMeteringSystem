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





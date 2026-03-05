"""Portal meters routes."""
from datetime import datetime, date, timedelta

from flask import render_template, request
from flask_login import current_user
from sqlalchemy import func

from . import portal
from .decorators import portal_login_required
from ...db import db
from ...services.mobile_users import get_user_units
from ...models import Unit, Meter, MeterReading, Estate, RateTable
from ...utils.rates import (
    calculate_consumption_charge,
    compute_hot_water_cost,
    get_default_rate_structure,
)

# Maps meter_type → (utility label, unit of measure, raw unit is liters?)
_UTILITY_META = {
    'electricity': ('Electricity', 'kWh', False),
    'water':       ('Water',       'kL',  True),
    'hot_water':   ('Hot Water',   'kL',  True),
    'solar':       ('Solar',       'kWh', False),
}

_METER_FIELD_MAP = [
    ('electricity_meter_id', 'electricity'),
    ('water_meter_id',       'water'),
    ('hot_water_meter_id',   'hot_water'),
    ('solar_meter_id',       'solar'),
]


def _get_rate_structure_for_meter(unit, estate, utility_type):
    """Resolve rate structure for a meter: unit override → estate → default."""
    rt_id = None
    markup = None

    if utility_type == 'electricity':
        rt_id = getattr(unit, 'electricity_rate_table_id', None) or getattr(estate, 'electricity_rate_table_id', None)
        markup = getattr(estate, 'electricity_markup_percentage', None)
    elif utility_type == 'water':
        rt_id = getattr(unit, 'water_rate_table_id', None) or getattr(estate, 'water_rate_table_id', None)
        markup = getattr(estate, 'water_markup_percentage', None)
    elif utility_type == 'hot_water':
        rt_id = getattr(unit, 'hot_water_rate_table_id', None) or getattr(estate, 'hot_water_rate_table_id', None)
        markup = getattr(estate, 'hot_water_markup_percentage', None)

    structure = None
    if rt_id:
        rt = RateTable.query.get(rt_id)
        if rt and rt.rate_structure:
            import json
            structure = rt.rate_structure if isinstance(rt.rate_structure, dict) else json.loads(rt.rate_structure)

    if not structure:
        structure = get_default_rate_structure(utility_type)

    return structure, float(markup or 0)


def _compute_meter_analytics(meter_id, utility_type, date_from, date_to,
                             rate_structure, markup_percent):
    """Compute consumption aggregates and cost for a meter over a date range."""
    label, uom, is_liters = _UTILITY_META.get(utility_type, ('Unknown', '', False))

    row = (
        db.session.query(
            func.sum(MeterReading.consumption_since_last).label('total'),
            func.count(MeterReading.id).label('readings'),
            func.min(MeterReading.reading_date).label('first_reading'),
            func.max(MeterReading.reading_date).label('last_reading'),
        )
        .filter(
            MeterReading.meter_id == meter_id,
            MeterReading.reading_date >= date_from,
            MeterReading.reading_date <= date_to,
            MeterReading.consumption_since_last.isnot(None),
        )
        .first()
    )

    total_raw = float(row.total or 0)
    reading_count = int(row.readings or 0)

    if reading_count == 0 or total_raw == 0:
        return {
            'has_data': False,
            'total': 0, 'uom': uom, 'readings': 0,
            'avg_day': 0, 'avg_week': 0, 'avg_month': 0,
            'total_cost': 0, 'cost_day': 0, 'cost_week': 0, 'cost_month': 0,
        }

    # Convert liters → kL for water types
    total_display = total_raw / 1000.0 if is_liters else total_raw

    # Days spanned by actual readings
    first_dt = row.first_reading
    last_dt = row.last_reading
    if hasattr(first_dt, 'date'):
        first_dt = first_dt
    if hasattr(last_dt, 'date'):
        last_dt = last_dt
    delta_days = max((last_dt - first_dt).days, 1) if first_dt and last_dt else 1

    avg_day = total_display / delta_days
    avg_week = avg_day * 7
    avg_month = avg_day * 30

    # Cost calculation
    if utility_type == 'hot_water':
        hw_result = compute_hot_water_cost(total_raw, rate_structure, markup_percent)
        total_cost = hw_result['total_cost']
    else:
        total_cost = calculate_consumption_charge(
            total_display, utility_type, rate_structure, markup_percent
        )

    cost_day = total_cost / delta_days if delta_days > 0 else 0
    cost_week = cost_day * 7
    cost_month = cost_day * 30

    return {
        'has_data': True,
        'total': round(total_display, 2),
        'uom': uom,
        'readings': reading_count,
        'avg_day': round(avg_day, 2),
        'avg_week': round(avg_week, 2),
        'avg_month': round(avg_month, 2),
        'total_cost': round(total_cost, 2),
        'cost_day': round(cost_day, 2),
        'cost_week': round(cost_week, 2),
        'cost_month': round(cost_month, 2),
    }


@portal.route('/meters')
@portal_login_required
def portal_meters():
    """All meters across all units the user has access to, with usage analytics."""
    units = get_user_units(current_user.person_id)

    # Parse date range (default: current month start → today)
    today = date.today()
    default_from = date(today.year, today.month, 1)

    date_from_str = request.args.get('date_from', '')
    date_to_str = request.args.get('date_to', '')

    try:
        date_from = datetime.strptime(date_from_str, '%Y-%m-%d') if date_from_str else datetime.combine(default_from, datetime.min.time())
    except ValueError:
        date_from = datetime.combine(default_from, datetime.min.time())

    try:
        date_to = datetime.strptime(date_to_str, '%Y-%m-%d').replace(hour=23, minute=59, second=59) if date_to_str else datetime.combine(today, datetime.max.time())
    except ValueError:
        date_to = datetime.combine(today, datetime.max.time())

    # --- Comparison mode ---
    compare = request.args.get('compare', '') == '1'
    cmp_from = cmp_to = None
    if compare:
        cmp_from_str = request.args.get('compare_from', '')
        cmp_to_str = request.args.get('compare_to', '')
        try:
            cmp_from = datetime.strptime(cmp_from_str, '%Y-%m-%d') if cmp_from_str else None
        except ValueError:
            cmp_from = None
        try:
            cmp_to = datetime.strptime(cmp_to_str, '%Y-%m-%d').replace(hour=23, minute=59, second=59) if cmp_to_str else None
        except ValueError:
            cmp_to = None
        if not cmp_from or not cmp_to:
            compare = False

    all_meters = []
    # Aggregate totals per utility for the summary KPIs
    utility_totals = {}  # utility_type → {total, total_cost, uom}
    compare_totals = {}  # same structure for comparison period

    for unit_info in units:
        unit = Unit.query.get(unit_info['unit_id'])
        if not unit:
            continue
        estate = Estate.query.get(unit.estate_id) if unit.estate_id else None

        for meter_field, utility_type in _METER_FIELD_MAP:
            meter_id = getattr(unit, meter_field, None)
            if not meter_id:
                continue
            meter = Meter.query.get(meter_id)
            if not meter:
                continue

            label, uom, _ = _UTILITY_META.get(utility_type, ('Unknown', '', False))

            # Last reading (all-time, for display)
            last_reading = (
                MeterReading.query
                .filter_by(meter_id=meter.id)
                .order_by(MeterReading.reading_date.desc())
                .first()
            )

            # Analytics for the selected date range
            rate_structure, markup = _get_rate_structure_for_meter(unit, estate, utility_type)
            analytics = _compute_meter_analytics(
                meter.id, utility_type, date_from, date_to,
                rate_structure, markup
            )

            # Comparison analytics
            compare_analytics = None
            if compare:
                compare_analytics = _compute_meter_analytics(
                    meter.id, utility_type, cmp_from, cmp_to,
                    rate_structure, markup
                )

            all_meters.append({
                'id': meter.id,
                'serial_number': meter.serial_number,
                'utility_type': label,
                'utility_key': utility_type,
                'status': meter.communication_status or 'unknown',
                'current_reading': float(last_reading.reading_value) if last_reading else None,
                'last_reading_date': last_reading.reading_date if last_reading else None,
                'unit_id': unit.id,
                'unit_number': unit.unit_number,
                'estate_name': unit_info.get('estate_name', ''),
                'analytics': analytics,
                'compare_analytics': compare_analytics,
            })

            # Accumulate utility-level totals
            if analytics['has_data']:
                if utility_type not in utility_totals:
                    utility_totals[utility_type] = {
                        'label': label, 'uom': uom,
                        'total': 0, 'total_cost': 0,
                    }
                utility_totals[utility_type]['total'] += analytics['total']
                utility_totals[utility_type]['total_cost'] += analytics['total_cost']

            if compare and compare_analytics and compare_analytics['has_data']:
                if utility_type not in compare_totals:
                    compare_totals[utility_type] = {
                        'label': label, 'uom': uom,
                        'total': 0, 'total_cost': 0,
                    }
                compare_totals[utility_type]['total'] += compare_analytics['total']
                compare_totals[utility_type]['total_cost'] += compare_analytics['total_cost']

    # Build summary list (sorted: electricity, water, hot_water, solar)
    utility_order = ['electricity', 'water', 'hot_water', 'solar']
    utility_summary = [
        {**utility_totals[k], 'key': k}
        for k in utility_order
        if k in utility_totals
    ]
    compare_summary = [
        {**compare_totals[k], 'key': k}
        for k in utility_order
        if k in compare_totals
    ] if compare else []

    return render_template(
        'portal/meters.html',
        all_meters=all_meters,
        utility_summary=utility_summary,
        compare_summary=compare_summary,
        date_from=date_from.strftime('%Y-%m-%d'),
        date_to=date_to.strftime('%Y-%m-%d'),
        compare=compare,
        compare_from=cmp_from.strftime('%Y-%m-%d') if cmp_from else '',
        compare_to=cmp_to.strftime('%Y-%m-%d') if cmp_to else '',
    )

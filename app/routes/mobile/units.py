"""Mobile app unit, meter, and wallet endpoints."""
from __future__ import annotations

from flask import jsonify, request
from datetime import datetime, date, timedelta
from sqlalchemy import func

from ...db import db
from ...services.mobile_users import can_access_unit, can_topup_unit
from ...services.meters import get_meter_by_id as svc_get_meter_by_id
from ...utils.feature_flags import is_feature_enabled
from ...utils.rates import (
    calculate_consumption_charge,
    compute_hot_water_cost,
    get_default_rate_structure,
)
from ...models import MobileUser, Unit, Meter, Wallet, MeterReading, Estate, RateTable
from .auth import require_mobile_auth
from . import mobile_api


# Utility metadata: label, unit of measure, raw-unit-is-liters flag
_UTILITY_META = {
    'electricity': ('Electricity', 'kWh', False),
    'water':       ('Water',       'kL',  True),
    'hot_water':   ('Hot Water',   'kL',  True),
    'solar':       ('Solar',       'kWh', False),
}

_METER_FIELDS = [
    ('electricity_meter_id', 'electricity'),
    ('water_meter_id',       'water'),
    ('hot_water_meter_id',   'hot_water'),
    ('solar_meter_id',       'solar'),
]


def _resolve_rate_structure(unit, estate, utility_type):
    """Resolve rate structure for a meter: unit override -> estate -> default."""
    import json as _json
    rt_id = None
    markup = None
    if utility_type == 'electricity':
        rt_id = getattr(unit, 'electricity_rate_table_id', None) or (getattr(estate, 'electricity_rate_table_id', None) if estate else None)
        markup = getattr(estate, 'electricity_markup_percentage', None) if estate else None
    elif utility_type == 'water':
        rt_id = getattr(unit, 'water_rate_table_id', None) or (getattr(estate, 'water_rate_table_id', None) if estate else None)
        markup = getattr(estate, 'water_markup_percentage', None) if estate else None
    elif utility_type == 'hot_water':
        rt_id = getattr(unit, 'hot_water_rate_table_id', None) or (getattr(estate, 'hot_water_rate_table_id', None) if estate else None)
        markup = getattr(estate, 'hot_water_markup_percentage', None) if estate else None

    structure = None
    if rt_id:
        rt = RateTable.query.get(rt_id)
        if rt and rt.rate_structure:
            structure = rt.rate_structure if isinstance(rt.rate_structure, dict) else _json.loads(rt.rate_structure)
    if not structure:
        structure = get_default_rate_structure(utility_type)
    return structure, float(markup or 0)


def _compute_analytics(meter_id, utility_type, date_from, date_to, rate_structure, markup_pct):
    """Compute consumption aggregates and cost for a meter over a date range."""
    label, uom, is_liters = _UTILITY_META.get(utility_type, ('Unknown', '', False))

    row = db.session.query(
        func.sum(MeterReading.consumption_since_last).label('total'),
        func.count(MeterReading.id).label('readings'),
        func.min(MeterReading.reading_date).label('first'),
        func.max(MeterReading.reading_date).label('last'),
    ).filter(
        MeterReading.meter_id == meter_id,
        MeterReading.reading_date >= date_from,
        MeterReading.reading_date <= date_to,
        MeterReading.consumption_since_last.isnot(None),
    ).first()

    total_raw = float(row.total or 0)
    count = int(row.readings or 0)
    if count == 0 or total_raw == 0:
        return None  # no data

    total = total_raw / 1000.0 if is_liters else total_raw
    delta = max((row.last - row.first).days, 1) if row.first and row.last else 1
    avg_day = total / delta

    # Cost
    if utility_type == 'hot_water':
        hw = compute_hot_water_cost(total_raw, rate_structure, markup_pct)
        total_cost = hw['total_cost']
    else:
        total_cost = calculate_consumption_charge(total, utility_type, rate_structure, markup_pct)

    cost_day = total_cost / delta if delta > 0 else 0

    return {
        'total': round(total, 2),
        'uom': uom,
        'avg_day': round(avg_day, 2),
        'avg_week': round(avg_day * 7, 2),
        'avg_month': round(avg_day * 30, 2),
        'total_cost': round(total_cost, 2),
        'cost_day': round(cost_day, 2),
        'cost_week': round(cost_day * 7, 2),
        'cost_month': round(cost_day * 30, 2),
        'readings': count,
    }


@mobile_api.get("/units/<int:unit_id>/meters")
@require_mobile_auth
def get_unit_meters(unit_id: int, mobile_user: MobileUser):
    """
    Get all meters for a specific unit.

    Requires authentication and unit access authorization.

    Response:
        {
            "meters": [
                {
                    "id": 1,
                    "serial_number": "MTR001",
                    "meter_type": "prepaid",
                    "utility_type": "electricity",
                    "current_reading": 1250.5,
                    "last_reading_date": "2024-01-15T10:30:00",
                    "status": "active"
                }
            ]
        }
    """
    # Check if user has access to this unit
    if not can_access_unit(mobile_user.person_id, unit_id):
        return jsonify({
            'error': 'Access denied',
            'message': 'You do not have access to this unit'
        }), 403

    # Get unit to verify it exists
    unit = Unit.query.get(unit_id)
    if not unit:
        return jsonify({
            'error': 'Unit not found',
            'message': f'Unit with ID {unit_id} not found'
        }), 404

    # Get wallet for this unit to include balance information
    wallet = Wallet.query.filter_by(unit_id=unit_id).first()

    # Get all meters for this unit
    # Unit has foreign keys to meters: electricity_meter_id, water_meter_id, solar_meter_id, hot_water_meter_id
    meters = []
    meter_mappings = [
        ('electricity', unit.electricity_meter_id),
        ('water', unit.water_meter_id),
        ('solar', unit.solar_meter_id),
        ('hot_water', unit.hot_water_meter_id),
    ]

    # Unified wallet: all meters share the same available balance
    shared_balance = float(wallet.balance) if wallet and wallet.balance else 0.0

    for utility_type, meter_id in meter_mappings:
        if meter_id:
            meter = Meter.query.get(meter_id)
            if meter:
                # Get cumulative consumption cost for this utility
                utility_spent = 0.0
                if wallet:
                    if utility_type == 'electricity':
                        utility_spent = float(wallet.electricity_balance) if wallet.electricity_balance else 0.0
                    elif utility_type == 'water':
                        utility_spent = float(wallet.water_balance) if wallet.water_balance else 0.0
                    elif utility_type == 'solar':
                        utility_spent = float(wallet.solar_balance) if wallet.solar_balance else 0.0
                    elif utility_type == 'hot_water':
                        utility_spent = float(wallet.hot_water_balance) if wallet.hot_water_balance else 0.0

                meters.append({
                    'id': meter.id,
                    'serial_number': meter.serial_number,
                    'meter_type': meter.meter_type,
                    'utility_type': utility_type,
                    'current_reading': float(meter.last_reading) if meter.last_reading else None,
                    'last_reading_date': meter.last_reading_date.isoformat() if meter.last_reading_date else None,
                    'status': meter.communication_status or 'unknown',
                    'device_eui': meter.device_eui,
                    'lorawan_device_type': meter.lorawan_device_type,
                    'communication_type': meter.communication_type,
                    'is_active': meter.is_active,
                    'balance': shared_balance,  # Unified wallet balance (shared pool)
                    'utility_spent': utility_spent,  # Cumulative consumption cost
                })

    _can_topup = can_topup_unit(mobile_user.person_id, unit_id) if is_feature_enabled('payment_roles') else True

    return jsonify({
        'meters': meters,
        'can_topup': _can_topup,
    }), 200


@mobile_api.get("/meters/<int:meter_id>")
@require_mobile_auth
def get_meter_details(meter_id: int, mobile_user: MobileUser):
    """
    Get detailed information about a specific meter.

    Requires authentication and unit access authorization.

    Response:
        {
            "meter": {
                "id": 1,
                "serial_number": "MTR001",
                "meter_type": "prepaid",
                "utility_type": "electricity",
                "current_reading": 1250.5,
                "last_reading_date": "2024-01-15T10:30:00",
                "status": "active",
                "unit_id": 10,
                "unit_number": "101"
            }
        }
    """
    meter = Meter.query.get(meter_id)
    if not meter:
        return jsonify({
            'error': 'Meter not found',
            'message': f'Meter with ID {meter_id} not found'
        }), 404

    # Find which unit this meter belongs to
    unit = Unit.query.filter(
        (Unit.electricity_meter_id == meter_id) |
        (Unit.water_meter_id == meter_id) |
        (Unit.solar_meter_id == meter_id) |
        (Unit.hot_water_meter_id == meter_id)
    ).first()

    if not unit:
        return jsonify({
            'error': 'Meter not assigned',
            'message': 'This meter is not assigned to any unit'
        }), 404

    # Check if user has access to the meter's unit
    if not can_access_unit(mobile_user.person_id, unit.id):
        return jsonify({
            'error': 'Access denied',
            'message': 'You do not have access to this meter'
        }), 403

    # Determine utility type
    utility_type = 'unknown'
    if unit.electricity_meter_id == meter_id:
        utility_type = 'electricity'
    elif unit.water_meter_id == meter_id:
        utility_type = 'water'
    elif unit.solar_meter_id == meter_id:
        utility_type = 'solar'
    elif unit.hot_water_meter_id == meter_id:
        utility_type = 'hot_water'

    # Unified wallet: shared balance + per-utility consumption cost
    wallet = Wallet.query.filter_by(unit_id=unit.id).first()
    balance = float(wallet.balance) if wallet and wallet.balance else 0.0
    utility_spent = 0.0
    if wallet:
        if utility_type == 'electricity':
            utility_spent = float(wallet.electricity_balance) if wallet.electricity_balance else 0.0
        elif utility_type == 'water':
            utility_spent = float(wallet.water_balance) if wallet.water_balance else 0.0
        elif utility_type == 'solar':
            utility_spent = float(wallet.solar_balance) if wallet.solar_balance else 0.0
        elif utility_type == 'hot_water':
            utility_spent = float(wallet.hot_water_balance) if wallet.hot_water_balance else 0.0

    _can_topup = can_topup_unit(mobile_user.person_id, unit.id) if is_feature_enabled('payment_roles') else True

    return jsonify({
        'meter': {
            'id': meter.id,
            'serial_number': meter.serial_number,
            'meter_type': meter.meter_type,
            'utility_type': utility_type,
            'current_reading': float(meter.last_reading) if meter.last_reading else None,
            'last_reading_date': meter.last_reading_date.isoformat() if meter.last_reading_date else None,
            'status': meter.communication_status or 'unknown',
            'unit_id': unit.id,
            'unit_number': unit.unit_number,
            'device_eui': meter.device_eui,
            'lorawan_device_type': meter.lorawan_device_type,
            'communication_type': meter.communication_type,
            'is_active': meter.is_active,
            'balance': balance,  # Unified wallet balance (shared pool)
            'utility_spent': utility_spent,  # Cumulative consumption cost
            'can_topup': _can_topup,
        }
    }), 200


@mobile_api.get("/meters/<int:meter_id>/readings")
@require_mobile_auth
def get_meter_readings(meter_id: int, mobile_user: MobileUser):
    """
    Get readings for a specific meter.

    Requires authentication and unit access authorization.

    Query parameters:
        - days: Number of days of history (default: 30)
        - limit: Maximum number of readings (default: 100)

    Response:
        {
            "readings": [
                {
                    "id": 1,
                    "reading_value": 1250.5,
                    "reading_date": "2024-01-15T10:30:00",
                    "cost": 125.50,
                    "consumption": 150.5
                }
            ],
            "meter": {
                "id": 1,
                "serial_number": "MTR001"
            }
        }
    """
    meter = Meter.query.get(meter_id)
    if not meter:
        return jsonify({
            'error': 'Meter not found',
            'message': f'Meter with ID {meter_id} not found'
        }), 404

    # Find which unit this meter belongs to
    unit = Unit.query.filter(
        (Unit.electricity_meter_id == meter_id) |
        (Unit.water_meter_id == meter_id) |
        (Unit.solar_meter_id == meter_id) |
        (Unit.hot_water_meter_id == meter_id)
    ).first()

    if not unit:
        return jsonify({
            'error': 'Meter not assigned',
            'message': 'This meter is not assigned to any unit'
        }), 404

    # Check if user has access to the meter's unit
    if not can_access_unit(mobile_user.person_id, unit.id):
        return jsonify({
            'error': 'Access denied',
            'message': 'You do not have access to this meter'
        }), 403

    # Get query parameters
    days = request.args.get('days', default=30, type=int)
    limit = request.args.get('limit', default=100, type=int)

    # Calculate date range
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=days)

    # Determine utility type
    utility_type = 'unknown'
    if unit.electricity_meter_id == meter_id:
        utility_type = 'electricity'
    elif unit.water_meter_id == meter_id:
        utility_type = 'water'
    elif unit.solar_meter_id == meter_id:
        utility_type = 'solar'
    elif unit.hot_water_meter_id == meter_id:
        utility_type = 'hot_water'

    # Get readings
    readings = MeterReading.query.filter(
        MeterReading.meter_id == meter_id,
        MeterReading.reading_date >= start_date,
        MeterReading.reading_date <= end_date
    ).order_by(MeterReading.reading_date.desc()).limit(limit).all()

    return jsonify({
        'readings': [
            {
                'id': r.id,
                'reading_value': float(r.reading_value) if r.reading_value else None,
                'reading_date': r.reading_date.isoformat() if r.reading_date else None,
                'cost': float(r.cost) if r.cost else None,
                'consumption': float(r.consumption) if r.consumption else None,
            }
            for r in readings
        ],
        'meter': {
            'id': meter.id,
            'serial_number': meter.serial_number,
            'utility_type': utility_type
        }
    }), 200


@mobile_api.get("/units/<int:unit_id>/wallet")
@require_mobile_auth
def get_unit_wallet(unit_id: int, mobile_user: MobileUser):
    """
    Get wallet information for a specific unit.

    Requires authentication and unit access authorization.

    Response:
        {
            "wallet": {
                "id": 1,
                "unit_id": 10,
                "balance": 2500.75,
                "status": "active",
                "last_transaction_date": "2024-01-15T10:30:00"
            }
        }
    """
    # Check if user has access to this unit
    if not can_access_unit(mobile_user.person_id, unit_id):
        return jsonify({
            'error': 'Access denied',
            'message': 'You do not have access to this unit'
        }), 403

    # Get unit to verify it exists
    unit = Unit.query.get(unit_id)
    if not unit:
        return jsonify({
            'error': 'Unit not found',
            'message': f'Unit with ID {unit_id} not found'
        }), 404

    # Get wallet
    wallet = Wallet.query.filter_by(unit_id=unit_id).first()
    if not wallet:
        return jsonify({
            'error': 'Wallet not found',
            'message': 'No wallet found for this unit'
        }), 404

    return jsonify({
        'wallet': {
            'id': wallet.id,
            'unit_id': wallet.unit_id,
            'wallet_mode': 'unified',
            'balance': float(wallet.balance) if wallet.balance else 0.0,
            'electricity_balance': float(wallet.electricity_balance) if wallet.electricity_balance else 0.0,
            'water_balance': float(wallet.water_balance) if wallet.water_balance else 0.0,
            'solar_balance': float(wallet.solar_balance) if wallet.solar_balance else 0.0,
            'hot_water_balance': float(wallet.hot_water_balance) if wallet.hot_water_balance else 0.0,
            'is_suspended': wallet.is_suspended,
            'suspension_reason': wallet.suspension_reason,
            'last_topup_date': wallet.last_topup_date.isoformat() if wallet.last_topup_date else None,
            'low_balance_threshold': float(wallet.low_balance_threshold) if wallet.low_balance_threshold else 50.0,
            'low_balance_alert_type': wallet.low_balance_alert_type or 'fixed',
            'low_balance_days_threshold': wallet.low_balance_days_threshold or 3,
            'can_topup': can_topup_unit(mobile_user.person_id, unit_id) if is_feature_enabled('payment_roles') else True,
        }
    }), 200


@mobile_api.get("/units/<int:unit_id>/transactions")
@require_mobile_auth
def get_unit_transactions(unit_id: int, mobile_user: MobileUser):
    """
    Get transactions for a specific unit's wallet.

    Requires authentication and unit access authorization.

    Query parameters:
        - days: Number of days of history (default: 30)
        - limit: Maximum number of transactions (default: 50)
        - type: Filter by transaction type (optional)

    Response:
        {
            "transactions": [
                {
                    "id": 1,
                    "transaction_type": "credit",
                    "amount": 500.00,
                    "description": "Wallet top-up",
                    "transaction_date": "2024-01-15T10:30:00",
                    "balance_after": 2500.75
                }
            ]
        }
    """
    # Check if user has access to this unit
    if not can_access_unit(mobile_user.person_id, unit_id):
        return jsonify({
            'error': 'Access denied',
            'message': 'You do not have access to this unit'
        }), 403

    # Get wallet
    wallet = Wallet.query.filter_by(unit_id=unit_id).first()
    if not wallet:
        return jsonify({
            'error': 'Wallet not found',
            'message': 'No wallet found for this unit'
        }), 404

    # Get query parameters
    days = request.args.get('days', default=30, type=int)
    limit = request.args.get('limit', default=50, type=int)
    transaction_type = request.args.get('type')

    # Calculate date range
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=days)

    # Build query
    from ...models import Transaction
    query = Transaction.query.filter(
        Transaction.wallet_id == wallet.id,
        Transaction.created_at >= start_date,
        Transaction.created_at <= end_date
    )

    # Filter by type if provided
    if transaction_type:
        query = query.filter(Transaction.transaction_type == transaction_type)

    # Get transactions
    transactions = query.order_by(Transaction.created_at.desc()).limit(limit).all()

    return jsonify({
        'transactions': [
            {
                'id': t.id,
                'transaction_type': t.transaction_type,
                'amount': float(t.amount) if t.amount else 0.0,
                'description': t.description,
                'transaction_date': t.created_at.isoformat() if t.created_at else None,
                'balance_after': float(t.balance_after) if t.balance_after else None,
            }
            for t in transactions
        ]
    }), 200


@mobile_api.put("/units/<int:unit_id>/wallet/threshold")
@require_mobile_auth
def update_wallet_threshold(unit_id: int, mobile_user: MobileUser):
    """
    Update wallet alert threshold settings for a specific unit.

    Requires authentication and unit access authorization.

    Request body:
        {
            "low_balance_threshold": 100.00,
            "low_balance_alert_type": "fixed",  // "fixed" or "days"
            "low_balance_days_threshold": 3
        }

    Response:
        {
            "success": true,
            "message": "Threshold updated successfully",
            "data": {
                "low_balance_threshold": 100.00,
                "low_balance_alert_type": "fixed",
                "low_balance_days_threshold": 3
            }
        }
    """
    # Check if user has access to this unit
    if not can_access_unit(mobile_user.person_id, unit_id):
        return jsonify({
            'success': False,
            'error': 'Access denied',
            'message': 'You do not have access to this unit'
        }), 403

    # Get wallet
    wallet = Wallet.query.filter_by(unit_id=unit_id).first()
    if not wallet:
        return jsonify({
            'success': False,
            'error': 'Wallet not found',
            'message': 'No wallet found for this unit'
        }), 404

    # Get request data
    data = request.get_json() or {}

    # Update threshold settings
    if 'low_balance_threshold' in data:
        threshold = data['low_balance_threshold']
        if threshold is not None and threshold >= 0:
            wallet.low_balance_threshold = float(threshold)

    if 'low_balance_alert_type' in data:
        alert_type = data['low_balance_alert_type']
        if alert_type in ['fixed', 'days']:
            wallet.low_balance_alert_type = alert_type

    if 'low_balance_days_threshold' in data:
        days = data['low_balance_days_threshold']
        if days is not None and days >= 0:
            wallet.low_balance_days_threshold = int(days)

    db.session.commit()

    return jsonify({
        'success': True,
        'message': 'Threshold updated successfully',
        'data': {
            'low_balance_threshold': float(wallet.low_balance_threshold) if wallet.low_balance_threshold else 50.0,
            'low_balance_alert_type': wallet.low_balance_alert_type or 'fixed',
            'low_balance_days_threshold': wallet.low_balance_days_threshold or 3,
        }
    }), 200


@mobile_api.get("/units/<int:unit_id>/consumption-analytics")
@require_mobile_auth
def get_consumption_analytics(unit_id: int, mobile_user: MobileUser):
    """
    Get consumption analytics for all meters on a unit.

    Query parameters:
        - days: Number of days to analyse (default: 30)

    Response:
        {
            "period_days": 30,
            "date_from": "2026-02-07",
            "date_to": "2026-03-09",
            "meters": [
                {
                    "meter_id": 1,
                    "serial_number": "MTR001",
                    "utility_type": "electricity",
                    "total": 40.0,
                    "uom": "kWh",
                    "avg_day": 1.33,
                    "avg_week": 9.33,
                    "avg_month": 40.0,
                    "total_cost": 100.0,
                    "cost_day": 3.33,
                    "cost_week": 23.33,
                    "cost_month": 100.0,
                    "readings": 3101
                }
            ]
        }
    """
    if not can_access_unit(mobile_user.person_id, unit_id):
        return jsonify({'error': 'Access denied', 'message': 'You do not have access to this unit'}), 403

    unit = Unit.query.get(unit_id)
    if not unit:
        return jsonify({'error': 'Unit not found', 'message': f'Unit with ID {unit_id} not found'}), 404

    days = request.args.get('days', default=30, type=int)
    today = date.today()
    date_to = datetime.combine(today, datetime.max.time())
    date_from = datetime.combine(today - timedelta(days=days), datetime.min.time())

    estate = Estate.query.get(unit.estate_id) if unit.estate_id else None

    results = []
    for meter_field, utility_type in _METER_FIELDS:
        meter_id = getattr(unit, meter_field, None)
        if not meter_id:
            continue
        meter = Meter.query.get(meter_id)
        if not meter:
            continue

        rate_structure, markup = _resolve_rate_structure(unit, estate, utility_type)
        analytics = _compute_analytics(meter_id, utility_type, date_from, date_to, rate_structure, markup)

        if analytics:
            results.append({
                'meter_id': meter.id,
                'serial_number': meter.serial_number,
                'utility_type': utility_type,
                **analytics,
            })

    return jsonify({
        'period_days': days,
        'date_from': date_from.strftime('%Y-%m-%d'),
        'date_to': date_to.strftime('%Y-%m-%d'),
        'meters': results,
    }), 200

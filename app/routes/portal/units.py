"""Portal units routes."""
from flask import render_template, abort
from flask_login import current_user
from . import portal
from .decorators import portal_login_required
from ...services.mobile_users import get_user_units, can_access_unit
from ...models import Unit, Wallet, Meter, MeterReading
from ...db import db


@portal.route('/units')
@portal_login_required
def portal_units():
    """List all units the user owns or rents."""
    units = get_user_units(current_user.person_id)

    # Enrich with wallet and meter data
    for unit_data in units:
        unit = Unit.query.get(unit_data['unit_id'])
        if unit:
            wallet = Wallet.query.filter_by(unit_id=unit.id).first()
            unit_data['wallet_balance'] = float(wallet.balance) if wallet else 0

            meters = []
            for meter_field, utility in [('electricity_meter_id', 'Electricity'), ('water_meter_id', 'Water'), ('hot_water_meter_id', 'Hot Water'), ('solar_meter_id', 'Solar')]:
                meter_id = getattr(unit, meter_field, None)
                if meter_id:
                    meter = Meter.query.get(meter_id)
                    if meter:
                        meters.append({
                            'id': meter.id,
                            'serial_number': meter.serial_number,
                            'utility_type': utility,
                            'status': meter.communication_status or 'unknown',
                        })
            unit_data['meters'] = meters

    return render_template('portal/units.html', units=units)


@portal.route('/units/<int:unit_id>')
@portal_login_required
def portal_unit_detail(unit_id):
    """Unit detail page with meters, wallet, and recent activity."""
    if not can_access_unit(current_user.person_id, unit_id):
        abort(403)

    unit = Unit.query.get_or_404(unit_id)
    wallet = Wallet.query.filter_by(unit_id=unit.id).first()

    meters = []
    for meter_field, utility in [('electricity_meter_id', 'Electricity'), ('water_meter_id', 'Water'), ('hot_water_meter_id', 'Hot Water'), ('solar_meter_id', 'Solar')]:
        meter_id = getattr(unit, meter_field, None)
        if meter_id:
            meter = Meter.query.get(meter_id)
            if meter:
                last_reading = MeterReading.query.filter_by(meter_id=meter.id).order_by(MeterReading.reading_date.desc()).first()
                meters.append({
                    'id': meter.id,
                    'serial_number': meter.serial_number,
                    'utility_type': utility,
                    'status': meter.communication_status or 'unknown',
                    'current_reading': float(last_reading.reading_value) if last_reading else None,
                    'last_reading_date': last_reading.reading_date if last_reading else None,
                })

    return render_template(
        'portal/unit_detail.html',
        unit=unit,
        wallet=wallet,
        meters=meters,
    )

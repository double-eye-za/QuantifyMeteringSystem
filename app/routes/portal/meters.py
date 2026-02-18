"""Portal meters routes."""
from flask import render_template
from flask_login import current_user
from . import portal
from .decorators import portal_login_required
from ...services.mobile_users import get_user_units
from ...models import Unit, Meter, MeterReading


@portal.route('/meters')
@portal_login_required
def portal_meters():
    """All meters across all units the user has access to."""
    units = get_user_units(current_user.person_id)

    all_meters = []
    for unit_info in units:
        unit = Unit.query.get(unit_info['unit_id'])
        if not unit:
            continue

        for meter_field, utility in [
            ('electricity_meter_id', 'Electricity'),
            ('water_meter_id', 'Water'),
            ('hot_water_meter_id', 'Hot Water'),
            ('solar_meter_id', 'Solar'),
        ]:
            meter_id = getattr(unit, meter_field, None)
            if not meter_id:
                continue
            meter = Meter.query.get(meter_id)
            if not meter:
                continue

            last_reading = (
                MeterReading.query
                .filter_by(meter_id=meter.id)
                .order_by(MeterReading.reading_date.desc())
                .first()
            )

            all_meters.append({
                'id': meter.id,
                'serial_number': meter.serial_number,
                'utility_type': utility,
                'status': meter.communication_status or 'unknown',
                'current_reading': float(last_reading.reading_value) if last_reading else None,
                'last_reading_date': last_reading.reading_date if last_reading else None,
                'unit_id': unit.id,
                'unit_number': unit.unit_number,
                'estate_name': unit_info.get('estate_name', ''),
            })

    return render_template('portal/meters.html', all_meters=all_meters)

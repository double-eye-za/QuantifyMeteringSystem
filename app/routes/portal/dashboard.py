"""Portal dashboard route."""
from flask import render_template
from flask_login import current_user
from . import portal
from .decorators import portal_login_required
from ...services.mobile_users import get_user_units
from ...models import Wallet, Meter, Unit, Notification
from ...db import db


@portal.route('/dashboard')
@portal_login_required
def portal_dashboard():
    """Portal home — summary of user's units, balances, and recent alerts."""
    units = get_user_units(current_user.person_id)

    # Enrich units with wallet balances and meter counts
    for unit_data in units:
        unit = Unit.query.get(unit_data['unit_id'])
        if unit:
            wallet = Wallet.query.filter_by(unit_id=unit.id).first()
            unit_data['wallet'] = {
                'balance': float(wallet.balance) if wallet else 0,
                'electricity_balance': float(wallet.electricity_balance) if wallet else 0,
                'water_balance': float(wallet.water_balance) if wallet else 0,
                'solar_balance': float(wallet.solar_balance) if wallet else 0,
                'hot_water_balance': float(wallet.hot_water_balance) if wallet else 0,
            } if wallet else None

            # Count active meters
            meter_count = 0
            for meter_field in ['electricity_meter_id', 'water_meter_id', 'hot_water_meter_id', 'solar_meter_id']:
                if getattr(unit, meter_field, None):
                    meter_count += 1
            unit_data['meter_count'] = meter_count

    # Recent notifications (Notification uses recipient_type + recipient_id)
    recent_notifications = (
        Notification.query
        .filter_by(recipient_type='resident', recipient_id=current_user.person_id)
        .order_by(Notification.created_at.desc())
        .limit(5)
        .all()
    )

    person = current_user.person

    return render_template(
        'portal/dashboard.html',
        units=units,
        person=person,
        recent_notifications=recent_notifications,
    )

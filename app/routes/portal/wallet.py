"""Portal wallet routes."""
from flask import render_template, request, abort
from flask_login import current_user
from . import portal
from .decorators import portal_login_required
from ...services.mobile_users import get_user_units, can_access_unit
from ...models import Unit, Wallet, Transaction
from ...db import db
from datetime import datetime, timedelta


@portal.route('/wallet')
@portal_login_required
def portal_wallet():
    """Wallet overview — balances for each unit."""
    units = get_user_units(current_user.person_id)

    wallet_data = []
    for unit_info in units:
        unit = Unit.query.get(unit_info['unit_id'])
        if unit:
            wallet = Wallet.query.filter_by(unit_id=unit.id).first()
            if wallet:
                wallet_data.append({
                    'unit': unit_info,
                    'wallet': wallet,
                })

    return render_template('portal/wallet.html', wallet_data=wallet_data)


@portal.route('/wallet/<int:unit_id>/transactions')
@portal_login_required
def portal_wallet_transactions(unit_id):
    """Transaction history for a specific unit's wallet."""
    if not can_access_unit(current_user.person_id, unit_id):
        abort(403)

    unit = Unit.query.get_or_404(unit_id)
    wallet = Wallet.query.filter_by(unit_id=unit.id).first()

    # Filter params
    days = request.args.get('days', 30, type=int)
    txn_type = request.args.get('type', None)
    page = request.args.get('page', 1, type=int)
    per_page = 20

    since = datetime.utcnow() - timedelta(days=days)

    query = Transaction.query.filter(
        Transaction.wallet_id == wallet.id,
        Transaction.initiated_at >= since,
    )
    if txn_type:
        query = query.filter(Transaction.transaction_type == txn_type)

    query = query.order_by(Transaction.initiated_at.desc())
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)

    return render_template(
        'portal/wallet_transactions.html',
        unit=unit,
        wallet=wallet,
        transactions=pagination.items,
        pagination=pagination,
        days=days,
        txn_type=txn_type,
    )

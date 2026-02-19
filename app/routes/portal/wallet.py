"""Portal wallet routes."""
import time
from collections import OrderedDict

from flask import render_template, request, abort, redirect, url_for, current_app, flash
from flask_login import current_user
from . import portal
from .decorators import portal_login_required
from ...services.mobile_users import get_user_units, can_access_unit
from ...services.transactions import create_transaction as svc_create_transaction
from ...models import Unit, Wallet, Transaction
from ...utils.payfast import generate_signature
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


# ---------------------------------------------------------------------------
# Top-up flow (PayFast redirect)
# ---------------------------------------------------------------------------

UTILITY_TYPES = ('electricity', 'water', 'solar', 'hot_water')
MIN_TOPUP = 10
MAX_TOPUP = 50_000


@portal.route('/wallet/<int:unit_id>/topup', methods=['GET'])
@portal_login_required
def portal_wallet_topup(unit_id):
    """Show the top-up form (amount + utility picker)."""
    if not can_access_unit(current_user.person_id, unit_id):
        abort(403)

    unit = Unit.query.get_or_404(unit_id)
    wallet = Wallet.query.filter_by(unit_id=unit.id).first()
    if not wallet:
        abort(404)

    return render_template(
        'portal/wallet_topup.html',
        unit=unit,
        wallet=wallet,
    )


@portal.route('/wallet/<int:unit_id>/topup', methods=['POST'])
@portal_login_required
def portal_wallet_topup_post(unit_id):
    """Create a pending transaction and redirect the user to PayFast."""
    if not can_access_unit(current_user.person_id, unit_id):
        abort(403)

    unit = Unit.query.get_or_404(unit_id)
    wallet = Wallet.query.filter_by(unit_id=unit.id).first()
    if not wallet:
        abort(404)

    # Validate inputs
    try:
        amount = float(request.form.get('amount', 0))
    except (ValueError, TypeError):
        flash('Invalid amount.', 'error')
        return redirect(url_for('portal.portal_wallet_topup', unit_id=unit_id))

    if amount < MIN_TOPUP or amount > MAX_TOPUP:
        flash(f'Amount must be between R{MIN_TOPUP} and R{MAX_TOPUP:,}.', 'error')
        return redirect(url_for('portal.portal_wallet_topup', unit_id=unit_id))

    # Generate unique payment reference (PP = Portal Payment)
    m_payment_id = f"PP{int(time.time() * 1000)}"

    # Unified wallet: top-up goes to the shared balance pool, no utility type needed
    txn = svc_create_transaction(
        wallet_id=wallet.id,
        transaction_type='topup',
        amount=amount,
        reference=m_payment_id,
        payment_method='card',
        metadata={'source': 'portal'},
    )

    # Store PayFast gateway info on the transaction
    txn.payment_gateway = 'payfast'
    db.session.commit()

    # Build PayFast form data — field order is CRITICAL for signature.
    # PayFast requires: merchant → buyer → transaction → options
    person = current_user.person
    return_url = url_for('portal.portal_payment_complete', _external=True)
    cancel_url = url_for('portal.portal_payment_cancelled', unit_id=unit_id, _external=True)
    notify_url = url_for('payfast.payfast_itn', _external=True)

    # Use a list of tuples to guarantee insertion order
    pf_fields = [
        # 1. Merchant details
        ('merchant_id', current_app.config['PAYFAST_MERCHANT_ID']),
        ('merchant_key', current_app.config['PAYFAST_MERCHANT_KEY']),
        ('return_url', return_url),
        ('cancel_url', cancel_url),
        ('notify_url', notify_url),
    ]

    # 2. Buyer details (must come before transaction fields)
    if person:
        if person.first_name:
            pf_fields.append(('name_first', person.first_name))
        if person.last_name:
            pf_fields.append(('name_last', person.last_name))
        if person.email:
            pf_fields.append(('email_address', person.email))

    # 3. Transaction details
    pf_fields.extend([
        ('m_payment_id', m_payment_id),
        ('amount', f"{amount:.2f}"),
        ('item_name', 'Wallet Top-up'),
        ('item_description', f"Top-up for unit {unit.unit_number or unit.id}"),
    ])

    # 4. Payment method (optional — if blank, PayFast shows all methods)
    pf_payment_method = request.form.get('payment_method', '')
    if pf_payment_method in ('cc', 'eft', 'dc'):
        pf_fields.append(('payment_method', pf_payment_method))

    # Convert to ordered dict for guaranteed field order in signature
    pf_data = OrderedDict(pf_fields)

    # Generate signature
    passphrase = current_app.config.get('PAYFAST_PASSPHRASE')
    signature = generate_signature(pf_data, passphrase)
    pf_data['signature'] = signature

    process_url = current_app.config['PAYFAST_PROCESS_URL']

    return render_template(
        'portal/payfast_redirect.html',
        pf_data=pf_data,
        process_url=process_url,
    )


@portal.route('/wallet/payment-complete')
@portal_login_required
def portal_payment_complete():
    """Success landing page after PayFast payment."""
    # Find the most recent pending PayFast transaction for this user's wallets
    pending_txn = None
    is_sandbox = current_app.config.get('PAYFAST_SANDBOX', False)

    if is_sandbox:
        units = get_user_units(current_user.person_id)
        wallet_ids = []
        for unit_info in units:
            w = Wallet.query.filter_by(unit_id=unit_info['unit_id']).first()
            if w:
                wallet_ids.append(w.id)

        if wallet_ids:
            pending_txn = Transaction.query.filter(
                Transaction.wallet_id.in_(wallet_ids),
                Transaction.status == 'pending',
                Transaction.payment_gateway == 'payfast',
            ).order_by(Transaction.created_at.desc()).first()

    return render_template(
        'portal/payment_complete.html',
        pending_txn=pending_txn,
        is_sandbox=is_sandbox,
    )


@portal.route('/wallet/payment-cancelled')
@portal_login_required
def portal_payment_cancelled():
    """Cancellation page — user backed out of PayFast."""
    unit_id = request.args.get('unit_id', type=int)

    # Mark any matching pending transaction as failed
    if unit_id:
        unit = Unit.query.get(unit_id)
        if unit:
            wallet = Wallet.query.filter_by(unit_id=unit.id).first()
            if wallet:
                pending = Transaction.query.filter_by(
                    wallet_id=wallet.id,
                    status='pending',
                    payment_gateway='payfast',
                ).order_by(Transaction.created_at.desc()).first()
                if pending:
                    pending.status = 'failed'
                    pending.payment_gateway_status = 'CANCELLED'
                    db.session.commit()

    return render_template('portal/payment_cancelled.html', unit_id=unit_id)

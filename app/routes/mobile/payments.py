"""Mobile payment routes — top-up initiation, status polling, and PayFast ITN redirect."""
from __future__ import annotations

import logging
import time

from flask import jsonify, redirect, request, url_for, current_app

from ...db import db
from ...models import MobileUser, Unit, Wallet, Transaction
from ...services.mobile_users import can_access_unit
from ...services.transactions import create_transaction as svc_create_transaction
from .auth import require_mobile_auth
from . import mobile_api

logger = logging.getLogger(__name__)

UTILITY_TYPES = ('electricity', 'water', 'solar', 'hot_water')
MIN_TOPUP = 10
MAX_TOPUP = 50_000


# ---------------------------------------------------------------------------
# 1. Initiate top-up — create pending transaction, return PayFast config
# ---------------------------------------------------------------------------

@mobile_api.route('/units/<int:unit_id>/topup', methods=['POST'])
@require_mobile_auth
def mobile_initiate_topup(unit_id: int, mobile_user: MobileUser):
    """Create a pending transaction and return PayFast payment data.

    The Flutter app uses this data to open the PayFast payment widget.
    Mirrors the portal's ``portal_wallet_topup_post`` flow.

    Request JSON::

        {
            "amount": 100.00,
            "utility_type": "electricity"
        }

    Response JSON::

        {
            "transaction_id": 123,
            "m_payment_id": "MP1707123456789",
            "payfast_data": { ... },
            "passphrase": "...",
            "sandbox": true,
            "process_url": "https://sandbox.payfast.co.za/eng/process",
            "onsite_activation_url": "https://..."
        }
    """
    # --- Access control ---
    if not can_access_unit(mobile_user.person_id, unit_id):
        return jsonify({'error': 'Access denied', 'message': 'You do not have access to this unit'}), 403

    unit = Unit.query.get(unit_id)
    if not unit:
        return jsonify({'error': 'Unit not found', 'message': f'Unit with ID {unit_id} not found'}), 404

    wallet = Wallet.query.filter_by(unit_id=unit.id).first()
    if not wallet:
        return jsonify({'error': 'Wallet not found', 'message': 'No wallet found for this unit'}), 404

    # --- Parse and validate input ---
    data = request.get_json(force=True) or {}

    try:
        amount = float(data.get('amount', 0))
    except (ValueError, TypeError):
        return jsonify({'error': 'Invalid amount', 'message': 'Amount must be a number'}), 400

    utility_type = data.get('utility_type', 'electricity')
    if utility_type not in UTILITY_TYPES:
        return jsonify({
            'error': 'Invalid utility type',
            'message': f'utility_type must be one of: {", ".join(UTILITY_TYPES)}',
        }), 400

    if amount < MIN_TOPUP or amount > MAX_TOPUP:
        return jsonify({
            'error': 'Invalid amount',
            'message': f'Amount must be between R{MIN_TOPUP} and R{MAX_TOPUP:,}',
        }), 400

    # --- Resolve meter_id for the requested utility ---
    meter_id = None
    if utility_type == 'electricity':
        meter_id = unit.electricity_meter_id
    elif utility_type == 'water':
        meter_id = unit.water_meter_id
    elif utility_type == 'solar':
        meter_id = unit.solar_meter_id
    elif utility_type == 'hot_water':
        meter_id = unit.hot_water_meter_id

    # --- Generate unique payment reference (MP = Mobile Payment) ---
    m_payment_id = f"MP{int(time.time() * 1000)}"

    # --- Create pending transaction (same service as portal) ---
    txn = svc_create_transaction(
        wallet_id=wallet.id,
        transaction_type='topup',
        amount=amount,
        reference=m_payment_id,
        payment_method='card',
        metadata={'utility_type': utility_type, 'source': 'mobile'},
        meter_id=meter_id,
    )

    # Store PayFast gateway info
    txn.payment_gateway = 'payfast'
    db.session.commit()

    # --- Build PayFast data for the onsite payment flow ---
    # The Flutter PayFast widget regenerates signatures itself using alphabetical
    # key sorting and Uri.encodeComponent encoding.
    # IMPORTANT: notify_url MUST be included so PayFast sends the ITN webhook
    # to complete the transaction and credit the wallet.
    # return_url and cancel_url are NOT needed — the Flutter widget handles
    # navigation callbacks directly via onPaymentCompleted/onPaymentCancelled.
    person = mobile_user.person

    # Build notify_url — must be publicly reachable by PayFast's servers.
    # url_for(_external=True) may produce http://localhost:5000/... when
    # SERVER_NAME is not configured, so prefer an explicit base URL.
    payfast_notify_base = current_app.config.get('PAYFAST_NOTIFY_BASE_URL', '')
    if payfast_notify_base:
        notify_url = f"{payfast_notify_base.rstrip('/')}/api/payfast/notify"
    else:
        notify_url = url_for('payfast.payfast_itn', _external=True)

    logger.info("notify_url = %s", notify_url)

    pf_data = {
        'merchant_id': current_app.config['PAYFAST_MERCHANT_ID'],
        'merchant_key': current_app.config['PAYFAST_MERCHANT_KEY'],
        'notify_url': notify_url,
    }

    # Buyer details
    # NOTE: The PayFast Flutter package encodes spaces as %20 (Uri.encodeComponent)
    # but PayFast validates signatures with spaces as + (quote_plus). To avoid
    # signature mismatch, ensure NO spaces in any field values. Names are split
    # to first word only as a safety measure for compound names.
    if person:
        if person.first_name:
            pf_data['name_first'] = person.first_name.split()[0]
        if person.last_name:
            pf_data['name_last'] = person.last_name.split()[0]
        if person.email:
            pf_data['email_address'] = person.email

    # Transaction details — item_name MUST be one word with no spaces
    # (see: https://github.com/youngcet/payfast/issues/14)
    pf_data['m_payment_id'] = m_payment_id
    pf_data['amount'] = f"{amount:.2f}"
    pf_data['item_name'] = f"{utility_type.replace('_', '').capitalize()}Topup"

    # NOTE: We do NOT generate a signature here. The PayFast Flutter package
    # regenerates the signature itself (using alphabetical key sorting and
    # the passphrase). Including a pre-computed signature would be ignored.
    passphrase = current_app.config.get('PAYFAST_PASSPHRASE')

    is_sandbox = current_app.config.get('PAYFAST_SANDBOX', True)
    process_url = current_app.config['PAYFAST_PROCESS_URL']

    # Onsite activation URL — sandbox uses a community-hosted script
    if is_sandbox:
        onsite_activation_url = 'https://youngcet.github.io/sandbox_payfast_onsite_payments/'
    else:
        onsite_activation_url = 'https://www.payfast.co.za/onsite/engine.js'

    # --- DEBUG: Log exact data being sent to Flutter ---
    logger.info("="*60)
    logger.info("PAYFAST MOBILE TOP-UP DEBUG")
    logger.info("="*60)
    logger.info("unit=%s amount=%.2f utility=%s ref=%s txn_id=%s",
                unit_id, amount, utility_type, m_payment_id, txn.id)
    logger.info("payfast_data keys: %s", list(pf_data.keys()))
    for k, v in pf_data.items():
        logger.info("  pf_data[%s] = %r (type=%s, len=%d)",
                     k, v, type(v).__name__, len(str(v)))
    logger.info("passphrase = %r (len=%d)", passphrase, len(passphrase) if passphrase else 0)
    logger.info("sandbox = %s", is_sandbox)
    logger.info("process_url = %s", process_url)
    logger.info("onsite_activation_url = %s", onsite_activation_url)

    # Also compute what the Flutter widget WOULD compute for signature
    # so we can compare it with what PayFast expects
    import hashlib
    import urllib.parse as _urlparse
    debug_data = dict(pf_data)
    debug_data['passphrase'] = passphrase or ''
    # Sort alphabetically (same as Flutter widget _generateSignature)
    sorted_items = sorted(debug_data.items(), key=lambda x: x[0])
    # Build param string with Uri.encodeComponent-style encoding (%20 for spaces)
    flutter_params = '&'.join(
        f"{k}={_urlparse.quote(str(v), safe='')}"
        for k, v in sorted_items
    )
    flutter_sig = hashlib.md5(flutter_params.encode()).hexdigest()
    logger.info("Flutter-style param string: %s", flutter_params)
    logger.info("Flutter-style signature: %s", flutter_sig)

    # Build param string with quote_plus-style encoding (+ for spaces)
    payfast_params = '&'.join(
        f"{k}={_urlparse.quote_plus(str(v))}"
        for k, v in sorted_items
    )
    payfast_sig = hashlib.md5(payfast_params.encode()).hexdigest()
    logger.info("PayFast-style param string: %s", payfast_params)
    logger.info("PayFast-style signature: %s", payfast_sig)
    logger.info("Signatures match: %s", flutter_sig == payfast_sig)
    logger.info("="*60)

    return jsonify({
        'transaction_id': txn.id,
        'm_payment_id': m_payment_id,
        'payfast_data': pf_data,
        'passphrase': passphrase or '',
        'sandbox': is_sandbox,
        'process_url': process_url,
        'notify_url': notify_url,
        'onsite_activation_url': onsite_activation_url,
    }), 201


# ---------------------------------------------------------------------------
# 2. Payment status — poll after PayFast returns
# ---------------------------------------------------------------------------

@mobile_api.route('/units/<int:unit_id>/topup/<int:transaction_id>/status', methods=['GET'])
@require_mobile_auth
def mobile_payment_status(unit_id: int, transaction_id: int, mobile_user: MobileUser):
    """Check payment status for a specific transaction.

    The Flutter app polls this after PayFast redirects back, to verify
    the ITN webhook has processed the payment.

    Response JSON::

        {
            "status": "completed" | "pending" | "failed",
            "amount": 100.00,
            "completed_at": "2024-01-15T10:30:00"
        }
    """
    # --- Access control ---
    if not can_access_unit(mobile_user.person_id, unit_id):
        return jsonify({'error': 'Access denied', 'message': 'You do not have access to this unit'}), 403

    # --- Look up transaction ---
    txn = Transaction.query.get(transaction_id)
    if not txn:
        return jsonify({'error': 'Transaction not found'}), 404

    # Verify the transaction belongs to a wallet for the requested unit
    wallet = Wallet.query.filter_by(unit_id=unit_id).first()
    if not wallet or txn.wallet_id != wallet.id:
        return jsonify({'error': 'Transaction does not belong to this unit'}), 403

    return jsonify({
        'status': txn.status,
        'amount': float(txn.amount) if txn.amount else 0.0,
        'completed_at': txn.completed_at.isoformat() if txn.completed_at else None,
        'transaction_number': txn.transaction_number,
    }), 200


# ---------------------------------------------------------------------------
# 2b. Sandbox confirm — manually complete a pending transaction (sandbox only)
# ---------------------------------------------------------------------------

@mobile_api.route('/units/<int:unit_id>/topup/<int:transaction_id>/confirm', methods=['POST'])
@require_mobile_auth
def mobile_sandbox_confirm(unit_id: int, transaction_id: int, mobile_user: MobileUser):
    """Manually confirm a pending transaction in sandbox mode.

    The PayFast sandbox may not always deliver ITN webhooks (especially
    when the server is behind NAT / notify_url is unreachable).  The
    Flutter app calls this as a fallback after the PayFast widget reports
    ``onPaymentCompleted`` but the transaction stays pending.

    Disabled in production (PAYFAST_SANDBOX=false).
    """
    if not current_app.config.get('PAYFAST_SANDBOX', False):
        return jsonify({'error': 'Only available in sandbox mode'}), 403

    # --- Access control ---
    if not can_access_unit(mobile_user.person_id, unit_id):
        return jsonify({'error': 'Access denied'}), 403

    txn = Transaction.query.get(transaction_id)
    if not txn:
        return jsonify({'error': 'Transaction not found'}), 404

    # Verify the transaction belongs to this unit's wallet
    wallet = Wallet.query.filter_by(unit_id=unit_id).first()
    if not wallet or txn.wallet_id != wallet.id:
        return jsonify({'error': 'Transaction does not belong to this unit'}), 403

    if txn.status == 'completed':
        return jsonify({'status': 'completed', 'message': 'Already completed'}), 200

    if txn.status not in ('pending', 'processing'):
        return jsonify({'error': f'Transaction is {txn.status}, cannot confirm'}), 400

    # Credit the wallet using the shared helper from the payfast module
    try:
        from ..payfast import _complete_transaction
        utility_type = _complete_transaction(txn)
    except (ImportError, ValueError):
        # Fallback: do it directly
        from ...services.wallet import credit_wallet
        from datetime import datetime
        utility_type = (txn.metadata or {}).get('utility_type', 'electricity')
        credit_wallet(wallet, float(txn.amount), utility_type)
        txn.status = 'completed'
        txn.completed_at = datetime.utcnow()

    txn.payment_gateway = 'payfast'
    txn.payment_gateway_status = 'COMPLETE'
    txn.payment_gateway_ref = 'SANDBOX-MOBILE-CONFIRM'
    db.session.commit()

    logger.info("Mobile sandbox confirm: txn=%s amount=%.2f utility=%s",
                txn.id, float(txn.amount), utility_type)

    return jsonify({
        'status': 'completed',
        'message': 'Transaction confirmed (sandbox)',
        'transaction_id': txn.id,
        'amount': float(txn.amount),
    }), 200


# ---------------------------------------------------------------------------
# 3. Return / Cancel URL stubs (PayFast requires valid URLs)
# ---------------------------------------------------------------------------

@mobile_api.route('/payment/success', methods=['GET'])
def mobile_payment_success():
    """PayFast return_url — landing page after successful payment.

    The Flutter PayFast widget handles the actual callback; this is a
    fallback URL required by PayFast's form submission.
    """
    return jsonify({
        'status': 'success',
        'message': 'Payment processed. You can close this page.',
    }), 200


@mobile_api.route('/payment/cancel', methods=['GET'])
def mobile_payment_cancel():
    """PayFast cancel_url — landing page when user cancels payment."""
    return jsonify({
        'status': 'cancelled',
        'message': 'Payment cancelled. You can close this page.',
    }), 200


# ---------------------------------------------------------------------------
# 4. ITN redirect (existing — PayFast server-to-server notification)
# ---------------------------------------------------------------------------

@mobile_api.route('/payment/notify', methods=['POST'])
def mobile_payment_notify():
    """Redirect mobile PayFast ITN to the shared handler.

    The Flutter app configures PayFast with notify_url pointing here.
    We use HTTP 307 to preserve the POST method and body.
    """
    return redirect(url_for('payfast.payfast_itn'), code=307)

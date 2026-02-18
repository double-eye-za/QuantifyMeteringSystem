"""PayFast ITN (Instant Transaction Notification) webhook.

Shared endpoint used by both the portal and mobile app.  PayFast POSTs
transaction results here after a customer completes (or cancels) payment.

No authentication decorator — this is a server-to-server callback from
PayFast, not a browser request.
"""
from __future__ import annotations

import json
import logging
from datetime import datetime

from flask import Blueprint, request, current_app, jsonify, render_template
from flask_login import login_required, current_user

from ..db import db
from ..models.transaction import Transaction
from ..models.wallet import Wallet
from ..services.wallets import credit_wallet
from ..utils.payfast import validate_itn_signature, verify_itn_with_payfast

logger = logging.getLogger(__name__)

payfast_bp = Blueprint("payfast", __name__, url_prefix="/api/payfast")


@payfast_bp.route("/onsite-activate/<mode>", methods=["GET"])
def onsite_activate(mode: str):
    """Serve the PayFast onsite activation page for the mobile app.

    This standalone HTML page loads the PayFast onsite engine script and
    triggers the payment modal.  No authentication required — the uuid
    query parameter (issued by PayFast) is the only security token.

    Path params:
        mode – 'sandbox' or 'live' (determines which engine.js to load)
    Query params (appended by the Flutter PayFast package):
        uuid – PayFast payment identifier
    """
    is_sandbox = (mode == 'sandbox')
    return render_template("mobile/payfast_onsite.html", is_sandbox=is_sandbox)


def _extract_utility_type(txn: Transaction) -> str:
    """Extract the utility_type from the original transaction metadata or description.

    The original payment_metadata (set at transaction creation) contains the
    utility_type.  The description also encodes it as 'Top-up for Electricity' etc.
    """
    # 1. Try the original payment_metadata JSON
    if txn.payment_metadata:
        try:
            meta = json.loads(txn.payment_metadata)
            if isinstance(meta, dict) and meta.get("utility_type"):
                return meta["utility_type"]
        except (json.JSONDecodeError, TypeError):
            pass

    # 2. Try the transaction_type (e.g. topup_electricity)
    if txn.transaction_type and txn.transaction_type.startswith("topup_"):
        return txn.transaction_type.replace("topup_", "")

    # 3. Try the description (e.g. "Top-up for Electricity")
    if txn.description:
        desc_lower = txn.description.lower()
        for ut in ("hot_water", "electricity", "water", "solar"):
            if ut.replace("_", " ") in desc_lower:
                return ut

    return "electricity"  # default fallback


def _complete_transaction(txn: Transaction) -> str:
    """Credit the wallet and mark the transaction as completed.

    Returns the utility_type used.  Does NOT commit — caller must commit.
    """
    wallet = Wallet.query.get(txn.wallet_id)
    if not wallet:
        raise ValueError(f"Wallet {txn.wallet_id} not found")

    utility_type = _extract_utility_type(txn)

    credit_wallet(wallet, float(txn.amount), utility_type)
    txn.status = "completed"
    txn.completed_at = datetime.utcnow()

    return utility_type


@payfast_bp.route("/notify", methods=["POST"])
def payfast_itn():
    """Handle PayFast Instant Transaction Notification.

    Flow:
    1. Validate ITN signature
    2. Server-to-server verify with PayFast (production only)
    3. Look up pending transaction by m_payment_id → reference
    4. Idempotency: if already completed, return 200
    5. COMPLETE  → credit wallet, mark completed, queue notification
    6. CANCELLED / other → mark failed
    """
    post_data = request.form.to_dict()
    logger.info("PayFast ITN received: m_payment_id=%s", post_data.get("m_payment_id"))

    # --- 1. Signature validation ---
    passphrase = current_app.config.get("PAYFAST_PASSPHRASE")
    if not validate_itn_signature(post_data, passphrase):
        logger.warning("PayFast ITN signature validation failed")
        return "INVALID SIGNATURE", 400

    # --- 2. Server-to-server verification (skip in sandbox) ---
    if not current_app.config.get("PAYFAST_SANDBOX", True):
        validate_url = current_app.config.get("PAYFAST_VALIDATE_URL")
        if not verify_itn_with_payfast(post_data, validate_url):
            logger.warning("PayFast server-to-server verification failed")
            return "VERIFICATION FAILED", 400

    # --- 3. Look up transaction ---
    m_payment_id = post_data.get("m_payment_id")
    if not m_payment_id:
        logger.warning("PayFast ITN missing m_payment_id")
        return "MISSING PAYMENT ID", 400

    txn = Transaction.query.filter_by(reference=m_payment_id).first()
    if not txn:
        logger.warning("PayFast ITN: no transaction for reference=%s", m_payment_id)
        return "TRANSACTION NOT FOUND", 404

    # --- 4. Idempotency ---
    if txn.status == "completed":
        logger.info("PayFast ITN: transaction %s already completed", m_payment_id)
        return "OK", 200

    # --- Read utility_type BEFORE overwriting payment_metadata ---
    utility_type = _extract_utility_type(txn)

    # --- Store PayFast data on the transaction ---
    txn.payment_gateway = "payfast"
    txn.payment_gateway_ref = post_data.get("pf_payment_id", "")
    txn.payment_gateway_status = post_data.get("payment_status", "")
    txn.payment_metadata = json.dumps(post_data)

    payment_status = post_data.get("payment_status", "")

    # --- 5. COMPLETE ---
    if payment_status == "COMPLETE":
        wallet = Wallet.query.get(txn.wallet_id)
        if not wallet:
            logger.error("PayFast ITN: wallet %s not found for txn %s", txn.wallet_id, m_payment_id)
            return "WALLET NOT FOUND", 500

        credit_wallet(wallet, float(txn.amount), utility_type)

        txn.status = "completed"
        txn.completed_at = datetime.utcnow()
        db.session.commit()

        # Queue async notification (SMS / in-app)
        try:
            from ..tasks.notification_tasks import send_topup_notification
            send_topup_notification.delay(
                wallet_id=txn.wallet_id,
                amount=float(txn.amount),
                payment_method=txn.payment_method or "card",
                utility_type=utility_type,
            )
        except Exception as e:
            logger.warning("Failed to queue top-up notification: %s", e)

        # Queue receipt email
        try:
            from ..tasks.payment_tasks import send_topup_receipt_email
            send_topup_receipt_email.delay(
                wallet_id=txn.wallet_id,
                amount=float(txn.amount),
                utility_type=utility_type,
                transaction_number=txn.transaction_number,
            )
        except Exception as e:
            logger.warning("Failed to queue receipt email: %s", e)

        logger.info("PayFast ITN: transaction %s completed successfully", m_payment_id)
        return "OK", 200

    # --- 6. CANCELLED / FAILED / other ---
    txn.status = "failed"
    db.session.commit()
    logger.info("PayFast ITN: transaction %s marked failed (status=%s)", m_payment_id, payment_status)
    return "OK", 200


# ---------------------------------------------------------------------------
# Sandbox / dev helper — manually confirm a pending PayFast transaction
# ---------------------------------------------------------------------------

@payfast_bp.route("/sandbox-confirm/<int:txn_id>", methods=["POST"])
@login_required
def sandbox_confirm(txn_id):
    """Manually confirm a pending PayFast transaction (sandbox/dev only).

    Available to logged-in portal users.  Disabled when PAYFAST_SANDBOX is False.
    """
    if not current_app.config.get("PAYFAST_SANDBOX", False):
        return jsonify({"error": "Only available in sandbox mode"}), 403

    txn = Transaction.query.get_or_404(txn_id)

    if txn.status == "completed":
        return jsonify({"message": "Already completed"}), 200

    if txn.status not in ("pending", "processing"):
        return jsonify({"error": f"Transaction is {txn.status}, cannot confirm"}), 400

    try:
        utility_type = _complete_transaction(txn)
        txn.payment_gateway = "payfast"
        txn.payment_gateway_status = "COMPLETE"
        txn.payment_gateway_ref = "SANDBOX-MANUAL"
        db.session.commit()
    except ValueError as e:
        return jsonify({"error": str(e)}), 500

    # Queue receipt email
    try:
        from ..tasks.payment_tasks import send_topup_receipt_email
        send_topup_receipt_email.delay(
            wallet_id=txn.wallet_id,
            amount=float(txn.amount),
            utility_type=utility_type,
            transaction_number=txn.transaction_number,
        )
    except Exception as e:
        logger.warning("Failed to queue receipt email (sandbox): %s", e)

    return jsonify({
        "message": "Transaction confirmed",
        "transaction_id": txn.id,
        "amount": float(txn.amount),
        "utility_type": utility_type,
    }), 200

from __future__ import annotations

from flask import jsonify, request, render_template, current_app
from flask_login import login_required, current_user

from ...models import Wallet, Transaction
from ...utils.pagination import paginate_query
from ...utils.audit import log_action
from . import api_v1

from ...utils.decorators import get_user_estate_filter, get_allowed_estates
from ...services.wallets import get_wallet_by_id as svc_get_wallet_by_id, credit_wallet
from ...services.transactions import (
    list_transactions as svc_list_transactions,
    create_transaction as svc_create_transaction,
)


@api_v1.route("/billing", methods=["GET"])
@login_required
def billing_page():
    """Render the billing page with real data"""
    from ...models import Estate, Unit, Wallet, Transaction
    from ...db import db
    from sqlalchemy import func
    from datetime import datetime, date, timedelta

    # Get filter parameters — estate-scoped users are locked to their estate
    user_estate = get_user_estate_filter()
    if user_estate:
        estate_id = str(user_estate)
    else:
        estate_id = request.args.get("estate", "all")
    status_filter = request.args.get("status", "all")
    search_query = request.args.get("search", "")

    # Calculate date ranges
    today = date.today()
    today_start = datetime.combine(today, datetime.min.time())
    today_end = datetime.combine(today, datetime.max.time())

    # Build estate filter
    estate_filter = []
    if estate_id != "all":
        estate_filter = [Estate.id == int(estate_id)]

    #  Calculate stats
    # All wallet balances
    total_balances_query = (
        db.session.query(func.sum(Wallet.balance))
        .join(Unit, Unit.id == Wallet.unit_id)
        .join(Estate, Estate.id == Unit.estate_id)
    )
    if estate_filter:
        total_balances_query = total_balances_query.filter(*estate_filter)
    total_balances = total_balances_query.scalar() or 0.0

    # Today's top-ups
    todays_topups_query = (
        db.session.query(func.sum(Transaction.amount))
        .join(Wallet, Wallet.id == Transaction.wallet_id)
        .join(Unit, Unit.id == Wallet.unit_id)
        .join(Estate, Estate.id == Unit.estate_id)
        .filter(
            Transaction.transaction_type == "topup",
            Transaction.status == "completed",
            Transaction.completed_at >= today_start,
            Transaction.completed_at <= today_end,
        )
    )
    if estate_filter:
        todays_topups_query = todays_topups_query.filter(*estate_filter)
    todays_topups = todays_topups_query.scalar() or 0.0

    # Today's usage (consumption transactions)
    todays_usage_query = (
        db.session.query(func.sum(Transaction.amount))
        .join(Wallet, Wallet.id == Transaction.wallet_id)
        .join(Unit, Unit.id == Wallet.unit_id)
        .join(Estate, Estate.id == Unit.estate_id)
        .filter(
            Transaction.transaction_type.in_(
                ["consumption_electricity", "consumption_water", "consumption_solar"]
            ),
            Transaction.status == "completed",
            Transaction.completed_at >= today_start,
            Transaction.completed_at <= today_end,
        )
    )
    if estate_filter:
        todays_usage_query = todays_usage_query.filter(*estate_filter)
    todays_usage = todays_usage_query.scalar() or 0.0

    # Low balance units (below threshold)
    low_balance_query = (
        db.session.query(func.count(Wallet.id))
        .join(Unit, Unit.id == Wallet.unit_id)
        .join(Estate, Estate.id == Unit.estate_id)
        .filter(Wallet.balance < Wallet.low_balance_threshold, Wallet.balance > 0)
    )
    if estate_filter:
        low_balance_query = low_balance_query.filter(*estate_filter)
    low_balance_units = low_balance_query.scalar() or 0

    # Zero balance units
    zero_balance_query = (
        db.session.query(func.count(Wallet.id))
        .join(Unit, Unit.id == Wallet.unit_id)
        .join(Estate, Estate.id == Unit.estate_id)
        .filter(Wallet.balance <= 0)
    )
    if estate_filter:
        zero_balance_query = zero_balance_query.filter(*estate_filter)
    zero_balance_units = zero_balance_query.scalar() or 0

    # Get estates — scoped users only see their estate
    estates = get_allowed_estates()

    # Get wallet overview data with last topup date
    from sqlalchemy import func, case

    wallet_query = (
        db.session.query(
            Wallet,
            Unit,
            Estate,
            func.max(
                case(
                    (Transaction.transaction_type == "topup", Transaction.completed_at),
                    else_=None,
                )
            ).label("last_topup_date"),
        )
        .join(Unit, Unit.id == Wallet.unit_id)
        .join(Estate, Estate.id == Unit.estate_id)
        .outerjoin(Transaction, Transaction.wallet_id == Wallet.id)
        .group_by(Wallet.id, Unit.id, Estate.id)
    )

    # Apply filters
    if estate_filter:
        wallet_query = wallet_query.filter(*estate_filter)

    if status_filter == "low":
        wallet_query = wallet_query.filter(
            Wallet.balance < Wallet.low_balance_threshold, Wallet.balance > 0
        )
    elif status_filter == "zero":
        wallet_query = wallet_query.filter(Wallet.balance <= 0)
    elif status_filter == "active":
        wallet_query = wallet_query.filter(
            Wallet.balance >= Wallet.low_balance_threshold
        )

    if search_query:
        wallet_query = wallet_query.filter(
            func.concat(Unit.unit_number, " ", Estate.name).ilike(f"%{search_query}%")
        )

    wallets = wallet_query.order_by(Wallet.balance.desc()).all()

    # Get recent transactions
    recent_transactions_query = (
        db.session.query(Transaction, Unit, Estate)
        .join(Wallet, Wallet.id == Transaction.wallet_id)
        .join(Unit, Unit.id == Wallet.unit_id)
        .join(Estate, Estate.id == Unit.estate_id)
    )
    if estate_filter:
        recent_transactions_query = recent_transactions_query.filter(*estate_filter)

    recent_transactions = (
        recent_transactions_query.order_by(Transaction.completed_at.desc())
        .limit(20)
        .all()
    )

    # Get top-up history
    topup_history_query = (
        db.session.query(Transaction, Unit, Estate)
        .join(Wallet, Wallet.id == Transaction.wallet_id)
        .join(Unit, Unit.id == Wallet.unit_id)
        .join(Estate, Estate.id == Unit.estate_id)
        .filter(Transaction.transaction_type == "topup")
    )
    if estate_filter:
        topup_history_query = topup_history_query.filter(*estate_filter)

    topup_history = (
        topup_history_query.order_by(Transaction.completed_at.desc()).limit(20).all()
    )

    # Generate dynamic months (current month + last 3 months)
    from calendar import month_name

    months = []
    current_date = datetime.now()
    for i in range(4):
        month_date = current_date - timedelta(days=30 * i)
        month_str = month_date.strftime("%B %Y")
        months.append({"value": month_date.strftime("%Y-%m"), "label": month_str})

    return render_template(
        "billing/billing.html",
        # Stats
        total_balances=float(total_balances),
        todays_topups=float(todays_topups),
        todays_usage=float(todays_usage),
        low_balance_units=low_balance_units,
        zero_balance_units=zero_balance_units,
        # Data
        estates=estates,
        wallets=wallets,
        recent_transactions=recent_transactions,
        topup_history=topup_history,
        months=months,
        # Filters
        current_estate=estate_id,
        current_status=status_filter,
        current_search=search_query,
    )


@api_v1.get("/wallets/<int:wallet_id>")
@login_required
def get_wallet(wallet_id: int):
    wallet = svc_get_wallet_by_id(wallet_id)
    if not wallet:
        return jsonify({"error": "Not Found", "code": 404}), 404
    return jsonify({"data": wallet.to_dict()})


@api_v1.post("/wallets/<int:wallet_id>/topup")
@login_required
def topup_wallet(wallet_id: int):
    from flask_login import current_user

    payload = request.get_json(force=True) or {}
    amount = payload.get("amount")
    payment_method = payload.get("payment_method")
    reference = payload.get("reference")
    metadata = payload.get("metadata") or {}

    # Validate wallet exists
    wallet = svc_get_wallet_by_id(wallet_id)
    if not wallet:
        return jsonify({"error": "Not Found", "code": 404}), 404

    if amount is None or payment_method is None:
        return (
            jsonify(
                {
                    "error": "amount and payment_method are required",
                    "code": 400,
                }
            ),
            400,
        )

    # For manual admin top-ups, require super admin
    if payment_method == "manual_admin":
        if not getattr(current_user, "is_super_admin", False):
            return jsonify({"error": "Unauthorized. Super admin access required.", "code": 403}), 403

    # Unified wallet: top-up goes to the shared balance pool
    transaction_type = "topup"

    # Create transaction (no meter_id — top-up isn't tied to a specific meter)
    txn = svc_create_transaction(
        wallet_id=wallet_id,
        transaction_type=transaction_type,
        amount=amount,
        reference=reference,
        payment_method=payment_method,
        metadata=metadata,
    )

    # Credit the main wallet balance
    from ...db import db
    credit_wallet(wallet, float(amount))
    db.session.commit()

    log_action(
        "wallet.topup",
        entity_type="wallet",
        entity_id=wallet_id,
        new_values={
            "amount": amount,
            "payment_method": payment_method,
            "reference": reference,
            "transaction_id": txn.id,
        },
    )

    # Send real-time notification (async via Celery)
    try:
        from ...tasks.notification_tasks import send_topup_notification
        send_topup_notification.delay(
            wallet_id=wallet_id,
            amount=float(amount),
            payment_method=payment_method,
        )
    except Exception as e:
        # Don't fail the transaction if notification fails
        import logging
        logging.warning(f"Failed to queue top-up notification: {e}")

    return jsonify(
        {
            "data": {
                "transaction_id": txn.id,
                "transaction_number": txn.transaction_number,
                "status": txn.status,
            }
        }
    ), 201


@api_v1.get("/wallets/<int:wallet_id>/pending-transactions")
@login_required
def list_pending_transactions(wallet_id: int):
    query = svc_list_transactions(wallet_id=wallet_id, status="pending")
    items, meta = paginate_query(query)
    return jsonify(
        {
            "data": [
                {
                    "transaction_id": t.id,
                    "amount": float(t.amount),
                    "payment_method": t.payment_method,
                    "status": t.status,
                    "payment_gateway_ref": t.payment_gateway_ref,
                    "created_at": t.created_at.isoformat() if t.created_at else None,
                    "expires_at": t.expires_at.isoformat() if t.expires_at else None,
                }
                for t in items
            ],
            **meta,
        }
    )


# ---------------------------------------------------------------------------
# Admin PayFast transaction management
# ---------------------------------------------------------------------------

@api_v1.route("/transactions/payfast", methods=["GET"])
@login_required
def payfast_transactions_page():
    """Admin page listing all PayFast transactions with filters."""
    from datetime import datetime, timedelta
    from ...db import db

    status_filter = request.args.get("status", "all")
    days = request.args.get("days", 30, type=int)
    page = request.args.get("page", 1, type=int)
    per_page = 25

    since = datetime.utcnow() - timedelta(days=days)

    query = Transaction.query.filter(
        Transaction.payment_gateway == "payfast",
        Transaction.created_at >= since,
    )

    if status_filter != "all":
        query = query.filter(Transaction.status == status_filter)

    query = query.order_by(Transaction.created_at.desc())
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)

    # Summary counts
    total_payfast = Transaction.query.filter(
        Transaction.payment_gateway == "payfast",
        Transaction.created_at >= since,
    ).count()
    pending_count = Transaction.query.filter(
        Transaction.payment_gateway == "payfast",
        Transaction.status == "pending",
        Transaction.created_at >= since,
    ).count()
    failed_count = Transaction.query.filter(
        Transaction.payment_gateway == "payfast",
        Transaction.status.in_(["failed", "expired"]),
        Transaction.created_at >= since,
    ).count()

    return render_template(
        "billing/payfast_transactions.html",
        transactions=pagination.items,
        pagination=pagination,
        status_filter=status_filter,
        days=days,
        total_payfast=total_payfast,
        pending_count=pending_count,
        failed_count=failed_count,
    )


@api_v1.route("/transactions/<int:txn_id>/retry-payfast", methods=["POST"])
@login_required
def retry_payfast_transaction(txn_id):
    """Admin: Retry/confirm a pending or failed PayFast transaction.

    Super admin only. Checks with PayFast validation endpoint if a gateway ref
    exists, otherwise allows manual force-complete.
    """
    from ...db import db
    from ...routes.payfast import _complete_transaction, _extract_utility_type

    if not getattr(current_user, "is_super_admin", False):
        return jsonify({"error": "Super admin access required"}), 403

    txn = Transaction.query.get_or_404(txn_id)

    if txn.payment_gateway != "payfast":
        return jsonify({"error": "Not a PayFast transaction"}), 400

    if txn.status == "completed":
        return jsonify({"message": "Already completed"}), 200

    if txn.status not in ("pending", "failed", "expired"):
        return jsonify({"error": f"Cannot retry transaction with status '{txn.status}'"}), 400

    action = request.json.get("action", "check") if request.is_json else "check"

    # If we have a PayFast reference, verify with PayFast
    if txn.payment_gateway_ref and action == "check":
        from ...utils.payfast import verify_itn_with_payfast
        import json

        # Try to reconstruct minimal post data for validation
        validate_url = current_app.config.get("PAYFAST_VALIDATE_URL")
        if txn.payment_metadata:
            try:
                post_data = json.loads(txn.payment_metadata)
                if isinstance(post_data, dict):
                    is_valid = verify_itn_with_payfast(post_data, validate_url)
                    if is_valid:
                        utility_type = _complete_transaction(txn)
                        txn.payment_gateway_status = "COMPLETE"
                        db.session.commit()
                        log_action(
                            "payfast.retry_success",
                            entity_type="transaction",
                            entity_id=txn.id,
                            new_values={"action": "auto_verified", "utility_type": utility_type},
                        )
                        return jsonify({
                            "message": "Transaction verified and completed",
                            "amount": float(txn.amount),
                            "utility_type": utility_type,
                        }), 200
                    else:
                        return jsonify({
                            "message": "PayFast verification returned INVALID. Use force-complete if you're sure.",
                            "status": "unverified",
                        }), 200
            except (json.JSONDecodeError, TypeError):
                pass

    # Force-complete (super admin override)
    if action == "force_complete":
        try:
            utility_type = _complete_transaction(txn)
            txn.payment_gateway_status = "FORCE_COMPLETED"
            txn.payment_gateway_ref = txn.payment_gateway_ref or "ADMIN-MANUAL"
            db.session.commit()
            log_action(
                "payfast.force_complete",
                entity_type="transaction",
                entity_id=txn.id,
                new_values={
                    "action": "force_complete",
                    "admin_user": current_user.id,
                    "utility_type": utility_type,
                },
            )
            return jsonify({
                "message": "Transaction force-completed by admin",
                "amount": float(txn.amount),
                "utility_type": utility_type,
            }), 200
        except ValueError as e:
            return jsonify({"error": str(e)}), 500

    return jsonify({"error": "No gateway reference found. Use force_complete action."}), 400


@api_v1.route("/payfast/reconciliation", methods=["GET"])
@login_required
def payfast_reconciliation_page():
    """Admin view showing reconciliation status and ability to trigger a run."""
    from datetime import datetime, timedelta
    from ...db import db
    from ...models.notification import Notification
    from sqlalchemy import func

    # Get recent reconciliation notifications (last 14 days)
    since = datetime.utcnow() - timedelta(days=14)
    recon_notifications = Notification.query.filter(
        Notification.notification_type == "payfast_reconciliation",
        Notification.created_at >= since,
    ).order_by(Notification.created_at.desc()).limit(14).all()

    # Summary stats for the reconciliation dashboard
    last_48h = datetime.utcnow() - timedelta(hours=48)
    payfast_txns_48h = Transaction.query.filter(
        Transaction.payment_gateway == "payfast",
        Transaction.created_at >= last_48h,
    ).all()

    total_txns = len(payfast_txns_48h)
    completed = sum(1 for t in payfast_txns_48h if t.status == "completed")
    pending = sum(1 for t in payfast_txns_48h if t.status == "pending")
    failed = sum(1 for t in payfast_txns_48h if t.status in ("failed", "expired"))
    reconciled = sum(1 for t in payfast_txns_48h if t.reconciled)

    return render_template(
        "billing/payfast_reconciliation.html",
        recon_notifications=recon_notifications,
        total_txns=total_txns,
        completed=completed,
        pending=pending,
        failed=failed,
        reconciled=reconciled,
    )


@api_v1.route("/payfast/reconciliation/run", methods=["POST"])
@login_required
def payfast_reconciliation_run():
    """Trigger a manual reconciliation run (admin only)."""
    if not getattr(current_user, "is_super_admin", False):
        return jsonify({"error": "Super admin access required"}), 403

    try:
        from ...tasks.payment_tasks import reconcile_payfast_transactions
        task = reconcile_payfast_transactions.delay()
        log_action(
            "payfast.reconciliation_manual",
            entity_type="system",
            entity_id=0,
            new_values={"task_id": task.id, "triggered_by": current_user.id},
        )
        return jsonify({
            "message": "Reconciliation task queued",
            "task_id": task.id,
        }), 200
    except Exception as e:
        return jsonify({"error": f"Failed to queue task: {str(e)}"}), 500

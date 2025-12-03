from __future__ import annotations

from flask import jsonify, request, render_template
from flask_login import login_required

from ...models import Wallet, Transaction
from ...utils.pagination import paginate_query
from ...utils.audit import log_action
from . import api_v1

from ...services.wallets import get_wallet_by_id as svc_get_wallet_by_id
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

    # Get filter parameters
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

    # Get estate
    estates = Estate.query.all()

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

    # Determine utility type from metadata (transaction type is always "topup")
    utility_type = metadata.get("utility_type", "electricity")
    transaction_type = "topup"

    # Get the meter_id for this utility type from the unit
    from ...db import db
    from ...models import Unit
    unit = db.session.query(Unit).filter(Unit.id == wallet.unit_id).first()
    meter_id = None

    if unit:
        if utility_type == "electricity":
            meter_id = unit.electricity_meter_id
        elif utility_type == "water":
            meter_id = unit.water_meter_id
        elif utility_type == "solar":
            meter_id = unit.solar_meter_id
        elif utility_type == "hot_water":
            meter_id = unit.hot_water_meter_id

    # Create transaction with meter_id link
    txn = svc_create_transaction(
        wallet_id=wallet_id,
        transaction_type=transaction_type,
        amount=amount,
        reference=reference,
        payment_method=payment_method,
        metadata=metadata,
        meter_id=meter_id,  # Link to specific meter
    )

    # Update wallet balance for the specific utility type
    if utility_type == "electricity":
        wallet.electricity_balance = float(wallet.electricity_balance or 0) + float(amount)
    elif utility_type == "water":
        wallet.water_balance = float(wallet.water_balance or 0) + float(amount)
    elif utility_type == "solar":
        wallet.solar_balance = float(wallet.solar_balance or 0) + float(amount)
    elif utility_type == "hot_water":
        wallet.hot_water_balance = float(wallet.hot_water_balance or 0) + float(amount)

    # Also update main balance
    wallet.balance = float(wallet.balance or 0) + float(amount)
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
            "utility_type": utility_type,
        },
    )

    # Send real-time notification (async via Celery)
    try:
        from ...tasks.notification_tasks import send_topup_notification
        send_topup_notification.delay(
            wallet_id=wallet_id,
            amount=float(amount),
            payment_method=payment_method,
            utility_type=utility_type
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

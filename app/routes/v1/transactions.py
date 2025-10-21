from __future__ import annotations

from flask import jsonify, request
from flask_login import login_required

from ...models import Transaction
from ...utils.pagination import paginate_query
from ...utils.audit import log_action
from . import api_v1


@api_v1.get("/transactions")
@login_required
def list_transactions():
    wallet_id = request.args.get("wallet_id", type=int)
    transaction_type = request.args.get("transaction_type")
    status = request.args.get("status")
    query = Transaction.list_filtered(
        wallet_id=wallet_id, transaction_type=transaction_type, status=status
    )
    items, meta = paginate_query(query)
    return jsonify(
        {
            "data": [
                {
                    "id": t.id,
                    "transaction_number": t.transaction_number,
                    "wallet_id": t.wallet_id,
                    "transaction_type": t.transaction_type,
                    "amount": float(t.amount),
                    "status": t.status,
                    "created_at": t.created_at.isoformat() if t.created_at else None,
                }
                for t in items
            ],
            **meta,
        }
    )


@api_v1.get("/transactions/<int:txn_id>")
@login_required
def get_transaction(txn_id: int):
    t = Transaction.get_by_id(txn_id)
    if not t:
        return jsonify({"error": "Not Found", "code": 404}), 404
    return jsonify(
        {
            "data": {
                "id": t.id,
                "transaction_number": t.transaction_number,
                "wallet_id": t.wallet_id,
                "transaction_type": t.transaction_type,
                "amount": float(t.amount),
                "status": t.status,
                "created_at": t.created_at.isoformat() if t.created_at else None,
            }
        }
    )


@api_v1.post("/transactions/<int:txn_id>/reverse")
@login_required
def reverse_transaction(txn_id: int):
    t = Transaction.get_by_id(txn_id)
    if not t:
        return jsonify({"error": "Not Found", "code": 404}), 404
    payload = request.get_json(force=True) or {}

    before_status = t.status
    before_amount = float(t.amount)

    t.reverse(reason=payload.get("reason"))

    log_action(
        "transaction.reverse",
        entity_type="transaction",
        entity_id=txn_id,
        old_values={"status": before_status, "amount": before_amount},
        new_values={"status": t.status, "reason": payload.get("reason")},
    )

    return jsonify({"data": {"id": t.id, "status": t.status}})

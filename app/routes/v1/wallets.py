from __future__ import annotations

from flask import jsonify, request
from flask_login import login_required

from ...models import Wallet, Transaction
from ...utils.pagination import paginate_query
from . import api_v1


@api_v1.get("/wallets/<int:wallet_id>")
@login_required
def get_wallet(wallet_id: int):
    wallet = Wallet.get_by_id(wallet_id)
    if not wallet:
        return jsonify({"error": "Not Found", "code": 404}), 404
    return jsonify({"data": wallet.to_dict()})


@api_v1.post("/wallets/<int:wallet_id>/topup")
@login_required
def topup_wallet(wallet_id: int):
    payload = request.get_json(force=True) or {}
    amount = payload.get("amount")
    payment_method = payload.get("payment_method")
    reference = payload.get("reference")
    metadata = payload.get("metadata")

    txn = Transaction.create(
        wallet_id=wallet_id,
        transaction_type="topup",
        amount=amount,
        reference=reference,
        payment_method=payment_method,
        metadata=metadata,
    )
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
    query = Transaction.list_filtered(wallet_id=wallet_id, status="pending")
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

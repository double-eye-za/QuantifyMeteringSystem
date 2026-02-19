from __future__ import annotations

from typing import Optional

from sqlalchemy import desc

from app.db import db
from app.models.transaction import Transaction


def list_transactions(
    wallet_id: Optional[int] = None,
    transaction_type: Optional[str] = None,
    status: Optional[str] = None,
):
    q = Transaction.query
    if wallet_id is not None:
        q = q.filter(Transaction.wallet_id == wallet_id)
    if transaction_type is not None:
        q = q.filter(Transaction.transaction_type == transaction_type)
    if status is not None:
        q = q.filter(Transaction.status == status)
    return q.order_by(desc(Transaction.completed_at))


def get_transaction_by_id(txn_id: int):
    return Transaction.query.get(txn_id)


def reverse_transaction(t: Transaction, reason: Optional[str] = None):
    t.reverse(reason=reason)
    db.session.commit()
    return t


def create_transaction(
    wallet_id: int,
    transaction_type: str,
    amount,
    reference: str | None = None,
    payment_method: str | None = None,
    metadata: dict | None = None,
    meter_id: int | None = None,
):
    import json
    from datetime import datetime
    from app.models.wallet import Wallet

    # Get wallet to track balance
    wallet = Wallet.query.get(wallet_id)
    if not wallet:
        raise ValueError(f"Wallet with id {wallet_id} not found")

    # Unified wallet: always track the main balance pool
    balance_before = float(wallet.balance)

    # Calculate balance after transaction
    if transaction_type.startswith("topup") or transaction_type.startswith("refund"):
        balance_after = balance_before + float(amount)
    elif transaction_type.startswith("deduction") or transaction_type.startswith("purchase") or transaction_type.startswith("consumption"):
        balance_after = balance_before - float(amount)
    else:
        balance_after = balance_before

    # Generate transaction number with timestamp
    txn_number = f"TXN{datetime.now().strftime('%Y%m%d%H%M%S')}{wallet_id}"

    # Convert metadata dict to JSON string for storage
    metadata_json = json.dumps(metadata) if metadata else None

    # Generate description based on transaction type and utility
    description = None
    if transaction_type == "topup" and utility_type:
        description = f"Top-up for {utility_type.replace('_', ' ').title()}"

    # Set status and completed_at based on payment method
    is_pending = transaction_type.startswith("purchase") or payment_method in ("eft", "card", "instant_eft")
    txn_status = "pending" if is_pending else "completed"
    completed_at = None if is_pending else datetime.now()

    txn = Transaction(
        transaction_number=txn_number,
        wallet_id=wallet_id,
        transaction_type=transaction_type,
        amount=amount,
        balance_before=balance_before,
        balance_after=balance_after,
        reference=reference,
        description=description,  # Human-readable description
        payment_method=payment_method,
        payment_metadata=metadata_json,
        status=txn_status,
        completed_at=completed_at,
        meter_id=meter_id,  # Link transaction to specific meter
    )
    db.session.add(txn)
    db.session.commit()
    return txn

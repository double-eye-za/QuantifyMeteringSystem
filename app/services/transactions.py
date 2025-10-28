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
):
    txn = Transaction(
        transaction_number=f"TXN{Transaction.created_at.func.now()}",
        wallet_id=wallet_id,
        transaction_type=transaction_type,
        amount=amount,
        balance_before=0,
        balance_after=0,
        reference=reference,
        payment_method=payment_method,
        payment_metadata=(metadata or {}),
        status="pending"
        if transaction_type.startswith("purchase")
        or payment_method in ("eft", "card", "instant_eft")
        else "completed",
    )
    db.session.add(txn)
    db.session.commit()
    return txn

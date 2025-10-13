from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Optional

from sqlalchemy import CheckConstraint
import json

from ..db import db


@dataclass
class Transaction(db.Model):
    __tablename__ = "transactions"

    id: Optional[int]
    transaction_number: str
    wallet_id: int
    transaction_type: str
    amount: float
    balance_before: float
    balance_after: float
    reference: Optional[str]
    description: Optional[str]
    payment_method: Optional[str]
    payment_gateway: Optional[str]
    payment_gateway_ref: Optional[str]
    payment_gateway_status: Optional[str]
    payment_metadata: Optional[str]
    status: Optional[str]
    initiated_at: Optional[datetime]
    completed_at: Optional[datetime]
    expires_at: Optional[datetime]
    reconciled: Optional[bool]
    reconciled_at: Optional[datetime]
    meter_id: Optional[int]
    consumption_kwh: Optional[float]
    rate_applied: Optional[float]
    created_at: Optional[datetime]
    created_by: Optional[int]

    id = db.Column(db.Integer, primary_key=True, autoincrement=True, nullable=False)
    transaction_number = db.Column(db.String(50), unique=True, nullable=False)
    wallet_id = db.Column(db.Integer, db.ForeignKey("wallets.id"), nullable=False)
    transaction_type = db.Column(db.String(30), nullable=False)
    amount = db.Column(db.Numeric(12, 2), nullable=False)
    balance_before = db.Column(db.Numeric(12, 2), nullable=False)
    balance_after = db.Column(db.Numeric(12, 2), nullable=False)
    reference = db.Column(db.String(255))
    description = db.Column(db.Text)
    payment_method = db.Column(db.String(20))
    payment_gateway = db.Column(db.String(50))
    payment_gateway_ref = db.Column(db.String(255))
    payment_gateway_status = db.Column(db.String(50))
    payment_metadata = db.Column(db.Text)
    status = db.Column(db.String(20), default="pending")
    initiated_at = db.Column(db.DateTime, default=datetime.utcnow)
    completed_at = db.Column(db.DateTime)
    expires_at = db.Column(db.DateTime)
    reconciled = db.Column(db.Boolean, default=False)
    reconciled_at = db.Column(db.DateTime)
    meter_id = db.Column(db.Integer, db.ForeignKey("meters.id"))
    consumption_kwh = db.Column(db.Numeric(10, 3))
    rate_applied = db.Column(db.Numeric(10, 4))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    created_by = db.Column(db.Integer, db.ForeignKey("users.id"))

    __table_args__ = (
        CheckConstraint(
            "transaction_type IN (\n            'topup','purchase_electricity','purchase_water','purchase_solar',\n            'consumption_electricity','consumption_water','consumption_solar',\n            'refund','adjustment','service_charge'\n        )",
            name="ck_transactions_type",
        ),
        CheckConstraint(
            "payment_method IS NULL OR payment_method IN ('eft','card','instant_eft','cash','system','adjustment')",
            name="ck_transactions_payment_method",
        ),
        CheckConstraint(
            "status IN ('pending','processing','completed','failed','reversed','expired')",
            name="ck_transactions_status",
        ),
    )

    @staticmethod
    def list_filtered(
        wallet_id: int = None, transaction_type: str = None, status: str = None
    ):
        query = Transaction.query
        if wallet_id is not None:
            query = query.filter(Transaction.wallet_id == wallet_id)
        if transaction_type is not None:
            query = query.filter(Transaction.transaction_type == transaction_type)
        if status is not None:
            query = query.filter(Transaction.status == status)
        return query.order_by(Transaction.created_at.desc())

    @staticmethod
    def get_by_id(txn_id: int):
        return Transaction.query.get(txn_id)

    @staticmethod
    def create(
        wallet_id: int,
        transaction_type: str,
        amount,
        reference: str = None,
        payment_method: str = None,
        metadata: dict = None,
    ) -> "Transaction":
        # balance updates should be handled at Wallet-level; this just records
        txn = Transaction(
            transaction_number=f"TXN{datetime.utcnow().strftime('%Y%m%d%H%M%S%f')}",
            wallet_id=wallet_id,
            transaction_type=transaction_type,
            amount=amount,
            balance_before=0,
            balance_after=0,
            reference=reference,
            payment_method=payment_method,
            payment_metadata=json.dumps(metadata or {}),
            status="pending"
            if transaction_type.startswith("purchase")
            or payment_method in ("eft", "card", "instant_eft")
            else "completed",
        )
        db.session.add(txn)
        db.session.commit()
        return txn

    def reverse(self, reason: str = None) -> "Transaction":
        self.status = "reversed"
        db.session.commit()
        return self

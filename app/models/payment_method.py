from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Optional

from sqlalchemy import CheckConstraint, UniqueConstraint
from ..db import db


@dataclass
class PaymentMethod(db.Model):
    __tablename__ = "payment_methods"

    id: Optional[int]
    wallet_id: int
    method_type: str
    card_token: Optional[str]
    card_last4: Optional[str]
    card_brand: Optional[str]
    card_exp_month: Optional[int]
    card_exp_year: Optional[int]
    bank_name: Optional[str]
    account_last4: Optional[str]
    account_type: Optional[str]
    is_default: Optional[bool]
    is_active: Optional[bool]
    last_used_at: Optional[datetime]

    id = db.Column(db.Integer, primary_key=True, autoincrement=True, nullable=False)
    wallet_id = db.Column(db.Integer, db.ForeignKey("wallets.id"), nullable=False)
    method_type = db.Column(db.String(20), nullable=False)
    card_token = db.Column(db.String(255))
    card_last4 = db.Column(db.String(4))
    card_brand = db.Column(db.String(20))
    card_exp_month = db.Column(db.Integer)
    card_exp_year = db.Column(db.Integer)
    bank_name = db.Column(db.String(100))
    account_last4 = db.Column(db.String(4))
    account_type = db.Column(db.String(20))
    is_default = db.Column(db.Boolean, default=False)
    is_active = db.Column(db.Boolean, default=True)
    last_used_at = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=True)
    updated_at = db.Column(
        db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=True
    )

    __table_args__ = (
        UniqueConstraint(
            "wallet_id", "card_token", name="uq_payment_methods_wallet_cardtoken"
        ),
        CheckConstraint(
            "method_type IN ('card','bank_account')",
            name="ck_payment_methods_type",
        ),
        CheckConstraint(
            "card_exp_month IS NULL OR (card_exp_month BETWEEN 1 AND 12)",
            name="ck_payment_methods_exp_month",
        ),
    )

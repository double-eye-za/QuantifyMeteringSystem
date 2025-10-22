from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Optional

from sqlalchemy import CheckConstraint
from ..db import db


@dataclass
class Wallet(db.Model):
    __tablename__ = "wallets"

    id: Optional[int]
    unit_id: int
    balance: float
    electricity_balance: float
    water_balance: float
    solar_balance: float
    low_balance_threshold: Optional[float]
    low_balance_alert_type: Optional[str]
    low_balance_days_threshold: Optional[int]
    last_low_balance_alert: Optional[datetime]
    alert_frequency_hours: Optional[int]
    electricity_minimum_activation: Optional[float]
    water_minimum_activation: Optional[float]
    auto_topup_enabled: Optional[bool]
    auto_topup_amount: Optional[float]
    auto_topup_threshold: Optional[float]
    daily_avg_consumption: Optional[float]
    last_consumption_calc_date: Optional[datetime]
    last_topup_date: Optional[datetime]
    is_suspended: Optional[bool]
    suspension_reason: Optional[str]

    id = db.Column(db.Integer, primary_key=True, autoincrement=True, nullable=False)
    unit_id = db.Column(
        db.Integer, db.ForeignKey("units.id"), unique=True, nullable=False
    )
    balance = db.Column(db.Numeric(12, 2), nullable=False, default=0.00)
    electricity_balance = db.Column(db.Numeric(12, 2), nullable=False, default=0.00)
    water_balance = db.Column(db.Numeric(12, 2), nullable=False, default=0.00)
    solar_balance = db.Column(db.Numeric(12, 2), nullable=False, default=0.00)
    low_balance_threshold = db.Column(db.Numeric(10, 2), default=50.00)
    low_balance_alert_type = db.Column(db.String(20), default="fixed")
    low_balance_days_threshold = db.Column(db.Integer, default=3)
    last_low_balance_alert = db.Column(db.DateTime)
    alert_frequency_hours = db.Column(db.Integer, default=24)
    electricity_minimum_activation = db.Column(db.Numeric(10, 2), default=20.00)
    water_minimum_activation = db.Column(db.Numeric(10, 2), default=20.00)
    auto_topup_enabled = db.Column(db.Boolean, default=False)
    auto_topup_amount = db.Column(db.Numeric(10, 2))
    auto_topup_threshold = db.Column(db.Numeric(10, 2))
    daily_avg_consumption = db.Column(db.Numeric(10, 2))
    last_consumption_calc_date = db.Column(db.DateTime)
    last_topup_date = db.Column(db.DateTime)
    is_suspended = db.Column(db.Boolean, default=False)
    suspension_reason = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=True)
    updated_at = db.Column(
        db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=True
    )

    __table_args__ = (
        CheckConstraint(
            "electricity_minimum_activation >= 0", name="ck_wallets_elec_min"
        ),
        CheckConstraint("water_minimum_activation >= 0", name="ck_wallets_water_min"),
    )

    @staticmethod
    def get_by_id(wallet_id: int):
        return Wallet.query.get(wallet_id)

    def to_dict(self):
        return {
            "id": self.id,
            "unit_id": self.unit_id,
            "balance": float(self.balance),
            "electricity_balance": float(self.electricity_balance),
            "water_balance": float(self.water_balance),
            "solar_balance": float(self.solar_balance),
            "low_balance_threshold": float(self.low_balance_threshold)
            if self.low_balance_threshold is not None
            else None,
            "low_balance_alert_type": self.low_balance_alert_type,
            "low_balance_days_threshold": self.low_balance_days_threshold,
            "last_low_balance_alert": self.last_low_balance_alert.isoformat()
            if self.last_low_balance_alert
            else None,
            "alert_frequency_hours": self.alert_frequency_hours,
            "electricity_minimum_activation": float(
                self.electricity_minimum_activation
            ),
            "water_minimum_activation": float(self.water_minimum_activation),
            "auto_topup_enabled": self.auto_topup_enabled,
            "auto_topup_amount": float(self.auto_topup_amount)
            if self.auto_topup_amount is not None
            else None,
            "auto_topup_threshold": float(self.auto_topup_threshold)
            if self.auto_topup_threshold is not None
            else None,
            "daily_avg_consumption": float(self.daily_avg_consumption)
            if self.daily_avg_consumption is not None
            else None,
            "last_consumption_calc_date": self.last_consumption_calc_date.isoformat()
            if self.last_consumption_calc_date
            else None,
            "is_suspended": self.is_suspended,
            "suspension_reason": self.suspension_reason,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

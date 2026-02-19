from __future__ import annotations

from datetime import datetime
from typing import Optional

from app.models.wallet import Wallet


def get_wallet_by_id(wallet_id: int):
    return Wallet.query.get(wallet_id)


def credit_wallet(wallet: Wallet, amount: float, utility_type: str = None) -> None:
    """Apply a top-up credit to the wallet's main balance.

    Unified wallet model: all top-ups go to the single shared balance pool.
    The utility_type parameter is accepted for backward compatibility but
    is no longer used — funds are not allocated to a specific utility.

    Utility columns (electricity_balance, water_balance, etc.) are now
    cumulative spend trackers updated only by consumption billing.

    Does NOT call db.session.commit() — the caller controls the transaction
    boundary so this can be composed with other DB operations atomically.
    """
    wallet.balance = float(wallet.balance or 0) + amount
    wallet.last_topup_date = datetime.utcnow()

from __future__ import annotations

from datetime import datetime
from typing import Optional

from app.models.wallet import Wallet


def get_wallet_by_id(wallet_id: int):
    return Wallet.query.get(wallet_id)


def credit_wallet(wallet: Wallet, amount: float, utility_type: str) -> None:
    """Apply a top-up credit to a wallet's utility-specific and main balances.

    Updates the appropriate utility balance (electricity, water, solar, or
    hot_water), the main balance, and the last_topup_date timestamp.

    Does NOT call db.session.commit() — the caller controls the transaction
    boundary so this can be composed with other DB operations atomically.
    """
    if utility_type == 'electricity':
        wallet.electricity_balance = float(wallet.electricity_balance or 0) + amount
    elif utility_type == 'water':
        wallet.water_balance = float(wallet.water_balance or 0) + amount
    elif utility_type == 'solar':
        wallet.solar_balance = float(wallet.solar_balance or 0) + amount
    elif utility_type == 'hot_water':
        wallet.hot_water_balance = float(wallet.hot_water_balance or 0) + amount

    wallet.balance = float(wallet.balance or 0) + amount
    wallet.last_topup_date = datetime.utcnow()

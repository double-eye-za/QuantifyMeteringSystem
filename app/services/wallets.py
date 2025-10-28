from __future__ import annotations

from typing import Optional

from app.models.wallet import Wallet


def get_wallet_by_id(wallet_id: int):
    return Wallet.query.get(wallet_id)

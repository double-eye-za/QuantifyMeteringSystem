from __future__ import annotations

from typing import Optional

from app.models import RateTable


def get_rate_table_by_id(rate_table_id: int):
    return RateTable.query.get(rate_table_id)


def list_rate_tables(utility_type: str | None = None, is_active: bool | None = None):
    query = RateTable.query
    if utility_type:
        query = query.filter(RateTable.utility_type == utility_type)
    if is_active is not None:
        query = query.filter(RateTable.is_active == is_active)
    return query.order_by(RateTable.effective_from.desc())

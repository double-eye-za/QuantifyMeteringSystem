from __future__ import annotations

from math import ceil
from typing import Any, Dict, List, Tuple

from flask import request
from sqlalchemy.orm import Query


DEFAULT_PER_PAGE = 20
MAX_PER_PAGE = 100


def parse_pagination_params() -> Tuple[int, int]:
    try:
        page = int(request.args.get("page", 1))
    except (TypeError, ValueError):
        page = 1
    try:
        per_page = int(request.args.get("per_page", DEFAULT_PER_PAGE))
    except (TypeError, ValueError):
        per_page = DEFAULT_PER_PAGE
    if per_page > MAX_PER_PAGE:
        per_page = MAX_PER_PAGE
    if page < 1:
        page = 1
    return page, per_page


def paginate_query(query: Query) -> Tuple[List[Any], Dict[str, Any]]:
    page, per_page = parse_pagination_params()
    total = query.order_by(None).count()
    items = query.limit(per_page).offset((page - 1) * per_page).all()
    pages = ceil(total / per_page) if per_page else 1
    next_page = page + 1 if page < pages else None
    prev_page = page - 1 if page > 1 else None
    meta = {
        "page": page,
        "per_page": per_page,
        "total": total,
        "pages": pages,
        "next_page": next_page,
        "prev_page": prev_page,
    }
    return items, meta

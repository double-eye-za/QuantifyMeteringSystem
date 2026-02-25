from __future__ import annotations

import logging
from typing import Any, Optional

from flask import request
from flask_login import current_user

from ..db import db
from ..models.audit_log import AuditLog

logger = logging.getLogger(__name__)


def log_action(
    action: str,
    *,
    entity_type: Optional[str] = None,
    entity_id: Optional[int] = None,
    old_values: Optional[dict[str, Any]] = None,
    new_values: Optional[dict[str, Any]] = None,
    request_id: Optional[str] = None,
) -> None:
    """Persist an audit log entry.
    Safe to call from any route; logs errors but does not break primary flow.
    """
    try:
        log = AuditLog(
            user_id=getattr(current_user, "id", None)
            if current_user.is_authenticated
            else None,
            action=action,
            entity_type=entity_type,
            entity_id=entity_id,
            old_values=(None if old_values is None else _safe_json(old_values)),
            new_values=(None if new_values is None else _safe_json(new_values)),
            ip_address=request.remote_addr if request else None,
            user_agent=(request.headers.get("User-Agent") if request else None),
            request_id=request_id,
        )
        db.session.add(log)
        db.session.commit()
    except Exception as exc:
        logger.error("Audit log failed for action=%s entity=%s/%s: %s",
                      action, entity_type, entity_id, exc)
        db.session.rollback()
        return


def _safe_json(obj: Any) -> str:
    import json

    try:
        return json.dumps(obj, default=str)
    except Exception as exc:
        logger.warning("Audit JSON serialization failed: %s", exc)
        return "{}"

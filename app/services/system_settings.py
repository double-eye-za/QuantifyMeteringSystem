from __future__ import annotations

from typing import Any, Iterable

from app.db import db
from app.models.system_setting import SystemSetting


def list_settings_as_dict() -> dict[str, Any]:
    settings = SystemSetting.query.all()
    result: dict[str, Any] = {}
    for s in settings:
        if s.setting_type == "boolean":
            result[s.setting_key] = (s.setting_value or "").lower() == "true"
        elif s.setting_type == "number":
            result[s.setting_key] = float(s.setting_value) if s.setting_value else 0
        else:
            result[s.setting_key] = s.setting_value
    return result


def save_settings(
    settings_data: Iterable[tuple[str, Any, str]], category: str, updated_by: int
) -> bool:
    for key, value, setting_type in settings_data:
        setting = SystemSetting.query.filter_by(setting_key=key).first()
        if setting:
            setting.setting_value = value
            setting.setting_type = setting_type
            setting.updated_by = updated_by
        else:
            setting = SystemSetting(
                setting_key=key,
                setting_value=value,
                setting_type=setting_type,
                category=category,
                updated_by=updated_by,
            )
            db.session.add(setting)
    db.session.commit()
    return True


def get_setting(key: str, default_value: Any = None) -> Any:
    s = SystemSetting.query.filter_by(setting_key=key).first()
    if not s:
        return default_value
    if s.setting_type == "boolean":
        return (s.setting_value or "").lower() == "true"
    if s.setting_type == "number":
        return float(s.setting_value) if s.setting_value else 0
    return s.setting_value


def save_setting(
    key: str,
    value: Any,
    setting_type: str,
    category: str,
    updated_by: int,
    description: str | None = None,
) -> SystemSetting:
    s = SystemSetting.query.filter_by(setting_key=key).first()
    if s:
        s.setting_value = value
        s.setting_type = setting_type
        s.updated_by = updated_by
        if description:
            s.description = description
    else:
        s = SystemSetting(
            setting_key=key,
            setting_value=value,
            setting_type=setting_type,
            category=category,
            updated_by=updated_by,
            description=description,
        )
        db.session.add(s)
    db.session.commit()
    return s

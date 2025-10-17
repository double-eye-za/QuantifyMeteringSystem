from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Optional

from sqlalchemy import CheckConstraint
from ..db import db


@dataclass
class SystemSetting(db.Model):
    __tablename__ = "system_settings"

    id: Optional[int]
    setting_key: str
    setting_value: Optional[str]
    setting_type: Optional[str]
    description: Optional[str]
    category: Optional[str]
    is_encrypted: Optional[bool]
    updated_by: Optional[int]
    created_at: Optional[datetime]
    updated_at: Optional[datetime]

    id = db.Column(db.Integer, primary_key=True, autoincrement=True, nullable=False)
    setting_key = db.Column(db.String(100), unique=True, nullable=False)
    setting_value = db.Column(db.Text)
    setting_type = db.Column(db.String(20))
    description = db.Column(db.Text)
    category = db.Column(db.String(50))
    is_encrypted = db.Column(db.Boolean, default=False)
    updated_by = db.Column(db.Integer, db.ForeignKey("users.id"))
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=True)
    updated_at = db.Column(
        db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=True
    )

    __table_args__ = (
        CheckConstraint(
            "setting_type IN ('string','number','boolean','json')",
            name="ck_system_settings_type",
        ),
    )

    @staticmethod
    def get_all_settings():
        """Get all system settings as a dictionary"""
        settings = SystemSetting.query.all()
        settings_dict = {}

        for setting in settings:
            # Convert value based on type
            if setting.setting_type == "boolean":
                settings_dict[setting.setting_key] = (
                    setting.setting_value.lower() == "true"
                )
            elif setting.setting_type == "number":
                settings_dict[setting.setting_key] = (
                    float(setting.setting_value) if setting.setting_value else 0
                )
            else:
                settings_dict[setting.setting_key] = setting.setting_value

        return settings_dict

    @staticmethod
    def save_settings(settings_data, category, updated_by):
        """Save multiple settings for a category"""
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

    @staticmethod
    def get_setting(key, default_value=None):
        """Get a single setting by key"""
        setting = SystemSetting.query.filter_by(setting_key=key).first()
        if not setting:
            return default_value

        # Convert value based on type
        if setting.setting_type == "boolean":
            return setting.setting_value.lower() == "true"
        elif setting.setting_type == "number":
            return float(setting.setting_value) if setting.setting_value else 0
        else:
            return setting.setting_value

    @staticmethod
    def save_setting(key, value, setting_type, category, updated_by, description=None):
        """Save a single setting"""
        setting = SystemSetting.query.filter_by(setting_key=key).first()
        if setting:
            setting.setting_value = value
            setting.setting_type = setting_type
            setting.updated_by = updated_by
            if description:
                setting.description = description
        else:
            setting = SystemSetting(
                setting_key=key,
                setting_value=value,
                setting_type=setting_type,
                category=category,
                updated_by=updated_by,
                description=description,
            )
            db.session.add(setting)

        db.session.commit()
        return setting

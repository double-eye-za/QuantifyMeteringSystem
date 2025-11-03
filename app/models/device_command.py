from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Optional

from sqlalchemy import CheckConstraint
from ..db import db


@dataclass
class DeviceCommand(db.Model):
    """Queue for commands to be sent to LoRaWAN devices via backend"""
    __tablename__ = "device_commands"

    id: Optional[int]
    meter_id: int
    device_eui: str
    command_type: str
    command_data: Optional[str]
    status: str
    priority: int
    scheduled_at: Optional[datetime]
    sent_at: Optional[datetime]
    completed_at: Optional[datetime]
    error_message: Optional[str]
    retry_count: int
    max_retries: int
    created_by: Optional[int]
    created_at: datetime

    id = db.Column(db.Integer, primary_key=True, autoincrement=True, nullable=False)
    meter_id = db.Column(db.Integer, db.ForeignKey("meters.id"), nullable=False, index=True)
    device_eui = db.Column(db.String(16), nullable=False, index=True)
    command_type = db.Column(db.String(50), nullable=False)  # switch_on, switch_off, update_credit, read_meter, etc.
    command_data = db.Column(db.Text, nullable=True)  # JSON data for command parameters
    status = db.Column(db.String(20), default="pending", nullable=False, index=True)
    priority = db.Column(db.Integer, default=5, nullable=False)  # 1=highest, 10=lowest

    # Scheduling and tracking
    scheduled_at = db.Column(db.DateTime, nullable=True)  # When to send command (null = immediate)
    sent_at = db.Column(db.DateTime, nullable=True)  # When command was sent to backend
    completed_at = db.Column(db.DateTime, nullable=True)  # When command was confirmed
    error_message = db.Column(db.Text, nullable=True)  # Error details if failed
    retry_count = db.Column(db.Integer, default=0, nullable=False)
    max_retries = db.Column(db.Integer, default=3, nullable=False)

    # Audit fields
    created_by = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    __table_args__ = (
        CheckConstraint(
            "command_type IN ('switch_on','switch_off','update_credit','read_meter','reset_meter','update_config')",
            name='ck_device_commands_type'
        ),
        CheckConstraint(
            "status IN ('pending','queued','sent','completed','failed','cancelled')",
            name='ck_device_commands_status'
        ),
        CheckConstraint(
            'priority >= 1 AND priority <= 10',
            name='ck_device_commands_priority'
        ),
    )

    def to_dict(self):
        return {
            "id": self.id,
            "meter_id": self.meter_id,
            "device_eui": self.device_eui,
            "command_type": self.command_type,
            "command_data": self.command_data,
            "status": self.status,
            "priority": self.priority,
            "scheduled_at": self.scheduled_at.isoformat() if self.scheduled_at else None,
            "sent_at": self.sent_at.isoformat() if self.sent_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "error_message": self.error_message,
            "retry_count": self.retry_count,
            "max_retries": self.max_retries,
            "created_by": self.created_by,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }

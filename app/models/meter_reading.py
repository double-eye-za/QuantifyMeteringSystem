from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Optional

from sqlalchemy import CheckConstraint
from ..db import db


@dataclass
class MeterReading(db.Model):
    __tablename__ = "meter_readings"

    id: Optional[int]
    meter_id: int
    reading_value: float
    reading_date: datetime
    reading_type: Optional[str]
    consumption_since_last: Optional[float]
    is_validated: Optional[bool]
    validation_date: Optional[datetime]
    created_at: Optional[datetime]
    pulse_count: Optional[int]
    temperature: Optional[float]
    humidity: Optional[float]
    rssi: Optional[int]
    snr: Optional[float]
    battery_level: Optional[int]
    raw_payload: Optional[str]

    id = db.Column(db.Integer, primary_key=True, autoincrement=True, nullable=False)
    meter_id = db.Column(db.Integer, db.ForeignKey("meters.id"), nullable=False)
    reading_value = db.Column(db.Numeric(15, 3), nullable=False)
    reading_date = db.Column(db.DateTime, nullable=False)
    reading_type = db.Column(db.String(20), default="automatic")
    consumption_since_last = db.Column(db.Numeric(15, 3))
    is_validated = db.Column(db.Boolean, default=False)
    validation_date = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # LoRaWAN Device Telemetry (for backend MQTT integration)
    pulse_count = db.Column(db.Integer, nullable=True)  # For pulse counter devices (Milesight EM300-DI)
    temperature = db.Column(db.Numeric(5, 2), nullable=True)  # Device temperature (°C)
    humidity = db.Column(db.Numeric(5, 2), nullable=True)  # Device humidity (%)
    rssi = db.Column(db.Integer, nullable=True)  # Signal strength (dBm)
    snr = db.Column(db.Numeric(5, 2), nullable=True)  # Signal-to-noise ratio (dB)
    battery_level = db.Column(db.Integer, nullable=True)  # Battery percentage (0-100)
    raw_payload = db.Column(db.Text, nullable=True)  # Store original hex/JSON payload

    __table_args__ = (
        CheckConstraint(
            "reading_type IN ('automatic','manual','estimated')",
            name="ck_meter_readings_type",
        ),
    )

    def to_dict(self):
        return {
            "id": self.id,
            "meter_id": self.meter_id,
            "reading_value": float(self.reading_value),
            "reading_date": self.reading_date.isoformat(),
            "reading_type": self.reading_type,
            "consumption_since_last": float(self.consumption_since_last)
            if self.consumption_since_last is not None
            else None,
            "is_validated": self.is_validated,
            "validation_date": self.validation_date.isoformat()
            if self.validation_date
            else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "pulse_count": self.pulse_count,
            "temperature": float(self.temperature) if self.temperature is not None else None,
            "humidity": float(self.humidity) if self.humidity is not None else None,
            "rssi": self.rssi,
            "snr": float(self.snr) if self.snr is not None else None,
            "battery_level": self.battery_level,
            "raw_payload": self.raw_payload,
        }

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
    voltage: Optional[float]
    current: Optional[float]
    power: Optional[float]
    power_factor: Optional[float]
    frequency: Optional[float]
    flow_rate: Optional[float]
    pressure: Optional[float]
    status: Optional[str]
    is_billed: Optional[bool]
    billed_at: Optional[datetime]
    transaction_id: Optional[int]

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

    # Electrical parameters (for electricity meters)
    voltage = db.Column(db.Numeric(6, 2), nullable=True)  # Voltage (V)
    current = db.Column(db.Numeric(8, 3), nullable=True)  # Current (A)
    power = db.Column(db.Numeric(10, 3), nullable=True)  # Active power (kW)
    power_factor = db.Column(db.Numeric(4, 3), nullable=True)  # Power factor
    frequency = db.Column(db.Numeric(5, 2), nullable=True)  # Frequency (Hz)

    # Water meter parameters
    flow_rate = db.Column(db.Numeric(10, 3), nullable=True)  # Flow rate (L/h)
    pressure = db.Column(db.Numeric(6, 2), nullable=True)  # Pressure (bar or kPa)

    status = db.Column(db.String(50), nullable=True)  # Meter status (online, offline, error, etc.)

    # Billing tracking fields (for consumption deduction)
    is_billed = db.Column(db.Boolean, default=False, nullable=False)
    billed_at = db.Column(db.DateTime, nullable=True)
    transaction_id = db.Column(db.Integer, db.ForeignKey("transactions.id"), nullable=True)

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
            "voltage": float(self.voltage) if self.voltage is not None else None,
            "current": float(self.current) if self.current is not None else None,
            "power": float(self.power) if self.power is not None else None,
            "power_factor": float(self.power_factor) if self.power_factor is not None else None,
            "frequency": float(self.frequency) if self.frequency is not None else None,
            "flow_rate": float(self.flow_rate) if self.flow_rate is not None else None,
            "pressure": float(self.pressure) if self.pressure is not None else None,
            "status": self.status,
            "is_billed": self.is_billed,
            "billed_at": self.billed_at.isoformat() if self.billed_at else None,
            "transaction_id": self.transaction_id,
        }

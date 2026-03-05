"""
KPM31 Telemetry Model — stores full raw data from Compere KPM31 4G electricity meters.

Supports both single-phase and three-phase variants. Single-phase fields are NULL
for three-phase meters and vice versa. System totals (zyggl, zwggl, etc.) are
common to both variants.

NOTE: The matching ORM model in Quantify-Metering-Monitor must be kept in sync.
See: Quantify-Metering-Monitor/water_meter_module/models.py
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Optional

from sqlalchemy import CheckConstraint, Index
from ..db import db


@dataclass
class Kpm31Telemetry(db.Model):
    __tablename__ = "kpm31_telemetry"

    # Type annotations for dataclass
    id: Optional[int]
    meter_id: int
    reading_id: Optional[int]
    recorded_at: datetime
    device_timestamp: Optional[str]
    phase_type: str

    # Primary key and relationships
    id = db.Column(db.Integer, primary_key=True, autoincrement=True, nullable=False)
    meter_id = db.Column(db.Integer, db.ForeignKey("meters.id"), nullable=False, index=True)
    reading_id = db.Column(db.Integer, db.ForeignKey("meter_readings.id"), nullable=True)

    # Timestamps
    recorded_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    device_timestamp = db.Column(db.String(14), nullable=True)  # Raw 'time' field (YYYYMMDDHHmmss)

    # Phase type discriminator
    phase_type = db.Column(db.String(10), nullable=False)  # 'single' or 'three'

    # ─── Single-phase only fields ───
    voltage = db.Column(db.Numeric(6, 2), nullable=True)           # u — voltage (V)
    current = db.Column(db.Numeric(8, 3), nullable=True)           # i — current (A)
    prepaid_balance_kwh = db.Column(db.Numeric(12, 3), nullable=True)  # sydn — prepaid balance (kWh)
    current_demand = db.Column(db.Numeric(8, 3), nullable=True)    # idm — current demand (A)

    # ─── Three-phase per-phase voltages ───
    voltage_a = db.Column(db.Numeric(6, 2), nullable=True)        # ua
    voltage_b = db.Column(db.Numeric(6, 2), nullable=True)        # ub
    voltage_c = db.Column(db.Numeric(6, 2), nullable=True)        # uc
    voltage_ab = db.Column(db.Numeric(6, 2), nullable=True)       # uab — line-to-line
    voltage_bc = db.Column(db.Numeric(6, 2), nullable=True)       # ubc
    voltage_ca = db.Column(db.Numeric(6, 2), nullable=True)       # uca

    # ─── Three-phase per-phase currents ───
    current_a = db.Column(db.Numeric(8, 3), nullable=True)        # ia
    current_b = db.Column(db.Numeric(8, 3), nullable=True)        # ib
    current_c = db.Column(db.Numeric(8, 3), nullable=True)        # ic

    # ─── Three-phase per-phase power ───
    active_power_a = db.Column(db.Numeric(10, 3), nullable=True)  # pa (kW)
    active_power_b = db.Column(db.Numeric(10, 3), nullable=True)  # pb
    active_power_c = db.Column(db.Numeric(10, 3), nullable=True)  # pc
    apparent_power_a = db.Column(db.Numeric(10, 3), nullable=True)  # sa (kVA)
    apparent_power_b = db.Column(db.Numeric(10, 3), nullable=True)  # sb
    apparent_power_c = db.Column(db.Numeric(10, 3), nullable=True)  # sc
    power_factor_a = db.Column(db.Numeric(4, 3), nullable=True)   # pfa
    power_factor_b = db.Column(db.Numeric(4, 3), nullable=True)   # pfb
    power_factor_c = db.Column(db.Numeric(4, 3), nullable=True)   # pfc

    # ─── System totals (both variants) ───
    total_active_power = db.Column(db.Numeric(10, 3), nullable=True)   # zyggl (kW)
    total_reactive_power = db.Column(db.Numeric(10, 3), nullable=True)  # zwggl (kvar)
    total_apparent_power = db.Column(db.Numeric(10, 3), nullable=True)  # zszgl (kVA)
    total_power_factor = db.Column(db.Numeric(4, 3), nullable=True)    # zglys
    frequency = db.Column(db.Numeric(5, 2), nullable=True)            # f (Hz)

    # ─── Demand values (both variants) ───
    active_demand = db.Column(db.Numeric(10, 3), nullable=True)   # pdm (kW)
    reactive_demand = db.Column(db.Numeric(10, 3), nullable=True)  # qdm (kvar)
    apparent_demand = db.Column(db.Numeric(10, 3), nullable=True)  # sdm (kVA)

    # ─── Sequence components (three-phase only) ───
    voltage_zero_seq = db.Column(db.Numeric(6, 2), nullable=True)  # u0
    voltage_pos_seq = db.Column(db.Numeric(6, 2), nullable=True)   # u+
    voltage_neg_seq = db.Column(db.Numeric(6, 2), nullable=True)   # u-
    current_zero_seq = db.Column(db.Numeric(8, 3), nullable=True)  # i0
    current_pos_seq = db.Column(db.Numeric(8, 3), nullable=True)   # i+
    current_neg_seq = db.Column(db.Numeric(8, 3), nullable=True)   # i-

    # ─── Fundamental/measured values (three-phase only) ───
    # uxja/uxjb/uxjc — appear to be fundamental/reference voltage measurements
    # Values observed: 228.889V, 202.809V (actual voltage magnitudes, not percentages)
    voltage_fund_a = db.Column(db.Numeric(6, 2), nullable=True)   # uxja
    voltage_fund_b = db.Column(db.Numeric(6, 2), nullable=True)   # uxjb
    voltage_fund_c = db.Column(db.Numeric(6, 2), nullable=True)   # uxjc
    current_fund_a = db.Column(db.Numeric(8, 3), nullable=True)   # ixja
    current_fund_b = db.Column(db.Numeric(8, 3), nullable=True)   # ixjb
    current_fund_c = db.Column(db.Numeric(8, 3), nullable=True)   # ixjc

    # ─── Unbalance rates (three-phase only) ───
    voltage_unbalance = db.Column(db.Numeric(5, 2), nullable=True)  # unb (%)
    current_unbalance = db.Column(db.Numeric(5, 2), nullable=True)  # inb (%)

    # ─── Raw payload & metadata ───
    raw_payload = db.Column(db.Text, nullable=True)
    isend = db.Column(db.String(5), nullable=True)

    __table_args__ = (
        CheckConstraint(
            "phase_type IN ('single','three')",
            name="ck_kpm31_telemetry_phase_type",
        ),
        Index("ix_kpm31_telemetry_meter_recorded", "meter_id", recorded_at.desc()),
        Index("ix_kpm31_telemetry_recorded_at", "recorded_at"),
    )

    def to_dict(self):
        def _f(val):
            return float(val) if val is not None else None

        return {
            "id": self.id,
            "meter_id": self.meter_id,
            "reading_id": self.reading_id,
            "recorded_at": self.recorded_at.isoformat() if self.recorded_at else None,
            "device_timestamp": self.device_timestamp,
            "phase_type": self.phase_type,
            # Single-phase
            "voltage": _f(self.voltage),
            "current": _f(self.current),
            "prepaid_balance_kwh": _f(self.prepaid_balance_kwh),
            "current_demand": _f(self.current_demand),
            # Three-phase voltages
            "voltage_a": _f(self.voltage_a),
            "voltage_b": _f(self.voltage_b),
            "voltage_c": _f(self.voltage_c),
            "voltage_ab": _f(self.voltage_ab),
            "voltage_bc": _f(self.voltage_bc),
            "voltage_ca": _f(self.voltage_ca),
            # Three-phase currents
            "current_a": _f(self.current_a),
            "current_b": _f(self.current_b),
            "current_c": _f(self.current_c),
            # Three-phase power
            "active_power_a": _f(self.active_power_a),
            "active_power_b": _f(self.active_power_b),
            "active_power_c": _f(self.active_power_c),
            "apparent_power_a": _f(self.apparent_power_a),
            "apparent_power_b": _f(self.apparent_power_b),
            "apparent_power_c": _f(self.apparent_power_c),
            "power_factor_a": _f(self.power_factor_a),
            "power_factor_b": _f(self.power_factor_b),
            "power_factor_c": _f(self.power_factor_c),
            # System totals
            "total_active_power": _f(self.total_active_power),
            "total_reactive_power": _f(self.total_reactive_power),
            "total_apparent_power": _f(self.total_apparent_power),
            "total_power_factor": _f(self.total_power_factor),
            "frequency": _f(self.frequency),
            # Demand
            "active_demand": _f(self.active_demand),
            "reactive_demand": _f(self.reactive_demand),
            "apparent_demand": _f(self.apparent_demand),
            # Sequence components
            "voltage_zero_seq": _f(self.voltage_zero_seq),
            "voltage_pos_seq": _f(self.voltage_pos_seq),
            "voltage_neg_seq": _f(self.voltage_neg_seq),
            "current_zero_seq": _f(self.current_zero_seq),
            "current_pos_seq": _f(self.current_pos_seq),
            "current_neg_seq": _f(self.current_neg_seq),
            # Fundamental/measured
            "voltage_fund_a": _f(self.voltage_fund_a),
            "voltage_fund_b": _f(self.voltage_fund_b),
            "voltage_fund_c": _f(self.voltage_fund_c),
            "current_fund_a": _f(self.current_fund_a),
            "current_fund_b": _f(self.current_fund_b),
            "current_fund_c": _f(self.current_fund_c),
            # Unbalance
            "voltage_unbalance": _f(self.voltage_unbalance),
            "current_unbalance": _f(self.current_unbalance),
            # Metadata
            "isend": self.isend,
        }

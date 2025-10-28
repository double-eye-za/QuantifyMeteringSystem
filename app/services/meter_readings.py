from __future__ import annotations

from datetime import datetime
from typing import Optional

from app.models.meter_reading import MeterReading


def list_for_meter(
    meter_id: int, start: Optional[datetime] = None, end: Optional[datetime] = None
):
    q = MeterReading.query.filter_by(meter_id=meter_id)
    if start:
        q = q.filter(MeterReading.reading_date >= start)
    if end:
        q = q.filter(MeterReading.reading_date <= end)
    return q.order_by(MeterReading.reading_date.desc())

# Meter Consumption to Wallet Deduction - Implementation Plan

## Overview

Implement automatic wallet deductions when meter usage is logged. Each meter reading will trigger a real-time calculation and deduction from the unit's wallet, creating a consumption transaction for full audit trail.

## User Requirements

| Requirement | Decision |
|-------------|----------|
| **Reading Source** | External LoRaWAN server pushes readings (trigger mechanism TBD with client) |
| **Deduction Timing** | Real-time when readings are processed |
| **Zero Balance** | Allow negative balances (debt accumulation) |
| **Transaction Granularity** | One transaction per meter reading |

---

## Architecture Overview

```
┌─────────────────────┐
│  LoRaWAN Server     │
│  (External)         │
└──────────┬──────────┘
           │ Writes to DB
           ▼
┌─────────────────────┐
│  meter_readings     │
│  table              │
│  - consumption_     │
│    since_last       │
│  - is_billed=False  │
└──────────┬──────────┘
           │ Trigger (TBD)
           ▼
┌─────────────────────┐
│  Consumption        │
│  Service            │
│  process_meter_     │
│  reading()          │
└──────────┬──────────┘
           │
     ┌─────┴─────┐
     ▼           ▼
┌─────────┐ ┌─────────┐
│ Wallet  │ │ Trans-  │
│ Balance │ │ action  │
│ Deduct  │ │ Record  │
└─────────┘ └─────────┘
```

---

## Phase 1: Database Schema Changes

### 1.1 Migration: Add Billing Tracking to MeterReading

**Migration file**: `migrations/versions/xxx_add_billing_fields_to_meter_readings.py`

Add columns to `meter_readings` table:

| Column | Type | Default | Purpose |
|--------|------|---------|---------|
| `is_billed` | Boolean | False | Flag if reading has been processed for billing |
| `billed_at` | DateTime | NULL | Timestamp when billing was processed |
| `transaction_id` | Integer FK | NULL | Link to the consumption transaction created |

**SQL**:
```sql
ALTER TABLE meter_readings ADD COLUMN is_billed BOOLEAN NOT NULL DEFAULT FALSE;
ALTER TABLE meter_readings ADD COLUMN billed_at TIMESTAMP;
ALTER TABLE meter_readings ADD COLUMN transaction_id INTEGER REFERENCES transactions(id);

CREATE INDEX ix_meter_readings_unbilled ON meter_readings(meter_id, is_billed) WHERE is_billed = FALSE;
```

### 1.2 Migration: Add Solar Free Allocation Tracking

**Migration file**: `migrations/versions/xxx_add_solar_allocation_tracking.py`

Create new table `solar_monthly_usage`:

| Column | Type | Purpose |
|--------|------|---------|
| `id` | Integer PK | Primary key |
| `unit_id` | Integer FK | Reference to unit |
| `year_month` | String(7) | Format: "YYYY-MM" |
| `free_allocation_kwh` | Numeric(10,2) | Estate's free allocation for this month |
| `used_kwh` | Numeric(10,2) | Free kWh consumed so far |
| `paid_kwh` | Numeric(10,2) | Paid kWh consumed |
| `created_at` | DateTime | Record creation |
| `updated_at` | DateTime | Last update |

**Constraints**:
- Unique: `(unit_id, year_month)`
- Foreign key: `unit_id → units.id`

---

## Phase 2: Model Updates

### 2.1 Update MeterReading Model

**File**: `app/models/meter_reading.py`

```python
# Add after existing fields (around line 70)

# Billing tracking fields
is_billed = db.Column(db.Boolean, default=False, nullable=False)
billed_at = db.Column(db.DateTime, nullable=True)
transaction_id = db.Column(db.Integer, db.ForeignKey("transactions.id"), nullable=True)

# Relationship to transaction
billing_transaction = db.relationship(
    "Transaction",
    backref="meter_reading",
    uselist=False,
    foreign_keys=[transaction_id]
)
```

**Update `to_dict()` method** to include:
```python
"is_billed": self.is_billed,
"billed_at": self.billed_at.isoformat() if self.billed_at else None,
"transaction_id": self.transaction_id,
```

### 2.2 Create SolarMonthlyUsage Model

**File**: `app/models/solar_monthly_usage.py` (NEW)

```python
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Optional

from ..db import db


@dataclass
class SolarMonthlyUsage(db.Model):
    """Tracks monthly solar free allocation usage per unit."""

    __tablename__ = "solar_monthly_usage"

    id: Optional[int]
    unit_id: int
    year_month: str
    free_allocation_kwh: float
    used_kwh: float
    paid_kwh: float
    created_at: Optional[datetime]
    updated_at: Optional[datetime]

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    unit_id = db.Column(db.Integer, db.ForeignKey("units.id"), nullable=False)
    year_month = db.Column(db.String(7), nullable=False)  # "YYYY-MM"
    free_allocation_kwh = db.Column(db.Numeric(10, 2), nullable=False)
    used_kwh = db.Column(db.Numeric(10, 2), default=0.00, nullable=False)
    paid_kwh = db.Column(db.Numeric(10, 2), default=0.00, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        db.UniqueConstraint('unit_id', 'year_month', name='uq_solar_usage_unit_month'),
    )

    # Relationship
    unit = db.relationship("Unit", backref="solar_monthly_usages")

    def to_dict(self):
        return {
            "id": self.id,
            "unit_id": self.unit_id,
            "year_month": self.year_month,
            "free_allocation_kwh": float(self.free_allocation_kwh),
            "used_kwh": float(self.used_kwh),
            "paid_kwh": float(self.paid_kwh),
            "remaining_free_kwh": max(0, float(self.free_allocation_kwh) - float(self.used_kwh)),
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
```

### 2.3 Update models/__init__.py

Add import:
```python
from .solar_monthly_usage import SolarMonthlyUsage
```

Add to `__all__`:
```python
"SolarMonthlyUsage",
```

---

## Phase 3: Core Consumption Service

### 3.1 Create Consumption Service

**File**: `app/services/consumption_service.py` (NEW)

This is the core service that processes meter readings and creates wallet deductions.

#### Result Dataclass

```python
from dataclasses import dataclass
from typing import Optional

@dataclass
class ConsumptionResult:
    """Result of processing a meter reading for consumption billing."""
    success: bool
    reading_id: int
    transaction_id: Optional[int] = None
    amount_charged: float = 0.0
    consumption: float = 0.0
    rate_applied: float = 0.0
    balance_before: float = 0.0
    balance_after: float = 0.0
    error_code: Optional[str] = None
    error_message: Optional[str] = None
    skipped: bool = False
    skip_reason: Optional[str] = None
```

#### Main Processing Function

```python
def process_meter_reading(reading_id: int) -> ConsumptionResult:
    """
    Process a single meter reading for consumption billing.

    This function is idempotent - safe to call multiple times.

    Flow:
    1. Fetch reading, check if already billed
    2. Find unit and wallet for the meter
    3. Get rate structure (unit → estate → default)
    4. Calculate charge with markup
    5. Handle solar free allocation if applicable
    6. Deduct from wallet (allows negative)
    7. Create consumption transaction
    8. Mark reading as billed
    9. Trigger low balance notification if needed

    Returns:
        ConsumptionResult with success/error details
    """
```

#### Helper Functions

| Function | Purpose |
|----------|---------|
| `_meter_type_to_utility(meter_type)` | Maps 'electricity'→'electricity', 'bulk_water'→'water', etc. |
| `_get_rate_structure(unit, meter_type)` | Gets rate with fallback: unit → estate → default |
| `_get_markup_percent(estate, utility_type)` | Gets markup from estate |
| `_calculate_charge(consumption, utility_type, rate_structure, markup)` | Uses existing `app/utils/rates.py` |
| `_apply_solar_free_allocation(unit_id, consumption, estate)` | Returns `(free_kwh, billable_kwh)` |
| `_deduct_from_wallet(wallet, utility_type, amount)` | Returns `(balance_before, balance_after)` |
| `_create_consumption_transaction(...)` | Creates Transaction record |
| `get_unbilled_readings(meter_id, limit)` | Query helper for batch processing |
| `process_batch_readings(reading_ids)` | Batch wrapper |

#### Rate Structure Lookup Logic

```python
def _get_rate_structure(unit: Unit, meter_type: str) -> Dict[str, Any]:
    """
    Get rate structure with fallback chain:
    1. Unit's rate table (if assigned)
    2. Estate's rate table (if assigned)
    3. System default rate
    """
    utility_type = _meter_type_to_utility(meter_type)
    estate = Estate.query.get(unit.estate_id) if unit.estate_id else None

    # Determine which rate table to use
    rate_table_id = None
    if utility_type == "electricity":
        rate_table_id = unit.electricity_rate_table_id or (
            estate.electricity_rate_table_id if estate else None
        )
    elif utility_type == "water":
        rate_table_id = unit.water_rate_table_id or (
            estate.water_rate_table_id if estate else None
        )

    # Get rate structure from table
    if rate_table_id:
        rate_table = RateTable.query.get(rate_table_id)
        if rate_table and rate_table.rate_structure:
            return json.loads(rate_table.rate_structure) if isinstance(
                rate_table.rate_structure, str
            ) else rate_table.rate_structure

    # Fallback to default
    return get_default_rate_structure(utility_type)
```

#### Wallet Deduction Logic

```python
def _deduct_from_wallet(wallet: Wallet, utility_type: str, amount: float) -> Tuple[float, float]:
    """
    Deduct amount from the appropriate wallet balance.
    Allows negative balances (debt accumulation).

    Returns:
        Tuple of (balance_before, balance_after)
    """
    # Map utility type to wallet balance field
    balance_field_map = {
        "electricity": "electricity_balance",
        "water": "water_balance",
        "solar": "solar_balance",
        "hot_water": "hot_water_balance"
    }
    balance_field = balance_field_map.get(utility_type, "balance")

    # Get current balance
    balance_before = float(getattr(wallet, balance_field) or 0)

    # Calculate new balance (can go negative)
    balance_after = balance_before - amount

    # Update wallet
    setattr(wallet, balance_field, balance_after)
    wallet.updated_at = datetime.utcnow()

    return (balance_before, balance_after)
```

#### Solar Free Allocation Logic

```python
def _apply_solar_free_allocation(
    unit_id: int,
    consumption: float,
    estate: Estate
) -> Tuple[float, float]:
    """
    Apply solar free allocation for the current month.

    Args:
        unit_id: The unit ID
        consumption: Solar consumption in kWh
        estate: The estate (for free allocation setting)

    Returns:
        Tuple of (free_kwh_used, billable_kwh)
    """
    year_month = datetime.utcnow().strftime("%Y-%m")
    free_allocation = float(estate.solar_free_allocation_kwh or 50.0)

    # Get or create monthly tracking record
    usage = SolarMonthlyUsage.query.filter_by(
        unit_id=unit_id,
        year_month=year_month
    ).first()

    if not usage:
        usage = SolarMonthlyUsage(
            unit_id=unit_id,
            year_month=year_month,
            free_allocation_kwh=free_allocation,
            used_kwh=0,
            paid_kwh=0
        )
        db.session.add(usage)

    # Calculate remaining free allocation
    remaining_free = max(0, free_allocation - float(usage.used_kwh))

    if remaining_free >= consumption:
        # All consumption is free
        usage.used_kwh = float(usage.used_kwh) + consumption
        return (consumption, 0.0)
    else:
        # Partial free, rest is billable
        billable = consumption - remaining_free
        usage.used_kwh = free_allocation  # Max out free usage
        usage.paid_kwh = float(usage.paid_kwh) + billable
        return (remaining_free, billable)
```

#### Transaction Creation

```python
def _create_consumption_transaction(
    wallet: Wallet,
    meter: Meter,
    utility_type: str,
    consumption: float,
    amount: float,
    balance_before: float,
    balance_after: float,
    rate_applied: float,
    reading: MeterReading
) -> Transaction:
    """Create a consumption transaction with full audit trail."""

    # Determine transaction type
    txn_type = f"consumption_{utility_type}"

    # Generate unique transaction number
    txn_number = f"CON{datetime.now().strftime('%Y%m%d%H%M%S')}{wallet.id}"

    # Determine unit (kWh for electricity/solar, kL for water)
    unit_label = "kWh" if utility_type in ["electricity", "solar"] else "kL"

    txn = Transaction(
        transaction_number=txn_number,
        wallet_id=wallet.id,
        transaction_type=txn_type,
        amount=amount,
        balance_before=balance_before,
        balance_after=balance_after,
        reference=f"Meter: {meter.serial_number}",
        description=f"Consumption: {consumption:.3f} {unit_label} @ R{rate_applied:.4f}/{unit_label}",
        payment_method="system",
        meter_id=meter.id,
        consumption_kwh=consumption,
        rate_applied=rate_applied,
        status="completed",
        completed_at=datetime.utcnow()
    )
    db.session.add(txn)
    return txn
```

---

## Phase 4: Trigger Mechanisms

The core `process_meter_reading()` function is trigger-agnostic. Choose one or more:

### Option A: Celery Polling Task (Recommended for LoRaWAN)

**File**: `app/tasks/consumption_tasks.py` (NEW)

```python
from celery import shared_task
from celery.utils.log import get_task_logger

logger = get_task_logger(__name__)

@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def process_unbilled_readings_task(self, meter_id: int = None, limit: int = 100):
    """
    Process all unbilled meter readings.

    Scheduled to run every 15 minutes via Celery Beat.
    """
    from ..services.consumption_service import get_unbilled_readings, process_meter_reading

    readings = get_unbilled_readings(meter_id=meter_id, limit=limit)
    logger.info(f"Found {len(readings)} unbilled readings to process")

    processed = 0
    errors = 0

    for reading in readings:
        try:
            result = process_meter_reading(reading.id)
            if result.success:
                processed += 1
                logger.info(f"Reading {reading.id}: R{result.amount_charged:.2f} charged")
            elif result.skipped:
                logger.debug(f"Reading {reading.id}: Skipped - {result.skip_reason}")
            else:
                errors += 1
                logger.error(f"Reading {reading.id}: Failed - {result.error_message}")
        except Exception as e:
            errors += 1
            logger.exception(f"Reading {reading.id}: Exception - {e}")

    logger.info(f"Batch complete: {processed} processed, {errors} errors")
    return {"processed": processed, "errors": errors}


@shared_task(bind=True, max_retries=3, default_retry_delay=30)
def process_single_reading_task(self, reading_id: int):
    """Process a single meter reading (for async triggering)."""
    from ..services.consumption_service import process_meter_reading

    result = process_meter_reading(reading_id)
    return result.__dict__
```

**Update `celery_app.py`**:

```python
# Add to include list
include=['app.tasks.notification_tasks', 'app.tasks.consumption_tasks']

# Add to beat_schedule
'process-unbilled-readings': {
    'task': 'app.tasks.consumption_tasks.process_unbilled_readings_task',
    'schedule': crontab(minute='*/15'),  # Every 15 minutes
    'options': {'queue': 'consumption'}
},
```

### Option B: API Endpoint

**File**: `app/routes/v1/meters.py` (ADD)

```python
@bp.route("/readings/<int:reading_id>/process", methods=["POST"])
@login_required
def process_reading(reading_id):
    """Manually trigger processing of a single meter reading."""
    from app.services.consumption_service import process_meter_reading

    result = process_meter_reading(reading_id)

    if result.success:
        return jsonify({
            "status": "success",
            "transaction_id": result.transaction_id,
            "amount_charged": result.amount_charged,
            "consumption": result.consumption,
            "balance_after": result.balance_after
        })
    elif result.skipped:
        return jsonify({
            "status": "skipped",
            "reason": result.skip_reason
        })
    else:
        return jsonify({
            "status": "error",
            "error_code": result.error_code,
            "message": result.error_message
        }), 400


@bp.route("/readings/unbilled", methods=["GET"])
@login_required
def list_unbilled_readings():
    """List meter readings that haven't been processed for billing."""
    from app.services.consumption_service import get_unbilled_readings

    meter_id = request.args.get("meter_id", type=int)
    limit = request.args.get("limit", 100, type=int)

    readings = get_unbilled_readings(meter_id=meter_id, limit=limit)

    return jsonify({
        "readings": [r.to_dict() for r in readings],
        "count": len(readings)
    })
```

### Option C: Webhook for LoRaWAN Server

If the LoRaWAN server can call an endpoint after inserting readings:

```python
@bp.route("/webhook/reading-created", methods=["POST"])
def webhook_reading_created():
    """Webhook called by LoRaWAN server after inserting a reading."""
    data = request.get_json()
    reading_id = data.get("reading_id")

    if not reading_id:
        return jsonify({"error": "reading_id required"}), 400

    # Process async
    from app.tasks.consumption_tasks import process_single_reading_task
    process_single_reading_task.delay(reading_id)

    return jsonify({"status": "queued"})
```

---

## Phase 5: Error Handling

### Error Codes

| Code | Cause | Action |
|------|-------|--------|
| `READING_NOT_FOUND` | Reading ID doesn't exist | Return 404, log warning |
| `ALREADY_BILLED` | Reading already processed | Return skip, no action (idempotent) |
| `NO_UNIT_ASSIGNED` | Meter not assigned to any unit | Log warning, skip reading |
| `NO_WALLET` | Unit has no wallet | Log error, skip (should auto-create) |
| `NO_CONSUMPTION_VALUE` | `consumption_since_last` is NULL | Skip, wait for value to be set |
| `NO_RATE_STRUCTURE` | Cannot determine rates | Use default rates, log warning |
| `DB_ERROR` | Database operation failed | Rollback, retry with backoff |

### Transaction Safety

All operations wrapped in a database transaction:

```python
def process_meter_reading(reading_id: int) -> ConsumptionResult:
    try:
        # ... all processing logic ...
        db.session.commit()
        return ConsumptionResult(success=True, ...)
    except Exception as e:
        db.session.rollback()
        logger.exception(f"Error processing reading {reading_id}")
        return ConsumptionResult(
            success=False,
            reading_id=reading_id,
            error_code="PROCESSING_ERROR",
            error_message=str(e)
        )
```

---

## Phase 6: Low Balance Notification Integration

After deducting from wallet, check balance and trigger notification:

```python
# At end of process_meter_reading(), after successful deduction:

def _check_low_balance_notification(wallet: Wallet, balance_after: float):
    """Check if balance is below threshold and send notification."""
    threshold = float(wallet.low_balance_threshold or 50.0)

    if balance_after < threshold:
        from app.services.notification_service import NotificationService

        is_critical = balance_after < (threshold * 0.2)  # Critical if below 20% of threshold

        NotificationService.notify_low_credit(
            wallet=wallet,
            threshold=threshold,
            is_critical=is_critical
        )
```

---

## Files Summary

### Files to Create

| File | Purpose |
|------|---------|
| `migrations/versions/xxx_add_billing_fields.py` | Add is_billed, billed_at, transaction_id to meter_readings |
| `migrations/versions/xxx_add_solar_tracking.py` | Create solar_monthly_usage table |
| `app/models/solar_monthly_usage.py` | SolarMonthlyUsage model |
| `app/services/consumption_service.py` | Core consumption processing logic |
| `app/tasks/consumption_tasks.py` | Celery tasks for batch processing |

### Files to Modify

| File | Changes |
|------|---------|
| `app/models/meter_reading.py` | Add billing tracking fields |
| `app/models/__init__.py` | Add SolarMonthlyUsage import |
| `app/routes/v1/meters.py` | Add processing endpoints |
| `celery_app.py` | Add consumption tasks and schedule |

---

## Key Existing Code to Reuse

| File | Function | Line | Usage |
|------|----------|------|-------|
| `app/utils/rates.py` | `calculate_consumption_charge()` | 202-225 | Calculate cost from consumption |
| `app/utils/rates.py` | `compute_from_structure()` | 38-50 | Handle tiered/flat rates |
| `app/utils/rates.py` | `apply_markup()` | 53-57 | Apply estate markup percentage |
| `app/utils/rates.py` | `get_default_rate_structure()` | 172-199 | Fallback rate lookup |
| `app/services/units.py` | `find_unit_by_meter_id()` | 129-139 | Find unit for a meter |
| `app/services/notification_service.py` | `notify_low_credit()` | - | Low balance alerts |

---

## Implementation Checklist

### Phase 1: Database
- [ ] Create migration for billing fields on meter_readings
- [ ] Create migration for solar_monthly_usage table
- [ ] Run migrations: `flask db upgrade`

### Phase 2: Models
- [ ] Update MeterReading model with new fields
- [ ] Create SolarMonthlyUsage model
- [ ] Update models/__init__.py

### Phase 3: Core Service
- [ ] Create consumption_service.py
- [ ] Implement process_meter_reading()
- [ ] Implement helper functions
- [ ] Write unit tests

### Phase 4: Trigger Mechanism
- [ ] Create Celery tasks (if using polling)
- [ ] Add API endpoints (if using webhook)
- [ ] Update celery_app.py configuration

### Phase 5: Integration
- [ ] Add low balance notification check
- [ ] End-to-end testing
- [ ] Documentation

---

## Open Items

1. **Trigger Mechanism**: Confirm with client whether to use:
   - Celery polling (recommended)
   - API webhook
   - On-demand processing

2. **Solar Free Allocation**: Confirm the default 50 kWh/month is correct per estate setting

3. **Negative Balance Alerts**: Should there be alerts when balance goes negative (debt)?

4. **Billing Frequency**: If using Celery polling, confirm 15-minute interval is acceptable

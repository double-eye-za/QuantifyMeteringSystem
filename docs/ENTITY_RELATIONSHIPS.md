# Entity Relationships - Quantify Metering System

> **Last Updated:** February 2026
> **Purpose:** Document the data model relationships between core entities

---

## Quick Reference Diagram

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              ESTATE                                          │
│  (Property/Building Complex)                                                 │
│  - Has bulk meters (electricity, water)                                      │
│  - Has default rate tables                                                   │
└─────────────────────┬───────────────────────────────────────────────────────┘
                      │ 1:N
                      ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                               UNIT                                           │
│  (Individual Apartment/Dwelling)                                             │
│  - Belongs to one Estate                                                     │
│  - Has up to 4 meters (electricity, water, solar, hot_water)                │
│  - Has exactly one Wallet                                                    │
│  - Can override estate rate tables                                           │
└───────┬─────────────────┬─────────────────┬─────────────────────────────────┘
        │                 │                 │
        │ 1:1             │ M:N             │ M:N
        ▼                 ▼                 ▼
┌───────────────┐  ┌─────────────┐  ┌─────────────────────┐
│    WALLET     │  │ OWNERSHIP   │  │      TENANCY        │
│               │  │ (Junction)  │  │     (Junction)      │
│ - Balances    │  │             │  │                     │
│ - Thresholds  │  │ - % owned   │  │ - Lease dates       │
│ - Alerts      │  │ - Primary?  │  │ - Rent amount       │
└───────┬───────┘  └──────┬──────┘  │ - Primary tenant?   │
        │                 │         └──────────┬──────────┘
        │ 1:N             │                    │
        ▼                 └────────┬───────────┘
┌───────────────┐                  │
│  TRANSACTION  │                  ▼
│               │         ┌───────────────┐
│ - Topups      │         │    PERSON     │
│ - Consumption │         │               │
│ - Refunds     │         │ - Contact info│
└───────────────┘         │ - Can be owner│
                          │ - Can be tenant│
                          └───────────────┘

┌─────────────────────────────────────────────────────────────────────────────┐
│                              METER                                           │
│  - Assigned to Unit (electricity, water, solar, hot_water)                  │
│  - Or assigned to Estate (bulk_electricity, bulk_water)                     │
└─────────────────────┬───────────────────────────────────────────────────────┘
                      │ 1:N
                      ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                          METER_READING                                       │
│  - Tracks consumption over time                                              │
│  - Linked to billing (is_billed flag)                                       │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 1. ESTATE

**Table:** `estates`
**Description:** Represents a property complex (apartment building, housing estate, etc.)

### Columns

| Column | Type | Nullable | Default | Description |
|--------|------|----------|---------|-------------|
| `id` | Integer | No | Auto | Primary key |
| `code` | String(20) | Yes | - | Estate code (e.g., "EST001") |
| `name` | String(255) | No | - | Estate name |
| `address` | Text | Yes | - | Street address |
| `city` | String(100) | Yes | - | City |
| `postal_code` | String(10) | Yes | - | Postal code |
| `contact_name` | String(200) | Yes | - | Primary contact name |
| `contact_phone` | String(20) | Yes | - | Contact phone |
| `contact_email` | String(255) | Yes | - | Contact email |
| `total_units` | Integer | Yes | 0 | Number of units |
| `electricity_markup_percentage` | Numeric(5,2) | Yes | 0.00 | Electricity rate markup % |
| `water_markup_percentage` | Numeric(5,2) | Yes | 0.00 | Water rate markup % |
| `solar_free_allocation_kwh` | Numeric(10,2) | Yes | 50.00 | Free solar kWh per month |
| `bulk_electricity_meter_id` | Integer | Yes | - | FK to meters |
| `bulk_water_meter_id` | Integer | Yes | - | FK to meters |
| `electricity_rate_table_id` | Integer | Yes | - | FK to rate_tables |
| `water_rate_table_id` | Integer | Yes | - | FK to rate_tables |
| `is_active` | Boolean | Yes | True | Active status |
| `created_at` | DateTime | Yes | Now | Creation timestamp |
| `updated_at` | DateTime | Yes | Now | Last update timestamp |

### Relationships

| Relationship | Type | Target | Description |
|--------------|------|--------|-------------|
| units | 1:N | Unit | All units in this estate |
| bulk_electricity_meter | 1:1 | Meter | Estate-level electricity meter |
| bulk_water_meter | 1:1 | Meter | Estate-level water meter |
| electricity_rate_table | 1:1 | RateTable | Default electricity rates |
| water_rate_table | 1:1 | RateTable | Default water rates |

---

## 2. UNIT

**Table:** `units`
**Description:** Individual dwelling unit within an estate (apartment, house, etc.)

### Columns

| Column | Type | Nullable | Default | Description |
|--------|------|----------|---------|-------------|
| `id` | Integer | No | Auto | Primary key |
| `estate_id` | Integer | No | - | FK to estates |
| `unit_number` | String(50) | No | - | Unit identifier (e.g., "A101") |
| `floor` | String(20) | Yes | - | Floor/location |
| `building` | String(50) | Yes | - | Building name |
| `bedrooms` | Integer | Yes | - | Number of bedrooms |
| `bathrooms` | Integer | Yes | - | Number of bathrooms |
| `size_sqm` | Numeric(10,2) | Yes | - | Size in square meters |
| `occupancy_status` | String(20) | Yes | 'vacant' | Status: occupied/vacant/maintenance |
| `electricity_meter_id` | Integer | Yes | - | FK to meters |
| `water_meter_id` | Integer | Yes | - | FK to meters |
| `solar_meter_id` | Integer | Yes | - | FK to meters |
| `hot_water_meter_id` | Integer | Yes | - | FK to meters |
| `electricity_rate_table_id` | Integer | Yes | - | FK to rate_tables (override) |
| `water_rate_table_id` | Integer | Yes | - | FK to rate_tables (override) |
| `is_active` | Boolean | Yes | True | Active status (False = decommissioned) |
| `created_at` | DateTime | Yes | Now | Creation timestamp |
| `updated_at` | DateTime | Yes | Now | Last update timestamp |

### Constraints

- `UNIQUE(estate_id, unit_number)` - No duplicate unit numbers within an estate
- `CHECK occupancy_status IN ('occupied', 'vacant', 'maintenance')`

### Relationships

| Relationship | Type | Target | Description |
|--------------|------|--------|-------------|
| estate | N:1 | Estate | Parent estate |
| wallet | 1:1 | Wallet | Unit's prepaid wallet |
| ownerships | 1:N | UnitOwnership | Ownership records (cascade delete) |
| tenancies | 1:N | UnitTenancy | Tenancy records (cascade delete) |
| electricity_meter | 1:1 | Meter | Electricity meter |
| water_meter | 1:1 | Meter | Water meter |
| solar_meter | 1:1 | Meter | Solar meter |
| hot_water_meter | 1:1 | Meter | Hot water meter |

### Computed Properties

| Property | Returns | Description |
|----------|---------|-------------|
| `owners` | List[Person] | All persons who own this unit |
| `tenants` | List[Person] | All active tenants (status=active, no move_out_date) |
| `all_tenants` | List[Person] | All tenants including inactive |
| `primary_owner` | Person | Primary owner or first owner |
| `primary_tenant` | Person | Primary tenant (responsible for billing) |
| `resident` | Person | Alias for primary_tenant |

---

## 3. PERSON

**Table:** `persons`
**Description:** An individual who can be an owner and/or tenant of units

### Columns

| Column | Type | Nullable | Default | Description |
|--------|------|----------|---------|-------------|
| `id` | Integer | No | Auto | Primary key |
| `first_name` | String(100) | No | - | First name |
| `last_name` | String(100) | No | - | Last name |
| `email` | String(255) | No | - | Email (unique, indexed) |
| `phone` | String(20) | No | - | Phone (unique, indexed) |
| `alternate_phone` | String(20) | Yes | - | Secondary phone |
| `id_number` | String(20) | Yes | - | ID/Passport number (unique, indexed) |
| `emergency_contact_name` | String(200) | Yes | - | Emergency contact |
| `emergency_contact_phone` | String(20) | Yes | - | Emergency phone |
| `is_active` | Boolean | Yes | True | Active status |
| `profile_photo_url` | String(512) | Yes | - | Profile photo URL |
| `created_at` | DateTime | Yes | Now | Creation timestamp |
| `updated_at` | DateTime | Yes | Now | Last update timestamp |

### Relationships

| Relationship | Type | Target | Description |
|--------------|------|--------|-------------|
| ownerships | 1:N | UnitOwnership | Ownership records (cascade delete) |
| tenancies | 1:N | UnitTenancy | Tenancy records (cascade delete) |

### Computed Properties

| Property | Returns | Description |
|----------|---------|-------------|
| `full_name` | String | "{first_name} {last_name}" |
| `units_owned` | List[Unit] | All units this person owns |
| `units_rented` | List[Unit] | All units this person rents (active tenancies) |
| `all_units` | List[Unit] | Combined owned + rented, deduplicated |
| `is_owner` | Boolean | True if owns any units |
| `is_tenant` | Boolean | True if rents any units |
| `has_app_access` | Boolean | True if has mobile_user account |

---

## 4. UNIT_OWNERSHIP (Junction Table)

**Table:** `unit_ownerships`
**Description:** Links Persons to Units as owners (supports joint ownership)

### Columns

| Column | Type | Nullable | Default | Description |
|--------|------|----------|---------|-------------|
| `id` | Integer | No | Auto | Primary key |
| `unit_id` | Integer | No | - | FK to units (cascade delete) |
| `person_id` | Integer | No | - | FK to persons (cascade delete) |
| `ownership_percentage` | Numeric(5,2) | Yes | 100.00 | Ownership % (0-100) |
| `purchase_date` | Date | Yes | - | Date of purchase |
| `purchase_price` | Numeric(15,2) | Yes | - | Purchase price |
| `is_primary_owner` | Boolean | Yes | False | Primary contact for correspondence |
| `notes` | Text | Yes | - | Additional notes |
| `created_at` | DateTime | Yes | Now | Creation timestamp |
| `updated_at` | DateTime | Yes | Now | Last update timestamp |

### Constraints

- `UNIQUE(unit_id, person_id)` - One ownership record per person per unit
- `CHECK ownership_percentage >= 0 AND ownership_percentage <= 100`

### Cascade Behavior

- Deleting a **Unit** → Deletes all UnitOwnership records for that unit
- Deleting a **Person** → Deletes all UnitOwnership records for that person

---

## 5. UNIT_TENANCY (Junction Table)

**Table:** `unit_tenancies`
**Description:** Links Persons to Units as tenants (supports multiple tenants)

### Columns

| Column | Type | Nullable | Default | Description |
|--------|------|----------|---------|-------------|
| `id` | Integer | No | Auto | Primary key |
| `unit_id` | Integer | No | - | FK to units (cascade delete) |
| `person_id` | Integer | No | - | FK to persons (cascade delete) |
| `lease_start_date` | Date | Yes | - | Lease start date |
| `lease_end_date` | Date | Yes | - | Lease end date (null = month-to-month) |
| `monthly_rent` | Numeric(10,2) | Yes | - | Monthly rent amount |
| `deposit_amount` | Numeric(10,2) | Yes | - | Security deposit |
| `is_primary_tenant` | Boolean | Yes | False | Responsible for billing |
| `status` | String(20) | Yes | 'active' | Status: active/expired/terminated |
| `move_in_date` | Date | Yes | - | Actual move-in date |
| `move_out_date` | Date | Yes | - | Move-out date (null = still living) |
| `notes` | Text | Yes | - | Additional notes |
| `created_at` | DateTime | Yes | Now | Creation timestamp |
| `updated_at` | DateTime | Yes | Now | Last update timestamp |

### Constraints

- `UNIQUE(unit_id, person_id)` - One tenancy record per person per unit
- `CHECK status IN ('active', 'expired', 'terminated')`

### Computed Properties

| Property | Returns | Description |
|----------|---------|-------------|
| `is_active` | Boolean | True if status='active' AND no move_out_date |
| `is_expired` | Boolean | True if lease_end_date is in the past |

---

## 6. WALLET

**Table:** `wallets`
**Description:** Prepaid wallet for a unit (holds balances for all utility types)

### Columns

| Column | Type | Nullable | Default | Description |
|--------|------|----------|---------|-------------|
| `id` | Integer | No | Auto | Primary key |
| `unit_id` | Integer | No | - | FK to units (unique - 1:1) |
| `balance` | Numeric(12,2) | Yes | 0.00 | Total balance |
| `electricity_balance` | Numeric(12,2) | Yes | 0.00 | Electricity-specific balance |
| `water_balance` | Numeric(12,2) | Yes | 0.00 | Water-specific balance |
| `solar_balance` | Numeric(12,2) | Yes | 0.00 | Solar-specific balance |
| `hot_water_balance` | Numeric(12,2) | Yes | 0.00 | Hot water-specific balance |
| `low_balance_threshold` | Numeric(10,2) | Yes | 50.00 | Alert threshold (R) |
| `low_balance_alert_type` | String(20) | Yes | 'fixed' | Threshold type |
| `low_balance_days_threshold` | Integer | Yes | 3 | Days of usage threshold |
| `last_low_balance_alert` | DateTime | Yes | - | Last alert sent |
| `alert_frequency_hours` | Integer | Yes | 24 | Hours between alerts |
| `electricity_minimum_activation` | Numeric(10,2) | Yes | 20.00 | Min topup for electricity |
| `water_minimum_activation` | Numeric(10,2) | Yes | 20.00 | Min topup for water |
| `auto_topup_enabled` | Boolean | Yes | False | Auto-topup enabled |
| `auto_topup_amount` | Numeric(10,2) | Yes | - | Auto-topup amount |
| `auto_topup_threshold` | Numeric(10,2) | Yes | - | Trigger threshold |
| `daily_avg_consumption` | Numeric(10,2) | Yes | - | Average daily usage (R) |
| `last_consumption_calc_date` | DateTime | Yes | - | Last avg calculation |
| `last_topup_date` | DateTime | Yes | - | Last topup received |
| `is_suspended` | Boolean | Yes | False | Wallet suspended |
| `suspension_reason` | Text | Yes | - | Suspension reason |
| `created_at` | DateTime | Yes | Now | Creation timestamp |
| `updated_at` | DateTime | Yes | Now | Last update timestamp |

### Relationships

| Relationship | Type | Target | Description |
|--------------|------|--------|-------------|
| unit | 1:1 | Unit | The unit this wallet belongs to |
| transactions | 1:N | Transaction | All transactions on this wallet |

---

## 7. METER

**Table:** `meters`
**Description:** Physical meter device (electricity, water, solar, etc.)

### Columns

| Column | Type | Nullable | Default | Description |
|--------|------|----------|---------|-------------|
| `id` | Integer | No | Auto | Primary key |
| `serial_number` | String(100) | No | - | Unique serial number |
| `meter_type` | String(20) | No | - | Type (see constraints) |
| `manufacturer` | String(100) | Yes | - | Manufacturer name |
| `model` | String(100) | Yes | - | Model number |
| `installation_date` | Date | Yes | - | Installation date |
| `last_reading` | Numeric(15,3) | Yes | - | Last reading value |
| `last_reading_date` | DateTime | Yes | - | Last reading timestamp |
| `communication_type` | String(20) | Yes | 'plc' | How meter communicates |
| `communication_status` | String(20) | Yes | 'online' | Current status |
| `last_communication` | DateTime | Yes | - | Last communication time |
| `firmware_version` | String(50) | Yes | - | Firmware version |
| `is_prepaid` | Boolean | Yes | True | Is prepaid meter |
| `is_active` | Boolean | Yes | True | Active status |
| `device_eui` | String(16) | Yes | - | LoRaWAN device EUI (unique) |
| `lorawan_device_type` | String(50) | Yes | - | LoRaWAN device type |
| `created_at` | DateTime | Yes | Now | Creation timestamp |
| `updated_at` | DateTime | Yes | Now | Last update timestamp |

### Constraints

- `UNIQUE(serial_number)`
- `UNIQUE(device_eui)` where not null
- `CHECK meter_type IN ('electricity', 'water', 'solar', 'hot_water', 'bulk_electricity', 'bulk_water')`
- `CHECK communication_type IN ('plc', 'cellular', 'wifi', 'manual', 'lora')`
- `CHECK communication_status IN ('online', 'offline', 'error')`

### Relationships

| Relationship | Type | Target | Description |
|--------------|------|--------|-------------|
| readings | 1:N | MeterReading | All readings from this meter |

---

## 8. METER_READING

**Table:** `meter_readings`
**Description:** Individual meter reading (consumption snapshot)

### Columns

| Column | Type | Nullable | Default | Description |
|--------|------|----------|---------|-------------|
| `id` | Integer | No | Auto | Primary key |
| `meter_id` | Integer | No | - | FK to meters |
| `reading_value` | Numeric(15,3) | No | - | Absolute reading value |
| `reading_date` | DateTime | No | - | Reading timestamp |
| `reading_type` | String(20) | Yes | 'automatic' | How reading was obtained |
| `consumption_since_last` | Numeric(15,3) | Yes | - | Delta from previous reading |
| `is_validated` | Boolean | Yes | False | Validated by system/user |
| `validation_date` | DateTime | Yes | - | When validated |
| `is_billed` | Boolean | No | False | Has been billed |
| `billed_at` | DateTime | Yes | - | When billed |
| `status` | String(50) | Yes | - | Processing status |
| `transaction_id` | Integer | Yes | - | FK to transactions (if billed) |
| `created_at` | DateTime | Yes | Now | Creation timestamp |

**LoRaWAN Telemetry Columns:**
- `pulse_count`, `temperature`, `humidity`, `rssi`, `snr`, `battery_level`, `raw_payload`

**Electrical Parameters:**
- `voltage`, `current`, `power`, `power_factor`, `frequency`

**Water Parameters:**
- `flow_rate`, `pressure`

### Constraints

- `CHECK reading_type IN ('automatic', 'manual', 'estimated')`

---

## 9. TRANSACTION

**Table:** `transactions`
**Description:** Financial transaction on a wallet (topup, consumption deduction, etc.)

### Columns

| Column | Type | Nullable | Default | Description |
|--------|------|----------|---------|-------------|
| `id` | Integer | No | Auto | Primary key |
| `transaction_number` | String(50) | No | - | Unique transaction ID |
| `wallet_id` | Integer | No | - | FK to wallets |
| `transaction_type` | String(30) | No | - | Type (see constraints) |
| `amount` | Numeric(12,2) | No | - | Transaction amount |
| `balance_before` | Numeric(12,2) | No | - | Balance before transaction |
| `balance_after` | Numeric(12,2) | No | - | Balance after transaction |
| `reference` | String(255) | Yes | - | External reference |
| `description` | Text | Yes | - | Description |
| `payment_method` | String(20) | Yes | - | Payment method |
| `payment_gateway` | String(50) | Yes | - | Gateway used |
| `payment_gateway_ref` | String(255) | Yes | - | Gateway reference |
| `status` | String(20) | Yes | 'pending' | Transaction status |
| `initiated_at` | DateTime | Yes | Now | When initiated |
| `completed_at` | DateTime | Yes | - | When completed |
| `meter_id` | Integer | Yes | - | FK to meters (for consumption) |
| `consumption_kwh` | Numeric(10,3) | Yes | - | kWh consumed (for deductions) |
| `rate_applied` | Numeric(10,4) | Yes | - | Rate used for calculation |
| `created_at` | DateTime | Yes | Now | Creation timestamp |

### Constraints

- `UNIQUE(transaction_number)`
- `CHECK transaction_type IN ('topup', 'purchase_electricity', 'purchase_water', 'purchase_solar', 'consumption_electricity', 'consumption_water', 'consumption_solar', 'refund', 'adjustment', 'service_charge')`
- `CHECK payment_method IN ('eft', 'card', 'instant_eft', 'cash', 'system', 'adjustment')` or NULL
- `CHECK status IN ('pending', 'processing', 'completed', 'failed', 'reversed', 'expired')`

---

## Relationship Cardinality Summary

| From | To | Cardinality | Notes |
|------|-----|-------------|-------|
| Estate | Unit | 1:N | One estate has many units |
| Estate | Meter (bulk) | 1:1 | Optional bulk meters |
| Unit | Estate | N:1 | Each unit belongs to one estate |
| Unit | Wallet | 1:1 | Each unit has exactly one wallet |
| Unit | Meter | 1:1 | Up to 4 meters per unit |
| Unit | UnitOwnership | 1:N | Cascade delete |
| Unit | UnitTenancy | 1:N | Cascade delete |
| Person | UnitOwnership | 1:N | Cascade delete |
| Person | UnitTenancy | 1:N | Cascade delete |
| **Unit ↔ Person** | **M:N** | Via UnitOwnership | Joint ownership support |
| **Unit ↔ Person** | **M:N** | Via UnitTenancy | Multiple tenants support |
| Wallet | Transaction | 1:N | Transaction history |
| Meter | MeterReading | 1:N | Reading history |
| MeterReading | Transaction | N:1 | Optional billing link |

---

## Data Flow Examples

### 1. Getting all persons associated with an estate

```python
estate = Estate.query.get(estate_id)
persons = set()
for unit in estate.units:
    for owner in unit.owners:
        persons.add(owner)
    for tenant in unit.tenants:
        persons.add(tenant)
```

### 2. Getting a unit's current balance for billing

```python
unit = Unit.query.get(unit_id)
wallet = unit.wallet
electricity_balance = wallet.electricity_balance
water_balance = wallet.water_balance
```

### 3. Tracking consumption from meter to wallet

```python
# Meter reading received
reading = MeterReading(
    meter_id=meter.id,
    reading_value=current_value,
    consumption_since_last=delta
)

# Find the unit
unit = Unit.query.filter(
    (Unit.electricity_meter_id == meter.id) |
    (Unit.water_meter_id == meter.id)
).first()

# Deduct from wallet
wallet = unit.wallet
cost = delta * rate
wallet.electricity_balance -= cost

# Create transaction
transaction = Transaction(
    wallet_id=wallet.id,
    transaction_type='consumption_electricity',
    amount=cost,
    meter_id=meter.id,
    consumption_kwh=delta
)
```

---

## Important Notes

1. **Wallet Auto-Creation:** When a Unit is created, a Wallet is automatically created for it.

2. **Cascade Behavior:**
   - Deleting a Unit does NOT automatically delete its Wallet (manual deletion required)
   - Deleting a Unit/Person DOES cascade delete UnitOwnership and UnitTenancy records

3. **Decommissioned Units:**
   - Set `is_active = False` instead of deleting
   - Preserves wallet and transaction history
   - Meters are unlinked but not deleted

4. **Rate Table Inheritance:**
   - Units inherit rate tables from Estate by default
   - Unit-level rate tables override estate defaults

5. **Multi-Utility Support:**
   - Each utility type (electricity, water, solar, hot_water) has its own balance
   - Each utility can have its own meter and rate table

---

## File Locations

| Model | File Path |
|-------|-----------|
| Estate | `app/models/estate.py` |
| Unit | `app/models/unit.py` |
| Person | `app/models/person.py` |
| UnitOwnership | `app/models/unit_ownership.py` |
| UnitTenancy | `app/models/unit_tenancy.py` |
| Wallet | `app/models/wallet.py` |
| Meter | `app/models/meter.py` |
| MeterReading | `app/models/meter_reading.py` |
| Transaction | `app/models/transaction.py` |
| RateTable | `app/models/rate_table.py` |

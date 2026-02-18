# Data Flow & Integrity Audit

## Document Purpose

This document provides a comprehensive audit of data relationships, CRUD operations, cascade behaviors, and potential integrity issues across the core entities in the Quantify Metering System. All findings are based on direct code inspection with exact file paths and line numbers.

**Audit Date:** January 2026
**Entities Covered:** Users, Persons, Estates, Units, Meters, Wallets/Transactions

---

## Table of Contents

1. [Entity Relationship Overview](#1-entity-relationship-overview)
2. [User Entity Audit](#2-user-entity-audit)
3. [Person Entity Audit](#3-person-entity-audit)
4. [Estate Entity Audit](#4-estate-entity-audit)
5. [Unit Entity Audit](#5-unit-entity-audit)
6. [Meter Entity Audit](#6-meter-entity-audit)
7. [Wallet & Transaction Audit](#7-wallet--transaction-audit)
8. [Cross-Entity Relationship Matrix](#8-cross-entity-relationship-matrix)
9. [Critical Data Integrity Issues](#9-critical-data-integrity-issues)
10. [Recommended Actions](#10-recommended-actions)

---

## 1. Entity Relationship Overview

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                           QUANTIFY METERING SYSTEM                               │
│                           Entity Relationship Diagram                            │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                  │
│    ┌──────────┐                                                                  │
│    │  USERS   │──────────────────────────────────────────────────────────────┐  │
│    └────┬─────┘                                                              │  │
│         │ created_by/updated_by (FK to 20+ tables)                           │  │
│         │ NO CASCADE on any FK                                               │  │
│         ▼                                                                    │  │
│    ┌──────────┐         ┌─────────────┐        ┌──────────────┐              │  │
│    │  PERSON  │◄────────│ UnitOwnership│────────►│    UNITS     │              │  │
│    │          │         │ CASCADE DEL  │        │              │              │  │
│    │          │◄────────│─────────────│────────►│              │              │  │
│    │          │         │ UnitTenancy │         │              │              │  │
│    └──────────┘         │ CASCADE DEL │         └──────┬───────┘              │  │
│         │               └─────────────┘                │                      │  │
│         │ person_id                                    │                      │  │
│         ▼                                              │ unit_id (UNIQUE)     │  │
│    ┌──────────┐                                        ▼                      │  │
│    │ MobileUser│                               ┌──────────────┐               │  │
│    │ SET NULL │                               │   WALLETS    │               │  │
│    └──────────┘                               │ NO CASCADE   │               │  │
│                                               └──────┬───────┘               │  │
│                                                      │                        │  │
│    ┌──────────┐                                      │ wallet_id              │  │
│    │ ESTATES  │                                      ▼                        │  │
│    │          │                               ┌──────────────┐               │  │
│    │          │────────estate_id─────────────►│ TRANSACTIONS │               │  │
│    │          │                               │ NO CASCADE   │               │  │
│    │          │                               └──────────────┘               │  │
│    └────┬─────┘                                                              │  │
│         │                                                                    │  │
│         │ bulk_meter_id (electricity/water)      meter_id (4 types per unit) │  │
│         ▼                                              ▲                      │  │
│    ┌──────────┐                               ┌────────┴─────┐               │  │
│    │  METERS  │◄──────────────────────────────│    UNITS     │               │  │
│    │          │                               └──────────────┘               │  │
│    └────┬─────┘                                                              │  │
│         │                                                                    │  │
│         │ meter_id (NO CASCADE)                                              │  │
│         ▼                                                                    │  │
│    ┌──────────────┐    ┌──────────────┐    ┌─────────────────┐               │  │
│    │MeterReadings │    │ MeterAlerts  │    │ DeviceCommands  │               │  │
│    │  NO CASCADE  │    │  NO CASCADE  │    │   NO CASCADE    │               │  │
│    └──────────────┘    └──────────────┘    └─────────────────┘               │  │
│                                                                              │  │
└──────────────────────────────────────────────────────────────────────────────┘
```

---

## 2. User Entity Audit

### 2.1 Model Definition

**File:** `app/models/user.py`

| Column | Type | Constraints | Line |
|--------|------|-------------|------|
| id | Integer | Primary Key, Auto-increment | 44 |
| email | String(120) | UNIQUE, NOT NULL | 45 |
| username | String(80) | UNIQUE, NOT NULL | 46 |
| password_hash | String(256) | NOT NULL | 47 |
| first_name | String(50) | Nullable | 48 |
| last_name | String(50) | Nullable | 49 |
| phone | String(20) | Nullable | 50 |
| role_id | Integer | FK to roles.id, Nullable | 51 |
| is_active | Boolean | Default True | 52 |
| is_super_admin | Boolean | Default False | 53 |
| last_login | DateTime | Nullable | 54 |
| failed_login_attempts | Integer | Default 0 | 55 |
| locked_until | DateTime | Nullable | 56 |
| created_at | DateTime | Default utcnow | 57 |
| updated_at | DateTime | Default utcnow, onupdate | 58-60 |

### 2.2 Foreign Key References TO users.id

| Table | Column | ON DELETE | File:Line | Risk |
|-------|--------|-----------|-----------|------|
| estates | created_by | NOT SET | estate.py:50 | ⚠️ |
| estates | updated_by | NOT SET | estate.py:51 | ⚠️ |
| units | created_by | NOT SET | unit.py:79 | ⚠️ |
| units | updated_by | NOT SET | unit.py:80 | ⚠️ |
| meters | created_by | NOT SET | - | ⚠️ |
| transactions | created_by | NOT SET | transaction.py:67 | ⚠️ |
| audit_log | user_id | NOT SET | audit_log.py | ⚠️ |
| tickets | assigned_to | NOT SET | ticket.py:53 | ⚠️ |
| notifications | user_id | NOT SET | notification.py | ⚠️ |
| mobile_invites | created_by | NOT SET | mobile_invite.py:27 | ⚠️ |
| (20+ more tables) | various | NOT SET | various | ⚠️ |

### 2.3 CRUD Operations

**Routes File:** `app/routes/v1/users.py`

| Operation | Endpoint | Permission | Lines |
|-----------|----------|------------|-------|
| List | GET /users | users.view | 29-75 |
| Create | POST /users | users.create | 109-196 |
| Read | GET /users/{id} | users.view | 78-106 |
| Update | PUT /users/{id} | users.edit | 199-284 |
| Delete | DELETE /users/{id} | users.delete | 287-318 |

**Delete Behavior (Lines 287-318):**
```python
# Line 305: Prevents self-deletion
if user.id == current_user.id:
    return jsonify({"message": "Cannot delete yourself"}), 400

# Line 308: Prevents deleting super admin
if user.is_super_admin:
    return jsonify({"message": "Cannot delete super admin"}), 400

# Line 311-312: Simple delete - NO CASCADE HANDLING
db.session.delete(user)
db.session.commit()
```

### 2.4 Critical Issues

| Issue | Severity | Description |
|-------|----------|-------------|
| No Cascade | HIGH | Deleting user leaves orphaned `created_by`/`updated_by` references in 20+ tables |
| No Soft Delete | MEDIUM | Hard delete loses audit trail |
| No Pre-Delete Check | HIGH | No validation for active assignments before delete |

---

## 3. Person Entity Audit

### 3.1 Model Definition

**File:** `app/models/person.py`

| Column | Type | Constraints | Line |
|--------|------|-------------|------|
| id | Integer | Primary Key | 36 |
| id_number | String(20) | UNIQUE | 37 |
| first_name | String(50) | NOT NULL | 38 |
| last_name | String(50) | NOT NULL | 39 |
| email | String(120) | Nullable | 40 |
| phone | String(20) | Nullable | 41 |
| alternative_phone | String(20) | Nullable | 42 |
| date_of_birth | Date | Nullable | 43 |
| is_active | Boolean | Default True | 44 |
| created_at | DateTime | Default utcnow | 45 |
| updated_at | DateTime | Default utcnow, onupdate | 46-48 |

### 3.2 Relationships Defined

**Lines 54-66:**
```python
ownerships = db.relationship(
    "UnitOwnership",
    back_populates="person",
    cascade="all, delete-orphan",  # Line 57
    lazy="selectin"
)
tenancies = db.relationship(
    "UnitTenancy",
    back_populates="person",
    cascade="all, delete-orphan",  # Line 63
    lazy="selectin"
)
```

### 3.3 Foreign Key References TO persons.id

| Table | Column | ON DELETE | File:Line | Status |
|-------|--------|-----------|-----------|--------|
| unit_ownerships | person_id | CASCADE | unit_ownership.py:37 | ✅ |
| unit_tenancies | person_id | CASCADE | unit_tenancy.py:41 | ✅ |
| mobile_users | person_id | SET NULL | mobile_user.py:29 | ✅ |
| tickets | created_by_person_id | NOT SET | ticket.py:52 | ⚠️ |

### 3.4 CRUD Operations

**Service File:** `app/services/persons.py`

| Function | Lines | Description |
|----------|-------|-------------|
| list_persons() | 11-45 | Filterable query with search |
| get_person_by_id() | 48-49 | Simple retrieval |
| create_person() | 52-80 | Creates with validation |
| update_person() | 83-113 | Updates specified fields |
| delete_person() | 116-140 | **PREVENTS deletion if ownerships/tenancies exist** |

**Delete Prevention Logic (Lines 116-140):**
```python
def delete_person(person: Person) -> dict:
    # Line 125-127: Blocks if any ownerships exist
    if person.ownerships:
        return {"success": False, "message": "Cannot delete person with unit ownerships"}

    # Line 130-132: Blocks if any tenancies exist
    if person.tenancies:
        return {"success": False, "message": "Cannot delete person with unit tenancies"}

    # Line 135-138: Proceeds with delete
    db.session.delete(person)
    db.session.commit()
    return {"success": True}
```

### 3.5 Critical Issues

| Issue | Severity | Description |
|-------|----------|-------------|
| Cascade Mismatch | MEDIUM | Model has `cascade="all, delete-orphan"` but service prevents delete anyway |
| Ticket Orphans | MEDIUM | tickets.created_by_person_id has no cascade |

---

## 4. Estate Entity Audit

### 4.1 Model Definition

**File:** `app/models/estate.py`

| Column | Type | Constraints | Line |
|--------|------|-------------|------|
| id | Integer | Primary Key | 39 |
| name | String(100) | UNIQUE, NOT NULL | 40 |
| address | String(255) | Nullable | 41 |
| city | String(100) | Nullable | 42 |
| province | String(100) | Nullable | 43 |
| postal_code | String(20) | Nullable | 44 |
| country | String(100) | Default "South Africa" | 45 |
| is_active | Boolean | Default True | 46 |
| bulk_electricity_meter_id | Integer | FK to meters.id | 47 |
| bulk_water_meter_id | Integer | FK to meters.id | 48 |
| electricity_rate_table_id | Integer | FK to rate_tables.id | 49 |
| water_rate_table_id | Integer | FK to rate_tables.id | 50 |
| created_by | Integer | FK to users.id | 51 |
| updated_by | Integer | FK to users.id | 52 |
| created_at | DateTime | Default utcnow | 53 |
| updated_at | DateTime | Default utcnow, onupdate | 54-56 |

### 4.2 Foreign Key References TO estates.id

| Table | Column | ON DELETE | File:Line | Risk |
|-------|--------|-----------|-----------|------|
| units | estate_id | NOT SET | unit.py:42 | ⚠️ RESTRICT |
| meter_readings | estate_id | NOT SET | - | ⚠️ Orphan |
| transactions | (via wallet→unit) | N/A | - | Indirect |

### 4.3 CRUD Operations

**Service File:** `app/services/estates.py`

**Delete Logic (Lines 65-95):**
```python
def delete_estate(estate: Estate) -> dict:
    # Lines 75-89: Manual cascade deletion
    for unit in estate.units:
        # Delete unit ownerships
        UnitOwnership.query.filter_by(unit_id=unit.id).delete()
        # Delete unit tenancies
        UnitTenancy.query.filter_by(unit_id=unit.id).delete()
        # Delete wallets
        Wallet.query.filter_by(unit_id=unit.id).delete()
        # Delete the unit
        db.session.delete(unit)

    # Line 92: Delete estate
    db.session.delete(estate)
    db.session.commit()
```

### 4.4 Critical Issues

| Issue | Severity | Description |
|-------|----------|-------------|
| Manual Cascade | MEDIUM | Deletion requires manual cleanup of children |
| MeterReadings Orphan | HIGH | MeterReadings with estate_id become orphaned |
| No Transaction Cleanup | HIGH | Transactions linked to wallets not deleted |

---

## 5. Unit Entity Audit

### 5.1 Model Definition

**File:** `app/models/unit.py`

| Column | Type | Constraints | Line |
|--------|------|-------------|------|
| id | Integer | Primary Key | 41 |
| estate_id | Integer | FK to estates.id, NOT NULL | 42 |
| unit_number | String(50) | NOT NULL | 43 |
| floor | String(20) | Nullable | 44 |
| building | String(50) | Nullable | 45 |
| bedrooms | Integer | Nullable | 46 |
| bathrooms | Integer | Nullable | 47 |
| size_sqm | Numeric(10,2) | Nullable | 48 |
| occupancy_status | String(20) | Default "vacant" | 49 |
| electricity_meter_id | Integer | FK to meters.id | 71 |
| water_meter_id | Integer | FK to meters.id | 72 |
| solar_meter_id | Integer | FK to meters.id | 73 |
| hot_water_meter_id | Integer | FK to meters.id | 74 |
| electricity_rate_table_id | Integer | FK to rate_tables.id | 75 |
| water_rate_table_id | Integer | FK to rate_tables.id | 76 |
| created_by | Integer | FK to users.id | 79 |
| updated_by | Integer | FK to users.id | 80 |
| is_active | Boolean | Default True | 78 |
| created_at | DateTime | Default utcnow | 81 |
| updated_at | DateTime | Default utcnow, onupdate | 82-84 |

### 5.2 Constraints

**Lines 86-94:**
```python
__table_args__ = (
    UniqueConstraint("estate_id", "unit_number", name="uq_units_estate_unit_number"),
    CheckConstraint("occupancy_status IN ('occupied','vacant','maintenance')",
                   name="ck_units_occupancy_status"),
)
```

### 5.3 Relationships with CASCADE

**Lines 58-69:**
```python
ownerships = db.relationship(
    "UnitOwnership",
    back_populates="unit",
    cascade="all, delete-orphan",  # ✅ CASCADE
    lazy="selectin"
)
tenancies = db.relationship(
    "UnitTenancy",
    back_populates="unit",
    cascade="all, delete-orphan",  # ✅ CASCADE
    lazy="selectin"
)
```

### 5.4 Foreign Key References TO units.id

| Table | Column | ON DELETE | File:Line | Status |
|-------|--------|-----------|-----------|--------|
| unit_ownerships | unit_id | CASCADE | unit_ownership.py:34 | ✅ |
| unit_tenancies | unit_id | CASCADE | unit_tenancy.py:38 | ✅ |
| wallets | unit_id | NOT SET | wallet.py:40 | ⚠️ Orphan |
| mobile_invites | unit_id | SET NULL | mobile_invite.py:29 | ✅ |
| tickets | unit_id | NOT SET | ticket.py:54 | ⚠️ Blocks Delete |

### 5.5 CRUD Operations

**Service File:** `app/services/units.py`

**Create Logic (Lines 47-91):**
- Creates unit with fields from payload
- Inherits rate tables from estate if not specified
- **Auto-creates Wallet** (Lines 77-89)

**Delete Logic (Lines 120-122):**
```python
def delete_unit(unit: Unit):
    db.session.delete(unit)  # Cascades to ownerships/tenancies
    db.session.commit()
    # WARNING: Wallet NOT deleted - becomes orphan
    # WARNING: Will FAIL if tickets exist
```

### 5.6 Critical Issues

| Issue | Severity | Description |
|-------|----------|-------------|
| Wallet Orphan | HIGH | Wallet not deleted when unit deleted |
| Ticket Blocks Delete | HIGH | Cannot delete unit if tickets exist (FK constraint) |
| No Pre-Check | MEDIUM | No validation before delete |

---

## 6. Meter Entity Audit

### 6.1 Model Definition

**File:** `app/models/meter.py`

| Column | Type | Constraints | Line |
|--------|------|-------------|------|
| id | Integer | Primary Key | 32 |
| serial_number | String(100) | UNIQUE, NOT NULL | 33 |
| meter_type | String(20) | NOT NULL, CHECK | 34 |
| manufacturer | String(100) | Nullable | 35 |
| model | String(100) | Nullable | 36 |
| installation_date | Date | Nullable | 37 |
| last_reading | Numeric(15,3) | Nullable | 38 |
| last_reading_date | DateTime | Nullable | 39 |
| communication_type | String(20) | Default 'plc', CHECK | 40 |
| communication_status | String(20) | Default 'online', CHECK | 41 |
| last_communication | DateTime | Nullable | 42 |
| firmware_version | String(50) | Nullable | 43 |
| is_prepaid | Boolean | Default True | 44 |
| is_active | Boolean | Default True | 45 |
| device_eui | String(16) | UNIQUE, Indexed, Nullable | 48 |
| lorawan_device_type | String(50) | Nullable | 49 |
| created_at | DateTime | Default utcnow | 50 |
| updated_at | DateTime | Default utcnow, onupdate | 51-53 |

### 6.2 Check Constraints

**Lines 56-68:**
```python
# Meter type constraint
"meter_type IN ('electricity','water','solar','hot_water','bulk_electricity','bulk_water')"

# Communication type constraint
"communication_type IN ('plc','cellular','wifi','manual','lora')"

# Communication status constraint
"communication_status IN ('online','offline','error')"
```

### 6.3 Foreign Key References TO meters.id

| Table | Column | ON DELETE | File:Line | Risk |
|-------|--------|-----------|-----------|------|
| units | electricity_meter_id | NOT SET | unit.py:71 | ⚠️ |
| units | water_meter_id | NOT SET | unit.py:72 | ⚠️ |
| units | solar_meter_id | NOT SET | unit.py:73 | ⚠️ |
| units | hot_water_meter_id | NOT SET | unit.py:74 | ⚠️ |
| estates | bulk_electricity_meter_id | NOT SET | estate.py:47 | ⚠️ |
| estates | bulk_water_meter_id | NOT SET | estate.py:48 | ⚠️ |
| meter_readings | meter_id | NOT SET | meter_reading.py:41 | ⚠️ BLOCKS |
| meter_alerts | meter_id | NOT SET | meter_alert.py:27 | ⚠️ BLOCKS |
| device_commands | meter_id | NOT SET | device_command.py:33 | ⚠️ BLOCKS |
| transactions | meter_id | NOT SET | transaction.py:63 | ⚠️ |

### 6.4 CRUD Operations

**Routes File:** `app/routes/v1/meters.py`

**Delete Logic (Lines 521-538):**
```python
@api_v1.route("/meters/<int:meter_id>", methods=["DELETE"])
@login_required
@requires_permission("meters.delete")
def delete_meter(meter_id):
    meter = svc_get_meter_by_id(meter_id)
    if not meter:
        return jsonify({"message": "Meter not found"}), 404

    # Line 529: Only unassigns from unit - DOES NOT delete readings/alerts/commands
    _assign_meter_to_unit(meter, None)

    db.session.delete(meter)  # WILL FAIL if readings/alerts/commands exist
    db.session.commit()
    return jsonify({"message": "Deleted"})
```

### 6.5 Device EUI Validation

**Lines 420-426:**
```python
if device_eui:
    device_eui = device_eui.lower().replace(":", "").replace("-", "")
    if len(device_eui) != 16:
        return jsonify({"message": "Device EUI must be exactly 16 hexadecimal characters"}), 400
    if not all(c in "0123456789abcdef" for c in device_eui):
        return jsonify({"message": "Device EUI must be exactly 16 hexadecimal characters"}), 400
```

### 6.6 Critical Issues

| Issue | Severity | Description |
|-------|----------|-------------|
| No Cascade to Readings | CRITICAL | Cannot delete meter if readings exist (thousands of records) |
| No Cascade to Alerts | HIGH | Cannot delete meter if alerts exist |
| No Cascade to Commands | HIGH | Cannot delete meter if commands exist |
| EUI Validation Location | MEDIUM | Validation only in routes, not service layer |
| Default Mismatch | LOW | Model default 'plc', service default 'cellular' |

---

## 7. Wallet & Transaction Audit

### 7.1 Wallet Model Definition

**File:** `app/models/wallet.py`

| Column | Type | Constraints | Line |
|--------|------|-------------|------|
| id | Integer | Primary Key | 38 |
| unit_id | Integer | FK to units.id, UNIQUE, NOT NULL | 39-41 |
| balance | Numeric(12,2) | NOT NULL, Default 0 | 42 |
| electricity_balance | Numeric(12,2) | NOT NULL, Default 0 | 43 |
| water_balance | Numeric(12,2) | NOT NULL, Default 0 | 44 |
| hot_water_balance | Numeric(12,2) | NOT NULL, Default 0 | 45 |
| solar_balance | Numeric(12,2) | NOT NULL, Default 0 | 46 |
| low_balance_threshold | Numeric(10,2) | Default 50 | 47 |
| electricity_minimum_activation | Numeric(10,2) | Default 20 | 52 |
| water_minimum_activation | Numeric(10,2) | Default 20 | 53 |
| auto_topup_enabled | Boolean | Default False | 54 |
| is_suspended | Boolean | Default False | 60 |
| suspension_reason | Text | Nullable | 61 |
| created_at | DateTime | Default utcnow | 62 |
| updated_at | DateTime | Default utcnow, onupdate | 63-65 |

### 7.2 Transaction Model Definition

**File:** `app/models/transaction.py`

| Column | Type | Constraints | Line |
|--------|------|-------------|------|
| id | Integer | Primary Key | 43 |
| transaction_number | String(50) | UNIQUE, NOT NULL | 44 |
| wallet_id | Integer | FK to wallets.id, NOT NULL | 45 |
| transaction_type | String(30) | NOT NULL, CHECK | 46 |
| amount | Numeric(12,2) | NOT NULL | 47 |
| balance_before | Numeric(12,2) | NOT NULL | 48 |
| balance_after | Numeric(12,2) | NOT NULL | 49 |
| reference | String(255) | Nullable | 50 |
| description | Text | Nullable | 51 |
| payment_method | String(20) | Nullable, CHECK | 52 |
| status | String(20) | Default "pending", CHECK | 57 |
| meter_id | Integer | FK to meters.id, Nullable | 63 |
| consumption_kwh | Numeric(10,3) | Nullable | 64 |
| rate_applied | Numeric(10,4) | Nullable | 65 |
| created_by | Integer | FK to users.id, Nullable | 67 |

### 7.3 Transaction Types (CHECK Constraint)

**Lines 70-72:**
- `topup`
- `purchase_electricity`
- `purchase_water`
- `purchase_solar`
- `consumption_electricity`
- `consumption_water`
- `consumption_solar`
- `refund`
- `adjustment`
- `service_charge`

### 7.4 Foreign Key References TO wallets.id

| Table | Column | ON DELETE | File:Line | Risk |
|-------|--------|-----------|-----------|------|
| transactions | wallet_id | NOT SET | transaction.py:45 | ⚠️ Orphan |
| payment_methods | wallet_id | NOT SET | payment_method.py:31 | ⚠️ Orphan |

### 7.5 Top-Up Flow

**File:** `app/routes/v1/wallets.py`, Lines 228-340

```
1. Validate wallet exists
2. Validate amount and payment_method
3. Determine meter_id from utility_type
4. Create transaction via svc_create_transaction()
5. Update utility-specific balance (electricity_balance, water_balance, etc.)
6. Update total balance
7. Commit to database
8. Log audit action
9. Send notification async
```

### 7.6 Balance Calculation Logic

**File:** `app/services/transactions.py`, Lines 71-76

```python
if transaction_type.startswith("topup") or transaction_type.startswith("refund"):
    balance_after = balance_before + float(amount)
elif transaction_type.startswith("deduction") or transaction_type.startswith("purchase"):
    balance_after = balance_before - float(amount)
else:
    balance_after = balance_before
```

### 7.7 Critical Issues

| Issue | Severity | Description |
|-------|----------|-------------|
| No Cascade to Transactions | HIGH | Wallet delete leaves orphaned transactions |
| No Cascade to PaymentMethods | HIGH | Wallet delete leaves orphaned payment methods |
| Manual Balance Sync | MEDIUM | Balance updates must be done explicitly, not automatic |
| Prepaid Disconnect Disabled | INFO | Zero-balance disconnect is commented out (safety) |

---

## 8. Cross-Entity Relationship Matrix

### 8.1 CASCADE Status Summary

| Parent | Child | CASCADE Setting | Status |
|--------|-------|-----------------|--------|
| User | 20+ audit tables | NOT SET | ⚠️ Orphan Risk |
| Person | UnitOwnership | CASCADE | ✅ |
| Person | UnitTenancy | CASCADE | ✅ |
| Person | MobileUser | SET NULL | ✅ |
| Person | Ticket | NOT SET | ⚠️ |
| Estate | Unit | NOT SET (manual) | ⚠️ |
| Unit | UnitOwnership | CASCADE | ✅ |
| Unit | UnitTenancy | CASCADE | ✅ |
| Unit | Wallet | NOT SET | ⚠️ Orphan |
| Unit | Ticket | NOT SET | ⚠️ Blocks |
| Unit | MobileInvite | SET NULL | ✅ |
| Meter | MeterReading | NOT SET | ⚠️ Blocks |
| Meter | MeterAlert | NOT SET | ⚠️ Blocks |
| Meter | DeviceCommand | NOT SET | ⚠️ Blocks |
| Meter | Transaction | NOT SET | ⚠️ |
| Wallet | Transaction | NOT SET | ⚠️ Orphan |
| Wallet | PaymentMethod | NOT SET | ⚠️ Orphan |

### 8.2 Deletion Dependency Chain

```
Delete Estate
├── Must delete all Units first
│   ├── Cascades: UnitOwnership, UnitTenancy
│   ├── Orphans: Wallet (with Transactions, PaymentMethods)
│   └── Blocks if: Tickets exist
├── Orphans: MeterReadings with estate_id
└── Orphans: Transactions (via wallets)

Delete Unit
├── Cascades: UnitOwnership, UnitTenancy
├── Orphans: Wallet (with Transactions, PaymentMethods)
├── Blocks if: Tickets exist
└── SET NULL: MobileInvite.unit_id

Delete Meter
├── Blocks if: MeterReadings exist (typically 1000s)
├── Blocks if: MeterAlerts exist
├── Blocks if: DeviceCommands exist
└── Orphans: Transaction.meter_id (nullable)

Delete Person
├── Blocked by: Service layer if ownerships/tenancies exist
├── Would cascade: UnitOwnership, UnitTenancy (if not blocked)
├── SET NULL: MobileUser.person_id
└── Orphans: Ticket.created_by_person_id

Delete User
├── No checks: Proceeds immediately
├── Orphans: All created_by/updated_by in 20+ tables
└── Orphans: Transaction.created_by, Ticket.assigned_to, etc.
```

---

## 9. Critical Data Integrity Issues

### 9.1 CRITICAL - Will Block Operations

| Entity | Issue | Impact | File:Line |
|--------|-------|--------|-----------|
| Meter | MeterReadings FK | Cannot delete meter with readings | meter_reading.py:41 |
| Meter | MeterAlerts FK | Cannot delete meter with alerts | meter_alert.py:27 |
| Meter | DeviceCommands FK | Cannot delete meter with commands | device_command.py:33 |
| Unit | Tickets FK | Cannot delete unit with tickets | ticket.py:54 |

### 9.2 HIGH - Orphaned Records

| Entity | Orphan Type | Impact | File:Line |
|--------|-------------|--------|-----------|
| User | 20+ tables | created_by/updated_by become invalid | various |
| Unit | Wallet | Wallet with transactions orphaned | wallet.py:40 |
| Wallet | Transaction | Transactions without parent wallet | transaction.py:45 |
| Wallet | PaymentMethod | Payment methods without wallet | payment_method.py:31 |
| Estate | MeterReadings | Readings with invalid estate_id | - |
| Person | Ticket | Tickets with invalid created_by_person_id | ticket.py:52 |

### 9.3 MEDIUM - Logic/Validation Issues

| Entity | Issue | Impact | Location |
|--------|-------|--------|----------|
| Meter | EUI validation only in routes | Celery tasks could bypass | meters.py:420-426 |
| Meter | Default mismatch | Model='plc', Service='cellular' | meter.py:40, meters.py:262 |
| Person | Cascade mismatch | Model has cascade, service blocks | person.py:57, persons.py:125 |
| Wallet | Manual balance sync | Balance not auto-updated | transactions.py |

---

## 10. Recommended Actions

### 10.1 Immediate - Database Constraints

```sql
-- Add CASCADE to meter_readings
ALTER TABLE meter_readings
DROP CONSTRAINT IF EXISTS meter_readings_meter_id_fkey;
ALTER TABLE meter_readings
ADD CONSTRAINT meter_readings_meter_id_fkey
FOREIGN KEY (meter_id) REFERENCES meters(id) ON DELETE CASCADE;

-- Add CASCADE to wallets
ALTER TABLE wallets
DROP CONSTRAINT IF EXISTS wallets_unit_id_fkey;
ALTER TABLE wallets
ADD CONSTRAINT wallets_unit_id_fkey
FOREIGN KEY (unit_id) REFERENCES units(id) ON DELETE CASCADE;

-- Add CASCADE to transactions
ALTER TABLE transactions
DROP CONSTRAINT IF EXISTS transactions_wallet_id_fkey;
ALTER TABLE transactions
ADD CONSTRAINT transactions_wallet_id_fkey
FOREIGN KEY (wallet_id) REFERENCES wallets(id) ON DELETE CASCADE;

-- Set NULL on tickets.unit_id
ALTER TABLE tickets
DROP CONSTRAINT IF EXISTS tickets_unit_id_fkey;
ALTER TABLE tickets
ADD CONSTRAINT tickets_unit_id_fkey
FOREIGN KEY (unit_id) REFERENCES units(id) ON DELETE SET NULL;
```

### 10.2 Application-Level Fixes

1. **User Delete** - Add pre-delete check for active references
2. **Meter Delete** - Implement soft delete or archive readings before delete
3. **Unit Delete** - Add wallet cleanup in delete_unit service
4. **Device EUI** - Move validation to service layer

### 10.3 Future Considerations

1. Implement soft delete across all entities
2. Add database triggers for cascade logging
3. Create orphan cleanup scheduled task
4. Add foreign key constraint documentation to models

---

## File Reference Summary

| Entity | Model | Routes | Service |
|--------|-------|--------|---------|
| User | app/models/user.py | app/routes/v1/users.py | app/services/users.py |
| Person | app/models/person.py | app/routes/v1/persons.py | app/services/persons.py |
| Estate | app/models/estate.py | app/routes/v1/estates.py | app/services/estates.py |
| Unit | app/models/unit.py | app/routes/v1/units.py | app/services/units.py |
| Meter | app/models/meter.py | app/routes/v1/meters.py | app/services/meters.py |
| Wallet | app/models/wallet.py | app/routes/v1/wallets.py | app/services/wallets.py |
| Transaction | app/models/transaction.py | app/routes/v1/transactions.py | app/services/transactions.py |
| UnitOwnership | app/models/unit_ownership.py | (via units.py) | app/services/unit_ownerships.py |
| UnitTenancy | app/models/unit_tenancy.py | (via units.py) | app/services/unit_tenancies.py |
| MeterReading | app/models/meter_reading.py | - | - |
| MeterAlert | app/models/meter_alert.py | - | - |
| DeviceCommand | app/models/device_command.py | - | - |
| Ticket | app/models/ticket.py | app/routes/v1/tickets.py | - |
| MobileUser | app/models/mobile_user.py | - | - |
| MobileInvite | app/models/mobile_invite.py | - | - |
| PaymentMethod | app/models/payment_method.py | - | - |

---

**Document Version:** 1.0
**Last Updated:** January 2026
**Methodology:** Direct code inspection with line-by-line verification

# Mobile App Phone-Based Authentication - Implementation Plan

**Project:** Quantify Metering System - Mobile App Authentication
**Date Started:** 2025-01-19
**Last Updated:** 2025-11-20
**Status:** ✅ Phases 1, 3, 4, 5 Complete - Ready for Testing! 🚀

---

## Table of Contents
1. [Overview](#overview)
2. [Requirements Summary](#requirements-summary)
3. [Architecture Decisions](#architecture-decisions)
4. [Database Schema Changes](#database-schema-changes)
5. [Backend Implementation Tasks](#backend-implementation-tasks)
6. [API Endpoints to Create](#api-endpoints-to-create)
7. [SMS Integration](#sms-integration)
8. [Security Considerations](#security-considerations)
9. [Testing Checklist](#testing-checklist)
10. [Progress Tracking](#progress-tracking)

---

## Overview

Implement phone-based authentication for the mobile app where Owners and Tenants can login using their phone number and password. The system will automatically create user accounts when persons are assigned as owners or tenants, and send SMS with temporary passwords that must be changed on first login.

### Key Features
- ✅ Phone number as primary login identifier (no email required in app)
- ✅ Temporary password sent via SMS when user is added
- ✅ Force password change on first login
- ✅ Support multiple units per user
- ✅ Password-based authentication (8 chars, mixed case + numbers)

---

## Requirements Summary

### 1. Email Field
- **Web Portal:** Email remains optional for Persons
- **Mobile App:** Email NOT used for authentication
- **Purpose:** Email kept for statements, receipts, notifications (optional)

### 2. Login Method
- **Method:** Phone number + password
- **Primary:** Option A (traditional password-based)
- **Future:** May add OTP as alternative

### 3. Password Requirements
- **Length:** Minimum 8 characters
- **Complexity:**
  - At least 1 uppercase letter
  - At least 1 lowercase letter
  - At least 1 number
  - Optional: special characters
- **Example:** `Abc12def`, `MyPass99`, `Home2024`

### 4. Temporary Password Generation
- **Format:** Matches password requirements (8 chars, mixed case + numbers)
- **Example:** `Temp1234`, `Start99A`
- **Delivery:** SMS to person's phone number
- **Expiry:** Must be changed on first login (never expires until changed)

### 5. Multiple Units Scenario
- **Approach:** User selects unit after login
- **Flow:**
  1. Login with phone + password → Authenticate Person
  2. Show list of all units user owns or rents
  3. User selects a unit
  4. App shows that unit's meters, wallet, transactions
  5. User can switch units anytime
- **API:** All meter/wallet endpoints require `unit_id` parameter
- **Authorization:** Person can only access units they own or rent (active ownership/tenancy)

### 6. User Account Creation Timing
- **Trigger:** When person is assigned to a unit as owner OR tenant
- **Process:**
  1. Admin adds person as owner/tenant via web portal
  2. System checks if Person has associated User account
  3. If no User account exists:
     - Create User account linked to Person
     - Generate temporary password
     - Send SMS with app link and temporary password
     - Set `password_must_change = True`
  4. If User account exists:
     - No action needed (they can already login)
     - Optional: Send SMS notification about new unit access

---

## Architecture Decisions

### User Account Model
```
Person (existing)
├── id
├── first_name
├── last_name
├── phone (required, unique)
├── email (optional)
├── id_number
└── ...

User (new)
├── id
├── person_id (FK to Person, unique)
├── phone_number (denormalized from Person for quick lookup)
├── password_hash
├── temporary_password_hash (nullable, cleared after first password change)
├── password_must_change (boolean, default False)
├── last_login
├── is_active (boolean, default True)
├── created_at
└── updated_at
```

**Why separate User from Person?**
- Person = Real person entity (owner, tenant, contact info)
- User = Authentication/login credentials
- Not all Persons need User accounts (e.g., emergency contacts, references)
- Cleaner separation of concerns

### Multiple Units Access
```python
# Get all units a user can access
def get_user_units(person_id):
    owned_units = UnitOwnership.query.filter_by(person_id=person_id).all()
    rented_units = UnitTenancy.query.filter_by(person_id=person_id, status='active').all()

    units = []
    for ownership in owned_units:
        units.append({
            'unit_id': ownership.unit_id,
            'role': 'owner',
            'unit_number': ownership.unit.unit_number,
            'estate_name': ownership.unit.estate.name
        })

    for tenancy in rented_units:
        units.append({
            'unit_id': tenancy.unit_id,
            'role': 'tenant',
            'unit_number': tenancy.unit.unit_number,
            'estate_name': tenancy.unit.estate.name
        })

    return units
```

---

## Database Schema Changes

### 1. Create `users` Table

```python
# File: app/models/user.py

from app.db import db
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash

class User(db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    person_id = db.Column(db.Integer, db.ForeignKey('persons.id'), unique=True, nullable=False)
    phone_number = db.Column(db.String(20), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    temporary_password_hash = db.Column(db.String(255), nullable=True)
    password_must_change = db.Column(db.Boolean, default=False, nullable=False)
    last_login = db.Column(db.DateTime, nullable=True)
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    person = db.relationship('Person', backref=db.backref('user', uselist=False))

    def set_password(self, password):
        """Set the user's permanent password"""
        self.password_hash = generate_password_hash(password)
        self.temporary_password_hash = None  # Clear temp password
        self.password_must_change = False

    def set_temporary_password(self, temp_password):
        """Set a temporary password that must be changed on first login"""
        self.temporary_password_hash = generate_password_hash(temp_password)
        self.password_must_change = True

    def check_password(self, password):
        """Check if password matches (checks both temp and permanent)"""
        # If temp password is set and matches, use it
        if self.temporary_password_hash and check_password_hash(self.temporary_password_hash, password):
            return True
        # Otherwise check permanent password
        return check_password_hash(self.password_hash, password)

    def to_dict(self):
        return {
            'id': self.id,
            'person_id': self.person_id,
            'phone_number': self.phone_number,
            'password_must_change': self.password_must_change,
            'last_login': self.last_login.isoformat() if self.last_login else None,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat(),
        }
```

### 2. Create Migration

**File:** `migrations/versions/XXXXX_create_users_table.py`

```python
"""create users table

Revision ID: p5q6r7s8t901
Revises: o0p1q2r3s456
Create Date: 2025-01-19

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers
revision = 'p5q6r7s8t901'
down_revision = 'o0p1q2r3s456'  # Last migration (drop resident_id)
branch_labels = None
depends_on = None

def upgrade():
    op.create_table(
        'users',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('person_id', sa.Integer(), nullable=False),
        sa.Column('phone_number', sa.String(length=20), nullable=False),
        sa.Column('password_hash', sa.String(length=255), nullable=False),
        sa.Column('temporary_password_hash', sa.String(length=255), nullable=True),
        sa.Column('password_must_change', sa.Boolean(), nullable=False, server_default='0'),
        sa.Column('last_login', sa.DateTime(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='1'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.ForeignKeyConstraint(['person_id'], ['persons.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('person_id'),
        sa.UniqueConstraint('phone_number')
    )

    # Add indexes
    op.create_index('ix_users_phone_number', 'users', ['phone_number'])
    op.create_index('ix_users_person_id', 'users', ['person_id'])

def downgrade():
    op.drop_index('ix_users_person_id', table_name='users')
    op.drop_index('ix_users_phone_number', table_name='users')
    op.drop_table('users')
```

### 3. Add Session/Token Table (for JWT alternative)

**Optional:** If we want to track sessions instead of stateless JWT

```python
# File: app/models/user_session.py

class UserSession(db.Model):
    __tablename__ = 'user_sessions'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    token = db.Column(db.String(255), unique=True, nullable=False, index=True)
    device_info = db.Column(db.String(255), nullable=True)  # Device type, OS version
    ip_address = db.Column(db.String(45), nullable=True)
    expires_at = db.Column(db.DateTime, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    user = db.relationship('User', backref='sessions')
```

---

## Backend Implementation Tasks

### Phase 1: Foundation (Core Models & Services) ✅ COMPLETED

#### ✅ Task 1.1: Create MobileUser Model - COMPLETED
- [x] Create `app/models/mobile_user.py` (separate from admin User model)
- [x] Add MobileUser model with all fields
- [x] Add helper methods (set_password, check_password, etc.)
- [x] Update `app/models/__init__.py` to import MobileUser

#### ✅ Task 1.2: Create Database Migration - COMPLETED
- [x] Create migration for mobile_users table (p5q6r7s8t901)
- [x] Run migration successfully
- [x] Verify table created with correct schema

#### ✅ Task 1.3: Create User Service Layer - COMPLETED
- [x] Create `app/services/mobile_users.py`
- [x] Implement `create_mobile_user(person_id, send_sms)`
- [x] Implement `get_mobile_user_by_phone(phone_number)`
- [x] Implement `get_mobile_user_by_person_id(person_id)`
- [x] Implement `authenticate_mobile_user(phone_number, password)`
- [x] Implement `change_password(mobile_user, new_password, current_password)`
- [x] Implement `get_user_units(person_id)` - returns all units user can access
- [x] Implement `can_access_unit(person_id, unit_id)` - authorization checker

#### ✅ Task 1.4: Password Utilities - COMPLETED
- [x] Create `app/utils/password_generator.py`
- [x] Implement `generate_temporary_password()` - 8 chars, mixed case + numbers
- [x] Implement `validate_password_strength(password)` - check requirements
- [x] Implement `validate_phone_number(phone)` - normalize to E.164 format
- [x] Add comprehensive tests (test_mobile_user.py) - All tests passing

### Phase 2: SMS Integration

#### ✅ Task 2.1: SMS Service Setup
- [ ] Choose SMS provider (Twilio? local SA provider?)
- [ ] Add SMS credentials to `.env`
- [ ] Create `app/services/sms_service.py`
- [ ] Implement `send_sms(phone_number, message)`
- [ ] Implement `send_welcome_sms(phone_number, temp_password, app_download_link)`

#### ✅ Task 2.2: SMS Templates
- [ ] Create SMS templates for:
  - Welcome message with temp password
  - Password changed confirmation
  - New unit added notification
  - Password reset (future)

### Phase 3: User Account Creation Triggers ✅ COMPLETED

#### ✅ Task 3.1: Owner Assignment Hook - COMPLETED
- [x] Update `app/routes/v1/unit_ownerships.py` endpoint `POST /api/units/{id}/owners`
- [x] After successful owner addition, check if Person has MobileUser account
- [x] If no MobileUser account, create one (SMS delivery pending Phase 2)
- [x] Return temp password in API response for manual delivery

#### ✅ Task 3.2: Tenant Assignment Hook - COMPLETED
- [x] Update `app/routes/v1/unit_tenancies.py` endpoint `POST /api/units/{id}/tenants`
- [x] After successful tenant addition, check if Person has MobileUser account
- [x] If no MobileUser account, create one (SMS delivery pending Phase 2)
- [x] Return temp password in API response for manual delivery

#### ✅ Task 3.3: Unit Creation Hook - COMPLETED
- [x] Update `app/routes/v1/units.py` endpoint `POST /units`
- [x] After creating unit and adding owners/tenants, trigger MobileUser account creation
- [x] Return list of created mobile users with temp passwords

### Phase 4: Mobile Authentication API ✅ COMPLETED

#### ✅ Task 4.1: Create Mobile Auth Routes - COMPLETED
- [x] Create `app/routes/mobile/__init__.py`
- [x] Create `app/routes/mobile/auth.py`
- [x] Register mobile blueprint in `application.py`
- [x] Implement JWT token generation and validation
- [x] Implement @require_mobile_auth decorator

#### ✅ Task 4.2: Login Endpoint - COMPLETED
- [x] `POST /api/mobile/auth/login`
- [x] Accept: phone_number, password
- [x] Validate phone format
- [x] Authenticate user using mobile_users service
- [x] Check if password_must_change
- [x] Generate JWT token (30 day expiry)
- [x] Return: token, user info, person info, units list, password_must_change flag

#### ✅ Task 4.3: Change Password Endpoint - COMPLETED
- [x] `POST /api/mobile/auth/change-password`
- [x] Accept: current_password (optional), new_password
- [x] Validate new password strength (8 chars, mixed case, numbers)
- [x] Check current password matches if provided
- [x] Update password using mobile_users service
- [x] Clear temporary password and password_must_change flag
- [x] Return success message

#### ✅ Task 4.4: Get User Units Endpoint - COMPLETED
- [x] `GET /api/mobile/auth/units`
- [x] Require authentication via JWT token
- [x] Return list of all units user owns or rents
- [x] Include role (owner/tenant) and relevant details for each unit

#### ✅ Task 4.5: Get Current User Endpoint - COMPLETED
- [x] `GET /api/mobile/auth/user`
- [x] Require authentication via JWT token
- [x] Return user profile info (mobile_user data)
- [x] Include person details (name, phone, email)

### Phase 5: Mobile Meter/Wallet APIs ✅ COMPLETED

#### ✅ Task 5.1: Get Unit Meters - COMPLETED
- [x] `GET /api/mobile/units/{unit_id}/meters`
- [x] Require authentication and verify unit access
- [x] Return all meters for the unit with current readings
- [x] Include device type and communication type

#### ✅ Task 5.2: Get Unit Wallet - COMPLETED
- [x] `GET /api/mobile/units/{unit_id}/wallet`
- [x] Require authentication and verify unit access
- [x] Return wallet balance, status, last transaction date

#### ✅ Task 5.3: Get Meter Details - COMPLETED
- [x] `GET /api/mobile/meters/{meter_id}`
- [x] Require authentication and verify unit access
- [x] Return meter details with unit info

#### ✅ Task 5.4: Get Meter Readings - COMPLETED
- [x] `GET /api/mobile/meters/{meter_id}/readings`
- [x] Support query parameters: days, limit
- [x] Return historical readings with consumption and cost

#### ✅ Task 5.5: Get Wallet Transactions - COMPLETED
- [x] `GET /api/mobile/units/{unit_id}/transactions`
- [x] Support query parameters: days, limit, type
- [x] Return transaction history ordered by date

#### ✅ Task 5.4: Get Meter Usage History
- [ ] `GET /api/mobile/meters/{meter_id}/usage`
- [ ] Query params: start_date, end_date, interval
- [ ] Return usage data for charts

### Phase 6: Authorization Middleware

#### ✅ Task 6.1: Create Mobile Auth Decorator
- [ ] Create `app/utils/mobile_auth.py`
- [ ] Implement `@require_mobile_auth` decorator
- [ ] Extract JWT token from Authorization header
- [ ] Validate token
- [ ] Load User and Person from token

#### ✅ Task 6.2: Create Unit Access Checker
- [ ] Implement `can_access_unit(person_id, unit_id)` helper
- [ ] Check UnitOwnership table
- [ ] Check UnitTenancy table (status = active)
- [ ] Return True if person owns or rents the unit

#### ✅ Task 6.3: Apply to All Mobile Endpoints
- [ ] Add authorization checks to all mobile endpoints
- [ ] Return 403 Forbidden if user tries to access unit they don't own/rent

### Phase 7: Testing & Documentation

#### ✅ Task 7.1: Unit Tests
- [ ] Test User model methods
- [ ] Test password generation and validation
- [ ] Test user service layer
- [ ] Test authentication logic
- [ ] Test unit access authorization

#### ✅ Task 7.2: Integration Tests
- [ ] Test complete owner/tenant assignment flow
- [ ] Test SMS sending (use mock in tests)
- [ ] Test login flow
- [ ] Test password change flow
- [ ] Test multi-unit access

#### ✅ Task 7.3: API Documentation
- [ ] Create `MOBILE_API_ENDPOINTS.md`
- [ ] Document all mobile endpoints with examples
- [ ] Include authentication requirements
- [ ] Add error response examples

---

## API Endpoints to Create

### Authentication Endpoints

```
POST   /api/mobile/auth/login
POST   /api/mobile/auth/change-password
GET    /api/mobile/auth/user
GET    /api/mobile/auth/units
POST   /api/mobile/auth/logout (optional)
```

### Unit & Meter Endpoints

```
GET    /api/mobile/units/{unit_id}/meters
GET    /api/mobile/units/{unit_id}/wallet
GET    /api/mobile/units/{unit_id}/transactions
GET    /api/mobile/meters/{meter_id}
GET    /api/mobile/meters/{meter_id}/usage
```

### Wallet & Payment Endpoints (from existing API doc)

```
GET    /api/mobile/wallet/balance
POST   /api/mobile/wallet/topup
GET    /api/mobile/wallet/transactions
```

---

## SMS Integration

### Provider Selection
- **Options:**
  - Twilio (international, reliable)
  - Clickatell (SA-based)
  - BulkSMS (SA-based, cheaper)
  - Custom provider

### Configuration
```python
# .env file
SMS_PROVIDER=twilio  # or 'clickatell', 'bulksms'
SMS_API_KEY=your_api_key
SMS_API_SECRET=your_api_secret
SMS_FROM_NUMBER=+27xxxxxxxxxx
APP_DOWNLOAD_LINK=https://play.google.com/store/apps/details?id=com.quantify.metering
```

### SMS Templates

**Welcome Message:**
```
Welcome to Quantify Metering!

Download our app: {app_link}

Your temporary password: {temp_password}

You must change this password when you first login.
```

**Password Changed:**
```
Your Quantify Metering password has been changed successfully.

If you didn't make this change, please contact support immediately.
```

**New Unit Added:**
```
Good news! You now have access to Unit {unit_number} at {estate_name} in the Quantify Metering app.
```

---

## Security Considerations

### Password Security
- ✅ Hash passwords using `werkzeug.security.generate_password_hash` (bcrypt)
- ✅ Never store plain text passwords
- ✅ Validate password strength on change
- ✅ Rate limit login attempts (prevent brute force)
- ✅ Temporary password cleared after first change

### JWT Tokens
- ✅ Use strong secret key (store in .env)
- ✅ Set reasonable expiration (24 hours)
- ✅ Include user_id and person_id in token payload
- ✅ Validate token on every request
- ✅ Consider refresh token mechanism

### Authorization
- ✅ Always verify user has access to requested unit
- ✅ Check both UnitOwnership and UnitTenancy
- ✅ Only return data for units user owns/rents
- ✅ Log all access attempts for audit

### Phone Number Validation
- ✅ Validate phone number format (E.164: +27xxxxxxxxx)
- ✅ Ensure phone numbers are unique
- ✅ Sanitize phone input

### Rate Limiting
- ✅ Login endpoint: 5 attempts per 15 minutes per IP
- ✅ Password change: 3 attempts per hour
- ✅ SMS sending: 3 per hour per phone number

---

## Testing Checklist

### Unit Tests
- [ ] User model password hashing works
- [ ] User model password checking works (temp and permanent)
- [ ] Password generator creates valid passwords
- [ ] Password validator rejects weak passwords
- [ ] User service creates users correctly
- [ ] User service authenticates correctly
- [ ] Unit access checker works for owners
- [ ] Unit access checker works for tenants
- [ ] Unit access checker denies unauthorized access

### Integration Tests
- [ ] Adding owner creates User account and sends SMS
- [ ] Adding tenant creates User account and sends SMS
- [ ] Login with correct credentials succeeds
- [ ] Login with wrong password fails
- [ ] Login with temporary password succeeds
- [ ] Password change with temp password works
- [ ] Password change clears password_must_change flag
- [ ] User can access all their units
- [ ] User cannot access other units
- [ ] JWT token validates correctly
- [ ] Expired JWT token is rejected

### Manual Testing
- [ ] Create person via web
- [ ] Assign person as owner to unit
- [ ] Verify SMS received with temp password
- [ ] Login via mobile API with temp password
- [ ] Verify password_must_change is true
- [ ] Change password via mobile API
- [ ] Logout and login with new password
- [ ] Verify can access unit's meters and wallet
- [ ] Add same person as tenant to another unit
- [ ] Verify both units appear in units list
- [ ] Switch between units in mobile app

---

## Progress Tracking

### Overall Status: 🟡 In Progress

### Phase Status
- [ ] Phase 1: Foundation (Core Models & Services) - **0% Complete**
- [ ] Phase 2: SMS Integration - **Not Started**
- [ ] Phase 3: User Account Creation Triggers - **Not Started**
- [ ] Phase 4: Mobile Authentication API - **Not Started**
- [ ] Phase 5: Mobile Meter/Wallet APIs - **Not Started**
- [ ] Phase 6: Authorization Middleware - **Not Started**
- [ ] Phase 7: Testing & Documentation - **Not Started**

### Completed Tasks
*(None yet)*

### Current Task
**Next:** Task 1.1 - Create User Model

### Blockers
*(None yet)*

---

## Notes & Decisions Log

### 2025-01-19 - Initial Planning
- Decided on phone-based authentication (Option A)
- Password requirements: 8 chars, mixed case, numbers
- Multiple units: Show selection screen after login
- User account created when person becomes owner/tenant
- Email optional, not used in mobile app

---

## Future Enhancements (Not in Scope)

- [ ] OTP login as alternative to password
- [ ] Biometric authentication (fingerprint, face)
- [ ] Push notifications for low balance
- [ ] In-app payments via PayFast
- [ ] Usage alerts and budgeting
- [ ] Multi-language support
- [ ] Offline mode for viewing cached data
- [ ] Password reset via SMS OTP

---

**Last Updated:** 2025-01-19
**Maintained By:** Development Team

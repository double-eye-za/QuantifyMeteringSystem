# API Documentation

## Quantify Metering System REST API v1

---

**Document Information**

- **Version**: 2.0
- **Date**: October 2025
- **Base URL**: `https://api.quantifymetering.com`
- **Architecture**: RESTful API with Flask 3.0+ and Jinja2 Templates
- **Based on**: Current implementation and route files analysis

---

## Overview

The Quantify Metering System provides both web interface routes (HTML templates) and JSON API endpoints. This documentation covers both types of endpoints.

### Key Features

- RESTful architecture
- JSON request/response format for API endpoints
- HTML template rendering for web interface
- Session-based authentication with Flask-Login
- Role-based permissions system
- Pagination and filtering support
- Comprehensive error handling
- Audit logging for all operations
- PDF export functionality
- Payment gateway integration support
- Real-time meter data management

---

## Authentication

### Session-Based Authentication

The system uses session-based authentication with Flask-Login. Users must first authenticate via the login endpoint to receive a session cookie.

#### Login

```http
POST /auth/login
Content-Type: application/json

{
    "username": "admin@quantify.com",
    "password": "secure_password"
}
```

#### Logout

```http
POST /auth/logout
```

#### Change Password

```http
POST /auth/change-password
Content-Type: application/json

{
    "current_password": "old_password",
    "new_password": "new_password"
}
```

---

## Common Headers

### Request Headers

```http
Content-Type: application/json
Accept: application/json
Cookie: session=<session_id> (for authenticated requests)
X-Request-ID: <uuid> (optional)
```

### Response Headers

```http
Content-Type: application/json (for API endpoints)
Content-Type: text/html (for template routes)
Set-Cookie: session=<session_id> (on login)
X-Rate-Limit-Limit: 1000
X-Rate-Limit-Remaining: 999
X-Rate-Limit-Reset: 1635724800
```

---

## Response Format

### JSON API Success Response

```json
{
    "data": {...},
    "message": "Success",
    "timestamp": "2025-10-09T12:00:00Z"
}
```

### JSON API List Response with Pagination

```json
{
    "data": [...],
    "page": 1,
    "per_page": 20,
    "total": 100,
    "pages": 5,
    "next_page": 2,
    "prev_page": null
}
```

### JSON API Error Response

```json
{
  "error": "Invalid credentials",
  "code": 401,
  "details": "Authentication failed",
  "timestamp": "2025-10-09T12:00:00Z"
}
```

### HTML Template Response

HTML template routes return rendered HTML pages with template data passed to Jinja2 templates.

---

## Status Codes

| Code | Description                                 |
| ---- | ------------------------------------------- |
| 200  | OK - Request successful                     |
| 201  | Created - Resource created                  |
| 204  | No Content - Request successful, no content |
| 400  | Bad Request - Invalid parameters            |
| 401  | Unauthorized - Authentication failed        |
| 403  | Forbidden - Access denied                   |
| 404  | Not Found - Resource not found              |
| 409  | Conflict - Resource conflict                |
| 422  | Unprocessable Entity - Validation error     |
| 429  | Too Many Requests - Rate limit exceeded     |
| 500  | Internal Server Error                       |

---

## API Endpoints

---

### Authentication APIs

#### POST /auth/login
Authenticate user and create session.

**Request:**
```json
{
  "username": "admin@quantify.com",
  "password": "secure_password"
}
```

**Response:**
```json
{
  "message": "Logged in",
  "data": {
    "user_id": 1
  }
}
```

#### POST /auth/logout
Logout user and destroy session.

**Response:**
```json
{
  "message": "Logged out"
}
```

#### POST /auth/change-password
Change user password.

**Request:**
```json
{
  "current_password": "old_password",
  "new_password": "new_password"
}
```

**Response:**
```json
{
  "message": "Password changed"
}
```

---

### Estates APIs

#### GET /estates
**HTML Template Route** - Renders the estates page with paginated estates and summary counts.

**Query Parameters:**
- `q` - Search query (searches name, code)
- `is_active` - Filter by active status (true/false)
- `page` - Page number (default: 1)
- `per_page` - Items per page (default: 20)

**Template Data Structure:**
```python
# Template receives these variables:
estates = [e.to_dict() for e in items]  
pagination = {
    "page": page,
    "per_page": per_page,
    "total": total,
    "pages": pages,
    "next_page": next_page,
    "prev_page": prev_page,
}
totals = {
    "estates": total_estates,
    "units": total_units,
    "meters": total_meters,
    "dc450s": active_dc450s,
}
electricity_rate_tables = [rt.to_dict() for rt in electricity_rate_tables]
water_rate_tables = [rt.to_dict() for rt in water_rate_tables]
meter_configs = {
    estate_id: {
        "elec": "X unit + 1 bulk",
        "water": "X unit + 1 bulk", 
        "solar": "X unit"
    }
}
```

**Response:** HTML page (`estates/estates.html`)

#### GET /estates/{id}
**JSON API Route** - Get estate details by ID.

**Response:**
```json
{
  "data": {
    "id": 1,
    "code": "WC001",
    "name": "Willow Creek",
    "address": "123 Main St",
    "city": "Johannesburg",
    "contact_name": "John Smith",
    "contact_phone": "+27 11 123 4567",
    "contact_email": "manager@willowcreek.com",
    "total_units": 50,
    "bulk_electricity_meter_id": 1,
    "bulk_water_meter_id": 2,
    "electricity_rate_table_id": 1,
    "water_rate_table_id": 2,
    "electricity_markup_percentage": 20.0,
    "water_markup_percentage": 0.0,
    "solar_free_allocation_kwh": 50.0,
    "is_active": true,
    "created_at": "2025-01-15T10:00:00Z"
  }
}
```

#### GET /estates/{id}/details
**HTML Template Route** - Get detailed estate information with units and statistics.

**Template Data Structure:**
```python
# Template receives these variables:
estate = estate.to_dict()
units = [
    {
        "unit": u.to_dict(),
        "resident": resident.to_dict() if resident else None,
        "wallet_balance": balance,
    }
    for u in units
]
pagination = pagination_meta
stats = {
    "total_units": total_units,
    "total_meters": total_meters
}
bulk_elec_meter = bulk_elec_meter.to_dict() if bulk_elec_meter else None
bulk_water_meter = bulk_water_meter.to_dict() if bulk_water_meter else None
elec_rate_table = elec_rate_table.to_dict() if elec_rate_table else None
water_rate_table = water_rate_table.to_dict() if water_rate_table else None
meter_config = {
    "elec": "X unit + 1 bulk",
    "water": "X unit + 1 bulk",
    "solar": "X unit"
}
```

**Response:** HTML page (`estates/estate_details.html`)

#### POST /estates
**JSON API Route** - Create a new estate.

**Request:**
```json
{
  "code": "OG001",
  "name": "Oak Gardens",
  "address": "456 Oak Street",
  "city": "Pretoria",
  "postal_code": "0001",
  "contact_name": "Jane Doe",
  "contact_phone": "+27 12 345 6789",
  "contact_email": "manager@oakgardens.com",
  "total_units": 75,
  "electricity_markup_percentage": 15.0,
  "water_markup_percentage": 5.0,
  "solar_free_allocation_kwh": 50.0
}
```

**Response:**
```json
{
  "data": {
    "id": 2,
    "code": "OG001",
    "name": "Oak Gardens",
    "address": "456 Oak Street",
    "city": "Pretoria",
    "postal_code": "0001",
    "contact_name": "Jane Doe",
    "contact_phone": "+27 12 345 6789",
    "contact_email": "manager@oakgardens.com",
    "total_units": 75,
    "electricity_markup_percentage": 15.0,
    "water_markup_percentage": 5.0,
    "solar_free_allocation_kwh": 50.0,
    "is_active": true,
    "created_at": "2025-01-15T10:00:00Z"
  }
}
```

#### PUT /estates/{id}
**JSON API Route** - Update estate details.

#### PATCH /api/estates/{id}/rate-assignment
**JSON API Route** - Update estate rate table assignments.

**Request:**
```json
{
  "electricity_rate_table_id": 1,
  "water_rate_table_id": 2,
  "electricity_markup_percentage": 20.0,
  "water_markup_percentage": 5.0,
  "solar_free_allocation_kwh": 50.0
}
```

**Response:**
```json
{
  "data": {
    "id": 1,
    "electricity_rate_table_id": 1,
    "water_rate_table_id": 2,
    "electricity_markup_percentage": 20.0,
    "water_markup_percentage": 5.0,
    "solar_free_allocation_kwh": 50.0
  }
}
```

#### DELETE /estates/{id}
**JSON API Route** - Soft delete an estate.

**Response:**
```json
{
  "message": "Deleted"
}
```

---

### Meters APIs

#### GET /meters
**HTML Template Route** - Renders the meters page with meters, unit assignments, balances, filters and stats.

**Query Parameters:**
- `meter_type` - Filter by type (electricity, water, solar, bulk_electricity, bulk_water)
- `communication_status` - Filter by status (online, offline, error)
- `estate_id` - Filter by estate
- `credit_status` - Filter by credit status (low, disconnected, ok)
- `page` - Page number (default: 1)
- `per_page` - Items per page (default: 20)

**Template Data Structure:**
```python
# Template receives these variables:
meters = [
    {
        **m.to_dict(),
        "unit": {
            "id": unit.id,
            "estate_id": unit.estate_id,
            "estate_name": estate_name,
            "unit_number": unit.unit_number,
            "occupancy_status": unit.occupancy_status,
        } if unit else None,
        "wallet": wallet.to_dict() if wallet else None,
        "credit_status": derived_credit,
    }
    for m in all_meters
]
pagination = {
    "page": page,
    "per_page": per_page,
    "total": total,
    "pages": pages,
    "next_page": next_page,
    "prev_page": prev_page,
}
estates = [{"id": e.id, "name": e.name} for e in Estate.query.all()]
units = [
    {
        "id": u.id,
        "unit_number": u.unit_number,
        "estate_id": u.estate_id,
        "has_electricity": bool(u.electricity_meter_id),
        "has_water": bool(u.water_meter_id),
        "has_solar": bool(u.solar_meter_id),
    }
    for u in Unit.query.all()
]
meter_types = [
    {"value": "electricity", "label": "Electricity"},
    {"value": "bulk_electricity", "label": "Bulk Electricity"},
    {"value": "water", "label": "Water"},
    {"value": "solar", "label": "Solar"},
]
stats = {
    "total": total_meters,
    "active": total_active,
    "low_credit": low_credit_count,
    "alerts": total_alerts,
}
current_filters = {
    "estate_id": estate_id,
    "meter_type": meter_type,
    "communication_status": comm_status,
    "credit_status": credit_status,
}
```

**Response:** HTML page (`meters/meters.html`)

#### GET /meters/{id}/details
**HTML Template Route** - Renders the meter details page with enriched data.

**Template Data Structure:**
```python
# Template receives these variables:
meter = meter.to_dict()
unit = {
    "unit_number": unit.unit_number,
    "estate_name": estate.name if estate else None,
    "resident_name": f"{resident.first_name} {resident.last_name}" if resident else None,
} if unit else None
wallet = wallet.to_dict() if wallet else None
balance_value = typed_balance(wallet, meter)
credit_status = "disconnected" if balance_value <= 0 else ("low" if balance_value < low_threshold else "ok")
recent_readings = [r.to_dict() for r in readings_items]
```

**Response:** HTML page (`meters/meter-details.html`)

#### GET /meters/{id}
**JSON API Route** - Get meter details by ID.

**Response:**
```json
{
  "data": {
    "id": 1,
    "serial_number": "E460-001",
    "meter_type": "electricity",
    "manufacturer": "Hexing",
    "model": "E460",
    "installation_date": "2025-01-15",
    "last_reading": 1234.567,
    "last_reading_date": "2025-10-09T12:00:00Z",
    "communication_type": "plc",
    "communication_status": "online",
    "last_communication": "2025-10-09T12:00:00Z",
    "firmware_version": "v2.1.0",
    "is_prepaid": true,
    "is_active": true,
    "created_at": "2025-01-15T10:00:00Z"
  }
}
```

#### POST /meters
**JSON API Route** - Register a new meter.

**Request:**
```json
{
  "serial_number": "E460-123",
  "meter_type": "electricity",
  "manufacturer": "Hexing",
  "model": "E460",
  "installation_date": "2025-01-15",
  "communication_type": "plc",
  "is_prepaid": true,
  "unit_id": 1
}
```

**Response:**
```json
{
  "data": {
    "id": 2,
    "serial_number": "E460-123",
    "meter_type": "electricity",
    "manufacturer": "Hexing",
    "model": "E460",
    "installation_date": "2025-01-15",
    "communication_type": "plc",
    "is_prepaid": true,
    "is_active": true,
    "created_at": "2025-01-15T10:00:00Z"
  }
}
```

#### PUT /meters/{id}
**JSON API Route** - Update meter information.

#### DELETE /meters/{id}
**JSON API Route** - Delete a meter.

#### GET /meters/available
**JSON API Route** - Get available meters by type.

**Query Parameters:**
- `meter_type` - Required meter type

**Response:**
```json
{
  "data": [
    {
      "id": 1,
      "serial_number": "E460-001",
      "meter_type": "electricity"
    }
  ]
}
```

#### GET /meters/{id}/readings
**JSON API Route** - Get meter readings history.

**Query Parameters:**
- `start_date` - Start date (ISO 8601)
- `end_date` - End date
- `page` - Page number
- `per_page` - Items per page

**Response:**
```json
{
  "data": [
    {
      "id": 1,
      "meter_id": 1,
      "reading_value": 1234.567,
      "reading_date": "2025-10-09T12:00:00Z",
      "reading_type": "automatic",
      "consumption_since_last": 12.34,
      "is_validated": true,
      "validation_date": "2025-10-09T12:05:00Z",
      "created_at": "2025-10-09T12:00:00Z"
    }
  ],
  "page": 1,
  "per_page": 20,
  "total": 100
}
```

#### GET /meters/export
**PDF Export Route** - Export meters data to PDF.

**Query Parameters:**
- `meter_type` - Filter by meter type
- `communication_status` - Filter by communication status
- `estate_id` - Filter by estate
- `credit_status` - Filter by credit status

**Response:** PDF file download

---

### Units APIs

#### GET /units
**HTML Template Route** - Renders the units page with units, estates, filters and pagination.

**Query Parameters:**
- `estate_id` - Filter by estate
- `occupancy_status` - Filter by status (occupied, vacant, maintenance)
- `q` - Search query
- `page` - Page number (default: 1)
- `per_page` - Items per page (default: 20)

**Template Data Structure:**
```python
# Template receives these variables:
units = [
    {
        **u.to_dict(),
        "resident": {
            "id": res.id,
            "first_name": res.first_name,
            "last_name": res.last_name,
            "phone": res.phone,
        } if u.resident_id and res else None
    }
    for u in items
]
estates = [{"id": e.id, "name": e.name} for e in Estate.get_all().all()]
electricity_meters = [serialize_meter(m) for m in Meter.get_electricity_meters()]
water_meters = [serialize_meter(m) for m in Meter.get_water_meters()]
solar_meters = [serialize_meter(m) for m in Meter.get_solar_meters()]
residents = [{"id": r.id, "name": f"{r.first_name} {r.last_name}"} for r in Resident.get_all_for_dropdown()]
pagination = meta
current_filters = {
    "estate_id": estate_id,
    "occupancy_status": occupancy_status,
    "q": q,
}
```

**Response:** HTML page (`units/units.html`)

#### GET /api/units
**JSON API Route** - Get units data as JSON.

**Query Parameters:**
- `estate_id` - Filter by estate
- `occupancy_status` - Filter by status
- `q` - Search query
- `page` - Page number (default: 1)
- `per_page` - Items per page (default: 20)

**Response:**
```json
{
  "data": [
    {
      "id": 1,
      "estate_id": 1,
      "unit_number": "A-101",
      "floor": "Ground",
      "building": "A",
      "bedrooms": 2,
      "bathrooms": 1,
      "size_sqm": 65.5,
      "occupancy_status": "occupied",
      "resident_id": 1,
      "electricity_meter_id": 1,
      "water_meter_id": 2,
      "solar_meter_id": 3,
      "electricity_rate_table_id": 1,
      "water_rate_table_id": 2,
      "is_active": true,
      "created_at": "2025-01-01T00:00:00Z"
    }
  ],
  "page": 1,
  "per_page": 20,
  "total": 50
}
```

#### GET /units/{id}
**HTML Template Route** - Renders the unit details page.

**Template Data Structure:**
```python
# Template receives these variables:
unit = unit
estate = estate
resident = resident
```

**Response:** HTML page (`units/unit-details.html`)

#### GET /api/units/{id}
**JSON API Route** - Get unit details as JSON.

**Response:**
```json
{
  "data": {
    "id": 1,
    "estate_id": 1,
    "unit_number": "A-101",
    "floor": "Ground",
    "building": "A",
    "bedrooms": 2,
    "bathrooms": 1,
    "size_sqm": 65.5,
    "occupancy_status": "occupied",
    "resident_id": 1,
    "electricity_meter_id": 1,
    "water_meter_id": 2,
    "solar_meter_id": 3,
    "electricity_rate_table_id": 1,
    "water_rate_table_id": 2,
    "is_active": true,
    "created_at": "2025-01-01T00:00:00Z"
  }
}
```

#### GET /units/{unit_id}/wallet-statement
**HTML Template Route** - Renders the wallet statement page.

**Template Data Structure:**
```python
# Template receives these variables:
unit = unit
wallet = wallet
estate = estate
transactions = transactions
last_topup_date = last_topup.completed_at if last_topup else None
```

**Response:** HTML page (`wallets/wallet-statement.html`)

#### GET /units/{unit_id}/visual
**HTML Template Route** - Renders the unit visual diagram page.

**Template Data Structure:**
```python
# Template receives these variables:
unit_id = unit_id
```

**Response:** HTML page (`units/unit-visual.html`)

#### POST /units
**JSON API Route** - Create a new unit.

**Request:**
```json
{
  "estate_id": 1,
  "unit_number": "B-201",
  "floor": "Second",
  "building": "B",
  "bedrooms": 2,
  "bathrooms": 1,
  "size_sqm": 65.5
}
```

**Response:**
```json
{
  "data": {
    "id": 2,
    "estate_id": 1,
    "unit_number": "B-201",
    "floor": "Second",
    "building": "B",
    "bedrooms": 2,
    "bathrooms": 1,
    "size_sqm": 65.5,
    "occupancy_status": "vacant",
    "is_active": true,
    "created_at": "2025-01-15T10:00:00Z"
  }
}
```

#### PUT /units/{id}
**JSON API Route** - Update unit information.

#### DELETE /units/{id}
**JSON API Route** - Delete a unit.

#### POST /api/units/overrides
**JSON API Route** - Apply rate table overrides to units.

**Request:**
```json
{
  "rate_table_id": 1,
  "utility_type": "electricity",
  "unit_ids": [1, 2, 3],
  "estate_id": 1,
  "unit_numbers": ["A-101", "A-102"]
}
```

**Response:**
```json
{
  "message": "Rate table override applied to 5 units",
  "updated_unit_ids": [1, 2, 3, 4, 5]
}
```

#### GET /api/units/overrides
**JSON API Route** - Get all units with rate table overrides.

**Response:**
```json
{
  "data": {
    "1": {
      "unit_id": 1,
      "unit_number": "A-101",
      "estate_id": 1,
      "electricity_rate_table_id": 1,
      "water_rate_table_id": null
    }
  }
}
```

#### DELETE /api/units/overrides
**JSON API Route** - Remove rate table overrides from units.

---

### Wallets APIs

#### GET /billing
**HTML Template Route** - Renders the billing page with wallet overview.

**Query Parameters:**
- `estate` - Filter by estate (default: "all")
- `status` - Filter by status (all, low, zero, active)
- `search` - Search query

**Template Data Structure:**
```python
# Template receives these variables:
total_balances = float(total_balances)
todays_topups = float(todays_topups)
todays_usage = float(todays_usage)
low_balance_units = low_balance_units
zero_balance_units = zero_balance_units
estates = estates
wallets = wallets  # Query result with last_topup_date
recent_transactions = recent_transactions
topup_history = topup_history
current_estate = estate_id
current_status = status_filter
current_search = search_query
```

**Response:** HTML page (`billing/billing.html`)

#### GET /wallets/{id}
**JSON API Route** - Get wallet details.

**Response:**
```json
{
  "data": {
    "id": 1,
    "unit_id": 1,
    "balance": 450.0,
    "electricity_balance": 200.0,
    "water_balance": 150.0,
    "solar_balance": 100.0,
    "low_balance_threshold": 50.0,
    "low_balance_alert_type": "fixed",
    "low_balance_days_threshold": 3,
    "last_low_balance_alert": null,
    "alert_frequency_hours": 24,
    "electricity_minimum_activation": 20.0,
    "water_minimum_activation": 20.0,
    "auto_topup_enabled": false,
    "auto_topup_amount": 0.0,
    "auto_topup_threshold": 0.0,
    "is_suspended": false,
    "last_topup_date": "2025-10-01T10:00:00Z",
    "created_at": "2025-01-01T00:00:00Z"
  }
}
```

#### POST /wallets/{id}/topup
**JSON API Route** - Add credit to wallet.

**Request:**
```json
{
  "amount": 500.0,
  "payment_method": "eft",
  "reference": "EFT123456",
  "metadata": {
    "bank": "Standard Bank",
    "account_holder": "John Smith"
  }
}
```

**Response:**
```json
{
  "data": {
    "transaction_id": 1,
    "transaction_number": "TXN20251009001",
    "status": "completed"
  }
}
```

#### GET /wallets/{id}/pending-transactions
**JSON API Route** - Get pending transactions awaiting payment confirmation.

**Response:**
```json
{
  "data": [
    {
      "transaction_id": 1,
      "amount": 500.0,
      "payment_method": "eft",
      "status": "pending",
      "payment_gateway_ref": "PG_TXN_123456",
      "created_at": "2025-10-09T10:00:00Z",
      "expires_at": "2025-10-09T11:00:00Z"
    }
  ],
  "page": 1,
  "per_page": 20,
  "total": 5
}
```

---

### Transactions APIs

#### GET /transactions
**JSON API Route** - List transactions with filtering.

**Query Parameters:**
- `wallet_id` - Filter by wallet
- `transaction_type` - Filter by type
- `status` - Filter by status
- `page` - Page number (default: 1)
- `per_page` - Items per page (default: 20)

**Response:**
```json
{
  "data": [
    {
      "id": 1,
      "transaction_number": "TXN20251009001",
      "wallet_id": 1,
      "transaction_type": "topup",
      "amount": 500.0,
      "status": "completed",
      "created_at": "2025-10-09T10:00:00Z"
    }
  ],
  "page": 1,
  "per_page": 20,
  "total": 100
}
```

#### GET /transactions/{id}
**JSON API Route** - Get transaction details.

**Response:**
```json
{
  "data": {
    "id": 1,
    "transaction_number": "TXN20251009001",
    "wallet_id": 1,
    "transaction_type": "topup",
    "amount": 500.0,
    "status": "completed",
    "created_at": "2025-10-09T10:00:00Z"
  }
}
```

#### POST /transactions/{id}/reverse
**JSON API Route** - Reverse a transaction.

**Request:**
```json
{
  "reason": "Error in payment processing"
}
```

**Response:**
```json
{
  "data": {
    "id": 1,
    "status": "reversed"
  }
}
```

---

### Rate Tables APIs

#### GET /rate-tables
**HTML Template Route** - Renders the rate tables page.

**Template Data Structure:**
```python
# Template receives these variables:
rate_tables = all_rate_tables
rate_table_tiers = rate_table_id_to_tiers
time_of_use_rates = rate_table_id_to_tou
estates = estates
electricity_rate_tables = electricity_rate_tables
water_rate_tables = water_rate_tables
```

**Response:** HTML page (`rate-tables/rate-table.html`)

#### GET /rate-tables/builder
**HTML Template Route** - Renders the rate table builder page.

**Response:** HTML page (`rate-tables/rate-table-builder.html`)

#### GET /rate-tables/{id}/edit
**HTML Template Route** - Renders the edit page for a specific rate table.

**Template Data Structure:**
```python
# Template receives these variables:
rate_table = rt.to_dict()
```

**Response:** HTML page (`rate-tables/edit-rate-table.html`)

#### GET /api/rate-tables
**JSON API Route** - List all rate tables.

**Query Parameters:**
- `utility_type` - Filter by type (electricity, water, solar)
- `is_active` - Filter by active status
- `page` - Page number (default: 1)
- `per_page` - Items per page (default: 20)

**Response:**
```json
{
  "data": [
    {
      "id": 1,
      "name": "Residential Electricity - Tiered",
      "utility_type": "electricity",
      "rate_structure": "tiered",
      "is_default": false,
      "effective_from": "2025-01-01",
      "effective_to": null,
      "is_active": true,
      "created_at": "2025-01-01T00:00:00Z"
    }
  ],
  "page": 1,
  "per_page": 20,
  "total": 5
}
```

#### GET /api/rate-tables/{id}
**JSON API Route** - Get rate table details.

**Response:**
```json
{
  "data": {
    "id": 1,
    "name": "Residential Electricity - Tiered",
    "utility_type": "electricity",
    "rate_structure": "tiered",
    "is_default": false,
    "effective_from": "2025-01-01",
    "effective_to": null,
    "is_active": true,
    "created_at": "2025-01-01T00:00:00Z"
  }
}
```

#### GET /api/rate-tables/{id}/details
**JSON API Route** - Get detailed rate table with tiers and time-of-use rates.

**Response:**
```json
{
  "data": {
    "id": 1,
    "name": "Residential Electricity - Tiered",
    "utility_type": "electricity",
    "rate_structure": "tiered",
    "is_default": false,
    "effective_from": "2025-01-01",
    "effective_to": null,
    "is_active": true,
    "tiers": [
      {
        "tier_number": 1,
        "from": 0.0,
        "to": 50.0,
        "rate": 1.5,
        "description": "First 50 kWh"
      }
    ],
    "time_of_use": [],
    "created_at": "2025-01-01T00:00:00Z"
  }
}
```

#### POST /api/rate-tables
**JSON API Route** - Create a new rate table.

**Request:**
```json
{
  "name": "Water Rates 2025",
  "utility_type": "water",
  "rate_structure": "tiered",
  "effective_from": "2025-01-01",
  "is_default": false,
  "is_active": true
}
```

**Response:**
```json
{
  "data": {
    "id": 2,
    "name": "Water Rates 2025",
    "utility_type": "water",
    "rate_structure": "tiered",
    "is_default": false,
    "effective_from": "2025-01-01",
    "effective_to": null,
    "is_active": true,
    "created_at": "2025-01-15T10:00:00Z"
  }
}
```

#### POST /api/rate-tables/preview
**JSON API Route** - Preview rate calculation.

**Request:**
```json
{
  "electricity_kwh": 175.0,
  "water_kl": 10.0,
  "electricity_rate_table_id": 1,
  "water_rate_table_id": 2,
  "electricity_markup_percentage": 20.0,
  "water_markup_percentage": 5.0,
  "service_fee": 0.0
}
```

**Response:**
```json
{
  "data": {
    "electricity_cost": 315.0,
    "water_cost": 157.5,
    "service_fee": 0.0,
    "total_cost": 472.5,
    "breakdown": {
      "electricity": {
        "consumption": 175.0,
        "base_cost": 262.5,
        "markup": 52.5,
        "total": 315.0
      },
      "water": {
        "consumption": 10.0,
        "base_cost": 150.0,
        "markup": 7.5,
        "total": 157.5
      }
    }
  }
}
```

#### PUT /api/rate-tables/{id}
**JSON API Route** - Update rate table.

#### DELETE /api/rate-tables/{id}
**JSON API Route** - Delete a rate table.

---

### Residents APIs

#### GET /residents
**HTML Template Route** - Renders the residents page.

**Query Parameters:**
- `q` - Search query
- `is_active` - Filter by active status (true/false)
- `unit_id` - Filter by unit

**Template Data Structure:**
```python
# Template receives these variables:
residents = [
    {
        **r.to_dict(),
        "unit": {
            "id": unit.id,
            "unit_number": unit.unit_number,
            "estate_name": estate.name if estate else None,
        } if unit else None
    }
    for r in items
]
units = [
    {
        "id": unit.id,
        "unit_number": unit.unit_number,
        "estate_name": estate.name if estate else "Unknown",
    }
    for unit in units_with_estates
]
pagination = meta
current_filters = {"q": search, "is_active": is_active, "unit_id": unit_id}
```

**Response:** HTML page (`residents/residents.html`)

#### GET /api/residents
**JSON API Route** - List all residents.

**Query Parameters:**
- `q` - Search query
- `page` - Page number (default: 1)
- `per_page` - Items per page (default: 20)

**Response:**
```json
{
  "data": [
    {
      "id": 1,
      "id_number": "8001015009087",
      "first_name": "John",
      "last_name": "Smith",
      "email": "john.smith@example.com",
      "phone": "+27 11 123 4567",
      "alternate_phone": "+27 82 123 4567",
      "emergency_contact_name": "Jane Smith",
      "emergency_contact_phone": "+27 11 987 6543",
      "lease_start_date": "2025-01-01",
      "lease_end_date": "2025-12-31",
      "status": "active",
      "is_active": true,
      "app_user_id": null,
      "created_at": "2025-01-01T00:00:00Z"
    }
  ],
  "page": 1,
  "per_page": 20,
  "total": 50
}
```

#### POST /residents
**JSON API Route** - Create a new resident.

**Request:**
```json
{
  "id_number": "8001015009087",
  "first_name": "John",
  "last_name": "Smith",
  "email": "john.smith@example.com",
  "phone": "+27 11 123 4567",
  "alternate_phone": "+27 82 123 4567",
  "emergency_contact_name": "Jane Smith",
  "emergency_contact_phone": "+27 11 987 6543",
  "lease_start_date": "2025-01-01",
  "lease_end_date": "2025-12-31"
}
```

**Response:**
```json
{
  "data": {
    "id": 1,
    "id_number": "8001015009087",
    "first_name": "John",
    "last_name": "Smith",
    "email": "john.smith@example.com",
    "phone": "+27 11 123 4567",
    "alternate_phone": "+27 82 123 4567",
    "emergency_contact_name": "Jane Smith",
    "emergency_contact_phone": "+27 11 987 6543",
    "lease_start_date": "2025-01-01",
    "lease_end_date": "2025-12-31",
    "status": "active",
    "is_active": true,
    "app_user_id": null,
    "created_at": "2025-01-01T00:00:00Z"
  }
}
```

#### PUT /residents/{id}
**JSON API Route** - Update resident information.

#### DELETE /residents/{id}
**JSON API Route** - Delete a resident.

---

### Users APIs

#### GET /users
**HTML Template Route** - Renders the users page.

**Query Parameters:**
- `search` - Search query
- `status` - Filter by status (active, disabled)
- `role_id` - Filter by role
- `page` - Page number (default: 1)
- `per_page` - Items per page (default: 25)

**Template Data Structure:**
```python
# Template receives these variables:
users = [
    {
        "id": user.id,
        "username": user.username,
        "email": user.email,
        "first_name": user.first_name,
        "last_name": user.last_name,
        "full_name": f"{user.first_name} {user.last_name}",
        "phone": user.phone,
        "is_active": user.is_active,
        "is_super_admin": user.is_super_admin,
        "role_id": user.role_id,
        "role_name": user.role.name if user.role else None,
        "created_at": user.created_at.strftime("%Y-%m-%d %H:%M") if user.created_at else None,
    }
    for user in users
]
roles = Role.get_roles_for_dropdown()
pagination = {
    "page": page,
    "per_page": per_page,
    "total": total,
    "total_pages": (total + per_page - 1),
}
current_filters = {"search": search, "status": status, "role_id": role_id}
```

**Response:** HTML page (`users/users.html`)

#### POST /api/users
**JSON API Route** - Create a new user.

**Request:**
```json
{
  "username": "manager@estate.com",
  "email": "manager@estate.com",
  "password": "secure_password",
  "first_name": "Estate",
  "last_name": "Manager",
  "phone": "+27 11 987 6543",
  "role_id": 2,
  "is_active": true
}
```

**Response:**
```json
{
  "success": true,
  "message": "User created successfully",
  "user_id": 2
}
```

#### PUT /api/users/{id}
**JSON API Route** - Update user information.

**Response:**
```json
{
  "success": true,
  "message": "User updated successfully"
}
```

#### DELETE /api/users/{id}
**JSON API Route** - Delete a user.

**Response:**
```json
{
  "success": true,
  "message": "User deleted successfully"
}
```

#### PUT /api/users/{id}/enable
**JSON API Route** - Enable a user.

**Response:**
```json
{
  "success": true,
  "message": "User enabled successfully"
}
```

#### PUT /api/users/{id}/disable
**JSON API Route** - Disable a user.

**Response:**
```json
{
  "success": true,
  "message": "User disabled successfully"
}
```

---

### Roles APIs

#### GET /roles
**HTML Template Route** - Renders the roles page.

**Query Parameters:**
- `search` - Search query
- `page` - Page number (default: 1)
- `per_page` - Items per page (default: 25)

**Template Data Structure:**
```python
# Template receives these variables:
roles = [
    {
        "id": role.id,
        "name": role.name,
        "description": role.description,
        "is_system_role": role.is_system_role,
        "permission_id": role.permission_id,
        "permission_name": role.permission.name if role.permission else None,
        "permission_description": role.permission.description if role.permission else None,
        "permissions": role.permission.permissions if role.permission else {},
        "user_count": len(role.users) if hasattr(role, "users") else 0,
        "created_at": role.created_at.strftime("%Y-%m-%d %H:%M") if role.created_at else None,
    }
    for role in roles
]
permissions = Permission.get_all_permissions()
modules_actions = {
    module: sorted(list(actions)) 
    for module, actions in sorted(modules_actions.items())
}
pagination = {
    "page": page,
    "per_page": per_page,
    "total": total,
    "total_pages": (total + per_page - 1) // per_page,
}
current_filters = {"search": search}
```

**Response:** HTML page (`roles&permissions/roles.html`)

#### POST /api/roles
**JSON API Route** - Create a new role.

**Request:**
```json
{
  "name": "estate_manager",
  "description": "Estate management access",
  "permissions": {
    "estates": {"view": true, "edit": true},
    "units": {"view": true, "edit": false}
  },
  "permission_id": 2
}
```

**Response:**
```json
{
  "success": true,
  "message": "Role created successfully",
  "role_id": 2
}
```

#### PUT /api/roles/{id}
**JSON API Route** - Update role information.

**Response:**
```json
{
  "success": true,
  "message": "Role updated successfully"
}
```

#### DELETE /api/roles/{id}
**JSON API Route** - Delete a role.

**Response:**
```json
{
  "success": true,
  "message": "Role deleted successfully"
}
```

---

### Settings APIs

#### GET /settings
**HTML Template Route** - Renders the settings page.

**Response:** HTML page (`settings/settings.html`)

#### GET /api/settings
**JSON API Route** - Get all system settings.

**Response:**
```json
{
  "settings": {
    "org_name": "Quantify Metering",
    "contact_email": "admin@quantifymetering.com",
    "default_language": "English",
    "timezone": "Africa/Johannesburg (GMT+2)",
    "date_format": "YYYY-MM-DD",
    "session_timeout": "15",
    "min_password_length": "8",
    "require_uppercase": "false",
    "require_numbers": "false",
    "require_special_chars": "false",
    "enable_2fa": "false",
    "account_lockout": "false",
    "allowed_ips": "",
    "sms_provider": "twilio",
    "emergency_contact": "",
    "system_alerts": "false",
    "security_alerts": "false",
    "system_updates": "false"
  }
}
```

#### POST /settings/general
**JSON API Route** - Save general settings.

**Request:**
```json
{
  "org_name": "Quantify Metering",
  "contact_email": "admin@quantifymetering.com",
  "default_language": "English",
  "timezone": "Africa/Johannesburg (GMT+2)",
  "date_format": "YYYY-MM-DD",
  "session_timeout": 15
}
```

**Response:**
```json
{
  "message": "General settings saved successfully"
}
```

#### POST /settings/security
**JSON API Route** - Save security settings.

#### POST /settings/notifications
**JSON API Route** - Save notification settings.

---

### Profile APIs

#### GET /profile
**HTML Template Route** - Renders the profile page.

**Template Data Structure:**
```python
# Template receives these variables:
user = {
    "id": user.id,
    "first_name": user.first_name,
    "last_name": user.last_name,
    "email": user.email,
    "phone": user.phone,
    "username": user.username,
    "role": role_name,
    "last_login": user.last_login.isoformat() if user.last_login else None,
    "created_at": user.created_at.isoformat() if user.created_at else None,
}
```

**Response:** HTML page (`profile/profile.html`)

#### POST /profile
**JSON API Route** - Update current user profile.

**Request:**
```json
{
  "first_name": "John",
  "last_name": "Doe",
  "email": "john.doe@example.com",
  "phone": "+27 11 987 6543"
}
```

**Response:**
```json
{
  "data": {
    "id": 1,
    "first_name": "John",
    "last_name": "Doe",
    "email": "john.doe@example.com",
    "phone": "+27 11 987 6543"
  }
}
```

#### POST /profile/change-password
**JSON API Route** - Change current user password.

**Request:**
```json
{
  "current_password": "old_password",
  "new_password": "new_password",
  "confirm_password": "new_password"
}
```

**Response:**
```json
{
  "message": "Password updated successfully"
}
```

#### GET /profile/password-requirements
**JSON API Route** - Get password requirements.

**Response:**
```json
{
  "requirements": {
    "min_length": 8,
    "require_uppercase": false,
    "require_numbers": false,
    "require_special_chars": false
  }
}
```

---

### Audit Logs APIs

#### GET /audit-logs
**HTML Template Route** - Renders the audit logs page.

**Query Parameters:**
- `action` - Filter by action
- `user_id` - Filter by user ID
- `start_date` - Start date filter
- `end_date` - End date filter
- `page` - Page number (default: 1)
- `per_page` - Items per page (default: 20)

**Template Data Structure:**
```python
# Template receives these variables:
logs = [
    {
        "id": a.id,
        "user_id": a.user_id,
        "user_name": None,  # Populated from users_map
        "action": a.action,
        "entity_type": a.entity_type,
        "entity_id": a.entity_id,
        "ip_address": a.ip_address,
        "created_at": a.created_at.strftime("%Y-%m-%d %H:%M:%S") if a.created_at else None,
    }
    for a in items
]
users_map = {u.id: f"{u.first_name} {u.last_name}".strip() for u in users}
users_for_filter = [
    {"id": u.id, "name": f"{u.first_name} {u.last_name}".strip() or u.email}
    for u in User.query.all()
]
pagination = meta
current_filters = {
    "action": action,
    "user_id": user_id,
    "start_date": start_date,
    "end_date": end_date,
}
```

**Response:** HTML page (`audit-logs/audit-logs.html`)

#### GET /api/audit-logs
**JSON API Route** - List audit logs.

**Query Parameters:**
- `action` - Filter by action
- `user_id` - Filter by user ID
- `entity_type` - Filter by entity type
- `page` - Page number (default: 1)
- `per_page` - Items per page (default: 20)

**Response:**
```json
{
  "data": [
    {
      "id": 1,
      "user_id": 1,
      "action": "estate.create",
      "entity_type": "estate",
      "entity_id": 1,
      "ip_address": "192.168.1.1",
      "user_agent": "Mozilla/5.0...",
      "request_id": "req_123456",
      "created_at": "2025-10-09T10:00:00Z"
    }
  ],
  "page": 1,
  "per_page": 20,
  "total": 150
}
```

#### GET /api/audit-logs/{id}
**JSON API Route** - Get specific audit log entry.

**Response:**
```json
{
  "data": {
    "id": 1,
    "user_id": 1,
    "user_name": "John Doe",
    "action": "estate.create",
    "entity_type": "estate",
    "entity_id": 1,
    "old_values": null,
    "new_values": {
      "name": "Willow Creek",
      "code": "WC001"
    },
    "ip_address": "192.168.1.1",
    "user_agent": "Mozilla/5.0...",
    "request_id": "req_123456",
    "created_at": "2025-10-09T10:00:00Z"
  }
}
```

---

### Notifications APIs

#### GET /notifications
**JSON API Route** - List notifications.

**Query Parameters:**
- `recipient_type` - Filter by recipient type
- `status` - Filter by status
- `priority` - Filter by priority
- `page` - Page number (default: 1)
- `per_page` - Items per page (default: 20)

**Response:**
```json
{
  "data": [
    {
      "id": 1,
      "recipient_type": "resident",
      "status": "sent",
      "priority": "high",
      "subject": "Low Balance Alert",
      "created_at": "2025-10-09T10:00:00Z"
    }
  ],
  "page": 1,
  "per_page": 20,
  "total": 25
}
```

---

## Rate Limiting

API rate limits per authentication level:

| User Type     | Requests/Hour | Burst |
| ------------- | ------------- | ----- |
| Anonymous     | 100           | 10    |
| Authenticated | 1000          | 100   |
| Super Admin   | 10000         | 500   |

Rate limit headers:

```http
X-Rate-Limit-Limit: 1000
X-Rate-Limit-Remaining: 999
X-Rate-Limit-Reset: 1635724800
```

---

## Error Handling

### Validation Errors

```json
{
  "error": "Validation failed",
  "code": 422,
  "details": {
    "fields": {
      "amount": ["Amount must be greater than 0"],
      "payment_method": ["Invalid payment method"]
    }
  }
}
```

### Business Logic Errors

```json
{
  "error": "Insufficient balance",
  "code": 400,
  "details": "Wallet balance of R25.00 is insufficient for purchase of R100.00"
}
```

---

## SDK Examples

### Python

```python
import requests

class QuantifyAPI:
    def __init__(self, base_url="https://api.quantifymetering.com"):
        self.base_url = base_url
        self.session = requests.Session()
    
    def login(self, username, password):
        response = self.session.post(
            f"{self.base_url}/auth/login",
            json={"username": username, "password": password}
        )
        return response.json()
    
    def get_estate(self, estate_id):
        response = self.session.get(
            f"{self.base_url}/estates/{estate_id}"
        )
        return response.json()
    
    def topup_wallet(self, wallet_id, amount, payment_method="eft"):
        response = self.session.post(
            f"{self.base_url}/wallets/{wallet_id}/topup",
            json={
                "amount": amount,
                "payment_method": payment_method,
                "reference": f"TXN{wallet_id}"
            }
        )
        return response.json()

# Usage
api = QuantifyAPI()
api.login("admin@quantify.com", "password")
estate = api.get_estate(1)
result = api.topup_wallet(1, 500.0)
```

### cURL

```bash
# Login
curl -X POST "https://api.quantifymetering.com/auth/login" \
     -H "Content-Type: application/json" \
     -d '{"username": "admin@quantify.com", "password": "password"}'

# Get estate details
curl -X GET "https://api.quantifymetering.com/estates/1" \
     -H "Accept: application/json" \
     -b cookies.txt

# Top up wallet
curl -X POST "https://api.quantifymetering.com/wallets/1/topup" \
     -H "Content-Type: application/json" \
     -b cookies.txt \
     -d '{"amount": 500.0, "payment_method": "eft", "reference": "TXN123"}'
```

---

## Testing

### Test Environment

- Base URL: `https://api-test.quantifymetering.com`
- Test credentials provided upon request
- Data reset daily at 00:00 UTC

### Postman Collection

Available at: `https://api.quantifymetering.com/docs/postman-collection.json`

---

## Changelog

### Version 3.0.0 (December 2024)

- Updated to reflect current API implementation
- Session-based authentication with Flask-Login
- Comprehensive API documentation for all endpoints
- Added all missing API endpoints (audit logs, profile, residents, roles, settings, users)
- Updated data types to use Integer primary keys instead of UUIDs
- Enhanced wallet APIs with payment gateway integration
- Added consumption analysis and smart alerts
- Comprehensive notification system
- System settings and health check endpoints
- Corrected all endpoint paths based on actual route files
- **MAJOR UPDATE**: Distinguished between HTML template routes and JSON API routes
- **ACCURATE**: Documented actual template data structures passed to Jinja2 templates
- **CORRECT**: Documented actual JSON API responses with proper data structures

### Version 2.0.0 (October 2025)

- Initial API documentation
- Basic authentication
- Core endpoints for estates, units, meters, wallets
- Reporting endpoints
- Rate limiting implementation

### Planned for Version 4.0.0 (Mobile App Phase)

- Mobile app API extensions
- Push notifications for low balance alerts
- WebSocket support for real-time updates
- Webhook system for meter events
- GraphQL endpoint
- Advanced analytics endpoints

---

## Support

For API support:

- Email: api-support@quantifymetering.com
- Documentation: https://api.quantifymetering.com/docs
- Status Page: https://status.quantifymetering.com

---

_End of API Documentation v3.0_
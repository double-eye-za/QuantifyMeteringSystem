# API Documentation
## Quantify Metering System REST API v1

---

**Document Information**
- **Version**: 1.0
- **Date**: October 2025
- **Base URL**: `https://api.quantifymetering.com/api/v1`
- **Architecture**: RESTful API with Flask 3.0+
- **Based on**: development_guidelines.md

---

## Overview

The Quantify Metering System API provides programmatic access to manage estates, units, meters, billing, and reporting functionality. The API follows RESTful principles and returns JSON responses.

### Key Features
- RESTful architecture
- JSON request/response format
- Basic Authentication for all access
- Pagination and filtering support
- Comprehensive error handling
- Rate limiting

---

## Authentication

### Basic Authentication

All API requests require Basic Authentication using the Authorization header:

```http
Authorization: Basic base64(username:password)
```

Example:
```python
import requests
from requests.auth import HTTPBasicAuth

response = requests.get(
    'https://api.quantifymetering.com/api/v1/estates',
    auth=HTTPBasicAuth('admin@quantify.com', 'secure_password')
)
```

---

## Common Headers

### Request Headers
```http
Content-Type: application/json
Accept: application/json
Authorization: Basic <credentials>
X-Request-ID: <uuid> (optional)
```

### Response Headers
```http
Content-Type: application/json
X-Request-ID: <uuid>
X-Rate-Limit-Limit: 1000
X-Rate-Limit-Remaining: 999
X-Rate-Limit-Reset: 1635724800
```

---

## Response Format

### Success Response
```json
{
    "data": {...},
    "message": "Success",
    "timestamp": "2025-10-09T12:00:00Z"
}
```

### List Response with Pagination
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

### Error Response
```json
{
    "error": "Invalid credentials",
    "code": 401,
    "details": "Authentication failed",
    "timestamp": "2025-10-09T12:00:00Z"
}
```

---

## Status Codes

| Code | Description |
|------|-------------|
| 200 | OK - Request successful |
| 201 | Created - Resource created |
| 204 | No Content - Request successful, no content |
| 400 | Bad Request - Invalid parameters |
| 401 | Unauthorized - Authentication failed |
| 403 | Forbidden - Access denied |
| 404 | Not Found - Resource not found |
| 409 | Conflict - Resource conflict |
| 422 | Unprocessable Entity - Validation error |
| 429 | Too Many Requests - Rate limit exceeded |
| 500 | Internal Server Error |

---

## Endpoints


### Estates

#### GET /estates
List all estates with pagination and filtering.

**Query Parameters:**
- `q` - Search query (searches name, code)
- `page` - Page number (default: 1)
- `per_page` - Items per page (default: 20, max: 100)
- `sort` - Sort field (name, created_at)
- `order` - Sort order (asc, desc)
- `is_active` - Filter by active status

**Response:**
```json
{
    "data": [
        {
            "id": "uuid",
            "code": "WC001",
            "name": "Willow Creek",
            "address": "123 Main St",
            "city": "Johannesburg",
            "total_units": 50,
            "contact_name": "John Smith",
            "contact_phone": "+27 11 123 4567",
            "contact_email": "manager@willowcreek.com",
            "bulk_electricity_meter_id": "uuid",
            "bulk_water_meter_id": "uuid",
            "electricity_rate_table_id": "uuid",
            "water_rate_table_id": "uuid",
            "electricity_markup_percentage": 20.00,
            "water_markup_percentage": 0.00,
            "solar_free_allocation_kwh": 50.00,
            "is_active": true,
            "created_at": "2025-01-15T10:00:00Z"
        }
    ],
    "page": 1,
    "per_page": 20,
    "total": 2
}
```

#### GET /estates/{id}
Get estate details by ID.

**Response:**
```json
{
    "data": {
        "id": "uuid",
        "code": "WC001",
        "name": "Willow Creek",
        "units_summary": {
            "total": 50,
            "occupied": 45,
            "vacant": 5
        },
        "meters_summary": {
            "total": 150,
            "online": 148,
            "offline": 2
        },
        "wallet_summary": {
            "total_balance": 145230.00,
            "low_balance_count": 3
        }
    }
}
```

#### POST /estates
Create a new estate.

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
    "electricity_markup_percentage": 15.00,
    "solar_free_allocation_kwh": 50.00
}
```

#### PUT /estates/{id}
Update estate details.

#### DELETE /estates/{id}
Soft delete an estate.

---

### Units

#### GET /units
List all units with filtering.

**Query Parameters:**
- `estate_id` - Filter by estate
- `occupancy_status` - Filter by status (occupied, vacant, maintenance)
- `has_low_balance` - Filter units with low balance
- `q` - Search query

**Response:**
```json
{
    "data": [
        {
            "id": "uuid",
            "estate_id": "uuid",
            "estate_name": "Willow Creek",
            "unit_number": "A-101",
            "floor": "Ground",
            "building": "A",
            "occupancy_status": "occupied",
            "resident": {
                "id": "uuid",
                "name": "John Smith",
                "phone": "+27 11 123 4567",
                "email": "john@example.com"
            },
            "wallet": {
                "balance": 250.00,
                "electricity_balance": 100.00,
                "water_balance": 150.00,
                "low_balance": false
            },
            "meters": {
                "electricity": {
                    "serial": "E460-001",
                    "status": "online",
                    "last_reading": 1234.567
                },
                "water": {
                    "serial": "WTR-001",
                    "status": "online",
                    "last_reading": 567.890
                },
                "solar": {
                    "serial": "SOL-001",
                    "status": "online",
                    "last_reading": 234.567
                }
            }
        }
    ]
}
```

#### GET /units/{id}
Get detailed unit information.

#### POST /units
Create a new unit.

**Request:**
```json
{
    "estate_id": "uuid",
    "unit_number": "B-201",
    "floor": "Second",
    "building": "B",
    "bedrooms": 2,
    "bathrooms": 1,
    "size_sqm": 65.5
}
```

#### PUT /units/{id}
Update unit information.

#### POST /units/{id}/assign-resident
Assign a resident to a unit.

**Request:**
```json
{
    "resident_id": "uuid",
    "lease_start_date": "2025-01-01",
    "lease_end_date": "2025-12-31"
}
```

---

### Meters

#### GET /meters
List all meters with filtering.

**Query Parameters:**
- `meter_type` - Filter by type (electricity, water, solar, bulk_electricity, bulk_water)
- `communication_status` - Filter by status (online, offline, error)
- `estate_id` - Filter by estate
- `unit_id` - Filter by unit

#### GET /meters/{id}
Get meter details.

#### POST /meters
Register a new meter.

**Request:**
```json
{
    "serial_number": "E460-123",
    "meter_type": "electricity",
    "manufacturer": "Hexing",
    "model": "E460",
    "installation_date": "2025-01-15",
    "communication_type": "plc",
    "is_prepaid": true
}
```

#### GET /meters/{id}/readings
Get meter readings history.

**Query Parameters:**
- `start_date` - Start date (ISO 8601)
- `end_date` - End date
- `interval` - Grouping interval (15min, hourly, daily, monthly)

**Response:**
```json
{
    "data": [
        {
            "reading_date": "2025-10-09T12:00:00Z",
            "reading_value": 1234.567,
            "consumption": 12.34,
            "is_validated": true
        }
    ]
}
```

#### POST /meters/{id}/readings
Submit manual meter reading.

**Request:**
```json
{
    "reading_value": 1250.00,
    "reading_date": "2025-10-09T14:00:00Z"
}
```

---

### Wallets

#### GET /wallets/{id}
Get wallet details with alert configuration.

**Response:**
```json
{
    "data": {
        "id": "uuid",
        "unit_id": "uuid",
        "balance": 450.00,
        "electricity_balance": 200.00,
        "water_balance": 150.00,
        "solar_balance": 100.00,
        "alert_config": {
            "low_balance_threshold": 50.00,
            "alert_type": "fixed",
            "days_threshold": 3,
            "alert_frequency_hours": 24,
            "smart_alerts_enabled": true,
            "daily_avg_consumption": 15.50,
            "estimated_days_remaining": 29
        },
        "activation_minimums": {
            "electricity_minimum": 20.00,
            "water_minimum": 20.00
        },
        "auto_topup_enabled": false,
        "is_suspended": false,
        "last_transaction": {
            "date": "2025-10-09T10:00:00Z",
            "type": "topup",
            "amount": 500.00
        }
    }
}
```

#### POST /wallets/{id}/topup
Add credit to wallet. Ready for payment gateway integration.

**Request:**
```json
{
    "amount": 500.00,
    "payment_method": "eft",  // "eft", "card", "instant_eft", "cash"
    "reference": "EFT123456",
    "payment_gateway_ref": "PG_TXN_123456",  // From payment gateway
    "payment_status": "success",  // For gateway callback
    "metadata": {
        "bank": "Standard Bank",
        "account_holder": "John Smith",
        "timestamp": "2025-10-09T10:00:00Z"
    }
}
```

**Response:**
```json
{
    "data": {
        "transaction_id": "uuid",
        "transaction_number": "TXN20251009001",
        "wallet_id": "uuid",
        "amount": 500.00,
        "balance_before": 100.00,
        "balance_after": 600.00,
        "payment_method": "eft",
        "reference": "EFT123456",
        "payment_gateway_ref": "PG_TXN_123456",
        "status": "completed",
        "created_at": "2025-10-09T10:00:00Z"
    }
}
```

#### POST /wallets/{id}/purchase
Purchase utility credits. Will only activate meter if minimum amount is met.

**Request:**
```json
{
    "utility_type": "electricity",
    "amount": 100.00
}
```

**Response:**
```json
{
    "data": {
        "transaction_id": "uuid",
        "transaction_number": "TXN20251009001",
        "amount": 100.00,
        "balance_before": 450.00,
        "balance_after": 350.00,
        "electricity_credit_added": 100.00,
        "meter_updated": true,
        "meter_activated": true,
        "activation_minimum_met": true
    }
}
```

#### PUT /wallets/{id}/alert-config
Update wallet alert configuration.

**Request:**
```json
{
    "low_balance_threshold": 75.00,
    "alert_type": "days",
    "days_threshold": 5,
    "alert_frequency_hours": 12,
    "smart_alerts_enabled": true
}
```

#### PUT /wallets/{id}/activation-minimums
Update meter activation minimums.

**Request:**
```json
{
    "electricity_minimum": 30.00,
    "water_minimum": 25.00
}
```

#### GET /wallets/{id}/consumption-analysis
Get consumption analysis for smart alerts.

**Response:**
```json
{
    "data": {
        "daily_avg_consumption": 22.50,
        "weekly_avg_consumption": 157.50,
        "peak_usage_hour": 18,
        "lowest_usage_hour": 3,
        "estimated_days_remaining": 20,
        "recommended_topup": 450.00,
        "consumption_trend": "increasing",
        "last_7_days": [
            {"date": "2025-10-03", "consumption": 20.50},
            {"date": "2025-10-04", "consumption": 21.00},
            {"date": "2025-10-05", "consumption": 22.50},
            {"date": "2025-10-06", "consumption": 23.00},
            {"date": "2025-10-07", "consumption": 24.00},
            {"date": "2025-10-08", "consumption": 23.50},
            {"date": "2025-10-09", "consumption": 23.00}
        ]
    }
}
```

#### POST /wallets/{id}/initiate-payment
Initiate payment via payment gateway (creates pending transaction).

**Request:**
```json
{
    "amount": 500.00,
    "payment_method": "card",
    "return_url": "https://app.quantify.com/payment/success",
    "cancel_url": "https://app.quantify.com/payment/cancel",
    "notification_url": "https://api.quantify.com/webhooks/payment"
}
```

**Response:**
```json
{
    "data": {
        "transaction_id": "uuid",
        "payment_gateway_ref": "PG_INIT_123456",
        "redirect_url": "https://gateway.provider.com/pay/PG_INIT_123456",
        "status": "pending",
        "expires_at": "2025-10-09T10:30:00Z"
    }
}
```

#### POST /wallets/payment-webhook
Payment gateway callback webhook (used by payment provider).

**Request (from payment gateway):**
```json
{
    "transaction_ref": "PG_TXN_123456",
    "internal_ref": "uuid",
    "status": "success",  // "success", "failed", "cancelled"
    "amount": 500.00,
    "payment_method": "card",
    "card_last4": "1234",
    "timestamp": "2025-10-09T10:05:00Z",
    "signature": "hmac_signature_here"
}
```

**Response:**
```json
{
    "received": true,
    "processed": true
}
```

#### GET /wallets/{id}/payment-methods
Get available payment methods for wallet.

**Response:**
```json
{
    "data": {
        "available_methods": [
            {
                "method": "eft",
                "name": "Electronic Funds Transfer",
                "enabled": true,
                "min_amount": 50.00,
                "max_amount": 10000.00,
                "processing_time": "instant"
            },
            {
                "method": "card",
                "name": "Credit/Debit Card",
                "enabled": true,
                "min_amount": 10.00,
                "max_amount": 5000.00,
                "processing_time": "instant"
            },
            {
                "method": "instant_eft",
                "name": "Instant EFT",
                "enabled": true,
                "min_amount": 50.00,
                "max_amount": 5000.00,
                "processing_time": "instant"
            }
        ],
        "saved_methods": [
            {
                "id": "uuid",
                "method": "card",
                "display": "**** **** **** 1234",
                "expires": "12/25",
                "is_default": true
            }
        ]
    }
}
```

#### GET /wallets/{id}/pending-transactions
Get pending transactions awaiting payment confirmation.

**Response:**
```json
{
    "data": [
        {
            "transaction_id": "uuid",
            "amount": 500.00,
            "payment_method": "card",
            "status": "pending",
            "payment_gateway_ref": "PG_INIT_123456",
            "created_at": "2025-10-09T10:00:00Z",
            "expires_at": "2025-10-09T10:30:00Z"
        }
    ]
}
```

---

### Transactions

#### GET /transactions
List transactions with filtering.

**Query Parameters:**
- `wallet_id` - Filter by wallet
- `transaction_type` - Filter by type
- `start_date` - Start date
- `end_date` - End date
- `status` - Filter by status

#### GET /transactions/{id}
Get transaction details.

#### POST /transactions/{id}/reverse
Reverse a transaction (admin only).

**Request:**
```json
{
    "reason": "Error in payment processing"
}
```

---

### Rate Tables

#### GET /rate-tables
List all rate tables.

**Query Parameters:**
- `utility_type` - Filter by type (electricity, water, solar)
- `is_active` - Filter by active status
- `estate_id` - Filter by assigned estate

#### GET /rate-tables/{id}
Get rate table details.

**Response:**
```json
{
    "data": {
        "id": "uuid",
        "name": "Residential Electricity - Tiered",
        "utility_type": "electricity",
        "rate_structure": {
            "type": "tiered",
            "tiers": [
                {
                    "from_kwh": 0,
                    "to_kwh": 50,
                    "rate_per_kwh": 1.50
                },
                {
                    "from_kwh": 51,
                    "to_kwh": 200,
                    "rate_per_kwh": 2.00
                },
                {
                    "from_kwh": 201,
                    "to_kwh": null,
                    "rate_per_kwh": 2.50
                }
            ]
        },
        "effective_from": "2025-01-01",
        "is_active": true
    }
}
```

#### POST /rate-tables
Create a new rate table.

**Request (Tiered):**
```json
{
    "name": "Water Rates 2025",
    "utility_type": "water",
    "rate_structure": {
        "type": "tiered",
        "tiers": [
            {
                "from_kl": 0,
                "to_kl": 10,
                "rate_per_kl": 15.00
            },
            {
                "from_kl": 11,
                "to_kl": 25,
                "rate_per_kl": 20.00
            }
        ]
    },
    "effective_from": "2025-01-01"
}
```

**Request (Time-of-Use):**
```json
{
    "name": "TOU Electricity 2025",
    "utility_type": "electricity",
    "rate_structure": {
        "type": "time_of_use",
        "periods": [
            {
                "name": "peak",
                "rate_per_kwh": 3.00,
                "times": [
                    {"start": "06:00", "end": "09:00", "days": ["weekday"]},
                    {"start": "17:00", "end": "20:00", "days": ["weekday"]}
                ]
            },
            {
                "name": "standard",
                "rate_per_kwh": 2.00,
                "times": [
                    {"start": "09:00", "end": "17:00", "days": ["weekday"]},
                    {"start": "07:00", "end": "20:00", "days": ["weekend"]}
                ]
            },
            {
                "name": "off_peak",
                "rate_per_kwh": 1.50,
                "times": [
                    {"start": "20:00", "end": "06:00", "days": ["all"]}
                ]
            }
        ]
    },
    "effective_from": "2025-01-01"
}
```

#### PUT /rate-tables/{id}
Update rate table.

#### POST /rate-tables/{id}/calculate
Calculate cost based on consumption.

**Request:**
```json
{
    "consumption_kwh": 175,
    "datetime": "2025-10-09T18:00:00Z"
}
```

**Response:**
```json
{
    "data": {
        "consumption": 175,
        "breakdown": [
            {"tier": 1, "units": 50, "rate": 1.50, "cost": 75.00},
            {"tier": 2, "units": 125, "rate": 2.00, "cost": 250.00}
        ],
        "total_cost": 325.00,
        "with_markup": 390.00,
        "markup_percentage": 20.00
    }
}
```

---

### Reports

#### GET /reports/estate-consumption
Estate consumption report.

**Query Parameters:**
- `estate_id` - Estate ID (required)
- `start_date` - Start date
- `end_date` - End date
- `utility_type` - electricity or water
- `interval` - daily, weekly, monthly

**Response:**
```json
{
    "data": {
        "estate": "Willow Creek",
        "period": "2025-10-01 to 2025-10-31",
        "utility_type": "electricity",
        "summary": {
            "total_consumption": 15000.00,
            "average_daily": 500.00,
            "peak_day": "2025-10-15",
            "peak_consumption": 750.00
        },
        "daily_breakdown": [
            {
                "date": "2025-10-01",
                "consumption": 480.00,
                "cost": 960.00
            }
        ]
    }
}
```

#### GET /reports/reconciliation
Bulk meter vs unit meters reconciliation.

**Query Parameters:**
- `estate_id` - Estate ID
- `date` - Report date
- `utility_type` - electricity or water

**Response:**
```json
{
    "data": {
        "estate": "Willow Creek",
        "date": "2025-10-09",
        "utility_type": "electricity",
        "bulk_meter_reading": 1500.00,
        "sum_unit_readings": 1450.00,
        "variance": 50.00,
        "variance_percentage": 3.33,
        "units_detail": [
            {
                "unit": "A-101",
                "reading": 25.50
            }
        ]
    }
}
```

#### GET /reports/low-credit
Units with low credit balances.

**Query Parameters:**
- `estate_id` - Filter by estate
- `threshold` - Custom threshold (default: 50.00)

**Response:**
```json
{
    "data": [
        {
            "unit_id": "uuid",
            "unit_number": "A-101",
            "estate": "Willow Creek",
            "wallet_balance": 25.00,
            "days_remaining": 2,
            "resident": {
                "name": "John Smith",
                "phone": "+27 11 123 4567",
                "email": "john@example.com"
            },
            "last_topup": "2025-10-01T10:00:00Z"
        }
    ]
}
```

#### GET /reports/revenue
Revenue report.

**Query Parameters:**
- `estate_id` - Filter by estate
- `start_date` - Start date
- `end_date` - End date
- `group_by` - day, week, month

**Response:**
```json
{
    "data": {
        "period": "2025-10-01 to 2025-10-31",
        "total_revenue": 45000.00,
        "breakdown": {
            "topups": 35000.00,
            "electricity": 25000.00,
            "water": 8000.00,
            "solar": 2000.00,
            "service_charges": 0.00
        },
        "daily_revenue": [
            {
                "date": "2025-10-01",
                "amount": 1500.00
            }
        ]
    }
}
```

#### POST /reports/export
Export report to file.

**Request:**
```json
{
    "report_type": "revenue",
    "format": "pdf",
    "parameters": {
        "estate_id": "uuid",
        "start_date": "2025-10-01",
        "end_date": "2025-10-31"
    }
}
```

**Response:**
```json
{
    "data": {
        "file_url": "https://api.quantifymetering.com/downloads/report_abc123.pdf",
        "expires_at": "2025-10-10T12:00:00Z"
    }
}
```

---

### Notifications

#### GET /notifications
List notifications.

**Query Parameters:**
- `recipient_type` - user, resident, system
- `status` - pending, sent, delivered, failed
- `priority` - low, normal, high, critical

#### POST /notifications
Send notification.

**Request:**
```json
{
    "recipient_type": "resident",
    "recipient_id": "uuid",
    "notification_type": "low_balance",
    "subject": "Low Balance Alert",
    "message": "Your wallet balance is below R50. Please top up to avoid disconnection.",
    "channel": "email",
    "priority": "high"
}
```

#### POST /notifications/bulk
Send bulk notifications.

**Request:**
```json
{
    "filter": {
        "estate_id": "uuid",
        "has_low_balance": true
    },
    "notification": {
        "type": "low_balance_reminder",
        "subject": "Urgent: Low Balance",
        "message": "Your balance is low. Top up now to avoid service interruption.",
        "channels": ["email", "sms"]
    }
}
```

---

### System

#### GET /system/health
System health check.

**Response:**
```json
{
    "data": {
        "status": "healthy",
        "database": "connected",
        "meters_online": 448,
        "meters_offline": 2,
        "api_version": "1.0.0",
        "timestamp": "2025-10-09T12:00:00Z"
    }
}
```

#### GET /system/settings
Get system settings with wallet and meter defaults.

**Response:**
```json
{
    "data": {
        "wallet": {
            "default_low_balance_threshold": 50.00,
            "default_low_balance_days": 3,
            "alert_frequency_hours": 24,
            "auto_calculate_daily_usage": true,
            "smart_alert_enabled": true
        },
        "meter": {
            "default_electricity_minimum": 20.00,
            "default_water_minimum": 20.00,
            "reading_interval": 900
        },
        "notification": {
            "retry_limit": 3,
            "email_enabled": true,
            "sms_enabled": false,
            "push_enabled": false
        },
        "system": {
            "session_timeout": 3600,
            "max_login_attempts": 5,
            "password_min_length": 8
        }
    }
}
```

#### PUT /system/settings
Update system settings (super admin only).

**Request:**
```json
{
    "category": "wallet",
    "settings": {
        "default_low_balance_threshold": 75.00,
        "default_low_balance_days": 5,
        "smart_alert_enabled": true
    }
}
```

#### GET /system/settings/wallet-defaults
Get default wallet configuration for new units.

**Response:**
```json
{
    "data": {
        "low_balance_threshold": 50.00,
        "alert_type": "fixed",
        "days_threshold": 3,
        "alert_frequency_hours": 24,
        "electricity_minimum": 20.00,
        "water_minimum": 20.00,
        "auto_calculate_usage": true,
        "calculation_period_days": 7
    }
}
```

---

### Audit

#### GET /audit/logs
Get audit logs.

**Query Parameters:**
- `user_id` - Filter by user
- `action` - Filter by action
- `entity_type` - Filter by entity type
- `start_date` - Start date
- `end_date` - End date

**Response:**
```json
{
    "data": [
        {
            "id": "uuid",
            "user": "admin@quantify.com",
            "action": "update_wallet_balance",
            "entity_type": "wallet",
            "entity_id": "uuid",
            "changes": {
                "balance": {
                    "old": 100.00,
                    "new": 600.00
                }
            },
            "ip_address": "192.168.1.1",
            "timestamp": "2025-10-09T10:00:00Z"
        }
    ]
}
```

---

## Batch Operations

### POST /batch
Execute multiple operations in a single request.

**Request:**
```json
{
    "operations": [
        {
            "method": "POST",
            "path": "/wallets/uuid1/topup",
            "body": {"amount": 500.00}
        },
        {
            "method": "POST",
            "path": "/wallets/uuid2/topup",
            "body": {"amount": 300.00}
        }
    ]
}
```

**Response:**
```json
{
    "data": {
        "results": [
            {"status": 200, "data": {...}},
            {"status": 200, "data": {...}}
        ]
    }
}
```

---

## Webhooks (Future)

### Webhook Events
- `meter.offline` - Meter goes offline
- `wallet.low_balance` - Balance below threshold
- `transaction.completed` - Transaction processed
- `meter.tamper_detected` - Tamper alert

### Webhook Payload
```json
{
    "event": "wallet.low_balance",
    "data": {
        "wallet_id": "uuid",
        "unit_id": "uuid",
        "balance": 25.00,
        "threshold": 50.00
    },
    "timestamp": "2025-10-09T12:00:00Z"
}
```

---

## Rate Limiting

API rate limits per authentication level:

| User Type | Requests/Hour | Burst |
|-----------|--------------|-------|
| Anonymous | 100 | 10 |
| Authenticated | 1000 | 100 |
| Super Admin | 10000 | 500 |

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
from requests.auth import HTTPBasicAuth

class QuantifyAPI:
    def __init__(self, username, password, base_url="https://api.quantifymetering.com/api/v1"):
        self.auth = HTTPBasicAuth(username, password)
        self.base_url = base_url
    
    def get_estates(self, page=1, per_page=20):
        response = requests.get(
            f"{self.base_url}/estates",
            params={"page": page, "per_page": per_page},
            auth=self.auth
        )
        return response.json()
    
    def topup_wallet(self, wallet_id, amount):
        response = requests.post(
            f"{self.base_url}/wallets/{wallet_id}/topup",
            json={"amount": amount, "payment_method": "eft"},
            auth=self.auth
        )
        return response.json()

# Usage
api = QuantifyAPI("admin@quantify.com", "password")
estates = api.get_estates()
result = api.topup_wallet("wallet_uuid", 500.00)
```

### cURL
```bash
# Get estates
curl -X GET "https://api.quantifymetering.com/api/v1/estates" \
     -u "admin@quantify.com:password" \
     -H "Accept: application/json"

# Top up wallet
curl -X POST "https://api.quantifymetering.com/api/v1/wallets/{id}/topup" \
     -u "admin@quantify.com:password" \
     -H "Content-Type: application/json" \
     -d '{"amount": 500.00, "payment_method": "eft"}'
```

---

## Testing

### Test Environment
- Base URL: `https://api-test.quantifymetering.com/api/v1`
- Test credentials provided upon request
- Data reset daily at 00:00 UTC

### Postman Collection
Available at: `https://api.quantifymetering.com/docs/postman-collection.json`

---

## Changelog

### Version 1.0.0 (October 2025)
- Initial API documentation
- Basic authentication
- Core endpoints for estates, units, meters, wallets
- Reporting endpoints
- Rate limiting implementation

### Planned for Version 2.0.0 (Mobile App Phase)
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

*End of API Documentation v1.0*
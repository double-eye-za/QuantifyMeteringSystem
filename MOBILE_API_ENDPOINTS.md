# Mobile App API Endpoints Documentation

**Base URL:** `/api/mobile`
**Authentication:** JWT Bearer Token (except login endpoint)
**Date:** 2025-11-20
**Status:** ✅ Implemented & Ready for Testing

---

## Table of Contents
1. [Authentication](#authentication)
2. [Units & Access](#units--access)
3. [Meters & Readings](#meters--readings)
4. [Wallet & Transactions](#wallet--transactions)
5. [Error Responses](#error-responses)
6. [Testing Guide](#testing-guide)

---

## Authentication

### 1. Login
**Endpoint:** `POST /api/mobile/auth/login`
**Authentication:** None (public endpoint)
**Description:** Authenticate user with phone number and password

#### Request Body
```json
{
  "phone_number": "+27821234567",
  "password": "MyPass123"
}
```

**Note:** Phone number must be in E.164 format (+27xxxxxxxxx) or South African format (0xxxxxxxxx)

#### Response (200 OK)
```json
{
  "token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "user": {
    "id": 1,
    "person_id": 4,
    "phone_number": "+27821234567",
    "password_must_change": false,
    "last_login": "2024-01-15T10:30:00",
    "is_active": true,
    "created_at": "2024-01-01T00:00:00"
  },
  "person": {
    "id": 4,
    "first_name": "John",
    "last_name": "Doe",
    "full_name": "John Doe",
    "phone": "+27821234567",
    "email": "john@example.com"
  },
  "units": [
    {
      "unit_id": 10,
      "unit_number": "101",
      "estate_id": 1,
      "estate_name": "Sunset Estate",
      "role": "owner",
      "is_primary": true,
      "ownership_percentage": 100.0
    }
  ],
  "password_must_change": false
}
```

#### Error Responses
- **400 Bad Request:** Missing phone_number or password
- **401 Unauthorized:** Invalid phone number or password
- **403 Forbidden:** Account is inactive

---

### 2. Change Password
**Endpoint:** `POST /api/mobile/auth/change-password`
**Authentication:** Required
**Description:** Change user's password (clears temporary password flag)

#### Request Headers
```
Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGc...
```

#### Request Body
```json
{
  "current_password": "OldPass123",
  "new_password": "NewPass456"
}
```

**Note:** `current_password` is optional. New password must meet requirements:
- Minimum 8 characters
- At least 1 uppercase letter
- At least 1 lowercase letter
- At least 1 number

#### Response (200 OK)
```json
{
  "message": "Password changed successfully"
}
```

#### Error Responses
- **400 Bad Request:** Password doesn't meet requirements
- **401 Unauthorized:** Current password is incorrect or token invalid
- **403 Forbidden:** Account inactive

---

### 3. Get Current User
**Endpoint:** `GET /api/mobile/auth/user`
**Authentication:** Required
**Description:** Get current authenticated user's profile

#### Request Headers
```
Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGc...
```

#### Response (200 OK)
```json
{
  "user": {
    "id": 1,
    "person_id": 4,
    "phone_number": "+27821234567",
    "password_must_change": false,
    "last_login": "2024-01-15T10:30:00",
    "is_active": true
  },
  "person": {
    "id": 4,
    "first_name": "John",
    "last_name": "Doe",
    "full_name": "John Doe",
    "phone": "+27821234567",
    "email": "john@example.com"
  }
}
```

---

### 4. Get User's Units
**Endpoint:** `GET /api/mobile/auth/units`
**Authentication:** Required
**Description:** Get all units the user owns or rents

#### Request Headers
```
Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGc...
```

#### Response (200 OK)
```json
{
  "units": [
    {
      "unit_id": 10,
      "unit_number": "101",
      "estate_id": 1,
      "estate_name": "Sunset Estate",
      "role": "owner",
      "is_primary": true,
      "ownership_percentage": 100.0
    },
    {
      "unit_id": 15,
      "unit_number": "205",
      "estate_id": 2,
      "estate_name": "Riverside Apartments",
      "role": "tenant",
      "is_primary": false,
      "monthly_rent": 8500.0,
      "lease_start_date": "2024-01-01",
      "lease_end_date": "2024-12-31"
    }
  ]
}
```

**Note:**
- `role` can be "owner" or "tenant"
- Owner units include `ownership_percentage`
- Tenant units include `monthly_rent`, `lease_start_date`, `lease_end_date`

---

## Units & Access

All unit-related endpoints require authentication and verify that the user has access to the unit (as owner or active tenant).

---

## Meters & Readings

### 5. Get Unit Meters
**Endpoint:** `GET /api/mobile/units/{unit_id}/meters`
**Authentication:** Required
**Description:** Get all meters for a specific unit

#### Request Headers
```
Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGc...
```

#### Response (200 OK)
```json
{
  "meters": [
    {
      "id": 1,
      "serial_number": "MTR001",
      "meter_type": "prepaid",
      "utility_type": "electricity",
      "current_reading": 1250.5,
      "last_reading_date": "2024-01-15T10:30:00",
      "status": "active",
      "device_type": "Smart Meter",
      "communication_type": "LoRa"
    },
    {
      "id": 2,
      "serial_number": "MTR002",
      "meter_type": "prepaid",
      "utility_type": "water",
      "current_reading": 450.2,
      "last_reading_date": "2024-01-15T09:00:00",
      "status": "active",
      "device_type": "Ultrasonic",
      "communication_type": "NB-IoT"
    }
  ]
}
```

#### Error Responses
- **403 Forbidden:** User doesn't have access to this unit
- **404 Not Found:** Unit not found

---

### 6. Get Meter Details
**Endpoint:** `GET /api/mobile/meters/{meter_id}`
**Authentication:** Required
**Description:** Get detailed information about a specific meter

#### Request Headers
```
Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGc...
```

#### Response (200 OK)
```json
{
  "meter": {
    "id": 1,
    "serial_number": "MTR001",
    "meter_type": "prepaid",
    "utility_type": "electricity",
    "current_reading": 1250.5,
    "last_reading_date": "2024-01-15T10:30:00",
    "status": "active",
    "unit_id": 10,
    "unit_number": "101",
    "device_type": "Smart Meter",
    "communication_type": "LoRa"
  }
}
```

#### Error Responses
- **403 Forbidden:** User doesn't have access to this meter's unit
- **404 Not Found:** Meter not found

---

### 7. Get Meter Readings
**Endpoint:** `GET /api/mobile/meters/{meter_id}/readings`
**Authentication:** Required
**Description:** Get historical readings for a meter

#### Request Headers
```
Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGc...
```

#### Query Parameters
| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| days | integer | 30 | Number of days of history |
| limit | integer | 100 | Maximum number of readings |

#### Example Request
```
GET /api/mobile/meters/1/readings?days=7&limit=50
```

#### Response (200 OK)
```json
{
  "readings": [
    {
      "id": 150,
      "reading_value": 1250.5,
      "reading_date": "2024-01-15T10:30:00",
      "cost": 125.50,
      "consumption": 150.5
    },
    {
      "id": 149,
      "reading_value": 1100.0,
      "reading_date": "2024-01-14T10:30:00",
      "cost": 110.00,
      "consumption": 145.2
    }
  ],
  "meter": {
    "id": 1,
    "serial_number": "MTR001",
    "utility_type": "electricity"
  }
}
```

**Note:**
- Readings are ordered by date descending (newest first)
- `consumption` is the usage between readings
- `cost` is the cost for that consumption period

---

## Wallet & Transactions

### 8. Get Unit Wallet
**Endpoint:** `GET /api/mobile/units/{unit_id}/wallet`
**Authentication:** Required
**Description:** Get wallet balance and info for a unit

#### Request Headers
```
Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGc...
```

#### Response (200 OK)
```json
{
  "wallet": {
    "id": 1,
    "unit_id": 10,
    "balance": 2500.75,
    "status": "active",
    "last_transaction_date": "2024-01-15T10:30:00"
  }
}
```

#### Error Responses
- **403 Forbidden:** User doesn't have access to this unit
- **404 Not Found:** Unit or wallet not found

---

### 9. Get Wallet Transactions
**Endpoint:** `GET /api/mobile/units/{unit_id}/transactions`
**Authentication:** Required
**Description:** Get transaction history for a unit's wallet

#### Request Headers
```
Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGc...
```

#### Query Parameters
| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| days | integer | 30 | Number of days of history |
| limit | integer | 50 | Maximum number of transactions |
| type | string | - | Filter by type: "credit" or "debit" |

#### Example Request
```
GET /api/mobile/units/10/transactions?days=7&type=credit
```

#### Response (200 OK)
```json
{
  "transactions": [
    {
      "id": 45,
      "transaction_type": "credit",
      "amount": 500.00,
      "description": "Wallet top-up",
      "transaction_date": "2024-01-15T10:30:00",
      "balance_after": 2500.75
    },
    {
      "id": 44,
      "transaction_type": "debit",
      "amount": 125.50,
      "description": "Electricity usage",
      "transaction_date": "2024-01-14T23:59:00",
      "balance_after": 2000.75
    }
  ]
}
```

**Note:**
- Transactions are ordered by date descending (newest first)
- `transaction_type`: "credit" (money added) or "debit" (money deducted)
- `balance_after`: Wallet balance after this transaction

---

## Error Responses

All endpoints return consistent error responses:

### 400 Bad Request
```json
{
  "error": "Missing required fields",
  "message": "phone_number and password are required"
}
```

### 401 Unauthorized
```json
{
  "error": "Invalid or expired token",
  "message": "Please login again"
}
```

### 403 Forbidden
```json
{
  "error": "Access denied",
  "message": "You do not have access to this unit"
}
```

### 404 Not Found
```json
{
  "error": "Unit not found",
  "message": "Unit with ID 10 not found"
}
```

---

## Testing Guide

### Prerequisites
1. **User Account:** Must have a person assigned as owner or tenant to a unit
2. **Valid Phone:** Person must have valid phone number (E.164 format: +27xxxxxxxxx)
3. **Temporary Password:** Obtained when mobile user account is created

### Testing Flow

#### 1. Create Mobile User Account (Admin Portal)
When you add a person as owner or tenant via the web portal, a mobile user account is automatically created. The API response will include:

```json
{
  "message": "Owner added successfully",
  "mobile_user": {
    "mobile_user_created": true,
    "phone_number": "+27821234567",
    "temporary_password": "Abc12345",
    "message": "Mobile app account created. Please provide the temporary password to the owner."
  }
}
```

**Save the temporary_password** - this is needed for first login.

#### 2. Test Login (Mobile App)
```bash
POST /api/mobile/auth/login
Content-Type: application/json

{
  "phone_number": "+27821234567",
  "password": "Abc12345"
}
```

**Save the token** from the response - it's needed for all other endpoints.

#### 3. Test Password Change (First Login)
```bash
POST /api/mobile/auth/change-password
Authorization: Bearer YOUR_TOKEN_HERE
Content-Type: application/json

{
  "current_password": "Abc12345",
  "new_password": "MyNewPass123"
}
```

#### 4. Test Get Units
```bash
GET /api/mobile/auth/units
Authorization: Bearer YOUR_TOKEN_HERE
```

This returns all units the user can access. **Save a unit_id** for subsequent tests.

#### 5. Test Get Meters
```bash
GET /api/mobile/units/10/meters
Authorization: Bearer YOUR_TOKEN_HERE
```

Replace `10` with your unit_id. **Save a meter_id** for the next test.

#### 6. Test Get Meter Readings
```bash
GET /api/mobile/meters/1/readings?days=30&limit=50
Authorization: Bearer YOUR_TOKEN_HERE
```

Replace `1` with your meter_id.

#### 7. Test Get Wallet
```bash
GET /api/mobile/units/10/wallet
Authorization: Bearer YOUR_TOKEN_HERE
```

Replace `10` with your unit_id.

#### 8. Test Get Transactions
```bash
GET /api/mobile/units/10/transactions?days=30&limit=50
Authorization: Bearer YOUR_TOKEN_HERE
```

Replace `10` with your unit_id.

### Using cURL

Example cURL commands:

```bash
# 1. Login
curl -X POST http://localhost:5000/api/mobile/auth/login \
  -H "Content-Type: application/json" \
  -d '{"phone_number":"+27821234567","password":"Abc12345"}'

# 2. Get units (with token)
curl -X GET http://localhost:5000/api/mobile/auth/units \
  -H "Authorization: Bearer YOUR_TOKEN_HERE"

# 3. Get meters
curl -X GET http://localhost:5000/api/mobile/units/10/meters \
  -H "Authorization: Bearer YOUR_TOKEN_HERE"
```

### Using Postman

1. Create a new collection "Mobile API"
2. Set collection variable `base_url` = `http://localhost:5000/api/mobile`
3. Set collection variable `token` (update after login)
4. Add requests:
   - Login (POST {{base_url}}/auth/login)
   - Get Units (GET {{base_url}}/auth/units, Header: Authorization: Bearer {{token}})
   - Get Meters (GET {{base_url}}/units/10/meters)
   - etc.

---

## Notes

### JWT Token
- **Expiry:** 30 days from issuance
- **Storage:** Store securely in mobile app (e.g., secure storage/keychain)
- **Refresh:** Re-login when token expires

### Phone Number Format
- **Input:** Can accept `0821234567` or `+27821234567`
- **Storage:** Always normalized to E.164 format (`+27821234567`)
- **Display:** Show in user's preferred format

### Authorization
- All endpoints (except login) require valid JWT token
- User can only access units they own or rent (active tenancy)
- Trying to access unauthorized units returns 403 Forbidden

### Multiple Units
- If user has multiple units, they must select which unit to view
- Use the `/auth/units` endpoint to list all available units
- Then use specific unit_id in meter/wallet endpoints

---

## Implementation Status

✅ **Phase 3: User Account Creation** - COMPLETE
- Auto-create mobile users when assigned as owner/tenant
- Return temporary password in API response
- Temp password included in unit creation, owner add, tenant add responses

✅ **Phase 4: Mobile API Endpoints** - COMPLETE
- Authentication endpoints (login, change password, get user, get units)
- Meter endpoints (list meters, get details, get readings)
- Wallet endpoints (get balance, get transactions)
- JWT-based authentication with Bearer tokens
- Authorization checks for unit access

🔜 **Phase 2: SMS Integration** - PENDING
- SMS provider setup (Twilio, Clickatell, BulkSMS)
- Automatic SMS delivery of temporary passwords
- Welcome messages and notifications

---

## Future Enhancements

- **Push Notifications:** Alert users about low wallet balance, usage alerts
- **Payment Integration:** Top up wallet via mobile app
- **Usage Analytics:** Daily/weekly/monthly consumption charts
- **Budget Alerts:** Set budget limits and get notified
- **Meter Alerts:** Get notified about meter issues or anomalies

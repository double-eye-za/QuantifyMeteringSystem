# Quantify Metering Mobile App - API Documentation

**Version:** 1.0.0
**Base URL:** `https://api.quantifymetering.com` (replace with your actual domain)
**Date:** 2025-01-19

---

## Table of Contents

1. [Authentication](#authentication)
2. [User/Profile Management](#userprofile-management)
3. [Meters](#meters)
4. [Wallet & Payments](#wallet--payments)
5. [Credit Purchases](#credit-purchases)
6. [Notifications](#notifications)
7. [Transaction History](#transaction-history)
8. [Common Response Formats](#common-response-formats)
9. [Error Codes](#error-codes)

---

## Authentication

All authenticated endpoints require a Bearer token in the Authorization header:
```
Authorization: Bearer {token}
```

### 1.1 Login with Email/Password

**Endpoint:** `POST /api/auth/login`

**Description:** Authenticate user with email/password

**Request Body:**
```json
{
  "email": "john.smith@email.com",
  "password": "userPassword123"
}
```

**Response (200 OK):**
```json
{
  "success": true,
  "data": {
    "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "user": {
      "id": "usr_12345",
      "email": "john.smith@email.com",
      "name": "John Smith",
      "firstName": "John",
      "lastName": "Smith",
      "phone": "+27821234567",
      "unit": "A-101",
      "estate": "Willow Creek Estate",
      "avatarUrl": "https://cdn.example.com/avatars/user_12345.jpg",
      "role": "tenant"
    }
  }
}
```

**Error Response (401 Unauthorized):**
```json
{
  "success": false,
  "error": {
    "code": "INVALID_CREDENTIALS",
    "message": "Invalid email or password"
  }
}
```

---

### 1.2 Login with OTP

**Endpoint:** `POST /api/auth/login/otp`

**Description:** Request OTP to be sent via SMS

**Request Body:**
```json
{
  "phone": "+27821234567"
}
```

**Response (200 OK):**
```json
{
  "success": true,
  "data": {
    "message": "OTP sent successfully",
    "expiresIn": 300
  }
}
```

---

### 1.3 Verify OTP

**Endpoint:** `POST /api/auth/login/otp/verify`

**Description:** Verify OTP and login

**Request Body:**
```json
{
  "phone": "+27821234567",
  "otp": "123456"
}
```

**Response (200 OK):**
```json
{
  "success": true,
  "data": {
    "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "user": {
      "id": "usr_12345",
      "email": "john.smith@email.com",
      "name": "John Smith",
      "phone": "+27821234567",
      "unit": "A-101",
      "estate": "Willow Creek Estate"
    }
  }
}
```

---

### 1.4 Register New User

**Endpoint:** `POST /api/auth/register`

**Description:** Register a new user account

**Request Body:**
```json
{
  "email": "john.smith@email.com",
  "password": "userPassword123",
  "name": "John Smith",
  "phone": "+27821234567",
  "unit": "A-101",
  "estateId": "estate_001"
}
```

**Response (201 Created):**
```json
{
  "success": true,
  "data": {
    "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "user": {
      "id": "usr_12346",
      "email": "john.smith@email.com",
      "name": "John Smith",
      "phone": "+27821234567",
      "unit": "A-101",
      "estate": "Willow Creek Estate"
    }
  }
}
```

---

### 1.5 Password Reset Request

**Endpoint:** `POST /api/auth/password/reset`

**Description:** Request password reset email

**Request Body:**
```json
{
  "email": "john.smith@email.com"
}
```

**Response (200 OK):**
```json
{
  "success": true,
  "data": {
    "message": "Password reset email sent successfully"
  }
}
```

---

### 1.6 Get Current User

**Endpoint:** `GET /api/auth/user`

**Authentication:** Required

**Description:** Get authenticated user details

**Response (200 OK):**
```json
{
  "success": true,
  "data": {
    "id": "usr_12345",
    "email": "john.smith@email.com",
    "name": "John Smith",
    "firstName": "John",
    "lastName": "Smith",
    "phone": "+27821234567",
    "unit": "A-101",
    "estate": "Willow Creek Estate",
    "estateId": "estate_001",
    "avatarUrl": "https://cdn.example.com/avatars/user_12345.jpg",
    "role": "tenant",
    "createdAt": "2024-01-15T10:30:00Z"
  }
}
```

---

### 1.7 Logout

**Endpoint:** `POST /api/auth/logout`

**Authentication:** Required

**Description:** Invalidate current token

**Response (200 OK):**
```json
{
  "success": true,
  "data": {
    "message": "Logged out successfully"
  }
}
```

---

## User/Profile Management

### 2.1 Update User Profile

**Endpoint:** `PUT /api/user/profile`

**Authentication:** Required

**Request Body:**
```json
{
  "name": "John Smith",
  "firstName": "John",
  "lastName": "Smith",
  "phone": "+27821234567",
  "email": "john.smith@email.com"
}
```

**Response (200 OK):**
```json
{
  "success": true,
  "data": {
    "id": "usr_12345",
    "email": "john.smith@email.com",
    "name": "John Smith",
    "phone": "+27821234567",
    "unit": "A-101",
    "estate": "Willow Creek Estate"
  }
}
```

---

### 2.2 Update Password

**Endpoint:** `PUT /api/user/password`

**Authentication:** Required

**Request Body:**
```json
{
  "currentPassword": "oldPassword123",
  "newPassword": "newPassword456"
}
```

**Response (200 OK):**
```json
{
  "success": true,
  "data": {
    "message": "Password updated successfully"
  }
}
```

---

### 2.3 Update Notification Preferences

**Endpoint:** `PUT /api/user/preferences/notifications`

**Authentication:** Required

**Request Body:**
```json
{
  "pushNotifications": true,
  "smsAlerts": true,
  "emailNotifications": true,
  "lowBalanceWarnings": true,
  "paymentConfirmations": true,
  "serviceDisconnections": true,
  "usageAlerts": true
}
```

**Response (200 OK):**
```json
{
  "success": true,
  "data": {
    "pushNotifications": true,
    "smsAlerts": true,
    "emailNotifications": true,
    "lowBalanceWarnings": true,
    "paymentConfirmations": true,
    "serviceDisconnections": true,
    "usageAlerts": true
  }
}
```

---

### 2.4 Update Alert Thresholds

**Endpoint:** `PUT /api/user/preferences/alerts`

**Authentication:** Required

**Request Body:**
```json
{
  "electricityLowCreditAlert": 50.00,
  "waterLowCreditAlert": 30.00,
  "dailyUsageAlert": 20.0
}
```

**Response (200 OK):**
```json
{
  "success": true,
  "data": {
    "electricityLowCreditAlert": 50.00,
    "waterLowCreditAlert": 30.00,
    "dailyUsageAlert": 20.0
  }
}
```

---

## Meters

### 3.1 Get All User Meters

**Endpoint:** `GET /api/meters`

**Authentication:** Required

**Description:** Get all meters linked to the authenticated user

**Response (200 OK):**
```json
{
  "success": true,
  "data": [
    {
      "id": "meter_001",
      "type": "electricity",
      "serialNumber": "ELEC-12345678",
      "balance": 45.00,
      "status": "connected",
      "lastUpdate": "2025-01-19T14:30:00Z",
      "metadata": {
        "tariff": "Standard Residential",
        "rate": 2.85,
        "dailyUsage": 12.5,
        "monthlyUsage": 375.0,
        "estimatedDaysRemaining": 3
      }
    },
    {
      "id": "meter_002",
      "type": "water",
      "serialNumber": "WATR-87654321",
      "balance": 150.00,
      "status": "connected",
      "lastUpdate": "2025-01-19T14:35:00Z",
      "metadata": {
        "tariff": "Standard Water",
        "rate": 18.50,
        "dailyUsage": 0.8,
        "monthlyUsage": 24.0,
        "estimatedDaysRemaining": 10
      }
    },
    {
      "id": "meter_003",
      "type": "hot_water",
      "serialNumber": "HWTR-99887766",
      "balance": 75.00,
      "status": "connected",
      "lastUpdate": "2025-01-19T14:33:00Z",
      "metadata": {
        "tariff": "Hot Water",
        "rate": 25.00,
        "dailyUsage": 0.5,
        "monthlyUsage": 15.0,
        "estimatedDaysRemaining": 6
      }
    },
    {
      "id": "meter_004",
      "type": "solar",
      "serialNumber": "SOLR-11223344",
      "balance": 100.00,
      "status": "connected",
      "lastUpdate": "2025-01-19T14:31:00Z",
      "metadata": {
        "tariff": "Solar Generation",
        "rate": 1.20,
        "todayGeneration": 8.2,
        "monthlyGeneration": 246.0
      }
    }
  ]
}
```

---

### 3.2 Get Meter Details

**Endpoint:** `GET /api/meters/{meterId}`

**Authentication:** Required

**Response (200 OK):**
```json
{
  "success": true,
  "data": {
    "id": "meter_001",
    "type": "electricity",
    "serialNumber": "ELEC-12345678",
    "balance": 45.00,
    "status": "connected",
    "lastUpdate": "2025-01-19T14:30:00Z",
    "unit": "A-101",
    "estate": "Willow Creek Estate",
    "metadata": {
      "tariff": "Standard Residential",
      "rate": 2.85,
      "dailyUsage": 12.5,
      "monthlyUsage": 375.0,
      "estimatedDaysRemaining": 3,
      "installDate": "2024-06-01T00:00:00Z"
    }
  }
}
```

---

### 3.3 Get Meter Usage History

**Endpoint:** `GET /api/meters/{meterId}/usage`

**Authentication:** Required

**Query Parameters:**
- `startDate` (optional): ISO 8601 date (e.g., 2025-01-01)
- `endDate` (optional): ISO 8601 date (e.g., 2025-01-31)
- `interval` (optional): `hourly`, `daily`, `weekly`, `monthly` (default: daily)

**Example:** `GET /api/meters/meter_001/usage?startDate=2025-01-01&endDate=2025-01-31&interval=daily`

**Response (200 OK):**
```json
{
  "success": true,
  "data": {
    "meterId": "meter_001",
    "interval": "daily",
    "startDate": "2025-01-01T00:00:00Z",
    "endDate": "2025-01-31T00:00:00Z",
    "usage": [
      {
        "date": "2025-01-01",
        "consumption": 15.2,
        "cost": 43.32,
        "peak": 2.5,
        "offPeak": 12.7
      },
      {
        "date": "2025-01-02",
        "consumption": 12.8,
        "cost": 36.48,
        "peak": 2.1,
        "offPeak": 10.7
      }
    ],
    "summary": {
      "totalConsumption": 375.0,
      "totalCost": 1068.75,
      "averageDaily": 12.5,
      "peakConsumption": 15.2,
      "peakDate": "2025-01-01"
    }
  }
}
```

---

### 3.4 Link New Meter

**Endpoint:** `POST /api/meters/link`

**Authentication:** Required

**Request Body:**
```json
{
  "serialNumber": "ELEC-12345678",
  "verificationCode": "ABC123"
}
```

**Response (201 Created):**
```json
{
  "success": true,
  "data": {
    "id": "meter_005",
    "type": "electricity",
    "serialNumber": "ELEC-12345678",
    "balance": 0.00,
    "status": "connected",
    "linkedAt": "2025-01-19T15:00:00Z"
  }
}
```

---

## Wallet & Payments

### 4.1 Get Wallet Balance

**Endpoint:** `GET /api/wallet/balance`

**Authentication:** Required

**Response (200 OK):**
```json
{
  "success": true,
  "data": {
    "balance": 450.00,
    "currency": "ZAR",
    "lastUpdated": "2025-01-19T14:15:00Z"
  }
}
```

---

### 4.2 Get Wallet Summary

**Endpoint:** `GET /api/wallet/summary`

**Authentication:** Required

**Query Parameters:**
- `month` (optional): Month number (1-12, default: current month)
- `year` (optional): Year (default: current year)

**Response (200 OK):**
```json
{
  "success": true,
  "data": {
    "balance": 450.00,
    "monthlyIn": 1500.00,
    "monthlyOut": 1050.00,
    "month": 1,
    "year": 2025
  }
}
```

---

### 4.3 Add Funds to Wallet

**Endpoint:** `POST /api/wallet/topup`

**Authentication:** Required

**Request Body:**
```json
{
  "amount": 500.00,
  "paymentMethod": "card",
  "paymentDetails": {
    "cardToken": "tok_1234567890",
    "lastFourDigits": "1234"
  }
}
```

**Response (200 OK):**
```json
{
  "success": true,
  "data": {
    "transactionId": "txn_wallet_001",
    "amount": 500.00,
    "newBalance": 950.00,
    "timestamp": "2025-01-19T15:30:00Z"
  }
}
```

---

### 4.4 Get Wallet Transactions

**Endpoint:** `GET /api/wallet/transactions`

**Authentication:** Required

**Query Parameters:**
- `page` (optional): Page number (default: 1)
- `limit` (optional): Items per page (default: 20)
- `type` (optional): `topup` or `purchase`

**Response (200 OK):**
```json
{
  "success": true,
  "data": {
    "transactions": [
      {
        "id": "txn_001",
        "type": "topup",
        "amount": 500.00,
        "description": "Wallet Top-Up",
        "timestamp": "2025-01-19T10:15:00Z",
        "status": "completed",
        "paymentMethod": "card"
      },
      {
        "id": "txn_002",
        "type": "purchase",
        "amount": -100.00,
        "description": "Purchased Electricity",
        "timestamp": "2025-01-19T10:30:00Z",
        "status": "completed",
        "meterId": "meter_001"
      }
    ],
    "pagination": {
      "currentPage": 1,
      "totalPages": 5,
      "totalItems": 100,
      "itemsPerPage": 20
    }
  }
}
```

---

### 4.5 Get Payment Methods

**Endpoint:** `GET /api/wallet/payment-methods`

**Authentication:** Required

**Response (200 OK):**
```json
{
  "success": true,
  "data": [
    {
      "id": "pm_001",
      "type": "card",
      "details": {
        "brand": "Visa",
        "lastFourDigits": "1234",
        "expiryMonth": 12,
        "expiryYear": 2025
      },
      "isDefault": true
    },
    {
      "id": "pm_002",
      "type": "bank",
      "details": {
        "bankName": "FNB",
        "accountType": "Cheque",
        "lastFourDigits": "5678"
      },
      "isDefault": false
    }
  ]
}
```

---

## Credit Purchases

### 5.1 Create Purchase Transaction

**Endpoint:** `POST /api/purchases/create`

**Authentication:** Required

**Description:** Create a new purchase transaction (before PayFast redirect)

**Request Body:**
```json
{
  "meterId": "meter_001",
  "amount": 100.00,
  "paymentMethod": "payfast"
}
```

**Response (201 Created):**
```json
{
  "success": true,
  "data": {
    "purchaseId": "prc_12345",
    "paymentId": "PM1737294123456",
    "meterId": "meter_001",
    "amount": 100.00,
    "status": "pending",
    "createdAt": "2025-01-19T15:45:00Z",
    "payfastData": {
      "merchant_id": "10000100",
      "merchant_key": "46f0cd694581a",
      "return_url": "https://yoursite.com/api/payfast/return",
      "cancel_url": "https://yoursite.com/api/payfast/cancel",
      "notify_url": "https://yoursite.com/api/payfast/notify"
    }
  }
}
```

---

### 5.2 PayFast Payment Notification (ITN)

**Endpoint:** `POST /api/payfast/notify`

**Authentication:** None (PayFast server-to-server)

**Description:** PayFast Instant Transaction Notification (ITN) callback

**Request Body (from PayFast):**
```json
{
  "m_payment_id": "PM1737294123456",
  "pf_payment_id": "1234567",
  "payment_status": "COMPLETE",
  "item_name": "Electricity Credit",
  "item_description": "Purchase Electricity credit for your meter",
  "amount_gross": "100.00",
  "amount_fee": "2.30",
  "amount_net": "97.70",
  "merchant_id": "10000100",
  "signature": "generated_signature_hash"
}
```

**Your Backend Should:**
1. Validate the signature
2. Verify payment with PayFast
3. Update purchase status in database
4. Credit the meter
5. Send confirmation notification to user

**Response (200 OK):**
```json
{
  "success": true
}
```

---

### 5.3 Get Purchase Status

**Endpoint:** `GET /api/purchases/{purchaseId}/status`

**Authentication:** Required

**Response (200 OK):**
```json
{
  "success": true,
  "data": {
    "purchaseId": "prc_12345",
    "paymentId": "PM1737294123456",
    "status": "completed",
    "amount": 100.00,
    "meterId": "meter_001",
    "meterType": "electricity",
    "createdAt": "2025-01-19T15:45:00Z",
    "completedAt": "2025-01-19T15:46:30Z",
    "paymentDetails": {
      "method": "payfast",
      "pfPaymentId": "1234567",
      "amountGross": 100.00,
      "amountFee": 2.30,
      "amountNet": 97.70
    }
  }
}
```

**Status Values:**
- `pending`: Payment initiated
- `processing`: Payment being verified
- `completed`: Payment successful, credit applied
- `failed`: Payment failed
- `cancelled`: Payment cancelled by user

---

### 5.4 Get Purchase History

**Endpoint:** `GET /api/purchases`

**Authentication:** Required

**Query Parameters:**
- `page` (optional): Page number (default: 1)
- `limit` (optional): Items per page (default: 20)
- `meterId` (optional): Filter by meter
- `status` (optional): Filter by status

**Response (200 OK):**
```json
{
  "success": true,
  "data": {
    "purchases": [
      {
        "id": "prc_12345",
        "paymentId": "PM1737294123456",
        "meterId": "meter_001",
        "meterType": "electricity",
        "amount": 100.00,
        "status": "completed",
        "createdAt": "2025-01-19T15:45:00Z",
        "completedAt": "2025-01-19T15:46:30Z"
      },
      {
        "id": "prc_12344",
        "paymentId": "PM1737293123456",
        "meterId": "meter_002",
        "meterType": "water",
        "amount": 50.00,
        "status": "completed",
        "createdAt": "2025-01-18T10:30:00Z",
        "completedAt": "2025-01-18T10:31:15Z"
      }
    ],
    "pagination": {
      "currentPage": 1,
      "totalPages": 10,
      "totalItems": 200,
      "itemsPerPage": 20
    }
  }
}
```

---

## Notifications

### 6.1 Get All Notifications

**Endpoint:** `GET /api/notifications`

**Authentication:** Required

**Query Parameters:**
- `page` (optional): Page number (default: 1)
- `limit` (optional): Items per page (default: 20)
- `unreadOnly` (optional): boolean (default: false)

**Response (200 OK):**
```json
{
  "success": true,
  "data": {
    "notifications": [
      {
        "id": "notif_001",
        "type": "low_credit",
        "title": "Low Credit Warning",
        "message": "Your electricity balance is running low (R 45.00). Top up now to avoid disconnection.",
        "isRead": false,
        "timestamp": "2025-01-19T08:00:00Z",
        "metadata": {
          "meterId": "meter_001",
          "meterType": "electricity",
          "balance": 45.00
        }
      },
      {
        "id": "notif_002",
        "type": "purchase_success",
        "title": "Purchase Successful",
        "message": "You have successfully purchased R 100.00 of electricity credit.",
        "isRead": true,
        "timestamp": "2025-01-19T10:30:00Z",
        "metadata": {
          "purchaseId": "prc_12345",
          "amount": 100.00,
          "meterId": "meter_001"
        }
      },
      {
        "id": "notif_003",
        "type": "wallet_topup",
        "title": "Wallet Top-Up",
        "message": "Your wallet has been topped up with R 500.00",
        "isRead": true,
        "timestamp": "2025-01-19T10:15:00Z",
        "metadata": {
          "amount": 500.00,
          "transactionId": "txn_001"
        }
      }
    ],
    "pagination": {
      "currentPage": 1,
      "totalPages": 3,
      "totalItems": 50,
      "itemsPerPage": 20
    },
    "unreadCount": 5
  }
}
```

**Notification Types:**
- `low_credit`: Low balance warning
- `purchase_success`: Successful credit purchase
- `purchase_failed`: Failed credit purchase
- `wallet_topup`: Wallet top-up successful
- `meter_updated`: Meter reading updated
- `high_usage`: High usage alert
- `system_maintenance`: System maintenance notice
- `service_disconnection`: Service disconnected

---

### 6.2 Mark Notification as Read

**Endpoint:** `PUT /api/notifications/{notificationId}/read`

**Authentication:** Required

**Response (200 OK):**
```json
{
  "success": true,
  "data": {
    "id": "notif_001",
    "isRead": true
  }
}
```

---

### 6.3 Mark All Notifications as Read

**Endpoint:** `PUT /api/notifications/read-all`

**Authentication:** Required

**Response (200 OK):**
```json
{
  "success": true,
  "data": {
    "markedCount": 5
  }
}
```

---

### 6.4 Get Unread Count

**Endpoint:** `GET /api/notifications/unread-count`

**Authentication:** Required

**Response (200 OK):**
```json
{
  "success": true,
  "data": {
    "unreadCount": 5
  }
}
```

---

## Transaction History

### 7.1 Get Transaction History

**Endpoint:** `GET /api/transactions`

**Authentication:** Required

**Query Parameters:**
- `page` (optional): Page number (default: 1)
- `limit` (optional): Items per page (default: 20)
- `type` (optional): Filter by type (`topup`, `purchase`)
- `meterId` (optional): Filter by meter
- `startDate` (optional): ISO 8601 date
- `endDate` (optional): ISO 8601 date
- `minAmount` (optional): Minimum amount filter
- `maxAmount` (optional): Maximum amount filter

**Example:** `GET /api/transactions?type=purchase&startDate=2025-01-01&endDate=2025-01-31`

**Response (200 OK):**
```json
{
  "success": true,
  "data": {
    "transactions": [
      {
        "id": "txn_001",
        "type": "topup",
        "category": "wallet",
        "amount": 500.00,
        "description": "Wallet Top-Up",
        "timestamp": "2025-01-19T10:15:00Z",
        "status": "completed",
        "paymentMethod": "card",
        "metadata": {
          "cardLastFour": "1234"
        }
      },
      {
        "id": "txn_002",
        "type": "purchase",
        "category": "electricity",
        "amount": -100.00,
        "description": "Purchased Electricity",
        "timestamp": "2025-01-19T10:30:00Z",
        "status": "completed",
        "meterId": "meter_001",
        "metadata": {
          "serialNumber": "ELEC-12345678",
          "previousBalance": 45.00,
          "newBalance": 145.00
        }
      }
    ],
    "summary": {
      "totalTransactions": 150,
      "totalSpent": 1050.00,
      "averagePurchase": 87.50,
      "totalTopups": 1500.00
    },
    "pagination": {
      "currentPage": 1,
      "totalPages": 8,
      "totalItems": 150,
      "itemsPerPage": 20
    }
  }
}
```

---

### 7.2 Export Transaction History

**Endpoint:** `GET /api/transactions/export`

**Authentication:** Required

**Query Parameters:**
- `format`: `pdf` or `csv`
- `startDate` (optional): ISO 8601 date
- `endDate` (optional): ISO 8601 date
- `type` (optional): Filter by type

**Example:** `GET /api/transactions/export?format=pdf&startDate=2025-01-01&endDate=2025-01-31`

**Response (200 OK):**
```json
{
  "success": true,
  "data": {
    "downloadUrl": "https://cdn.example.com/exports/transactions_20250119.pdf",
    "expiresAt": "2025-01-19T16:00:00Z",
    "filename": "transactions_20250119.pdf"
  }
}
```

---

## Common Response Formats

### Success Response

```json
{
  "success": true,
  "data": { /* response data */ }
}
```

### Error Response

```json
{
  "success": false,
  "error": {
    "code": "ERROR_CODE",
    "message": "Human readable error message",
    "details": {} /* optional additional error details */
  }
}
```

### Paginated Response

```json
{
  "success": true,
  "data": {
    "items": [ /* array of items */ ],
    "pagination": {
      "currentPage": 1,
      "totalPages": 10,
      "totalItems": 200,
      "itemsPerPage": 20,
      "hasNextPage": true,
      "hasPreviousPage": false
    }
  }
}
```

---

## Error Codes

| Code | HTTP Status | Description |
|------|-------------|-------------|
| `INVALID_CREDENTIALS` | 401 | Invalid email or password |
| `UNAUTHORIZED` | 401 | Authentication token missing or invalid |
| `FORBIDDEN` | 403 | User doesn't have permission |
| `NOT_FOUND` | 404 | Resource not found |
| `VALIDATION_ERROR` | 422 | Request validation failed |
| `METER_NOT_FOUND` | 404 | Meter not found |
| `METER_ALREADY_LINKED` | 409 | Meter already linked to another user |
| `INSUFFICIENT_BALANCE` | 402 | Insufficient wallet balance |
| `PAYMENT_FAILED` | 402 | Payment processing failed |
| `INVALID_OTP` | 401 | Invalid or expired OTP |
| `RATE_LIMIT_EXCEEDED` | 429 | Too many requests |
| `SERVER_ERROR` | 500 | Internal server error |

---

## Additional Notes

### Authentication
- All authenticated endpoints require a valid JWT token
- Tokens should expire after 24 hours (configurable)
- Include refresh token mechanism for seamless re-authentication

### Security
- Use HTTPS for all API calls
- Validate PayFast signatures for ITN callbacks
- Implement rate limiting (e.g., 100 requests/minute per user)
- Hash passwords using bcrypt or similar
- Sanitize all user inputs

### PayFast Integration
1. User initiates payment in app
2. App calls `/api/purchases/create` to create transaction
3. Backend returns PayFast data including payment_id
4. App redirects to PayFast with payment data
5. PayFast processes payment
6. PayFast calls your `/api/payfast/notify` endpoint (ITN)
7. Your backend validates and processes the payment
8. Backend updates meter balance
9. Backend sends notification to user
10. User returns to app (via return_url or cancel_url)

### Testing
- Use PayFast sandbox credentials for development
- Implement proper logging for all API calls
- Return detailed error messages in development mode
- Use generic error messages in production

### Data Retention
- Store all transactions for compliance
- Archive old notifications after 90 days
- Keep audit logs for all financial transactions

---

**Last Updated:** 2025-01-19
**Version:** 1.0.0
**Maintained By:** Quantify Metering Development Team

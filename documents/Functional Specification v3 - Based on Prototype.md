# Functional Specification v3.0
## Quantify Metering System - Based on Prototype Implementation

---

**Document Information**
- **Document Title**: Functional Specification - Quantify Metering System
- **Version**: 3.0
- **Date**: October 2025
- **Status**: Updated based on prototype implementation
- **Based on**: Prototype development and Business Requirements v1.0

---

## Executive Summary

The Quantify Metering System is a comprehensive prepaid utility management platform for residential estates. This specification has been updated based on the implemented prototype, which demonstrates the core functionality for Phase 1 (Admin System) with enhanced features for prepaid wallet management, rate table configuration, and comprehensive billing.

---

## System Architecture Overview

### Core Components

1. **Web Administration Portal** (Implemented in Prototype)
   - Estate and unit management
   - Meter monitoring and configuration
   - Prepaid wallet and billing management
   - Rate table builder and configuration
   - Comprehensive reporting and analytics
   - User and role management

2. **Mobile Application** (Phase 2 - To be implemented)
   - Resident portal for balance management
   - Wallet top-up and credit purchases
   - Usage monitoring and statements

3. **Backend Services** (To be implemented per development_guidelines.md)
   - Python 3.9+ with Flask 3.0+
   - PostgreSQL database
   - SQLAlchemy 2.0+ ORM
   - Basic Authentication with role-based access
   - RESTful API (v1)

---

## Phase 1 - Admin System (Implemented in Prototype)

### 1. Authentication & Security

#### Login System
- Secure login page with username/password authentication
- Session management with timeout controls
- Password reset functionality
- Demo credentials display for prototype testing

#### User Roles (Implemented)
- **Super Admin**: Full system access, all estates
- **Property Manager**: Estate-specific access
- **Billing Admin**: Financial operations only
- **Viewer**: Read-only access

### 2. Dashboard & Analytics

#### Main Dashboard (index.html)
- **Estate Overview Cards**
  - Total units and active meters
  - Total wallet balances
  - Monthly revenue tracking
  - Alert notifications count

- **Interactive Charts**
  - Daily consumption patterns (electricity/water)
  - Revenue trends (30-day view)
  - Estate comparison metrics
  - Expandable chart views with proper container management

- **Quick Actions**
  - View low balance units
  - Recent transactions
  - System alerts
  - Quick navigation to key features

### 3. Estate Management

#### Estate Administration (estates.html)
- Create and manage residential estates
- Estate details:
  - Name and location
  - Contact information
  - Number of units
  - Bulk meter assignments
  - Rate table assignments with markup percentages

#### Bulk Meter Integration
- Link bulk electricity meter per estate
- Link bulk water meter per estate
- Monitor total estate consumption
- Reconciliation reports between bulk and unit meters

### 4. Unit Management

#### Unit Records (units.html)
- Comprehensive unit listing with search and filters
- Unit information:
  - Unit identifier and floor location
  - Resident assignment
  - Meter status (3 meters per unit)
  - Current wallet balance
  - Occupancy status

#### Unit Details View (unit-details.html)
- **Meter Information**
  - Electricity meter (E460 Smart Prepayment)
  - Water meter (Smart meter)
  - Solar meter (E460 for solar monitoring)
  - Real-time credit balance per meter
  - Connection status

- **Wallet Information**
  - Combined wallet balance
  - Recent transactions
  - Quick top-up actions
  - View detailed statement link

- **Unit Visual Diagram** (unit-visual.html)
  - Graphical representation of meter connections
  - Solar panel integration visualization
  - Eskom grid connection
  - Water supply connection
  - Real-time status indicators

### 5. Meter Management

#### Meter Registry (meters.html)
- Complete meter inventory
- Meter details:
  - Serial number and type
  - Installation date
  - Current reading
  - Communication status
  - Last reading timestamp
  - Tariff assignment

#### Meter Details (meter-details.html)
- Real-time meter readings
- Communication history
- Tamper detection alerts
- Configuration settings
- Historical consumption data
- Meter-specific alerts and notifications

### 6. Prepaid Wallet & Billing System

#### Billing Dashboard (billing.html)
- **Overview Metrics**
  - Total wallet balances across all units
  - Low balance count
  - Today's collections
  - Pending top-ups

- **Unit Wallet Management**
  - Quick search and filter
  - Batch top-up capabilities
  - Individual wallet adjustments
  - Transaction history access

#### Wallet Statement (wallet-statement.html)
- **Detailed Transaction History**
  - Credit purchases (electricity/water/solar)
  - Automatic deductions
  - Top-up transactions
  - Service charges

- **Consumption Breakdown**
  - Daily usage patterns
  - Cost per utility type
  - Free solar allocation tracking (50 kWh/month)
  - Tiered rate calculations

- **Balance Projections**
  - Estimated days remaining
  - Average daily consumption
  - Low balance warnings

### 7. Rate Management System

#### Rate Table Builder (rate-table-builder.html)
- **Multiple Pricing Models Support**
  1. **Tiered Block Rates**
     - Consumption-based pricing tiers
     - Different rates per consumption block
     - Example: 0-50 kWh @ R1.50, 51-200 kWh @ R2.00

  2. **Time-of-Use (TOU) Rates**
     - Peak/Standard/Off-peak pricing
     - Configurable time periods
     - Different rates for different times

  3. **Seasonal Rates**
     - Summer/Winter pricing variations
     - Date range configuration
     - Automatic seasonal switching

  4. **Flat Rates**
     - Single rate regardless of consumption
     - Simple pricing model

  5. **Fixed Charges**
     - Monthly service charges
     - Connection fees
     - Administrative charges

  6. **Demand Charges**
     - Peak demand monitoring
     - Maximum demand charges

#### Rate Table Management (rate-tables-simplified.html)
- **Estate Assignment**
  - Direct rate table to estate linking
  - Markup percentage configuration (e.g., 20% on electricity)
  - Effective date management
  - Rate table versioning

- **Rate Validation**
  - Preview calculations
  - Test scenarios
  - Impact analysis before activation

### 8. Reporting System

#### Available Reports (reports.html)

1. **Estate Consumption Report**
   - Bulk meter vs unit meters reconciliation
   - Variance analysis
   - Loss detection
   - Monthly/daily breakdowns

2. **Low Credit Report**
   - Units below threshold
   - Predicted disconnection dates
   - Contact information for notifications
   - Bulk notification capabilities

3. **Revenue Report**
   - Daily/monthly collections
   - Payment methods breakdown
   - Outstanding balances
   - Revenue trends

4. **Disconnection Report**
   - Currently disconnected units
   - Disconnection history
   - Reconnection requirements
   - Revenue impact

5. **Transaction Report**
   - All financial transactions
   - Filtering by date/type/unit
   - Export capabilities
   - Audit trail

6. **Consumption Analytics**
   - Usage patterns by estate/unit
   - Peak usage identification
   - Comparative analysis
   - Anomaly detection

### 9. System Administration

#### User Management (users.html)
- User account creation and editing
- Role assignment
- Password management
- Bulk user import (CSV/Excel)
- Activity tracking

#### Role Management (roles.html)
- Predefined role templates
- Custom role creation
- Permission matrix configuration
- Role assignment to users

#### System Settings (settings.html)
- Global configuration parameters
- **Wallet & Meter Settings**:
  - Default low balance thresholds
  - Alert type configuration (fixed/days/smart)
  - Meter activation minimums
  - Alert frequency settings
  - Per-estate overrides
- Notification thresholds
- Default rate tables
- System preferences
- Integration settings

#### Audit Log (audit-log.html)
- Complete activity tracking
- User action history
- System event logging
- Security audit trail
- Export capabilities

#### Notifications Center (notifications.html)
- System-wide announcements
- Alert management
- Notification templates
- Delivery channel configuration
- Notification history

---

## Prepaid System Rules (Implemented Logic)

### Electricity
- **Prepaid Model**: Pay before use
- **Minimum Activation Amount**: R20.00 (configurable) - meter only activates when minimum is met
- **Auto-disconnection**: Service stops at R0.00 balance
- **Auto-reconnection**: Service resumes upon credit purchase IF minimum activation amount is met
- **Solar Allocation**: 50 kWh free per month
- **Markup**: Configurable percentage (default 20%)

### Water
- **Prepaid Model**: Pay before use
- **Minimum Tracking Amount**: R20.00 (configurable) - minimum to begin tracking usage
- **No Physical Disconnection**: Meters cannot restrict flow
- **Debt Accumulation**: Negative balance allowed
- **Notification**: Alerts when balance goes negative
- **Recovery**: Debt cleared with next top-up

### Wallet System
- **Single Wallet**: One wallet per unit for all utilities
- **Automatic Deduction**: Real-time deduction based on consumption
- **Transaction History**: Complete audit trail

### Low Balance Alert Configuration
- **Alert Types**:
  1. **Fixed Amount**: Alert when balance drops below set amount (default R50)
  2. **Days Remaining**: Alert when estimated days of usage remaining falls below threshold (default 3 days)
  3. **Smart Alert**: Automatically adjust based on consumption patterns
- **Alert Frequency**: Configurable repeat interval (default 24 hours)
- **Consumption Analysis**: 
  - Automatic daily average calculation
  - 7-day rolling average for predictions
  - Trend detection (increasing/decreasing/stable)
- **Estate Overrides**: Each estate can have custom alert thresholds

### Meter Activation Rules
- **Electricity Meter**:
  - Requires minimum R20.00 in wallet to activate
  - Automatically disconnects at R0.00
  - Will not reconnect until minimum amount is added
- **Water Meter**:
  - Requires minimum R20.00 to begin tracking
  - Continues to flow even with negative balance
  - Accumulates debt until topped up
- **Solar Meter**:
  - No minimum required for free allocation (50 kWh/month)
  - Standard minimums apply for additional usage

---

## Phase 2 - Mobile App & Payment Gateway (Specification)

### Mobile Application Features

#### 1. Dashboard
- Current balances (electricity/water/solar)
- Quick top-up buttons
- Recent usage graph
- Alert notifications

#### 2. Wallet Management
- Balance overview
- Top-up via EFT/Card
- Transaction history
- Auto top-up settings

#### 3. Usage Monitoring
- Real-time consumption
- Daily/weekly/monthly views
- Cost breakdown
- Usage predictions

#### 4. Statements
- Downloadable PDF statements
- Detailed transaction history
- Consumption analytics
- Payment receipts

### Payment Gateway Integration

#### Supported Methods
- EFT (Electronic Funds Transfer)
- Credit/Debit Cards
- Instant EFT
- Scheduled payments

#### Security Requirements
- PCI DSS compliance
- SSL/TLS encryption
- Tokenization
- 3D Secure authentication

---

## Phase 3 - Pilot Testing & Optimization

### Testing Scope
- User acceptance testing
- Performance testing
- Security testing
- Integration testing

### Success Metrics
- 99.5% uptime
- <3 second response times
- Zero security incidents
- >90% user satisfaction

---

## Technical Implementation Notes

### Based on development_guidelines.md

#### Backend Architecture
```
quantify-metering/
├─ src/
│  ├─ app/
│  │  ├─ api/v1/
│  │  │  ├─ auth/
│  │  │  ├─ estates/
│  │  │  ├─ units/
│  │  │  ├─ meters/
│  │  │  ├─ billing/
│  │  │  ├─ rates/
│  │  │  └─ reports/
│  │  ├─ core/
│  │  │  ├─ config.py
│  │  │  ├─ database.py
│  │  │  └─ security.py
│  │  ├─ models/
│  │  │  ├─ estate.py
│  │  │  ├─ unit.py
│  │  │  ├─ meter.py
│  │  │  ├─ wallet.py
│  │  │  ├─ transaction.py
│  │  │  └─ rate_table.py
│  │  └─ services/
│  │     ├─ meter_service.py
│  │     ├─ billing_service.py
│  │     └─ notification_service.py
│  └─ wsgi.py
├─ tests/
├─ requirements.txt
└─ .env.example
```

#### API Versioning
- Base URL: `/api/v1/`
- RESTful design
- JSON responses
- Pagination support
- Search capabilities

#### Authentication
- Basic Auth for all API access
- Role-based access control
- Session management

---

## Performance Requirements

### System Performance
- 99.5% uptime
- <60 second meter data updates
- <3 second page load times
- Support 450+ concurrent meters
- Handle 1000+ transactions/day

### Scalability
- Horizontal scaling capability
- Database connection pooling
- Caching layer (Redis)
- CDN for static assets
- Load balancer ready

---

## Security & Compliance

### POPIA Compliance
- Minimal data collection
- Encryption at rest and in transit
- Data retention policies
- User consent management
- Breach notification procedures

### Security Measures
- HTTPS enforcement
- SQL injection prevention
- XSS protection
- CSRF tokens
- Rate limiting
- Audit logging

---

## Conclusion

This functional specification reflects the actual implementation in the prototype, with detailed descriptions of all features and workflows. The system is designed to be scalable, secure, and user-friendly, providing comprehensive prepaid utility management for residential estates.

The prototype successfully demonstrates Phase 1 functionality, laying a solid foundation for Phase 2 (Mobile App) and Phase 3 (Pilot Testing) implementations.

---

**Document Version History**
- v1.0 - Initial specification
- v2.0 - Updated with phased approach
- v3.0 - Updated based on prototype implementation

---

*End of Functional Specification v3.0*
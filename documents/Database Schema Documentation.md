# Database Schema Documentation
## Quantify Metering System

---

**Document Information**
- **Version**: 1.0
- **Date**: October 2025
- **Database**: PostgreSQL
- **ORM**: SQLAlchemy 2.0+
- **Based on**: development_guidelines.md and Functional Specification v3.0

---

## Database Overview

The Quantify Metering System uses PostgreSQL as its primary database, with SQLAlchemy 2.0+ as the ORM layer. The schema is designed to support multi-tenant operations, prepaid billing, and real-time meter data management.

### Design Principles
- Normalized design (3NF) with strategic denormalization for performance
- UUID primary keys for distributed systems compatibility
- Audit columns on all tables (created_at, updated_at, created_by, updated_by)
- Soft deletes where appropriate (deleted_at)
- Indexed columns for query optimization
- Check constraints for data integrity

---

## Core Tables

### 1. users
Stores system user accounts for administrators and property managers.

```sql
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    username VARCHAR(64) UNIQUE NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    first_name VARCHAR(100) NOT NULL,
    last_name VARCHAR(100) NOT NULL,
    phone VARCHAR(20),
    role_id UUID REFERENCES roles(id),
    is_active BOOLEAN DEFAULT true,
    last_login TIMESTAMP,
    failed_login_attempts INTEGER DEFAULT 0,
    locked_until TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by UUID REFERENCES users(id),
    updated_by UUID REFERENCES users(id)
);

CREATE INDEX idx_users_username ON users(username);
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_role_id ON users(role_id);
```

### 2. roles
Defines user roles and permission levels.

```sql
CREATE TABLE roles (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(50) UNIQUE NOT NULL,
    description TEXT,
    permissions JSONB NOT NULL DEFAULT '{}',
    is_system_role BOOLEAN DEFAULT false,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Predefined roles
INSERT INTO roles (name, description, is_system_role) VALUES
('super_admin', 'Full system access', true),
('property_manager', 'Estate management access', true),
('billing_admin', 'Billing and financial access', true),
('viewer', 'Read-only access', true);
```

### 3. estates
Manages residential estate information.

```sql
CREATE TABLE estates (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    code VARCHAR(20) UNIQUE NOT NULL,
    name VARCHAR(255) NOT NULL,
    address TEXT,
    city VARCHAR(100),
    postal_code VARCHAR(10),
    contact_name VARCHAR(200),
    contact_phone VARCHAR(20),
    contact_email VARCHAR(255),
    total_units INTEGER NOT NULL DEFAULT 0,
    bulk_electricity_meter_id UUID REFERENCES meters(id),
    bulk_water_meter_id UUID REFERENCES meters(id),
    electricity_rate_table_id UUID REFERENCES rate_tables(id),
    water_rate_table_id UUID REFERENCES rate_tables(id),
    electricity_markup_percentage DECIMAL(5,2) DEFAULT 0.00,
    water_markup_percentage DECIMAL(5,2) DEFAULT 0.00,
    solar_free_allocation_kwh DECIMAL(10,2) DEFAULT 50.00,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by UUID REFERENCES users(id),
    updated_by UUID REFERENCES users(id)
);

CREATE INDEX idx_estates_code ON estates(code);
CREATE INDEX idx_estates_is_active ON estates(is_active);
```

### 4. units
Stores individual unit/apartment information.

```sql
CREATE TABLE units (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    estate_id UUID REFERENCES estates(id) NOT NULL,
    unit_number VARCHAR(50) NOT NULL,
    floor VARCHAR(20),
    building VARCHAR(50),
    bedrooms INTEGER,
    bathrooms INTEGER,
    size_sqm DECIMAL(10,2),
    occupancy_status VARCHAR(20) DEFAULT 'vacant' CHECK (occupancy_status IN ('occupied', 'vacant', 'maintenance')),
    resident_id UUID REFERENCES residents(id),
    wallet_id UUID REFERENCES wallets(id),
    electricity_meter_id UUID REFERENCES meters(id),
    water_meter_id UUID REFERENCES meters(id),
    solar_meter_id UUID REFERENCES meters(id),
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by UUID REFERENCES users(id),
    updated_by UUID REFERENCES users(id),
    UNIQUE(estate_id, unit_number)
);

CREATE INDEX idx_units_estate_id ON units(estate_id);
CREATE INDEX idx_units_resident_id ON units(resident_id);
CREATE INDEX idx_units_wallet_id ON units(wallet_id);
CREATE INDEX idx_units_occupancy_status ON units(occupancy_status);
```

### 5. residents
Stores resident/tenant information.

```sql
CREATE TABLE residents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    id_number VARCHAR(20) UNIQUE,
    first_name VARCHAR(100) NOT NULL,
    last_name VARCHAR(100) NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    phone VARCHAR(20) NOT NULL,
    alternate_phone VARCHAR(20),
    emergency_contact_name VARCHAR(200),
    emergency_contact_phone VARCHAR(20),
    lease_start_date DATE,
    lease_end_date DATE,
    is_active BOOLEAN DEFAULT true,
    app_user_id UUID,  -- For mobile app login (Phase 2)
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by UUID REFERENCES users(id),
    updated_by UUID REFERENCES users(id)
);

CREATE INDEX idx_residents_email ON residents(email);
CREATE INDEX idx_residents_id_number ON residents(id_number);
CREATE INDEX idx_residents_is_active ON residents(is_active);
```

### 6. meters
Central meter registry for all meter types.

```sql
CREATE TABLE meters (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    serial_number VARCHAR(100) UNIQUE NOT NULL,
    meter_type VARCHAR(20) NOT NULL CHECK (meter_type IN ('electricity', 'water', 'solar', 'bulk_electricity', 'bulk_water')),
    manufacturer VARCHAR(100),
    model VARCHAR(100),
    installation_date DATE,
    last_reading DECIMAL(15,3),
    last_reading_date TIMESTAMP,
    communication_type VARCHAR(20) DEFAULT 'plc' CHECK (communication_type IN ('plc', 'cellular', 'wifi', 'manual')),
    communication_status VARCHAR(20) DEFAULT 'online' CHECK (communication_status IN ('online', 'offline', 'error')),
    last_communication TIMESTAMP,
    firmware_version VARCHAR(50),
    is_prepaid BOOLEAN DEFAULT true,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_meters_serial_number ON meters(serial_number);
CREATE INDEX idx_meters_meter_type ON meters(meter_type);
CREATE INDEX idx_meters_communication_status ON meters(communication_status);
```

### 7. meter_readings
Stores all meter readings for historical tracking.

```sql
CREATE TABLE meter_readings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    meter_id UUID REFERENCES meters(id) NOT NULL,
    reading_value DECIMAL(15,3) NOT NULL,
    reading_date TIMESTAMP NOT NULL,
    reading_type VARCHAR(20) DEFAULT 'automatic' CHECK (reading_type IN ('automatic', 'manual', 'estimated')),
    consumption_since_last DECIMAL(15,3),
    is_validated BOOLEAN DEFAULT false,
    validation_date TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_meter_readings_meter_id ON meter_readings(meter_id);
CREATE INDEX idx_meter_readings_reading_date ON meter_readings(reading_date DESC);
CREATE INDEX idx_meter_readings_meter_date ON meter_readings(meter_id, reading_date DESC);
```

### 8. wallets
Manages prepaid wallet balances for units.

```sql
CREATE TABLE wallets (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    unit_id UUID REFERENCES units(id) UNIQUE NOT NULL,
    balance DECIMAL(12,2) NOT NULL DEFAULT 0.00,
    electricity_balance DECIMAL(12,2) NOT NULL DEFAULT 0.00,
    water_balance DECIMAL(12,2) NOT NULL DEFAULT 0.00,
    solar_balance DECIMAL(12,2) NOT NULL DEFAULT 0.00,
    -- Alert Configuration
    low_balance_threshold DECIMAL(10,2) DEFAULT 50.00,
    low_balance_alert_type VARCHAR(20) DEFAULT 'fixed' CHECK (low_balance_alert_type IN ('fixed', 'days_remaining')),
    low_balance_days_threshold INTEGER DEFAULT 3, -- Alert when X days of usage remaining
    last_low_balance_alert TIMESTAMP,
    alert_frequency_hours INTEGER DEFAULT 24, -- How often to send alerts
    -- Meter Activation Minimums
    electricity_minimum_activation DECIMAL(10,2) DEFAULT 20.00, -- Min amount to activate electricity
    water_minimum_activation DECIMAL(10,2) DEFAULT 20.00, -- Min amount to activate water
    -- Auto Top-up Configuration
    auto_topup_enabled BOOLEAN DEFAULT false,
    auto_topup_amount DECIMAL(10,2),
    auto_topup_threshold DECIMAL(10,2),
    -- Usage Tracking for Smart Alerts
    daily_avg_consumption DECIMAL(10,2), -- Average daily consumption in Rands
    last_consumption_calc_date TIMESTAMP, -- When average was last calculated
    -- Account Status
    is_suspended BOOLEAN DEFAULT false,
    suspension_reason TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CHECK (balance >= 0), -- Allow negative for water debt
    CHECK (electricity_minimum_activation >= 0),
    CHECK (water_minimum_activation >= 0)
);

CREATE INDEX idx_wallets_unit_id ON wallets(unit_id);
CREATE INDEX idx_wallets_balance ON wallets(balance);
CREATE INDEX idx_wallets_is_suspended ON wallets(is_suspended);
```

### 9. transactions
Records all financial transactions with payment gateway integration support.

```sql
CREATE TABLE transactions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    transaction_number VARCHAR(50) UNIQUE NOT NULL,
    wallet_id UUID REFERENCES wallets(id) NOT NULL,
    transaction_type VARCHAR(30) NOT NULL CHECK (transaction_type IN (
        'topup', 'purchase_electricity', 'purchase_water', 'purchase_solar',
        'consumption_electricity', 'consumption_water', 'consumption_solar',
        'refund', 'adjustment', 'service_charge'
    )),
    amount DECIMAL(12,2) NOT NULL,
    balance_before DECIMAL(12,2) NOT NULL,
    balance_after DECIMAL(12,2) NOT NULL,
    reference VARCHAR(255),
    description TEXT,
    -- Payment Gateway Fields
    payment_method VARCHAR(20) CHECK (payment_method IN ('eft', 'card', 'instant_eft', 'cash', 'system', 'adjustment')),
    payment_gateway VARCHAR(50), -- 'paygate', 'payfast', 'ozow', etc.
    payment_gateway_ref VARCHAR(255), -- External transaction reference
    payment_gateway_status VARCHAR(50), -- Raw status from gateway
    payment_metadata JSONB, -- Additional payment info (card last4, bank, etc.)
    -- Status and Timing
    status VARCHAR(20) DEFAULT 'pending' CHECK (status IN ('pending', 'processing', 'completed', 'failed', 'reversed', 'expired')),
    initiated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP,
    expires_at TIMESTAMP,
    -- Reconciliation
    reconciled BOOLEAN DEFAULT false,
    reconciled_at TIMESTAMP,
    -- Other Fields
    meter_id UUID REFERENCES meters(id),
    consumption_kwh DECIMAL(10,3),
    rate_applied DECIMAL(10,4),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by UUID REFERENCES users(id)
);

CREATE INDEX idx_transactions_wallet_id ON transactions(wallet_id);
CREATE INDEX idx_transactions_transaction_type ON transactions(transaction_type);
CREATE INDEX idx_transactions_created_at ON transactions(created_at DESC);
CREATE INDEX idx_transactions_transaction_number ON transactions(transaction_number);
CREATE INDEX idx_transactions_status ON transactions(status);
CREATE INDEX idx_transactions_payment_gateway_ref ON transactions(payment_gateway_ref);
CREATE INDEX idx_transactions_pending ON transactions(status) WHERE status = 'pending';
```

### 10. payment_methods
Stores saved payment methods for quick payments (PCI compliant - no full card numbers).

```sql
CREATE TABLE payment_methods (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    wallet_id UUID REFERENCES wallets(id) NOT NULL,
    method_type VARCHAR(20) NOT NULL CHECK (method_type IN ('card', 'bank_account')),
    -- Card Details (tokenized)
    card_token VARCHAR(255), -- Token from payment gateway
    card_last4 VARCHAR(4),
    card_brand VARCHAR(20), -- 'visa', 'mastercard', 'amex'
    card_exp_month INTEGER CHECK (card_exp_month BETWEEN 1 AND 12),
    card_exp_year INTEGER CHECK (card_exp_year >= EXTRACT(YEAR FROM CURRENT_DATE)),
    -- Bank Account Details (for EFT)
    bank_name VARCHAR(100),
    account_last4 VARCHAR(4),
    account_type VARCHAR(20), -- 'savings', 'current'
    -- Common Fields
    is_default BOOLEAN DEFAULT false,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_used_at TIMESTAMP,
    UNIQUE(wallet_id, card_token),
    CHECK (
        (method_type = 'card' AND card_token IS NOT NULL) OR
        (method_type = 'bank_account' AND bank_name IS NOT NULL)
    )
);

CREATE INDEX idx_payment_methods_wallet_id ON payment_methods(wallet_id);
CREATE INDEX idx_payment_methods_is_default ON payment_methods(is_default);
```

### 11. rate_tables
Defines utility rate structures.

```sql
CREATE TABLE rate_tables (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    utility_type VARCHAR(20) NOT NULL CHECK (utility_type IN ('electricity', 'water', 'solar')),
    rate_structure JSONB NOT NULL,
    is_default BOOLEAN DEFAULT false,
    effective_from DATE NOT NULL,
    effective_to DATE,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by UUID REFERENCES users(id),
    updated_by UUID REFERENCES users(id)
);

CREATE INDEX idx_rate_tables_utility_type ON rate_tables(utility_type);
CREATE INDEX idx_rate_tables_is_active ON rate_tables(is_active);
CREATE INDEX idx_rate_tables_effective_from ON rate_tables(effective_from);
```

### 12. rate_table_tiers
Stores tiered pricing for consumption-based rates.

```sql
CREATE TABLE rate_table_tiers (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    rate_table_id UUID REFERENCES rate_tables(id) NOT NULL,
    tier_number INTEGER NOT NULL,
    from_kwh DECIMAL(10,2) NOT NULL,
    to_kwh DECIMAL(10,2),
    rate_per_kwh DECIMAL(10,4) NOT NULL,
    description VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(rate_table_id, tier_number)
);

CREATE INDEX idx_rate_table_tiers_rate_table_id ON rate_table_tiers(rate_table_id);
```

### 13. time_of_use_rates
Stores time-based pricing for TOU rate tables.

```sql
CREATE TABLE time_of_use_rates (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    rate_table_id UUID REFERENCES rate_tables(id) NOT NULL,
    period_name VARCHAR(50) NOT NULL,
    start_time TIME NOT NULL,
    end_time TIME NOT NULL,
    weekdays BOOLEAN DEFAULT true,
    weekends BOOLEAN DEFAULT false,
    rate_per_kwh DECIMAL(10,4) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_time_of_use_rates_rate_table_id ON time_of_use_rates(rate_table_id);
```

### 14. notifications
Manages system notifications and alerts. Supports push notifications for mobile app (Phase 2).

```sql
CREATE TABLE notifications (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    recipient_type VARCHAR(20) NOT NULL CHECK (recipient_type IN ('user', 'resident', 'system')),
    recipient_id UUID,
    notification_type VARCHAR(50) NOT NULL,
    subject VARCHAR(255),
    message TEXT NOT NULL,
    priority VARCHAR(20) DEFAULT 'normal' CHECK (priority IN ('low', 'normal', 'high', 'critical')),
    channel VARCHAR(20) NOT NULL CHECK (channel IN ('email', 'sms', 'push', 'in_app')),
    status VARCHAR(20) DEFAULT 'pending' CHECK (status IN ('pending', 'sent', 'delivered', 'failed', 'read')),
    sent_at TIMESTAMP,
    read_at TIMESTAMP,
    error_message TEXT,
    -- Phase 2: Push notification fields
    push_token TEXT,  -- Device push token for mobile app
    push_provider VARCHAR(20), -- 'fcm' (Firebase), 'apns' (Apple)
    push_payload JSONB, -- Push notification payload
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_notifications_recipient ON notifications(recipient_type, recipient_id);
CREATE INDEX idx_notifications_status ON notifications(status);
CREATE INDEX idx_notifications_created_at ON notifications(created_at DESC);
```

### 15. audit_logs
Comprehensive audit trail for all system activities.

```sql
CREATE TABLE audit_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id),
    action VARCHAR(100) NOT NULL,
    entity_type VARCHAR(50),
    entity_id UUID,
    old_values JSONB,
    new_values JSONB,
    ip_address INET,
    user_agent TEXT,
    request_id UUID,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_audit_logs_user_id ON audit_logs(user_id);
CREATE INDEX idx_audit_logs_entity ON audit_logs(entity_type, entity_id);
CREATE INDEX idx_audit_logs_created_at ON audit_logs(created_at DESC);
CREATE INDEX idx_audit_logs_action ON audit_logs(action);
```

### 16. system_settings
Stores global system configuration.

```sql
CREATE TABLE system_settings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    setting_key VARCHAR(100) UNIQUE NOT NULL,
    setting_value TEXT,
    setting_type VARCHAR(20) CHECK (setting_type IN ('string', 'number', 'boolean', 'json')),
    description TEXT,
    category VARCHAR(50), -- 'wallet', 'meter', 'notification', 'system'
    is_encrypted BOOLEAN DEFAULT false,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_by UUID REFERENCES users(id)
);

CREATE INDEX idx_system_settings_key ON system_settings(setting_key);
CREATE INDEX idx_system_settings_category ON system_settings(category);

-- Default system settings
INSERT INTO system_settings (setting_key, setting_value, setting_type, category, description) VALUES
('default_low_balance_threshold', '50.00', 'number', 'wallet', 'Default low balance alert threshold in Rands'),
('default_low_balance_days', '3', 'number', 'wallet', 'Alert when X days of usage remaining'),
('default_electricity_minimum', '20.00', 'number', 'meter', 'Minimum amount to activate electricity meter'),
('default_water_minimum', '20.00', 'number', 'meter', 'Minimum amount to activate water meter'),
('alert_frequency_hours', '24', 'number', 'notification', 'Hours between repeat alerts'),
('auto_calculate_daily_usage', 'true', 'boolean', 'wallet', 'Automatically calculate daily average usage'),
('smart_alert_enabled', 'true', 'boolean', 'notification', 'Enable smart alerts based on usage patterns');
```

### 17. meter_alerts
Tracks meter-specific alerts and issues.

```sql
CREATE TABLE meter_alerts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    meter_id UUID REFERENCES meters(id) NOT NULL,
    alert_type VARCHAR(50) NOT NULL CHECK (alert_type IN (
        'communication_loss', 'tamper_detected', 'low_credit', 
        'disconnection', 'reconnection', 'abnormal_usage', 'meter_fault'
    )),
    severity VARCHAR(20) NOT NULL CHECK (severity IN ('info', 'warning', 'error', 'critical')),
    message TEXT,
    is_resolved BOOLEAN DEFAULT false,
    resolved_at TIMESTAMP,
    resolved_by UUID REFERENCES users(id),
    resolution_notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_meter_alerts_meter_id ON meter_alerts(meter_id);
CREATE INDEX idx_meter_alerts_alert_type ON meter_alerts(alert_type);
CREATE INDEX idx_meter_alerts_is_resolved ON meter_alerts(is_resolved);
CREATE INDEX idx_meter_alerts_created_at ON meter_alerts(created_at DESC);
```

### 18. reconciliation_reports
Stores bulk meter vs unit meter reconciliation data.

```sql
CREATE TABLE reconciliation_reports (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    estate_id UUID REFERENCES estates(id) NOT NULL,
    report_date DATE NOT NULL,
    utility_type VARCHAR(20) NOT NULL CHECK (utility_type IN ('electricity', 'water')),
    bulk_meter_reading DECIMAL(15,3) NOT NULL,
    sum_unit_readings DECIMAL(15,3) NOT NULL,
    variance DECIMAL(15,3) NOT NULL,
    variance_percentage DECIMAL(5,2),
    loss_amount DECIMAL(15,3),
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by UUID REFERENCES users(id),
    UNIQUE(estate_id, report_date, utility_type)
);

CREATE INDEX idx_reconciliation_estate_id ON reconciliation_reports(estate_id);
CREATE INDEX idx_reconciliation_date ON reconciliation_reports(report_date DESC);
```

---

## Views

### 1. v_unit_current_status
Provides a complete view of unit status including meters and wallet.

```sql
CREATE VIEW v_unit_current_status AS
SELECT 
    u.id AS unit_id,
    u.unit_number,
    e.name AS estate_name,
    r.first_name || ' ' || r.last_name AS resident_name,
    r.phone AS resident_phone,
    w.balance AS wallet_balance,
    em.serial_number AS electricity_meter,
    em.last_reading AS electricity_reading,
    em.communication_status AS electricity_status,
    wm.serial_number AS water_meter,
    wm.last_reading AS water_reading,
    wm.communication_status AS water_status,
    sm.serial_number AS solar_meter,
    sm.last_reading AS solar_reading,
    sm.communication_status AS solar_status,
    u.occupancy_status,
    CASE 
        WHEN w.balance < w.low_balance_threshold THEN 'low_balance'
        WHEN em.communication_status = 'offline' OR wm.communication_status = 'offline' THEN 'meter_issue'
        ELSE 'normal'
    END AS alert_status
FROM units u
LEFT JOIN estates e ON u.estate_id = e.id
LEFT JOIN residents r ON u.resident_id = r.id
LEFT JOIN wallets w ON u.wallet_id = w.id
LEFT JOIN meters em ON u.electricity_meter_id = em.id
LEFT JOIN meters wm ON u.water_meter_id = wm.id
LEFT JOIN meters sm ON u.solar_meter_id = sm.id
WHERE u.is_active = true;
```

### 2. v_daily_consumption_summary
Aggregates daily consumption data by estate and utility type.

```sql
CREATE VIEW v_daily_consumption_summary AS
SELECT 
    DATE(mr.reading_date) AS consumption_date,
    e.id AS estate_id,
    e.name AS estate_name,
    m.meter_type,
    COUNT(DISTINCT u.id) AS units_count,
    SUM(mr.consumption_since_last) AS total_consumption,
    AVG(mr.consumption_since_last) AS avg_consumption,
    MAX(mr.consumption_since_last) AS max_consumption,
    MIN(mr.consumption_since_last) AS min_consumption
FROM meter_readings mr
JOIN meters m ON mr.meter_id = m.id
JOIN units u ON (u.electricity_meter_id = m.id OR u.water_meter_id = m.id OR u.solar_meter_id = m.id)
JOIN estates e ON u.estate_id = e.id
WHERE mr.is_validated = true
GROUP BY DATE(mr.reading_date), e.id, e.name, m.meter_type;
```

---

## Indexes Strategy

### Performance Indexes
- Primary keys: UUID with default gen_random_uuid()
- Foreign keys: All FK columns indexed
- Search columns: username, email, serial_number
- Filter columns: is_active, status, meter_type
- Date columns: created_at DESC for recent records
- Composite indexes for common JOIN operations

### Recommended Additional Indexes

```sql
-- For meter reading queries
CREATE INDEX idx_meter_readings_composite ON meter_readings(meter_id, reading_date DESC, is_validated);

-- For transaction searches
CREATE INDEX idx_transactions_wallet_date ON transactions(wallet_id, created_at DESC);

-- For notification delivery
CREATE INDEX idx_notifications_pending ON notifications(status, created_at) WHERE status = 'pending';

-- For audit trail queries
CREATE INDEX idx_audit_logs_user_date ON audit_logs(user_id, created_at DESC);
```

---

## Data Integrity Constraints

### Business Rules Enforced

1. **Wallet Balance Consistency**
   - Total balance must equal sum of utility balances
   - Electricity can go to zero (disconnection)
   - Water can go negative (debt accumulation)

2. **Meter Assignment**
   - Each unit must have exactly 3 meters (electricity, water, solar)
   - Bulk meters can only be assigned to one estate

3. **Rate Table Validity**
   - No overlapping effective date ranges for same utility type
   - Only one default rate table per utility type

4. **Transaction Integrity**
   - Balance after = Balance before + Amount (for credits)
   - Balance after = Balance before - Amount (for debits)

---

## Migration Strategy

### Initial Setup

```sql
-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Create audit trigger function
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Apply trigger to all tables with updated_at
CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON users
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
-- Repeat for all tables with updated_at column
```

### Data Migration from Legacy Systems

1. **Estate and Unit Import**
   - CSV import for bulk creation
   - Validation of required fields
   - Duplicate detection

2. **Meter Registration**
   - Serial number validation
   - Communication test before activation
   - Initial reading capture

3. **Resident Data**
   - POPIA-compliant data collection
   - Email/phone verification
   - Wallet initialization

---

## Backup and Recovery

### Backup Strategy

```sql
-- Daily full backup
pg_dump -h localhost -U quantify_user -d quantify_metering -f backup_$(date +%Y%m%d).sql

-- Continuous archiving with WAL
archive_mode = on
archive_command = 'cp %p /backup/wal/%f'

-- Point-in-time recovery capability
restore_command = 'cp /backup/wal/%f %p'
```

### Critical Tables for Priority Recovery
1. wallets - Current balances
2. transactions - Financial records
3. meter_readings - Consumption data
4. users/residents - Account information

---

## Performance Optimization

### Partitioning Strategy

```sql
-- Partition meter_readings by month
CREATE TABLE meter_readings_2025_01 PARTITION OF meter_readings
    FOR VALUES FROM ('2025-01-01') TO ('2025-02-01');

-- Partition transactions by month
CREATE TABLE transactions_2025_01 PARTITION OF transactions
    FOR VALUES FROM ('2025-01-01') TO ('2025-02-01');
```

### Materialized Views for Reports

```sql
-- Daily revenue summary
CREATE MATERIALIZED VIEW mv_daily_revenue AS
SELECT 
    DATE(created_at) AS revenue_date,
    transaction_type,
    COUNT(*) AS transaction_count,
    SUM(amount) AS total_amount
FROM transactions
WHERE status = 'completed'
GROUP BY DATE(created_at), transaction_type;

-- Refresh daily
CREATE INDEX idx_mv_daily_revenue_date ON mv_daily_revenue(revenue_date DESC);
REFRESH MATERIALIZED VIEW mv_daily_revenue;
```

---

## Security Considerations

### Data Encryption
- Password fields: bcrypt hashing
- Sensitive settings: AES encryption
- PII data: Column-level encryption for ID numbers

### Access Control
- Row-level security for multi-tenant isolation
- Role-based table permissions
- Audit logging for all data modifications

### SQL Injection Prevention
- Parameterized queries only
- Input validation at application layer
- Stored procedures for complex operations

---

## Monitoring Queries

### System Health Checks

```sql
-- Check offline meters
SELECT COUNT(*) AS offline_meters
FROM meters
WHERE communication_status = 'offline'
AND last_communication < NOW() - INTERVAL '24 hours';

-- Low balance units
SELECT COUNT(*) AS low_balance_units
FROM wallets
WHERE balance < low_balance_threshold
AND is_suspended = false;

-- Failed transactions
SELECT COUNT(*) AS failed_transactions
FROM transactions
WHERE status = 'failed'
AND created_at > NOW() - INTERVAL '24 hours';
```

---

## Document Version History

- v1.0 - Initial database schema design based on prototype requirements

---

*End of Database Schema Documentation*
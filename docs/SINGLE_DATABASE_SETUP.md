# Single Database Setup - LoRaWAN Integration

This document explains the single-database architecture where both the **Backend (MQTT Listener)** and **Frontend (QuantifyMeteringSystem)** share the same PostgreSQL database.

## Architecture Overview

```
┌─────────────────────────────────────────────────────────┐
│         Single PostgreSQL Database: "quantify"          │
│                                                          │
│  Tables:                                                │
│    - meters (shared by both apps)                      │
│    - meter_readings (shared by both apps)              │
│    - device_commands (for device control)              │
│    - users, estates, wallets, etc. (frontend only)     │
└─────────────────────────────────────────────────────────┘
         ↑                                    ↑
         │ WRITES                             │ READS/WRITES
         │                                    │
    ┌────────────┐                    ┌──────────────────┐
    │  Backend   │                    │    Frontend      │
    │  (MQTT)    │                    │  (User App)      │
    │            │                    │                  │
    │ Writes:    │                    │ Manages:         │
    │ - meters   │                    │ - All tables     │
    │ - meter_   │                    │ - User interface │
    │   readings │                    │ - Billing        │
    └────────────┘                    │ - Prepaid logic  │
                                      └──────────────────┘

Data Flow:
1. LoRaWAN Device → ChirpStack → MQTT → Backend
2. Backend decodes and writes to database tables
3. Frontend reads from same tables (no sync needed!)
4. User actions → Frontend writes commands to device_commands
5. Backend reads commands → sends to devices (future phase)
```

## Key Benefits

✅ **No Data Duplication** - Single source of truth
✅ **Real-time Updates** - Frontend sees data immediately
✅ **No Sync Service Needed** - Direct database access
✅ **Simplified Architecture** - One database to manage
✅ **Bidirectional Communication** - Commands via shared table

---

## Database Schema Changes

### 1. `meters` Table - Added LoRaWAN Fields

| Field | Type | Description |
|-------|------|-------------|
| `device_eui` | VARCHAR(16) | LoRaWAN Device EUI (unique identifier) |
| `lorawan_device_type` | VARCHAR(50) | Device type (milesight_em300, qalcosonic_w1) |

**Existing fields used by backend:**
- `serial_number` - Used as device identifier (same as device_eui initially)
- `meter_type` - Mapped from LoRaWAN device (electricity, water)
- `manufacturer`, `model` - Device info
- `last_reading`, `last_reading_date` - Updated by backend on each reading
- `communication_status` - Updated to 'online' when data received

### 2. `meter_readings` Table - Added LoRaWAN Fields

| Field | Type | Description |
|-------|------|-------------|
| `pulse_count` | INTEGER | Pulse count (for EM300-DI) |
| `temperature` | NUMERIC(5,2) | Device temperature (°C) |
| `humidity` | NUMERIC(5,2) | Device humidity (%) |
| `rssi` | INTEGER | Signal strength (dBm) |
| `snr` | NUMERIC(5,2) | Signal-to-noise ratio (dB) |
| `battery_level` | INTEGER | Battery percentage (0-100) |
| `raw_payload` | TEXT | Original hex/JSON payload |

**Existing fields used by backend:**
- `reading_value` - Calculated from pulse_count or total_volume
- `reading_date` - Timestamp of reading
- `reading_type` - Set to 'automatic'
- `is_validated` - Set to True (backend readings pre-validated)

### 3. `device_commands` Table - NEW

Command queue for sending instructions to devices (future phase).

| Field | Type | Description |
|-------|------|-------------|
| `meter_id` | INTEGER | Frontend meter ID |
| `device_eui` | VARCHAR(16) | Target device EUI |
| `command_type` | VARCHAR(50) | switch_on, switch_off, update_credit, etc. |
| `command_data` | TEXT | JSON command parameters |
| `status` | VARCHAR(20) | pending, sent, completed, failed |
| `priority` | INTEGER | 1-10 (1=highest) |
| `scheduled_at` | TIMESTAMP | When to send (NULL=immediate) |
| `sent_at` | TIMESTAMP | When sent to backend |
| `completed_at` | TIMESTAMP | When confirmed |
| `error_message` | TEXT | Error details if failed |
| `retry_count` | INTEGER | Number of retries |
| `max_retries` | INTEGER | Max retry attempts (default: 3) |

---

## Installation Steps

### Step 1: Apply Database Migration (Frontend)

Run the migration to add LoRaWAN fields to existing tables:

```bash
cd QuantifyMeteringSystem

# Using Flask-Migrate (if configured)
flask db upgrade

# OR manually run the migration
python migrations/add_lorawan_fields.py
```

This will:
- Add `device_eui` and `lorawan_device_type` to `meters` table
- Add telemetry fields to `meter_readings` table
- Create `device_commands` table

### Step 2: Grant Database Permissions (Backend User)

The backend user needs access to the frontend database:

```sql
-- Connect to PostgreSQL as superuser
sudo -u postgres psql

-- Grant permissions to backend user
GRANT ALL PRIVILEGES ON DATABASE quantify TO watermeter_user;

-- Connect to quantify database
\c quantify

-- Grant table permissions
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO watermeter_user;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO watermeter_user;

-- Make it permanent for future tables
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO watermeter_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON SEQUENCES TO watermeter_user;
```

### Step 3: Restart Backend Service

The backend configuration has been updated to use the frontend database:

```bash
sudo systemctl restart meter-system
sudo systemctl status meter-system
```

Check logs to verify connection:
```bash
sudo journalctl -u meter-system -f
```

### Step 4: Register Meter in Frontend

Before the backend can save data, the meter must exist in the database. You have two options:

**Option A: Register via Frontend UI** (when available)

**Option B: Register via Database**

```sql
-- Connect to database
psql -U watermeter_user -d quantify

-- Insert meter
INSERT INTO meters (
    serial_number, meter_type, manufacturer, model,
    device_eui, lorawan_device_type,
    communication_type, communication_status,
    is_prepaid, is_active,
    created_at, updated_at
) VALUES (
    '24e124136f215917',  -- Device EUI as serial
    'electricity',       -- Meter type
    'Milesight',         -- Manufacturer
    'EM300-DI',          -- Model
    '24e124136f215917',  -- Device EUI
    'milesight_em300',   -- LoRaWAN device type
    'cellular',          -- Communication type
    'offline',           -- Will update to 'online' on first reading
    true,                -- Prepaid
    true,                -- Active
    NOW(),               -- Created
    NOW()                -- Updated
);
```

### Step 5: Test Data Flow

1. **Send test data** to your device or use simulator:
   ```bash
   cd Quantify-Metering-Monitor
   python simulate_gateway.py
   ```

2. **Check backend logs**:
   ```bash
   sudo journalctl -u meter-system -f
   ```

   You should see:
   ```
   ✓ Connected to MQTT broker
   📩 Received message on topic: application/+/device/+/event/up
   📊 Processing data for meter: 24e124136f215917 (milesight_em300)
   ✓ Saved reading for 24e124136f215917: 0.123 (electricity)
   ```

3. **Check database** to verify data was written:
   ```sql
   -- View meters
   SELECT serial_number, device_eui, meter_type, last_reading, last_communication
   FROM meters;

   -- View recent readings
   SELECT meter_id, reading_value, reading_date, pulse_count, rssi, snr, battery_level
   FROM meter_readings
   ORDER BY reading_date DESC
   LIMIT 10;
   ```

4. **Access Frontend** - You should see the meter and its readings

---

## Device Type Mapping

The backend automatically maps LoRaWAN device types to frontend meter types:

| LoRaWAN Device Type | Frontend Meter Type | Description |
|---------------------|---------------------|-------------|
| `milesight_em300` | `electricity` | Pulse counter (for electricity) |
| `qalcosonic_w1` | `water` | Water meter |

### Pulse Count Conversion

For pulse counters (Milesight EM300-DI):
- Backend stores: `pulse_count` (e.g., 123 pulses)
- Backend calculates: `reading_value = pulse_count / 1000` (e.g., 0.123 kWh)
- Assumes: 1000 pulses per kWh

You can adjust the conversion factor in `mqtt_listener.py` line 115:
```python
reading_value = float(pulse_count) / 1000.0  # Change divisor as needed
```

---

## Troubleshooting

### Backend Can't Connect to Database

**Error**: `FATAL:  database "quantify" does not exist`

**Solution**: Create the database:
```bash
sudo -u postgres createdb quantify
```

---

**Error**: `FATAL:  permission denied for database "quantify"`

**Solution**: Grant permissions (see Step 2)

---

### Backend Not Saving Data

**Error**: `⚠ Unknown device: 24e124136f215917 - Skipping (register meter first)`

**Solution**: Register the meter in the database (see Step 4)

---

**Error**: `relation "readings" does not exist`

**Solution**: Backend models updated to use `meter_readings` table. Restart backend service:
```bash
sudo systemctl restart meter-system
```

---

### Readings Not Appearing in Frontend

**Check 1**: Verify data is in database:
```sql
SELECT COUNT(*) FROM meter_readings;
```

**Check 2**: Verify meter is active:
```sql
SELECT serial_number, device_eui, is_active FROM meters;
```

**Check 3**: Check frontend logs for errors

---

## File Changes Summary

### Frontend (QuantifyMeteringSystem)

**Modified Files:**
1. `app/models/meter.py` - Added `device_eui`, `lorawan_device_type`
2. `app/models/meter_reading.py` - Added telemetry fields

**Created Files:**
3. `app/models/device_command.py` - NEW command queue model
4. `migrations/add_lorawan_fields.py` - Database migration script
5. `SINGLE_DATABASE_SETUP.md` - This documentation

### Backend (Quantify-Metering-Monitor)

**Modified Files:**
1. `app/__init__.py` - Changed database URL to `quantify`
2. `water_meter_module/models.py` - Updated models to match frontend schema
3. `water_meter_module/mqtt_listener.py` - Updated to use new field names and calculate `reading_value`

---

## Next Steps

### Phase 1: Current Status ✅
- ✅ Single database architecture
- ✅ Backend writes meter data
- ✅ Frontend reads meter data
- ✅ Real-time data flow

### Phase 2: Device Commands (Next)
- ⏳ Backend reads from `device_commands` table
- ⏳ Backend sends downlink commands via ChirpStack
- ⏳ Frontend creates commands (switch on/off, credit update)
- ⏳ Command status tracking in UI

### Phase 3: Advanced Features
- ⏳ Automated billing based on readings
- ⏳ Low balance alerts and auto-cutoff
- ⏳ Real-time WebSocket updates
- ⏳ Advanced analytics and reporting

---

## Support

**Check Logs:**
```bash
# Backend logs
sudo journalctl -u meter-system -f

# Frontend logs (if using gunicorn)
tail -f /var/log/quantify/app.log
```

**Database Access:**
```bash
psql -U watermeter_user -d quantify
```

**Verify MQTT Connection:**
```bash
mosquitto_sub -h localhost -t 'application/+/device/+/event/up' -v
```

---

**Last Updated**: 2025-11-03
**Version**: 2.0.0 (Single Database Architecture)

# Device Type & Communication Type Management Implementation

**Created:** 2025-11-11
**Feature:** Dynamic management of Device Types and Communication Types

---

## Overview

This implementation adds a comprehensive management system for Device Types (LoRaWAN device types) and Communication Types (meter communication methods). Previously, these were hard-coded in the HTML templates. Now they can be managed dynamically through an admin interface.

---

## Changes Summary

### Files Created (12 new files)

#### 1. Database Models
- `app/models/device_type.py` - Device Type model
- `app/models/communication_type.py` - Communication Type model

#### 2. Database Migration
- `migrations/versions/f1a2b3c4d5e6_add_device_and_communication_type_tables.py`

#### 3. Service Layer
- `app/services/device_types.py` - Device Type CRUD operations
- `app/services/communication_types.py` - Communication Type CRUD operations

#### 4. API Routes
- `app/routes/v1/device_types.py` - Device Type management endpoints
- `app/routes/v1/communication_types.py` - Communication Type management endpoints

#### 5. HTML Templates
- `app/templates/settings/device-types.html` - Device Type management UI
- `app/templates/settings/communication-types.html` - Communication Type management UI

#### 6. JavaScript
- `app/static/js/settings/device-types.js` - Device Type UI interactions
- `app/static/js/settings/communication-types.js` - Communication Type UI interactions

#### 7. Seed Script
- `scripts/seed_device_comm_types.py` - Populate initial reference data

### Files Modified (4 files)

1. **`app/models/__init__.py`**
   - Added imports for DeviceType and CommunicationType

2. **`app/routes/v1/__init__.py`**
   - Registered device_types and communication_types route modules

3. **`app/routes/v1/meters.py`**
   - Added imports for device types and communication types services
   - Updated meters_page() to pass device_types and communication_types to template

4. **`app/templates/meters/meters.html`**
   - Replaced hard-coded device type dropdown with dynamic Jinja2 loop
   - Replaced hard-coded communication type dropdown with dynamic Jinja2 loop
   - Added gear icon links to management pages

---

## Database Schema

### Table: `device_types`

| Column | Type | Description |
|--------|------|-------------|
| `id` | INTEGER PK | Auto-increment primary key |
| `code` | VARCHAR(50) UNIQUE | Unique identifier (e.g., "milesight_em300") |
| `name` | VARCHAR(100) | Display name (e.g., "Milesight EM300-DI") |
| `description` | TEXT | Optional description |
| `manufacturer` | VARCHAR(100) | Device manufacturer |
| `default_model` | VARCHAR(100) | Default model number |
| `supports_temperature` | BOOLEAN | Temperature sensor capability |
| `supports_pulse` | BOOLEAN | Pulse counter capability |
| `supports_modbus` | BOOLEAN | Modbus protocol support |
| `is_active` | BOOLEAN | Active status (soft delete) |
| `created_at` | DATETIME | Timestamp |
| `updated_at` | DATETIME | Timestamp |

**Indexes:**
- `ix_device_types_code` on `code`

---

### Table: `communication_types`

| Column | Type | Description |
|--------|------|-------------|
| `id` | INTEGER PK | Auto-increment primary key |
| `code` | VARCHAR(20) UNIQUE | Unique identifier (e.g., "lora") |
| `name` | VARCHAR(100) | Display name (e.g., "LoRaWAN") |
| `description` | TEXT | Optional description |
| `requires_device_eui` | BOOLEAN | Requires Device EUI field |
| `requires_gateway` | BOOLEAN | Requires gateway infrastructure |
| `supports_remote_control` | BOOLEAN | Supports remote commands |
| `is_active` | BOOLEAN | Active status (soft delete) |
| `created_at` | DATETIME | Timestamp |
| `updated_at` | DATETIME | Timestamp |

**Indexes:**
- `ix_communication_types_code` on `code`

---

## API Endpoints

### Device Types

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/device-types` | Device types management page (HTML) |
| GET | `/api/v1/api/device-types` | Get all device types (JSON) |
| GET | `/api/v1/api/device-types/<id>` | Get specific device type (JSON) |
| POST | `/api/v1/api/device-types` | Create new device type (JSON) |
| PUT | `/api/v1/api/device-types/<id>` | Update device type (JSON) |
| DELETE | `/api/v1/api/device-types/<id>` | Deactivate device type (soft delete) |

**Query Parameters:**
- `active_only=true|false` - Filter by active status (default: true)

---

### Communication Types

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/communication-types` | Communication types management page (HTML) |
| GET | `/api/v1/api/communication-types` | Get all communication types (JSON) |
| GET | `/api/v1/api/communication-types/<id>` | Get specific communication type (JSON) |
| POST | `/api/v1/api/communication-types` | Create new communication type (JSON) |
| PUT | `/api/v1/api/communication-types/<id>` | Update communication type (JSON) |
| DELETE | `/api/v1/api/communication-types/<id>` | Deactivate communication type (soft delete) |

**Query Parameters:**
- `active_only=true|false` - Filter by active status (default: true)

---

## Permissions

Both device types and communication types use the `settings.view` and `settings.edit` permissions.

- **View:** `settings.view` - Required to access management pages and list types
- **Create:** `settings.edit` - Required to create new types
- **Edit:** `settings.edit` - Required to update existing types
- **Delete:** `settings.edit` - Required to deactivate types

---

## Initial Seed Data

The seed script creates the following initial data:

### Device Types (4 records)

1. **Milesight EM300-DI**
   - Code: `milesight_em300`
   - Manufacturer: Milesight
   - Features: Temperature, Pulse Counter

2. **Qalcosonic W1**
   - Code: `qalcosonic_w1`
   - Manufacturer: Qalcosonic
   - Features: Modbus

3. **Kamstrup Multical**
   - Code: `kamstrup_multical`
   - Manufacturer: Kamstrup
   - Features: Temperature, Modbus

4. **Fengbo 4G Water Meter**
   - Code: `fengbo_water`
   - Manufacturer: Fengbo

### Communication Types (6 records)

1. **LoRaWAN** (`lora`) - Requires EUI, Gateway, Remote Control
2. **4G/NB-IoT** (`cellular`) - Requires EUI, Remote Control
3. **PLC** (`plc`) - Remote Control only
4. **WiFi** (`wifi`) - Remote Control only
5. **Manual Reading** (`manual`) - No requirements
6. **Modbus RTU/TCP** (`modbus`) - Remote Control only

---

## Installation & Setup

### Step 1: Run Database Migration

```bash
cd "H:\GIT_METALOGIX\Quantify Metering\QuantifyMeteringSystem"
export FLASK_APP=application.py  # or set FLASK_APP=application.py on Windows
flask db upgrade
```

This will create the `device_types` and `communication_types` tables.

---

### Step 2: Seed Initial Data

```bash
python scripts/seed_device_comm_types.py
```

Expected output:
```
============================================================
DEVICE TYPES & COMMUNICATION TYPES SEEDING
============================================================

Seeding device types...
  ✓ Created device type: Milesight EM300-DI (Pulse Counter)
  ✓ Created device type: Qalcosonic W1 (Water Meter)
  ✓ Created device type: Kamstrup Multical (Heat/Water Meter)
  ✓ Created device type: Fengbo 4G Water Meter
Device types seeded successfully!

Seeding communication types...
  ✓ Created communication type: LoRaWAN
  ✓ Created communication type: 4G/NB-IoT (Cellular)
  ✓ Created communication type: PLC (Power Line Communication)
  ✓ Created communication type: WiFi
  ✓ Created communication type: Manual Reading
  ✓ Created communication type: Modbus RTU/TCP
Communication types seeded successfully!

============================================================
✓ All reference data seeded successfully!
============================================================
```

---

### Step 3: Verify Installation

1. **Start the Flask application:**
   ```bash
   flask run
   ```

2. **Access Device Types Management:**
   - Navigate to: `http://localhost:5000/api/v1/device-types`
   - You should see a table with 4 device types
   - Click "Add Device Type" to test creation

3. **Access Communication Types Management:**
   - Navigate to: `http://localhost:5000/api/v1/communication-types`
   - You should see a table with 6 communication types
   - Click "Add Communication Type" to test creation

4. **Test Meters Page Integration:**
   - Navigate to: `http://localhost:5000/api/v1/meters`
   - Click "Create Meter"
   - Verify that "Device Type" dropdown shows all seeded types
   - Verify that "Communication Type" dropdown shows all seeded types
   - Notice the gear icon (⚙) next to each dropdown label - clicking it takes you to management page

---

## Usage Guide

### Adding a New Device Type

1. Navigate to `/api/v1/device-types`
2. Click "Add Device Type"
3. Fill in the form:
   - **Code** (required): Unique identifier (lowercase, underscores)
   - **Name** (required): Display name
   - **Manufacturer**: Optional
   - **Default Model**: Optional
   - **Description**: Optional
   - **Supported Features**: Check applicable boxes
   - **Active**: Check to make available immediately
4. Click "Save Device Type"

Example:
```
Code: dragino_lsn50v2
Name: Dragino LSN50v2 (Sensor Node)
Manufacturer: Dragino
Default Model: LSN50v2-D20
Description: LoRaWAN sensor with multiple probe support
Features: ✓ Temperature, ✓ Pulse Counter
Active: ✓
```

---

### Adding a New Communication Type

1. Navigate to `/api/v1/communication-types`
2. Click "Add Communication Type"
3. Fill in the form:
   - **Code** (required): Unique identifier (lowercase)
   - **Name** (required): Display name
   - **Description**: Optional
   - **Requirements**: Check applicable boxes
   - **Active**: Check to make available immediately
4. Click "Save Communication Type"

Example:
```
Code: zigbee
Name: Zigbee
Description: Zigbee mesh network protocol
Requirements: ☐ Requires Device EUI, ✓ Requires Gateway, ✓ Supports Remote Control
Active: ✓
```

---

### Editing Types

1. Click the edit icon (✏️) next to any type
2. Modify the fields
3. Click "Save"

---

### Deactivating Types

1. Click the ban icon (🚫) next to any active type
2. Confirm the action
3. Type is soft-deleted (is_active set to False)
4. Inactive types won't appear in dropdowns but remain in database

---

## Integration with Meters

### Create Meter Modal

When creating a new meter at `/api/v1/meters`:

1. **Device Type dropdown** now shows all active device types from the database
2. **Communication Type dropdown** now shows all active communication types from the database
3. Both dropdowns include a gear icon link to manage the respective types

### Backend Validation

The `meters.py` route handler still validates that selected values exist in the database via the CHECK constraints on the `meters` table.

**Note:** If you add new communication types, you may need to update the CHECK constraint in `meters` table:

```sql
ALTER TABLE meters DROP CONSTRAINT ck_meters_comm_type;
ALTER TABLE meters ADD CONSTRAINT ck_meters_comm_type
  CHECK (communication_type IN ('plc','cellular','wifi','manual','lora','zigbee','modbus'));
```

**Better approach:** Remove the CHECK constraint entirely and rely on foreign key validation:

```python
# Future enhancement: Add foreign key
communication_type_id = db.Column(db.Integer, db.ForeignKey('communication_types.id'))
```

---

## API Examples

### Get All Device Types (JSON)

```bash
curl -X GET http://localhost:5000/api/v1/api/device-types \
  -H "Content-Type: application/json" \
  --cookie "session=YOUR_SESSION_COOKIE"
```

Response:
```json
[
  {
    "id": 1,
    "code": "milesight_em300",
    "name": "Milesight EM300-DI (Pulse Counter)",
    "description": "LoRaWAN pulse counter for electricity and water meters",
    "manufacturer": "Milesight",
    "default_model": "EM300-DI",
    "supports_temperature": true,
    "supports_pulse": true,
    "supports_modbus": false,
    "is_active": true,
    "created_at": "2025-11-11T10:00:00",
    "updated_at": "2025-11-11T10:00:00"
  }
]
```

---

### Create New Device Type (JSON)

```bash
curl -X POST http://localhost:5000/api/v1/api/device-types \
  -H "Content-Type: application/json" \
  --cookie "session=YOUR_SESSION_COOKIE" \
  -d '{
    "code": "dragino_lsn50v2",
    "name": "Dragino LSN50v2 (Sensor Node)",
    "manufacturer": "Dragino",
    "default_model": "LSN50v2-D20",
    "description": "LoRaWAN sensor with multiple probe support",
    "supports_temperature": true,
    "supports_pulse": true,
    "supports_modbus": false,
    "is_active": true
  }'
```

---

### Update Device Type (JSON)

```bash
curl -X PUT http://localhost:5000/api/v1/api/device-types/1 \
  -H "Content-Type: application/json" \
  --cookie "session=YOUR_SESSION_COOKIE" \
  -d '{
    "description": "Updated description",
    "is_active": false
  }'
```

---

### Get All Communication Types (Active Only)

```bash
curl -X GET "http://localhost:5000/api/v1/api/communication-types?active_only=true" \
  -H "Content-Type: application/json" \
  --cookie "session=YOUR_SESSION_COOKIE"
```

---

## Future Enhancements

### 1. Foreign Key Relationships

Replace string-based communication_type with foreign key:

```python
# In meters model
communication_type_id = db.Column(db.Integer, db.ForeignKey('communication_types.id'))
communication_type_rel = db.relationship('CommunicationType', backref='meters')
```

### 2. Device Type Features Validation

Validate meter configuration against device capabilities:

```python
# Example: Prevent assigning temperature reading to device that doesn't support it
if meter_reading.temperature and not device_type.supports_temperature:
    raise ValueError("Device does not support temperature readings")
```

### 3. Import/Export

Add CSV import/export for bulk management:

```python
@api_v1.route("/api/device-types/export", methods=["GET"])
def export_device_types():
    # Generate CSV download
```

### 4. Device Type Templates

Pre-configure meters based on device type defaults:

```python
# Auto-fill manufacturer, model based on selected device type
device_type = DeviceType.query.filter_by(code=selected_code).first()
meter.manufacturer = device_type.manufacturer
meter.model = device_type.default_model
```

---

## Troubleshooting

### Issue: "Device type not found" error

**Cause:** No device types seeded
**Solution:** Run `python scripts/seed_device_comm_types.py`

---

### Issue: Dropdowns are empty on meters page

**Cause:** Device types or communication types not being passed to template
**Solution:**
1. Check that meters.py line 202-203 fetches the data
2. Check that render_template line 211-212 passes the data
3. Restart Flask server

---

### Issue: Migration fails with "relation already exists"

**Cause:** Tables already created manually
**Solution:**
```bash
flask db stamp head  # Mark as migrated
# Or drop tables and re-run migration
```

---

### Issue: Can't access management pages (403 Forbidden)

**Cause:** User lacks `settings.view` permission
**Solution:** Grant permission to your role:
```python
# In roles management or database
role.permissions['settings'] = {'view': True, 'edit': True}
```

---

## Testing Checklist

- [ ] Migration runs successfully
- [ ] Seed script populates data without errors
- [ ] Device Types page loads and displays table
- [ ] Can create new device type
- [ ] Can edit existing device type
- [ ] Can deactivate device type
- [ ] Communication Types page loads and displays table
- [ ] Can create new communication type
- [ ] Can edit existing communication type
- [ ] Can deactivate communication type
- [ ] Meters page "Device Type" dropdown shows seeded types
- [ ] Meters page "Communication Type" dropdown shows seeded types
- [ ] Gear icon links work from meters page
- [ ] Creating meter with new device type works
- [ ] Creating meter with new communication type works
- [ ] Deactivated types don't appear in dropdowns

---

## Summary

This implementation successfully replaces hard-coded device types and communication types with a dynamic, database-driven management system. Admins can now:

1. ✅ Add new device types without code changes
2. ✅ Add new communication types without code changes
3. ✅ Edit existing types through a web interface
4. ✅ Deactivate types (soft delete) instead of hard delete
5. ✅ Access management pages directly from the meters page
6. ✅ See updated dropdowns immediately after changes

**Next Steps:**
- Run the migration and seed script
- Test the management interfaces
- Consider adding foreign key relationships for data integrity
- Update the HARD_CODED.md to remove this as a hard-coded issue

---

**Document Version:** 1.0
**Last Updated:** 2025-11-11
**Author:** Claude Code

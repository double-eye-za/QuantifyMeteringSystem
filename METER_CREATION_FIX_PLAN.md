# Meter Creation Fix Plan

## Executive Summary

This document outlines a careful, phased approach to fixing the meter creation flow in QuantifyMeteringSystem. The goal is to ensure that when a meter is created from the frontend, it works correctly with Quantify-Metering-Monitor without manual workarounds.

**Current Status:** 10 of 11 meters are working correctly. The system is functional but requires manual field duplication during meter creation.

---

## Problem Statement

### Current Issues

1. **Frontend Form Confusion:**
   - The form has `Device EUI / IMEI` field which maps to `device_eui`
   - The form has `Serial Number` field (marked as optional) which is actually **required by the backend**
   - Users have to manually enter the device_eui in both fields for LoRaWAN meters to work

2. **No ChirpStack Sync:**
   - Adding a meter in the Meters page does NOT create the device in ChirpStack
   - Adding a device in the LoRaWAN page does NOT create a meter in the database
   - Users must perform two separate operations manually

3. **Device Type Validation Missing:**
   - The form allows selecting device types that have no decoder (e.g., `fengbo_water`, `kamstrup_multical`)
   - The Monitor silently discards data for these meters with no user feedback

---

## Current Data Flow Analysis

### What Happens Today

```
Frontend Form Submission:
├── device_eui: "24e124136f215917" (from Device EUI field)
├── serial_number: "" (empty - marked optional in UI)
├── lorawan_device_type: "milesight_em300"
└── meter_type: "electricity"

Backend (meters.py line 414):
├── required = ["serial_number", "meter_type"]  ← serial_number IS REQUIRED!
└── Returns 400 error if serial_number is empty

Result: User must manually fill serial_number (often copying device_eui)
```

### What the Monitor Needs

```python
# mqtt_listener.py line 93
meter = Meter.query.filter_by(device_eui=device_eui).first()

# Line 102 - Decoder selection
decoded = decode_payload(meter.lorawan_device_type, data)
```

**Critical Fields for Monitor:**
1. `device_eui` - exact match with MQTT message (lowercase, 16 hex chars)
2. `lorawan_device_type` - must be one of: `qalcosonic_w1`, `milesight_em300`, `eastron_sdm`

---

## Risk Assessment

### High Risk Areas (DO NOT TOUCH)

| Component | Risk | Reason |
|-----------|------|--------|
| `meter_readings` table | CRITICAL | 242,511+ readings, cannot lose data |
| `meters` table existing records | CRITICAL | 11 meters with live data |
| Monitor MQTT listener | HIGH | Any changes could stop data collection |
| Decoder functions | HIGH | Changes could corrupt reading values |

### Medium Risk Areas (Change Carefully)

| Component | Risk | Reason |
|-----------|------|--------|
| `create_meter` endpoint | MEDIUM | New meters only, existing unaffected |
| Frontend form validation | MEDIUM | UI changes, no data impact |
| Frontend form JS | MEDIUM | Client-side only |

### Low Risk Areas (Safe to Change)

| Component | Risk | Reason |
|-----------|------|--------|
| Form labels and help text | LOW | No functional impact |
| Add new validation warnings | LOW | Informational only |

---

## Proposed Solution

### Phase 1: Frontend Improvements (LOW RISK)

**Goal:** Fix the form UX without changing backend behavior

#### Changes:

1. **Auto-populate serial_number from device_eui**
   - When user enters Device EUI, auto-fill Serial Number if empty
   - File: `app/static/js/meters/meters.js`
   - Impact: UI only, no backend changes

2. **Make Device Type required for LoRaWAN**
   - If communication_type is "lora", require lorawan_device_type
   - Show warning if selected device type has no decoder
   - File: `app/static/js/meters/meters.js`
   - Impact: Client-side validation only

3. **Add decoder status indicator**
   - Show ✓/✗ next to device types based on decoder availability
   - File: `app/templates/meters/meters.html`
   - Impact: Visual only

#### Validation Rules (Client-Side):

```javascript
// Pseudo-code for validation
const VALID_DECODER_TYPES = ['qalcosonic_w1', 'milesight_em300', 'eastron_sdm'];

function validateMeterForm(form) {
  const deviceEui = form.device_eui.value.trim();
  const serialNumber = form.serial_number.value.trim();
  const communicationType = form.communication_type.value;
  const lorawanDeviceType = form.lorawan_device_type.value;

  // Auto-fill serial_number if empty and device_eui provided
  if (deviceEui && !serialNumber) {
    form.serial_number.value = deviceEui;
  }

  // Warn if LoRaWAN device type has no decoder
  if (communicationType === 'lora' && lorawanDeviceType) {
    if (!VALID_DECODER_TYPES.includes(lorawanDeviceType)) {
      showWarning('Warning: This device type has no decoder. Data will not be processed.');
    }
  }

  // Require device type for LoRaWAN
  if (communicationType === 'lora' && !lorawanDeviceType) {
    showError('Device Type is required for LoRaWAN meters');
    return false;
  }

  return true;
}
```

---

### Phase 2: Optional ChirpStack Sync (MEDIUM RISK)

**Goal:** Optionally create device in ChirpStack when creating a LoRaWAN meter

#### Approach:

1. Add checkbox: "Also register in ChirpStack" (default: unchecked)
2. If checked, require additional fields:
   - Application (dropdown from ChirpStack API)
   - Device Profile (dropdown from ChirpStack API)
   - App Key (optional, for OTAA)
3. On submit, first create in ChirpStack, then create meter in DB

#### Why Optional?

- Some devices may already exist in ChirpStack
- Some users may prefer manual ChirpStack management
- Reduces risk of breaking existing workflows

#### Implementation:

```python
# In meters.py create_meter endpoint
if payload.get("register_in_chirpstack"):
    # Validate ChirpStack fields
    required_cs = ["application_id", "device_profile_id"]
    missing_cs = [f for f in required_cs if not payload.get(f)]
    if missing_cs:
        return jsonify({"message": f"Missing ChirpStack fields: {', '.join(missing_cs)}"}), 400

    # Create in ChirpStack first
    success, result = chirpstack_service.create_device(
        device_eui=payload["device_eui"],
        name=payload.get("serial_number", payload["device_eui"]),
        application_id=payload["application_id"],
        device_profile_id=payload["device_profile_id"],
    )

    if not success:
        return jsonify({"message": f"ChirpStack error: {result}"}), 400

    # Set OTAA keys if provided
    if payload.get("app_key"):
        chirpstack_service.set_device_keys(
            device_eui=payload["device_eui"],
            app_key=payload["app_key"],
        )

# Then create meter in DB (existing code)
meter = svc_create_meter(payload)
```

---

## Implementation Order

### Step 1: Database Backup (REQUIRED FIRST)

```bash
# On server
sudo -u postgres pg_dump quantify > /backup/quantify_$(date +%Y%m%d_%H%M%S).sql
```

### Step 2: Phase 1 Changes (Frontend Only)

1. Edit `app/static/js/meters/meters.js`:
   - Add auto-fill logic for serial_number
   - Add validation for LoRaWAN device types
   - Add decoder warning

2. Edit `app/templates/meters/meters.html`:
   - Update help text for clarity
   - Add decoder status indicators to device type dropdown

3. Test with new meter creation (use test device_eui)

4. Verify existing meters still work

### Step 3: Phase 2 Changes (ChirpStack Sync - Optional)

1. Edit `app/templates/meters/meters.html`:
   - Add "Register in ChirpStack" checkbox
   - Add ChirpStack fields (hidden by default)

2. Edit `app/static/js/meters/meters.js`:
   - Toggle ChirpStack fields visibility
   - Load applications and device profiles from API

3. Edit `app/routes/v1/meters.py`:
   - Add ChirpStack integration to create_meter

4. Test with new meter creation

5. Verify existing meters still work

---

## Rollback Plan

### If Phase 1 Fails:

```bash
# Revert JS changes
git checkout app/static/js/meters/meters.js

# Revert template changes
git checkout app/templates/meters/meters.html

# Restart app
sudo systemctl restart quantify-web
```

### If Phase 2 Fails:

```bash
# Revert route changes
git checkout app/routes/v1/meters.py

# Revert JS and template changes
git checkout app/static/js/meters/meters.js
git checkout app/templates/meters/meters.html

# Restart app
sudo systemctl restart quantify-web
```

### If Data Corruption Detected:

```bash
# Stop services
sudo systemctl stop quantify-web
sudo systemctl stop water-meter-monitor

# Restore database
sudo -u postgres psql -c "DROP DATABASE quantify;"
sudo -u postgres psql -c "CREATE DATABASE quantify;"
sudo -u postgres psql quantify < /backup/quantify_YYYYMMDD_HHMMSS.sql

# Restart services
sudo systemctl start water-meter-monitor
sudo systemctl start quantify-web
```

---

## Testing Checklist

### Pre-Deployment

- [ ] Database backup created
- [ ] Current meter count verified (11 meters)
- [ ] Current reading count verified (~242,511 readings)
- [ ] All 10 working meters still receiving data

### Phase 1 Testing

- [ ] Create new meter with device_eui only → serial_number auto-filled
- [ ] Create new meter with valid decoder type → success
- [ ] Create new meter with invalid decoder type → warning shown
- [ ] Create new LoRaWAN meter without device type → error shown
- [ ] Edit existing meter → no issues
- [ ] Existing meters still receiving data

### Phase 2 Testing

- [ ] Create meter without ChirpStack sync → works as before
- [ ] Create meter with ChirpStack sync → device appears in ChirpStack
- [ ] Create meter with ChirpStack sync + app_key → keys set correctly
- [ ] ChirpStack sync failure → meter NOT created in DB (atomic)
- [ ] Existing meters still receiving data

---

## Questions for User Before Proceeding

1. Do you want Phase 1 only (frontend fixes) or both phases?
2. For Phase 2, should ChirpStack sync be:
   - Optional checkbox (recommended)
   - Always enabled for LoRaWAN meters
   - Separate "Create & Register" button
3. What is the backup location on your server?
4. What is the service name for the web app? (e.g., `quantify-web`, `flask-app`)

---

## Files to be Modified

### Phase 1

| File | Changes |
|------|---------|
| `app/static/js/meters/meters.js` | Auto-fill logic, validation, warnings |
| `app/templates/meters/meters.html` | Help text, decoder indicators |

### Phase 2

| File | Changes |
|------|---------|
| `app/routes/v1/meters.py` | ChirpStack integration in create_meter |
| `app/static/js/meters/meters.js` | ChirpStack field toggle, API calls |
| `app/templates/meters/meters.html` | ChirpStack checkbox and fields |

---

## Estimated Time

- Phase 1: 1-2 hours (including testing)
- Phase 2: 2-3 hours (including testing)
- Total with buffer: 4-6 hours

---

## Sign-Off Required

Before proceeding, please confirm:

1. [ ] Database backup location confirmed
2. [ ] Phase scope confirmed (1 only, or 1+2)
3. [ ] Rollback procedure understood
4. [ ] Testing time available

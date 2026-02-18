# Meter Relay Control Implementation Plan

## Overview

Enable remote disconnect/reconnect functionality for Eastron SDM320C meters via LoRaWAN downlink commands through the Milesight UC100 bridge.

## Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           COMMAND FLOW                                       │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│   Admin Portal                                                               │
│   (QuantifyMeteringSystem)                                                   │
│         │                                                                    │
│         │ 1. Admin clicks "Disconnect"                                       │
│         ▼                                                                    │
│   ┌─────────────┐                                                            │
│   │ Flask API   │  POST /meters/<id>/relay                                   │
│   │ Endpoint    │  { "action": "off" }                                       │
│   └──────┬──────┘                                                            │
│          │                                                                   │
│          │ 2. Call ChirpStack API                                            │
│          ▼                                                                   │
│   ┌─────────────────┐                                                        │
│   │  ChirpStack     │  POST /api/devices/{devEui}/queue                      │
│   │  Network Server │  Payload: 010500000000CDCA (relay OFF)                 │
│   │                 │  Port: 5 (pass-through)                                │
│   └──────┬──────────┘                                                        │
│          │                                                                   │
│          │ 3. LoRaWAN Downlink (waits for next uplink from device)           │
│          ▼                                                                   │
│   ┌─────────────────┐                                                        │
│   │  UC100          │  Receives downlink in RX window                        │
│   │  (LoRa-RS485)   │  Forwards raw bytes to RS485 bus                       │
│   └──────┬──────────┘                                                        │
│          │                                                                   │
│          │ 4. Modbus RTU command                                             │
│          ▼                                                                   │
│   ┌─────────────────┐                                                        │
│   │  SDM320C        │  Receives: 01 05 00 00 00 00 CD CA                     │
│   │  (Meter)        │  Executes: Relay OFF → Power disconnected              │
│   └─────────────────┘                                                        │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

## Hardware Configuration

### Milesight UC100 Settings (Confirmed)
- **Pass-through:** Enabled
- **Pass-through Mode:** Active Pass-through
- **Port:** 5
- **Baud Rate:** 9600
- **Parity:** None
- **Data Bits:** 8
- **Stop Bits:** 1

### Eastron SDM320C Relay Commands
| Action | Modbus Command (Hex) | Description |
|--------|---------------------|-------------|
| Relay OFF | `01 05 00 00 00 00 CD CA` | Open relay, disconnect power |
| Relay ON | `01 05 00 00 FF 00 8C 3A` | Close relay, restore power |

Command breakdown:
- `01` = Slave address (Modbus ID 1)
- `05` = Function code (Write Single Coil)
- `00 00` = Coil address (relay)
- `00 00` / `FF 00` = Value (OFF / ON)
- `CD CA` / `8C 3A` = CRC16 checksum

---

## Implementation Phases

### Phase 1: Proof of Concept (Simple Test) ✅ COMPLETED

**Goal:** Validate we can send a command from the admin portal to the physical meter.

**Status:** Successfully tested on 2026-01-27. Relay disconnect/reconnect works via LoRaWAN.

**Scope:**
- Add a simple test endpoint to send relay commands
- Minimal UI - just a button that calls the endpoint
- No command queue, no status tracking
- Direct ChirpStack API call

**Files created/modified:**
1. `QuantifyMeteringSystem/config.py` - Added ChirpStack settings ✅
2. `QuantifyMeteringSystem/app/services/chirpstack_service.py` - ChirpStack API client ✅
3. `QuantifyMeteringSystem/app/routes/v1/meters.py` - Relay control endpoint ✅
4. `QuantifyMeteringSystem/app/templates/meters/meter-details.html` - Disconnect/Reconnect buttons ✅

**Test Results:**
1. ✅ Navigate to meter details page for a meter with device_eui
2. ✅ Click "Disconnect" button
3. ✅ Verify in ChirpStack UI that downlink is queued
4. ✅ Wait for device to send uplink (triggers downlink delivery)
5. ✅ Verify relay physically disconnects

**Note:** Reconnect command cannot be delivered if meter is disconnected (UC100 loses power). Physical reconnection required first.

---

### Phase 2: Command Queue & Status Tracking

**Goal:** Reliable command delivery with status tracking.

**Scope:**
- Use existing `DeviceCommand` model for command queue
- Track command lifecycle: pending → queued → sent → confirmed/failed
- Show command history on meter details page
- Handle retries

**Files to modify:**
1. `QuantifyMeteringSystem/app/models/__init__.py` - Export DeviceCommand
2. `QuantifyMeteringSystem/app/services/device_commands.py` - NEW: Command business logic
3. `QuantifyMeteringSystem/app/routes/v1/meters.py` - Enhanced endpoints
4. `QuantifyMeteringSystem/app/templates/meters/meter-details.html` - Command history UI

---

### Phase 3: Confirmation & Monitoring

**Goal:** Confirm command execution and update status.

**Scope:**
- Monitor service subscribes to ChirpStack downlink ACK topics
- Update command status when confirmed
- Handle failed deliveries
- Add audit logging

**Files to modify:**
1. `Quantify-Metering-Monitor/water_meter_module/mqtt_listener.py` - Subscribe to ACK topics
2. Update command status in database

---

### Phase 4: Full Feature Set

**Goal:** Production-ready feature with all bells and whistles.

**Scope:**
- Permission controls (who can disconnect)
- Confirmation modal before disconnect
- Reconnect button
- Scheduled commands (e.g., auto-reconnect after payment)
- Notifications to residents
- Bulk operations
- Audit trail

---

## Environment Variables

Add to `.env`:
```
# ChirpStack API Configuration
# Note: Use port 8090 for REST API (not 8080 which is gRPC)
CHIRPSTACK_API_URL=http://localhost:8090
CHIRPSTACK_API_KEY=your-api-key-here
```

## ChirpStack API Reference

### Enqueue Downlink
```
POST {CHIRPSTACK_API_URL}/api/devices/{devEui}/queue

Headers:
  Grpc-Metadata-Authorization: Bearer {API_KEY}
  Content-Type: application/json

Body:
{
  "queueItem": {
    "confirmed": false,
    "data": "AQUAAAANyg==",  // base64 encoded payload
    "fPort": 5
  }
}
```

### Get Device Queue
```
GET {CHIRPSTACK_API_URL}/api/devices/{devEui}/queue

Headers:
  Grpc-Metadata-Authorization: Bearer {API_KEY}
```

---

## Testing Checklist

### Phase 1 Testing ✅ COMPLETED
- [x] ChirpStack API connection works
- [x] Downlink appears in ChirpStack queue
- [x] UC100 receives downlink after uplink
- [x] SDM320C relay physically switches
- [x] No errors in logs

### Phase 2 Testing
- [ ] Command saved to database
- [ ] Status updates correctly
- [ ] Command history displays
- [ ] Retry logic works

### Phase 3 Testing
- [ ] ACK received and processed
- [ ] Command marked as confirmed
- [ ] Failed commands handled

### Phase 4 Testing
- [ ] Permissions enforced
- [ ] Confirmation modal works
- [ ] Audit log entries created
- [ ] Notifications sent

---

## Rollback Plan

If issues occur:
1. Commands are queued, not immediate - can cancel pending
2. Relay ON command always available to restore power
3. Manual override possible via ChirpStack UI
4. Physical access to meter as last resort

---

## Notes

- Class A devices: Downlink only delivered after device sends uplink
- UC100 typical uplink interval: 5-15 minutes (configurable)
- SDM320C Modbus address assumed to be 1 (default)
- CRC is pre-calculated for standard commands

---

## References

- [Milesight UC100 User Guide](https://resource.milesight.com/milesight/iot/document/uc100-user-guide-en.pdf)
- [ChirpStack REST API](https://www.chirpstack.io/docs/chirpstack/api/rest.html)
- Eastron SDM320C Modbus Protocol (relay control via coil write)

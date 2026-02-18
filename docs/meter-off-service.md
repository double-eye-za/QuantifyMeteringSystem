# Meter Off Service

Automated service for disconnecting prepaid electricity meters with zero or negative credit balance.

## Overview

This service runs daily at 6 AM (Africa/Johannesburg timezone) and automatically disconnects electricity meters for units that have exhausted their prepaid credit.

## How It Works

1. **Scheduled Check**: Celery Beat triggers the task at 6 AM daily
2. **Query**: Finds all electricity meters where:
   - Unit's `electricity_balance <= 0`
   - Meter has a `device_eui` (LoRaWAN controllable)
   - Both meter and unit are `is_active = True`
3. **Disconnect**: Sends relay OFF command via ChirpStack to the Milesight UC100 bridge
4. **Logging**: All actions are logged for audit trail

## Architecture

```
Celery Beat (6 AM)
    |
    v
disconnect_zero_balance_meters task
    |
    v
Query: Units + Wallets + Meters
    |
    v
For each zero-balance meter:
    |
    v
ChirpStack REST API (port 8090)
    |
    v
LoRaWAN Downlink Queue
    |
    v
Milesight UC100 Bridge (next uplink)
    |
    v
Modbus Relay OFF Command
    |
    v
Eastron SDM320C Relay Disconnects
```

## Files

| File | Purpose |
|------|---------|
| `app/tasks/prepaid_disconnect_tasks.py` | Celery task implementation |
| `celery_app.py` | Beat schedule configuration |
| `app/services/chirpstack_service.py` | ChirpStack API integration |
| `app/routes/v1/meters.py` | Test endpoints |

## API Endpoints

### Get Zero Balance Report
```
GET /api/v1/meters/prepaid/zero-balance-report
```
Returns list of meters that would be disconnected. No actual disconnects performed.

**Response:**
```json
{
  "success": true,
  "total_meters": 2,
  "note": "This is a report only - no disconnects performed",
  "meters": [
    {
      "unit_id": 1,
      "unit_number": "A101",
      "estate_id": 1,
      "estate_name": "Test Estate",
      "meter_id": 5,
      "meter_serial": "SDM320-001",
      "device_eui": "24e124621f170095",
      "electricity_balance": -15.50,
      "total_balance": 0.00,
      "can_disconnect": true
    }
  ]
}
```

### Test Disconnect Check (Dry Run)
```
POST /api/v1/meters/prepaid/test-disconnect-check
```
Manually triggers the scheduled task. Currently runs in dry-run mode.

**Response:**
```json
{
  "success": true,
  "message": "Disconnect check completed (dry run mode)",
  "result": {
    "status": "success",
    "timestamp": "2026-01-23T06:00:00.000000",
    "meters_processed": 2,
    "meters_disconnected": 0,
    "meters_failed": 0,
    "dry_run": true,
    "details": [...]
  }
}
```

## Configuration

### Environment Variables
```bash
CHIRPSTACK_API_URL=http://localhost:8090
CHIRPSTACK_API_KEY=your_api_key_here
CHIRPSTACK_PASSTHROUGH_PORT=5
```

### Celery Beat Schedule
```python
'disconnect-zero-balance-meters': {
    'task': 'app.tasks.prepaid_disconnect_tasks.disconnect_zero_balance_meters',
    'schedule': crontab(hour=6, minute=0),
    'options': {'queue': 'prepaid'}
}
```

## Running the Service

### Start Celery Worker + Beat
```bash
cd /opt/QuantifyMeteringSystem
source venv/bin/activate
export $(cat .env | xargs)
celery -A celery_app.celery worker --beat --loglevel=info -Q notifications,prepaid
```

### Run Worker and Beat Separately (Production)
```bash
# Terminal 1: Worker
celery -A celery_app.celery worker --loglevel=info -Q notifications,prepaid

# Terminal 2: Beat Scheduler
celery -A celery_app.celery beat --loglevel=info
```

## Safety Mode

The actual disconnect command is **COMMENTED OUT** for safety during development.

To enable actual disconnects, edit `app/tasks/prepaid_disconnect_tasks.py` and uncomment the section around lines 80-100:

```python
# TODO: Uncomment when payment integration is complete
# try:
#     success, message = send_relay_command(meter.device_eui, "off")
#     ...
```

## Important Notes

### Class A Delivery Delay
LoRaWAN Class A devices only receive downlinks immediately after sending an uplink. The UC100 reports every ~2 minutes, so there may be up to 2 minutes delay before the disconnect command is delivered.

### Power Dependency
If the UC100 is powered from the meter being controlled, disconnecting the meter will also power off the UC100. This means:
- The reconnect command cannot be delivered until power is restored manually
- Consider powering the UC100 from a separate always-on supply

### Reconnection
Meters can be reconnected via:
1. The UI Reconnect button on meter details page
2. API: `POST /api/v1/meters/<meter_id>/relay` with `{"action": "on"}`
3. Manual intervention at the property

## Logging

Task logs are output to Celery worker console:
```
[2026-01-23 06:00:00] INFO: ============================================================
[2026-01-23 06:00:00] INFO: Starting zero balance meter disconnect check...
[2026-01-23 06:00:00] INFO: Found 2 meters with zero/negative balance
[2026-01-23 06:00:00] INFO: ----------------------------------------
[2026-01-23 06:00:00] INFO: Processing Unit A101:
[2026-01-23 06:00:00] INFO:   Meter: SDM320-001
[2026-01-23 06:00:00] INFO:   Device EUI: 24e124621f170095
[2026-01-23 06:00:00] INFO:   Electricity Balance: R-15.50
[2026-01-23 06:00:00] INFO:   DRY RUN: Would disconnect (command disabled)
```

## Troubleshooting

### Task Not Running
1. Check Celery Beat is running: `ps aux | grep celery`
2. Check Redis is running: `docker ps | grep redis`
3. Check logs: `celery -A celery_app.celery inspect active`

### ChirpStack API Errors
1. Verify API URL is port 8090 (REST API), not 8080 (gRPC)
2. Check API key is valid:
   ```bash
   curl -H "Authorization: Bearer YOUR_KEY" http://localhost:8090/api/devices?limit=1
   ```

### No Meters Found
1. Verify meters have `device_eui` set
2. Verify units have `electricity_meter_id` linked
3. Verify wallets exist for units with `electricity_balance` field
4. Check meters and units are `is_active = True`

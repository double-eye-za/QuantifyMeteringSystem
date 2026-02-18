# LoRaWAN & ChirpStack Integration

## Overview

The Quantify Metering System integrates with ChirpStack, an open-source LoRaWAN Network Server, to manage LoRaWAN-enabled meters and gateways. This integration allows administrators to provision and manage devices directly from the Quantify dashboard without needing to access the ChirpStack UI.

## Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                     Quantify Metering System                        │
│  ┌─────────────────┐    ┌──────────────────┐    ┌───────────────┐  │
│  │   LoRaWAN UI    │───▶│  Flask Routes    │───▶│  ChirpStack   │  │
│  │  /lorawan/*     │    │  lorawan.py      │    │   Service     │  │
│  └─────────────────┘    └──────────────────┘    └───────┬───────┘  │
└─────────────────────────────────────────────────────────┼───────────┘
                                                          │
                                                          ▼
                                              ┌───────────────────────┐
                                              │   ChirpStack Server   │
                                              │   REST API (8090)     │
                                              └───────────┬───────────┘
                                                          │
                                    ┌─────────────────────┼─────────────────────┐
                                    │                     │                     │
                                    ▼                     ▼                     ▼
                            ┌───────────────┐    ┌───────────────┐    ┌───────────────┐
                            │   Gateway 1   │    │   Gateway 2   │    │   Gateway N   │
                            └───────┬───────┘    └───────┬───────┘    └───────┬───────┘
                                    │                     │                     │
                                    └─────────────────────┼─────────────────────┘
                                                          │ LoRaWAN Radio
                                                          ▼
                                    ┌─────────────────────────────────────────────┐
                                    │              LoRaWAN Devices                │
                                    │  (Water Meters, Electricity Meters, etc.)   │
                                    └─────────────────────────────────────────────┘
```

## Configuration

### Environment Variables

Add the following to your `.env` file:

```env
# ChirpStack Configuration
CHIRPSTACK_API_URL=http://your-chirpstack-server:8090
CHIRPSTACK_API_KEY=your-api-key-here
```

### Obtaining a ChirpStack API Key

1. Log into the ChirpStack web interface
2. Navigate to **API Keys** in the left menu
3. Click **Create API Key**
4. Give it a descriptive name (e.g., "Quantify Metering Integration")
5. Copy the generated key immediately (it won't be shown again)
6. Add it to your `.env` file

## Features

### LoRaWAN Dashboard (`/api/v1/lorawan`)

The main LoRaWAN management page provides:

- **Connection Status**: Real-time ChirpStack connection status indicator
- **Quick Stats**: Count of gateways, devices, and applications
- **Quick Actions**: Shortcuts to add new devices and gateways
- **Help Information**: Brief explanation of LoRaWAN concepts

### Gateway Management (`/api/v1/lorawan/gateways`)

Gateways are the radio receivers that communicate with LoRaWAN devices.

#### Listing Gateways
- View all registered gateways
- See online/offline status (based on last seen time)
- View gateway location coordinates

#### Adding a Gateway
Required fields:
- **Gateway ID (EUI)**: 16 hexadecimal characters (found on gateway label)
- **Name**: Human-readable name
- **Tenant**: ChirpStack tenant to assign the gateway to

Optional fields:
- **Description**: Additional details
- **Location**: Latitude, longitude, and altitude

#### Deleting a Gateway
- Removes the gateway from ChirpStack
- Devices will lose connectivity if no other gateways are in range

### Device Management (`/api/v1/lorawan/devices`)

Devices are the LoRaWAN endpoints (meters, sensors, etc.).

#### Listing Devices
- View all registered devices across all applications
- See device status and last activity
- Filter by application (future enhancement)

#### Adding a Device
Required fields:
- **Device EUI**: 16 hexadecimal characters (unique device identifier)
- **Name**: Human-readable name
- **Application**: ChirpStack application to assign the device to
- **Device Profile**: Defines device capabilities (LoRaWAN version, class, codec)

Optional fields:
- **Description**: Additional details
- **Join EUI**: For OTAA devices (usually all zeros or specific to device)
- **Application Key**: 32 hexadecimal characters for OTAA authentication

#### Deleting a Device
- Removes the device from ChirpStack
- Device will no longer be able to communicate

## API Endpoints

### Connection Test
```
GET /api/v1/api/lorawan/test-connection
```
Tests connectivity to ChirpStack server.

**Response:**
```json
{
  "success": true,
  "message": "Connected to ChirpStack"
}
```

### Applications
```
GET /api/v1/api/lorawan/applications
```
Lists all applications in ChirpStack.

### Device Profiles
```
GET /api/v1/api/lorawan/device-profiles
```
Lists all device profiles in ChirpStack.

### Tenants
```
GET /api/v1/api/lorawan/tenants
```
Lists all tenants in ChirpStack.

### Devices

#### List Devices
```
GET /api/v1/api/lorawan/devices
GET /api/v1/api/lorawan/devices?application_id=<uuid>&limit=100&offset=0
```

#### Get Device
```
GET /api/v1/api/lorawan/devices/<device_eui>
```

#### Create Device
```
POST /api/v1/api/lorawan/devices
Content-Type: application/json

{
  "device_eui": "0123456789abcdef",
  "name": "Water Meter - Unit 5",
  "application_id": "uuid-of-application",
  "device_profile_id": "uuid-of-device-profile",
  "description": "Qalcosonic W1 water meter",
  "join_eui": "0000000000000000",
  "app_key": "00112233445566778899aabbccddeeff"
}
```

#### Update Device
```
PUT /api/v1/api/lorawan/devices/<device_eui>
Content-Type: application/json

{
  "name": "New Name",
  "description": "Updated description",
  "is_disabled": false
}
```

#### Delete Device
```
DELETE /api/v1/api/lorawan/devices/<device_eui>
```

#### Set Device Keys (OTAA)
```
POST /api/v1/api/lorawan/devices/<device_eui>/keys
Content-Type: application/json

{
  "app_key": "00112233445566778899aabbccddeeff"
}
```

### Gateways

#### List Gateways
```
GET /api/v1/api/lorawan/gateways
GET /api/v1/api/lorawan/gateways?tenant_id=<uuid>&limit=100&offset=0
```

#### Get Gateway
```
GET /api/v1/api/lorawan/gateways/<gateway_id>
```

#### Create Gateway
```
POST /api/v1/api/lorawan/gateways
Content-Type: application/json

{
  "gateway_id": "24e124fffefd378a",
  "name": "Office Gateway",
  "tenant_id": "uuid-of-tenant",
  "description": "Main office rooftop gateway",
  "latitude": -26.2041,
  "longitude": 28.0473,
  "altitude": 1500
}
```

#### Update Gateway
```
PUT /api/v1/api/lorawan/gateways/<gateway_id>
Content-Type: application/json

{
  "name": "New Name",
  "description": "Updated description",
  "latitude": -26.2050,
  "longitude": 28.0480,
  "altitude": 1510
}
```

#### Delete Gateway
```
DELETE /api/v1/api/lorawan/gateways/<gateway_id>
```

## Files Structure

```
app/
├── services/
│   └── chirpstack_service.py    # ChirpStack API client
├── routes/v1/
│   └── lorawan.py               # API routes and page routes
└── templates/lorawan/
    ├── index.html               # Main LoRaWAN dashboard
    ├── gateways.html            # Gateway management page
    └── devices.html             # Device management page
```

## Service Layer (`chirpstack_service.py`)

The ChirpStack service provides a clean interface for all ChirpStack API operations:

### Connection
- `test_connection()` - Verify API connectivity

### Applications & Profiles
- `list_applications()` - Get all applications
- `list_device_profiles()` - Get all device profiles
- `list_tenants()` - Get all tenants

### Device Management
- `create_device()` - Register a new device
- `get_device()` - Get device details
- `get_device_with_status()` - Get device with activation status
- `list_devices()` - List all devices
- `update_device()` - Update device properties
- `delete_device()` - Remove a device
- `set_device_keys()` - Set OTAA keys

### Gateway Management
- `create_gateway()` - Register a new gateway
- `get_gateway()` - Get gateway details
- `list_gateways()` - List all gateways
- `update_gateway()` - Update gateway properties
- `delete_gateway()` - Remove a gateway

### Downlink Commands
- `send_downlink()` - Queue a downlink message to a device

## Meter Integration

### Device EUI Field

Every meter in Quantify has an optional `device_eui` field that links it to ChirpStack:

- **16 hexadecimal characters** (LoRaWAN EUI-64 format)
- **Unique constraint** - No two meters can have the same Device EUI
- **Validation** - Enforced on create and update operations

### Creating a Meter with LoRaWAN

When creating a meter through the Quantify UI:

1. Enter the **Device EUI** from the meter's label or documentation
2. The meter is created in Quantify's database
3. (Future) Optionally auto-provision in ChirpStack

### Relay Control via LoRaWAN

For meters with relay control (e.g., Eastron SDM320C via Milesight UC100):

```python
from app.services.chirpstack_service import send_downlink

# Disconnect relay (turn off power)
send_downlink(
    device_eui="device_eui_here",
    data="11010001000100020006000100",  # Modbus command
    f_port=85,
    confirmed=True
)

# Reconnect relay (turn on power)
send_downlink(
    device_eui="device_eui_here",
    data="11010001000100020006000000",  # Modbus command
    f_port=85,
    confirmed=True
)
```

## Permissions

LoRaWAN management uses existing meter permissions:

| Permission | Access |
|------------|--------|
| `meters.view` | View devices, gateways, connection status |
| `meters.create` | Add new devices and gateways |
| `meters.edit` | Update devices and gateways, set keys |
| `meters.delete` | Delete devices and gateways |

## Audit Logging

All LoRaWAN operations are logged for audit purposes:

- `lorawan.device.create` - Device created
- `lorawan.device.update` - Device updated
- `lorawan.device.delete` - Device deleted
- `lorawan.device.set_keys` - OTAA keys set
- `lorawan.gateway.create` - Gateway created
- `lorawan.gateway.update` - Gateway updated
- `lorawan.gateway.delete` - Gateway deleted

## Troubleshooting

### Connection Failed
1. Verify `CHIRPSTACK_API_URL` is correct
2. Check if ChirpStack server is running
3. Ensure port 8090 is accessible (not 8080 which is gRPC)
4. Verify API key is valid and not expired

### Device Not Joining
1. Verify Device EUI matches the physical device
2. Check Application Key is correct (32 hex characters)
3. Ensure device is within gateway range
4. Check device profile matches device capabilities

### Gateway Offline
1. Check gateway power and network connectivity
2. Verify gateway ID matches the physical gateway
3. Check gateway is configured to connect to your ChirpStack server

### Commands Not Received
1. LoRaWAN Class A devices only receive during brief windows after uplinks
2. Ensure device has recent uplink activity
3. Check command was queued in ChirpStack (not immediately delivered)

## Future Enhancements

- [ ] Auto-provision devices in ChirpStack when creating meters
- [ ] Sync device status from ChirpStack to Quantify
- [ ] Device activation status monitoring
- [ ] Gateway metrics and statistics display
- [ ] Bulk device import/export
- [ ] Device profile management from Quantify UI
- [ ] Real-time device event streaming

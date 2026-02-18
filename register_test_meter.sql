-- Register Test LoRaWAN Meter
-- Device: Milesight EM300-DI (24e124136f215917)
-- Run this after applying the database migration

-- Check if meter already exists
SELECT serial_number, device_eui, meter_type
FROM meters
WHERE device_eui = '24e124136f215917';

-- If not exists, insert the meter
INSERT INTO meters (
    serial_number,
    meter_type,
    manufacturer,
    model,
    device_eui,
    lorawan_device_type,
    communication_type,
    communication_status,
    is_prepaid,
    is_active,
    created_at,
    updated_at
) VALUES (
    '24e124136f215917',     -- Device EUI as serial number
    'electricity',           -- Meter type (electricity for pulse counter)
    'Milesight',            -- Manufacturer
    'EM300-DI',             -- Model
    '24e124136f215917',     -- Device EUI
    'milesight_em300',      -- LoRaWAN device type
    'cellular',             -- Communication type
    'offline',              -- Status (will update to 'online' on first reading)
    true,                   -- Prepaid enabled
    true,                   -- Active
    NOW(),                  -- Created timestamp
    NOW()                   -- Updated timestamp
)
ON CONFLICT (serial_number) DO UPDATE
SET
    device_eui = EXCLUDED.device_eui,
    lorawan_device_type = EXCLUDED.lorawan_device_type,
    updated_at = NOW();

-- Verify the meter was created
SELECT id, serial_number, device_eui, meter_type, lorawan_device_type, is_active
FROM meters
WHERE device_eui = '24e124136f215917';

-- Show summary
SELECT
    COUNT(*) as total_meters,
    COUNT(device_eui) as lorawan_meters
FROM meters;

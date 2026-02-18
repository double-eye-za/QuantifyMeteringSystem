# Meter Device Capabilities Matrix

**Purpose:** Document what data each meter type/device combination actually provides to ensure the UI displays appropriate information.

---

## Supported Meter Types

Based on `app/models/meter.py` constraints:
- `electricity` - Electricity consumption meters
- `water` - Cold water meters
- `hot_water` - Hot water meters (treated as water type)
- `solar` - Solar generation meters
- `bulk_electricity` - Bulk/shared electricity meters
- `bulk_water` - Bulk/shared water meters

---

## Device Types & Capabilities

### 1. Milesight EM300-DI (Pulse Counter)

**LoRaWAN Device Type:** `milesight_em300`

**Suitable For:**
- Electricity meters (with S0 pulse output)
- Water meters (with pulse output)
- Gas meters (with pulse output)
- Any meter with dry contact pulse output

**Data Provided:**
- ✅ Pulse count (cumulative)
- ✅ Battery level (%)
- ✅ Temperature (°C) - internal sensor
- ✅ Humidity (%) - internal sensor
- ✅ RSSI (signal strength)
- ✅ SNR (signal quality)

**Data NOT Provided:**
- ❌ Voltage
- ❌ Current
- ❌ Power (kW)
- ❌ Power factor
- ❌ Frequency
- ❌ Flow rate (calculated externally from pulse rate)

**Conversion:**
- Pulse count → kWh (electricity): Divide by pulse factor (typically 1000 pulses/kWh)
- Pulse count → m³ (water): Divide by pulse factor (typically 1-10 pulses/liter)

**Current Usage:**
- Meter ID 1: `24e124136f215917`
- Type: `electricity`
- Reading: 655.37 kWh (655,370 pulses ÷ 1000)

---

### 2. Axioma Qalcosonic W1 (Ultrasonic Water Meter)

**LoRaWAN Device Type:** `qalcosonic_w1`

**Suitable For:**
- Water meters (cold water)
- Hot water meters

**Data Provided:**
- ✅ Total volume (m³) - direct measurement
- ✅ Flow rate (L/h or m³/h) - real-time flow
- ✅ Battery level (%)
- ✅ Leak detection flags
- ✅ Temperature (optional, depending on model)
- ✅ RSSI/SNR

**Data NOT Provided:**
- ❌ Voltage
- ❌ Current
- ❌ Power
- ❌ Pulse count (uses ultrasonic, not pulses)

**Current Usage:**
- Not yet deployed (pending AppKey configuration)

---

## UI Display Strategy by Meter Type

### Electricity Meters (`electricity`)

**With EM300-DI (Pulse Counter):**

**Show:**
- Total Consumption (kWh) - from pulse_count ÷ 1000
- Today's Usage (kWh) - calculated from max-min today
- Cost (if unit assigned with rate table)
- Battery Level
- Signal Quality (RSSI/SNR)
- Last Reading Time
- Consumption Chart (historical trend)

**Hide/Don't Show:**
- Current Load (kW) - not available
- Voltage - not available
- Current - not available
- Power Factor - not available

**With Direct Power Meter (future):**
- Would show: Voltage, Current, Power, Power Factor, Frequency

---

### Water Meters (`water`)

**With EM300-DI (Pulse Counter):**

**Show:**
- Total Volume (m³) - from pulse_count ÷ conversion_factor
- Today's Usage (m³) - calculated from max-min today
- Cost (if unit assigned with water rate table)
- Battery Level
- Signal Quality
- Last Reading Time
- Consumption Chart

**Hide/Don't Show:**
- Flow Rate - not available from pulse counter
- Pressure - not available
- Voltage/Current/Power - not applicable

**With Qalcosonic W1 (Ultrasonic):**

**Show:**
- Total Volume (m³) - direct measurement
- Current Flow Rate (L/h) - real-time measurement
- Today's Usage (m³)
- Cost (if assigned)
- Battery Level
- Leak Detection Status ⚠️
- Temperature (if available)
- Consumption Chart
- Flow Rate Chart (over time)

---

### Hot Water Meters (`hot_water`)

**Same as Water Meters, but:**
- Temperature reading is important (if available)
- May show "Hot Water" label/icon
- Cost calculation uses hot water rate table

---

### Solar Meters (`solar`)

**With EM300-DI (Pulse Counter):**

**Show:**
- Total Generation (kWh) - cumulative
- Today's Generation (kWh)
- Generation Chart
- Battery Level
- Signal Quality
- Revenue (if feed-in tariff configured)

**Different from Consumption:**
- Shows "Generation" instead of "Consumption"
- Positive values (generating, not consuming)
- Different icon/color scheme (green/positive)

---

### Bulk Meters (`bulk_electricity`, `bulk_water`)

**Similar to individual meters, but:**
- Associated with Estate, not Unit
- Aggregate consumption for entire building/complex
- Different UI section (estate-level view)
- May have sub-metering calculations

---

## Meter Details Page - Dynamic Content Strategy

### Approach: **Capability-Based Display**

Instead of showing all fields with "Not Available", show only what the device CAN measure.

### Implementation Pattern:

```python
# Backend determines meter capabilities
meter_capabilities = {
    'shows_power': False,  # EM300-DI doesn't have this
    'shows_voltage': False,
    'shows_flow_rate': False,
    'shows_total_only': True,  # Only cumulative reading
    'shows_temperature': True,  # Environmental sensor
    'shows_battery': True,
    'unit_type': 'kWh',  # or 'm³' for water
    'measurement_type': 'pulse',  # or 'ultrasonic', 'direct'
}

# Pass to template
return render_template(
    'meters/meter-details.html',
    meter=meter,
    capabilities=meter_capabilities,
    ...
)
```

### Template Pattern:

```html
<!-- Only show if device supports it -->
{% if capabilities.shows_power %}
<div class="stat-card">
  <h3>Current Load</h3>
  <p id="current-load">{{ latest_power }} kW</p>
</div>
{% endif %}

{% if capabilities.shows_voltage %}
<div class="stat-card">
  <h3>Voltage</h3>
  <p id="voltage">{{ latest_voltage }} V</p>
</div>
{% endif %}

<!-- Always show for all devices -->
<div class="stat-card">
  <h3>Today's {{ 'Generation' if meter_type == 'solar' else 'Usage' }}</h3>
  <p id="today-usage">{{ today_consumption }} {{ capabilities.unit_type }}</p>
</div>

{% if capabilities.shows_temperature %}
<div class="stat-card">
  <h3>Temperature</h3>
  <p>{{ latest_temperature }}°C</p>
  <small>Device sensor</small>
</div>
{% endif %}
```

---

## Database Schema Recommendations

### Current Schema: ✅ Good
The `meter_readings` table is generic enough to support all meter types:
- `reading_value` - Universal (kWh, m³, etc.)
- `pulse_count` - For pulse-based devices
- `temperature` - For devices with temp sensors
- `humidity` - For devices with humidity sensors
- `battery_level` - For battery-powered devices
- `rssi`, `snr` - For wireless devices

### Optional Additions (if needed later):
```sql
-- For devices that measure flow
ALTER TABLE meter_readings
ADD COLUMN flow_rate NUMERIC(10, 3);  -- L/h or m³/h

-- For devices that measure power
ADD COLUMN power_kw NUMERIC(10, 3);
ADD COLUMN voltage NUMERIC(10, 2);
ADD COLUMN current_amps NUMERIC(10, 3);
```

**But:** Only add if you actually deploy devices that provide this data!

---

## API Response Strategy

### `/api/v1/meters/<meter_id>/realtime-stats`

**Should return:**
```json
{
  "meter_id": "24e124136f215917",
  "meter_type": "electricity",
  "device_type": "milesight_em300",
  "capabilities": {
    "measures_power": false,
    "measures_voltage": false,
    "measures_flow": false,
    "measures_temperature": true,
    "unit": "kWh"
  },
  "latest_reading": {
    "timestamp": "2025-11-04T09:37:53",
    "value": 655.37,
    "pulse_count": 655370,
    "temperature": 24.0,
    "humidity": 49.5,
    "battery_level": 100,
    "rssi": -66,
    "snr": 0.0
  },
  "today": {
    "consumption": 0.0,  // No usage today (constant reading)
    "cost": null,  // No unit assigned
    "unit": "kWh"
  },
  "communication": {
    "last_communication": "2025-11-04T09:37:53",
    "status": "online"
  }
}
```

**Frontend then:**
- Checks `capabilities` object
- Only renders UI elements for available capabilities
- Shows appropriate messaging for unavailable features

---

## Cost Calculation Logic

### Prerequisite: Meter must be assigned to a unit

```python
# Check if meter is assigned
unit = Unit.query.filter(
    (Unit.electricity_meter_id == meter.id) |
    (Unit.water_meter_id == meter.id) |
    (Unit.hot_water_meter_id == meter.id) |
    (Unit.solar_meter_id == meter.id)
).first()

if not unit:
    cost = None  # Can't calculate without unit assignment
    cost_message = "Meter not assigned to a unit"
else:
    # Get rate table
    if meter.meter_type == 'electricity':
        rate_table_id = unit.electricity_rate_table_id
    elif meter.meter_type == 'water':
        rate_table_id = unit.water_rate_table_id
    elif meter.meter_type == 'hot_water':
        rate_table_id = unit.hot_water_rate_table_id
    # ... etc

    if not rate_table_id:
        cost = None
        cost_message = "No rate table assigned"
    else:
        # Calculate using rate table tiers
        cost = calculate_cost_from_rate_table(consumption, rate_table_id)
```

---

## Proposed Implementation Plan

### Phase 1: Core Functionality (All Meter Types)
1. ✅ Display total reading (kWh or m³)
2. ✅ Display today's consumption (calculated)
3. ✅ Display battery, temperature, signal quality
4. ✅ Display consumption chart
5. ✅ Display last update time

### Phase 2: Capability-Based UI
1. Create `get_meter_capabilities()` function
2. Pass capabilities to template
3. Conditionally render UI elements
4. Show appropriate labels (Generation vs Consumption)

### Phase 3: Cost Calculation
1. Check for unit assignment
2. Check for rate table
3. Calculate cost with tiered rates
4. Show cost or appropriate message

### Phase 4: Device-Specific Features
1. For Qalcosonic W1: Show flow rate
2. For future power meters: Show voltage/current/power
3. For solar: Show generation instead of consumption

---

## Testing Matrix

| Meter Type | Device Type | Total Reading | Flow/Power | Temperature | Cost | Chart |
|------------|-------------|---------------|------------|-------------|------|-------|
| Electricity | EM300-DI | ✅ kWh | ❌ | ✅ | 🟡* | ✅ |
| Water | EM300-DI | ✅ m³ | ❌ | ✅ | 🟡* | ✅ |
| Water | Qalcosonic W1 | ✅ m³ | ✅ L/h | 🟡** | 🟡* | ✅ |
| Hot Water | Qalcosonic W1 | ✅ m³ | ✅ L/h | ✅ | 🟡* | ✅ |
| Solar | EM300-DI | ✅ kWh | ❌ | ✅ | 🟡*** | ✅ |

*Requires unit assignment + rate table
**Depends on Qalcosonic model
***Revenue calculation (feed-in tariff)

---

## Questions to Answer Before Implementation

1. **Do you plan to deploy actual power meters** (that measure voltage/current/power)?
   - If NO: Don't build voltage/power UI at all
   - If YES: Build but hide based on capabilities

2. **Will all meters be assigned to units?**
   - If NO: Cost calculation is optional/conditional
   - If YES: We can assume cost is always calculable

3. **Priority order for implementation?**
   - Electricity meters first?
   - Water meters?
   - All types simultaneously?

4. **Should bulk meters have different UI?**
   - Same details page or separate view?
   - Different permissions/access?

---

**Next Step:** Please answer the questions above and share the query results, then I'll create a precise implementation plan based on your actual needs!

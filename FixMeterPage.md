# Fix Meter Details Page - Replace Hardcoded Data with Real Data

## Current Status

The meter details page (`/meters/<meter_id>/details`) currently displays a mix of real and fake data:

### ✅ Real Data (Currently Working)
- **Meter Information Section**: Serial number, type, status, firmware, installation date
- **Location Section**: Estate, Unit, Tenant (from database)
- **Current Balance**: Wallet balance (from database)
- **Recent Readings Table**: Last 20 readings from `meter_readings` table

### ❌ Hardcoded/Fake Data (Needs Fixing)

#### 1. Location Data (Lines 94-105 in meter-details.html)
- **Concentrator**: `DC450-WC-01` (hardcoded)
- **GPS Coordinates**: `-26.195, 28.034` (hardcoded)

#### 2. Real-time Data Cards (Lines 167-209 in meter-details.html)
- **Current Load**: `2.4 kW` (hardcoded)
- **Updated Time**: `14:32:45` (hardcoded)
- **Voltage**: `230 V` (hardcoded)
- **Today's Usage**: `12.5 kWh` (hardcoded)
- **Cost**: `R 20.83` (hardcoded)

#### 3. 24-Hour Consumption Chart (meter-details.js lines 6-10)
- **Chart Labels**: `["00:00", "04:00", "08:00", "12:00", "16:00", "20:00", "24:00"]` (hardcoded intervals)
- **Chart Data**: `[0.8, 0.6, 1.2, 2.4, 2.8, 3.2, 2.1]` (hardcoded fake consumption data)

---

## Required Changes

### 1. Database Schema Changes

#### Option A: Add fields to existing `meters` table
Add these columns to store LoRaWAN/device metadata:
```sql
ALTER TABLE meters
ADD COLUMN concentrator_id VARCHAR(50),
ADD COLUMN gps_latitude NUMERIC(10, 6),
ADD COLUMN gps_longitude NUMERIC(10, 6);
```

#### Option B: Create a new `meter_metadata` table (Recommended)
```sql
CREATE TABLE meter_metadata (
    id SERIAL PRIMARY KEY,
    meter_id INTEGER NOT NULL REFERENCES meters(id) ON DELETE CASCADE,
    concentrator_id VARCHAR(50),
    gps_latitude NUMERIC(10, 6),
    gps_longitude NUMERIC(10, 6),
    network_server VARCHAR(100),
    last_seen TIMESTAMP,
    rssi INTEGER,
    snr NUMERIC(5, 2),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(meter_id)
);
```

#### Add columns to `meter_readings` table (if not already present)
Check if these columns exist, add if missing:
```sql
-- Check current schema
\d meter_readings

-- Add missing columns
ALTER TABLE meter_readings
ADD COLUMN IF NOT EXISTS voltage NUMERIC(10, 2),
ADD COLUMN IF NOT EXISTS current_amps NUMERIC(10, 3),
ADD COLUMN IF NOT EXISTS power_kw NUMERIC(10, 3),
ADD COLUMN IF NOT EXISTS power_factor NUMERIC(3, 2),
ADD COLUMN IF NOT EXISTS frequency_hz NUMERIC(5, 2);
```

---

### 2. Backend Changes

#### A. Create New API Endpoint: Get Real-time Stats

**File**: `app/routes/v1/meters.py`

**Location**: Add after line 296

**New Endpoint**:
```python
@api_v1.route("/meters/<meter_id>/realtime-stats", methods=["GET"])
@login_required
@requires_permission("meters.view")
def get_meter_realtime_stats(meter_id: str):
    """
    Get real-time statistics for a meter

    Returns:
    - Latest reading with voltage, current, power
    - Today's total consumption
    - Today's cost
    - Last communication time
    """
    # Find meter by serial number or ID
    meter = Meter.query.filter_by(serial_number=meter_id).first()
    if meter is None and meter_id.isdigit():
        meter = svc_get_meter_by_id(int(meter_id))

    if not meter:
        return jsonify({"error": "Meter not found"}), 404

    # Get latest reading
    latest_reading = MeterReading.query.filter_by(meter_id=meter.id)\
        .order_by(MeterReading.reading_date.desc())\
        .first()

    # Get today's consumption (sum of all readings today)
    from datetime import datetime, time
    today_start = datetime.combine(datetime.today(), time.min)
    today_readings = MeterReading.query.filter(
        MeterReading.meter_id == meter.id,
        MeterReading.reading_date >= today_start
    ).all()

    # Calculate today's consumption
    if today_readings:
        today_consumption = max([r.reading_value for r in today_readings]) - min([r.reading_value for r in today_readings])
    else:
        today_consumption = 0.0

    # Get unit and rate table for cost calculation
    unit = Unit.query.filter(
        (Unit.electricity_meter_id == meter.id) |
        (Unit.water_meter_id == meter.id) |
        (Unit.solar_meter_id == meter.id)
    ).first()

    # Calculate cost (simplified - you may need to use rate table logic)
    cost_per_kwh = 1.67  # Default ZAR per kWh - should come from rate table
    if unit:
        if meter.meter_type == "electricity" and unit.electricity_rate_table_id:
            rate_table = RateTable.query.get(unit.electricity_rate_table_id)
            if rate_table and rate_table.tiers:
                # Use first tier rate as base (or implement proper tier calculation)
                cost_per_kwh = float(rate_table.tiers[0].rate)
        elif meter.meter_type == "water" and unit.water_rate_table_id:
            rate_table = RateTable.query.get(unit.water_rate_table_id)
            if rate_table and rate_table.tiers:
                cost_per_kwh = float(rate_table.tiers[0].rate)

    today_cost = today_consumption * cost_per_kwh

    # Build response
    return jsonify({
        "latest_reading": {
            "timestamp": latest_reading.reading_date.isoformat() if latest_reading else None,
            "value": float(latest_reading.reading_value) if latest_reading else None,
            "voltage": float(latest_reading.voltage) if latest_reading and latest_reading.voltage else None,
            "current": float(latest_reading.current_amps) if latest_reading and hasattr(latest_reading, 'current_amps') and latest_reading.current_amps else None,
            "power_kw": float(latest_reading.power_kw) if latest_reading and hasattr(latest_reading, 'power_kw') and latest_reading.power_kw else None,
        },
        "today": {
            "consumption": float(today_consumption),
            "cost": float(today_cost),
            "unit": "kWh" if meter.meter_type in ["electricity", "solar"] else "m³"
        },
        "communication": {
            "last_communication": meter.last_communication.isoformat() if meter.last_communication else None,
            "status": meter.communication_status or "unknown"
        }
    })
```

#### B. Create New API Endpoint: Get Chart Data

**File**: `app/routes/v1/meters.py`

**Location**: Add after the realtime-stats endpoint

**New Endpoint**:
```python
@api_v1.route("/meters/<meter_id>/chart-data", methods=["GET"])
@login_required
@requires_permission("meters.view")
def get_meter_chart_data(meter_id: str):
    """
    Get consumption chart data for different time periods

    Query params:
    - period: hour|day|week|month (default: day)
    """
    from datetime import datetime, timedelta
    from sqlalchemy import func

    period = request.args.get('period', 'day')

    # Find meter
    meter = Meter.query.filter_by(serial_number=meter_id).first()
    if meter is None and meter_id.isdigit():
        meter = svc_get_meter_by_id(int(meter_id))

    if not meter:
        return jsonify({"error": "Meter not found"}), 404

    now = datetime.now()

    if period == 'hour':
        # Last 60 minutes, 1 reading per minute
        start_time = now - timedelta(hours=1)
        interval_minutes = 5  # Group by 5-minute intervals

        readings = db.session.query(
            func.date_trunc('minute', MeterReading.reading_date).label('interval'),
            func.avg(MeterReading.reading_value).label('avg_value')
        ).filter(
            MeterReading.meter_id == meter.id,
            MeterReading.reading_date >= start_time
        ).group_by('interval').order_by('interval').all()

        labels = [r.interval.strftime('%H:%M') for r in readings]
        data = [float(r.avg_value) for r in readings]

    elif period == 'day':
        # Last 24 hours, 1 reading per hour
        start_time = now - timedelta(days=1)

        readings = db.session.query(
            func.date_trunc('hour', MeterReading.reading_date).label('interval'),
            func.max(MeterReading.reading_value).label('max_value'),
            func.min(MeterReading.reading_value).label('min_value')
        ).filter(
            MeterReading.meter_id == meter.id,
            MeterReading.reading_date >= start_time
        ).group_by('interval').order_by('interval').all()

        labels = [r.interval.strftime('%H:%M') for r in readings]
        # Calculate consumption per hour (max - min in that hour)
        data = [float(r.max_value - r.min_value) if r.max_value and r.min_value else 0 for r in readings]

    elif period == 'week':
        # Last 7 days, 1 reading per day
        start_time = now - timedelta(days=7)

        readings = db.session.query(
            func.date_trunc('day', MeterReading.reading_date).label('interval'),
            func.max(MeterReading.reading_value).label('max_value'),
            func.min(MeterReading.reading_value).label('min_value')
        ).filter(
            MeterReading.meter_id == meter.id,
            MeterReading.reading_date >= start_time
        ).group_by('interval').order_by('interval').all()

        labels = [r.interval.strftime('%a %d') for r in readings]
        data = [float(r.max_value - r.min_value) if r.max_value and r.min_value else 0 for r in readings]

    elif period == 'month':
        # Last 30 days, 1 reading per day
        start_time = now - timedelta(days=30)

        readings = db.session.query(
            func.date_trunc('day', MeterReading.reading_date).label('interval'),
            func.max(MeterReading.reading_value).label('max_value'),
            func.min(MeterReading.reading_value).label('min_value')
        ).filter(
            MeterReading.meter_id == meter.id,
            MeterReading.reading_date >= start_time
        ).group_by('interval').order_by('interval').all()

        labels = [r.interval.strftime('%d %b') for r in readings]
        data = [float(r.max_value - r.min_value) if r.max_value and r.min_value else 0 for r in readings]
    else:
        return jsonify({"error": "Invalid period"}), 400

    return jsonify({
        "labels": labels,
        "data": data,
        "period": period,
        "unit": "kWh" if meter.meter_type in ["electricity", "solar"] else "m³"
    })
```

#### C. Update the meter_details_page endpoint

**File**: `app/routes/v1/meters.py`

**Location**: Lines 221-295

**Changes Needed**:
Add GPS and concentrator data to the response:

```python
# After line 247 (after wallet = ...)
# Get meter metadata (if table exists)
# For now, we can add placeholder fields or populate from device_eui mapping
concentrator_id = "Unknown"  # TODO: Get from meter_metadata table
gps_coords = None  # TODO: Get from meter_metadata table

# ... existing code ...

# Around line 278, update the return template to include:
return render_template(
    "meters/meter-details.html",
    meter_id=meter.serial_number,
    meter=meter_dict,
    unit={
        "unit_number": unit.unit_number,
        "estate_name": estate.name if estate else None,
        "resident_name": (
            f"{resident.first_name} {resident.last_name}" if resident else None
        ),
    }
    if unit
    else None,
    wallet=wallet.to_dict() if wallet else None,
    balance_value=balance_value,
    credit_status=credit_status,
    recent_readings=recent_readings,
    concentrator_id=concentrator_id,  # NEW
    gps_latitude=gps_coords[0] if gps_coords else None,  # NEW
    gps_longitude=gps_coords[1] if gps_coords else None,  # NEW
)
```

---

### 3. Frontend Changes

#### A. Update HTML Template: meter-details.html

**File**: `app/templates/meters/meter-details.html`

**Changes**:

##### 1. Location Section (Lines 94-105)
Replace hardcoded values with template variables:

```html
<div class="flex justify-between">
  <span class="text-sm text-gray-600 dark:text-gray-400">Concentrator</span>
  <span class="text-sm font-medium text-gray-900 dark:text-white"
    >{{ concentrator_id or '—' }}</span
  >
</div>
<div class="flex justify-between">
  <span class="text-sm text-gray-600 dark:text-gray-400">GPS</span>
  <span class="text-sm font-medium text-gray-900 dark:text-white"
    >{% if gps_latitude and gps_longitude %}{{ gps_latitude }}, {{ gps_longitude }}{% else %}—{% endif %}</span
  >
</div>
```

##### 2. Real-time Data Cards (Lines 167-209)
Replace hardcoded values with dynamic data loaded via JavaScript:

```html
<div class="bg-gray-50 dark:bg-gray-700 rounded-lg p-4">
  <div class="flex items-center justify-between mb-2">
    <span class="text-sm text-gray-600 dark:text-gray-400">Current Load</span>
    <i class="fas fa-bolt text-yellow-500"></i>
  </div>
  <div class="text-2xl font-bold text-gray-900 dark:text-white" id="current-load">
    —
  </div>
  <div class="text-xs text-gray-500 dark:text-gray-400 mt-1" id="load-updated">
    Loading...
  </div>
</div>

<div class="bg-gray-50 dark:bg-gray-700 rounded-lg p-4">
  <div class="flex items-center justify-between mb-2">
    <span class="text-sm text-gray-600 dark:text-gray-400">Voltage</span>
    <i class="fas fa-plug text-green-500"></i>
  </div>
  <div class="text-2xl font-bold text-gray-900 dark:text-white" id="voltage">
    —
  </div>
  <div class="text-xs text-gray-500 dark:text-gray-400 mt-1" id="voltage-status">
    Loading...
  </div>
</div>

<div class="bg-gray-50 dark:bg-gray-700 rounded-lg p-4">
  <div class="flex items-center justify-between mb-2">
    <span class="text-sm text-gray-600 dark:text-gray-400">Today's Usage</span>
    <i class="fas fa-chart-line text-primary"></i>
  </div>
  <div class="text-2xl font-bold text-gray-900 dark:text-white" id="today-usage">
    —
  </div>
  <div class="text-xs text-gray-500 dark:text-gray-400 mt-1" id="today-cost">
    Loading...
  </div>
</div>
```

##### 3. Add meter_id to JavaScript scope
Add before the closing `{% endblock %}` (around line 321):

```html
{% endblock %}

{% block extra_js %}
<script src="https://cdn.jsdelivr.net/npm/chart.js@3.9.1"></script>
<script>
  // Make meter_id available to JavaScript
  window.METER_ID = "{{ meter_id }}";
</script>
<script src="/static/js/meters/meter-details.js"></script>
{% endblock %}
```

#### B. Update JavaScript: meter-details.js

**File**: `app/static/js/meters/meter-details.js`

**Replace entire contents with**:

```javascript
// Global chart instance
let consumptionChart = null;
let currentPeriod = 'day';

// Fetch and display real-time stats
async function fetchRealtimeStats() {
  try {
    const response = await fetch(`/api/v1/meters/${window.METER_ID}/realtime-stats`);
    if (!response.ok) throw new Error('Failed to fetch stats');

    const data = await response.json();

    // Update current load
    const powerKw = data.latest_reading.power_kw;
    if (powerKw !== null && powerKw !== undefined) {
      document.getElementById('current-load').textContent = `${powerKw.toFixed(1)} kW`;
    } else {
      document.getElementById('current-load').textContent = '—';
    }

    // Update timestamp
    if (data.latest_reading.timestamp) {
      const timestamp = new Date(data.latest_reading.timestamp);
      document.getElementById('load-updated').textContent = `Updated: ${timestamp.toLocaleTimeString()}`;
    } else {
      document.getElementById('load-updated').textContent = 'No recent data';
    }

    // Update voltage
    const voltage = data.latest_reading.voltage;
    if (voltage !== null && voltage !== undefined) {
      document.getElementById('voltage').textContent = `${voltage.toFixed(0)} V`;

      // Voltage status based on range (assuming 230V ±10%)
      if (voltage >= 207 && voltage <= 253) {
        document.getElementById('voltage-status').textContent = 'Normal range';
      } else {
        document.getElementById('voltage-status').textContent = 'Out of range';
      }
    } else {
      document.getElementById('voltage').textContent = '—';
      document.getElementById('voltage-status').textContent = 'No data';
    }

    // Update today's usage
    const todayUsage = data.today.consumption;
    const todayCost = data.today.cost;
    const unit = data.today.unit;

    if (todayUsage !== null && todayUsage !== undefined) {
      document.getElementById('today-usage').textContent = `${todayUsage.toFixed(1)} ${unit}`;
      document.getElementById('today-cost').textContent = `Cost: R ${todayCost.toFixed(2)}`;
    } else {
      document.getElementById('today-usage').textContent = '—';
      document.getElementById('today-cost').textContent = 'No data';
    }

  } catch (error) {
    console.error('Error fetching realtime stats:', error);
    document.getElementById('current-load').textContent = 'Error';
    document.getElementById('voltage').textContent = 'Error';
    document.getElementById('today-usage').textContent = 'Error';
  }
}

// Fetch and display chart data
async function fetchChartData(period = 'day') {
  try {
    const response = await fetch(`/api/v1/meters/${window.METER_ID}/chart-data?period=${period}`);
    if (!response.ok) throw new Error('Failed to fetch chart data');

    const data = await response.json();

    // Update or create chart
    updateChart(data.labels, data.data, data.unit);
    currentPeriod = period;

  } catch (error) {
    console.error('Error fetching chart data:', error);
  }
}

// Update the consumption chart
function updateChart(labels, data, unit) {
  const ctx = document.getElementById("consumptionChart").getContext("2d");

  // Destroy existing chart if it exists
  if (consumptionChart) {
    consumptionChart.destroy();
  }

  // Create new chart
  consumptionChart = new Chart(ctx, {
    type: "line",
    data: {
      labels: labels,
      datasets: [
        {
          label: `Consumption (${unit})`,
          data: data,
          borderColor: "#1A73E8",
          backgroundColor: "rgba(26, 115, 232, 0.1)",
          tension: 0.4,
          fill: true,
        },
      ],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: { display: false },
      },
      scales: {
        y: {
          beginAtZero: true,
          ticks: {
            callback: function (value) {
              return value + " " + unit;
            },
          },
        },
      },
    },
  });
}

// Add event listeners for period buttons
document.addEventListener('DOMContentLoaded', function() {
  // Initial load
  fetchRealtimeStats();
  fetchChartData('day');

  // Refresh realtime stats every 30 seconds
  setInterval(fetchRealtimeStats, 30000);

  // Add click handlers for period buttons
  const periodButtons = document.querySelectorAll('[data-period]');
  periodButtons.forEach(button => {
    button.addEventListener('click', function() {
      const period = this.getAttribute('data-period');

      // Update active state
      periodButtons.forEach(btn => {
        btn.classList.remove('bg-primary', 'text-white');
        btn.classList.add('bg-white', 'dark:bg-gray-600');
      });
      this.classList.remove('bg-white', 'dark:bg-gray-600');
      this.classList.add('bg-primary', 'text-white');

      // Fetch new data
      fetchChartData(period);
    });
  });
});
```

##### Update period buttons in HTML (Lines 217-236)
Add `data-period` attributes to buttons:

```html
<div class="flex space-x-2">
  <button
    data-period="hour"
    class="px-3 py-1 text-xs bg-white dark:bg-gray-600 rounded-lg"
  >
    Hour
  </button>
  <button
    data-period="day"
    class="px-3 py-1 text-xs bg-primary text-white rounded-lg"
  >
    Day
  </button>
  <button
    data-period="week"
    class="px-3 py-1 text-xs bg-white dark:bg-gray-600 rounded-lg"
  >
    Week
  </button>
  <button
    data-period="month"
    class="px-3 py-1 text-xs bg-white dark:bg-gray-600 rounded-lg"
  >
    Month
  </button>
</div>
```

---

### 4. Migration Steps

#### Create Migration for meter_metadata table

```bash
cd /opt/QuantifyMeteringSystem
source venv/bin/activate
export FLASK_APP=application.py
flask db migrate -m "Add meter_metadata table for concentrator and GPS data"
flask db upgrade
```

#### Check if meter_readings has voltage/power columns

```sql
-- On server
psql -U admin -h localhost -d quantify

-- Check schema
\d meter_readings

-- If columns are missing, add them
ALTER TABLE meter_readings
ADD COLUMN IF NOT EXISTS voltage NUMERIC(10, 2),
ADD COLUMN IF NOT EXISTS current_amps NUMERIC(10, 3),
ADD COLUMN IF NOT EXISTS power_kw NUMERIC(10, 3),
ADD COLUMN IF NOT EXISTS power_factor NUMERIC(3, 2),
ADD COLUMN IF NOT EXISTS frequency_hz NUMERIC(5, 2);
```

---

### 5. Testing Checklist

After implementing changes:

- [ ] `/api/v1/meters/<meter_id>/realtime-stats` returns correct data
- [ ] `/api/v1/meters/<meter_id>/chart-data?period=day` returns correct data
- [ ] `/api/v1/meters/<meter_id>/chart-data?period=hour` returns correct data
- [ ] `/api/v1/meters/<meter_id>/chart-data?period=week` returns correct data
- [ ] `/api/v1/meters/<meter_id>/chart-data?period=month` returns correct data
- [ ] Meter details page shows real "Current Load" from latest reading
- [ ] Meter details page shows real "Voltage" from latest reading
- [ ] Meter details page shows real "Today's Usage" calculated from today's readings
- [ ] Meter details page shows real cost based on rate table
- [ ] Chart updates when clicking Hour/Day/Week/Month buttons
- [ ] Chart shows real data from meter_readings table
- [ ] GPS coordinates display correctly (if available)
- [ ] Concentrator ID displays correctly (if available)
- [ ] Real-time stats refresh every 30 seconds
- [ ] No JavaScript console errors
- [ ] Page works with meters that have no readings (shows "—" or "No data")

---

### 6. Data Population Notes

#### LoRaWAN Metadata
The MQTT listener (`data_collector_app.py`) receives additional metadata in the uplink messages:

- **Device EUI**: Already stored as `device_eui` in meters table
- **Gateway/Concentrator ID**: Available in MQTT payload under `rxInfo[0].gatewayId`
- **GPS**: Available in MQTT payload under `rxInfo[0].location` (if gateway has GPS)
- **RSSI/SNR**: Available in MQTT payload under `rxInfo[0].rssi` and `rxInfo[0].loRaSNR`

**Action Required**: Update `mqtt_listener.py` to extract and store this metadata:

```python
# In handle_uplink function, extract metadata
rx_info = payload.get('rxInfo', [])
if rx_info:
    gateway_id = rx_info[0].get('gatewayId')
    location = rx_info[0].get('location')
    rssi = rx_info[0].get('rssi')
    snr = rx_info[0].get('loRaSNR')

    # Store in meter_metadata table
    # ... implementation needed
```

---

### 7. Implementation Order (Recommended)

1. **Database Changes** (15 min)
   - Create migration for meter_metadata table
   - Add voltage/power columns to meter_readings if missing
   - Run migrations

2. **Backend API - Realtime Stats** (30 min)
   - Create `/realtime-stats` endpoint
   - Test with Postman/curl

3. **Backend API - Chart Data** (45 min)
   - Create `/chart-data` endpoint
   - Test all periods (hour/day/week/month)

4. **Frontend - HTML Updates** (15 min)
   - Update location section template variables
   - Add IDs to real-time data cards
   - Add data-period attributes to buttons
   - Add meter_id to JavaScript scope

5. **Frontend - JavaScript Updates** (30 min)
   - Replace meter-details.js with new dynamic version
   - Test chart rendering
   - Test period switching

6. **Backend - Update Details Endpoint** (15 min)
   - Add GPS/concentrator to meter_details_page response

7. **MQTT Listener Updates** (Optional, 30 min)
   - Extract and store gateway metadata
   - Store voltage/power data from device telemetry

8. **Testing** (30 min)
   - Test all endpoints
   - Test UI interactions
   - Test with no data scenarios
   - Test error handling

**Total Estimated Time**: 3-4 hours

---

## Files to Modify

1. `app/routes/v1/meters.py` - Add 2 new API endpoints, update details endpoint
2. `app/templates/meters/meter-details.html` - Update hardcoded values with dynamic IDs and template variables
3. `app/static/js/meters/meter-details.js` - Complete rewrite to fetch real data
4. `water_meter_module/mqtt_listener.py` - (Optional) Extract and store metadata
5. Database migrations - Create meter_metadata table, add columns

---

## Notes

- The current meter readings table already has data, so we can immediately show real consumption data
- Voltage and power data depends on what the Milesight EM300-DI actually sends via MQTT
- The EM300-DI is a **pulse counter**, so it may NOT send voltage/power data (only pulse counts)
- If voltage/power are not available from the device, those cards should show "Not supported by device" instead of hardcoded values
- Consider adding a device capabilities field to indicate what data each meter type can provide

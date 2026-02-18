# Meter Details Page Fix - Implementation Plan

**Date Created:** November 4, 2025
**Status:** Planning Complete - Ready for Implementation
**Goal:** Replace hardcoded data with real meter readings in the meter details page

---

## 📊 Current State Analysis

### What We Have
- **1 Electricity Meter** operational
  - Device: Milesight EM300-DI (pulse counter)
  - DevEUI: 24e124136f215917
  - Type: `electricity`
  - Device Type: `milesight_em300`

### Database Reality Check ✅
```sql
-- meter_readings table HAS:
- reading_value (655.370 kWh)       ✅
- pulse_count (655,370)             ✅
- temperature (24.00°C)             ✅
- humidity (49.50%)                 ✅
- battery_level (100%)              ✅
- rssi (-66 dBm)                    ✅
- snr (0.00 dB)                     ✅
- reading_date (timestamp)          ✅

-- meter_readings table DOES NOT HAVE:
- voltage                           ❌
- current_amps                      ❌
- power_kw                          ❌
- power_factor                      ❌
- frequency_hz                      ❌

-- Meter NOT assigned to unit:
- No unit assignment                ❌
- No rate table                     ❌
- Cannot calculate cost             ❌
```

### Current Template Issues
**File:** `app/templates/meters/meter-details.html`

**Hardcoded Data (Lines 167-209):**
- Current Load: `2.4 kW` (line 175)
- Voltage: `230 V` (line 188)
- Today's Usage: `12.5 kWh` (line 203)
- Cost: `R 20.83` (line 206)

**Hardcoded Data (Lines 94-105):**
- Concentrator: `DC450-WC-01` (line 98)
- GPS: `-26.195, 28.034` (line 104)

**Hardcoded Chart Data:**
**File:** `app/static/js/meters/meter-details.js`
- Chart data: `[0.8, 0.6, 1.2, 2.4, 2.8, 3.2, 2.1]` (line 10)

---

## 🎯 Implementation Strategy

### Decision: Single Adaptive Template ✅
Keep ONE `meter-details.html` template that adapts based on:
1. **Meter Type** (electricity, water, hot_water, solar)
2. **Device Capabilities** (what the device can actually measure)

### Why Not Separate Templates?
- Easier maintenance (one template vs. 4-5)
- Less code duplication
- Already has meter type awareness (icons, colors)
- Can conditionally show/hide cards based on capabilities

---

## 📋 Implementation Phases

### Phase 1: Backend API Endpoints (Priority: HIGH)

#### Endpoint 1: Real-time Stats
**Route:** `GET /api/v1/meters/<meter_id>/realtime-stats`

**Purpose:** Return current meter statistics

**Response Example:**
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
    "consumption": 0.0,
    "cost": null,
    "unit": "kWh",
    "cost_message": "Meter not assigned to unit"
  },
  "communication": {
    "last_communication": "2025-11-04T09:37:53",
    "status": "online"
  }
}
```

**Implementation Notes:**
- Calculate today's consumption: `MAX(reading_value) - MIN(reading_value)` for today
- Check for unit assignment before calculating cost
- Return null/message if cost cannot be calculated
- Include device capabilities to inform UI what to show

---

#### Endpoint 2: Chart Data
**Route:** `GET /api/v1/meters/<meter_id>/chart-data?period=day`

**Purpose:** Return consumption data for charts

**Query Parameters:**
- `period`: hour | day | week | month (default: day)

**Response Example:**
```json
{
  "labels": ["00:00", "01:00", "02:00", "03:00", ...],
  "data": [0.0, 0.0, 0.0, 0.0, ...],
  "period": "day",
  "unit": "kWh",
  "meter_type": "electricity"
}
```

**Implementation Notes:**
- For electricity: Calculate consumption per interval (max - min)
- Group by hour/day based on period
- Return empty arrays if no data
- Use PostgreSQL `date_trunc()` for grouping

---

### Phase 2: Template Updates (Priority: HIGH)

#### 2.1 Make Real-Time Cards Dynamic

**File:** `app/templates/meters/meter-details.html` (Lines 166-209)

**Current:** 3 hardcoded cards (Current Load, Voltage, Today's Usage)

**New:** Conditional cards based on meter type and capabilities

**For Electricity Meters (EM300-DI):**

**Card 1: Today's Usage**
```html
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

**Card 2: Total Consumption**
```html
<div class="bg-gray-50 dark:bg-gray-700 rounded-lg p-4">
  <div class="flex items-center justify-between mb-2">
    <span class="text-sm text-gray-600 dark:text-gray-400">Total Consumption</span>
    <i class="fas fa-bolt text-yellow-500"></i>
  </div>
  <div class="text-2xl font-bold text-gray-900 dark:text-white" id="total-reading">
    —
  </div>
  <div class="text-xs text-gray-500 dark:text-gray-400 mt-1" id="last-reading-time">
    Loading...
  </div>
</div>
```

**Card 3: Device Status**
```html
<div class="bg-gray-50 dark:bg-gray-700 rounded-lg p-4">
  <div class="flex items-center justify-between mb-2">
    <span class="text-sm text-gray-600 dark:text-gray-400">Device Status</span>
    <i class="fas fa-battery-full text-green-500"></i>
  </div>
  <div class="text-sm text-gray-900 dark:text-white space-y-1">
    <div>Battery: <span id="battery-level" class="font-bold">—</span></div>
    <div>Temp: <span id="temperature" class="font-bold">—</span></div>
    <div>Signal: <span id="signal-strength" class="font-bold">—</span></div>
  </div>
</div>
```

**Remove:** Current Load and Voltage cards (not available from EM300-DI)

---

#### 2.2 Add meter_id to JavaScript Scope

**File:** `app/templates/meters/meter-details.html` (Around line 321)

**Add before `{% endblock %}`:**
```html
{% block extra_js %}
<script src="https://cdn.jsdelivr.net/npm/chart.js@3.9.1"></script>
<script>
  // Make meter_id and meter_type available to JavaScript
  window.METER_ID = "{{ meter_id }}";
  window.METER_TYPE = "{{ meter.meter_type if meter else 'unknown' }}";
</script>
<script src="/static/js/meters/meter-details.js"></script>
{% endblock %}
```

---

#### 2.3 Update Period Buttons

**File:** `app/templates/meters/meter-details.html` (Lines 217-236)

**Add `data-period` attributes:**
```html
<div class="flex space-x-2">
  <button data-period="hour" class="px-3 py-1 text-xs bg-white dark:bg-gray-600 rounded-lg">
    Hour
  </button>
  <button data-period="day" class="px-3 py-1 text-xs bg-primary text-white rounded-lg">
    Day
  </button>
  <button data-period="week" class="px-3 py-1 text-xs bg-white dark:bg-gray-600 rounded-lg">
    Week
  </button>
  <button data-period="month" class="px-3 py-1 text-xs bg-white dark:bg-gray-600 rounded-lg">
    Month
  </button>
</div>
```

---

### Phase 3: JavaScript Updates (Priority: HIGH)

#### 3.1 Complete Rewrite of meter-details.js

**File:** `app/static/js/meters/meter-details.js`

**New Functions:**
1. `fetchRealtimeStats()` - Get current meter data
2. `fetchChartData(period)` - Get chart data for period
3. `updateChart(labels, data, unit)` - Render chart
4. Auto-refresh every 30 seconds

**Key Features:**
- Fetch from new API endpoints
- Update DOM elements with real data
- Handle null/undefined values gracefully
- Show appropriate messages for missing data
- Dynamic chart based on selected period

---

### Phase 4: Backend Endpoint Implementation Details

#### 4.1 File: `app/routes/v1/meters.py`

**Add after line 296 (after existing meter_details_page function)**

**Function 1: get_meter_realtime_stats**
```python
@api_v1.route("/meters/<meter_id>/realtime-stats", methods=["GET"])
@login_required
@requires_permission("meters.view")
def get_meter_realtime_stats(meter_id: str):
    """Get real-time statistics for a meter"""

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

    # Calculate today's consumption
    from datetime import datetime, time
    today_start = datetime.combine(datetime.today(), time.min)
    today_readings = MeterReading.query.filter(
        MeterReading.meter_id == meter.id,
        MeterReading.reading_date >= today_start
    ).all()

    if today_readings and len(today_readings) > 1:
        values = [r.reading_value for r in today_readings]
        today_consumption = max(values) - min(values)
    else:
        today_consumption = 0.0

    # Check unit assignment for cost calculation
    unit = Unit.query.filter(
        (Unit.electricity_meter_id == meter.id) |
        (Unit.water_meter_id == meter.id) |
        (Unit.hot_water_meter_id == meter.id) |
        (Unit.solar_meter_id == meter.id)
    ).first()

    cost = None
    cost_message = None

    if not unit:
        cost_message = "Meter not assigned to unit"
    elif meter.meter_type == 'electricity' and not unit.electricity_rate_table_id:
        cost_message = "No rate table assigned"
    elif meter.meter_type == 'water' and not unit.water_rate_table_id:
        cost_message = "No rate table assigned"
    else:
        # Calculate cost (simplified - can be enhanced later)
        cost_per_unit = 1.67  # Default ZAR per kWh/m³
        cost = today_consumption * cost_per_unit

    # Determine device capabilities
    capabilities = {
        "measures_power": False,  # EM300-DI doesn't measure power
        "measures_voltage": False,
        "measures_flow": False,
        "measures_temperature": meter.lorawan_device_type == "milesight_em300",
        "unit": "kWh" if meter.meter_type in ["electricity", "solar"] else "m³"
    }

    # Build response
    return jsonify({
        "meter_id": meter.serial_number,
        "meter_type": meter.meter_type,
        "device_type": meter.lorawan_device_type,
        "capabilities": capabilities,
        "latest_reading": {
            "timestamp": latest_reading.reading_date.isoformat() if latest_reading else None,
            "value": float(latest_reading.reading_value) if latest_reading else None,
            "pulse_count": latest_reading.pulse_count if latest_reading else None,
            "temperature": float(latest_reading.temperature) if latest_reading and latest_reading.temperature else None,
            "humidity": float(latest_reading.humidity) if latest_reading and latest_reading.humidity else None,
            "battery_level": latest_reading.battery_level if latest_reading else None,
            "rssi": latest_reading.rssi if latest_reading else None,
            "snr": float(latest_reading.snr) if latest_reading and latest_reading.snr else None,
        },
        "today": {
            "consumption": float(today_consumption),
            "cost": float(cost) if cost is not None else None,
            "unit": capabilities["unit"],
            "cost_message": cost_message
        },
        "communication": {
            "last_communication": meter.last_communication.isoformat() if meter.last_communication else None,
            "status": meter.communication_status or "unknown"
        }
    })
```

**Function 2: get_meter_chart_data**
```python
@api_v1.route("/meters/<meter_id>/chart-data", methods=["GET"])
@login_required
@requires_permission("meters.view")
def get_meter_chart_data(meter_id: str):
    """Get consumption chart data for different time periods"""
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
    labels = []
    data = []

    if period == 'hour':
        # Last 60 minutes
        start_time = now - timedelta(hours=1)
        readings = db.session.query(
            func.date_trunc('minute', MeterReading.reading_date).label('interval'),
            func.max(MeterReading.reading_value).label('max_value'),
            func.min(MeterReading.reading_value).label('min_value')
        ).filter(
            MeterReading.meter_id == meter.id,
            MeterReading.reading_date >= start_time
        ).group_by('interval').order_by('interval').all()

        labels = [r.interval.strftime('%H:%M') for r in readings]
        data = [float(r.max_value - r.min_value) if r.max_value and r.min_value else 0 for r in readings]

    elif period == 'day':
        # Last 24 hours
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
        data = [float(r.max_value - r.min_value) if r.max_value and r.min_value else 0 for r in readings]

    elif period == 'week':
        # Last 7 days
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
        # Last 30 days
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
        return jsonify({"error": "Invalid period. Use: hour, day, week, or month"}), 400

    return jsonify({
        "labels": labels,
        "data": data,
        "period": period,
        "unit": "kWh" if meter.meter_type in ["electricity", "solar"] else "m³",
        "meter_type": meter.meter_type
    })
```

---

## ✅ Testing Checklist

### API Endpoints
- [ ] `/api/v1/meters/24e124136f215917/realtime-stats` returns valid JSON
- [ ] Returns 404 for non-existent meter
- [ ] `capabilities` object correctly identifies EM300-DI limitations
- [ ] `today.consumption` calculates correctly (or 0 if no data today)
- [ ] `today.cost_message` shows when meter not assigned to unit
- [ ] `/api/v1/meters/24e124136f215917/chart-data?period=day` returns data
- [ ] All periods work: hour, day, week, month
- [ ] Returns empty arrays if no readings

### UI Updates
- [ ] Page loads without JavaScript errors
- [ ] Three cards display: Today's Usage, Total Consumption, Device Status
- [ ] "Today's Usage" shows real calculation
- [ ] "Total Consumption" shows 655.37 kWh
- [ ] "Device Status" shows battery, temp, signal
- [ ] Cost shows message if no unit assigned
- [ ] Chart renders with real data
- [ ] Period buttons work (Hour/Day/Week/Month)
- [ ] Chart updates when switching periods
- [ ] Auto-refresh works (30 second interval)
- [ ] No hardcoded values visible

### Edge Cases
- [ ] Works when meter has no readings
- [ ] Works when meter not assigned to unit
- [ ] Works when only 1 reading exists (today's usage = 0)
- [ ] Handles missing temperature/humidity gracefully
- [ ] Handles null RSSI/SNR values

---

## 🚀 Deployment Steps

1. **Backend Implementation**
   ```bash
   # Edit app/routes/v1/meters.py
   # Add two new route functions after line 296
   ```

2. **Template Updates**
   ```bash
   # Edit app/templates/meters/meter-details.html
   # Update lines 166-209 (real-time cards)
   # Update lines 217-236 (period buttons)
   # Add JavaScript scope at line 321
   ```

3. **JavaScript Rewrite**
   ```bash
   # Edit app/static/js/meters/meter-details.js
   # Replace entire file with new implementation
   ```

4. **Test on Dev**
   ```bash
   # Restart frontend service
   sudo systemctl restart quantify-frontend

   # Check logs
   sudo journalctl -u quantify-frontend -f

   # Test in browser
   # Navigate to http://13.246.155.85:5000/api/v1/meters/24e124136f215917/details
   ```

5. **Verify**
   - Check API endpoints directly
   - Verify UI shows real data
   - Test all period switches
   - Check browser console for errors

---

## 📝 Notes & Decisions

### Cost Calculation Strategy
**Decision:** Show message when cost cannot be calculated
- "Meter not assigned to unit" - if no unit
- "No rate table assigned" - if unit exists but no rate table
- Show actual cost only when both exist

### Device Capabilities
**Decision:** Include in API response
- Frontend can check `capabilities.measures_power` before showing power card
- Extensible for future device types

### Chart Data Strategy
**Decision:** Use max-min approach for consumption
- For cumulative meters (pulse counters), consumption = max - min in period
- Handles missing data gracefully
- Works for all meter types

### Template Strategy
**Decision:** Single adaptive template
- Use Jinja2 conditionals based on meter_type
- Use JavaScript conditionals based on capabilities
- Easier to maintain than separate templates

---

## 🔄 Future Enhancements (Post-MVP)

### Phase 2: Water Meters
- Add flow rate card for Qalcosonic W1
- Add leak detection alerts
- Different icon/color for water vs electricity

### Phase 3: Solar Meters
- Change "Consumption" to "Generation"
- Show feed-in revenue instead of cost
- Green/positive UI styling

### Phase 4: Unit Assignment
- Add "Assign to Unit" button on meter details page
- Quick assignment modal
- Auto-calculate cost when assigned

### Phase 5: Advanced Features
- Real-time websocket updates (instead of 30s polling)
- Predictive usage forecasting
- Anomaly detection alerts
- Export readings to CSV/Excel
- Mobile-responsive improvements

---

## 📚 Related Documentation

- `METER_CAPABILITIES.md` - Complete device capabilities matrix
- `FixMeterPage.md` - Original fix specification (more detailed)
- `PROGRESS.md` - Overall project progress

---

**Status:** Ready to implement
**Estimated Time:** 3-4 hours
**Next Step:** Begin Phase 1 - Backend API endpoint implementation

# Server Setup Guide - QuantifyMeteringSystem

Complete setup instructions for deploying the frontend on Ubuntu server.

## Architecture Overview

```
Ubuntu Server (13.246.155.85)
├── /opt/chirpstack-docker     (ChirpStack + MQTT)
├── /opt/water-meter-app        (Backend - MQTT Listener)
└── /opt/QuantifyMeteringSystem (Frontend - User App) ← YOU ARE HERE
                                 ↓
                            PostgreSQL Database: "quantify"
                            User: admin
                            Password: a3OH72lD4tl8
```

---

## Prerequisites

✅ PostgreSQL installed and running
✅ Database "quantify" created
✅ User "admin" with password "a3OH72lD4tl8" exists
✅ Backend (water-meter-app) already running

---

## Quick Setup (Automated)

### Step 1: Upload Files

Copy these new files to the server:
```bash
# On your local machine
cd "H:\GIT_METALOGIX\Quantify Metering\QuantifyMeteringSystem"

# Copy to server (adjust path as needed)
scp setup_server.sh ubuntu@13.246.155.85:/opt/QuantifyMeteringSystem/
scp quantify-frontend.service ubuntu@13.246.155.85:/opt/QuantifyMeteringSystem/
scp register_test_meter.sql ubuntu@13.246.155.85:/opt/QuantifyMeteringSystem/
scp migrations/add_lorawan_fields.py ubuntu@13.246.155.85:/opt/QuantifyMeteringSystem/migrations/
```

### Step 2: Run Setup Script

```bash
# SSH to server
ssh ubuntu@13.246.155.85

# Run setup script
cd /opt/QuantifyMeteringSystem
sudo chmod +x setup_server.sh
sudo ./setup_server.sh
```

This will:
- Install system dependencies
- Create Python virtual environment
- Install Python packages
- Check/create .env file
- Optionally run database migration

---

## Manual Setup (Step-by-Step)

If you prefer manual setup:

### Step 1: Install System Dependencies

```bash
sudo apt-get update
sudo apt-get install -y python3-pip python3-venv python3-dev libpq-dev
```

### Step 2: Create Virtual Environment

```bash
cd /opt/QuantifyMeteringSystem
python3 -m venv .venv
source .venv/bin/activate
```

### Step 3: Install Python Dependencies

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### Step 4: Configure Environment

Check if `.env` file exists and has correct settings:
```bash
cat .env
```

Should contain:
```
SECRET_KEY=ilovequantifymetering94t253
DATABASE_URL=postgresql+psycopg2://admin:a3OH72lD4tl8@localhost:5432/quantify
```

### Step 5: Apply Database Migration

```bash
cd /opt/QuantifyMeteringSystem
source .venv/bin/activate
python migrations/add_lorawan_fields.py
```

This adds:
- `device_eui` and `lorawan_device_type` to `meters` table
- Telemetry fields to `meter_readings` table
- `device_commands` table

### Step 6: Register Test Meter

```bash
psql -U admin -d quantify -f register_test_meter.sql
# Password: a3OH72lD4tl8
```

Or manually:
```sql
psql -U admin -d quantify

INSERT INTO meters (
    serial_number, meter_type, manufacturer, model,
    device_eui, lorawan_device_type,
    communication_type, is_prepaid, is_active,
    created_at, updated_at
) VALUES (
    '24e124136f215917',
    'electricity',
    'Milesight',
    'EM300-DI',
    '24e124136f215917',
    'milesight_em300',
    'cellular',
    true,
    true,
    NOW(),
    NOW()
);
```

---

## Running the Application

### Option A: Run Manually (For Testing)

```bash
cd /opt/QuantifyMeteringSystem
source .venv/bin/activate
python application.py
```

Access at: http://13.246.155.85:5000

### Option B: Run as Systemd Service (Production)

```bash
# Copy service file
sudo cp quantify-frontend.service /etc/systemd/system/

# Reload systemd
sudo systemctl daemon-reload

# Enable service (auto-start on boot)
sudo systemctl enable quantify-frontend

# Start service
sudo systemctl start quantify-frontend

# Check status
sudo systemctl status quantify-frontend

# View logs
sudo journalctl -u quantify-frontend -f
```

---

## Verification

### 1. Check Both Services Running

```bash
# Backend (MQTT Listener)
sudo systemctl status meter-system

# Frontend (User App)
sudo systemctl status quantify-frontend
```

### 2. Check Database Connection

```bash
psql -U admin -d quantify

-- Check meters
SELECT serial_number, device_eui, meter_type, lorawan_device_type
FROM meters;

-- Check readings
SELECT COUNT(*) FROM meter_readings;
```

### 3. Test Data Flow

```bash
# Send test MQTT message (if backend has simulator)
cd /opt/water-meter-app
python simulate_gateway.py
```

Watch logs:
```bash
# Backend logs
sudo journalctl -u meter-system -f

# Frontend logs
sudo journalctl -u quantify-frontend -f
```

Check database:
```sql
-- View latest readings
SELECT m.serial_number, mr.reading_value, mr.reading_date, mr.pulse_count, mr.rssi, mr.battery_level
FROM meter_readings mr
JOIN meters m ON m.id = mr.meter_id
ORDER BY mr.reading_date DESC
LIMIT 10;
```

---

## Troubleshooting

### Frontend Won't Start

**Check logs:**
```bash
sudo journalctl -u quantify-frontend -n 50
```

**Common issues:**
1. Python dependencies missing: `pip install -r requirements.txt`
2. Database connection: Check DATABASE_URL in `.env`
3. Port already in use: Check if another app is using port 5000

### Database Migration Failed

**Error**: "relation already exists"
```bash
# Check if migration already applied
psql -U admin -d quantify -c "\d meters" | grep device_eui
```

If columns exist, migration is already applied.

### Can't Connect to Database

**Error**: "FATAL: password authentication failed"
```bash
# Reset admin user password
sudo -u postgres psql
ALTER USER admin WITH PASSWORD 'a3OH72lD4tl8';
GRANT ALL PRIVILEGES ON DATABASE quantify TO admin;
\q
```

### No Readings Appearing

**Check:**
1. Backend is running: `sudo systemctl status meter-system`
2. Meter is registered: `psql -U admin -d quantify -c "SELECT * FROM meters WHERE device_eui='24e124136f215917'"`
3. Backend can connect to database
4. MQTT messages are being received

---

## Port Configuration

**Both apps currently use port 5000!** You need to change one:

### Option 1: Change Frontend Port

Edit `/opt/QuantifyMeteringSystem/application.py`:
```python
app.run(host='0.0.0.0', port=8000)  # Change from 5000 to 8000
```

Then access at: http://13.246.155.85:8000

### Option 2: Use Nginx Reverse Proxy (Recommended)

```nginx
# /etc/nginx/sites-available/quantify

server {
    listen 80;
    server_name 13.246.155.85;

    location / {
        proxy_pass http://127.0.0.1:8000;  # Frontend
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    location /api/meters {
        proxy_pass http://127.0.0.1:5000;  # Backend
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

---

## Next Steps

1. ✅ Frontend deployed
2. ✅ Database migration applied
3. ✅ Test meter registered
4. ⏳ Test end-to-end: Device → Backend → Database → Frontend
5. ⏳ Configure proper port separation
6. ⏳ Set up Nginx reverse proxy
7. ⏳ Enable HTTPS with Let's Encrypt

---

**Last Updated**: 2025-11-03
**Server**: ubuntu@13.246.155.85

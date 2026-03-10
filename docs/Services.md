# Quantify Metering - Services Reference

> Comprehensive guide to all systemd services running the Quantify Metering platform.
> Server OS: Ubuntu | User: `ubuntu` | Timezone: `Africa/Johannesburg`

---

## Architecture Overview

```
LoRaWAN Devices / 4G Meters
        |
        v
  ChirpStack (MQTT Broker :1883)
        |
        v
  meter-system              <-- MQTT listener, stores readings, runs billing
        |
        v
  PostgreSQL (quantify)     <-- Shared database
        ^
        |
  quantify-frontend         <-- Flask web app (port 5000)
        ^
        |
  Redis (:6379)             <-- Celery message broker
   |          |
   v          v
  quantify-celery-worker    <-- Executes background tasks
  quantify-celery-beat      <-- Schedules periodic tasks
```

---

## 1. quantify-frontend

| Property | Value |
|----------|-------|
| **Description** | Flask web application — admin dashboard, API, and owner/tenant portal |
| **Project** | `QuantifyMeteringSystem` |
| **Server Path** | `/opt/QuantifyMeteringSystem` |
| **Entry Point** | `application.py` |
| **Port** | `5000` |
| **Depends On** | `postgresql.service` |

### What It Does
- Serves the admin web dashboard and owner/tenant portal
- Provides REST API endpoints (`/api/v1/`, `/api/mobile/`)
- Handles PayFast payment webhooks (ITN callbacks)
- Manages user authentication (session-based for web, JWT for mobile)
- Initialises Celery with Flask app context (but does NOT run worker/beat)

### Service File

```ini
[Unit]
Description=Quantify Metering Frontend - User Application
After=network.target postgresql.service
Wants=postgresql.service

[Service]
Type=simple
User=ubuntu
Group=ubuntu
WorkingDirectory=/opt/QuantifyMeteringSystem
Environment="PATH=/opt/QuantifyMeteringSystem/venv/bin"
ExecStart=/opt/QuantifyMeteringSystem/venv/bin/python application.py
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal
SyslogIdentifier=quantify-frontend

[Install]
WantedBy=multi-user.target
```

### Commands
```bash
sudo systemctl status quantify-frontend
sudo systemctl restart quantify-frontend
sudo journalctl -u quantify-frontend -f
```

---

## 2. meter-system

| Property | Value |
|----------|-------|
| **Description** | MQTT listener — receives meter telemetry, stores readings, runs consumption billing |
| **Project** | `Quantify-Metering-Monitor` |
| **Server Path** | `/opt/Quantify-Metering-Monitor` |
| **Entry Point** | `data_collector_app.py` |
| **Port** | None (MQTT client, not a web server) |
| **Depends On** | `postgresql.service`, MQTT broker (ChirpStack) |

### What It Does
- Subscribes to ChirpStack MQTT topics (`application/+/device/+/event/up`)
- Listens for KPM31 4G electricity meter MQTT topics (`MQTT_RT_DATA`, `MQTT_TELEIND`)
- Decodes LoRaWAN payloads (Milesight EM300-DI, Axioma Qalcosonic W1, KPM31)
- Stores meter readings in `meter_readings` table
- Runs consumption billing on every reading (deducts from wallet)
- Tracks meter online/offline status and communication timestamps
- Auto-resolves `communication_loss` alerts when a meter comes back online
- Auto-registers KPM31 meters on first sighting

### Service File

```ini
[Unit]
Description=Quantify Metering Monitor - MQTT Data Collector
After=network.target postgresql.service
Wants=postgresql.service

[Service]
Type=simple
User=ubuntu
Group=ubuntu
WorkingDirectory=/opt/Quantify-Metering-Monitor
Environment="PATH=/opt/Quantify-Metering-Monitor/venv/bin"
ExecStart=/opt/Quantify-Metering-Monitor/venv/bin/python data_collector_app.py
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal
SyslogIdentifier=meter-system

[Install]
WantedBy=multi-user.target
```

### Commands
```bash
sudo systemctl status meter-system
sudo systemctl restart meter-system
sudo journalctl -u meter-system -f
```

---

## 3. quantify-celery-worker

| Property | Value |
|----------|-------|
| **Description** | Celery worker — executes background tasks from Redis queues |
| **Project** | `QuantifyMeteringSystem` |
| **Server Path** | `/opt/QuantifyMeteringSystem` |
| **Entry Point** | `celery_app.py` (via `celery` CLI) |
| **Port** | None |
| **Depends On** | `redis.service`, `postgresql.service` |

### What It Does

Picks up task messages from Redis and executes them. Processes three queues:

#### `notifications` queue
| Task | Trigger | Description |
|------|---------|-------------|
| `check_low_credit_wallets` | Beat (daily 6 AM) | Finds wallets below their `low_balance_threshold`, creates in-app notifications |
| `check_critical_credit_wallets` | Beat (every 4h) | Finds critically low wallets (below 20% of threshold), creates urgent notifications |
| `analyze_high_usage` | Beat (daily 7 AM) | Flags meters with usage 50%+ above their historical average |
| `send_topup_notification` | Real-time | Creates in-app notification after wallet top-up |
| `send_purchase_notification` | Real-time | Creates in-app notification after utility purchase |
| `check_wallet_after_transaction` | Real-time | Checks balance after purchase, alerts if below threshold |
| `check_meter_communication_health` | Beat (every 15 min) | Detects meters that haven't communicated within expected interval, creates `communication_loss` alerts |

#### `payments` queue
| Task | Trigger | Description |
|------|---------|-------------|
| `expire_stale_payfast_transactions` | Beat (every 30 min) | Expires pending PayFast transactions older than 1 hour (user abandoned payment page) |
| `reconcile_payfast_transactions` | Beat (daily midnight) | Verifies last 48h of PayFast transactions against PayFast server; auto-fixes missed completions, flags mismatches |
| `send_topup_receipt_email` | Real-time | Sends email receipt to tenant/owner after successful PayFast payment |

#### `prepaid` queue (DISABLED)
| Task | Status | Description |
|------|--------|-------------|
| `disconnect_zero_balance_meters` | **COMMENTED OUT** | Would disconnect meters with zero balance — NOT active |
| `reconnect_topped_up_meters` | **COMMENTED OUT** | Would reconnect meters after top-up — NOT active |

> **WARNING:** The prepaid disconnect/reconnect tasks are intentionally disabled.
> Do NOT uncomment until proper testing with real meters is complete.
> Manual relay switching is currently in use and must not be disrupted.

### Configuration
- **Concurrency:** 4 workers
- **Prefetch:** 1 task at a time per worker
- **Task time limit:** 300 seconds (5 minutes)
- **Serializer:** JSON
- **Broker:** Redis (`redis://localhost:6379/0`)

### Service File

```ini
[Unit]
Description=Quantify Metering Celery Worker
After=network.target redis.service postgresql.service
Wants=redis.service postgresql.service

[Service]
Type=simple
User=ubuntu
Group=ubuntu
WorkingDirectory=/opt/QuantifyMeteringSystem
Environment="PATH=/opt/QuantifyMeteringSystem/venv/bin"
ExecStart=/opt/QuantifyMeteringSystem/venv/bin/celery -A celery_app.celery worker --loglevel=info -Q notifications,payments,prepaid
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal
SyslogIdentifier=quantify-celery-worker

[Install]
WantedBy=multi-user.target
```

### Commands
```bash
sudo systemctl status quantify-celery-worker
sudo systemctl restart quantify-celery-worker
sudo journalctl -u quantify-celery-worker -f
```

---

## 4. quantify-celery-beat

| Property | Value |
|----------|-------|
| **Description** | Celery beat scheduler — fires periodic tasks on a cron schedule |
| **Project** | `QuantifyMeteringSystem` |
| **Server Path** | `/opt/QuantifyMeteringSystem` |
| **Entry Point** | `celery_app.py` (via `celery` CLI) |
| **Port** | None |
| **Depends On** | `redis.service` |

### What It Does

Acts as a cron scheduler. Does NOT execute tasks itself — it sends task messages
to Redis at the configured intervals, which the worker then picks up and runs.

### Beat Schedule (Africa/Johannesburg timezone)

| Schedule | Task | Queue |
|----------|------|-------|
| Every 15 minutes | `check_meter_communication_health` | notifications |
| Every 30 minutes | `expire_stale_payfast_transactions` | payments |
| Every 4 hours (at :30) | `check_critical_credit_wallets` | notifications |
| Daily 00:00 | `reconcile_payfast_transactions` | payments |
| Daily 06:00 | `check_low_credit_wallets` | notifications |
| Daily 07:00 | `analyze_high_usage` | notifications |

### Service File

```ini
[Unit]
Description=Quantify Metering Celery Beat Scheduler
After=network.target redis.service
Wants=redis.service

[Service]
Type=simple
User=ubuntu
Group=ubuntu
WorkingDirectory=/opt/QuantifyMeteringSystem
Environment="PATH=/opt/QuantifyMeteringSystem/venv/bin"
ExecStart=/opt/QuantifyMeteringSystem/venv/bin/celery -A celery_app.celery beat --loglevel=info
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal
SyslogIdentifier=quantify-celery-beat

[Install]
WantedBy=multi-user.target
```

### Commands
```bash
sudo systemctl status quantify-celery-beat
sudo systemctl restart quantify-celery-beat
sudo journalctl -u quantify-celery-beat -f
```

---

## Deployment Checklist

### Prerequisites
- [x] PostgreSQL running and `quantify` database exists
- [x] Python virtual environments created in each project directory
- [ ] Redis installed and running (`sudo systemctl status redis`)
- [ ] All `.env` files configured on the server

### Install Services
```bash
# Copy service files to systemd
sudo cp quantify-frontend.service /etc/systemd/system/
sudo cp meter-system.service /etc/systemd/system/
sudo cp quantify-celery-worker.service /etc/systemd/system/
sudo cp quantify-celery-beat.service /etc/systemd/system/

# Reload systemd
sudo systemctl daemon-reload

# Enable services (start on boot)
sudo systemctl enable quantify-frontend
sudo systemctl enable meter-system
sudo systemctl enable quantify-celery-worker
sudo systemctl enable quantify-celery-beat

# Start services
sudo systemctl start quantify-frontend
sudo systemctl start meter-system
sudo systemctl start quantify-celery-worker
sudo systemctl start quantify-celery-beat
```

### Verify All Running
```bash
sudo systemctl status quantify-frontend meter-system quantify-celery-worker quantify-celery-beat
```

### Restart Order (after deployment)
When deploying code changes, restart in this order:
1. `quantify-celery-beat` — stop scheduler first
2. `quantify-celery-worker` — let running tasks finish, then restart
3. `quantify-frontend` — restart web app
4. `meter-system` — restart MQTT listener (only if Monitor code changed)

```bash
sudo systemctl restart quantify-celery-beat
sudo systemctl restart quantify-celery-worker
sudo systemctl restart quantify-frontend
sudo systemctl restart meter-system  # only if Monitor changed
```

---

## Quick Reference

| Service | Project | What | Status Check |
|---------|---------|------|--------------|
| `quantify-frontend` | QuantifyMeteringSystem | Web app (port 5000) | `curl http://localhost:5000` |
| `meter-system` | Quantify-Metering-Monitor | MQTT listener | `journalctl -u meter-system -n 20` |
| `quantify-celery-worker` | QuantifyMeteringSystem | Task executor | `journalctl -u quantify-celery-worker -n 20` |
| `quantify-celery-beat` | QuantifyMeteringSystem | Task scheduler | `journalctl -u quantify-celery-beat -n 20` |
| `redis` | System | Message broker | `redis-cli ping` → `PONG` |
| `postgresql` | System | Database | `pg_isready` |

---

## Log Monitoring

### Follow all Quantify logs at once
```bash
sudo journalctl -u quantify-frontend -u meter-system -u quantify-celery-worker -u quantify-celery-beat -f
```

### Check for errors only
```bash
sudo journalctl -u quantify-celery-worker -p err -n 50
sudo journalctl -u quantify-celery-beat -p err -n 50
```

### Check Celery task execution
```bash
# See which tasks are being picked up
sudo journalctl -u quantify-celery-worker --since "1 hour ago" | grep "Task"
```

# Notification System

This document describes the automated notification system for Quantify Metering.

## Overview

The notification system uses **Celery** with **Redis** as the message broker to handle:
- **Real-time notifications** - Triggered immediately by user actions (top-ups, purchases)
- **Scheduled notifications** - Run periodically to check for low credit, high usage, etc.

## Architecture

```
┌─────────────────┐     ┌─────────────┐     ┌─────────────────┐
│  Flask App      │────▶│   Redis     │────▶│  Celery Worker  │
│  (Web Server)   │     │  (Broker)   │     │  (Background)   │
└─────────────────┘     └─────────────┘     └─────────────────┘
                                                    │
                              ┌─────────────────────┼─────────────────────┐
                              │                     │                     │
                              ▼                     ▼                     ▼
                        ┌──────────┐         ┌──────────┐         ┌──────────┐
                        │ Real-time│         │ Scheduled│         │ Database │
                        │  Tasks   │         │  Tasks   │         │          │
                        └──────────┘         └──────────┘         └──────────┘
```

## Prerequisites

1. **Redis Server** - Install and run Redis
   - Windows: Download from https://github.com/microsoftarchive/redis/releases
   - Linux: `sudo apt install redis-server`
   - macOS: `brew install redis`

2. **Python Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

## Configuration

Environment variables (add to `.env` file):

```env
# Celery Configuration
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0
CELERY_TIMEZONE=Africa/Johannesburg
```

## Running the System

### 1. Start Redis
```bash
# Windows (if installed as service, it auto-starts)
redis-server

# Linux/macOS
redis-server
```

### 2. Start Celery Worker
```bash
# Windows
scripts\run_celery_worker.bat

# Linux/macOS
./scripts/run_celery_worker.sh

# Or manually:
celery -A celery_app.celery worker --loglevel=info --queues=notifications
```

### 3. Start Celery Beat (Scheduler)
```bash
# Windows
scripts\run_celery_beat.bat

# Or manually:
celery -A celery_app.celery beat --loglevel=info
```

### 4. Start Flask App
```bash
python application.py
```

## Notification Types

| Type | Trigger | Schedule |
|------|---------|----------|
| `low_credit` | Balance < threshold | Daily at 6 AM |
| `critical_credit` | Balance < 20% of threshold | Every 4 hours |
| `topup_success` | Wallet top-up | Real-time |
| `purchase_success` | Utility purchase | Real-time |
| `high_usage` | Usage > 50% above average | Daily at 7 AM |

## Scheduled Tasks (Celery Beat)

| Task | Schedule | Description |
|------|----------|-------------|
| `check_low_credit_wallets` | Daily 6:00 AM | Check all wallets for low balance |
| `check_critical_credit_wallets` | Every 4 hours | Check for critically low balances |
| `analyze_high_usage` | Daily 7:00 AM | Analyze usage patterns |

## Real-time Tasks

These are triggered immediately when events occur:

- `send_topup_notification` - Called after wallet top-up
- `send_purchase_notification` - Called after utility purchase
- `check_wallet_after_transaction` - Check balance after transactions

## Testing

### Manual Task Trigger
```python
from celery_app import celery
from app.tasks.notification_tasks import check_low_credit_wallets

# Trigger task immediately
result = check_low_credit_wallets.delay()
print(result.get())  # Wait for result
```

### Check Task Status
```python
from celery_app import celery

# Check if worker is running
i = celery.control.inspect()
print(i.active())  # Currently running tasks
print(i.scheduled())  # Scheduled tasks
```

## Files

```
├── celery_app.py                    # Celery configuration
├── config.py                        # App config with Celery settings
├── app/
│   ├── services/
│   │   └── notification_service.py  # Notification creation logic
│   └── tasks/
│       ├── __init__.py
│       └── notification_tasks.py    # Celery task definitions
└── scripts/
    ├── run_celery_worker.bat        # Windows worker script
    ├── run_celery_worker.sh         # Linux/macOS worker script
    └── run_celery_beat.bat          # Windows beat script
```

## Production Deployment

For production, use a process manager like **supervisord** or **systemd**:

### Systemd Service (Linux)

Create `/etc/systemd/system/quantify-celery-worker.service`:
```ini
[Unit]
Description=Quantify Celery Worker
After=network.target redis.service

[Service]
Type=simple
User=www-data
WorkingDirectory=/path/to/QuantifyMeteringSystem
ExecStart=/path/to/venv/bin/celery -A celery_app.celery worker --loglevel=info
Restart=always

[Install]
WantedBy=multi-user.target
```

Create `/etc/systemd/system/quantify-celery-beat.service`:
```ini
[Unit]
Description=Quantify Celery Beat
After=network.target redis.service

[Service]
Type=simple
User=www-data
WorkingDirectory=/path/to/QuantifyMeteringSystem
ExecStart=/path/to/venv/bin/celery -A celery_app.celery beat --loglevel=info
Restart=always

[Install]
WantedBy=multi-user.target
```

Enable and start:
```bash
sudo systemctl enable quantify-celery-worker quantify-celery-beat
sudo systemctl start quantify-celery-worker quantify-celery-beat
```

## Troubleshooting

### Worker not receiving tasks
1. Check Redis is running: `redis-cli ping` should return `PONG`
2. Check worker is connected: Look for "celery@hostname ready" in worker logs
3. Verify task is imported: Check `celery_app.py` includes list

### Tasks not being scheduled
1. Ensure Celery Beat is running
2. Check timezone configuration
3. Verify beat schedule in `celery_app.py`

### Notifications not appearing in mobile app
1. Check notification was created in database
2. Verify `recipient_id` matches the person's ID
3. Check `channel` is set to `in_app`

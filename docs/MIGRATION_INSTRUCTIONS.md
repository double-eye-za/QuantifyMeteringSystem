# Migration Instructions - Device & Communication Types

**Date:** 2025-11-11
**Migration:** `f1a2b3c4d5e6_add_device_and_communication_type_tables.py`

---

## Quick Start

### On Linux/Mac Server:

```bash
# 1. Navigate to project directory
cd /path/to/QuantifyMeteringSystem

# 2. Activate virtual environment (if using one)
source venv/bin/activate

# 3. Set Flask app environment variable
export FLASK_APP=application.py

# 4. Run the migration
flask db upgrade

# 5. Seed initial data
python scripts/seed_device_comm_types.py
```

---

### On Windows Server:

```cmd
REM 1. Navigate to project directory
cd C:\path\to\QuantifyMeteringSystem

REM 2. Activate virtual environment (if using one)
venv\Scripts\activate

REM 3. Set Flask app environment variable
set FLASK_APP=application.py

REM 4. Run the migration
flask db upgrade

REM 5. Seed initial data
python scripts\seed_device_comm_types.py
```

---

## Detailed Steps

### Step 1: Connect to Your Server

```bash
ssh user@your-server-ip
```

---

### Step 2: Navigate to Project Directory

```bash
cd /path/to/QuantifyMeteringSystem
```

Find your project location. Common locations:
- `/var/www/QuantifyMeteringSystem`
- `/opt/QuantifyMeteringSystem`
- `/home/user/QuantifyMeteringSystem`

---

### Step 3: Activate Virtual Environment (if applicable)

If you're using a Python virtual environment:

```bash
source venv/bin/activate
# or
source env/bin/activate
# or
source .venv/bin/activate
```

You should see `(venv)` or similar prefix in your prompt.

---

### Step 4: Set Flask App Variable

```bash
export FLASK_APP=application.py
```

**Note:** Add this to your `~/.bashrc` or `~/.bash_profile` to make it permanent:
```bash
echo 'export FLASK_APP=application.py' >> ~/.bashrc
source ~/.bashrc
```

---

### Step 5: Verify Current Migration State

Check which migrations have been applied:

```bash
flask db current
```

Output should show something like:
```
e9f4a5b6c789 (head)
```

---

### Step 6: Check Pending Migrations

See what migrations are waiting:

```bash
flask db history
```

You should see:
```
e9f4a5b6c789 -> f1a2b3c4d5e6 (head), add device and communication type tables
```

---

### Step 7: Run the Migration

```bash
flask db upgrade
```

**Expected Output:**
```
INFO  [alembic.runtime.migration] Context impl PostgresqlImpl.
INFO  [alembic.runtime.migration] Will assume transactional DDL.
INFO  [alembic.runtime.migration] Running upgrade e9f4a5b6c789 -> f1a2b3c4d5e6, add device and communication type tables
```

---

### Step 8: Verify Migration Success

Check the current migration state again:

```bash
flask db current
```

Should now show:
```
f1a2b3c4d5e6 (head)
```

---

### Step 9: Seed Initial Data

Populate the new tables with initial device types and communication types:

```bash
python scripts/seed_device_comm_types.py
```

**Expected Output:**
```
============================================================
DEVICE TYPES & COMMUNICATION TYPES SEEDING
============================================================

Seeding device types...
  ✓ Created device type: Milesight EM300-DI (Pulse Counter)
  ✓ Created device type: Qalcosonic W1 (Water Meter)
  ✓ Created device type: Kamstrup Multical (Heat/Water Meter)
  ✓ Created device type: Fengbo 4G Water Meter
Device types seeded successfully!

Seeding communication types...
  ✓ Created communication type: LoRaWAN
  ✓ Created communication type: 4G/NB-IoT (Cellular)
  ✓ Created communication type: PLC (Power Line Communication)
  ✓ Created communication type: WiFi
  ✓ Created communication type: Manual Reading
  ✓ Created communication type: Modbus RTU/TCP
Communication types seeded successfully!

============================================================
✓ All reference data seeded successfully!
============================================================
```

---

### Step 10: Restart Flask Application

If running with Gunicorn or systemd service:

```bash
# Option 1: Systemd service
sudo systemctl restart quantify-metering

# Option 2: Supervisor
sudo supervisorctl restart quantify-metering

# Option 3: Manual Gunicorn restart
pkill gunicorn
gunicorn -w 4 -b 0.0.0.0:5000 application:app

# Option 4: Flask development server (not recommended for production)
flask run --host=0.0.0.0
```

---

### Step 11: Verify in Browser

1. **Access Device Types:**
   - Navigate to: `http://your-server-ip:5000/api/v1/device-types`
   - You should see a table with 4 device types

2. **Access Communication Types:**
   - Navigate to: `http://your-server-ip:5000/api/v1/communication-types`
   - You should see a table with 6 communication types

3. **Test Meters Page:**
   - Navigate to: `http://your-server-ip:5000/api/v1/meters`
   - Click "Create Meter"
   - Verify "Device Type" dropdown is populated
   - Verify "Communication Type" dropdown is populated

---

## Troubleshooting

### Issue: "flask: command not found"

**Cause:** Flask not installed or virtual environment not activated

**Solution:**
```bash
# Check if in virtual environment
which python

# Activate virtual environment
source venv/bin/activate

# Or install flask-migrate if missing
pip install flask-migrate
```

---

### Issue: "FLASK_APP environment variable not set"

**Cause:** FLASK_APP not exported

**Solution:**
```bash
export FLASK_APP=application.py
flask db upgrade
```

---

### Issue: "Can't locate revision identified by 'e9f4a5b6c789'"

**Cause:** Migration files out of sync or missing

**Solution:**
```bash
# Check migration files exist
ls migrations/versions/

# If files are missing, pull from git again
git pull origin main

# If still issues, stamp current state
flask db stamp head
```

---

### Issue: "Target database is not up to date"

**Cause:** Database has newer migrations than code

**Solution:**
```bash
# Check current database state
flask db current

# Downgrade if needed (be careful!)
flask db downgrade e9f4a5b6c789

# Then upgrade
flask db upgrade
```

---

### Issue: "relation 'device_types' already exists"

**Cause:** Tables already created (migration run twice or manually created)

**Solution:**
```bash
# Mark migration as applied without running it
flask db stamp f1a2b3c4d5e6

# Or drop tables and re-run (WARNING: destroys data)
# psql -d quantify -c "DROP TABLE IF EXISTS device_types CASCADE;"
# psql -d quantify -c "DROP TABLE IF EXISTS communication_types CASCADE;"
# flask db upgrade
```

---

### Issue: Seed script fails with "table does not exist"

**Cause:** Migration not run before seeding

**Solution:**
```bash
# Run migration first
flask db upgrade

# Then seed
python scripts/seed_device_comm_types.py
```

---

### Issue: Seed script says "already exists, skipping"

**Cause:** Data already seeded (this is normal on re-runs)

**Solution:** This is expected behavior. The script skips existing records to prevent duplicates.

---

### Issue: Permission denied when running migration

**Cause:** Database user lacks CREATE TABLE permission

**Solution:**
```sql
-- Connect as postgres superuser
sudo -u postgres psql

-- Grant permissions
GRANT CREATE ON DATABASE quantify TO your_db_user;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO your_db_user;
```

---

## Database Verification

### Check Tables Were Created

```bash
psql -d quantify -c "\dt"
```

Should show:
```
 public | device_types           | table | quantify_user
 public | communication_types    | table | quantify_user
```

---

### Check Data Was Seeded

```bash
# Check device types count
psql -d quantify -c "SELECT COUNT(*) FROM device_types;"

# Should show: 4

# Check communication types count
psql -d quantify -c "SELECT COUNT(*) FROM communication_types;"

# Should show: 6

# View all device types
psql -d quantify -c "SELECT code, name FROM device_types;"

# View all communication types
psql -d quantify -c "SELECT code, name FROM communication_types;"
```

---

## Rollback (If Needed)

If something goes wrong and you need to rollback:

```bash
# Downgrade to previous migration
flask db downgrade e9f4a5b6c789

# This will:
# - Drop device_types table
# - Drop communication_types table
```

**WARNING:** Rollback will delete all data in these tables!

---

## Production Deployment Checklist

Before running in production:

- [ ] Backup database: `pg_dump quantify > backup_$(date +%Y%m%d).sql`
- [ ] Test migration on staging/dev environment first
- [ ] Verify application is stopped or in maintenance mode
- [ ] Run migration: `flask db upgrade`
- [ ] Run seed script: `python scripts/seed_device_comm_types.py`
- [ ] Verify tables created: `psql -d quantify -c "\dt"`
- [ ] Verify data seeded: `psql -d quantify -c "SELECT COUNT(*) FROM device_types;"`
- [ ] Restart application
- [ ] Test UI in browser
- [ ] Check logs for errors: `tail -f /var/log/quantify/app.log`
- [ ] Monitor application for issues

---

## Summary Commands (Copy-Paste Ready)

```bash
# Full deployment script
cd /path/to/QuantifyMeteringSystem
source venv/bin/activate
export FLASK_APP=application.py
flask db upgrade
python scripts/seed_device_comm_types.py
sudo systemctl restart quantify-metering
```

---

## Need Help?

Check these logs for errors:

```bash
# Flask/Gunicorn logs
tail -f /var/log/quantify/app.log

# Systemd service logs
sudo journalctl -u quantify-metering -f

# PostgreSQL logs
sudo tail -f /var/log/postgresql/postgresql-14-main.log
```

---

**Document Version:** 1.0
**Last Updated:** 2025-11-11
**Author:** Claude Code

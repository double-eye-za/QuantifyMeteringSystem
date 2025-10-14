# Installation Guide

This guide walks you through setting up the Quantify Metering System backend for local development.

## Prerequisites

- Python 3.9+
- PostgreSQL 14+
- Git

Optional (for tests only): SQLite is used automatically; no local Postgres needed for running tests.

## 1) Clone the repository

```bash
git clone git@github.com:willieprinsloo/QuantifyMeteringSystem.git
cd QuantifyMeteringSystem
```

## 2) Create a virtual environment

```bash
python3 -m venv .venv
source .venv/bin/activate
```

Windows (Powershell):

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
```

## 3) Install dependencies

```bash
pip install -r requirements.txt
```

## 4) Configure environment

```bash
export FLASK_APP=application.py
export FLASK_ENV=development
export DATABASE_URL=postgresql+psycopg2://postgres:postgres@localhost:5432/quantify
```

On Windows (Powershell):

```powershell
$env:FLASK_APP = "application.py"
$env:FLASK_ENV = "development"
$env:DATABASE_URL = "postgresql+psycopg2://postgres:postgres@localhost:5432/quantify"
```

Create the database in Postgres if it does not exist:

```sql
CREATE DATABASE quantify;
```

## 5) Initialize and upgrade the database (Flask-Migrate)

```bash
flask db init    # first time only
flask db migrate -m "initial schema"
flask db upgrade
```

## 6) Run the application

```bash
python application.py
```

The server starts on http://127.0.0.1:5000.

## 7) Run the tests

```bash
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 pytest -q
```

Tests run against an in-memory SQLite database and do not require local Postgres.

## 8) Using database migrations

After modifying models under `app/models`, create and apply a migration:

```bash
flask db migrate -m "describe your change"
flask db upgrade
```

To downgrade:

```bash
flask db downgrade
```

## Troubleshooting

- Ensure your virtualenv is active when running commands.
- If `flask` command is not found, reinstall requirements or activate the venv.
- For Postgres connection issues, verify `DATABASE_URL`, DB exists, and credentials.

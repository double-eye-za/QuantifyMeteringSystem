# Quantify Metering — Brochure Implementation Gap Analysis

> **Audit Date:** 2026-02-18
> **Audited Projects:** QuantifyMeteringSystem + Quantify-Metering-Monitor
> **Purpose:** Line-by-line verification of every brochure claim against actual codebase
> **Directive:** The brochure is the specification. Every claim must be built.

---

## How To Read This Document

Each brochure claim is assessed as:

| Status | Meaning |
|--------|---------|
| DONE | Feature exists and works as described |
| PARTIAL | Some implementation exists, needs completion |
| TODO | No code exists — must be built |

Each gap includes:
- **What exists** in code (with file references)
- **What must be built** to fulfil the claim
- **Dependencies** on other gaps
- **Effort estimate** (S = days / M = 1-2 weeks / L = 2-4 weeks / XL = 4+ weeks)

---

## Table of Contents

1. [Tokenless Wallet-Based Metering (Core Claims)](#1-tokenless-wallet-based-metering)
2. [Tenant App (Layer 1)](#2-tenant-app-layer-1)
3. [Owner / Landlord Portal (Layer 2)](#3-owner--landlord-portal-layer-2)
4. [Family / Multi-Account Layer (Layer 3)](#4-family--multi-account-layer-layer-3)
5. [Body Corporate Dashboard (Layer 4)](#5-body-corporate-dashboard-layer-4)
6. [Managing Agent Interface (Layer 5)](#6-managing-agent-interface-layer-5)
7. [Utility & Bulk Supply Layer (Layer 6)](#7-utility--bulk-supply-layer-layer-6)
8. [How The Wallet Works (5-Step Flow)](#8-how-the-wallet-works)
9. [Why Quantify (Selling Points)](#9-why-quantify-selling-points)
10. [Communication Protocols](#10-communication-protocols)
11. [Optional Add-Ons](#11-optional-add-ons)
12. [Implementation Roadmap](#12-implementation-roadmap)

---

## 1. Tokenless Wallet-Based Metering

### 1.1 "Users load funds into a secure wallet" — PARTIAL

**What exists:**
- Wallet model with per-utility balances (`app/models/wallet.py`)
- PayFast payment gateway integration — sandbox only (`app/routes/payfast.py`)
- Mobile top-up: `POST /api/mobile/units/<id>/topup` (`app/routes/mobile/payments.py`)
- Portal top-up form (`app/routes/portal/wallet.py`)
- `credit_wallet()` updates balance immediately on PayFast ITN callback (`app/services/wallets.py`)

**What must be built:**
- [ ] Complete PayFast production setup (10-step checklist in `PayFastProd-TO-DO.md`)
- [ ] PayFast covers EFT, card, and instant EFT via its payment page — verify all methods work in production
- [ ] Manual EFT reconciliation workflow (admin marks manual bank deposits as received)

**Dependencies:** None — this is foundational
**Effort:** M

---

### 1.2 "Consumption deducts automatically in real time" — PARTIAL

**What exists:**
- `process_consumption_billing()` deducts from wallet on every MQTT reading (`Quantify-Metering-Monitor/water_meter_module/consumption_billing.py`)
- Supports flat rate, tiered, and time-of-use billing
- Transaction record created for every deduction

**What must be built:**
- [ ] Credit control — stop allowing infinite negative balances (see Gap 8.3)
- [ ] Electricity: enable relay disconnect at R0.00 (code exists but commented out in `app/tasks/prepaid_disconnect_tasks.py`)
- [ ] Reconnection workflow when balance restored above `electricity_minimum_activation` (R20)
- [ ] Water: implement debt cap (no physical disconnect but limit negative balance)

**Dependencies:** Gap 8.3 (credit control)
**Effort:** M

---

### 1.3 "No codes. No slip-ups. No physical intervention." — DONE

System is fully balance-based. No token generation anywhere.

---

### 1.4 "Instant credit" — PARTIAL

**What exists:**
- PayFast ITN webhook calls `credit_wallet()` synchronously — instant balance update

**What must be built:**
- [ ] Same as Gap 1.1 — move PayFast to production so instant credit actually works for real payments

**Dependencies:** Gap 1.1
**Effort:** Included in 1.1

---

### 1.5 "Live balance" — DONE

Wallet balances update synchronously on every topup and consumption event. Mobile API, portal, and admin all return current balances.

---

### 1.6 "Automated settlement" — TODO

**What exists:** Nothing.

**What must be built:**
- [ ] `SettlementRule` model — defines who gets what share of revenue per estate (operator, body corporate, utility)
- [ ] `SettlementRun` model — records each execution with amounts distributed
- [ ] Settlement calculation engine — applies rules to collected revenue for a period
- [ ] Settlement transaction types: `settlement_operator`, `settlement_body_corporate`, `settlement_utility`
- [ ] Celery task for scheduled settlement runs (monthly)
- [ ] Settlement reporting endpoint and PDF export
- [ ] Admin UI for configuring settlement rules per estate

**Dependencies:** Gap 1.1 (payments must work first)
**Effort:** XL

---

### 1.7 "Smart reporting" — PARTIAL

**What exists:**
- Reports API: consumption, financial, system, estate-level (`app/routes/v1/reports.py`)
- CSV and PDF export via ReportLab
- Chart.js visualisations in admin dashboard

**What must be built:**
- [ ] Scheduled report generation Celery task (daily/weekly/monthly per estate)
- [ ] Report subscription model — estates/users subscribe to specific reports
- [ ] Email distribution of generated reports via Flask-Mail
- [ ] Per-unit monthly statement template (PDF)

**Dependencies:** None
**Effort:** M

---

### 1.8 "Layered user access" — DONE

Role-based permission system with `Role` + `Permission` models, `@requires_permission()` decorator, three user tiers (Admin, Portal/Mobile, Super Admin).

---

## 2. Tenant App (Layer 1)

### 2.1 "Load funds instantly" — PARTIAL

Same as Gap 1.1. PayFast sandbox works, needs production setup.

---

### 2.2 "View live consumption" — DONE

`GET /api/mobile/units/<id>/meters` returns current readings, communication status, balances.

---

### 2.3 "Daily/weekly/monthly usage graphs" — TODO (for tenants)

**What exists:**
- Chart.js graphs in admin reports section
- Daily consumption trend aggregation in reports API

**What must be built:**
- [ ] `GET /api/mobile/units/<id>/consumption-history` — time-series data endpoint with `period` parameter (daily/weekly/monthly)
- [ ] Aggregate `meter_readings` by day/week/month for the unit's meters
- [ ] Return chart-ready JSON (labels + datasets for each utility)
- [ ] Mobile app frontend implementation for charts

**Dependencies:** None
**Effort:** M

---

### 2.4 "Budget alerts" — DONE

`low_balance_threshold`, `alert_frequency_hours`, critical credit checks (20% of threshold), high-usage detection (50%+ above average). All via Celery scheduled tasks.

---

### 2.5 "Multi-meter view (electricity, water, hot water, solar power)" — DONE

Unit model has 4 meter FKs, wallet has 4 separate balances, mobile API returns all meters with per-utility balances.

---

## 3. Owner / Landlord Portal (Layer 2)

### 3.1 "Portfolio-level dashboard" — DONE

`GET /api/dashboard` with estate selector, cross-estate aggregation, KPIs.

---

### 3.2 "Revenue reconciliation" — DONE

`ReconciliationReport` model, financial reports with revenue by utility type, credit purchase reports.

---

### 3.3 "Usage analytics per unit" — DONE

Unit consumption summary per utility, top consumers ranking, bulk vs sub-meter comparison, solar generation vs usage.

---

### 3.4 "Vacancy tracking" — DONE

`Unit.occupancy_status` with CHECK constraint: `occupied`, `vacant`, `maintenance`.

---

### 3.5 "Automated statements" — PARTIAL

**What exists:**
- PDF/CSV export via ReportLab (on-demand)

**What must be built:**
- [ ] Per-unit monthly statement PDF template (transaction list, opening/closing balance, consumption summary)
- [ ] `generate_monthly_statements` Celery task — runs on 1st of each month
- [ ] Email distribution to unit owners/tenants via Flask-Mail
- [ ] Statement archive (store generated PDFs or regenerate on demand)
- [ ] Admin setting to enable/disable per estate

**Dependencies:** Gap 1.7 (shared with smart reporting infrastructure)
**Effort:** L

---

## 4. Family / Multi-Account Layer (Layer 3)

### 4.1 "Master wallet" — TODO

**What exists:**
- Wallet is 1:1 with Unit via UNIQUE constraint

**What must be built:**
- [ ] `WalletGroup` model — groups multiple unit wallets under one owner
  - Fields: `id`, `name`, `owner_person_id` (FK), `created_at`
- [ ] `WalletGroupMembership` model — links wallets to group
  - Fields: `wallet_group_id`, `wallet_id`
- [ ] Master balance view — aggregate balance across grouped wallets
- [ ] Cross-wallet top-up — load funds to group, distribute to member wallets
- [ ] `GET /api/mobile/wallet-groups` — list user's wallet groups with aggregated balances
- [ ] `POST /api/mobile/wallet-groups/<id>/topup` — top up and distribute across members

**Dependencies:** None
**Effort:** L

---

### 4.2 "Multi-party access" — TODO

**What exists:**
- `UnitOwnership` and `UnitTenancy` link persons to units (not wallets)

**What must be built:**
- [ ] `WalletAccess` model
  - Fields: `id`, `wallet_id` (FK), `person_id` (FK), `access_level` (view/topup/manage), `granted_by`, `created_at`
- [ ] Permission checks on wallet endpoints (topup, view balance, view transactions)
- [ ] `POST /api/v1/wallets/<id>/grant-access` — admin grants wallet access to a person
- [ ] `POST /api/mobile/wallets/<id>/grant-access` — wallet manager invites others
- [ ] Mobile API filters wallet list by person's `WalletAccess` records

**Dependencies:** Gap 4.1 (wallet group makes this more useful)
**Effort:** M

---

### 4.3 "Spend controls" — TODO

**What exists:**
- `low_balance_threshold` for alerts only
- `electricity_minimum_activation` / `water_minimum_activation` (minimum to activate supply)

**What must be built:**
- [ ] Add to Wallet model: `daily_spend_limit` (Numeric, nullable), `monthly_spend_limit` (Numeric, nullable)
- [ ] Add to WalletAccess model: `topup_limit` (Numeric, nullable — max single top-up amount per user)
- [ ] Validation in `deduct_from_wallet()` — check daily/monthly limits, reject if exceeded
- [ ] Validation in top-up flow — check per-user top-up limits
- [ ] `GET /api/mobile/wallets/<id>/spending-summary` — current spend vs limits
- [ ] Alert when approaching spend limit (80% threshold)

**Dependencies:** Gap 4.2 (per-user limits need WalletAccess)
**Effort:** M

---

### 4.4 "Parents managing student apartments / Multi-property families" — TODO

**What exists:**
- A person can own multiple units via `UnitOwnership`

**What must be built:**
- [ ] This is covered by Gap 4.1 (WalletGroup) + Gap 4.2 (WalletAccess) + Gap 4.3 (SpendControls)
- [ ] Parent creates WalletGroup containing their units
- [ ] Parent has `manage` access, student has `view` + `topup` (capped)
- [ ] Push notifications to parent when student's balance is low
- [ ] Cross-unit notification routing (configurable per WalletAccess record)

**Dependencies:** Gaps 4.1, 4.2, 4.3
**Effort:** Included in 4.1-4.3

---

### 4.5 "Shared wallets with controlled permissions" — TODO

**What exists:** Nothing. Wallets cannot be shared.

**What must be built:**
- [ ] This is the combination of Gap 4.1 + 4.2 + 4.3
- [ ] WalletGroup provides the grouping
- [ ] WalletAccess provides the permissions
- [ ] Spend controls provide the limits
- [ ] Audit trail per user on shared wallet operations (use existing AuditLog)

**Dependencies:** Gaps 4.1, 4.2, 4.3
**Effort:** Included in 4.1-4.3

---

## 5. Body Corporate Dashboard (Layer 4)

### 5.1 "Full scheme visibility" — PARTIAL

**What exists:**
- Estate dashboard with units, meters, wallets, revenue

**What must be built:**
- [ ] Scheme-level financial KPIs: total levies collected, total utility spend, surplus/deficit
- [ ] Scheme health indicators: % meters online, % wallets in good standing, % units occupied
- [ ] Body corporate role template with scheme-only permissions
- [ ] Common area cost summary (from bulk meter readings minus unit meter sum)

**Dependencies:** None
**Effort:** M

---

### 5.2 "Common property metering" — DONE

Estate model has `bulk_electricity_meter_id` and `bulk_water_meter_id`. Bulk meter types exist. Communal usage calculated in reports.

---

### 5.3 "Levy integration" — TODO

**What exists:** Nothing.

**What must be built:**
- [ ] `Levy` model
  - Fields: `id`, `estate_id` (FK), `name`, `amount` (Numeric), `frequency` (monthly/quarterly/annually), `allocation_method` (equal/floor_area/custom), `is_active`, `effective_from`
- [ ] `LevyAllocation` model
  - Fields: `id`, `levy_id` (FK), `unit_id` (FK), `allocated_amount` (Numeric), `period_start`, `period_end`
- [ ] `LevyTransaction` — extends Transaction with levy-specific type: `levy_charge`, `levy_payment`
- [ ] Celery task: `generate_levy_charges` — runs monthly, creates levy transactions per unit
- [ ] Option to auto-deduct levies from wallet or track separately
- [ ] Levy arrears tracking and reporting
- [ ] Admin UI: configure levies per estate, view levy status per unit

**Dependencies:** None
**Effort:** XL

---

### 5.4 "Utility reconciliation" — DONE

Bulk vs sub-meter comparison with variance and loss calculations.

---

### 5.5 "Audit-ready reporting" — PARTIAL

**What exists:**
- `AuditLog` model with `old_values`/`new_values`, user/IP tracking
- Transaction ledger with `balance_before`/`balance_after`

**What must be built:**
- [ ] Audit compliance report PDF template (suitable for body corporate AGM)
  - Period summary, all transactions, all balance changes, variance analysis
- [ ] Period locking — prevent modifications to closed financial periods
  - `FinancialPeriod` model with `status` (open/closed/locked)
  - Validation: reject transaction modifications in locked periods
- [ ] Audit report export endpoint: `GET /api/v1/reports/audit?estate_id=X&period=YYYY-MM`

**Dependencies:** None
**Effort:** M

---

## 6. Managing Agent Interface (Layer 5)

### 6.1 "Bulk account management" — TODO

**What exists:**
- All CRUD operations are per-record only

**What must be built:**
- [ ] `POST /api/v1/units/bulk-import` — CSV upload for unit creation
- [ ] `POST /api/v1/persons/bulk-import` — CSV upload for resident import
- [ ] `POST /api/v1/meters/bulk-import` — CSV upload for meter registration
- [ ] `POST /api/v1/wallets/bulk-topup` — top up multiple wallets in one request
- [ ] CSV template download endpoints for each entity
- [ ] Validation and error reporting per row (partial success support)
- [ ] Import history/audit log

**Dependencies:** None
**Effort:** L

---

### 6.2 "Tenant onboarding" — TODO

**What exists:**
- `UnitTenancy` model, `MobileInvite` model, individual person/tenancy creation

**What must be built:**
- [ ] `POST /api/v1/units/<id>/onboard-tenant` — single endpoint that:
  1. Creates Person (or links existing)
  2. Creates UnitTenancy with `move_in_date`
  3. Creates MobileUser account
  4. Creates or resets Wallet
  5. Captures opening meter readings
  6. Sends MobileInvite (SMS + email)
- [ ] `POST /api/v1/units/<id>/offboard-tenant` — single endpoint that:
  1. Captures closing meter readings
  2. Calculates final consumption and charges
  3. Sets `move_out_date` on UnitTenancy
  4. Settles wallet (refund remaining balance or flag debt)
  5. Deactivates MobileUser account
- [ ] Bulk onboarding via CSV (for managing agents onboarding entire buildings)

**Dependencies:** Gap 6.1 (bulk import reuses same CSV infrastructure)
**Effort:** M

---

### 6.3 "Arrears monitoring" — PARTIAL

**What exists:**
- Low balance alert reports, `is_suspended` / `suspension_reason` on wallet

**What must be built:**
- [ ] `credit_limit` field on Wallet model (Numeric, nullable — max negative balance allowed)
- [ ] Arrears aging calculation: 30/60/90 day buckets based on when balance went negative
- [ ] Arrears report endpoint: `GET /api/v1/reports/arrears?estate_id=X`
  - Per-unit: current balance, days in arrears, total debt, last payment date
- [ ] Arrears escalation rules per estate:
  - 0 days: warning notification
  - 30 days: restriction notification
  - 60 days: suspension (set `is_suspended = True`)
  - 90 days: escalate to managing agent
- [ ] `check_arrears_escalation` Celery task (daily)
- [ ] Arrears notification sequences (in-app + SMS + email)

**Dependencies:** Gap 1.2 (credit control)
**Effort:** L

---

### 6.4 "Automated billing exports" — DONE

CSV and PDF export for all report types via `GET /api/reports/export/<report_type>?format=csv|pdf`.

---

### 6.5 "API integration" — PARTIAL

**What exists:**
- REST API with 18+ route files, JSON responses, pagination
- Session-based authentication only

**What must be built:**
- [ ] `ApiKey` model — `id`, `key_hash`, `name`, `user_id`, `permissions` (JSON), `is_active`, `last_used_at`, `created_at`
- [ ] API key authentication middleware (check `X-API-Key` header alongside session auth)
- [ ] API key management endpoints: create, revoke, list
- [ ] Rate limiting per API key (e.g., 1000 requests/hour)
- [ ] OpenAPI/Swagger documentation auto-generated from routes
- [ ] Webhook model for event notifications to external systems
  - Events: `wallet.topup`, `wallet.low_balance`, `meter.reading`, `meter.offline`, `tenant.onboarded`

**Dependencies:** None
**Effort:** L

---

## 7. Utility & Bulk Supply Layer (Layer 6)

### 7.1 "Bulk meter reconciliation" — DONE

Bulk vs sub-meter comparison with variance/loss calculation in reports.

---

### 7.2 "Loss detection" — PARTIAL

**What exists:**
- Variance/loss amounts in reconciliation reports

**What must be built:**
- [ ] `loss_threshold_percentage` field on Estate model (default 15%)
- [ ] `check_utility_losses` Celery task (daily) — compare bulk vs sub-meter, alert if threshold exceeded
- [ ] Loss trend tracking — store daily loss percentages for trend analysis
- [ ] Loss alert notification to estate admin
- [ ] Loss analysis dashboard widget: trend chart, current loss %, threshold line

**Dependencies:** None
**Effort:** M

---

### 7.3 "Settlement management" — TODO

**What exists:** Nothing.

**What must be built:**
- [ ] `SettlementRule` model
  - Fields: `id`, `estate_id` (FK), `party_name`, `party_type` (operator/body_corporate/utility/other), `share_percentage` (Numeric), `share_type` (percentage/fixed/remainder), `bank_reference`, `is_active`
- [ ] `SettlementRun` model
  - Fields: `id`, `estate_id` (FK), `period_start`, `period_end`, `total_revenue`, `total_distributed`, `status` (pending/completed/failed), `run_date`, `created_by`
- [ ] `SettlementLineItem` model
  - Fields: `id`, `settlement_run_id` (FK), `settlement_rule_id` (FK), `amount`, `party_name`, `status`
- [ ] Settlement calculation engine:
  1. Sum all completed transactions for estate in period
  2. Apply settlement rules (percentage splits)
  3. Create line items for each party
  4. Mark run as completed
- [ ] `run_monthly_settlement` Celery task
- [ ] Settlement report endpoint + PDF export
- [ ] Admin UI for configuring settlement rules per estate
- [ ] Settlement history and audit trail

**Dependencies:** Gap 1.1 (payments working), Gap 1.6 (shared with automated settlement)
**Effort:** XL

---

### 7.4 "Revenue assurance tools" — PARTIAL

**What exists:**
- Revenue reports, PayFast reconciliation task, audit trail, variance reporting

**What must be built:**
- [ ] Consumption anomaly scoring — flag readings that deviate significantly from expected patterns
- [ ] Tamper detection alerts — integrate with `MeterAlert` model (`tamper_detected` type already exists)
  - Trigger on: sudden drop to zero, impossible negative readings, reading < previous reading
- [ ] Revenue leakage report: expected revenue (from meter readings) vs actual revenue (from transactions)
- [ ] Meter bypass detection: flag units with zero consumption but known occupancy
- [ ] Suspicious pattern dashboard widget

**Dependencies:** None
**Effort:** L

---

## 8. How The Wallet Works (5-Step Flow)

### 8.1 "User loads funds (EFT, card, integrated payment gateway)" — PARTIAL

Same as Gap 1.1. PayFast handles EFT + card + instant EFT — must move to production.

Additionally:
- [ ] Manual EFT reconciliation for direct bank deposits (admin workflow: mark deposit → credit wallet)

**Dependencies:** Gap 1.1
**Effort:** Included in 1.1

---

### 8.2 "Funds reflect instantly" — PARTIAL

Works for PayFast sandbox. Must complete production setup (Gap 1.1).

---

### 8.3 "Meter deducts per kWh / kL in real time" — PARTIAL (critical)

**What exists:**
- Consumption billing deducts on every MQTT reading
- Allows infinite negative balance (comment: "CAN GO NEGATIVE - no disconnection!")
- Disconnect task code exists but is commented out in dry-run mode

**What must be built:**
- [ ] Feature flag: `credit_control_enabled` in SystemSetting (per estate, default OFF for safe rollout)
- [ ] Modify `deduct_from_wallet()` in Monitor billing engine:
  - Check `credit_control_enabled`
  - If electricity balance <= 0 and credit control enabled: trigger disconnect
  - If water balance < -`credit_limit`: flag for arrears (no physical disconnect)
- [ ] Enable `disconnect_zero_balance_meters` Celery task (remove dry-run)
  - Gate behind feature flag
  - Add ChirpStack relay OFF command via `chirpstack_service.py`
- [ ] Reconnection workflow:
  - After successful top-up, check if meter was disconnected
  - If balance >= `electricity_minimum_activation` (R20): send relay ON command
  - Create `reconnection` transaction and notification
- [ ] Test with single meter before enabling estate-wide

**Dependencies:** None — this is foundational
**Effort:** M

---

### 8.4 "Central ledger records every transaction" — DONE

Transaction model with 30+ fields, unique transaction numbers, full balance tracking, AuditLog for all entity changes.

---

### 8.5 "Settlement rules distribute funds automatically" — TODO

Same as Gap 1.6 / 7.3. Settlement engine must be built.

---

### 8.6 "No manual reconciliation" — PARTIAL

**What exists:**
- PayFast reconciliation runs daily via Celery (`reconcile_payfast_transactions`)
- Bulk vs sub-meter reconciliation is a manual on-demand report

**What must be built:**
- [ ] `run_daily_reconciliation` Celery task:
  - Compare all consumption transactions vs meter readings (ensure nothing missed)
  - Compare all payment transactions vs payment gateway records
  - Compare bulk meter vs sum of unit meters
  - Generate variance report and flag discrepancies
- [ ] Auto-reconciliation for billing: verify every meter reading has a matching consumption transaction
- [ ] Scheduled reconciliation report email to estate admins
- [ ] Reconciliation dashboard with pass/fail status per estate

**Dependencies:** None
**Effort:** L

---

## 9. Why Quantify (Selling Points)

### 9.1 "Secure Ledger Architecture" — PARTIAL

**What exists:**
- PostgreSQL with audit logging, transaction tracking with balance_before/after

**What must be built to justify "Secure Ledger":**
- [ ] Append-only transaction table (add DB trigger that prevents UPDATE/DELETE on transactions)
- [ ] Cryptographic hash chain on transactions:
  - Add `hash` field to Transaction model
  - Each transaction's hash = SHA-256(previous_hash + transaction_data)
  - Allows integrity verification: any tampering breaks the chain
- [ ] Period locking (shared with Gap 5.5) — prevent modification of closed periods
- [ ] Integrity verification endpoint: `GET /api/v1/ledger/verify?wallet_id=X` — validates hash chain

**Dependencies:** None
**Effort:** M

---

### 9.2 "Every transaction recorded and auditable" — DONE

No gaps.

---

### 9.3 "Built for Developments" — DONE

No gaps.

---

### 9.4 "Revenue Assurance / Eliminates token fraud" — PARTIAL

**What exists:**
- Tokenless system, audit trail, PayFast reconciliation

**What must be built:**
- [ ] Credit control (Gap 8.3) — prevents infinite debt
- [ ] Tamper detection (Gap 7.4) — flags suspicious meter behaviour
- [ ] Revenue leakage report (Gap 7.4)

**Dependencies:** Gaps 8.3, 7.4
**Effort:** Included in 8.3 + 7.4

---

### 9.5 "Advanced Analytics — Consumption patterns, Demand profiling, Loss analysis" — TODO

**What exists:**
- 30-day rolling average for high-usage detection
- Basic consumption reports

**What must be built:**
- [ ] Consumption pattern classification per unit:
  - Calculate: avg daily usage, peak hour usage, weekend vs weekday
  - Classify: light/moderate/heavy consumer
  - Store in new `ConsumptionProfile` model per unit per utility
- [ ] Demand profiling:
  - Aggregate readings by hour-of-day across estate
  - Identify peak/off-peak demand periods
  - Demand profile report and chart
- [ ] Loss analysis:
  - Bulk vs sub-meter trend over time
  - Loss percentage trend chart
  - Anomalous loss spike detection
- [ ] `update_consumption_profiles` Celery task (weekly)
- [ ] Analytics dashboard section with profile charts and demand curves

**Dependencies:** Gap 7.2 (loss detection data feeds into this)
**Effort:** L

---

## 10. Communication Protocols

**Brochure claim:** "RS485 / Modbus / LoRaWAN / 4G / NB-IoT / IoT-ready"

| Protocol | Status | What Must Be Built |
|----------|--------|-------------------|
| **LoRaWAN** | DONE | Nothing — full ChirpStack MQTT integration, 3 device decoders, active production |
| **Modbus** | PARTIAL | Direct RS485/Modbus RTU master listener (currently only via LoRaWAN gateway passthrough). Build: serial port listener service, Modbus register map config, reading extraction for common meters |
| **RS485** | TODO | Physical layer for Modbus. Build: RS485 serial adapter config, add `rs485` to `communication_type` CHECK constraint, direct meter polling service |
| **4G / Cellular** | TODO | Build: HTTP/MQTT endpoint for cellular meter gateways to push data. Add cellular gateway registration. Decode payloads from 4G-connected meters. `cellular` already in DB CHECK constraint |
| **NB-IoT** | TODO | Build: NB-IoT endpoint (typically MQTT or CoAP). Add `nbiot` to `communication_type` CHECK constraint. Decoder support for NB-IoT meter payloads |

**Implementation approach:**
- [ ] Create abstraction layer in Monitor: `DataIngestionHandler` base class
- [ ] Current MQTT listener becomes `LoRaWANIngestionHandler`
- [ ] Add `ModbusIngestionHandler` — serial port polling
- [ ] Add `CellularIngestionHandler` — HTTP webhook receiver
- [ ] Add `NBIoTIngestionHandler` — CoAP/MQTT listener
- [ ] All handlers share the same decode → calculate → bill → store pipeline

**Dependencies:** None (each protocol is independent)
**Effort:** M per protocol (Modbus/RS485), S per protocol (4G/NB-IoT if just HTTP endpoints)

---

## 11. Optional Add-Ons

### 11.1 "Smart demand management" — TODO

**What exists:** Nothing.

**What must be built:**
- [ ] Demand thresholds per estate: max kW per unit, max kW per estate
- [ ] `DemandProfile` model: `estate_id`, `max_demand_kw`, `peak_hours`, `restriction_level`
- [ ] Real-time demand monitoring (aggregate current power readings across estate)
- [ ] Demand response actions:
  - Warning notification when approaching threshold
  - Load restriction relay command when exceeded (via ChirpStack)
  - Automatic restoration when demand drops
- [ ] Demand analytics: peak demand history, demand forecasting
- [ ] `monitor_estate_demand` Celery task (every 15 minutes during peak hours)

**Dependencies:** Gap 8.3 (relay control infrastructure), Gap 10 (multiple protocols for more meter data)
**Effort:** XL

---

### 11.2 "Solar integration" — PARTIAL

**What exists:**
- `solar` meter type, `solar_balance`, `solar_meter_id`, `solar_free_allocation_kwh` on estate (default 50 kWh)
- Transaction types: `topup_solar`, `consumption_solar`
- Solar generation vs usage report

**What must be built:**
- [ ] Solar allocation logic in `consumption_billing.py`:
  - Track monthly solar generation per estate from solar meter readings
  - Calculate per-unit allocation: `estate_solar_kwh / active_units` (or by floor area)
  - Apply free allocation before billing grid electricity
  - Excess solar beyond allocation: bill at reduced solar rate
- [ ] Solar feed-in tracking (units with own solar panels feeding back)
- [ ] Net metering calculation: solar generated minus grid consumed
- [ ] Solar allocation report per estate and per unit
- [ ] `calculate_solar_allocations` Celery task (monthly)

**Dependencies:** None (existing schema supports this)
**Effort:** M

---

### 11.3 "Hot Water as a Service (HWS)" — PARTIAL

**What exists:**
- `hot_water` meter type, `hot_water_balance`, billing works via standard consumption flow

**What must be built:**
- [ ] HWS rate table type with standing charge + volumetric component
  - Standing charge: fixed monthly fee for hot water service
  - Volumetric: per-litre charge for actual usage
- [ ] HWS-specific transaction types: `hws_standing_charge`, `hws_consumption`
- [ ] `generate_hws_standing_charges` Celery task (monthly)
- [ ] Temperature data integration (from meter telemetry — `temperature` field exists on `MeterReading`)
- [ ] HWS service dashboard: temperature monitoring, consumption per unit, cost vs standing charge

**Dependencies:** None
**Effort:** L

---

### 11.4 "Carbon footprint reporting" — TODO

**What exists:** Nothing.

**What must be built:**
- [ ] `CarbonFactor` model: `utility_type`, `emission_factor_kg_per_kwh` (or per_kl), `source`, `effective_from`
  - Default factors: Eskom grid ~0.95 kgCO2e/kWh, water ~0.376 kgCO2e/kL
- [ ] Carbon calculation in reports:
  - Per unit: `consumption_kwh * emission_factor = kgCO2e`
  - Per estate: aggregate
  - Solar offset: solar kWh * grid factor = avoided emissions
- [ ] Carbon footprint report endpoint: `GET /api/v1/reports/carbon?estate_id=X&period=YYYY-MM`
- [ ] Carbon dashboard widget: monthly emissions trend, solar offset, per-unit comparison
- [ ] PDF export for sustainability reporting

**Dependencies:** None
**Effort:** M

---

### 11.5 "Tariff automation" — PARTIAL

**What exists:**
- Rate table model with `effective_from` dating and versioning
- Manual rate table CRUD

**What must be built:**
- [ ] Tariff schedule import: admin uploads CSV/JSON with new rates + effective date
- [ ] `apply_scheduled_tariffs` Celery task — activates new rate tables on their `effective_from` date
- [ ] Tariff change notifications: alert affected users N days before new rates take effect
- [ ] Tariff comparison report: old vs new rates, estimated impact per unit
- [ ] Future: Eskom/municipal tariff API integration (scrape or manual import with standard templates)

**Dependencies:** None
**Effort:** L

---

### 11.6 "Smart alerts & AI anomaly detection" — PARTIAL

**What exists:**
- High-usage detection (50%+ above 30-day average)
- Low/critical credit alerts
- `MeterAlert` model with `tamper_detected`, `abnormal_usage`, `meter_fault` types
- Notification service (in_app, email, sms, push channels)

**What must be built:**
- [ ] Statistical anomaly detection (not ML, but statistically sound):
  - Z-score based: flag readings > 3 standard deviations from unit's historical mean
  - Sudden change detection: flag if consumption changes by >200% between consecutive readings
  - Zero consumption detection: flag occupied units with no readings for >24 hours
  - Negative consumption: flag if reading < previous reading (meter rollback/tamper)
- [ ] Anomaly scoring model: assign severity score (0-100) based on deviation magnitude
- [ ] `detect_consumption_anomalies` Celery task (daily)
- [ ] Alert routing: anomalies create `MeterAlert` records + notifications
- [ ] Anomaly dashboard: list of flagged readings with severity, investigation status
- [ ] Enable all notification channels:
  - [ ] Email delivery via Flask-Mail (infrastructure exists)
  - [ ] SMS delivery via Clickatell (service exists in `sms_service.py`)
  - [ ] Push notification integration (FCM or similar)

**Dependencies:** None
**Effort:** L

---

## 12. Implementation Roadmap

### Guiding Principles

1. **Feature flags** — Every new behaviour gated via `SystemSetting` (model already exists). Production keeps running on old path until flag is enabled.
2. **Additive migrations only** — New columns are `nullable=True` or have defaults. No destructive schema changes.
3. **Tests first** — Each gap gets a test file before implementation. Existing pytest + SQLite in-memory infrastructure supports this.
4. **One branch per gap** — Self-contained, independently deployable, easy to rollback.
5. **Monitor project untouched** until System changes are proven — The MQTT listener is stable in production.

---

### Phase 0: Foundation (Week 1)
*Build the safety net before any features*

| # | Gap | What | Effort | Depends On |
|---|-----|------|--------|------------|
| 0A | New | Feature flag utility using `SystemSetting` model | S | — |
| 0B | New | Test infrastructure hardening (conftest fixtures for new models) | S | — |

---

### Phase 1: Production Safety (Weeks 2-3)
*Fix what's broken — the system allows infinite debt and payments are sandbox-only*

| # | Gap | What | Effort | Depends On |
|---|-----|------|--------|------------|
| 1A | 8.3 | Credit control (wallet limits + disconnect/reconnect) | M | 0A |
| 1B | 1.1 | PayFast production setup | M | — |
| 1C | 9.1 | Secure ledger (append-only transactions + hash chain) | M | — |

---

### Phase 2: Complete Tenant & Owner Experience (Weeks 4-6)
*Fill the gaps tenants and owners will notice first*

| # | Gap | What | Effort | Depends On |
|---|-----|------|--------|------------|
| 2A | 2.3 | Tenant consumption history API (mobile graphs) | M | — |
| 2B | 11.2 | Solar allocation logic in billing | M | — |
| 2C | 6.3 | Arrears monitoring (aging + credit limits + escalation) | L | 1A |
| 2D | 3.5 | Automated monthly statements (Celery + PDF + email) | L | — |
| 2E | 1.7 | Scheduled report generation + subscriptions | M | 2D |

---

### Phase 3: Managing Agent & Body Corporate (Weeks 7-9)
*Features these user types need before they'll adopt*

| # | Gap | What | Effort | Depends On |
|---|-----|------|--------|------------|
| 3A | 6.1 | Bulk operations (CSV import for units/persons/meters) | L | — |
| 3B | 6.2 | Tenant onboarding/offboarding workflow | M | 3A |
| 3C | 5.1 | Body corporate scheme dashboard + KPIs | M | — |
| 3D | 5.5 | Audit compliance reports (PDF + period locking) | M | 1C |
| 3E | 6.5 | API key authentication + rate limiting | L | — |

---

### Phase 4: Family & Multi-Account (Weeks 10-11)
*The entire Layer 3 — built as a connected set*

| # | Gap | What | Effort | Depends On |
|---|-----|------|--------|------------|
| 4A | 4.1 | WalletGroup model (master wallet) | L | — |
| 4B | 4.2 | WalletAccess model (multi-party permissions) | M | 4A |
| 4C | 4.3 | Spend controls (daily/monthly limits) | M | 4B |

*Gaps 4.4 and 4.5 are automatically fulfilled by 4A + 4B + 4C*

---

### Phase 5: Revenue, Reconciliation & Analytics (Weeks 12-14)
*The financial backbone for scale*

| # | Gap | What | Effort | Depends On |
|---|-----|------|--------|------------|
| 5A | 8.6 | Automated reconciliation (Celery task + dashboard) | L | — |
| 5B | 7.2 | Loss detection alerts (threshold + trend) | M | — |
| 5C | 7.4 | Revenue assurance (anomaly scoring + tamper detection) | L | — |
| 5D | 9.5 | Advanced analytics (consumption profiles + demand curves) | L | 5B |
| 5E | 1.6/7.3 | Settlement engine (rules + runs + distribution) | XL | 5A |

---

### Phase 6: Communication Protocols (Weeks 15-16)
*Expand beyond LoRaWAN*

| # | Gap | What | Effort | Depends On |
|---|-----|------|--------|------------|
| 6A | 10 | Modbus/RS485 direct listener | M | — |
| 6B | 10 | 4G cellular HTTP gateway endpoint | S | — |
| 6C | 10 | NB-IoT endpoint | S | — |

---

### Phase 7: Optional Add-Ons (Weeks 17-22)
*Build last — these are add-ons, not core*

| # | Gap | What | Effort | Depends On |
|---|-----|------|--------|------------|
| 7A | 5.3 | Levy integration | XL | — |
| 7B | 11.6 | Smart alerts + anomaly detection (statistical) | L | 5C |
| 7C | 11.3 | Hot Water as a Service billing model | L | — |
| 7D | 11.4 | Carbon footprint reporting | M | — |
| 7E | 11.5 | Tariff automation (scheduled activation + notifications) | L | — |
| 7F | 11.1 | Smart demand management | XL | 1A, 6A-6C |

---

### Summary

| Phase | Duration | Gaps Closed | Key Deliverable |
|-------|----------|-------------|-----------------|
| 0 | Week 1 | 2 | Safety net (feature flags + test infra) |
| 1 | Weeks 2-3 | 3 | Production-ready payments + credit control |
| 2 | Weeks 4-6 | 5 | Complete tenant/owner experience |
| 3 | Weeks 7-9 | 5 | Managing agent + body corporate ready |
| 4 | Weeks 10-11 | 3 | Family/multi-account layer (Layer 3) |
| 5 | Weeks 12-14 | 5 | Revenue assurance + settlement |
| 6 | Weeks 15-16 | 3 | Multi-protocol support |
| 7 | Weeks 17-22 | 6 | All optional add-ons |
| **Total** | **~22 weeks** | **32 gaps** | **Full brochure compliance** |

---

## Dependency Graph

```
Phase 0: Feature Flags + Test Infra
    │
    ├─→ Phase 1: Credit Control ──→ Phase 2C: Arrears
    │       │                            │
    │       └──────────────────────→ Phase 7F: Demand Mgmt
    │
    ├─→ Phase 1: PayFast Prod ──→ Phase 5E: Settlement
    │
    ├─→ Phase 1: Secure Ledger ──→ Phase 3D: Audit Reports
    │
    ├─→ Phase 2: Statements ──→ Phase 2E: Report Subscriptions
    │
    ├─→ Phase 3A: Bulk Ops ──→ Phase 3B: Onboarding
    │
    ├─→ Phase 4A: WalletGroup ──→ 4B: Access ──→ 4C: Spend Controls
    │
    ├─→ Phase 5A: Reconciliation ──→ Phase 5E: Settlement
    │
    ├─→ Phase 5B: Loss Detection ──→ Phase 5D: Analytics
    │
    └─→ Phase 5C: Revenue Assurance ──→ Phase 7B: AI Alerts
```

# Rate Table Billing & Wallet Deductions

This document describes how the Quantify Metering system calculates consumption costs and deducts from tenant wallets based on rate tables.

---

## Table of Contents

1. [Overview](#overview)
2. [Utility Types](#utility-types)
3. [Rate Table Resolution](#rate-table-resolution)
4. [Pricing Models](#pricing-models)
   - [Flat Rate](#1-flat-rate)
   - [Tiered Rate](#2-tiered-rate)
   - [Time of Use (TOU)](#3-time-of-use-tou)
   - [Seasonal](#4-seasonal)
   - [Fixed Charge](#5-fixed-charge)
   - [Demand Charge](#6-demand-charge)
   - [Hot Water Dual-Component](#7-hot-water-dual-component)
5. [Markup](#markup)
6. [VAT](#vat)
7. [Billing Flow](#billing-flow)
8. [Worked Examples](#worked-examples)
9. [Default Rates](#default-rates)
10. [Implementation Status](#implementation-status)

---

## Overview

When a meter sends a reading, the system automatically:
1. Calculates consumption since the last reading
2. Looks up the applicable rate table
3. Computes the cost using the rate structure
4. Applies any estate-level markup
5. Deducts the total from the tenant's wallet
6. Records a transaction for the audit trail

All amounts are in **South African Rand (ZAR)**.

---

## Utility Types

| Utility Type | Meter Unit | Billing Unit | Conversion |
|-------------|-----------|-------------|------------|
| Electricity | kWh | kWh | None |
| Water | Litres | Kilolitres (kL) | litres / 1000 |
| Hot Water | Litres | kL + kWh | Dual-component (see below) |
| Solar | kWh | kWh | None |

---

## Rate Table Resolution

When billing a meter reading, the system resolves the rate table in this order:

```
1. Unit-level rate table (if assigned to the specific unit)
   |
   v  (not found)
2. Estate-level rate table (assigned to the estate the unit belongs to)
   |
   v  (not found)
3. Default flat rate (hardcoded fallback)
```

This allows estates to set a standard rate for all units, with the ability to override specific units that need different pricing.

**For hot water**, the resolution includes an additional fallback:
```
1. Unit hot_water_rate_table_id
2. Unit water_rate_table_id (fallback)
3. Estate hot_water_rate_table_id
4. Estate water_rate_table_id (fallback)
5. Default flat rate
```

---

## Pricing Models

### 1. Flat Rate

The simplest pricing model. A single rate per unit of consumption.

**Rate structure:**
```json
{
  "flat_rate": 2.50
}
```

**Formula:**
```
cost = consumption x flat_rate
```

**Example:** 150 kWh of electricity at R2.50/kWh
```
cost = 150 x R2.50 = R375.00
```

---

### 2. Tiered Rate

Progressive pricing where different consumption bands are charged at different rates. Higher usage tiers typically have higher rates to encourage conservation.

**Rate structure:**
```json
{
  "tiers": [
    { "from": 0, "to": 50, "rate": 2.00 },
    { "from": 50, "to": 150, "rate": 2.50 },
    { "from": 150, "to": null, "rate": 3.00 }
  ]
}
```

- `from`: Start of the tier (inclusive)
- `to`: End of the tier (exclusive). `null` means unlimited (the final tier).
- `rate`: Price per unit within this tier

**Formula:**
```
For each tier (sorted by "from"):
  tier_consumption = min(remaining_consumption, tier.to - tier.from)
  tier_cost = tier_consumption x tier.rate
  remaining_consumption -= tier_consumption

total_cost = sum of all tier costs
```

**Example:** 200 kWh with the tiers above
```
Tier 1:  0-50 kWh   = 50 x R2.00  = R100.00
Tier 2:  50-150 kWh  = 100 x R2.50 = R250.00
Tier 3:  150+ kWh    = 50 x R3.00  = R150.00
                                      ---------
Total:                                R500.00
```

---

### 3. Time of Use (TOU)

Different rates apply depending on the time of day and whether it is a weekday or weekend. The rate that applies is determined by when the meter reading is received.

**Rate structure:**
```json
{
  "time_of_use": [
    {
      "period_name": "Peak",
      "start_time": "17:00",
      "end_time": "22:00",
      "weekdays": true,
      "weekends": false,
      "rate": 4.50
    },
    {
      "period_name": "Standard",
      "start_time": "06:00",
      "end_time": "17:00",
      "weekdays": true,
      "weekends": true,
      "rate": 2.85
    },
    {
      "period_name": "Off-Peak",
      "start_time": "22:00",
      "end_time": "06:00",
      "weekdays": true,
      "weekends": true,
      "rate": 1.50
    }
  ]
}
```

- `period_name`: Label for the period
- `start_time` / `end_time`: 24-hour format. Supports overnight periods (e.g. 22:00 to 06:00)
- `weekdays` / `weekends`: Whether this period applies on weekdays and/or weekends
- `rate`: Price per unit during this period

**Formula:**
```
1. Check current time and day of week
2. Find the matching TOU period
3. cost = consumption x matched_period.rate
```

**Example:** 80 kWh reading received at 19:00 on a Tuesday
```
Time = 19:00, Day = Tuesday (weekday)
Matches "Peak" period (17:00-22:00, weekdays)
Rate = R4.50/kWh

cost = 80 x R4.50 = R360.00
```

**Overnight periods:** A period like 22:00 to 06:00 correctly wraps across midnight. A reading at 02:00 would match this period.

---

### 4. Seasonal

Different rates for summer and winter months.

**Rate structure:**
```json
{
  "seasonal": {
    "summer": 3.50,
    "winter": 2.80
  }
}
```

> **Status: Not yet implemented in billing engine.** This model can be configured in the rate table builder UI but is not currently used during wallet deductions. See [Implementation Status](#implementation-status).

**Intended formula:**
```
if current_month in summer_months:
    cost = consumption x summer_rate
else:
    cost = consumption x winter_rate
```

---

### 5. Fixed Charge

A fixed monthly fee added on top of consumption-based charges. Typically used for service fees or basic infrastructure charges.

**Rate structure:**
```json
{
  "flat_rate": 2.50,
  "fixed_charge": 50.00
}
```

> **Status: Not yet implemented in billing engine.** This model can be configured in the rate table builder UI but is not currently used during wallet deductions. See [Implementation Status](#implementation-status).

**Intended formula:**
```
consumption_cost = consumption x flat_rate
total = consumption_cost + fixed_charge
```

**Example:** 100 kWh at R2.50/kWh with R50.00 fixed charge
```
Consumption: 100 x R2.50 = R250.00
Fixed charge:               R50.00
                            --------
Total:                      R300.00
```

---

### 6. Demand Charge

A charge based on peak demand, typically for commercial or industrial metering.

**Rate structure:**
```json
{
  "flat_rate": 2.50,
  "demand_charge": 100.00
}
```

> **Status: Not yet implemented in billing engine.** This model can be configured in the rate table builder UI but is not currently used during wallet deductions. See [Implementation Status](#implementation-status).

**Intended formula:**
```
consumption_cost = consumption x flat_rate
total = consumption_cost + demand_charge
```

---

### 7. Hot Water Dual-Component

Hot water billing has **two cost components** because heating water requires both water and electricity:

1. **Water component** - the volume of heated water consumed (R per kL)
2. **Electricity component** - the energy required to heat that water (R per kWh), derived from the water volume using a conversion factor

**Rate structure:**
```json
{
  "water_component": {
    "flat_rate": 18.00
  },
  "electricity_component": {
    "flat_rate": 2.50
  },
  "conversion_factor": 0.065
}
```

The water component can also use tiered pricing:
```json
{
  "water_component": {
    "tiers": [
      { "from": 0, "to": 6, "rate": 15.00 },
      { "from": 6, "to": null, "rate": 22.00 }
    ]
  },
  "electricity_component": {
    "flat_rate": 2.50
  },
  "conversion_factor": 0.065
}
```

**Parameters:**
- `conversion_factor`: kWh of electricity required to heat 1 litre of water (default: 0.065). This depends on the heating system efficiency and temperature rise.

**Formula:**
```
1. volume_kl = litres / 1000
2. electricity_kwh = litres x conversion_factor

3. water_cost = volume_kl x water_rate
4. electricity_cost = electricity_kwh x electricity_rate
5. total = water_cost + electricity_cost
```

**Example:** 500 litres of hot water (R18/kL, R2.50/kWh, factor 0.065)
```
volume_kl      = 500 / 1000         = 0.5 kL
electricity_kwh = 500 x 0.065       = 32.5 kWh

water_cost      = 0.5 x R18.00      = R9.00
electricity_cost = 32.5 x R2.50     = R81.25
                                       -------
total                                = R90.25
```

**Backward compatibility:** Hot water meters that do not have a dedicated hot water rate table assigned will continue to use the estate's water rate table with single-component billing (same as cold water).

---

## Markup

Estates can apply a **percentage markup** on top of the calculated rate. This is configured per estate, per utility type.

**Estate-level markup fields:**
- `electricity_markup_percentage`
- `water_markup_percentage`
- `hot_water_markup_percentage`

**Formula:**
```
final_cost = base_cost x (1 + markup_percentage / 100)
```

**Example:** R250.00 base cost with 15% markup
```
final_cost = R250.00 x (1 + 15/100)
           = R250.00 x 1.15
           = R287.50
```

For hot water dual-component billing, markup is applied to **both** the water and electricity components individually.

---

## VAT

VAT (15%) is **not** applied during wallet deductions. The billing engine calculates and deducts pre-VAT amounts only.

VAT is shown in the rate table builder preview for informational purposes, but it is not included in the actual wallet deduction.

---

## Billing Flow

Step-by-step process from meter reading to wallet deduction:

```
                    METER READING RECEIVED
                           |
                           v
               Calculate consumption since
                    last reading
                           |
                           v
              Resolve rate table for this meter
           (Unit level -> Estate level -> Default)
                           |
                           v
               Get the rate structure JSON
               and markup percentage
                           |
                           v
         +------- Is this hot water with -------+
         |        dual-component rates?         |
         |                                       |
      YES |                                 NO  |
         v                                       v
  Calculate water cost              Calculate cost using:
  Calculate electricity cost        - Flat rate, OR
  (using conversion factor)         - Tiered rate, OR
         |                          - Time of Use rate
         v                                       |
  Apply markup to both                           v
  components                          Apply markup
         |                                       |
         +----------- Combine ---------+
                           |
                           v
                Deduct from tenant wallet
                (wallet.balance -= cost)
                           |
                           v
               Update utility spend tracker
          (e.g. wallet.electricity_balance)
                           |
                           v
               Create transaction record
             (amount, rate, timestamps)
                           |
                           v
               Link transaction to reading
                (reading.is_billed = true)
```

---

## Worked Examples

### Example 1: Tiered Water Billing

**Setup:**
- Estate: "Riverside Apartments"
- Water rate table: Tiered
  - 0-6 kL: R15.00/kL
  - 6-10 kL: R22.00/kL
  - 10+ kL: R30.00/kL
- Water markup: 10%
- Meter reading: 8,500 litres consumed

**Calculation:**
```
Consumption = 8,500 litres = 8.5 kL

Tier 1:  0-6 kL  = 6.0 x R15.00 = R90.00
Tier 2:  6-10 kL = 2.5 x R22.00 = R55.00
                                    -------
Base cost:                          R145.00

With 10% markup:
Final = R145.00 x 1.10 = R159.50

Wallet deduction: -R159.50
```

### Example 2: TOU Electricity at Peak

**Setup:**
- Estate: "City Centre Office Park"
- Electricity rate table: Time of Use
  - Peak (17:00-22:00 weekdays): R4.50/kWh
  - Standard (06:00-17:00): R2.85/kWh
  - Off-Peak (22:00-06:00): R1.50/kWh
- Electricity markup: 20%
- Meter reading: 250 kWh at 19:30 on Wednesday

**Calculation:**
```
Time = 19:30, Day = Wednesday (weekday)
Matched period: Peak (17:00-22:00, weekdays)
Rate = R4.50/kWh

Base cost = 250 x R4.50 = R1,125.00

With 20% markup:
Final = R1,125.00 x 1.20 = R1,350.00

Wallet deduction: -R1,350.00
```

### Example 3: Hot Water Dual-Component

**Setup:**
- Estate: "Mountain View Estate"
- Hot water rate table:
  - Water: R18.00/kL (flat)
  - Electricity: R3.00/kWh (flat)
  - Conversion factor: 0.065 kWh/L
- Hot water markup: 15%
- Meter reading: 300 litres consumed

**Calculation:**
```
volume_kl      = 300 / 1000     = 0.3 kL
electricity_kwh = 300 x 0.065   = 19.5 kWh

Water base      = 0.3 x R18.00  = R5.40
Elec base       = 19.5 x R3.00  = R58.50
                                   -------
Total base:                        R63.90

With 15% markup:
Water final  = R5.40 x 1.15  = R6.21
Elec final   = R58.50 x 1.15 = R67.28
                                 -------
Total final:                     R73.49

Wallet deduction: -R73.49
```

### Example 4: Flat Rate Electricity (No Markup)

**Setup:**
- Estate: "Greenfield Complex"
- Electricity rate table: Flat rate R2.50/kWh
- Markup: 0%
- Meter reading: 420 kWh consumed

**Calculation:**
```
Base cost = 420 x R2.50 = R1,050.00
No markup applied.

Wallet deduction: -R1,050.00
```

### Example 5: No Rate Table Assigned (Default Fallback)

**Setup:**
- Estate: "New Development" (no rate tables assigned yet)
- Meter type: Water
- Meter reading: 2,000 litres consumed

**Calculation:**
```
No unit or estate rate table found.
Using default: flat_rate = R15.00/kL

Consumption = 2,000 litres = 2.0 kL
Base cost = 2.0 x R15.00 = R30.00

Wallet deduction: -R30.00
```

---

## Default Rates

When no rate table is assigned to a unit or its estate, the system uses these default flat rates:

| Utility Type | Default Rate | Unit |
|-------------|-------------|------|
| Electricity | R2.50 | per kWh |
| Water | R15.00 | per kL |
| Hot Water | R15.00 | per kL (water component only) |
| Solar | R2.50 | per kWh |

---

## Implementation Status

| Pricing Model | Configurable in UI | Used in Billing Engine | Status |
|--------------|-------------------|----------------------|--------|
| Flat Rate | Yes | Yes | Fully implemented |
| Tiered Rate | Yes | Yes | Fully implemented |
| Time of Use (TOU) | Yes | Yes | Fully implemented |
| Hot Water Dual-Component | Yes | Yes | Fully implemented |
| Seasonal | Yes | **No** | UI only - not used in billing |
| Fixed Charge | Yes | **No** | UI only - not used in billing |
| Demand Charge | Yes | **No** | UI only - not used in billing |

**Note:** Seasonal, Fixed Charge, and Demand Charge can be saved in rate table configurations but are not currently included in the wallet deduction calculations. These models will need billing engine implementation before they can be used in production.

---

## Combining Pricing Models

A single rate table can combine multiple pricing models. For example:

```json
{
  "tiers": [
    { "from": 0, "to": 100, "rate": 2.00 },
    { "from": 100, "to": null, "rate": 3.00 }
  ],
  "fixed_charge": 50.00,
  "seasonal": { "summer": 2.50, "winter": 2.00 }
}
```

However, the billing engine currently only uses the **first matching model** in this priority order:
1. Flat rate
2. Time of Use
3. Utility-specific tiers (e.g. `"electricity": [...]`)
4. Generic tiers (e.g. `"tiers": [...]`)

If a rate structure contains both `flat_rate` and `tiers`, only the flat rate will be used. Fixed charge, seasonal, and demand charge fields are stored but not included in the calculation.

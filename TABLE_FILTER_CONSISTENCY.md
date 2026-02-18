# Table Filter Consistency Analysis

## Current State Analysis

### 1. Users Page
| Feature | Status | Details |
|---------|--------|---------|
| Search Input | ✅ Yes | Searches: name, email |
| Status Filter | ✅ Yes | Active/Disabled |
| Additional Filters | ✅ Yes | Role filter |
| Clear Button | ✅ Yes | |
| Layout | Search left, filters right | |

**Table Columns:** Name, Email, Phone, Role, Status, Created, Actions

---

### 2. Persons Page
| Feature | Status | Details |
|---------|--------|---------|
| Search Input | ✅ Yes | Searches: name, email, phone |
| Status Filter | ✅ Yes | Active/Inactive |
| Additional Filters | ✅ Yes | Unit, Owner, Tenant filters |
| Clear Button | ✅ Yes | |
| Layout | Search left, filters right | |

**Table Columns:** Name/ID, Contact, Units, Role, Status, Actions

---

### 3. Units Page
| Feature | Status | Details |
|---------|--------|---------|
| Search Input | ✅ Yes | Searches: unit number only |
| Status Filter | ✅ Yes | Occupied/Vacant |
| Additional Filters | ✅ Yes | Estate filter |
| Clear Button | ✅ Yes | |
| Layout | Search left, filters right | |

**Table Columns:** Unit, Estate, Tenants, Electricity, Water, Hot Water, Solar, Status, Actions

---

### 4. Meters Page
| Feature | Status | Details |
|---------|--------|---------|
| Search Input | ❌ NO | **MISSING** |
| Status Filter | ✅ Yes | Credit status (ok/low/disconnected) |
| Additional Filters | ✅ Yes | Estate, Type, Communication status |
| Clear Button | ✅ Yes | |
| Layout | Filters left, clear right | **DIFFERENT LAYOUT** |

**Table Columns:** Device EUI, Unit/Location, Type, Status, Credit, Consumption, Last Reading, Actions

---

## Identified Issues

### Issue 1: Missing Search on Meters Page
**Problem:** Meters page has no search functionality while all other pages do.
**Impact:** Users cannot quickly find meters by Device EUI, serial number, or unit.
**Fix Required:** Add search input that searches across Device EUI, Serial Number, and Unit Number.

### Issue 2: Inconsistent Layout
**Problem:** Meters page has filters on the left side, while all other pages have search on the left.
**Impact:** Inconsistent UX across the application.
**Fix Required:** Move search to left side, keep filters on right side (same as other pages).

### Issue 3: Search Scope Too Limited
**Problem:** Each page's search only covers specific columns, not all searchable columns.
**Current State:**
- Users: name, email (missing: phone)
- Persons: name, email, phone (good)
- Units: unit number only (missing: estate name, tenant name)
- Meters: N/A (no search)

**Fix Required:** Expand search to cover all relevant text columns.

### Issue 4: Inconsistent Input Styling
**Problem:** Filter dropdowns have inconsistent styling:
- Meters page uses `appearance-none` with chevron icons
- Other pages use default select styling
**Fix Required:** Standardize on one style across all pages.

---

## Target Consistent Design

### Standard Filter Bar Layout
```
+------------------------------------------------------------------+
| [Search Input...........................] | [Filter1] [Filter2] [Clear] |
+------------------------------------------------------------------+
```

### Search Requirements by Page
| Page | Search Should Cover |
|------|---------------------|
| Users | Name, Email, Phone |
| Persons | Name, ID Number, Email, Phone |
| Units | Unit Number, Estate Name, Tenant Name |
| Meters | Device EUI, Serial Number, Unit Number, Estate Name |

### Standard Filter Options by Page
| Page | Required Filters |
|------|------------------|
| Users | Status (Active/Disabled), Role |
| Persons | Status (Active/Inactive), Unit, Owner (Yes/No), Tenant (Yes/No) |
| Units | Estate, Status (Occupied/Vacant) |
| Meters | Estate, Type, Communication Status, Credit Status |

### Standard Input Styling
All filter dropdowns should use consistent styling:
```html
<select class="px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg
               bg-white dark:bg-gray-700 text-gray-900 dark:text-white text-sm
               focus:ring-2 focus:ring-primary focus:border-primary">
```

---

## Implementation Plan

### Phase 1: Add Search to Meters Page
1. Add search input to meters.html template
2. Update meters.py API to support search parameter
3. Update meters.js to wire up search with TableFilter

### Phase 2: Expand Search Scope
1. Update users.py API to search phone
2. Update units.py API to search estate name, tenant name
3. Update search placeholders to reflect full scope

### Phase 3: Standardize Styling
1. Update meters.html to match standard layout (search left, filters right)
2. Standardize dropdown styling across all pages

### Phase 4: Testing
1. Test search works across all columns on each page
2. Test filters combine correctly with search
3. Test clear button resets everything

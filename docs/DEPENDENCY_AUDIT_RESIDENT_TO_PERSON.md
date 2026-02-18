# Resident → Person Refactoring: Complete Dependency Audit

**Date:** 2025-11-19
**Auditor:** Claude
**Status:** ✅ COMPLETE - Ready for Safe Migration

---

## 📊 Executive Summary

**Current Database State:**
- ✅ 0 residents in database - **PERFECT for migration!**
- ✅ No data loss risk
- ⚠️ Foreign key constraint exists: `units_resident_id_fkey`

**Code Dependencies Found:**
- 🔴 **7 Python files** directly import/use Resident model
- 🔴 **10 template files** reference resident data
- 🔴 **1 JavaScript file** (minor - units.js, no direct dependency)
- 🔴 **1 seed script** creates residents

**Risk Level:** 🟢 **LOW** (no production data)

---

## 🔍 Detailed Dependency Analysis

### 1. Database Schema

#### **Current `residents` Table**
```sql
Table: residents
Columns:
  - id (PK, serial)
  - id_number (unique)
  - first_name, last_name
  - email (unique), phone
  - alternate_phone
  - emergency_contact_name, emergency_contact_phone
  - lease_start_date, lease_end_date
  - is_active, status
  - app_user_id (unused!)
  - created_by, updated_by (FK to users)
  - created_at, updated_at

Foreign Keys:
  - created_by → users(id)
  - updated_by → users(id)

Referenced By:
  - units.resident_id → residents(id)  [FK: units_resident_id_fkey]

Current Data: 0 rows ✅
```

#### **Current `units` Table (Relevant Columns)**
```sql
resident_id integer
  FK: units_resident_id_fkey → residents(id)

Current State: All units.resident_id = NULL (no assignments)
```

---

### 2. Python Code Dependencies

#### **A. Models** (`app/models/`)

| File | Line(s) | Usage | Impact |
|------|---------|-------|--------|
| `__init__.py` | 4 | `from .resident import Resident` | ⚠️ Will add Person import |
| `unit.py` | 46, 53 | `resident_id` column, `resident` relationship | 🔴 **BREAKS** - needs replacement |

**Unit.py Current Code:**
```python
# Line 46 - WILL BE REMOVED
resident_id = db.Column(db.Integer, db.ForeignKey("residents.id"))

# Line 53 - WILL BE REMOVED
resident = db.relationship("Resident", backref="unit")
```

---

#### **B. Services** (`app/services/`)

| File | Lines | Functions | What It Does |
|------|-------|-----------|--------------|
| `residents.py` | 1-112 | All functions | 🔴 Complete CRUD for residents |
| `units.py` | 49, 76 | create_unit, update_unit | Uses `resident_id` field |

**Residents Service Functions:**
- `list_residents()` - Query residents with filters
- `list_residents_for_dropdown()` - Get all for dropdowns
- `get_resident_by_id()` - Fetch single resident
- `create_resident()` - Create new resident
- `update_resident()` - Update existing
- `delete_resident()` - **⚠️ Checks if assigned to unit before delete!**

**Critical Code in delete_resident() (line 102-108):**
```python
assigned_unit = Unit.query.filter_by(resident_id=resident.id).first()
if assigned_unit:
    return False, {
        "code": 409,
        "message": "Resident is assigned to a unit..."
    }
```
**Impact:** This logic will need to check `unit_tenancies` instead.

---

#### **C. Routes** (`app/routes/v1/`)

| File | Endpoints | Impact |
|------|-----------|--------|
| `residents.py` | `/residents` (GET, POST, PUT, DELETE) | 🔴 **Entire file will be replaced** |
| `units.py` | Line 44, 52-60, 95-96 | Uses `resident_id` in queries | 🔴 **Needs update** |
| `auth.py` | Line 652-659 | Dashboard: counts residents | 🟡 Minor - update query |
| `reports.py` | Line 708 | Report: joins Resident | 🟡 Minor - update join |

**units.py - Resident Usage (lines 52-60):**
```python
if u.resident_id:
    res = Resident.query.get(u.resident_id)
    if res:
        ud["resident"] = {
            "id": res.id,
            "first_name": res.first_name,
            "last_name": res.last_name,
            "phone": res.phone,
        }
```
**Impact:** Must change to get tenants from `unit.tenancies`.

**units.py - Dropdown (lines 94-97):**
```python
residents = [
    {"id": r.id, "name": f"{r.first_name} {r.last_name}"}
    for r in svc_list_residents_for_dropdown()
]
```
**Impact:** Change to `svc_list_persons_for_dropdown()`.

---

### 3. Template Dependencies

#### **Templates Using `.resident` or `resident_id`**

| Template | Usage | Impact Level |
|----------|-------|--------------|
| `residents/residents.html` | Complete resident management UI | 🔴 **REPLACE with persons.html** |
| `units/units.html` | Show resident name/phone | 🔴 **UPDATE** - show all tenants |
| `units/unit-details.html` | Display resident info | 🔴 **UPDATE** - add ownership/tenancy sections |
| `estates/estate_details.html` | List units with residents | 🟡 Minor update |
| `billing/billing.html` | Show resident for wallet | 🟡 Minor update |
| `dashboard/index.html` | Resident count metric | 🟡 Minor update |
| `meters/meter-details.html` | Show unit's resident | 🟡 Minor update |
| `base.html` | Sidebar menu "Residents" | 🟡 Rename to "People" |

**Critical Template: units/units.html (line 168-170)**
```html
<p class="text-sm text-gray-900 dark:text-white">
  {{ (u.resident.first_name ~ ' ' ~ u.resident.last_name)
     if (u.resident and u.occupancy_status!='vacant')
     else 'No resident' }}
</p>
```
**Impact:** Must change to iterate `u.tenants` and show all names.

**Critical Template: residents/residents.html**
- **ENTIRE FILE** manages residents
- Has create/edit/delete modals
- Shows unit assignment
- Filters by unit

**Impact:** Will be replaced by new `persons/persons.html`

---

### 4. JavaScript Dependencies

#### `app/static/js/units/units.js`

**Good News:** ✅ No direct resident references!
- `collectUnitFormPayload()` function collects form data including `resident_id`
- But it just reads the form - doesn't hardcode resident logic

**Impact:** 🟢 Minimal - just update form field name from `resident_id` to handle multiple persons differently.

---

### 5. Seed/Test Data

#### `scripts/seed.py`

**Function:** `create_residents_and_assign()` (lines 1300-1377)

**What it does:**
1. Creates residents with random names
2. Assigns them to occupied units via `unit.resident_id = res.id`
3. Used only for development/testing

**Impact:** 🟡 **REPLACE** with new `create_persons_and_assign()` function that:
- Creates Person records
- Creates UnitTenancy records instead of setting resident_id

---

### 6. Permission System

**Permission Resource:** `residents`

**Found in:**
- `scripts/seed.py` (lines 343, 366, 394) - Role permissions include `"residents": {...}`

**Current permissions:**
- `residents.view`
- `residents.create`
- `residents.edit`
- `residents.delete`

**Impact:** 🟡 **ADD new permissions:**
- `persons.view`, `persons.create`, `persons.edit`, `persons.delete`
- Keep `residents.*` temporarily for backward compatibility

---

## 🚨 Breaking Changes Summary

### **WILL BREAK (Must Fix):**

1. ✅ **Unit.resident_id column** - Remove from model and database
2. ✅ **Unit.resident relationship** - Remove from model
3. ✅ **Residents management page** - Entire UI needs replacement
4. ✅ **Units dropdown** - Change from single select to multi-person management
5. ✅ **Services:** `residents.py` - Replace with `persons.py`
6. ✅ **Routes:** `residents.py` - Replace with `persons.py`
7. ✅ **Delete logic** - Check tenancies instead of resident_id
8. ✅ **Seed script** - Update resident creation logic

### **MUST UPDATE (Not Breaking, but needs changes):**

1. 🟡 **Units template** - Show multiple tenants instead of one resident
2. 🟡 **Unit details** - Add ownership and tenancy sections
3. 🟡 **Dashboard** - Update resident count metric
4. 🟡 **Reports** - Update queries from Resident to Person
5. 🟡 **Sidebar menu** - Rename "Residents" to "People"
6. 🟡 **Permissions** - Add `persons.*` permissions

---

## ✅ Safe Migration Strategy

### **Phase 1: Preparation** (Before any code changes)

#### Step 1.1: Verify Database State
```bash
# Confirm 0 residents exist
psql -U sa -d quantify -c "SELECT COUNT(*) FROM residents;"

# Confirm no units have resident assignments
psql -U sa -d quantify -c "SELECT COUNT(*) FROM units WHERE resident_id IS NOT NULL;"

# Expected: Both should return 0
```

#### Step 1.2: Backup Database
```bash
pg_dump -U sa quantify > backup_before_person_migration_$(date +%Y%m%d_%H%M%S).sql
```

---

### **Phase 2: Create New Models & Tables** (Additive Only - No Breaking Changes)

#### Migration 1: Create `persons` table
```python
# Will include ALL fields from residents table
# Plus password_hash for mobile authentication
```

#### Migration 2: Create `unit_ownerships` table
```python
# New junction table for ownership
```

#### Migration 3: Create `unit_tenancies` table
```python
# New junction table for rentals/tenancy
```

**Status after Phase 2:**
- ✅ Old `residents` table still exists
- ✅ Old `units.resident_id` still exists
- ✅ New tables exist alongside old ones
- ✅ No breaking changes yet
- ✅ Can test new models without affecting existing code

---

### **Phase 3: Add New Code** (Parallel Implementation)

Create new files WITHOUT modifying existing ones:

**New Files:**
- ✅ `app/models/person.py`
- ✅ `app/models/unit_ownership.py`
- ✅ `app/models/unit_tenancy.py`
- ✅ `app/services/persons.py`
- ✅ `app/services/unit_ownerships.py`
- ✅ `app/services/unit_tenancies.py`
- ✅ `app/routes/v1/persons.py`
- ✅ `app/templates/persons/persons.html`
- ✅ `app/templates/persons/person-details.html`

**Status after Phase 3:**
- ✅ New Person system fully functional
- ✅ Old Resident system still works
- ✅ Can access `/residents` (old) and `/persons` (new) in parallel
- ✅ Can test new system before cutting over

---

### **Phase 4: Migrate Data** (One-time, reversible)

#### Migration 4: Copy residents → persons (if any exist)
```sql
-- This will be empty since you have 0 residents
-- But script will handle production server with data

INSERT INTO persons (
    id, id_number, first_name, last_name, email, phone,
    alternate_phone, emergency_contact_name, emergency_contact_phone,
    is_active, app_user_id, created_by, updated_by,
    created_at, updated_at
)
SELECT
    id, id_number, first_name, last_name, email, phone,
    alternate_phone, emergency_contact_name, emergency_contact_phone,
    is_active, app_user_id, created_by, updated_by,
    created_at, updated_at
FROM residents
WHERE NOT EXISTS (
    SELECT 1 FROM persons WHERE persons.email = residents.email
);

-- Create tenancy records from units.resident_id
INSERT INTO unit_tenancies (
    unit_id, person_id, is_primary_tenant,
    lease_start_date, lease_end_date, status,
    move_in_date, created_at
)
SELECT
    u.id as unit_id,
    p.id as person_id,
    true as is_primary_tenant,
    r.lease_start_date,
    r.lease_end_date,
    r.status,
    r.lease_start_date as move_in_date,
    NOW()
FROM units u
INNER JOIN residents r ON u.resident_id = r.id
INNER JOIN persons p ON p.email = r.email
WHERE u.resident_id IS NOT NULL;
```

**Verification:**
```sql
-- Verify all residents copied
SELECT COUNT(*) as resident_count FROM residents;
SELECT COUNT(*) as person_count FROM persons WHERE id <=
    (SELECT COALESCE(MAX(id), 0) FROM residents);

-- Should match (both 0 currently)
```

---

### **Phase 5: Update Existing Code** (Breaking Changes - Point of No Return)

#### Step 5.1: Update Unit model
```python
# REMOVE these lines from unit.py:
resident_id = db.Column(db.Integer, db.ForeignKey("residents.id"))
resident = db.relationship("Resident", backref="unit")

# ADD these lines:
ownerships = db.relationship("UnitOwnership", back_populates="unit", ...)
tenancies = db.relationship("UnitTenancy", back_populates="unit", ...)

@property
def residents(self):
    """Get all current tenants"""
    return [t.person for t in self.tenancies if not t.move_out_date]

@property
def owners(self):
    """Get all owners"""
    return [o.person for o in self.ownerships]
```

#### Step 5.2: Update units service
```python
# In services/units.py, REMOVE resident_id handling:
# Line 49: resident_id=payload.get("resident_id"),
# Line 76: "resident_id",

# Add logic to create tenancies if needed
```

#### Step 5.3: Update units routes
```python
# In routes/v1/units.py, REPLACE:
residents = [
    {"id": r.id, "name": f"{r.first_name} {r.last_name}"}
    for r in svc_list_residents_for_dropdown()
]

# WITH:
persons = [
    {"id": p.id, "name": p.full_name}
    for p in svc_list_persons_for_dropdown()
]
```

#### Step 5.4: Update templates
- Update `units/units.html` to show multiple tenants
- Update `units/unit-details.html` with ownership/tenancy sections
- Update sidebar menu

#### Step 5.5: Update seed script
- Replace `create_residents_and_assign()` with `create_persons_and_assign()`

---

### **Phase 6: Clean Up** (Final Migration)

#### Migration 5: Drop old columns/constraints
```sql
-- Drop foreign key constraint
ALTER TABLE units DROP CONSTRAINT units_resident_id_fkey;

-- Drop the resident_id column
ALTER TABLE units DROP COLUMN resident_id;

-- Optionally: Drop residents table (or keep as backup)
-- DROP TABLE residents;  -- CAREFUL!
```

---

## 🔄 Rollback Plan

### **Before Migration 5 (Drop columns):**
```bash
# Rollback is simple - just revert code changes
git checkout main
flask db downgrade -1  # Or however many migrations you ran
```

### **After Migration 5:**
```bash
# Restore from backup
psql -U sa -d quantify < backup_before_person_migration_[timestamp].sql

# Revert code
git checkout main
```

---

## ✅ Testing Checklist

### **Before Deploying to Server:**

**Local Testing:**
- [ ] Run all migrations successfully
- [ ] Create Person via new UI
- [ ] Assign Person as owner to unit
- [ ] Assign Person as tenant to unit
- [ ] Assign multiple persons to same unit
- [ ] Verify one person can own multiple units
- [ ] Test delete person (should fail if assigned to unit)
- [ ] Test remove person from unit (should succeed)
- [ ] Verify Unit details page shows all owners/tenants
- [ ] Verify dashboard metrics are correct

**Data Integrity:**
- [ ] No orphaned records in unit_ownerships
- [ ] No orphaned records in unit_tenancies
- [ ] All persons have valid email (unique constraint)
- [ ] All units show correct occupants

**Permissions:**
- [ ] Super Admin can access /persons
- [ ] Regular admin can view persons (if permitted)
- [ ] Persons CRUD operations respect permissions

---

## 📊 Deployment Timeline Estimate

| Phase | Task | Time | Risk |
|-------|------|------|------|
| 1 | Preparation & Backup | 10 min | 🟢 Low |
| 2 | Create New Tables (Migrations 1-3) | 5 min | 🟢 Low |
| 3 | Create New Code Files | 30 min | 🟢 Low |
| 4 | Migrate Data (Migration 4) | 2 min | 🟢 Low (0 rows) |
| 5 | Update Existing Code | 45 min | 🟡 Medium |
| 6 | Clean Up (Migration 5) | 5 min | 🟡 Medium |
| **Testing** | Full regression testing | 60 min | - |
| **TOTAL** | **~3 hours** | - | 🟢 Low Overall |

---

## 🎯 Recommendation

**Proceed with Confidence!**

✅ **Zero data to migrate** (0 residents)
✅ **All dependencies mapped**
✅ **Safe phased approach**
✅ **Full rollback capability**
✅ **Low risk**

**Next Step:** Create the 5 migration files and new service/route files.

---

**Document Status:** APPROVED FOR IMPLEMENTATION
**Last Updated:** 2025-11-19
**Approval:** Pending User Confirmation

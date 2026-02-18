# Person Model Refactoring - Implementation Plan

**Date:** 2025-11-19
**Status:** Approved - Ready for Implementation
**Goal:** Replace single-resident-per-unit with proper multi-person architecture

---

## 🎯 Objectives

1. Support multiple residents/owners per unit
2. Support one person owning/renting multiple units
3. Clean separation between ownership and tenancy
4. Proper mobile app user authentication via `app_user_id`
5. Maintain backward compatibility during migration

---

## 📊 New Models

### 1. Person (Core Identity)

**Purpose:** Central identity for all app users (owners, tenants, occupants)

**Fields:**
- `id` - Primary key
- `first_name` - Required
- `last_name` - Required
- `email` - Unique, required
- `phone` - Required
- `alternate_phone` - Optional
- `id_number` - Unique (passport/ID)
- `emergency_contact_name` - Optional
- `emergency_contact_phone` - Optional
- `app_user_id` - UUID for mobile authentication
- `password_hash` - For mobile login (nullable initially)
- `is_active` - Boolean
- `profile_photo_url` - Optional
- `created_by` - FK to users (admin who created)
- `updated_by` - FK to users
- `created_at` - Timestamp
- `updated_at` - Timestamp

**Relationships:**
- `ownerships` → List[UnitOwnership]
- `tenancies` → List[UnitTenancy]
- `units_owned` → Calculated from ownerships
- `units_rented` → Calculated from tenancies

---

### 2. UnitOwnership (Ownership Relationship)

**Purpose:** Track who owns which units and ownership details

**Fields:**
- `id` - Primary key
- `unit_id` - FK to units, NOT NULL
- `person_id` - FK to persons, NOT NULL
- `ownership_percentage` - Decimal(5,2), default 100.00
- `purchase_date` - Date
- `purchase_price` - Decimal(15,2)
- `is_primary_owner` - Boolean (for correspondence)
- `notes` - Text
- `created_at` - Timestamp
- `updated_at` - Timestamp

**Constraints:**
- Unique(unit_id, person_id)
- ownership_percentage between 0 and 100
- SUM(ownership_percentage) per unit should = 100 (app-level validation)

**Relationships:**
- `unit` → Unit
- `person` → Person

---

### 3. UnitTenancy (Rental Relationship)

**Purpose:** Track who rents which units with lease information

**Fields:**
- `id` - Primary key
- `unit_id` - FK to units, NOT NULL
- `person_id` - FK to persons, NOT NULL
- `lease_start_date` - Date
- `lease_end_date` - Date (nullable for month-to-month)
- `monthly_rent` - Decimal(10,2)
- `deposit_amount` - Decimal(10,2)
- `is_primary_tenant` - Boolean (responsible for billing)
- `status` - Enum: active, expired, terminated
- `move_in_date` - Date
- `move_out_date` - Date (nullable if still living there)
- `notes` - Text
- `created_at` - Timestamp
- `updated_at` - Timestamp

**Constraints:**
- Unique(unit_id, person_id)
- Only one is_primary_tenant=true per unit (app-level validation)
- lease_end_date >= lease_start_date

**Relationships:**
- `unit` → Unit
- `person` → Person

---

## 🔄 Migration Strategy

### Phase 1: Create New Tables (No Breaking Changes)

1. Create `persons` table
2. Create `unit_ownerships` table
3. Create `unit_tenancies` table
4. Keep existing `residents` table temporarily

### Phase 2: Migrate Data

```sql
-- Migrate all residents to persons
INSERT INTO persons (
    first_name, last_name, email, phone, alternate_phone,
    id_number, emergency_contact_name, emergency_contact_phone,
    app_user_id, is_active, created_by, updated_by,
    created_at, updated_at
)
SELECT
    first_name, last_name, email, phone, alternate_phone,
    id_number, emergency_contact_name, emergency_contact_phone,
    app_user_id, is_active, created_by, updated_by,
    created_at, updated_at
FROM residents;

-- Create tenancy relationships from units.resident_id
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
    CASE
        WHEN r.status = 'active' THEN 'active'
        ELSE 'expired'
    END as status,
    r.lease_start_date as move_in_date,
    NOW()
FROM units u
INNER JOIN residents r ON u.resident_id = r.id
INNER JOIN persons p ON p.email = r.email;  -- Link via email
```

### Phase 3: Update Code

1. Update `Unit` model - remove `resident_id`, add relationships
2. Create `Person`, `UnitOwnership`, `UnitTenancy` models
3. Create services: `persons.py`, `unit_ownerships.py`, `unit_tenancies.py`
4. Update `units.py` service to use new relationships
5. Update routes to handle multiple persons
6. Update templates to show multiple residents/owners

### Phase 4: Deprecate Old Model

1. Drop `units.resident_id` column
2. Mark `Resident` model as deprecated (or remove entirely)
3. Drop foreign key constraint
4. Clean up old code references

---

## 📝 Code Changes Required

### Models to Create

- ✅ `app/models/person.py`
- ✅ `app/models/unit_ownership.py`
- ✅ `app/models/unit_tenancy.py`

### Models to Update

- ✅ `app/models/unit.py` - Remove resident_id, add new relationships
- ⚠️ `app/models/resident.py` - Deprecate (keep for reference during migration)

### Services to Create

- ✅ `app/services/persons.py`
- ✅ `app/services/unit_ownerships.py`
- ✅ `app/services/unit_tenancies.py`

### Services to Update

- ✅ `app/services/units.py` - Update to work with new relationships
- ⚠️ `app/services/residents.py` - Deprecate

### Routes to Update

- ✅ `app/routes/v1/units.py` - Handle multiple persons
- ✅ Create `app/routes/v1/persons.py` - New management UI
- ⚠️ `app/routes/v1/residents.py` - Deprecate or redirect

### Templates to Update

- ✅ `app/templates/units/units.html` - Show multiple residents/owners
- ✅ `app/templates/units/unit-details.html` - Display all persons
- ✅ Create `app/templates/persons/` - New person management UI

### Migrations

- ✅ `xxx_create_persons_table.py`
- ✅ `xxx_create_unit_ownership_table.py`
- ✅ `xxx_create_unit_tenancy_table.py`
- ✅ `xxx_migrate_residents_to_persons.py` - Data migration
- ✅ `xxx_drop_unit_resident_id.py` - Cleanup

---

## 🎨 UI Changes

### Units Management Page

**Before:**
```
Unit A-101 | John Smith | 123-456-7890 | [Occupied]
```

**After:**
```
Unit A-101 | Owners: Sarah Lee (100%)
           | Tenants: John Smith (Primary), Jane Doe
           | [Occupied - Rented]
```

### New "People" Management Page

Replaces "Residents" page with:
- List all persons (owners + tenants + occupants)
- Filter by role: All / Owners / Tenants / Both
- Show units associated with each person
- Click person → see all their units
- Add/Edit/Delete persons
- Link person to units as owner or tenant

### Unit Details Page

**New sections:**
1. **Ownership**
   - List all owners with percentage
   - Add/Remove owners
   - Update ownership percentage

2. **Tenancy**
   - List all tenants
   - Show lease dates
   - Indicate primary tenant (billing responsible)
   - Add/Remove tenants

3. **All Occupants**
   - Combined view of everyone with access to unit
   - Mobile app access status

---

## 🔐 Mobile App Integration

### Authentication Flow

1. Person registers via mobile app
2. Backend creates `Person` record with `app_user_id` (UUID)
3. Person can see ALL units they're associated with:
   - Units they own (via UnitOwnership)
   - Units they rent (via UnitTenancy)

### API Endpoints (Future Mobile API)

```
GET /api/mobile/v1/auth/user
→ Returns Person with all associated units

GET /api/mobile/v1/my-units
→ Returns all units person owns OR rents

GET /api/mobile/v1/units/{unit_id}
→ Returns unit details (only if person has access)
```

---

## ✅ Validation Rules

### Unit Level

- A unit can have multiple owners (sum of ownership % must = 100%)
- A unit can have multiple tenants
- A unit can have owners AND tenants simultaneously
- At most ONE primary_owner and ONE primary_tenant per unit

### Person Level

- Email must be unique across all persons
- Phone should be unique (warning if duplicate)
- ID number must be unique if provided
- Can be owner of multiple units
- Can be tenant of multiple units
- Cannot be both owner AND tenant of the SAME unit

---

## 📊 Reporting Changes

### Dashboard Metrics

Update to show:
- Total persons in system
- Persons with app access (app_user_id not null)
- Units with owners
- Units with tenants
- Vacant units (no tenants)
- Owner-occupied units (owner is also marked as occupant)

### Reports to Update

1. **Resident Directory** → **People Directory**
   - Show all persons with their roles

2. **Unit Occupancy** → Updated
   - Show ownership status
   - Show tenancy status

3. **Lease Expiry Report** → New
   - Units with leases expiring soon

4. **Ownership Report** → New
   - Who owns what
   - Joint ownership details

---

## 🚀 Implementation Order

### Week 1: Foundation

**Day 1-2:** Create Models
- [ ] Create `Person` model
- [ ] Create `UnitOwnership` model
- [ ] Create `UnitTenancy` model
- [ ] Write unit tests for models

**Day 3-4:** Create Migrations
- [ ] Migration: Create persons table
- [ ] Migration: Create unit_ownerships table
- [ ] Migration: Create unit_tenancies table
- [ ] Test migrations on clean database

**Day 5:** Data Migration
- [ ] Migration: Migrate residents → persons
- [ ] Migration: Create tenancy records from units.resident_id
- [ ] Verify data integrity
- [ ] Backup/rollback testing

### Week 2: Services & API

**Day 1-2:** Services Layer
- [ ] Create `persons.py` service (CRUD)
- [ ] Create `unit_ownerships.py` service
- [ ] Create `unit_tenancies.py` service
- [ ] Update `units.py` service for new relationships
- [ ] Write service tests

**Day 3-4:** API Routes
- [ ] Create `/api/v1/persons` routes
- [ ] Update `/api/v1/units` routes
- [ ] Create ownership management endpoints
- [ ] Create tenancy management endpoints
- [ ] Test all endpoints

**Day 5:** Cleanup Migration
- [ ] Migration: Drop units.resident_id column
- [ ] Deprecate old Resident model/routes
- [ ] Update all import statements

### Week 3: UI & Testing

**Day 1-2:** Admin UI
- [ ] Create People management page
- [ ] Update Units page (show multiple persons)
- [ ] Update Unit details page (ownership + tenancy sections)
- [ ] Add person selection modals

**Day 3-4:** Testing & Bug Fixes
- [ ] Integration testing
- [ ] UI testing
- [ ] Fix any bugs discovered
- [ ] Performance testing with multiple persons

**Day 5:** Documentation & Handoff
- [ ] Update API documentation
- [ ] Update user guide
- [ ] Code review
- [ ] Merge to main

---

## 🔍 Testing Checklist

### Data Migration Tests

- [ ] All residents migrated to persons (count matches)
- [ ] All units.resident_id relationships → unit_tenancies
- [ ] Email uniqueness maintained
- [ ] No data loss
- [ ] Can rollback cleanly

### Functional Tests

- [ ] Create unit with multiple owners
- [ ] Create unit with multiple tenants
- [ ] Person can be owner of unit A, tenant of unit B
- [ ] Calculate ownership percentage validation
- [ ] Primary tenant/owner designation works
- [ ] Wallet access for all unit members

### UI Tests

- [ ] People page shows all persons correctly
- [ ] Unit page shows all owners and tenants
- [ ] Can add/remove owners
- [ ] Can add/remove tenants
- [ ] Filters and search work
- [ ] Pagination works

---

## 📌 Notes & Considerations

### Backward Compatibility

- Keep Resident model read-only during transition
- Provide data migration script for production
- Document breaking changes for mobile app

### Performance

- Index on persons.email, persons.app_user_id
- Index on unit_ownerships (unit_id, person_id)
- Index on unit_tenancies (unit_id, person_id)
- Eager loading for unit.owners, unit.tenants queries

### Security

- Ensure persons can only see their own units via mobile API
- Admin users can see all persons
- Audit log all person changes

---

## 🆘 Rollback Plan

If issues arise during migration:

1. **Before removing units.resident_id:**
   - Data exists in both old and new structure
   - Can revert code changes
   - No data loss

2. **After removing units.resident_id:**
   - Restore from backup
   - Re-run old migrations
   - Fix issues before re-attempting

3. **Emergency Rollback:**
   - Database backup before migration
   - Tagged git commit before changes
   - Documented rollback SQL scripts

---

**Status:** Ready to implement
**Approved by:** [Your name]
**Start Date:** [TBD]
**Expected Completion:** 3 weeks

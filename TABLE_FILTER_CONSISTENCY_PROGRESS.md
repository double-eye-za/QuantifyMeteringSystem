# Table Filter Consistency - Progress Tracker

## Legend
- [ ] Not started
- [x] Completed
- [!] Blocked/Issue

---

## Phase 1: Add Search to Meters Page

### Backend (meters.py)
- [x] Add `search` or `q` parameter to `/api/meters` endpoint
- [x] Implement search across Device EUI field
- [x] Implement search across Serial Number field
- [x] Implement search across Unit Number (via joined unit)
- [x] Implement search across Estate name
- [ ] Test API returns filtered results

### Frontend (meters.html)
- [x] Add search input to left side of filter bar
- [x] Update layout to match other pages (search left, filters right)
- [x] Add search icon inside input

### JavaScript (meters.js)
- [x] Add search filter configuration to TableFilter
- [x] Enable debounce for search input
- [ ] Test search triggers AJAX filtering

---

## Phase 2: Expand Search Scope on Users Page

### Backend (users.py service)
- [x] Add phone number to search query
- [ ] Test search finds users by phone

### Frontend (users.html)
- [x] Update placeholder text to "Search name, email, phone..."

---

## Phase 3: Expand Search Scope on Units Page

### Backend (units.py service)
- [x] Add estate name to search query (via joined estate)
- [x] Add tenant name to search query (via joined tenants)
- [ ] Test search finds units by estate name
- [ ] Test search finds units by tenant name

### Frontend (units.html)
- [x] Update placeholder text to "Search unit, estate, tenant..."

---

## Phase 4: Standardize Dropdown Styling

### Meters Page
- [x] Remove chevron icons from dropdowns
- [x] Match dropdown styling to other pages

### All Pages
- [x] Verify consistent padding (px-4 py-2)
- [x] Verify consistent border styling
- [x] Verify consistent focus ring styling

---

## Phase 5: Testing Checklist

### Users Page
- [ ] Search by name works
- [ ] Search by email works
- [ ] Search by phone works
- [ ] Status filter works
- [ ] Role filter works
- [ ] Search + filters combined works
- [ ] Clear resets everything

### Persons Page
- [ ] Search by name works
- [ ] Search by email works
- [ ] Search by phone works
- [ ] Search by ID number works
- [ ] Unit filter works
- [ ] Owner filter works
- [ ] Tenant filter works
- [ ] Status filter works
- [ ] Search + filters combined works
- [ ] Clear resets everything

### Units Page
- [ ] Search by unit number works
- [ ] Search by estate name works
- [ ] Search by tenant name works
- [ ] Estate filter works
- [ ] Status filter works
- [ ] Search + filters combined works
- [ ] Clear resets everything

### Meters Page
- [ ] Search by Device EUI works
- [ ] Search by Serial Number works
- [ ] Search by Unit Number works
- [ ] Estate filter works
- [ ] Type filter works
- [ ] Communication status filter works
- [ ] Credit status filter works
- [ ] Search + filters combined works
- [ ] Clear resets everything

---

## Summary

| Page | Search | Filters | Layout | Styling |
|------|--------|---------|--------|---------|
| Users | [x] | [x] | [x] | [x] |
| Persons | [x] | [x] | [x] | [x] |
| Units | [x] | [x] | [x] | [x] |
| Meters | [x] | [x] | [x] | [x] |

# Quantify Metering System - Standardized Menu Structure

## Simplified Navigation Hierarchy

### 🏠 Main Operations
Primary day-to-day operations for managing the prepaid metering system:

1. **Dashboard** (`dashboard.html`)
   - System overview and KPIs
   - Critical alerts and notifications
   - Estate performance summary
   - Quick access to common tasks

2. **Estates** (`estates.html`)
   - View and manage estates
   - Bulk meter readings
   - Reconciliation (bulk vs unit usage)
   - Estate-level reporting

3. **Units** (`units.html`)
   - List all units across estates
   - Unit details and meter readings
   - Wallet balances and top-ups
   - Individual unit management
   - Visual unit diagram (`unit-visual.html`)

4. **Meters** (`meters.html`)
   - All meter readings
   - Meter status and health
   - Communication status
   - Detailed meter view (`meter-details.html`)

5. **Billing** (`billing.html`)
   - Wallet statements (`wallet-statement.html`)
   - Transaction history
   - Top-up management
   - Payment reconciliation

6. **Reports** (`reports.html`)
   - Consumption analytics
   - Revenue reports
   - Reconciliation reports
   - Custom report generation

### ⚙️ Configuration
System configuration and settings:

7. **Rate Tables** (`rate-tables.html`)
   - Define base electricity and water rates
   - Configure estate-specific markups
   - Set free solar allocations
   - Manage service fees
   - Individual unit overrides

8. **Settings** (`settings.html`)
   - System preferences
   - Notification settings
   - Backup and restore
   - API configuration

### 👥 Administration
Administrative functions (visible only to admin users):

9. **Users** (`users.html`)
   - User management
   - Role assignments
   - Access control

## Removed/Consolidated Items

To simplify the system, we've consolidated:

- ~~Tariff Groups~~ → Merged into **Rate Tables** with estate assignments
- ~~Solar Config~~ → Merged into **Rate Tables** as free allocation settings
- ~~Tariffs~~ → Simplified into **Rate Tables**

## Key Improvements

1. **Clearer Hierarchy**: Grouped menu items by function (Main, Config, Admin)
2. **Reduced Confusion**: Eliminated duplicate concepts (tariffs vs rate tables)
3. **Simplified Workflow**: Direct rate table to estate assignment with markup configuration
4. **Better Organization**: Related functions grouped together
5. **Consistent Naming**: All pages follow clear naming conventions

## Implementation Notes

### For Each Page Update:
1. Replace old navigation with standardized structure
2. Highlight current page with `bg-blue-50 dark:bg-blue-900/20 text-primary` classes
3. Ensure mobile responsiveness
4. Keep theme toggle and user profile consistent

### Rate Table Assignment Flow:
1. Create base rate table with tiers
2. Assign rate table to estate
3. Configure estate-specific markups:
   - Electricity markup %
   - Water markup %
   - Free solar kWh
   - Service fees
4. Apply individual unit overrides as needed

This simplified structure makes the system more intuitive and easier to manage.
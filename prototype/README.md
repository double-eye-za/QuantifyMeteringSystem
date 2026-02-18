# Quantify Metering System - Prototype HTML Files

This folder contains the HTML prototype files for the Quantify Metering System. These are static HTML mockups that demonstrate the UI/UX design and functionality before backend integration.

---

## 📁 Files Overview

### 🏠 Main Application Pages

| File | Description | Purpose |
|------|-------------|---------|
| `index.html` | Dashboard / Home Page | System overview, KPIs, alerts, and quick actions |
| `estates.html` | Estate Management | View and manage residential estates |
| `units.html` | Unit Management | List and manage individual units |
| `unit-details.html` | Unit Details View | Detailed view of a specific unit with meters and wallet |
| `unit-visual.html` | Unit Visual Diagram | Graphical representation of meter connections |
| `meters.html` | Meter Registry | All meters with status and readings |
| `meter-details.html` | Meter Details | Detailed meter information and history |
| `billing.html` | Billing Dashboard | Wallet management and transactions |
| `wallet-statement.html` | Wallet Statement | Detailed transaction history and consumption breakdown |
| `reports.html` | Reporting System | Generate various reports and analytics |

### ⚙️ Configuration & Settings

| File | Description | Purpose |
|------|-------------|---------|
| `rate-table-builder.html` | Rate Table Builder | Create complex rate structures (tiered, TOU, seasonal) |
| `rate-tables-simplified.html` | Rate Table Management | Simplified rate table interface |
| `settings.html` | System Settings | Global configuration and preferences |

### 👥 User Management

| File | Description | Purpose |
|------|-------------|---------|
| `users.html` | User Management | CRUD operations for users |
| `roles.html` | Role Management | Define roles and permissions |
| `profile.html` | User Profile | Personal profile and settings |

### 🔐 Authentication

| File | Description | Purpose |
|------|-------------|---------|
| `login.html` | Login Page | User authentication |
| `register.html` | Registration | New user registration |
| `reset-password.html` | Password Reset | Password recovery flow |

### 📊 Additional Features

| File | Description | Purpose |
|------|-------------|---------|
| `notifications.html` | Notifications Center | System notifications and alerts |
| `audit-log.html` | Audit Trail | System activity logging |

### 📖 Documentation

| File | Description |
|------|-------------|
| `MENU-STRUCTURE.md` | Navigation structure and menu hierarchy |

---

## 🎨 How to View the Prototype

### Method 1: Direct Browser Opening

Simply double-click any HTML file, or right-click and choose "Open with Browser"

```
Right-click → Open with → Chrome/Edge/Firefox
```

### Method 2: Local Development Server (Recommended)

For better functionality and to avoid CORS issues:

```bash
# Using Python (if installed)
cd prototype
python -m http.server 8000

# Then open: http://localhost:8000
```

### Method 3: VS Code Live Server

If you have the Live Server extension in VS Code:
1. Right-click on any HTML file
2. Select "Open with Live Server"

---

## 🗺️ Navigation Structure

### Main Menu Hierarchy

**🏠 Main Operations**
1. Dashboard → `index.html`
2. Estates → `estates.html`
3. Units → `units.html`
   - Unit Details → `unit-details.html`
   - Unit Visual → `unit-visual.html`
4. Meters → `meters.html`
   - Meter Details → `meter-details.html`
5. Billing → `billing.html`
   - Wallet Statement → `wallet-statement.html`
6. Reports → `reports.html`

**⚙️ Configuration**
7. Rate Tables → `rate-tables-simplified.html`
   - Rate Builder → `rate-table-builder.html`
8. Settings → `settings.html`

**👥 Administration**
9. Users → `users.html`
10. Roles → `roles.html`

**🔔 Additional**
- Notifications → `notifications.html`
- Audit Log → `audit-log.html`
- Profile → `profile.html`

---

## 🎯 Key Features Demonstrated

### Dashboard (`index.html`)
- ✅ Real-time KPI cards
- ✅ Interactive charts (consumption, revenue)
- ✅ Alert notifications
- ✅ Quick action buttons
- ✅ Estate performance overview

### Estate Management (`estates.html`)
- ✅ Estate listing with search/filter
- ✅ Bulk meter readings
- ✅ Reconciliation reports
- ✅ Estate-level statistics

### Unit Management (`units.html`, `unit-details.html`)
- ✅ Unit listing with wallet balances
- ✅ Three meters per unit (electricity, water, solar)
- ✅ Occupancy status
- ✅ Resident information
- ✅ Quick wallet actions

### Meter System (`meters.html`, `meter-details.html`)
- ✅ Meter registry with status
- ✅ Communication monitoring
- ✅ Reading history
- ✅ Tamper detection alerts

### Billing System (`billing.html`, `wallet-statement.html`)
- ✅ Prepaid wallet management
- ✅ Transaction history
- ✅ Automatic deductions
- ✅ Top-up functionality
- ✅ Consumption breakdown

### Rate Management (`rate-table-builder.html`)
- ✅ Tiered block rates
- ✅ Time-of-Use (TOU) rates
- ✅ Seasonal rates
- ✅ Flat rates
- ✅ Fixed charges
- ✅ Demand charges

### Reporting (`reports.html`)
- ✅ Estate consumption reports
- ✅ Low credit alerts
- ✅ Revenue reports
- ✅ Reconciliation reports
- ✅ Transaction reports
- ✅ Export functionality (PDF/Excel)

---

## 🎨 Design System

### Color Palette
- **Primary Blue:** `#1A73E8` - Buttons, links, highlights
- **Success Green:** `#28A745` - Positive actions, confirmations
- **Warning Amber:** `#FFC107` - Warnings, low balances
- **Error Red:** `#DC3545` - Errors, disconnections
- **Info Teal:** `#17A2B8` - Information, tips

### Typography
- **Font:** Inter (sans-serif)
- **Page Title:** 24px Bold
- **Section Header:** 18px Medium
- **Body Text:** 14-16px Regular
- **Labels:** 12px Regular

### Layout
- **Grid System:** 12-column responsive grid
- **Spacing:** Consistent 16px padding
- **Breakpoints:**
  - Mobile: < 768px
  - Tablet: 768px - 1024px
  - Desktop: > 1024px

---

## 🔧 Technical Details

### Technologies Used
- **HTML5** - Semantic markup
- **Tailwind CSS** - Utility-first styling (via CDN)
- **Vanilla JavaScript** - Interactive functionality
- **Font Awesome** - Icons
- **Chart.js** - Data visualization

### Features Implemented
- ✅ Responsive design (mobile-first)
- ✅ Dark/Light theme toggle
- ✅ Interactive charts
- ✅ Modal dialogs
- ✅ Form validation
- ✅ Search and filtering
- ✅ Pagination
- ✅ Dropdown menus
- ✅ Toast notifications

### Browser Support
- ✅ Chrome (latest)
- ✅ Firefox (latest)
- ✅ Edge (latest)
- ✅ Safari (latest)

---

## 📝 Notes for Developers

### Converting to Backend-Integrated Application

When integrating with the Flask backend:

1. **Replace Static Data**
   - Convert hardcoded values to template variables
   - Use Jinja2 templating: `{{ variable }}`
   - Add API calls for dynamic data

2. **Form Submissions**
   - Add proper action URLs
   - Include CSRF tokens
   - Handle form validation server-side

3. **Authentication**
   - Add login_required decorators
   - Implement permission checks
   - Secure sensitive endpoints

4. **API Integration**
   - Replace mock data with API calls
   - Add error handling
   - Implement loading states

5. **State Management**
   - Use sessions for user state
   - Implement proper caching
   - Add real-time updates

### Files to Reference

- **Style Guide:** `../documents/Administration System Style Guide - Quantify Metering.md`
- **API Documentation:** `../documents/API Documentation.md`
- **Functional Spec:** `../documents/Functional Specification v3 - Based on Prototype.md`

---

## 🎯 Use Cases

### For Designers
- Reference UI/UX patterns
- Test responsive layouts
- Experiment with color schemes
- Prototype new features

### For Developers
- Understand user flows
- Copy component structure
- Reference CSS classes
- Plan API integrations

### For Product Managers
- Demo functionality to stakeholders
- Gather user feedback
- Plan feature priorities
- Document user stories

### For QA/Testers
- Understand expected behavior
- Create test scenarios
- Validate UI requirements
- Document bugs

---

## 🚀 Quick Start Guide

### View Dashboard
```bash
# Open dashboard
open index.html
# or
start index.html
```

### Explore Features
1. Start with `index.html` (Dashboard)
2. Navigate through the menu structure
3. Test interactive elements
4. Switch between light/dark themes
5. Try responsive layouts (resize browser)

### Test User Flows

**Estate Management Flow:**
1. `index.html` → View overview
2. `estates.html` → Select estate
3. `units.html` → View units
4. `unit-details.html` → Check unit details

**Billing Flow:**
1. `billing.html` → Overview
2. `wallet-statement.html` → Transaction details
3. `units.html` → Top-up wallet

**Meter Monitoring Flow:**
1. `meters.html` → View all meters
2. `meter-details.html` → Check specific meter
3. `unit-visual.html` → Visual representation

---

## 📊 Prototype vs Production

### What's Included in Prototype
- ✅ UI/UX design
- ✅ Visual layouts
- ✅ Interactive elements (client-side)
- ✅ Mock data
- ✅ Navigation flows

### What's NOT Included (Backend Required)
- ❌ Database integration
- ❌ User authentication
- ❌ Real meter data
- ❌ Payment processing
- ❌ API endpoints
- ❌ Data persistence
- ❌ Email notifications
- ❌ Role-based security

---

## 🔄 Updates and Maintenance

### Version History
- **v1.0** - Initial prototype with all main features
- Based on Functional Specification v3.0

### Future Enhancements
See the main project documentation for planned features in Phase 2 and Phase 3.

---

## 📞 Related Documentation

- [Menu Structure](MENU-STRUCTURE.md) - Navigation hierarchy
- [Style Guide](../documents/Administration%20System%20Style%20Guide%20-%20Quantify%20Metering.md) - Design specifications
- [Functional Spec v3](../documents/Functional%20Specification%20v3%20-%20Based%20on%20Prototype.md) - Feature descriptions
- [Setup Guide](../SETUP_GUIDE.md) - Backend application setup

---

**Project:** Quantify Metering System  
**Type:** HTML Prototype / Static Mockup  
**Last Updated:** October 2025  
**Status:** Complete - Ready for Backend Integration

---

*These prototypes serve as the visual and functional blueprint for the full-stack application.*


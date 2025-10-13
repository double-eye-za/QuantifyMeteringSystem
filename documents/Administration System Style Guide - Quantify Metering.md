# Administration System Style Guide
## Quantify Metering System

---

**Document Information**
- **Document Title**: Administration System Style Guide - Quantify Metering System
- **Version**: 1.0
- **Date**: December 2024
- **Project**: Quantify Metering System
- **Purpose**: UI/UX Design Standards for Admin Portal

---

## Table of Contents

1. [Branding & Identity](#1-branding--identity)
2. [Layout & Structure](#2-layout--structure)
3. [Components](#3-components)
4. [Content & Writing Style](#4-content--writing-style)
5. [Accessibility](#5-accessibility)
6. [Interaction Patterns](#6-interaction-patterns)
7. [Security & Data Handling](#7-security--data-handling)
8. [Implementation Examples](#8-implementation-examples)

---

## 1. Branding & Identity

### 1.1 Logo
- **Placement**: Top-left of navigation bar  
- **Clear Space**: Maintain at least 16px clear space around the logo  
- **Sizing**: 
  - Desktop: Maximum height 40px
  - Mobile: Maximum height 32px
- **Format**: SVG preferred for scalability

### 1.2 Colour Palette

#### Primary Colours
| Name | Hex Code | Usage |
|------|----------|-------|
| Primary Blue | `#1A73E8` | Buttons, links, highlights, active states |
| Light Grey | `#F9FAFB` | Backgrounds, inactive elements |
| Dark Grey | `#212121` | Text, icons, borders |

#### Status Colours
| Status | Hex Code | Usage |
|--------|----------|-------|
| Success | `#28A745` | Success messages, completed actions, tick icons |
| Warning | `#FFC107` | Warning messages, caution states |
| Error | `#DC3545` | Error messages, delete actions, cross icons |
| Info | `#17A2B8` | Informational messages, tips |

#### Additional Colours
| Name | Hex Code | Usage |
|------|----------|-------|
| White | `#FFFFFF` | Card backgrounds, input fields |
| Border Grey | `#CCCCCC` | Borders, dividers |
| Hover Grey | `#F5F5F5` | Table row hover, card hover |
| Disabled Grey | `#BDBDBD` | Disabled buttons, inactive states |
| Header Grey | `#F1F3F4` | Table headers, section backgrounds |

### 1.3 Typography

#### Font Family
- **Primary Font**: *Inter* (preferred) or *Roboto*
- **Font Type**: Sans-serif
- **Web Font**: Google Fonts or self-hosted

#### Font Sizes & Weights
| Element | Size | Weight | Line Height | Example |
|---------|------|--------|-------------|---------|
| Page Title | 24px | Bold (700) | 32px | *"Administration Dashboard"* |
| Section Header | 18px | Medium (500) | 24px | *"User Management"* |
| Body Text | 14–16px | Regular (400) | 22px | *"Enter user details below"* |
| Button Text | 14px | Medium (500) | 20px | *"Save changes"* |
| Captions & Labels | 12px | Regular (400) | 16px | *"Last updated: 10 Dec 2024"* |
| Small Text | 10px | Regular (400) | 14px | *"Version 1.0"* |

#### Typography Best Practices
- Use sentence case for most text (e.g., "Add user")
- Use Title Case only for page titles
- Maximum line length: 80 characters for readability
- Letter spacing: default (0) for body text, slight increase (+0.5px) for uppercase labels

---

## 2. Layout & Structure

### 2.1 Navigation

#### Sidebar Navigation (Recommended for Admin Portal)
- **Position**: Fixed left sidebar
- **Width**: 
  - Expanded: 240px
  - Collapsed: 60px (icon only)
- **Background**: `#212121` (Dark Grey)
- **Text Colour**: `#FFFFFF`
- **Active State**: Bold text + highlight colour (`#1A73E8`) background
- **Hover State**: Lighten background by 10%

**Navigation Items**:
```
☰ Menu
├─ 📊 Dashboard
├─ 🏢 Complexes
├─ 🏠 Units
├─ 📟 Meters
├─ 👥 Users
├─ 📈 Reports
└─ ⚙️ Settings
```

#### Collapsible Navigation
- **Mobile/Tablet**: Hamburger menu icon (☰) in top-left
- **Overlay**: Semi-transparent dark overlay when open
- **Animation**: Slide from left (300ms ease)

### 2.2 Page Layout

#### Header Section
```
┌─────────────────────────────────────────────────────────┐
│ 🏠 Breadcrumbs > Current Page             🔍 [Search]  │
│                                                          │
│ Page Title                              [+ Add New]     │
│ Subtitle or description                                 │
└─────────────────────────────────────────────────────────┘
```

**Header Components**:
- **Breadcrumbs**: Top-left, small text (12px), separated by ">"
- **Page Title**: 24px bold, left-aligned
- **Quick Actions**: Top-right (buttons, search)
- **Subtitle**: 14px regular, grey text below title

#### Content Section
- **Maximum Width**: 1400px (centered)
- **Padding**: 24px on all sides
- **Content Organization**:
  - Cards for grouped information
  - Tables for data lists
  - Forms for data entry

#### Footer Section
```
┌─────────────────────────────────────────────────────────┐
│ © 2024 Quantify Metering | Privacy | Terms | Help      │
│ Version 1.0                                             │
└─────────────────────────────────────────────────────────┘
```

**Footer Styling**:
- Background: `#F9FAFB`
- Text: 12px regular, `#757575`
- Height: 60px
- Padding: 16px

### 2.3 Grid System

#### Responsive Grid
- **System**: 12-column responsive grid
- **Gutter**: 16px between columns
- **Breakpoints**:
  - Mobile: < 768px (1 column)
  - Tablet: 768px - 1024px (2-3 columns)
  - Desktop: > 1024px (up to 12 columns)

#### Spacing Scale
| Size | Value | Usage |
|------|-------|-------|
| XS | 4px | Icon spacing, tight padding |
| SM | 8px | Form element spacing |
| MD | 16px | Default spacing between components |
| LG | 24px | Section spacing |
| XL | 32px | Large section breaks |
| XXL | 48px | Page section dividers |

### 2.4 Responsive Design

#### Mobile (< 768px)
- Collapsible sidebar menu
- Stack all columns vertically
- Full-width cards
- Touch-friendly buttons (minimum 44px height)
- Hide non-essential columns in tables

#### Tablet (768px - 1024px)
- Sidebar can be collapsed
- 2-3 column layout
- Adjusted card spacing
- Show essential table columns only

#### Desktop (> 1024px)
- Full sidebar navigation
- Multi-column layouts
- All table columns visible
- Hover states active

---

## 3. Components

### 3.1 Buttons

#### Primary Button
- **Background**: `#1A73E8`
- **Text**: White, 14px medium
- **Height**: 40px
- **Padding**: 12px 24px
- **Border Radius**: 4px
- **Hover**: Darken to `#1557B0`
- **Active**: Darken to `#0D47A1`
- **Focus**: 2px outline `#1A73E8` with 2px offset

**Example**:
```
[ Save Changes ]
```

#### Secondary Button
- **Background**: Transparent
- **Border**: 1px solid `#1A73E8`
- **Text**: `#1A73E8`, 14px medium
- **Height**: 40px
- **Padding**: 12px 24px
- **Hover**: Background `#E8F0FE`

**Example**:
```
[ Cancel ]
```

#### Tertiary Button (Text Only)
- **Background**: Transparent
- **Text**: `#1A73E8`, 14px medium
- **Hover**: Underline

#### Disabled Button
- **Background**: `#BDBDBD`
- **Text**: `#FFFFFF`
- **Cursor**: not-allowed
- **No hover or click effects**

**Example**:
```
[ Save ] (greyed out)
```

#### Button Sizes
| Size | Height | Padding | Font Size |
|------|--------|---------|-----------|
| Small | 32px | 8px 16px | 12px |
| Medium | 40px | 12px 24px | 14px |
| Large | 48px | 16px 32px | 16px |

#### Icon Buttons
- **Size**: 40px × 40px
- **Icon Size**: 20px
- **Background**: Transparent or `#F5F5F5`
- **Hover**: Background `#E0E0E0`

**Example**: [ 🗑️ ] [ ✏️ ] [ ⋮ ]

### 3.2 Forms

#### Form Layout
```
Label Text *
┌─────────────────────────────────────┐
│ Input field                         │
└─────────────────────────────────────┘
Helper text or error message
```

#### Form Field Specifications
- **Label**:
  - Position: Above input field
  - Font: 12px regular
  - Colour: `#212121`
  - Required indicator: Red asterisk `*`
- **Input Height**: 40px
- **Input Padding**: 12px
- **Border**: 1px solid `#CCCCCC`
- **Border Radius**: 4px
- **Background**: `#FFFFFF`

#### Input States
**Default**:
- Border: `#CCCCCC`

**Focus**:
- Border: `#1A73E8` (2px)
- Box Shadow: `0 0 0 3px rgba(26, 115, 232, 0.1)`

**Error**:
- Border: `#DC3545` (2px)
- Error message below in `#DC3545`

**Disabled**:
- Background: `#F5F5F5`
- Border: `#E0E0E0`
- Text: `#BDBDBD`

#### Error Messages
- **Position**: Directly below input field
- **Font**: 12px regular
- **Colour**: `#DC3545`
- **Icon**: ⚠️ or ❌
- **Example**: *"⚠️ You must enter a valid email address"*

#### Help Text
- **Position**: Below input field
- **Font**: 12px regular
- **Colour**: `#757575`
- **Example**: *"Enter a phone number with country code"*

### 3.3 Input Fields

#### Text Input
```html
<label>Email Address *</label>
<input type="email" placeholder="user@example.com" />
```

#### Dropdown/Select
- **Height**: 40px
- **Arrow Icon**: ▼ (right side, 8px from edge)
- **Hover**: Border `#1A73E8`

#### Checkbox
- **Size**: 20px × 20px
- **Border**: 1px solid `#CCCCCC`
- **Checked**: Background `#1A73E8`, white checkmark ✓
- **Label**: 14px regular, 8px spacing from checkbox

#### Radio Button
- **Size**: 20px × 20px (circle)
- **Border**: 1px solid `#CCCCCC`
- **Selected**: Inner dot `#1A73E8` (12px)

#### Toggle Switch
- **Width**: 48px
- **Height**: 24px
- **Border Radius**: 12px
- **Off**: Background `#CCCCCC`
- **On**: Background `#28A745`
- **Handle**: 20px circle, white

### 3.4 Tables

#### Table Structure
```
┌─────────────────────────────────────────────────────────┐
│ Column 1       Column 2       Column 3       Actions    │ ← Header
├─────────────────────────────────────────────────────────┤
│ Data 1         Data 2         Data 3         [ ⋮ ]     │
│ Data 1         Data 2         Data 3         [ ⋮ ]     │
│ Data 1         Data 2         Data 3         [ ⋮ ]     │
└─────────────────────────────────────────────────────────┘
                                           ← 1 2 3 4 5 →  ← Pagination
```

#### Table Styling
- **Header Row**:
  - Background: `#F1F3F4`
  - Font: 12px bold
  - Text: `#212121`
  - Height: 48px
  - Padding: 12px
- **Data Rows**:
  - Font: 14px regular
  - Height: 56px
  - Padding: 12px
  - Border Bottom: 1px solid `#E0E0E0`
- **Row Hover**: Background `#F5F5F5`
- **Row Selected**: Background `#E8F0FE`
- **Striped Rows** (optional): Alternate `#FFFFFF` and `#FAFAFA`

#### Pagination
- **Position**: Bottom right
- **Font**: 14px regular
- **Active Page**: `#1A73E8` background, white text
- **Hover**: Background `#E8F0FE`

### 3.5 Cards & Panels

#### Card Structure
```
┌─────────────────────────────────────────────────────┐
│ Card Title                            [ Action ] [ ⋮ ]│
│ ─────────────────────────────────────────────────── │
│                                                      │
│ Card content goes here                               │
│                                                      │
└─────────────────────────────────────────────────────┘
```

#### Card Styling
- **Background**: `#FFFFFF`
- **Border**: None or 1px solid `#E0E0E0`
- **Border Radius**: 8px
- **Box Shadow**: `0 1px 3px rgba(0, 0, 0, 0.05)`
- **Padding**: 24px
- **Hover** (if clickable): Box Shadow: `0 4px 12px rgba(0, 0, 0, 0.1)`

#### Card Header
- **Title**: 16px medium, `#212121`
- **Actions**: Top right, icon buttons or text buttons
- **Divider**: 1px solid `#E0E0E0` below header

### 3.6 Icons

#### Icon Library
- **Preferred**: Lucide Icons or Feather Icons
- **Format**: SVG
- **Default Size**: 20px × 20px
- **Colour**: Inherit from parent or `#212121`

#### Icon Colours by Status
| Icon | Colour | Usage |
|------|--------|-------|
| ✓ Tick / Check | `#28A745` | Success, completed |
| ❌ Cross / X | `#DC3545` | Error, delete, close |
| ⚠️ Warning | `#FFC107` | Caution, alert |
| ℹ️ Info | `#17A2B8` | Information, help |
| 📟 Meter | `#1A73E8` | Meter-related |
| 👤 User | `#757575` | User-related |

#### Icon Usage
- **With Text**: 8px spacing between icon and text
- **Button Icons**: 20px size, center-aligned
- **Table Icons**: 16px size for actions column

---

## 4. Content & Writing Style

### 4.1 Tone & Voice
- **Tone**: Clear, concise, professional, helpful
- **Voice**: Friendly but authoritative
- **Avoid**: Jargon, slang, overly technical terms

### 4.2 Writing Guidelines

#### Capitalization
- **Sentence case**: Use for most UI text
  - ✅ "Add new user"
  - ❌ "Add New User"
- **Title Case**: Only for page titles
  - ✅ "User Management Dashboard"

#### Labels & Buttons
- **Action Buttons**: Verb + Noun
  - ✅ "Save changes", "Add user", "Delete meter"
  - ❌ "Save", "Add", "Delete"
- **Labels**: Clear and descriptive
  - ✅ "Email address", "Phone number"
  - ❌ "Email", "Phone"

#### Error Messages
- **Be specific**: Explain what went wrong and how to fix it
  - ✅ "Enter a valid phone number (e.g., +27821234567)"
  - ❌ "Invalid input"
- **Plain English**: No error codes visible to users
  - ✅ "Unable to save changes. Please try again."
  - ❌ "Error 500: Internal Server Error"

#### Success Messages
- **Be positive**: Confirm the action
  - ✅ "User added successfully"
  - ✅ "Changes saved"

#### Help Text
- **Be helpful**: Provide context or examples
  - ✅ "Enter the meter serial number (found on the device label)"

#### Abbreviations
- **Avoid**: Unless widely understood
  - ✅ Use "identification number" instead of "ID"
  - ✓ OK: "kWh" (kilowatt-hour), "SMS", "PDF"

---

## 5. Accessibility

### 5.1 Contrast Requirements
- **Text Contrast**: Minimum 4.5:1 for normal text
- **Large Text**: Minimum 3:1 for text 18px+ or 14px+ bold
- **UI Components**: Minimum 3:1 for borders, icons

**Tested Combinations**:
| Foreground | Background | Ratio | Pass |
|------------|------------|-------|------|
| `#212121` | `#FFFFFF` | 16.1:1 | ✅ AAA |
| `#1A73E8` | `#FFFFFF` | 4.6:1 | ✅ AA |
| `#757575` | `#FFFFFF` | 4.7:1 | ✅ AA |

### 5.2 Keyboard Navigation
- **Tab Order**: Logical flow through all interactive elements
- **Focus Indicators**: Visible 2px outline on all focusable elements
- **Shortcuts**:
  - `Tab`: Next field
  - `Shift + Tab`: Previous field
  - `Enter`: Submit form / Activate button
  - `Esc`: Close modal / Cancel action
  - `Space`: Toggle checkbox / radio

### 5.3 Screen Reader Support
- **ARIA Labels**: Add descriptive labels to all interactive elements
  ```html
  <button aria-label="Delete user John Doe">🗑️</button>
  ```
- **Alt Text**: Provide for all images
- **Semantic HTML**: Use proper heading hierarchy (h1, h2, h3)
- **Form Labels**: Associate with inputs using `<label for="id">`

### 5.4 Colour Independence
- **Don't rely on colour alone**: Use icons, text, or patterns
  - ✅ "✓ Active" (green checkmark + text)
  - ❌ Just green background
- **Status Indicators**: Combine colour with icon or text
  - Success: `✓` + Green + "Success"
  - Error: `❌` + Red + "Error"

### 5.5 Motion & Animation
- **Respect User Preferences**: Disable animations if `prefers-reduced-motion` is set
- **Animation Duration**: 200-300ms for most interactions
- **Purpose**: Animations should enhance, not distract

---

## 6. Interaction Patterns

### 6.1 Notifications

#### Toast Notifications (Temporary)
```
┌─────────────────────────────────────────────┐
│ ✓ Success: User added successfully     [ X ]│
└─────────────────────────────────────────────┘
```

**Specifications**:
- **Position**: Top-right corner, 24px from edges
- **Width**: Maximum 400px
- **Duration**: 5 seconds (auto-dismiss)
- **Animation**: Slide in from right, fade out
- **Close Button**: X icon top-right

**Types**:
| Type | Icon | Background | Text |
|------|------|------------|------|
| Success | ✓ | `#28A745` | White |
| Error | ❌ | `#DC3545` | White |
| Warning | ⚠️ | `#FFC107` | `#212121` |
| Info | ℹ️ | `#17A2B8` | White |

#### Inline Notifications (Persistent)
```
┌─────────────────────────────────────────────┐
│ ⚠️ Warning: Some meters have not reported   │
│    data in the last 24 hours.               │
└─────────────────────────────────────────────┘
```

**Specifications**:
- **Position**: Above or below relevant content
- **Full Width**: Spans content area
- **Padding**: 16px
- **Border Radius**: 4px
- **Dismissible**: X button if user can close

#### Banner Notifications (System-Wide)
```
┌──────────────────────────────────────────────────────┐
│ ℹ️ System maintenance scheduled for 10 PM tonight   │
└──────────────────────────────────────────────────────┘
```

**Specifications**:
- **Position**: Top of page, below header
- **Full Width**: 100% of viewport
- **Background**: Status colour (lighter shade)
- **Icon**: Left-aligned
- **Close**: Optional X button right-aligned

### 6.2 Modals & Dialogs

#### Modal Structure
```
        ┌─────────────────────────────────────┐
        │ Modal Title                    [ X ]│
        ├─────────────────────────────────────┤
        │                                     │
        │ Modal content goes here...          │
        │                                     │
        ├─────────────────────────────────────┤
        │              [ Cancel ] [ Confirm ] │
        └─────────────────────────────────────┘
```

**Specifications**:
- **Width**: 
  - Small: 400px
  - Medium: 600px
  - Large: 800px
- **Max Height**: 80vh (scroll if needed)
- **Backdrop**: Semi-transparent dark overlay (`rgba(0, 0, 0, 0.5)`)
- **Border Radius**: 8px
- **Animation**: Fade in (200ms)

**Modal Types**:
- **Confirmation**: "Are you sure you want to delete this user?"
- **Form**: Add/edit data
- **Information**: Display details

**Best Practices**:
- Use modals sparingly (avoid modal fatigue)
- Always provide a clear way to close (X button + Cancel button)
- Focus trap: Keep keyboard focus within modal
- Prevent scrolling of background content

### 6.3 Loading States

#### Spinner (Short Waits < 5s)
```
     ⟲
  Loading...
```

**Specifications**:
- **Size**: 32px × 32px
- **Colour**: `#1A73E8`
- **Animation**: Rotate 360° in 1 second, infinite
- **Text**: "Loading..." below spinner

#### Skeleton Loaders (Content Loading)
```
┌─────────────────────────────────┐
│ ████████████                    │ ← Header
│ ████████      ██████            │ ← Content
│ ████████████████                │
└─────────────────────────────────┘
```

**Specifications**:
- **Background**: `#E0E0E0`
- **Animation**: Shimmer effect left to right
- **Usage**: Tables, cards, forms while loading

#### Progress Bar (Long Processes > 10s)
```
Processing...
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 75%
```

**Specifications**:
- **Height**: 8px
- **Border Radius**: 4px
- **Background**: `#E0E0E0`
- **Progress**: `#1A73E8`
- **Percentage**: Display below or on right

#### Disabled State (During Processing)
- Disable buttons/inputs to prevent duplicate submissions
- Show spinner or "Processing..." text
- Cursor: `wait` or `not-allowed`

### 6.4 Search

#### Search Input
```
┌─────────────────────────────────────┐
│ 🔍 Search users...             [ X ]│
└─────────────────────────────────────┘
```

**Specifications**:
- **Height**: 40px
- **Icon**: 🔍 left-aligned, 12px from edge
- **Placeholder**: Descriptive hint (e.g., "Search users...")
- **Clear Button**: X icon appears when text is entered
- **Width**: Minimum 240px, maximum 600px

#### Predictive Search
- **Debounce**: 300ms after user stops typing
- **Dropdown**: Shows top 5-10 results
- **Highlight**: Match text in bold
- **Keyboard Navigation**: Arrow keys to navigate, Enter to select

### 6.5 Tooltips

#### Tooltip Style
```
        ┌─────────────┐
        │ Meter ID    │  ← Tooltip
        └──────┬──────┘
               │
           [ ℹ️ ]  ← Icon
```

**Specifications**:
- **Background**: `#212121`
- **Text**: White, 12px
- **Padding**: 8px 12px
- **Border Radius**: 4px
- **Arrow**: 6px pointing to element
- **Trigger**: Hover or focus
- **Delay**: 500ms before showing
- **Max Width**: 200px

### 6.6 Dropdowns & Menus

#### Dropdown Menu
```
           [ Actions ▼ ]
           ┌──────────────┐
           │ Edit         │
           │ Delete       │
           │ View details │
           └──────────────┘
```

**Specifications**:
- **Background**: `#FFFFFF`
- **Border**: 1px solid `#E0E0E0`
- **Box Shadow**: `0 2px 8px rgba(0, 0, 0, 0.15)`
- **Border Radius**: 4px
- **Item Height**: 40px
- **Item Hover**: Background `#F5F5F5`
- **Item Padding**: 12px

---

## 7. Security & Data Handling

### 7.1 Password Fields

#### Password Input
```
Password *
┌─────────────────────────────────────┐
│ ••••••••••••                   [ 👁 ]│
└─────────────────────────────────────┘
```

**Specifications**:
- **Default**: Hidden (type="password")
- **Toggle**: Eye icon (👁) to show/hide
- **Requirements**: Display below field
  - "At least 8 characters"
  - "Include uppercase, lowercase, number"
- **Strength Indicator**: 
  - Weak (red), Medium (yellow), Strong (green)

### 7.2 Auto-Logout

**Behavior**:
- **Timeout**: 15 minutes of inactivity
- **Warning**: Show modal 2 minutes before logout
  - "Your session will expire in 2 minutes. Continue?"
  - [ Logout ] [ Stay Logged In ]
- **Redirect**: Return to login page on timeout

### 7.3 Role-Based Access

**UI Behavior**:
- **Hide**: Remove entire UI elements if user lacks permission
- **Disable**: Grey out buttons with tooltip "Insufficient permissions"
- **Example**:
  - Super Admin: Sees all buttons
  - Property Manager: Delete button disabled
  - Resident: Delete button hidden

### 7.4 Sensitive Data Masking

**Data Types to Mask**:
- **Credit Card**: **** **** **** 1234
- **Bank Account**: ****5678
- **ID Number**: ****789
- **Phone**: +27 ** *** 4567

**Implementation**:
- Show last 4 digits only
- Provide "Show" button for authorized users
- Log access to unmasked data

### 7.5 Audit Trails

**Display**:
- Show "Last modified by [User] on [Date]"
- Activity log table for admins
- Include: Action, User, Date/Time, IP Address

---

## 8. Implementation Examples

### 8.1 Dashboard Card Example

```html
<div class="card">
  <div class="card-header">
    <h3 class="card-title">Meter Summary</h3>
    <button class="btn-icon">⋮</button>
  </div>
  <div class="card-body">
    <div class="stat">
      <div class="stat-value">450</div>
      <div class="stat-label">Total Meters</div>
    </div>
    <div class="stat">
      <div class="stat-value success">435</div>
      <div class="stat-label">Active</div>
    </div>
    <div class="stat">
      <div class="stat-value warning">15</div>
      <div class="stat-label">Low Credit</div>
    </div>
  </div>
</div>
```

### 8.2 Form Example

```html
<form class="form">
  <div class="form-group">
    <label for="email">Email Address *</label>
    <input 
      type="email" 
      id="email" 
      placeholder="user@example.com"
      required
    />
    <span class="help-text">We'll never share your email</span>
  </div>
  
  <div class="form-group">
    <label for="role">Role *</label>
    <select id="role" required>
      <option value="">Select role...</option>
      <option value="resident">Resident</option>
      <option value="property_manager">Property Manager</option>
    </select>
  </div>
  
  <div class="form-actions">
    <button type="button" class="btn-secondary">Cancel</button>
    <button type="submit" class="btn-primary">Save User</button>
  </div>
</form>
```

### 8.3 Table Example

```html
<table class="data-table">
  <thead>
    <tr>
      <th>Unit</th>
      <th>Resident</th>
      <th>Meter Type</th>
      <th>Balance</th>
      <th>Status</th>
      <th>Actions</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <td>A101</td>
      <td>John Doe</td>
      <td>Electricity</td>
      <td class="success">R 150.50</td>
      <td><span class="badge success">Active</span></td>
      <td>
        <button class="btn-icon" aria-label="Actions">⋮</button>
      </td>
    </tr>
  </tbody>
</table>
```

### 8.4 Notification Toast Example

```html
<div class="toast toast-success">
  <span class="toast-icon">✓</span>
  <span class="toast-message">User added successfully</span>
  <button class="toast-close" aria-label="Close">×</button>
</div>
```

---

## Appendix A: Color Palette Reference

### Primary Colors
```
#1A73E8  ████  Primary Blue
#F9FAFB  ████  Light Grey
#212121  ████  Dark Grey
```

### Status Colors
```
#28A745  ████  Success Green
#FFC107  ████  Warning Amber
#DC3545  ████  Error Red
#17A2B8  ████  Info Teal
```

### Neutral Colors
```
#FFFFFF  ████  White
#F5F5F5  ████  Hover Grey
#F1F3F4  ████  Header Grey
#E0E0E0  ████  Border Grey
#CCCCCC  ████  Border
#BDBDBD  ████  Disabled Grey
#757575  ████  Secondary Text
```

---

## Appendix B: Component Library

**Recommended UI Libraries**:
- Material-UI (MUI) for React
- Ant Design for React
- Bootstrap 5
- Tailwind CSS

**Icon Libraries**:
- Lucide Icons: https://lucide.dev/
- Feather Icons: https://feathericons.com/
- Material Icons: https://fonts.google.com/icons

---

## Appendix C: Accessibility Testing Tools

- **WAVE**: Web accessibility evaluation tool
- **axe DevTools**: Browser extension for accessibility testing
- **Lighthouse**: Chrome DevTools audit
- **Contrast Checker**: WebAIM Contrast Checker

---

*This style guide ensures consistency, accessibility, and usability across the Quantify Metering Administration System. All UI components should adhere to these standards.*


# Administration System Style Guide

## 1. Branding & Identity

- **Logo**

  - Placement: top-left of navigation bar
  - Maintain at least 16px clear space around the logo

- **Colour Palette**

  - Primary: `#1A73E8` (Blue – buttons, links, highlights)
  - Secondary: `#F9FAFB` (Light Grey – backgrounds)
  - Neutral: `#212121` (Dark Grey – text, icons)
  - Status:
    - Success: `#28A745` (Green)
    - Warning: `#FFC107` (Amber)
    - Error: `#DC3545` (Red)
    - Info: `#17A2B8` (Teal)

- **Typography**
  - Primary font: _Inter_ or _Roboto_ (sans-serif)
  - Sizes:
    - Page Title: 24px / Bold
    - Section Header: 18px / Medium
    - Body: 14–16px / Regular
    - Captions & Labels: 12px / Regular
  - Example:
    - **Page Title**: _“Administration Dashboard”_
    - **Section Header**: _“User Management”_
    - **Button Text**: _“Save changes”_

---

## 2. Layout & Structure

- **Navigation**

  - Left sidebar for complex systems; top bar for simpler setups
  - Active state: bold + highlight colour (`#1A73E8`)
  - Collapsible option for smaller screens

- **Page Layout**

  - Header: page title, breadcrumbs, search, and quick actions
  - Content: cards, tables, or forms
  - Footer: legal links, version number, copyright

- **Grid System**

  - 12-column responsive grid
  - Spacing: minimum 16px padding between components

- **Responsive Design**
  - Mobile: collapsible menus, stacked layout
  - Tablet/Desktop: grid-based alignment

---

## 3. Components

- **Buttons**

  - Primary: solid `#1A73E8` with white text
  - Secondary: outline with `#1A73E8` border
  - Disabled: `#BDBDBD`, no hover or click
  - Hover: darken by 5–10%
  - Standard height: 40px
  - Example:
    - Primary → `#1A73E8` Save

- **Forms**

  - Labels: always above input fields
  - Required fields: marked with `*`
  - Error messages: red (`#DC3545`), shown directly below input
  - Example:
    - Email Address *  
      [ input box ]  
      *You must enter a valid email address\*

- **Input Fields**

  - Standard height: 40px
  - Border: `#CCCCCC`, 1px solid
  - Focus: border `#1A73E8`, subtle shadow

- **Tables**

  - Header row: bold, background tint (`#F1F3F4`)
  - Row hover: light grey (`#F5F5F5`)
  - Pagination: bottom right

- **Cards & Panels**

  - Rounded corners: 8px
  - Subtle shadow: rgba(0, 0, 0, 0.05)
  - Title: top left; actions: top right

- **Icons**
  - Use vector icons (Lucide / Feather)
  - Colour examples:
    - Tick → Green (`#28A745`)
    - Cross → Red (`#DC3545`)

---

## 4. Content & Writing Style

- **Tone**: Clear, concise, professional
- **Guidelines**:
  - Use sentence case (e.g. “Add user”)
  - Error messages in plain English: _“Enter a valid phone number”_
  - Avoid abbreviations unless widely known

---

## 5. Accessibility

- Text contrast: at least 4.5:1
- Keyboard navigation: `Tab` cycle for all fields
- Screen reader: include `aria-labels`
- Do not rely on colour alone (use icons/text as well)

---

## 6. Interaction Patterns

- **Notifications**

  - Success: green banner
  - Error: red inline message
  - Info/Warning: blue/yellow banner

- **Modals/Dialogs**

  - Use only for confirmation or critical actions
  - Must include:
    - Title
    - Clear action button(s)
    - Close option (“X” or Cancel button)

- **Loading States**

  - Use spinner for short waits (<5s)
  - Use skeleton loaders for content loading
  - Show progress bar for long processes (>10s)

- **Search**
  - Predictive text where possible
  - “Clear” button inside field

---

## 7. Security & Data Handling

- Passwords: hidden by default, with “Show” toggle
- Auto-logout: after 15 minutes of inactivity
- Role-based access: hide or disable restricted actions
- Sensitive data: masked where appropriate (e.g. credit card numbers)

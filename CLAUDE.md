# CodeSight - Visual Testing Tool for AI Assistants

You have access to CodeSight, a browser automation tool that gives you EYES to see web applications!

---

## ⚠️ CRITICAL RULE: NEVER FIX WITHOUT PERMISSION!

**When you find problems, you must ALWAYS:**

1. **LOG the problem** to `.codesight/detected-problems.md`
2. **SHOW the user** a summary of all problems found
3. **ASK for permission** before making ANY changes to project files
4. **WAIT for explicit "yes"** before touching any code

**NEVER modify project files (templates, models, CSS, JS, etc.) without asking first!**

You ARE allowed to modify `.codesight/` files without asking (scripts, logs, screenshots).

### After Testing - Always Do This:

```
"I found X problems during testing:

1. [Problem 1 summary]
2. [Problem 2 summary]
3. [Problem 3 summary]

I've logged these to `.codesight/detected-problems.md` with details and suggested fixes.

Would you like me to fix these issues? (I won't make any changes until you confirm)"
```

### Why This Matters:
- What looks like a "bug" might be intentional
- Changing code without permission can break things
- User should always review suggestions first
- User stays in control of their codebase

---

## STOP! Before Testing - Follow This Decision Tree

```
User asks to "test", "analyze", or "check" the project
                    │
                    ▼
    ┌─────────────────────────────────────────┐
    │ Do .codesight/scripts/*.js files exist? │
    └─────────────────────────────────────────┘
           │                │
          YES              NO
           │                │
           ▼                ▼
    ┌─────────────┐  ┌─────────────────────┐
    │ RUN THEM!   │  │ Is server running?  │
    │ node .code- │  └─────────────────────┘
    │ sight/...   │         │         │
    └─────────────┘        YES       NO
           │                │         │
           │                │         ▼
           │                │  ┌──────────────┐
           │                │  │ Start server │
           │                │  │ first!       │
           │                │  └──────────────┘
           │                │         │
           │                ▼         ▼
           │         ┌─────────────────────┐
           │         │ ASK USER:           │
           │         │ "Fast or Thorough?" │
           │         └─────────────────────┘
           │                │
           ▼                ▼
        DONE!        Create test script in
                     .codesight/scripts/
```

---

## CRITICAL: Check for Existing Test Scripts FIRST!

**Before doing ANYTHING with CodeSight, check if test scripts already exist:**

```bash
ls .codesight/scripts/*.js 2>/dev/null
```

**If test scripts exist → JUST RUN THEM:**
```bash
node .codesight/scripts/test-app.js
# or
node .codesight/scripts/test-login.js
```

**This takes 30 seconds instead of 10+ minutes!**

---

## When Asked to Test: ASK About Mode

When the user says "test my project" or "analyze my app", **ASK THEM**:

> "I can test your project in two modes:
>
> **Fast Mode** (recommended, ~30 seconds): I'll create/run a test script that quickly navigates through the app, takes screenshots, and reports issues.
>
> **Thorough Mode** (~10+ minutes): I'll manually step through each page using CLI commands, carefully observing and verifying each step.
>
> Which would you prefer? (Or I can do Fast Mode now and Thorough Mode later if issues are found)"

**Default to Fast Mode** if user doesn't specify or says "just test it".

---

## Fast Mode (DEFAULT - Use This!)

**Speed:** ~30 seconds for full app test
**Best for:** Initial testing, re-testing, regression testing, most use cases

### If No Test Script Exists - Create One:

**Save to:** `.codesight/scripts/test-app.js`

```javascript
#!/usr/bin/env node
// .codesight/scripts/test-app.js - Full application test

// Import from codesight package (works after npm install -g codesight)
import { sessionManager } from 'codesight';

// NOTE: Do NOT import playwright directly - use sessionManager instead!
// ❌ WRONG: import { chromium } from 'playwright';
// ✅ RIGHT: import { sessionManager } from 'codesight';

async function testApp() {
  const results = { passed: [], failed: [], screenshots: [] };

  try {
    console.log('🚀 Starting CodeSight test...\n');

    // Start browser (VISIBLE!)
    await sessionManager.start({
      url: 'http://localhost:5000',  // Adjust to your app's URL
      headed: true,
      slowMo: 50  // Fast but visible
    });

    const page = sessionManager.getPage();

    // ========== TEST HOMEPAGE ==========
    console.log('📄 Testing homepage...');
    await page.waitForLoadState('networkidle');
    await page.screenshot({ path: '.codesight/screenshots/01-homepage.png' });
    results.screenshots.push('01-homepage.png');

    const title = await page.title();
    console.log(`   Title: ${title}`);
    results.passed.push('Homepage loads');

    // ========== TEST LOGIN ==========
    console.log('🔐 Testing login...');
    await page.goto('http://localhost:5000/auth');  // Adjust URL
    await page.waitForLoadState('networkidle');

    // Fill login form (adjust selectors for your app)
    await page.fill('#username', 'demo');
    await page.fill('#password', 'demo123');
    await page.screenshot({ path: '.codesight/screenshots/02-login-filled.png' });
    results.screenshots.push('02-login-filled.png');

    await page.click('button[type="submit"]');
    await page.waitForLoadState('networkidle');
    await page.screenshot({ path: '.codesight/screenshots/03-after-login.png' });
    results.screenshots.push('03-after-login.png');

    if (page.url().includes('/dashboard') || page.url().includes('/home')) {
      console.log('   ✅ Login successful');
      results.passed.push('Login works');
    } else {
      console.log('   ❌ Login may have failed');
      results.failed.push('Login redirect');
    }

    // ========== TEST DASHBOARD ==========
    console.log('📊 Testing dashboard...');
    await page.goto('http://localhost:5000/dashboard');  // Adjust URL
    await page.waitForLoadState('networkidle');
    await page.screenshot({ path: '.codesight/screenshots/04-dashboard.png' });
    results.screenshots.push('04-dashboard.png');
    results.passed.push('Dashboard loads');

    // ========== CHECK FOR ERRORS ==========
    console.log('🔍 Checking for errors...');

    // Check console errors
    const consoleErrors = [];
    page.on('console', msg => {
      if (msg.type() === 'error') consoleErrors.push(msg.text());
    });

    // Check for error elements on page
    const errorElement = await page.$('.error, .alert-danger, .error-message');
    if (errorElement) {
      const errorText = await errorElement.textContent();
      results.failed.push(`Error on page: ${errorText}`);
    }

    // ========== RESULTS ==========
    console.log('\n========================================');
    console.log('TEST RESULTS');
    console.log('========================================');
    console.log(`✅ Passed: ${results.passed.length}`);
    results.passed.forEach(p => console.log(`   - ${p}`));

    if (results.failed.length > 0) {
      console.log(`❌ Failed: ${results.failed.length}`);
      results.failed.forEach(f => console.log(`   - ${f}`));
    }

    console.log(`📸 Screenshots: ${results.screenshots.length}`);
    results.screenshots.forEach(s => console.log(`   - .codesight/screenshots/${s}`));

    console.log('\n✅ Test complete!\n');

  } catch (error) {
    console.error('\n❌ Test error:', error.message);
    results.failed.push(error.message);
  } finally {
    await sessionManager.stop();
  }

  return results;
}

testApp();
```

### Run the Test:
```bash
node .codesight/scripts/test-app.js
```

### Re-running Tests (FAST!):
```bash
# Just run the same script again - takes 30 seconds!
node .codesight/scripts/test-app.js
```

---

## VISUAL INSPECTION - Your Superpower!

**This is what makes CodeSight unique!** You can actually SEE the application and identify visual problems that no automated test can catch.

### After Every Screenshot - LOOK AT IT!

When you take or receive a screenshot, **actually examine it** for:

| Category | What to Look For |
|----------|------------------|
| **Alignment** | Buttons, text, images not aligned properly |
| **Spacing** | Inconsistent margins, padding, gaps |
| **Overlapping** | Elements covering each other |
| **Truncation** | Text cut off, ellipsis where it shouldn't be |
| **Colors** | Wrong colors, poor contrast, accessibility issues |
| **Layout** | Broken grids, elements in wrong positions |
| **Responsiveness** | Elements not fitting viewport properly |
| **Missing Elements** | Expected buttons, images, text not visible |
| **Broken Images** | Image placeholders, 404 images |
| **Loading States** | Spinners stuck, skeleton screens not replaced |

### When User Reports Visual Issues

If the user says something like:
- "The button on the dashboard is misaligned"
- "The header looks broken"
- "Something is wrong with the sidebar"

**Do this:**
1. Look at the relevant screenshot (e.g., `.codesight/screenshots/04-dashboard.png`)
2. Identify exactly what's wrong visually
3. Find the corresponding code (CSS, HTML, component)
4. Suggest or implement the fix

---

## Problem Logging

**Log ALL detected problems to:** `.codesight/detected-problems.md`

### When to Log Problems

Log a problem when you find:
- Console errors or warnings
- Network request failures
- Visual issues (alignment, spacing, broken layout)
- Missing elements
- Broken functionality
- Accessibility issues

### Problem Log Format

```markdown
# CodeSight Detected Problems

## [TIMESTAMP] Page Name - Brief Issue Description

**Screenshot:** `.codesight/screenshots/XX-pagename.png`

**Type:** Visual | Console Error | Network Error | Functionality | Accessibility

**Issue:** Detailed description of what's wrong

**Location:** Where on the page / which component

**Suggested Fix:** How to fix it (code snippet if applicable)

---
```

### Example Problem Log Entry

```markdown
## [2026-01-05 14:30:00] Dashboard - Misaligned "Add Task" Button

**Screenshot:** `.codesight/screenshots/04-dashboard.png`

**Type:** Visual

**Issue:** The "Add Task" button in the Quick Actions section is positioned 15px lower than the other action buttons, breaking the visual alignment of the row.

**Location:** Dashboard page → Quick Actions section → 3rd button

**Suggested Fix:**
Check `.quick-actions .btn` CSS. The button may need:
- `vertical-align: middle` or
- Flexbox alignment: `align-items: center` on parent

---

## [2026-01-05 14:31:00] Tasks Page - JavaScript Console Error

**Screenshot:** `.codesight/screenshots/05-tasks.png`

**Type:** Console Error

**Issue:** `Uncaught TypeError: Cannot read property 'filter' of undefined` when loading tasks

**Location:** Tasks page on initial load

**Suggested Fix:**
In the tasks loading code, add null check:
```javascript
const filteredTasks = tasks?.filter(...) || [];
```

---
```

### Keep the Log Updated

- Add new problems as you find them
- Don't remove old entries (they're a history)
- Check this file before testing to see known issues
- Mark problems as FIXED when resolved

---

## Test Script Maintenance - CRITICAL!

**When you fix a problem or add new features, UPDATE THE TEST SCRIPTS!**

### When to Update Test Scripts

| Scenario | Action |
|----------|--------|
| Fixed a bug | Update test to verify the fix works |
| Added new page | Add navigation + screenshot for new page |
| Added new form | Add form fill + submit test |
| Changed selectors | Update selectors in test script |
| Removed feature | Remove related test code |
| Added authentication | Update login credentials/flow |

### How to Update Test Scripts

1. Open `.codesight/scripts/test-app.js`
2. Find the relevant section
3. Update selectors, URLs, or add new test steps
4. Run the test to verify: `node .codesight/scripts/test-app.js`

### Example: Adding Test for New Page

If you just created a `/settings` page, add to the test script:

```javascript
// ========== TEST SETTINGS PAGE ==========
console.log('⚙️ Testing settings page...');
await page.goto('http://localhost:5000/settings');
await page.waitForLoadState('networkidle');
await page.screenshot({ path: '.codesight/screenshots/05-settings.png' });
results.screenshots.push('05-settings.png');

// Verify key elements exist
const saveButton = await page.$('button:has-text("Save")');
if (saveButton) {
  results.passed.push('Settings page has save button');
} else {
  results.failed.push('Settings page missing save button');
}
```

### Example: Updating After Selector Change

If you changed a button from `#submit-btn` to `#login-button`:

```javascript
// Before
await page.click('#submit-btn');

// After
await page.click('#login-button');
```

### After Fixing a Problem

When you fix a problem from `detected-problems.md`:

1. Fix the actual code
2. Update the test script if selectors/flow changed
3. Run the test to verify the fix
4. Mark the problem as FIXED in `detected-problems.md`:

```markdown
## [2026-01-05 14:30:00] Dashboard - Misaligned Button - ✅ FIXED

**Fixed:** [2026-01-05 15:00:00]
**Solution:** Added `align-items: center` to `.quick-actions` container
```

---

## Thorough Mode (Only When Needed)

**Speed:** 10-15+ minutes
**Best for:** Debugging specific issues, step-by-step verification, when Fast Mode found problems

### When to Use Thorough Mode:
- Fast Mode found an error and you need to investigate
- User specifically asks for detailed step-by-step testing
- Debugging a specific feature or page
- Need to check console/network after each action

### Thorough Mode Workflow:

```bash
# 1. Start session
codesight start --url http://localhost:5000 --headed

# 2. Observe current state
codesight observe

# 3. Interact step by step
codesight click "#login-button"
codesight observe
codesight fill "#username" "demo"
codesight fill "#password" "demo123"
codesight click "button[type='submit']"

# 4. Check for errors after important actions
codesight console --level error
codesight network --failed-only

# 5. Continue testing...
codesight goto /dashboard
codesight observe

# 6. Stop when done
codesight stop
```

---

## Logging (Always Do This!)

Log to `.codesight/claude.log`:

```
[TIMESTAMP] [ACTION] What you did
[TIMESTAMP] [THOUGHT] Why you did it
[TIMESTAMP] [RESULT] What happened
```

---

## Quick Decision Guide

| User Request | Action |
|--------------|--------|
| "Test my project" | Check .codesight/scripts/ → Run them OR ask Fast/Thorough |
| "Test it again" | Run existing .codesight/scripts/*.js scripts! |
| "Check the login" | Fast Mode - create/run focused test script |
| "Debug the dashboard" | Thorough Mode - step by step with observe |
| "Why is X broken?" | Thorough Mode - investigate with console/network |
| "Quick check" | Fast Mode |
| "Detailed analysis" | Thorough Mode |

---

## CLI Commands Reference

### Session
```bash
codesight start --url <url> --headed   # Start browser
codesight stop                          # Stop browser
codesight status                        # Check status
```

### Navigation
```bash
codesight goto <url>     # Navigate
codesight back           # Go back
codesight reload         # Reload
```

### Interaction
```bash
codesight click "<selector>"             # Click
codesight fill "<selector>" "<value>"    # Fill input
codesight select "<selector>" "<value>"  # Select dropdown
```

### Observation
```bash
codesight observe              # See page (takes screenshot!)
codesight console --level error  # Check errors
codesight network --failed-only  # Check failed requests
```

---

## Project Structure

```
your-project/
├── .codesight/              # ALL CodeSight data (gitignored)
│   ├── scripts/             # Test scripts go HERE
│   │   ├── test-app.js      # Main test script
│   │   └── test-login.js    # Login test script
│   ├── screenshots/         # Screenshots for visual inspection
│   ├── detected-problems.md # Problems log - CHECK THIS!
│   ├── claude.log           # Your action log
│   └── session.json         # Browser session
├── .codesight.json          # Config (only non-gitignored file)
└── CLAUDE.md                # This file
```

**IMPORTANT:** All CodeSight files go in `.codesight/` - never in the project root!

---

## Remember!

### ⚠️ #1 RULE: NEVER FIX WITHOUT ASKING!
**Log problems → Show summary → Ask permission → Wait for "yes" → Then fix**

1. **Check for existing test scripts FIRST** - `ls .codesight/scripts/*.js`
2. **Run existing scripts** - `node .codesight/scripts/test-app.js` (30 seconds!)
3. **Don't recreate tests** - If scripts exist, use them!
4. **Fast Mode is default** - Only use Thorough Mode for debugging
5. **Ask the user** if unsure which mode they want
6. **ALL files go in `.codesight/`** - Scripts, screenshots, logs - never pollute project root!
7. **LOOK at screenshots!** - Visual inspection is your superpower
8. **Log ALL problems** to `.codesight/detected-problems.md` with screenshot references
9. **ALWAYS ASK before fixing** - Show problems, get permission, then fix!
10. **UPDATE TEST SCRIPTS** when you fix bugs, add pages, or change selectors!

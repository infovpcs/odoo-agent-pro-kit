---
name: agent_browser_automation
description: Browser automation for Odoo web testing, form filling, screenshots, documentation, and frontend validation. Use when testing Odoo web pages, creating module screenshots, validating forms, or automating browser interactions for Odoo 17/18/19.
version: 1.0.0
author: VPCS Team
category: testing_automation
odoo_versions: ["17.0", "18.0", "19.0"]
tags: [browser, automation, testing, screenshot, odoo, web, forms, validation, documentation, playwright]
allowed-tools: Bash(agent-browser:*)
---

# Browser Automation with agent-browser

## Goal
Automate Odoo browser testing, form interactions, screenshot generation for module documentation, and frontend validation across Odoo 17/18/19.

## ⚠️ Important: Dynamic Port Configuration

**Before running any browser automation commands**, you must determine your local Odoo server's actual port and URL:

### Step 1: Check your Odoo config file
```bash
# For your workspace version (17, 18, or 19)
cat /path/to/VERSION_workspace/config/odoo.conf.VERSION

# Look for the 'xmlrpc_port' parameter:
xmlrpc_port = 8017    # Odoo 17
xmlrpc_port = 8018    # Odoo 18  
xmlrpc_port = 8019    # Odoo 19
```

### Step 2: Verify Odoo is running on that port
```bash
curl http://localhost:8017/web/health || echo "Odoo not running on 8017"
```

### Step 3: Use the correct URL in your commands
```bash
# Examples (replace 8017 with your actual port):
agent-browser open http://localhost:8017/web                    # Login page
agent-browser open http://localhost:8017/web#model=res.partner  # List view
agent-browser open http://localhost:8017/shop                   # Website page
```

**⚠️ Common Mistake:** Using hardcoded URLs like `http://localhost:8090` when your config has `xmlrpc_port = 8017`

### Step 4: Automatically detect port from config (Recommended for Agents)

Instead of manually checking, agents should automatically extract the port:

```bash
#!/bin/bash
# auto_detect_odoo_url.sh - Dynamically determine Odoo URL from config

WORKSPACE_PATH="${1:-.}"  # Default to current directory
VERSION="${2:-19}"         # Default to version 19

# Find the config file
CONFIG_FILE="$WORKSPACE_PATH/config/odoo.conf.$VERSION"

if [ ! -f "$CONFIG_FILE" ]; then
    echo "❌ Config file not found: $CONFIG_FILE"
    echo "Check that WORKSPACE_PATH is correct"
    exit 1
fi

# Extract xmlrpc_port from config
XMLRPC_PORT=$(grep "^xmlrpc_port" "$CONFIG_FILE" | awk '=' '{print $NF}' | tr -d ' ')

if [ -z "$XMLRPC_PORT" ]; then
    echo "❌ xmlrpc_port not found in $CONFIG_FILE"
    echo "Add this to your config: xmlrpc_port = 8017"
    exit 1
fi

# Construct Odoo URL
ODOO_URL="http://localhost:$XMLRPC_PORT"

echo "✅ Detected Odoo URL: $ODOO_URL"
echo "Export for use in scripts:"
echo "export ODOO_URL='$ODOO_URL'"

# Return the URL
echo "$ODOO_URL"
```

**Usage in agent scripts:**

```bash
# Source the detection script
source auto_detect_odoo_url.sh "${ODOO_WORKSPACES_ROOT:-$HOME/odoo-workspaces}/17_workspace" 17

# Or extract directly:
XMLRPC_PORT=$(grep "^xmlrpc_port" /path/to/config/odoo.conf.17 | awk '{print $NF}')
ODOO_URL="http://localhost:$XMLRPC_PORT"

# Use in browser automation:
agent-browser open "$ODOO_URL/web"
agent-browser open "$ODOO_URL/web#model=res.partner"
agent-browser open "$ODOO_URL/shop"
```

**One-liner to get port:**
```bash
ODOO_PORT=$(grep "xmlrpc_port" /path/to/config/odoo.conf.VERSION | tail -1 | awk '{print $NF}')
agent-browser open http://localhost:$ODOO_PORT/web
```

## When to use
- Testing Odoo web pages and forms (login, create, update, delete)
- Generating screenshots for module documentation
- Validating frontend behavior (JavaScript, OWL components in Odoo 19)
- Automating repetitive web interactions
- Testing XML-rendered views and dynamic content
- Creating CI/CD test suites for Odoo modules

## Quick start

```bash
agent-browser open <url>        # Navigate to page
agent-browser snapshot -i       # Get interactive elements with refs
agent-browser click @e1         # Click element by ref
agent-browser fill @e2 "text"   # Fill input by ref
agent-browser close             # Close browser
```

## Core workflow

1. Navigate: `agent-browser open <url>`
2. Snapshot: `agent-browser snapshot -i` (returns elements with refs like `@e1`, `@e2`)
3. Interact using refs from the snapshot
4. Re-snapshot after navigation or significant DOM changes

---

## 📖 Level 2: Full Instructions & Commands

Complete command reference and usage patterns for browser automation.

## Commands

### Navigation
```bash
agent-browser open <url>      # Navigate to URL
agent-browser back            # Go back
agent-browser forward         # Go forward
agent-browser reload          # Reload page
agent-browser close           # Close browser
```

### Snapshot (page analysis)
```bash
agent-browser snapshot            # Full accessibility tree
agent-browser snapshot -i         # Interactive elements only (recommended)
agent-browser snapshot -c         # Compact output
agent-browser snapshot -d 3       # Limit depth to 3
agent-browser snapshot -s "#main" # Scope to CSS selector
```

### Interactions (use @refs from snapshot)
```bash
agent-browser click @e1           # Click
agent-browser dblclick @e1        # Double-click
agent-browser focus @e1           # Focus element
agent-browser fill @e2 "text"     # Clear and type
agent-browser type @e2 "text"     # Type without clearing
agent-browser press Enter         # Press key
agent-browser press Control+a     # Key combination
agent-browser keydown Shift       # Hold key down
agent-browser keyup Shift         # Release key
agent-browser hover @e1           # Hover
agent-browser check @e1           # Check checkbox
agent-browser uncheck @e1         # Uncheck checkbox
agent-browser select @e1 "value"  # Select dropdown
agent-browser scroll down 500     # Scroll page
agent-browser scrollintoview @e1  # Scroll element into view
agent-browser drag @e1 @e2        # Drag and drop
agent-browser upload @e1 file.pdf # Upload files
```

### Get information
```bash
agent-browser get text @e1        # Get element text
agent-browser get html @e1        # Get innerHTML
agent-browser get value @e1       # Get input value
agent-browser get attr @e1 href   # Get attribute
agent-browser get title           # Get page title
agent-browser get url             # Get current URL
agent-browser get count ".item"   # Count matching elements
agent-browser get box @e1         # Get bounding box
```

### Check state
```bash
agent-browser is visible @e1      # Check if visible
agent-browser is enabled @e1      # Check if enabled
agent-browser is checked @e1      # Check if checked
```

### Screenshots & PDF
```bash
agent-browser screenshot          # Screenshot to stdout
agent-browser screenshot path.png # Save to file
agent-browser screenshot --full   # Full page
agent-browser pdf output.pdf      # Save as PDF
```

### Video recording
```bash
agent-browser record start ./demo.webm    # Start recording (uses current URL + state)
agent-browser click @e1                   # Perform actions
agent-browser record stop                 # Stop and save video
agent-browser record restart ./take2.webm # Stop current + start new recording
```
Recording creates a fresh context but preserves cookies/storage from your session. If no URL is provided, it automatically returns to your current page. For smooth demos, explore first, then start recording.

### Wait
```bash
agent-browser wait @e1                     # Wait for element
agent-browser wait 2000                    # Wait milliseconds
agent-browser wait --text "Success"        # Wait for text
agent-browser wait --url "**/dashboard"    # Wait for URL pattern
agent-browser wait --load networkidle      # Wait for network idle
agent-browser wait --fn "window.ready"     # Wait for JS condition
```

### Mouse control
```bash
agent-browser mouse move 100 200      # Move mouse
agent-browser mouse down left         # Press button
agent-browser mouse up left           # Release button
agent-browser mouse wheel 100         # Scroll wheel
```

### Semantic locators (alternative to refs)
```bash
agent-browser find role button click --name "Submit"
agent-browser find text "Sign In" click
agent-browser find label "Email" fill "user@test.com"
agent-browser find first ".item" click
agent-browser find nth 2 "a" text
```

### Browser settings
```bash
agent-browser set viewport 1920 1080      # Set viewport size
agent-browser set device "iPhone 14"      # Emulate device
agent-browser set geo 37.7749 -122.4194   # Set geolocation
agent-browser set offline on              # Toggle offline mode
agent-browser set headers '{"X-Key":"v"}' # Extra HTTP headers
agent-browser set credentials user pass   # HTTP basic auth
agent-browser set media dark              # Emulate color scheme
```

### Cookies & Storage
```bash
agent-browser cookies                     # Get all cookies
agent-browser cookies set name value      # Set cookie
agent-browser cookies clear               # Clear cookies
agent-browser storage local               # Get all localStorage
agent-browser storage local key           # Get specific key
agent-browser storage local set k v       # Set value
agent-browser storage local clear         # Clear all
```

### Network
```bash
agent-browser network route <url>              # Intercept requests
agent-browser network route <url> --abort      # Block requests
agent-browser network route <url> --body '{}'  # Mock response
agent-browser network unroute [url]            # Remove routes
agent-browser network requests                 # View tracked requests
agent-browser network requests --filter api    # Filter requests
```

### Tabs & Windows
```bash
agent-browser tab                 # List tabs
agent-browser tab new [url]       # New tab
agent-browser tab 2               # Switch to tab
agent-browser tab close           # Close tab
agent-browser window new          # New window
```

### Frames
```bash
agent-browser frame "#iframe"     # Switch to iframe
agent-browser frame main          # Back to main frame
```

### Dialogs
```bash
agent-browser dialog accept [text]  # Accept dialog
agent-browser dialog dismiss        # Dismiss dialog
```

### JavaScript Evaluation
```bash
agent-browser eval "document.title"                      # Run JavaScript
agent-browser eval "document.querySelector('.btn').click()"  # Execute DOM operations
agent-browser eval "return window.location.href"         # Return values
agent-browser eval "JSON.stringify(odoo.session_info)"   # Get Odoo session data
agent-browser eval "document.querySelectorAll('.o_form_label').length"  # Count elements
```

#### Advanced JavaScript for Odoo Testing
```bash
# Check Odoo version and modules
agent-browser eval "odoo.session_info.server_version"
agent-browser eval "JSON.stringify(odoo.session_info.web_tours)"

# Wait for Odoo web client to be ready
agent-browser eval "typeof odoo !== 'undefined' && odoo.isReady"

# Trigger Odoo actions programmatically
agent-browser eval "document.querySelector('[name=\"action_confirm\"]').click()"

# Extract form field values
agent-browser eval "Array.from(document.querySelectorAll('.o_field_widget')).map(el => ({name: el.getAttribute('name'), value: el.textContent}))"

# Check for Odoo error notifications
agent-browser eval "document.querySelectorAll('.o_notification_manager .o_notification').length"

# Get current view type (form, list, kanban, etc.)
agent-browser eval "document.querySelector('.o_action_manager').dataset.viewType"
```

## Example: Form submission

```bash
agent-browser open https://example.com/form
agent-browser snapshot -i
# Output shows: textbox "Email" [ref=e1], textbox "Password" [ref=e2], button "Submit" [ref=e3]

agent-browser fill @e1 "user@example.com"
agent-browser fill @e2 "password123"
agent-browser click @e3
agent-browser wait --load networkidle
agent-browser snapshot -i  # Check result
```

## Odoo-Specific Testing Patterns

### 1. Odoo Website Testing (Public Pages)

**IMPORTANT: Always get Odoo port from config, NOT hardcoded!**
```bash
# Dynamic detection (recommended):
ODOO_PORT=$(grep "^xmlrpc_port" /path/to/17_workspace/config/odoo.conf.17 | awk '{print $NF}')
ODOO_URL="http://localhost:$ODOO_PORT"

# Verify it's running:
curl "$ODOO_URL/web/health" && echo "✅ Running" || echo "❌ Not running"
```

Website pages are publicly accessible and don't require authentication.

```bash
# Test homepage (using dynamic URL)
agent-browser open "$ODOO_URL/"
agent-browser screenshot homepage.png

# Test e-commerce
agent-browser open "$ODOO_URL/shop"
agent-browser snapshot -i
agent-browser screenshot shop_page.png

# Test contact page
agent-browser open "$ODOO_URL/contactus"
agent-browser screenshot contact_page.png
```

### 2. Odoo Backend Module Testing (Authenticated)

Backend modules require login via `/web` endpoint before accessing menu items.

```bash
# Get dynamic URL
ODOO_PORT=$(grep "^xmlrpc_port" /path/to/17_workspace/config/odoo.conf.17 | awk '{print $NF}')
ODOO_URL="http://localhost:$ODOO_PORT"

# Step 1: Navigate to login page
agent-browser open "$ODOO_URL/web"

# Step 2: Get interactive elements
agent-browser snapshot -i
# Output shows: textbox "Email" [ref=e14], textbox "Password" [ref=e16], button "Log in" [ref=e18]

# Step 3: Login with credentials
agent-browser fill @e14 "admin"
agent-browser fill @e16 "your_password"
agent-browser click @e18

# Step 4: Wait for dashboard to load
sleep 2  # More reliable than networkidle for Odoo

# Step 5: Check current URL
agent-browser get url  # Should show /odoo/* after login

# Step 6: Open app menu (hamburger icon)
agent-browser snapshot -i | head -20
agent-browser click @e1  # Usually the hamburger menu button

# Step 7: Find your module menu item
sleep 1
agent-browser snapshot -i | grep -i "your_module_name"
# Output shows: menuitem "Your Module" [ref=e29]

# Step 8: Navigate to module
agent-browser click @e29
sleep 2

# Step 9: Capture main dashboard
agent-browser screenshot static/description/01_main_menu.png

# Step 10: Navigate through submenu items
agent-browser snapshot -i | grep -i "submenu"
agent-browser click @e<N>  # Click submenu item
sleep 2
agent-browser screenshot static/description/02_submenu_view.png
```

### 3. Odoo Module Documentation Workflow

Complete workflow for creating module documentation with screenshots.

```bash
#!/bin/bash
# Step 0: Get dynamic Odoo URL from config
WORKSPACE_PATH="/path/to/17_workspace"
VERSION="17"
CONFIG_FILE="$WORKSPACE_PATH/config/odoo.conf.$VERSION"
ODOO_PORT=$(grep "^xmlrpc_port" "$CONFIG_FILE" | awk '{print $NF}')
ODOO_URL="http://localhost:$ODOO_PORT"

echo "📍 Using Odoo URL: $ODOO_URL"

# Step 1: Login to Odoo
agent-browser open "$ODOO_URL/web"
agent-browser snapshot -i
agent-browser fill @e14 "admin" && agent-browser fill @e16 "password" && agent-browser click @e18
sleep 2

# Step 2: Navigate to module
agent-browser click @e1  # Open app menu
sleep 1
agent-browser snapshot -i | grep -i "module_name"
agent-browser click @e<N>  # Click module
sleep 2

# Step 3: Capture screenshots of key features
agent-browser screenshot static/description/01_main_dashboard.png

# Step 4: Navigate to list view
agent-browser snapshot -i | grep -i "menu_item"
agent-browser click @e<N>
sleep 2
agent-browser screenshot static/description/02_list_view.png

# Step 5: Create new record
agent-browser snapshot -i | grep -i "new"
agent-browser click @e<N>  # New button
sleep 2
agent-browser screenshot static/description/03_create_form.png

# Navigate to settings
agent-browser snapshot -i | grep -i "configuration\|settings"
agent-browser click @e<N>
sleep 2
agent-browser screenshot static/description/04_settings.png

# Close browser
agent-browser close
```

### 4. Odoo OWL Framework Testing (Odoo 19)

Odoo 19 uses the OWL (Odoo Web Library) framework for JavaScript components. Always check console for errors.

```bash
# After navigating to any page
agent-browser console  # View all console messages
agent-browser errors   # View only errors

# Check for OWL-specific debug info
agent-browser eval "console.log(odoo.__DEBUG__)"
agent-browser eval "console.log(Object.keys(odoo))"

# Check OWL component registry
agent-browser eval "console.log(odoo.__WOWL_DEBUG__)"

# Monitor for common OWL errors:
# - Component not found
# - Missing props
# - Mount/unmount errors
# - Lifecycle hook failures

# Clear console before navigating to new page
agent-browser console --clear
agent-browser click @e<N>  # Navigate
sleep 2
agent-browser console  # Check new page console
```

### 5. Common Odoo Testing Patterns

#### Pattern: Test Menu Navigation
```bash
# After login, test all menu items
agent-browser click @e1  # Open app menu
sleep 1

# Get all menu items
agent-browser snapshot -i > menu_items.txt
cat menu_items.txt | grep "menuitem"

# Click each menu item and verify
for ref in e3 e5 e6 e7; do
  agent-browser click @$ref
  sleep 2
  agent-browser get url
  agent-browser errors  # Check for errors
done
```

#### Pattern: Test Form Submission
```bash
# Navigate to create form
agent-browser click @e12  # New button
sleep 2

# Fill form fields
agent-browser snapshot -i | grep -i "textbox\|checkbox\|select"
agent-browser fill @e<N> "Test Value"
agent-browser click @e<M>  # Checkbox
agent-browser select @e<X> "option_value"

# Save form
agent-browser snapshot -i | grep -i "save"
agent-browser click @e<Y>  # Save button
sleep 2

# Verify success
agent-browser get url  # Should change to view mode
agent-browser snapshot -i | grep -i "edit"  # Edit button should be visible
```

#### Pattern: Test Search and Filters
```bash
# In list view
agent-browser snapshot -i | grep -i "search"
agent-browser click @e14  # Search button

# Type search query
agent-browser fill @e17 "search term"
agent-browser press Enter
sleep 2

# Capture filtered results
agent-browser screenshot search_results.png

# Clear search
agent-browser click @e16  # Remove filter
sleep 1
```

### 8. XML and Dynamic Content Handling

#### Handling XML Views (Odoo Form/Tree Views)
Odoo heavily uses XML to define views that are dynamically rendered to HTML.

```bash
# Wait for dynamic content to load
agent-browser open http://localhost:8090/web#model=res.partner
sleep 3  # Allow time for XML rendering

# Check if view is fully rendered
agent-browser eval "document.querySelector('.o_form_view') !== null"
agent-browser eval "document.readyState === 'complete'"

# Wait for specific Odoo components
agent-browser wait --fn "document.querySelector('.o_content').children.length > 0"

# Handle dynamically loaded list items
agent-browser snapshot -i | grep "row"
agent-browser click @e12  # Click first row
sleep 2
agent-browser snapshot -i  # Re-snapshot to get form elements
```

#### Async Content Loading Patterns
```bash
# Pattern 1: Wait for AJAX requests to complete
agent-browser click @e<N>  # Trigger action
agent-browser wait --load networkidle  # Wait for network activity
agent-browser snapshot -i

# Pattern 2: Wait for specific element to appear
agent-browser click @e<N>
agent-browser wait --text "Loading complete"
agent-browser snapshot -i

# Pattern 3: Poll for element with JavaScript
agent-browser eval "new Promise(r => {let i = setInterval(() => {if(document.querySelector('.o_form_view')){clearInterval(i);r(true)}}, 100)})"

# Pattern 4: Wait for Odoo's internal state
agent-browser eval "return new Promise(resolve => {
  const check = () => {
    if (odoo.__WOWL_DEBUG__?.root?.el) {
      resolve(true);
    } else {
      setTimeout(check, 100);
    }
  };
  check();
})"
```

#### Handling Odoo Dialogs and Wizards
```bash
# Open a wizard/dialog
agent-browser click @e<N>  # Button that opens dialog
sleep 1

# Wait for modal to appear
agent-browser wait --fn "document.querySelector('.modal') !== null"
agent-browser snapshot -i

# Interact with dialog elements
agent-browser snapshot -i | grep "modal\|dialog"
agent-browser fill @e<N> "value"
agent-browser click @e<M>  # Confirm button

# Handle dialog acceptance
agent-browser dialog accept "confirm text"
```

#### Testing XML-defined Many2one/Many2many Fields
```bash
# Click Many2one dropdown
agent-browser snapshot -i | grep -i "many2one\|dropdown"
agent-browser click @e<N>
sleep 1

# Wait for dropdown options to load
agent-browser snapshot -i | grep -i "option\|item"
agent-browser click @e<M>  # Select option

# For Many2many with search
agent-browser click @e<N>  # Open Many2many field
agent-browser fill @e<X> "search term"  # Type to search
sleep 1
agent-browser click @e<Y>  # Select from results
```

### 9. Automated Test Templates

#### Template 1: Module Installation Verification
```bash
#!/bin/bash
# Verify module is installed and accessible

MODULE_NAME="your_module"
ODOO_URL="http://localhost:8090"
ADMIN_USER="admin"
ADMIN_PASS="password"

# Login
agent-browser open ${ODOO_URL}/web
agent-browser snapshot -i
agent-browser fill @e14 "$ADMIN_USER"
agent-browser fill @e16 "$ADMIN_PASS"
agent-browser click @e18
sleep 2

# Verify successful login
URL=$(agent-browser get url)
if [[ $URL != *"/odoo"* ]]; then
  echo "❌ Login failed"
  exit 1
fi
echo "✅ Login successful"

# Open apps menu
agent-browser click @e1
sleep 1

# Search for module
agent-browser snapshot -i > menu.txt
if grep -qi "$MODULE_NAME" menu.txt; then
  echo "✅ Module found in menu"
else
  echo "❌ Module not found"
  exit 1
fi

# Cleanup
rm -f menu.txt
agent-browser close
```

#### Template 2: Form CRUD Operations Test
```bash
#!/bin/bash
# Test Create, Read, Update, Delete operations

RECORD_NAME="Test Record $(date +%s)"

# Navigate to module and create new record
agent-browser click @e<menu_ref>  # Module menu item
sleep 2
agent-browser click @e<new_button>  # New button
sleep 2

# Fill form fields
agent-browser fill @e<name_field> "$RECORD_NAME"
agent-browser fill @e<other_field> "test value"
agent-browser click @e<save_button>
sleep 2

# Verify creation
agent-browser get url | grep -q "id=" && echo "✅ Record created"

# Edit record
agent-browser click @e<edit_button>
sleep 1
agent-browser fill @e<name_field> "${RECORD_NAME} (Updated)"
agent-browser click @e<save_button>
sleep 2
echo "✅ Record updated"

# Delete record
agent-browser click @e<action_button>
sleep 1
agent-browser snapshot -i | grep -i "delete"
agent-browser click @e<delete_option>
agent-browser dialog accept
sleep 2
echo "✅ Record deleted"

agent-browser close
```

#### Template 3: Multi-page Documentation Generator
```bash
#!/bin/bash
# Generate complete documentation screenshots for a module

MODULE_NAME="your_module"
OUTPUT_DIR="static/description"
PAGES=(
  "dashboard:Main Dashboard"
  "list:List View"
  "form:Form View"
  "settings:Configuration"
  "reports:Reports"
)

mkdir -p "$OUTPUT_DIR"

# Login
agent-browser open http://localhost:8090/web
agent-browser snapshot -i
agent-browser fill @e14 "admin"
agent-browser fill @e16 "password"
agent-browser click @e18
sleep 2

# Navigate to module
agent-browser click @e1  # App menu
sleep 1
agent-browser snapshot -i | grep -i "$MODULE_NAME"
agent-browser click @e<module_ref>
sleep 2

# Capture each page
counter=1
for page in "${PAGES[@]}"; do
  page_id="${page%%:*}"
  page_name="${page##*:}"
  
  echo "Capturing: $page_name"
  
  # Navigate to page
  agent-browser snapshot -i | grep -i "$page_id"
  agent-browser click @e<page_ref>
  sleep 2
  
  # Take screenshot
  filename=$(printf "%02d_%s.png" $counter "${page_id}")
  agent-browser screenshot "$OUTPUT_DIR/$filename"
  echo "✅ Saved: $filename"
  
  ((counter++))
done

agent-browser close
echo "📸 Documentation complete! Check $OUTPUT_DIR/"
```

#### Template 4: Performance and Load Testing
```bash
#!/bin/bash
# Test module performance under load

MODULE_URL="http://localhost:8090/web#model=your.model"
ITERATIONS=10

echo "🚀 Starting performance test..."

for i in $(seq 1 $ITERATIONS); do
  start_time=$(date +%s%N)
  
  agent-browser open "$MODULE_URL"
  agent-browser wait --load networkidle
  
  end_time=$(date +%s%N)
  elapsed=$((($end_time - $start_time) / 1000000))
  
  echo "Iteration $i: ${elapsed}ms"
  
  # Check for errors
  errors=$(agent-browser errors | wc -l)
  if [ $errors -gt 0 ]; then
    echo "⚠️  Errors detected in iteration $i"
  fi
done

agent-browser close
echo "✅ Performance test complete"
```

### 10. Enhanced Troubleshooting Guide

#### Network Timeout Issues
```bash
# If agent-browser wait --load networkidle fails:
# Use fixed sleep instead
sleep 2  # Wait 2 seconds
sleep 3  # Wait 3 seconds for slower pages

# Or check readiness with JavaScript
agent-browser eval "document.readyState"
```

#### Element Not Found
```bash
# Always re-snapshot after dynamic content loads
agent-browser click @e<N>
sleep 2  # Wait for content
agent-browser snapshot -i  # Get fresh elements
```

#### Menu Not Visible
```bash
# Ensure app menu is opened first
agent-browser snapshot -i | head -20 | grep "button"
agent-browser click @e1  # Usually first button (hamburger menu)
sleep 1
agent-browser snapshot -i | grep -i "menu_name"
```

#### Login Verification
```bash
# After login, verify authentication
agent-browser get url  # Should redirect from /web/login
# Successful: http://localhost:8090/odoo/*
# Failed: http://localhost:8090/web/login*

# Check for error messages
agent-browser snapshot -i | grep -i "error\|invalid"
```

#### Common Issues and Solutions

**Issue: "Odoo form fields not responding"**
```bash
# Problem: Odoo uses custom widgets
# Solution: Use focus + type instead of fill
agent-browser focus @e<field>
sleep 0.5
agent-browser type @e<field> "value"
agent-browser press Tab  # Trigger onchange
```

**Issue: "Can't interact with Many2one dropdown"**
```bash
# Problem: Odoo's Many2one uses autocomplete
# Solution: Click field, wait, type to search
agent-browser click @e<many2one_field>
sleep 0.5
agent-browser type @e<many2one_field> "search term"
sleep 1
agent-browser snapshot -i | grep -i "dropdown\|autocomplete"
agent-browser click @e<dropdown_option>
```

**Issue: "Modal/Dialog not detected"**
```bash
# Problem: Dialog rendered outside main viewport
# Solution: Wait for modal class specifically
agent-browser wait --fn "document.querySelector('.modal.show') !== null"
agent-browser snapshot -i | grep -i "modal"
```

**Issue: "OWL component errors in console"**
```bash
# Problem: Odoo 19 component lifecycle issues
# Solution: Check component mounting
agent-browser console --clear
agent-browser click @e<action>
sleep 2
agent-browser console | grep -i "owl\|component"

# Verify component mounted
agent-browser eval "document.querySelector('[data-owl-component]') !== null"
```

#### Debug Workflow Checklist

When a test fails, follow this checklist:

```bash
# 1. Check current URL
agent-browser get url

# 2. Check for JavaScript errors
agent-browser errors
agent-browser console | tail -20

# 3. Get page title (verify correct page)
agent-browser get title

# 4. Take debug screenshot
agent-browser screenshot debug_$(date +%s).png

# 5. Check network requests
agent-browser network requests | tail -10

# 6. Verify Odoo session
agent-browser eval "JSON.stringify(odoo.session_info)" | jq '.'

# 7. Check for notifications/warnings
agent-browser snapshot -i | grep -i "notification\|warning\|error"
```

### 11. Integration with CI/CD Pipelines

```bash
#!/bin/bash
# ci-test.sh - Run browser tests in CI/CD

set -e

export HEADLESS=true
export SCREENSHOTS_DIR="test_results/screenshots"
mkdir -p "$SCREENSHOTS_DIR"

# Run test suite
./test_login.sh
./test_module_navigation.sh
./test_form_operations.sh

# Generate report
echo "Test Results: $(date)" > test_results/report.txt
echo "✅ All tests passed" >> test_results/report.txt
```

### 7. Screenshot Best Practices for Odoo Modules

```bash
# Use consistent naming with numbering
01_main_menu.png          # Dashboard/main view
02_list_view.png          # List of records
03_form_view.png          # Single record form
04_create_form.png        # Create new record
05_kanban_view.png        # Kanban view
06_settings.png           # Configuration page
07_reports.png            # Reports/analytics
08_wizard.png             # Wizard/popup

# Capture at appropriate viewport
agent-browser set viewport 1920 1080  # Desktop
# or
agent-browser set viewport 1366 768   # Laptop
# or
agent-browser set device "iPhone 14"  # Mobile

# Full page screenshots for documentation
agent-browser screenshot --full static/description/full_page.png

# Element-specific screenshots
agent-browser screenshot @e<N> static/description/element.png
```

## Example: Authentication with saved state

```bash
# Login once
agent-browser open https://app.example.com/login
agent-browser snapshot -i
agent-browser fill @e1 "username"
agent-browser fill @e2 "password"
agent-browser click @e3
agent-browser wait --url "**/dashboard"
agent-browser state save auth.json

# Later sessions: load saved state
agent-browser state load auth.json
agent-browser open https://app.example.com/dashboard
```

## Sessions (parallel browsers)

```bash
agent-browser --session test1 open site-a.com
agent-browser --session test2 open site-b.com
agent-browser session list
```

## JSON output (for parsing)

Add `--json` for machine-readable output:
```bash
agent-browser snapshot -i --json
agent-browser get text @e1 --json
```

## Debugging

```bash
agent-browser open example.com --headed              # Show browser window
agent-browser console                                # View console messages
agent-browser errors                                 # View page errors
agent-browser record start ./debug.webm   # Record from current page
agent-browser record stop                            # Save recording
agent-browser open example.com --headed  # Show browser window
agent-browser --cdp 9222 snapshot        # Connect via CDP
agent-browser console                    # View console messages
agent-browser console --clear            # Clear console
agent-browser errors                     # View page errors
agent-browser errors --clear             # Clear errors
agent-browser highlight @e1              # Highlight element
agent-browser trace start                # Start recording trace
agent-browser trace stop trace.zip       # Stop and save trace
```

---

## 📂 Level 3: References & External Resources

### Official Documentation
- **Playwright Browser API**: https://playwright.dev/docs/api/class-browser
- **Playwright Selectors**: https://playwright.dev/docs/selectors
- **Accessibility Tree**: https://playwright.dev/docs/accessibility-testing

### Odoo-Specific Resources
- **Odoo Web Client Architecture**: https://github.com/odoo/odoo/tree/19.0/addons/web/static/src
- **OWL Framework (Odoo 19)**: https://github.com/odoo/owl
- **Odoo Testing Guide**: https://www.odoo.com/documentation/19.0/developer/reference/backend/testing.html
- **Odoo Views XML Reference**: https://github.com/odoo/odoo/blob/19.0/odoo/import_xml.rng

### Related Skills
- `Odoo_Custom_Frontend_Testing` - Odoo-specific frontend test patterns
- `Odoo_Module_Documentation_Screenshot` - Module screenshot guidelines
- `Odoo19_Tools` / `Odoo18_Tools` / `Odoo17_Tools` - Version-specific dev tools

### Configuration Files
- `.env` - Environment configuration with Odoo URLs and credentials
- `odoo.conf` - Odoo server configuration for test environments
- `manage_modules.sh` - Module management script integration

### Best Practices
1. **Always re-snapshot** after DOM changes (clicks, navigation)
2. **Use fixed sleep** for Odoo (avoid networkidle due to websockets)
3. **Wait 2-3 seconds** after major actions (save, navigation)
4. **Clear console** before testing to isolate errors
5. **Take screenshots** at key validation points
6. **Use semantic selectors** when refs are unstable
7. **Test in headed mode** first to debug interactions

### Performance Tips
- Use `snapshot -c` for compact output
- Limit depth with `snapshot -d 2`
- Scope snapshots with `-s "#content"`
- Batch similar operations
- Use `--json` for programmatic parsing
```
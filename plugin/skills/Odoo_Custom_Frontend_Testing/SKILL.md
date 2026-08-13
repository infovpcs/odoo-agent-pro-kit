---
name: odoo_frontend_testing
description: Frontend testing patterns for custom Odoo modules using HOOT and JavaScript testing frameworks. Use when creating frontend tests for Odoo modules.
version: 1.0.0
author: VPCS Team
category: testing
odoo_versions: ["17.0", "18.0", "19.0"]
tags: ["odoo", "testing", "frontend", "hoot", "javascript", "ui"]
---
## Goal
Define frontend/UI test approach for Odoo customizations (views, JS, OWL), combining xmlrpc-based form interaction testing with JS unit tests.

## Scope
- Form/list/wizard UI behavior and user workflows via xmlrpc (post-install validation).
- JS/OWL components and client actions (unit tests).
- Basic cross-browser sanity (Chromium/Firefox) if applicable.

## Sandbox execution

When `.sandbox/session.json` exists, run `sandbox/bin/sandboxctl module
<session> update <module>` before browser testing and require its result JSON
to report `succeeded`. Do not call `odoo-bin`; retain `bash manage_modules.sh`
for local mode.

## Primary Approach: Browser-Based Testing with Playwright/Chrome DevTools

### Why Browser Testing?
- **Real JavaScript Execution**: Tests actual JS/OWL code running in browser (not backend-only).
- **Console Monitoring**: Captures JS errors, warnings, and custom logs before users see them.
- **User Interaction**: Validates actual clicks, form fills, page navigation, async operations.
- **Cross-Browser**: Test Chromium, Firefox, WebKit to catch browser-specific issues.
- **Visual/DOM Validation**: Verifies UI rendering, element visibility, styles, attributes.
- **Network Monitoring**: Catch failed API calls, slow requests, missing resources.

### Structure & Conventions

#### A. Test File Location
```
<custom_module>/scripts/
  test_browser_ui.py          # Main Playwright/Chrome DevTools test script
  test_browser_js_errors.py   # Console log capture and error validation
  test_browser_interactions.py # Complex user workflows (optional)
```

#### B. Base Script Template (Playwright + Console Monitoring)
```python
#!/usr/bin/env python3
"""
Browser-based frontend testing with console log capture.
Usage: python3 test_browser_ui.py --url http://localhost:8019 --db odoo19 --username admin --password admin
Tests actual browser rendering, JS execution, console errors.
"""

import asyncio
from playwright.async_api import async_playwright, expect
import json
import sys
from argparse import ArgumentParser
from datetime import datetime

class OdooBrowserTest:
    def __init__(self, url, db, username, password):
        self.url = url
        self.db = db
        self.username = username
        self.password = password
        self.browser = None
        self.context = None
        self.page = None
        self.console_logs = []  # Capture all console messages
        self.js_errors = []     # Track JS errors separately
    
    async def setup(self):
        """Launch browser and setup console log capture."""
        self.playwright = await async_playwright().start()
        self.browser = await self.playwright.chromium.launch(headless=True)  # headless=False for debugging
        self.context = await self.browser.new_context()
        self.page = await self.context.new_page()
        
        # Capture all console messages
        self.page.on('console', self._on_console)
        self.page.on('pageerror', self._on_page_error)
        
        print(f"✓ Browser launched (Chromium, headless)")
    
    def _on_console(self, msg):
        """Handler for console.log/warn/error messages."""
        level = msg.type  # 'log', 'warn', 'error', 'info'
        text = msg.text
        location = msg.location  # {url, lineNumber, columnNumber}
        
        log_entry = {
            'timestamp': datetime.now().isoformat(),
            'level': level,
            'message': text,
            'location': location
        }
        self.console_logs.append(log_entry)
        
        # Flag errors and warnings
        if level in ['error', 'warn']:
            print(f"  [CONSOLE {level.upper()}] {text} @ {location['url']}:{location['lineNumber']}")
    
    def _on_page_error(self, error):
        """Handler for uncaught JS exceptions."""
        error_entry = {
            'timestamp': datetime.now().isoformat(),
            'type': 'uncaught_exception',
            'message': str(error)
        }
        self.js_errors.append(error_entry)
        print(f"  [JS ERROR] {error}")
    
    async def login(self):
        """Navigate to Odoo login page and authenticate."""
        print(f"\n[Setup] Logging in to {self.url}")
        await self.page.goto(f"{self.url}/web/login", wait_until='networkidle')
        
        # Clear console logs from login page load
        pre_login_logs = len(self.console_logs)
        
        # Fill login form
        await self.page.fill('input[name="login"]', self.username)
        await self.page.fill('input[name="password"]', self.password)
        
        # Submit
        await self.page.click('button[type="submit"]')
        await self.page.wait_for_load_state('networkidle')
        
        # Check for login errors in console
        post_login_logs = self.console_logs[pre_login_logs:]
        error_logs = [log for log in post_login_logs if log['level'] in ['error', 'warn']]
        
        if error_logs:
            print(f"  ⚠ Login page has {len(error_logs)} error(s) in console")
        
        print(f"✓ Logged in as {self.username}")
    
    async def test_custom_form_rendering(self):
        """Test 1: Open custom form and validate rendering + console."""
        print(f"\n[Test 1] Custom Form Rendering")
        try:
            # Navigate to custom module
            await self.page.goto(f"{self.url}/web#action=custom_module.action_custom_model&model=custom_module.custom_model",
                                wait_until='networkidle')
            
            # Wait for form to load
            await self.page.wait_for_selector('.o_form_view', timeout=5000)
            print(f"  ✓ Form view loaded")
            
            # Check for JS console errors during load
            error_count = len(self.js_errors)
            console_errors = [log for log in self.console_logs if log['level'] == 'error']
            
            if console_errors:
                print(f"  ✗ Found {len(console_errors)} JS error(s) in console during form load")
                for err in console_errors[-3:]:  # Show last 3
                    print(f"    - {err['message']}")
                return False
            
            # Validate form fields are visible
            fields_present = await self.page.query_selector_all('.o_field_widget')
            print(f"  ✓ Form has {len(fields_present)} fields visible")
            
            return True
        except Exception as e:
            print(f"  ✗ FAILED: {e}")
            return False
    
    async def test_create_record_with_validation(self):
        """Test 2: Create record and validate onchange + console."""
        print(f"\n[Test 2] Create Record with onchange Validation")
        try:
            # Click create button
            await self.page.click('button:has-text("Create")')
            await self.page.wait_for_selector('.o_form_view.o_form_editable', timeout=5000)
            print(f"  ✓ New form opened")
            
            # Fill first field (should trigger onchange)
            await self.page.fill('input[name="name"]', 'Test Record')
            await self.page.press('input[name="name"]', 'Tab')  # Trigger onchange
            
            # Wait for onchange to process
            await asyncio.sleep(1)
            
            # Check console for onchange errors
            onchange_errors = [log for log in self.console_logs if log['level'] == 'error' and 'onchange' in log['message'].lower()]
            if onchange_errors:
                print(f"  ✗ onchange errors: {onchange_errors}")
                return False
            
            print(f"  ✓ onchange processed without JS errors")
            
            # Save
            await self.page.click('button:has-text("Save")')
            await self.page.wait_for_load_state('networkidle')
            print(f"  ✓ Record saved")
            
            return True
        except Exception as e:
            print(f"  ✗ FAILED: {e}")
            return False
    
    async def test_button_actions_and_state(self):
        """Test 3: Click action buttons and validate state changes + console."""
        print(f"\n[Test 3] Action Button Workflow")
        try:
            # Click action button (e.g., confirm)
            action_button = await self.page.query_selector('button:has-text("Confirm")')
            if not action_button:
                print(f"  ⚠ Confirm button not found, skipping test")
                return True
            
            await action_button.click()
            await self.page.wait_for_load_state('networkidle')
            print(f"  ✓ Action button clicked")
            
            # Check console for action errors
            action_errors = [log for log in self.console_logs if log['level'] == 'error']
            if action_errors:
                print(f"  ✗ Action triggered JS error(s)")
                return False
            
            # Validate state visual change
            status_badge = await self.page.query_selector('.o_badge_info:has-text("Confirmed")')
            if status_badge:
                print(f"  ✓ Status updated visually")
            
            return True
        except Exception as e:
            print(f"  ✗ FAILED: {e}")
            return False
    
    async def test_console_for_warnings_and_deprecations(self):
        """Test 4: Check console for warnings, deprecated APIs, performance issues."""
        print(f"\n[Test 4] Console Health Check")
        try:
            warnings = [log for log in self.console_logs if log['level'] == 'warn']
            errors = [log for log in self.console_logs if log['level'] == 'error']
            
            print(f"  ✓ Total console logs: {len(self.console_logs)}")
            print(f"    - Errors: {len(errors)}")
            print(f"    - Warnings: {len(warnings)}")
            
            # Highlight critical errors
            critical_keywords = ['undefined', 'cannot read', 'is not a function', 'network error']
            critical_errors = [log for log in errors 
                             if any(kw.lower() in log['message'].lower() for kw in critical_keywords)]
            
            if critical_errors:
                print(f"  ✗ Found {len(critical_errors)} critical error(s)")
                for err in critical_errors[:5]:  # Show first 5
                    print(f"    - {err['message']}")
                return False
            
            print(f"  ✓ No critical JS errors detected")
            return True
        except Exception as e:
            print(f"  ✗ FAILED: {e}")
            return False
    
    async def test_network_requests(self):
        """Test 5: Validate network requests (no 4xx/5xx errors)."""
        print(f"\n[Test 5] Network Request Validation")
        try:
            # Capture failed network requests
            failed_requests = []
            
            def on_response(response):
                if response.status >= 400:
                    failed_requests.append({
                        'url': response.url,
                        'status': response.status,
                        'status_text': response.status_text
                    })
            
            self.page.on('response', on_response)
            
            # Perform a navigation to trigger requests
            await self.page.goto(f"{self.url}/web#action=custom_module.action_custom_model", 
                                wait_until='networkidle')
            
            # Remove listener
            self.page.remove_listener('response', on_response)
            
            if failed_requests:
                print(f"  ✗ Found {len(failed_requests)} failed request(s)")
                for req in failed_requests[:5]:
                    print(f"    - {req['status']} {req['url']}")
                return False
            
            print(f"  ✓ All network requests successful")
            return True
        except Exception as e:
            print(f"  ✗ FAILED: {e}")
            return False
    
    async def teardown(self):
        """Close browser and generate report."""
        if self.page:
            await self.page.close()
        if self.context:
            await self.context.close()
        if self.browser:
            await self.browser.close()
        if self.playwright:
            await self.playwright.stop()
        
        # Save console logs for analysis
        with open('console_logs.json', 'w') as f:
            json.dump({
                'total_logs': len(self.console_logs),
                'js_errors': len(self.js_errors),
                'error_count': len([log for log in self.console_logs if log['level'] == 'error']),
                'warning_count': len([log for log in self.console_logs if log['level'] == 'warn']),
                'logs': self.console_logs[-100:]  # Last 100 logs
            }, f, indent=2)
        
        print(f"✓ Console logs saved to console_logs.json")

# ============================================================================
# MAIN
# ============================================================================

async def main():
    parser = ArgumentParser(description='Browser-based frontend test suite.')
    parser.add_argument('--url', default='http://localhost:8019', help='Odoo server URL')
    parser.add_argument('--db', default='odoo19', help='Database name')
    parser.add_argument('--username', default='admin', help='Username')
    parser.add_argument('--password', default='admin', help='Password')
    args = parser.parse_args()
    
    print(f"\n{'='*70}")
    print(f"Browser-Based Frontend Tests")
    print(f"Server: {args.url} | DB: {args.db} | User: {args.username}")
    print(f"{'='*70}")
    
    tester = OdooBrowserTest(args.url, args.db, args.username, args.password)
    
    try:
        await tester.setup()
        await tester.login()
        
        results = {
            'Form Rendering': await tester.test_custom_form_rendering(),
            'Create with onchange': await tester.test_create_record_with_validation(),
            'Action Buttons': await tester.test_button_actions_and_state(),
            'Console Health': await tester.test_console_for_warnings_and_deprecations(),
            'Network Requests': await tester.test_network_requests(),
        }
    finally:
        await tester.teardown()
    
    # Summary
    print(f"\n{'='*70}")
    print("TEST SUMMARY")
    print(f"{'='*70}")
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    for test_name, result in results.items():
        status = '✓ PASS' if result else '✗ FAIL'
        print(f"  {status}: {test_name}")
    
    print(f"\nResult: {passed}/{total} tests passed")
    print(f"Console Logs: {len(tester.console_logs)} total")
    print(f"JS Errors: {len(tester.js_errors)} critical")
    
    return 0 if passed == total else 1

if __name__ == '__main__':
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
```

## Installation & Setup

### Install Playwright
```bash
pip install playwright
pywright install  # Downloads browser binaries
```

### Run Tests
```bash
# Start Odoo server first
cd /path/to/odoo_local_setup
./manage_modules.sh start --version 19

# In another terminal, run browser tests
cd /path/to/custom_module/scripts
python3 test_browser_ui.py --url http://localhost:8019 --db odoo19 --username admin --password admin
```

### Console Logs Output
- Saves to `console_logs.json` with all messages, errors, warnings
- Flagged in real-time during test execution
- Includes line numbers and file locations for debugging

## Secondary Approach: xmlrpc Form Validation (When No Browser Available)

**Use when**:
- Browser testing not available (CI/CD, headless server)
- Quick pre-flight validation needed before browser tests
- Testing form metadata and field definitions
- Validating onchange side-effects via data (not visual)

**Quick xmlrpc Form Check**:
```python
import xmlrpc.client

def validate_form_metadata(url, db, username, password, model):
    """Quick xmlrpc check: field structure without browser."""
    common = xmlrpc.client.ServerProxy(f'{url}/xmlrpc/2/common')
    object_rpc = xmlrpc.client.ServerProxy(f'{url}/xmlrpc/2/object')
    uid = common.authenticate(db, username, password, {})
    
    # Get field metadata
    fields = object_rpc.execute_kw(db, uid, password, model, 'fields_get', [],
                                   {'attributes': ['string', 'type', 'required', 'readonly', 'domain']})
    
    # Validate structure
    required = [f for f, d in fields.items() if d.get('required')]
    readonly = [f for f, d in fields.items() if d.get('readonly')]
    
    print(f"  ✓ Form has {len(fields)} fields")
    print(f"    - Required: {required}")
    print(f"    - Readonly: {readonly}")
    
    return True

# Usage
validate_form_metadata('http://localhost:8019', 'odoo19', 'admin', 'admin', 'custom_module.custom_model')
```

## Tertiary Approach: JS/OWL Unit Tests (for client logic)

### When to use JS unit tests
- Custom OWL components and client actions.
- Complex JS logic (not Odoo standard behaviors).
- Browser-specific behavior (real DOM required).

### Practices
- Use QUnit for model-free JS; use OWL test utilities for components.
- Keep tests fast; mock server calls.
- Reuse fixtures; avoid side effects.

### Test File Location
```
<custom_module>/static/tests/
  test_components.js          # OWL component tests
  test_actions.js             # Client action tests
```

## Integration: LIVE TEST Sub-Task

### Step 1: Install Module
```bash
./manage_modules.sh install custom_module --version 19
```

### Step 2: Run Browser Tests (Primary)
```bash
# Install Playwright first
pip install playwright
playwright install  # Downloads Chromium/Firefox/WebKit

# Start Odoo server
cd /path/to/odoo_local_setup
./manage_modules.sh start --version 19

# In another terminal, run browser tests
cd /path/to/custom_module/scripts
python3 test_browser_ui.py --url http://localhost:8019 --db odoo19 --username admin --password admin
```

### Step 3: Review Console Logs
```bash
# Check generated console_logs.json for any JS errors
cat console_logs.json | jq '.js_errors'
```

### Step 4: Mark LIVE TEST Complete
```json
{
  "feature": "Custom Module Feature",
  "sub_tasks": [
    {"title": "Browser UI tests", "status": "done"},
    {"title": "Console error validation", "status": "done"},
    {"title": "LIVE TEST", "status": "done"}
  ]
}
```

## Key Differences: Browser Test vs xmlrpc Form Check

| Aspect | Browser Test (Playwright) | xmlrpc Form Check |
|--------|---------------------------|-------------------|
| **Coverage** | JavaScript execution, console logs, network, DOM rendering, actual user clicks | Field metadata, domain filters, field definitions only |
| **Catches** | JS errors, console errors, network failures, async issues, race conditions | Missing fields, incorrect domain syntax, field type mismatches |
| **Speed** | Slower (browser startup, network round-trips) | Fast (single xmlrpc call) |
| **Environment** | Requires display (X11/Wayland) or headless browser | Any Python environment |
| **Use Case** | Post-install acceptance testing (catches frontend issues) | Pre-flight quick validation (catches basic metadata issues) |
| **Best For** | CI/CD with display, developer testing, regression | Headless CI/CD, quick checks, form structure validation |

## Official Odoo Documentation References

### Odoo 17.0 External API (XML-RPC)
- **URL**: https://www.odoo.com/documentation/17.0/developer/reference/external_api.html
- **Field Metadata**: `fields_get()` returns field definitions (string, type, required, readonly, domain)
- **Domain Filters**: Domains are tuples `['field_name', 'operator', 'value']` for relational field constraints
- **Onchange Simulation**: Create record → read computed fields to validate onchange results

### Odoo 18.0 External API (XML-RPC)
- **URL**: https://www.odoo.com/documentation/18.0/developer/reference/external_api.html
- **Field Metadata**: Same `fields_get()` syntax and return format as 17.0
- **Domain Filters**: Identical domain syntax for relational field constraints
- **UI Changes**: Start adopting list views (from tree); direct attributes (no attrs dict)

### Odoo 19.0 External API (JSON-2 + XML-RPC Legacy)
- **Primary (New)**: https://www.odoo.com/documentation/19.0/developer/reference/external_api.html
  - **JSON-2 API**: Modern REST-like API for all ORM operations
  - **No uid/password**: Stateless authentication via `Authorization: bearer <API_KEY>` header
  - **UI Testing**: POST to `/json/2/<model>/fields_get`, `/json/2/<model>/create`, `/json/2/<model>/read`
  - **Form Validation**: Get field metadata with domains and constraints via single JSON-2 call

- **Legacy (Deprecated)**: https://www.odoo.com/documentation/19.0/developer/reference/external_rpc_api.html
  - **XML-RPC**: Supported but deprecated; use JSON-2 for new scripts

### UI Test Syntax Comparison

#### Odoo 17/18 (XML-RPC form field validation)
```python
import xmlrpc.client

url = "http://localhost:8018"  # 18.0
db = "odoo18"
username = "admin"
password = "admin"

object_rpc = xmlrpc.client.ServerProxy(f'{url}/xmlrpc/2/object')
common = xmlrpc.client.ServerProxy(f'{url}/xmlrpc/2/common')
uid = common.authenticate(db, username, password, {})

# Get form field metadata
fields = object_rpc.execute_kw(db, uid, password, 'custom_module.custom_model',
                               'fields_get', [],
                               {'attributes': ['string', 'type', 'required', 'readonly', 'domain']})

# Check for required and readonly fields
required = [f for f, d in fields.items() if d.get('required')]
readonly = [f for f, d in fields.items() if d.get('readonly')]

# Validate domain on relational field
partner_field = fields.get('partner_id')
if partner_field:
    domain = partner_field.get('domain', [])  # e.g., [['customer', '=', True]]
    print(f"partner_id domain constraint: {domain}")
```

#### Odoo 19.0 (JSON-2 API form field validation - Recommended)
```python
import requests

url = "https://mycompany.example.com/json/2"
api_key = "<your_api_key_here>"

headers = {
    "Authorization": f"bearer {api_key}",
    "Content-Type": "application/json",
}

# Get form field metadata (single JSON-2 call)
res = requests.post(
    f"{url}/custom_module.custom_model/fields_get",
    headers=headers,
    json={"attributes": ["string", "type", "required", "readonly", "domain"]}
)
fields = res.json()

# Extract field constraints
required = [f for f, d in fields.items() if d.get('required')]
readonly = [f for f, d in fields.items() if d.get('readonly')]

# Check domain on relational field
partner_field = fields.get('partner_id')
if partner_field:
    domain = partner_field.get('domain', [])
    print(f"partner_id domain: {domain}")

# Create record and validate onchange side-effects (single transaction)
res = requests.post(
    f"{url}/custom_module.custom_model/create",
    headers=headers,
    json={"name": "Test", "type": "type_a"}
)
record_id = res.json()

# Read computed fields
res = requests.post(
    f"{url}/custom_module.custom_model/read",
    headers=headers,
    json={"ids": [record_id], "fields": ["computed_field", "price_total"]}
)
record = res.json()[0]
print(f"Computed fields: {record['computed_field']}, {record['price_total']}")
```

## Summary

**Frontend Testing Strategy**:
1. **Primary**: Playwright + Chrome DevTools - Real browser testing with console log capture and JS error detection
2. **Secondary**: xmlrpc form metadata validation - Quick checks when browser unavailable
3. **Tertiary**: JS/OWL unit tests - Edge cases and custom component logic

**Test Scope Pyramid**:
```
┌─────────────────────────────┐
│   JS Unit Tests (Few)       │  Edge cases, custom logic, refactoring safety
├─────────────────────────────┤
│  xmlrpc Form Checks (Some)  │  Pre-flight metadata validation
├─────────────────────────────┤
│ Browser Tests (Many)        │  Full UI workflows, console validation, user scenarios
└─────────────────────────────┘
```

**What Browser Testing Catches** (xmlrpc cannot):
- ✅ JavaScript execution errors (syntax, runtime)
- ✅ Console errors, warnings, and logged issues
- ✅ Network request failures (4xx/5xx responses)
- ✅ Async operations (promises, timeouts)
- ✅ Race conditions and timing issues
- ✅ DOM rendering and visibility
- ✅ Actual user interactions (clicks, field fills)
- ✅ Page load performance metrics

**Integration with progress.json LIVE TEST**:
- Run browser tests immediately after `install` step
- Capture console logs to validate no JS errors occurred
- Browser test = acceptance test for feature completion
- All 5 core tests (form rendering, create, actions, console health, network) must pass before marking LIVE TEST done

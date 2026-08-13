---
name: odoo_backend_testing
description: Backend testing patterns for custom Odoo modules using xmlrpc scripts for post-installation validation. Use when creating backend tests for Odoo modules.
version: 1.0.0
author: VPCS Team
category: testing
odoo_versions: ["17.0", "18.0", "19.0"]
tags: ["odoo", "testing", "xmlrpc", "backend", "validation", "scripts"]
---
## Goal
Define post-installation/update backend test approach for custom Odoo modules using **xmlrpc scripts** for direct functionality validation, aligned with progress/task live-test loops.

## Primary Approach: xmlrpc Scripts (Post-Install/Update)

### Why xmlrpc?
- **BEST WAY**: RPC-based testing is the **PREFERRED** and **BEST WAY** to test custom Odoo apps. It validates real interaction logic after installation and bypasses the limitations of Odoo's built-in test runner.
- **Direct**: Tests real module behavior after installation/update (full RPC workflow).
- **Executable**: Runs standalone after `manage_modules.sh install/update` without pytest overhead.
- **Effective**: Validates complete flows (CRUD, access rights, cron jobs, integrations) in single script.
- **Maintainable**: Stored in module's `/scripts/` folder alongside module code.
- **Clear**: Non-technical stakeholders can understand test intent and results.

### Structure & Conventions

#### A. Script Location
```
<custom_module>/
  __init__.py
  __manifest__.py
## Goal

Define post-installation/update backend test approach for custom Odoo modules using xmlrpc/json2 scripts for direct functionality validation, aligned with progress/task live-test loops.

## Primary Approach: xmlrpc / JSON-2 Scripts (Post-Install/Update)

Why use scripts:
- Run after install/update to validate full workflows (CRUD, transitions, ACLs, cron jobs, integrations).
- Stored in the module `scripts/` folder and executable by the agent.
- Support both legacy XML-RPC (Odoo <=18) and JSON-2 API (Odoo 19+).

Script layout example:

```text
<custom_module>/
  __init__.py
  __manifest__.py
  models/
  views/
  data/
  security/
  scripts/
    __init__.py
    test_workflows.py
    test_integrations.py
    test_migrations.py
```

Base xmlrpc test template (simplified):

```python
#!/usr/bin/env python3
"""
Module post-installation validation script.
Usage: python3 test_workflows.py [--url URL] [--db DB] [--user USER] [--password PASSWORD]

Credentials default to .env values (ODOO_URL, ODOO_DB_NAME, ODOO_DB_USER, ODOO_DB_PASSWORD)
"""

import xmlrpc.client
import sys
import os
from argparse import ArgumentParser

class OdooTestClient:
    def __init__(self, url, db, user, password):
        self.url = url
        self.db = db
        self.user = user
        self.password = password
        self.common = xmlrpc.client.ServerProxy(f"{url}/xmlrpc/2/common")
        self.object = xmlrpc.client.ServerProxy(f"{url}/xmlrpc/2/object")
        self.uid = self.common.authenticate(db, user, password, {})
        if not self.uid:
            raise ValueError(f"Authentication failed for {user}@{db} on {url}")

    def create(self, model, values):
        return self.object.execute_kw(self.db, self.uid, self.password, model, 'create', [values])

    def read(self, model, record_id, fields=None):
        return self.object.execute_kw(self.db, self.uid, self.password, model, 'read', [record_id], {'fields': fields or []})

    def call_method(self, model, method, record_id, args=None):
        args = args or []
        return self.object.execute_kw(self.db, self.uid, self.password, model, method, [[record_id]] + args)
    
    def write(self, model, record_id, values):
        """Update record; return True."""
        return self.object.execute_kw(self.db, self.uid, self.password,
                                      model, 'write', [record_id], values)
    
    def search(self, model, domain):
        """Search records; return IDs."""
        return self.object.execute_kw(self.db, self.uid, self.password,
                                      model, 'search', [domain])
    
    def call_method(self, model, method, record_id, args=None):
        """Call model method; return result."""
        args = args or []
        return self.object.execute_kw(self.db, self.uid, self.password,
                                      model, method, [[record_id]] + args)
```

## Configuration (use .env)

- The agent MUST read `AgentSkills/.env` (copy from `env_template.txt`) for runtime paths and credentials. Key variables:
    - **Paths**: `ODOO_LOCAL_PATH` / `ODOO{X}_LOCAL_PATH`, `ODOO_MANAGE_SCRIPT`, `ODOO_CUSTOM_ADDONS`, `ODOO_LOG_FILE`, `FILESYSTEM_ROOT_PATH`
    - **Database Credentials**: `ODOO_DB_NAME`, `ODOO_DB_USER`, `ODOO_DB_PASSWORD`, `ODOO_API_KEY`, `ODOO_URL`
    - **Version-specific**: `ODOO17_DB_NAME`, `ODOO18_DB_NAME`, `ODOO19_DB_NAME`, etc.

Example usage in xmlrpc scripts:

```python
import os

# Load credentials from environment (set in AgentSkills/.env)
url = os.getenv('ODOO_URL', 'http://localhost:8069')
db = os.getenv('ODOO_DB_NAME', 'odoo19')
user = os.getenv('ODOO_DB_USER', 'admin')
password = os.getenv('ODOO_DB_PASSWORD', 'admin')
api_key = os.getenv('ODOO_API_KEY', '')  # Optional, for Odoo 14+

# Use api_key if available, otherwise use password
auth_credential = api_key if api_key else password
```

If version-specific env vars exist (e.g., `ODOO19_DB_NAME`), prefer them for that version.

## API Choice: XML-RPC vs JSON-2 (Odoo 19+)

- For Odoo 19+ prefer the JSON-2 API (`/json/2/...`) when available because it's modern and supports API keys. Use XML-RPC for backward compatibility and when JSON-2 isn't available.
- Detection pseudocode:

```py
if version >= 19 and endpoint_responds('/json/2'):
        use_json2 = True
else:
        use_json2 = False
```

When using JSON-2, tests should switch to HTTP `requests` calls and bearer API keys. Provide both templates in `/scripts/` and prefer JSON-2 template when Odoo 19+.

## Executing Tests (recommended agent workflow)

When `.sandbox/session.json` exists, use the controller contract:

```bash
SESSION_ID=$(python3 -c 'import json; print(json.load(open(".sandbox/session.json"))["session_id"])')
sandbox/bin/sandboxctl module "$SESSION_ID" install <module>
sandbox/bin/sandboxctl module "$SESSION_ID" test <module>
```

The newest result JSON must report `succeeded`. Do not run raw `odoo-bin`;
local mode continues to use `bash manage_modules.sh`.

1. Ensure Odoo is running and port ready (see port readiness section below).
2. Run the module's xmlrpc or json2 script from the module `scripts/` folder using the AgentSkills venv Python:

```bash
VENV_PY="$FILESYSTEM_ROOT_PATH/AgentSkills/.venv/bin/python"
cd "$ODOO_CUSTOM_ADDONS/<module>/scripts"
"$VENV_PY" python3 test_workflows.py --url http://127.0.0.1:8069 --db mydb --user admin --password admin
```

3. Capture exit code and stdout/stderr. On failure, parse stacktrace and update progress file with error context.

## Port readiness and verification

Before running tests, verify Odoo HTTP port (default 8069) is accepting connections:

```bash
curl -sSf http://127.0.0.1:8069/ -o /dev/null && echo "open" || echo "closed"
```

If closed, tail `ODOO_LOG_FILE` and surface the last 200 lines to help debugging.

## Reporting test results to progress file

- After running tests, agent MUST append a `test_results` entry to `PROGRESS_DIR/<module>_progress.json` containing:

```json
"test_results": {
    "timestamp": 1234567890,
    "script": "scripts/test_workflows.py",
    "stdout": "...",
    "stderr": "...",
    "exit_code": 1
}
```

Set `sub_task` status to `complete` or `failed` depending on `exit_code` and include `retry_count` if retries were attempted.

## Retry policy and backoff

- Use up to 3 attempts with exponential backoff (2s, 5s, 10s). After 3 failed attempts mark the test sub-task as `failed` and attach logs to progress file.

## Example: Running JSON-2 test snippet (Odoo 19+)

```python
import requests
url = 'http://127.0.0.1:8069/json/2/res.partner/search'
payload = {
    'params': {
        'domain': [],
        'fields': ['name']
    }
}
headers = {'Authorization': 'Bearer ' + API_KEY}
resp = requests.post(url, json=payload, headers=headers)
resp.raise_for_status()
```


# ============================================================================
# TEST FLOWS
# ============================================================================
```python

def test_model_creation_and_validation(client):
    """Test 1: Create and validate custom model records."""
    print("\\n[Test 1] Model Creation & Validation")
    try:
        # Create
        record_id = client.create('custom_module.custom_model', {
            'name': 'Test Record',
            'description': 'Automated test via xmlrpc',
            'status': 'draft',
        })
        print(f"  ✓ Created record ID {record_id}")
        
        # Read
        record = client.read('custom_module.custom_model', record_id, ['name', 'status'])
        assert record['status'] == 'draft', f"Status mismatch: {record['status']}"
        print(f"  ✓ Record validated: {record['name']} (status={record['status']})")
        
        return True
    except Exception as e:
        print(f"  ✗ FAILED: {e}")
        return False

def test_workflow_transitions(client):
    """Test 2: Workflow state transitions and side effects."""
    print("\\n[Test 2] Workflow Transitions")
    try:
        # Create record
        record_id = client.create('custom_module.custom_model', {
            'name': 'Workflow Test',
            'status': 'draft',
        })
        print(f"  ✓ Created record {record_id}")
        
        # Transition to confirmed (triggers compute/onchange)
        result = client.call_method('custom_module.custom_model', 'action_confirm', record_id)
        print(f"  ✓ Transitioned to confirmed")
        
        # Validate side effects
        record = client.read('custom_module.custom_model', record_id, ['status', 'confirmed_by', 'confirmed_date'])
        assert record['status'] == 'confirmed', f"Expected 'confirmed', got {record['status']}"
        assert record['confirmed_by'], "confirmed_by not set"
        print(f"  ✓ Side effects validated: confirmed_by={record['confirmed_by']}, date={record['confirmed_date']}")
        
        return True
    except Exception as e:
        print(f"  ✗ FAILED: {e}")
        return False

def test_acl_and_record_rules(client):
    """Test 3: Access Control & Record Rules."""
    print("\\n[Test 3] ACL & Record Rules")
    try:
        # Create as admin
        record_id = client.create('custom_module.custom_model', {
            'name': 'ACL Test',
            'restricted_field': 'sensitive_data',
        })
        print(f"  ✓ Created record {record_id} as admin")
        
        # Verify admin can read
        record = client.read('custom_module.custom_model', record_id, ['name', 'restricted_field'])
        print(f"  ✓ Admin can read: {record['name']}")
        
        # (Optional) Test as restricted user if user exists
        # - Create OdooTestClient with restricted user
        # - Verify domain/rule restrictions applied
        
        return True
    except Exception as e:
        print(f"  ✗ FAILED: {e}")
        return False

def test_cron_and_scheduled_actions(client):
    """Test 4: Cron Jobs & Scheduled Actions."""
    print("\\n[Test 4] Cron Jobs & Scheduled Actions")
    try:
        # Search for module's crons
        crons = client.search('ir.cron', [('name', 'ilike', 'custom_module')])
        print(f"  ✓ Found {len(crons)} cron(s) for custom_module")
        
        if crons:
            # Manually trigger first cron
            cron_id = crons[0]
            result = client.call_method('ir.cron', 'method_direct_trigger', cron_id)
            print(f"  ✓ Triggered cron {cron_id}; result={result}")
        
        return True
    except Exception as e:
        print(f"  ✗ FAILED: {e}")
        return False
```
## TEST FLOWS

Below are recommended test functions to include in `scripts/test_workflows.py`.

```python
def test_model_creation_and_validation(client):
    """Test 1: Create and validate custom model records."""
    print("\n[Test 1] Model Creation & Validation")
    try:
        # Create
        record_id = client.create('custom_module.custom_model', {
            'name': 'Test Record',
            'description': 'Automated test via xmlrpc',
            'status': 'draft',
        })
        print(f"  ✓ Created record ID {record_id}")

        # Read
        record = client.read('custom_module.custom_model', record_id, ['name', 'status'])
        assert record['status'] == 'draft', f"Status mismatch: {record['status']}"
        print(f"  ✓ Record validated: {record['name']} (status={record['status']})")

        return True
    except Exception as e:
        print(f"  ✗ FAILED: {e}")
        return False


def test_workflow_transitions(client):
    """Test 2: Workflow state transitions and side effects."""
    print("\n[Test 2] Workflow Transitions")
    try:
        record_id = client.create('custom_module.custom_model', {'name': 'Workflow Test', 'status': 'draft'})
        print(f"  ✓ Created record {record_id}")

        # Transition to confirmed
        client.call_method('custom_module.custom_model', 'action_confirm', record_id)
        print(f"  ✓ Transitioned to confirmed")

        record = client.read('custom_module.custom_model', record_id, ['status', 'confirmed_by', 'confirmed_date'])
        assert record['status'] == 'confirmed'
        assert record['confirmed_by']
        print(f"  ✓ Side effects validated")
        return True
    except Exception as e:
        print(f"  ✗ FAILED: {e}")
        return False


def test_acl_and_record_rules(client):
    """Test 3: Access Control & Record Rules."""
    print("\n[Test 3] ACL & Record Rules")
    try:
        record_id = client.create('custom_module.custom_model', {'name': 'ACL Test', 'restricted_field': 'sensitive_data'})
        print(f"  ✓ Created record {record_id} as admin")
        record = client.read('custom_module.custom_model', record_id, ['name', 'restricted_field'])
        print(f"  ✓ Admin can read: {record['name']}")
        return True
    except Exception as e:
        print(f"  ✗ FAILED: {e}")
        return False


def test_cron_and_scheduled_actions(client):
    """Test 4: Cron Jobs & Scheduled Actions."""
    print("\n[Test 4] Cron Jobs & Scheduled Actions")
    try:
        crons = client.search('ir.cron', [('name', 'ilike', 'custom_module')])
        print(f"  ✓ Found {len(crons)} cron(s)")
        if crons:
            cron_id = crons[0]
            client.call_method('ir.cron', 'method_direct_trigger', cron_id)
            print(f"  ✓ Triggered cron {cron_id}")
        return True
    except Exception as e:
        print(f"  ✗ FAILED: {e}")
        return False


def test_integrations_and_external_calls(client):
    """Test 5: External Integrations (APIs, webhooks)."""
    print("\n[Test 5] Integrations & External Calls")
    try:
        record_id = client.create('custom_module.custom_model', {'name': 'Integration Test', 'external_id': 'test_ext_123'})
        print(f"  ✓ Created record {record_id}")
        # Additional integration checks go here
        return True
    except Exception as e:
        print(f"  ✗ FAILED: {e}")
        return False
```

### MAIN runner

```python
def main():
    # Load defaults from environment variables (from AgentSkills/.env)
    default_url = os.getenv('ODOO_URL', 'http://localhost:8069')
    default_db = os.getenv('ODOO_DB_NAME', 'odoo19')
    default_user = os.getenv('ODOO_DB_USER', 'admin')
    default_password = os.getenv('ODOO_DB_PASSWORD', 'admin')

    parser = ArgumentParser(description='Custom module xmlrpc test suite.')
    parser.add_argument('--url', default=default_url, help=f'Odoo server URL (default: {default_url})')
    parser.add_argument('--db', default=default_db, help=f'Database name (default: {default_db})')
    parser.add_argument('--user', default=default_user, help=f'Username (default: {default_user})')
    parser.add_argument('--password', default=default_password, help=f'Password (default: from .env)')
    args = parser.parse_args()

    print(f"\n{'='*70}")
    print("Testing Custom Module: post-install/update validation")
    print(f"Server: {args.url} | DB: {args.db} | User: {args.user}")
    print(f"{'='*70}")

    try:
        client = OdooTestClient(args.url, args.db, args.user, args.password)
    except Exception as e:
        print(f"✗ Connection failed: {e}")
        sys.exit(1)

    results = {
        'Model Creation & Validation': test_model_creation_and_validation(client),
        'Workflow Transitions': test_workflow_transitions(client),
        'ACL & Record Rules': test_acl_and_record_rules(client),
        'Cron Jobs & Scheduled Actions': test_cron_and_scheduled_actions(client),
        'Integrations & External Calls': test_integrations_and_external_calls(client),
    }

    print(f"\n{'='*70}")
    print("TEST SUMMARY")
    print(f"{'='*70}")
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    for test_name, result in results.items():
        status = '✓ PASS' if result else '✗ FAIL'
        print(f"  {status}: {test_name}")
    print(f"\nResult: {passed}/{total} tests passed")

    return 0 if passed == total else 1

if __name__ == '__main__':
    sys.exit(main())
```
```

## Secondary Approach: Unit Tests (for regression/edge cases)

### When to use unit tests
- Edge cases and error paths (not covered by xmlrpc flow tests).
- Complex compute/constraint logic.
- Mocking external calls (APIs, payment gateways).
- Performance/load testing.

### Practices
- Use `--test-tags <module>` to isolate; keep tests deterministic.
- Arrange/Act/Assert pattern; cover happy path + error cases.
- Seed data with YAML/CSV/demo when needed; clean up after tests.
- Validate ACL/record rules explicitly (sudo vs non-sudo).
- **Odoo 19 Data**: `type='product'` is removed. Use `'type': 'consu'` and `'is_storable': True` for storable products.

### Unit Test File Location
```
<custom_module>/tests/
  __init__.py
  common.py          # Test fixtures, test data
  test_models.py     # Model creation, compute, constraints
  test_workflows.py  # Workflow transitions, side effects
  test_security.py   # ACL, record rules, access denial
```

## Integration: LIVE TEST Sub-Task

### Step 1: Install/Update Module
```bash
cd /path/to/odoo_local_setup
./manage_modules.sh install custom_module --version 19
```

### Step 2: Run xmlrpc Test Script
```bash
cd /path/to/custom_module/scripts
python3 test_workflows.py \
  --url http://localhost:8019 \
  --db odoo19 \
  --user admin \
  --password admin
```

### Step 3: Verify Results
- All xmlrpc tests pass (5/5 ✓).
- No exceptions or connection errors.
- External integrations validated (webhooks, API calls logged).

### Step 4: Mark as LIVE TEST Complete
```json
{
  "feature": "Custom Module Feature",
  "sub_tasks": [
    {"title": "Install module", "status": "done"},
    {"title": "Run xmlrpc tests", "status": "done"},
    {"title": "LIVE TEST", "status": "done"}
  ]
}
```

## Key Differences: xmlrpc vs Unit Tests

| Aspect | xmlrpc Script | Unit Test |
|--------|---------------|-----------|
| **Scope** | Full workflow (CRUD→validate→transition→side effects) | Single method/constraint |
| **Trigger** | Post-install/update (manual or CI/CD) | Before commit (`--test-tags`) |
| **Execution** | Standalone Python script (no pytest) | pytest framework |
| **Mocking** | Minimal; tests real module behavior | Heavy; isolates component |
| **Speed** | Slower (full RPC + DB ops) | Fast (in-memory, mocked) |
| **Stakeholder** | Can review test intent easily | Requires Python knowledge |
| **Use Case** | Acceptance testing, regression validation | Edge case coverage, refactoring safety |

## Example: Custom App Dependency Testing

If custom_app depends on custom_lib:
1. Create `/custom_lib/scripts/test_api.py` to validate lib exports (functions, models).
2. Create `/custom_app/scripts/test_workflows.py` to test integration with custom_lib.
3. Run both after install: `test_api.py` → `test_workflows.py`.
4. Mark LIVE TEST complete only if both pass.

## Official Odoo Documentation References

### Odoo 17.0 External API (XML-RPC)
- **URL**: https://www.odoo.com/documentation/17.0/developer/reference/external_api.html
- **Authentication**: `xmlrpc/2/common` endpoint → `authenticate(db, username, password, {})` returns uid
- **Method calls**: `xmlrpc/2/object` endpoint → `execute_kw(db, uid, password, model, method, args, kw={})`
- **Key methods**: search, search_count, read, write, create, unlink, fields_get, search_read
- **API Keys**: Supported since Odoo 14.0; use API key instead of password

### Odoo 18.0 External API (XML-RPC)
- **URL**: https://www.odoo.com/documentation/18.0/developer/reference/external_api.html
- **Authentication**: Same as 17.0 → `xmlrpc/2/common` with `authenticate()`
- **Method calls**: Same `xmlrpc/2/object` with `execute_kw()`
- **Key methods**: Identical to 17.0 (search, read, write, create, unlink, etc.)
- **API Keys**: Required for enhanced security; replace password with API key

### Odoo 19.0 External API (JSON-2 + XML-RPC Legacy)
- **Primary (New)**: https://www.odoo.com/documentation/19.0/developer/reference/external_api.html
  - **JSON-2 API** (New in 19.0): Modern HTTP REST-like API via `/json/2/<model>/<method>`
  - **Headers**: `Authorization: bearer <API_KEY>`, `X-Odoo-Database` (optional), `Content-Type: application/json`
  - **No uid/password**: Uses API keys directly; stateless per-call authentication
  - **Example**: `POST /json/2/res.partner/search` with domain/fields in JSON body
  - **Deprecated**: XML-RPC and JSON-RPC endpoints scheduled for removal in Odoo 20 (fall 2026)

- **Legacy (Deprecated)**: https://www.odoo.com/documentation/19.0/developer/reference/external_rpc_api.html
  - **XML-RPC**: Still supported but deprecated; same as 17.0/18.0 syntax
  - **Migration**: For 19.0+ projects, prefer JSON-2 API over XML-RPC

### Syntax Reference

#### Odoo 17/18 (XML-RPC)
```python
import xmlrpc.client

url = "http://localhost:8017"  # 17.0
db = "odoo17"
username = "admin"
password = "admin"  # or API_KEY (Odoo 14+)

common = xmlrpc.client.ServerProxy(f'{url}/xmlrpc/2/common')
object_rpc = xmlrpc.client.ServerProxy(f'{url}/xmlrpc/2/object')

uid = common.authenticate(db, username, password, {})

# Search
ids = object_rpc.execute_kw(db, uid, password, 'res.partner', 'search', [[['is_company', '=', True]]])

# Read
records = object_rpc.execute_kw(db, uid, password, 'res.partner', 'read', [ids], {'fields': ['name', 'email']})

# Create
id = object_rpc.execute_kw(db, uid, password, 'res.partner', 'create', [{'name': 'Test'}])

# Write
object_rpc.execute_kw(db, uid, password, 'res.partner', 'write', [[id], {'name': 'Updated'}])

# Call method
object_rpc.execute_kw(db, uid, password, 'custom_module.model', 'action_confirm', [[id]])
```

#### Odoo 19.0 (JSON-2 API - Recommended)
```python
import requests

url = "https://mycompany.example.com/json/2"
api_key = "<your_api_key_here>"
db = "mycompany"  # only if not in domain

headers = {
    "Authorization": f"bearer {api_key}",
    "X-Odoo-Database": db,
    "Content-Type": "application/json",
}

# Search
res = requests.post(
    f"{url}/res.partner/search",
    headers=headers,
    json={"domain": [["is_company", "=", True]]}
)
ids = res.json()

# Read
res = requests.post(
    f"{url}/res.partner/read",
    headers=headers,
    json={"ids": ids, "fields": ["name", "email"]}
)
records = res.json()

# Create
res = requests.post(
    f"{url}/res.partner/create",
    headers=headers,
    json={"name": "Test"}
)
id = res.json()

# Call method
res = requests.post(
    f"{url}/custom_module.model/action_confirm",
    headers=headers,
    json={"ids": [id]}
)
result = res.json()
```

## Summary
- **Primary**: xmlrpc scripts in `/scripts/` folder for post-install validation.
- **Secondary**: Unit tests for edge cases and regression safety.
- **Integration**: Both tied to progress.json LIVE TEST sub-task.
- **Version Strategy**:
  - **Odoo 17/18**: Use XML-RPC (xmlrpc.client) via `/xmlrpc/2/common` and `/xmlrpc/2/object`
  - **Odoo 19**: Prefer JSON-2 API (requests library) via `/json/2/<model>/<method>`; XML-RPC deprecated
  - **API Keys**: Use instead of password for enhanced security (all versions)

---
name: odoo_restart_upgrade_rules
description: Rules and patterns for Odoo module upgrades, restarts, and migration scripts. Use when upgrading Odoo modules or handling version migrations.
version: 1.0.0
author: VPCS Team
category: operations
odoo_versions: ["17.0", "18.0", "19.0"]
tags: ["odoo", "upgrade", "migration", "restart", "operations"]
---
# Odoo Server Restart vs. Upgrade Rules

## Critical Distinction: Restart vs. Module Upgrade

Odoo requires different restart/upgrade strategies depending on **what changed** in your custom code. This skill defines the rules.

---

## 1. Server RESTART Only (Fast - No Module Upgrade Needed)

Use **restart** when changes are confined to:

### 1a. Normal Python Methods (Business Logic)
- Compute methods (`@api.depends(...)`)
- Action methods (`def action_*`)
- Helper methods (internal logic)
- **EXCEPT**: Methods that touch `fields` or use `@api.onchange` with new fields

**Example:**
```python
@api.depends('amount', 'tax_rate')
def _compute_total(self):
    self.total = self.amount * (1 + self.tax_rate / 100)  # ✅ RESTART ONLY
```

### 1b. Decorators & Constraints (No Field Changes)
- `@api.constrains(...)` - constraint logic
- `@api.onchange(...)` - on existing fields only
- `@api.depends(...)` - on existing fields only
- SQL/ORM queries refactoring

**Example:**
```python
@api.constrains('price')
def _check_price(self):
    if self.price < 0:
        raise ValidationError("Price must be positive")  # ✅ RESTART ONLY
```

### 1c. Controller / Endpoint Logic
- HTTP route handlers
- JSON-RPC methods
- Authentication/authorization logic

**Example:**
```python
@http.route('/my_module/api/data', auth='user', type='json')
def get_data(self):
    return {'data': self.env['my.model'].search_read([])}  # ✅ RESTART ONLY
```

### 1d. Python Imports & Dependencies
- Adding new `import` statements
- Refactoring function calls
- Logic reorganization

**Restart Command:**
```bash
# Kill and restart Odoo server on port
pkill -f "odoo-bin.*19.0"
# or use manage_modules.sh
./manage_modules.sh restart
```

---

## 2. Module UPGRADE (Full Module Reload - Required)

Use **upgrade** when changes include:

### 2a. ⚠️ Field Definitions (ALWAYS)
- Adding new fields (`fields.Char()`, `fields.Many2one()`, etc.)
- Changing field type (e.g., `Char` → `Integer`)
- Modifying field attributes (`string=`, `required=True`, `readonly=True`, etc.)
- Adding/removing field constraints or validators
- **INCLUDES**: Function fields (`compute=`, `search=`, `inverse=`)

**Example - REQUIRES UPGRADE:**
```python
# Old version
class CoffeeOrder(models.Model):
    amount = fields.Float()

# New version - ⚠️ REQUIRES UPGRADE
class CoffeeOrder(models.Model):
    amount = fields.Float()
    total_with_tax = fields.Float(compute='_compute_total')  # ⚠️ NEW FIELD → UPGRADE
    tax_rate = fields.Float(default=0.15)  # ⚠️ NEW FIELD → UPGRADE
```

### 2b. View-Level Changes (ALWAYS)
- Adding/removing fields in `<form>`, `<list>`, `<kanban>` views
- Changing field visibility (`invisible="..."`)
- Updating form layouts or tab structures
- Adding new action buttons
- Modifying search filter columns

**Example - REQUIRES UPGRADE:**
```xml
<!-- Old view -->
<form>
    <field name="name"/>
</form>

<!-- New view - ⚠️ REQUIRES UPGRADE -->
<form>
    <field name="name"/>
    <field name="category_id"/>  <!-- ⚠️ NEW FIELD IN VIEW → UPGRADE -->
    <field name="total" invisible="state != 'done'"/>  <!-- ⚠️ NEW LOGIC → UPGRADE -->
</form>
```

### 2c. Model Changes
- Creating new models
- Modifying `_name`, `_description`, `_order`
- Changing inheritance (`_inherit`)
- Updating `_sql_constraints`
- Adding/removing model methods used in views

**Example - REQUIRES UPGRADE:**
```python
# New model added - ⚠️ REQUIRES UPGRADE
class CoffeeRoastingBatch(models.Model):
    _name = 'coffee.roasting.batch'
    _description = 'Coffee Roasting Batch'
    
    name = fields.Char()
    roast_level = fields.Selection([
        ('light', 'Light'),
        ('dark', 'Dark'),
    ])
```

### 2d. Data Files (CSV, XML) Changes
- Adding/updating records in `data/*.xml`
- Modifying `security/ir.model.access.csv`
- Adding workflow definitions
- Creating report templates

**Example - REQUIRES UPGRADE:**
```
security/ir.model.access.csv

id,name,model_id:id,group_id:id,perm_read,perm_write,perm_create,perm_unlink
access_coffee_user,Coffee User,model_coffee_manufacturing,group_coffee_user,1,0,0,0
# ⚠️ NEW RECORD → REQUIRES UPGRADE
```

### 2e. Report Changes
- QWeb template modifications
- Adding new report actions
- Changing report layouts

**Example - REQUIRES UPGRADE:**
```xml
<!-- reports/coffee_label_report.xml - ⚠️ NEW REPORT → UPGRADE -->
<template id="report_coffee_label">
    <div class="page">
        <h2><span t-field="record.name"/></h2>
        <p><strong>Roast Level:</strong> <span t-field="record.roast_level"/></p>
    </div>
</template>
```

**Upgrade Command:**
```bash
./manage_modules.sh update module_name
```

---

## 3. Decision Flow Chart

```
┌─────────────────────────────────┐
│   What Changed?                 │
└─────────────────────────────────┘
         │
         ├─ New/Modified FIELD? ────────→ 🔴 UPGRADE MODULE
         │
         ├─ View Changes (<form>, <list>, etc.)? ──→ 🔴 UPGRADE MODULE
         │
         ├─ New Model Created? ────────→ 🔴 UPGRADE MODULE
         │
         ├─ Data/CSV/XML Changes? ────────→ 🔴 UPGRADE MODULE
         │
         ├─ Python Method/Logic Only? ────→ 🟢 RESTART SERVER
         │   (no fields, no views, no models)
         │
         └─ Controller/Route Changes? ────→ 🟢 RESTART SERVER
```

---

## 4. Progress File Strategy

### First Feature (Module Install)
```json
{
  "features": [{
    "task": "Initial Setup",
    "sub_tasks": [
      { "name": "Create models with fields", "status": "pending" },
      { "name": "Create views", "status": "pending" },
      { "name": "LIVE TEST: Install module (manage_modules.sh install)", "status": "pending" }
    ]
  }]
}
```
**Action**: `./manage_modules.sh install module_name`

### Subsequent Features

#### If only Python logic changes:
```json
{
  "features": [
    { "task": "Feature 1", "status": "complete" },
    {
      "task": "Improve Order Logic",
      "sub_tasks": [
        { "name": "Update compute method", "status": "pending" },
        { "name": "LIVE TEST: Restart server (manage_modules.sh restart)", "status": "pending" }
      ]
    }
  ]
}
```
**Action**: `./manage_modules.sh restart`

#### If field/view changes:
```json
{
  "features": [
    { "task": "Feature 1", "status": "complete" },
    {
      "task": "Add Flavor Support",
      "sub_tasks": [
        { "name": "Add flavor_id field to product", "status": "pending" },
        { "name": "Update product view with flavor field", "status": "pending" },
        { "name": "LIVE TEST: Upgrade module (manage_modules.sh update)", "status": "pending" }
      ]
    }
  ]
}
```
**Action**: `./manage_modules.sh update module_name`

---

## 5. Testing Strategy: XMLRPC vs. JSONRPC

### 5a. XMLRPC (Older, RPCs-style)
Use when testing **model data operations**:
```python
# test_coffee_order_xmlrpc.py
import xmlrpc.client

url = 'http://localhost:8090'
db = 'odoo19'
username = 'admin'
password = 'admin'

common = xmlrpc.client.ServerProxy(f'{url}/xmlrpc/2/common')
uid = common.authenticate(db, username, password, {})

models = xmlrpc.client.ServerProxy(f'{url}/xmlrpc/2/object')

# Create order
order_id = models.execute_kw(db, uid, password, 'coffee.order', 'create', [{
    'name': 'Test Order',
    'amount': 100.0,
}])

# Read
order = models.execute_kw(db, uid, password, 'coffee.order', 'read', [order_id], {'fields': ['name', 'amount']})
print(order)
```

### 5b. JSONRPC (Modern, API-style)
Use when testing **controllers/endpoints**:
```python
# test_coffee_api_jsonrpc.py
import requests
import json

session = requests.Session()
session.auth = ('admin', 'admin')

# Call JSON-RPC endpoint
data = {
    'jsonrpc': '2.0',
    'method': 'call',
    'params': {
        'service': 'object',
        'method': 'execute_kw',
        'args': ['odoo19', 2, 'admin', 'coffee.order', 'create', [{
            'name': 'API Test Order',
            'amount': 150.0,
        }]]
    }
}

response = session.post('http://localhost:8090/jsonrpc', json=data)
result = response.json()
print(result)
```

### Test Script Auto-Generation
After **each sub-task**, agent should:
1. **Detect change type** (field/view/logic)
2. **Generate test script** (XMLRPC for data, JSONRPC for API)
3. **Run test** via `execute_bash`
4. **Capture output** and log to progress file

**Example test sub-task addition:**
```json
{
  "name": "Create test script and verify",
  "test_type": "xmlrpc",
  "test_file": "tests/test_coffee_order.py",
  "status": "pending"
}
```

---

## 6. Implementation in Agent

### Prompt Rule Injection
```python
ODOO_RESTART_UPGRADE_RULES = """
When implementing Odoo features:
1. **Field Changes** → Always use `upgrade` (manage_modules.sh update)
2. **View Changes** → Always use `upgrade` (manage_modules.sh update)
3. **Python Logic Only** → Use `restart` (manage_modules.sh restart)
4. **First Feature** → Use `install` (manage_modules.sh install)
5. **Generate test scripts** (XMLRPC/JSONRPC) per sub-task

Consult Odoo Restart vs. Upgrade Rules skill for details.
"""
```

### Tool Selection in Agent
```python
def select_test_command(changes: Dict[str, bool]) -> str:
    """Select restart vs upgrade based on changes."""
    if changes['has_field_changes'] or changes['has_view_changes'] or changes['has_model_changes']:
        return 'upgrade'  # manage_modules.sh update
    elif changes['has_python_logic']:
        return 'restart'  # manage_modules.sh restart
    return 'install'  # First time only
```

---

## 7. Examples by Module Type

### Example 1: Coffee Manufacturing (Multi-Feature)

**Feature 1: Product Setup**
```
Tasks:
  - Define coffee.roasting.batch model (field: roast_level)
  - Create form/list views
  - LIVE TEST: install (manager_modules.sh install)
→ Action: INSTALL (first time)
```

**Feature 2: Add Flavor Support**
```
Tasks:
  - Add flavor_id field to product
  - Update product view
  - LIVE TEST: upgrade (manage_modules.sh update)
→ Action: UPGRADE (field + view changes)
```

**Feature 3: Improve Roasting Logic**
```
Tasks:
  - Add compute method for _compute_roast_time
  - LIVE TEST: restart (manage_modules.sh restart)
→ Action: RESTART (Python logic only)
```

### Example 2: E-Shop Module

**Feature 1: Shop Setup**
```
→ Action: INSTALL
```

**Feature 2: Add Cart Discount**
```
→ Action: UPGRADE (new field discount_rate on sale.order.line)
```

**Feature 3: Fix Price Calculation**
```
→ Action: RESTART (fix _compute_total method)
```

---

## 8. Key Takeaways

| Change Type | Action | Time | Reason |
|---|---|---|---|
| New Field | UPGRADE | 10-30s | Database schema + ORM cache |
| View Change | UPGRADE | 10-30s | XML parsing + view registry |
| Python Logic | RESTART | 2-5s | Code reload only |
| New Model | UPGRADE | 10-30s | Full registry rebuild |
| Data Files | UPGRADE | 10-30s | Data loading + constraints |
| Controllers | RESTART | 2-5s | Route handler reload |

---

## 9. Skill Integration Notes

- **When to apply this skill**: During task decomposition in progress file
- **Trigger**: Agent detects sub-task type (model/view/logic) and selects appropriate test command
- **Validation**: Check manage_modules.sh logs for success; auto-retry if failure detected
- **Documentation**: Keep progress file annotated with why `install` vs `update` vs `restart` was used


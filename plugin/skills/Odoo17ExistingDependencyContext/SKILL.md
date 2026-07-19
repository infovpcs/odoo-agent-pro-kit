---
name: odoo_17_dependency_context
description: Capture current Odoo 17.0 modules, customizations, and dependency trees. REQUIRES LIVE ODOO CONNECTION. This skill enables the Odoo 17 environment and MCP server to gather live data on installed modules, dependency graphs, and model extensions via XML-RPC. Use this to maintain context on the existing Odoo 17 setup, ensuring that new features or changes are consistent with the current architecture.
version: 17.0.0
author: VPCS Team
category: dependency_analysis
odoo_versions: ["17.0"]
tags: ["odoo", "dependencies", "modules", "analysis", "customizations"]
allowed-tools: ["mcp-odoo:*"]
---
## Goal
Capture current Odoo 17.0 modules, customizations, and dependency trees to drive reuse and avoid regressions.

## Standard Addons Reference Path
- Local: `<your-workspace>/17.0/addons/`
- Upstream: github.com/odoo/odoo/tree/17.0/addons
- Key modules to check: base, web, sale, account, stock, mrp, crm, hr, project, purchase

## What to record

### 1. Installed Modules
- List from `ir_module_module` DB table; flag standard vs custom.
- Check manifest.py `depends` for dependency chain.
- Note version compatibility: if upgrading from 16.0 → 17.0, check breaking changes.

### 2. Standard Addons in Use
- Map each installed standard module to upstream features.
- Check `/addons/<module>/__manifest__.py` (depends list, features).
- Cross-reference against local 17.0 path to understand available models/views.

### 3. Custom Module Dependencies
- For each custom module: list all `depends` (standard + custom).
- Verify all dependencies exist and are installed.
- Build dependency graph: custom_app → [standard_modules, custom_modules].

### 4. Customizations/Overrides
- Models: inheritance chains, monkey patches, field additions.
- Views: XPath modifications, new views, attrs changes.
- Security: custom record rules, group modifications.
- Cron/jobs, integrations, controllers, reports.

### 5. Data & Migrations
- Reference data (sequences, templates, demo records).
- Pending data migrations (if upgrading versions).
- Links to external systems (APIs, webhooks).

### 6. Known Constraints
- Performance hot spots (heavy domains, N+1 queries).
- Upgrade blockers (breaking API changes, removed modules).
- Tech debt, known defects, workarounds.

## Live Context (MCP)
When MCP server is available (`MCP_ENABLED=true`), use live Odoo queries:
- `mcp_search_models`: Discover installed models via XML-RPC
- `mcp_get_fields`: Retrieve field definitions for any model
- `mcp_get_relationships`: Map model inheritance and relations
- `mcp_validate_field`: Validate field names exist on a model
Protocol: XML-RPC (Odoo 17.0)

## Static Fallback
When MCP is unavailable, fall back to static analysis:
- File system scan of `/17.0/addons/`
- Database inspection via odoo-bin shell
- Cached context from previous MCP sessions

## How to gather

### A. Database Inspection
```python
# In odoo-bin shell:
Modules = env['ir.module.module']
installed = Modules.search([('state', '=', 'installed')])
for mod in installed:
    print(f"{mod.name}: depends={mod.dependencies_id.mapped('name')}")
```

### B. File System Scan
- Check `<custom_addons>/*/manifest.py` for custom modules and their dependencies.
- Cross-check against `/17.0/addons/<module>` to confirm standard modules exist.

### C. Code Review
- Grep models for inheritance (e.g., `_inherit = 'sale.order'`).
- Find monkey patches, onchanges, constrains, computes.
- List overridden methods and side effects.

### D. Stakeholder Input
- Which features are business-critical? Which are nice-to-have?
- Any known performance issues or workarounds?
- Planned features or modules to add?

## Output format (concise)

### Dependency Matrix
```
Module | Standard? | Purpose | Customizations | Dependencies | Risks | Reuse Plan
--- | --- | --- | --- | --- | --- | ---
sale | Y | Order mgmt | Order workflow override | account, stock | Custom validation may break on upgrade | Extend, don't duplicate
custom_app | N | Custom workflow | New models, views, crons | sale, custom_lib | Depends on 2 custom modules | Keep focused; split if grows
```

### Hard Constraints (separate list)
- Blocker: custom_app depends on deprecated module X (plan migration).
- Performance: sale order list with 100k+ records (add index on status field).
- Upgrade: dropping support for Odoo 16 custom code (requires refactor).

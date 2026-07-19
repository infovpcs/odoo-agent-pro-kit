---
name: odoo_18_dependency_context
description: Capture current Odoo 18.0 modules, customizations, and dependency trees. REQUIRES LIVE ODOO CONNECTION. This skill triggers the dynamic startup of the Odoo 18 environment and the corresponding MCP server to perform live analysis of installed modules, inherited models, and view structures using XML-RPC. Ideal for ensuring compatibility and identifying dependencies in existing Odoo 18 installations.
version: 18.0.0
author: VPCS Team
category: dependency_analysis
odoo_versions: ["18.0"]
tags: ["odoo", "dependencies", "modules", "analysis", "customizations"]
allowed-tools: ["mcp-odoo:*"]
---
## Goal
Capture current Odoo 18.0 modules, customizations, and dependency trees to maximize reuse and avoid regressions.

## Standard Addons Reference Path
- Local: `<your-workspace>/18.0/addons/`
- Upstream: github.com/odoo/odoo/tree/18.0/addons
- Key modules to check: base, web, sale, account, stock, mrp, crm, hr, project, purchase, web_unseen

## What to record

### 1. Installed Modules
- List from `ir_module_module` DB table; separate standard from custom.
- Parse manifest.py `depends` for dependency chains.
- Note migration status: if upgrading 17.0 → 18.0, check for API changes (list vs tree, attrs vs direct, etc.).

### 2. Standard Addons in Use
- Map each installed standard module to upstream features/models.
- Check `/addons/<module>/__manifest__.py` (depends, assets, data).
- Cross-reference against local 18.0 path to understand available models/views/controllers.

### 3. Custom Module Dependencies
- For each custom module: list all `depends` (standard + custom).
- Validate all dependencies exist and are installed (no orphaned modules).
- Build dependency graph: custom_app → [standard_modules, custom_modules].

### 4. Customizations/Overrides (18.0 differences)
- Models: inheritance chains, field extensions, compute/store changes.
- Views: migration from `<tree>` → `<list>`? attrs → direct attributes?
- Security: record rules, group ACLs.
- Cron/jobs, integrations (webhooks, external APIs), controllers.

### 5. Data & Migrations
- Reference data: sequences, templates, demo data.
- Pending migrations (17.0 → 18.0 schema/data changes).
- External system links (APIs, webhooks, ETL).

### 6. Known Constraints
- Performance hot spots (heavy domains, N+1 queries, missing indexes).
- Upgrade blockers (tree vs list views, attrs parsing, constraint changes).
- Tech debt, known defects, workarounds.

## Live Context (MCP)
When MCP server is available (`MCP_ENABLED=true`), use live Odoo queries:
- `mcp_search_models`: Discover installed models via XML-RPC
- `mcp_get_fields`: Retrieve field definitions for any model
- `mcp_get_relationships`: Map model inheritance and relations
- `mcp_validate_field`: Validate field names exist on a model
Protocol: XML-RPC (Odoo 18.0)

## Static Fallback
When MCP is unavailable, fall back to static analysis:
- File system scan of `/18.0/addons/`
- Database inspection via odoo-bin shell
- Cached context from previous MCP sessions

## How to gather

### A. Database Inspection
```python
# In odoo-bin shell:
Modules = env['ir.module.module']
installed = Modules.search([('state', '=', 'installed')])
for mod in installed:
    deps = mod.dependencies_id.mapped('name')
    print(f"{mod.name}: depends={deps}")
    
# Check for broken dependencies:
orphaned = Modules.search([('state', '=', 'uninstalled'), ('depends_id.state', '=', 'installed')])
print(f"Orphaned: {orphaned.mapped('name')}")
```

### B. File System Scan
- Iterate `<custom_addons>/*/manifest.py` for custom modules.
- Verify all listed `depends` modules exist in `/18.0/addons/` (standard) or `<custom_addons>/` (custom).

### C. Code Review (18.0 specific)
- Grep for `<tree>` views (replace with `<list>`).
- Grep for `attrs="{...}"` in views (convert to direct attributes like `readonly="..."`).
- Check for `_sql_constraints` (plan migration to `models.Constraint`).
- Find `self._context` usages (update to `self.env.context`).

### D. Stakeholder Input
- Which features drive revenue? Which are required for compliance?
- Any blocking issues on 17.0 that 18.0 migration will fix?
- Planned features or new modules needed?

## Output format (concise)

### Dependency Matrix
```
Module | Standard? | Purpose | Customizations | Dependencies | Migration Effort | Risks | Reuse Plan
--- | --- | --- | --- | --- | --- | --- | ---
sale | Y | Order mgmt | List view update, attrs→direct | account, stock | Medium | Custom workflow may break | Extend, don't duplicate
custom_app | N | Custom workflow | New models, constraints, views | sale, custom_lib | High | Depends on 2 custom; need to migrate to models.Constraint | Refactor for 18 while extending
```

### Migration Checklist
- [ ] All custom `<tree>` views converted to `<list>`.
- [ ] All `attrs` replaced with direct field attributes.
- [ ] `_sql_constraints` reviewed; plan `models.Constraint` migration.
- [ ] Routes: check for `type='json'` (plan `jsonrpc` adoption).
- [ ] Models: add `<chatter/>` to mail-enabled forms.
- [ ] No orphaned dependencies.

### Hard Constraints (separate list)
- Blocker: custom_app inherits from module X (removed in 18.0).
- Performance: heavy domain query on order list (add index on state + date).
- Compliance: audit logging must continue across upgrade (validate hooks).

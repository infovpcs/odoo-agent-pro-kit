---
name: odoo_19_dependency_context
description: Capture current Odoo 19.0 modules, customizations, and dependency trees. REQUIRES LIVE ODOO CONNECTION. Use when you need an accurate, live view of the Odoo environment to avoid regressions during development or upgrades.
version: 19.0.1
author: VPCS Team
category: dependency_analysis
odoo_versions: ["19.0"]
tags: ["odoo", "dependencies", "modules", "analysis", "customizations"]
allowed-tools: ["mcp-odoo:*"]
model: haiku
---
## Session Cache Guard
**SKIP this skill if dependency context was already gathered this session.** Only re-run if modules or schema changed.

## Goal
Capture Odoo 19.0 installed modules, customizations, and dependency trees to drive reuse and avoid regressions.

## Paths
- Custom addons: `<your-workspace>/19.0/addons/`
- Standard addons: github.com/odoo/odoo/tree/19.0/addons (key: base, web, sale, account, stock, mrp, crm, hr, project, purchase, mail)

## What to Capture (priority order)

1. **Installed Modules** — query `ir_module_module`; classify standard vs custom; flag unmet dependencies
2. **Custom Module Deps** — `depends` list per custom module; full dep graph; circular dep check
3. **Customizations** — model inheritance, new fields, compute/store; `<list>` views (not `<tree>`); `<chatter/>` usage; `@http.route(type='jsonrpc')`
4. **Known Risks** — N+1 queries, missing indexes, upgrade blockers, API removals

## Live Context (MCP — preferred)
- `mcp_search_models` → discover installed models
- `mcp_get_fields` → field definitions
- `mcp_get_relationships` → inheritance/relations
- `mcp_validate_field` → field existence check

## Static Fallback (when MCP unavailable)
```python
# odoo-bin shell — quick installed module scan
installed = env['ir.module.module'].search([('state','=','installed')])
for m in installed:
    print(m.name, [d.name for d in m.dependencies_id])
```
File scan: `find /19.0/addons -name '__manifest__.py' | xargs grep -l 'depends'`

## 19.0 Code Checks (grep these)
- `<tree>` → must be `<list>`
- `_sql_constraints` → migrate to `models.Constraint`
- `self._context` → use `self.env.context`
- `type='json'` route → use `type='jsonrpc'`
- `message_post()` without `Markup()` → XSS risk

## Output Format (compact)
```
| Module | Type | Depends On | Key Models | Customizations | Risk |
|--------|------|------------|------------|----------------|------|
| sale   | Std  | account,stock | sale.order | custom fields | upgrade-check |
| vpcs_x | Custom | sale,mail | vpcs.x | full MVC | low |
```
List hard constraints separately (blockers, perf issues, compliance).

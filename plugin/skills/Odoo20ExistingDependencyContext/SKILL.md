---
name: odoo_20_dependency_context
description: Capture current Odoo 20.0 modules, customizations, access rows, and dependency trees. REQUIRES LIVE ODOO CONNECTION. Use when you need an accurate, live view of an Odoo 20 environment to avoid regressions during development or 19→20 upgrades.
version: 20.0.0
author: VPCS Team
category: dependency_analysis
odoo_versions: ["20.0"]
tags: ["odoo", "odoo-20", "dependencies", "modules", "analysis", "customizations", "ir-access"]
allowed-tools: ["mcp-odoo:*"]
model: haiku
---
## Session Cache Guard
**SKIP this skill if dependency context was already gathered this session.** Re-run only if
modules or schema changed.

## Goal
Capture Odoo 20.0 installed modules, customizations, access rights, and dependency trees to
drive reuse and avoid regressions.

## Paths
- Custom addons: `<your-workspace>/20.0/addons/`
- Standard addons: github.com/odoo/odoo/tree/20.0/addons (key: base, web, mail, mail_tracking,
  sale, account, stock, mrp, crm, hr, project, purchase, rpc)

## What to Capture (priority order)
1. **Installed Modules** — `ir.module.module` state=installed; standard vs custom; unmet deps.
2. **Custom Module Deps** — `depends` per custom module; note whether `mail_tracking` is needed.
3. **Access** — `ir.access` rows per custom model (`group_id`, `operation`, `domain`, `kind`);
   flag models with no permission row and restriction rows that hide everything.
4. **Customizations** — inheritance, new fields, `<list>` views, `<chatter/>`, routes
   (`type='jsonrpc'`), external callers still on `/xmlrpc` or `/jsonrpc` (removal in 22).
5. **Known Risks** — N+1 queries, missing indexes, upgrade blockers, API removals.

## Live Context (MCP — preferred)
- `odoo_search_models`, `odoo_get_fields`, `odoo_get_relationships`, `odoo_validate_field`
  (kit tools; 20.0 detected via `common.version`).

## Static Fallback (when MCP unavailable)
```python
# odoo-bin shell
for m in env['ir.module.module'].search([('state', '=', 'installed')]):
    print(m.name, [d.name for d in m.dependencies_id])
for a in env['ir.access'].search([('model_id.model', '=like', 'x_%')]):
    print(a.model_id.model, a.group_id.name or '(global)', a.operation, a.kind, a.domain)
```

## 20.0 Code Checks (grep these)
- `ir.model.access.csv` or `model="ir.rule"` → convert to `security/ir.access.csv`
  (`odoo-bin upgrade_code --script 19.4-00-ir-access`)
- `mail.tracking.value` / `tracking_value_ids` → depend on `mail_tracking`
- `<tree>`, `attrs=`, `states=`, `type='json'`, `category_id` on `res.groups` → still blocked
- `class="fa fa-` in new templates → prefer Material Symbols
- `toggle_active` / `boolean_button`, `t-esc` in view arch, `registry._init` → removed in 20
- kanban inheritance of views that now use `card_id` → inherit the `*_card` view instead
- manifest `version` still `19.0.x` → module silently not installable

## Output Format (compact)
```
| Module | Type | Depends On | Key Models | Access rows | Customizations | Risk |
|--------|------|------------|------------|-------------|----------------|------|
| vpcs_x | Custom | sale,mail | vpcs.x | 3 perm / 1 restr | full MVC | acl-migrated |
```
List hard constraints separately (blockers, perf issues, compliance).

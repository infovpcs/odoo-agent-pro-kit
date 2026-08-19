---
name: odoo_19_coding_standard
description: Odoo 19.0 coding standards for models, views, security, constraints, routes, mail/HTML, decorators, tests, and performance. Use when developing Odoo 19 modules to ensure maintainable, upgrade-friendly code.
version: 19.0.1
author: VPCS Team
category: coding_standards
odoo_versions: ["19.0"]
tags: [odoo, python, xml, security, models, views, constraints, performance, testing, controllers, routes, website]
---

# Odoo 19.0 Coding Standard

## Goal
Apply Odoo 19.0 coding standards for maintainable, upgrade-friendly code.

## Sources
- sample_module/ODOO19_CODING_STANDARDS.md (authoritative)
- Upstream references: github.com/odoo/odoo/tree/19.0 (and 18.0/17.0 for compatibility cues)

## Key rules (version-specific)
- Views: use `<list>` (no `<tree>`); replace attrs with direct expressions; always add `<chatter/>` when mail-enabled.
- View Actions: If a view references a method (e.g. `type="object" name="action_view_history"` stat buttons), the method MUST exist in the Python model. Missing methods cause a `ParseError` on module installation.
- XML Domains: `context_today()` is invalid and undefined in evaluated XML domains (like `domain_force`). Use proper Python datetime math or python-computed fields if using `eval="True"`.
- Constraints: use `models.Constraint` (replace `_sql_constraints`); `@api.constrains` for logic.
- Context: use `self.env.context` (not `_context`).
- Routes: prefer `type='jsonrpc'`; `type='json'` deprecated.
- Mail/HTML: wrap user input with `Markup` + `escape` before message_post.
- Decorators: `@api.model_create_multi` for create; keep overrides thin.
- Security: ACL + record rules; minimal `sudo`; validate access in business logic.
- Tests & Data: Odoo 19 removed `type='product'`. For storable products use `'type': 'consu'` and `'is_storable': True`.

## Odoo 19 Security Model (BREAKING vs 17/18)

### `res.groups` — `privilege_id` replaces `category_id`
In Odoo 19, `res.groups` no longer has a `category_id` field. The new hierarchy is:

```
ir.module.category  ←  res.groups.privilege  ←  res.groups
```

**security.xml pattern:**
```xml
<!-- 1. Module category (for App Store / Settings grouping) -->
<record id="module_category_myapp" model="ir.module.category">
    <field name="name">My App</field>
    <field name="sequence" eval="100"/>
</record>

<!-- 2. Privilege (replaces direct category on groups in Odoo 19) -->
<record id="privilege_myapp" model="res.groups.privilege">
    <field name="name">My App</field>
    <field name="category_id" ref="module_category_myapp"/>
</record>

<!-- 3. Groups reference privilege_id, NOT category_id -->
<record id="group_myapp_user" model="res.groups">
    <field name="name">User</field>
    <field name="privilege_id" ref="privilege_myapp"/>
    <field name="implied_ids" eval="[(4, ref('base.group_user'))]"/>
</record>

<record id="group_myapp_manager" model="res.groups">
    <field name="name">Manager</field>
    <field name="privilege_id" ref="privilege_myapp"/>
    <field name="implied_ids" eval="[(4, ref('group_myapp_user'))]"/>
    <!-- field is now user_ids, not users -->
    <field name="user_ids" eval="[(4, ref('base.user_root')), (4, ref('base.user_admin'))]"/>
</record>
```

**Key changes from 17/18:**
- `res.groups.category_id` → `res.groups.privilege_id` (Many2one to `res.groups.privilege`)
- `res.groups.users` → `res.groups.user_ids`
- New model: `res.groups.privilege` (links groups to module categories)

### Search View `<group>` — No `expand` or `string` attributes
In Odoo 19, the `<group>` element in search views only accepts form/list-style attributes (`colspan`, `name`, etc.). It does NOT accept `expand` or `string`. Group By filters must be placed directly in `<search>`, not wrapped in `<group>`:

```xml
<!-- WRONG (Odoo 17/18 pattern) -->
<group expand="0" string="Group By">
    <filter name="group_stage" string="Stage" context="{'group_by': 'stage'}"/>
</group>

<!-- CORRECT (Odoo 19) -->
<separator/>
<filter name="group_stage" string="Stage" context="{'group_by': 'stage'}"/>
<filter name="group_partner" string="Client" context="{'group_by': 'partner_id'}"/>
```

### Action Methods Must Return `True` for XML-RPC
Model methods called via buttons or XML-RPC must return a non-None value. Odoo 19 XML-RPC raises an error if a method returns `None`:

```python
# WRONG
def action_activate(self):
    self.write({'stage': 'active'})

# CORRECT
def action_activate(self):
    self.write({'stage': 'active'})
    return True
```

### XML-RPC `execute_kw` Call Convention
When writing test scripts, `execute_kw` takes `args` (list) and `kw` (dict) as SEPARATE positional params. Do NOT bundle `kw` into `args`:

```python
# WRONG — kw dict ends up in args
models.execute_kw(db, uid, pw, model, 'search', [[domain], {'limit': 1}])

# CORRECT
models.execute_kw(db, uid, pw, model, 'search', [[domain]], {'limit': 1})
#                                                 ^args^     ^--kw--^
```
- Cron Jobs: `ir.cron` in Odoo 19 DOES NOT have `numbercall` or `doall` fields. Do not include them in XML data, doing so throws a ValueError.
- Performance: add indexes for heavy domains; avoid N+1 via `.mapped()`/prefetch; batch ops.
- SQL Computed Fields (19.3+/SaaS): `compute_sql='_compute_sql_myfield'` on a field avoids a stored column while keeping GROUP BY / ORDER BY / search at DB level. Pair with `compute='_compute_myfield'` for Python fallback. See dedicated section below.

## Compute methods on smart-button/counter fields: guard against `NewId`

A compute (e.g. a related-record count feeding a form smart button) that
builds a `dict` via `read_group()`/`search_count()` keyed by `self.id`, then
does a raw dict lookup like `counts[record.id]`, throws
`KeyError: <NewId 0x... instance>` the moment a user opens a brand-new,
unsaved form — the in-memory `NewId` record is never a key in that dict
because it has no matching related rows yet. Always use `counts.get(record.id, 0)`
(or equivalent `.get()` with a safe default) in any compute that indexes a
`read_group`/aggregate result by record id. This is a real, reproducible bug
class — verified live in production Odoo 18 code, not theoretical (see
`docs/docker-sandbox/phase-8/live-test.md` step 7 in odoo-agent-pro-kit), and
applies identically in Odoo 19.

## Controllers And Routes

### Production mindset
- AI can generate an Odoo controller in seconds. That does **not** mean it generated a production-grade one.
- Treat `@route()` arguments as behavior-defining infrastructure, not boilerplate.
- When a controller moves from demo traffic to real traffic, auth choice, session writes, CSRF behavior, and parameter access fallbacks matter as much as the method body.

### Baseline route rules
- Choose `type='jsonrpc'` for Odoo RPC-style APIs and `type='http'` for rendered pages, redirects, files, or raw HTTP responses.
- Always restrict `methods=[...]` for non-trivial endpoints. Do not leave mutating routes open to every HTTP verb.
- Use `website=True` only when the route truly needs website context, website rendering, or current-website behavior. Do not add it to internal/back-office APIs by habit.
- `csrf=True` is the default for `type='http'`; `csrf=False` is the default for `type='jsonrpc'`. Disable CSRF only when the caller is external and you replace it with signature/token/idempotency validation.
- Keep controllers thin. Put business rules, access checks, and write logic in models/services so the endpoint stays auditable and testable.

### Auth layers you must choose intentionally
- `auth='user'`: authenticated session user; default choice for back-office or portal flows requiring a logged-in user.
- `auth='bearer'`: API token auth through the `Authorization` header; best for stateless API integrations. Odoo defaults `save_session=False` here.
- `auth='public'`: request runs as the logged-in user if present, otherwise as the shared Public user. Safe only if you explicitly design for anonymous access and re-check record visibility.
- `auth='none'`: use only for framework/nodb/bootstrap endpoints. Avoid normal business logic here because there may be no database/user facilities.
- Never rely on `sudo()` to "make the controller work." If a public route needs `sudo()`, narrow it carefully and validate exactly what may be read or changed.

### High-impact `@route()` details in Odoo 19

```python
@http.route(
    '/api/my-endpoint',
    type='jsonrpc',
    auth='public',
    methods=['GET'],
    csrf=False,
    readonly=True,
    save_session=False,
    handle_params_access_error=my_fallback,
)
```

#### `readonly=True`
- Use it only for endpoints that are genuinely read-only.
- In Odoo 19 this tells the framework the route can start on the read-only cursor path and, in the right infrastructure, may use a read replica.
- It is **not** a security mechanism and **not** write protection.
- Core Odoo will retry with a read/write cursor if the route writes and first hits a read-only transaction error. So `readonly=True` expresses intent and performance/infrastructure preference, not safety.
- Do not mark a route readonly if it updates sessions, logs business events, creates records, posts chatter, or triggers write side effects.

#### `save_session=False`
- Use it for public APIs, bearer APIs, webhooks, payment callbacks, health checks, and heartbeat endpoints when the request does not need to persist session state.
- This prevents unnecessary session cookie creation and dirty-session writes.
- This matters under real traffic. If an external service calls a route 1,000 times per minute, you usually do not want 1,000 session writes.
- Odoo already defaults `save_session=False` for `auth='bearer'`; for `auth='public'` or `auth='none'`, set it explicitly when the endpoint should stay stateless.
- Do **not** disable session saving on flows that intentionally mutate session/cart/visitor state.

#### `handle_params_access_error`
- Use it when route parameters convert URL segments into records such as `<model("product.template"):product>`.
- In Odoo 19, converted records are checked for read access during dispatch. If access or existence fails, `handle_params_access_error` lets you return your own fallback instead of leaking a generic website-style error into an API or UX flow.
- Good uses: return `404`, redirect to a safe canonical URL, or map access failures to a cleaner API response.
- This is especially important in website controllers where deleted/unpublished/inaccessible records should degrade gracefully.

### Website controller guidance
- For website pages, pair `website=True` with explicit `sitemap=` or `sitemap=False`. Do not let private or noisy routes leak into sitemap generation.
- Use `readonly=True` on public website pages that truly only read published content.
- Prefer `handle_params_access_error` for routes using `<model(...)>` parameters so unpublished/missing content becomes a redirect or `404`, not an ugly access traceback.
- If the endpoint is a form POST, checkout step, webhook, or payment return, review `csrf`, `save_session`, and idempotency together rather than independently.
- Use `multilang=False` only when website language switching would break the flow or layout; do not disable it by default.
- `auth='public'` on a website route does not mean "safe by default." Public users still need domain filtering, record access validation, and careful avoidance of broad `sudo()`.

### API and webhook guidance
- Prefer `type='jsonrpc'` for Odoo-native APIs; return structured data and keep the route stateless when possible.
- For third-party callbacks/webhooks, usually combine `methods=['POST']`, `csrf=False`, `save_session=False`, and your own signature/shared-secret verification.
- For token APIs, prefer `auth='bearer'` over ad hoc tokens in query strings.
- For read APIs with high volume, combine narrow domains, explicit field lists, `readonly=True`, and no session persistence.

### What to avoid
- Do not use `readonly=True` as a substitute for access control.
- Do not expose write behavior on `GET` routes.
- Do not set `csrf=False` on browser form routes unless you fully understand the attack surface.
- Do not use `auth='public'` plus `sudo()` plus unfiltered record browsing on business data.
- Do not use `website=True` on endpoints that are purely integration APIs with no website behavior.

### What good controller reviews should check
- Is the auth layer the narrowest one that still fits the use case?
- Are HTTP methods restricted correctly?
- Is CSRF behavior appropriate for the caller type?
- Should the route be stateless with `save_session=False`?
- Is `readonly=True` truthful, or will the route/session write anyway?
- If URL params resolve records, is `handle_params_access_error` needed?
- Is `website=True` really needed, and is sitemap behavior explicit?
- Are business writes and `sudo()` usage minimized and pushed out of the controller body?

## XML Data Files: RELAX NG Schema Compliance

### Official Schema Reference
**URL**: https://github.com/odoo/odoo/blob/19.0/odoo/import_xml.rng

**CRITICAL**: All XML data files (views, data, security, reports, menus) MUST follow the RELAX NG schema defined in `odoo/import_xml.rng`. This schema is the authoritative definition of valid XML structure.

### Key RNG Rules

**Root elements**: `<odoo>`, `<openerp>`, or `<data>` (with optional `noupdate`, `auto_sequence`, `uid`, `context` attributes)

**Record structure**:
```xml
<record id="unique_id" model="model.name">
  <field name="field_name">value</field>
  <!-- Field types: base64, char, file, int, float, list, tuple, html, xml -->
  <!-- Field attributes: ref, eval, search (mutually exclusive) -->
</record>
```

**Template structure**:
```xml
<template id="unique_id" name="Template Name" inherit_id="base.template" primary="True">
  <!-- Optional: t-name, forcecreate, context, priority, groups, active -->
</template>
```

**Menu items**:
```xml
<!-- Root menu: can have web_icon, action, children -->
<menuitem id="menu_root" name="Root" web_icon="module,static/icon.png" sequence="10"/>

<!-- Sub-menu: requires parent, can have action OR children -->
<menuitem id="menu_sub" name="Sub" parent="menu_root" action="action_id" groups="base.group_user"/>
```

**Window actions**:
```xml
<act_window id="action_id" name="Action" res_model="model.name" view_mode="tree,form"
            domain="[]" context="{}" target="current" groups="base.group_user"
            binding_model="other.model" binding_type="action"/>
```

### Common RNG Validation Errors

❌ **WRONG**:
```xml
<record model="ir.ui.view">  <!-- Missing required 'id' -->
<field name="x" type="int" eval="123"/>  <!-- Can't mix type with eval -->
<field name="x" ref="module.id" eval="123"/>  <!-- Can't mix ref with eval -->
<menuitem id="x" web_icon="icon.png" parent="y"/>  <!-- web_icon only for root menus -->
<module>  <!-- Invalid root element -->
```

✅ **CORRECT**:
```xml
<odoo>
  <record id="view_form" model="ir.ui.view">
    <field name="name">model.form</field>
    <field name="arch" type="xml">
      <form><field name="name"/></form>
    </field>
  </record>
</odoo>
```

### Validation
- **xmllint**: `xmllint --noout --relaxng odoo/import_xml.rng module/data/file.xml`
- **Odoo**: Validates XML on module install/upgrade
- **IDE**: Use XML schema validation in VS Code/PyCharm

## Website & Asset Customization (Dark Mode & Styles)

### Dynamic Dark Mode and High-Contrast Guidelines
When building a custom theme or implementing a theme switcher (e.g. `/website/static/src/scss/user_custom_rules.scss`):
- **Dynamic Variable Scope**: Scope all dark mode styles and CSS variables under a clean toggle class (e.g. `html.vpcs-dark-mode`, `#wrapwrap.vpcs-dark-mode`, `.vpcs-dark-mode`) to allow instant theme switches without reloading the DOM.
- **Bootstrap 5 Variable Overrides**: Override standard Bootstrap variables at the root/wrapper selector to cleanly adapt core elements:
  ```css
  #wrapwrap.vpcs-dark-mode {
      --bs-body-bg: #0b0f19 !important;
      --bs-body-color: #f8fafc !important;
      --bs-card-bg: #162032 !important;
      --bs-card-color: #f8fafc !important;
      --bs-tertiary-bg: #162032 !important;
      --bs-border-color: #23314a !important;
      --bs-heading-color: #f8fafc !important;
  }
  ```
- **Bypassing High-Specificity Card Selectors**: Odoo 19 uses high-specificity CSS selectors for cards like `:where(.card:not([data-vxml])) .card-body:not(.card[data-vxml] .card-body)`. Ensure to target these exact selectors to prevent Odoo from keeping card backgrounds light:
  ```css
  #wrapwrap.vpcs-dark-mode :where(.card:not([data-vxml])) .card-body:not(.card[data-vxml] .card-body),
  #wrapwrap.vpcs-dark-mode .card,
  #wrapwrap.vpcs-dark-mode .card-body {
      background-color: var(--vpcs-v4-surface) !important;
      --bs-card-bg: var(--vpcs-v4-surface) !important;
      color: var(--vpcs-v4-text) !important;
  }
  ```
- **Overriding Inline Colored Fonts**: Inline styles (e.g. `<font style="color: rgb(49, 24, 115);">` or `<span style="color: ...">`) applied by drag-and-drop editors override CSS classes. Force them to invert in dark mode using inline attribute selectors:
  ```css
  #wrapwrap.vpcs-dark-mode font[style*="color"],
  #wrapwrap.vpcs-dark-mode span[style*="color"],
  #wrapwrap.vpcs-dark-mode strong[style*="color"],
  #wrapwrap.vpcs-dark-mode [style*="color"]:not(.btn):not(.nav-link) {
      color: var(--vpcs-v4-text) !important;
  }
  ```
- **Overriding General Background Classes & Inline Editor Backgrounds**: Drag-and-drop editor containers or Bootstrap utility classes (e.g. `bg-white`, `bg-light`, `bg-200`, `list-group-item`) specify hardcoded light backgrounds that cause unreadable white-on-white text blocks in dark mode. Override them globally using specific class selectors and attribute selectors matching background attributes:
  ```css
  #wrapwrap.vpcs-dark-mode .bg-white,
  #wrapwrap.vpcs-dark-mode .list-group-item,
  #wrapwrap.vpcs-dark-mode [style*="background-color: rgb(255, 255, 255)"],
  #wrapwrap.vpcs-dark-mode [style*="background: #ffffff"] {
      background-color: var(--vpcs-v4-surface) !important;
      --bs-list-group-bg: var(--vpcs-v4-surface) !important;
      color: var(--vpcs-v4-text) !important;
  }
  ```

### Programmatic SCSS Asset Persistence
- **Native `save_asset` Pattern**: Use Odoo's native `website.assets` `save_asset(url, bundle, content, file_type)` model method rather than raw SQL or views insertion to create a compliant attachment structure.
- **XML-RPC Marshaler Workaround**: Calling `save_asset` via external XML-RPC commits successfully but throws a `TypeError: cannot marshal None` because the Odoo marshaller has `allow_none=False`. Wrap it in a fallback block:
  ```python
  try:
      obj.execute_kw(db, uid, key, "website.assets", "save_asset", [url, bundle, content, "scss"])
  except xmlrpc.client.Fault as f:
      if "cannot marshal None" in str(f.faultString):
          # Database committed successfully!
          pass
  ```
- **Compiled Assets Cache Invalidation**: Delete cached bundles from `ir.attachment` matching `web.assets_frontend.min.css` (or equivalent) to force Odoo to recompile with new SCSS rules on the next page fetch.

## SQL Computed Fields (Odoo 19.3+ / SaaS-19.3)

> **Version gate**: This feature is available in Odoo **19.3 and later SaaS releases**.
> The stable `19.0` branch does NOT include it. Do not use in 19.0 modules targeting stable.
> Validated: feature absent from `/19.0/odoo/orm/fields.py` as of 2026-05-31.

### What it solves
Previously, to filter/group/sort by a computed field you had to set `store=True`, which:
- Adds a physical column to the table
- Requires recompute on every related write
- Can be expensive at scale

`compute_sql` lets the field stay **un-stored** while the DB evaluates it inline using a SQL expression — enabling `GROUP BY`, `SUM`, `ORDER BY`, and `search` at the database level with no extra column.

### Syntax

```python
from odoo import models, fields
from odoo.tools import SQL  # SQL helper — odoo/tools/sql.py

class SaleOrder(models.Model):
    _inherit = 'sale.order'

    total = fields.Float(
        compute='_compute_total',        # Python fallback (required)
        compute_sql='_compute_sql_total', # SQL expression method (new in 19.3)
        compute_sudo=False,               # respect record-level ACL
    )

    def _compute_total(self):
        for rec in self:
            rec.total = rec.qty * rec.price  # Python fallback

    def _compute_sql_total(self, table):
        # Must return a SQL() object using the table alias
        # table._alias is the internal ORM alias; verify against Table class if upgrading
        return SQL(
            "(%s * %s)",
            SQL.identifier(table._alias, 'qty'),
            SQL.identifier(table._alias, 'price'),
        )
```

### Rules

| Rule | Details |
|------|---------|
| Always pair with `compute=` | `compute_sql` alone is not valid; Python fallback is required for single-record access, RPC calls, and tests |
| Use `SQL.identifier()` | Never string-format column names — always use `SQL.identifier(alias, col)` to prevent SQL injection |
| `compute_sudo=False` | Default; inherit ACL from the current user. Set `True` only when field must bypass RLS for reporting |
| Field stays un-stored | Do NOT add `store=True` — that defeats the whole purpose |
| Return type is `SQL()` | The method receives `table` (a `Table` ORM object with `._alias`); return value must be a `SQL()` instance |
| No `depends` needed | The SQL expression is evaluated at query time; no trigger-based recompute |

### What you can now do with an un-stored field

```python
# Group by — works at DB level
self.env['sale.order'].read_group([], ['total:sum'], ['partner_id'])

# Order by
self.env['sale.order'].search([], order='total desc')

# Domain filter
self.env['sale.order'].search([('total', '>', 1000)])
```

> **Note:** `compute_sql` makes the field natively searchable via the SQL expression. A separate `search=` method is NOT required — the ORM uses the SQL expression directly for domain evaluation.

### When NOT to use

- When you need the value in `onchange` (un-stored, no DB round-trip for UI)
- When the SQL expression is complex enough to need subqueries — test performance first
- When the Python fallback would be wrong (e.g., involves `request` context not available in SQL)
- In **Odoo 19.0 stable** — the API does not exist yet

### Migration note (17/18 → 19.3+)

```python
# BEFORE (17/18 — required store=True just to filter)
total = fields.Float(compute='_compute_total', store=True)

# AFTER (19.3+ — no column, full DB capabilities)
total = fields.Float(
    compute='_compute_total',
    compute_sql='_compute_sql_total',
)
```

## Output expectation
Reference the standard file and call out any intentional deviations with rationale/risks.

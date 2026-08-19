---
name: odoo_18_coding_standard
description: Odoo 18.0 coding standards for models, views, security, constraints, and performance. Bridge version to 19.0 with transitional patterns. Use when developing Odoo 18 modules.
version: 18.0.0
author: VPCS Team
category: coding_standards
odoo_versions: ["18.0"]
tags: [odoo, python, xml, security, models, views, constraints, performance, testing]
---

# Odoo 18.0 Coding Standard

## Goal
Apply Odoo 18.0 coding standards for clean, upgrade-friendly code (bridge to 19).

## Sources
- sample_module/ODOO18_CODING_STANDARDS.md (authoritative)
- Upstream refs: github.com/odoo/odoo/tree/18.0 (compare to 17 for deltas)

## Key rules (version-specific)
- Views: start using `<list>` (19 mandates); direct attributes (`readonly="state == 'done'"`) over attrs; `<chatter/>` available.
- Constraints: begin migrating to `models.Constraint`; `_sql_constraints` still valid; `@api.constrains` for logic.
- Decorators: prefer `@api.model_create_multi` for create.
- Routes: `type='json'` still works; adopt `type='jsonrpc'` for forward compatibility.
- Context: `self._context` works; can use `self.env.context`.
- HTML safety: escape user input (Markup/escape) in chatter posts.
- Tests: unit/integration + JS/HOOT where client logic exists; cover access/edge cases.
- Performance: indexes on hot domains; batch ops; avoid N+1; use `.mapped()`.

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
`docs/docker-sandbox/phase-8/live-test.md` step 7 in odoo-agent-pro-kit).

## XML Data Files: RELAX NG Schema Compliance

### Official Schema Reference
**URL**: https://github.com/odoo/odoo/blob/18.0/odoo/import_xml.rng

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

## Output expectation
Reference the standard file; highlight any deviations with rationale/risks.

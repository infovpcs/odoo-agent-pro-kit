---
name: odoo_17_coding_standard
description: Odoo 17.0 coding standards for models, views, security, constraints, and performance. Use when developing Odoo 17 modules to ensure maintainable, upgrade-safe code.
version: 17.0.0
author: VPCS Team
category: coding_standards
odoo_versions: ["17.0"]
tags: [odoo, python, xml, security, models, views, constraints, performance, testing]
---

# Odoo 17.0 Coding Standard

## Goal
Apply Odoo 17.0 coding standards for maintainable, upgrade-safe code.

## Sources
- sample_module/ODOO17_CODING_STANDARDS.md (authoritative)
- Upstream refs: github.com/odoo/odoo/tree/17.0

## Key rules (version-specific)
- Views: use `<tree>` (lists arrive in 18/19); attrs allowed; domains explicit.
- Constraints: `_sql_constraints` for DB checks/uniques; `@api.constrains` for logic.
- Context: use `self._context` (19 moves to `self.env.context`).
- Controllers: `type='json'` valid; `jsonrpc` optional.
- Mail: chatter via mail mixins; no `<chatter/>` tag yet.
- Module layout: manifest data lists XML; no XML in `__init__.py`.
- Security: ACL + record rules; limit `sudo`; assert access in business methods.
- Tests: TransactionCase/unit; cover constraints, access, edge cases.
- Performance: avoid N+1; use `.mapped()`, indexes on hot domains; batch ops.

## XML Data Files: RELAX NG Schema Compliance

### Official Schema Reference
**URL**: https://github.com/odoo/odoo/blob/17.0/odoo/import_xml.rng

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
Reference the standard file and call out any intentional deviations with rationale/risks.

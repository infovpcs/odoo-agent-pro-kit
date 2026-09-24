---
name: odoo_20_coding_standard
description: Odoo 20.0 coding standards for models, views, security (ir.access), mail tracking, icons, routes, external API, and tests. Use when developing or migrating Odoo 20 modules; carries every Odoo 19 rule forward plus the 20.0 breaking changes verified in odoo/odoo@20.0.
version: 20.0.1
author: VPCS Team
category: coding_standards
odoo_versions: ["20.0"]
tags: [odoo, odoo-20, python, xml, security, ir-access, models, views, migration, testing]
---

# Odoo 20.0 Coding Standard

## Goal
Write Odoo 20.0 code that installs cleanly and survives upgrades. Everything in
`Odoo19CodingStandard` still applies unless this file overrides it — load that skill
too for the full view/controller/RNG/SCSS/SQL-computed-field guidance.

## Evidence (verify against your checkout, never from memory)
- Community `odoo/odoo@20.0` `d3236ca5c7052e892a097b007c38b9501888e406` (2026-09-24),
  `odoo/release.py` → `version_info = (20, 0, 0, FINAL, 0, '')`.
- Odoo's own agent skills ship in the repo at `skills/` (`odoo-guidelines`, `odoo-review`,
  `odoo-security`, `odoo-web-guidelines`). **Use them for review, security audit, and generic
  guidelines**; this skill only adds 20.0 migration specifics and the kit's lifecycle rules.
- Official release notes: https://www.odoo.com/odoo-20-release-notes

## Carried forward from 19.0 (still hard errors in 20.0)
- `<list>` not `<tree>`; no `attrs=`/`states=` (ValidationError "Since 17.0 …").
- `@http.route(type='jsonrpc')`; `type='json'` is a deprecated alias (`odoo/http/routing_map.py`).
- `res.groups.privilege_id` (not `category_id`); no `expand=` on search-view `<group>`.
- `models.Constraint` instead of `_sql_constraints`; `self.env.context` not `self._context`.
- Storable products: `'type': 'consu', 'is_storable': True`.

## 20.0 BREAKING: access rights are one model — `ir.access`
`ir.model.access` and `ir.rule` are gone. Source: `odoo/addons/base/models/ir_access.py`.

- File: `security/ir.access.csv` (list it in `__manifest__.py` `data`). Header, exactly as in
  standard addons:
  ```csv
  id,name,model_id,group_id/id,operation,domain
  access_my_model_user,my.model user,my.model,base.group_user,cru,
  access_my_model_manager,my.model manager,my.model,my_module.group_manager,crud,
  my_model_company_rule,my.model multi-company,my.model,,crud,"[('company_id', 'in', company_ids)]"
  ```
- `model_id` is the model's **technical name** (e.g. `sale.order`), not an `model_*` xmlid.
- `operation` is a CRUD subset string: `c`,`r`,`u`,`d` in that order (`crud`, `cru`, `ru`, `r` …).
- `domain` optional (empty = all records). Same eval context as old rules
  (`user`, `company_ids`, `company_id`).
- `kind` is computed: **group set → `permission`** (grants), **group empty → `restriction`**
  (global filter every user must satisfy — replaces global `ir.rule`).
- A former group-scoped `ir.rule` becomes a permission row with a domain on that group.
- Tests: assert with `with_user(...)` and `check_access(...)`; don't query `ir.model.access`.

**Migration:** run Odoo's own rewriter, then review every WARNING/ERROR line it prints:
```bash
./odoo-bin upgrade_code --script 19.4-00-ir-access --addons-path=<custom_addons> --dry-run
./odoo-bin upgrade_code --script 19.4-00-ir-access --addons-path=<custom_addons>
```
(`odoo/upgrade_code/19.4-00-ir-access.py` merges ACL + rules; it limits rule operations to
those granted by the module's ACLs and warns on orphan rules.) Kit lint: L7/L8 block.

## 20.0: mail tracking values moved out of `mail`
- `mail.tracking.value` and `mail.message.tracking_value_ids` now live in the new
  `mail_tracking` module (`addons/mail_tracking/`, depends only on `mail`). Tracking messages
  are rendered on the fly.
- Code/reports/tests that read `tracking_value_ids` must add `'mail_tracking'` to `depends`
  or stop relying on stored values. `tracking=True` on fields still works. Kit lint: L9 warn.

## 20.0: icons — Material Symbols
- Web client icons come from `addons/web/static/src/libs/materialsymbols/`; core web XML no
  longer uses `fa fa-*`. Font Awesome stays for compatibility — prefer Material Symbols in new
  templates. Kit lint: L10 warn.

## 20.0: external API
- `/xmlrpc`, `/xmlrpc/2`, `/jsonrpc` still exist but are **deprecated since 19, removal
  scheduled for Odoo 22** (`addons/rpc/controllers/__init__.py`). New integrations use
  `POST /json/2/<model>/<method>` with an API key (`addons/rpc/controllers/json2.py`).

## 20.0: breaking changes `upgrade_code` does NOT fix (found in a live 19→20 migration)
These made real 19.0 modules fail to install or fail at runtime on 20.0 even after running
`19.4-00-ir-access`. The kit's hook lint blocks each one on 20:
- **L11 — `toggle_active` / `boolean_button` removed.** `BaseModel.toggle_active` no longer exists
  and there is no `boolean_button` widget ("toggle_active is not a valid action on …"). Replace the
  archive stat button with `<widget name="web_ribbon" title="Archived" bg_color="text-bg-danger"
  invisible="active"/>` + `<field name="active" invisible="1"/>`; call `action_archive()` /
  `action_unarchive()` in Python.
- **L12 — `t-esc` forbidden in view arch.** Kanban/card arch accepts only `t-out`, `t-set`,
  `t-value`, `t-if/elif/else`, `t-foreach/as/key`, `t-att*`, `t-call`, `t-name`, `t-debug`,
  `t-translation` (`ir_ui_view.py`). The owl3 script rewrites `t-esc` only under `/static/`, so
  fix `views/*.xml` by hand.
- **L13 — `Registry._init` removed.** Use `not self.env.registry.ready` (or the `install_mode` /
  `module` context keys). Fails only at runtime (AttributeError), so lint is the early warning.
- **Kanban cards moved to a separate `card` view.** `project.view_task_kanban` (and 6 other
  standard kanbans) now reference `card_id="%(…_card)d"`; the fields/templates live in e.g.
  `project.view_task_card`. Inherit the card view, not the kanban, or you get
  "Element '<field name="stage_id">' cannot be located in parent view".
- **Manifest `version` must be `20.0.x`.** A `19.0.x` manifest is silently marked
  `installable=False` ("incompatible version") and `-i` installs nothing (0 tests run, exit 0).

## Upgrade-code scripts available on 20.0
`odoo/upgrade_code/`: `17.5-01-tree-to-list`, `18.1-00-sql-constraint`, `18.1-02-route-jsonrpc`,
`19.1-00-t-call`, `19.3-00-base64-in-xml`, `19.4-00-ir-access`, `19.4-00-ormcache-on-transaction`,
`19.5-00-tuple-rec_names_search`, `owl3-migration`. Each is best-effort — re-run the module's tests
afterwards. See `OdooTools20` for the pitfalls observed running them (they also rewrite Odoo's own
addons; `--from 19.0` can crash in `19.3-00-account-groups`; exit 1 means "files changed").

## Output expectation
Reference the file/SHA you verified, run the kit's `/rules-check-drift`, and never mark a 20.0
migration done without an install + test run in the Docker Sandbox (`sandboxctl module … test`).

# Phase 8 Step 1-2 Findings: Dependency/Context Intake + Coding Standard

Applied against the live pilot module source as it exists inside the running
sandbox session `phase8-pricelist-18`
(`phase8-pilot:/home/ubuntu/odoo-agent-pro-kit/.sandbox/sessions/phase8-pricelist-18/addons/edit_remove_pricelist_rule/`),
retrieved via `sbx exec phase8-pilot -- cat ...` on 2026-08-18 (round 3
continuation). This is a static/manual application of the
`odoo-17-dependency-context`, `odoo-18-dependency-context`, and
`odoo-18-coding-standard` skill checklists (no live XML-RPC/MCP connection
was available for this pass — the module is not yet installed against a
running DB session with MCP wired up, so this follows the "Static Fallback"
path documented in both dependency-context skills).

## Module inventory (verified via `find` inside the sandbox)

```
LICENSE
__init__.py
__manifest__.py
data/remove_price_list_rule.xml
models/__init__.py
models/price_list.py
static/description/*.png (6 images, no JS/OWL/QWeb assets)
views/price_list_view.xml
```

No `static/src/js`, no `static/src/xml`, no `assets` key in the manifest.
**Confirms design.md's step-8 (frontend testing) scoping as N/A is correct**
for this module — nothing to test on the JS/OWL layer.

## Step 1: Dependency/Context Intake

### Dependency Matrix

| Module | Standard? | Purpose | Customizations | Dependencies | Migration Effort | Risks |
|---|---|---|---|---|---|---|
| `edit_remove_pricelist_rule` | N (custom) | Adds a stat-button + server action to bulk-remove all pricelist rule lines from a `product.pricelist` record, and enables multi-edit on the pricelist item list view | New compute field `pricelist_rule_line` on `product.pricelist`; new method `open_pricelist_rules`; new method `action_unlink_pricelist_rule`; view xpath injecting a button box; view xpath enabling `multi_edit` on the item list | `sale_management` (standard, brings in `product.pricelist`, `product.pricelist.item`) | Low — manifest version already bumped to `18.0.1.0.0`, no deprecated API surface used | None found blocking; `pricelist_rule_line == 0` uses `invisible=` direct attribute already (not `attrs=`), so this module's XML was already ported cleanly for 18.0 |

### Custom module dependency chain
`edit_remove_pricelist_rule` -> `sale_management` (standard) -> (implicitly)
`sale`, `product`, `account` per Odoo's own manifest chain. No other custom
modules are depended upon. No orphaned dependencies possible since there is
exactly one `depends` entry and it is a standard, always-available module.

### Customizations/Overrides recorded
- Model: `product.pricelist` inherited (`_inherit`), one computed integer
  field (`pricelist_rule_line`, non-stored, computed via `search_count`), two
  new public methods (`open_pricelist_rules`, `action_unlink_pricelist_rule`).
  No monkey patches, no overridden core methods.
- View: two `ir.ui.view` records via `inherit_id` + `xpath`, both additive
  (button box injection, `multi_edit` attribute injection) — no destructive
  `position="replace"` used.
- Data: one `ir.actions.server` record binding
  `action_unlink_pricelist_rule` to the `product.pricelist` model as a
  bindable action.
- No cron jobs, no controllers, no security/ACL changes, no external
  integrations.

### Known constraints
- Performance: `_compute_count_rule_line` runs one `search_count` per
  record per read — fine at pricelist scale (typically dozens, not
  thousands, of pricelists per DB) but would need batching
  (`read_group`) if ever used on a list view with hundreds of pricelists
  visible simultaneously. Not currently exercised that way (stat button
  only, on the form view).
- No 17.0 -> 18.0 breaking API usage detected: no `<tree>` tags (only
  `<list>`/xpath targeting `//list`), no `attrs="{...}"` (uses direct
  `invisible=` attribute already), no `_sql_constraints`, no
  `self._context` usage, no `type='json'` routes (no controllers at all).
- **This module's XML was evidently already written/ported against an
  18.0-era codebase** (its own manifest version string is `18.0.1.0.0`),
  which is why the Odoo18CodingStandard checklist below finds zero
  violations — there is little/no forward-porting work actually required
  for this specific pilot module. This is a useful, real finding: not
  every module needs code changes to close Phase 8 steps 1-3; some just
  need the process run against them to produce the standard artifacts
  and confidence record.

## Step 2: Coding Standard (`odoo-18-coding-standard`) — file-by-file

| File | Rule checked | Result |
|---|---|---|
| `views/price_list_view.xml` | `<list>` vs `<tree>` | PASS — xpath targets `//list`, no `<tree>` tags anywhere |
| `views/price_list_view.xml` | `attrs="{...}"` vs direct attributes | PASS — uses `invisible="pricelist_rule_line == 0"` directly |
| `views/price_list_view.xml` | RELAX NG structure (`<record id=... model="ir.ui.view">`, `<field name="arch" type="xml">`) | PASS — matches the documented-correct pattern exactly |
| `data/remove_price_list_rule.xml` | RELAX NG structure for `ir.actions.server` record | PASS — `id`/`model` present, `ref=` used (not mixed with `eval=`) |
| `models/price_list.py` | `@api.model_create_multi` (create decorator) | N/A — module defines no `create()` override |
| `models/price_list.py` | `_sql_constraints` / `models.Constraint` migration | N/A — no SQL constraints defined |
| `models/price_list.py` | `self._context` vs `self.env.context` | N/A — neither is used in this module |
| `models/price_list.py` | HTML/user-input escaping in chatter posts | N/A — module posts no chatter messages |
| `__manifest__.py` | RNG-adjacent manifest sanity (depends/data/license present) | PASS — `license: LGPL-3`, `depends: [sale_management]`, `data` lists both XML files that exist on disk |
| Tests | Presence of unit/integration tests | **GAP FOUND** — no `tests/` directory exists in the module at all. This is a real, recorded gap, not fabricated: the coding-standard skill calls for test coverage and none currently exists for this module. Flagged for step 6 (backend testing) to address, not silently ignored. |

### Deviations / risks summary (per Odoo18CodingStandard "Output expectation")
- No standards deviations found in existing code (views/model/manifest all
  already 18.0-idiomatic).
- One real gap: **zero automated tests** ship with this module. This must
  be addressed during step 6 (Odoo_Custom_Backend_Testing) — not a step
  1-3 blocker, but recorded now so it isn't lost.

## Step 1/2 completion status

Steps 1 (dependency/context intake, both 17.0 and 18.0 skill checklists
applied) and 2 (coding standard) are **DONE** for this module as a static
analysis pass. No live XML-RPC/MCP connection was exercised (module is
installed in the sandbox DB — see live-test.md step 4 evidence — but this
particular pass used direct source inspection rather than a live
`mcp_search_models`/`mcp_get_fields` call chain, since no MCP server against
`phase8-pricelist-18`'s Odoo instance was set up this round). If a stricter
reading requires the live-MCP path specifically, that remains a gap to close
in a follow-up round.

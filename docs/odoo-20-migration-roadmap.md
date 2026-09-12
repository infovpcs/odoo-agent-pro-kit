# Odoo 20.0 Migration Roadmap

Status: **tracking — pre-release**
Created: 2026-09-12
Owner: Vinay Rana / infovpcs

## Timeline

- Odoo's `master` branch on `github.com/odoo/odoo` is what eventually becomes
  the `20.0` release branch. Per Odoo's own convention (confirmed via the
  community forum and prior major-version cycles), the `master` → `20.0`
  branch conversion happens **a few days before** the public release, not on
  release day itself.
- Odoo 20 is expected **2026-09-23 to 2026-09-26**, one day ahead of/aligned
  with **Odoo Experience 2026** in Brussels:
  https://www.odoo.com/event/odoo-experience-2026-9099/page/oxp26-be-introduction
- Odoo's official agent-skills library already exists on `master` today, at
  `github.com/odoo/odoo/tree/master/skills` — see "Official skill structure"
  below. It ships alongside whatever version `master` currently represents, so
  it will convert to a 20.0-labeled skill set automatically once the branch
  cut happens.

## Trigger plan (automated)

Two Hermes cron jobs track this from the VPS, independent of any laptop:

1. **`odoo-20-branch-watch`** (monitor-gated, runs ~daily) — polls the GitHub
   API for the `20.0` branch's existence on `odoo/odoo`. The monitor only
   wakes the agent when the branch appears (baseline tick today records
   "not yet"); once live, the agent:
   - Pulls `skills/` from the new `20.0` branch (or `master` if not yet cut).
   - Diffs it against this repo's `plugin/skills/` (`Odoo19CodingStandard`,
     `OdooTools19`, `Odoo19ExistingDependencyContext`, etc.) and the four
     official skills (`odoo-guidelines`, `odoo-review`, `odoo-security`,
     `odoo-web-guidelines`).
   - Reports the diff and a first-pass integration plan back to WhatsApp.
2. **`odoo-20-release-reminder`** (one-shot, fires 2026-09-24) — backup
   reminder in case the branch-watch monitor misses the cut (GitHub branch
   protection / rename edge cases). Prompts a full manual review regardless of
   what the monitor found.

Both jobs are VPS-side (Hermes cron), not tied to any laptop session.

## What "official Odoo skill structure" means for us

Reference (fetched 2026-09-11 from `odoo/odoo` `master`):

- `skills/odoo-guidelines/` — coding rules split into per-domain files under
  `guidelines/` (module structure, Python/ORM, fields, controllers, XML,
  access rights, performance, stable-version rules). Table-of-contents style
  `SKILL.md` that routes the agent to only the relevant guideline file instead
  of loading everything.
- `skills/odoo-review/` — review process: read `__manifest__.py` first, apply
  matching guideline sections per changed file, explicit **version-trap**
  warnings (`attrs=`, `<tree>`, `name_get`, `read_group` all removed in recent
  versions — verify against the actual checkout, never trust a remembered
  API), and a reminder that Odoo modules override each other freely
  (including enterprise/customer addons outside the diff).
- `skills/odoo-security/` — audit checklist: `sudo()`/`with_user()`/
  `with_company()` sweep, cross-model `related=` fields, `file_open()` instead
  of raw `open()`, CSRF on state-changing GET routes, XSS via `Markup`/
  `t-out`, constant-time secret comparison (`odoo.tools.consteq`).
- `skills/odoo-web-guidelines/` — JS/frontend conventions (organize by
  feature, asset handling).
- All four must be installed together (they cross-reference each other), at
  `.agents/skills/` or `.claude/skills/` at the Odoo project root, or globally
  in the harness.

## Integration plan (once 20.0 lands)

1. **Diff, don't replace.** Our skills (`Odoo17/18/19CodingStandard`,
   `OdooTools17/18/19`, `Odoo*ExistingDependencyContext`,
   `OdooRulesDriftCheck`, `OdooRestartUpgradeRules`,
   `Odoo_Custom_App_Install_Update`, etc.) cover the full custom-app lifecycle
   (planning → coding → testing → deployment → drift-check) that Odoo's
   official skills do not attempt — those four are guidelines/review/security
   only, no lifecycle commands, no MCP tools, no Docker Sandbox. Keep our
   lifecycle layer; absorb any genuinely new/changed guideline content from
   the official set into ours as version-specific update sections.
2. **Add `Odoo20CodingStandard` + `Odoo20ExistingDependencyContext` +
   `OdooTools20`**, following the exact pattern of the 19.0 set, seeded from:
   - the diffed official `odoo-guidelines`/`odoo-review`/`odoo-security`
     content for what changed 19→20, and
   - our own migration-testing pass against a real Odoo 20 sandbox
     (`odoo_local_setup/` / Docker Sandbox).
3. **Run our migration task/testing guideline** against an actual Odoo 20
   install as soon as it's installable (Docker Sandbox or local setup) —
   not just a documentation diff. Record real test results in
   `SESSION_CONTEXT.md`, same as every other phase in this repo.
4. **Update `plugin/plugin.yaml` and `plugin/skills_mapping.json`** — bump
   `tags` to include `odoo-20`, add the new skill entries, bump plugin
   version per `CHANGELOG.md` convention.
5. **Update `README.md`, `CHANGELOG.md`, `docs/commercial/delivery-roadmap.md`**
   together, per this repo's existing AGENTS.md contributor rule (never touch
   one without the others).
6. **Check Odoo Experience 2026 announcements** (Sept 24-26, Brussels) for any
   headline features that change scope beyond a pure version bump (new
   AI/agent-facing APIs, ORM changes, etc.) — fold those into the roadmap
   before committing the final Odoo 20 skill set.

## Open items / to confirm once 20.0 branch exists

- [ ] Confirm actual `20.0` branch cut date vs. this doc's estimate.
- [ ] Confirm whether Odoo's official skills changed at all between the
      2026-09-11 snapshot above and the 20.0 cut (re-diff, don't assume).
  - [ ] Pull full `guidelines/*.md` files (only `SKILL.md` table-of-contents
        was captured 2026-09-11 — the per-domain guideline files themselves
        still need a full fetch once we do the real integration pass).
- [ ] Odoo 20 install/migration test in Docker Sandbox — real run, not
      documentation-only.
- [ ] Cross-check `OdooRulesDriftCheck` catalog for new 20.0-specific drift
      patterns (new deprecated APIs, renamed fields/methods).

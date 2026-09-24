# Odoo 20.0 Migration Roadmap

Status: **released 2026-09-24 — kit support in progress (see "Release and kit support")**
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

## Branch cut detected - 2026-09-17

Detected by the `odoo-20-branch-watch` monitor (GitHub API poll on
`odoo/odoo/branches/20.0` flipped `false` (404) → `true`). Verified directly
against the GitHub API in this run, not assumed from the monitor output:

- **Branch confirmed live.** `GET /repos/odoo/odoo/branches/20.0` → HTTP 200.
  Tip commit `e264fedc` "`[REL] 20.0`" by Christophe Monniez (GitHub user
  `d-fence`), authored 2026-09-11T07:15:26Z, last updated
  2026-09-17T06:48:25Z. Branch protection is enabled (no required status
  checks configured yet). This lands inside the window this doc already
  predicted (2026-09-23 to 2026-09-26 for the public 20.0 release, branch cut
  "a few days before").
- **`skills/` directory present on `20.0`**, same structure as `master`:
  `README.md` + `odoo-guidelines/`, `odoo-review/`, `odoo-security/`,
  `odoo-web-guidelines/`.
- **Content diff vs. `master`: byte-identical.** Fetched
  `skills/*/SKILL.md` from `20.0` and diffed against the same paths on
  `master` right now — zero differences across all four files. This confirms
  the roadmap's assumption above ("it will convert to a 20.0-labeled skill
  set automatically once the branch cut happens") held exactly: nothing
  skill-specific changed at cut time, only the branch label.
- **Content diff vs. the 2026-09-11 snapshot referenced earlier in this doc:
  unchanged.** The table-of-contents structure, guideline routing tables,
  review process (manifest-first, sibling-skill dispatch, version-trap
  warnings), security sweep checklist (`sudo()`/`with_user()`/`with_company()`,
  SQL/domain injection, CSRF, XSS via `Markup`/`t-out`, `consteq`), and web
  guidelines (organize-by-feature, SCSS/assets) all read the same as what was
  already documented in the "What official Odoo skill structure means for us"
  section above. No new guideline files, no removed sections, no renamed
  skills.
- **`19.0` branch has no `skills/` directory at all** (`404` on
  `skills/*/SKILL.md?ref=19.0`) — confirms the official agent-skills library
  is new since 19.0 shipped and only exists on `master`/`20.0` today; there is
  no 19.0-vs-20.0 skill diff to draw from upstream, only master-vs-20.0 (which
  is empty, per above).
- **Local repo state:** `/home/ubuntu/workspace/odoo-agent-pro-kit` was
  already up to date with `origin/main` (`9bd1d64`) before this run, no pull
  needed. `plugin/skills/Odoo19CodingStandard`, `OdooTools19`, and
  `Odoo19ExistingDependencyContext` are unaffected by this cut — they still
  cover the custom-app lifecycle work (install/update/test via Docker
  Sandbox, MCP tools, drift checks) that Odoo's four official skills do not
  attempt, so the integration plan above (diff-and-absorb, don't replace)
  still applies as written.

**Next step (manual, not done in this job):** create
`Odoo20CodingStandard` + `OdooTools20` + `Odoo20ExistingDependencyContext`
following the 19.0 pattern, seeded from the (unchanged) official guideline
content above plus a real Docker Sandbox install/migration test against
Odoo 20 once it is installable. This needs a dedicated session, not an
unattended cron run.

## Release and kit support - 2026-09-24

- Odoo 20 released at Odoo Experience; official notes public 2026-09-24T08:30Z at
  https://www.odoo.com/odoo-20-release-notes. Community `20.0` @
  `d3236ca5c7052e892a097b007c38b9501888e406` (`version_info = (20, 0, 0, FINAL, 0, '')`),
  docs `20.0` @ `0f2e25d99173e62198e73eb2efa047922bc11679`. No `20.0` git tag yet.
- `skills/` unchanged since `21764715` (2026-09-22); still byte-identical in structure to the
  2026-09-11 snapshot above.

### Decision: defer, don't duplicate
Odoo's own `skills/` (guidelines, review, security, web) are the source of truth for Odoo 20
review and coding rules. The kit keeps what they don't do: lifecycle commands, Docker Sandbox,
install/upgrade/test runners, rules-drift, MCP discovery, KB tools, and version-aware hooks.

### Code-verified 19 → 20 breaking changes (kit coverage)
| Change | Evidence | Kit |
|---|---|---|
| `ir.model.access` + `ir.rule` → `ir.access` (`security/ir.access.csv`: `id,name,model_id,group_id/id,operation,domain`; `kind` = permission if group else restriction) | `odoo/addons/base/models/ir_access.py`; official rewriter `odoo/upgrade_code/19.4-00-ir-access.py` | L7/L8 block; `Odoo20CodingStandard` |
| `mail.tracking.value` / `tracking_value_ids` moved to `mail_tracking` | `addons/mail_tracking/` | L9 warn |
| Font Awesome → Material Symbols in web client | `addons/web/static/src/libs/materialsymbols/` | L10 warn |
| `/xmlrpc`, `/jsonrpc` deprecated (removal in 22); JSON-2 `/json/2/<model>/<method>` | `addons/rpc/controllers/` | `OdooTools20`; MCP uses JSON-RPC 2.0 for 19–20 |
| `BaseModel.toggle_active` and `boolean_button` widget removed | `odoo/orm/models.py` (only `action_archive`/`action_unarchive`) | L11 block — found in live migration |
| `t-esc` forbidden in view arch | `odoo/addons/base/models/ir_ui_view.py` allowed owl directives | L12 block — found in live migration |
| `Registry._init` removed | `odoo/orm/registry.py` | L13 block — found in live migration |
| Kanban cards split into a `card` view (`card_id`) | `project.view_task_card` etc. (7 standard kanbans) | `Odoo20CodingStandard` (no lint) |
| Manifest `19.0.x` → silently not installable | module loader | `OdooTools20` |

### Backward-version support policy
- 17.0, 18.0, 19.0 remain fully supported; all existing tests still pass and every 17–19 lint
  severity is unchanged (asserted in `tests/hooks/test_odoo20_support.py`).
- Migration paths: run the needed `odoo-bin upgrade_code --script …` one by one (`--from 19.0`
  can abort in `19.3-00-account-groups`), bump the manifest to `20.0.x`, lint at 20, fix L11–L13
  and card-view inheritance by hand, then install + test against a 19.0 baseline.

### Remaining (not done)
- [ ] Docker Sandbox 20.0: blocked on an official `odoo:20.0` image (Docker Hub shows 17/18/19
      only on 2026-09-24). Then: pin digest, add `versions.yaml` 20 entry + Dockerfile, extend
      schema enum and `lifecycle.sh`, run the Phase-7 acceptance on the Ubuntu KVM host.
- [x] Real install/migration test of custom modules on Odoo 20 (2026-09-24; see `SESSION_CONTEXT.md`).
- [ ] `OdooRulesDriftCheck` catalogue entries for L7–L13.
- [ ] `knowledge-20` OKF bundle (DSH/Hermes `odoo_kb_*` tools have no 20 KB yet).

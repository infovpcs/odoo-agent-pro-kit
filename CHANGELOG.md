# Changelog

All notable changes to `odoo-agent-pro-kit` are documented here. Versions
track the `plugin/.claude-plugin/plugin.json` `version` field.

## Unreleased

### Added

- **DeepSeek Harness (DSH) integration** — `integrations/deepseek/` ships an
  agent preset that gives a DSH session the same Odoo 17/18/19 lifecycle the
  Claude Code and Hermes plugins provide:
  - `preset/agent.cordis.yml` — the shipped `standard` coding agent plus one
    `odoo-kit` row. Every service-owning group (`planning`, `compaction`,
    `delegation`) keeps the entry-local `isolate` realm the loader requires;
    `odoo-kit` registers only into the scoped `tools`, `commands`, `skills`,
    and `systemPrompt` registries, so it sits loose with no realm.
  - `preset/odoo-kit.mjs` — a plain-ESM Cordis plugin using `node:` builtins
    only (a user preset under `$DSH_HOME/.agent-presets` cannot resolve the
    harness's own packages). It registers:
    - the five lifecycle commands, each reading its `plugin/commands/*.md`
      body and submitting it as a model-visible user message through
      `agent.followup`;
    - all 22 bundled skills, renamed to DSH's kebab-case skill grammar
      (`odoo_17_coding_standard` → `odoo-17-coding-standard`), because
      `dsh-skill-filesystem` silently drops underscore names;
    - 7 in-process `odoo_*` model-discovery tools over JSON-RPC-2.0 with one
      pooled session per version, plus a JSON-RPC fallback from Odoo's
      renamed `common.login` to `common.authenticate`;
    - 3 `odoo_kb_*` tools that search and read the per-version OKF knowledge
      bundles offline, path-contained to the bundle root;
    - `odoo_workspace_info`, reporting the detected version/module/sandbox
      session and the resolved knowledge bases and connections;
    - a lifecycle prompt section, and a `tools.guard` re-implementing the
      `plugin/hooks/checks/guard.py` refusals (raw `odoo-bin`, direct
      `manage_modules.sh`, VCS writes, destructive cleanup, and writes into an
      Enterprise source tree). It honours exactly the Python hooks'
      authorizations: `ODOO_KIT_ALLOW_RAW_ODOO` / `ODOO_KIT_ALLOW_VCS_WRITE`
      with the same truthy spellings (`1`/`true`/`yes`/`on`), plus a
      `.sandbox/AUTHORIZED` marker read per tool call. The contributor hook's
      `AGENTS_PHASE_AUTHORIZED` is deliberately not consulted — a contributor's
      exported shell must not disable an agent session's guard.
  - `install.sh` — copies the preset into `${DSH_HOME:-$HOME/.dsh}/.agent-presets/`,
    records the checkout path in `kit-root.txt`, reports which knowledge
    bundles were found, and supports `--dry-run` and `--uninstall`.
  - `tests/plugin.test.mjs` — drives `apply()` against a recording stub of the
    Cordis context and asserts the registered command/skill/tool catalog, the
    guard's allow/deny decisions, and a real knowledge-base round-trip.
  - `tests/test_deepseek_integration.py` — preset shape, realm placement,
    installer contract, and documentation-link checks, wired into
    `./scripts/validate.sh`.

### Fixed

- **The DSH tools ignored the workspace `.env`.** `odoo_workspace_info` reported
  every connection as `credentials_present: false` in a workspace whose `.env`
  already carried `ODOO_URL` / `ODOO_DB_NAME` / `ODOO17_*` / `ODOO18_*` — the
  plugin read only `process.env`, while the Python/Hermes path loads `.env` via
  `python-dotenv`. The harness process's cwd is the harness's own, so the
  connection is now resolved **per tool call** from the calling agent's
  workspace: `.env` files are found by walking up from that workspace (five
  levels, matching `python-dotenv`'s upward search) with the kit checkout as a
  final fallback, cached per file by mtime, and merged under the process
  environment with the row's own `config.odoo` on top — the same precedence
  `plugin/odoo_mcp/config.py` uses. `DEFAULT_ODOO_VERSION` in a `.env` now
  selects the default version. A malformed line is skipped rather than failing
  the call, and no password value reaches tool output.

- **A re-installed preset kept running the old plugin.** After the schema fix
  above was installed, a *new* session still failed with the identical error.
  Two independent harness behaviours were responsible, neither visible from the
  filesystem:
  1. The preset roster decides whether its standing mount is current by
     stamping **only `agent.cordis.yml`** (mtime + size). `odoo-kit.mjs` is a
     separate file, so editing it left the stamp identical and `ensureStanding`
     served the already-mounted generation to every later session.
  2. `EntryTree.import()` hands a row's specifier to Node's ESM loader with no
     cache-busting query, so even a fresh mount resolves to the module Node
     already evaluated in that process.

  `install.sh` now rewrites the plugin row to a content-addressed specifier
  (`name: ./odoo-kit.mjs?v=<sha256-12>`), which addresses both at once: the
  composition file changes (new stamp → next session re-mounts) and the module
  URL changes (→ Node imports the new code). `?v=` does not confuse the roster's
  health check, because `fileURLToPath()` strips the query. The repo's own
  composition stays clean at `./odoo-kit.mjs`; only installs are versioned.
  `INSTALL.md` gained an "Updating an installed preset" section, and
  `tests/test_deepseek_integration.py` now asserts the installed row is
  content-addressed, still resolves to a real file, and is reproducible across
  reinstalls.

- **DSH tools rejected by the model provider — `required: true` in the parameter
  schemas.** Every real turn on the DeepSeek Harness preset failed with
  `Invalid schema for function 'odoo_get_fields': true is not of type "array"`.
  The tool parameters were written in `defineTool`'s *spec* dialect (a boolean
  `required: true` on a property) but handed straight to `ctx.tools.register`,
  which takes already-converted raw JSON Schema, where `required` is an array of
  property names at the object level. DSH's own subset checker accepts the
  boolean form, so the preset mount-validated clean and the defect only appeared
  when the schemas reached the provider. `integrations/deepseek/preset/odoo-kit.mjs`
  now uses pure JSON Schema for all 11 tools, and
  `integrations/deepseek/tests/plugin.test.mjs` gained a strict-JSON-Schema
  validator that fails on any non-array `required`, naming the offending tool and
  property — the exact shape of the reported error.

- **Undeclared Python test dependencies.** `tests/test_deepseek_integration.py`
  made PyYAML a real test dependency, but nothing declared it, so
  `./scripts/validate.sh` silently required every contributor's virtualenv to
  already have it. `pytest` was in the same position. Both are now pinned in a
  new root `requirements-dev.txt` (the shipped plugin, hooks, and MCP server
  still need neither), the validation entrypoint preflights them and fails with
  the install command instead of failing part-way through the suite, and CI
  installs the file and actually runs the test suite — it previously ran only
  the skill validator and unittest module. `tests/test_dev_dependencies.py`
  derives the real dependency set from the source with `ast`, so adding an
  import without declaring it fails the suite and names the importing file.

- **Three DSH discovery tools failed every call with `value is not lossless
  JSON`.** `odoo_get_fields`, `odoo_validate_field`, and `odoo_workspace_info`
  were unusable against a live database, and failed identically for *every*
  model and field — which read exactly like a connection fault rather than a
  serialization one. The cause sat in the tool bodies: DSH snapshots each tool's
  returned value into lossless JSON and rejects the call outright
  (`snapshotToolValue` → `tool returned invalid output: value is not lossless
  JSON`) when any member is `undefined`. Odoo's `fields_get` returns only the
  attributes a field actually declares, so requesting `relation`/`help` yields
  an **absent** key for every scalar field, and `fieldList()` passed that
  absence straight through as a present-but-`undefined` property.
  `detectWorkspace()` carried the same defect for an absent
  `.sandbox/session.json` member; `odoo_get_model_info` (a model with no
  `ir.model` row) and `odoo_get_version_info` (an unreadable `latest_version`,
  or no configured user) held it latently. Every optional attribute now
  collapses to `null`.

  `integrations/deepseek/tests/plugin.test.mjs` gains regression checks that
  reproduce DSH's seam directly — an `undefined` walk plus a
  `JSON.parse(JSON.stringify(v))` round-trip assertion — for all three tools,
  driving the real code path through a stubbed `fetch`. The existing suite had
  missed this because it called `execute()` and inspected the returned object
  in-process, never crossing the boundary that was rejecting it. The new checks
  were verified to fail on the pre-fix preset at exactly the three diagnosed
  sites (`$.fields[0].relation`, `$.field.help`, `$.detected.module`).

- **`manage_modules.sh start` never managed the MCP server.** Every `start`
  printed `⚠️ MCP Server script not found, skipping automation`, even in a
  workspace whose `.gemini/AgentSkills/odoo_mcp/start_mcp_server.sh` existed and
  was byte-identical to the kit's. `setup_environment()` `cd`s into `$ODOO_DIR`
  during `start`, and `resolve_mcp_script()` ran *after* that with
  `PROJECT_DIR="$WORKSPACE_PATH"`, where `WORKSPACE_PATH` defaults to `"."`. By
  then every relative candidate resolved from `<workspace>/19.0` instead of the
  workspace root, so all six paths failed, and the script the kit actually ships
  under `${ODOO_AGENT_PRO_KIT_HOME}/plugin/odoo_mcp/` was reachable only when
  that variable happened to be exported — it is not read from `.env`.
  `WORKSPACE_PATH` is now anchored to an absolute path at the top of the script,
  while the working directory is still the invocation directory, and the
  log-directory guard compares against `$SCRIPT_DIR` so its intent — log beside
  the script when the workspace was not set explicitly — is preserved. The
  configuration header now reports the absolute workspace path instead of `.`.

- **`manage_modules.sh` targeted the wrong database in a tenant workspace.**
  `DATABASE` defaulted to `odoo${ODOO_VERSION}`, and the script never sources the
  workspace `.env`, so an install/update from `aptus_19ent`, `autopack_19ent`, or
  `globalcadtech_19ent` built `./odoo-bin -c config/odoo.conf.19 -d odoo19` —
  against a config whose only database selector is `dbfilter = ^aptus19ent$` and
  which pins no `db_name` at all. The run either failed on that filter or pointed
  the module operations at the shared `odoo19` database. The configuration header
  made it visible by printing `Database: odoo19` in a workspace named for a
  different tenant — and reading it as harmless was the trap.

  `DATABASE` now resolves as shell environment, then the workspace `.env`, then
  the version default, so a tenant workspace reports and operates on its own
  database. A new `get_env_file_value()` helper reads one key from `.env` without
  sourcing it — the file carries secrets and is not written to be evaluated as
  shell — handling the `export` prefix, single/double quotes, and trailing `#`
  comments, and always succeeding so a missing file or key can sit directly
  inside a `${VAR:-…}` default. `17`/`18`/`19` are unchanged in practice because
  their `.env` database equals the `odooNN` default; `ODOO_DB_NAME` exported in
  the shell still outranks the file.

## 0.6.0 — 2026-09-03

### Added

- **`/rules-check-drift` command + `OdooRulesDriftCheck` skill** — audits whether
  the project's rules files (`CLAUDE.md`, `AGENTS.md`, `GEMINI.md`,
  `.github/copilot-instructions.md`) still match the code after recent changes.
  Adapted from the upstream generic `rules-check-drift` skill
  (github.com/coleam00/skills, MIT) and extended for Odoo:
  - **Four drift classes** instead of three — the fourth is *gate-state
    contradiction*, where a phase/status table claims Complete while
    `docs/tasks.md` still has open `[ ]` items. `tasks.md` always wins.
  - **Odoo drift catalog** — script paths, model/`_name` renames, dropped
    fields, `__manifest__.py` depends, version idiom (`<tree>` vs `<list>`,
    `attrs=`), MCP ports, database/instance keys, external and `view_id`
    records, and pruned backup/run identifiers.
  - **Rules-file divergence check** — catches the case where the
    context-handoff guard wrote all four rules files but only one was later
    updated by hand.
  - **Optional Tier 2 database confirmation** through the in-process
    `odoo_search_models` / `odoo_get_fields` / `odoo_validate_field` /
    `odoo_get_relationships` tools. No connection means `tier: static-only`
    with the unverified claims listed — never a failure, and it never starts a
    server.
  - Advisory and read-only: it never marks a task `[x]`, never edits a progress
    percentage, and never writes to an Odoo database. No prerequisite gate.
  - `plugin/skills/OdooRulesDriftCheck/SKILL.md`,
    `plugin/commands/rules-check-drift.md`, registered for native Hermes in
    `plugin/__init__.py`, and mirrored into
    `integrations/{cursor,antigravity,vscode}/`.
- `_make_command_handler(..., version_optional=True)` — commands that take no
  Odoo version no longer prompt the user for one.

### Fixed

- README skill and command counts were stale (claimed 18/20 skills and 4
  commands); corrected to 22 skills and 5 commands.

## 0.5.1 — 2026-08-27

Fixes from the first full live pipeline run against a real pending-migration
module (`excel_sheet_data_import`, 17.0 → 18.0, in Docker Sandbox session
`mig-excel-18`; evidence under `docs/docker-sandbox/phase-8/mig-excel-18/`).

### Changed

- **Linter rule L1 (`<tree>`) is now `block` severity on Odoo 18**, not just
  19. Recent 18.0 builds (verified on 18.0-20260810) removed `<tree>`
  entirely — it is a hard `ParseError: Invalid view type: 'tree'`, not a
  deprecation warning. `plugin/hooks/checks/odoo_lint.py`.
- **`checks/sandbox_result` now finds the results directory when the edited
  module lives outside the kit checkout.** It captures the session id from
  `sandboxctl module <session> …`, honours a new `ODOO_KIT_SANDBOX_ROOT`
  environment variable pointing at the kit checkout, and falls back to the
  newest `.sandbox/sessions/*/results/` directory. Previously the PostToolUse
  "do not mark the task complete" advisory only fired when the agent ran from
  the kit repo root.
- **`docs/architecture.excalidraw` / `.png`**: new "Deterministic pipeline
  hooks — one rule set, both runtimes" section between the Docker Sandbox
  plane and Deployment — the 7-event dispatch → shared `checks/` library →
  Claude Code (`hooks.json` → `odoo_hook.py`) and Hermes (`pre_tool_call` /
  `post_tool_call`) → block / advisory / lint outcomes. Deploy caption and
  version labels bumped to 0.5.1.

### Verified

- **`/testing` frontend phase, live.** Completed for `excel_sheet_data_import`
  against sandbox `mig-excel-18` with `agent-browser` (headless Chrome/CDP) over
  a loopback `socat` bridge — login, migrated `<list>` view, form + action
  button, CSV upload, "Imported Successfully", zero console errors. The
  `Odoo_Module_Documentation_Screenshot`, `Agent-browser-skill`, and
  `CommandingSystem/testing_workflow` skills were rewritten to this verified
  flow (named session, real login refs, `/odoo/action-…` URLs, the sandbox
  bridge, secret hygiene).
- **`/plan-analysis`, live on the Oracle Cloud VPS.** `odoo17-dev` and
  `odoo18-dev` Hermes 0.20.5 profiles, plugin 0.5.1, `doctor --ci` clean
  (7 tools / 5 hooks). Both dispatched `/plan-analysis` and produced a PRD
  artifact. Evidence: `docs/docker-sandbox/phase-8/vps-plan-analysis/`.

### Known limitations

- `/testing`'s browser flow targets `http://localhost:<port>`, but the Docker
  Sandbox publishes no port and `sandboxctl` has no `publish` verb. A one-line
  `docker run … alpine/socat` bridge on the session's compose network is the
  working stopgap (agent-browser drives it fine); a first-class
  `sandboxctl publish <session>` verb would remove the manual step.
- Hermes 0.20.5 `plugins install` blocks a reinstall from a `file://` source
  over the `allowed-tools: ["mcp-odoo:*"]` wildcard in the
  `Odoo{17,18,19}ExistingDependencyContext` skills (scan `privilege_escalation`
  false-positive). Worked around by syncing plugin content into the profile
  dirs directly; narrowing that grant is a later-release fix.

## 0.5.0 — 2026-08-27

### Added

- **Deterministic pipeline hooks** (`plugin/hooks/odoo_hook.py` +
  `plugin/hooks/checks/`): command-prerequisite gates for `/start-coding`
  (needs `docs/tasks.md`) and `/testing` (needs zero open tasks and passed
  backend tests), sandbox operation-result verification (`sandboxctl module
  … install/update/test` that did not reach `succeeded` → "do not mark the
  task complete" advisory), and `odoo-bin` / `manage_modules.sh` / VCS
  (`git push/merge/tag`) / secret / Enterprise-source guardrails. Wired into
  all Claude Code hook events (`plugin/hooks/hooks.json`) and mirrored on
  Hermes via `pre_tool_call` / `post_tool_call` (`plugin/__init__.py`) and the
  slash-command handlers. Kill switch: `ODOO_KIT_HOOKS_DISABLED=1`. VCS-write
  authorization: `ODOO_KIT_ALLOW_VCS_WRITE=1` or a `.sandbox/AUTHORIZED`
  marker. Every hook fails open (any error → exit 0).
- **Version-aware Odoo 17/18/19 coding-standard linter**
  (`plugin/hooks/checks/odoo_lint.py`, runs on `PostToolUse[Write/Edit]`).
  Only inspects `*.py` under `controllers/` or `models/` and `*.xml` under
  `views/`, `security/`, `data/`, `report/`, or `wizard/`. All rules strip
  XML comments (`<!-- … -->`) and Python `#` comments before matching. The
  shipped rules (refined during review):
  - **L1** `<tree>` view element → block on 19, warn on 18.
  - **L2** `attrs=` / `states=` on a view node → block on 19, warn on 18.
  - **L3** `type='json'` in an `@http.route` (regex has a `\b` left boundary)
    → block on 19, warn on 18.
  - **L4** `<group … expand=>` — matches **only** `expand=`, not `string=`
    (narrowed to avoid false-positives on a valid form-view `<group
    string=>`) → block on 19.
  - **L5** `res.groups` `category_id` — requires a `model="res.groups"`
    declaration within 400 characters of the `category_id` field (narrowed to
    avoid false-positives on `res.partner`'s `category_id`) → block on 19.
  - **L6** `_sql_constraints` entry whose SQL contains `CHECK(` implementing a
    value rule → warn on 17/18/19.
- Contributor-only `.claude/settings.json` + `scripts/contributor_hook.py`
  enforcing the `AGENTS.md` phase-workflow rules for people developing this
  repository (not shipped in the plugin package): session-start state banner,
  `git push/merge/tag` + destructive-cleanup block unless
  `AGENTS_PHASE_AUTHORIZED=1`, and a `git commit` block **only when**
  `.git/odoo-kit-validate.stamp` exists and is older than the newest tracked
  change (an absent stamp does not block). `./scripts/validate.sh` refreshes the
  stamp automatically on success. Read-only git subcommands (`git merge-base`,
  `git tag -l`/`--list`/`-n`, `git rebase --abort`/`--continue`/…) are not
  blocked; `.claude/settings.json` invokes the hook via `$CLAUDE_PROJECT_DIR` so
  it works regardless of the hook's cwd.
- `scripts/validate.sh` now `py_compile`s every new hook module and runs a
  hook smoke test (each event with an empty payload must exit 0) plus a
  `hooks.json` / `.claude/settings.json` JSON parse check.

### Changed

- MCP process cleanup moved from the `Stop` hook to `SessionEnd`
  (`cleanup_mcp.sh` logic folded into `odoo_hook.py SessionEnd`).
- Plugin version 0.4.0 → 0.5.0; `plugin/plugin.yaml` `provides_hooks` now
  lists 5 hooks (`on_session_start`, `on_session_end`, `post_api_request`,
  `pre_tool_call`, `post_tool_call`). Verified on the Oracle KVM host with
  Hermes 0.20.4 **and 0.20.5**: `hermes plugins doctor odoo-agent-pro-kit
  --ci` reports `7 tool(s), 5 hook(s)`, registration OK, zero warnings, in
  all three profiles (odoo17/18/19-dev); a live in-process `pre_tool_call`
  check blocks raw `odoo-bin` / `git push` / private-key writes and allows
  clean commands.
- `plugin/hooks/hooks.json` now nests the event map under a top-level
  `hooks` key (same shape as the `hooks` block of `settings.json`), and the
  `hooks` declaration was removed from `plugin/.claude-plugin/plugin.json`.
  Claude Code 2.1.247 auto-loads `plugin/hooks/hooks.json`; the previous
  bare top-level event map failed `claude plugin validate` and loaded with
  `Hooks (0)`, and a redundant `manifest.hooks` pointer triggered a
  "Duplicate hooks file detected" load error. Verified on the Oracle VPS
  (Claude Code 2.1.247, Node 22): `claude plugin list` → `enabled`,
  `claude plugin details` → `Hooks (7)`, and invoking the cached
  `odoo_hook.py` blocks raw `odoo-bin` (exit 2) and `/testing` with open
  tasks (exit 2).
- `.claude-plugin/marketplace.json` plugin entry bumped `0.1.0` → `0.5.0`
  to match `plugin.json`.

### Known limitations

- Linter rules **L7** (models added without a matching `ir.model.access.csv`
  row) and **L8** (action methods returning `None`) from the design spec
  (`docs/superpowers/specs/2026-08-27-odoo-pipeline-hooks-design.md` §5) are
  **not implemented** — they need multi-file / semantic context that the
  single-file linter does not have.
- Hermes `post_tool_call` cannot block, so Odoo-19 linter `block`-severity
  findings are advisory-only on Hermes (they hard-block on Claude Code).
- The design's Stop-hook context-handoff writer and the SessionEnd `sbx ls` /
  `docker ps -a` orphan assertion are not yet implemented on the Claude Code
  dispatcher (Hermes context handoff is covered by the existing
  `post_api_request` guard).
- The Hermes `pre_tool_call` block-directive shape was **verified against
  Hermes 0.20.4** and corrected: an in-process `register_hook("pre_tool_call",
  …)` callback must return `{"action": "block", "message": …}` (the
  Claude-Code `{"decision": "block", "reason": …}` shape is only translated
  for external stdout hooks, never in-process). `hermes_adapter.py` now
  returns both key pairs. The `plugin/__init__.py` wrapper also now reads the
  tool args from the `args` kwarg (Hermes' actual key), not `tool_args`.

## 0.4.0 — 2026-08-20

### Added

- **Phase 8 exit gate is now MET — the full skill-orchestrated migration
  pipeline is client-ready.** All four Deliverables and all five
  "platform/orchestration coverage" checklist items in
  `docs/docker-sandbox/tasks.md` Phase 8 are complete with real evidence:
  - Standalone Phase 8 design note (`docs/docker-sandbox/phase-8/design.md`)
    generalized to the canonical sequence, Enterprise-dependency handling,
    all reference-run summaries, and the go/no-go batching decision
    (**GO, phased/staggered**), referenced directly from
    `CommandingSystem/SKILL.md`.
  - Session-start hook detection verified for both the shell hook
    (`plugin/hooks/session_start.sh`) and the native Hermes hook
    (`_on_session_start`) across three real cases: a live Docker Sandbox
    session, a bare local Odoo-version workspace, and a genuinely empty
    directory.
  - Version→skill mapping table verified to resolve correctly for all
    three Odoo versions inside a live Docker Sandbox session.
  - `sandboxctl module` sole-entrypoint audit found and fixed a real gap:
    `OdooTools{17,18,19}/SKILL.md`'s "Tests" bullet recommended raw
    `odoo-bin --test-tags` with no caveat, unlike every other
    lifecycle-touching skill. Fixed to route through
    `sandboxctl module ... test` exclusively, with a new regression test
    (`test_odoo_tools_skills_route_test_lifecycle_through_sandboxctl`)
    enforcing it going forward.
  - `context_guard.py`'s dynamic context-usage handoff guard verified on
    both the write side (real threshold computation, real handoff write,
    real dedup on re-trigger) and the read side (a fresh, zero-context
    Hermes subagent given only the written `CLAUDE.md` — with no explicit
    skip instruction — correctly identified which completed tasks to skip
    and correctly sequenced the remaining tasks, proving the context-load
    design measurably changes agent behavior on resume).
  - Full evidence:
    `docs/docker-sandbox/phase-8/orchestration-coverage-evidence.md`.
- **Real Odoo Enterprise-dependency-module test passed twice**, once
  against an internal fixture module (`real_estate`, 17.0, ORM
  hard-failure path) and once against a real client project's module
  (`account_report_template`, depends on the real Enterprise Accounting
  app, CLI skip-with-warning path) — reproduced consistently across Odoo
  17.0/18.0/19.0 in a reverse-migration test, with zero Enterprise source
  ever fetched or mounted in any run. See
  `docs/docker-sandbox/phase-8/enterprise-dependency-evidence/` and
  `docs/docker-sandbox/phase-8/aptus-enterprise-dependency-evidence/`.

## 0.3.3 — 2026-08-20

### Fixed

- **`manage_modules.sh` no longer reports a false "succeeded" install/update
  when Odoo silently skips an unresolvable module dependency.** Odoo's
  `-i`/`-u` CLI path treats a missing dependency (e.g. an Enterprise-only
  app like `accountant`/`account_accountant`/`account_reports`) as a
  skip-with-warning, not a hard error, and still exits 0 — leaving the
  target module stuck at `ir_module_module.state == 'to install'` forever.
  The Compose executor now re-checks `module_is_installed` for the target
  module after every `install`/`update` operation and fails the structured
  operation result (`install_failed`/`update_failed`) when the module never
  actually reached `installed`. Discovered via real testing against a
  client project (`account_report_template`, depends on the real Enterprise
  Accounting app) reproduced consistently across Odoo 17.0/18.0/19.0; a new
  regression test (`test_compose_executor_fails_when_module_not_actually_installed`)
  covers it. See `docs/docker-sandbox/phase-8/aptus-enterprise-dependency-evidence/`
  for the full evidence trail.

## 0.3.2 — 2026-08-19

### Added

- **Phase 8 pilot marked complete** — the canonical 10-step skill-orchestrated
  migration pipeline ran end to end **inside a Docker Sandbox microVM** on the
  real VPCSCloud Apps Store 17.0→18.0 module `edit_remove_pricelist_rule`
  (sandbox session `phase8-pricelist-18`). Evidence is in
  `docs/docker-sandbox/phase-8/live-test.md`:
  - Step 7 (live UI): a real `KeyError<NewId>` bug was found and fixed in
    `_compute_pricelist_rule_count`, verified via a live sandboxed browser
    session.
  - Step 9 (docs): `/testing` regenerated `coverage_summary.md`,
    `static/description/index.html`, and the `CLAUDE.md`/`GEMINI.md`/
    `AGENTS.md` context-handoff files inside the sandbox.
  - Step 10 (resume): a brand-new Codex session with no continuation from the
    writing session resumed correctly from only `CLAUDE.md` +
    `docs/tasks.md`, proving the context-handoff design survives a real
    session reset.
  - `sandboxctl module ... test` exited 0 with 0 failed / 0 error of 8.
- **NewId compute pitfall documented in the coding-standard skills** —
  `Odoo17CodingStandard`, `Odoo18CodingStandard`, and `Odoo19CodingStandard`
  each gained a "Compute methods on smart-button/counter fields: guard against
  `NewId`" section: any compute that indexes a `read_group()`/`search_count()`
  result by record id must use `counts.get(record.id, 0)` (never `counts[id]`),
  or opening a brand-new unsaved form throws `KeyError: <NewId 0x...>`. This is
  the exact bug class fixed in the pilot, not a theoretical rule.
- **Architecture diagram refreshed** (`docs/architecture.excalidraw` +
  `docs/architecture.png`) — a new Phase 8 section below the Deployment
  section shows the 10-step timeline, the pilot evidence box, and the still-open
  broader exit-gate box (second sandboxed module, Enterprise-dependency case,
  timing/resource measurement, design note, go/no-go). Rendered with the
  `excalidraw-diagram` skill's Playwright/Chromium renderer and visually
  verified for no overlap or clipping.

### Documentation

- `README.md` — Phase 8 status now reads "pilot complete" with a link to
  `live-test.md`; the broader exit-gate items remain listed as open.
- `CHANGELOG.md` — this entry.

## Unreleased — Phase 8 planning

### Added

- **Phase 8: Full-coverage skill-orchestrated migration pipeline
  (client-readiness proof)** defined in `docs/docker-sandbox/tasks.md` — the
  next Docker Sandbox phase. Names the canonical 10-step skill invocation
  sequence (dependency/context intake, coding standard, `/plan-analysis`,
  install/update lifecycle rules, `/start-coding` with per-task auto-test and
  episodic context writes, backend testing, live browser evidence, frontend
  testing, `/testing` documentation regeneration, and a fresh-session
  context-handoff/reset check) that must run correctly **inside a Docker
  Sandbox microVM** using the real VPCSCloud Apps Store 17.0→18.0/19.0
  module migration backlog as the proving ground. This is the gate the kit
  must pass before it is considered ready for external client project work,
  including custom customer repositories and Odoo Enterprise dependency
  detection (never Enterprise source bundling/committal).

## 0.3.1 — 2026-08-18

### Added

- **Dynamic context-usage handoff guard** (`plugin/context_guard.py`) — a
  new `post_api_request` hook fires on real per-turn token usage (not a
  guess) for any in-progress command inside a module workspace (any command
  with `docs/tasks.md` present, not just `/start-coding`). When usage
  crosses a threshold, it writes the same `CLAUDE.md`/`GEMINI.md`/
  `AGENTS.md` episodic-context files the manual per-command writes already
  produce, then nudges the live agent to wrap up and hand off to a fresh
  session. The threshold is dynamic, not a single fixed percentage: base
  60% (configurable via `context_handoff.threshold_pct`), auto-tightened to
  50% for modules with >15 `docs/tasks.md` tasks and loosened to 65% for
  modules with ≤5 tasks, bounded to 40%-80%, and re-fires only once usage
  crosses a new 10-point bucket past the last trigger for that module. See
  `plugin/skills/CommandingSystem/context_handoff_workflow.md` "Dynamic
  Context-Usage Handoff (Phase 8)".
- Ported the previously-external `AgentSkills/auto_test/{context_writer.py,
  auto_test_runner.py}` harness (from the separate
  `Odoo_Agents_MultiSupport` workspace, only ever installed into a bootstrap
  workspace copy) into
  `plugin/skills/CommandingSystem/auto_test/` so it actually ships with
  this repository/plugin, matching what `CommandingSystem/SKILL.md` and
  `context_handoff_workflow.md` already documented as the canonical paths.
- 16 new unit tests (`tests/test_context_guard.py`) covering threshold
  scaling, task counting, usage-percentage computation, module-workspace
  detection, and an end-to-end trigger test that verifies the real
  `register(ctx)` entrypoint writes the handoff files and injects the nudge
  message. Repository suite: 73 tests passing (up from 57).

## 0.3.0 — 2026-08-18

### Added

- **Native Hermes plugin** (`plugin/plugin.yaml` + `plugin/__init__.py`) —
  `hermes plugins install infovpcs/odoo-agent-pro-kit/plugin --enable` now
  registers everything in-process, no separate MCP server/port/sidecar
  required for a Hermes session:
  - 7 `odoo_*` tools (`odoo_search_models`, `odoo_get_fields`,
    `odoo_get_relationships`, `odoo_validate_field`, `odoo_get_model_info`,
    `odoo_list_all_models`, `odoo_get_version_info`) — in-process wrappers
    around the existing `plugin/odoo_mcp/{config,connection_manager,
    model_extractor}.py` (same pooling, retry, and XML-RPC/JSON-RPC-2.0
    protocol selection as the standalone MCP server), each accepting an
    optional `version` argument.
  - 4 slash commands (`/plan-analysis`, `/start-coding`, `/testing`,
    `/fleet`) — real Hermes commands via `ctx.register_command()`, routing
    into the `odoo_commanding_system` skill exactly like the Claude Code
    command files.
  - 2 hooks — `on_session_start` (Odoo workspace / sandbox session
    detection banner, replacing `hooks/session_start.sh`) and
    `on_session_end` (closes pooled Odoo connections opened during the
    session).
  - All 20 bundled skills registered via `ctx.register_skill()`, namespaced
    as `odoo-agent-pro-kit:<skill-name>` (e.g.
    `skill_view("odoo-agent-pro-kit:CommandingSystem")`).
  - Coexists with the pre-existing Claude-Code-style manifest at
    `.claude-plugin/plugin.json` — that one is read when this `plugin/`
    directory is installed as a Claude Code plugin; `plugin.yaml` is read
    when it's installed via `hermes plugins install`.
  - Verified with `hermes plugins doctor plugin --ci` (7 tools, 2 hooks,
    4 slash commands, 20 skills, zero warnings) and a real install+enable
    cycle in an isolated `HERMES_HOME`.

## 0.2.0 — 2026-08-18

### Added

- `sandbox/mcp-sidecar/` — an additive Compose override that runs
  `plugin/odoo_mcp` as a first-class sidecar service inside an existing
  Docker Sandbox session's Compose project, so agents can reach a live,
  session-scoped Odoo MCP endpoint over SSE from the `sbx` host:
  - `odoo_mcp_sidecar.Dockerfile` — bakes the MCP server into an image
    pinned to `mcp[server]>=1.0.0,<2.0.0`.
  - `mcp.override.yaml` — registers an `mcp` Compose service,
    `restart: unless-stopped`, in the same project as `db`/`odoo`,
    connected via the internal service name `http://odoo:8069`.
  - `mcp_up.sh <session-id> [port]` — brings the sidecar up against a
    session created by `sandboxctl create`; auto-selects port
    8765/8766/8767 by Odoo version unless overridden.
  - Does not modify the pinned, phase-gated `sandbox/compose/compose.yaml`.
- `plugin/skills/OdooHermesEnvironmentSetup/SKILL.md` — a new, portable,
  end-to-end provisioning playbook for standing up any AI agent/IDE (Hermes
  profiles today; Claude Code, Cursor, Codex, Copilot by the same steps)
  for Odoo 17/18/19 custom module development on a fresh host. Covers host
  prerequisites, agent install, per-version profile/workspace setup, skill
  loading pitfalls (including the plugin security-scanner false-positive
  on this repo's Odoo dev patterns), a required Docker Sandbox LIVE TEST,
  the new MCP sidecar wiring, and a reusability verification checklist.
  Intended for reuse across customer/project-specific deployments, not
  just this repository's own development.

### Fixed

- `plugin/odoo_mcp/requirements.txt` — pinned `mcp[server]<2.0.0`. The
  previous unbounded `>=1.0.0` constraint resolved to `mcp` 2.0.0 on a
  fresh install, which removed the `mcp.server.fastmcp` submodule that
  `odoo_mcp_server.py` imports, breaking every fresh MCP server setup with
  `ModuleNotFoundError: No module named 'mcp.server.fastmcp'`.

### Documentation

- `plugin/skills/DockerSandboxOperations/SKILL.md` — added an "Expose
  odoo_mcp to a live session" section cross-referencing the new sidecar
  commands and the new environment-setup skill.
- `README.md` — documented the MCP sidecar pattern and the new setup
  skill in the components table and Docker Sandbox roadmap section.

## 0.1.0 — 2026-08-13

Initial public release: 18 Odoo skills, 4 slash commands, 3 hooks, the
`odoo_mcp` server for Odoo 17/18/19 live model discovery, local Odoo
workspace bootstrap scripts, agent context templates, six agent/IDE
integrations, and the complete Docker Sandbox Foundation (Phases 0–7:
per-session isolated Odoo + PostgreSQL microVM runtime, bounded local
concurrency, observability/recovery, and release hardening). See
`docs/docker-sandbox/tasks.md` for full phase-by-phase history.

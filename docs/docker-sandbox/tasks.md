# Docker Sandbox Delivery Tasks

Legend: `[ ]` pending, `[x]` complete. A phase cannot start until the prior
phase exit gate passes.

## Phase 0: Validate product assumptions — complete

- [x] Record the supported `sbx` version range and capture `sbx version`,
  diagnostics, template, kit, secret, policy, ports, skills, and SSH capabilities.
- [x] Create an architecture decision record for outer microVM plus inner
  Compose, clone-mode default, and local-mode compatibility.
- [x] Select and document PostgreSQL versions for Odoo 17/18/19.
- [x] Prove official Odoo image availability for amd64 and arm64 and record any
  platform exceptions.
- [x] Define Community and separately licensed Enterprise addon handling.
- [x] Approve session/result JSON schemas and resource/retention defaults.
- [x] LIVE TEST (Ubuntu 24.04 amd64): manually create a stock Codex sandbox, run an inner Compose
  hello-world service, publish a port, stop/start, export state, and remove it.

Exit gate: repository, Docker daemon, and registry checks pass on the available
macOS workstation; commands and experimental features used by the Sandbox
design are verified against pinned `sbx` on the designated Ubuntu 24.04+ KVM
validation host. An Apple Silicon macOS Sandbox run is required only for a task
that claims native macOS Sandbox support.

## Phase 1: Runtime proof of concept (Odoo 19)

- [x] Add `sandbox/compose/compose.yaml` with healthy PostgreSQL and Odoo.
- [x] Add the Odoo 19 dev image with pinned inputs and lock manifest.
- [x] Add generated config with container-safe paths and distinct DB/application
  credentials.
- [x] Bind-mount one fixture addon from the session workspace.
- [x] Add session-private DB, filestore, cache, logs, and results volumes/paths.
- [x] Add Odoo and database readiness checks with bounded timeouts.
- [x] Add basic `sandboxctl create/status/exec/logs/stop/start/destroy` commands.
- [x] Emit `session.json`, `events.jsonl`, and operation result JSON.
- [x] Add automatic diagnostic collection on failed readiness.
- [x] LIVE TEST: install, update, RPC-test, restart, export, and destroy an Odoo
  19 fixture module with no orphaned volumes.

Exit gate: a fresh Odoo 19 session passes twice from a clean state and twice
from a warm image cache.

## Phase 2: Odoo 17 and 18 matrix

- [x] Add Odoo 17 and 18 image definitions and digest locks.
- [x] Move version-specific image, protocol, dependency, and config values to
  `versions.yaml`.
- [x] Test XML-RPC paths for 17 and 18.
- [x] Validate the supported Odoo 19 RPC/API path rather than relying on a
  hard-coded version assumption.
- [x] Add per-version fixture-module install/update/CRUD tests.
- [x] Add amd64/arm64 build and runtime matrix where supported.
- [x] LIVE TEST: run 17, 18, and 19 concurrently and complete the full fixture
  lifecycle in each.

Exit gate: the same controller interface passes for all three versions.

## Phase 3: Existing kit integration — complete

- [x] Refactor `manage_modules.sh` into environment resolution, executor, and
  operation layers while retaining local mode.
- [x] Add the `compose` executor and machine-readable exit/result contract.
- [x] Update install/update decision logic to query the session database and
  isolated progress state.
- [x] Update MCP configuration for Compose service discovery and session-scoped
  endpoints.
- [x] Update SessionStart and context handoff to read `session.json`.
- [x] Update backend/frontend testing skills with sandbox command examples.
- [x] Update `/plan-analysis`, `/start-coding`, and `/testing` gates to record
  session operation results.
- [x] Add `.sandbox/` ignore rules while preserving user-authored docs/context.
- [x] LIVE TEST: execute all three lifecycle commands in an Odoo 19 Codex
  sandbox and verify install/update/log gates.

Exit gate: existing local-mode tests still pass and sandbox mode completes one
real module lifecycle without raw `odoo-bin` calls from skills.

## Phase 4: Agent templates, kits, and IDE adapters — complete

- [x] Create and validate a minimal Odoo mixin kit.
- [x] Create Codex, Claude Code, and Copilot-compatible templates/kits only where
  agent-specific packaging is required.
- [x] Add Docker Sandbox shared-skills import/setup documentation and fallback.
- [x] Add scoped secret/OAuth setup without secret-bearing `.env` files.
- [x] Add minimal network policy and policy preflight checks.
- [x] Add SSH setup and VS Code/Cursor attach documentation.
- [x] Add launch wrappers/tasks for current project integrations.
- [x] Pin kit/template artifact versions and add release packaging checks.
- [x] LIVE TEST: Codex CLI plus one SSH-attached IDE—or the explicitly approved
  `sbx exec` terminal fallback after a recorded experimental SSH probe
  failure—edit the fixture, run module tests, and retrieve correlated logs.

Platform fallback (approved 2026-08-13): Codex CLI, the fixture lifecycle,
module test, correlated logs, kit/policy preflight, and cleanup passed on the
Ubuntu KVM host. The
experimental 0.38.0 SSH endpoint completed protocol negotiation but closed at
authentication with exit 255. After a fresh login and retry reproduced it, the
user explicitly approved the validated `sbx exec` IDE-equivalent terminal
adapter. OpenCode also passed the same edit/test/log contract. See
`phase-4/live-test.md`.

Exit gate: platform differences are confined to launch/attach adapters.

## Phase 5: Local concurrency

- [x] Replace the Community `/fleet` subprocess/thread allocation with one local
  sandbox session per module task; keep shared/remote fleet scheduling in Pro.
- [x] Add normalized unique session naming and branch creation.
- [x] Add controller locks and idempotent lifecycle transitions.
- [x] Add dynamic port allocation and manifest recording.
- [x] Add maximum concurrency, CPU/memory/disk budgets, idle stop, and retention.
- [x] Aggregate status/results without granting cross-session write access.
- [x] Require commit, push, or patch export before destructive cleanup.
- [x] Add graceful cancellation and partial-failure reporting.
- [x] LIVE TEST: run six sessions (two each for 17/18/19), including two copies
  of the same module, and prove source/database/log isolation.

Exit gate: one failed session does not change or stop any sibling session.

## Phase 6: Observability and recovery

- [x] Implement unified service log streaming and filtering.
- [x] Implement redacted diagnostic bundles with Compose state, health, events,
  resources, policy diagnostics, and operation results.
- [x] Emit JUnit/coverage/browser artifacts in stable locations.
- [x] Add optional OpenTelemetry log export interface.
- [x] Add crash, denied-network, disk-pressure, invalid-module, interrupted
  operation, and controller-restart tests.
- [x] Add backup/restore for session development databases when explicitly
  requested.
- [x] LIVE TEST: inject each supported failure and confirm actionable logs,
  bounded retry, recovery/cleanup, and sibling health.

Exit gate: every failure scenario produces a redacted diagnostic bundle and a
deterministic terminal or recoverable state.

## Phase 7: Release hardening — complete

- [x] Add CI for shell/Python tests, Compose validation, kit validation, image
  builds, dependency/license inventory, and version smoke tests.
- [x] Add macOS Apple Silicon, Windows 11, and Ubuntu operator runbooks.
- [x] Add upgrade/rollback tests for template, kit, Odoo image, Postgres image,
  and session schema versions.
- [x] Measure cold/warm startup, disk growth, memory, and six-session load.
- [x] Document capacity recommendations from measured results.
- [x] Add local-to-sandbox migration and compatibility documentation.
- [x] Publish tested platform runbooks generated from the validated controller,
  Compose, template, and kit versions.
- [x] LIVE TEST: execute the release acceptance matrix from a clean host setup.

Exit gate: all requirements acceptance scenarios pass, artifacts are pinned,
and rollback plus cleanup are demonstrated.

## Phase 8: Full-coverage skill-orchestrated migration pipeline (client-readiness proof) — complete

Purpose: prove that this repository's complete skill set, dynamic context
handoff, and Docker Sandbox microVM execution model together form a mature,
client-ready pipeline for real Odoo custom-module work — using the
VPCSCloud Apps Store 17.0 -> 18.0/19.0 migration backlog as the live proving
ground, not a synthetic fixture. This phase is the bridge from "the sandbox
runs Odoo" (Phases 0-7) to "the sandbox runs a correctly sequenced,
multi-skill agent development lifecycle end to end, unattended, inside an
isolated microVM, with evidence." Only after this phase's LIVE TEST passes is
the pipeline considered proven for external client project work.

### Scope: skill sequence to validate, per migrated module

Each pilot/batch module run must exercise this exact sequence inside a Docker
Sandbox session (not the bare local workspace used for the first pilot
module), with every step's output captured as session artifacts under
`.sandbox/sessions/<session-id>/`:

1. **Dependency/context intake** — `Odoo{17,18,19}ExistingDependencyContext`
   (source version, then target version) to capture the module's real model,
   view, and cross-module dependency footprint before any edit, including
   Odoo Enterprise dependency detection where relevant.
2. **Coding standard** — `Odoo{17,18,19}CodingStandard` for the *target*
   version, applied to every ported file (manifest, models, views, security,
   data, static assets).
3. **Planning** — `PRD-Writing` + `CommandingSystem` `/plan-analysis
   {version} {module}` to produce `docs/requirements.md`, `docs/design.md`,
   `docs/tasks.md`, `docs/module_meta.md` for the port, using the intake
   context from step 1 as input (not re-derived from scratch).
4. **Install/update lifecycle** — `Odoo_Custom_App_Install_Update` +
   `OdooRestartUpgradeRules` govern every module (re)install/update/upgrade
   inside the sandbox's inner Compose Odoo instance; no ad hoc `-u`/`-i`
   flag usage outside the documented restart-vs-upgrade decision rules.
5. **Coding loop** — `CommandingSystem` `/start-coding {version} {module}`:
   per-task implementation with `auto_test_runner.py` after every task,
   `CLAUDE.md`/`GEMINI.md`/`AGENTS.md` episodic-context writes after every
   command per `context_handoff_workflow.md`, and the PASS/PARTIAL/FAIL gate
   already defined in `CommandingSystem/SKILL.md` enforced (no `[x]` without
   a passing or reviewed-PARTIAL auto-test).
6. **Backend testing** — `Odoo_Custom_Backend_Testing` against the sandboxed
   instance (ORM/ACL/constraint/report coverage as applicable to the module).
7. **Live UI evidence** — `Agent-browser-skill` (or
   `Odoo_Module_Documentation_Screenshot` where it supersedes it) drives the
   sandboxed Odoo instance's real published port to capture functional
   screenshots — replacing the ad hoc/blocked browser-login attempt from the
   local-workspace pilot with a sandbox-native, cookie/CSRF-clean session.
8. **Frontend testing** — `Odoo_Custom_Frontend_Testing` for any
   JS/OWL/QWeb-touching module.
9. **Documentation regeneration** — `CommandingSystem` `/testing {version}
   {module}` regenerates `static/description/index.html` and screenshots
   from the live sandboxed instance for the *target* version; a prior
   version's assets are reused only when explicitly confirmed UI-identical,
   never assumed.
10. **Context handoff and session reset** — verify `CLAUDE.md` reflects
    100%-complete state at the end of step 9, then start a **fresh** agent
    session/context against the same module directory and confirm it can
    resume purely from `CLAUDE.md` + `docs/tasks.md` state (proves the
    dynamic context hook/handoff design actually survives a full context
    reset, not just an in-session memory carryover).

### Scope: platform/orchestration coverage to validate

- [x] Confirm `plugin/__init__.py`'s `on_session_start` hook correctly
  detects an Odoo Sandbox workspace vs. a bare local workspace and loads the
  right skill subset without manual selection. Verified 2026-08-20 against
  both the shell hook (`plugin/hooks/session_start.sh`) and the native
  Hermes hook (`_on_session_start`) across three real cases: a live Docker
  Sandbox `session.json`, a bare local Odoo-version directory, and a
  genuinely empty directory — all three produced the correct detection
  (sandbox / local / silent no-op). See
  `docs/docker-sandbox/phase-8/orchestration-coverage-evidence.md` item 1.
- [x] Confirm the version -> skill mapping table in `CommandingSystem/
  SKILL.md` resolves correctly for all three versions inside a sandbox
  session (not just documented). Verified 2026-08-20 inside Docker Sandbox
  `phase8-orchestration-test`: all nine mapped skill directories
  (`Odoo{17,18,19}CodingStandard`, `OdooTools{17,18,19}`,
  `Odoo{17,18,19}ExistingDependencyContext`) exist and are readable from the
  sandbox's mounted repo clone. See
  `docs/docker-sandbox/phase-8/orchestration-coverage-evidence.md` item 2.
- [x] Confirm `sandbox/bin/sandboxctl module` is the sole install/update/test
  entrypoint used across the full sequence above — no direct `odoo-bin`
  calls bypass it. Audit found and fixed a real gap 2026-08-20:
  `OdooTools{17,18,19}/SKILL.md`'s "Tests" bullet recommended raw
  `odoo-bin --test-tags` with no caveat, unlike every other lifecycle skill.
  Fixed to route through `sandboxctl module ... test` exclusively, with a
  new regression test
  (`test_odoo_tools_skills_route_test_lifecycle_through_sandboxctl`)
  enforcing it going forward. See
  `docs/docker-sandbox/phase-8/orchestration-coverage-evidence.md` item 3.
- [x] Confirm session-start context load (`CLAUDE.md` read before skill
  loading, per `context_handoff_workflow.md`) actually changes agent
  behavior on a real second run of the same module (measurable: it skips
  already-completed tasks rather than re-deriving them). Verified
  2026-08-20: a brand-new, zero-context Hermes subagent, given only a real
  `context_writer.py`-format `CLAUDE.md` (2/5 tasks done, with command
  history naming the completed tasks) and `docs/tasks.md`, and with no
  explicit skip instruction, correctly named both completed tasks as
  skip-worthy (citing their auto-test pass counts) and correctly sequenced
  the three remaining tasks as next work. See
  `docs/docker-sandbox/phase-8/orchestration-coverage-evidence.md` item 5.
- [x] Confirm the dynamic context-usage handoff guard
  (`plugin/context_guard.py`, fired on the real per-turn `post_api_request`
  usage hook) actually writes `CLAUDE.md`/`GEMINI.md`/`AGENTS.md` and nudges
  the agent when usage crosses its module-size-adjusted threshold — for at
  least one step of the sequence, not only for `/start-coding` — and that a
  genuinely fresh session (new process, not the same context) resumes
  correctly from the written handoff without operator intervention.
  Verified 2026-08-20 by calling the real `maybe_handle_context_pressure`
  hook function directly with real usage data against a seeded 5-task
  module directory: correctly computed the size-adjusted threshold (65% for
  a 5-task module), triggered on 70.3% usage, wrote all three handoff files
  plus `sessions/context_handoff.json` with the accurate task/usage/trigger
  state, injected the nudge message, correctly deduped a same-bucket
  re-trigger, and — independently, via a brand-new zero-context Hermes
  subagent given only the two handoff files — correctly resumed with the
  right module/version/task-count/last-command/trigger state. See
  `docs/docker-sandbox/phase-8/orchestration-coverage-evidence.md` item 4.
- [x] Confirm the pipeline behaves correctly for a module with a real
  **Odoo Enterprise dependency** (not just Community-only modules) —
  dependency detection must flag it without ever fetching, bundling, or
  committing licensed Enterprise source. Verified 2026-08-20 inside Docker
  Sandbox `phase8-enterprise-dep-test` (Odoo 17.0, Ubuntu KVM host): ported
  `vpcs_apps_cloud_17/real_estate` (`depends: purchase, sale_subscription,
  website_crm, web_studio, sale_renting_crm` — all four non-`purchase`/
  `website_crm` deps are genuine Odoo Enterprise-only apps) into the
  session's `/mnt/extra-addons` and ran `sandboxctl module ... install`
  exclusively. Odoo's own dependency resolver failed the install with a
  structured `install_failed` operation result (exit 255) and the exact
  `UserError`: "You try to install module 'real_estate' that depends on
  module 'sale_renting_crm'. But the latter module is not available in
  your system." A redacted diagnostic bundle was captured automatically on
  failure. A post-failure `find` across the entire sandbox filesystem for
  any Enterprise module name (`sale_renting`, `sale_subscription`,
  `web_studio`) returned zero matches — no Enterprise source was ever
  fetched, mounted, or present. Evidence in
  `docs/docker-sandbox/phase-8/enterprise-dependency-evidence/`. Sandbox
  session and outer Sandbox were fully destroyed after evidence capture; no
  orphaned containers/volumes remained.

  Supplemental real-client-project evidence (2026-08-20): re-verified with
  a genuine GitHub-access client repository, `Aptusinfotech/aptus` (staging
  branch, Odoo.sh-hosted 19.0), module `account_report_template` (depends
  on the real Enterprise Accounting app `accountant`/`account_accountant`
  across the 17.0/18.0/19.0 name split). This run surfaced an additional
  real finding: `sandboxctl module ... install` returns CLI exit 0 via
  Odoo's `-i` skip-with-warning path when a dependency is missing (unlike
  the ORM `button_install()` hard-failure path exercised by the
  `real_estate` test above) — the authoritative signal is
  `ir_module_module.state`, confirmed stuck at `to install` with the
  Enterprise dependency `uninstallable`, consistently reproduced across all
  three Odoo versions (17.0/18.0/19.0) in a reverse-migration test of the
  same module, with zero Enterprise source ever fetched or mounted in any
  of the three sandbox runs. Full evidence and the CLI-exit-code caveat are
  documented in
  `docs/docker-sandbox/phase-8/aptus-enterprise-dependency-evidence/README.md`.
- [x] Measure and record wall-clock time and Sandbox resource usage for one
  full single-module run through all 10 steps, to size future batch runs
  within the Phase 7-measured host capacity limits (2-vCPU/15-GiB Oracle
  host: max ~2 constrained concurrent sessions). Recorded for
  `hr_document_report` (2026-08-19T11:06:29Z): outer/inner wall time
  58m55s/46m32s; Odoo/PostgreSQL cumulative CPU 40.197s/142.675s; memory
  peaks 245.3/255.2 MiB. See `SESSION_CONTEXT.md` "second Tier-1 module
  complete" entry.

### Deliverables

- [x] A written **Phase 8 design note**
  (`docs/docker-sandbox/phase-8/design.md`) naming the exact skill
  invocation order above as the canonical sequence, referenced from
  `CommandingSystem/SKILL.md` so it is not only documented here. Generalized
  2026-08-20 from the pilot-scoped draft to the canonical Phase 8 design
  note: full 10-step sequence, Enterprise-dependency handling (including the
  `manage_modules.sh` 0.3.3 fix), reference-run summaries for all three
  completed test runs, and the go/no-go batching decision below.
  `CommandingSystem/SKILL.md` "Phase 8" now cites it directly.
- [x] At least one Tier-1 (17.0-only) VPCSCloud Apps Store module migrated
  **inside a Docker Sandbox session** (not the bare local workspace used for
  the earlier ad hoc pilot) through the full 10-step sequence, with every
  step's artifact path recorded in `docs/docker-sandbox/phase-8/live-test.md`.
  Satisfied by `edit_remove_pricelist_rule` (17.0 -> 18.0), executed inside
  Docker Sandbox `phase8-pilot`/inner session `phase8-pricelist-18` — see
  "Progress record" below for the full 10-step evidence trail.
- [x] A second Tier-1 module, `hr_document_report` (17.0 -> 18.0), completed
  its ten-step sequence inside Docker Sandbox `phase8-hr-document-report`,
  including 6/6 backend tests, live UI/PDF evidence, frontend N/A inventory,
  documentation regeneration, resource capture, and fresh-process resume.
- [x] Confirmation that the already-completed `edit_remove_pricelist_rule`
  local-workspace pilot's outstanding gap (blocked browser screenshot) is
  closed via the sandbox-native `Agent-browser-skill` path in this phase,
  not worked around locally. Closed 2026-08-19: a real SSH-tunnel + `socat`
  browser session against the sandboxed Odoo 18 instance (`phase8-pilot`)
  captured real screenshots of the smart button and drill-through list
  (`docs/docker-sandbox/phase-8/step7-evidence/`), and in the process found
  and fixed a real `KeyError: <NewId ...>` bug — see
  `docs/docker-sandbox/phase-8/live-test.md` "Step 7 — Live UI evidence —
  COMPLETE".
- [x] A go/no-go decision, recorded in `SESSION_CONTEXT.md`, on batching the
  remaining ~45 backlog modules through this proven sequence versus doing
  targeted per-module runs, based on the measured single-module time/resource
  cost above. **Decision: GO, phased/staggered** — see
  `docs/docker-sandbox/phase-8/design.md` "Go/no-go: batching the remaining
  ~45 backlog modules" for the full rationale and recommended batching
  shape (triage pass first, then Community-only modules at ≤2 concurrent
  sandbox sessions per the Phase 7 capacity limit, Enterprise-dependent
  modules handled as a separate explicitly-flagged batch, and the four
  still-open platform/orchestration checklist items re-run before
  committing to full-scale batching).

### Progress record (2026-08-18, real evidence — see `docs/docker-sandbox/phase-8/live-test.md`)

Pilot module `edit_remove_pricelist_rule` (17.0 -> 18.0), executed inside
Docker Sandbox `phase8-pilot` (Codex agent) on the Ubuntu KVM host:

- [x] Step 1 — Dependency/context intake (static analysis; live XML-RPC/MCP
  pass not yet performed — flagged gap, not silently dropped).
- [x] Step 2 — Coding standard (0 violations against Odoo 18 standard).
- [x] Step 3 — Planning (`/plan-analysis`) — real Codex run produced
  `requirements.md`, `design.md`, `tasks.md`, `module_meta.md`; corrected a
  real bug (wrong model name) from an earlier hand-drafted plan.
- [x] Step 4 — Install/update lifecycle via `sandboxctl module ... install`
  exclusively (no raw `odoo-bin`); `Module loaded in 0.19s, 71 queries`, no
  errors.
- [x] Step 5 — Coding loop (`/start-coding`) — Codex implemented
  `models/price_list.py`, `views/price_list_view.xml`,
  `data/remove_price_list_rule.xml`; static checks passed.
- [x] Step 6 — Backend testing — Codex wrote 8 real `TransactionCase` tests;
  ran via `sandboxctl module ... test`: **0 failed, 0 error(s) of 8 tests**
  against a live Odoo 18 database, including pricing-recomputation
  correctness after rule deletion.
- [x] Step 7 — Live UI evidence: real SSH-tunnel + socat browser session
  against the sandboxed Odoo 18 instance, logged in as admin. Found and
  fixed a real bug (`KeyError: <NewId ...>` in
  `_compute_pricelist_rule_count` for unsaved records), re-ran
  `sandboxctl module ... update`/`... test` (8/8 tests still passing, no
  regression), and captured real screenshots of the smart button and the
  scoped drill-through list. Evidence in
  `docs/docker-sandbox/phase-8/step7-evidence/`.
- [x] Step 8 — Frontend testing — confirmed N/A (module has no JS/OWL/QWeb
  assets), not assumed.
- [x] Step 9 — Documentation regeneration (`/testing 18.0
  edit_remove_pricelist_rule` inside `phase8-pricelist-18`) — real Codex run
  regenerated `docs/coverage_summary.md` and
  `static/description/index.html`, plus `AGENTS.md`/`CLAUDE.md`/`GEMINI.md`
  and `sessions/context_handoff.json`. Backed by a fresh
  `sandboxctl module ... update`/`... test` pass (exit 0, 0 failed/0 error
  of 8 tests). Evidence in
  `docs/docker-sandbox/phase-8/step9-evidence/`.
- [x] Step 10 — Context handoff and fresh-session resume verification — a
  brand-new `codex exec` session, given only the module's `AGENTS.md` and
  `sessions/context_handoff.json`, correctly reported module/version, last
  command (`/testing`, 2026-08-19T07:07:47Z), `0/9` tasks, and the accurate
  outstanding-work summary with no other files read.

The finished module was synced from the sandbox to the canonical
`vpcs_apps_cloud_18` module-store repository (branch `18.0`), merging in the
pre-existing commercial manifest fields the from-scratch plan/coding steps
did not know to preserve. `./scripts/validate.sh` passed 73/73 on the local
macOS workstation after the sync.

All 10 pilot-module sequence steps are now complete with real evidence (see
`docs/docker-sandbox/phase-8/live-test.md` for steps 7, 9, 10). **This is
still not a PASS of the exit gate below** — the exit gate additionally
requires the broader "Scope: platform/orchestration coverage to validate"
and "Deliverables" checklist items above (a second Tier-1 module migrated
inside a Docker Sandbox session, an Enterprise-dependency module test,
wall-clock/resource timing, the standalone Phase 8 design note, and the
go/no-go batching decision), none of which are complete yet. Also resolved
along the way: the Codex sandbox's OAuth token was expired at session start;
fixed via a host-level `sbx secret set openai --oauth` re-authentication
(see `plugin/skills/DockerSandboxMultiCliAdapter/SKILL.md` for the exact
reusable procedure, including the SSH port-forward workaround for the OAuth
callback on a remote VPS).

### LIVE TEST (Ubuntu 24.04+ KVM validation host)

Run one full pilot module through all 10 sequence steps end-to-end inside a
real Docker Sandbox session on the designated Ubuntu KVM host, using the
live-verified Hermes + `openrouter/free`/Hetzner fallback inference chain
(already proven 2026-08-18 for `/plan-analysis`). A failed or skipped step,
or any step that falls back to bare local execution instead of the sandbox
controller, is a blocker — not a pass. Record exact commands, artifact
paths, timings, and any deviation from the documented sequence.

Second-module result (2026-08-19): `hr_document_report` was migrated and
installed successfully in Odoo 18 session `phase8-hr-document-report` through
`sandboxctl module` (exit 0, 43.069s). Update passed in 17.675s wall time;
the final 6-test TransactionCase suite passed with `0 failed, 0 error(s)` in
17.624s wall time; and both standalone (9,050 bytes) and company-layout
(24,160 bytes) final live PDF routes returned HTTP 200. Clean `.venv` validation
passed 73/73, and `/testing` regenerated the coverage summary and description.
The live browser confirmed two configurations, two employee assignments,
working PDF buttons, and literal/non-executing script text. The final manifest
declares `LGPL-3`; frontend testing is N/A by inventory. `/testing` regenerated
the documentation/handoff, closeout resource counters were captured, and a
brand-new Codex process resumed accurately from only `module_meta.md` and
`context_handoff.json`. This closes the second-module deliverable.
See `vpcs_apps_cloud_18/hr_document_report/docs/implementation_evidence.md`.

Final clean-shell `./scripts/validate.sh`: 73 tests passed in 1.00s, 21 skills
validated, and artifact/contracts/rollback, Compose, shell, Python, and
whitespace checks passed. Live `sbx` kit validation was skipped because `sbx`
is unavailable inside this sandbox process.

**The full Phase 8 exit gate is now MET (2026-08-20)**: all four Deliverables
are complete (design note, first sandbox-native Tier-1 module, second
Tier-1 module, browser-evidence gap closure, and the go/no-go batching
decision), and all five "platform/orchestration coverage" checklist items
are verified with real evidence — session-start hook detection (both shell
and native hook, three real cases), version→skill mapping resolution
(inside a live sandbox session), `sandboxctl module` sole-entrypoint audit
(found and fixed a real gap in `OdooTools{17,18,19}/SKILL.md`), the
`context_guard.py` live-usage-hook write path (real threshold computation,
real handoff write, real dedup), and the session-start context-load read
path (a fresh subagent measurably skipped completed work based purely on
`CLAUDE.md`, with no explicit instruction to do so). See
`docs/docker-sandbox/phase-8/orchestration-coverage-evidence.md` for full
evidence on all five items.

Exit gate: one full pilot module passes the sequence above with recorded
evidence for every step, the dynamic context handoff/session-reset check in
step 10 is independently verified (not self-reported by the same
uninterrupted session), and the go/no-go batching decision is recorded.
**MET.**

## Phase 9: Docker Cloud Sandbox runtime (Odoo 17/18/19) — complete

Cloud Sandboxes run the same microVM isolation on Docker-managed compute (`sbx --cloud`,
`sbx` ≥ 0.45.1). The maintainer workstation is Intel macOS, where the `sbx` cask and every macOS
binary are arm64-only, so the client is the official linux/amd64 `sbx` in a local container image
(`sbx-cloud:0.45.1`). Evidence: `SESSION_CONTEXT.md` "Phase 9 probe" and "Phase 9 run mode".

- [x] Cloud-only `sbx` client on Intel macOS (checksum = SLSA provenance), owner device login.
- [x] Probe: medium amd64 sandbox + `odoo-mixin`; found `docker exec` into running containers
      broken in cloud (health checks never pass), Docker Hub blob host missing from the allowlist,
      GitHub clone blocked without a cloud credential.
- [x] `SANDBOX_EXEC_MODE=run` executor in `sandboxctl` and `manage_modules.sh`: every exec →
      `compose run --rm --no-deps`, health-check waits → network probes from one-shot containers,
      `pg_dump`/`pg_restore` via a one-shot client (password only in env); recorded in
      `runtime.env` at create; `exec` mode unchanged. Tests: `tests/test_phase9_cloud_exec.py`.
- [x] `odoo-mixin` 0.5.2: allow `production.cloudfront.docker.com`; `artifacts.lock` bumped;
      `upgrade-rollback.py` derives the kit version from the lock.
- [x] Live Odoo 19 cloud run with the kit's own controller: create, module install, module test,
      backup, restore, stop, start, status, export, destroy — PASS.
- [x] `exec` fixture CRUD in run mode: failed `lifecycle_marker == "updated"` because the live
      script skipped `lifecycle.sh`'s fixture update step. Make `sandbox/tests/lifecycle.sh`
      run-mode aware (its direct `compose run`/`stop`/`start` calls need `--no-deps` and network
      readiness) and re-run.
      Code done 2026-09-25: `lifecycle.sh` reads `SANDBOX_EXEC_MODE` from the session's
      `runtime.env` (`--no-deps` runs, `up -d --no-deps odoo`, probe via `ODOO_URL`) and takes
      `SANDBOX_LIFECYCLE_VERSIONS`; tests in `tests/test_phase9_cloud_exec.py`. Live Odoo 19 cloud `lifecycle.sh` run mode: PASS
      (42 s, sandbox lived ~4 min medium); long runs need `setsid nohup` under `sbx --cloud exec`.
- [x] Phase-7 acceptance matrix for 17, 18 and 19 in cloud (concurrent sessions in one `large`
      sandbox or one `medium` sandbox per version); record wall-clock and cost per run.
      Step 2 PASS 2026-09-25: concurrent 17/18/19 `lifecycle.sh` in one `large` sandbox, 117 s,
      sandbox lived ~3.5 min. Steps 1, 3, 4, 5, 6, 8 PASS 2026-09-25 via
      `sandbox/tests/phase9-cloud-acceptance.sh` (large, ~9 min; step 5 after a driver fix).
      Step 7 (agent CLIs/SSH) deferred to Phase 10 by the owner (2026-09-25).
- [~] `/plan-analysis` → `/start-coding` → `/testing` with hooks inside a cloud sandbox — deferred
      to Phase 10 by the owner (2026-09-25), to run with the 19→20 custom-app migration.
- [~] `/fleet` with three cloud sandboxes (`sandbox-fleet` cloud allocation) — deferred to Phase 10
      by the owner (2026-09-25).
- [x] Code delivery: documented `git archive` / working-tree tar + `sbx --cloud cp` (runbook).
      The stored cloud `github` secret is invalid (401); replacing it is an owner action tracked
      in Phase 10.
- [x] Decide the `sbx_version` contract: `artifacts.lock` pins `0.38.x` (local KVM); cloud needs
      ≥ 0.45.1. Decided 2026-09-25: keep `sbx_version` 0.38.x, add `sbx_cloud_version` 0.45.x
      (validated 0.45.1); `release-acceptance.py compare` reports both.
- [x] Cloud runbook (`docs/docker-sandbox/phase-9/`), `DockerSandboxOperations` skill, README,
      and an `AGENTS.md` amendment accepting Cloud Sandboxes as a runtime LIVE TEST host.
      Drafted 2026-09-25 (uncommitted): `phase-9/cloud-runbook.md`, skill section, README +
      `sandbox/README.md` + docs index + Phase 7 runbook pointers, `AGENTS.md` rule 3 amendment —
      `AGENTS.md` wording approved by the owner 2026-09-25.
- [x] `./scripts/validate.sh`, SESSION_CONTEXT evidence, one focused commit. macOS 313 passed;
      Ubuntu 24.04 VPS (`sbx` 0.38.0) 311 passed + 2 unrelated `pydantic` skips, kit validation ran.

Exit gate: Odoo 17/18/19 acceptance passes in Docker Cloud Sandboxes through `sandboxctl` in
run mode, local `exec` mode is unchanged (full suite green), costs are recorded. Items marked
`[~]` were moved to Phase 10 by the owner and do not block this gate.

## Phase 10: Odoo 20.0 sandbox runtime — complete (2026-09-28)

- [x] Odoo 20 image: `odoo/docker` published `20.0/` on 2026-09-26 (`d543160420`: ubuntu:noble,
      nightly deb `20260926` sha1-pinned, wkhtmltopdf 0.12.6.1-3, pgdg `postgresql-client`), but
      Docker Hub has no `odoo:20.0` tag yet. Build the base from that commit, layer
      `sandbox/images/odoo-dev/20.Dockerfile`, record the digest in `images.lock`; switch to the
      official `odoo:20.0` digest once Hub publishes it.
      Done: `20.Dockerfile` reproduces the recipe on `ODOO_20_BASE` = pinned `ubuntu:noble` digest
      (helper files sha256-checked; pgdg key over HTTPS + fingerprint check because dirmngr fails
      in sbx microVMs). Built on macOS and in a kit-backed KVM microVM. Hub re-checked 2026-09-27:
      still no `odoo:20.0`.
- [x] `POSTGRES_16` lock (Odoo 20 `MIN_PG_VERSION = 16`), `versions.yaml` 20 entry,
      `20.Dockerfile`, schema enum, `lifecycle.sh`/`ci-smoke.sh`/`multiarch-build.sh`,
      `sandbox-fleet`, release workflow matrix, `/fleet` accepts 20.
      Also: fixture overlay (`ir.access`), `set_str` fallback, `http_interface = 0.0.0.0`, PDF
      render step in `lifecycle.sh`, kit 0.6.0 (Odoo 20 build egress). 364 tests pass.
- [x] MCP sidecar for 20: create a scope-`rpc` API key in the session database and pass it as
      `ODOO_API_KEY` so `odoo_mcp` uses `/json/2` (the sidecar still sends a password today).
      Done: `create` already generates the key for json2 series; the override passes it; port 8768.
      Live on macOS: `protocol=json-2`, real query returned the fixture record, SSE 200.
- [x] LIVE TEST (local exec mode): `ci-smoke.sh 20` + concurrent `lifecycle.sh` 17/18/19/20 on
      macOS Docker Desktop 29.8.0 (rc 0, 225 s); `ci-smoke.sh 20` in a kit-backed microVM on the
      Ubuntu 24.04 KVM host (rc 0, 425 s). `lifecycle.sh` 20 was not run on KVM (host disk);
      the owner moved it to Docker Cloud Sandboxes (2026-09-27).
- [x] LIVE TEST (cloud run mode, owner approved spend 2026-09-27): `SANDBOX_EXEC_MODE=run
      SANDBOX_LIFECYCLE_VERSIONS=20 lifecycle.sh` (rc 0, 278 s incl. the cold 20 image build),
      then `phase9-cloud-acceptance.sh` extended to 20 (warm create 20, two 20 sessions in the
      concurrent step): all 16 steps PASS, rc 0, 439 s. One large sandbox, 14:44–15:16 UTC.
- [x] Module Python requirements + real-module import: `sandboxctl create --import DIR
      --requirements FILE` (validated PyPI lines, venv overlay layer, freeze recorded), kit 0.7.0
      allows `pypi.org`/`files.pythonhosted.org`. LIVE: real `vpcs_llm_provider` installs on 19;
      19 baseline 3F/16E of 34 reproduced.
- [x] `docs/docker-sandbox/phase-10/live-test.md`, CHANGELOG entry, runbook/README updates,
      contributor-hook hint fix (2026-09-28). The implementation landed as `595c2ca`.
- [x] Re-run the 19→20 migration of `vpcs_llm_provider` + `vpcs_progressive_payment_terms`
      inside a sandbox; Phase-7 acceptance for 20. 2026-09-28, cloud: both install on 20;
      2F+2E of 8 and 0F+14E of 26 = the same named tests as the 19 baseline re-run in the same
      sandbox (one 19 failure now passes). Evidence: `phase-10/live-test.md`.
- [x] Carried over from Phase 9 (owner decision 2026-09-25), run together with the 19→20
      custom-app migration once the Odoo 20 image is ready:
  - [x] Phase-7 acceptance step 7 in cloud: Codex + one more agent CLI via the stored cloud
        `anthropic`/`openai` secrets (untested), SSH probe or the approved `sbx exec` fallback.
        2026-09-28: Claude Code (workspace-scoped key) `CLAUDE-OK`; Codex on the owner's ChatGPT
        OAuth secret in a `codex` template `CODEX-OK`; `sbx exec` fallback.
  - [x] `/plan-analysis` → `/start-coding` → `/testing` with hooks inside a cloud sandbox,
        driving the migration task. 2026-09-28: the first run's `/testing` was blocked by the
        gate; the root cause was a prose `tasks.md` plus no recorded outcome. The kit was fixed
        (checklist gate, baseline-parity record, Stop enforcement), and the re-run passed every
        gate.
  - [x] `/fleet` cloud allocation in `sandbox-fleet` (code shipped by archive, `sbx --cloud ports`
        gives a public URL — owner to decide public exposure vs internal-only) with three
        cloud sandboxes.
  - [x] Owner: replace the invalid cloud `github` secret — done 2026-09-25; API calls
        authenticate (`infovpcs`).
  - [x] Git over HTTPS in cloud still fails with the valid secret (`invalid credentials`);
        find the supported clone path before replacing tar + `sbx cp`. 2026-09-28: once the
        owner gave the fine-grained token private-repo access, plain private `git clone` passed
        in the `claude` and `codex` templates. The `shell` template still gets 401, a
        recorded limit.
  - Done 2026-09-27: `sandbox-fleet create --cloud` (internal-only by owner decision, no
    `sbx ports`); 3 cloud sessions 20/19/18 created, fixture test rc 0, destroyed.
  - Blocked 2026-09-27, resolved 2026-09-28: step 7 + command loop — cloud `anthropic` secret
    was not workspace-scoped (API 400); Codex needs a `codex`-template sandbox.
  - Exit gate passed 2026-09-28; evidence in `phase-10/live-test.md`.

## Phase 11: Batch 19→20 custom-module migration on a cloud fleet — complete (2026-09-28)

Owner decision 2026-09-28. The kit gains what a multi-module batch migration needs, then proves
it by migrating eight Odoo 19 modules from the owner's private `VPCS-Cloud` repository to 20.0
in three parallel Docker Cloud Sandboxes. Codex runs the LLM steps on the owner's ChatGPT
subscription. **Code stays private (owner, 2026-09-28):** module and repository names may appear
in public docs, but module source, migrated code and patches never enter tracked files, commits
or public artifacts; they live only in the gitignored `.sandbox/`. Pushing migrated code to the
private repository is an owner action.

| Group | Modules (install order) | Test files on 19 |
|-------|-------------------------|------------------|
| A: LLM stack | `vpcs_llm_provider` (Phase 10 control) → `vpcs_typesafe_ai`, `vpcs_ai_livechat` (+ new reranker tests on 20), `website_blog_ai_generator` | 4+1+0+4 |
| B: commerce chain | `currency_rate_of_rbi` → `vpcs_gitlab` → `vpcs_cloud_website_customization` | 0+2+1 |
| C: WhatsApp base | `odoo_whatsapp_mcp` | 5 |

`vpcs_github_copilot_provider` was dropped (owner does not use it) and replaced by
`vpcs_ai_livechat`: it has no tests on 19, but with `odoo_whatsapp_mcp` it unblocks the WhatsApp
chatbot chain for a later phase. Its embeddings already go through provider HTTP APIs (OpenAI,
Google, Ollama server); `sentence-transformers` (PyTorch, several GB) is used only by the optional
cross-encoder reranker, which the 20.0 version drops (owner decision). pgvector stays optional
(`init()` tolerates a missing `vector` extension; the sandbox Postgres has none, so vector search
is recorded as not exercised). Known risk: `odoo_whatsapp_mcp` pins `Pillow==10.0.1` /
`requests==2.31.0` over the Odoo 20 system packages.

- [x] Multi-module requirements: `sandboxctl create --requirements` accepts the flag more than
      once (or a staging tree with several `requirements.txt`), merges the validated lines and
      fails on conflicting pins with a clear error. Test first, on synthetic fixtures only.
      Done 2026-09-28: `merge_requirements` in `sandboxctl`; tests in
      `tests/test_phase10_requirements.py`. Real group A/C files merge cleanly.
- [x] `sandbox-fleet create --cloud --import DIR [--requirements FILE ...]`: ship the staging
      tree with the snapshot and pass it through to `sandboxctl create` in the cloud sandbox.
      `--module` stays the install target list. Test first; update `plugin/commands/fleet.md`.
      Done 2026-09-28: `import_payload` → `.sandbox/fleet/imports/<session>.tgz`, cloud-only;
      tests in `tests/test_phase10_fleet_cloud.py`; `plugin/commands/fleet.md` updated.
- [x] Deterministic baseline-parity check (no LLM): a script that parses two Odoo test logs
      (19 baseline, 20 result), lists every test by name with its status, and exits non-zero
      when a test that passed on 19 fails, errors or is missing on 20. It writes a JSON result
      that `backend_tests_baseline_parity` can cite. Test first on synthetic fixture logs.
      Done 2026-09-28: `sandbox/scripts/test-parity.py`, tests in
      `tests/test_phase11_test_parity.py`. On the Phase 10 logs: parity PASS, 1 fix, and failed
      and error counts match Odoo's summary (a class-level error from `odoo.tests.suite` counts as
      its own row, so the total is 35, not 34).
- [x] Private-code guard: a validate/test check that fails when an Odoo module
      (`__manifest__.py`) is tracked outside `sandbox/fixtures/`, or when a tracked or staged file
      is a migration patch/bundle of module code, so private module source cannot be committed.
      Done 2026-09-28: `scripts/private_code_guard.py` (two Phase 8 evidence files
      grandfathered), run by `validate.sh`; tests in `tests/test_private_code_guard.py`.
- [x] `vpcs_ai_livechat` 20.0 migration spec (given to `/plan-analysis` for group A): remove
      `sentence-transformers` from `requirements.txt` and `reranking_service.py`; replace the
      cross-encoder with a pure-Python hybrid reranker (BM25 over the retrieved chunks blended
      with the vector similarity score; no new dependency) as the default, plus an optional
      `llm` mode that reranks through the configured `vpcs_llm_provider`; keep
      `use_reranking`/`rerank_top_k`, migrate `rerank_model` values that name a cross-encoder;
      fix the docstring that says Ollama embeddings use sentence-transformers. Ship new unit
      tests for the reranker (ordering, blend weights, empty input, `llm` fallback on provider
      error).
      Done: `rerank_model` Selection (`hybrid` default, `llm`), BM25+vector reranker, provider
      fallback, pre-migration of old values, 5 tests pass on 20; `sentence-transformers` removed.
- [x] Stage the three groups with `migrate-local.py` from a clean `VPCS-Cloud` checkout (commit
      recorded) into `.sandbox/`, and record each group's 19 baseline (install + tests, by name)
      inside its cloud sandbox before any change.
      Staged 2026-09-28 (local, no spend) from `VPCS-Cloud` `3530251` into
      `.sandbox/phase11/groups/{a,b,c}` (11 / 8 / 49 MB; a 78 MB marketing `.mp4` left out).
      Requirements mirror each manifest's `external_dependencies`; group A's livechat file drops
      `sentence-transformers`. Finding: `vpcs_gitlab` imports `paramiko` at load time without
      declaring it (added to group B's file; fix the manifest in the migration). All three groups'
      requirements merge without conflict. The 19 baselines run in the cloud sandboxes (open).
- [x] LIVE TEST (cloud, owner-approved spend): three parallel `sandbox-fleet create --cloud`
      sandboxes (codex template, internal-only), one per group. In
      each: 19 baseline → `/plan-analysis` → `/start-coding` → `/testing` with Codex (ChatGPT
      OAuth) and the plugin hooks → parity check on 20. Pass: every module installs on 20; the
      parity check exits 0 for every group (unless a difference is recorded and accepted by the
      owner); every command gate is passed rather than bypassed; `sbx --cloud ls` is empty at
      the end (owner runs removals).
      Run 1 (2026-09-28, `phase-11/live-test.md`): group C PASS (installs, parity 9/3/4 of 16 on
      19 and 20). Groups A and B partial: Codex hit the ChatGPT usage limit at 10:53 UTC in all
      three sandboxes; A has 2 of 4 modules migrated, and B is blocked by the removed
      `website_sale_comparison.product_attributes_body` template. Sandboxes removed by the owner.
      Closed 2026-09-28 by owner decision: the evidence is accepted as is — cloud run 1
      (fleet allocation, 19 baselines, Codex, group C PASS) plus the local completion run and
      live UI test (groups A, B, C parity PASS; all eight modules in one Odoo 20 database). The
      owner accepts that groups A and B did not finish in the cloud (ChatGPT usage limit); no
      no-LLM cloud re-verification was run. `sbx --cloud ls` was empty at the end.
- [x] Fix the fail-open gates found in run 1, test-first: `/start-coding` and `/testing` must
      refuse when no `docs/tasks.md` checklist is found for the target (repository root or the
      named module), not treat the target as out of scope.
      Done 2026-09-28: `common.find_module_dir` also recognises a module, or a directory of
      modules, up to the repository root; a single module holding the only checklist is the
      gated target. Tests: `tests/hooks/test_gates_fail_closed.py` (11). On the pulled run 1
      repositories: A and B `/testing` still blocked (open tasks); C now blocked for `/testing`
      and at Stop (its outcome was written to the repository's `sessions/`, not next to its
      module checklist).
- [x] Finish groups A and B from the pulled work repositories (`.sandbox/phase11/results/`) in
      fresh sandboxes; model quota plan agreed with the owner first (serial groups, or a second
      OpenAI-compatible provider such as the owner's Kaggle Ollama endpoint once its self-test
      passes: tool calls, `/v1/responses`, speed).
      Done 2026-09-28 locally (owner decision: Claude Code session + Docker Desktop, no cloud
      spend): A, B, C install on 20 with parity PASS in fresh sessions; gates pass. Details and
      the Odoo 20 change list: `phase-11/live-test.md` "Completion run".
- [x] If a run stops at `/start-coding` with no outcome recorded, the Stop-hook enforcement
      (`gates.needs_backend_test_record`) blocks it. Record that as live evidence;
      otherwise note it as still unit-test-only.
      2026-09-28: not triggered live (no run ended at Stop with all tasks done and no record). On
      the pulled group C repository the fixed hook's Stop check returns 2 with its message; still
      no in-agent live trigger.
- [x] `docs/docker-sandbox/phase-11/live-test.md` (commands, versions, per-module install and
      parity tables by test name, costs, blockers; no module code or diffs), CHANGELOG
      *Unreleased*, README/runbook updates, `SESSION_CONTEXT.md`. Migrated code is exported as
      patches under `.sandbox/phase11/` only.
      Done 2026-09-28: `live-test.md` (run 1, completion run, branch + live UI test, owner
      decision), CHANGELOG *Unreleased*, README, documentation skill acceptance rule.
- [x] Exit gate: all items above checked, the private-code guard passes on the final tree,
      `./scripts/validate.sh` green, one focused commit.
      Met 2026-09-28: `./scripts/validate.sh` OK (443 passed), `private_code_guard.py` rc 0.

## Phase 12: Batch-migration kit fixes from the Phase 11 findings

Owner decision 2026-09-28 (candidate 1 of 3). Turns the Phase 11 findings
(`phase-11/live-test.md`, findings 2, 3, 4, 7 and 9) into shipped, tested kit behaviour, so the
next batch (the WhatsApp chatbot chain) runs on kit code instead of the private helper scripts in
`.sandbox/phase11/`. Module code stays private as in Phase 11: only generic, module-agnostic
tooling enters tracked files, and `scripts/private_code_guard.py` must pass.

- [ ] Pinned requirements replay (finding 7), test-first: `sandboxctl create` accepts a recorded
      `results/requirements-freeze.txt` as a pinned input (pip constraints layered with the
      `--requirements` lines), so a build that resolved once resolves the same way later.
      Refuse a freeze recorded for another Odoo version or base image digest.
- [ ] Pass/fail criterion (finding 3), test-first: `test-parity.py` takes the expected module
      list and the install exit codes; a module that did not install, or has no test result
      where the baseline had one, fails the check even when no baseline pass regresses.
- [ ] Batch migration runner in the kit (findings 2 and 4): a generic
      `sandbox/scripts/migration-runner.sh` (from `.sandbox/phase11/runner.sh`, with no module
      names or private paths) with stages baseline → plan → code → test → verify; prompts in plain
      words naming the workflow file (no leading slash command); install exit codes recorded
      per module; groups run serially by default, parallel only when asked; each stage appends
      a machine-readable status line. Unit tests with fake `sandboxctl`/agent binaries.
- [ ] Live UI gate (finding 9): ship the proven browser checks as kit scripts (page errors,
      console `[error]`, error dialogs, new `odoo.http` exceptions in the session log) and make a
      recorded UI-check outcome required by `/testing` for migration targets, test-first
      (gate refuses without it; the Stop hook names it).
- [ ] Quota plan documented in the runbook and the runner (serial default, per-group budget
      stop, resume from the last finished stage).
- [ ] LIVE TEST (host agreed with the owner at the start of the phase; no cloud spend without
      approval): (1) the group A requirements that failed with `ResolutionImpossible` on
      2026-09-28 build from the cloud run's freeze file; (2) the runner's no-LLM `baseline` +
      `verify` stages on group C's 19 source and its `20.0` branch give parity PASS with install
      exit codes recorded; (3) a deliberately broken install fails the new pass criterion;
      (4) the UI check on one migrated app passes, and fails on an injected JS console error.
- [ ] Docs: `docs/docker-sandbox/phase-12/live-test.md`, README, `DockerSandboxOperations`
      skill / runbook, CHANGELOG *Unreleased*, `SESSION_CONTEXT.md`.
- [ ] Exit gate: all items above checked, `./scripts/validate.sh` green, the private-code guard
      passes, one focused commit.

## Definition of done for every implementation task

- Code/config and user documentation are updated together.
- Static validation and the narrowest relevant integration test pass.
- No secret is added to Git, logs, images, templates, or fixtures.
- Both success and failure emit a machine-readable operation result.
- Any experimental Docker Sandbox dependency is capability-checked and pinned.
- The task ends with a LIVE TEST appropriate to its scope.

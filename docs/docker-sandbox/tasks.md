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

## Phase 8: Full-coverage skill-orchestrated migration pipeline (client-readiness proof)

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

- [ ] Confirm `plugin/__init__.py`'s `on_session_start` hook correctly
  detects an Odoo Sandbox workspace vs. a bare local workspace and loads the
  right skill subset without manual selection.
- [ ] Confirm the version -> skill mapping table in `CommandingSystem/
  SKILL.md` resolves correctly for all three versions inside a sandbox
  session (not just documented).
- [ ] Confirm `sandbox/bin/sandboxctl module` is the sole install/update/test
  entrypoint used across the full sequence above — no direct `odoo-bin`
  calls bypass it.
- [ ] Confirm session-start context load (`CLAUDE.md` read before skill
  loading, per `context_handoff_workflow.md`) actually changes agent
  behavior on a real second run of the same module (measurable: it skips
  already-completed tasks rather than re-deriving them).
- [ ] Confirm the dynamic context-usage handoff guard
  (`plugin/context_guard.py`, fired on the real per-turn `post_api_request`
  usage hook) actually writes `CLAUDE.md`/`GEMINI.md`/`AGENTS.md` and nudges
  the agent when usage crosses its module-size-adjusted threshold — for at
  least one step of the sequence, not only for `/start-coding` — and that a
  genuinely fresh session (new process, not the same context) resumes
  correctly from the written handoff without operator intervention.
- [ ] Confirm the pipeline behaves correctly for a module with a real
  **Odoo Enterprise dependency** (not just Community-only modules) —
  dependency detection must flag it without ever fetching, bundling, or
  committing licensed Enterprise source.
- [ ] Measure and record wall-clock time and Sandbox resource usage for one
  full single-module run through all 10 steps, to size future batch runs
  within the Phase 7-measured host capacity limits (2-vCPU/15-GiB Oracle
  host: max ~2 constrained concurrent sessions).

### Deliverables

- [ ] A written **Phase 8 design note**
  (`docs/docker-sandbox/phase-8/design.md`) naming the exact skill
  invocation order above as the canonical sequence, referenced from
  `CommandingSystem/SKILL.md` so it is not only documented here.
- [ ] At least one Tier-1 (17.0-only) VPCSCloud Apps Store module migrated
  **inside a Docker Sandbox session** (not the bare local workspace used for
  the `edit_remove_pricelist_rule` pilot) through the full 10-step sequence,
  with every step's artifact path recorded in
  `docs/docker-sandbox/phase-8/live-test.md`.
- [ ] Confirmation that the already-completed `edit_remove_pricelist_rule`
  local-workspace pilot's outstanding gap (blocked browser screenshot) is
  closed via the sandbox-native `Agent-browser-skill` path in this phase,
  not worked around locally.
- [ ] A go/no-go decision, recorded in `SESSION_CONTEXT.md`, on batching the
  remaining ~45 backlog modules through this proven sequence versus doing
  targeted per-module runs, based on the measured single-module time/resource
  cost above.

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
- [ ] Step 7 — Live UI evidence (`Agent-browser-skill` screenshots against
  the sandboxed instance's published port) — **not yet performed**.
- [x] Step 8 — Frontend testing — confirmed N/A (module has no JS/OWL/QWeb
  assets), not assumed.
- [ ] Step 9 — Documentation regeneration (`/testing {version} {module}`
  regenerating `static/description/index.html`) — **not yet performed**.
- [ ] Step 10 — Context handoff and fresh-session resume verification —
  **not yet performed**.

The finished module was synced from the sandbox to the canonical
`vpcs_apps_cloud_18` module-store repository (branch `18.0`), merging in the
pre-existing commercial manifest fields the from-scratch plan/coding steps
did not know to preserve. `./scripts/validate.sh` passed 73/73 on the local
macOS workstation after the sync.

**Not yet a PASS of the exit gate below** — steps 7, 9, and 10 remain
outstanding and must be completed and evidenced before Phase 8 can be
marked done. Also resolved along the way: the Codex sandbox's OAuth token
was expired at session start; fixed via a host-level `sbx secret set openai
--oauth` re-authentication (see `plugin/skills/DockerSandboxMultiCliAdapter/
SKILL.md` for the exact reusable procedure, including the SSH port-forward
workaround for the OAuth callback on a remote VPS).

### LIVE TEST (Ubuntu 24.04+ KVM validation host)

Run one full pilot module through all 10 sequence steps end-to-end inside a
real Docker Sandbox session on the designated Ubuntu KVM host, using the
live-verified Hermes + `openrouter/free`/Hetzner fallback inference chain
(already proven 2026-08-18 for `/plan-analysis`). A failed or skipped step,
or any step that falls back to bare local execution instead of the sandbox
controller, is a blocker — not a pass. Record exact commands, artifact
paths, timings, and any deviation from the documented sequence.

Exit gate: one full pilot module passes the sequence above with recorded
evidence for every step, the dynamic context handoff/session-reset check in
step 10 is independently verified (not self-reported by the same
uninterrupted session), and the go/no-go batching decision is recorded.

## Definition of done for every implementation task

- Code/config and user documentation are updated together.
- Static validation and the narrowest relevant integration test pass.
- No secret is added to Git, logs, images, templates, or fixtures.
- Both success and failure emit a machine-readable operation result.
- Any experimental Docker Sandbox dependency is capability-checked and pinned.
- The task ends with a LIVE TEST appropriate to its scope.

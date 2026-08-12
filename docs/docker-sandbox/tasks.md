# Docker Sandbox Delivery Tasks

Legend: `[ ]` pending, `[x]` complete. A phase cannot start until the prior
phase exit gate passes.

## Phase 0: Validate product assumptions

- [ ] Record the supported `sbx` version range and capture `sbx version`,
  diagnostics, template, kit, secret, policy, ports, skills, and SSH capabilities.
- [ ] Create an architecture decision record for outer microVM plus inner
  Compose, clone-mode default, and local-mode compatibility.
- [ ] Select and document PostgreSQL versions for Odoo 17/18/19.
- [ ] Prove official Odoo image availability for amd64 and arm64 and record any
  platform exceptions.
- [ ] Define Community and separately licensed Enterprise addon handling.
- [ ] Approve session/result JSON schemas and resource/retention defaults.
- [ ] LIVE TEST: manually create a stock Codex sandbox, run an inner Compose
  hello-world service, publish a port, stop/start, export state, and remove it.

Exit gate: commands and experimental features used by the design are verified
against the pinned `sbx` version on at least macOS and Ubuntu.

## Phase 1: Runtime proof of concept (Odoo 19)

- [ ] Add `sandbox/compose/compose.yaml` with healthy PostgreSQL and Odoo.
- [ ] Add the Odoo 19 dev image with pinned inputs and lock manifest.
- [ ] Add generated config with container-safe paths and distinct DB/application
  credentials.
- [ ] Bind-mount one fixture addon from the session workspace.
- [ ] Add session-private DB, filestore, cache, logs, and results volumes/paths.
- [ ] Add Odoo and database readiness checks with bounded timeouts.
- [ ] Add basic `sandboxctl create/status/exec/logs/stop/start/destroy` commands.
- [ ] Emit `session.json`, `events.jsonl`, and operation result JSON.
- [ ] Add automatic diagnostic collection on failed readiness.
- [ ] LIVE TEST: install, update, RPC-test, restart, export, and destroy an Odoo
  19 fixture module with no orphaned volumes.

Exit gate: a fresh Odoo 19 session passes twice from a clean state and twice
from a warm image cache.

## Phase 2: Odoo 17 and 18 matrix

- [ ] Add Odoo 17 and 18 image definitions and digest locks.
- [ ] Move version-specific image, protocol, dependency, and config values to
  `versions.yaml`.
- [ ] Test XML-RPC paths for 17 and 18.
- [ ] Validate the supported Odoo 19 RPC/API path rather than relying on a
  hard-coded version assumption.
- [ ] Add per-version fixture-module install/update/CRUD tests.
- [ ] Add amd64/arm64 build and runtime matrix where supported.
- [ ] LIVE TEST: run 17, 18, and 19 concurrently and complete the full fixture
  lifecycle in each.

Exit gate: the same controller interface passes for all three versions.

## Phase 3: Existing kit integration

- [ ] Refactor `manage_modules.sh` into environment resolution, executor, and
  operation layers while retaining local mode.
- [ ] Add the `compose` executor and machine-readable exit/result contract.
- [ ] Update install/update decision logic to query the session database and
  isolated progress state.
- [ ] Update MCP configuration for Compose service discovery and session-scoped
  endpoints.
- [ ] Update SessionStart and context handoff to read `session.json`.
- [ ] Update backend/frontend testing skills with sandbox command examples.
- [ ] Update `/plan-analysis`, `/start-coding`, and `/testing` gates to record
  session operation results.
- [ ] Add `.sandbox/` ignore rules while preserving user-authored docs/context.
- [ ] LIVE TEST: execute all three lifecycle commands in an Odoo 19 Codex
  sandbox and verify install/update/log gates.

Exit gate: existing local-mode tests still pass and sandbox mode completes one
real module lifecycle without raw `odoo-bin` calls from skills.

## Phase 4: Agent templates, kits, and IDE adapters

- [ ] Create and validate a minimal Odoo mixin kit.
- [ ] Create Codex, Claude Code, and Copilot-compatible templates/kits only where
  agent-specific packaging is required.
- [ ] Add Docker Sandbox shared-skills import/setup documentation and fallback.
- [ ] Add scoped secret/OAuth setup without secret-bearing `.env` files.
- [ ] Add minimal network policy and policy preflight checks.
- [ ] Add SSH setup and VS Code/Cursor attach documentation.
- [ ] Add launch wrappers/tasks for current project integrations.
- [ ] Pin kit/template artifact versions and add release packaging checks.
- [ ] LIVE TEST: Codex CLI plus one SSH-attached IDE edit the fixture, run module
  tests, and retrieve correlated logs.

Exit gate: platform differences are confined to launch/attach adapters.

## Phase 5: Local concurrency

- [ ] Replace the Community `/fleet` subprocess/thread allocation with one local
  sandbox session per module task; keep shared/remote fleet scheduling in Pro.
- [ ] Add normalized unique session naming and branch creation.
- [ ] Add controller locks and idempotent lifecycle transitions.
- [ ] Add dynamic port allocation and manifest recording.
- [ ] Add maximum concurrency, CPU/memory/disk budgets, idle stop, and retention.
- [ ] Aggregate status/results without granting cross-session write access.
- [ ] Require commit, push, or patch export before destructive cleanup.
- [ ] Add graceful cancellation and partial-failure reporting.
- [ ] LIVE TEST: run six sessions (two each for 17/18/19), including two copies
  of the same module, and prove source/database/log isolation.

Exit gate: one failed session does not change or stop any sibling session.

## Phase 6: Observability and recovery

- [ ] Implement unified service log streaming and filtering.
- [ ] Implement redacted diagnostic bundles with Compose state, health, events,
  resources, policy diagnostics, and operation results.
- [ ] Emit JUnit/coverage/browser artifacts in stable locations.
- [ ] Add optional OpenTelemetry log export interface.
- [ ] Add crash, denied-network, disk-pressure, invalid-module, interrupted
  operation, and controller-restart tests.
- [ ] Add backup/restore for session development databases when explicitly
  requested.
- [ ] LIVE TEST: inject each supported failure and confirm actionable logs,
  bounded retry, recovery/cleanup, and sibling health.

Exit gate: every failure scenario produces a redacted diagnostic bundle and a
deterministic terminal or recoverable state.

## Phase 7: Release hardening

- [ ] Add CI for shell/Python tests, Compose validation, kit validation, image
  builds, dependency/license inventory, and version smoke tests.
- [ ] Add macOS Apple Silicon, Windows 11, and Ubuntu operator runbooks.
- [ ] Add upgrade/rollback tests for template, kit, Odoo image, Postgres image,
  and session schema versions.
- [ ] Measure cold/warm startup, disk growth, memory, and six-session load.
- [ ] Document capacity recommendations from measured results.
- [ ] Add local-to-sandbox migration and compatibility documentation.
- [ ] Publish tested platform runbooks generated from the validated controller,
  Compose, template, and kit versions.
- [ ] LIVE TEST: execute the release acceptance matrix from a clean host setup.

Exit gate: all requirements acceptance scenarios pass, artifacts are pinned,
and rollback plus cleanup are demonstrated.

## Definition of done for every implementation task

- Code/config and user documentation are updated together.
- Static validation and the narrowest relevant integration test pass.
- No secret is added to Git, logs, images, templates, or fixtures.
- Both success and failure emit a machine-readable operation result.
- Any experimental Docker Sandbox dependency is capability-checked and pinned.
- The task ends with a LIVE TEST appropriate to its scope.

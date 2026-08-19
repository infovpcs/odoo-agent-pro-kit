# Changelog

All notable changes to `odoo-agent-pro-kit` are documented here. Versions
track the `plugin/.claude-plugin/plugin.json` `version` field.

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

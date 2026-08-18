# Changelog

All notable changes to `odoo-agent-pro-kit` are documented here. Versions
track the `plugin/.claude-plugin/plugin.json` `version` field.

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

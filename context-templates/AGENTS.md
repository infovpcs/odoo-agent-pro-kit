# Odoo Agent Pro Kit — Agent Context

This file is the canonical context document for any AI coding agent working in
an Odoo 17/18/19 custom-app workspace bootstrapped with the Odoo Agent Pro Kit.
`CLAUDE.md`, `GEMINI.md`, and `.github/copilot-instructions.md` in this same
workspace are thin pointers back to this file, so keep this one up to date and
let the others stay short.

## Quick Start — MCP Server

The MCP (Model Context Protocol) server enables live Odoo database queries for
real-time model/field discovery. Start it from the kit's `plugin/odoo_mcp/` directory:

```bash
cd <path-to-odoo-agent-pro-kit>/plugin/odoo_mcp
./start_mcp_server.sh --all      # start all configured versions
./start_mcp_server.sh --status   # check status
```

| Odoo Version | MCP Port | Protocol |
|---|---|---|
| 17.0 | 8765 | XML-RPC |
| 18.0 | 8766 | XML-RPC |
| 19.0 | 8767 | JSON-RPC 2.0 |

See `plugin/odoo_mcp/MCP_SERVER_USAGE.md` for full start/test/connect instructions.

### MCP Tools Available

| Tool | Purpose |
|---|---|
| `mcp_search_models` | Search models by name/description |
| `mcp_get_fields` | Get field definitions for a model |
| `mcp_get_relationships` | Get related models |
| `mcp_validate_field` | Validate field exists before coding |
| `mcp_refresh_context` | Refresh context cache |

## Commanding System — Slash Commands

Four version-aware (17\|18\|19) slash commands orchestrate the full custom-app
lifecycle. They work identically from Claude Code, Codex, Cursor, Antigravity,
VS Code, or GitHub Copilot — see `integrations/<tool>/INSTALL.md` for each.

| Command | Purpose | Gate |
|---|---|---|
| `/plan-analysis (17\|18\|19)` | Requirements gathering, MCP model discovery, PRD `docs/` folder generation | None |
| `/start-coding (17\|18\|19)` | Task-loop with a backend test per task | Requires `docs/tasks.md` |
| `/testing (17\|18\|19)` | Frontend UI tests + responsive `index.html` documentation | Requires all tasks `[x]` |
| `/fleet (17\|18\|19)` | Parallel workspace orchestration for multiple modules | None |

### Skill loading per command

**`/plan-analysis` loads:**
1. `Odoo{V}CodingStandard`
2. `OdooTools{V}`
3. `Odoo{V}ExistingDependencyContext`
4. `PRD-Writing`

**`/start-coding` loads:**
1. `Odoo{V}CodingStandard`
2. `Odoo{V}ExistingDependencyContext`
3. `sessions/{module_name}_progress.json` (context restore, written by the
   `PreCompact` hook)
4. `Odoo_Custom_Backend_Testing` (for each task)

**`/testing` loads:**
1. `Agent-browser-skill`
2. `Odoo_Module_Documentation_Screenshot`

**`/fleet` loads:**
1. `CommandingSystem` (`SKILL.md` + `fleet_workflow.md`)

### PRD output structure

```
{module_name}/
  docs/
    requirements.md   ← functional requirements
    design.md         ← technical design
    tasks.md          ← implementation checklist
    module_meta.md    ← name, author, license
```

### Key rules

- **Always** load `CommandingSystem/SKILL.md` first before reading a workflow file.
- **Do not hard-stop on gate failures** — auto-route to the prerequisite command:
  - `/start-coding` missing PRD docs → route to `/plan-analysis`, then resume.
  - `/testing` with incomplete tasks → route to `/start-coding`, then resume.
- Version is **mandatory** — ask the user if it's missing from the command.
- Use MCP tools (`mcp_search_models`, `mcp_get_fields`) during `/plan-analysis`
  for live model discovery — don't guess field names.
- Detect whether Odoo Enterprise is available before assuming enterprise-only
  modules can be used.

## Hooks (context optimization)

This kit ships three hooks (`plugin/hooks/hooks.json`) that run automatically
once the plugin is installed:

- **SessionStart** prints the detected Odoo version/MCP port for the current
  workspace, so you don't have to re-derive it.
- **PreCompact** snapshots task progress to `sessions/{module}_progress.json`
  before context is summarized, so long `/start-coding` loops survive compaction.
- **Stop** gracefully terminates any MCP server processes started this session.

## Skills Reference

| Skill | Purpose |
|---|---|
| `Odoo{17,18,19}CodingStandard` | Models, views, security, constraints, performance per version |
| `Odoo{17,18,19}ExistingDependencyContext` | Live discovery of installed modules/dependencies (needs a running Odoo + MCP server) |
| `OdooTools{17,18,19}` | Scaffolding, shell, testing, linting, data import/export |
| `OdooRestartUpgradeRules` | When to restart vs. upgrade a module |
| `Odoo_Custom_Backend_Testing` | XML-RPC/JSON-2 backend test patterns |
| `Odoo_Custom_Frontend_Testing` | HOOT/JS frontend test patterns |
| `Odoo_Custom_App_Install_Update` | `manage_modules.sh`-based install/update patterns |
| `Odoo_Module_Documentation_Screenshot` | Module documentation, screenshots, `index.html` generation |
| `Agent-browser-skill` | Browser automation for Odoo web testing |
| `excalidraw-diagram-skill` | Architecture diagram generation |
| `PRD-Writing` | Requirements/design/tasks PRD authoring |
| `CommandingSystem` | The slash-command router documented above |

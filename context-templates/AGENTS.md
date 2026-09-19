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

### Discovery Tools

Live model discovery is exposed on two surfaces with the same capability and
different names. Match on the suffix: MCP clients namespace these by server
(e.g. `mcp__<server>__search_models`), which is why older notes wrote them as
`mcp_search_models`.

| Kit MCP server (`plugin/odoo_mcp/`) | DSH preset | Purpose |
|---|---|---|
| `search_models` | `odoo_search_models` | Search models by name/description |
| `get_fields` | `odoo_get_fields` | Get field definitions for a model |
| `get_relationships` | `odoo_get_relationships` | Get a model's relational fields |
| `validate_field` | `odoo_validate_field` | Confirm a field exists before coding |
| `get_model_info` | `odoo_get_model_info` | Display name, transient flag, field and relationship counts |
| `get_version_info` | `odoo_get_version_info` | Connected version, URL, database, user, uid |
| `list_all_models` | `odoo_list_all_models` | List the models on the connected database |
| — | `odoo_workspace_info` | Detected workspace, resolved connections, guard posture |

The DSH preset adds three offline knowledge-base tools that need no connection:
`odoo_kb_search`, `odoo_kb_read`, and `odoo_kb_list`, over the per-version OKF
bundles.

## Commanding System — Slash Commands

Five version-aware (17\|18\|19) slash commands orchestrate the full custom-app
lifecycle. They work identically from Claude Code, Codex, Cursor, Antigravity,
VS Code, or GitHub Copilot — see `integrations/<tool>/INSTALL.md` for each.

| Command | Purpose | Gate |
|---|---|---|
| `/plan-analysis (17\|18\|19)` | Requirements gathering, MCP model discovery, PRD `docs/` folder generation | None |
| `/start-coding (17\|18\|19)` | Task-loop with a backend test per task | Requires `docs/tasks.md` |
| `/testing (17\|18\|19)` | Frontend UI tests + responsive `index.html` documentation | Requires all tasks `[x]` |
| `/fleet (17\|18\|19)` | Parallel workspace orchestration for multiple modules | None |
| `/rules-check-drift [range]` | Audit the rules files against recent changes + PRD gate state (advisory, read-only) | None |

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

**`/rules-check-drift` loads:**
1. `OdooRulesDriftCheck`

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
- Use the discovery tools above (`odoo_search_models` / `odoo_get_fields` on
  DSH, `search_models` / `get_fields` over MCP) during `/plan-analysis` for live
  model discovery — don't guess field names.
- Detect whether Odoo Enterprise is available before assuming enterprise-only
  modules can be used.

## Hooks (context optimization)

This kit ships **seven** hook events (`plugin/hooks/hooks.json`), all running
automatically once the plugin is installed:

| Hook | What it does |
|---|---|
| `SessionStart` | Prints the detected Odoo version and MCP port for this workspace, so you don't have to re-derive them |
| `UserPromptSubmit` | Enforces the command gates — blocks `/start-coding` without `docs/tasks.md` and `/testing` while tasks remain unchecked |
| `PreToolUse` | The guard, on `Bash` and `Write\|Edit\|MultiEdit`: refuses raw `odoo-bin`, direct `manage_modules.sh`, VCS writes, destructive cleanup, and writes into an Enterprise source tree |
| `PostToolUse` | Lints edited Python against the version's Odoo rules, and reports Docker Sandbox module-operation status after a `Bash` call |
| `PreCompact` | Snapshots task progress to `sessions/{module}_progress.json`, so long `/start-coding` loops survive compaction |
| `Stop` | Reminds you to run `./scripts/validate.sh` when the validation stamp exists and is stale |
| `SessionEnd` | Terminates any MCP server processes this session started |

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
| `DockerSandboxOperations` | Sandbox setup, migration, lifecycle, release, benchmark, upgrade, and rollback workflow |
| `DockerSandboxMultiCliAdapter` | Drive multiple coding-agent CLIs (Codex, Claude, Hermes, Gemini) inside Docker Sandbox phases |
| `OdooHermesEnvironmentSetup` | Provision an AI agent for Odoo development on a fresh host |
| `OdooRulesDriftCheck` | Audit the rules files against recent changes and PRD gate state (advisory) |
| `OdooRequirementGapAnalysis` | Turn a requirements document into a code-verified fit-gap analysis and a lifecycle-aware implementation-time estimate (three scenarios); optional delivery profile via `GAP_PROFILE` |

When configuring or releasing Docker Sandbox, first load
`DockerSandboxOperations/SKILL.md`, then follow the platform runbook it names.
Do not claim support for a platform until its clean-host acceptance matrix has
been executed and recorded.

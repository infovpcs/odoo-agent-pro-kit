---
name: odoo_commanding_system
description: "Slash command router providing three lifecycle commands for Odoo custom app development: /plan-analysis (requirements & PRD generation), /start-coding (task-loop with backend testing), /testing (frontend UI testing & documentation). Version-aware (17|18|19), IDE/CLI agnostic. Works from VS Code, Antigravity, Cursor, or terminal."
version: "1.0.0"
author: "Vinay Rana"
category: "workflow"
odoo_versions: ["17", "18", "19"]
tags: ["commanding", "slash-commands", "plan-analysis", "start-coding", "testing", "workflow", "prd", "lifecycle"]
---

# Odoo Commanding System

Three slash commands that orchestrate the complete Odoo custom-app development lifecycle.
Commands are IDE/CLI agnostic — use from VS Code, Antigravity, Cursor, or any terminal.

## 🎮 Commands Overview

| Command | Purpose | Prerequisite |
|---------|---------|-------------|
| `/plan-analysis (17\|18\|19)` | Gather requirements, load Odoo structure, generate PRD docs/ folder | None |
| `/start-coding (17\|18\|19)` | Implement tasks from PRD with backend testing per task | docs/ PRD files |
| `/testing (17\|18\|19)` | Frontend UI testing + documentation asset generation | All tasks complete |

## 🚦 Command Routing Logic

When you receive a message starting with `/plan-analysis`, `/start-coding`, or `/testing`:

1. **Parse** the command and version number: `/plan-analysis 19` → `command=plan-analysis, version=19`
2. **Load** this SKILL.md (Level 2) — you are reading it now
3. **Load** the detailed workflow file (Level 3):
   - `/plan-analysis` → read `plan_analysis_workflow.md`
   - `/start-coding` → read `start_coding_workflow.md`
   - `/testing` → read `testing_workflow.md`
4. **Execute** the workflow step-by-step
5. **Gate check** each command's prerequisites before proceeding

## 📋 Version → Skill Mapping

When processing any command, load these skills in order for the given version:

### Odoo 19
```
1. AgentSkills/Odoo19CodingStandard/SKILL.md
2. AgentSkills/OdooTools19/SKILL.md
3. AgentSkills/Odoo19ExistingDependencyContext/SKILL.md
4. AgentSkills/Agents/ (pick relevant agent: POS, Website, ServerSide, Web, Migration)
5. AgentSkills/PRD-Writing/SKILL.md (for /plan-analysis only)
6. AgentSkills/excalidraw-diagram-skill/SKILL.md (for /plan-analysis only — architecture diagram generation)
```

### Odoo 18
```
1. AgentSkills/Odoo18CodingStandard/SKILL.md
2. AgentSkills/OdooTools18/SKILL.md
3. AgentSkills/Odoo18ExistingDependencyContext/SKILL.md
4. AgentSkills/Agents/ (pick relevant agent)
5. AgentSkills/PRD-Writing/SKILL.md (for /plan-analysis only)
6. AgentSkills/excalidraw-diagram-skill/SKILL.md (for /plan-analysis only — architecture diagram generation)
```

### Odoo 17
```
1. AgentSkills/Odoo17CodingStandard/SKILL.md
2. AgentSkills/OdooTools17/SKILL.md
3. AgentSkills/Odoo17ExistingDependencyContext/SKILL.md
4. AgentSkills/Agents/ (pick relevant agent)
5. AgentSkills/PRD-Writing/SKILL.md (for /plan-analysis only)
6. AgentSkills/excalidraw-diagram-skill/SKILL.md (for /plan-analysis only — architecture diagram generation)
```

## 🔌 MCP Port Reference

| Odoo Version | MCP Port | Protocol |
|-------------|----------|---------|
| 17 | 8765 | XML-RPC |
| 18 | 8766 | XML-RPC |
| 19 | 8767 | JSON-RPC 2.0 |

## ⚡ Quick Command Examples

```bash
# Start requirements analysis for Odoo 19 module
/plan-analysis 19

# Begin coding with task loop (requires docs/ from plan-analysis)
/start-coding 19

# Run frontend tests and generate documentation (requires all tasks complete)
/testing 19
```

## 📁 PRD Output Structure (created by /plan-analysis)

```
{module_name}/
  docs/
    requirements.md        ← functional requirements
    design.md              ← technical design decisions
    tasks.md               ← implementation task checklist
    module_meta.md         ← module name, author, license, version
    architecture.excalidraw   ← (optional) architecture diagram source
    architecture.png          ← (optional) rendered architecture diagram PNG
```

## 🛡️ Gate Rules

- **`/start-coding`** will NOT run unless `{module_name}/docs/tasks.md` exists.
- **`/testing`** will NOT run unless ALL tasks in `docs/tasks.md` are `[x]`.
- If gates fail → show exact error + redirect instruction to user.

## 🪝 Deterministic Hooks (v0.5.0)

These rules are now enforced by hooks (`plugin/hooks/odoo_hook.py`, wired in
`plugin/hooks/hooks.json`; Hermes parity via `pre_tool_call` / `post_tool_call`
in `plugin/__init__.py`), so they hold whether or not the agent remembers them:

| Moment | Hook | Effect |
| --- | --- | --- |
| `/start-coding` without `docs/tasks.md` | UserPromptSubmit | blocked, redirect to `/plan-analysis` |
| `/testing` with open tasks or unpassed backend tests | UserPromptSubmit | blocked, redirect to `/start-coding` |
| raw `odoo-bin`, `./manage_modules.sh`, unauthorized `git push/merge/tag` | PreToolUse[Bash] | blocked |
| writing secrets / Enterprise source into the repo | PreToolUse[Write] | blocked |
| Odoo 19 `<tree>` / `type='json'` / `attrs=` / `category_id` on a `res.groups` record in edited files | PostToolUse[Write] | blocked until fixed |
| `sandboxctl module … install/update/test` not `succeeded` | PostToolUse[Bash] | advisory: do not mark task complete |

Reading or searching the guarded scripts (`cat odoo-bin`, `grep odoo-bin`,
`cat manage_modules.sh`) and read-only git subcommands (`git merge-base`,
`git tag -l`, `git rebase --abort`) are **not** blocked.

Disable all hooks with `ODOO_KIT_HOOKS_DISABLED=1`. Authorize VCS writes with
`ODOO_KIT_ALLOW_VCS_WRITE=1` or a `.sandbox/AUTHORIZED` marker. Allow a raw
`odoo-bin` / `./manage_modules.sh` run (only when the user explicitly needs it)
with `ODOO_KIT_ALLOW_RAW_ODOO=1`.

## 📖 Detailed Workflow Files

For step-by-step execution of each command, read:
- `plan_analysis_workflow.md` — complete /plan-analysis execution steps
- `start_coding_workflow.md` — complete /start-coding execution steps
- `testing_workflow.md` — complete /testing execution steps

### Phase 25: Harness Engineering & Context Handoff

**New behaviors in Phase 25:**

| Feature | Tool | Trigger |
|---------|------|---------|
| Episodic memory (CLAUDE.md) | `auto_test/context_writer.py write` | End of each command |
| Context load on startup | Read `{module_dir}/CLAUDE.md` | Start of `/start-coding` + `/testing` |
| Per-task auto-testing | `auto_test/auto_test_runner.py` | After each task implemented |
| Multi-agent context | Writes CLAUDE.md + GEMINI.md + AGENTS.md | Same write call |

**Context Pipeline:**

```
/plan-analysis  → writes  → {module_dir}/CLAUDE.md  (analysis context)
/start-coding   → reads   → CLAUDE.md at startup
                → runs    → auto_test_runner.py after each task
                → writes  → CLAUDE.md after each task
/testing        → reads   → CLAUDE.md at startup
                → writes  → CLAUDE.md at 100% complete
```

**Auto-Test Gate:**

| Result | Action |
|--------|--------|
| PASS | Mark task `[x]`, update context, continue |
| PARTIAL | Review failures, optionally patch, update context, continue |
| FAIL | HALT — fix module install or CRUD before marking `[x]` |

**4 Memory Types:**

| Type | Where | Lifecycle |
|------|-------|-----------|
| Working | `sessions/{module}_progress.json` | Current session |
| Episodic | `{module_dir}/CLAUDE.md` | Cross-session/command |
| Semantic | `Odoo{V}CodingStandard/SKILL.md` | Persistent |
| Procedural | `*_workflow.md` files | Persistent |

**Reference:** `CommandingSystem/context_handoff_workflow.md`

### Phase 8: Sandbox-native canonical skill sequence (client-readiness proof)

For any real module port/migration (not a quick fixture test), the full
canonical sequence is: `Odoo{V}ExistingDependencyContext` (source, then
target) → `Odoo{V}CodingStandard` (target) → `PRD-Writing` +
`/plan-analysis` → `Odoo_Custom_App_Install_Update` +
`OdooRestartUpgradeRules` for every install/update inside the Sandbox's
inner Compose Odoo instance → `/start-coding` (per-task auto-test +
episodic context write) → `Odoo_Custom_Backend_Testing` →
`Agent-browser-skill` (or `Odoo_Module_Documentation_Screenshot`) against
the Sandbox's real published port → `Odoo_Custom_Frontend_Testing` →
`/testing` → a fresh-session context-reset check confirming a new agent
session resumes purely from `CLAUDE.md` + `docs/tasks.md`. This sequence
must run inside a Docker Sandbox microVM, not the bare local workspace.
Full detail, scope checklist, and exit gate: `docs/docker-sandbox/tasks.md`
"Phase 8". The canonical sequence, execution-environment contract, and
reference-run history are recorded in
`docs/docker-sandbox/phase-8/design.md`.

**Dynamic context-usage handoff, throughout the sequence:** any step above
can independently trigger the handoff guard (`plugin/context_guard.py`,
fired on real per-turn token usage via the `post_api_request` hook) — the
threshold is not fixed and not tied to a specific command; it adjusts to
the module's actual task count from `docs/tasks.md` (smaller modules run
closer to the limit, larger ones hand off earlier). When triggered, the
current step's episodic context is written and a fresh session resumes
from it automatically — no manual context-budget tracking required. See
`context_handoff_workflow.md` "Dynamic Context-Usage Handoff (Phase 8)".

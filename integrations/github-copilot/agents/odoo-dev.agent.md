---
id: copilot-odoo-sdk-agent
name: Copilot Odoo SDK Agent
description: |
  Discoverable VS Code Copilot agent that uses the repository's AgentSkills
  (copied from `plugin/skills/` per this integration's INSTALL.md) to run
  lifecycle commands and Odoo development workflows. Default Odoo version: 19.
version: 1.0
visibility: workspace
tools:
  - run_in_terminal
  - read_file
  - write_file
  - apply_patch
constraints:
  - must_load_skills: true
  - forbid_external_network: true
---

# Registration for VS Code Copilot Agents UI

This file registers the `copilot-odoo-sdk-agent` so it appears in the VS Code
Copilot Agents explorer.

Notes
- The agent will follow the repository's SKILL.md loading rules and use MCP
  connectivity where available.
- run_in_terminal usage must be confirmed by the user before performing
  destructive operations (module installs, DB resets, etc.).

Pre-run validation
- Before taking actions that depend on Skill metadata, the agent SHOULD run
  the repository's skill validator directly:
  `python3 scripts/validate_skills.py plugin/skills`
  (the same command used by `CONTRIBUTING.md` and `.github/workflows/ci.yml`).

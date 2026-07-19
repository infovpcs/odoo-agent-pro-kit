---
id: copilot-odoo-sdk-agent
name: Copilot Odoo SDK Agent
description: |
  Discoverable VS Code Copilot agent that uses the repository's AgentSkills and
  the `AgentSkills/copilot_odoo_agent.py` SDK to run lifecycle commands and Odoo
  development workflows. Default Odoo version: 19.
version: 1.0
entrypoint: /.agent.md
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
Copilot Agents explorer. It references the root `.agent.md` entry for details.

Notes
- The agent will follow the repository's SKILL.md loading rules and use MCP
  connectivity where available.
- run_in_terminal usage must be confirmed by the user before performing
  destructive operations (module installs, DB resets, etc.).

Pre-run validation
- A helper script is available at `.github/copilot/agents/validate_agent_skills.sh` which runs the repository validation (`AgentSkills/scripts/validate_skills.py`). The agent SHOULD execute this validation before taking actions that depend on Skill metadata.

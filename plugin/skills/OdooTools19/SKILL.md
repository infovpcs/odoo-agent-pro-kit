---
name: odoo_tools_19
description: Standard Odoo 19.0 development tools including scaffolding, shell, testing, linting, data import/export, and performance profiling. Use when working with Odoo 19 development workflows.
version: 19.0.0
author: VPCS Team
category: development_tools
odoo_versions: ["19.0"]
tags: [odoo, tools, scaffold, shell, testing, linting, performance, profiling]
---

# Odoo 19.0 Development Tools

## Goal
Use standard Odoo 19.0 tooling to accelerate development, testing, and review.

## Core tools
- Scaffolding: `odoo-bin scaffold` for new modules; align with coding standards.
- Shell: `odoo-bin shell` for quick data/model inspection; prefer read-only checks.
- Tests: `odoo-bin -d <db> --test-tags <tag>`; isolate modules; add fixtures.
- Linting: enable pylint-odoo/black where available; keep CI-friendly.
- Data: use export/import for reference data; avoid manual prod edits.
- Performance: `--dev=profile` or log queries for hotspots; add indexes/domains based on findings.

## Copilot Agent Integration (v4.0+)
- Scaffolding: Use `copilot_odoo_agent.py` to auto-scaffold modules from natural language.
- Real-time Sync: Integrates with `static/src/main.js` via WebSocket for live state visualization.
- Multi-Model Selection: Uses `model_selector.py` to dynamic switch between `gpt-4o`, `claude-3-5-sonnet`, and free models based on task complexity.
- Progress Management: Uses `update_progress_tool` to maintain `*_progress.json` state, driving the automated workflow.
- Execution Monitoring: Emits `tool_start`, `tool_complete`, and `progress_updated` events for the OWL Control Center.

## Reuse odoo.tools (upstream)
- Reference: github.com/odoo/odoo/tree/19.0/odoo/tools
- Prefer importing helpers instead of re-implementing: `safe_eval`, `float_round/float_repr`, `date_utils`, `image`, `misc`, `pycompat`, `config`, `file_open`.
- When extending behavior, mirror upstream patterns and keep signatures/backward compatibility.

## Usage pattern
- During PRD/design: validate reuse ideas in shell; list existing models/views/rules.
- During build: scaffold, code, lint, test; document commands in tasks.
- During rollout: script migrations; capture dry-run outputs.

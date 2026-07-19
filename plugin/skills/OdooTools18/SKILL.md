---
name: odoo_tools_18
description: Standard Odoo 18.0 development tools including scaffolding, shell, testing, linting, data import/export, and performance profiling. Use when working with Odoo 18 development workflows.
version: 18.0.0
author: VPCS Team
category: development_tools
odoo_versions: ["18.0"]
tags: [odoo, tools, scaffold, shell, testing, linting, performance, profiling]
---

# Odoo 18.0 Development Tools

## Goal
Use Odoo 18.0 tooling to accelerate development, testing, and review.

## Core tools
- Scaffold: `odoo-bin scaffold <module> <addons_path>` (respect 18 standards).
- Shell: `odoo-bin shell -d <db>` for inspection; avoid destructive writes.
- Tests: `odoo-bin -d <db> --test-tags <tag>`; isolate modules.
- Lint: pylint-odoo/black if enabled.
- Data: export/import reference data; avoid manual prod edits.
- Performance: log queries; profile hotspots; add indexes/domains accordingly.

## Reuse odoo.tools (upstream)
- Reference: github.com/odoo/odoo/tree/18.0/odoo/tools
- Import rather than rewrite: `safe_eval`, `float_round/float_repr`, `date_utils`, `image`, `misc`, `config`, `file_open`.
- Match upstream patterns; keep signatures compatible when extending.

## Usage pattern
- Discovery: shell/export to see existing models/views/rules to extend.
- Build: scaffold, code, lint, test; note commands in tasks.
- Rollout: script migrations/backfills; keep dry-run logs.

---
name: odoo_tools_17
description: Standard Odoo 17.0 development tools including scaffolding, shell, testing, linting, data import/export, and performance profiling. Use when working with Odoo 17 development workflows.
version: 17.0.0
author: VPCS Team
category: development_tools
odoo_versions: ["17.0"]
tags: [odoo, tools, scaffold, shell, testing, linting, performance, profiling]
---

# Odoo 17.0 Development Tools

## Goal
Use standard Odoo 17.0 tooling to inspect, develop, and test efficiently.

## Core tools
- Scaffold: `odoo-bin scaffold <module> <addons_path>` (match coding standards).
- Shell: `odoo-bin shell -d <db>` for read-only inspection; avoid destructive changes.
- Tests: `odoo-bin -d <db> --test-tags <tag>`; keep modules isolated.
- Lint: pylint-odoo/black if available.
- Data: export/import reference data; avoid manual prod edits.
- Performance: log queries; add indexes based on heavy domains.

## Reuse odoo.tools (upstream)
- Reference: github.com/odoo/odoo/tree/17.0/odoo/tools
- Import utilities instead of duplicating: `safe_eval`, `float_round/float_repr`, `date_utils`, `misc`, `config`, `file_open`.
- Follow upstream patterns; maintain signature compatibility if extending.

## Usage pattern
- During discovery: shell/export to list models/views/rules to reuse.
- During build: scaffold, code, lint, test; document commands per task.
- During rollout: script migrations; capture dry-run outputs.

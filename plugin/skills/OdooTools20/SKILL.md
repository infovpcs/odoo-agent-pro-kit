---
name: odoo_tools_20
description: Standard Odoo 20.0 development tools including scaffolding, shell, upgrade_code source rewriters, testing, linting, JSON-2 API, and profiling. Use when working with Odoo 20 development or 19→20 migration workflows.
version: 20.0.0
author: VPCS Team
category: development_tools
odoo_versions: ["20.0"]
tags: [odoo, odoo-20, tools, scaffold, shell, upgrade_code, testing, linting, json2]
---

# Odoo 20.0 Development Tools

## Goal
Use standard Odoo 20.0 tooling to build, migrate, test, and review custom modules.

## Core tools
- Scaffolding: `odoo-bin scaffold` — then replace any generated `ir.model.access.csv` with
  `security/ir.access.csv` (see `Odoo20CodingStandard`).
- Shell: `odoo-bin shell` for read-only inspection.
- Tests: inside a Docker Sandbox session use `sandbox/bin/sandboxctl module <session> test <module>`
  only — never raw `odoo-bin --test-tags` for lifecycle gates (see `DockerSandboxOperations`).
  Local mode: `manage_modules.sh test <module>`.
- Linting: pylint-odoo/black where available; the kit's hook lint adds 20.0 rules L7–L10.

## Migration: `odoo-bin upgrade_code` (source rewriter)
Documented in `odoo/cli/upgrade_code.py`; scripts in `odoo/upgrade_code/`.
```bash
./odoo-bin upgrade_code --addons-path=<custom_addons> --from 19.0 --to 20.0 --dry-run  # list files
./odoo-bin upgrade_code --addons-path=<custom_addons> --script 19.4-00-ir-access        # one script
./odoo-bin upgrade_code --addons-path=<custom_addons> --glob '**/security/*'           # limit files
```
Scripts are best-effort: commit before running, read WARNING/ERROR output, diff, then install
+ test in the sandbox. For 17/18 sources run the full range (`--from 17.0 --to 20.0`) so
`tree-to-list`, `sql-constraint`, and `route-jsonrpc` apply before `ir-access`.

## External API (JSON-2)
- New: `POST /json/2/<model>/<method>` with `Authorization: bearer <api_key>`
  (`addons/rpc/controllers/json2.py`; `api_doc` module documents models).
- `/xmlrpc/2` and `/jsonrpc` still work in 20.0 but are deprecated with removal planned for 22.

## Reuse odoo.tools (upstream)
- Reference: github.com/odoo/odoo/tree/20.0/odoo/tools — prefer `safe_eval`, `float_round`,
  `date_utils`, `file_open`, `SQL` over re-implementations.

## Usage pattern
- PRD/design: inspect models and existing `ir.access` rows before adding new ones.
- Build: scaffold → code → lint → test; record commands in `docs/tasks.md`.
- Rollout: run `upgrade_code` on a branch, capture the dry-run list, then sandbox-test.

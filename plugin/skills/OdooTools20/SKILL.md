---
name: odoo_tools_20
description: Standard Odoo 20.0 development tools including scaffolding, shell, upgrade_code source rewriters, testing, linting, JSON-2 API, and profiling. Use when working with Odoo 20 development or 19→20 migration workflows.
version: 20.0.2
author: VPCS Team
category: development_tools
odoo_versions: ["20.0"]
tags: [odoo, odoo-20, tools, scaffold, shell, upgrade_code, populate, testing, linting, json2]
---

# Odoo 20.0 Development Tools

## Goal
Use standard Odoo 20.0 tooling to build, migrate, test, and review custom modules.

## Runtime
- Python ≥ 3.12 (≤ 3.14) and **PostgreSQL ≥ 16** (`odoo/release.py`). A 17–19 workspace on an
  older local PostgreSQL cannot host 20: give the 20 workspace its own PostgreSQL 16 server, e.g.
  `odoo_local_setup/setup_local_macos.sh --versions 20 --db-port 5436` against a `postgres:16`
  container published on `127.0.0.1:5436`.
- Local workspace: `<base>/20_workspace/{20.0,extra-20,config/odoo.conf.20,manage_modules.sh}`;
  HTTP port 8110, database `odoo20`, MCP port 8768 (`ODOO20_URL`, `ODOO20_DB_NAME`).

## Core tools
- Scaffolding: `odoo-bin scaffold` — then replace any generated `ir.model.access.csv` with
  `security/ir.access.csv` (see `Odoo20CodingStandard`).
- Shell: `odoo-bin shell` for read-only inspection.
- Tests: inside a Docker Sandbox session use `sandbox/bin/sandboxctl module <session> test <module>`
  only — never raw `odoo-bin --test-tags` for lifecycle gates (see `DockerSandboxOperations`).
  Local mode: `manage_modules.sh test <module>`.
- Linting: pylint-odoo/black where available; the kit's hook lint adds 20.0 rules L7–L17.
- Synthetic data: the `populate` addon (LGPL) adds `odoo-bin populate -d <db> -b <blueprint>`
  (`--scale`, `--seed`, `-j <workers>`, `--resume`, `--profile`). Blueprints live in a module's
  `populate/` folder (see `addons/sale/populate/`); run `-u populate` after installing a module
  that ships blueprints.

## Migration: `odoo-bin upgrade_code` (source rewriter)
Documented in `odoo/cli/upgrade_code.py`; scripts in `odoo/upgrade_code/`.

Pitfalls verified in a live 19→20 run (odoo/odoo@20.0 d3236ca5):
- **It rewrites Odoo's own addons too.** `--addons-path` is *added* to the server's default
  path, so scripts such as `owl3-migration`, `19.1-00-t-call` and `19.5-00-tuple-rec_names_search`
  rewrote ~1,000 files in the Odoo checkout. Run it against a throwaway Odoo checkout, or restore
  afterwards with `git -C <odoo> checkout -- . && git -C <odoo> clean -fd -- addons odoo`, and
  confirm the checkout SHA/clean state before installing.
- **`--from 19.0` can abort** in `19.3-00-account-groups` (`KeyError: 'ar_base'`), stopping every
  later script. Run the scripts that matter one by one with `--script`.
- **Exit code 1 means "files were changed"** (`sys.exit(int(is_dirty))`), not failure; read the
  `updated:` / `deleted:` lines.
- It does **not** bump the manifest `version`; a `19.0.x` manifest is silently skipped as
  "incompatible version" on 20. Bump to `20.0.x` yourself.

```bash
git -C <custom_repo> switch -c migrate-20            # commit before rewriting
./odoo-bin upgrade_code --addons-path=<custom_addons> --script 19.4-00-ir-access
git -C <odoo_checkout> status --short | wc -l         # must be 0 — restore if not
```
Then run the kit lint at version 20 (L7–L17) over the module, fix what remains by hand, install +
test on 20, and compare failures test-by-test against a 19.0 baseline run of the same source.
For 17/18 sources also run `17.5-01-tree-to-list`, `18.1-00-sql-constraint`, `18.1-02-route-jsonrpc`.

## External API (JSON-2)
- New: `POST /json/2/<model>/<method>` with `Authorization: bearer <api_key>`
  (`addons/rpc/controllers/json2.py`; `api_doc` module documents models).
- `/xmlrpc/2` and `/jsonrpc` still work in 20.0 but are deprecated with removal planned for 22.
- Binary fields read as `{'content': <base64>, 'filename'?, 'size'}` and accept a base64 string
  on write; see `Odoo20CodingStandard` (L16/L17).

## Reuse odoo.tools (upstream)
- Reference: github.com/odoo/odoo/tree/20.0/odoo/tools — prefer `safe_eval`, `float_round`,
  `date_utils`, `file_open`, `SQL` over re-implementations.

## Usage pattern
- PRD/design: inspect models and existing `ir.access` rows before adding new ones.
- Build: scaffold → code → lint → test; record commands in `docs/tasks.md`.
- Rollout: run `upgrade_code` on a branch, capture the dry-run list, then sandbox-test.

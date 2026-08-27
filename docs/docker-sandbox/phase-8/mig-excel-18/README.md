# Live pipeline validation — excel_sheet_data_import 17.0 → 18.0

First end-to-end run of the CommandingSystem lifecycle (`/plan-analysis` →
`/start-coding` → `/testing`) against a real pending-migration module, in a live
Docker Sandbox session, with the 0.5.0 deterministic pipeline hooks exercised.

- **Module:** `vpcs_apps_cloud_17/excel_sheet_data_import` → `vpcs_apps_cloud_18/excel_sheet_data_import`
- **Sandbox session:** `mig-excel-18` (Odoo 18.0-20260810 + PostgreSQL 15), stopped (volumes kept)
- **Full write-up:** `vpcs_apps_cloud_18/excel_sheet_data_import/docs/MIGRATION_REPORT.md`

## Files here

| File | What |
|------|------|
| `00-baseline-install-result.json` / `00-baseline-odoo-log.txt` | unmigrated 17 module → `install failed exit 1`, `invalid module names, ignored` |
| `T1-T2-install-succeeded.json` | after manifest + `<list>` fixes → `succeeded exit 0` |
| `T5-update-succeeded.json` / `T5-test-succeeded.json` | clean-room re-run → both `succeeded exit 0` |
| `phaseC-odoo-log-module-lines.txt` | odoo.log slice: 7 tests, `0 failed, 0 error(s)` |
| `phaseD-rpc-validation.txt` | live web-request checks (get_views, e2e xlsx import, security) |
| `excel_sheet.py.diff` / `module.diffstat.txt` | the actual code delta |
| `events-*.jsonl` | sandbox session lifecycle events |

## Hook behaviour verified (run from inside the module dir)

| Hook | Input | Result |
|------|-------|--------|
| PreToolUse | Bash `odoo-bin -u …` | **exit 2 — blocked**, routes to `sandboxctl module` |
| PreToolUse | Bash `git push origin main` | **exit 2 — blocked**, needs `ODOO_KIT_ALLOW_VCS_WRITE` / `.sandbox/AUTHORIZED` |
| PostToolUse | Edit adding `<tree>` to an 18 view | **L1 lint warn** → "Replace `<tree>` with `<list>`" |

Note: `odoo_hook.py` is **scoped** — `main()` no-ops unless `cwd` is inside an
Odoo module, so it does not interfere with work in the kit repo root or other
projects. The plugin is not installed as a Claude Code plugin in the dev
session used for this run, so hooks were exercised by direct dispatch, not
auto-fired.

## Findings for the pipeline

1. `/testing`'s browser flow assumes `http://localhost:<port>` — the Docker
   Sandbox publishes **no port** by design and `sandboxctl` has no `publish`
   verb, so the standard agent-browser screenshot/GIF flow can't reach a
   sandbox session. A loopback `socat` bridge gets JSON-RPC through but the
   web client's asset/websocket load stalls. Options: add `sandboxctl publish`,
   or an official RPC-based frontend-check path for sandbox mode.
2. `checks/sandbox_result.read_operation_result` resolves `.sandbox/…/results/`
   relative to `cwd`; from a module dir outside the kit repo it returns `None`.
   The PostToolUse sandbox advisory therefore only fires when the agent runs
   from the kit repo. Worth making the lookup session-aware.
3. Recent Odoo 18 nightlies have **fully removed `<tree>`** (not just
   deprecated). Linter rule L1 should treat `<tree>` as `block` severity for
   18 as well as 19, not `warn`.

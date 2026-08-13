# Phase 7 release acceptance and rollback

## Automated gates

The GitHub Actions workflow runs repository/skill/artifact validation, Compose
configuration, pinned-contract verification, dependency/license inventory,
amd64 builds, and one lifecycle smoke job for each Odoo version. CI cannot
substitute for Docker Sandbox microVM acceptance.

Run locally:

```bash
./scripts/validate.sh
python3 sandbox/scripts/release-acceptance.py verify
python3 sandbox/tests/upgrade-rollback.py
python3 sandbox/scripts/dependency-inventory.py --output .sandbox/release/dependencies.json
```

To review a proposed artifact-lock upgrade:

```bash
python3 sandbox/scripts/release-acceptance.py compare /path/to/previous-artifacts.lock
```

Upgrade one component at a time: template/Sandbox CLI, kit, Odoo image,
PostgreSQL image, then schemas. Re-run the three-version lifecycle and recovery
tests after every change. Roll back by restoring the prior tested lock files
and recreating disposable sessions. Never downgrade a live PostgreSQL volume
or persisted schema in place; restore an explicit compatible backup into a new
session and verify it before deleting the failed session.

`upgrade-rollback.py` mutates staged copies of the template reference, kit,
Odoo/PostgreSQL locks, and both schemas, proves every change is detected, then
proves byte-identical contract rollback. The LIVE TEST separately demonstrates
database backup/restore and clean runtime recreation.

## Clean-host LIVE TEST matrix

Record exact host OS/architecture, Docker client/daemon, Compose, `sbx`, agent
template, kit, image digests, commands, durations, disk, and peak memory.

1. Run common preflight and dependency inventory.
2. Create cold Odoo 17/18/19 sessions; install, update, test, API CRUD, restart,
   export, and destroy each.
3. Repeat warm and verify the 90-second warm-ready target.
4. Run six sessions (two/version), inject Phase 6 failures, and prove sibling
   health and isolation.
5. Exercise template, kit, Odoo, PostgreSQL, and schema upgrade/rollback using
   prior lock copies and a database backup/restore into a new session.
6. Test migration from a clean disposable local custom-addons Git repository.
7. Test Codex and one additional CLI agent; probe SSH and use the approved
   `sbx exec` fallback only after recording the pinned SSH failure.
8. Destroy everything and prove there are no matching sandboxes, containers,
   volumes, networks, or ports.

Unsupported platform tests and failed gates are blockers, not passes.

Release review additionally requires that failed outer port publication never
marks a fleet session ready and cleanup runs after every outer creation attempt,
including a creation command that fails after partial success. Failed
provisioning interruption follows the same cleanup and terminal-state path.
Repeated SIGINT is ignored until cleanup and terminal-state persistence finish.
Failed database restore records failed state before quarantine, preserves that state
even if quarantine or diagnostics also fail, and uses force-removal fallback
plus a volume-preserving full-stack teardown to keep the modified database
inaccessible. An unsuccessful restore leaves a persistent integrity block that
generic recovery cannot clear; only a successful explicit restore clears it.
Direct session start and module install/update/test enforce the same integrity
block, as do database backup and arbitrary Odoo-service execution. Status,
logs, diagnostics, explicit restore, and cleanup remain available.
Migration names must match the controller's Odoo
technical-name contract and its conservative 52-character generated-session limit before a
target path is constructed. Direct controller creation enforces the same bound.

# Phase 5 local concurrency

Community fleet orchestration is limited to one Docker Sandbox host.
`sandbox/bin/sandbox-fleet` owns allocation and aggregate metadata; each module
task runs in a separate Docker Sandbox microVM and calls `sandboxctl` inside it.
Remote workers, shared queues, and organization scheduling remain Pro features.

## Configuration and identity

Defaults live in `sandbox/config/concurrency.json`. The initial host limit is
six active sessions; CPU, memory, disk, idle-stop, stopped-session retention,
and artifact-retention targets are recorded there. Inner Odoo and PostgreSQL
CPU/memory limits are enforced by Compose. The 40 GiB outer disk value is
advisory with `sbx` 0.38.x because create has no disk-limit flag.

Each ID is `odoo-<major>-<module>-<random>`, with writable branch
`sandbox/<session-id>`. Duplicate module names therefore have independent
names, branches, filesystems, Compose projects, databases, filestores, logs,
and published ports.

## Commands

```bash
sandbox/bin/sandbox-fleet create --version 19 --module sandbox_fixture
sandbox/bin/sandbox-fleet status
sandbox/bin/sandbox-fleet run <session> test sandbox_fixture
sandbox/bin/sandbox-fleet cancel <session>
sandbox/bin/sandbox-fleet protect <session> commit
sandbox/bin/sandbox-fleet destroy <session>
sandbox/bin/sandbox-fleet maintain
```

Creation requests loopback-only ephemeral publication of Odoo port 8069 and
records the assigned host port when `sbx` reports it. Status aggregation reads
only coordinator manifests and never enters a sibling workspace.

`cancel` stops only the selected inner runtime and records a cancelled result.
Create failures do not stop siblings. Repeated stop/start/destroy operations
are idempotent, and per-session locks serialize lifecycle and module mutations.

## Retention and cleanup

`maintain` stops sessions idle for 60 minutes. It reports stopped sessions that
reach seven days but never destroys them automatically. Result/diagnostic
retention is 14 days with a 250 MiB target; artifact pruning belongs to Phase 6
with redacted diagnostic bundles.

Before `destroy`, record a recovery path with `protect`: `commit`, `push`, or
`patch_export`. Cleanup is otherwise refused. `--force` and inner
`--allow-unexported` are explicit escape hatches for disposable test sessions.

## LIVE TEST contract

On Ubuntu 24.04+ KVM, create six simultaneous outer Sandboxes: two each for
Odoo 17, 18, and 19, including duplicate `sandbox_fixture` tasks. Give the
duplicates distinct source markers and database records and prove neither is
visible in the sibling. Force one operation to fail and prove the other five
remain healthy. Record ports, logs, results, resources, branches, cleanup
guards, and complete inner/outer cleanup.

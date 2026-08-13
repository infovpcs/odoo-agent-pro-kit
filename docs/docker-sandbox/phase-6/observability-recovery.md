# Phase 6 observability and recovery

Every session exposes one controller contract for service logs, evidence,
artifacts, recovery, and explicitly requested database snapshots. Generated
state stays under `.sandbox/sessions/<session-id>/` and remains Git-ignored.

## Operator commands

```bash
sandbox/bin/sandboxctl logs SESSION [--service odoo|db|controller|agent|mcp] [--since 10m] [--follow]
sandbox/bin/sandboxctl diagnose SESSION --reason invalid-module [--policy-file PATH]
sandbox/bin/sandboxctl recover SESSION --timeout 180
sandbox/bin/sandboxctl backup SESSION
sandbox/bin/sandboxctl restore SESSION .sandbox/sessions/SESSION/backups/SESSION-TIMESTAMP.dump
```

Log lines include session, Odoo version, module, service, and the Compose
timestamp. `--follow` streams incrementally. Known runtime secret values and
credential-shaped key/value pairs are replaced with `[REDACTED]`.

Diagnostics are timestamped `tar.gz` bundles containing Compose state and
processes, health/state JSON, recent timestamped service logs, Docker resource
snapshots, session events, operation results, and supplied Docker Sandbox
policy diagnostics. `runtime.env` and generated Odoo configuration are never
included. Failed create, lifecycle, module, interrupted, and recovery
operations automatically create a bundle and store its path in the operation
result. A failed module operation is `recoverable`; `recover` performs one
bounded Compose reconciliation and health wait before selecting `ready` or
terminal `failed`.

Test integrations use stable paths:

```text
tests/junit/junit.xml
tests/coverage/coverage.xml
tests/browser/result.json
tests/browser/screenshots/
```

The module test gate always emits JUnit. Until an instrumented coverage or
browser runner is requested, valid zero-measurement coverage and an explicit
`not_run` browser result prevent missing artifacts from being mistaken for a
pass.

Set `SANDBOX_OTEL_LOG_ENDPOINT=stdout` or `file:///absolute/path/events.jsonl`
before session creation to opt into the version-one telemetry adapter. It
exports controller operation and diagnostic events as JSONL without changing
log producers. Network OTLP transport is intentionally not enabled by this
local interface.

Database backup and restore are never automatic. `backup` runs `pg_dump -Fc`
inside the session database service. `restore` accepts only a backup beneath
that same session, stops Odoo, applies `pg_restore --clean --if-exists`, then
restarts Odoo and waits for health. Source, filestore, and cache are not part of
the database dump; use `export` for the broader retained session artifact.

## Failure-injection acceptance

The live test must exercise Odoo and PostgreSQL crashes, a Docker Sandbox
denied-network policy event, bounded disk pressure, an invalid module,
SIGINT-interrupted operation, and controller restart. For every injection it
must record the exact command, a redacted bundle, the deterministic terminal or
recoverable state, cleanup, and an independent sibling health check. Disk
pressure must use a bounded disposable file and retain enough free space for
diagnostics and cleanup.

# ADR-0001: Sandbox and Odoo Runtime Boundaries

- Status: accepted
- Date: 2026-08-12

## Decision

Use one Docker Sandbox microVM for each writable agent/module session. Run one
private Docker Compose project inside it with the selected Odoo service and a
PostgreSQL service. Keep the agent/tooling template independent of the Odoo
service images.

Clone mode is the default for writable Git repositories. The controller creates
a session branch inside the sandbox because `sbx --clone` follows the host ref
but does not create a branch. Direct mode remains an explicit single-session
compatibility path with a collision warning. Non-Git sources are copied into a
session-owned workspace.

`manage_modules.sh` remains the module-operation entrypoint. It will acquire a
Compose executor while preserving local execution for one compatibility cycle.
Session manifests and operation-result JSON are the stable Community/Pro
boundary; shared and remote scheduling remains private Pro functionality.

## Consequences

- Source, database, filestore, logs, ports, Docker state, and progress are
  isolated by session.
- Odoo images can be patched and tested independently from agent templates.
- Clone-mode work must be committed or exported before sandbox removal.
- Nested Docker costs more disk and memory and therefore requires quotas.
- Docker Sandbox experimental features must remain behind capability checks.
- The Community runtime cannot depend on remote fleet or Kubernetes services.

## Rejected alternatives

- One writable host workspace shared by several agents.
- Host Docker socket or host PostgreSQL access from the sandbox.
- Odoo installed into every agent template.
- A private long-lived fork of the Community runtime for Pro.

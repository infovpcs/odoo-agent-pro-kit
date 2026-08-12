# Superseded Docker Sandbox Research Decisions

## Summary

The initial setup research correctly identified Docker Sandboxes as a strong
isolation boundary for coding agents and correctly targeted reusable tooling,
concurrent sessions, network policy, logs, and IDE access. That draft has now
been consolidated into the authoritative requirements, design, and delivery
tasks in this directory and removed to prevent conflicting instructions.

## Keep

- Docker Sandbox microVM isolation as the outer agent boundary.
- Separate sessions for Odoo 17, 18, and 19.
- Reusable templates/kits, explicit networking, log access, and SSH/editor
  integration.
- Continued use of `manage_modules.sh` as the module-operation control point.
- Read-only/reference mounts and isolated clone workflows as safety options.

## Correct before implementation

1. **Do not use a plain `python:3.11` image as a Codex Sandbox template.** A
   custom template should extend the matching Docker Sandbox agent template.
   Put Odoo in inner service images, not in the agent template.
2. **Do not depend on `pip install odoo-bin`.** It does not reproduce the three
   checked-out Odoo source environments or the official versioned container
   images described elsewhere in the guide.
3. **Replace the single all-version writable mount.** Multiple agents writing
   `/workspace` can corrupt or mix changes. Use a clone/session per module and
   mount shared sources read-only.
4. **Add PostgreSQL explicitly.** The proposed template installs only a client,
   while Odoo requires a server and isolated database state. Each session needs
   its own Compose database service and volume.
5. **Replace fixed ports.** Concurrent sandboxes can reuse internal ports, but
   host-published ports must be dynamic or uniquely allocated and recorded.
6. **Use the current kit directory/spec model.** The draft's single
   `odoo-dev-kit.yaml`, `apiVersion`, `baseImage`, `mounts`, and custom `tools`
   shape must be checked against the installed experimental kit schema rather
   than treated as established syntax.
7. **Update template commands.** Current CLI uses `sbx template ...`; a locally
   built image must be pushed to a registry or loaded into the Sandbox runtime.
   The host Docker image store is not automatically shared.
8. **Update credential handling.** Do not source API keys from a host file or
   pass them through command-line `--env`. Use Docker Sandbox stored secrets or
   OAuth so real values do not enter images or the sandbox filesystem.
9. **Update diagnostics and port workflows.** Use current `sbx diagnose`,
   `sbx ports`, policy, and SSH commands based on a pinned supported CLI. Docker
   Sandbox is evolving, so wrappers need capability checks.
10. **Do not claim production readiness yet.** The guide has no tested image
    locks, Compose stack, session state model, cleanup proof, concurrency suite,
    resource limits, or cross-platform acceptance evidence.
11. **Fix Odoo workspace assumptions.** This repository bootstraps directories
    such as `17_workspace`, `18_workspace`, and `19_workspace`, each containing
    `17.0`, `18.0`, or `19.0` source. The guide alternates between that model and
    a single `/workspace/{17.0,18.0,19.0}` tree.
12. **Fix test semantics.** Odoo module tests are not generally equivalent to
    `pytest tests/$MODULE`. Preserve the existing install/update and RPC-based
    live-test gates, then add native Odoo test execution where appropriate.
13. **Separate credentials.** PostgreSQL user/password and the Odoo application
    login are different identities; current environment naming can confuse
    them, especially in MCP configuration.
14. **Treat saved templates carefully.** Saved sandbox templates can capture
    filesystem state. Enforce a no-secret validation step before export/share.

## Disposition

The research draft was removed after its useful context was consolidated here.
The requirements, design, and tasks in this directory are authoritative. Once
Phase 0 validates a pinned Docker Sandbox release, add tested, generated
platform runbooks rather than restoring standalone command examples.

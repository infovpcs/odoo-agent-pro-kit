# Docker Sandbox Requirements

## Problem

The current kit prepares Odoo workspaces, Python virtual environments,
PostgreSQL databases, ports, logs, MCP servers, and agent context directly on a
developer host. That works for a small number of local sessions, but concurrent
agents can share mutable source trees, databases, ports, processes, Python
packages, logs, and progress files. A failed or untrusted task can also affect
the host environment.

The product needs a reproducible sandbox execution layer while keeping the
existing `/plan-analysis` -> `/start-coding` -> `/testing` workflow and the
version-aware Odoo skills.

## Goals

1. Support Odoo 17.0, 18.0, and 19.0 with pinned, reproducible runtime images.
2. Run multiple agent sessions concurrently without source, database, port,
   filestore, log, MCP, or progress-state collisions.
3. Give each custom-app task an isolated Git workspace and Odoo stack.
4. Preserve `manage_modules.sh` as the single module install/update/test control
   point through a stable container-aware command contract.
5. Make Odoo, PostgreSQL, module-operation, test, MCP, and agent logs easy to
   stream, inspect, archive, and correlate by session.
6. Support Codex, Claude Code, Cursor, VS Code, GitHub Copilot, Antigravity, and
   terminal use without duplicating the Odoo runtime design.
7. Provide deterministic health checks, cleanup, retry, and recovery behavior.
8. Keep credentials outside images, repositories, logs, and saved templates.

## Non-goals for the first release

- Production Odoo hosting or production database operations.
- Kubernetes or a remote multi-node scheduler.
- Odoo Enterprise source/image distribution.
- A custom replacement for the Docker Sandbox daemon or agent runtimes.
- Perfect hot reuse of databases across unrelated module sessions.

## Actors

- **Developer:** creates, attaches to, stops, resumes, exports, and removes a
  sandbox session.
- **Coding agent:** edits one module workspace and invokes approved lifecycle
  commands.
- **Fleet orchestrator:** allocates sessions and aggregates status without
  entering another session's workspace.
- **Maintainer:** builds version images, releases kits/templates, defines policy,
  and diagnoses failed environments.
- **CI runner:** validates images and exercises session lifecycle contracts.

## Functional requirements

### Session identity and isolation

- A session ID must be unique and immutable, using a normalized form such as
  `<version>-<module>-<short-id>`.
- A session manifest must record session ID, Odoo version, module, Git origin,
  commit/branch, template/kit version, image digests, creation time, status,
  assigned resources, and published ports.
- Every writable development session must use an isolated Git clone or worktree.
- Concurrent sessions must use distinct PostgreSQL volumes, Odoo filestore
  volumes, Compose projects, progress directories, and host port mappings.
- A session may mount shared reference repositories read-only.
- No session may mount the complete multi-version host workspace read-write by
  default.

### Odoo runtime

- Each session runs exactly one selected Odoo major version: 17, 18, or 19.
- The runtime must contain PostgreSQL, Odoo, the selected custom-addons tree,
  configuration, health checks, and test tooling.
- Odoo and PostgreSQL image references must be pinned by immutable digest in
  released lock files. Friendly tags may be used only as build inputs.
- Community images may be built from the official Odoo Docker image. Enterprise
  addons, if licensed, must be supplied through a separate private read-only
  source and must never be baked into a public image.
- The custom module source must remain in the session Git workspace; generated
  data, database files, filestore, and caches must remain outside Git.

### Module control contract

The sandbox controller must expose these stable operations:

```text
sandboxctl create --version <17|18|19> --module <name> [--agent <agent>]
sandboxctl status <session>
sandboxctl exec <session> -- <command>
sandboxctl logs <session> [--service <odoo|db|mcp|agent>] [--follow]
sandboxctl module <session> install|update|test <module>
sandboxctl stop|start|destroy <session>
sandboxctl export <session>
```

- `sandboxctl module` must call `manage_modules.sh`; it must not duplicate
  module state logic.
- `manage_modules.sh` must accept environment/config overrides for the Odoo
  executable/container, database host, database name, addons path, config path,
  log path, and RPC URL.
- Operations must return meaningful exit codes and write a machine-readable
  result containing session, operation, module, attempt, duration, status, and
  relevant log paths.

The Phase 3 implementation writes these results below the canonical session
state directory and records the latest result in `module-progress.json`.
Sandbox lifecycle skills gate on `status: succeeded`; local-mode callers retain
their existing commands and defaults.

### Agent skills and context

- The existing coding standards, version tools, backend/frontend testing,
  dependency context, documentation, and lifecycle skills must be available in
  every supported agent runtime.
- Shared skills may be imported centrally, but session-generated context
  (`AGENTS.md`, `CLAUDE.md`, `GEMINI.md`, progress JSON, PRD files) must live in
  the isolated session workspace.
- Lifecycle gates remain authoritative: coding requires planned tasks; frontend
  testing requires completed implementation tasks; install/update/live tests
  must pass before completion.

### MCP and ports

- MCP must address Odoo by the Compose service name inside the sandbox network,
  not a host-global `localhost` port.
- Odoo, MCP, debug, and test ports must be private unless explicitly published.
- Host ports must be dynamically assigned by default and recorded in the
  session manifest. Fixed ports are permitted only for an explicitly selected
  single-session compatibility mode.

### Logs and diagnostics

- All output must carry at least session ID, Odoo version, module, service, and
  timestamp as metadata or filename context.
- `docker compose logs`, Odoo file logs, module-operation results, test results,
  MCP logs, and agent/session events must be discoverable from one session log
  command.
- Destroying a session must offer or automatically perform an artifact export
  according to retention policy.
- Secret values must be redacted from logs and diagnostic bundles.

### Coding-platform integration

- CLI agents launch through Docker Sandbox kits/templates.
- VS Code and Cursor attach through the supported Sandbox SSH endpoint when
  its capability and authentication probe pass. On a pinned platform where the
  experimental endpoint fails that probe, `sbx exec` is the documented
  IDE-equivalent terminal fallback; direct host editing remains opt-in.
- GitHub Copilot and other CLI agents use the same `sandboxctl` and Compose
  contracts even when their agent-specific template differs.
- Platform adapters may translate launch/attach commands but must not define a
  separate Odoo runtime.

## Non-functional requirements

- **Reproducibility:** the same lock manifest produces equivalent service image
  digests and configuration on supported hosts.
- **Isolation:** two sessions may use the same module name and internal ports
  without collisions or cross-visible database/filestore state.
- **Startup target:** warm session ready within 90 seconds; cold start and image
  pull are measured separately rather than hidden.
- **Reliability:** a failed Odoo or module operation must not terminate sibling
  sessions; retries are bounded and observable.
- **Resource control:** configurable CPU, memory, Docker-volume size, maximum
  concurrent sessions, idle timeout, and retention limits.
- **Security:** non-root Odoo process, deny-by-default outbound network, no host
  Docker socket mount, scoped secrets, and least-privilege workspace mounts.
- **Portability:** macOS Apple Silicon, Windows 11, and supported Ubuntu hosts;
  multi-architecture image validation for amd64 and arm64 where upstream images
  permit it.

Phase 2 validates dev-image construction for both amd64 and arm64 and validates
the concurrent runtime matrix on the designated Ubuntu amd64 KVM host. Arm64
runtime support remains unclaimed until a supported arm64 Sandbox host executes
the same controller contract.

## Acceptance scenarios

1. Create Odoo 17, 18, and 19 sessions concurrently; install a smoke module in
   each; verify all health, RPC, logs, and cleanup checks pass.
2. Create two Odoo 19 sessions for the same module; make different changes and
   database records; prove neither source nor data crosses sessions.
3. Kill Odoo, PostgreSQL, and the agent separately; verify diagnostics and
   recovery behavior, with sibling sessions unaffected.
4. Stop and restart a session; verify its Git changes, database, filestore,
   installed images, agent history, and progress survive as documented.
5. Destroy a session; verify retained artifacts exist and database/filestore
   volumes are removed when requested.
6. Attempt disallowed network and filesystem access; verify it is blocked and
   appears in policy diagnostics without exposing credentials.
7. Run `/plan-analysis`, `/start-coding`, and `/testing` through Codex and one
   IDE adapter against the same runtime contract. Prefer SSH attach; accept the
   documented `sbx exec` terminal adapter only after recording a reproducible
   failure of the pinned experimental SSH authentication probe.

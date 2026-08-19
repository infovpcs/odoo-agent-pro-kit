# Docker Sandbox Technical Design

## Architecture decision

Use Docker Sandboxes as the outer security and agent boundary, and Docker
Compose inside each sandbox as the Odoo application boundary.

```text
Developer / IDE / Fleet controller
                 |
          sbx CLI and SSH
                 |
  +--------------+----------------------------------+
  | Docker Sandbox microVM: one session             |
  |                                                  |
  |  Agent runtime + imported Odoo skills            |
  |        |                                         |
  |        +-- isolated Git clone / session context  |
  |        |                                         |
  |        +-- sandboxctl -> manage_modules.sh       |
  |                         |                        |
  |                 private Docker daemon            |
  |                         |                        |
  |       +-----------------+------------------+     |
  |       | Compose project: session ID        |     |
  |       |                                    |     |
  |       |  Odoo 17/18/19 <----> PostgreSQL   |     |
  |       |       |                 |          |     |
  |       |  custom addons      DB volume      |     |
  |       |  filestore volume   healthcheck    |     |
  |       +------------------------------------+     |
  |             |                                    |
  |       MCP + structured logs                      |
  +--------------------------------------------------+
                 |
       explicit dynamic host ports
```

Each microVM has a separate Docker daemon and filesystem, so Compose project
names, container ports, network names, and volume names may be identical
internally without colliding with other sessions. Session IDs are still used in
names and logs to simplify diagnosis and future non-sandbox execution.

## Why this boundary

- Building Odoo directly into an agent template couples agent release cadence
  to three Odoo runtimes and makes cross-agent support expensive.
- Mounting one host workspace into several write-enabled sandboxes does not
  isolate source changes.
- Sharing host PostgreSQL or fixed host ports reintroduces concurrency conflicts.
- A Compose stack is independently testable in CI without requiring an agent,
  while Docker Sandbox tests validate the outer isolation and integrations.

## Proposed repository layout

```text
sandbox/
  README.md
  bin/sandboxctl
  compose/compose.yaml
  config/
    odoo.conf.template
    versions.yaml
  images/odoo-dev/Dockerfile
  kits/
    odoo-mixin/spec.yaml
    odoo-codex/spec.yaml
  scripts/
    entrypoint.sh
    healthcheck.sh
    collect-logs.sh
    session-manifest.sh
  schemas/
    session.schema.json
    operation-result.schema.json
  tests/
    smoke.sh
    isolation.sh
    lifecycle.sh
    failure-injection.sh
    integration-codex.sh
```

The exact kit format is intentionally isolated under `sandbox/kits/` because
Docker currently marks kits as experimental. `sandboxctl` owns the stable
project-facing contract and checks the installed `sbx` version/capabilities.

## Image strategy

### Outer agent template

Create one template per supported agent only when customization is needed:

```text
docker/sandbox-templates:codex-docker -> odoo-agent-codex:<kit-release>
docker/sandbox-templates:claude-code-docker -> odoo-agent-claude:<kit-release>
docker/sandbox-templates:copilot-docker -> odoo-agent-copilot:<kit-release>
```

The template contains `sandboxctl`, Compose files, JSON tools, Git helpers,
PostgreSQL client, log collection utilities, and validated Odoo skills. It does
not contain API keys, Odoo source checkouts, databases, or custom modules.

### Inner Odoo images

Build `odoo-dev:17`, `odoo-dev:18`, and `odoo-dev:19` from the corresponding
official Odoo image, adding only development/test dependencies, a healthcheck,
and a small entrypoint. Release manifests pin the final images by digest.
Every 17/18/19 image build verifies Odoo's required `wkhtmltopdf` and
`wkhtmltoimage` 0.12.6 patched-Qt renderer. Report-rendering tests must retain
HTTP because wkhtmltopdf fetches CSS and other assets from Odoo itself.

Do not use `pip install odoo-bin` as the runtime source. The current local setup
uses Odoo Git checkouts while the official image uses packaged Odoo; tests must
confirm that all existing management and addon paths work against the chosen
image. If source-level core debugging is required, offer a separate
`runtime=source` profile rather than changing the default image.

Use a compatible pinned PostgreSQL major after validating it against all three
Odoo versions. Keep the Postgres image in the version lock file so upgrades are
explicit.

## Compose contract

Required services:

- `db`: PostgreSQL with healthcheck and session-private named volume.
- `odoo`: selected version image, depends on healthy `db`, mounts custom addons,
  configuration, filestore, and result/log paths.
- `mcp` (profile `mcp`): current Odoo MCP server configured with `ODOO_URL` set
  to `http://odoo:8069` and its session database.

Optional profiles:

- `browser`: browser test dependencies.
- `observability`: local log collector for development of the logging pipeline.
- `enterprise`: private read-only enterprise addons mount.

All services use the internal Compose network. Only Odoo HTTP, MCP, and debug
ports selected by the user are published from the microVM to the host.

## Workspace and Git model

Default concurrent mode is Docker Sandbox clone mode:

1. The host repository is mounted read-only as Sandbox source.
2. Docker Sandbox creates an internal clone at the checked-out host ref.
3. `sandboxctl` creates/checks a session branch before writing.
4. Custom addons are bind-mounted from that internal clone into the Odoo
   container.
5. The agent commits or exports a patch before destructive cleanup.

Direct mode is supported for a single interactive session and must display a
collision warning if another direct session targets the same workspace.

For development that starts from a non-Git Odoo workspace, `sandboxctl` first
creates a session-owned copy; it must not use a shared read-write mount.

## Session state machine

```text
requested -> provisioning -> starting -> ready -> active
                 |             |          |        |
                 +-----------> failed <---+--------+
                                             |
                                    stopping -> stopped
                                             |       |
                                             +-> destroying
                                                    |
                                              exported -> destroyed
```

Every transition is idempotent. A lock prevents two controller processes from
mutating one session concurrently. `failed` retains enough state for logs and
recovery; it does not imply immediate deletion.

## Configuration hierarchy

Highest priority first:

1. Explicit `sandboxctl` flags.
2. Session manifest values.
3. Project `.sandbox.env` (non-secret values only).
4. Version configuration in `sandbox/config/versions.yaml`.
5. safe defaults.

The Phase 2 version contract is data-driven:

| Series | RPC lifecycle | Odoo image definition | Database |
| --- | --- | --- | --- |
| 17.0 | XML-RPC `/xmlrpc/2` | pinned 17 Dockerfile/base index | PostgreSQL 15 |
| 18.0 | XML-RPC `/xmlrpc/2` | pinned 18 Dockerfile/base index | PostgreSQL 15 |
| 19.0 | JSON-2 `/json/2` with a short-lived API key | pinned 19 Dockerfile/base index | PostgreSQL 15 |

The controller reads these values from `sandbox/config/versions.yaml`; it does
not infer protocol behavior from hard-coded version checks. Fixture source is
copied into session-private state and its manifest series is resolved before
the Compose stack starts.

The existing `.env` names remain supported through an adapter, but new code
uses explicit container-safe values such as:

```text
ODOO_VERSION=19
ODOO_DB_HOST=db
ODOO_DB_PORT=5432
ODOO_DB_NAME=session_db
ODOO_RPC_URL=http://odoo:8069
ODOO_CUSTOM_ADDONS=/workspace/custom-addons
ODOO_LOG_FILE=/workspace/.sandbox/logs/odoo.log
COMPOSE_PROJECT_NAME=<session-id>
SESSION_ID=<session-id>
MODULE_NAME=<module>
```

Application login credentials and PostgreSQL credentials must use distinct
variable names. This corrects the current ambiguity in MCP and local setup
configuration.

## `manage_modules.sh` adaptation

Preserve its user-facing operations and error extraction, but separate three
layers:

1. Environment resolution and validation.
2. Runtime executor (`local` or `compose`).
3. Install/update/test/log parsing operation.

For `compose`, an operation resembles:

```text
docker compose exec -T odoo odoo \
  --config /etc/odoo/odoo.conf \
  --database <session-db> \
  --stop-after-init \
  --init|--update <module>
```

The final implementation must use the flags supported by the selected official
image and must serialize module mutations within one session. Different
sessions require no shared database lock.

Phase 3 implements this boundary with `ODOO_EXECUTOR=local|compose` and keeps
the Compose host bind-mount config (`ODOO_CONFIG_FILE`) distinct from the
container CLI path (`ODOO_EXEC_CONFIG_FILE`). `sandboxctl module` supplies the
session environment, and `manage_modules.sh` owns database-state resolution,
bounded post-operation health, result JSON, and isolated progress state.

## Logging and observability

Each session has a `.sandbox/` directory ignored by Git:

```text
.sandbox/
  session.json
  events.jsonl
  logs/{agent,controller,compose,odoo,postgres,mcp}.log
  results/<operation-id>.json
  tests/{junit.xml,coverage.xml,screenshots/}
  diagnostics/<timestamp>.tar.gz
```

`sandboxctl logs` merges or selects sources and prefixes streamed lines with
session/service metadata. `collect-logs.sh` captures Compose state, health,
resource usage, recent service logs, operation results, and policy diagnostics.
It redacts known secret patterns before export.

The first release uses files/JSONL and standard Docker logs. A later adapter may
forward OpenTelemetry logs to Loki/OpenSearch/Splunk without changing producers.

## Secrets and network policy

- Use `sbx secret`/OAuth for agent provider credentials. Never place secrets in
  `.env`, kit static files, image layers, or saved templates.
- Use Docker Sandbox network policy with a minimal per-session allowlist for
  source registries, package registries, Odoo sources, and the selected model
  provider.
- Do not mount `/var/run/docker.sock` from the host. The sandbox's private Docker
  daemon is the only daemon the agent may control.
- Mount enterprise addons and signing material read-only and only in sessions
  that explicitly request them.
- Bind published ports to loopback; publish none by default.
- Run Odoo as its image's non-root user and avoid privileged inner containers.

## Skills and agent integration

- Import/share stable Odoo skills through Docker Sandbox where supported, with a
  versioned kit fallback for other agents.
- Generate agent-specific context from `context-templates/` at session creation.
- Extend SessionStart detection to read `.sandbox/session.json` rather than infer
  a version from whichever Odoo directory happens to exist.
- Change MCP discovery from fixed global ports to the session manifest/service
  address.
- Update the existing Community `/fleet` command for bounded single-host use so
  each module allocation calls `sandboxctl create`; progress aggregation reads
  exported session status, not shared mutable paths. Shared/remote scheduling,
  organization policy, and multi-host fleet management remain Pro features.
- Keep platform launchers thin: CLI launch, SSH attach, or editor task wrappers
  all call the same controller.

## Scalability and resource policy

Start with one host and enforce:

- maximum active sessions;
- per-sandbox VM/Docker disk budget;
- Odoo/PostgreSQL container CPU and memory limits;
- idle stop timeout;
- stopped-session retention;
- artifact retention and maximum size;
- image pre-pull/cache warming for 17/18/19.

When a remote control plane is needed, keep `session.json`, operation results,
and controller commands as the Community/Pro compatibility boundary. Do not put
a remote scheduler or Kubernetes dependency into the Community runtime.

## Test strategy

### Static and unit

- Shell lint and unit tests for version resolution, naming, config precedence,
  redaction, result schemas, and idempotent state transitions.
- Compose validation and kit validation.
- Image vulnerability/license reporting as a release check, with an explicit
  exception process rather than silent failures.

### Per-version integration matrix

For each of 17, 18, and 19:

1. Cold create and warm create.
2. Database/Odoo health.
3. Base login and RPC protocol check.
4. Install a fixture module with model, access rule, view, and data.
5. CRUD through XML-RPC for 17/18 and the supported Odoo 19 API path.
6. Update the fixture module and verify schema/data behavior.
7. Run backend tests and browser smoke tests.
8. Verify MCP model discovery.
9. Stop/start persistence.
10. Export and destroy cleanup.

### Concurrency and fault tests

- At least six sessions concurrently: two per Odoo version.
- Same module and internal database name in two sessions.
- Odoo crash, PostgreSQL restart, disk pressure, invalid addon, denied network,
  interrupted install, agent exit, and controller restart.
- Verify no sibling failure, source cross-write, data leak, fixed-port collision,
  orphaned process, or unbounded retry.

### Platform acceptance

- Codex CLI end-to-end lifecycle.
- One additional CLI agent end-to-end.
- VS Code SSH attach, edit, test, and log view when the pinned SSH probe passes;
  otherwise the documented `sbx exec` terminal adapter after recording the
  experimental endpoint failure.
- Cursor SSH attach or the same documented `sbx exec` equivalent.
- CI runtime-only Compose matrix on amd64, plus arm64 where available.

## Compatibility and migration

Ship the sandbox path alongside local mode for one deprecation cycle:

```text
./bootstrap.sh --runtime local
./bootstrap.sh --runtime sandbox --versions 17,18,19
```

Existing local workspaces are never silently moved or mounted read-write into
fleet sessions. A migration command imports a selected custom-addons Git repo,
generates non-secret configuration, and reports unsupported assumptions.

The Phase 7 migration implementation requires a clean Git source and creates a
secret-filtered copy under ignored staging state. Release upgrades compare lock
contracts and rebuild disposable sessions. Rollback restores prior tested lock
files and, where data is required, an explicit compatible database backup into
a new session; persisted database or schema state is never downgraded in place.

## Major risks

- Docker Sandbox kits and SSH are evolving: isolate them behind version checks
  and a stable wrapper.
- Odoo 19 API behavior and image patch releases change: pin digests and maintain
  version-specific smoke tests.
- Nested Docker consumes substantial disk/RAM: enforce quotas and warm only the
  versions actively used.
- Clone-mode work can be lost on destroy: require commit/patch export checks.
- Enterprise addons licensing: never copy them into public artifacts.

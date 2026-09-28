# Odoo Docker Sandbox runtime

The inner Compose runtime supports Odoo 17, 18, 19, and 20 through one controller.
Run it inside
the designated Docker Sandbox microVM (or directly against a disposable Docker
daemon for development):

```bash
sandbox/bin/sandboxctl create --version 19 --module sandbox_fixture
sandbox/bin/sandboxctl status <session-id>
sandbox/bin/sandboxctl exec <session-id> -- odoo --version
sandbox/bin/sandboxctl logs <session-id> --service odoo
sandbox/bin/sandboxctl stop <session-id>
sandbox/bin/sandboxctl start <session-id>
sandbox/bin/sandboxctl export <session-id>
sandbox/bin/sandboxctl destroy <session-id>
```

Version-specific image locks, Dockerfiles, addons paths, PostgreSQL dependency,
and RPC protocol live in `config/versions.yaml` and `config/images.lock`.
Odoo 17/18/19 run on PostgreSQL 15; Odoo 20 needs PostgreSQL 16 (`MIN_PG_VERSION`)
and runs on `POSTGRES_16`. Docker Hub has no `odoo:20.0` image yet, so
`images/odoo-dev/20.Dockerfile` reproduces the official `odoo/docker` 20.0
recipe (commit `d5431604`, sha1-checked Odoo nightly deb and wkhtmltopdf, helper
files sha256-checked) on the pinned `ubuntu:noble` digest (`ODOO_20_BASE`). One
deviation: the pgdg key is fetched with `curl` over HTTPS and must match the pinned
fingerprint, because `gpg --recv-keys` fails inside sbx microVMs. The
first Odoo 20 session on a host builds it (a few minutes; it needs Ubuntu apt,
`apt.postgresql.org`, `keyserver.ubuntu.com`, `nightly.odoo.com`, the npm registry,
and GitHub release assets, all on the `odoo-mixin` kit allow-list, so create the
microVM with `sandbox/bin/sandbox-agent create`, which attaches the kit). Once Hub
publishes `odoo:20.0`, pin that digest and cut the Dockerfile down to the dev layer.
Odoo 20 replaced `ir.model.access` with `ir.access`, so the fixture gets its
Odoo 20 files from `fixtures/_overlays/20/` (a `.remove` file lists deletions).
Each Odoo 17/18/19/20 development image build verifies the image's
`wkhtmltopdf` and `wkhtmltoimage` 0.12.6 patched-Qt executables. This is the
renderer version Odoo requires for styled PDFs with headers and footers; do not
replace it with an arbitrary distribution package. Compose-backed module tests
keep HTTP enabled so report rendering can retrieve Odoo's own CSS and assets.
The controller also sets `report.url=http://localhost:8069` in each sandbox
database, avoiding an externally tunneled `web.base.url` that wkhtmltopdf
cannot reach from inside the Odoo container.
Odoo 17 and 18 lifecycle checks use the documented XML-RPC endpoints. Odoo 19
and 20 use the JSON-2 endpoint with a one-day, session-generated API key; the key and
the distinct XML-RPC password remain only in the ignored mode-`0600`
`runtime.env`.

Runtime state is written under `.sandbox/sessions/<session-id>/`. Generated
credentials are distinct from application credentials and excluded from Git.
The private environment is mode `0600`; the generated config is mode `0644` so
the non-root image user can read a Linux bind mount. Neither file may be copied
into diagnostic evidence. Images are pinned
to immutable multi-architecture index digests in `config/images.lock`.
The session-scoped logs and results drop zones are writable across native Linux
host/container UID mappings; they must contain artifacts only, never secrets.

`create` waits a bounded 180 seconds by default. A readiness failure records
Compose state and the last 200 service log lines under the session diagnostics
directory, marks the manifest failed, and emits a failed operation result.

The fixture is intentionally public and contains no Enterprise source. Each
session receives a private copy whose manifest series matches the selected
Odoo version. Run the concurrent amd64 runtime matrix with
`sandbox/tests/lifecycle.sh`, and validate both amd64 and arm64 image builds
with `sandbox/tests/multiarch-build.sh`. `SANDBOX_LIFECYCLE_VERSIONS="19"`
limits the matrix to the listed versions. The lifecycle also renders one real PDF
(`base.ir_module_reference_print`, `scripts/report-pdf-smoke.py`) inside each
running session.

To run real modules instead of the fixture, pass `create --import DIR`: it copies
every Odoo module of a `scripts/migrate-local.py` staging tree (or one module
directory) into the session and refuses symlinks that leave the tree. `--module`
must name one of the imported modules.
`--requirements FILE` adds the modules' PyPI dependencies. Only
`name[extras] specifiers` lines are accepted (no pip options, URLs, paths or
markers). They are built by `images/odoo-dev/requirements.Dockerfile` on the pinned
dev image as a `--system-site-packages` venv overlay, so only missing or too-old
packages are installed. The image is tagged `<dev image>-req<sha256[:12]>` and
reused across sessions with the same file; `pip freeze` of the overlay goes to
`results/requirements-freeze.txt`. The build fails fast when the overlay breaks
Odoo's own imports. Example: requirements that upgrade `cryptography` break Odoo
17's Debian pyOpenSSL. Kit 0.7.0 allows `pypi.org` and `files.pythonhosted.org`
for this build.

```bash
sandbox/bin/sandboxctl create --version 20 --session mig20 --module vpcs_llm_provider \
    --import .sandbox/imports/20-vpcs-apps \
    --requirements .sandbox/imports/20-vpcs-apps/vpcs_llm_provider/requirements.txt
```

The MCP sidecar (`mcp-sidecar/mcp_up.sh`) passes the session's `ODOO_API_KEY`, so on
19 and 20 it uses `/json/2` with the `rpc`-scope key that `create` generates; the
default ports are 8765/8766/8767/8768 for 17/18/19/20.

In Docker Cloud Sandboxes, `docker exec` into running containers does not work,
so health checks never pass. Export `SANDBOX_EXEC_MODE=run` before `create`: it
is recorded in `runtime.env`, and the controller, `manage_modules.sh`, and
`lifecycle.sh` then use one-shot `compose run --rm --no-deps` containers and
readiness probes over the Compose network (`pg_isready -h db`,
`http://odoo:8069/web/health`). The default `exec` mode is unchanged. See
`docs/docker-sandbox/phase-9/cloud-runbook.md`.

Phase 3 adds `sandboxctl module <session> install|update|test <module>`. The
controller delegates to `manage_modules.sh`, which selects local or Compose
execution, queries session database state, waits for health, and writes result
JSON plus isolated progress. See `docs/docker-sandbox/phase-3/live-test.md`.

Phase 4 layers the agent-neutral `sandbox/kits/odoo-mixin` onto Docker's
built-in Codex, Claude, or Copilot agents. `sandbox/bin/sandbox-agent` performs
the pinned CLI, kit, and policy preflight and provides thin create, SSH attach,
test, and log adapters. Artifact versions and the kit digest are pinned in
`config/artifacts.lock`; run `scripts/validate-artifacts.sh` before packaging.
Shared-skills, scoped secret/OAuth, policy, VS Code, and Cursor setup are in
`docs/docker-sandbox/phase-4/agent-adapters.md`.

Phase 5 replaces shared-workspace `/fleet` threads/subprocesses with the bounded
single-host `sandbox/bin/sandbox-fleet` coordinator. Every module task receives
one outer Sandbox, normalized name, branch, inner runtime, dynamic port, and
private result manifest. See
`docs/docker-sandbox/phase-5/local-concurrency.md` for capacity, cancellation,
retention, aggregation, and cleanup-guard behavior.

Phase 6 adds prefixed multi-service log streaming, redacted diagnostic bundles,
stable JUnit/coverage/browser paths, opt-in JSONL telemetry, bounded recovery,
and explicit `pg_dump`/`pg_restore` snapshots. See
`docs/docker-sandbox/phase-6/observability-recovery.md` for commands, retention
boundaries, and the failure-injection contract.

Phase 7 adds CI, pinned release verification, dependency inventory, benchmark
recording, guarded local migration, platform runbooks, and rollback rules. See
`docs/docker-sandbox/phase-7/operator-runbooks.md` and load the
`DockerSandboxOperations` skill for agent-led setup.

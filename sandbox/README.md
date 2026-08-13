# Odoo Docker Sandbox runtime

The inner Compose runtime supports Odoo 17, 18, and 19 through one controller.
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
Odoo 17 and 18 lifecycle checks use the documented XML-RPC endpoints. Odoo 19
uses its JSON-2 endpoint with a one-day, session-generated API key; the key and
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
with `sandbox/tests/multiarch-build.sh`.

Phase 3 adds `sandboxctl module <session> install|update|test <module>`. The
controller delegates to `manage_modules.sh`, which selects local or Compose
execution, queries session database state, waits for health, and writes result
JSON plus isolated progress. See `docs/docker-sandbox/phase-3/live-test.md`.

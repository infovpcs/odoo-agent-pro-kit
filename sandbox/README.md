# Odoo Docker Sandbox runtime

Phase 1 provides the inner Compose proof of concept for Odoo 19. Run it inside
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

The Phase 1 fixture is intentionally public and contains no Enterprise source.
Module install/update/RPC lifecycle helpers are exercised by the live-test
script; integration with `manage_modules.sh` remains Phase 3 work.

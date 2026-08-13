# Existing kit integration LIVE TEST

Phase 3 connects the module manager, SessionStart hook, MCP configuration,
lifecycle commands, and testing skills to the session controller while
retaining local mode.

## Evidence captured on 2026-08-13

On the designated Ubuntu 24.04 x86_64 KVM host, `docker-sbx` 0.38.0 created an
8-GiB Codex Sandbox. Odoo 19 and PostgreSQL 15 passed install, database-aware
install-to-update resolution, data-changing update, test execution, JSON-2
CRUD (`server_version: 19.0`), structured result/progress gates, SessionStart
manifest discovery, and a 61,597-byte Odoo log gate. Session destruction left
no matching volume, and the outer Sandbox was removed.

After OpenAI OAuth was configured through the host Sandbox secret store, a
fresh Codex Sandbox (`codex-cli 0.146.0`, `gpt-5.6-sol`) literally executed the
three lifecycle commands against session `19-fixture-phase3-agent`:

- `/plan-analysis 19 sandbox_fixture` installed the fixture through
  `sandboxctl module`, performed JSON-2 discovery, and wrote its handoff.
- `/start-coding 19 sandbox_fixture` performed a data-changing update, emitted
  succeeded update/test results, and passed JSON-2 CRUD on Odoo 19.0.
- `/testing 19 sandbox_fixture` emitted a succeeded update result and retrieved
  71,498 bytes through `sandboxctl logs --service odoo`.

All handoffs recorded exact operation-result paths. No lifecycle skill invoked
raw `odoo-bin`, no agent committed changes, all session volumes were removed,
and `sbx ls` reported no remaining Sandbox.

The first install attempt exposed and then verified a fix for config path
precedence. A later RPC check exposed and verified bounded Odoo health waiting
after module operations. Both failures were reported rather than treated as
passes.

The Intel macOS workstation passed shell/Python and contract tests. Its real
container attempt stopped before provisioning because Docker was unavailable;
no container or volume was created.

## Result

The Phase 3 LIVE TEST and exit gate pass. OAuth credentials remained in the
Docker Sandbox secret store and were not written to the repository or evidence.

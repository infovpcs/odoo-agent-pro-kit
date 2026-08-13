# Phase 6 LIVE TEST evidence

Date: 2026-08-13. Host: Oracle Ubuntu 24.04.4 LTS x86_64, kernel
6.17.0-1018-oracle, nested KVM, 2 vCPU, 15 GiB RAM, 45 GiB root disk. Docker
Sandbox CLI: `v0.38.0 c022b14634c4bea846ca12870d1d5e97d5868b54`.

Two clone-mode Codex Sandboxes used the constrained-host validation override of
1 CPU and 3 GiB each. Both ran Odoo 19 and PostgreSQL 15 through independent
inner Compose projects, `phase6-primary` and `phase6-sibling`.

## Recovery and evidence

The primary installed and tested `sandbox_fixture`; JUnit, coverage, and
explicit browser `not_run` JSON appeared at the documented stable paths. The
test then injected:

- Odoo and PostgreSQL `SIGKILL`, each followed by a diagnostic and bounded
  `sandboxctl recover`;
- `definitely_invalid_phase6_module`, which produced exit 2, a failed operation
  result, and recoverable state;
- a one-second `SIGINT` timeout during module update;
- a bounded 128 MiB disposable disk-pressure file;
- controller interruption/re-entry followed by recovery; and
- `sbx policy check network denied-phase6.invalid:443`, which returned policy
  exit 1 with `no matching allow rule (default deny)`.

Eleven resulting bundles collectively covered `odoo-crash`, `postgres-crash`,
`invalid-module`, `interrupted-operation`, `disk-pressure`,
`controller-restart`, `denied-network`, and `telemetry-proof`. Every archive
contained the required state, process, resource, service-log, policy, event,
result, and metadata evidence. Scanning every archive against all generated
runtime credential values returned:

```text
BUNDLES=11 REDACTION=passed REASONS=passed
```

The independent sibling reported healthy Odoo and PostgreSQL after all primary
faults: `SIBLING_HEALTH=passed`.

## Backup, telemetry, and logs

`pg_dump -Fc` captured a database containing one probe row. A second row was
inserted, `sandboxctl restore` applied the snapshot, and the post-restore query
returned `1`. Odoo restarted healthy. File telemetry emitted a JSONL
`diagnostic_bundle` event, and unified log output began with:

```text
[phase6-primary/19.0/sandbox_fixture/odoo]
```

## Issues found and corrected

The first candidate failed before Docker startup because nested test artifact
directories lacked parent creation. The controller now creates those paths
with `parents=True`. An interrupted cold pull also demonstrated that retrying
with new credentials against the retained old database volume fails safely and
produces a redacted create bundle; the disposable volume was explicitly reset
before the accepted clean run.

The live test also found that the legacy module manager returned success for a
missing module. `sandboxctl module` now validates that a session-private module
manifest exists and emits deterministic failed/recoverable evidence otherwise.

Docker login JWKS connectivity and refresh-lock timeouts intermittently
detached long `sbx exec` output streams. Actual operation state, processes,
results, bundles, and health were checked inside the microVM; no detached
command was counted merely from its client return.

## Cleanup

Both sessions were exported, and both inner Compose projects removed their
containers, networks, database, filestore, and cache volumes. Both outer
Sandboxes were force-removed through the explicit test cleanup path. `sbx ls`
reported no Sandboxes, the disposable `/home/ubuntu/phase6-src` tree and policy
file were removed, and the host returned to 7.5 GiB used with 37 GiB free.

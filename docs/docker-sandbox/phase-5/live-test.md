# Phase 5 LIVE TEST evidence

Date: 2026-08-13. Host: Oracle Ubuntu 24.04.4 LTS x86_64, kernel
6.17.0-1018-oracle, nested KVM, 2 vCPU, 15 GiB RAM, 45 GiB root disk. Docker
Sandbox CLI: `v0.38.0 c022b14634c4bea846ca12870d1d5e97d5868b54`.

The host began with no Sandboxes, 37 GiB free disk, and 13 GiB available RAM.
The shipped resource policy remains 2 CPUs/8 GiB per session; this constrained
validation host used the supported 1 CPU/2 GiB override for each outer microVM.
The disk target remained the advisory 40 GiB value.

## Commands and results

Six allocations were created with the Community coordinator, two per version:

```bash
for version in 17 17 18 18 19 19; do
  sandbox/bin/sandbox-fleet create --version "$version" --module sandbox_fixture
done
sandbox/bin/sandbox-fleet status
```

All six were simultaneously `ready`, used unique
`odoo-<version>-sandbox-fixture-<id>` names and matching `sandbox/<session>`
branches, and had distinct loopback publications in the observed 32771-32781
range. `sandboxctl module <session> install sandbox_fixture` returned zero for
all six.

The two Odoo 19 duplicate-module sessions received `phase5-source-A` and
`phase5-source-B` in their private addon copies. Each marker was absent from
the sibling. SQL inserted `db-marker-A` and `db-marker-B`; each database query
returned only its own marker. Private Odoo logs were non-empty; one measured
35,019 bytes at its session-specific path.

A missing `manage_modules.sh` was injected into only
`odoo-17-sandbox-fixture-356126`. The coordinator returned exit 1 and reported
`failed: 1, ready: 5`; every sibling status still reported healthy services.
Earlier invalid-module and stopped-database probes returned success through the
legacy test path and were explicitly not accepted as failure evidence.

Two simultaneous `sandboxctl stop` calls against one session completed with
`LOCK_STOP_RC=0`; the second idempotent transition waited on the session lock.
`start` restored the session. A recreated Odoo 19 container reported inner
limits `3221225472 1000000000` (3 GiB and 1.0 CPU).

An unprotected coordinator destroy returned exit 1 with
`destructive cleanup refused`. Each disposable clone then made a test commit
and recorded the `commit` protection method.

## Issues found and corrected during validation

Docker clone mode follows the committed host ref and does not include host
working-tree changes. The first allocations therefore contained the Phase 4
inner controller. The Phase 5 candidate controller and Compose file were copied
from the sandbox's read-only source mount into every disposable clone before
lock, resource, and destructive-cleanup validation.

The live test also found and fixed three candidate defects: the existing-state
lock path called `mkdir` without `exist_ok`, an inner cleanup failure did not
retain the outer Sandbox, and noninteractive `sbx rm` lacked its required
`--force` flag. CPU limits now adapt to the configured outer CPU count. The
corrected paths were rerun before the exit gate.

## Cleanup

Inner Compose teardown showed removal of containers, networks, database,
filestore, and cache volumes. `sbx rm --force` removed every outer Sandbox;
`sbx ls` returned `No sandboxes found`. All six tested loopback ports were
closed. The host ended at 7.5 GiB disk used with 13 GiB available RAM. The exact
disposable `/home/ubuntu/phase5-src` tree was removed after verification.

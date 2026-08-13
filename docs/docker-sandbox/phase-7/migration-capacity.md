# Local migration and capacity measurement

## Local-to-sandbox migration

`migrate-local.py` accepts only a clean Git repository. It copies source into
an ignored staging directory and excludes `.git`, `.env`, Odoo config, logs,
and bytecode. It never imports a database, filestore, virtual environment, or
Enterprise source. Review the generated report, then create the session and
run install/test gates. Keep local mode available for the documented
deprecation cycle; migration is always explicit and reversible.

Compatibility assumptions to review include absolute host paths, fixed ports,
host PostgreSQL roles, localhost service addresses, undeclared Python/system
packages, Enterprise dependencies, and filesystem writes outside Odoo data or
artifact directories.

## Measurements

Wrap each real acceptance command and retain JSONL evidence:

```bash
python3 sandbox/scripts/benchmark.py --label cold -- sandbox/tests/lifecycle.sh 19
python3 sandbox/scripts/benchmark.py --label warm -- sandbox/tests/lifecycle.sh 19
python3 sandbox/scripts/benchmark.py --label recovery -- sandbox/tests/phase6-live.sh
python3 sandbox/scripts/benchmark.py --label six-session -- sandbox/tests/phase6-live.sh
```

Measure host free disk before/after pulls, session create, test artifacts, and
cleanup. Record peak host and inner-container memory plus CPU pressure. Do not
publish estimates as measurements.

The shipped upper-bound default remains 2 CPU, 8 GiB RAM, and 40 GiB disk per
session with at most six active sessions; host capacity must lower it. On the
measured 2-vCPU/15-GiB/45-GiB Ubuntu host, six outer 1-CPU/2-GiB sandboxes can
boot, but six simultaneous cold inner builds caused load average ~82, only
289 MB available memory, and SSH starvation. Configure **one cold provision at
a time and at most two active constrained sessions** on this host. Six active
sessions require a larger host and a fresh load test; use at least 12 vCPU,
48 GiB RAM, and 240 GiB available disk as the initial unvalidated sizing input.
Retain at least 20 GiB free host disk. Reduce concurrency before reducing
PostgreSQL/Odoo memory below tested values. See `live-test.md` for evidence.

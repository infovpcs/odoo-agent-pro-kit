---
name: docker-sandbox-operations
description: Configure, migrate, operate, validate, benchmark, upgrade, roll back, and release the Odoo 17/18/19 Docker Sandbox runtime. Use for Docker Sandbox onboarding, platform setup, local-to-sandbox migration, session lifecycle, release acceptance, capacity measurement, or troubleshooting in this repository.
---

# Docker Sandbox Operations

## Establish context

1. Read repository `AGENTS.md`, `SESSION_CONTEXT.md`, and `docs/docker-sandbox/tasks.md`.
2. Work on only the current eligible phase. Never claim an unexecuted LIVE TEST.
3. Read `docs/docker-sandbox/phase-7/operator-runbooks.md` for the host platform.
4. Keep secrets out of Git, arguments, logs, diagnostics, skills, and images.

## Configure a host

1. Verify Git, Docker client/daemon, Compose, available CPU/RAM/disk, and the pinned `sbx` capability range in `sandbox/config/artifacts.lock`.
2. Use the Intel macOS workstation for repository, Docker, and registry checks. Run microVM/runtime acceptance on an Ubuntu 24.04+ KVM host. Treat other platform claims as unverified until their runbook matrix passes.
3. Run `./scripts/validate.sh` and `python3 sandbox/scripts/release-acceptance.py verify`.
4. Use `sandbox/bin/sandbox-agent preflight` before creating an outer agent Sandbox.

## Operate a session

Use `sandbox/bin/sandboxctl` for inner runtime lifecycle and module operations. Use `sandbox/bin/sandbox-fleet` only for bounded single-host concurrency. Never invoke raw `odoo-bin` for an install, update, or test lifecycle gate.

```bash
sandbox/bin/sandboxctl create --version 19 --module my_module
sandbox/bin/sandboxctl module <session> install my_module
sandbox/bin/sandboxctl module <session> test my_module
sandbox/bin/sandboxctl logs <session> --service odoo
sandbox/bin/sandboxctl export <session>
sandbox/bin/sandboxctl destroy <session>
```

Read `.sandbox/session.json` and operation-result JSON. Require `status: succeeded` before advancing a lifecycle gate.

## Migrate local work

Require a clean source Git repository, then stage a secret-filtered copy:

```bash
python3 sandbox/scripts/migrate-local.py --source /absolute/custom-addons --version 19 --name my_module
```

Review `migration-report.json`; do not silently move a workspace or import a production database.

## Release and rollback

Run the release verifier, Compose validation, CI smoke matrix, and documented clean-host LIVE TEST. Record benchmarks with `benchmark.py`. For rollback, restore the prior lock files and clean session data; restore a database only from an explicit compatible backup. Never downgrade persisted schema/database state in place.

Update implementation, README, requirements/design/runbooks, phase tasks, and `SESSION_CONTEXT.md` together. Run `./scripts/validate.sh` from a clean shell before a focused phase commit.

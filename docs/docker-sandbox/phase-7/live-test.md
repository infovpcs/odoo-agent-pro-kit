# Phase 7 LIVE TEST — 2026-08-13

## Platform and versions

- Host: Oracle Cloud Ubuntu 24.04 x86_64, Linux 6.17, nested KVM, 2 vCPU,
  15 GiB RAM, 45 GiB root disk.
- Docker Sandbox: `sbx` 0.38.0; diagnostics passed 8 checks with one
  update-check HTTP 403 warning.
- Outer template: `docker/sandbox-templates:codex-docker`.
- Outer validation Sandbox: 2 CPU, 11 GiB RAM. A 12 GiB request was correctly
  rejected by the 75%-of-host policy ceiling.
- Inner Docker: 29.7.1; Compose: 5.4.0; linux/amd64.
- Runtime locks: Odoo 17/18/19 and PostgreSQL 15 digests from `images.lock`;
  mixin 0.4.0 and `sbx` 0.38.x from `artifacts.lock`.

## Results

The clean staged Git repository passed the following inside a newly created
Codex Sandbox:

- Cold concurrent Odoo 17/18/19 lifecycle: build/pull, create, install,
  data-changing update, XML-RPC/JSON-2 CRUD, stop/start, export, destroy, and
  orphan-volume/network checks. Total full lifecycle: **435.525 seconds**.
- Warm repetition of the same full matrix: **118.385 seconds**. A separate
  warm Odoo 19 create-to-ready measurement was **42 seconds**, passing the
  90-second readiness target.
- Phase 6 recovery matrix: install/test artifacts, PostgreSQL backup/restore,
  Odoo and PostgreSQL crashes, invalid module, interrupted operation, disk
  pressure, controller recovery, and seven redacted bundles passed in
  **73.201 seconds**.
- Staged template, kit, Odoo image lock, PostgreSQL image lock, and both schema
  changes were detected; restoring prior files produced byte-identical
  rollback. Database rollback used explicit backup/restore rather than an
  in-place downgrade.
- A clean disposable local Git repository migrated through `migrate-local.py`;
  `.git` and secret/config patterns were excluded and the report stated
  `secrets_copied: false`.
- Real `sbx kit pack` validated mixin 0.4.0. Dependency/license inventory was
  generated without secrets.

## Six-session capacity result

Six 1-CPU/2-GiB Codex sandboxes created concurrently in **134 seconds**, with
unique ports. Starting six cold inner Odoo/PostgreSQL builds concurrently on
the 2-vCPU host exceeded safe capacity: load average reached about 82, available
memory fell as low as **289,169,408 bytes**, SSH banner delivery timed out, and
disk use grew from 7.5 GiB to 13 GiB during image pulls. This is a measured
capacity rejection, not a successful six-cold-provision claim.

The load driver was interrupted, the bounded controller attempts stopped, and
the Sandbox daemon was restarted. Restart required Docker device OAuth; the
user completed it. All six sandboxes were then removed. Final state was no
sandboxes, 14 GiB available memory, 7.5 GiB disk used, and no published Sandbox
ports. Phase 5 remains the successful six-session isolation proof; Phase 7
therefore limits this host to one cold provision at a time and recommends no
more than two active constrained sessions.

## Platform scope

Ubuntu 24.04 x86_64 KVM is the tested runtime platform. Intel macOS passed
repository, Docker daemon, Compose, and registry checks but cannot install the
arm64-only Sandbox cask. Apple Silicon macOS and Windows 11 runbooks are
published as candidate procedures; native runtime support remains unclaimed
until those clean-host matrices execute.

Raw non-secret evidence remains on the authorized host under
`/home/ubuntu/phase7-evidence`. The disposable source staging directory remains
for audit; no Sandbox, container daemon, port, or test runtime remains active.

GitHub Actions run `31701912811` passed after the authorized branch push:
repository/release validation and dependency inventory, Odoo 17/18/19 amd64
image builds, and all three Compose lifecycle smoke jobs. GitHub emitted a
non-blocking annotation that the pinned action majors targeting Node 20 were
being forced to Node 24 by the runner.

# Phase 0 Validation Baseline

This directory records the product assumptions tested before runtime
implementation begins.

- [`adr-0001-runtime-boundaries.md`](adr-0001-runtime-boundaries.md) approves
  the outer Sandbox/inner Compose architecture and compatibility boundaries.
- [`runtime-baseline.md`](runtime-baseline.md) selects PostgreSQL, records Odoo
  image architectures, licensing rules, resource defaults, and retention.
- [`sbx-capability-matrix.md`](sbx-capability-matrix.md) records the CLI contract
  and the current host blocker.
- [`live-test.md`](live-test.md) is the repeatable stock-sandbox acceptance run.

Phase 0 is complete. Repository, Docker daemon, and registry checks passed on
the available Intel macOS workstation, while `live-test.md` passed on the
designated Ubuntu 24.04 KVM host with the pinned `sbx` release.

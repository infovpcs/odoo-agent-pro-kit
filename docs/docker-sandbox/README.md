# Docker Sandbox Program Plan

This directory is the authoritative implementation plan for isolated,
concurrent Odoo 17.0, 18.0, and 19.0 development sessions. It consolidates the
earlier Docker Sandbox research into a versioned, test-gated product design.

## Documents

- `requirements.md` defines scope, users, acceptance criteria, and constraints.
- `design.md` defines the target architecture, session lifecycle, interfaces,
  security model, logging, and testing strategy.
- `tasks.md` is the ordered delivery backlog with release gates.
- `source-review.md` records the decisions made while consolidating the earlier
  setup research and prevents obsolete approaches from being reintroduced.
- `phase-0/` records architecture, runtime, CLI capability, and LIVE TEST
  evidence required before runtime implementation.

Approved session and operation-result contracts live in `sandbox/schemas/`.
Phase 1 runtime usage is documented in [`../../sandbox/README.md`](../../sandbox/README.md),
and its required microVM procedure is in [`phase-1/live-test.md`](phase-1/live-test.md).

## Recommended delivery decision

Use one Docker Sandbox microVM per agent/module session. Run an Odoo and
PostgreSQL Docker Compose project inside that microVM. Use clone mode by default
for concurrent write sessions, and give every session its own Git branch,
database, filestore, Compose project, log directory, and progress state.

Do not put Odoo itself into the Docker Sandbox template. The template is the
agent/tooling layer; version-pinned Odoo images and PostgreSQL belong to the
inner Compose runtime. This keeps Odoo 17/18/19 reproducible and independently
testable without rebuilding the agent template for every Odoo patch release.

## Delivery order

1. Build and validate a single Odoo 19 sandbox session.
2. Generalize the image and Compose contracts for Odoo 18 and 17.
3. Adapt `manage_modules.sh`, MCP startup, logs, and lifecycle commands.
4. Add bounded single-host concurrency, quotas, recovery, and coding-platform
   adapters. Shared or remote team fleet orchestration remains a Pro concern.
5. Run the concurrency, isolation, failure, and cross-platform acceptance suite.

The detailed exit criteria are in `tasks.md`.

Commercial packaging, repository boundaries, and go-to-market sequencing are
defined separately in [`../commercial/`](../commercial/README.md).

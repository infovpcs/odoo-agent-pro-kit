---
description: Parallel workspace orchestration across multiple Odoo modules for Odoo 17, 18, 19, or 20.
argument-hint: <17|18|19|20>
---

Use the `odoo_commanding_system` skill and load `fleet_workflow.md`. Execute it
for Odoo version $1. Allocate every module with `sandbox/bin/sandbox-fleet`;
never replace the Sandbox boundary with threads or subprocess agents sharing a
writable workspace. Aggregate only coordinator manifests and preserve sibling
sessions when one allocation fails or is cancelled.

Odoo 20 sessions run on PostgreSQL 16 and an image built from the official
`odoo/docker` 20.0 recipe (Docker Hub has no `odoo:20.0` tag yet), so the first
Odoo 20 allocation on a host builds that image and takes longer.

For hosts without local microVMs, `sandbox-fleet create --cloud` allocates each
session in a Docker Cloud Sandbox (billable shape and TTL from
`sandbox/config/concurrency.json`, owner-approved spend). Cloud sessions are
internal-only: no Odoo port is published, because `sbx --cloud ports` gives a
public URL. The code is shipped as a git bundle of a working-tree snapshot, and
`SANDBOX_SBX` can point at a non-native `sbx` client (see the cloud runbook).

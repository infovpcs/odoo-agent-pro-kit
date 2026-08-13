---
description: Parallel workspace orchestration across multiple Odoo modules for Odoo 17, 18, or 19.
argument-hint: <17|18|19>
---

Use the `odoo_commanding_system` skill and load `fleet_workflow.md`. Execute it
for Odoo version $1. Allocate every module with `sandbox/bin/sandbox-fleet`;
never replace the Sandbox boundary with threads or subprocess agents sharing a
writable workspace. Aggregate only coordinator manifests and preserve sibling
sessions when one allocation fails or is cancelled.

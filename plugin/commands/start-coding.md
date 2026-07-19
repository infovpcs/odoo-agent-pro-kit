---
description: Task-loop implementation with backend tests per task, for Odoo 17, 18, or 19. Requires a PRD (docs/tasks.md) — auto-routes to /plan-analysis if missing.
argument-hint: <17|18|19> [module_name]
---

Use the Skill tool to invoke the `odoo_commanding_system` skill, then load
`start_coding_workflow.md` from that same skill directory. Before starting,
check whether `{module_name}/docs/tasks.md` exists. If it does not, tell the
user and route to the `/plan-analysis` command first, then resume this
workflow once the PRD exists. Otherwise execute the workflow for Odoo
version $1 (ask the user for the version if $1 is not exactly one of 17, 18,
or 19), working through `docs/tasks.md` task-by-task with a backend test after
each task, per the `odoo_backend_testing` skill.

---
description: Frontend UI tests plus responsive documentation (index.html, screenshots) for Odoo 17, 18, or 19. Requires all tasks complete — auto-routes to /start-coding if not.
argument-hint: <17|18|19> [module_name]
---

Use the Skill tool to invoke the `odoo_commanding_system` skill, then load
`testing_workflow.md` from that same skill directory. Before starting, check
whether every task in `{module_name}/docs/tasks.md` is checked off. If any
are incomplete, tell the user and route to the `/start-coding` command first,
then resume this workflow once all tasks are done. Otherwise execute the
workflow for Odoo version $1 (ask the user for the version if $1 is not
exactly one of 17, 18, or 19), using the `agent_browser_automation` and
`odoo_module_documentation` skills for frontend tests and documentation assets.

In sandbox mode require a successful session `update` result before browser
testing and record the final `test` result. Never invoke `odoo-bin` directly.

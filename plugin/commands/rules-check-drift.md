---
description: Audit whether the rules files (CLAUDE.md / AGENTS.md / GEMINI.md / copilot-instructions.md) still match the code after recent changes, including PRD gate-state contradictions. Advisory — reports drift, never edits unless asked.
argument-hint: "[diff range, e.g. main...HEAD]"
---

Use the Skill tool to invoke the `odoo_rules_drift_check` skill, then follow its
Process steps 1 through 5 for the diff range in `$ARGUMENTS` (default: `git diff HEAD`,
falling back to `main...HEAD` when that is empty).

No Odoo version argument is required. Do not ask for one — the version is read from
`__manifest__.py` when a version-idiom claim needs checking.

This command is **advisory and read-only**. Report the drift table; apply edits only if
the user explicitly asks in a follow-up. Never mark a task `[x]`, never change a progress
percentage, and never write to an Odoo database.

Run Tier 2 database confirmation only if a live connection is already available — prefer
the in-process `odoo_search_models` / `odoo_get_fields` / `odoo_validate_field` /
`odoo_get_relationships` tools. If no connection is reachable, do not start a server:
report `tier: static-only` and list the claims left unverified.

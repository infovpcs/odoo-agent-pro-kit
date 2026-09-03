---
name: rules-check-drift
description: "Audit whether CLAUDE.md / AGENTS.md / GEMINI.md / copilot-instructions.md still match the code after recent changes, including PRD gate-state contradictions. Advisory and read-only."
argument-hint: "Optional diff range, e.g. main...HEAD"
---

You are running the Odoo **rules-check-drift** command.

## Setup
Load `.github/AgentSkills/OdooRulesDriftCheck/SKILL.md` — it is the execution guide.

No Odoo version argument is required. Use the diff range from the arguments, or default to
`git diff HEAD`, falling back to `main...HEAD` when that is empty.

## Execution
Follow **Process steps 1 through 5** from the skill:

- **Step 1**: read the diff and `git status --short`
- **Step 2**: load every rules file that exists; hold each concrete claim against the change set
- **Step 3**: flag only four things — now-false rule, drifted path map, new invariant, gate-state contradiction
- **Step 4**: run the Odoo drift catalog (paths, models, fields, manifest depends, version idiom, MCP ports, pruned run identifiers, rules-file disagreement)
- **Step 5**: Tier 2 database confirmation only if a connection is already reachable; otherwise report `tier: static-only`

## Hard Rules
- Advisory: report the drift table, apply edits only if explicitly asked.
- Never mark a task `[x]`, never change a progress percentage, never write to Odoo.
- Lean by default — when in doubt, suggest nothing.

Output: the skill's drift report, or "The rules files are still accurate for these changes — no edits needed."

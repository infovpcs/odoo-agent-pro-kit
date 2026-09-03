---
description: Odoo /rules-check-drift — audit CLAUDE.md / AGENTS.md / GEMINI.md / copilot-instructions.md against recent changes and PRD gate state. Advisory, read-only.
---

You are running the Odoo **`/rules-check-drift`** command.

## Ask First
Nothing. This command needs no Odoo version. If the user supplied a diff range
(e.g. `main...HEAD`), use it; otherwise default to `git diff HEAD` and fall back to
`main...HEAD` when that is empty.

## Step-by-Step Execution

// turbo
1. Load `AgentSkills/OdooRulesDriftCheck/SKILL.md` — read it fully.

2. **Step 1** — run `git diff <range> --stat`, `git diff <range>`, and `git status --short`.

3. **Step 2** — load every rules file in the skill's Audited column that exists.

4. **Step 3** — flag only the four drift classes: now-false rule, drifted path map,
   new durable invariant, gate-state contradiction.

5. **Step 4** — run the Odoo drift catalog table, including the two rows that a normal
   diff review misses: pruned backup/run identifiers, and rules files that disagree with
   each other because only one was edited.

6. **Step 5** — Tier 2 database confirmation only if a connection is already reachable.
   Never start a server. No connection → report `tier: static-only`.

7. Emit the skill's Output block. If nothing drifted, say so in one line.

## Hard Rules
- Advisory only. Do not apply edits unless the user explicitly asks in a follow-up.
- Never mark a task `[x]`, never change a progress percentage, never write to Odoo.
- When the phase table and `docs/tasks.md` disagree, `tasks.md` wins.

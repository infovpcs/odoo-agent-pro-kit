# rules-check-drift

> **Rules-file drift audit** — checks whether `CLAUDE.md` / `AGENTS.md` / `GEMINI.md` /
> `copilot-instructions.md` still match the code after recent changes, and whether any phase
> or status claim contradicts `docs/tasks.md`.
> Advisory and read-only. No gate, no version argument.

## Usage
```
/rules-check-drift
/rules-check-drift main...HEAD
```

## What This Does
1. Reads the diff (`git diff HEAD`, falling back to `main...HEAD`)
2. Loads every rules file that exists and holds each concrete claim against the change set
3. Reports four drift classes: now-false rule, drifted path map, new invariant, gate-state contradiction
4. Runs the Odoo drift catalog — paths, model/field names, manifest depends, version idiom, MCP ports, pruned run identifiers, rules-file disagreement
5. Optionally confirms model/field/ID claims against a live database, if one is already reachable

## Rules
- Advisory: reports drift, applies edits only if you explicitly ask.
- Never marks a task `[x]`, never changes a progress percentage, never writes to Odoo.
- Missing database connection downgrades to `tier: static-only` — it is not a failure.

## Instructions
Load `.cursor/AgentSkills/OdooRulesDriftCheck/SKILL.md` and follow its Process steps 1 through 5.

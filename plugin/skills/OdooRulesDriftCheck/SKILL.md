---
name: odoo_rules_drift_check
description: Use when finishing an Odoo task, before a merge, or before a context handoff, and the rules files (CLAUDE.md / AGENTS.md / GEMINI.md / copilot-instructions.md) may no longer match the code — moved script paths, renamed models or dropped fields, changed manifest depends, stale MCP ports, expired backup/run identifiers, or a phase table claiming Complete while docs/tasks.md still has open items.
version: 1.0.0
category: operations
odoo_versions: ["17.0", "18.0", "19.0"]
tags: ["odoo", "rules", "drift", "claude-md", "agents-md", "audit", "gate-state", "operations"]
---

# Odoo Rules Drift Check

Your rules files — `CLAUDE.md`, `AGENTS.md`, `GEMINI.md`, `copilot-instructions.md` — are a
**steering document, not documentation**: ground rules, conventions, and a current map of where
things live. Their only failure mode that matters is being **wrong**. A stale rule or a drifted
map misleads every future agent run, and in this kit it also misleads the *next session*, because
the context-handoff guard rewrites those same files when context pressure triggers a handoff.

> **Wrong rules are worse than missing rules. A longer rules file is worse than a lean one.**
> Most changes need *no* edit at all. Adding a wrong or verbose line makes it worse.

Adapted from the upstream generic `rules-check-drift` skill
(github.com/coleam00/skills, MIT), extended with Odoo-specific drift classes, PRD gate-state
verification, and optional live-database confirmation through the `odoo_*` discovery tools.

## Input

- `$ARGUMENTS` — optional diff range. Default: uncommitted + staged (`git diff HEAD`);
  fall back to `main...HEAD` if that is empty.

## Scope

| Audited | Ignored |
|---------|---------|
| `CLAUDE.md` (root + package-level) | `README.md` |
| `AGENTS.md`, `GEMINI.md` | `docs/*.md` other than `tasks.md` |
| `.github/copilot-instructions.md` | `CHANGELOG.md`, release notes |
| `docs/tasks.md`, `docs/progress.json` — **gate state only** | `.claude/` agent/command/skill definitions |
| `SESSION_CONTEXT.md` — **gate state only** | Build output, logs, test fixtures |

If `CLAUDE.md` is only an `@AGENTS.md` import, audit `AGENTS.md`.

`docs/tasks.md` and `progress.json` are audited **for contradiction against the rules files**,
not for their own prose quality. This skill does not review PRD content — that is `prd_writing`.

## Process

### 1. See what changed

```bash
git diff <range> --stat
git diff <range>
git status --short
```

Note: moved/renamed/removed files, new or removed models and fields, changed
`__manifest__.py` depends, changed script entry points, and any new invariant the change
establishes.

### 2. Read the rules files as they are now

Load every file in the Audited column that exists. Hold each concrete claim against the change
set. Concrete claims are the ones that can be false: paths, model names, field names, external
IDs, ports, version numbers, run identifiers, status words.

### 3. Flag ONLY these four things

1. **A stated rule or fact is now false** — e.g. "install logic lives in `manage_modules.sh`"
   but it moved. → fix it.
2. **The architecture / key-files map drifted** — a path or "where things live" pointer no longer
   matches reality. → fix the wrong entry. Do not catalog every new file.
3. **A new durable invariant must hold going forward** — the change establishes a rule that must
   stay true (e.g. "never call `env.cr.execute` from a controller — go through the model").
   → add it as **one line**.
4. **Gate state contradicts the rules file** — the phase table, progress percentage, or session
   context asserts a state that `docs/tasks.md` / `progress.json` does not support. → correct the
   claim to match reality, never the reverse.

Everything else, leave alone. Do **not** suggest an edit to record that a feature was added
(that is a changelog — the codebase is the source of truth), to restate what the code already
makes obvious, or to add background prose that does not steer future work.

### 4. Run the Odoo drift catalog

These are the claim types that actually go stale in an Odoo project. Check each one the rules
files assert:

| Claim in rules file | How it drifts | How to check |
|---|---|---|
| Script or module path in a key-files table | Renamed, moved, or deleted | `test -f <path>` for every path cited |
| Model name (`res.partner`, `sale.order`) | Model renamed or `_name` changed | grep `_name =` across addons; Tier 2 confirms |
| Field name in a rule or example | Field dropped or renamed in a later commit | grep the model file; Tier 2 confirms |
| Module `depends` list | `__manifest__.py` gained/lost a dependency | diff the manifest against the documented list |
| Version idiom (`<tree>` vs `<list>`, `attrs=`) | Rules describe 17 idiom, module targets 18/19 | check `__manifest__.py` version vs the stated idiom |
| MCP port (8765 / 8766 / 8767) | Port map changed in `odoo_mcp/config.py` | grep the config for the actual port constants |
| Database / instance key | `.env` or `config.py` key renamed | grep `config.py` and the env template |
| External ID / `view_id` / attachment ID | Record recreated with a new ID | Tier 2 only — IDs cannot be verified statically |
| Backup, snapshot, or run identifier | **Retention pruned it** — only the last N runs survive | `test -d`/`test -f` the artifact for every id cited |
| Phase or status table | Says Complete while `tasks.md` has `[ ]` | count `[ ]` vs `[x]` in `docs/tasks.md` |
| Rules-file agreement | One of CLAUDE.md / AGENTS.md / GEMINI.md / copilot-instructions.md was edited alone | diff the shared claims across all four |

The **pruned identifier** and **rules-file disagreement** rows catch the two failures that are
invisible in a normal diff review. Check them even when the diff looks unrelated.

### 5. Tier 2 — confirm database claims (optional)

Tier 1 (steps 1–4) is static and always runs. It never needs credentials or a connection.

If a live Odoo connection is available, additionally confirm the model, field, and ID claims that
static checking marked UNVERIFIED. Prefer the in-process tools when running under this kit;
fall back to the standalone MCP server otherwise.

| Tool | Confirms |
|---|---|
| `odoo_search_models` / `mcp_search_models` | the documented model still exists |
| `odoo_get_fields` / `mcp_get_fields` | the documented field still exists on it |
| `odoo_validate_field` / `mcp_validate_field` | a specific model+field pair before trusting a rule that names it |
| `odoo_get_relationships` / `mcp_get_relationships` | a documented relation target still resolves |

Standalone server ports: Odoo 17 → 8765 (XML-RPC), Odoo 18 → 8766 (XML-RPC),
Odoo 19 → 8767 (JSON-RPC 2.0). Check with `odoo_mcp/start_mcp_server.sh --status`.

**If no connection is available, do not start a server and do not block.** Report static-only and
list the specific claims left unverified. A skipped Tier 2 is a normal, complete run.

## Output

```
## Odoo rules-file drift check — range: <range> — tier: <static-only | DB-confirmed vX>

### Fix (now false)
| Where | What's wrong | Minimal fix |
|-------|--------------|-------------|
| CLAUDE.md "Key Files" | scripts/foo.py moved to scripts/pricing/ | update the one path |

### Gate-state contradiction
| Claim | Reality | Minimal fix |
|-------|---------|-------------|
| Phase table: "Phase 4 Complete" | docs/tasks.md has 3 open [ ] | mark In Progress |

### Add (new invariant only)
- <one-line rule> — established by <the change that made it durable>

### Rules-file divergence
- GEMINI.md still says <X>; CLAUDE.md was updated to <Y> — align GEMINI.md

### Unverified (Tier 2 skipped)
- <model/field/ID claims that need a live DB to confirm>

### Checked, still true — no edit
- <areas verified as needing no change>
```

If nothing drifted: **"The rules files are still accurate for these changes — no edits needed."**

## Writing the suggestions

- **One bullet, not a paragraph.** A rule is a line, not an essay.
- **Keep the map current — don't grow it.** Fix the wrong path; do not enumerate the new ones.
- **State rules in natural language; reference the codebase, never paste code.** Copied code goes
  stale; the codebase stays true. Good: "follow the constraint pattern in `models/sale_order.py`."
  Bad: pasting the method.
- **Correct claims toward reality.** When the phase table and `tasks.md` disagree, `tasks.md` wins.
  Never edit `tasks.md` to make the rules file look right.

## Rules

- **Advisory. Report drift; apply edits only if the caller explicitly asks.**
- **Rules files and gate state only.** Not README, not `docs/design.md`, not PRD prose.
- **Never mark a task `[x]`, never change a progress percentage, never write to Odoo.** This skill
  is read-only against the database and against task state.
- **Lean by default.** When in doubt, suggest nothing.
- **Tier 2 is optional.** A missing connection is a downgrade, never a failure.
- Run it before every merge and before every context handoff, so the next session inherits rules
  that are true.

## Red flags — you are drifting from this skill

- Proposing a line that records *what was built* rather than *what must stay true* → that is a changelog entry, drop it.
- Proposing to add three or more lines for one change → you are documenting, not steering.
- Editing `docs/tasks.md` or `progress.json` to resolve a contradiction → wrong direction; fix the claim.
- Starting an MCP server, or blocking on one being down → Tier 2 is optional.
- Pasting a code block into a rules file → reference the path instead.
- Reporting "no drift" without having `test -f`'d the cited paths and identifiers → you did not check.

## Common mistakes

| Mistake | Fix |
|---|---|
| Auditing README and `docs/` too | Scope is rules files + gate state. Nothing else. |
| Rewriting a whole section to fix one path | Change the one wrong entry. |
| Adding "as of <date>" qualifiers | Rules are present-tense. A dated rule is already stale. |
| Trusting a documented record ID statically | IDs need Tier 2. Mark UNVERIFIED otherwise. |
| Fixing CLAUDE.md and leaving GEMINI.md behind | Handoff writes all of them; align them together. |

## Related skills

- `odoo_commanding_system` — owns the `/plan-analysis` → `/start-coding` → `/testing` gates this
  skill audits for contradiction.
- `prd_writing` — owns the content of `docs/tasks.md`; this skill only reads its gate state.

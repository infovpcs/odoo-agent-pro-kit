# Design: Deterministic hooks for the Odoo 17/18/19 pipeline and sandbox test flow

- Date: 2026-08-27
- Status: Approved (design); implementation plan not yet written
- Author: pipeline maintainers
- Related: `plugin/hooks/hooks.json`, `plugin/context_guard.py`, `plugin/__init__.py`,
  `plugin/skills/CommandingSystem/`, `AGENTS.md`, `docs/docker-sandbox/`

## 1. Purpose

Several rules in this repo *name a lifecycle moment* rather than encode judgement.
Today they live only as prose in skill files and `AGENTS.md`, so they hold only
when the agent remembers them. This design converts that handful of
moment-naming rules into deterministic hooks that fire whether the model
remembers or not, while leaving taste/fact rules (coding-standard rationale,
"one phase per session", "never claim unexecuted evidence") as prose.

The triage method is from the external `hooks-create` skill
(`github.com/coleam00/skills`): for each rule line, ask "does this name an
EVENT?" -> hook; "encodes judgement/taste/facts?" -> stays a rule; "neither"
-> delete. Blocking-capable events (`PreToolUse`, `UserPromptSubmit`, `Stop`)
are gates; observe-only events (`PostToolUse`, `SessionStart`, `SessionEnd`,
`Notification`) are logs.

## 2. Scope

In scope:

1. **Plugin pipeline hooks** — shipped in `plugin/hooks/hooks.json` (Claude Code)
   and `plugin/__init__.py` `register()` (Hermes). Affects everyone who installs
   the kit. Covers command gates, the version-aware coding-standard linter,
   sandbox operation-result verification, and git/secret/Enterprise-source
   guardrails.
2. **Contributor workflow hooks** — a new repo-root `.claude/settings.json`, NOT
   shipped in the plugin. Enforces the `AGENTS.md` phase-workflow rules for
   people developing this repository.

Out of scope:

- Rewriting the existing `context_guard.py` dynamic-handoff logic (reused as-is;
  a Claude-Code-side equivalent is added).
- New CI beyond extending `scripts/validate.sh` and the `hermes plugins doctor`
  expectations.
- Any change to `sandbox/bin/sandboxctl` or `odoo_local_setup/manage_modules.sh`
  behaviour. Hooks observe and gate around them; they do not modify them.

## 3. Decisions (from brainstorming)

| Question | Decision |
| --- | --- |
| Which hook sets | Both: plugin pipeline hooks **and** contributor `.claude/settings.json` |
| Runtime coverage | Claude Code **and** Hermes parity for every plugin hook |
| Enforcement posture | Hard-block non-negotiables (exit 2); observe/warn everything else |
| Version-aware linter | Full 17/18/19 pattern linter |

## 4. Architecture

### 4.1 Shared check library — `plugin/hooks/checks/` (new)

Pure functions, no process I/O, independently unit-tested. Single source of
truth for both runtimes.

| Module | Responsibility |
| --- | --- |
| `version.py` | `detect_odoo_version(cwd) -> "17" \| "18" \| "19" \| None`. Reuses the exact 3-tier detection already in `plugin/hooks/session_start.sh` and `plugin/context_guard.py::_module_version`: (1) `.sandbox/session.json` `odoo_version`; (2) a `17.0/18.0/19.0` sibling or child directory; (3) `docs/module_meta.md` version regex; then env `DEFAULT_ODOO_VERSION`; else `None`. |
| `odoo_lint.py` | `lint(path: str, content: str, version: str) -> list[Finding]`. `Finding = {severity: "block"\|"warn", rule: str, line: int, message: str, fix: str}`. Rule table in section 5. Only inspects `*.py` and `*.xml` under a module tree. |
| `sandbox_result.py` | `read_operation_result(bash_command: str, cwd: Path) -> Result \| None`. Given a `sandboxctl module <session> (install\|update\|test) <module>` command string, locate the operation-result JSON it writes (path convention from `sandbox/schemas/` + `docs/docker-sandbox/design.md`), return `{status, module_state, reason, result_path}`. |
| `guard.py` | `classify_bash(command: str) -> list[Violation]`. Detects: raw `odoo-bin` invocation; `./manage_modules.sh` (must be `bash manage_modules.sh`); `git push`/`git merge`/`git tag`/`git commit --amend` on pushed history; `gh pr create`/`gh release`/`gh pr merge`; destructive `docker`/`sbx` cleanup. |
| `paths.py` | `scan_write(target_path: str, content: str \| None) -> list[Violation]`. Flags writing into the repo tree: secret-shaped content (API keys, `PRIVATE KEY`, `.env` with values), `*enterprise*` / `OEEL-1` / `OPL-1` licensed Odoo source, customer-data paths (configurable deny-list, default covers `*/ent-1[789]/*`, known client repo names). |
| `gates.py` | `check_start_coding(module_dir) -> Gate` and `check_testing(module_dir) -> Gate`. `/start-coding`: `docs/tasks.md` must exist. `/testing`: zero `- [ ]` lines in `docs/tasks.md` **and** `sessions/<module>_progress.json` `backend_tests_passed == true`. |
| `authz.py` | `vcs_write_allowed(cwd) -> bool`. True iff env `ODOO_KIT_ALLOW_VCS_WRITE=1` or a `.sandbox/AUTHORIZED` marker file exists. Contributor settings use `AGENTS_PHASE_AUTHORIZED=1`. |
| `common.py` | `in_odoo_module(cwd) -> bool` fast no-op guard (has `docs/tasks.md` **or** a version signal); `hooks_disabled() -> bool` (`ODOO_KIT_HOOKS_DISABLED=1`); `Finding`/`Violation`/`Gate`/`Result` dataclasses. |

### 4.2 Claude Code dispatcher — `plugin/hooks/odoo_hook.py` (new)

A `uv` single-file script (`#!/usr/bin/env -S uv run --script`, `requires-python
>=3.10`, no third-party deps). Invocation: `odoo_hook.py <Event>`.

Flow:

1. Read JSON from stdin (Claude Code hook payload). If parse fails -> exit 0.
2. If `common.hooks_disabled()` or not `common.in_odoo_module(cwd)` -> exit 0.
3. Dispatch on `<Event>`:
   - `SessionStart` -> print context + gate-state summary to stdout (injected),
     exit 0.
   - `UserPromptSubmit` -> if the prompt starts with `/start-coding` or
     `/testing`, run the matching `gates` check; on failure print the redirect
     message to **stderr** and exit 2; else exit 0.
   - `PreToolUse` -> for `Bash`, run `guard.classify_bash`; for `Write`/`Edit`,
     run `paths.scan_write`. Any `Violation` (respecting `authz` for VCS) ->
     stderr + exit 2. Else exit 0.
   - `PostToolUse` -> for `Write`/`Edit`, run `odoo_lint.lint` on the touched
     file; any `severity == "block"` -> stderr (all findings) + exit 2;
     `warn`-only -> stdout + exit 0. For `Bash` matching a `sandboxctl module`
     command, run `sandbox_result.read_operation_result`; non-`succeeded`
     status or `module_state != "installed"` -> stdout advisory (observe, exit
     0).
   - `Stop` -> honour `stop_hook_active` (exit 0 immediately if set). Otherwise:
     if tracked files changed since the last `validate.sh` stamp, print a
     reminder to stdout; run the context-handoff writer if usage data is
     available in the payload. Exit 0.
   - `SessionEnd` -> run MCP pid cleanup (logic from `cleanup_mcp.sh`) and the
     `sbx ls` / `docker ps -a` orphan assertion. Exit 0.
4. Any unhandled exception anywhere -> log to stderr, exit 0 (fail-open).

### 4.3 Claude Code wiring — `plugin/hooks/hooks.json` (extend)

```jsonc
{
  "SessionStart": [
    { "hooks": [
      { "type": "command", "command": "\"${CLAUDE_PLUGIN_ROOT}\"/hooks/session_start.sh" },
      { "type": "command", "command": "\"${CLAUDE_PLUGIN_ROOT}\"/hooks/odoo_hook.py SessionStart" }
    ] }
  ],
  "UserPromptSubmit": [
    { "hooks": [
      { "type": "command", "command": "\"${CLAUDE_PLUGIN_ROOT}\"/hooks/odoo_hook.py UserPromptSubmit" }
    ] }
  ],
  "PreToolUse": [
    { "matcher": "Bash",
      "hooks": [ { "type": "command", "command": "\"${CLAUDE_PLUGIN_ROOT}\"/hooks/odoo_hook.py PreToolUse" } ] },
    { "matcher": "Write|Edit",
      "hooks": [ { "type": "command", "command": "\"${CLAUDE_PLUGIN_ROOT}\"/hooks/odoo_hook.py PreToolUse" } ] }
  ],
  "PostToolUse": [
    { "matcher": "Write|Edit",
      "hooks": [ { "type": "command", "command": "\"${CLAUDE_PLUGIN_ROOT}\"/hooks/odoo_hook.py PostToolUse" } ] },
    { "matcher": "Bash",
      "hooks": [ { "type": "command", "command": "\"${CLAUDE_PLUGIN_ROOT}\"/hooks/odoo_hook.py PostToolUse" } ] }
  ],
  "PreCompact": [
    { "hooks": [ { "type": "command", "command": "\"${CLAUDE_PLUGIN_ROOT}\"/hooks/save_progress.sh" } ] }
  ],
  "Stop": [
    { "hooks": [ { "type": "command", "command": "\"${CLAUDE_PLUGIN_ROOT}\"/hooks/odoo_hook.py Stop" } ] }
  ],
  "SessionEnd": [
    { "hooks": [ { "type": "command", "command": "\"${CLAUDE_PLUGIN_ROOT}\"/hooks/odoo_hook.py SessionEnd" } ] }
  ]
}
```

`cleanup_mcp.sh` moves from `Stop` to `SessionEnd` (its logic is folded into
`odoo_hook.py SessionEnd`; the script is kept as a thin wrapper for anyone
referencing it directly, or removed if nothing does — decided during
implementation).

### 4.4 Hermes wiring — `plugin/__init__.py` `register()` (extend)

Event mapping (Hermes has no `user_prompt_submit` / `Stop` / `PreCompact`):

| Plugin concern | Claude Code event | Hermes mechanism |
| --- | --- | --- |
| Session context + gate state | `SessionStart` | `on_session_start` (already registered — extend body) |
| `/start-coding` + `/testing` gates | `UserPromptSubmit` | inside each `ctx.register_command` handler (already registered — add a `gates` pre-check that returns the redirect instead of running) |
| Bash / Write guardrails | `PreToolUse` | `ctx.register_hook("pre_tool_call", …)` returning a block directive |
| Version linter + sandbox result | `PostToolUse` | `ctx.register_hook("post_tool_call", …)` |
| Context handoff | `Stop` | `post_api_request` (already registered — unchanged) |
| MCP cleanup + orphan check | `SessionEnd` | `on_session_end` (already registered — extend body) |

A `plugin/hooks/checks/hermes_adapter.py` translates Hermes hook kwargs
(`tool_name`, `tool_args`, `result`, …) into the same `checks/` function calls.
The block signal differs: Claude Code = exit 2 + stderr; Hermes = return the
documented block/approve directive from `pre_tool_call`.

### 4.5 Contributor workflow — `.claude/settings.json` (new, repo root)

Not part of the plugin package; git-tracked for contributors.

| Event | Matcher | Action | Block? |
| --- | --- | --- | --- |
| `SessionStart` | — | print `SESSION_CONTEXT.md` "Current state" section + `git branch`/`git status -s` + next incomplete phase from `docs/docker-sandbox/tasks.md` | no |
| `PreToolUse` | `Bash` | block `git push`/`merge`/`tag`, `gh …`, destructive `docker`/`sbx` cleanup unless `AGENTS_PHASE_AUTHORIZED=1`; block `git commit` unless `scripts/validate.sh` ran since the last tracked-file change (mtime stamp in `.git/odoo-kit-validate.stamp`) | yes |
| `Stop` | — | if tracked code changed but none of `docs/docker-sandbox/tasks.md`, `SESSION_CONTEXT.md`, `README.md` changed, print a reminder | no |

Implemented as a second small script `scripts/contributor_hook.py` (same
fail-open contract), referenced from `.claude/settings.json`.

## 5. Version-aware linter rules

`Finding.severity` is `block` only where the pattern causes a real install/RPC
failure on that version; everything else is `warn`.

| # | Pattern (detection) | 17 | 18 | 19 | File type | Fix message |
| --- | --- | --- | --- | --- | --- | --- |
| L1 | `<tree` open tag in a view arch | ok | warn | **block** | `*.xml` under `views/` | Replace `<tree>` with `<list>` |
| L2 | `attrs=` or `states=` attribute on a view node | ok | warn | **block** | `*.xml` | Use direct `invisible=`/`readonly=`/`required=` attributes |
| L3 | `type=('"')json('"')` in an `@http.route(...)` call | n/a | warn | **block** | `*.py` under `controllers/` | Use `type='jsonrpc'` |
| L4 | `<group ...>` with `expand=` or `string=` inside a `<search>` view | ok | ok | **block** | `*.xml` | Remove `expand`/`string` from `<group>` in search views |
| L5 | `category_id=` on a `res.groups` record | ok | ok | **block** | `*.xml` under `security/` or `data/` | Use `privilege_id` (`res.groups.privilege`) |
| L6 | `_sql_constraints` entry whose SQL contains `CHECK(` implementing a value rule | warn | warn | warn | `*.py` under `models/` | Prefer `@api.constrains` for value validation |
| L7 | new `models/*.py` adds a `_name` but no matching row in `security/ir.model.access.csv` | warn | **block** | **block** | model + security | Add an `ir.model.access.csv` row for the new model |
| L8 | action method returning `None` (no `return` / bare `return`) reachable from a button | warn | warn | warn | `*.py` | Return `True` from action methods (Odoo 19 raises `Fault` on `None`) |

Line numbers are best-effort (regex match line). L7/L8 are heuristic and always
`warn` at most on 17; false positives are acceptable because they are advisory.

## 6. Data flow

```
prompt "/testing 19 mymod"
  -> UserPromptSubmit hook -> gates.check_testing(mymod)
       tasks.md has "- [ ]"      -> stderr redirect, exit 2  (agent routes to /start-coding)
       backend_tests_passed false -> stderr redirect, exit 2
       else                       -> exit 0, command proceeds

agent edits mymod/views/x.xml (adds <tree>)
  -> PostToolUse[Write] hook -> version.detect_odoo_version() = "19"
       -> odoo_lint.lint(...) -> [Finding(block, L1, ...)]
       -> stderr with finding + fix, exit 2  (agent must fix before continuing)

agent runs `sandbox/bin/sandboxctl module s-123 install mymod`
  -> PreToolUse[Bash] hook -> guard.classify_bash() -> [] -> exit 0
  -> (command runs)
  -> PostToolUse[Bash] hook -> sandbox_result.read_operation_result()
       status "install_failed" / module_state "to install"
       -> stdout advisory "module did not reach 'installed' — see <result_path>", exit 0

agent runs `git push origin main`
  -> PreToolUse[Bash] hook -> guard.classify_bash() -> [Violation(vcs_push)]
       authz.vcs_write_allowed() false -> stderr, exit 2
```

## 7. Error handling

- Every hook entry point wraps its body in `try/except Exception` -> log to
  stderr, `sys.exit(0)`. A hook bug can never break a turn.
- `Stop` honours `stop_hook_active` to avoid loops.
- Hooks no-op (exit 0, no output) within ~milliseconds when `cwd` is not inside
  an Odoo module workspace.
- `ODOO_KIT_HOOKS_DISABLED=1` disables all plugin hooks; `AGENTS_PHASE_AUTHORIZED`
  / `ODOO_KIT_ALLOW_VCS_WRITE` / `.sandbox/AUTHORIZED` lift specific gates.
- Missing `uv` on a user's machine: `hooks.json` commands invoke the script
  directly (`#!/usr/bin/env -S uv run --script`); the implementation plan must
  include a fallback (plain `python3` shebang variant or a `command -v uv`
  check) since the kit does not currently require `uv`.

## 8. Testing

| Layer | Test |
| --- | --- |
| `checks/*` | `tests/test_hooks_checks.py` — table-driven unit tests per function, including every linter rule L1–L8 across 17/18/19, `guard` command classification, `gates` pass/fail, `paths` secret/Enterprise detection, `version` 3-tier detection. |
| `odoo_hook.py` | `tests/test_hooks_dispatcher.py` — feed a recorded stdin payload per event, assert exit code (0/2) and stdout/stderr substring. Fixtures under `tests/fixtures/hook_payloads/`. |
| Fail-open | Test that a `checks/` function raising still yields exit 0. |
| Hermes | Extend the `hermes plugins doctor … --ci` expectation in `OdooHermesEnvironmentSetup/SKILL.md` and any test asserting the hook count (2/3 -> new count). Add a direct-call test of `hermes_adapter` translation. |
| `scripts/validate.sh` | Add a step that runs `odoo_hook.py` with an empty payload for each event and asserts exit 0 (smoke), plus `python -m py_compile` on all new files. |
| Contributor hook | `tests/test_contributor_hook.py` — `validate.sh` stamp logic, VCS block with/without `AGENTS_PHASE_AUTHORIZED`. |

Manual validation before merge (per `hooks-create`): run each hook with a real
blocking payload and a real allowing payload, confirm exit 2 vs 0.

## 9. Docs and packaging updates (same change)

- `plugin/skills/CommandingSystem/SKILL.md` — new "Deterministic hooks" section
  describing which gates are now enforced by hooks vs prose.
- `AGENTS.md` — note that the phase-workflow rules are backed by
  `.claude/settings.json` for contributors.
- `README.md` — hooks list in the plugin feature summary.
- `CHANGELOG.md` — new entry.
- `plugin/.claude-plugin/plugin.json` + `plugin/plugin.yaml` — version bump
  (0.4.0 -> 0.5.0); `plugin.yaml` `provides_hooks` list extended.
- `docs/architecture.excalidraw` / `.png` — add the hook layer if the diagram
  covers control flow (decided during implementation).

## 10. Rollout

1. Land `checks/` + unit tests (no wiring) — inert.
2. Land `odoo_hook.py` + dispatcher tests — inert (not in `hooks.json` yet).
3. Wire `hooks.json` observe-only events first (`SessionStart`, `PostToolUse`
   advisory paths, `SessionEnd`); dogfood.
4. Wire the blocking events (`UserPromptSubmit`, `PreToolUse`, `PostToolUse`
   linter blockers).
5. Land Hermes `register()` changes + adapter.
6. Land `.claude/settings.json` + `contributor_hook.py`.
7. Docs, version bump, `CHANGELOG.md`.

Each step passes `scripts/validate.sh` from a clean shell before the next.

## 11. Open items for the implementation plan

- `uv` availability fallback strategy (section 7).
- Exact operation-result JSON path convention — confirm against
  `sandbox/schemas/` and a live `sandboxctl module` run.
- Whether `cleanup_mcp.sh` / `session_start.sh` are absorbed into `odoo_hook.py`
  or kept as separate `hooks.json` entries alongside it.
- Confirm the Hermes `pre_tool_call` block-directive return shape against the
  installed Hermes version on the Oracle VPS profiles.
- Customer-data deny-list contents for `paths.py` (keep it out of the public
  repo if it names client repos — load from an optional untracked file).

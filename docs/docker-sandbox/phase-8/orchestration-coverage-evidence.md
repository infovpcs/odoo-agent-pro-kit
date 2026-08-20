# Phase 8 — Platform/Orchestration Coverage Verification

Verifies the five remaining "Scope: platform/orchestration coverage to
validate" checklist items in `docs/docker-sandbox/tasks.md` Phase 8, closing
the Phase 8 exit gate.

## Item 1: `on_session_start` correctly detects Sandbox vs. bare local workspace

Both the Claude-Code-style shell hook (`plugin/hooks/session_start.sh`) and
the native Hermes hook (`plugin/__init__.py:_on_session_start`) were
exercised against three real cases:

1. **Sandbox session** — a real `session.json` from Docker Sandbox
   `phase8-orchestration-test` (Odoo 17.0, module `sandbox_fixture`), read
   via `SANDBOX_SESSION_FILE`. Both hooks correctly reported the session id,
   Odoo version, module, status, and Compose project / Odoo target.
2. **Bare local Odoo workspace** — a directory with an `18.0/` subdirectory
   and no `.sandbox/session.json`. The shell hook correctly fell through to
   local-workspace detection and reported the right MCP port (8766).
3. **Genuinely bare directory** — no session file, no version directory.
   Both hooks correctly no-op (silent, exit 0) rather than emitting a false
   detection.

## Item 2: version -> skill mapping resolves inside a sandbox session

Confirmed inside the same live Docker Sandbox session that the
`CommandingSystem/SKILL.md` "Version -> Skill Mapping" table's skill
directories genuinely exist on disk for all three versions, not just
documented: `Odoo{17,18,19}CodingStandard/SKILL.md`,
`OdooTools{17,18,19}/SKILL.md`, and
`Odoo{17,18,19}ExistingDependencyContext/SKILL.md` all resolved correctly
via `ls`/`head` against the sandbox's mounted repo clone.

## Item 3: `sandboxctl module` is the sole install/update/test entrypoint

Audit found a real gap: `OdooTools17/18/19/SKILL.md`'s "Tests" bullet
recommended raw `odoo-bin -d <db> --test-tags <tag>` with no caveat, while
every other lifecycle-touching skill (`Odoo_Custom_App_Install_Update`,
`Odoo_Custom_Backend_Testing`, `Odoo_Custom_Frontend_Testing`,
`CommandingSystem/*_workflow.md`, `DockerSandboxOperations`) already
enforces `sandboxctl module ... install|update|test` exclusively. Fixed all
three `OdooTools*` skills to route the Tests bullet through
`sandboxctl module <session> test <module>` (or `manage_modules.sh test` in
local mode) with an explicit "never invoke raw odoo-bin" caveat. Added
`test_odoo_tools_skills_route_test_lifecycle_through_sandboxctl` to
`tests/test_phase3_integration.py` so this is enforced automatically going
forward, alongside the existing
`test_lifecycle_skills_use_controller_and_forbid_raw_odoo_bin` test that
covered the other four skills.

## Item 4: `context_guard.py` fires on real per-turn usage and a fresh session resumes correctly

Exercised `plugin/context_guard.py`'s real `maybe_handle_context_pressure`
function directly (the actual hook code registered on Hermes'
`post_api_request` event, not a mock/reimplementation) against a seeded
5-task module directory (`docs/tasks.md` with 2/5 tasks `[x]`):

1. **Threshold computation**: for a 5-task module, `_effective_threshold_pct`
   correctly tightens the base 60% threshold to 65% (small-module adjustment
   of `+0.05`, since `tasks_total <= 5`).
2. **First call** with a real `usage={"total_tokens": 90000}` (90000/128000 =
   70.3% of the default 128k context window, above the 65% threshold):
   - Correctly triggered and wrote `CLAUDE.md`, `GEMINI.md`, `AGENTS.md`,
     and `sessions/context_handoff.json` via the real
     `context_writer.write_context` call.
   - The written handoff accurately captured `2/5` tasks done, `70.3%`
     usage, `65.0%` threshold, and the triggering command (`start-coding`).
   - Correctly called `ctx.inject_message(..., role="system")` with a nudge
     telling the agent to finish cleanly and hand off.
3. **Second call, same usage bucket**: correctly did NOT re-trigger
   (`_last_triggered_bucket` dedup), matching the documented "re-fires only
   when usage grows by another full bucket" behavior — no spam on a
   long-running command already past threshold.
4. **Fresh-session resume, independently verified**: a brand-new,
   zero-context Hermes subagent was given only two file paths — the written
   `CLAUDE.md` and the pre-existing `docs/tasks.md` — with explicit
   instructions not to read anything else. It correctly reported: module
   name, Odoo version 17, `2/5` tasks done, last command `/start-coding`,
   the dynamic-handoff trigger and its 70.3% usage percentage, and
   correctly identified what to do next as a resuming agent. It also
   correctly caught a real discrepancy in the test fixture (a naming
   mismatch I introduced between the test directory name embedded in
   `CLAUDE.md` and the title text in `tasks.md`) — proof it was actually
   reading and reasoning over the file content, not pattern-matching a
   canned answer.

This satisfies the "genuinely fresh session (new process, not the same
context) resumes correctly from the written handoff without operator
intervention" requirement using an independent subagent process rather than
self-reporting from the same uninterrupted session, matching the bar set by
the earlier pilot-module Step 10 verification.

## Item 5: session-start context load measurably changes agent behavior on resume

Distinct from Item 4 (which tests the *write* side of the handoff), this
tests the *read* side: does an agent that reads `CLAUDE.md` before starting
actually skip already-completed work rather than re-deriving it from
`docs/tasks.md` alone?

Seeded a real `context_writer.py`-format `CLAUDE.md` (module
`lot_auto_generate`, 2/5 tasks done, with a "Latest Summary" narrative and a
"Command History" line naming the two completed tasks and their auto-test
pass counts — matching the exact real output shape, no synthetic "skip
this" instruction injected) alongside the same 2/5-checked `docs/tasks.md`.
A brand-new, zero-context Hermes subagent was given only these two files
and asked, with no hint about what to skip, which task(s) it would start
next and which it would explicitly skip re-implementing.

Result: it correctly identified both completed tasks by name ("Add lot
sequence model", "Add purchase order view hook") as skip-worthy, cited
their auto-test pass counts from CLAUDE.md's command history as the reason,
and correctly sequenced the three remaining unchecked tasks in
`tasks.md`'s order as the next work. This demonstrates the context-load
design measurably changes planned behavior (skip vs. re-derive) purely from
reading the episodic-memory file, not from an explicit skip directive.

## Cleanup

The Docker Sandbox session (`phase8-orchestration-test`) used for items 1-2
was fully destroyed after evidence capture (`--allow-unexported`, disposable
test fixture); `sbx ls`, `docker ps -a` confirmed no orphaned
containers/volumes/sandboxes, and the two pre-existing sandbox sessions on
the host (`phase8-hr-document-report`, `phase8-hr-payroll-invoice`) were
left untouched throughout. All local scratch directories used for items 1,
4, and 5 (`/tmp/context-guard-test`, `/tmp/local-workspace-test`,
`/tmp/bare-workspace-test`, `/tmp/native-hook-sandbox-test`,
`/tmp/start-coding-resume-test`) were removed after evidence capture.

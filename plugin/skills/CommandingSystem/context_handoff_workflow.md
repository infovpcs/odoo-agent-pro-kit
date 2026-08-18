# Context Handoff Workflow (Phase 25, extended Phase 8)

How CommandingSystem commands pass episodic memory to the next command, and
how context pressure triggers an automatic handoff mid-command.

---

## The 4 Memory Types

| Type | Implementation | Scope |
|------|---------------|-------|
| **Working memory** | `sessions/{module}_progress.json` | Current session |
| **Episodic memory** | `{module_dir}/CLAUDE.md` | Across sessions/commands |
| **Semantic memory** | `Odoo{V}CodingStandard/SKILL.md` | Persistent reference |
| **Procedural memory** | `CommandingSystem/*_workflow.md` | Persistent reference |

---

## Context Write: End of Each Command

In sandbox mode, record the path and status of the latest result under
`.sandbox/sessions/<session-id>/results/`. A gate passes only when that JSON
reports `status: succeeded`; terminal output alone is not evidence.

### After /plan-analysis completes

```bash
python3 CommandingSystem/auto_test/context_writer.py write \
  --module {module_name} \
  --module-dir {module_dir} \
  --version {version} \
  --command plan-analysis \
  --summary "PRD complete. {task_count} tasks defined. {requirements_summary}" \
  --tasks-done 0 \
  --tasks-total {task_count}
```

### After each task in /start-coding

```bash
# 1. Run auto-test for the completed task
python3 CommandingSystem/auto_test/auto_test_runner.py \
  --version {version} \
  --module {module_name} \
  --task "{task_title}"

# 2. Update context with test result
python3 CommandingSystem/auto_test/context_writer.py write \
  --module {module_name} \
  --module-dir {module_dir} \
  --version {version} \
  --command start-coding \
  --summary "Completed: {task_title} | Test: {test_status}" \
  --models "{current_models_csv}" \
  --tasks-done {done_count} \
  --tasks-total {total_count}
```

### After /testing completes

```bash
python3 CommandingSystem/auto_test/context_writer.py write \
  --module {module_name} \
  --module-dir {module_dir} \
  --version {version} \
  --command testing \
  --summary "UI tests complete. Documentation index.html generated." \
  --tasks-done {total_count} \
  --tasks-total {total_count}
```

---

## Context Read: Start of Each Command

At the start of `/start-coding` and `/testing`, BEFORE loading skills:

```python
claude_md = os.path.join(module_dir, "CLAUDE.md")
if os.path.exists(claude_md):
    prior_context = read_file(claude_md)
    prepend_to_system_prompt("## Prior Session Context\n\n" + prior_context)
    print(f"Context loaded: {claude_md}")
```

---

## Multi-Agent Platform Support

`context_writer.py write` always generates three identical files:

| File | Platform |
|------|---------|
| `CLAUDE.md` | Claude Code (auto-loaded from working directory) |
| `GEMINI.md` | Gemini CLI (auto-loaded) |
| `AGENTS.md` | GitHub Copilot (auto-loaded) |

---

## Auto-Test Feedback Loop

```
Task N implemented
  → auto_test_runner.py runs
    → PASS:    mark [x], update context, continue to Task N+1
    → PARTIAL: review failures, optionally patch, update context, continue
    → FAIL:    HALT — fix module install or CRUD error, retest before [x]
```

The agent MUST NOT mark a task `[x]` in `docs/tasks.md` until auto-test returns PASS or PARTIAL (with review).

---

## Dynamic Context-Usage Handoff (Phase 8)

Beyond the per-command writes above, `plugin/context_guard.py` fires on
Hermes' real `post_api_request` hook — actual per-turn token usage, not a
guess — for **any** in-progress command (`/plan-analysis`, `/start-coding`,
`/testing`, `/fleet`, or plain conversation inside a module workspace with
`docs/tasks.md`). This is deliberately command-agnostic: context pressure
comes from how complex the module is and how much work the running command
has already done, not from which command happens to be running.

**Threshold is dynamic, not a single fixed percentage:**

- Base threshold: `context_handoff.threshold_pct` plugin config, default 60%.
- Auto-tightened per module complexity, read from `docs/tasks.md`'s task
  count at trigger time:
  - ≤ 5 tasks: threshold +5 points (run closer to the limit — little
    remaining work per task).
  - 6-15 tasks: threshold unchanged.
  - \> 15 tasks: threshold -10 points (hand off earlier — each remaining
    task needs more headroom).
  - Bounded to 40%-80% regardless of config.
- Re-fires only once usage crosses into a new 10-point bucket past the last
  trigger for that module (`context_handoff.retrigger_bucket_pct`), so a
  long-running command past threshold isn't nudged every single API call.

**What happens at trigger:**

1. `context_guard.py` calls `context_writer.write_context()` directly (same
   contract as the manual per-command writes above), stamping an additional
   `extra.context_handoff` block into the session JSON and a visible
   "⚠️ Dynamic Context Handoff" section into `CLAUDE.md`/`GEMINI.md`/
   `AGENTS.md` with the usage%, threshold%, triggering command, and
   timestamp.
2. `ctx.inject_message()` nudges the live agent: finish the current step
   cleanly, don't start new large work, and tell the user this session
   should reset.
3. The **next** session (fresh context) reads `CLAUDE.md` at the normal
   command-start read step above and resumes purely from that file plus
   `docs/tasks.md` — no special-casing needed, because it is the same
   episodic-memory contract every command already writes to and reads from.

**Verification requirement (Phase 8 exit gate, step 10):** a handoff caused
by this guard must be confirmed by actually starting a **new** agent
session against the same module directory and checking it resumes from
`CLAUDE.md` state — never self-reported by the same uninterrupted session
that triggered the handoff.

**Reference:** `plugin/context_guard.py` (implementation),
`plugin/plugin.yaml` `config_schema.context_handoff.*` (tunables).

# Context Handoff Workflow (Phase 25)

How CommandingSystem commands pass episodic memory to the next command.

---

## The 4 Memory Types

| Type | Implementation | Scope |
|------|---------------|-------|
| **Working memory** | `sessions/{module}_progress.json` | Current session |
| **Episodic memory** | `{module_dir}/CLAUDE.md` | Across sessions/commands |
| **Semantic memory** | `AgentSkills/Odoo{V}CodingStandard/SKILL.md` | Persistent reference |
| **Procedural memory** | `CommandingSystem/*_workflow.md` | Persistent reference |

---

## Context Write: End of Each Command

### After /plan-analysis completes

```bash
python3 AgentSkills/auto_test/context_writer.py write \
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
python3 AgentSkills/auto_test/auto_test_runner.py \
  --version {version} \
  --module {module_name} \
  --task "{task_title}"

# 2. Update context with test result
python3 AgentSkills/auto_test/context_writer.py write \
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
python3 AgentSkills/auto_test/context_writer.py write \
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

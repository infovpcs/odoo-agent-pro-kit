# start-coding

> **Odoo task-loop implementation** with backend testing per task, git commit generation, and progress tracking.
> Requires `docs/tasks.md` from `/plan-analysis`.

## Usage
```
/start-coding 19
/start-coding 18
/start-coding 17
```

## Gate Check
⛔ If `{module_name}/docs/tasks.md` is missing → stop and redirect to `/plan-analysis {version}`.

## What This Does
1. Restores context from `sessions/{module_name}_progress.json` if it exists
2. Loops through each `[ ]` task in docs/tasks.md
3. For each task: code → quality gates → backend tests via RPC → mark `[x]` → generate git commit message → save progress
4. Ends with summary and redirects to `/testing`

## Instructions
Load `.cursor/AgentSkills/CommandingSystem/SKILL.md` then load `.cursor/AgentSkills/CommandingSystem/start_coding_workflow.md`.
Execute STEP 1 through STEP 5. Ask for version (17|18|19) and module name if not provided.

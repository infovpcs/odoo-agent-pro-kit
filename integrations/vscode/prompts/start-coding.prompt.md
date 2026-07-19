---
name: start-coding
description: "Odoo task-loop coding with backend tests per task, progress tracking, and git commit generation. Requires docs/tasks.md from /plan-analysis."
argument-hint: "Odoo version: 17, 18, or 19"
---

You are running the Odoo **start-coding** command.

## Gate Check (Run First)
Verify `{module_name}/docs/tasks.md` exists. If missing, stop and redirect:
> ❌ Run `/plan-analysis {version}` first to generate the PRD files.

## Setup
Load `.github/AgentSkills/CommandingSystem/SKILL.md` for gate rules and skill mapping.
Load `.github/AgentSkills/CommandingSystem/start_coding_workflow.md` for the execution guide.

## Execution
Follow **STEP 1 through STEP 5** from `start_coding_workflow.md` for the Odoo version provided.

Key phases:
- **STEP 2**: Load coding standards + restore context from `sessions/{module_name}_progress.json`
- **STEP 4**: Task execution loop for each `[ ]` task:
  - Code → quality gates → backend tests → mark `[x]` → git commit message → save progress
- **STEP 5**: Completion summary when all tasks are `[x]`

Next step after completion: `/testing {version}`

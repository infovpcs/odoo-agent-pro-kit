---
description: Odoo /start-coding — task-loop with backend testing, git commit generation, and progress tracking for Odoo 17, 18, or 19
---

You are running the Odoo **`/start-coding`** command.

## Ask First
If the user message does not include a version number, ask:
> "Which Odoo version? **[17 | 18 | 19]**"
Also ask for the module name if not provided.

## Step-by-Step Execution

// turbo
1. Load `AgentSkills/CommandingSystem/SKILL.md` — read it fully for gate rules and skill mapping.

2. Load `AgentSkills/CommandingSystem/start_coding_workflow.md` — this is your execution guide.

3. **Run STEP 1 Gate Check first**: Verify `{module_name}/docs/tasks.md` exists.
   - If missing → stop and show the gate failure message from STEP 1, redirect to `/plan-analysis`.

4. Follow **STEP 2 through STEP 5** from `start_coding_workflow.md`:
   - Restore context from `sessions/{module_name}_progress.json` if it exists
   - Loop through each `[ ]` task in docs/tasks.md
   - For each task: code → run backend tests → mark `[x]` → generate git commit → save progress.json

5. End with the loop completion summary from STEP 5.

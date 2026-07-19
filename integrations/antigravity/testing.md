---
description: Odoo /testing — frontend UI tests, screenshot capture, GIF generation, and responsive index.html documentation for Odoo 17, 18, or 19
---

You are running the Odoo **`/testing`** command.

## Ask First
If the user message does not include a version number, ask:
> "Which Odoo version? **[17 | 18 | 19]**"
Also ask for the module name if not provided.

## Step-by-Step Execution

// turbo
1. Load `AgentSkills/CommandingSystem/SKILL.md` — read it fully for gate rules and skill mapping.

2. Load `AgentSkills/CommandingSystem/testing_workflow.md` — this is your execution guide.

3. **Run STEP 1 Gate Check first**: Verify all tasks in `{module_name}/docs/tasks.md` are `[x]`.
   - If any `[ ]` remain → stop and show the gate failure message with the list, redirect to `/start-coding`.

4. Follow **STEP 2 through STEP 8** from `testing_workflow.md`:
   - Check system dependencies (Node.js, agent-browser, ffmpeg)
   - Install/update the module via manage_modules.sh
   - Run frontend test loop with agent-browser
   - Generate icon, banner, GIFs, screenshots
   - Build the responsive `static/description/index.html`

5. End with the completion summary from STEP 8.

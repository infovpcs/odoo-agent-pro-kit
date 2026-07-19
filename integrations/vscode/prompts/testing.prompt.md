---
name: testing
description: "Odoo frontend UI testing, screenshot capture, GIF animation generation, and responsive static/description/index.html documentation. Requires all tasks complete."
argument-hint: "Odoo version: 17, 18, or 19"
---

You are running the Odoo **testing** command.

## Gate Check (Run First)
Verify all tasks in `{module_name}/docs/tasks.md` are marked `[x]`. If any `[ ]` remain, stop and redirect:
> ❌ Complete all tasks first with `/start-coding {version}`.

## Setup
Load `.github/AgentSkills/CommandingSystem/SKILL.md` for gate rules.
Load `.github/AgentSkills/CommandingSystem/testing_workflow.md` for the execution guide.

## Execution
Follow **STEP 1 through STEP 8** from `testing_workflow.md` for the Odoo version provided.

Key phases:
- **STEP 3**: Auto-install system deps (Node.js, agent-browser, ffmpeg)
- **STEP 4**: Install/update module via manage_modules.sh
- **STEP 5**: Frontend test loop (agent-browser screenshots, JS error→fix cycle)
- **STEP 6**: Generate icon, banner, GIFs from recordings
- **STEP 7**: Build responsive `static/description/index.html`
- **STEP 8**: Final verification summary

Output: Module ready for Odoo app store submission.

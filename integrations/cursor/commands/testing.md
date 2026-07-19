# testing

> **Odoo frontend UI testing and documentation generation** — screenshots, GIF animations, and responsive `static/description/index.html`.
> Requires all tasks `[x]` in docs/tasks.md.

## Usage
```
/testing 19
/testing 18
/testing 17
```

## Gate Check
⛔ If any `[ ]` tasks remain in docs/tasks.md → stop and redirect to `/start-coding {version}`.

## What This Does
1. Auto-installs system dependencies (Node.js, agent-browser, ffmpeg) if missing
2. Installs/updates the module via manage_modules.sh
3. Navigates all module menus with agent-browser, captures screenshots, handles JS errors
4. Generates AI icon and banner for the module
5. Converts recordings to GIF animations
6. Builds responsive `static/description/index.html` documentation page

## Instructions
Load `.cursor/AgentSkills/CommandingSystem/SKILL.md` then load `.cursor/AgentSkills/CommandingSystem/testing_workflow.md`.
Execute STEP 1 through STEP 8. Ask for version (17|18|19) and module name if not provided.

# VS Code Copilot Chat Integration

1. Copy `prompts/*.prompt.md` from this directory into your project's
   `.github/prompts/`.
2. Copy `context-templates/copilot-instructions.md` (from the kit root) into
   your project's `.github/copilot-instructions.md`.
3. Copy `plugin/skills/` (from the kit root) into `.github/AgentSkills/` in your
   project, preserving the directory structure, so the prompt files' relative
   references resolve.
4. Run `/plan-analysis`, `/start-coding`, `/testing`, or `/fleet` from Copilot
   Chat, passing the Odoo version as an argument. `/rules-check-drift` takes an
   optional diff range instead of a version.

# Cursor Integration

1. Copy `commands/*.md` from this directory into your project's `.cursor/commands/`.
2. Copy `context-templates/AGENTS.md` (from the kit root) into your project root,
   or symlink it — Cursor reads `AGENTS.md` for project context.
3. Copy `plugin/skills/` (from the kit root) into `.cursor/AgentSkills/` in your
   project, preserving the directory structure, so the command files' relative
   references resolve.
4. Use `/plan-analysis 19`, `/start-coding 19`, `/testing 19`, `/fleet 19`, or
   `/rules-check-drift` (no version argument) from the Cursor chat.

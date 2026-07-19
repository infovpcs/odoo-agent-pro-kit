# Codex Integration

Codex has no formal plugin system, but it reads `AGENTS.md` at the project root
natively — so the setup is direct:

1. Copy `context-templates/AGENTS.md` (from the kit root) into your project
   root as `AGENTS.md` (or symlink it, to pick up future kit updates automatically).
2. Copy `plugin/skills/` (from the kit root) into your project, preserving the
   directory structure, so `AGENTS.md`'s skill references resolve.
3. Optional — mirror the four command definitions as Codex custom prompts:
   copy `plugin/commands/*.md` into `~/.codex/prompts/`, stripping the
   Claude Code-specific YAML frontmatter (`description`/`argument-hint`) down
   to a plain markdown prompt, since Codex custom prompts don't use that
   frontmatter format.
4. Start Codex in the project directory — it will pick up `AGENTS.md`
   automatically at session start.

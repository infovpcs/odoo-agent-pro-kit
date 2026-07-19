# plan-analysis

> **Odoo requirement analysis, MCP model discovery, and PRD generation** for Odoo 17, 18, or 19.
> Produces a complete `docs/` folder with requirements, design, tasks, module metadata, and architecture diagram.

## Usage
```
/plan-analysis 19
/plan-analysis 18
/plan-analysis 17
```

## What This Does
1. Loads the CommandingSystem skill and version-specific Odoo skills
2. Uses MCP tools to discover models in the linked Odoo database
3. Asks clarification questions (module category, base model, enterprise?)
4. Generates a PRD draft for your review
5. Creates `{module_name}/docs/` with 5 files: requirements.md, design.md, tasks.md, module_meta.md, Architecture.md

## Instructions
Load `.cursor/AgentSkills/CommandingSystem/SKILL.md` then load `.cursor/AgentSkills/CommandingSystem/plan_analysis_workflow.md`.
Execute STEP 1 through STEP 11. Ask for version (17|18|19) if not provided.

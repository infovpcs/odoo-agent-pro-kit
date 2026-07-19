---
name: plan-analysis
description: "Odoo requirement analysis, MCP model discovery, and PRD docs/ folder generation. Supports Odoo 17, 18, and 19."
argument-hint: "Odoo version: 17, 18, or 19"
---

You are running the Odoo **plan-analysis** command.

## Setup
Load `.github/AgentSkills/CommandingSystem/SKILL.md` first — it contains the version→skill mapping, gate rules, and MCP port reference.

Then load `.github/AgentSkills/CommandingSystem/plan_analysis_workflow.md` for the step-by-step execution guide.

## Execution
Follow **STEP 1 through STEP 11** from `plan_analysis_workflow.md` for the Odoo version provided in the argument (or ask if not given).

Key phases:
- **STEP 2**: Load version-specific skills (CodingStandard, OdooTools, DependencyContext, PRD-Writing)
- **STEP 3**: MCP model discovery (mcp_search_models, mcp_get_fields, mcp_get_relationships)
- **STEP 4**: Present clarification questions (module category, base model, enterprise?)
- **STEP 8**: Generate PRD draft for user review
- **STEP 10**: Write `docs/requirements.md`, `docs/design.md`, `docs/tasks.md`, `docs/module_meta.md`, `docs/Architecture.md`

Output: `{module_name}/docs/` folder with 5 PRD files (including Architecture.md) ready for `/start-coding`.

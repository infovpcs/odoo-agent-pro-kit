---
description: Odoo /plan-analysis — requirement gathering, MCP model discovery, and PRD docs/ folder generation for Odoo 17, 18, or 19
---

You are running the Odoo **`/plan-analysis`** command.

## Ask First
If the user message does not include a version number, ask:
> "Which Odoo version? **[17 | 18 | 19]**"

## Step-by-Step Execution

// turbo
1. Load `AgentSkills/CommandingSystem/SKILL.md` — read it fully to get the version→skill mapping, gate rules, MCP ports.

2. Load `AgentSkills/CommandingSystem/plan_analysis_workflow.md` — this is your execution guide.

3. Follow **STEP 1 through STEP 11** from `plan_analysis_workflow.md` for the requested Odoo version.
   - Load the correct version-specific skills as specified in SKILL.md
   - Use MCP tools (mcp_search_models, mcp_get_fields) for live model discovery
   - Present clarification questions from STEP 4 before generating PRD
   - Create `{module_name}/docs/` folder with all 5 PRD files (including Architecture.md) on confirmation

4. End with the completion summary from STEP 11.

# /plan-analysis Workflow

Complete step-by-step execution guide for the `/plan-analysis (17|18|19)` command.

---

## STEP 0 (Optional): External Repo Auto-Load (Phase 25)

Before requirements deep-dive, check whether the user wants to build on external addons (GitHub/GitLab/Odoo.sh).

```python
# Ask once, then proceed without blocking
# "Do you want to load an external repository first? (GitHub/GitLab URL optional)"

if repo_url_provided:
    # version from command (17|18|19)
    load_result = load_git_modules_tool(
        repo_url=repo_url,
        version=version,
        provider=provider_or_auto,
        branch=branch_if_any,
        private_repo=private_flag,
    )
    # load_git_modules_tool auto-refreshes MCP context on success
```

Record loaded context for downstream commands:
- `external_dependencies` in `docs/module_meta.md` (provider, repo, branch, modules loaded)
- `save_memory_tool(key="external_dependencies", ...)` for `/start-coding` and `/testing`

If load fails, continue `/plan-analysis` with local workspace context and include warning in PRD.

---

## STEP 1: Parse & Announce

```
User runs: /plan-analysis 19
→ version = 19
→ Announce: "🔍 Starting Plan Analysis for Odoo 19..."
→ Ask for module name if not provided
```

---

## STEP 2: Load Version-Specific Skills (Level 2)

Load each skill in order and confirm it is read before proceeding:

```
1. read AgentSkills/Odoo19CodingStandard/SKILL.md
2. read AgentSkills/OdooTools19/SKILL.md
3. read AgentSkills/Odoo19ExistingDepencencyContext/SKILL.md
4. read AgentSkills/PRD-Writing/SKILL.md
5. read AgentSkills/excalidraw-diagram-skill/SKILL.md
```

> For Odoo 17: replace 19 with 17 in paths. For Odoo 18: replace with 18.

---

## STEP 3: MCP Model Discovery

Start MCP server for the target version if not already running:

```bash
# Odoo 19: port 8767, Odoo 18: port 8766, Odoo 17: port 8765
python AgentSkills/odoo_mcp/run_mcp_server.py --version {version}
```

Then use MCP tools to discover installed structures:

```python
# Search for base models relevant to the module
mcp_search_models(query="sale order")      # example for sales module
mcp_get_fields(model_name="sale.order")    # get all fields
mcp_get_relationships(model_name="sale.order")  # get related models
```

**If required module not installed:**
> ⚠️ Module `sale` not found as installed in the linked Odoo DB.
> Please install it via Settings → Apps, or confirm it exists in your addons path.
> Alternatively, I can scan the addons path directly (slower, uses more tokens).

**Fallback**: If MCP unavailable → read static context from `Odoo{V}ExistingDepencencyContext/SKILL.md`.

---

## STEP 4: Clarification Questions

Present structured questions. Wait for user answers before proceeding.

```
📋 PLAN ANALYSIS — Clarification Questions
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Q1: What is the primary module category?
  [1] Sales & CRM
  [2] Inventory & Manufacturing
  [3] Accounting & Finance
  [4] HR & Payroll
  [5] Website & E-commerce
  [6] Point of Sale
  [7] Custom: ______________________

Q2: Which Odoo base module does this extend or depend on?
  [1] sale / sale.order
  [2] account.move / account.invoice
  [3] stock.picking / stock.move
  [4] hr.employee / hr.leave
  [5] None — standalone module
  [6] Custom: ______________________

Q3: Is this built on top of an Odoo Enterprise module?
  [1] Yes — enterprise repo is already cloned at: ______________________
  [2] Yes — I need to clone the enterprise repo
  [3] No — Community only

Q4: What is the main problem this module solves? (free text)
  > ______________________

Q5: Who are the end users? (e.g., Sales Manager, Accountant, Warehouse Staff)
  > ______________________
```

---

## STEP 5: Enterprise Module Handling (if Q3 = Yes)

### 5a. Enterprise repo already cloned
```python
# Verify the path exists and load enterprise code context
enterprise_path = user_provided_path
# Scan for relevant enterprise modules to understand structure
```

### 5b. Need to clone
```
⚠️  Enterprise module access requires an active Odoo Enterprise contract.

Options:
  [1] I'll clone it manually:
      git clone git@github.com:odoo/enterprise.git --branch {version}.0

  [2] Auto-clone (requires GitHub access with Odoo Enterprise subscription):
      Provide your GitHub token: ______________________

After cloning, provide the local enterprise path and re-run /plan-analysis.
```

---

## STEP 6: GitHub / Deepwiki Documentation Lookup

Fetch official documentation for identified base modules:

```python
# Option A: GitHub MCP (if available)
github_search_code(
    query="sale_order inherit",
    repo="odoo/odoo",
    ref="{version}.0"
)

# Option B: Deepwiki MCP (if available)
deepwiki_fetch(url="odoo/odoo", page="sale_order")

# Option C: Direct URL read
read_url("https://github.com/odoo/documentation/tree/{version}.0/content/developer/reference/backend/orm.rst")
```

Extract:
- Model API definitions
- Available fields and their types
- View patterns (form, list, kanban)
- Security rule patterns

---

## STEP 7: Agent Persona Selection

Based on Q1 module category, load the relevant agent persona:

| Category | Agent | Path |
|----------|-------|------|
| Sales/CRM | OdooServerSide | `Agents/OdooServerSide/SKILL.md` |
| POS | OdooPOSAgent | `Agents/OdooPOSAgent/SKILL.md` |
| Website/E-commerce | OdooWebsiteAgent | `Agents/OdooWebsiteAgent/SKILL.md` |
| OWL/Frontend | OdooWebAgent | `Agents/OdooWebAgent/SKILL.md` |
| Migration/Upgrade | OdooMigrationAgent | `Agents/OdooMigrationAgent/SKILL.md` |
| All others | OdooServerSide | `Agents/OdooServerSide/SKILL.md` |

---

## STEP 8: PRD Draft Generation

Using `PRD-Writing/SKILL.md` templates and all gathered context, generate:

```markdown
# {Module Display Name} — PRD Draft

## Functional Requirements
[From Q4 + Q5 + clarification discussion]

## Technical Design
[Based on MCP model analysis + coding standards]

## Implementation Tasks
[Task checklist from PRD-Writing skill template]

## Architecture & Flow Diagram
[Overview of the flow diagram embedded from Architecture.md generated using the excalidraw-diagram skill]

## Proposed Module Metadata
- Module name: {technical_name}
- Author: {user_name / company}
- License: LGPL-3 (Community) / OPL-1 (Proprietary)
- Odoo version: {version}.0
- Category: {Q1 answer}
- Depends: {list of dependency modules}

## Architecture Diagram (Optional)
[If the user requested a visual architecture diagram, this will be generated using the excalidraw-diagram-skill and copilot_odoo_agent.py agents to model the MCP and dependencies data visually, outputting directly to Architecture.md]
```

**Present draft to user for review before writing files. Also ask if they would like an architecture diagram generated using the excalidraw-diagram skill based on the MCP findings and embedded into a dedicated `Architecture.md`.**

---

## STEP 9: Module Name, Author & License Confirmation

```
📝 Module Metadata Confirmation
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Proposed module name: {technical_name}
  ✅ Accept  |  ✏️  Change: ______________________

Author / Company: {detected_or_asked}
  ✅ Accept  |  ✏️  Change: ______________________

License:
  [1] LGPL-3  — Open source, can be freely distributed (recommended for Community)
  [2] OPL-1   — Odoo Proprietary License (for commercial/enterprise modules)
  [3] MIT     — Fully permissive
  [4] Other: ______________________

Anything else to add or change in the PRD? (Including generating an .excalidraw diagram and Architecture.md?)
  ✅ Looks good, create files  |  ✏️  Changes / Diagram generation: ______________________
```

---

## STEP 10: Create Module PRD Output Files

After confirmation, create the docs/ folder and all PRD files at the correct target location:

```python
# 1. Resolve target path (Phase 20.5)
# Use version-specific custom addons path based on {version}
custom_keys = {
    "17": "ODOO17_CUSTOM_ADDONS",
    "18": "ODOO18_CUSTOM_ADDONS",
    "19": "ODOO_CUSTOM_ADDONS"
}
key = custom_keys.get(str(version))
target_root = os.getenv(key) or os.getenv("ODOO_CUSTOM_PATH") or os.getcwd()
module_dir = os.path.join(target_root, module_name)
docs_dir = os.path.join(module_dir, "docs")

# 2. Create directories with absolute path
os.makedirs(docs_dir, exist_ok=True)

# 3. Write each file using absolute paths
write_file(os.path.join(docs_dir, "requirements.md"), requirements_content)
write_file(os.path.join(docs_dir, "design.md"), design_content)
write_file(os.path.join(docs_dir, "tasks.md"), tasks_content)
write_file(os.path.join(docs_dir, "module_meta.md"), meta_content)

# 4. Generate Excalidraw Diagram & Architecture.md (If Requested)
# Use excalidraw-diagram skill and copilot_odoo_agent.py agents to generate `{module_name}/docs/architecture.excalidraw` mapping the whole flow.
# Render the diagram to PNG for validation: `cd .claude/skills/excalidraw-diagram/... && uv run python render_excalidraw.py ...`
# Write `{module_name}/docs/Architecture.md` document that embeds the rendered PNG diagram and explains the architecture flows.
```

**module_meta.md format:**
```markdown
# Module Metadata

- **Technical Name**: {module_name}
- **Display Name**: {display_name}
- **Author**: {author}
- **License**: {license}
- **Odoo Version**: {version}.0
- **Category**: {category}
- **Depends**: {depends_list}
- **Created**: {date}
- **Analysis Version**: plan-analysis v1.0

## External Dependencies
- **Enabled**: {yes_or_no}
- **Provider**: {github|gitlab|none}
- **Repository**: {repo_url_or_none}
- **Branch**: {branch_or_default}
- **Loaded Modules**: {comma_separated_modules_or_none}
- **Auto-Load Status**: {success|warning|skipped}
```

---

## STEP 11: Agentic Memory Storage (Phase 20.G)

Before concluding, save key architectural facts using `save_memory_tool` so that `/start-coding` and `/testing` can inherit them later.

```python
save_memory_tool(key="module_category", content="{Q1 answer}")
save_memory_tool(key="base_dependencies", content="{depends_list}")
save_memory_tool(key="core_models", content="{models analyzed during MCP discovery}")
```

---

## STEP 12: Completion Summary

```
✅ Plan Analysis Complete!

📁 Files created in {module_name}/docs/:
  • requirements.md  — {N} functional requirements
  • design.md        — technical architecture decisions
  • Architecture.md  — visual architecture and flow diagram (if generated)
  • tasks.md         — {N} implementation tasks
  • module_meta.md   — module name, author, license confirmed

🚀 Next step: Run /start-coding {version} to begin implementation
   The agent will load these PRD files automatically.
```

---

## Gate Check Output (if docs/ already exists)

```
ℹ️  PRD files already exist at {module_name}/docs/
Options:
  [1] Continue — use existing docs (skip to /start-coding)
  [2] Regenerate — overwrite existing docs with new analysis
  [3] View existing — show current docs/requirements.md
```

**If [2] Regenerate is chosen:**
```python
# Clear the cross-session memory pool from any previous runs
clear_memory_tool(confirm=True)
```

---

## FINAL STEP: Context Handoff (Phase 25)

After all PRD docs are written and confirmed, run the context writer:

```python
import re, os
tasks_content = open(os.path.join(module_dir, "docs/tasks.md")).read()
task_count = len(re.findall(r'^- \[ \]', tasks_content, re.M))
with open(os.path.join(module_dir, "docs/requirements.md")) as f:
    req_summary = f.readline().strip().lstrip('#').strip()
```

```bash
python3 AgentSkills/auto_test/context_writer.py write \
  --module {module_name} \
  --module-dir {module_dir} \
  --version {version} \
  --command plan-analysis \
  --summary "PRD complete. {task_count} tasks defined. {req_summary}" \
  --tasks-done 0 \
  --tasks-total {task_count}
```

This creates `{module_dir}/CLAUDE.md`, `GEMINI.md`, `AGENTS.md` — all agent platforms auto-load this context when the next command starts.

**Output confirmation:**
```
Context written: {module_dir}/CLAUDE.md
Context written: {module_dir}/GEMINI.md
Context written: {module_dir}/AGENTS.md

Next command will auto-load this context:
  /start-coding {version} {module_name}
```

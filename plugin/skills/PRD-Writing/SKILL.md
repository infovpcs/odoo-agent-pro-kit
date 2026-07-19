---
name: prd_writing
description: Produce concise PRD artifacts (requirements, design, tasks) for Odoo custom apps, mapping new needs to existing functionality. Use when creating product requirements documents.
version: 1.0.0
author: VPCS Team
category: documentation
odoo_versions: ["17.0", "18.0", "19.0"]
tags: ["prd", "requirements", "design", "tasks", "documentation", "planning"]
---
## Goal
Produce concise PRD artifacts (requirements → design → tasks) for Odoo custom apps, mapping new needs to existing functionality first, and staying aligned with 19.0 standards/tooling.

## Inputs
- Business brief and stakeholders.
- Existing dependency context (see AgentSkills/Odoo19ExistingDepencencyContext/SKILL.md).
- Coding standards (see AgentSkills/Odoo19CodingStandard/SKILL.md and sample_module/ODOO19_CODING_STANDARDS.md).
- Reusable tools (see AgentSkills/OdooTools19/SKILL.md) and upstream refs (odoo/odoo 19.0, 18.0, 17.0).

## Outputs
- requirements.md: scoped needs and existing/new mapping.
- design.md: solution outline derived from requirements.
- tasks.md: actionable breakdown derived from design.
- Architecture.md: visual architecture document demonstrating the entire flow diagram, generated using the `excalidraw-diagram-skill` combined with analysis from `copilot_odoo_agent.py` agents.
- Progress seeds: feature blocks align with agent `progress.json` (task, details, priority, extends_model, files_to_create, sub_tasks ending with LIVE TEST).

## Process
1) Gather context: confirm scope, actors, pain points, and constraints; review existing modules/customizations before proposing net-new.
2) Draft requirements.md: capture existing functionality mapping, new stories with acceptance, data/security, integrations, NFRs, risks.
3) Draft design.md from requirements: architecture choices, data model, flows, UI, integrations, reuse plan, performance, migration, testing.
4) Generate Architecture.md: use `excalidraw-diagram-skill` combined with `copilot_odoo_agent.py` agents to map out the whole flow diagram.
5) Draft tasks.md from design: ordered, testable tasks with dependencies and acceptance; mirror the progress.json sub_tasks order and include a final LIVE TEST step.
6) Review with stakeholders; revise until requirements → design → Architecture → tasks stay consistent.

## Quality bars
- Prefer reuse/extension over rewrite; note upgrade impacts.
- Keep artifacts concise and structured; avoid jargon and prose bloat.
- Every new feature has a measurable acceptance outcome and a test hook.
- Note cross-version compatibility when feasible (19/18/17).

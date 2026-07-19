---
name: Fleet Orchestration Workflow
description: Orchestrates parallel Odoo custom app development using Copilot CLI /fleet and autopilot.
version: 1.0.0
category: commanding
tags: [fleet, autopilot, orchestration, scaling]
---

# 🚀 Fleet Orchestration Workflow (`/fleet` & Autopilot)

This workflow defines how the agent handles parallel, multi-module Odoo development tasks when invoked via the GitHub Copilot CLI `/fleet` command or in `--autopilot` mode.

## **STEP 1: Fleet Command Parsing & Session Allocation**

When a `/fleet` command is received (e.g., `/fleet M1: sale_custom, M2: stock_custom`), the orchestrator MUST:
1. Parse the target modules to be developed in parallel.
2. Allocate a distinct workspace and progress directory for each module.
3. Validate session isolation: Ensure `sessions/M1_progress.json` and `sessions/M2_progress.json` do not intersect and manage distinct Odoo dependencies.

## **STEP 2: Parallel Dispatch (Autopilot Delegation)**

For each identified module session:
1. The orchestrator spawns an isolated `agent_api.py` subprocess or Python thread.
2. The orchestrator injects the respective module context into each session.
3. Each subagent automatically begins executing its own `/plan-analysis` -> `/start-coding` -> `/testing` lifecycle in `--autopilot` mode.
   * `&` background delegation ensures the main CLI terminal is not blocked.

## **STEP 3: Subagent Lifecycle Monitoring**

While the subagents are running autonomously:
1. The orchestrator polls the `sessions/{module_name}_progress.json` for status updates (`in_progress`, `completed`, `failed`).
2. If a subagent encounters a fatal error or exceeds `AGENT_MAX_LOOPS`, the orchestrator marks that specific module stream as FAILED and captures the error log, allowing other modules to continue.

## **STEP 4: Aggregation & Final Reporting**

Once all subagents in the fleet have concluded (Success or Failure):
1. The orchestrator reads the final completion status from all module sessions.
2. A single, comprehensive "Fleet Summary Report" is generated.
3. The report is output to the CLI, detailing:
   * **Modules Successfully Completed**: Git commit hashes, feature summaries, and test statuses.
   * **Modules Failed**: Error trace and last attempted task.

## **Rules & Constraints**

*   **No Cross-Contamination**: A subagent working on `module_A` MUST NOT write files or context into `module_B`'s directory.
*   **Database Locking Avoidance**: When multiple agents install modules or run backend tests on the same Odoo DB, the orchestrator MUST serialize sensitive operations (e.g., `odoo-bin -i module_A,module_B`) or use isolated DBs if configured.
*   **Autopilot Compliance**: In autopilot mode, agents MUST NOT prompt the user for interactive confirmation mid-task. All decisions must be made autonomously or safely deferred/failed if critical information is missing.

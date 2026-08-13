---
name: Fleet Orchestration Workflow
description: Orchestrates parallel Odoo custom app development using Copilot CLI /fleet and autopilot.
version: 2.0.0
category: commanding
tags: [fleet, autopilot, orchestration, scaling]
---

# 🚀 Fleet Orchestration Workflow (`/fleet` & Autopilot)

This workflow defines how the agent handles parallel, multi-module Odoo development tasks when invoked via the GitHub Copilot CLI `/fleet` command or in `--autopilot` mode.

## **STEP 1: Fleet Command Parsing & Session Allocation**

When a `/fleet` command is received (e.g., `/fleet M1: sale_custom, M2: stock_custom`), the orchestrator MUST:
1. Parse the target modules to be developed in parallel.
2. Call `sandbox/bin/sandbox-fleet create --version <version> --module <module>` once per task. Each allocation is a separate local Docker Sandbox microVM, clone, branch, inner Compose project, database, filestore, logs, and result tree.
3. Do not create subprocess/thread agents in a shared workspace. Shared and remote scheduling belongs to Pro.

## **STEP 2: Parallel Dispatch (Autopilot Delegation)**

For each allocated Sandbox, dispatch work with `sbx exec <session> -- ...`. The
agent follows `/plan-analysis` -> `/start-coding` -> `/testing` inside its own
clone. The Community coordinator is bounded to the configured local-host limit.

## **STEP 3: Subagent Lifecycle Monitoring**

While the subagents are running autonomously:
1. Poll `sandbox/bin/sandbox-fleet status`; aggregation reads coordinator-owned manifests and never grants cross-session workspace writes.
2. Use `sandbox-fleet cancel <session>` for graceful cancellation. A failed or cancelled session is reported independently and siblings remain running.

## **STEP 4: Aggregation & Final Reporting**

Once all subagents in the fleet have concluded (Success or Failure):
1. The orchestrator reads the final completion status from all module sessions.
2. A single, comprehensive "Fleet Summary Report" is generated.
3. The report is output to the CLI, detailing:
   * **Modules Successfully Completed**: Git commit hashes, feature summaries, and test statuses.
   * **Modules Failed**: Error trace and last attempted task.

## **Rules & Constraints**

*   **No Cross-Contamination**: A session working on `module_A` MUST NOT enter or write `module_B`'s Sandbox. Even duplicate module names receive unique sessions and branches.
*   **Cleanup Guard**: Before destroy, record a commit, push, or patch export with `sandbox-fleet protect`; destructive cleanup is otherwise refused unless the operator explicitly uses `--force`.
*   **Maintenance**: Run `sandbox-fleet maintain` to stop idle sessions and report stopped sessions whose retention is due. It never auto-destroys unexported work.
*   **Autopilot Compliance**: In autopilot mode, agents MUST NOT prompt the user for interactive confirmation mid-task. All decisions must be made autonomously or safely deferred/failed if critical information is missing.

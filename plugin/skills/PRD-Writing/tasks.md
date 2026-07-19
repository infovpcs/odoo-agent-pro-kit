# Task Breakdown (PRD Output 2)

Format each task: `ID | Description | Owner | Depends On | Acceptance`.

- Planning: dependency context review; confirm scope and risks.
- Data model: models/fields/constraints/security rules defined and approved.
- Backend logic: business rules, cron/jobs, access control enforcement.
- UI: views/wizards/menus/actions; usability and translations.
- Integrations: endpoints, mapping, retries/idempotency, secrets handling.
- Data migration: scripts/backfill; dry-run results captured.
- Testing: unit/integration/UI/acceptance; fixtures and edge cases.
- Observability: logging/audit; alerts if applicable.
- Docs & handover: user notes, admin runbooks, release notes.
- Rollout: deploy plan, rollback, smoke checklist.

## Progress-Oriented Template (mirrors agent progress.json)
- Task (feature) → Sub-tasks (ordered) → Acceptance.
- Include a final sub-task: "LIVE TEST: install/update".
- Keep sub-tasks small: model fields, constraints, __init__.py, views, security, data, tests.

Example (concise):
- Task: Customer Credit Hold
	- Sub: Add credit_hold field on res.partner
	- Sub: Block confirmation when credit_hold = true
	- Sub: Add warning banner in sale order form
	- Sub: Update access rules (if needed)
	- Sub: LIVE TEST: update module and validate flow
	- Acceptance: credit-hold customers cannot confirm orders; banner visible; tests green.

# Design (PRD Output 1)

## Summary
- Objective, target users, and deployment scope (companies, environments).

## Architecture
- Key modules/features reused vs new; inheritance vs extension choices.
- Data flow diagram description (sources → transformations → destinations).

## Data Model & Security
- Models, fields, relations; computed/stored rules; constraints.
- Record rules/ACL per role; access patterns (create/read/update/delete).

## Application Flows
- Main user journeys (step list). Note validations, errors, side effects.
- Background/cron jobs and triggers.

## UI/UX
- Views to add/extend (tree/form/kanban/wizard), grouping/sorting, labels.
- Usability notes: defaults, search domains, responsive needs.

## Integrations
- Interfaces, payloads, mapping, idempotency, retries, auth, rate limits.

## Reuse & Dependencies
- Existing modules/customizations leveraged; upgrade impacts.
- Tech debt to avoid; compatibility for 19/18/17 if relevant.

## Progress JSON Mapping
- For each feature: set `extends_model`, `files_to_create`, `priority`, and granular `sub_tasks`.
- Ensure last sub_task is "LIVE TEST: install/update" to match agent loop.
- Keep descriptions concise to stay tool-friendly.

## Performance & Quality
- Expected volumes; indices/domains; caching; batch vs real-time.
- Logging/audit, observability hooks.

## Migration & Rollout
- Data migration steps; backfill strategy; cutover/rollback plan.

## Testing Strategy
- Unit/integration/UX/acceptance coverage; fixtures; edge cases.

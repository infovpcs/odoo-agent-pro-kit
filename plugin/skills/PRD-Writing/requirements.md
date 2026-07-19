# Requirements (PRD Input)

## Business Context
- Purpose of the custom app and target business outcome.
- Primary KPIs and success criteria.

## Scope
- In scope: bullet list of capabilities/processes.
- Out of scope: what will not be addressed now.

## Actors & Personas
- Who uses it, their goals, and key pain points.

## Existing Functionality Mapping
- Core module / behavior / gaps.
- Customizations already present (19.0) and constraints.
- Data to preserve or migrate.

## New Functionality (User Stories)
- As a <role>, I want <capability> so that <benefit>.
- Acceptance: observable outcome, data/state changes, errors handled.

## Data & Rules
- Entities, fields, validation rules, default values.
- Security/ACL expectations per role.

## Integrations
- Systems, endpoints, direction (push/pull), trigger, payload, auth.

## Reporting & Analytics
- KPIs, dimensions, filters, freshness/latency needs.

## Non-Functional
- Performance targets, scalability, availability, auditability, UX constraints, localization.

## Risks & Assumptions
- Known risks, blockers, assumptions to validate early.

## Progress JSON Seeds (align with agent format)
- Module: <name>
- Depends: ["base", ...]; parent modules to extend.
- Features (one per story/custom capability):
	- task: <short name>
	- details: <what is custom vs reused>
	- priority: high|medium|low
	- extends_model: <existing model> or null
	- files_to_create: ["models/x.py", "views/x.xml", ...]
	- sub_tasks: ordered steps ending with "LIVE TEST: install/update".

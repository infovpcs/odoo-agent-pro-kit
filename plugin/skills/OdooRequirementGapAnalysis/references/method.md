# Evidence-backed gap-analysis method

## Evidence hierarchy

Use the strongest available evidence for the exact target version:

1. Live read-only metadata and installed-module state when the customer's database is in scope.
2. Target-version Odoo Community and Enterprise source: manifests, models, views, security, data, and tests.
3. Official Odoo documentation for the target version.
4. Verified existing custom or Apps Store module code.
5. Clearly labelled inference or assumption.

Marketing descriptions, module names, screenshots, and memory are discovery aids, not sufficient proof for a consequential Fit decision. Record the evidence location in a human-readable form.

## Atomic requirements

One row should describe one independently testable business outcome. Split a sentence when parts can have different fit, priority, owner, module, or acceptance criteria.

Minimum fields:

- Requirement ID
- Source document, section, and page
- Business area
- Requirement
- Priority
- Fit classification
- Standard coverage percentage
- Odoo app(s) and technical module(s)
- Edition
- Available standard behavior
- Configuration needed
- Remaining gap
- Custom work item or disposition
- Evidence
- Assumptions/open question

Preserve requirement wording faithfully but paraphrase long copyrighted passages. Flag contradictions, missing referenced sections, and ambiguous priority.

## Classification

- **Fit:** The outcome is delivered by standard Odoo in the target version with configuration, master data, access rights, routes, or templates. As a guide, coverage is 90-100%.
- **Partial:** Standard Odoo delivers the core but a bounded extension, report, field set, approval rule, integration, or process decision remains. Guide: 30-89%.
- **Gap:** Standard Odoo delivers little or none of the outcome, or the missing control is the essence of the requirement. Guide: 0-29%.

Coverage is a reasoned aid, not a substitute for the written explanation. A hard compliance or control gap can keep a requirement Partial or Gap even when many screens already exist.

## Custom work items

Group gaps by cohesive deployable outcome, not one module per requirement. Each item should include:

- Stable ID and proposed module/work-package name
- Scope: core, phase 2, optional, or excluded
- Effort type: model/UI, business logic, report/dashboard, integration, migration, or other
- Requirements covered
- Business explanation
- Target-version technical approach
- Dependencies and reuse candidates
- Data model/migration, security, audit, and reporting impact
- Estimate, confidence, and acceptance criteria

Check that all Gap rows have a disposition and that no custom item is orphaned.

## Apps Store and reuse screening

Treat this as an optional evidence track when the user has a module catalogue or repositories:

1. Screen catalogue descriptions to find candidates.
2. Verify candidate manifests, supported versions, models, views, security, and meaningful feature code.
3. Map only the part of a requirement actually covered.
4. Record target status: ready, needs porting, near-miss, rejected, or unknown.
5. Include porting/integration/QA cost and licence cost; reuse is not zero effort by default.

Never send confidential customer requirements to an external classifier without authorization.

## Estimation

Estimate in person-hours or person-days and state the conversion. Keep separate:

- Standard configuration
- Data migration and cleansing
- Custom development by work item
- Integrations
- Testing/UAT and fixes
- Training and documentation
- Project management
- Contingency

A useful baseline is conventional delivery. A pipeline-assisted or reuse-accelerated scenario is optional and must show every factor, requirement change, reused module, deferred item, and validation cost. Do not advertise AI or reuse savings without a defensible basis. Use formulas in the workbook so inputs and totals recalculate.

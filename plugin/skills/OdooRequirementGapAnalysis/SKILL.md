---
name: odoo_requirement_gap_analysis
description: Use when a client shares a requirements document (PDF, DOCX, spreadsheet, notes) for an Odoo 17/18/19 implementation and you must turn it into a verified gap analysis - requirement-to-app mapping checked against the Community and Enterprise code, Fit/Partial/Gap classification, custom work items with implementation-time estimates that account for the automated Odoo development lifecycle (plan, code, sandbox test, QA), reuse of an organisation's module catalogue, and requirement changes that shorten delivery.
version: 1.1.0
category: analysis
odoo_versions: ["17.0", "18.0", "19.0"]
tags: ["gap-analysis", "requirements", "estimation", "fit-gap", "odoo", "implementation", "planning", "delivery-profile"]
---

# Odoo Requirement Gap Analysis

## Goal

Turn any requirements document into a gap analysis that a delivery team can quote and build from:
every claim of "Odoo covers this" is checked against code, every gap becomes a custom work item that
can be fed straight into `/plan-analysis`, and the estimate reflects how the work is actually delivered
(the automated lifecycle), not a generic waterfall.

Outputs (one dataset, several renderers so the files can never disagree):

1. a gap-analysis document (DOCX) - findings, module-wise coverage, gap register, estimate, risks;
2. a mapping workbook (XLSX) - requirement mapping, module inventory, estimate model with live formulas;
3. per-work-item PRD stubs (`docs/requirements.md`, `design.md`, `tasks.md`) that `/start-coding` can consume.

## References and reusable components

- [references/method.md](references/method.md) - evidence hierarchy, atomic-requirement fields, Fit/Partial/Gap
  thresholds, custom work-item fields, reuse screening and estimation rules. Read before Phase 1.
- [references/deliverables.md](references/deliverables.md) - DOCX outline, workbook sheet list and the validation
  gates. Read before Phase 9.
- `scripts/audit_document.py` (Phase 0), `scripts/verify_modules.py` (Phase 2), `scripts/catalog_match.py` (Phase 8).
- `templates/delivery-profile.template.md` - the private delivery profile (Phase 8).
- Reference build pipeline (Phase 9): keep one proven one-dataset / many-renderers build (dataset modules, estimate
  model, workbook and document renderers, chart script, delivery sync) and record its location in the delivery
  profile under "Reference build". For a new client, copy it into the new working folder, replace only the dataset
  files and re-run the renderers; do not fork the renderers per client.

## Dynamic parameters

Resolve these first. Read them from the environment or the workspace context; ask the user only for
what is missing. Never hard-code a path or a client name into the deliverables.

| Parameter | Default / where it comes from |
|---|---|
| `ODOO_VERSION` | `17`, `18` or `19` - ask if the document does not say. Some documents say "Odoo or similar": confirm Odoo. |
| `COMMUNITY_ADDONS` | `$HOME/odoo-workspaces/<v>_workspace/<v>.0/addons` (created by `bootstrap.sh`) |
| `ENTERPRISE_ADDONS` | ask; if none, mark every Enterprise-only module as "licence required" |
| `KNOWLEDGE_BASE` | an OKF bundle for the version (for example `odoo<v>-okf`) - used to cite what each app does |
| `GAP_PROFILE` | delivery-profile file (see Phase 8). Discovery order: `$GAP_PROFILE`, `./gap_profile.md`, `~/.config/odoo-gap-analysis/profile.md`. If none exists, use the generic factors below. |
| `OUTPUT_DIR` | `./gap_analysis` next to the source document |
| `EDITION_TARGET` | `enterprise` (default) or `community` |

## Phase 0 - Intake gate (do this before mapping anything)

Run `scripts/audit_document.py <document>` and work through the checklist. Report every finding to the
user; do not silently resolve them.

| # | Check | How | If it fails |
|---|---|---|---|
| 1 | The file is readable and complete | script extracts PDF/DOCX text (PyMuPDF, pypdf, pdftotext or pandoc); a scanned PDF returns almost no words | ask for a text version or note that OCR is needed |
| 2 | Structure is understood | heading map printed by the script; untitled blocks (content with no heading) noted by hand | record them as their own requirement group |
| 3 | Cross-references resolve | script lists `Section N` references with no heading, and resolved references with the heading title | list mismatches as open questions; use the printed headings, never the cross-references |
| 4 | Referenced sections are present | unresolved references usually mean missing chapters (open questions, evaluation criteria) | ask for the missing chapters before estimating |
| 5 | Priorities are consistent | script flags "Nice to Have" sections that use words like "hard requirement" | ask the author; state the assumption you used in the estimate |
| 6 | Platform and edition | "Odoo or similar" wording, Community vs Enterprise, hosting (SaaS, Odoo.sh, on-premise) | confirm; hosting decides Studio, IAP and custom-module options |
| 7 | Systems of record | which existing tools stay (payroll, project, banking, e-invoicing) | draw the integration boundary early |
| 8 | Sizing inputs | users, legal entities, currencies, data volumes, go-live date, rollout model (unified or phased) | list as open questions; they drive licence and migration effort |
| 9 | Compliance gates | tax, audit, data-residency or sign-off requirements that block go-live | mark as hard gates in the plan |
| 10 | Confidentiality | client names and figures must not enter a public repository or a public skill | see "Publishing rules" |
| 11 | Tooling preflight | code trees exist, MCP server reachable (`mcp_search_models`), Python libs present | fix before continuing |

## Phase 1 - Atomise the requirements

- One row per testable requirement, with a stable ID (`R-001 ...`), the printed section number, the
  document's own priority (Must / Should / Nice / Not stated) and a short title.
- Keep the document's wording in the title; put your interpretation in separate columns.
- Group rows into 8-12 functional areas. Keep areas in the document's order.
- Derived requirements (implied but not written, for example a statutory return that follows from a
  described flow) get their own row and are flagged "derived".

## Phase 2 - Map to Odoo apps and verify in code

1. For each row list the Odoo apps and the **technical module names** that would cover it.
2. Verify every name: `scripts/verify_modules.py --community $COMMUNITY_ADDONS --enterprise $ENTERPRISE_ADDONS --dataset rows.json`.
   The build fails on a missing module. Edition (Community / Enterprise), version and licence come from the manifest.
3. For every claim that decides Fit versus Gap, read the source rather than trusting memory. Typical checks:
   field-level `groups=` on cost fields, uniqueness constraints, whether a report or workflow exists, whether
   a state machine can be extended. Record each check in an evidence table (capability, file, finding).
4. Cite the version's documentation (OKF bundle) for how the app is configured.
5. Never map a requirement to a feature you could not find. Say "not found in 19.0" and mark it Gap.

## Phase 3 - Classify

| Class | Meaning | Coverage guide |
|---|---|---|
| Fit | met by standard Odoo with configuration only | 90% or more |
| Partial | standard covers the core; extra fields, a report, a rule or a thin extension is needed | 30% to 89% |
| Gap | little or nothing in standard; needs a custom module or an integration | under 30% |

Coverage % is a judgement used for prioritisation, not a measurement - say so in the document. Store fit
as an editable input so stakeholders can re-classify and see the totals recalculate.

## Phase 4 - Group gaps into custom work items

- One work item (`CM-01 ...`) per module that could be built and shipped on its own, named with a
  project prefix (for example `<prefix>_customer_advance`), with: short explanation, Odoo technical
  approach, dependencies, the requirements it closes, an effort type, and a scope tag
  (Core = go-live, Phase-2, Optional).
- Every Gap row must reference a work item; every work item must be referenced by a row (the build checks both).
- Put the build order in a dependency list: foundation (security, masters), then the module the client calls
  most critical, then the rest. A unified go-live is sequenced technically, not by department.

## Phase 5 - Edge cases, integrations, risks, open questions

- Turn the document's edge-case list into a matrix: Standard / Configuration / Custom, with how it is handled.
- One integration table: system, purpose, direction, Odoo approach, technology, note.
- Risks with rating and mitigation; open questions with impact (High / Medium / Low). Close High items
  before the estimate is committed.

## Phase 6 - Implementation-time estimate (lifecycle-aware)

Estimate **implementation time**, not a waterfall of separate development, testing and QA phases. When the
team delivers through the Odoo development lifecycle and its sandbox pipeline, module-level design, coding,
backend and frontend tests, quality gates and documentation are one automated loop.

### 6.1 What the lifecycle already covers

| Activity | Covered by | Evidence to keep |
|---|---|---|
| Requirements to PRD, live model discovery | `/plan-analysis <v> <module>` (workflow steps 1-11, `mcp_search_models`, `mcp_get_fields`, `mcp_validate_field`) | `docs/requirements.md`, `design.md`, `tasks.md` |
| Coding to the version's standard | `/start-coding <v>` with the CodingStandard skill; each task ends with a live test | task list with `[x]` |
| Install / update / test in an isolated database | `sandbox/bin/sandboxctl module <session> install\|update\|test <module>`; one microVM and one private Docker daemon per module task | result JSON under `.sandbox/sessions/<id>/` |
| Frontend tests, screenshots, user guide | `/testing <v>` | documentation with screenshots |
| Parallel modules | `/fleet <v>` with `sandbox/bin/sandbox-fleet` (bounded by host capacity) | coordinator manifests |
| Guardrails and drift | plugin hooks and `/rules-check-drift` | drift report |

Consequences for the estimate:
- Do **not** add a separate module-test or QA percentage on top of a work item that goes through this loop.
  Keep only human-gated verification (see 6.2).
- Cross-module integration testing is largely covered by fleet runs on the sandbox; keep a small
  human share for scenario walk-throughs.

### 6.2 Model

Split every work item into a **pipeline-covered** part and a **human-gated** part.

```
pipeline_days  = design + build + module tests + docs        (compressed by the pipeline factor for its effort type)
human_days     = workshops + review + data cleansing + UAT + training + statutory sign-off + external access
item_days      = baseline_days x factor(type) [ x (1 - reuse%) ] [ using the post-change baseline ]
```

Report three scenarios side by side so the client can choose:

1. **Conventional** - baseline days per item, no lifecycle credit.
2. **Pipeline-assisted** - baseline x factor(type); testing/QA absorbed as described in 6.1.
3. **Profile-accelerated** - scenario 2 after applying the delivery profile: accepted requirement changes
   (Phase 7), reusable catalogue modules (Phase 8) and any factor overrides. Every reduction carries an
   evidence tag and a confidence level.

Add separate lines for configuration, data migration, testing/UAT/training/go-live, project management and
contingency. Keep all percentages and factors as editable inputs in the workbook (blue font), and totals as formulas.

### 6.3 Default factors (use only when no profile overrides them)

| Effort type | Factor | Reason |
|---|---|---|
| Model and UI | 0.50 | models, views, security and data files are repeatable and follow the coding standard |
| Business logic | 0.55 | constraints, workflows and wizards need design and review |
| Reports and dashboards | 0.55 | generated quickly, validated with the business |
| Integration | 0.70 | external APIs and sandbox access keep a human in the loop |
| Configuration | 0.80 | scripts and import templates help; workshops do not shrink |
| Data migration | 0.60 | transformation scripts are automatable; cleansing is not |
| Testing, UAT, training, go-live | 1.00 | organisational effort; only cross-module integration testing is credited to the pipeline |

These are planning assumptions, not measurements. Label them so. Replace them with measured values as soon
as module runs have produced evidence (6.5).

### 6.4 Calendar time

- Elapsed time = total person-days / (team size x working days per month), then check the critical path:
  the module the client calls most critical goes first and later items depend on it.
- `/fleet` parallelism is limited by host capacity. The kit's recorded measurements say to provision one
  cold session at a time and run at most two constrained sessions on a 2-vCPU host; six sessions need a much
  larger host (its capacity notes give a starting size). State the host assumption next to any parallel plan.
- A unified go-live needs the parallel-run window and cutover time added after the last module, whatever the
  build speed.

### 6.5 Calibration loop

After each module run, record actual person-hours and the pipeline result JSON against the estimate, then
update the factor for that effort type in the profile. A factor without a source is an assumption; one with a
recorded run is measured. Do not publish an estimate as a measurement.

## Phase 7 - Requirement-change playbook (shorten delivery without losing intent)

For each work item ask whether a change to the requirement wording would deliver the same business outcome
sooner. Record each proposal as a row: current wording, proposed wording, work items affected, days before and
after, trade-off, and whether the client must decide.

Common levers:

| Lever | Typical form |
|---|---|
| Fit to standard | replace a custom screen with the standard flow plus configuration |
| Replace instead of integrate | move a side tool into the Odoo app that already does it, removing a connector |
| Warn before block | hard stop becomes a warning with an approval override; the hard stop can follow in phase 2 |
| Attributes and tags before models | structured fields and tags now, a dedicated model later |
| Defer analytics | store the data model on day one, build the analysis later |
| Standard approvals | use the approvals engine instead of a custom matrix model |
| Standard reports and pivots | replace a bespoke report by a saved standard report |
| Narrow the first release | acceptance criteria per item; extras become Phase-2 rows |
| Confirm applicability | a compliance item may not apply (confirm with the responsible professional before removing it) |

Never remove a statutory or safety requirement to save time. Mark conditional changes as conditional.

## Phase 8 - Delivery profile and reuse catalogue

An organisation's expertise lives in a **profile file**, not in this skill, so the skill stays generic.
Load it from `GAP_PROFILE`. A profile contains: accelerators (pipeline, tooling, prior engagements), a reuse
catalogue (ready-made modules with versions, prices and features), factor overrides with evidence tags, a
requirement-change playbook specific to the organisation, and its rate card. See
`templates/delivery-profile.template.md`.

If the profile lists a module catalogue (for example an apps store):

1. Build a catalogue JSON (module, versions, summary, description, price) and screen it:
   `scripts/catalog_match.py --catalog store.json --requirements rows.json --target 19.0`. The score is a
   shortlist aid only; keyword overlap is noisy.
2. Read each shortlisted module's manifest, models **and its own index page**
   (`static/description/index.html`, stripped to text): the index page carries the feature list the vendor
   describes and often shows limits the manifest hides (for example one amount trigger and admin-role approvers
   where the requirement asks for department and category rules). Judge the share of the requirement (or of a
   sub-feature) it really covers and record what in the code and page supports it.
3. Optional classification assist. A decision model (a "System One" classifier such as TypeSafe Jev) can screen
   the whole catalogue in seconds instead of hours. Rules that kept it accurate:
   - send only public catalogue text (manifest and index page) plus generic capability questions; never send
     client requirement text unless the client has agreed and the service's retention terms are known;
   - one request per module: one Choice for the capability domain, and several yes/no (Noul) questions of the form
     "Does this module ... ?" about generic capabilities, not client wording;
   - drop questions that fire on almost every module (for example "integrates with an external API");
   - phrase questions about what the module *is or does*, not the purpose it serves: "Is this module a data import
     tool that loads spreadsheet rows into records?" separated real import tools (0.97) from controls (0.02) while a
     purpose-laden wording scored the same tools about 0.3;
   - test the wording on a labelled sample plus a control set before the full run, and re-run after any change;
   - use 0.70 as a shortlist threshold, then measure recall on positives you verified in code and precision on the
     unlabeled positives (read each one), and report both;
   - use it for negative evidence too: capabilities where no module in the whole catalogue reaches the threshold
     are confirmed custom builds; keep a list of positives rejected after reading, so tables and text agree.
   The classifier output is a screening aid; it is never coverage evidence.
4. Apply the **inclusion threshold** (default 70% of the requirement or sub-feature): at or above it, include the
   module in the analysis as covering that part; below it, keep it as a near-miss note that may reduce effort but
   does not change the classification. Combined coverage is the larger of standard and catalogue coverage - do not add them.
5. Check the target version. A module published only for older versions needs a **port**: add port days and mark
   the row "port from <version>". Net saving = work-item days removed - port days.
6. Record price, licence and code-ownership terms from the profile so the client sees the licence cost next to the saving.
7. Show the reviewed catalogue in the workbook: every entry with a disposition (mapped, near-miss, reviewed - no
   match) so the reader can see the whole catalogue was considered, not only the hits.

Evidence tags for every reduction: **Measured** (recorded run), **Catalogue** (module verified in code, fit
stated), **Pattern** (know-how from earlier work; re-implemented, not copied), **Assumption** (planning value).
Add a confidence level (High / Medium / Low). Code written for a client belongs to that client under many
engagement models - reuse the pattern and the published catalogue, never another client's source.

## Phase 9 - Build the deliverables

- Keep one dataset (rows, work items, edge cases, integrations, risks, catalogue mappings) and render both
  files from it. Validate cross-references in the build (unknown work item, module not found, duplicate ID).
- Workbook: Read Me, Summary (formulas, chart), Requirement Mapping (filterable, Fit drop-down), App Mapping,
  Module Inventory, Gap and Customisation, Estimation (three scenarios, toggles for requirement changes and
  reuse), Requirement Changes, Catalogue Mapping and Screening, Edge Cases, Integrations, Open Questions and
  Risks. Blue = input, black = formula, green = cross-sheet link. Recalculate and confirm zero errors; cross-check
  totals against an independent calculation. Use only formulas LibreOffice can evaluate.
- Document: executive summary with headline numbers and decisions, method and evidence table, landscape module
  coverage tables, gap register, three-scenario estimate, delivery approach, edge cases, integrations, risks and
  open questions, module inventory appendix, notes on the source document.
- Render to PDF and look at the pages before delivering.

## Phase 10 - Hand off into the lifecycle

For each Core work item create the PRD stub from the dataset and start the loop:

```
/plan-analysis <v> <module>     # refine docs/requirements.md, design.md, tasks.md from the work item
/start-coding  <v> <module>     # task loop with a live test per task
/testing       <v> <module>     # frontend tests, screenshots, user guide
/fleet         <v>              # several independent modules in parallel, within host capacity
```

Record actual effort per module (6.5) and update the profile.

When the client accepts a scope, raise the quotation from the approved scenario through the organisation's
quotation workflow named in the profile (dry-run first; hours, rate, inclusions and exclusions taken from the
estimate, never from a draft).

## Phase 11 - Verification checklist before delivery

- [ ] every module name verified in the code trees; edition and version taken from manifests
- [ ] every Gap row has a work item and every work item has at least one row
- [ ] workbook recalculates with zero errors; totals match the independent calculation
- [ ] cross-references inside the deliverables resolve (R-xxx, CM-xx, section numbers)
- [ ] open questions cover every intake finding
- [ ] estimate states its assumptions, factors, exclusions and evidence tags
- [ ] catalogue inclusions show version status, port days, price and confidence
- [ ] pages rendered and inspected; charts readable in light and dark viewing
- [ ] no client-specific text in anything that will be published (see below)

## Publishing rules

- Client documents, names and figures stay in the private working folder and private knowledge base.
- A skill or template that is shared publicly holds only the method. Organisation-specific expertise, rate
  cards and client examples belong in the profile file, which stays private.
- The kit's skill validator rejects a list of private strings; run `./scripts/validate.sh` before publishing.

## Anti-patterns

- Trusting module names from memory instead of the code trees.
- Adding a separate testing/QA percentage to work that runs through the automated lifecycle.
- Presenting assumed acceleration as measured.
- Adding catalogue coverage to standard coverage (take the larger).
- Counting a module that needs a port as free.
- Removing a compliance item because it shortens the schedule.
- Keeping the estimate only in the document; the workbook must recalculate.
